# CONTEXT BUDGET — 긴 세션의 토큰을 줄이는 rlo 훅 (BD-296)

## 1. 왜 — AO 토큰 분석 (Telemetry L0, 2026-10-04)

AO(session_01JWUCzhkqtsYpyJ6PyRq9cA) 의 이벤트 기록(list_events)을 Claude Code JSONL 꼴로 바꿔 Telemetry
`from_cc_jsonl` 에 넣고, 나온 `llm.response` · `tool.start/end` 사건만으로 셈했다([`ops/ctxbudget/ao_tokens.py`](ops/ctxbudget/ao_tokens.py)).
주 사슬만(하위 에이전트 제외), AO 의 누적 보고(cache_read 172M)와 거의 맞음.

| 항목 | 값 |
|---|---|
| 모형 호출 | 448 |
| 읽은 토큰(캐시 읽기 + 쓰기 + 입력) | 171.5M — **캐시 읽기 168.7M (98.4%)** |
| 출력 토큰 | 49.9k (0.03%) |
| 호출 한 번의 컨텍스트 | 평균 383k · 중앙값 318k · 최대 783k |
| 컨텍스트 ≥ 300k 인 호출 | 238 / 448 — 이 호출들이 읽은 토큰 129.9M (**76%**) |
| 압축 | 1 번(783k → 72k) |
| 컨텍스트에 들어간 새 글 | 도구 결과 ~0.7M 자 · 도구 입력 ~0.45M 자(대부분 Bash 로 올린 긴 지시 · 보고 본문) |

컨텍스트를 채운 것(글자 × 그 뒤 압축까지의 호출 수, 큰 순): Bash(gh · curl · git) 94.6M · ReadNotifications 20.5M ·
Write 9.7M · send_message 8.7M · update_trigger 8.1M · github issue_read 6.0M · list_events 5.4M.

무엇이 호출을 일으켰나(전체 기록 23 쪽 · 결과 사건 78 개 기준):

| 차례를 연 것 | 차례 | 호출 | 캐시 읽기 몫 |
|---|---|---|---|
| 다른 세션의 메시지(send_message, 52 통 중 32 통이 baseline) | 49 | 353 (68%) | 77% |
| 예약 루틴(안전망 · 3 시간 감시) | 13 | 67 (13%) | 14% — 그리고 **캐시 쓰기의 71%**: 3 시간 간격이 1 시간 캐시보다 길어 깰 때마다 70 만 토큰을 다시 씀 |
| 사용자 | 8 | 82 (16%) | 9% |

지시가 불분명해서 헛돈 흔적은 약하다: 되묻기 1 번, 'unclear' 류 없음, 되풀이는 CMD-AO3 rev 2→4(사용자가 목표를 바꾼 13:09–13:21, 캐시 읽기의 약 5%).
압축 전 반쪽(380 호출, 평균 380k+)이 캐시 읽기의 85%.

**결론.** 토큰은 '모형이 많이 쓴 것' 도 '지시가 틀려 헛돈 것' 도 아니다(출력 0.03%). 한 세션이 하루 넘게 살면서
대화를 30만~78만 토큰까지 쌓고, 알림이 올 때마다 그것을 통째로 다시 읽은 것이다(호출 448 × 평균 383k).
새로 들어온 글은 도구 결과(GitHub 본문 · 알림 본문)와 AO 가 쓴 긴 지시 본문이고, 그것들이 압축 전까지 수백 번 다시 읽혔다.

## 2. 무엇 — 컨텍스트 예산 (`context-budget/1`)

원형: [`ops/ctxbudget/ctxbudget.py`](ops/ctxbudget/ctxbudget.py) (시험 6, 변이 2/2 잡힘). PreToolUse 훅에서:

| 단계 | 조건 | 훅 출력(문서에 있는 칸만) |
|---|---|---|
| ok | ctx < soft | 없음 — 가드에 맡김 |
| warn | soft ≤ ctx < hard | `additionalContext`: 지금 단계만 끝내고 STATE.md 에 상태를 쓰고 push 한 뒤 차례를 끝내라 |
| checkpoint | ctx ≥ hard | 상태 파일 Write/Edit · `git add/commit/push` 는 막지 않음(알림만; `allow` 는 내지 않음 — BD-299), 나머지 `deny` + 까닭 |
| unknown | usage 를 못 읽음 | 없음 — 모름은 막지 않음(기록만) |

ctx = transcript 의 마지막 주 사슬 assistant `usage` 의 input + cache_read + cache_creation(원천 보고값).
압축을 요청하는 훅 출력은 문서에 없다 → 다시 시작(압축 · 새 세션)은 바깥(오케스트레이터 · 사람)이 STATE.md 에서 한다.

## 3. 얼마나 — AO 기록에 대본 추정(L1, 같은 일의 양 가정)

| soft / hard | 다시 시작 | 읽은 토큰 | 절감 |
|---|---|---|---|
| 100k / 150k | 10 | 50.4M | −70.6% |
| **150k / 200k** | 6 | 62.5M | **−63.6%** |
| 200k / 300k | 4 | 86.8M | −49.4% |

가정: hard 뒤 checkpoint 호출 2 번, 다시 시작한 컨텍스트 72k(AO 의 실제 압축 뒤 크기), 그 뒤 증가분은 기록과 같음.
다시 시작할 때 STATE.md · 이슈를 다시 읽는 비용은 넣지 않았다 — 실제 절감은 shadow 측정으로 다시 잰다.

## 4. 적용 순서

1. SDK: `rlo` 에 제품(CMD-K17) — 기본값 없음(예산은 연동 쪽, BD-289), shadow(기록만) → enforce.
2. ga rlo 훅 생성에 연결(GR, K17 판정 뒤).
3. 세션에 설치는 사용자 몫(가드 · 설정 변경): 먼저 shadow 로 한 세션, 측정 뒤 enforce.
