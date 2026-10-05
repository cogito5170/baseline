# FINAL TASK — 토큰 사용량 비교 실험 (POL-3 P4, BD-314)

**언제:** 지금이 아니라 ④ 구조 완성 뒤(NET1–5 · GA28 · GA30 · GA31 판정 끝). 사용자 지시(2026-10-04) 원문의 규칙 · 측정값을 그대로 고정한다.

## 1. 실행 규칙 (모든 비교 대상에 똑같이)

1. 필요한 정보만 Context 에서 선택한다.
2. 이미 State 에 있는 사실을 다시 추론하지 않는다.
3. 필요한 정보가 없으면 추측하지 말고 UNKNOWN 으로 둔다.
4. 필요한 경우에만 tool/peer 를 사용한다.
5. 작업을 완료한 뒤 측정값(§3)을 반환한다.

규칙을 지키는 기존 부품: 1 → ctxpack 상한 · MS ContextPolicy(KEEP/SUMMARIZE/RETRIEVE/DROP) · 2 → DC 가 State 의 유효한 값을 먼저 씀(값이 있고 VALID 면 다시 구하지 않음) · 3 → Sensor/DC Status UNKNOWN(0 으로 메우지 않음) · 4 → DC `peer_interaction`(기본 skip) · π 임계 · Arbiter/Guard.

## 2. 비교 대상 (같은 과제 · 같은 모형 표 · 각 3 회)

| 팔 | 구조 |
|---|---|
| A | 지금 방식: 오래 사는 LLM baseline 이 판정 · 지시, 작업 세션은 fresh |
| B | ③: 가운데는 코드(ga tick + ga judge), 작업 세션 fresh |
| C | ④: 노드끼리 직접(π · 간선 예산), 가운데는 코드 런타임 |

과제 묶음(정답이 정해진 것만):
- T1 능력 공백: 이미지 입력을 못 받는 모형의 노드가 이미지 설명이 필요한 일을 받음(정답 = 이미지 내용)
- T2 저장소 변경: 함수 + 시험 추가(정답 = 숨은 검사 통과)
- T3 모순: 두 노드가 같은 StateRef 에 다른 값(정답 = 근거로 확정된 값, 또는 근거 부족이면 UNKNOWN)
- T4 이미 아는 것: 답이 이미 State 에 있음(정답 = 도구 · 동료 0 회로 답함 — 규칙 2 시험)
- T5 정보 없음: 답할 근거가 어디에도 없음(정답 = UNKNOWN — 규칙 3 시험)

## 3. 반환 측정값 (`final-task-metrics/1`, 과제 · 팔 · 회차마다 한 줄)

| 칸 | 정의 | 출처 |
|---|---|---|
| input_tokens | 모든 LLM 호출의 input + cache_read + cache_creation 합(세 값도 따로 적음) | 공급자 usage → Telemetry L0 `llm.response` / ga `run.end` |
| output_tokens | 모든 호출의 output(thinking 포함, 따로 적음) | 같음 |
| total_tokens | input_tokens + output_tokens | 계산 |
| tool_calls | 도구 호출 수 | L0 `tool.start` |
| peer_messages | 노드 사이 메시지 수 | L0 `peer.message.sent`(NET1) |
| context_items_used | 프롬프트에 실제로 들어간 단위 수(State 항목 · inbox 머리 · 참조 파일 조각 · 동료 메시지; KEEP/SUMMARIZE/RETRIEVE 별로 나눠 적음) | ctxpack 머리 · ContextPolicy 결과 |
| context_items_available | 정책 적용 전 후보 단위 수 | 같음(drop 기록 포함) |
| repeated_information | (a) 같은 내용(근거 id · 내용 해시)이 한 실행 안에서 두 번 이상 프롬프트에 들어간 횟수 + (b) State 에 이미 VALID 로 있던 사실을 다시 구한 횟수(값이 바뀌지 않은 재계산 · 같은 질의 도구 호출) | ctxpack 단위 해시 · StateEngine 전이 로그 · L0 |

덧붙여(합격 판단용): `result_correct`(정답 일치), `unknown_correct`(T5 에서 UNKNOWN 을 냈나), `tokens_per_correct` = total_tokens / 맞은 과제 수.

## 4. 합격 기준

- C 의 tokens_per_correct ≤ A, 그리고 정답률 C ≥ A(토큰만 줄고 결과가 나빠지면 실패).
- T4 에서 tool_calls = peer_messages = 0, T5 에서 UNKNOWN(추측하면 실패).
- repeated_information 이 A 보다 적음.
- spec §15: 높은 연결도 · 많은 메시지를 지능의 증거로 보지 않는다.

## 5. 실행 설정 (사용자 결정 2026-10-05, BD-329)

- 노드 3 개, 모두 Haiku(`claude-haiku-4-5-20251001`), fresh 모드(ga 0.5.0 · ctxpack), 실행 주체는 `claude -p` bare 호출(BD-302).
- 비용 상한: 전체 $15(팔 A · B · C × 과제 T1–T5 × 3 회 = 45 실행). 상한에 닿으면 그 자리에서 멈추고 그때까지의 측정값으로 보고(부분 결과로 표시).
- 시작 조건: CMD-GA32 rev 3(ga 0.5.0, ga-sdk[net]) 판정 성공 뒤. 실행 · 측정은 새 세션 하나(CMD-FT1)가 하고, baseline 은 판정만 한다.
