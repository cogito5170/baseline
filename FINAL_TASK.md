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

## 5. 실행 설정 (사용자 결정 2026-10-05, BD-329 → BD-330 으로 바뀜)

사용자: "FINAL_TASK 는 haiku 와 sonnet 을 모두 사용한다. '단 1회의 호출이라도 프로젝트 파일들을 대량으로 컨텍스트에 주입(수만~수십만 토큰)하거나 연산 가중치가 높은 무거운 모델을 사용할 경우 쿼터가 크게 소모됩니다' 라는 설명에 맞게, 쿼터 소모량을 비교해보아라."

### 5.1 요인 (두 요인이 그 설명의 두 원인과 1:1)

| 요인 | 수준 | 설명의 어느 부분 |
|---|---|---|
| 모형 | Haiku 4.5 (`claude-haiku-4-5-20251001`) · Sonnet 5.5 (`claude-sonnet-5-5`) | "연산 가중치가 높은 무거운 모형" |
| 문맥 주입 | selective(ctxpack · State · 규칙 1–4) · bulk(작업 저장소 파일을 통째로 프롬프트에 넣음, 호출당 50k–150k 토큰; Haiku 창 200k 안) | "프로젝트 파일 대량 주입" |
| 구조 | A · B · C (§2) | 우리 설계의 효과 |

### 5.2 실행 행렬 (노드 3, fresh 모드, bare `claude -p`)

- 주 행렬: 팔 A · B · C × 모형 2 × T1–T5 × 3 회, 문맥 selective = 90 실행.
- bulk 대조: 팔 A × 모형 2 × T1–T5 × 1 회, 문맥 bulk = 10 실행(같은 과제 · 같은 모형의 selective 와 짝지어 비교).
- 비용 상한 전체 $35(예상: selective Haiku ~$8 · Sonnet ~$17 · bulk ~$5 — BD-307 의 실행당 $0.19 를 위쪽 어림으로). 상한에 닿으면 멈추고 부분 결과로 보고. 실행 순서는 bulk 대조와 각 팔의 Haiku/Sonnet 짝을 먼저(멈춰도 비교가 남게).

### 5.3 쿼터 측정 (`final-task-metrics/1` 에 칸 추가)

정액 구독 쿼터의 토큰별 가중치는 공개되어 있지 않다. 그래서 **API 정가 환산(USD)을 쿼터 대용치**로 쓰고, 원 토큰 수를 함께 적는다(가중치가 바뀌어도 다시 계산 가능).

| 칸 | 정의 |
|---|---|
| quota_usd | 모든 호출의 Σ(input×p_in + cache_creation×1.25·p_in + cache_read×0.1·p_in + output×p_out). 정가(/Mtok): Haiku 4.5 in $1 · out $5, Sonnet 5.5 in $2 · out $10 (claude-api 참고 2026-09-25 · ga/backends/catalog.py 와 같음). `claude -p` JSON 의 total_cost_usd 와 대조 |
| quota_hte | quota_usd 를 Haiku 입력 토큰 환산으로(= quota_usd / $1e-6) |
| max_call_input | 한 실행 안에서 입력(input+cache_read+cache_creation)이 가장 큰 호출의 토큰 수 — "단 1회의 호출이라도" 를 직접 잼 |
| max_call_share | 그 가장 큰 호출의 quota_usd 가 실행 전체에서 차지하는 비율 |
| quota_per_correct | quota_usd / 맞은 과제 수 |

### 5.4 보고할 비교 (가설, 미리 고정)

- H1 bulk vs selective(같은 모형 · 팔 A): quota_usd 비, max_call_input 비, 정답률 차. 설명이 맞다면 bulk 가 수 배 이상 크고 정답률은 같거나 낮다.
- H2 Sonnet vs Haiku(같은 팔 · selective): quota_per_correct 비. 단가는 2 배지만 실행당 호출 · 재시도 수가 달라 실제 비는 다를 수 있다 — 과제별로 어느 모형이 맞힌 과제당 쿼터가 적은지(라우터 §7 의 근거).
- H3 C vs A(같은 모형): §4 합격 기준을 모형별로 따로 판정.
- 모든 비는 3 회 평균과 범위를 같이 적고, 1 회뿐인 bulk 는 "1 회" 로 표시.

## 6. 결과 (CMD-FT1 rev 1 + rev 2, ga-sdk `5e8ef4b`, BD-332 · BD-333)

전체 100/100 유효 실행(rev 1 의 T2 12 행은 무효로 남김), `claude -p` 213 호출, 쿼터 usage 기준 $9.60 · CLI 기준 $18.32(상한 $35). 표 전체: ga-sdk `bench/final_task/results/SUMMARY.md`. baseline 이 ledger 로 다시 셈 — 합계 · 실행 수 · 정답률 일치.

| 비교 | Haiku | Sonnet |
|---|---|---|
| H1 bulk/selective 쿼터 (usage · CLI) | 24.7× · 47.3× | 59.8× · 63.1× |
| H1 가장 큰 호출 입력 | 110,559 vs 1,565 (70.6×) | 131,014 vs 1,980 (66.2×) |
| H1 정답 bulk · selective | 5/5 · 5/5 | 4/5 · 5/5 |
| H3 C vs A 맞힌 과제당 토큰 | 3,776 vs 8,117 | 2,408 vs 5,833 |
| H3 C vs A 맞힌 과제당 쿼터 (usage) | $0.0118 vs $0.0218 | $0.0037 vs $0.0145 |
| H3 정답 C · A | 15/15 · 14/15 | 15/15 · 15/15 |
| H3 repeated_information C · A | 0.33 · 3.73 | 0.33 · 3.20 |
| H3 §4 판정 | PASS | PASS |

- H2(selective, 맞힌 과제당): T1 은 Haiku 가 쌈(Sonnet 1.08× usage · 1.49× CLI); T2–T5 는 Sonnet 이 쌈(0.42–0.59× usage · 0.59–0.84× CLI). 까닭: Sonnet 은 반복되는 짧은 프롬프트가 캐시 읽기(0.1×)로 잡혔다. 큰 문맥(bulk)에서는 Sonnet 이 Haiku 의 약 2.3×(usage) · 1.8×(CLI).
- 해석: "대량 주입 · 무거운 모형이 쿼터를 크게 쓴다" — 대량 주입은 두 측정 모두 수십 배로 확인. 무거운 모형은 큰 문맥에서만 확인, 작은 선택 문맥에서는 캐시 때문에 오히려 쌀 수 있음. 가장 큰 절감은 구조(C · B: 호출 1–1.3 개, 반복 정보 거의 0)와 선택 문맥에서 나옴.
- 한계: 과제 5 종 · 3 회 · 노드 3 의 작은 실험; 실제 구독 쿼터 가중치는 공개되지 않아 두 측정을 나란히 둠; `claude -p` 는 호출마다 내부 Haiku 호출을 더해 CLI 비용이 usage 의 약 1.9×.
