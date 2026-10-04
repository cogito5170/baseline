"""컨텍스트 예산 훅 원형(BD-296) -- rlo 훅에 넣을 동작의 기준. 제품은 SDK 가 rlo-sdk 에 짓는다(CMD-K17).

긴 자율 세션은 모형을 부를 때마다 쌓인 대화 전체를 다시 읽는다(캐시 읽기). 그래서 토큰은
'컨텍스트 크기 x 호출 수' 로 늘어난다. 이 훅은 컨텍스트가 예산을 넘으면 세션이 일을 줄이고
상태를 파일에 남긴 뒤 차례를 끝내게 한다. 새 컨텍스트(새 세션 · 압축)는 그 파일에서 다시 시작한다.

컨텍스트 = 직전 주 사슬 assistant 응답의 usage 에서 input + cache_read + cache_creation (원천이 보고한 값, L0).
문서에 있는 훅 출력만 쓴다(PreToolUse: hookSpecificOutput.permissionDecision / permissionDecisionReason /
additionalContext). 압축을 요청하는 훅 출력은 문서에 없다 -- 그래서 '끝내고 다시 시작' 은 바깥(오케스트레이터)이 한다.

    단계        조건                 PreToolUse 출력
    ok          ctx < soft           {} (다른 훅 · 가드에 맡김)
    warn        soft <= ctx < hard   additionalContext: 예산 알림, 지금 하는 일만 끝내고 checkpoint
    checkpoint  ctx >= hard          checkpoint 도구(상태 파일 쓰기 · git add/commit/push)만 allow, 나머지 deny + 까닭
    unknown     usage 를 못 읽음      {} (모름은 막지 않는다 -- 가드의 rule D 와 같은 태도; 기록만)
"""
from __future__ import annotations

import json
import re

NAME = "context-budget/1"


def context_tokens(transcript_path: str) -> "int | None":
    """transcript JSONL 의 마지막 주 사슬 assistant usage -> 컨텍스트 토큰. 못 읽으면 None(0 으로 메우지 않음)."""
    last = None
    try:
        with open(transcript_path, encoding="utf-8") as f:
            for line in f:
                try:
                    d = json.loads(line)
                except ValueError:
                    continue
                if d.get("type") != "assistant" or d.get("isSidechain"):
                    continue
                m = d.get("message") or {}
                if m.get("model") == "<synthetic>":
                    continue
                u = m.get("usage")
                if isinstance(u, dict):
                    last = u
    except OSError:
        return None
    if not last:
        return None
    parts = [last.get(k) for k in ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens")]
    if any(p is None for p in parts):
        return None
    return sum(parts)


def is_checkpoint(tool_name: str, tool_input: dict, state_paths: "tuple[str, ...]") -> bool:
    """상태를 남기는 일만: 상태 파일 Write/Edit, 그리고 git add/commit/push 만 있는 Bash."""
    if tool_name in ("Write", "Edit"):
        p = str((tool_input or {}).get("file_path", ""))
        return any(p.endswith(s) for s in state_paths)
    if tool_name == "Bash":
        cmd = str((tool_input or {}).get("command", ""))
        parts = [c.strip() for c in re.split(r"&&|;|\n", cmd) if c.strip()]
        ok = re.compile(r"^(cd\s+\S+|git\s+(-C\s+\S+\s+)?(add|commit|push|status)\b.*)$")
        return bool(parts) and all(ok.match(c) for c in parts)
    return False


def decide(ctx: "int | None", tool_name: str, tool_input: dict, *, soft: int, hard: int,
           state_paths: "tuple[str, ...]" = ("STATE.md",)) -> "tuple[str, dict]":
    """-> (단계, PreToolUse JSON 출력)."""
    if not (0 < soft <= hard):
        raise ValueError("need 0 < soft <= hard")
    if ctx is None:
        return "unknown", {}
    if ctx < soft:
        return "ok", {}
    note = (f"[{NAME}] context is {ctx} tokens (soft {soft}, hard {hard}). Every model call re-reads all of it. "
            f"Finish only the current step, write your state to {state_paths[0]}, commit and push it, then end your turn. "
            "Do not read more issues or logs in this turn.")
    if ctx < hard:
        return "warn", {"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": note}}
    if is_checkpoint(tool_name, tool_input, state_paths):
        return "checkpoint", {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "allow",
                                                     "additionalContext": note}}
    return "checkpoint", {"hookSpecificOutput": {
        "hookEventName": "PreToolUse", "permissionDecision": "deny",
        "permissionDecisionReason": f"[{NAME}] over the hard budget ({ctx} >= {hard}): only checkpoint tools are "
                                    f"allowed (write {state_paths[0]}, git add/commit/push). Then end your turn."}}


def simulate(contexts: "list[int]", *, soft: int, hard: int, reset_to: int, calls_after_hard: int = 2) -> dict:
    """기록된 호출별 컨텍스트로 '예산이 있었다면' 을 셈한다(추정, L1). hard 를 넘은 뒤 checkpoint 호출
    calls_after_hard 번을 더 하고, 그다음 호출부터 새 컨텍스트(reset_to 토큰)에서 다시 시작해 원래 기록의
    증가분만큼 자란다고 본다. 기록에서 컨텍스트가 크게 줄면(실제 압축) 그 뒤는 기록 그대로 둔다."""
    actual = sum(contexts)
    sim, shift, pending, resets, warn, prev = 0, 0, None, 0, 0, None
    for c in contexts:
        if prev is not None and c < prev * 0.6:
            shift = 0                       # 실제 압축이 있었다 -- 기록이 이미 줄었다
        prev = c
        cur = max(1, c - shift)
        if pending is not None:
            if pending == 0:
                shift = c - reset_to
                cur = reset_to
                pending = None
                resets += 1
            else:
                pending -= 1
        elif cur >= hard:
            pending = calls_after_hard
        elif cur >= soft:
            warn += 1
        sim += cur
    return {"calls": len(contexts), "actual_tokens_read": actual, "simulated_tokens_read": sim,
            "saved_pct": round(100 * (1 - sim / actual), 1) if actual else 0.0, "resets": resets, "warn_calls": warn}
