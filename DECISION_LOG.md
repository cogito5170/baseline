# DECISION LOG (baseline-1.0 — 승인 2026-10-02)

상태 표시: **ADOPTED** = 결정됨. 사용자는 2026-10-02 에 baseline-1.0 을 승인하며 BD-01–BD-20 과 미결 질문의 권고안(BD-21–BD-42)을 함께 채택했다.
**OPEN** = 아직 미결(OPEN_QUESTIONS.md). **SUPERSEDES** = 앞선 사용자 결정을 이 결정이 대신한다.
틀: 결정 · 까닭 · 검토한 대안 · 버린 대안 · 근거 · 결과.

---

### BD-01 정규 층 순서 OBSERVE–VERIFY — ADOPTED (사용자 승인, 2026-10-02 · baseline-1.0)
- **결정.** Observe → Measure → Estimate → Assess → Contextualize → Decide → Validate → Arbitrate → Guard → Execute → Verify. 되먹임은 Observation 으로만 한다.
- **까닭.** 지금 세 저장소의 그림은 같은 방향이다. 다만 진단 · 결정(Sensor Verifier), 판정 · 허가(MS Arbiter)를 합쳐 두었다.
- **대안.** (a) MS 의 세 층(Telemetry · State · Policy). (b) Sensor 파이프라인(센서 → Q → 판정기). (c) 사용자가 준 고리(OBSERVE … VERIFY).
- **버림.** (a) 진단 · 안전이 들어설 자리가 없다. (b) BV-01. (c)는 버리지 않았다. ESTIMATE 를 Measure 와 Estimate 로 가른 것만 다르다(BD-03).
- **근거.** BASELINE §1 · §6. NASA 의 "진단 ≠ 결정" 원칙(원문 재확인 못 함, OQ-20).
- **결과.** Guard · Action · Assess 의 자리가 생긴다. 그 자리는 지금 비어 있다(GAP-01–05).

### BD-02 Observation 은 뜻의 단위이고, Telemetry 는 운반 꼴이다 — ADOPTED (사용자 승인, 2026-10-02 · baseline-1.0)
- **까닭.** MS 의 RunRecord 와 Sensor v3 는 같은 관측을 다른 꼴로 나른다. 꼴을 뜻으로 삼으면 꼴이 바뀔 때마다 뜻이 흔들린다.
- **대안.** Telemetry = State 의 입력 꼴 하나. **버림** — 두 저장소의 꼴이 실제로 다르다(DUP-02).
- **결과.** 정준 Observation 이름 집합이 필요하다(SCHEMA §5, OQ-08).

### BD-03 Measurement 를 따로 층으로 둔다 — ADOPTED (사용자 승인, 2026-10-02 · baseline-1.0)
- **까닭.** Sensor 는 상태 규칙의 입력을 지표로만 제한하고 시험으로 지킨다. 원 관측이 상태 규칙에 바로 들어가면, 같은 산술이 규칙마다 되풀이된다.
- **근거.** `Sensor/llmsensor/state/registry.py` `check()` · `docs/STATE_MODEL.md` §2.
- **결과.** MS 의 evidence 창(집계)은 Measurement 다(BD-06).

### BD-04 Assess 는 Decide 와 다른 층이다. 건강 · 고장은 State 다 — ADOPTED (사용자 승인, 2026-10-02 · baseline-1.0)
- **까닭.** 진단과 결정은 다른 기능이다. 건강도 유효성 · 신선도 · 근거 · 생애가 필요하다. 그래서 같은 State 기계를 쓰고, 소유 규칙만 ASSESS 에 둔다.
- **대안.** (a) 건강 저장소를 따로 둔다. (b) 판정기처럼 합친다.
- **버림.** (a) 생애 · 신선도 기계가 둘이 된다. (b) BV-01.
- **결과.** Sensor `verifier.py` 를 셋으로 가른다: Q 융합 = ASSESS · ACCEPT/RETRY = DECIDE 의 `acceptance` 목적 · 설정 제안 = 고리 밖 (PC-06).

### BD-05 DC 저장소를 Decision Context 의 기준 구현으로 삼는다 — ADOPTED (사용자 승인, 2026-10-02 · baseline-1.0)
- **까닭.** 네 구현 가운데 불변식(I1–I7)이 가장 많고, 변이 15 가지로 시험을 확인했다. 시계를 읽지 않는다. 다른 저장소를 import 하지 않는다.
- **대안.** Sensor `decision/context`. 장점: `allow_stale` 명시 · ContextStore · explain. 단점: 근거 사슬을 문맥마다 복사한다(6–22 KB).
- **버림.** Sensor 의 것을 기준으로 삼는 안 · MS `snapshot()` 을 기준으로 삼는 안(신선도 · 근거 없음).
- **결과.** Sensor 의 장점(`allow_stale` · ContextStore)은 DC 로 옮길 후보다. Sensor 의 두 DC 는 걷어 낸다(PC-08). 목적 어휘 통일은 OQ-10.

### BD-06 Evidence 는 참조다. MS 의 "evidence" 는 Measurement 창으로 부른다 — ADOPTED (사용자 승인, 2026-10-02 · baseline-1.0)
- **근거.** DUP-01. MS `model.py` 의 `role: evidence` 는 원 측정을 창으로 모은 것이다. Sensor · DC 의 evidence 는 id 참조다.
- **결과.** 이름만 바뀐다. 동작은 같다(PC-04).

### BD-07 Guard 는 Policy 와 독립이다. 닫는 쪽으로만. 지금 상태를 읽는다 — ADOPTED (앞 절은 사용자 2026-10-02, 뒤 절은 baseline-1.0 승인)
- **ADOPTED (사용자, 2026-10-02, MS `docs/계획.md` §3).** Arbitrate = 선택 · Guard = 허가. `GUARD_MODE` shadow/enforce 는 모드만 바꾼다.
  불변식은 빼지 못한다. 훅이 터지면 shadow 는 기록하고 계속, enforce 는 명시적으로 거부한다.
- **ADOPTED (baseline-1.0 승인).** Guard 는 Policy · CR 을 import 하지 않는 **별도 부품**이다(저장소도 따로, BD-20). 안전 동작을 스스로 낼 수 있다.
  프롬프트의 도구 좁히기(BV-05)도 Guard 의 규칙으로 옮긴다.
- **까닭.** 런타임 보증의 독립성. 명목 정책과 고장 모드를 나누지 않는다.

### BD-08 DC 는 State Store 가 아니다. core 와 provenance 로 가른다 — ADOPTED (사용자 승인, 2026-10-02 · baseline-1.0)
- **근거.** SCHEMA §4.4: 정책이 읽는 것은 DC 의 ~10 %. `reason` 이 core 만큼 크다. 그 안에 원 수치가 새어 든다.
- **결과.** PC-07.

### BD-09 LLM 은 층이 아니라 Policy 의 실행기다 — ADOPTED (사용자 승인, 2026-10-02 · baseline-1.0)
- **까닭.** 결정론으로 충분한 곳에는 결정론을 둔다. MS `계획.md` 도 "LLM 을 빼도 구조가 남는다" 고 적었다.
- **결과.** LLM 출력은 ActionIntent 다(MS `Proposal` 을 일반화, 사용자 순서 ⑥ 과 같다).

### BD-10 문턱은 근거 종류가 선언된 것만 쓴다 — ADOPTED (Sensor 의 관행)
- 근거가 없으면 상태는 NOT_APPLICABLE 또는 UNKNOWN 이다. 문턱을 지어내지 않는다(`Sensor/llmsensor/state/config.py` 머리말).

### BD-11 캐시 규칙 — ADOPTED (사용자 승인, 2026-10-02 · baseline-1.0)
- 잃었을 때 행동이 바뀌면 캐시가 아니다. 캐시는 권위가 없다. provider 프롬프트 캐시(바이트)와 결정 재사용(뜻)은 다른 캐시다(MS `계획.md` §0 과 같다).

### BD-12 범위와 생애를 칸이 아니라 저장소로 드러낸다 — ADOPTED (사용자 승인, 2026-10-02 · baseline-1.0)
- BASELINE §4. 요금 한도는 **계정** 범위다(Sensor 조사).

### BD-13 운영자 설정은 관측이 아니다 — ADOPTED (사용자 승인, 2026-10-02 · baseline-1.0)
- **근거.** BV-03. 예산을 텔레메트리로 넣은 탓에 MS 파생 상태의 시각이 세션을 연 시각에 묶인다. DC 문서도 이것을 "알려진 한계" 로 적었다.
- **결과.** 예산 · SLO 는 Model(운영자 가정, 판본) 또는 요청 Constraint 다. **예산의 주인은 하나다**: 지금은 Sensor `cost_budget_usd` · MS `token_budget` · DC `max_cost_usd` 셋이 따로 있다 (OQ-21).

### BD-14 사건 구동, digest 로 다시 쓰기 — ADOPTED (사용자 승인, 2026-10-02 · baseline-1.0)
- DATA_FLOW §4.

### BD-15 결정의 내용은 원장에, 텔레메트리에는 `decision_ref` 만 — ADOPTED (사용자 승인, 2026-10-02 · baseline-1.0)
- BV-04. 재현(`ms.policy.replay`)은 원장을 읽는다.

### BD-16 자율 부품의 자기 관측도 Observation 이다 — ADOPTED (사용자 승인, 2026-10-02 · baseline-1.0)
- `arbiter_denies` · `proposal_invalid` · Guard 거부 · 사람의 고침. 실체는 그 부품이다. 판정의 내용이 아니라 **결과의 수**만 관측이다.

### BD-17 관계 술어 — ADOPTED (사용자 승인, 2026-10-02 · baseline-1.0)
- 채택: observes · derived_from · depends_on(유형) · affects · requires · conflicts_with(유형) · contains · uses · executed_by · runs_on.
  버림: measures · evidenced_by · degrades · constrains · enables. 보류: supports. 까닭은 SEMANTIC §4.

### BD-18 인코딩을 고르지 않는다 — ADOPTED (사용자 승인, 2026-10-02 · baseline-1.0)
- 평가 기준만 적는다(SCHEMA §6). "표준 라이브러리만" 규칙과 부딪힌다 → OQ-19.

### BD-19 사용자가 이미 정한 것을 옮긴다 — ADOPTED (사용자, 2026-10-02)
- WALP 는 쓰지 않는다. Sensor 출력은 텔레메트리로만 받는다. Verifier 의 판정 · 정책 제안은 배선하지 않는다. CR 은 입출력 계약이 먼저이고
  자리는 그다음이다. 순서는 ① CR 분리 → ② Sensor→Telemetry → ③ Telemetry→DC → ④ DC→CR → ⑤ Policy → ⑥ Action Intent →
  ⑦ Validate/Arbitrate/Guard → ⑧ Shadow → ⑨ API 평가. (출처: `MS/docs/계획.md` §2–§3)
- 이 기준선의 층 순서(BD-01)는 이 순서와 부딪히지 않는다.

### BD-20 저장소 구성 — ADOPTED (사용자 승인, 2026-10-02 · baseline-1.0)
- **결정.** 시퀀싱 저장소보다 먼저: **Telemetry 를 채운다**(정준 Observation 꼴 · 이름 · 검증기). 새로 셋을 둔다: **Action**(EXECUTE) · **Guard**(VALIDATE–GUARD) ·
  **Health**(ASSESS · VERIFY). 계약(어휘 · 실체 id · 시간 기준 · 의존 그래프)은 **baseline** 이 기계가 읽는 꼴로 갖는다. 새 저장소를 더 만들지 않는다.
- **까닭.** Guard 는 Policy 와 고장 모드를 나누지 않아야 한다 → 저장소 분리. Action 이 없으면 Verify · `action_state` · S6 이 설 자리가 없다.
  Health 가 없으면 진단이 다시 Sensor 판정기와 MS 품질 상태에 흩어진다.
- **대안.** (a) Guard · Action 을 MS 안에 둔다. (b) Model Registry 를 따로 둔다. (c) Verify 를 따로 둔다.
- **버림.** (a) 지금의 BV-05 · 06 이 굳는다. (b) 계약은 baseline 이 가질 수 있다 — 저장소만 늘어난다. (c) 검증은 Assess 와 같은 기계(기대 대 관측)를 쓴다 → Health 에.
- **결과.** OQ-02(Health 를 따로 둘지), OQ-22(시퀀싱의 뜻).

### BD-43 층 번호 L0–L5 는 코드의 것을 쓰고, 기준선의 단계는 이름으로 부른다 — ADOPTED (baseline-1.0)
- **까닭.** 승인 직전에 다시 확인해 보니 Telemetry · Sensor 가 이미 L0 Telemetry · L1 Sensor · L2 State · L3 DC · L4 Policy · L5 Action 을 코드와
  문서에 쓰고 있었다(`llmsensor.telemetry.l0`, Telemetry README). 기준선 0.1 의 L0–L11(단계 번호)과 같은 글자에 다른 뜻이었다 — 그 자체가 DUP 다.
- **대안.** (a) 기준선 번호를 코드에 강요한다. (b) 코드 번호를 쓰고 기준선의 단계는 이름으로 부른다.
- **버림.** (a) 이미 커밋된 모듈 이름과 문서를 바꿔야 한다.
- **결과.** Guard 는 L4 와 L5 사이, Health 는 L1–L2 옆이다. 둘 다 새 번호를 받지 않는다(BASELINE §10.1). 사용자가 다른 번호를 원하면 이 결정을 바꾼다.

### BD-44 L0 출처 종류와 State 의 Basis 를 가른다 — ADOPTED (baseline-1.0)
- 출처 종류(reported · declared · measured · translated · ref)는 **관측 하나**에 붙는다. Basis 는 **규칙 하나**에 붙는다. 같은 것이 아니다.
- 옮김 규칙: reported · measured → 관측 Basis OBSERVED. declared → RUNTIME_DECLARED(런타임) 또는 PROVIDER_DECLARED(공급자). translated → 원래 종류를
  그대로 둔다(어휘만 바뀌었다). ref → Basis 가 없다(참조). 규칙의 Basis 는 규칙이 정한다(문턱의 출처).
- 결과: PC-02 의 검증기에 이 대응을 시험으로 붙인다.

---

## 미결 질문에서 온 결정 — ADOPTED (사용자: "권고안대로 결정", 2026-10-02)

근거 · 선택지는 [`OPEN_QUESTIONS.md`](OPEN_QUESTIONS.md) 의 같은 번호 행에 남아 있다. 여기에는 결정과 결과만 적는다.

| # | 원 질문 | 결정 | 결과 · 대신하는 것 |
|---|---|---|---|
| BD-21 | OQ-01 CR 의 자리 | CR 은 **DC 를 받아 LLM 입력으로 그리는 어댑터**다. Policy 실행기 쪽에 속한다. DC 에 없는 정보를 더하지 않는다. CR 이 내는 것의 이름은 `LLMContext` 다 | **SUPERSEDES** `MS/docs/계획.md` §1 "CR = DC 와 Policy 사이의 decision context construction rule". 그 문서는 PC-21 로 고친다. 맥락 예산 · 배치 · 캐시 경계 선언은 그대로 CR 의 일이다 |
| BD-22 | OQ-02 Assess · Verify 의 집 | 새 **Health** 저장소 | PC-06 의 ASSESS 부분이 이리로 옮겨 간다 |
| BD-23 | OQ-03 안전 기본 결정 | 목적마다 Model 에 `default_decision` 을 판본으로 둔다. context_policy = KEEP (고정 맥락) · prompt_policy = 고정 프롬프트 계획 · provider_selection = KEEP_PROVIDER · execution_control = ESCALATE. **ESCALATE 능력(human_reviewer)이 없으면 STOP** | 마지막 문장은 권고를 끝까지 정하려고 더한 것이다. ESCALATE 를 할 수 없을 때 남는 보수적 행동이 STOP 이기 때문이다. 바꾸려면 Model 판본을 올린다 |
| BD-24 | OQ-04 A0–A8 배분 | **Validate** = A0 · A1 · A2 · A3 · A4 (꼴 · 자기 DC 안의 근거). **Arbitrate** = 후보 사이 선택(Model 의 우선순위 · `conflicts_with`). 지금 옮길 규칙은 없다. **Guard** = A5 · A6 · A7 · A8 (지금 상태 기준의 낡음 · 사전조건 · 허가 · 되풀이). 예외 E 는 세 단계 모두 거부 | **SUPERSEDES** `MS/docs/계획.md` §2 ⑦ 의 배분(Arbitrate = A1 · A2 · A3 · A5 · A8). PC-21 |
| BD-25 | OQ-05 행동 실행 주체 | 새 **Action** 저장소가 꼴(ActionIntent · ActionCommand · ActionOutcome)과 실행기를 갖는다. 첫 실행기는 MS `tools.py` 를 옮긴 것 + Claude Code 훅의 shadow. **Sensor 는 행동 기록을 내지 않는다** | DATA_FLOW §7. Sensor 세션의 S6 에 대한 답 |
| BD-26 | OQ-06 질의형 선택 | DC 목적 명세가 질의(StateQuery 계열)를 가질 수 있다. CR 은 그래프를 직접 질의하지 않는다 | BV-07 을 푸는 길. PC-23 |
| BD-27 | OQ-07 관계를 누가 쓰나 | 관측(ESTIMATE)과 구조 선언(Runtime) 둘 다 쓴다. 간선에 `basis` ∈ {OBSERVED, DECLARED} 를 붙인다 | |
| BD-28 | OQ-08 텔레메트리 계약의 집 · 의존 방향 | **Telemetry 저장소**가 정준 Observation 꼴 · 이름 · 검증기를 갖는다. 내용은 Sensor v3 를 바탕으로 하고 MS 의 자기 관측 칸(`kind=self`)을 더한다. 의존 방향: Telemetry ← Sensor · MS · Health · Action · Guard. DC 는 아무것도 import 하지 않는다. MS → DC | PC-02. SCHEMA §5 의 대응표가 첫 입력이다 |
| BD-29 | OQ-09 상태 엔진 합치기 | 지금은 합치지 않는다. **의미 규약**(유효성 · 신선도 · 근거 종류 · 생애)만 공유한다. PC-02 · PC-05 뒤에 다시 본다 | |
| BD-30 | OQ-10 목적 · 행동 이름 | DC 의 이름을 쓴다. 여기에 Sensor 의 `WAIT` 행동, 그리고 `execution_interruption` · `quality_state` 참조를 더한다 | PC-15 |
| BD-31 | OQ-11 사후조건 | Model 의 ActionSpec 에 사후조건 · 검증 시간 창을 적는다. MS `ToolSpec` 은 그 투영이다 | VERIFY 의 입력 |
| BD-32 | OQ-12 실체 id | `<유형>:<범위>:<지역 id>`. 요금 한도는 `account:<id>` 실체에 단다 | PC-02 · PC-20 |
| BD-33 | OQ-13 시간 기준 | 경계에서 ms + `time_base`(unix_ms · monotonic_ms). MS 의 초는 경계에서 바꾼다 | PC-12 |
| BD-34 | OQ-14 `supports` · 진단 가설 | 미룬다. 고장 모드 모형이 선 뒤에 다시 본다 | |
| BD-35 | OQ-15 건강 성격 상태의 소유 | 이름 · 값은 그대로 두고 소유 층 표시만 ASSESS 로 한다(`execution_health` · `tool_execution_health` · `execution_interruption` · `runtime_reliability` · `answer_reliability` · `correction_rate`) | |
| BD-36 | OQ-16 신뢰도 | State 에 선택 칸 `confidence{kind: none · ordinal · calibrated, value}` 를 둔다. **`kind=ordinal` 은 Guard · 정책이 문턱으로 쓰지 못한다** | 보정 전 Q 는 ordinal 이다 |
| BD-37 | OQ-18 결정 재사용 열쇠 | DC digest(as_of 포함)는 그대로 둔다. 재사용 열쇠는 **as_of 를 뺀 core 의 해시**로 따로 둔다 | PC-07 |
| BD-38 | OQ-20 원문 확인 | 원문을 확인하기 전까지 BASELINE §0 의 원칙은 "인용" 표시를 유지한다 | 확인 일은 남는다(사용자 할 일) |
| BD-39 | OQ-21 `resource_state` | (1) 예산이 없으면 **NOT_APPLICABLE 을 유지**한다. 예산이 반드시 있어야 하는 배치는 Model 에 "필수" 로 적는다. 없으면 ASSESS 의 설정 적합성 고장 상태가 선다. (2) **실행 중 비용으로 판정한다**: OPEN_QUESTIONS 의 조건 1–5 를 지키고, 부분 합 ≥ 예산이면 BUDGET_EXHAUSTED(permanent), WITHIN_BUDGET 은 합이 완전할 때만. `resource-state-v2`. 예산의 주인은 **Model 의 운영자 가정 하나**다(BD-13) | **SUPERSEDES** Sensor `docs/MS_HEALTH_INVENTORY.md` §4 가 사용자 답으로 읽은 "예산이 없으면 UNKNOWN". PC-22 |
| BD-40 | OQ-22 시퀀싱 엔진의 뜻 | **개발 순서 관리자**: baseline 의 계약 · 의존 그래프(BASELINE §10)를 읽고 저장소 · 세션에 일을 지시하고, 피드백(시험 · 적합성)을 받아 다시 정한다. 런타임 실행층이 아니다 | BD-20 의 저장소들이 선 뒤에 만든다 |
| BD-41 | OQ-23 영속성 | Observation Log · Model · Ledger 를 영속한다. 재시작하면 State 는 재생으로 다시 짓는다 | |
| BD-42 | OQ-24 Decision Ledger 의 집 | 쓰기 순서는 Runtime(MS)이 갖는다. 꼴은 baseline 계약에 둔다 | PC-11 |

**미결로 남은 것 (승인을 막지 않는다 — 까닭은 OPEN_QUESTIONS.md):** OQ-17 안전 동작 순서 · OQ-19 인코딩과 "표준 라이브러리만" 규칙.

---

## 통합 1 회차에서 온 결정 — ADOPTED (2026-10-02, 사용자: "결과와 권고를 읽고 baseline 에 맞게 각 레포에 명령하라")

| # | 결정 | 까닭 · 근거 | 결과 |
|---|---|---|---|
| BD-45 | **파일 하나에 소유 세션 하나**(PROTOCOL §5). L1 팩은 **전부 Sensor 세션**의 것이다. Telemetry 세션은 L0 만 맡는다 | liveness 를 Sensor 세션이 이미 구현했는데(`28c8af4`), Telemetry 세션도 "새 L1 팩 넷" 을 1 순위로 제안했다(baseline#1). 같은 것을 둘이 짓는다 | Telemetry 세션의 제안 1 은 Sensor 세션의 일로 옮긴다 |
| BD-46 | **Sensor → MS 경로는 Sensor state-export → DC(SensorSource) → MS `state_reader` 하나다.** MS 는 Sensor 의 판독(readings) · Q · 판정을 자기 그래프에 넣지 않는다. `ms/sensing.py` 는 더 넓히지 않고, 이 경로가 확인되면 걷어 낸다. MS 가 제안한 센서 상태(`outcome_confidence` · `false_success_risk` · `loop_risk` · `cost_anomaly`)는 MS 가 짓지 않는다 — Sensor(L1 · L2)나 Health 의 일이다 | 판독(OK · SUSPECT · FAULT)은 판정이다. L0 는 판정을 받지 않는다(Telemetry 저장소 자신의 규칙). Sensor 에는 이미 바깥이 읽는 유일한 길(`llmsensor.state-export/1`)이 있고 DC 가 그것만 읽는다(`4b97cea`). MS 가 따로 해석하면 같은 상태가 두 곳에서 다른 뜻으로 생긴다 | **SUPERSEDES** BD-19 의 "Sensor 출력은 텔레메트리로만 받는다" — 그 결정 뒤에 L0 층이 따로 섰고, 판정을 받지 않기 때문이다. Verifier 의 판정 · 정책 제안을 받지 않는다는 뜻은 그대로다 |
| BD-47 | **liveness 의 입력은 L0 사건이다.** 이름은 Telemetry 세션이 정한다. `turn_open` · 마지막 활동 시각 · 무음 길이는 Sensor 가 L0 사건에서 계산하는 **측정(MEASURE)**이다. 지금 Sensor 가 스스로 정한 `run.turn_open` 등 다섯 칸은 L0 사건이 생길 때까지 compat 투영으로만 둔다 | 같은 관측의 이름을 두 세션이 따로 정하고 있었다(Sensor run 레코드 칸 대 L0 사건 흐름). BD-28 · BD-45 | Telemetry 세션: 차례 경계 사건(입력 받음 · 차례 끝 · 흐름 닫힘)을 L0 에 더한다. Sensor 세션: S1 의 입력 계약을 그 사건 이름으로 다시 쓴다 |
| BD-48 | 전달 규약과 통합 브랜치(PROTOCOL.md) | 보고가 이미 두 통로(이슈 · 저장소 파일)로 갈렸다 | 세션마다 baseline 이슈 하나 |
| BD-49 | MS 측정: 후보 F2 를 ④(CR v2)의 첫 사전등록 대상으로 삼는다. 상태는 DC 를 꽂은 `state_reader` 로 읽는다. 과업 t6 은 **고친다**. 과업 묶음 판본을 올리고, 비교는 같은 판본 안에서만 한다 | F2 는 네 측정에서 같은 방향이다(증거 아님). t6 은 과업 정의의 결함이다(X4). 판본을 올리면 앞 측정을 지우지 않고 가를 수 있다 | |
| BD-50 | Sensor 를 Telemetry 의 **필수** 의존으로 바꾸는 기준: 수집기 셋(cc_jsonl · cc_stream · sweagent)마다 **서로 다른 실데이터 기록 3 개 이상**에서 `l0-check` 가 100 % 같다 + MS `inproc:ms` 원장이 Sensor State 까지 흐른다 + `l0-check` 를 시험으로 붙인다. 그 뒤 Sensor 의 수집기를 지운다(Telemetry 세션) | 지금 대조는 이 세션 기록 하나뿐이다(Telemetry 보고). 원천마다 꼴이 다르다 | |
| BD-51 | 세션은 PR 을 만들지 않는다. 통합은 baseline 이 저장소마다 `claude/gracious-meitner-vp49xe` 에서 한다 | 각 저장소의 기본 브랜치가 지금 다른 세션의 작업 브랜치다(Sensor = `nice-wright`, DC = `nifty-volta`, MS = `eloquent-turing`, Telemetry = `jolly-einstein`). PR 을 거기로 열면 서로의 일을 덮는다 | 기본 브랜치를 어떻게 둘지는 사용자가 정한다 |

### 통합 2 회차 (2026-10-02, Sensor 보고 `a173ca2` 에 대한 결정)

| # | 결정 | 까닭 | 결과 |
|---|---|---|---|
| BD-52 | `liveness_state`(실행 · task 의 liveness)는 **Sensor 에 둔다.** 소유 층 표시만 ASSESS(BD-35 와 같은 방식). Health 저장소가 서면 그때 옮긴다. 수집기의 liveness(DATA_FLOW C1)는 **다른 실체**(`collector:*`)의 상태다. 값 이름은 `ENDED_WITHOUT_TERMINAL` 로 맞춘다 | Health 저장소가 아직 없다. 대상이 다른 두 liveness 를 한 상태로 합치지 않는다 | DATA_FLOW C1 의 값 이름을 고쳤다 |
| BD-53 | 수집기 결함 D1–D4 와 런타임 자신의 행동(압축 · 백그라운드 이동 · 권한 거부) 수집은 **Telemetry 세션**의 일이다. PC-20 의 주인을 바꾼다 | 수집기는 Telemetry 저장소로 옮겨졌고, Sensor `llmsensor/telemetry/*` 는 Telemetry 세션 소유다(PROTOCOL §5). 사용자 지시("Sensor 는 센서만")와도 맞는다 | DATA_FLOW §7 · PC-20 고침 |
| BD-54 | S3 `dependency_fault` 를 **승인한다**. 조건: 실체 id `dependency:<범위>:<이름>`(BD-32) · 런타임이 구조화한 원인만 · `NO_FAULT_DECLARED` ≠ HEALTHY · 소유 층 표시 ASSESS · 상태 수 상한을 올린다. 입력 이름은 L0 가 정한다 | BD-10(선언된 근거만) · BD-47 | |
| BD-55 | PC-08(Sensor 의 DC 둘 · 참조 정책 걷어 내기)은 **DC 가 Sensor DC 의 장점(`allow_stale` 명시 · ContextStore/explain)을 옮긴 뒤**에 한다. Phase 8 결과 파일은 그 날짜의 기록으로 남긴다 | BD-05 가 그 둘을 옮길 후보로 적었다. 먼저 걷으면 기능이 사라진다 | DC 에 CMD-D6 |

### 통합 3 회차 (2026-10-02, 보고 baseline#5 · Telemetry `e246ada` · MS `ced8186`–`ffa78c3`)

| # | 결정 | 까닭 | 결과 |
|---|---|---|---|
| BD-56 | **Sensor 저장소를 두 세션이 쓴다 — 경계를 다시 긋는다.** Sensor `llmsensor/state/*`(규칙 · 엔진 · 모형) · `sensing/*` · `sensors/*` · `verifier.py` = **Sensor 세션(`nice-wright`)**. Sensor `llmsensor/state/export.py`(state-export 계약) = **DC 세션(`nifty-volta`)** — 그 계약을 지었고 유일한 소비자가 DC 다. PC-08 은 사용자 지시로 DC 세션이 했고, 이식(allow_stale · ContextStore)과 함께 했으므로 BD-55 의 뜻(기능을 잃지 않음)을 지켰다 — 받아들인다 | baseline#5 의 다음 할 일 일곱 가운데 넷이 다른 세션에 이미 지시한 일이었다(PC-22 = CMD-S3 · PC-20 = CMD-T6 · PC-09/Q4/PC-06 = Sensor 규칙 · 엔진) | PROTOCOL §5 고침 |
| BD-57 | **집계 상태의 근거 시각 = 그 값을 정한 근거의 시각**(근거 전체 중 가장 늦은 것이 아니다). 예: `execution_health = UNRESOLVED_FAILURES` 가 7 시간 전 `tool[WebFetch]` 실패에서 나왔으면, 집계의 시각도 그 실패의 시각이다. 규칙 판본을 올린다 | baseline#5 Q4: 실제 세션에서 신선한 집계가 낡은 구성 요소 위에 서 있었다. 값을 정하지 않은 새 근거가 집계를 신선하게 보이게 하면 STALE 판정이 틀린다 | SCHEMA §2.4 `observed_at` 정의를 고쳤다. Sensor 세션의 일 |
| BD-58 | DC 목적에 **`agent_context`**(런타임 자신의 맥락: KEEP · COMPACT(능력 `runtime_compaction`) …)를 더한다. PC-15 에 넣는다 | baseline#5 Q1: Sensor 의 `COMPACT_CONTEXT` 가 DC 어휘에 없다. MS 의 LLM 맥락(`context_policy`)과 런타임 맥락은 다른 결정이다 | DC 세션의 일 |

### 사용자 결정 (2026-10-02)

| # | 결정 | 결과 |
|---|---|---|
| BD-59 | **`claude -p` 를 세 번까지 실행해도 된다** (사용자). BD-50 의 cc_stream 표본용 | Telemetry 세션에 CMD-T8 로 전달. 세 번이 한도 · 캡처 글은 커밋하지 않음 · 비용은 보고값 |
| BD-61 | DC 의 적용 TTL(`ttl_ms`)은 투영이 아니라 provenance 의 **입력 기록**으로 둔다 | DC 보고(baseline#4 5945541426): DC 는 소스의 Model 을 다시 읽지 않으므로 신선도를 투영하려면 그 값이 필요하다. SCHEMA §4.2 의 "파생 가능" 은 Model 을 읽을 수 있는 쪽의 이야기다 |
| BD-62 | **BD-50 기준 충족** — sweagent 7/7 · cc_jsonl 서로 다른 기록 3 이상(Telemetry · baseline · MS 세션) · cc_stream 3/3(`claude -p`, BD-59) · `inproc:ms` 원장이 Sensor State 까지(MS `tests/test_l0.py`) · `l0-check` 시험(Sensor `tests/test_layer.py`). 다음: Sensor 의 수집기를 걷고 Telemetry 를 **필수 의존**으로 — Telemetry 세션의 일(CMD-T9) | 하류 영향: Sensor `l0.py` · Sensor 시험 셋(Telemetry 세션 소유) · Sensor `eval/health_inventory.py`(Sensor 세션) · DC `examples/sensor_session.py`(DC 세션). MS 는 직접 쓰지 않는다 |
| BD-63 | BD-57 을 분명히 한다: 값을 정한 근거가 **여럿이면 그 가운데 가장 이른 시각**이다(결론은 가장 낡은 결정 근거만큼만 신선하다). MS 파생(모든 입력이 술어에 들어가 값을 정한다)은 지금처럼 입력 중 가장 이른 시각이 맞다. Sensor 집계(`execution_health`)는 값을 정한 구성 요소(예: 실패한 도구 결과)의 시각이다 | MS 보고(baseline#2 5945550488) 물음 2 |
| BD-64 | `resource-state-v2` 에서 **보고가 이긴다**(BD-39 조건 2 우선). 단가표 추정만으로 선 BUDGET_EXHAUSTED 는 **영구가 아니다** — 영구는 되돌릴 수 없는 사실에만 붙는다(보고된 비용 ≥ 예산). 더 낮은 보고가 와서 추정과 모순되면 INVALIDATE + 전이로 고치고, 그 어긋남(`cost_estimate_error`)은 단가표의 건강 문제(ASSESS)로 남긴다. 추정으로 이미 내려진 보수적 결정(STOP 등)은 되돌리지 않는다 | Sensor 보고(baseline#3 5945573792)의 판단 요청: 조건 3(부분 합 → 영구 소진)은 단가가 정확하다는 전제 위의 증명이다. 그 전제가 깨지면 증명도 깨진다. 지금 데이터에서는 일어나지 않는다(두 모형 단가 정확) — 규칙의 뜻만 바로잡는다 |
| BD-65 | 질의형 선택(PC-23)에서 **낡은 속성 값은 core 에 싣지 않는다(None)** — DC 기본을 따른다. LLM 에게 낡은 값을 보여야 하는 곳은 MS 가 그 질의에 `allow_stale` 을 **명시**한다. 지금 MS 가 값과 `_stale` 표시를 함께 보이는 동작은 그 명시로만 남는다 | DC 보고(baseline#4 5945599256) 요청 3. 기준선 I3(STALE 은 지금 값이 아니다) · BD-57 · 키별 `allow_stale`(CMD-D6)과 같은 규칙 |
| BD-66 | **PC-23 의 MS 쪽(CR 이 `ctx.rows` 를 받기 · `state_reader` 에 요청 넘기기)은 F2 측정 결정이 날 때까지 미룬다.** F2 를 돌리면 F2 를 먼저(사전등록이 지금 코드에 묶여 있다), 돌리지 않으면 바로 | CR 의 입력 길이 바뀌면 LLM 이 보는 맥락이 달라진다(BD-65 로 낡은 값이 None 이 된다) — 사전등록된 F2 의 측정 대상이 바뀐다 |
| BD-67 | **F2 측정 실행 — 사용자 결정, 끝남 → BD-72**(2026-10-02, 백그라운드). BD-66 에 따라 PC-23 의 MS 쪽은 F2 보고 뒤에 한다 | 사용자: "F2 지금 백그라운드로 돌리고 있어. 추후에 보고 받아" |
| BD-68 | Sensor 의 Telemetry 의존(`l0-telemetry @ git+…/Telemetry`)은 **통합 브랜치에 고정**한다: `@claude/gracious-meitner-vp49xe`. 단계가 끝나면 그 머리에 태그를 달고 태그로 옮긴다 | Telemetry 보고(baseline#1 5945634788): 지금은 GitHub 기본 브랜치(= 세션 작업 브랜치, BD-51)를 따라가 다른 세션의 진행 중 작업을 받을 수 있다. 통합 브랜치는 baseline 이 시험을 마친 것만 담는다 |
| BD-69 | `l0.compare` · `llmsensor l0-check` 의 뜻이 "두 수집기 대조" 에서 **"얼린 출력 · 불변식 대조"** 로 바뀐 것을 받아들인다(반환 꼴 유지 + `against` 칸). Sensor 수집기가 사라졌으므로 비교 대상이 없다. 실기록 대조는 Telemetry `eval/l0_check.py --verify` 와 얼린 지문으로 한다 | interface change 이지만 하류(Sensor `cli.py`)는 그대로 돈다(Telemetry 확인). BD-50 의 "l0-check 시험" 은 이제 golden · 불변식 · 변이 37 로 대신한다 |
| BD-70 | 내보내기 계약 `/2`(CMD-D7): **실체 id 는 Sensor 엔진의 것을 그대로 낸다**(id 규칙은 Sensor 세션 소유). 계약은 그 id 가 BD-32 꼴임을 명시하고, 소비자는 id 를 **해석하지 않는 불투명한 문자열**로 다룬다. `/1` 은 저장된 소비자가 없으므로 판본별 읽기 대신 분명한 오류로 거절한다 | DC 보고(baseline#4 5945654156)의 질문. 지금 `agent:cc_stream:demo` 는 이미 `<유형>:<범위>:<지역>` 꼴이다 |
| BD-71 | MS 의 호환 속성 `StateManager.evidence` 는 **F2 보고 뒤에** 뗀다 | DC 가 새 이름으로 옮겼고 그 속성 없이도 DC 88 통과(DC 확인). 다만 F2 가 MS 코드 위에서 돌고 있어 그 사이 MS 를 바꾸지 않는다(BD-66 과 같은 까닭) |
| BD-72 | **F2 판정**(MS 보고 baseline#2 5945675444, 결과 MS `c21abcf`). 실행 자체는 **성공**: 사전등록대로 63 실행 · 무효 조건 없음 · S4 동작점 18/21. 가설은 **사전등록 읽기 그대로** 판정한다: Q1 꺼냄 B→D +0.381 [0, 0.952] — 구간이 0 에 닿으므로 **F2(꺼냄 증가)는 후보에서 내린다**. "하한 0 은 설계상 피할 수 없었다" 는 다음 사전등록의 교훈이지 이번 읽기를 바꾸는 까닭이 아니다. Q1 지연 B→D **+2,565 ms [+163, +6,218] — 늘었다(확인)**. S2(미리 정한 수)로는 37% 만 꺼냄으로 설명되므로 "느린 것은 꺼냄의 결과" 는 **확인되지 않는다**. Q2 D→G 꺼냄 +0.048 [0, 0.143] — **DROP · DEFER 는 꺼냄의 원인이 아니다**. Q2 지연은 모른다. 품질은 세 칸 모두 21/21 이라 천장이다(비열등은 정보가 적다). 입력은 줄지 않았다(B→D +410 [−446, +1,564]). **요약: 이 과업 묶음 · claude-cli 에서 적응 맥락(D)은 비용(지연 +2.6 s · 출력 +137 토큰 [4.5, 337])이 재졌고 이득은 재지 못했다.** 기본 맥락 선택기는 지금처럼 `FixedContext` 로 둔다(바꾸지 않는다) | claude-cli 값이다 — 사전등록 §9 대로 "이 도구로 본 값" 이지 API 일반의 증거가 아니다. DC 상태 읽기는 실행 때의 통합 머리 `a061c65`(사전등록 §4 그대로 — 유효) |
| BD-73 | **BD-66 · BD-71 의 미룸을 푼다**: F2 보고가 왔으므로 MS 는 PC-23 의 MS 쪽(CR 이 `ctx.rows` 를 받기 · `state_reader` 에 요청 넘기기) → `StateManager.evidence` 호환 속성 떼기 순으로 한다. **F2 후속 사전등록은 PC-23 뒤**에, 그리고 사용자 결정(실행 비용)을 받은 뒤에 돌린다. 후속은 (1) 사전등록 읽기가 **원리적으로 확인 가능한** 설계여야 하고(이번처럼 과업 다수가 차 0 이면 부트스트랩 하한이 0 에 묶인다 — 돌리기 전에 그 확률을 적는다), (2) 적응 맥락의 **이득 쪽**(품질이 천장이 아닌 과업 또는 입력이 실제로 주는 동작점)을 잴 수 있어야 한다. 비용만 재는 측정은 되풀이하지 않는다 | PC-23 뒤에는 CR 입력 길이 바뀌어(BD-65) F2 의 측정 대상이 달라진다 — 후속은 새 코드 위에서 새 판본으로 재는 것이 맞다. GUIDANCE: 같은 측정의 되풀이를 피한다 |
| BD-74 | BD-63 의 범위: **"없음" 을 말하는 값(전칭 · 부재 — 예: NO_FAILURE_OBSERVED)의 `observed_at` 은 그 말을 마지막으로 다시 확인한 관측, 곧 덮는 결과 가운데 가장 늦은 시각**이다. 가장 이른 시각 규칙(BD-63)은 특정한 관측이 값을 정할 때(UNRESOLVED 의 실패 결과 등)에 쓴다 | 부재 주장의 신선도 물음은 "마지막으로 본 뒤에 무슨 일이 있었나" 다. 결과가 올 때마다 주장이 다시 확인되므로 첫 결과 시각을 쓰면 계속 관측되는 중에도 STALE 이 된다(Sensor 보고 2, baseline#3 5945705814). 원천이 멈추면 가장 늦은 시각도 늙어 STALE 이 된다 — 맞는 동작 |
| BD-75 | BD-64 를 고친다: 추정 소진을 낮은 보고가 뒤집을 때 **전이(UPDATE) + 이유 `cost_estimate_error` 로 충분**하다. 규칙이 엔진의 INVALIDATE 를 부르는 길은 그것을 읽는 소비자가 생길 때 짓는다. 상태 내보내기 `catalog` 에 `owner_layer` 를 싣는 요청도 **소비자가 없으므로 지금 하지 않는다**(Registry 에는 있다) | 이력에 이유가 남아 "틀린 추정이었다" 가 읽힌다. 소비자 없는 칸 · 사건은 짓지 않는다(GUIDANCE: 과한 지시를 피한다) |
| BD-76 | **정책은 필수 상태의 모름(None)을 지나쳐 다른 분기로 가지 않는다.** 필수 키가 쓸 수 없어 규칙이 정해지지 않으면 그 목적의 `default_decision`(BD-23)을 쓴다. 아는 값만으로 정해지는 분기(예: 예산 소진 → STOP)는 남아도 된다. `default_decision` 의 자리는 **DC 의 목적 명세(`Purpose`, 판본 있음)** 다 — BD-23 의 "Model 의 목적마다" 가 가리키는 곳이고, 시험 정책과 MS 가 같은 값을 읽는다 | DC CMD-D11(baseline#4 5945779517): 실데이터 `cc_jsonl_self:self_sna` i=154 에서 `execution_health` 가 의도대로 STALE(None)이 되자 시험 정책 `refpolicy/execution.py` 가 맨 끝 분기로 빠져 RETRY → **CONTINUE**. BD-23 은 ESCALATE, DATA_FLOW §2 "모름으로는 행동을 바꾸지 않는다". baseline 이 코드에서 확인(`refpolicy/execution.py:24-29`). 기준선 규칙이 실데이터에서 처음 드러낸 정책 결함이다 |
| BD-77 | BD-65 는 **MS 전체**에 적용한다: DC 를 꽂았든 아니든(기본 길 포함) 낡은 값은 `allow_stale` 을 명시한 질의에서만 LLM 에 간다. MS 가 그런 질의가 지금 없다고 판단한 것을 받아들인다. CR 판본 `cr-1 → cr-2` 이므로 앞의 claude-cli 측정(F2 포함)과는 견주지 않는다(BD-49: 같은 판본 안에서만) | 길에 따라 LLM 이 보는 것이 달라지면 DC 를 꽂는 것 자체가 결과를 바꾼다 — 배선이 의미를 바꾸면 안 된다. MS 보고 baseline#2 5945795137 |
| BD-78 | **다섯 저장소의 GitHub 기본 브랜치 = 통합 브랜치 `claude/gracious-meitner-vp49xe`**(사용자가 바꿈, 2026-10-02 · baseline 이 `git ls-remote --symref` 로 다섯 모두 확인). 새 세션 · 기본 clone · 고정 없는 설치는 이제 통합 머리를 받는다. BD-68 의 고정은 그대로 둔다(단계 끝에 태그로) | 전에는 기본 브랜치가 세션 작업 브랜치라 다른 세션의 진행 중 작업이 섞여 들 수 있었다(BD-51 · BD-68 의 까닭) |
| BD-79 | MS 가 제안한 센서 상태 넷(`outcome_confidence` · `false_success_risk` · `loop_risk` · `cost_anomaly`)은 **새 상태로 짓지 않는다**. 이미 있는 것(`progress_state` · `resource_state` · Consistency 판독 · `cost_estimate_error`)을 BD-46 길(state-export → DC → MS)로 읽는다. 근거 없는 문턱이 박힌 판독(`loop_k=3` · `BURST_FACTOR=4` · 보정 전 Q 의 띠)은 상태로 올리지 않는다 | Sensor CMD-S5 대조(baseline#3 5945888869): 셋은 중복, 하나는 기준 분포가 없다. 확률(risk)은 보정 없이 만들 수 없고(BD-36), SWE-bench 실험에서 Q 는 기준선보다 낫다는 증거가 없었다 |
| BD-80 | Telemetry 의 compat(꼴 v3)은 **넓히지 않는다**. L1 팩이 L0 칸(`tool.end.moved_to_background` · `provider.rate_limit.resets_at_ms` 등)을 쓰려면 Sensor 의 L0 묶기(`llmsensor/sensing/l0.py`)로 **L0 사건을 직접** 읽는다 — 두 칸은 이미 L0 catalog 에 있다. 요금 한도의 계정 식별자는 **원천이 보고할 때만** L0 에 싣는다(지어내지 않는다); 없으면 S4 처럼 런타임 실체에 두고 "계정 범위" 라고 적는다 | compat 은 옛 State 엔진 입력을 위한 투영이고 "v3 를 넓히지 않는다" 가 그 설계다(Telemetry `compat.py` 머리말). 길이 둘(compat 덧대기 · L0 직접)이면 같은 값이 두 벌 생긴다 |
| BD-81 | BD-23 의 `prompt_policy` = "고정 프롬프트 계획" 은 DC 행동 이름으로 **`FULL_INSTRUCTION`** 이다 — MS `FIXED_PROMPT` 의 `instruction_mode: full` 과 같다. DC `Purpose.default_decision` 에 넣는다(CMD-D13 에 덧붙임). MS `MSStateReader` 반환 `record` 에 `default_action` 을 싣는다 — MS 가 같은 값을 읽는 자리(CMD-M9) | DC 보고(baseline#4 5945915401) 질문 2 · 3. BD-23 이 값을 정했으나 이름이 MS 쪽 말이었다 |
| BD-82 | BD-76 의 "규칙이 정해지지 않으면" 을 DC 가 읽은 대로 받아들인다: 목적의 필수 상태라도 **그 정책 규칙이 읽지 않는 키**의 모름은 기본 결정으로 보내지 않는다(`execution_control` 의 `progress_state` · `rate_limit_state`). 결정 변화 수 484 → 450 은 **개선이 아니다** — 대부분 SWE-agent 에서 `execution_health` 가 끝내 UNKNOWN 이라 정책이 상태 대신 기본값으로 정하는 데서 온다. 그 까닭과 실행 첫 평가점(도구 결과 전)의 값은 Sensor 가 가린다(CMD-S17) | 기본값으로 늘 가는 정책은 안전하지만 아무것도 정하지 않는다. 원인이 원천의 한계인지 Sensor 규칙의 구멍인지에 따라 할 일이 다르다 |
| BD-83 | **F2b 사전등록(MS `2912912`)은 BD-73 의 두 조건을 채운다**: 돌리기 전 확인 확률(R1a 1.00 · R1b 1.00 · R2 0.82, p=1/9 — baseline 이 `eval/power_F2b.py` 를 다시 돌려 같은 표 확인) · 이득 쪽 동작점(서버 36 · 예산 3,000, 호출당 −26%, 품질 천장은 미끼로 피함). 짓는 순서: 선행조사(지금 해도 된다) → 과업 묶음 3 · 층화 하니스 → M9(D13 뒤) → **실행은 사용자 결정**(약 $2.9–3.6 · 20–25 분, claude-cli 이므로 "이 도구로 본 값") | 가설이 F2 의 과업별 차에서 나왔고(탐색), 결과가 적응 맥락을 기본값으로 올릴지(BD-72) 판단할 첫 이득 측정이다 |
| BD-84 | `execution_health` 의 두 "모름" 을 가른다. (a) 도구 호출이 **아직 없다**(결과를 본 것 0 · 못 본 것 0) → 새 값 **`NO_TOOL_RUN_YET`**(INFERRED, 근거 OBSERVED — "도구 실행이 아직 없다" 는 관측된 사실이고 건강을 말하지 않는다, NO_FAILURE_OBSERVED 와 다르다), `execution-health-v3`. (b) 호출은 있는데 결과를 볼 수 없다(SWE-agent: `tool.end` 9,378/9,378 `is_error` unobserved, traj 에 구조화된 결과 칸 없음) → **UNKNOWN 그대로** — 원천 한계이며, 그 원천에서 실행 정책이 기본값(ESCALATE)으로 정하는 것은 맞는 동작이다(글에서 오류를 읽어 내지 않는다, BD-10). NOT_APPLICABLE 은 쓰지 않는다("이 배치에서 정의되지 않음" 이 아니다 · usable 도 아니다) | Sensor CMD-S17(baseline#3 5946000658). 모든 실행의 첫 결정이 ESCALATE 인 것은 정책이 아무것도 정하지 않는 것이다(BD-82). 새 값은 관측된 사실이라 근거 없는 짐작이 아니다. 센서는 그대로 두고 정책이 지표를 읽는 길은 원 수치를 DC core 로 끌어들인다(BD-08) |
| BD-85 | 결정 문맥(DC core)은 **순서에 무관**하다(정준 JSON 은 열쇠를 정렬한다). LLM 에 보이는 **표시 순서는 CR(MS)의 일**이다 — MS 가 DC 결과를 받아 모형 선언 순으로 다시 놓는다. DC core 에 속성 순서를 싣지 않는다 | DC 보고(baseline#4 5946002824): DC 길과 MS 직접 길은 내용은 같고 순서만 달라 LLM 글자열 · `prefix_hash` · 프롬프트 캐시가 갈린다. 배선이 LLM 이 보는 것을 바꾸면 안 된다(BD-77 과 같은 원칙) |
| BD-86 | F2b 의 판단 기준은 **새로움이 아니라 이 시스템의 결정**이다 — 적응 맥락을 기본으로 올릴지(BD-72), CR 을 어떻게 지을지(J_CR). 선행조사(Liu arXiv:2608.16370 등, 확인 수준 `[출처:조각]`)가 현상을 이미 보고했으므로, **'덮음 선언' 칸을 더해 사전등록을 고친다**: 그 칸은 줄임이 꺼냄을 부르지 않게 하는 CR 설계 수단을 직접 잰다. 고친 사전등록에 확인 확률을 다시 계산하고 비용(약 +50%)을 적는다. 실행은 여전히 사용자 결정 | MS 선행조사 보고(baseline#2 5946007487). 같은 현상의 재현만으로는 우리 결정에 더하는 것이 적다 |
| BD-87 | L0 출처 종류: **단위 변환(초 → ms)은 값의 출처를 바꾸지 않는다** — 원천이 선언한 값이면 `declared` 그대로, 칸 설명에 원래 단위를 적는다. `translated` 는 출처 있는 대응표로 **어휘**를 옮길 때만 쓴다(catalog 정의). cc_stream `rate_limit_info.unifiedWindows`(창별 사용률 — Sensor S4 `quota_headroom` 이 읽을 `utilization` 의 실제 출처)는 **소비자가 있으므로** L0 에 싣는다(꼴 변경, 창 이름 보존 · 해석 없음 — CMD-T15). `isUsingOverage` · `upgradePaths` 는 소비자가 없어 싣지 않는다 | Telemetry 보고(baseline#1 5946013476)의 Deviation 이 맞다 — baseline 지시("translated")가 catalog 정의와 어긋났다 |
| BD-88 | BD-76 은 **품질 상태(`answer_reliability` · `correction_rate`)의 모름에도 적용**한다. 품질 우선 분기를 고를 수 있는지 모르면 줄이는 분기로 가지 않고 목적의 기본 결정(KEEP = 고정 맥락)을 쓴다. 적응 선택기 판본을 올린다(`ctx-adaptive-1` → `-3`, `-2` → `-4`). 결과로 세션 초반 적응 실행은 고정이 된다 — 의도한 것이다 | MS M9 보고(baseline#2 5946075005): 지금 선택기는 품질을 모를 때 "LOW 아님" 으로 지나쳐 줄인다. 줄임은 기본에서 행동을 바꾸는 것이고, 품질 우선은 줄임을 허락하는 안전 조건이다 — 그 조건을 모르면 허락하지 않는다(DATA_FLOW §2 "모름으로는 행동을 바꾸지 않는다") |
| BD-89 | BD-84 (a) 의 조건을 **"그 실행의 흐름을 관측했다(그 실행의 L0 사건 ≥ 1)"** 로 둔다 — 근거 시각은 마지막으로 본 그 실행의 사건(BD-74, 부재 주장). Sensor 가 붙인 "모델 호출 ≥ 1" 은 시각 있는 관측이 필요하다는 뜻은 맞지만, `input.received` · `turn.start` 도 시각 있는 관측이다. `NO_TOOL_RUN_YET` → 값 전이가 `RECOVER` 가 아니라 `UPDATE` 인 것은 맞다(둘 다 usable) | Sensor 보고 6(baseline#3 5946127692): 시각으로 합친(실시간에 가까운) 순서에서는 첫 묶음이 L0 묶기라 cc 26/26 의 첫 평가점이 UNKNOWN 이었다 — 그러면 실행 첫 결정이 여전히 ESCALATE 이고 BD-84 의 목적이 반만 선다 |
| BD-90 | **시간 기준을 섞지 않는다**(BD-33): 평가 시각이 unix 가 아닌 원천(cc_stream: `monotonic_ms`)에서 "리셋까지 남은 시간" 을 빼서 내지 않는다. 대신 Sensor S4 는 **선언된 리셋 시각 그대로**(`quota_resets_at_ms`, unix ms, declared — 평가 시각이 필요 없다)를 함께 낸다. 남은 시간은 unix `now` 를 가진 쪽이 계산한다. L0 에 수집기 수신 벽시계를 더하는 길(Telemetry)은 소비자가 더 생길 때 다시 본다 | Sensor 보고 7(baseline#3 5946157365): stream 에서 `resets_at_ms` 14/14 인데 지표 0/12 — S4 가 두 시간 기준을 섞지 않으려 거절했다(맞는 동작). 작은 쪽이 값의 출처를 그대로 보존하는 길이다 |
| BD-91 | BD-88 을 **프롬프트 선택기(`prompt-adaptive-1`)에도** 적용한다: 품질 상태를 모르면 압력이 HIGH 여도 지시를 concise 로 바꾸지 않고 목적의 기본(`FULL_INSTRUCTION`, BD-81)을 쓴다. 판본을 올린다. F2b(고정 프롬프트)에는 영향이 없다 | MS M12 보고(baseline#2 5948619425). 같은 꼴(품질 우선이라는 안전 조건을 모르면서 행동을 바꿈)이고 같은 원칙(DATA_FLOW §2)이다 |
| BD-92 | **단계 1 마감**(사용자 결정 2026-10-02): 네 저장소 통합 머리를 `STAGES.md` 에 커밋 sha 로 고정한다. 태그는 이 세션이 밀 수 없으므로(403) BD-68 의 "태그로 옮긴다" 를 **커밋 sha 고정**으로 대신한다 — Sensor 의 L0 의존은 `Telemetry@70b4febc…` | 바뀌지 않는 참조라는 BD-68 의 뜻을 sha 가 채운다. 태그는 사용자가 원하면 같은 sha 에 단다 |
| BD-93 | **F2b 실행** — 사용자 결정(2026-10-02): MS 세션이 돌린다. 사전등록 고침 2 그대로(칸 B · G=`ctx-adaptive-4` · H=`-4c`, 285 실행, 약 $5~7) | 사용자 응답 "MS 세션이 돌림" |
| BD-94 | **F2b 판정**(MS `4c6cfe2`, claude-cli 값). 실행 **성공**(285, $3.83, 무효 조건 안 걸림). **R2 확인**: 있음 층 입력 G−B −907 [−954, −866](약 −26%), 품질 비열등(세 칸 70/80 — 천장 아님), 안전 통과, 지연 차 없음. **R1 · R4 는 정보 부족 — 시험이 서지 않았다**: 285 실행 꺼냄 0, G · H 측정 80 중 60 에서 복잡도 규칙이 예산을 ×0.75 로 올려 숨긴 행이 없었다. 절약도 숨김이 아니라 대부분 COMPRESS · 예산에서 나왔다. **교훈**: 무효 조건은 재려던 조건을 **직접** 재야 한다(S4 가 계획 이유 글을 세어 80/80 으로 통과했지만 실제 숨김은 20/80). **결정**: 기본 맥락은 그대로 `FixedContext`(claude-cli 한 묶음뿐, 사전등록 §9). 기제(숨김 → 꺼냄 · 덮음 선언) 측정은 **지금 하지 않는다** — 우리 결정(기본을 올릴지)에 필요한 쪽(이득)은 이번에 답이 나왔고, 기제는 숨김 기반 CR 을 지을 때 다시 연다 | MS 보고(baseline#2 5949967686). GUIDANCE: 같은 측정을 되풀이하지 않는다 |
| BD-95 | **Action 저장소 시작**(`cogito5170/action`, 사용자가 만듦 2026-10-02). 첫 일은 꼴 셋(BD-25)의 계약 — 실행기 · Guard 는 꼴이 굳은 뒤(§10.2). 통로 baseline#6, 소유는 Action 세션. **비밀값(API 키)은 저장소 · 이슈 · 세션 메시지에 적지 않는다** — 환경 비밀로만 받는다 | 사용자 요청 · BASELINE §10.2 |
| BD-96 | **`action-contract/1` 계약 동결**(Action CMD-A1, action `c29dfbc`): SCHEMA_PROPOSAL §2.6 과 다른 넷을 받아들인다 — D1 `ActionCommand.decision_ref`(의도는 결정 기록보다 먼저 생기므로 허가 뒤 명령에 둔다) · D2 `policy` = `"<이름>@<판본>"` · D3 `ActionOutcome.error` → `exception`(L0 이름과 같게, 종류 이름만) · D4 id 는 내용 해시. 바꿀 것은 판본을 올려 더하는 쪽으로만. SCHEMA_PROPOSAL 표는 이 계약을 가리킨다. §10.2 의 다음 단계(Guard shadow · 실행기)가 열린다. Telemetry `Recorder.action` 이 밖의 `action_ref`(= `command_id`)를 받게 한다(CMD-T16) — L0 에서 명령 → 의도 → 결정으로 거슬러 가려면 필요. `deadline_ms` · `args_sig` 는 소비자(Guard)가 생길 때 | Action 보고(baseline#6 5951932945): 시험 25 · 변이 25/25 RED · Telemetry `event.check` 통과, baseline 이 통합 머리에서 다시 돌림 |
| BD-97 | PC-19(MS 가 ActionIntent 를 낸다)의 답(Action CMD-A2): **Q1** 의도는 **DC 배선일 때만** 낸다(a) — 행동은 결정 문맥을 거친 길(BD-46)에서만 생긴다. 계약은 그대로(`dc_id` 필수). **Q2** `policy` = `"ms-cr@cr-3"`, 나머지 판본은 DecisionRecord 에. **Q3** 한 사실은 한 사건(DUP 금지): 실행기가 서면 MS 의 도구 실행은 `action.*` 로만 낸다. `tool.*` 은 관측 대상 런타임(Claude Code 등)의 도구 호출로 남는다. Sensor 가 MS 실행의 건강을 `action.result` 에서 읽는 일은 실행기와 함께 정한다. **MS 는 Proposal 을 고쳐 쓰지 않고 ActionIntent 를 따로 짓는다**(P1: 고쳐 쓰면 MS 시험 37 빨강). DecisionRecord 는 실행 **직전**에 짓는다(P0: 425 실행 모두 id 같음) | Action 보고(baseline#6 5952074541). A1 의 "실행 전에 씀" 정정 — 그래도 D1 은 선다(P0) |
| BD-98 | **Guard · Health 저장소 시작**(사용자, 2026-10-02). 통로는 세션이 연 #7(Guard) · #9(Health) — baseline 이 동시에 연 #8 · #10 은 중복으로 닫음. Guard 는 action 계약을 **필수** 의존(커밋 sha 고정)으로 쓴다(입력 꼴). Health 는 경계 조사부터 — ASSESS 표시 상태의 파일은 Sensor 에 그대로 둔다 | 사용자 · §10.2 · BD-22 |
| BD-99 | **Health 경계**(Health CMD-H1, health `1d6cace`): ASSESS 표시 상태 여섯은 **모두 Sensor 에 남는다**(한 실체의 원장 지표만 읽는 탐지다). BD-52 의 "Health 가 서면 `liveness_state` 를 옮긴다" 를 **거둔다**. Health 의 ASSESS 는 옮겨 오는 것이 아니라 **상태 + 관계 위의 새 층**(원인 · 범위 가르기 — 대상 멈춤 vs 수집 멈춤, 공통 원인)이다. 입력은 Sensor state-export(+ 앞으로 관계)만, Sensor import 없음. **VERIFY**: `verification-record/1` 꼴을 받는다 — 단 `evidence` 는 **값 없이 참조**(실체 · 상태 · observed_at; 재생은 State 이력으로, PC-09 와 같은 원칙), 실체 `action:<run>:<command_id>`(BD-32), 명령 전 관측은 근거 아님, `action.result` 는 판정에 넣지 않음. **사후조건의 집은 DC `purpose.ActionSpec`**(Model 의 행동 명세 — MS `ToolSpec` 은 그 투영, BD-30 · BD-31); DC 에 넣는 일은 실행기와 함께. **S6 ↔ VERIFY 경계**: S6 = 실행됐나(L0 짝짓기, Sensor) · VERIFY = 효과가 났나(Health, S6 상태를 export 로 읽음) | Health 보고(baseline#9 5952289986) |
| BD-100 | MS ActionIntent shadow(M15)의 해석 다섯: (1) LLM 의도의 `used_keys` 는 질의 이름에 **`query:` 접두**를 붙인다(상태 키 `<역할>.<상태>` 와 꼴을 가른다). (2) 규칙 의도의 역할 가정을 없애려 DC `MSStateReader` record 에 `role` 을 싣는다(DC 작은 일). (3) DENY 된 도구 제안도 의도로 기록한다 — Guard · Validate 의 입력이다. (4) **CR 안의 맥락 결정(KEEP · REDUCE · COMPACT, 목적 `context_runtime`)은 ActionIntent 가 아니다** — 실행기로 갈 행동만 의도다. 규칙 의도(KEEP)는 내지 않는다. (5) shadow 의 계약 오류는 기록만. 사후조건의 **꼴**은 MS 술어 `[속성, 연산, 값]`(새 꼴 없음, Health 고침); **집**(DC ActionSpec 대 MS ToolSpec 의 통합)은 실행기 때 정한다 — BD-99 의 "집은 DC" 를 보류로 고친다 | MS 보고(baseline#2 5952298399) · Health 고침(baseline#9 5952307062) — 사전조건이 이미 MS ToolSpec 에 같은 꼴로 있다 |
| BD-101 | **`verification-record/1` 계약 동결**(Health CMD-H2, health `457973f`): V1 근거 참조에 `time_base`(BD-33) · V2 창이 닫혔을 때 쓸 만한 근거로 거짓인 절이 하나라도 있으면 NOT_VERIFIED(논리곱: 거짓 ∧ 모름 = 거짓) · V3 `UNRESOLVED_ENTITY` · V4 술어의 속성 참조 없음 — 넷 다 받는다. **`config.conformance`(H3)는 미룬다**: 필수 상태가 운영자 설정이 없어 NOT_APPLICABLE 이면 DC 가 이미 `complete=False` → 목적의 기본 결정으로 간다(BD-76) — 안전 길은 서 있고, 진단 상태는 그것을 읽을 소비자(운영자 화면 · Health 격리)가 생길 때 짓는다. Health 의 다음 일은 실행기(VERIFY 입력) 또는 관계 내보내기(격리 입력)가 선 뒤 | Health 보고(baseline#9 5952405967) · GUIDANCE(소비자 없는 상태는 짓지 않는다) |
| BD-102 | **`guard-result/1` · `validation-result/1` 계약 동결**(Guard CMD-G1, guard `0170f0a`): G-D1 `GuardResult.safe_action` 칸 · G-D2 `validate(intent, dc, model)`(A4 는 Model 의 ActionSpec 에 맞춤) · G-D3 `guard(intent, dc, state, model)` · G-D4 A8 기억은 호출자가 `StateView.allowed` 로 · G-D5 `rule` 은 MS 순서의 첫 걸림, `reasons` 는 모두 — 받는다. 가정 둘도 받는다: 위험 등급 기본 = `external` · `irreversible`(Model 이 바꿈) · **SAFE_ACTION 은 D(DC 불완전 · 낡음)에서만** — A5–A8 거부는 DENY 로 남겨 Policy 가 다시 제안하게 한다(닫는 쪽으로만, BD-07). **다음 순서**: F5(DC core → `DCView` 어댑터, **Guard 소유** — Guard 는 DC 코드를 import 하지 않고 DC core 데이터만 읽는다) → F4(MS 가 Arbiter 옆에서 `guard.evaluate` 를 shadow 로 부르고 결과를 DecisionRecord 에). 술어 · 인자 검사가 MS 와 두 곳에 있는 것(F1)은 대조 시험이 같음을 붙드는 동안 둔다 — 행동 명세 통합(BD-100 보류)과 함께 | Guard 보고(baseline#7 5952700090) — baseline 이 대조 102,960 경우 · 68,688 비교 · 다름 0, 시험 60 을 통합 머리에서 재현 |
| BD-103 | Guard D 의 입력(Guard CMD-G2, guard `20b4aab`): (1) **G2-D1 사실 정정을 받는다** — DC core 에는 `complete` · `missing_required` · `default_decision` 이 없다(투영 · 목적 명세에 있다). 어댑터는 DC 문맥 `to_dict()`(digest 다시 계산) + **목적 명세 데이터**를 받아 스스로 계산한다 — DC 가 계산한 `record.complete` 를 믿지 않는다. (2) **D 의 낡은 키 범위를 좁힌다**: **필수 키 ∪ 의도가 쓴 키(`used_keys`; `query:<이름>` 은 그 질의의 행 속성 전부)** 의 STALE 만 D 를 건다. 결정이 쓰지도 않고 필수도 아닌 키의 낡음은 그 행동의 근거가 아니다 — 지금처럼 문맥 전체를 보면 완전한 문맥에서도 위험 행동이 늘 SAFE_ACTION 이 된다. `allow_stale` 로 일부러 보인 값이라도 의도가 썼으면 D 를 건다(엄한 쪽) | Guard 보고(baseline#7 5952869017) — baseline 지시의 core 칸 서술이 틀렸다 |
| BD-104 | **Guard SAFE_ACTION 은 실행기 행동만**: D 가 갈아 끼울 행동(DC `default_action`)이 Model 의 실행기 행동(GuardModel 의 ActionSpec)이 아니면 — 예: 목적 `context_runtime` 의 KEEP(CR 안의 맥락 결정, BD-100) — **DENY(D)** 를 낸다. 도구 의도가 실행기 밖 행동으로 바뀌는 일을 막는다. D 가 A7 보다 앞서는 순서는 그대로(허가 없는 위험 행동도 위 규칙으로 DENY 가 된다). DC 길 결정 id 가 프로세스 안 관측 id 셈에 묶이는 성질(MS 발견 3)은 기록만 — 재생은 새 프로세스에서 같다 | MS M17 대조(baseline#2 5953144916): 모의 DC 길 464 의도 같음 432 · 다름 0 · D 32, 정해 둔 제안 960 같음 952 · 다름 0 · D 8 — D 의 SAFE_ACTION 이 KEEP 이었다 |
| BD-60 | 세션 interaction 의 참고 기준으로 [`GUIDANCE.md`](GUIDANCE.md)(사용자 제공)를 둔다. 새 규칙이 아니다 | PROTOCOL §3 지시 꼴에 왜 · 성공 기준 · 결과 분류 · wait 를 반영 |

---

## 변경 제안 (PC) — 기준선은 승인됐다. PC 는 **아직 하나도 실행하지 않았다.** 실행은 사용자가 PC 마다(또는 묶음으로) 허가한 뒤에 한다

| # | 변경 | 까닭 | 파일 (정확히) | 의존 | 위험 |
|---|---|---|---|---|---|
| PC-01 | DC 통합 시험 · 시연의 MS 신호를 `interaction.arbiter_denies` 로 바꾸고, 표본 3 을 넣는다 | 지금 실패하는 시험 1 개 (§1.1) | `DC/tests/test_integration.py` · `DC/examples/demo.py` · `DC/examples/demo_output.txt` | 없음 | 낮음. 계약 시험(PC-02)이 없으면 다시 흘러간다 |
| PC-02 | 정준 Observation 꼴 · 이름 · 검증기 | DUP-02 · BV-04 | `Telemetry/` (새 파일) · `Sensor/schema/telemetry.schema.json` · `Sensor/llmsensor/state/normalize.py` · `MS/ms/run_telemetry.py` · `MS/ms/telemetry.py` | OQ-08 · OQ-12 · OQ-13 | 중간. 두 저장소의 이름이 바뀐다 |
| PC-03 | 운영자 설정을 관측에서 뺀다. 파생 시각은 관측 입력만으로 | BV-03 | `MS/ms/usage_model.py` · `MS/ms/manager.py` · `MS/ms/runtime.py` · `DC/dc/sources.py` | BD-13 · OQ-21 | 중간. usage-model 판본이 오른다 → `replay` 의 옛 기록 |
| PC-04 | MS `role: evidence` → measurement 창 | DUP-01 | `MS/ms/model.py` · `MS/ms/manager.py` · `MS/ms/usage_model.py` · `MS/README.md` · `DC/dc/sources.py` | 없음 | 낮음 (이름만) |
| PC-05 | MS Runtime 이 `snapshot()` 대신 DC 를 쓴다 | BV-08 · GAP-06 | `MS/ms/runtime.py` · `MS/ms/cr.py` · `MS/ms/policy.py` (`replay`) · `MS/pyproject.toml` · `DC/dc/bridge.py` | OQ-08 · PC-01 · PC-03 | 중간. 낡은 상태가 None 이 되어 계획이 바뀔 수 있다(DC 시연 §8) |
| PC-06 | Sensor Verifier 를 ASSESS 평가 / DECIDE 수락 결정으로 가르고 설정 제안을 뺀다 | BV-01 | `Sensor/llmsensor/verifier.py` · `Sensor/llmsensor/pipeline.py` · `Sensor/llmsensor/cli.py` · `Sensor/README.md` · `Sensor/tests/test_sensors.py` | OQ-02 | 중간. `read` CLI 출력이 바뀐다 |
| PC-07 | DC core/provenance 분리 · `reason` 을 DC 에서 뺀다 · 투영 칸 | BD-08 | `DC/dc/model.py` · `DC/dc/builder.py` · `DC/dc/snapshot.py` · `DC/dc/bridge.py` · `DC/tests/test_dc.py` · `DC/docs/DECISION_CONTEXT.md` | OQ-18 | 중간. digest 가 바뀐다 → 옛 기록은 판본으로 가른다 |
| PC-08 | Sensor 의 DC 둘을 걷어 낸다. 참조 정책은 DC 기반 시험 정책으로 옮긴다 | DUP-04 · BV-02 · BV-11 | `Sensor/llmsensor/decision/context/__init__.py` · `Sensor/llmsensor/state/engine.py` (`decision_context`) · `Sensor/llmsensor/policy/*.py` · `Sensor/eval/ms_end_to_end.py` · `Sensor/tests/test_decision_context.py` · `Sensor/tests/test_decision.py` | BD-05 · OQ-10 | 중간. Sensor Phase 8 평가가 이것을 쓴다 |
| PC-09 | Evidence 에서 값 복사를 뺀다 (Sensor 세션) | §SCHEMA 2.5 | `Sensor/llmsensor/state/model.py` · `Sensor/llmsensor/state/engine.py` | 없음 | 낮음 |
| PC-10 | Arbiter 를 Validate / Arbitrate / Guard 로 가른다. 도구 좁히기를 Guard 로 | BV-05 · BV-06 | `MS/ms/arbiter.py` · `MS/ms/pipeline.py` · `MS/ms/policy.py` · `MS/ms/prompt.py` · Guard 저장소 (새) | OQ-04 · BD-20 | 높음. 안전 경로다. shadow 로 먼저 |
| PC-11 | RunRecord 의 `policy` 칸을 원장으로 옮긴다 | BV-04 | `MS/ms/run_telemetry.py` · `MS/ms/runtime.py` · `MS/ms/policy.py` (`replay` 입력) | BD-15 | 중간. 꼴 판본이 오른다 |
| PC-12 | 시계를 Runtime 하나로 | BV-09 | `MS/ms/telemetry.py` · `MS/ms/manager.py` | OQ-13 | 낮음 |
| PC-13 | 과업 성공 판정을 Runtime 에서 평가 하니스로 | BV-10 | `MS/ms/runtime.py` · `MS/ms/eval.py` | 없음 | 낮음 |
| PC-14 | DC 근거 종류 어휘를 Sensor 8 개로 | DUP-13 | `DC/dc/model.py` | PC-02 | 낮음 |
| PC-15 | 목적 · 행동 어휘 하나로 | DUP-06 | `DC/dc/purpose.py` · (PC-08 뒤) Sensor 쪽은 사라진다 | OQ-10 | 중간 |
| PC-16 | MS `context_pressure` → `context_budget_pressure` | DUP-11 | `MS/ms/usage_model.py` · `MS/ms/policy.py` · `DC/dc/purpose.py` | PC-15 | 낮음 |
| PC-17 | MS `tokens.context_tokens`(추정) 이름을 가른다 | SCHEMA §5 | `MS/ms/run_telemetry.py` · `MS/ms/usage_model.py` · `MS/ms/runtime.py` | PC-02 | 낮음 |
| PC-18 | 문서 그림에서 WALP 를 Arbiter/Guard 로 | BD-19 | `Sensor/docs/MS_SENSING.md` · `DC/README.md` · `DC/docs/DECISION_CONTEXT.md` · `DC/dc/__init__.py` (머리말) | 없음 | 없음 |
| PC-19 | `Proposal` → ActionIntent 꼴 | BD-09 | `MS/ms/llm.py` · `MS/ms/pipeline.py` · `MS/ms/arbiter.py` · Action 저장소 (새) | OQ-05 · BD-20 | 중간 |
| PC-20 | 수집기 결함 D1–D4 — **주인: Telemetry 세션**(BD-53). 기준선 쪽에서는 **적합성만** 본다: 429 → 계정 실체 · `<synthetic>` 을 호출에서 뺌 · 압축 사건은 런타임 자신의 행동 관측 | Sensor `MS_HEALTH_INVENTORY.md` §1 | `Sensor/llmsensor/telemetry/collect.py` · `Sensor/schema/telemetry.schema.json` | PC-02 · OQ-12 | Sensor 세션 소관 |
| PC-21 | MS 계획 문서를 BD-21(CR 자리) · BD-24(A0–A8 배분)에 맞춘다 | 앞선 결정을 대신했다 | `MS/docs/계획.md` · `MS/docs/역할.md` · `MS/README.md` · `MS/ms/arbiter.py` (머리말의 ⑦ 배분) | 없음 | 낮음 (문서) |
| PC-22 | Sensor 문서의 `resource_state` 읽기를 BD-39 로 고친다. 규칙은 `resource-state-v2` | BD-39 | `Sensor/docs/MS_SENSING.md` §6 · `Sensor/docs/MS_HEALTH_INVENTORY.md` §4 · `Sensor/llmsensor/state/rules.py` · `Sensor/llmsensor/sensing/cost/__init__.py` · `Sensor/tests/test_state.py` | PC-20 (D3) · BD-13 | 중간. 예산 주인이 Model 로 옮겨 간다 |
| PC-23 | DC 목적에 질의형 선택을 더하고, CR 은 DC 만 받는다 | BD-26 · BV-07 | `DC/dc/purpose.py` · `DC/dc/builder.py` · `DC/dc/model.py` · `MS/ms/cr.py` · `MS/ms/query.py` | PC-05 · PC-07 | 중간 |

### PC 실행 순서 (BASELINE §10.2 의 의존 그래프를 따른다)

| 단계 | PC | 맡을 곳 | 앞 단계에 기대는 까닭 |
|---|---|---|---|
| 0 | **브랜치 합치기 X-1 → X-3 → X-2** (BASELINE §13.3) · PC-18 · PC-21 · PC-22(문서 부분) | 사용자(합치기) · DC · Sensor · MS 세션 | 같은 파일을 여러 브랜치가 바꿨다. 합치기 전에 새 일을 얹으면 충돌이 커진다 |
| 1 | **PC-02** Telemetry 계약 마무리 (L0 원장은 섰다 — 남은 것: MS 자기 관측 `kind=self` · 실체 id(BD-32) · BD-44 대응 · MS Recorder 배선) | Telemetry 세션 | 모든 이름 · 실체 id · 시간 기준이 여기서 굳는다 |
| 2 | PC-03 · PC-04 · PC-12 · PC-14 · PC-16 · PC-17 · PC-09 · PC-20 · PC-22(규칙) | MS · DC · Sensor 세션 | PC-02 의 이름 · 실체 id 를 쓴다 |
| 3 | PC-07 → PC-05 → PC-23 · PC-15 | DC 다음에 MS | DC 꼴이 먼저 굳어야 MS 가 배선한다 |
| 4 | PC-06 · PC-08 · PC-13 · PC-11 | Sensor · Health(새) · MS | DC 기준 구현 · 원장 꼴이 선 뒤 |
| 5 | PC-19 | Action (새) | ActionIntent 꼴 |
| 6 | PC-10 (shadow 먼저, 그다음 enforce) | Guard (새) | Action 꼴 + OQ-17 (enforce 전에) |

### PC 진행 현황 (2026-10-02 다시 확인)

| PC | 현황 | 어디 |
|---|---|---|
| PC-01 | **됨** · 통합됨 (X-2 해소) | DC 통합 8c4d0e0 |
| PC-02 | **진행 중** — L0 원장 · 출처 종류 · compat · `action.*` 사건 | Telemetry `jolly-einstein` |
| PC-05 | **됨** · 통합됨 (이음매 방식, 출처는 DecisionRecord) — 아직 기본값은 `snapshot()` | MS 통합 43f4294 + DC 통합 8c4d0e0 |
| PC-11 | **됨** · 통합됨 | MS `jolly-einstein` c0733de → 통합 43f4294 |
| PC-20 | 설계만 — D1–D4 는 입력 계약 조건으로 넘김 | Sensor `nice-wright` 24265da |
| 나머지 | 시작 안 함 | |
| (4 회차) PC-03 · PC-04 · PC-12 · PC-13 | **됨** · 통합됨 | MS `39e2b59` |
| (4 회차) PC-22 (`resource-state-v2`) | **됨** · 통합됨 | Sensor `38892cd` (nice-wright `597e74b`) |
| (4 회차) PC-20 (D1–D4) | **됨** · 통합됨 | Telemetry `20dc8df` · Sensor `38892cd` (jolly) |
| (4 회차) PC-08 · PC-14 | **됨** · 통합됨 | DC `c68ebfa` · Sensor `38892cd` |
