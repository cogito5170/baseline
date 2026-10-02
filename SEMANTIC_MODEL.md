# SEMANTIC MODEL — 낱말의 뜻을 하나로 (baseline-1.0, 승인 2026-10-02)

이 문서는 **뜻**만 정한다. 칸 · 크기 · 인코딩은 [`SCHEMA_PROPOSAL.md`](SCHEMA_PROPOSAL.md), 흐름은 [`DATA_FLOW.md`](DATA_FLOW.md) 에 있다.
각 정의는 같은 틀을 따른다: **정의 · 답하는 물음 · 담는 것 · 담지 않는 것 · 지금 코드 · 충돌 정리.**

## 1. 읽는 법 — 한 줄 정의

| 낱말 | 한 줄 | 층 |
|---|---|---|
| Observation | 원천이 직접 보고한 사실 하나(값이거나 "보고된 null") | OBSERVE |
| Telemetry | Observation 을 나르고 보고하는 **전송 꼴** | OBSERVE (전송) |
| Measurement | Observation 에서 결정론적 산술로 얻은 양 | MEASURE |
| State | 실체에 대해 지금 참이라고 믿는 의미 값 + 유효성 · 신선도 · 근거 | ESTIMATE · ASSESS |
| Assessment | 고장 · 건강을 탐지 · 격리 · 진단하는 기능. 결과는 State 다 | ASSESS |
| Model | 실체 · 상태 · 규칙 · 행동이 무엇을 뜻하는지의 판본 있는 정의 | M |
| Relationship | 유형 있는 간선 | R |
| Evidence | 값을 받치는 것에 대한 **참조** | E |
| Decision Context | 한 결정에 필요한 최소 충분 정보의 고정 스냅숏 | CONTEXTUALIZE |
| Policy | DecisionContext → Decision 인 판본 있는 함수 | DECIDE |
| Decision | Policy 의 출력: ActionIntent 후보와 까닭 | DECIDE |
| Arbitration | 후보 여럿 사이의 명시적 선택 | ARBITRATE |
| Safety (Guard) | 고른 것을 지금 실행해도 되는지의 허가. 닫는 쪽으로만 | GUARD |
| Action | 실행할 수 있는 명령(또는 명령 명세) | EXECUTE |
| Verification | 행동의 의도한 효과가 관측되었는지의 판정 | VERIFY |
| Runtime | 고리를 돌리는 기반 시설 | — |
| Opinion | LLM · 사람의 해석 제안. 권위가 없다 | (밖) |

---

## 2. 정의

### 2.1 Observation (관측)

- **정의.** 원천(런타임 · provider · 도구 · 사람 · 외부 평가)이 **직접** 보고하거나, 수집기가 직접 본 사실 하나.
- **답하는 물음.** 무엇이 보였나.
- **담는 것.** 실체 id · 정준 필드 이름 · 값 · `reported_null`(원천이 그 칸을 null 로 보고했다) · 관측 시각 · 시간 기준 · 원천 · 수집기 판본.
- **담지 않는 것.** 해석(HIGH · 건강) · 문턱 · 판정 · 정책 제안 · 운영자 설정.
- **보지 못한 것은 Observation 이 아니다.** 보지 못한 칸은 `unobserved` 로 따로 적는다(Sensor v2 규약). 보지 못한 것은 0 도, 거짓도, 정상도 아니다.
- **자기 관측도 Observation 이다.** Arbiter 의 거부 수 · 못 읽은 제안 수 · Guard 결과 · 사람의 고침은 **자율 시스템 자기 부품에 대한 관측**이다.
  실체는 그 부품이다(`policy_executor:*`, `guard:*`).
- **지금 코드.** Sensor `state/model.Observation` (가장 가깝다) · MS `Telemetry`(신호 하나).
- **충돌 정리.** MS 의 `config.*` 신호는 Observation 이 아니다 → Model(운영자 가정) 또는 Constraint (BD-13).

### 2.2 Telemetry (텔레메트리)

- **정의.** Observation 과 런타임 측정을 **나르고 보고하는 꼴**: 레코드 · 묶음 · 봉투 · 꼴 판본 · 레코드 id(멱등).
- **답하는 물음.** 무엇이 관측 · 보고되었나(전송의 관점에서).
- **담지 않는 것.** 정책 결정의 내용. 텔레메트리는 결정 기록을 `decision_ref`(id)로 **가리킬** 수만 있다 (BV-04 를 푸는 규칙).
- **Observation 과의 관계.** Telemetry 는 Observation 을 싣는다. 뜻의 단위는 Observation 이고, Telemetry 는 그것의 운반 형식이다.
  같은 Observation 은 형식(JSONL · stream-json · OTel)이 달라도 같은 Observation 이다.
- **지금 코드.** Sensor `schema/telemetry.schema.json`(v3) · MS `RunRecord`(ms-run-telemetry-2) · MS `Telemetry`.

### 2.3 State (상태)

- **정의.** 실체 하나 · 상태 이름 하나에 대해, **판본 있는 규칙**이 Measurement(와 다른 State)에서 지은, 지금 참이라고 믿는 의미 값.
  늘 유효성 · 신선도 · 근거 종류 · 근거 참조 · 규칙 id@판본 · 시각(observed_at · since)과 함께 산다.
- **답하는 물음.** 시스템(또는 실체)이 지금 무엇이라고 믿어지나.
- **추정 · 파생 · 영속 · 일시는 칸으로 드러낸다.**
  - 추정이냐 파생이냐 → `basis` (OBSERVED · DEFINITIONAL · RUNTIME_DECLARED · PROVIDER_DECLARED · OPERATOR_ASSUMED · EXTERNAL_LABEL · VALIDATED_EXPERIMENT · ESTIMATE).
  - 영속이냐 일시냐 → 저장소 · 범위(BASELINE §4). 끝난 일의 사실은 `permanent`.
- **담지 않는 것.** 원 측정값(그것은 OBSERVE · MEASURE 에 남고 Evidence 로 가리킨다) · 행동 · 정책의 선호 · LLM 의 의견.
- **상태 이름마다 소유 규칙은 하나다.** 두 규칙이 같은 (실체 유형, 이름)을 쓰지 않는다(Sensor Registry 가 이미 지킨다).
- **건강 · 고장 상태도 State 다.** 소유 규칙이 ASSESS 에 있을 뿐이다 (BD-04).
- **지금 코드.** Sensor `state/model.State` (기준) · MS `graph.Value`(유효성 칸 없음, 없음 = 모름).

### 2.4 Model (모형)

- **정의.** 실체 · 상태가 무엇을 뜻하는지의 형식적 정의. **판본이 있고 실행 중에는 읽기만 한다.**
- **담는 것.** 실체 유형 · 속성 · 값 집합 · 제약 · 유효성 규칙 · 기대 동작(성능 기대값) · 허용 관계 유형 · 신호 바인딩 · 파생 규칙 · TTL ·
  운영자 가정(예산 · SLO · 띠) · 목적(purpose) 명세 · 행동 명세(필요 능력 · 사전/사후조건 · 위험) · 고장 모드(무엇이 무엇에 영향을 주나) ·
  안전 제약 · 안전 동작 순서.
- **담지 않는 것.** 현재 값 · 실행.
- **충돌 정리.** "Model" 은 이 뜻뿐이다. Sensor `PerformanceModel` 은 Model 의 **기대 동작** 부분이다. `OutcomeModel` 은 ASSESS 의
  **융합 규칙**(Model 이 정의하고 ASSESS 가 돌린다)이다. LLM 의 "모형" 은 `provider_model` 로 부른다 (DUP-07).

### 2.5 Relationship (관계)

- **정의.** 실체 · 상태 · 사건 · 능력 · 모형 사이의 유형 있는 의미 연결. 꼴: 주어 · 술어 · 목적어 · 유효 구간 · (근거 · 신뢰도).
- **행동이 아니다.** "도구가 서버를 재부팅한다" 는 관계가 아니라 Action 이다.
- **세 부류를 섞지 않는다** (§4):
  1. **실체 관계**(실행 중 사실) — Relationship Store 에 산다.
  2. **유형 관계**(모형 지식: 고장 모드 · 행동의 필요 능력 · 충돌) — Model 에 산다.
  3. **인식 관계**(파생 · 근거) — Evidence 사슬에 산다. 세계의 간선이 아니다.

### 2.6 Evidence (근거)

- **정의.** 어떤 State · 추론을 받치는 정보에 대한 **참조**. 값을 복사하지 않는다.
- **꼴.** `ref`(Observation · Measurement · State id) · 층 · 원천 · 관측 시각 · 신선도 · 근거 종류 · 규칙/수집기 판본 · (신뢰도).
- **복원 규칙.** 쓸 수 있는(usable) State 는 모두 Evidence 를 거쳐 Observation 까지 되짚혀야 한다 (DC 불변식 I5).
- **충돌 정리.** MS `role: evidence`(원 측정 창)는 Evidence 가 아니다. **Measurement 창**이다 (BD-06).

### 2.7 Decision Context (결정 문맥)

- **정의.** 사용할 수 있는 시스템 지식 가운데, **특정 결정 하나**를 위해 고른 최소 충분 정보의 고정 스냅숏.
- **State 데이터베이스 전체가 아니다.** 목적이 부른 것만 담는다.
- **담을 수 있는 것.** 목적(=목표의 이름) · 관련 상태(값 · 유효성) · 관련 관계 · 근거 참조 · 신뢰도 · 신선도 · 제약 · 불확실성
  (UNKNOWN · STALE · INVALID 목록) · 가능 행동(구조적 능력으로 본 실행 가능성).
- **해서는 안 되는 것.** 숨은 정책 엔진 되기(목적함수 · 가중치 · 선호 · 고른 행동을 담기) · 행동 실행 · 상태 계산 · LLM 프롬프트 짓기 ·
  원 텔레메트리 싣기.
- **가능 행동은 사실로만 거른다.** 능력이 있으면 가능이다. 상태로 거르지 않는다(그것은 정책 · Guard 의 일). DC 저장소가 이미 시험으로 지킨다.
- **충돌 정리.** MS 의 "Context Decision(CD)" 은 DC 가 아니다. CR 이 낸 **LLM 맥락**이다 → `LLMContext` 로 부른다. CR 은 DC 를 받아 그리는 어댑터다 (BD-21).

### 2.8 Policy (정책)

- **정의.** `Policy: DecisionContext → Decision`. 판본이 있고, 같은 DC + 같은 판본이면 같은 결정을 다시 계산할 수 있다(재현).
  LLM 이 실행기일 때는 그 출력이 표본이라 재현은 "기록된 출력 + 판본" 으로 한다.
- **하지 않는 것.** 원 텔레메트리 수집 · 센서 전송 정의 · 전역 상태를 몰래 바꾸기 · 허가 · 실행.
- **실행기.** 규칙 함수 · LLM · 사람 모두 Policy 의 실행기가 될 수 있다. 실행기가 LLM 이면 DC 를 LLM 입력으로 그리는 어댑터(CR)가 붙는다.
- **목적함수는 Policy 가 갖는다.** DC 에는 목적함수 칸이 없다.

### 2.9 Decision (결정)

- **정의.** Policy 의 출력: ActionIntent 후보 하나 이상 + 까닭 + 사용한 DC 키 + 정책 판본 + DC id.
- **ActionIntent.** 누가 냈든(규칙 · LLM · 사람) 같은 꼴의 **실행 요청 제안**이다. 실행이 아니다.
- **결정이 아닌 것.** Validate · Arbitrate · Guard 의 결과(각각 ValidationResult · ArbitrationResult · GuardResult), ASSESS 의 수락 평가.

### 2.10 Arbitration (중재)

- **정의.** 정책 여럿 · 목표 여럿 · 우선순위 · 자원 제약 사이에서 후보 의도 가운데 **무엇을** 고르는 명시적 단계.
- **허가가 아니다** (그것은 Guard). Policy 안에 숨기지 않는다(정책 안의 선호 순서는 그 정책의 일이고, 정책 **사이**의 선택은 중재다).
- **규칙은 Model 에 판본으로.** 우선순위 · 충돌(`conflicts_with`)은 Model 에 적는다.

### 2.11 Safety / FDIR / Runtime Assurance

- **정의.** 필요할 때 명목 결정을 **제한하거나 뒤엎는** 장치. 명목 최적화와 구별된다.
- **방아쇠 예.** 제약 위반 · 고장 탐지 · 위험한 행동 · 자원 소진 · 관측 가능성 상실 · 결정의 근거가 낡음.
- **성질.** (a) 닫는 쪽으로만 개입한다. (b) Policy 와 독립된 부품이다. (c) 지금 상태를 직접 읽는다. (d) 터지면 거부한다(enforce).
  (e) 안전 동작(STOP · HOLD · ESCALATE …)을 스스로 낼 수 있다.
- **FDIR 의 자리.** 탐지 · 격리 = ASSESS · 복구 결정 = DECIDE · 복구의 제약 = GUARD · 복구 확인 = VERIFY.

### 2.12 Action (행동)

- **정의.** 실행할 수 있는 명령, 또는 명령 명세. 실행 경계에 속한다.
- **세 꼴.** `ActionSpec`(Model: 이름 · 필요 능력 · 사전/사후조건 · 위험) → `ActionIntent`(DECIDE) → `ActionCommand`(GUARD 가 허가한 것, 실행 id) →
  `ActionOutcome`(EXECUTE, Observation 으로).
- **박아 넣지 않는다.** 텔레메트리 · 상태 · 모형 · 관계 · 근거에 행동을 넣지 않는다. DC 는 **가능성**만 말한다.

### 2.13 Runtime (런타임)

- **정의.** 생애 · 일정 · 실행 · 상태 접근 · 통신 · 정책 호출 · 안전 감시 구동 · 행동 배차를 맡는 기반 시설.
- **시계를 읽는 유일한 곳.** 다른 층은 '지금' 을 인자로 받는다(Sensor 엔진 · DC 빌더가 이미 그렇다).
- **뜻을 다시 정하지 않는다.** 상태 계산 · 성공 판정 · 정책 규칙을 안에 두지 않는다 (BV-10).

### 2.14 Measurement (측정 · 파생 값)

- **정의.** Observation 에서 결정론적 산술로 얻은 양: 합 · 비 · 창 집계 · 백분위 · 차분.
- **뜻이 없다.** `context_utilization = 0.761` 은 Measurement 다. `context_pressure = BELOW_COMPACTION_THRESHOLD` 는 State 다.
- **입력이 모자라면 UNKNOWN.** 옛 값으로 메우지 않는다.

### 2.15 Assessment (평가 — 탐지 · 격리 · 진단)

- **정의.** 기대(Model)와 관측 · 상태를 견주어 고장 · 건강을 판정하는 기능. 결과는 State Store 의 건강 · 고장 상태다.
- **결정이 아니다.** ACCEPT · RETRY · DEGRADE 같은 행동 이름을 내지 않는다.
- **지금 코드.** Sensor Reading(OK · SUSPECT · FAULT · UNKNOWN) · 잔차 · Q, MS 의 `answer_reliability` · `correction_rate`
  (= 정책 실행기 LLM 의 건강).

### 2.16 Verification (검증)

- **정의.** 실행된 행동의 사후조건(Model)이 그 뒤의 관측 · 상태에서 성립하는지의 판정. 결과는 행동 실체의 State(`action_state`)다.
- **수락 판정과 다르다.** 과업 결과의 외부 라벨(`quality_state`)은 Observation(외부 평가) → State 이다.

### 2.17 Constraint · Capability · Purpose

- **Constraint.** 넘으면 안 되는 선(이름 · 연산 · 값 · 누가 걸었나). 목적함수가 아니다. DC 는 싣고, **평가는 Guard 가** 한다.
- **Capability.** 구조적 능력(다른 provider 가 설정됐나 · 사람이 붙어 있나). 가능 행동을 정하는 유일한 입력이다.
- **Purpose.** "이 결정에 무엇이 필요한가" 의 판본 있는 명세(Model). 정책이 아니다.

### 2.18 Opinion (의견)

- LLM · 사람이 상태에 대해 낸 해석. 보관만 한다. State · DC 에 들어가지 않는다(Sensor `propose()`, DC I7 이 이미 지킨다).

---

## 3. 공용 어휘 (계약 후보 — Telemetry/baseline 이 갖는다)

| 어휘 | 값 | 출처 · 비고 |
|---|---|---|
| Status (유효성) | OBSERVED · DERIVED · INFERRED · UNKNOWN · STALE · INVALID · NOT_APPLICABLE | Sensor 와 DC 가 같다. MS 는 없음(None) → 어댑터가 번역 |
| usable | {OBSERVED, DERIVED, INFERRED} 이고 신선도가 STALE 아님 | |
| Freshness | FRESH · STALE · UNTIMED · PERMANENT | 같음 |
| Basis | OBSERVED · DEFINITIONAL · RUNTIME_DECLARED · PROVIDER_DECLARED · OPERATOR_ASSUMED · EXTERNAL_LABEL · VALIDATED_EXPERIMENT · ESTIMATE | Sensor 8 개를 정본으로. DC 는 5 개뿐이다(DUP-13) |
| Lifecycle | CREATE · UPDATE · REFRESH · STALE · INVALIDATE · RECOVER | Sensor |
| Reading (ASSESS 판독) | OK · SUSPECT · FAULT · UNKNOWN | Sensor. ASSESS 안에서만 쓴다 |
| Guard 결과 | ALLOW · DENY · SAFE_ACTION (+ 모드 shadow/enforce) | MS ALLOW/DENY/NOOP 를 넓힌 제안 |
| 실체 id | `<유형>:<범위>:<지역 id>` — 지금 Sensor `agent:<run>` · `tool:<run>:<이름>`, MS `session:<이름>` · `srv1`. 요금 한도는 `account:<id>` | BD-32 |
| 시각 | ms + `time_base`(unix_ms · monotonic_ms). MS 는 초 → 경계에서 ms 로 | BD-33 |
| 관측 출처 종류 (L0) | reported · declared · measured · translated · ref | Telemetry 저장소. 관측 수준이다. State 의 Basis 로 옮기는 규칙은 BD-44 |

---

## 4. 관계 모형 — 무엇을 받아들이고 무엇을 버리나

조사한 술어 12 개를 하나씩 판정했다. 받아들인 것만 계약에 들어간다.

| 술어 | 판정 | 부류 | 까닭 | 지금 코드 |
|---|---|---|---|---|
| `observes` | **채택** | 실체 | 수집기 · 센서 → 실체. 수집기가 죽으면 무엇이 함께 UNKNOWN 이 되는지(공통 원인 격리)에 꼭 필요하다 | 없음 (Observation.source 에 암시만) |
| `measures` | 버림 | — | `observes` + Observation 의 `field` 로 충분하다. 따로 두면 중복이다 | — |
| `derived_from` | **채택** | 인식 | Measurement → Observation, State → Measurement. 근거 사슬의 뼈대 | Sensor `Metric.inputs` · `explain()` |
| `evidenced_by` | 버림 (`derived_from` 에 합침) | — | State 수준의 `derived_from` 과 같은 것을 가리킨다 | Sensor `State.evidence` |
| `depends_on` | **채택 (유형 수준만)** | 모형 | 상태 정의 → 입력 정의. 실체 수준에서는 `derived_from` 과 같아 쓰지 않는다 | Sensor `Registry.graph()` · MS `Derivation.inputs` |
| `affects` | **채택** | 모형 | 고장 모드 → 능력/실체. 속성 `effect ∈ {degrades, disables}`. 격리와 Guard 에 필요하다 | 없음 (GAP-12) |
| `degrades` | 버림 (`affects{effect: degrades}`) | — | `affects` 의 한 경우다 | — |
| `constrains` | 버림 (Constraint 객체의 `target` 칸으로) | — | 제약은 이미 객체다. 간선으로 또 두면 둘이 어긋난다 | DC `Constraint` |
| `requires` | **채택** | 모형 | 행동 → 능력. 가능 행동을 정한다 | DC `ActionSpec.requires` |
| `enables` | 버림 (`requires` 의 역) | — | 역관계를 따로 저장하지 않는다 | — |
| `conflicts_with` | **채택 (유형 수준)** | 모형 | 행동 ↔ 행동, 목표 ↔ 목표. 중재(ARBITRATE)의 입력 | 없음 |
| `supports` | **보류** | 인식 | 근거 → 진단 가설. 진단 가설 객체가 생길 때 다시 본다 | 없음 (BD-34) |
| 도메인 간선 `contains` · `uses` · `executed_by` · `runs_on` | **채택** | 실체 | 이미 쓰인다. 질의 · 선택 · 격리에 쓰인다 | MS `contains` · `uses`, Sensor `uses` · `executed_by` · `runs_on` |

모든 관계는 `subject · predicate · object · valid_from · valid_to(또는 last_seen) · basis · evidence_refs` 를 가진다. 유형 관계는 판본 있는
Model 에 있으므로 유효 구간 대신 Model 판본을 가진다.

---

## 5. 원 값과 파생 — 분류표

분류: **RAW**(원 관측) · **MEAS**(측정 · 파생 값) · **STATE** · **MODEL** · **REL** · **EVID** · **DC** · **DEC** · **ACT**.
같은 개념이 여러 층에 따로 나타나면 안 된다. 나타나는 곳은 "사는 곳" 하나이고, 나머지는 **참조**다.

| 자료 | 분류 | 사는 곳 | 위층에서는 | 비고 |
|---|---|---|---|---|
| `input_tokens` · `cache_read_input_tokens` · `cache_creation_input_tokens` · `output_tokens` · `thinking_tokens` | RAW | OBSERVE (Telemetry) | Evidence id 로만 | 공급자 차이는 OBSERVE 정규화에서 맞춘다 |
| `context_window` · `autocompact_threshold` | RAW (런타임 선언) | OBSERVE | — | |
| `context_tokens` = input + cache_read + cache_creation | MEAS | MEASURE | Evidence id | MS 의 `context_tokens` 는 **추정**(글자 비율) — basis=ESTIMATE |
| `context_utilization` · `compaction_margin` · `context_growth` | MEAS | MEASURE | Evidence id | |
| `context_pressure` (Sensor, 런타임 문턱) | STATE | ESTIMATE | DC 키 `agent.context_pressure` | |
| `context_budget_pressure` (MS 의 `context_pressure`, 운영자 띠) | STATE | ESTIMATE | DC 키 `session.context_budget_pressure` | 이름을 바꿔 가른다 (DUP-11) |
| `token_budget` · `context_budget` · `latency_budget_ms` · SLO · 띠 · TTL | MODEL (운영자 가정) 또는 DC Constraint | M / 요청 | — | 지금은 RAW 처럼 들어온다 (BV-03) |
| `is_error` · `timed_out` · `interrupted` (도구) | RAW | OBSERVE | — | |
| `tool_failure_rate` · `tool_retries` | MEAS | MEASURE | — | |
| `execution_health` · `tool_execution_health` · `execution_interruption` | STATE (건강 성격) | ESTIMATE/ASSESS | DC | 소유 규칙을 ASSESS 로 옮길지는 BD-35 |
| `rate_limit_utilization` · `rate_limit_status` | RAW | OBSERVE (계정 실체) | — | |
| `rate_limit_state` | STATE | ESTIMATE (계정 실체 — BD-32) | DC | |
| `cost_usd` (런타임 보고) | RAW | OBSERVE | — | |
| `cost_estimate` (토큰 × 단가표) | MEAS (basis PROVIDER_DECLARED) | MEASURE | — | |
| `resource_state` · `resource_pressure` | STATE | ESTIMATE | DC | |
| `arbiter_denies` · `proposal_invalid` · `retries` | RAW (자기 관측) | OBSERVE (실체: 정책 실행기) | — | 판정의 **결과**를 세는 관측이다. 판정 내용은 Ledger |
| `answer_reliability` · `correction_rate` | STATE (정책 실행기의 건강) | ASSESS | DC | |
| `user_correction` | RAW (사람) | OBSERVE | — | |
| Reading (OK · SUSPECT · FAULT · UNKNOWN) | STATE (ASSESS 판독) | ASSESS | Evidence | |
| `Q` (융합 점수) | STATE (ASSESS, 보정 전에는 순서 점수 — 신뢰도 종류를 붙인다) | ASSESS | DC (필요한 목적만) | BD-36 |
| `quality_state` (외부 라벨) | STATE (basis EXTERNAL_LABEL) | ESTIMATE | DC | 라벨 자체는 RAW |
| 상태 → 지표 → 관측 사슬 | EVID | Evidence 사슬 | DC 에는 id 만 | Sensor DC 는 사슬 전체를 복사해 문맥마다 6–22 KB 를 싣는다 (SCHEMA §4.4) |
| `uses` · `executed_by` · `runs_on` · `contains` | REL | Relationship Store | DC (질의형 선택에서) | |
| DecisionContext | DC | DC Store | DecisionRecord 에 id | |
| Policy 의 행동 이름 · 까닭 | DEC | Decision Ledger | 텔레메트리에는 id 만 | MS RunRecord 는 내용을 싣는다 (BV-04) |
| Verifier 의 ACCEPT · RETRY | DEC (목적 acceptance) | Ledger | — | BV-01 |
| Verifier 의 `token_budget` · `retry_limit` · `route` 제안 | **어느 층도 아님** — 거버넌스(모형 변경 제안) | 고리 밖 | — | Model 을 바꾸려면 판본 절차를 거친다 |
| 도구 호출(이름 · 인자) | ACT | EXECUTE | Ledger 에 command id | |
| 도구 결과 | RAW | OBSERVE | — | "됐다" 고 해도 관측이다(MS 원칙 1) |

### 5.1 예: 토큰에서 결정까지 — 각 층에는 하나만 산다

```
RAW     input_tokens=10 · cache_read=130,000 · cache_write=6,990 · context_window=180,000 · autocompact_threshold=144,000   (OBSERVE)
          │ derived_from
MEAS    context_tokens=137,000 · context_utilization=0.761 · compaction_margin=7,000                                       (MEASURE)
          │ derived_from   (규칙 context-pressure-v1, basis RUNTIME_DECLARED)
STATE   agent.context_pressure = BELOW_COMPACTION_THRESHOLD   status INFERRED · FRESH                                     (ESTIMATE)
          │ 목적 context_policy 가 부른다
DC      {"agent.context_pressure": ["BELOW_COMPACTION_THRESHOLD", "INFERRED"]}  + evidence_refs (id 만)                    (CONTEXTUALIZE)
          │
DEC     KEEP (까닭: 압축 문턱 아래)                                                                                     (DECIDE)
```

토큰 수 `137,000` 은 OBSERVE · MEASURE 에만 있다. DC · 결정에는 **값으로 올라가지 않는다.** (지금 DC 의 `reason` 문자열은 이 수를 싣는다 →
SCHEMA §4.2 에서 `reason` 을 provenance 로 내린다.)
