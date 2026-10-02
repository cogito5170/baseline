# DECISION LOG (baseline-0.1)

상태 표시: **ADOPTED (사용자, 날짜)** = 사용자가 이미 정한 것을 옮겨 적음 · **PROPOSED** = 이 기준선의 제안, 승인 전.
틀: 결정 · 까닭 · 검토한 대안 · 버린 대안 · 근거 · 결과.

---

### BD-01 정규 층 순서 L1–L11 — PROPOSED
- **결정.** Observe → Measure → Estimate → Assess → Contextualize → Decide → Validate → Arbitrate → Guard → Execute → Verify. 되먹임은 Observation 으로만 한다.
- **까닭.** 지금 세 저장소의 그림은 같은 방향이다. 다만 진단 · 결정(Sensor Verifier), 판정 · 허가(MS Arbiter)를 합쳐 두었다.
- **대안.** (a) MS 의 세 층(Telemetry · State · Policy). (b) Sensor 파이프라인(센서 → Q → 판정기). (c) 사용자가 준 고리(OBSERVE … VERIFY).
- **버림.** (a) 진단 · 안전이 들어설 자리가 없다. (b) BV-01. (c)는 버리지 않았다. ESTIMATE 를 Measure 와 Estimate 로 가른 것만 다르다(BD-03).
- **근거.** BASELINE §1 · §6. NASA 의 "진단 ≠ 결정" 원칙(원문 재확인 못 함, OQ-20).
- **결과.** Guard · Action · Assess 의 자리가 생긴다. 그 자리는 지금 비어 있다(GAP-01–05).

### BD-02 Observation 은 뜻의 단위이고, Telemetry 는 운반 꼴이다 — PROPOSED
- **까닭.** MS 의 RunRecord 와 Sensor v3 는 같은 관측을 다른 꼴로 나른다. 꼴을 뜻으로 삼으면 꼴이 바뀔 때마다 뜻이 흔들린다.
- **대안.** Telemetry = State 의 입력 꼴 하나. **버림** — 두 저장소의 꼴이 실제로 다르다(DUP-02).
- **결과.** 정준 Observation 이름 집합이 필요하다(SCHEMA §5, OQ-08).

### BD-03 Measurement 를 따로 층으로 둔다 — PROPOSED
- **까닭.** Sensor 는 상태 규칙의 입력을 지표로만 제한하고 시험으로 지킨다. 원 관측이 상태 규칙에 바로 들어가면, 같은 산술이 규칙마다 되풀이된다.
- **근거.** `Sensor/llmsensor/state/registry.py` `check()` · `docs/STATE_MODEL.md` §2.
- **결과.** MS 의 evidence 창(집계)은 Measurement 다(BD-06).

### BD-04 Assess 는 Decide 와 다른 층이다. 건강 · 고장은 State 다 — PROPOSED
- **까닭.** 진단과 결정은 다른 기능이다. 건강도 유효성 · 신선도 · 근거 · 생애가 필요하다. 그래서 같은 State 기계를 쓰고, 소유 규칙만 L4 에 둔다.
- **대안.** (a) 건강 저장소를 따로 둔다. (b) 판정기처럼 합친다.
- **버림.** (a) 생애 · 신선도 기계가 둘이 된다. (b) BV-01.
- **결과.** Sensor `verifier.py` 를 셋으로 가른다: Q 융합 = L4 · ACCEPT/RETRY = L6 의 `acceptance` 목적 · 설정 제안 = 고리 밖 (PC-06).

### BD-05 DC 저장소를 Decision Context 의 기준 구현으로 삼는다 — PROPOSED
- **까닭.** 네 구현 가운데 불변식(I1–I7)이 가장 많고, 변이 15 가지로 시험을 확인했다. 시계를 읽지 않는다. 다른 저장소를 import 하지 않는다.
- **대안.** Sensor `decision/context`. 장점: `allow_stale` 명시 · ContextStore · explain. 단점: 근거 사슬을 문맥마다 복사한다(6–22 KB).
- **버림.** Sensor 의 것을 기준으로 삼는 안 · MS `snapshot()` 을 기준으로 삼는 안(신선도 · 근거 없음).
- **결과.** Sensor 의 장점(`allow_stale` · ContextStore)은 DC 로 옮길 후보다. Sensor 의 두 DC 는 걷어 낸다(PC-08). 목적 어휘 통일은 OQ-10.

### BD-06 Evidence 는 참조다. MS 의 "evidence" 는 Measurement 창으로 부른다 — PROPOSED
- **근거.** DUP-01. MS `model.py` 의 `role: evidence` 는 원 측정을 창으로 모은 것이다. Sensor · DC 의 evidence 는 id 참조다.
- **결과.** 이름만 바뀐다. 동작은 같다(PC-04).

### BD-07 Guard 는 Policy 와 독립이다. 닫는 쪽으로만. 지금 상태를 읽는다 — 일부 ADOPTED
- **ADOPTED (사용자, 2026-10-02, MS `docs/계획.md` §3).** Arbitrate = 선택 · Guard = 허가. `GUARD_MODE` shadow/enforce 는 모드만 바꾼다.
  불변식은 빼지 못한다. 훅이 터지면 shadow 는 기록하고 계속, enforce 는 명시적으로 거부한다.
- **PROPOSED (이 기준선).** Guard 는 Policy · CR 을 import 하지 않는 **별도 부품**이다(저장소도 따로, BD-20). 안전 동작을 스스로 낼 수 있다.
  프롬프트의 도구 좁히기(BV-05)도 Guard 의 규칙으로 옮긴다.
- **까닭.** 런타임 보증의 독립성. 명목 정책과 고장 모드를 나누지 않는다.

### BD-08 DC 는 State Store 가 아니다. core 와 provenance 로 가른다 — PROPOSED
- **근거.** SCHEMA §4.4: 정책이 읽는 것은 DC 의 ~10 %. `reason` 이 core 만큼 크다. 그 안에 원 수치가 새어 든다.
- **결과.** PC-07.

### BD-09 LLM 은 층이 아니라 Policy 의 실행기다 — PROPOSED
- **까닭.** 결정론으로 충분한 곳에는 결정론을 둔다. MS `계획.md` 도 "LLM 을 빼도 구조가 남는다" 고 적었다.
- **결과.** LLM 출력은 ActionIntent 다(MS `Proposal` 을 일반화, 사용자 순서 ⑥ 과 같다).

### BD-10 문턱은 근거 종류가 선언된 것만 쓴다 — ADOPTED (Sensor 의 관행)
- 근거가 없으면 상태는 NOT_APPLICABLE 또는 UNKNOWN 이다. 문턱을 지어내지 않는다(`Sensor/llmsensor/state/config.py` 머리말).

### BD-11 캐시 규칙 — PROPOSED
- 잃었을 때 행동이 바뀌면 캐시가 아니다. 캐시는 권위가 없다. provider 프롬프트 캐시(바이트)와 결정 재사용(뜻)은 다른 캐시다(MS `계획.md` §0 과 같다).

### BD-12 범위와 생애를 칸이 아니라 저장소로 드러낸다 — PROPOSED
- BASELINE §4. 요금 한도는 **계정** 범위다(Sensor 조사).

### BD-13 운영자 설정은 관측이 아니다 — PROPOSED
- **근거.** BV-03. 예산을 텔레메트리로 넣은 탓에 MS 파생 상태의 시각이 세션을 연 시각에 묶인다. DC 문서도 이것을 "알려진 한계" 로 적었다.
- **결과.** 예산 · SLO 는 Model(운영자 가정, 판본) 또는 요청 Constraint 다. **예산의 주인은 하나다**: 지금은 Sensor `cost_budget_usd` · MS `token_budget` · DC `max_cost_usd` 셋이 따로 있다 (OQ-21).

### BD-14 사건 구동, digest 로 다시 쓰기 — PROPOSED
- DATA_FLOW §4.

### BD-15 결정의 내용은 원장에, 텔레메트리에는 `decision_ref` 만 — PROPOSED
- BV-04. 재현(`ms.policy.replay`)은 원장을 읽는다.

### BD-16 자율 부품의 자기 관측도 Observation 이다 — PROPOSED
- `arbiter_denies` · `proposal_invalid` · Guard 거부 · 사람의 고침. 실체는 그 부품이다. 판정의 내용이 아니라 **결과의 수**만 관측이다.

### BD-17 관계 술어 — PROPOSED
- 채택: observes · derived_from · depends_on(유형) · affects · requires · conflicts_with(유형) · contains · uses · executed_by · runs_on.
  버림: measures · evidenced_by · degrades · constrains · enables. 보류: supports. 까닭은 SEMANTIC §4.

### BD-18 인코딩을 고르지 않는다 — PROPOSED
- 평가 기준만 적는다(SCHEMA §6). "표준 라이브러리만" 규칙과 부딪힌다 → OQ-19.

### BD-19 사용자가 이미 정한 것을 옮긴다 — ADOPTED (사용자, 2026-10-02)
- WALP 는 쓰지 않는다. Sensor 출력은 텔레메트리로만 받는다. Verifier 의 판정 · 정책 제안은 배선하지 않는다. CR 은 입출력 계약이 먼저이고
  자리는 그다음이다. 순서는 ① CR 분리 → ② Sensor→Telemetry → ③ Telemetry→DC → ④ DC→CR → ⑤ Policy → ⑥ Action Intent →
  ⑦ Validate/Arbitrate/Guard → ⑧ Shadow → ⑨ API 평가. (출처: `MS/docs/계획.md` §2–§3)
- 이 기준선의 층 순서(BD-01)는 이 순서와 부딪히지 않는다.

### BD-20 저장소 구성 — PROPOSED (사용자의 시퀀싱 질문과 묶임)
- **결정.** 시퀀싱 저장소보다 먼저: **Telemetry 를 채운다**(정준 Observation 꼴 · 이름 · 검증기). 새로 셋을 둔다: **Action**(L10) · **Guard**(L7–L9) ·
  **Health**(L4 · L11). 계약(어휘 · 실체 id · 시간 기준 · 의존 그래프)은 **baseline** 이 기계가 읽는 꼴로 갖는다. 새 저장소를 더 만들지 않는다.
- **까닭.** Guard 는 Policy 와 고장 모드를 나누지 않아야 한다 → 저장소 분리. Action 이 없으면 Verify · `action_state` · S6 이 설 자리가 없다.
  Health 가 없으면 진단이 다시 Sensor 판정기와 MS 품질 상태에 흩어진다.
- **대안.** (a) Guard · Action 을 MS 안에 둔다. (b) Model Registry 를 따로 둔다. (c) Verify 를 따로 둔다.
- **버림.** (a) 지금의 BV-05 · 06 이 굳는다. (b) 계약은 baseline 이 가질 수 있다 — 저장소만 늘어난다. (c) 검증은 Assess 와 같은 기계(기대 대 관측)를 쓴다 → Health 에.
- **결과.** OQ-02(Health 를 따로 둘지), OQ-22(시퀀싱의 뜻).

---

## 승인 뒤의 변경 제안 (PC) — 지금은 하나도 하지 않았다

| # | 변경 | 까닭 | 파일 (정확히) | 의존 | 위험 |
|---|---|---|---|---|---|
| PC-01 | DC 통합 시험 · 시연의 MS 신호를 `interaction.arbiter_denies` 로 바꾸고, 표본 3 을 넣는다 | 지금 실패하는 시험 1 개 (§1.1) | `DC/tests/test_integration.py` · `DC/examples/demo.py` · `DC/examples/demo_output.txt` | 없음 | 낮음. 계약 시험(PC-02)이 없으면 다시 흘러간다 |
| PC-02 | 정준 Observation 꼴 · 이름 · 검증기 | DUP-02 · BV-04 | `Telemetry/` (새 파일) · `Sensor/schema/telemetry.schema.json` · `Sensor/llmsensor/state/normalize.py` · `MS/ms/run_telemetry.py` · `MS/ms/telemetry.py` | OQ-08 · OQ-12 · OQ-13 | 중간. 두 저장소의 이름이 바뀐다 |
| PC-03 | 운영자 설정을 관측에서 뺀다. 파생 시각은 관측 입력만으로 | BV-03 | `MS/ms/usage_model.py` · `MS/ms/manager.py` · `MS/ms/runtime.py` · `DC/dc/sources.py` | BD-13 · OQ-21 | 중간. usage-model 판본이 오른다 → `replay` 의 옛 기록 |
| PC-04 | MS `role: evidence` → measurement 창 | DUP-01 | `MS/ms/model.py` · `MS/ms/manager.py` · `MS/ms/usage_model.py` · `MS/README.md` · `DC/dc/sources.py` | 없음 | 낮음 (이름만) |
| PC-05 | MS Runtime 이 `snapshot()` 대신 DC 를 쓴다 | BV-08 · GAP-06 | `MS/ms/runtime.py` · `MS/ms/cr.py` · `MS/ms/policy.py` (`replay`) · `MS/pyproject.toml` · `DC/dc/bridge.py` | OQ-08 · PC-01 · PC-03 | 중간. 낡은 상태가 None 이 되어 계획이 바뀔 수 있다(DC 시연 §8) |
| PC-06 | Sensor Verifier 를 L4 평가 / L6 수락 결정으로 가르고 설정 제안을 뺀다 | BV-01 | `Sensor/llmsensor/verifier.py` · `Sensor/llmsensor/pipeline.py` · `Sensor/llmsensor/cli.py` · `Sensor/README.md` · `Sensor/tests/test_sensors.py` | OQ-02 | 중간. `read` CLI 출력이 바뀐다 |
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
| PC-18 | Sensor 문서 그림에서 WALP 를 Arbiter/Guard 로 | BD-19 | `Sensor/docs/MS_SENSING.md` | 없음 | 없음 |
| PC-19 | `Proposal` → ActionIntent 꼴 | BD-09 | `MS/ms/llm.py` · `MS/ms/pipeline.py` · `MS/ms/arbiter.py` · Action 저장소 (새) | OQ-05 · BD-20 | 중간 |
| PC-20 | Sensor 수집기 결함 D1–D4 (Sensor 세션이 이미 계획) — 기준선 쪽에서는 **적합성만** 본다: 429 → 계정 실체 · `<synthetic>` 을 호출에서 뺌 · 압축 사건은 런타임 자신의 행동 관측 | Sensor `MS_HEALTH_INVENTORY.md` §1 | `Sensor/llmsensor/telemetry/collect.py` · `Sensor/schema/telemetry.schema.json` | PC-02 · OQ-12 | Sensor 세션 소관 |
