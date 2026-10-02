# AUTONOMY ARCHITECTURE BASELINE — FREEZE PHASE

| 항목 | 값 |
|---|---|
| 판본 | **baseline-1.0 (승인)** — 0.1 제안을 사용자가 2026-10-02 에 승인 |
| 날짜 | 2026-10-02 |
| 조사 커밋 (§1) | Sensor `dd779e0` · DC `e277144` · MS `06fcb09` · Telemetry (커밋 없음) · baseline `1539228` |
| 적합성 확인 커밋 (§13) | 2026-10-02 다시 확인. 저장소마다 브랜치가 여럿이다 — §13.1 |
| 상태 | **ACCEPTED.** 승인 시험 25 문항 모두 A (§11). 모든 브랜치는 이 기준선을 따른다. 변경 제안(PC)은 사용자가 허가한 것만 실행한다 |
| 남은 미결 | OQ-17 (안전 동작 순서 — Guard enforce 전에) · OQ-19 (인코딩 — 프로세스 간 전송 전에). 승인은 막지 않는다 (OPEN_QUESTIONS 머리) |

함께 읽는 문서: [`SEMANTIC_MODEL.md`](SEMANTIC_MODEL.md) (낱말의 뜻) · [`DATA_FLOW.md`](DATA_FLOW.md) (흐름과 실패 흐름) ·
[`SCHEMA_PROPOSAL.md`](SCHEMA_PROPOSAL.md) (칸 · 소유 · 생애 · 최소성) · [`DECISION_LOG.md`](DECISION_LOG.md) (결정 BD-xx) ·
[`OPEN_QUESTIONS.md`](OPEN_QUESTIONS.md) (미결 OQ-xx).

이 문서에서 쓰는 꼬리표: **BV** 경계 위반 · **DUP** 중복 개념 · **GAP** 빠진 것 · **PC** 승인 뒤의 변경 제안 · **BD** 결정 · **OQ** 미결 질문.

---

## 0. 참조한 원칙과 그 한계

**이 세션에서는 원문을 다시 읽지 못했다.** learn.microsoft.com · nasa.gov · ntrs.nasa.gov · swehb.nasa.gov · arxiv.org 모두 이 컨테이너의
네트워크 정책에 막혔다(2026-10-02, curl 응답 없음). Sensor 저장소의 앞선 조사(`Sensor/docs/MS_HEALTH_INVENTORY.md` §5)도 같은 차단을
기록했다. 아래 원칙은 **널리 알려진 아키텍처 원칙을 이름으로 인용한 것**이다. 문헌의 특정 쪽수나 문구에 기대지 않는다. 원문 확인은
BD-38 에 남긴다.

| 출처 계열 | 가져온 원칙 | 이 기준선에서의 자리 |
|---|---|---|
| NASA FDIR · ISHM · 모형 기반 진단 | 탐지(detection) → 격리(isolation) → 복구(recovery)는 다른 기능이다. **진단은 결정이 아니다** | ASSESS 와 DECIDE 를 떼었다 (BD-04) |
| NASA 모형 기반 자율 (상태 추정 / 실행 분리) | 상태 추정은 모형을 쓰고, 명령은 실행층(executive)을 지난다 | M(Model) 은 실행 중 읽기 전용이다. Action 은 EXECUTE 에서만 실행된다 |
| NASA 런타임 보증 (Simplex 계열) | 명목 제어기와 안전 감시기는 독립이다. 감시기는 **닫는 쪽으로만** 개입하고 안전 동작으로 전환한다 | GUARD 를 Policy 와 다른 부품으로 둔다 (BD-07) |
| NASA cFS Limit Checker · F´ Health (Sensor 앞선 조사가 원문을 읽었음) | 문턱을 넘으면 **사건**이 생긴다. 대응은 따로 시작된다. 문턱은 미리 설정한 것이다 | 상태 규칙에 근거 종류(Basis)를 붙인다. 문턱 출처가 없으면 NOT_APPLICABLE · UNKNOWN (BD-10) |
| Azure 상태 있는 AI · Agent Framework 상태 모형 | 상태에는 범위(scope)와 생애(lifecycle)가 있다. 영속 상태와 일시 맥락은 다르다 | §4 저장소 · 범위 표 (BD-12) |
| Microsoft Research 맥락 공학 · 압축 | 지금 과업에 맞는 맥락만 넘긴다. 줄일 수 있으면 줄인다 | CONTEXTUALIZE Decision Context 의 최소성 (BD-08, SCHEMA §4) |
| Azure 오케스트레이션 패턴 | 결정론적 흐름으로 충분하면 결정론으로 둔다. 할 수 있다는 이유로 에이전트 층을 더하지 않는다 | LLM 은 Policy 를 돌리는 실행기의 하나일 뿐이다 (BD-09) |
| Azure (상태 저장 ≠ 맥락 선택) | 상태를 저장하는 일과 맥락을 고르는 일은 다른 관심사다 | State Store(ESTIMATE) 와 Context Selection(CONTEXTUALIZE) 을 가른다 (BD-08) |

---

## 1. 현재 시스템 재구성

> 이 절은 baseline-0.1 조사 시점(머리 표의 "조사 커밋")의 기록이다. 그 뒤의 변화와 적합성은 §13 에 있다.

### 1.1 저장소 · 브랜치 · 시험 (읽기 전용으로 확인)

| 저장소 | 브랜치 | 머리 | 시험 (`PYTHONDONTWRITEBYTECODE=1`, 파일 변경 없음) | 의존 |
|---|---|---|---|---|
| Sensor (`llmsensor`) | `claude/gracious-meitner-vp49xe`, `claude/nice-wright-50oyvm` — **같은 머리** | dd779e0 | 113 통과 | 표준 라이브러리만 |
| DC | `claude/gracious-meitner-vp49xe`, `claude/nifty-volta-3u5ygl` — **같은 머리** | e277144 | 49 중 **1 실패** (`test_integration.WithMS.test_policy_state_equals_ms_snapshot_when_fresh`) | 표준 라이브러리만 · Sensor/MS 는 덕 타이핑 |
| MS | `claude/gracious-meitner-vp49xe`, `claude/eloquent-turing-m33zjw` — **같은 머리** | 06fcb09 | 102 통과 | 표준 라이브러리만 |
| Telemetry | `claude/gracious-meitner-vp49xe` | 커밋 없음 | — | — |
| baseline | `claude/gracious-meitner-vp49xe`, `main` | 1539228 | — | — |

DC 의 실패는 **저장소 사이 계약이 흘러간 증거**다. MS 가 신호 `interaction.walp_denies` 를 `interaction.arbiter_denies` 로 바꿨다
(usage-model-3, 2026-10-02). MS 는 품질 상태에 표본 3 개 이상도 요구한다(usage-model-2). DC 의 통합 시험과 시연은 옛 신호를 쓴다
(`DC/tests/test_integration.py:93,160`, `DC/examples/demo.py:40`). 두 저장소를 함께 지키는 계약이 없어서 생긴 일이다 → GAP-10, PC-01.

### 1.2 개념별 실제 구현 위치

| 개념 | Sensor | MS | DC | 비고 |
|---|---|---|---|---|
| 관측 수집 | `telemetry/collect.py` (cc_jsonl · cc_stream · sweagent), `sensors/*.py` (Reading), `trace.py` | `providers/*` (사용량 정규화), `tools.py` (도구 결과 → 신호) | — | |
| 텔레메트리 꼴 | `schema/telemetry.schema.json` (llm-telemetry/v3: model_call · tool_call · run, `unobserved` · `reported_null`) | `telemetry.Telemetry` (source · entity · signal · value · ts), `run_telemetry.RunRecord` (ms-run-telemetry-2) | — | **꼴이 둘이다** (DUP-02) |
| 측정 · 파생 값 | `state/metrics.py` (Metric, 38 개), `telemetry/derive.py` | `manager.evidence` 창 (last · mean · sum · max, `__n` · `__sum`) | — | |
| 상태 | `state/engine.py` StateEngine (상태 12 개, 이력 · 전이 · 생애) | `manager.StateManager` + `graph.StateGraph` (usage 파생 상태 8 개 + 세계 모형) | — (읽기만) | **상태 층이 둘이다** (DUP-03) |
| 모형 | `state/registry.py` · `rules.py` · `config.py` · `model.py` (PerformanceModel) · `fusion.py` (OutcomeModel) | `model.py` (Model · Binding · Derivation · RelationshipSpec), `usage_model.py` | `purpose.py` (목적 명세) | "Model" 의 뜻이 셋이다 (DUP-07) |
| 관계 | `state/model.Relationship` (uses · executed_by · runs_on) | `RelationshipSpec` + `graph.edges` (cardinality 있음) | — | |
| 근거 (Evidence) | `state/model.Evidence` (ref · level), `explain()` | **"evidence" = 원 측정 창**(뜻이 다르다) | `StateRecord.evidence_refs` | 이름 충돌 (DUP-01) |
| 건강 · 고장 판정 | `sensors/*` Reading (OK · SUSPECT · FAULT · UNKNOWN), `residual.py`, `fusion.py` Q, `verifier.py` Verdict | `answer_reliability` · `correction_rate` · `retry_pressure` · `tool_churn` (정책 실행기의 건강) | — | 독립된 층이 없다 (GAP-01) |
| Decision Context | ① `engine.decision_context(run)` dict ② `decision/context` ContextBuilder (목적 4) | ③ `usage_model.snapshot()` (Runtime 이 실제로 쓰는 것) | ④ DecisionContextBuilder (목적 4, 불변식 I1–I7) | **구현이 넷이다** (DUP-04) |
| LLM 맥락 (CR) | — | `cr.py` · `context.py` · `prompt.py` · `query.py` | — | DC 를 거치지 않고 그래프를 직접 질의한다 (BV-07) |
| 정책 | `policy/*` (참조 정책, "MS 정책 아님"), `verifier.py` 의 `policy` 제안 | `policy.py` (선택기 → 이제 CR 내부로 이름을 고침), `ExplicitProvider`, LLM `Proposal` | — | |
| 중재 | `policy._pick` (정책 안의 선호 순서) | `arbiter.Arbiter` A0–A8 (판정 · 허가를 섞음) | — | 후보 여럿 사이의 중재는 **어디에도 없다** (GAP-02) |
| 안전 · Guard | — | A6 (사전조건 · ttl) · A7 (허가) · 예외면 DENY, 프롬프트의 `tool_permission` 좁히기 | 제약을 싣기만 하고 평가하지 않는다 | Guard 가 따로 없다 (GAP-03) |
| 행동 · 실행기 | **없음** ("실행하는 주체가 없다", `MS_HEALTH_INVENTORY.md`) | `tools.ToolSpec` (risk, 사전조건, handler → 텔레메트리), 호출 자리 하나 | 가능 행동 목록만 | GAP-04 |
| 검증 | `ExternalOutcomeSensor`, `quality_state` (외부 라벨) | `check_success` (평가용 그래프 술어), `tool_success` | — | 행동의 기대 효과 검증이 없다 (GAP-05) |
| 런타임 | 없음 (엔진은 시계를 읽지 않는다) | `runtime.Runtime.handle` · `pipeline.Pipeline` · 원장 JSONL | 빌더는 시계를 읽지 않는다 | |
| 캐시 | (Health Endpoint "cache the status" 를 원칙으로만 인용) | provider 프롬프트 캐시 (`cache_boundary` · `prefix_hash`), 결정 재사용은 계획만 | — | |
| 직렬화 | JSON Schema 2020-12, 결정 문맥 `_digest` (`default=str`, 16 hex) | `RunRecord.to_json`, OTel 이름, 모형 JSON | 정준 JSON + sha256 (`dc-` + 16 hex), `from_dict` 가 검증 | 해시 규칙이 둘이다 (DUP-09) |
| 전송 | 파일 · stream-json 읽기 | `HttpTransport` (표준 라이브러리), `claude -p` 하위 프로세스 | — | 부품 사이 전송은 없다(모두 프로세스 안) |

### 1.3 문서가 말하는 의도 구조 (세 갈래)

```
Sensor (MS_SENSING.md):  Telemetry → Observation → Metric → State → DC → Policy(참조) → LLM Context → LLM → WALP → Action → Telemetry
DC (README):             Telemetry → State → DC → Policy
MS (계획.md, 2026-10-02 사용자 결정):
                         SENSOR(텔레메트리만) → STATE/DC → CR → POLICY → ACTION INTENT → VALIDATE → ARBITRATE → GUARD → EXECUTOR
                         + Runtime Telemetry → 다음 DC.   순서 ① CR 분리 ✅ ② Sensor→Telemetry ③ Telemetry→DC ④ DC→CR ⑤ Policy
                         ⑥ Action Intent ⑦ Validate/Arbitrate/Guard ⑧ Claude Code Shadow ⑨ API evaluation
```

세 그림은 같은 방향을 가리키지만 **세 곳이 다르다.** (a) Sensor 그림에는 아직 WALP 가 남아 있다(MS 는 쓰지 않기로 했다). (b) CR 의
자리가 다르다: Sensor 그림에서는 "정책의 일", MS 그림에서는 DC 와 Policy 사이의 층이다 → BD-21. (c) Sensor 는 "MS" 라는 낱말을
"MS 센싱 확장" 의 뜻으로 쓴다 → DUP-10.

### 1.4 지도 — 현재 → 실제 → 의도 → 빠진 것 → 중복 → 위반

```
CURRENT SYSTEM          세 저장소 · 프로세스 하나 · 메모리 안의 상태 · 저장소 사이 배선 없음(DC 는 어댑터로 읽기만)
    ↓
actual implementation   관측 꼴 2 · 상태 층 2 · DC 4 · 정책 3 갈래(MS 선택기 · Sensor 참조 · Verifier 제안) · Arbiter 1(판정+허가) · 실행기 1(MS 도구)
    ↓
intended architecture   §2 의 OBSERVE–VERIFY (아래). MS 계획 ①–⑨ 과 같은 방향
    ↓
gaps                    GAP-01 Assessment 층 · 02 다후보 중재 · 03 Guard · 04 행동 실행기/ActionIntent · 05 검증 · 06 DC 가 MS 에 미배선
                        · 07 질의형 DC 선택 · 08 실체 id · 시간 기준 통일 · 09 영속성 · 10 공용 계약(Telemetry 저장소 비어 있음)
                        · 11 교차 소스 일관성 · 12 고장 모드 모형 · 13 동시성 · 14 신뢰도 표현 · 15 liveness
    ↓
duplications           DUP-01–DUP-12 (§7)
    ↓
boundary violations     BV-01–BV-12 (§6)
```

---

## 2. 정규 아키텍처

> 단계 이름(OBSERVE … VERIFY)은 **기능 단계**다. 코드와 다른 저장소 문서가 쓰는 **층 번호 L0–L5**(L0 Telemetry · L1 Sensor · L2 State · L3 DC ·
> L4 Policy · L5 Action)는 저장소 층이다. 둘의 대응은 §10.1 에 있다 (BD-43). 이 기준선은 L 번호를 다른 뜻으로 쓰지 않는다.

```
                 ┌──────────────── M · MODEL (판본이 있다. 실행 중에는 읽기만 한다) ────────────────┐
                 │ 실체 유형 · 속성 · 값 집합 · 규칙(id@ver, basis) · 바인딩 · TTL · 운영자 가정(config) │
                 │ 목적(purpose) · 행동 명세(requires · pre/postcondition · risk) · 고장 모드(affects) │
                 │ 관계 유형 · 안전 제약 · 안전 동작(safe action) 순서                                │
                 └─────▲──────────▲──────────▲──────────▲──────────▲──────────▲──────────▲────────────┘
                       │          │          │          │          │          │          │
SOURCE ─► OBSERVE ─► MEASURE ─► ESTIMATE ─► ASSESS ─► CONTEXTUALIZE ─► DECIDE
 세계 · 런타임 Observation     Measurement   State(명목)    State(건강/고장) DecisionContext     ActionIntent[]
 provider ·   (Telemetry 는    (Metric)      ┌────────── STATE STORE ──────────┐ (고정 · id)       (Policy 판본)
 도구 · 사람   그 전송 꼴)                    │ current · history · transitions │      │
 · 설정은 M 로                               │ RELATIONSHIP STORE (실체 간선)    │      │
                                            │ EVIDENCE = 출처 연결(복사 아님)   │      │
                                            └───────────────▲─────────────────┘      ▼
                                                            │ 직접 읽기     VALIDATE ─► ARBITRATE ─► GUARD
                                                            └──────────────── (지금 상태) ───────────────┘  │ 허가 / 거부 / 안전 동작
                                                                                                          ▼
         ◄────────── 결과 · 자기 텔레메트리는 Observation 으로 돌아온다 ◄── VERIFY ◄── EXECUTE (ActionCommand → Executor → Outcome)

DECISION LEDGER (덧붙이기만): dc_id · policy@ver · intents · validate · arbitrate · guard · command · outcome refs · verification
RUNTIME (기반 시설): 시계('지금' 주입) · 일정 · 저장소 접근 · 전송 · 배차 · 원장 · 생애 관리 — 뜻을 정하지 않는다
```

**고리 하나가 아니라 두 길이다.** 명목 고리는 OBSERVE → VERIFY 이다. 안전 감시는 GUARD 가 **State Store 를 직접** 읽는 별도의 길이다. 안전
감시는 명목 고리를 기다리지 않고 안전 동작을 낼 수 있다 (BD-07).

---

## 3. 층 정의 — 책임과 금지

| 층 | 묻는 것 | 책임 | **금지** | 입력 → 출력 | 지금 코드에서 |
|---|---|---|---|---|---|
| SOURCE | — | 세계 · 런타임 · provider · 도구 · 사람 | — | — | — |
| OBSERVE | 무엇이 관측·보고되었나 | 원천의 값을 정준 Observation 으로 옮긴다. 보고된 null 과 못 본 값을 가른다. 공급자 모양을 여기서 정규화한다 | 해석 · 문턱 · 판정 · 정책 제안 · 상태 쓰기 | 원천 → Observation(+Telemetry 봉투) | Sensor `telemetry/`, `state/normalize.py`, `providers/` · MS `telemetry.py`, `providers/`, `run_telemetry.py` |
| MEASURE | 관측에서 무엇을 계산할 수 있나 | 결정론적 산술 · 집계(비율 · 창 · 백분위). 입력이 모자라면 UNKNOWN | 뜻 붙이기(HIGH 등) · 빈 칸을 옛 값으로 메우기 | Observation → Measurement | Sensor `state/metrics.py` · MS `manager.evidence` 창 |
| ESTIMATE | 시스템이 지금 무엇이라고 믿나(명목) | Model 의 규칙으로 실체마다 상태를 짓는다. 유효성 · 신선도 · 근거 · 전이 · 생애 | 행동 고르기 · 원 측정을 상태로 두기 · LLM 의견 받기 · 시계 읽기 | Measurement → State | Sensor `state/engine.py` · MS `manager.py` · `usage_model.py` |
| ASSESS | 무엇이 고장 났나 · 건강한가 · 왜 | 고장 탐지(잔차 · 선언된 오류 · 문턱 사건) · 격리(관계 그래프로 공통 원인 찾기) · 진단 · 건강 상태 | **행동 고르기**(RETRY · ACCEPT 등) · 다음 실행의 설정 제안 | State · Measurement · Model(기대값 · 고장 모드) → 건강/고장 State | Sensor `sensors/` · `residual.py` · `fusion.py` · (`verifier.py` 의 판정 부분 **제외**) · MS 품질 상태 |
| M Model | 이 상태는 무엇을 뜻하나 | 정의 · 값 집합 · 규칙 · 바인딩 · TTL · 목적 · 행동 명세 · 고장 모드 · 안전 제약 · 운영자 가정 | 실행 · 실행 중 값 바꾸기(바꾸면 판본을 올린다) | — (판본별로 불변) | Sensor `registry.py` · `rules.py` · `config.py` · MS `model.py` · `usage_model.py` · DC `purpose.py` |
| R Relationship | 무엇이 무엇과 어떻게 이어졌나 | 유형 있는 간선. 실체 간선은 저장소에, 유형 규칙은 M 에 | 행동을 담기 · 측정값 복사 | → Relationship | Sensor `engine.relationships` · MS `graph.edges` |
| E Evidence | 이 값을 무엇이 받치나 | 출처 · 시각 · 근거 종류 · 판본을 **참조로** 남긴다 | 원 측정값을 위층으로 복사 | → 출처 연결 | Sensor `Evidence` · `explain()` · DC `evidence_refs` |
| CONTEXTUALIZE | 이번 결정에 무엇이 필요한가 · 무엇이 가능한가 | 목적별 선택(Select) → 신선도(Filter) → 검사(Validate) → 투영(Project) → 고정(Freeze). 제약 · 능력 · 가능 행동을 붙인다 | 상태 계산 · 행동 선택 · 목적함수 · 프롬프트 짓기 · 실행 | State Store + 요청 → DecisionContext | DC 저장소 (기준 구현으로 삼는다, BD-05) |
| DECIDE (Policy) | 무엇을 할까 | DecisionContext → Decision(ActionIntent 후보 + 까닭). 판본 · 재현 | 원 텔레메트리 읽기 · 상태 쓰기 · 센서 전송 정의 · 허가하기 · 실행 | DC → Decision | MS `policy.py`(Provider) · LLM 제안 · Sensor `policy/`(참조) |
| VALIDATE | 이 의도는 꼴이 맞고 자기 근거에 서 있나 | 형식 · 인자 · DC 안에서의 근거 확인 | 고르기 · 허가 | Intent → 유효 Intent | MS A0 · A1 · A2 · A3 · A4 (BD-24) |
| ARBITRATE | 후보 가운데 무엇을 고르나 | 여러 정책 · 목표 · 우선순위 사이의 명시적 선택. 규칙 · 판본 · 기록 | 허가(Guard 의 일) · 숨은 정책 | 유효 Intent[] → 선택 Intent | **없음** (GAP-02) |
| GUARD (Safety/RTA) | 고른 것을 지금 실행해도 되나 | 안전 제약 · 권한 · 자원 한도 · 지금 상태의 신선도 · 사전조건 · 되풀이. **닫는 쪽으로만** 개입한다. 안전 동작으로 전환한다. shadow/enforce | 허가를 **더하기** · 명목 최적화 · 프롬프트나 LLM 말에 영향받기 | 선택 Intent + **지금 State** → 허가 · 거부 · 안전 동작 | MS A5 · A6 · A7 · A8 (BD-24) |
| EXECUTE | 실행한다 | ActionCommand 를 실행기에 보낸다. 결과를 Observation 으로 돌려준다 | 상태를 직접 쓰기 · 허가 없이 실행 | 허가된 Command → Outcome Observation | MS `tools.ToolSpec.run` (호출 자리 하나) |
| VERIFY | 의도한 효과가 났나 | 행동 명세의 사후조건과 관측된 다음 상태를 견준다. 검증 결과를 상태로 남긴다 | 행동 다시 고르기(그것은 다음 DECIDE) | Command + 사후조건 + 다음 State → Verification | 없음 (GAP-05). 평가용 `check_success` 만 |
| Runtime | — | 생애 · 일정 · 시계 주입 · 저장소 접근 · 전송 · 배차 · 원장 · 안전 감시 구동 | 뜻을 다시 정하기 · 상태 계산 · 정책 내장 | — | MS `runtime.py` · `pipeline.py` |

---

## 4. 데이터 소유 · 생애 · 범위

### 4.1 저장소 (쓰는 쪽은 하나뿐이다)

| 저장소 | 담는 것 | **유일한 쓰는 쪽** | 읽는 쪽 | 바뀜 | 영속 | 다시 지을 수 있나 |
|---|---|---|---|---|---|---|
| Observation Log | Observation (덧붙이기만) | OBSERVE (Runtime 의 ingest 를 통해) | MEASURE · Evidence 해석 · 감사 | 불변 | **영속** (권위 있는 원본) | 아니오 — 원본이다 |
| Model Registry | 판본별 정의 · 운영자 가정 | 사람(변경 절차 + 판본 올림) | 모든 층 | 판본마다 불변 | **영속** | 아니오 |
| Measurement Ledger | Metric 값 | MEASURE | ESTIMATE · ASSESS · explain | 덧붙이기 | 선택 (감사용) | **예** — Observation Log + 모형 판본에서 |
| State Store | 현재 State · 이력 · 전이 · 생애 사건 | ESTIMATE(명목 규칙) · ASSESS(건강 규칙). **상태 이름마다 규칙 하나가 소유한다** | CONTEXTUALIZE · GUARD · VERIFY · 질의 · explain | current 는 소유 규칙만, 이력은 덧붙이기 | 스냅숏은 최적화 | **예** — 사건 재생으로 |
| Relationship Store | 실체 간선 + 유효 구간 | ESTIMATE (관측에서) · Runtime(구조 선언) — BD-27 | CONTEXTUALIZE · ASSESS(격리) · 질의 | 덧붙이기 + 유효 구간 닫기 | 선택 | 예 (관측분) / 아니오 (선언분) |
| Opinion Store | LLM · 사람의 해석 제안 | 누구나 | 감사만. **ESTIMATE · CONTEXTUALIZE 는 읽지 않는다** | 덧붙이기 | 선택 | — |
| DecisionContext Store | 고정된 DC (내용 주소) | CONTEXTUALIZE | DECIDE · 원장 · 재현 | 불변 | 원장과 같은 보존 | 예 (State 이력 + 같은 as_of 에서) |
| Decision Ledger | DecisionRecord (단계마다 자기 절을 덧붙인다) | DECIDE–VERIFY (각자 자기 절만) | 재현 · 감사 · 텔레메트리 참조 | 덧붙이기 | **영속** | 아니오 |
| Caches | provider 프롬프트 캐시 · 결정 재사용(DC digest + 정책 판본) · 질의 결과 | 그 캐시를 둔 단계 | 같은 단계 | 버릴 수 있음 | 아니오 | — |

**캐시 규칙 (BD-11):** 잃었을 때 행동이 바뀌는 것은 캐시가 아니다. 캐시는 권위가 없고, 언제 버려도 뜻이 바뀌지 않아야 한다.
지금 MS `StateGraph` 는 캐시가 아니라 State Store 다(메모리에만 있다는 것은 영속성의 문제다, GAP-09).

**설정 규칙 (BD-13):** 예산 · SLO · 띠 · TTL 같은 운영자 설정은 **관측이 아니다.** 판본이 있는 Model(운영자 가정)이거나, 요청마다 주는
Constraint 다. 지금 MS 는 `config.token_budget` 을 텔레메트리로 넣는다 → BV-03.

### 4.2 범위 (scope) 와 생애

| 범위 | 무엇이 사나 | 끝나는 때 |
|---|---|---|
| 판(round) / 요청 | LLM 맥락 · 프롬프트 · 원장에 적기 전의 후보 의도 | 판이 끝날 때 (원장에 남은 것만 산다) |
| 실행(run) / 세션 | run · session 범위 실체의 State · Relationship · DC | 실행 · 세션이 끝날 때. 끝난 일의 사실은 PERMANENT 로 남는다 |
| 계정 / 배치 | 요금 한도처럼 여러 실행이 나누는 것 (Sensor 조사: 요금 한도는 **계정**의 것이다) | 리셋 시각 · 배치가 바뀔 때 |
| 배치(deployment) | Model 판본 · Observation Log 보존 · Ledger | 보존 정책에 따라 |

---

## 5. 의존 방향

```
데이터는 앞으로만 흐른다:   OBSERVE → MEASURE → ESTIMATE → ASSESS → CONTEXTUALIZE → DECIDE → VALIDATE → ARBITRATE → GUARD → EXECUTE → VERIFY
되먹임은 한 길뿐이다:       EXECUTE/VERIFY 의 결과 · 모든 단계의 자기 텔레메트리 → OBSERVE (Observation 으로)
M 은 모두가 읽고 아무도 실행 중에 쓰지 않는다
```

| 읽는 쪽 \ 읽을 수 있는 것 | Obs | Meas | State | Rel | DC | Ledger | M |
|---|---|---|---|---|---|---|---|
| MEASURE | ✔ | — | — | — | — | — | ✔ |
| ESTIMATE | — | ✔ | 자기 이전 값 | ✔ | — | — | ✔ |
| ASSESS | — | ✔ | ✔ | ✔ | — | ✔ (행동 결과 참조) | ✔ |
| CONTEXTUALIZE | — | — | ✔ | ✔ | — | — | ✔ |
| DECIDE Policy | — | — | **✘** | — | ✔ (오직 이것) | — | 자기 판본 |
| VALIDATE–ARBITRATE | — | — | ✘ | — | ✔ | — | ✔ |
| GUARD | — | — | ✔ (**지금** 값) | ✔ | ✔ | ✔ | ✔ |
| EXECUTE | — | — | ✘ | — | — | ✔ (허가) | ✔ |
| VERIFY | ✔ (결과) | ✔ | ✔ | — | ✔ | ✔ | ✔ |

**저장소 사이 코드 의존 (BD-28):** `Telemetry`(계약 · 잎) ← `Sensor` · `MS`. `DC` 는 아무것도 import 하지 않는다(소스 규약, 덕 타이핑).
`MS` → `DC`. `Sensor` 는 `DC` · `MS` 를 import 하지 않는다. Guard · Action 은 Policy 를 import 하지 않는다(§10).

---

## 6. 경계 위반 (BV)

| # | 위반 | 근거 (파일:줄) | 어느 경계 |
|---|---|---|---|
| BV-01 | Sensor 판정기가 **판정과 정책 제안**을 함께 낸다(ACCEPT · RETRY + `token_budget` · `route` 등) | `Sensor/llmsensor/verifier.py:63,65,81,87,92` | ASSESS ↔ DECIDE (진단 ≠ 결정) |
| BV-02 | 상태 층이 정책 입력을 짓는다. 그 안의 `why` 문자열에 원 수치가 남는다 | `Sensor/llmsensor/state/engine.py:276-311` | ESTIMATE ↔ CONTEXTUALIZE, I1 |
| BV-03 | 운영자 설정(예산)을 텔레메트리로 넣는다. 그래서 파생 상태의 시각이 세션을 연 시각에 묶여 늙는다 | `MS/ms/usage_model.py:92-94,147-154` · `MS/ms/manager.py:152` | Config ≠ Observation |
| BV-04 | 실행 텔레메트리(RunRecord)가 정책 결정의 **내용**(state · plans · arbiter_decision)을 싣는다 | `MS/ms/runtime.py:168` · `MS/ms/run_telemetry.py` (`policy` 칸) | Telemetry ≠ Decision Ledger |
| BV-05 | 안전에 가까운 제한(되돌릴 수 없는 도구를 좁힘)이 CR/Policy 의 계획 안에 있다 | `MS/ms/policy.py:113` | DECIDE ↔ GUARD |
| BV-06 | Arbiter 한 부품이 형식 검사 · 근거 · 낡음 · 허가 · 되풀이를 모두 한다. 정작 고르기는 하지 않는다 | `MS/ms/arbiter.py` (A0–A8) | VALIDATE · ARBITRATE · GUARD 를 합쳤다 |
| BV-07 | CR 이 DC 를 거치지 않고 그래프를 직접 질의해 LLM 맥락을 짓는다 | `MS/ms/cr.py:70-72` | CONTEXTUALIZE 를 우회 |
| BV-08 | Runtime 이 DC 대신 `usage_model.snapshot()` 을 정책에 준다. 이 값은 신선도 · 근거가 없다 | `MS/ms/runtime.py:80` | CONTEXTUALIZE 를 우회 |
| BV-09 | 텔레메트리 꼴이 만들어질 때 시계를 읽는다(`ts` 기본값 `time.time`). StateManager 의 기본 시계도 같다 | `MS/ms/telemetry.py:24` · `MS/ms/manager.py:35` | Runtime 만 시계를 읽는다 |
| BV-10 | Runtime 이 과업 성공을 판정한다(평가 하니스의 일) | `MS/ms/runtime.py:36` `check_success` | Runtime ↔ 평가 |
| BV-11 | 정책이 Sensor 저장소 안에 산다(이름은 "참조"다) | `Sensor/llmsensor/policy/*` | 저장소 경계 |
| BV-12 | LLM 의 판단 문장(`post_turn_summary`)을 결과 근거로 쓰자는 제안이 있었다. 지금은 쓰지 않지만 규칙으로 막혀 있지 않다 | `Sensor/docs/MS_HEALTH_INVENTORY.md` §2 | Opinion ≠ Observation |

## 7. 중복 개념 (DUP)

| # | 개념 | 어디에 둘 이상 | 정리 (제안) |
|---|---|---|---|
| DUP-01 | **Evidence** | Sensor: 근거 참조 / MS: 원 측정 창(role="evidence") / DC: `evidence_refs` | Evidence = 출처 연결. MS 의 것은 **Measurement 창**으로 이름을 바꾼다 (BD-06) |
| DUP-02 | 텔레메트리 꼴 | Sensor llm-telemetry/v3 · MS Telemetry/RunRecord | Telemetry 저장소가 정준 Observation 봉투를 갖는다 (BD-28) |
| DUP-03 | 상태 층 | Sensor StateEngine · MS StateManager | 상태 하나의 의미 규약(유효성 · 신선도 · 근거)을 공유한다. 엔진을 합칠지는 BD-29 |
| DUP-04 | Decision Context | 4 개 (§1.2) | DC 저장소를 기준 구현으로 삼는다 (BD-05) |
| DUP-05 | StateView | Sensor `state/model` · Sensor `decision/context` · DC `model` | DC 의 StateView 하나 |
| DUP-06 | 목적 · 행동 어휘 | DC: context_policy · provider_selection … `KEEP_PROVIDER` / Sensor: manage_context · select_provider … `STAY_PROVIDER` · `WAIT` | Model Registry 의 목적 표 하나 (BD-30) |
| DUP-07 | "Model" | 의미 모형 · PerformanceModel · OutcomeModel · LLM 모형 id | Model = 의미 · 지식 모형. 나머지는 `expectation model`(M 의 일부) · `fusion model`(ASSESS) · `provider_model` |
| DUP-08 | "Decision" | MS `arbiter.Decision`(판정) · Sensor `policy.Decision`(행동) · Verifier `Verdict` · MS "Context Decision" | Decision = DECIDE 의 출력뿐. 나머지는 ValidationResult · ArbitrationResult · GuardResult · AcceptanceAssessment · LLMContext |
| DUP-09 | 내용 해시 | DC 정준 JSON(`allow_nan=False`) · Sensor `default=str` | 정준화 규칙 하나 (SCHEMA §6) |
| DUP-10 | "MS" | MS 저장소 · Sensor 의 "MS 센싱" | Sensor 쪽은 "sensing expansion" 으로 부른다 |
| DUP-11 | `context_pressure` | Sensor: 런타임 선언 문턱 / MS: 손으로 둔 띠 | 다른 상태다. MS 쪽 이름을 `context_budget_pressure` 로 (DC 는 이미 키로 가른다) |
| DUP-12 | Proposal | MS: LLM 의 행동 제안 / Sensor: LLM 의 상태 해석 제안 | 앞은 ActionIntent, 뒤는 Opinion |
| DUP-13 | 유효성 · 근거 어휘 | DC `BASES` 5 개 ⊂ Sensor `Basis` 8 개(PROVIDER_DECLARED · VALIDATED_EXPERIMENT · EXTERNAL_LABEL 빠짐). MS 는 None 하나 | 어휘 하나를 계약으로 (SEMANTIC §3) |

---

## 8. 정규 런타임 고리

```
OBSERVE → ESTIMATE → ASSESS → CONTEXTUALIZE → DECIDE → VALIDATE → ARBITRATE → GUARD → EXECUTE → VERIFY → (OBSERVE)
  OBSERVE       MEASURE+ESTIMATE       ASSESS         CONTEXTUALIZE             DECIDE        VALIDATE          ARBITRATE         GUARD       EXECUTE       VERIFY
```

| 기능 | 어느 단계 | 왜 거기인가 / 왜 다른 곳이 아닌가 |
|---|---|---|
| 고장 탐지 (잔차 · 선언된 오류 · 문턱 사건) | ASSESS | 기대(Model)와 관측을 견주는 일이다. 결정이 아니다 |
| 진단 · 격리 | ASSESS | 관계 그래프로 공통 원인을 찾는다(수집기가 죽으면 여러 상태가 한꺼번에 UNKNOWN 이 된다) |
| 건강 평가 | ASSESS → State Store | 건강도 상태다. 소유 규칙이 다를 뿐이다 (BD-04) |
| 정책 | DECIDE | DC 만 본다 |
| 복구 결정 | DECIDE (목적 `recovery`) + GUARD 의 제약 | 복구도 결정이다. 다만 Guard 가 묶는다 |
| 안전 | GUARD, 그리고 **고리 밖의 안전 감시** | 명목 고리가 멈춰도 안전 동작을 낼 수 있어야 한다 |
| 행동 검증 | VERIFY → 결과는 State(`action_state`) | 사후조건 대 관측. 다시 고르는 것은 다음 DECIDE |
| LLM 답의 수락 (Sensor Verifier) | Q 융합 = ASSESS · ACCEPT/RETRY = DECIDE(목적 `acceptance`) · 다음 실행 설정 제안 = **고리 밖**(거버넌스) | BV-01 을 푸는 방법 |
| LLM 맥락 짓기 (CR) | DECIDE 안의 **정책 실행기 어댑터** — DC 를 받아 LLMContext 로 그린다 (BD-21) | DC 에 없는 정보를 더하지 않는다. 그래프 직접 질의 대신 DC 의 질의형 선택(BD-26) |

**방아쇠 (기본은 사건 구동이다, BD-14):** 관측 도착 → MEASURE–ASSESS → 바뀐 상태의 생애 사건. 결정 요청 · DC 가 가리키는 상태의 (값,
유효성) 변화 · TTL 만료 → CONTEXTUALIZE. Guard 는 모든 명령 배차 때 돌고, 안전 관련 상태가 바뀔 때도 돈다.

## 9. FDIR · 안전 경계 (요약 — 부품별 표는 [`DATA_FLOW.md`](DATA_FLOW.md) §5)

1. **고장도 상태다.** 건강 · 고장 상태는 ASSESS 의 규칙이 쓰고 State Store 에 산다. 유효성 · 신선도 · 근거 규약은 명목 상태와 같다.
2. **관측이 없는 것은 건강이 아니다.** `NO_FAILURE_OBSERVED` ≠ `HEALTHY`. 관측 상실도 그 자체로 고장 상태다(관측 가능성 상실).
3. **환경 변화와 고장을 가르는 근거는 Model 에 적힌 고장 모드다.** 고장 모드가 없으면 판정하지 않고 UNKNOWN 이다(지어내지 않는다).
4. **Guard 는 닫는 쪽으로만 간다.** 여러 고장의 제약은 논리곱으로 묶는다. 가장 엄한 것이 이긴다. 안전 동작의 순서는 Model 에 있다.
5. **Policy 는 Guard 를 넘지 못한다.** 거부는 원장과 자기 텔레메트리로 돌아간다. 다음 결정은 그것을 관측으로 본다. "강제" 경로는 없다.
6. **Guard 가 터지면 거부다**(enforce). shadow 에서는 기록하고 진행한다. 바뀌는 것은 모드뿐이다. 불변식은 코드에서 빠지지 않는다
   (사용자 결정, MS `docs/계획.md` §3-3).

---

## 10. 저장소 지도와 구현 순서 의존 그래프 (시퀀싱 엔진이 읽을 것)

### 10.1 층 번호(L0–L5) · 기능 단계 · 저장소 (BD-43)

| 층 번호 (코드가 쓰는 것) | 기능 단계 (이 기준선) | 저장소 | 상태 (2026-10-02) |
|---|---|---|---|
| — 계약 | 어휘 · 꼴 · 실체 id · 시간 기준 · 의존 그래프 | **baseline** | 이 문서 |
| **L0 Telemetry** | OBSERVE (판단 없는 관측 원장 · 행동 사건 `action.*` 은 `decision_ref` 만) | **Telemetry** | 섰다 (`jolly-einstein` 브랜치, 시험 33) |
| **L1 Sensor** | MEASURE + ASSESS 의 **탐지 판독**(운영자 문턱이 있는 판독 · 사건) | Sensor | 있음 |
| **L2 State** | ESTIMATE (+ 건강 상태의 저장) | Sensor(실행 단위) · MS(세션 단위) — 의미 규약만 공유 (BD-29) | 있음 |
| (L1–L2 옆) | ASSESS 의 진단 · 격리 · VERIFY | **Health** (새, BD-22) | 없음 |
| **L3 DC** | CONTEXTUALIZE | DC | 있음 · MS 에 배선됨 (`nifty-volta`) |
| **L4 Policy** | DECIDE (+ CR 어댑터) | MS | 있음 |
| (L4 와 L5 사이 — 새 번호를 붙이지 않는다) | VALIDATE · ARBITRATE · GUARD | **Guard** (새, BD-07 · BD-24) | 없음 |
| **L5 Action** | EXECUTE (결과는 L0 로) | **Action** (새, BD-25) | 없음 — L0 의 `action.*` 사건 꼴만 있다 |
| — 기반 시설 | Runtime · Decision Ledger 쓰기 순서 | MS (BD-42) | 있음 · DecisionRecord 분리됨 (`jolly-einstein`) |
| — 개발 | 시퀀싱 (개발 순서 관리자, BD-40) | **Sequencing** (새, 위가 선 뒤) | 없음 |

### 10.2 의존 그래프 — 무엇이 무엇보다 먼저 굳어야 하나

```
baseline 계약 ──► Telemetry 봉투 ──► Sensor/MS 의 OBSERVE 정규화 ──► State 규약 공유 ──► Health(ASSESS)
      │                                                    │
      │                                                    └──► DC 배선(MS Runtime) ──► Policy(ActionIntent 출력)
      │                                                                                        │
      └──► Action 꼴(ActionIntent · Command · Outcome) ─────────────────────────────────► Guard(VALIDATE–GUARD) ──► Executor ──► Verify(VERIFY)
```

규칙: 화살표의 꼬리가 **계약 동결** 상태가 되기 전에는 머리를 구현하지 않는다. 시퀀싱 엔진은 이 그래프와 §11 의 판정표를 읽는다.

---

## 11. 승인 시험 (§14 of the brief)

판정: **A** = 이 기준선으로 답이 정해진다 · **B** = 미결 질문에 막혀 있다. 0.1 에서 B 였던 7 문항은 BD-21–BD-42 로 풀렸다.

| 물음 | 답 | 판정 |
|---|---|---|
| State 란? | 실체 · 이름마다, 판본 있는 규칙이 Measurement 에서 지은, 지금 참이라고 믿는 값 + 유효성 · 신선도 · 근거 (SEMANTIC §2.3) | A |
| Model 이란? | 판본 있는, 실행 중 읽기만 하는 정의 · 규칙 · 명세의 묶음 | A |
| Relationship 이란? | 유형 있는 간선(주어 · 술어 · 목적어 · 유효 구간 · 근거). 행동이 아니다 | A |
| Decision Context 란? | 한 목적에 대해 State Store 에서 고른 최소 충분 정보의 고정 스냅숏 | A |
| Policy 는 어디에? | DECIDE. DC → Decision. MS 의 Provider Policy, LLM 실행기 | A |
| Action 은 어디에? | L5 · Action 저장소의 실행기. 꼴은 ActionIntent → ActionCommand → ActionOutcome(L0 사건). Sensor 는 행동 기록을 내지 않는다 (BD-25) | A |
| Arbitration 은 어디에? | Guard 저장소 안의 ARBITRATE 단계. Model 의 우선순위 · `conflicts_with` 로 후보 사이를 고른다. Validate = A0–A4, Guard = A5–A8 (BD-24) | A |
| FDIR 은 어디에? | 탐지 · 격리 = ASSESS · 복구 결정 = DECIDE(목적 recovery) · 제약 = GUARD · 검증 = VERIFY | A |
| Runtime 은 무엇을 소유하나? | 시계 · 일정 · 저장소 접근 · 전송 · 배차 · 원장 쓰기 순서 · 생애. 뜻은 소유하지 않는다 | A |
| 칸마다 소유자는? | SCHEMA §2–§3 | A |
| 무엇이 원 값 · 파생인가? | SEMANTIC §5 | A |
| 무엇이 영속 · 만료하나? | §4.1 · SCHEMA | A |
| 무엇을 보내고 무엇을 다시 짓나? | SCHEMA §4.3 (core 는 보내고, 파생 칸은 읽을 때 다시 계산한다) | A |
| DC 칸마다 왜 필요한가 · 무엇을 뺄 수 있나? | SCHEMA §4.2 | A |
| 신선도를 정하는 것은? | min(소스 TTL, 목적 max_age). TTL 은 Model(운영자 가정) | A |
| 관련성을 정하는 것은? | 목적 명세(Model) — 이름 붙은 상태 참조와 질의형 선택(BD-26) | A |
| 관측 → 상태 → 근거 → DC → 결정 | DATA_FLOW §2 | A |
| 결정은 어떻게 묶이나? | VALIDATE(꼴 · 자기 DC 안의 근거) → ARBITRATE(선택) → GUARD(지금 상태 기준 허가 · 닫는 쪽으로만) (BD-24 · BD-07) | A |
| 행동은 어떻게 실행되나? | Guard 가 낸 ActionCommand 를 Action 실행기가 실행하고, 결과를 L0 사건으로 낸다 (BD-25) | A |
| 행동 성공은 어떻게 검증하나? | Health 의 VERIFY 가 ActionSpec(Model)의 사후조건 · 시간 창을 그 뒤의 State 와 견준다 → `action_state` (BD-31) | A |
| 센서가 고장 나면? | DATA_FLOW §6.1 | A |
| 상태가 낡으면? | STALE 은 쓸 수 없다. Guard 가 배차 때 다시 본다 | A |
| Policy 와 Safety 가 다르면? | Guard 가 이긴다 | A |
| 고장이 여럿이면? | DATA_FLOW §6.4 | A |
| 유효한 DC 가 없으면? | 목적마다 Model 의 `default_decision`: KEEP · 고정 프롬프트 · KEEP_PROVIDER · ESCALATE(없으면 STOP) (BD-23) | A |

**결론: 25 문항 모두 A. 기준선을 승인한다 (baseline-1.0, 2026-10-02).**
남은 미결 OQ-17 · OQ-19 는 물음의 **답**을 바꾸지 않는다. 의미는 정해졌고(안전 동작은 Model 의 전순서에서 고른다 · 인코딩은 스키마 뒤),
값만 남았다. 각각 Guard enforce 전, 프로세스 간 전송 전에 정한다.

## 12. 고칠 파일 — 변경 제안(PC)

[`DECISION_LOG.md`](DECISION_LOG.md) 끝의 PC 표와 **실행 순서** 표에 있다. 기준선이 승인되었다고 PC 가 허가된 것은 아니다. PC 는 사용자가 허가한
것만, 실행 순서대로 한다.

## 13. 저장소 현황과 적합성 (2026-10-02 다시 확인 — 프롬프트마다 다시 본다)

### 13.1 브랜치 머리

| 저장소 | 브랜치 | 머리 | 조사 커밋 이후 |
|---|---|---|---|
| Telemetry | `claude/jolly-einstein-3y9icv` | 9c03ffc | L0 원장 신설: 판단 없는 관측 · 출처 종류 · `action.*` 사건 · Recorder · compat(Sensor v3 로 되짓기) |
| Sensor | `claude/jolly-einstein-3y9icv` | d1db787 | L0 선택 의존(`l0-check`) · 문턱 있는 토큰 사건을 `telemetry/derive.py` → `sensing/token` 으로 |
| Sensor | `claude/nice-wright-50oyvm` | 24265da | 건강 차원 설계 S1–S7 (구현 없음) |
| DC | `claude/jolly-einstein-3y9icv` | 50b4be7 | 통합 시험 고침 (= PC-01) |
| DC | `claude/nifty-volta-3u5ygl` | 48b9908 | MS 배선: `MSStateReader` · 목적 `context_runtime` · `context_policy` → purpose-context-2 (= PC-05 의 DC 쪽) |
| MS | `claude/jolly-einstein-3y9icv` | c0733de | `RunRecord.policy` → `DecisionRecord`, RunRecord 는 `decision_ref` 만 (= PC-11) |
| MS | `claude/nifty-volta-3u5ygl` | ee941ae | Runtime 의 `state_reader` 이음매 (= PC-05 의 MS 쪽) — `RunRecord.policy.state_source` 를 더한다 |
| MS | `claude/eloquent-turing-m33zjw` | 698edc8 | 선행조사: ② Sensor → Telemetry 배선 (구현 없음) |

### 13.2 적합성 — 기준선과 맞나

| 작업 | 판정 | 근거 |
|---|---|---|
| Telemetry L0 원장 | **맞음** | BD-02 · BD-15 · BD-16 · BD-28. 해석 어휘를 칸 이름에 못 쓰게 시험이 막는다. 출처 종류(reported · declared · measured · translated · ref)는 관측 수준의 근거 종류다 — State 의 Basis 와 대응표가 필요하다 (BD-44) |
| Sensor 토큰 사건을 L1 로 | **맞음** | 문턱 있는 판독은 관측이 아니다 (BD-10 · SEMANTIC §2.14) |
| DC PC-01 | **맞음** | |
| DC · MS 배선 (`state_reader`) | **맞음** | BV-08 을 푼다. 두 저장소가 서로 import 하지 않는다 (BD-28). `context_runtime` 목적의 소비자가 CR 계획인 것은 BD-21(CR 은 DC 를 받는 어댑터)과 맞는다 |
| MS DecisionRecord 분리 | **맞음** | BD-15 · BD-42 |
| Sensor S6 (`action.decision_id` 등 행동 기록 칸) | **고칠 것** | 행동 사건의 꼴은 이미 L0 에 있다(`action.dispatch {action_type, decision_ref}`). Sensor 는 L0 의 이름을 입력 계약으로 써야 한다 — 같은 기록을 두 꼴로 정하면 DUP 가 된다 (BD-28) |
| Sensor S7 (`resource_state` v2) | **결정됨** | "사용자 확인 대기" → BD-39 (예산 없으면 NOT_APPLICABLE 유지 · 실행 중 비용 판정은 조건부 채택) |
| MS ② 계획: Sensor `readings` 를 텔레메트리로 받음 | **고칠 것** | Reading(OK · SUSPECT · FAULT)은 판정이다 → ASSESS 의 출력, State 로 받는다(SEMANTIC §5). L0 는 해석을 받지 않는다(Telemetry 저장소 자신의 규칙). `fusion` · `verdict` 를 받지 않는 것은 맞다(BD-04 · BD-19) |

### 13.3 브랜치 사이의 충돌 — 합치기 전에 순서를 정해야 한다

| 충돌 | 브랜치 | 무엇이 부딪히나 | 권하는 순서 |
|---|---|---|---|
| X-1 | MS `jolly-einstein` ↔ MS `nifty-volta` | 한쪽은 `RunRecord.policy` 를 없앴고, 다른 쪽은 그 안에 `state_source` 를 더했다. `ms/runtime.py` · `ms/run_telemetry.py` · `tests/test_runtime.py` 가 둘 다 바뀐다 | `jolly-einstein`(DecisionRecord)을 먼저 합친다. 그다음 `state_source` 를 **DecisionRecord** 로 옮겨 `nifty-volta` 를 다시 맞춘다 (BD-15) |
| X-2 | DC `jolly-einstein` ↔ DC `nifty-volta` | 두 브랜치가 모두 `tests/test_integration.py` 의 MS 신호 · 표본을 고쳤다 | `nifty-volta` 가 더 넓다(PC-01 을 포함). `jolly-einstein` 은 버리거나 `nifty-volta` 위로 |
| X-3 | DC `nifty-volta` ↔ MS X-1 결과 | **확인됨**: DC 통합 시험이 `rec["policy"]["state_source"]` · `rec["policy"]["state"]` 를 읽는다(`tests/test_integration.py:189-212` on `nifty-volta`). X-1 뒤에 깨진다 | X-1 다음에 DC 통합 시험을 DecisionRecord 기준으로 |
| X-4 | Sensor `nice-wright` S6 ↔ Telemetry `action.*` | 행동 기록 꼴이 둘 | Telemetry 꼴을 기준으로 S6 입력 계약을 고친다 |

### 13.4 통합 1 회차 (2026-10-02) — 저장소마다 `claude/gracious-meitner-vp49xe`

| 저장소 | 통합 머리 | 들어간 세션 브랜치 | 시험 (옆 저장소를 통합 머리로 두고) |
|---|---|---|---|
| MS | `43f4294` | eloquent-turing(d3b5fda) · jolly-einstein(da9abbe) · nifty-volta(ee941ae) | 129 통과 · 건너뜀 0 |
| Sensor | `de659f5` | nifty-volta(51b825d, 안에 jolly-einstein · nice-wright 설계) · nice-wright(28c8af4) | 151 통과 |
| DC | `8c4d0e0` | nifty-volta(4b97cea) · jolly-einstein(50b4be7) | 61 통과 · 건너뜀 0 · 시연 재생성(바뀐 것은 DC id 뿐) |
| Telemetry | `52f354a` (브랜치 하나 — 합칠 것 없음) | jolly-einstein | (그 세션 보고: 38 통과) |

- **X-1 해소**: `state_source` 를 `RunRecord.policy` 에서 `DecisionRecord.state_source` 로 옮겼다(출처가 있을 때만 결정 id 에 든다).
- **X-2 해소**: DC 충돌 셋은 `nifty-volta` 쪽.
- **X-3 해소**: DC 통합 시험 · 시연이 MS 결정 기록을 읽는다.
- **X-4 남음** + 새로 찾은 중복 둘 → BD-45 · BD-47 로 지시했다:

| # | 중복 | 누구 | 지시 |
|---|---|---|---|
| X-5 | L1 liveness 팩 | Sensor `nice-wright` 가 구현 · Telemetry 세션이 1 순위로 제안 | L1 은 Sensor 세션만 (BD-45) |
| X-6 | liveness 입력 이름 | Sensor 의 `run.turn_open` 등 다섯 칸 대 L0 의 `heartbeat` · `run.start/end` 사건 | 이름은 L0 가, 계산은 Sensor 가 (BD-47) |
| X-7 | Sensor → MS 경로 둘 | MS `ms/sensing.py`(판독을 MS 그래프로) 대 Sensor state-export → DC → MS | state-export 경로 하나 (BD-46) |

전달 규약은 [`PROTOCOL.md`](PROTOCOL.md).

### 13.5 통합 3 회차 (2026-10-02)

| 저장소 | 통합 머리 | 새로 들어간 것 | 시험 (옆 저장소 모두 통합 머리) |
|---|---|---|---|
| MS | `ca71379` | CMD-M2(PC-21 문서) · PC-13 · PC-12 (eloquent) · CMD-T3 시험 (jolly) | 137 통과 · 건너뜀 0 |
| DC | `d8efadf` | PC-08 · PC-14 (nifty) — allow_stale · ContextStore · 시험 정책 refpolicy | 73 통과 · 건너뜀 0 |
| Sensor | `92cc46b` | CMD-T3 꼴 v4 `inproc:*` (jolly) · PC-08: Sensor 안의 결정 문맥 · 참조 정책 제거 (nifty) | 138 통과 · 건너뜀 0 |
| Telemetry | `780867b` | CMD-T2 차례 경계 사건(`input.received` · `turn.start` · `turn.end` · `turn.continued` · `source.closed`) · CMD-T4 대조 장부(sweagent 7 · cc_jsonl 1) | 47 통과 |

- DUP-04(결정 문맥 구현 넷)가 둘로 줄었다: DC 와 MS `snapshot()`(기본값 전환을 기다림). BV-11 해소.
- 충돌: Sensor `registry.py` · `STATE_DERIVATION.md` 의 후보 목록 한 줄 — `uncertainty_state` 설명은 nifty 쪽, `liveness DEAD · ALIVE` 줄은 통합 쪽을 남겼다.
- Sensor 를 두 세션이 쓴다 → BD-56 으로 경계를 다시 그었다.

### 13.6 통합 4 회차 (2026-10-02)

| 저장소 | 통합 머리 | 새로 들어간 것 | 시험 (옆 저장소 모두 통합 머리) |
|---|---|---|---|
| Sensor | `38892cd` | CMD-S3 `resource-state-v2`(BD-39) · CMD-T6 수집기 결함 D1 · D2 | 152 통과 |
| Telemetry | `20dc8df` | CMD-T6 · T5: D1–D4 · 런타임 자신의 행동 · 진행 신호 · 흡수된 입력. 실데이터: 시간 한도 초과 → 백그라운드 이동이 `tool.end` 로 | 53 통과 |
| MS | `39e2b59` | PC-04(`role: measurement`) · PC-03(예산을 관측에서 뺌) · 과업 묶음 datacenter-tasks-2(t6) · F2 사전등록 | 146 통과 |
| DC | `c68ebfa` | CMD-D1 정책 쓸모 재측정(483 그대로) | 72 통과 · **1 실패(예상된 것)** |

- **DC 실패 1 = BV-03 이 풀렸다는 증거.** `test_known_limit_config_input_ages_derived_state` 는 "예산 입력 때문에 MS 파생 상태가 세션을 연 시각으로 늙는다" 는 알려진 한계를 붙든 시험이다. MS PC-03 뒤로 그 상태가 STALE 이 아니라 INFERRED 로 나온다. 시험을 "고쳐졌다" 쪽으로 뒤집는 일을 DC 세션에 지시했다(CMD-D9, DC 소유 파일).
- Sensor 결과 파일 `eval/results/state_demo.txt` 충돌은 통합 코드로 다시 생성해 풀었다(6 절이 결정 문맥에서 내보내기 계약으로 바뀌어 있다 — PC-08).
- 사용자가 `nifty-volta` 를 DC 세션으로 확정했다(DC 보고) — BD-56 과 같다.

### 13.7 통합 5 회차 (2026-10-02)

- DC `d3be1e7`(CMD-D2 PC-07 core/provenance 분리 · `reason` 제거 · `reuse_key` · 키별 `allow_stale`) 통합 → DC 79 중 78 통과. 남은 1 은 4 회차의 CMD-D9(BV-03 이 풀려 빨개진 시험)이고 아직 처리되지 않았다 — DC 세션의 옆 MS 가 PC-03 이전(`ca71379`)이라 그 환경에서는 초록으로 보인다(환경 차이). MS 146 통과.
- DC 의 실데이터 회귀(결정 변화 483 · 결정론)와 크기(core 17–22 %)는 DC 세션의 측정이다. 크기 비율이 §4.4 의 ~10 % 보다 큰 까닭(core 에 subject · 제약 · 행동이 들어간다)은 보고에 설명돼 있다.

### 13.8 통합 6 회차 (2026-10-02)

| 저장소 | 통합 머리 | 새로 들어간 것 | 시험 |
|---|---|---|---|
| Telemetry | `0d7aa35` | CMD-T8 cc_stream 실기록 3(`claude -p`) | 54 통과 |
| Sensor | `f6f02fc` | CMD-S2 liveness 입력을 L0 사건으로(`liveness-state-v2`) | 156 통과 |
| MS | `7798205` | replay 가 상태 모형 판본으로 갈림 · F2 측정 준비(사전등록 고침 1, 돌리기 전) · CMD-M5 cc_jsonl 표본 631/631 | 153 통과 |
| DC | `a061c65` | CMD-D4 WALP → Arbiter/Guard | 78 / 79 — 남은 1 은 CMD-D9(4 회차부터) |

- **BD-50 충족**(BD-62). Sensor 수집기를 걷는 일을 하류 영향 목록과 함께 Telemetry 세션에 넘겼다.

### 13.9 통합 7 · 8 회차 (2026-10-02)

- Sensor `53c3a4c`(158 통과): CMD-S11 닫힘 줄. Telemetry `3453434`(54 통과). DC `e28d00d`(88 중 87 — 남은 1 은 CMD-D9): CMD-D5 질의형 선택(DC 쪽).
- **반복 신호(GUIDANCE 15)**: CMD-D9 가 세 회차째 처리되지 않았다. DC 세션의 옆 MS 가 PC-03 이전이라 그 환경에서는 시험이 초록이고, DC 세션은 "PC-03 의 DC 쪽은 MS 가 고치면 맞춘다" 고 적었다 — MS 는 이미 고쳤다. 원인은 세션 환경의 옆 저장소 판본이다(통합 브랜치를 옆에 두지 않음). 지시 문구를 이 사실 중심으로 바꿨다.
- MS PC-04 는 옛 이름 `evidence` 를 호환 속성으로 남겼다(`ms/manager.py:194`) — DC `sources.py:152` 가 아직 그 이름을 읽는다. DC 를 새 이름으로 옮기는 일은 DC 세션에.
- 9 회차: Sensor `340ea57`(164 통과) — CMD-S8 집계 근거 시각(BD-57 · BD-63) · CMD-S6 ASSESS 표시. DC `b94035c`(88 중 87, 남은 1 = D9) — BD-58 `agent_context`. MS 153 · Telemetry 54 통과. F2 는 사용자 결정으로 진행 중(BD-67).
- 10 회차: **Sensor 가 Telemetry 를 필수 의존으로 쓴다**(CMD-T9). Sensor 수집기는 같은 이름 · 서명의 이음매(L0 수집기 + compat)로 바뀌었고, 지우기 전 출력을 얼려 대조 기준으로 삼는다(BD-69). 의존은 통합 브랜치에 고정한다(BD-68). Sensor S9(PC-09 근거 값 복사 제거)도 들어갔다. 통합: Telemetry `a23285c`(55) · Sensor `a713f05`(166) · MS 153 · DC 88 중 87(D9).
- 11 회차: **통합 브랜치가 네 저장소 모두 초록**(4 회차 이후 처음). Telemetry `2140d2f` 56 · Sensor `a713f05` 166 · MS `7798205` 153 · DC `74d89ce` 88, 건너뜀 0. DC CMD-D9(BV-03 풀림을 붙드는 시험) · D10(MS 새 이름 `measurements`) · Telemetry CMD-T10(cc_stream 진행 신호 → `heartbeat`). D9 가 네 회차 걸린 원인은 DC 세션이 보고 사이에 baseline 댓글을 다시 읽지 않은 것과 옆 저장소 판본이었다 — DC 세션이 "일을 시작하기 전마다 최신 댓글을 먼저 읽는다" 로 고쳤다.

### 13.10 통합 12 · 13 회차 (2026-10-02)

- 12 회차: Telemetry `2f9ae0c`(57) — CMD-T10(cc_stream 진행 신호 → `heartbeat`) · CMD-T11(`StopFailure` → `turn.end(api_error)`, 덧붙인 칸 `error_type`). 둘 다 합성 자료로만 확인 → 실기록 확인은 Sensor 세션 CMD-S14.
- 13 회차: 네 저장소 모두 초록 — Telemetry `2f9ae0c` 57 · Sensor `5e59198` 167 · MS `c21abcf` 153 · DC `74d89ce` 88.
  - Sensor: CMD-T9'(Telemetry 의존을 `@claude/gracious-meitner-vp49xe` 로 고정, BD-68 — `direct_url.json` 이 `2f9ae0c` 를 받음) · BD-64 `resource-state-v3`(추정 소진은 영구가 아니다, 보고가 뒤집는다).
  - MS: **F2 결과**(BD-72). 적응 맥락은 지연 +2.6 s 가 재졌고 꺼냄 증가(F2)는 사전등록 읽기로 후보에서 내렸다. 이득은 재지 못했다. 기본 선택기는 고정 그대로.
  - 다음: MS 는 PC-23 의 MS 쪽 → `evidence` 호환 속성 떼기(BD-73). F2 후속은 그 뒤, 사용자 결정으로.
- 14 회차: Sensor `294683d`(170) — liveness 가 `input.removed` 를 처리하지 않은 입력 수로 센다. 실데이터에서 429 뒤 5.5 시간이 이제 AWAITING_INPUT(T11 실기록 확인). **T10 은 실기록에서 아직 0/8** — 합성으로만 맞았다; 실제 `tool_progress` 키 목록(CMD-S14 1)이 와야 고친다. BD-74(부재 주장의 근거 시각) · BD-75. 네 저장소 초록(57 · 170 · 153 · 88).
- 15 회차: **상태 내보내기 계약 `/2`**(CMD-D7, BD-70) — Sensor `9b331cd`(171) · DC `e35fa1d`(89). `entity` 는 엔진 id 그대로(불투명) · `entity_ref` BD-32 꼴 · 상태마다 `time_base` · `reason` 뺌 · DC 는 `/2` 만 받는다. 실데이터 결정 변화 483 → 484 는 `/2` 가 아니라 Sensor CMD-S8(집계 근거 시각)의 결과 — 그 한 실행을 CMD-D11 로 확인한다. DC `examples/sensor_session.py` 는 Sensor 수집기 이음매(BD-69)로 그대로 돈다(통합 머리에서 실행 확인).
- 16 회차: DC `113898a`(89) — CMD-D11 `eval/decision_trace.py`. 484 번째 결정 변화 = `cc_jsonl_self:self_sna` i=154: 상태는 의도대로 STALE, **결정은 BD-23 과 어긋남**(모름 → CONTINUE). BD-76 · CMD-D12 로 고친다.
- 17 회차: **PC-23 의 MS 쪽 끝**(CMD-M6) — CR `cr-2` 가 DC 질의 결과를 받고, 낡은 값은 `allow_stale` 없이는 LLM 에 안 간다(BD-77). `StateManager.evidence` 뗌(M7). Sensor CMD-S7 진행분(S2 시간 초과 처분 `execution-interruption-v3` · S4 요금 한도 여유 `rate-limit-state-v3`). 통합: Telemetry `2f9ae0c` 57 · Sensor `ce993fc` 175 · MS `4cad68a` 160 · DC `113898a` 89 — 모두 초록. 남은 복제: MS 평가 하니스의 DC 리더 약 15 줄 → DC `MSStateReader` 가 요청을 받으면 걷는다(CMD-D13 · M9).
- 18 회차: Sensor `1367fc2`(186, 변이 42/42) — **L1 팩 넷 끝**(CMD-S7: S2 시간 초과 처분 · S4 요금 한도 여유 · S5 runtime_actions · S3 dependency_fault, BD-54 조건 · ASSESS 표시 확인). S14 실기록: T11 맞음 · **T10 은 실제 꼴과 다름**(`tool_use_id` 는 합성 `bash-progress-n`, 장부에 있는 것은 `parent_tool_use_id`, 8/8) · **새 구멍**: API 오류 뒤 사람의 재시도 입력으로 시작한 차례의 `turn.start` 누락(47 응답). → Telemetry CMD-T12 · T13. BD-79(MS 센서 상태 넷 짓지 않음) · BD-80(compat 넓히지 않음). 네 저장소 초록(57 · 186 · 160 · 89).
- 19 회차: DC `5344a27`(95) — **안전 기본 결정이 목적 명세에**(CMD-D12, BD-76): `dc-builder-3` · `core.default_action`(능력 있는 첫 후보) · 시험 정책 `dc-test-*-2`. `self_sna` i=154–159 = ESCALATE. 결정 변화 484 → 450 — SWE-agent 288 실행은 `execution_health` 가 19,331 평가점 전부 UNKNOWN 이라 실행 정책이 처음부터 기본값(BD-82 · CMD-S17). `self_sna` i=56 은 BD-76 의 둘째 실례(18.9 분 틈 → STALE → ESCALATE). 네 저장소 초록(57 · 186 · 160 · 95).
- 20 회차: Telemetry `6d4d96e`(58) — CMD-T12 `tool_progress` 를 실제 꼴(두 id 중 장부에 있는 것 + 도구 이름 맞춤)로; T10 은 실기록 실패로 고쳐 적음. CMD-T13 은 원천 꼴이 없어 **막힘** — 꼴만 내는 탐침 `eval/shape_probe.py` 를 두었고, Sensor 세션이 그 실기록에 돌린다(CMD-S18). 네 저장소 초록(58 · 186 · 160 · 95).
- 21 회차: MS `2912912`(160) — CMD-M8 F2b 사전등록(쓰기만, BD-83). 실행은 코드(과업 묶음 3 · 층화 하니스 · M9)가 선 뒤 사용자 결정.
- 22 회차: Sensor `505cdf6`(186, 변이 43/43) — CMD-S16: S2 · S4 가 L0 를 직접 읽음(BD-80), 덧대기 걷음. **L0 구멍**: `provider.rate_limit.resets_at_ms` 를 수집기가 옮기지 않아 unobserved 로 적힘 — 원천(cc_jsonl `quotaLimits` · cc_stream `rate_limit_info`)에 `resetsAt`(초) 가 있다(baseline 이 수집기 코드에서 그 키를 읽는 곳이 없음을 확인) → CMD-T14.
- 23 회차(코드 변화 없음): Sensor CMD-S18 — **T12 실기록 8/8**(성공). 02:13 재개 줄(1047)은 `type=user` · `isMeta` · `turnOrigin=system` · `turnPosition` 있음이고 L0 사건이 없다 — 수집기가 `isMeta` 줄을 입력에서 빼면서 차례 경계도 함께 놓친다(T13 의 H2, baseline 이 `collect/__init__.py:255` 에서 확인). CMD-S17 — SWE-agent 의 UNKNOWN 은 원천 한계 · 도구 전 값은 BD-84 `NO_TOOL_RUN_YET`.
- 24 회차: DC `27bac8c`(100) — CMD-D13: `MSStateReader` 가 요청 질의를 받고 질의별 `allow_stale`(BD-65) · `prompt_policy` 기본 `FULL_INSTRUCTION` · `record.default_action`(BD-81). MS `f2fe93c`(160) — F2b 선행조사: 현상은 이미 보고됨 → BD-86(덮음 선언 칸). BD-85(표시 순서는 CR 의 일). 네 저장소 초록(58 · 186 · 160 · 100). MS M9 가 풀렸다.
- 25 회차: Telemetry `8488808`(62) — CMD-T14 `resetsAt` → `resets_at_ms`(실기록 claude -p 3/3 값, 단위 초 확인) · 같은 함수의 stream 한도 종류 · 초과 사용 칸도 기존 칸으로 · CMD-T13 커밋(보고 대기). BD-87. 네 저장소 초록(62 · 186 · 160 · 100).
- 26 회차: Telemetry `70b4feb`(65) — CMD-T15 새 사건 `provider.rate_limit_window`(창마다 하나, 창 이름은 원천 키 · 주된 창을 고르지 않음 · 실기록 창 2: five_hour · seven_day). MS `3034578`(162) — CMD-M9 커밋(복제 리더 걷음 · 표시 순서 `cr-3` · 기본 결정을 문맥에서), 보고 대기. 네 저장소 초록(65 · 186 · 162 · 100).
- 26 회차(이어서): MS CMD-M9 성공 — 복제 리더 없음 · 두 길 같은 LLM 글자열(`cr-3`, 직접 길의 꺼냄도 질의 열 안에서만) · 기본 결정을 문맥에서 읽음. BD-88(품질 상태 모름에도 BD-76).
- 27 회차: MS `e2a7a4a`(162) — CMD-M10 F2b 고침 1(칸 H 덮음 선언 · 동작점 고침: 서버 36 · 예산 4,000 · keep_max 40 · R4 · 285 실행 약 $5~7) — BD-88 과 엇갈려 선택기 판본 · 워밍업 근거를 CMD-M12 로. Sensor `8978265`(197) — CMD-S19 커밋(`NO_TOOL_RUN_YET`, 보고 대기) → DC CMD-D14. 네 저장소 초록(65 · 197 · 162 · 100).
- 27 회차(이어서): Sensor CMD-S19 성공 — `execution-health-v3`(197, 변이 47/47). 사건 순서에서 첫 평가점 314/314 `NO_TOOL_RUN_YET`(정의에서 나옴), SWE-agent 는 그 뒤 UNKNOWN 288/288. 시각 순서에서는 "모델 호출 ≥ 1" 조건 때문에 cc 첫 평가점이 UNKNOWN → BD-89 로 조건을 "그 실행의 L0 사건 ≥ 1" 로(CMD-S22).
- 27 회차(이어서): Sensor CMD-S20 — **T13 실기록 성공**(같은 사본에서 `turn.start` 정확히 +1, 02:13:38 origin system · liveness 값 변화 없음, 근거만 바뀜) · **T14 실기록 성공**(JSONL `quota_time_to_reset_ms` 1,330/2,865 평가). cc_stream 은 `monotonic_ms` 라 남은 시간을 내지 않음 → BD-90.
- 28 회차: MS `7272cf8`(170) — F2b 지음(과업 묶음 3 · 칸 H · 층별 판정). 선택기가 BD-88 이전 판본이라 **아직 실행 준비 아님** — M11 · M12 뒤 사용자에게 묻는다. 네 저장소 초록(65 · 197 · 170 · 100).
- (05:30–08:54 모든 세션이 함께 멈췄다가 다시 돎.) 29 회차: DC `7a944b1`(104) — CMD-D14 `dc-test-execution-3`: RUNNING × `NO_TOOL_RUN_YET` → CONTINUE(명시), 정책이 모르는 값은 기본 결정. 수치 잠정(S22 전): 결정 변화 450 → 729 — 늘어난 몫은 i=0 이 앎이 되며 i=1 에서 바뀌는 수(개선 아님). MS `4c775be`(171) — M11 · M12 커밋(보고 대기). 네 저장소 초록(65 · 197 · 171 · 104).
- 29 회차(이어서): MS CMD-M11 성공(`ctx-adaptive-3` · `-4` · `-4c`, 모의 실행 1~5 KEEP, 기본 경로 LLM 본 글 0 행 변화) · CMD-M12 성공(F2b 칸 G = `-4` · H = `-4c`, 워밍업 3 의 근거 — 묶음 3 은 고침이 없어 실행 3 뒤 품질 상태 확정, 모의 32/32 · 95% 무효 조건). **F2b 실행 준비 끝 — 사용자 결정 대기**(285 실행 · 약 $5~7 · 30~40 분). BD-91.
- 30 회차: MS `0fc211d`(172) — CMD-M13 `prompt-adaptive-2`(BD-91). Sensor `638869f`(201, 변이 49/49) — CMD-S22(BD-89): seq 순서로 흘려 넣은 첫 평가점 `NO_TOOL_RUN_YET` 314/314(시각 순서의 UNKNOWN 26/26 이 풀림). 첫 `tool.start` 순간은 314/314 UNKNOWN(도는 중 — 의도한 동작, 이유 글만 원천 한계와 같아 CMD-S23 으로 가름). DC D14 다시 재기로. 네 저장소 초록(65 · 201 · 172 · 104).
- 31 회차: DC `1387318`(104) — CMD-D14 닫음: S22 뒤 19,592 평가점 모두 같음, 결정 변화 729 · 기본 결정 18,475 확정(늘어난 몫은 모든 실행 i=0 하나 — 개선 아님). 네 저장소 초록(65 · 201 · 172 · 104).
- 32 회차: Sensor `9689a66`(218, 변이 56/56) — CMD-S21: `quota_headroom` v2(선언된 창 가운데 최소 여유, 정한 창을 이유에 · 창 하나라도 모르면 모름) · `quota_resets_at_ms`(BD-90, cc_stream 12/12) · `quota_windows`(창마다, 고르지 않음). 표본에서는 값이 v1 과 같다(최소 창 = limit_type 창) — 새로 생긴 것은 다른 창의 가시성과 근거. 원시 사건 재계산 12/12 일치.
- 33 회차: Sensor `0764a75`(225, 변이 61/61) — CMD-S23: 결과를 못 본 도구 호출의 UNKNOWN 이유를 "기다리는 중 · 원천이 안 줌 · 모른다" 로 가름(기준: 그 호출의 `tool.end` 를 봤나 — `t_result_ms` 는 시각 없는 원천에서 거짓 "기다리는 중" 을 냄). SWE-agent 끝 원천 한계 288/288. 네 저장소 초록(65 · 225 · 172 · 104). **받은 지시가 모두 끝났다** — 남은 것은 사용자 결정(F2b 실행 · 단계 마감 태그).
- **단계 1 마감**(BD-92, `STAGES.md`): Telemetry `70b4feb` · Sensor `10bb7ad` · MS `0fc211d` · DC `1387318`, 모두 초록. Sensor L0 의존을 Telemetry 커밋 sha 에 고정. F2b 실행은 MS 세션(BD-93).
- 34 회차: MS `4c6cfe2`(173) — **F2b 결과**(BD-94): R2 확인(있음 층 입력 −26%, 품질 비열등 · 안전 통과), R1 · R4 는 시험이 서지 않음(꺼냄 0 — 복잡도 규칙이 예산을 올려 숨긴 행이 없음). 기본 맥락은 고정 그대로, 기제 측정은 미룸.
- 35 회차: **action 저장소 통합 브랜치 시작** — action `c29dfbc`(25 통과 · 변이 25/25, Telemetry `70b4feb` 옆에). CMD-A1 `action-contract/1` → 계약 동결(BD-96). 다음: Telemetry CMD-T16(밖의 `action_ref`) · Action CMD-A2(PC-19 차이 보고) · Guard 저장소(사용자).
- 36 회차: Telemetry `d60d591`(70, 변이 57/57) — CMD-T16: `Recorder.action(action_ref=command_id)`(BD-96), 안 주면 지금과 같음 · 겹쳐 열기 거절. 다섯 저장소 초록(Telemetry 70 · Sensor 225 · MS 173 · DC 104 · action 25). Sensor 의 L0 의존은 단계 1 고정(`70b4feb`) 그대로 — 다음 단계 마감 때 옮긴다.
