# PROTOCOL — baseline ↔ 세션 전달 규약 (baseline-1.0, 2026-10-02)

세션은 서로 직접 지시하지 않는다. **모든 요청 · 보고 · 지시는 baseline 을 거친다**(허브 하나, 바퀴살 여럿).
같은 것을 두 세션이 짓는 일(2026-10-02 liveness 가 실제로 그랬다)을 막기 위해서다.

```
   [Telemetry 세션] ─보고─┐                      ┌─지시─► [Telemetry 세션]
   [Sensor 세션]    ─보고─┤                      ├─지시─► [Sensor 세션]
   [DC 세션]        ─보고─┼──► baseline ──판단──┼─지시─► [DC 세션]
   [MS 세션]        ─보고─┘   (이 저장소 + 이 세션)  └─지시─► [MS 세션]
                                   │
                         통합: 저장소마다 claude/gracious-meitner-vp49xe
```

## 1. 통로

| 방향 | 통로 | 꼴 |
|---|---|---|
| 세션 → baseline (보고 · 질문 · 다른 세션에 대한 요청) | **cogito5170/baseline 의 이슈, 세션마다 하나.** 제목 머리 `[Telemetry]` · `[Sensor]` · `[DC]` · `[MS]`. 보고 하나 = 댓글 하나 | §2 의 보고 꼴 |
| baseline → 세션 (판단 · 지시) | 그 세션의 이슈에 **댓글** + 세션을 깨우는 **세션 메시지**(댓글을 가리키는 한 줄) | §3 의 지시 꼴 |
| 구속력 있는 결정 | 이 저장소의 `claude/gracious-meitner-vp49xe` — DECISION_LOG(BD) · BASELINE §13 · 이 문서 | 이슈 댓글은 결정의 전달이다. 결정의 원본은 이 저장소다 |
| 세션 ↔ 세션 | **없다.** 다른 세션의 일이 필요하면 자기 이슈에 `요청: <대상 세션> …` 으로 적는다. baseline 이 소유 세션에 지시로 옮긴다 | |

MS 세션이 이 저장소의 자기 브랜치(`claude/eloquent-turing-m33zjw`, `MS/` 폴더)에 남긴 보고 파일은 그대로 기록으로 둔다. 다음 보고부터는 이슈로 한다.

## 2. 보고 꼴 (세션 → baseline)

```
[<세션>] <한 줄>
처리한 지시: CMD-xx ✅ · CMD-yy ⏸(까닭)            ← 받은 지시마다 하나
커밋: <저장소>@<브랜치> <sha> …
시험: 몇 개 통과 · 변이 · 실데이터 대조(있으면)
확인하지 못한 것:
묻는 것 / 요청: <대상 세션> …
```

## 3. 지시 꼴 (baseline → 세션)

```
CMD-<세션 머리글자><번호>  <할 일 한 줄>
  근거: BD-xx / PC-xx / 보고의 어느 줄
  범위: 손대도 되는 파일 · 손대면 안 되는 파일
  끝난 기준: 시험 · 확인할 것
  순서: 앞에 끝나야 하는 지시
```

머리글자: T = Telemetry · S = Sensor · D = DC · M = MS. 번호는 세션마다 1 부터.

## 4. 통합 규칙

1. 세션은 **자기 브랜치에만** 푸시한다.
2. 세션은 새 일을 시작할 때마다 **통합 브랜치를 먼저 합친다**:
   `git fetch origin claude/gracious-meitner-vp49xe && git merge origin/claude/gracious-meitner-vp49xe` (각 저장소에서).
3. baseline 은 프롬프트마다 모든 저장소 · 브랜치 · 이슈를 다시 읽는다. 세션 브랜치를 통합 브랜치로 합치고, 시험을 옆 저장소와 함께 돌리고, 결과를 §13 에 적는다.
4. PR · 기본 브랜치로의 합치기는 세션이 하지 않는다. 통합 브랜치가 단계를 마치면 baseline 이 사용자에게 묻고 한다.

## 5. 소유 — 파일 하나에 세션 하나 (BD-45)

| 저장소 · 경로 | 소유 세션 | 비고 |
|---|---|---|
| Telemetry `*` | **Telemetry** (`jolly-einstein`) | L0 사건 이름 · 꼴 · 수집기의 유일한 주인 |
| Sensor `llmsensor/telemetry/*` · `schema/*` | **Telemetry** | L0 ↔ Sensor 꼴 v3 경계(`l0.py` · compat) |
| Sensor `llmsensor/sensing/*` · `llmsensor/state/*` (아래 제외) · `sensors/*` · `verifier.py` · 그 밖 | **Sensor** (`nice-wright`) | **L1 팩 전부**(liveness · recovery · dependency · action_outcome 포함) |
| Sensor `llmsensor/state/export.py` (state-export/1) | **Sensor** | 바깥(DC)이 읽는 유일한 길. 바꾸려면 DC 가 baseline 을 거쳐 요청 |
| DC `*` | **DC** (`nifty-volta`) | |
| MS `ms/l0.py` · `tests/test_l0.py` | **Telemetry** | MS 안의 L0 Recorder 배선 |
| MS 그 밖 `*` | **MS** (`eloquent-turing`) | `runtime.py` 의 `state_reader` 이음매 포함 |
| baseline `*` | **baseline** (이 세션) | |

소유하지 않은 파일을 고쳐야 하면 고치지 말고 이슈에 `요청:` 으로 적는다.
