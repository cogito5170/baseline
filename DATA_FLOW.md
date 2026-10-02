# DATA FLOW — Sensor → Telemetry → State → Model/Relationship → DC → Policy → Arbitration → Action → Verification

(baseline-0.1, 제안) 낱말의 뜻은 [`SEMANTIC_MODEL.md`](SEMANTIC_MODEL.md), 칸은 [`SCHEMA_PROPOSAL.md`](SCHEMA_PROPOSAL.md) 에 있다.

## 1. 단계 계약 — 한 표

| # | 단계 | 입력 | 출력 | 소유 (유일한 쓰는 쪽) | 방아쇠 | 실패하면 |
|---|---|---|---|---|---|---|
| 1 | Sensor 수집 | 원천(API 응답 · 스트림 · JSONL · 도구 결과 · 사람 피드백 · 외부 라벨) | Observation (`unobserved` · `reported_null` 표시) | 수집기 (Sensor `telemetry/collect.py`, MS `providers/`) | 원천 사건 | 칸을 `unobserved` 로. 지어내지 않는다 |
| 2 | Telemetry 운반 | Observation | Telemetry 레코드 (꼴 판본 · record_id) | 수집기 → Runtime ingest | — | 같은 record_id 는 버린다(멱등). 꼴 위반은 격리함 |
| 3 | Measure | Observation (Model 의 바인딩 · 측정 정의) | Measurement (+ `derived_from`) | L2 | 관측 도착 | 입력이 모자라면 UNKNOWN |
| 4 | Estimate | Measurement · 이전 State (Model 의 규칙) | State · 전이 · 생애 사건 | L3 (상태 이름마다 규칙 하나) | Measurement 변화 · `tick(now)` | UNKNOWN · STALE 로 표시. 지우지 않는다 |
| 5 | Assess | State · Measurement · Model(기대값 · 고장 모드) · Relationship | 건강 · 고장 State | L4 | State 변화 · 관측 결손 | 판정 근거가 없으면 UNKNOWN |
| 6 | Relationship 갱신 | Observation(간선 증거) · 구조 선언 | 실체 간선 + 유효 구간 | L3 / Runtime (OQ-07) | 관측 도착 · 선언 | — |
| 7 | Contextualize | State Store · Relationship · 목적(Model) · 요청(제약 · 능력) · `now` | DecisionContext (고정 · 내용 해시) | L5 (DC) | 결정 요청 · DC 가 가리키는 키의 (값, 유효성) 변화 · TTL 만료 | 필수 상태가 못 쓰이면 `complete=False`. 빌드 자체가 실패하면 DC 없음 (§6.5) |
| 8 | Decide | DecisionContext 만 | Decision = ActionIntent[] + 까닭 + 사용 키 + 판본 | L6 Policy | DC 도착 | 실행기 오류 → 의도 없음 + 자기 관측 (A0 처럼) |
| 9 | Validate | ActionIntent · 그 DC · ActionSpec(Model) | 유효 의도 / 거절 + 까닭 | L7 | Decision | 거절 → 원장 + 자기 관측 |
| 10 | Arbitrate | 유효 의도 여럿 · 우선순위 · `conflicts_with`(Model) | 선택 의도 하나 (또는 없음) | L8 | 판(round)의 마감 | 고를 것이 없으면 없음 |
| 11 | Guard | 선택 의도 · **지금** State · 제약 · 권한 · 안전 규칙(Model) | ALLOW → ActionCommand / DENY / SAFE_ACTION | L9 | 배차 직전 · 안전 관련 상태 변화 | 예외 → DENY (enforce) |
| 12 | Execute | ActionCommand | ActionOutcome (Observation 으로) | L10 실행기 | 허가 | 실행 오류도 Observation (`tool_error`) |
| 13 | Verify | Command · ActionSpec 사후조건 · 그 뒤의 State | Verification (`action_state` State) | L11 | 결과 관측 도착 · 사후조건의 시간 창 만료 | 판정 못 하면 UNKNOWN |
| ↺ | 되먹임 | 12 · 13 의 결과 · 모든 단계의 자기 관측 | → 1 | — | — | — |

**결정 원장 (Decision Ledger).** 7–13 의 각 단계는 같은 DecisionRecord 에 **자기 절만** 덧붙인다. 텔레메트리에는 `decision_ref` 만 실린다.

## 2. 관측이 결정이 되기까지 — 승인 시험의 "Autonomy" 물음에 대한 답

| 물음 | 답 | 무엇이 지키나 |
|---|---|---|
| 관측은 어떻게 상태가 되나? | 관측 → (바인딩 · 측정 정의) → Measurement → (규칙 id@판본) → State. 층을 건너뛰지 않는다: 상태 규칙의 입력은 Measurement 뿐이다 | Sensor `registry.check()` + 시험. MS 는 바인딩 · 파생으로 같은 일을 한다 |
| 상태는 어떻게 근거가 되나? | 상태는 근거가 **되는** 것이 아니라 근거를 **가진다**. `evidence_refs` 가 Measurement → Observation 으로 되짚힌다. 다른 결정 · 상태의 입력으로 쓰일 때 그 State id 가 다음 것의 근거 참조가 된다 | DC I5 · Sensor `explain()` |
| 근거는 어떻게 결정 문맥이 되나? | DC 는 근거를 **참조**로만 싣는다(복사하지 않는다). Validate 단계가 근거 없는 상태를 INVALID 로 강등한다 | DC `NO_EVIDENCE` · `NO_RULE` |
| 문맥은 어떻게 결정이 되나? | Policy(판본)가 DC 의 **usable 값**만 읽는다. 쓸 수 없으면 None(=모름)이다. 모름으로는 행동을 바꾸지 않는다 — 목적의 기본값을 쓴다 | DC `value()` · `policy_state()` · Sensor 참조 정책 |
| 결정은 어떻게 묶이나? | Validate(꼴 · 근거) → Arbitrate(선택) → Guard(허가 · 안전, **지금** 상태 기준) | (GAP-02 · 03: 아직 MS Arbiter 하나) |
| 행동은 어떻게 실행되나? | Guard 가 낸 ActionCommand 를 실행기가 받는다. 실행 자리는 하나다 | MS `pipeline` 의 호출 자리 하나 (시험) |
| 행동 성공은 어떻게 검증하나? | 실행기의 "됐다" 는 관측일 뿐이다. 사후조건이 그 뒤의 상태에서 성립하는지를 L11 이 본다 | 없음 (GAP-05) |

## 3. 흐름 그림 — 실제 예 (Sensor §40 수치)

```
[1 Sensor]   model_call: input_tokens=10 cache_read=130000 cache_creation=6990 · run: context_window=180000 autocompact_threshold=144000
             tool_call × 11 (pytest 1회 실패 뒤 성공, WebFetch 실패)
[2 Telem.]   llm-telemetry/v3 레코드, record_id 로 멱등
[3 Measure]  context_tokens=137000 · context_utilization=0.761 · tool_failure_rate=0.1818
[4 Estimate] agent.context_pressure=BELOW_COMPACTION_THRESHOLD (RUNTIME_DECLARED)
             agent.execution_health=UNRESOLVED_FAILURES (DEFINITIONAL) · tool[WebFetch].tool_execution_health=UNRESOLVED_FAILURES
[5 Assess]   (WebFetch 실패 원인 EGRESS_BLOCKED 이 구조화돼 있으면) dependency fault = 네트워크 정책 — 고장 모드가 Model 에 있을 때만
[7 DC]       purpose=execution_control · states 10 · complete=True · actions: CONTINUE · RETRY(retry_budget) · ESCALATE(human_reviewer) · STOP
[8 Decide]   Intent RETRY (까닭: 풀리지 않은 도구 실패)
[9–11]       Validate ✔ → Arbitrate (후보 하나) → Guard: retry 상한 · 비용 제약 · 근거 신선도 확인 → ALLOW
[12 Execute] 재시도 명령 → 도구 결과 Observation
[13 Verify]  사후조건 "그 겨냥의 마지막 결과가 성공" → execution_health 가 RECOVERED_FAILURES 로 바뀌었나 → action_state=VERIFIED / NOT_VERIFIED
```

## 4. 사건 구동 · 무엇을 보내나

| 대상 | 계속 보내나 · 사건으로 보내나 | 까닭 |
|---|---|---|
| Observation | 사건 (원천이 낼 때) | 원천이 사건 꼴이다 |
| State | **바뀔 때만** 생애 사건 (CREATE · UPDATE · STALE …) | 같은 값의 되풀이는 REFRESH 하나 |
| DecisionContext | 결정이 필요할 때만. DC 가 가리키는 키의 (값, 유효성)이 그대로면 **digest 가 같다 → 다시 쓴다** | 내용 해시가 곧 뜻의 캐시 키다 |
| Decision · Guard 결과 | 결정마다 원장에. 텔레메트리에는 id 와 결과 수만 | BV-04 |
| 안전 상태 | 바뀔 때 Guard 를 깨운다 | 명목 고리를 기다리지 않는다 |

## 5. FDIR — 부품마다

열: 무엇이 고장 나나 · 어떻게 관측하나 · 환경 변화와 어떻게 가르나 · 어느 상태가 나타내나 · 근거 · 반응하는 정책 · 묶는 안전 장치 ·
허용 행동 · 복구 확인.

| 부품 | 고장 | 관측 | 환경과 가르기 | 상태 | 근거 | 반응 정책 | 안전 장치 | 허용 행동 | 복구 확인 |
|---|---|---|---|---|---|---|---|---|---|
| C1 수집기 · 센서 어댑터 | 멈춤 · 꼴 바뀜 · 칸 놓침 (Sensor 조사 D1–D4 가 실제로 났다) | 레코드 끊김 · `unobserved` 급증 · 꼴 검증 실패 | **같은 기록 안에서는 가를 수 없다**(조사 결론). 기록 밖 채널(프로세스 확인 · 합성 점검)이 있어야 한다 | `collector.liveness` (계획: ENDED · ENDED_WITHOUT_RESULT · AWAITING_INPUT · ACTIVE · UNKNOWN) | 마지막 레코드 시각 · 끝 `result` 유무 | 이 수집기가 `observes` 하는 실체의 상태를 쓰는 목적 전부: 모름 → 기본값 | 그 상태를 사전조건으로 쓰는 행동은 Guard 가 거부 | HOLD · ESCALATE | 새 레코드 도착 + 꼴 검증 통과 |
| C2 텔레메트리 운반 · ingest | 중복 · 순서 뒤집힘 · 늦게 도착 | record_id 중복 · 시각 역전 | 순서는 환경(네트워크)이다 → 고장 아님. 꼴 위반만 고장 | 격리함 수(MS `quarantine`) · `ingest.rejected_rate` | 격리 레코드 | — | — | — | 격리율이 되돌아옴 |
| C3 Provider (LLM API) | 429 · 5xx · 시간 초과 · 거절 | `api_error_status` · `rate_limit_status` · `stop_reason` | 429 · 리셋 시각은 **선언된** 환경 신호다(계정 한도). 5xx 연속은 Model 의 문턱이 있을 때만 고장 | `rate_limit_state`(계정 실체) · `runtime_reliability` | 오류 관측 id | `provider_selection`: SWITCH · WAIT | 허용 provider 제약 · 데이터 거주 | SWITCH_PROVIDER · WAIT · STOP | 다음 호출 성공 관측 |
| C4 도구 | 실패 · 시간 초과 · 중단 · 바깥 차단(EGRESS_BLOCKED) | `is_error` · `timed_out`(구조화 칸 우선) · `interrupted` · 구조화된 오류 종류 | 구조화된 원인(EGRESS_BLOCKED · HTTP 코드)은 환경. 원인 없는 실패는 UNKNOWN 원인 | `tool_execution_health` · `execution_interruption` | 도구 호출 id | `execution_control`: RETRY · ESCALATE | retry 상한 · 되돌릴 수 없는 도구 허가 | RETRY · ESCALATE · STOP | 같은 겨냥의 다음 결과 성공 (RECOVERED_FAILURES) |
| C5 상태 엔진 · 규칙 | 규칙 오류 · 비결정 · 시계 어긋남 | 스냅숏 비교 · `FUTURE_OBSERVATION` · 규칙 예외 | 환경과 무관한 내부 고장 | `state_engine.integrity` (새, OQ-15) | 결정성 시험 · 이슈 코드 | — | 해당 상태 INVALID → DC 강등 | HOLD | 재생 결과가 기록과 같음 |
| C6 Model Registry | 판본 어긋남(DC ↔ MS 신호 이름이 실제로 어긋났다) | 계약 시험 실패 · 모르는 신호(unbound) 급증 | 내부 고장 | `contract.conformance` (시퀀싱 쪽 판정) | 계약 시험 결과 | 고리 밖 — 개발 절차 | 판본이 맞지 않는 소스는 DC 가 거절 | — | 계약 시험 통과 |
| C7 DC 빌더 | 빌드 예외 · 목적 없음 · '지금' 없음 | 예외 | 내부 | DC 없음 | 원장의 빌드 실패 기록 | 목적의 안전 기본 결정 (OQ-03) | Guard 가 DC 없는 의도를 거부 | 안전 기본 · ESCALATE | 다음 빌드 성공 |
| C8 정책 실행기 (LLM) | 못 읽는 출력 · 지어낸 대상 · 되풀이 · 형식 신뢰도 하락 | `proposal_invalid` · `arbiter_denies` · `user_correction` | 한 번은 표본 잡음이다. **표본 3 · 사건 2 이상**일 때만 상태를 뒤집는다(MS usage-model-2, 측정으로 정함) | `answer_reliability` · `correction_rate` | 자기 관측 id | CR: 품질 우선(줄이지 않는다) | Guard 는 LLM 의 말에 영향받지 않는다 | 고정 정책 · ESCALATE | 창 안 사건이 문턱 밑으로 |
| C9 Validate · Arbitrate | 규칙 예외 | 예외 | 내부 | `guard.health` | 예외 기록 | — | 예외면 DENY | — | — |
| C10 Guard | 예외 · 느림 · shadow 에 머묾 | 예외 · 지연 · 모드 | 내부 | `guard.mode` · `guard.health` | — | — | enforce 에서 예외 = 거부 | 안전 동작만 | Guard 자기 시험 통과 |
| C11 실행기 | 명령 안 감 · 반만 실행 · 결과 없음 | 결과 관측 없음 · 시간 창 만료 | 사후조건 창 안에 결과가 없으면 고장 후보 | `action_state` (PENDING · VERIFIED · NOT_VERIFIED · UNKNOWN) | command id · 결과 관측 | `recovery` 목적 | 같은 명령 되풀이 금지(A8 계열) | RETRY(상한) · ESCALATE | Verify |
| C12 Runtime · 시계 | 시계 역행 · 일정 밀림 | 단조 시계 비교 · 판 지연 | 내부 | `runtime.clock_integrity` | — | — | 신선도 판정 불가 → 쓸 수 없음 | HOLD | — |
| C13 사람 피드백 채널 | 피드백 없음 | 응답 없음 | 사람을 기다리는 것은 고장이 아니다(조사: 5.5 시간 공백 = AWAITING_INPUT) | `liveness = AWAITING_INPUT` | — | — | — | — | — |

## 6. 실패 흐름 — 승인 시험의 "Safety" 물음

### 6.1 센서가 고장 나면

```
수집기 멈춤 → 새 Observation 없음 → 그 실체의 상태들은 값을 지킨 채 TTL 이 지나면 STALE (지우지 않는다)
            → L4: collector.liveness = ENDED_WITHOUT_RESULT 또는 UNKNOWN. observes 간선으로 영향받는 실체를 묶는다(공통 원인)
            → L5: 필수 상태가 STALE → complete=False, missing_required 에 적힌다
            → L6: usable 값이 없다 → 목적의 기본 결정(바꾸지 않는다)
            → L9: 그 상태를 사전조건으로 쓰는 행동은 거부. 안전 동작(HOLD · ESCALATE)은 허용
```

### 6.2 상태가 낡으면

STALE 은 **어느 단계에서도 VALID 로 되돌아가지 않는다**(DC I3). Policy 는 None 을 받는다. 정책이 낡은 값을 쓰려면 목적 명세가 `allow_stale` 을
**명시**해야 한다(Sensor DC 의 규약). Guard 는 배차 직전 **지금** 상태로 신선도를 다시 본다(MS A5 · A6 의 일).

### 6.3 정책과 안전이 다르면

Guard 가 이긴다. 거부는 (a) 원장의 Guard 절, (b) 정책 실행기에 대한 자기 관측(`guard_denies`)으로 남는다. 다음 결정은 그것을 **관측으로**
본다. 정책이 Guard 를 넘는 길(강제 · 재정의 · 프롬프트 지시)은 없다. MS 는 이미 지킨다: 프롬프트는 중재자를 import 조차 하지 않는다.

### 6.4 고장이 여럿이면

1. 고장마다 자기 실체의 건강 상태가 따로 선다(도구마다 따로 서는 지금의 `tool_execution_health` 처럼).
2. L4 는 `observes` · `runs_on` · `uses` 로 **공통 원인**을 먼저 찾는다. 수집기 하나가 죽어 상태 다섯이 UNKNOWN 이면 고장 다섯이 아니라 하나다.
3. Guard 는 모든 활성 제약의 **논리곱**을 본다. 가장 엄한 것이 이긴다. 제약끼리는 서로 풀어 주지 못한다.
4. 안전 동작이 여럿 요구되면 Model 의 안전 동작 순서(예: STOP > HOLD > ESCALATE)로 하나를 고른다 — 순서는 OQ-17.
5. 복구는 하나씩 검증한다. 하나의 복구 확인이 다른 고장의 확인을 대신하지 않는다.

### 6.5 유효한 DC 가 없으면

| 경우 | 지금 | 기준선 |
|---|---|---|
| 빌드 실패(모르는 목적 · '지금' 없음 · 예외) | DC 저장소: 예외. Sensor DC: `INVALID` | 결정 없음 → 목적의 **안전 기본 결정** + 원장에 빌드 실패 |
| `complete=False` | DC: 정책에 넘긴다. Sensor DC: `DEGRADED` | 정책은 usable 값만 쓴다. 필수가 빠진 결정은 Guard 가 위험 등급 행동을 거부 |
| 안전 기본 결정이 무엇인가 | MS: 모름 = 고정 정책. Sensor 참조 정책: 완료 상태를 모르면 ESCALATE | **미결 — OQ-03** |

## 7. 행동 기록은 누가 내나 (Sensor 세션의 S6 물음에 대한 답)

| 기록 | 내는 쪽 | 꼴 | 지금 |
|---|---|---|---|
| "무엇을 하기로 했나" (의도 · 선택 · 허가) | L6–L9 가 Decision Ledger 에 | DecisionRecord | MS Arbiter ledger · RunRecord.policy (BV-04) |
| "무엇을 실행했나" (명령) | L10 실행기가 Ledger 에 | ActionCommand | MS 도구 실행 |
| "무엇이 일어났나" (결과) | L10 실행기가 **Observation 으로** | Telemetry 레코드 `action_outcome` (새 종류, 제안) | MS 도구 handler 가 텔레메트리를 돌려준다 |
| "효과가 났나" | L11 | `action_state` State | 없음 |
| 런타임 **자신의** 행동(압축 · 백그라운드 이동 · 권한 거부) | 런타임이 이미 원천에 남긴다 → **Sensor 수집기가 Observation 으로** | 기존 v3 꼴의 확장 | Sensor 조사: `compact_boundary` · 백그라운드 이동이 원천에 있는데 안 거둔다 (D4) |

**Sensor 는 우리 정책의 행동 기록을 내지 않는다.** 실행기가 없는 지금은 그 기록이 없다. 지어내지 않는다. Sensor 가 지금 할 수 있는 것은 런타임
자신의 행동을 거두는 일뿐이다. 우리 정책의 `action_state` 는 Action 실행기(OQ-05)가 선 뒤에 짓는다.
