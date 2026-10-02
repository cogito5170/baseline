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
| PC-09 | Evidence 에서 값 복사를 뺀다 | §SCHEMA 2.5 | `Sensor/llmsensor/state/model.py` · `Sensor/llmsensor/state/engine.py` | 없음 | 낮음 |
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
| PC-20 | Sensor 수집기 결함 D1–D4 (Sensor 세션이 이미 계획) — 기준선 쪽에서는 **적합성만** 본다: 429 → 계정 실체 · `<synthetic>` 을 호출에서 뺌 · 압축 사건은 런타임 자신의 행동 관측 | Sensor `MS_HEALTH_INVENTORY.md` §1 | `Sensor/llmsensor/telemetry/collect.py` · `Sensor/schema/telemetry.schema.json` | PC-02 · OQ-12 | Sensor 세션 소관 |
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
| PC-01 | **됨** (두 브랜치에서 따로 — 충돌 X-2) | DC `jolly-einstein` 50b4be7 · `nifty-volta` 48b9908 |
| PC-02 | **진행 중** — L0 원장 · 출처 종류 · compat · `action.*` 사건 | Telemetry `jolly-einstein` |
| PC-05 | **됨** (이음매 방식) — 아직 기본값은 `snapshot()` | MS `nifty-volta` ee941ae + DC `nifty-volta` 48b9908 |
| PC-11 | **됨** | MS `jolly-einstein` c0733de |
| PC-20 | 설계만 — D1–D4 는 입력 계약 조건으로 넘김 | Sensor `nice-wright` 24265da |
| 나머지 | 시작 안 함 | |
