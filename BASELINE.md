# AUTONOMY ARCHITECTURE BASELINE — FREEZE PHASE

| 항목 | 값 |
|---|---|
| 판본 | baseline-0.1 (**제안**, 아직 승인 전) |
| 날짜 | 2026-10-02 |
| 대상 커밋 | Sensor `dd779e0` · DC `e277144` · MS `06fcb09` · Telemetry (커밋 없음) · baseline `1539228` |
| 상태 | **ACCEPTANCE 미통과.** §9 의 BLOCKED 항목이 풀릴 때까지 이 문서를 근거로 구현하지 않는다 |

함께 읽는 문서: [`SEMANTIC_MODEL.md`](SEMANTIC_MODEL.md) (낱말의 뜻) · [`DATA_FLOW.md`](DATA_FLOW.md) (흐름과 실패 흐름) ·
[`SCHEMA_PROPOSAL.md`](SCHEMA_PROPOSAL.md) (칸 · 소유 · 생애 · 최소성) · [`DECISION_LOG.md`](DECISION_LOG.md) (결정 BD-xx) ·
[`OPEN_QUESTIONS.md`](OPEN_QUESTIONS.md) (미결 OQ-xx).

이 문서에서 쓰는 꼬리표: **BV** 경계 위반 · **DUP** 중복 개념 · **GAP** 빠진 것 · **PC** 승인 뒤의 변경 제안 · **BD** 결정 · **OQ** 미결 질문.

---

## 0. 참조한 원칙과 그 한계

**이 세션에서는 원문을 다시 읽지 못했다.** learn.microsoft.com · nasa.gov · ntrs.nasa.gov · swehb.nasa.gov · arxiv.org 모두 이 컨테이너의
네트워크 정책에 막혔다(2026-10-02, curl 응답 없음). Sensor 저장소의 앞선 조사(`Sensor/docs/MS_HEALTH_INVENTORY.md` §5)도 같은 차단을
기록했다. 아래 원칙은 **널리 알려진 아키텍처 원칙을 이름으로 인용한 것**이다. 문헌의 특정 쪽수나 문구에 기대지 않는다. 원문 확인은
OQ-20 에 남긴다.

| 출처 계열 | 가져온 원칙 | 이 기준선에서의 자리 |
|---|---|---|
| NASA FDIR · ISHM · 모형 기반 진단 | 탐지(detection) → 격리(isolation) → 복구(recovery)는 다른 기능이다. **진단은 결정이 아니다** | L4 ASSESS 와 L6 DECIDE 를 떼었다 (BD-04) |
| NASA 모형 기반 자율 (상태 추정 / 실행 분리) | 상태 추정은 모형을 쓰고, 명령은 실행층(executive)을 지난다 | M(Model) 은 실행 중 읽기 전용이다. Action 은 L10 에서만 실행된다 |
| NASA 런타임 보증 (Simplex 계열) | 명목 제어기와 안전 감시기는 독립이다. 감시기는 **닫는 쪽으로만** 개입하고 안전 동작으로 전환한다 | L9 GUARD 를 Policy 와 다른 부품으로 둔다 (BD-07) |
| NASA cFS Limit Checker · F´ Health (Sensor 앞선 조사가 원문을 읽었음) | 문턱을 넘으면 **사건**이 생긴다. 대응은 따로 시작된다. 문턱은 미리 설정한 것이다 | 상태 규칙에 근거 종류(Basis)를 붙인다. 문턱 출처가 없으면 NOT_APPLICABLE · UNKNOWN (BD-10) |
| Azure 상태 있는 AI · Agent Framework 상태 모형 | 상태에는 범위(scope)와 생애(lifecycle)가 있다. 영속 상태와 일시 맥락은 다르다 | §4 저장소 · 범위 표 (BD-12) |
| Microsoft Research 맥락 공학 · 압축 | 지금 과업에 맞는 맥락만 넘긴다. 줄일 수 있으면 줄인다 | L5 Decision Context 의 최소성 (BD-08, SCHEMA §4) |
| Azure 오케스트레이션 패턴 | 결정론적 흐름으로 충분하면 결정론으로 둔다. 할 수 있다는 이유로 에이전트 층을 더하지 않는다 | LLM 은 Policy 를 돌리는 실행기의 하나일 뿐이다 (BD-09) |
| Azure (상태 저장 ≠ 맥락 선택) | 상태를 저장하는 일과 맥락을 고르는 일은 다른 관심사다 | State Store(L3) 와 Context Selection(L5) 을 가른다 (BD-08) |

---

## 1. 현재 시스템 재구성

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
자리가 다르다: Sensor 그림에서는 "정책의 일", MS 그림에서는 DC 와 Policy 사이의 층이다 → OQ-01. (c) Sensor 는 "MS" 라는 낱말을
"MS 센싱 확장" 의 뜻으로 쓴다 → DUP-10.

### 1.4 지도 — 현재 → 실제 → 의도 → 빠진 것 → 중복 → 위반

```
CURRENT SYSTEM          세 저장소 · 프로세스 하나 · 메모리 안의 상태 · 저장소 사이 배선 없음(DC 는 어댑터로 읽기만)
    ↓
actual implementation   관측 꼴 2 · 상태 층 2 · DC 4 · 정책 3 갈래(MS 선택기 · Sensor 참조 · Verifier 제안) · Arbiter 1(판정+허가) · 실행기 1(MS 도구)
    ↓
intended architecture   §2 의 L1–L11 (아래). MS 계획 ①–⑨ 과 같은 방향
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

```
                 ┌──────────────── M · MODEL (판본이 있다. 실행 중에는 읽기만 한다) ────────────────┐
                 │ 실체 유형 · 속성 · 값 집합 · 규칙(id@ver, basis) · 바인딩 · TTL · 운영자 가정(config) │
                 │ 목적(purpose) · 행동 명세(requires · pre/postcondition · risk) · 고장 모드(affects) │
                 │ 관계 유형 · 안전 제약 · 안전 동작(safe action) 순서                                │
                 └─────▲──────────▲──────────▲──────────▲──────────▲──────────▲──────────▲────────────┘
                       │          │          │          │          │          │          │
L0 SOURCE ─► L1 OBSERVE ─► L2 MEASURE ─► L3 ESTIMATE ─► L4 ASSESS ─► L5 CONTEXTUALIZE ─► L6 DECIDE
 세계 · 런타임 Observation     Measurement   State(명목)    State(건강/고장) DecisionContext     ActionIntent[]
 provider ·   (Telemetry 는    (Metric)      ┌────────── STATE STORE ──────────┐ (고정 · id)       (Policy 판본)
 도구 · 사람   그 전송 꼴)                    │ current · history · transitions │      │
 · 설정은 M 로                               │ RELATIONSHIP STORE (실체 간선)    │      │
                                            │ EVIDENCE = 출처 연결(복사 아님)   │      │
                                            └───────────────▲─────────────────┘      ▼
                                                            │ 직접 읽기     L7 VALIDATE ─► L8 ARBITRATE ─► L9 GUARD
                                                            └──────────────── (지금 상태) ───────────────┘  │ 허가 / 거부 / 안전 동작
                                                                                                          ▼
         ◄────────── 결과 · 자기 텔레메트리는 Observation 으로 돌아온다 ◄── L11 VERIFY ◄── L10 EXECUTE (ActionCommand → Executor → Outcome)

DECISION LEDGER (덧붙이기만): dc_id · policy@ver · intents · validate · arbitrate · guard · command · outcome refs · verification
RUNTIME (기반 시설): 시계('지금' 주입) · 일정 · 저장소 접근 · 전송 · 배차 · 원장 · 생애 관리 — 뜻을 정하지 않는다
```

**고리 하나가 아니라 두 길이다.** 명목 고리는 L1 → L11 이다. 안전 감시는 L9 가 **State Store 를 직접** 읽는 별도의 길이다. 안전
감시는 명목 고리를 기다리지 않고 안전 동작을 낼 수 있다 (BD-07).

---

## 3. 층 정의 — 책임과 금지

| 층 | 묻는 것 | 책임 | **금지** | 입력 → 출력 | 지금 코드에서 |
|---|---|---|---|---|---|
| L0 Source | — | 세계 · 런타임 · provider · 도구 · 사람 | — | — | — |
| L1 Observe | 무엇이 관측·보고되었나 | 원천의 값을 정준 Observation 으로 옮긴다. 보고된 null 과 못 본 값을 가른다. 공급자 모양을 여기서 정규화한다 | 해석 · 문턱 · 판정 · 정책 제안 · 상태 쓰기 | 원천 → Observation(+Telemetry 봉투) | Sensor `telemetry/`, `state/normalize.py`, `providers/` · MS `telemetry.py`, `providers/`, `run_telemetry.py` |
| L2 Measure | 관측에서 무엇을 계산할 수 있나 | 결정론적 산술 · 집계(비율 · 창 · 백분위). 입력이 모자라면 UNKNOWN | 뜻 붙이기(HIGH 등) · 빈 칸을 옛 값으로 메우기 | Observation → Measurement | Sensor `state/metrics.py` · MS `manager.evidence` 창 |
| L3 Estimate | 시스템이 지금 무엇이라고 믿나(명목) | Model 의 규칙으로 실체마다 상태를 짓는다. 유효성 · 신선도 · 근거 · 전이 · 생애 | 행동 고르기 · 원 측정을 상태로 두기 · LLM 의견 받기 · 시계 읽기 | Measurement → State | Sensor `state/engine.py` · MS `manager.py` · `usage_model.py` |
| L4 Assess | 무엇이 고장 났나 · 건강한가 · 왜 | 고장 탐지(잔차 · 선언된 오류 · 문턱 사건) · 격리(관계 그래프로 공통 원인 찾기) · 진단 · 건강 상태 | **행동 고르기**(RETRY · ACCEPT 등) · 다음 실행의 설정 제안 | State · Measurement · Model(기대값 · 고장 모드) → 건강/고장 State | Sensor `sensors/` · `residual.py` · `fusion.py` · (`verifier.py` 의 판정 부분 **제외**) · MS 품질 상태 |
| M Model | 이 상태는 무엇을 뜻하나 | 정의 · 값 집합 · 규칙 · 바인딩 · TTL · 목적 · 행동 명세 · 고장 모드 · 안전 제약 · 운영자 가정 | 실행 · 실행 중 값 바꾸기(바꾸면 판본을 올린다) | — (판본별로 불변) | Sensor `registry.py` · `rules.py` · `config.py` · MS `model.py` · `usage_model.py` · DC `purpose.py` |
| R Relationship | 무엇이 무엇과 어떻게 이어졌나 | 유형 있는 간선. 실체 간선은 저장소에, 유형 규칙은 M 에 | 행동을 담기 · 측정값 복사 | → Relationship | Sensor `engine.relationships` · MS `graph.edges` |
| E Evidence | 이 값을 무엇이 받치나 | 출처 · 시각 · 근거 종류 · 판본을 **참조로** 남긴다 | 원 측정값을 위층으로 복사 | → 출처 연결 | Sensor `Evidence` · `explain()` · DC `evidence_refs` |
| L5 Contextualize | 이번 결정에 무엇이 필요한가 · 무엇이 가능한가 | 목적별 선택(Select) → 신선도(Filter) → 검사(Validate) → 투영(Project) → 고정(Freeze). 제약 · 능력 · 가능 행동을 붙인다 | 상태 계산 · 행동 선택 · 목적함수 · 프롬프트 짓기 · 실행 | State Store + 요청 → DecisionContext | DC 저장소 (기준 구현으로 삼는다, BD-05) |
| L6 Decide (Policy) | 무엇을 할까 | DecisionContext → Decision(ActionIntent 후보 + 까닭). 판본 · 재현 | 원 텔레메트리 읽기 · 상태 쓰기 · 센서 전송 정의 · 허가하기 · 실행 | DC → Decision | MS `policy.py`(Provider) · LLM 제안 · Sensor `policy/`(참조) |
| L7 Validate | 이 의도는 꼴이 맞고 자기 근거에 서 있나 | 형식 · 인자 · DC 안에서의 근거 확인 | 고르기 · 허가 | Intent → 유효 Intent | MS A0 · A1 · A2 · A3 · A4 (제안 매핑, OQ-04) |
| L8 Arbitrate | 후보 가운데 무엇을 고르나 | 여러 정책 · 목표 · 우선순위 사이의 명시적 선택. 규칙 · 판본 · 기록 | 허가(Guard 의 일) · 숨은 정책 | 유효 Intent[] → 선택 Intent | **없음** (GAP-02) |
| L9 Guard (Safety/RTA) | 고른 것을 지금 실행해도 되나 | 안전 제약 · 권한 · 자원 한도 · 지금 상태의 신선도 · 사전조건 · 되풀이. **닫는 쪽으로만** 개입한다. 안전 동작으로 전환한다. shadow/enforce | 허가를 **더하기** · 명목 최적화 · 프롬프트나 LLM 말에 영향받기 | 선택 Intent + **지금 State** → 허가 · 거부 · 안전 동작 | MS A5 · A6 · A7 · A8 (제안 매핑, OQ-04) |
| L10 Execute | 실행한다 | ActionCommand 를 실행기에 보낸다. 결과를 Observation 으로 돌려준다 | 상태를 직접 쓰기 · 허가 없이 실행 | 허가된 Command → Outcome Observation | MS `tools.ToolSpec.run` (호출 자리 하나) |
| L11 Verify | 의도한 효과가 났나 | 행동 명세의 사후조건과 관측된 다음 상태를 견준다. 검증 결과를 상태로 남긴다 | 행동 다시 고르기(그것은 다음 L6) | Command + 사후조건 + 다음 State → Verification | 없음 (GAP-05). 평가용 `check_success` 만 |
| Runtime | — | 생애 · 일정 · 시계 주입 · 저장소 접근 · 전송 · 배차 · 원장 · 안전 감시 구동 | 뜻을 다시 정하기 · 상태 계산 · 정책 내장 | — | MS `runtime.py` · `pipeline.py` |

---

## 4. 데이터 소유 · 생애 · 범위

### 4.1 저장소 (쓰는 쪽은 하나뿐이다)

| 저장소 | 담는 것 | **유일한 쓰는 쪽** | 읽는 쪽 | 바뀜 | 영속 | 다시 지을 수 있나 |
|---|---|---|---|---|---|---|
| Observation Log | Observation (덧붙이기만) | L1 (Runtime 의 ingest 를 통해) | L2 · Evidence 해석 · 감사 | 불변 | **영속** (권위 있는 원본) | 아니오 — 원본이다 |
| Model Registry | 판본별 정의 · 운영자 가정 | 사람(변경 절차 + 판본 올림) | 모든 층 | 판본마다 불변 | **영속** | 아니오 |
| Measurement Ledger | Metric 값 | L2 | L3 · L4 · explain | 덧붙이기 | 선택 (감사용) | **예** — Observation Log + 모형 판본에서 |
| State Store | 현재 State · 이력 · 전이 · 생애 사건 | L3(명목 규칙) · L4(건강 규칙). **상태 이름마다 규칙 하나가 소유한다** | L5 · L9 · L11 · 질의 · explain | current 는 소유 규칙만, 이력은 덧붙이기 | 스냅숏은 최적화 | **예** — 사건 재생으로 |
| Relationship Store | 실체 간선 + 유효 구간 | L3 (관측에서) · Runtime(구조 선언) — OQ-07 | L5 · L4(격리) · 질의 | 덧붙이기 + 유효 구간 닫기 | 선택 | 예 (관측분) / 아니오 (선언분) |
| Opinion Store | LLM · 사람의 해석 제안 | 누구나 | 감사만. **L3 · L5 는 읽지 않는다** | 덧붙이기 | 선택 | — |
| DecisionContext Store | 고정된 DC (내용 주소) | L5 | L6 · 원장 · 재현 | 불변 | 원장과 같은 보존 | 예 (State 이력 + 같은 as_of 에서) |
| Decision Ledger | DecisionRecord (단계마다 자기 절을 덧붙인다) | L6–L11 (각자 자기 절만) | 재현 · 감사 · 텔레메트리 참조 | 덧붙이기 | **영속** | 아니오 |
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
데이터는 앞으로만 흐른다:   L1 → L2 → L3 → L4 → L5 → L6 → L7 → L8 → L9 → L10 → L11
되먹임은 한 길뿐이다:       L10/L11 의 결과 · 모든 단계의 자기 텔레메트리 → L1 (Observation 으로)
M 은 모두가 읽고 아무도 실행 중에 쓰지 않는다
```

| 읽는 쪽 \ 읽을 수 있는 것 | Obs | Meas | State | Rel | DC | Ledger | M |
|---|---|---|---|---|---|---|---|
| L2 Measure | ✔ | — | — | — | — | — | ✔ |
| L3 Estimate | — | ✔ | 자기 이전 값 | ✔ | — | — | ✔ |
| L4 Assess | — | ✔ | ✔ | ✔ | — | ✔ (행동 결과 참조) | ✔ |
| L5 Contextualize | — | — | ✔ | ✔ | — | — | ✔ |
| L6 Policy | — | — | **✘** | — | ✔ (오직 이것) | — | 자기 판본 |
| L7–L8 | — | — | ✘ | — | ✔ | — | ✔ |
| L9 Guard | — | — | ✔ (**지금** 값) | ✔ | ✔ | ✔ | ✔ |
| L10 Execute | — | — | ✘ | — | — | ✔ (허가) | ✔ |
| L11 Verify | ✔ (결과) | ✔ | ✔ | — | ✔ | ✔ | ✔ |

**저장소 사이 코드 의존 (제안, OQ-08):** `Telemetry`(계약 · 잎) ← `Sensor` · `MS`. `DC` 는 아무것도 import 하지 않는다(소스 규약, 덕 타이핑).
`MS` → `DC`. `Sensor` 는 `DC` · `MS` 를 import 하지 않는다. Guard · Action 은 Policy 를 import 하지 않는다(§10).

---

## 6. 경계 위반 (BV)

| # | 위반 | 근거 (파일:줄) | 어느 경계 |
|---|---|---|---|
| BV-01 | Sensor 판정기가 **판정과 정책 제안**을 함께 낸다(ACCEPT · RETRY + `token_budget` · `route` 등) | `Sensor/llmsensor/verifier.py:63,65,81,87,92` | L4 ↔ L6 (진단 ≠ 결정) |
| BV-02 | 상태 층이 정책 입력을 짓는다. 그 안의 `why` 문자열에 원 수치가 남는다 | `Sensor/llmsensor/state/engine.py:276-311` | L3 ↔ L5, I1 |
| BV-03 | 운영자 설정(예산)을 텔레메트리로 넣는다. 그래서 파생 상태의 시각이 세션을 연 시각에 묶여 늙는다 | `MS/ms/usage_model.py:92-94,147-154` · `MS/ms/manager.py:152` | Config ≠ Observation |
| BV-04 | 실행 텔레메트리(RunRecord)가 정책 결정의 **내용**(state · plans · arbiter_decision)을 싣는다 | `MS/ms/runtime.py:168` · `MS/ms/run_telemetry.py` (`policy` 칸) | Telemetry ≠ Decision Ledger |
| BV-05 | 안전에 가까운 제한(되돌릴 수 없는 도구를 좁힘)이 CR/Policy 의 계획 안에 있다 | `MS/ms/policy.py:113` | L6 ↔ L9 |
| BV-06 | Arbiter 한 부품이 형식 검사 · 근거 · 낡음 · 허가 · 되풀이를 모두 한다. 정작 고르기는 하지 않는다 | `MS/ms/arbiter.py` (A0–A8) | L7 · L8 · L9 를 합쳤다 |
| BV-07 | CR 이 DC 를 거치지 않고 그래프를 직접 질의해 LLM 맥락을 짓는다 | `MS/ms/cr.py:70-72` | L5 를 우회 |
| BV-08 | Runtime 이 DC 대신 `usage_model.snapshot()` 을 정책에 준다. 이 값은 신선도 · 근거가 없다 | `MS/ms/runtime.py:80` | L5 를 우회 |
| BV-09 | 텔레메트리 꼴이 만들어질 때 시계를 읽는다(`ts` 기본값 `time.time`). StateManager 의 기본 시계도 같다 | `MS/ms/telemetry.py:24` · `MS/ms/manager.py:35` | Runtime 만 시계를 읽는다 |
| BV-10 | Runtime 이 과업 성공을 판정한다(평가 하니스의 일) | `MS/ms/runtime.py:36` `check_success` | Runtime ↔ 평가 |
| BV-11 | 정책이 Sensor 저장소 안에 산다(이름은 "참조"다) | `Sensor/llmsensor/policy/*` | 저장소 경계 |
| BV-12 | LLM 의 판단 문장(`post_turn_summary`)을 결과 근거로 쓰자는 제안이 있었다. 지금은 쓰지 않지만 규칙으로 막혀 있지 않다 | `Sensor/docs/MS_HEALTH_INVENTORY.md` §2 | Opinion ≠ Observation |

## 7. 중복 개념 (DUP)

| # | 개념 | 어디에 둘 이상 | 정리 (제안) |
|---|---|---|---|
| DUP-01 | **Evidence** | Sensor: 근거 참조 / MS: 원 측정 창(role="evidence") / DC: `evidence_refs` | Evidence = 출처 연결. MS 의 것은 **Measurement 창**으로 이름을 바꾼다 (BD-06) |
| DUP-02 | 텔레메트리 꼴 | Sensor llm-telemetry/v3 · MS Telemetry/RunRecord | Telemetry 저장소가 정준 Observation 봉투를 갖는다 (OQ-08) |
| DUP-03 | 상태 층 | Sensor StateEngine · MS StateManager | 상태 하나의 의미 규약(유효성 · 신선도 · 근거)을 공유한다. 엔진을 합칠지는 OQ-09 |
| DUP-04 | Decision Context | 4 개 (§1.2) | DC 저장소를 기준 구현으로 삼는다 (BD-05) |
| DUP-05 | StateView | Sensor `state/model` · Sensor `decision/context` · DC `model` | DC 의 StateView 하나 |
| DUP-06 | 목적 · 행동 어휘 | DC: context_policy · provider_selection … `KEEP_PROVIDER` / Sensor: manage_context · select_provider … `STAY_PROVIDER` · `WAIT` | Model Registry 의 목적 표 하나 (OQ-10) |
| DUP-07 | "Model" | 의미 모형 · PerformanceModel · OutcomeModel · LLM 모형 id | Model = 의미 · 지식 모형. 나머지는 `expectation model`(M 의 일부) · `fusion model`(L4) · `provider_model` |
| DUP-08 | "Decision" | MS `arbiter.Decision`(판정) · Sensor `policy.Decision`(행동) · Verifier `Verdict` · MS "Context Decision" | Decision = L6 의 출력뿐. 나머지는 ValidationResult · ArbitrationResult · GuardResult · AcceptanceAssessment · LLMContext |
| DUP-09 | 내용 해시 | DC 정준 JSON(`allow_nan=False`) · Sensor `default=str` | 정준화 규칙 하나 (SCHEMA §6) |
| DUP-10 | "MS" | MS 저장소 · Sensor 의 "MS 센싱" | Sensor 쪽은 "sensing expansion" 으로 부른다 |
| DUP-11 | `context_pressure` | Sensor: 런타임 선언 문턱 / MS: 손으로 둔 띠 | 다른 상태다. MS 쪽 이름을 `context_budget_pressure` 로 (DC 는 이미 키로 가른다) |
| DUP-12 | Proposal | MS: LLM 의 행동 제안 / Sensor: LLM 의 상태 해석 제안 | 앞은 ActionIntent, 뒤는 Opinion |
| DUP-13 | 유효성 · 근거 어휘 | DC `BASES` 5 개 ⊂ Sensor `Basis` 8 개(PROVIDER_DECLARED · VALIDATED_EXPERIMENT · EXTERNAL_LABEL 빠짐). MS 는 None 하나 | 어휘 하나를 계약으로 (SEMANTIC §3) |

---

## 8. 정규 런타임 고리

```
OBSERVE → ESTIMATE → ASSESS → CONTEXTUALIZE → DECIDE → VALIDATE → ARBITRATE → GUARD → EXECUTE → VERIFY → (OBSERVE)
  L1       L2+L3       L4         L5             L6        L7          L8         L9       L10       L11
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
| LLM 맥락 짓기 (CR) | DECIDE 안의 **정책 실행기 어댑터** (제안) | OQ-01 — 사용자가 앞서 다른 자리를 정했다 |

**방아쇠 (기본은 사건 구동이다, BD-14):** 관측 도착 → L2–L4 → 바뀐 상태의 생애 사건. 결정 요청 · DC 가 가리키는 상태의 (값,
유효성) 변화 · TTL 만료 → L5. Guard 는 모든 명령 배차 때 돌고, 안전 관련 상태가 바뀔 때도 돈다.

## 9. FDIR · 안전 경계 (요약 — 부품별 표는 [`DATA_FLOW.md`](DATA_FLOW.md) §5)

1. **고장도 상태다.** 건강 · 고장 상태는 L4 의 규칙이 쓰고 State Store 에 산다. 유효성 · 신선도 · 근거 규약은 명목 상태와 같다.
2. **관측이 없는 것은 건강이 아니다.** `NO_FAILURE_OBSERVED` ≠ `HEALTHY`. 관측 상실도 그 자체로 고장 상태다(관측 가능성 상실).
3. **환경 변화와 고장을 가르는 근거는 Model 에 적힌 고장 모드다.** 고장 모드가 없으면 판정하지 않고 UNKNOWN 이다(지어내지 않는다).
4. **Guard 는 닫는 쪽으로만 간다.** 여러 고장의 제약은 논리곱으로 묶는다. 가장 엄한 것이 이긴다. 안전 동작의 순서는 Model 에 있다.
5. **Policy 는 Guard 를 넘지 못한다.** 거부는 원장과 자기 텔레메트리로 돌아간다. 다음 결정은 그것을 관측으로 본다. "강제" 경로는 없다.
6. **Guard 가 터지면 거부다**(enforce). shadow 에서는 기록하고 진행한다. 바뀌는 것은 모드뿐이다. 불변식은 코드에서 빠지지 않는다
   (사용자 결정, MS `docs/계획.md` §3-3).

---

## 10. 저장소 지도와 구현 순서 의존 그래프 (시퀀싱 엔진이 읽을 것)

### 10.1 층 → 저장소 (현재 · 제안)

| 층 | 지금 | 제안 | 상태 |
|---|---|---|---|
| 계약 (어휘 · 꼴 · 실체 id · 시간 기준) | 세 저장소에 흩어짐 | **baseline** (문서 + 기계가 읽는 계약) | 이 문서 |
| L1 Observe · 정준 Observation 봉투 | Sensor · MS 따로 | **Telemetry** (계약 + 봉투 + 검증기), 수집기는 Sensor | Telemetry 비어 있음 |
| L2–L3 Measure · Estimate | Sensor · MS | Sensor(실행 단위) · MS(세션 단위) — 합칠지는 OQ-09 | 있음 |
| L4 Assess (FDIR · 건강 · 검증 L11) | Sensor verifier · MS 품질 상태에 섞임 | **Health** (새) | 없음 |
| L5 Contextualize | DC + 셋 더 | **DC** | 있음 (MS 미배선) |
| L6 Decide | MS · Sensor 참조 | MS (CR · Provider Policy) | 있음 |
| L7–L9 Validate · Arbitrate · Guard | MS Arbiter | **Guard** (새) — Policy 와 독립 | 없음 |
| L10 Execute | MS 도구 | **Action** (새) — ActionIntent · Command · Executor · Outcome | 없음 |
| Runtime | MS `runtime.py` | MS (지금은) | 있음 |
| 시퀀싱 (개발 순서 관리) | 없음 | **Sequencing** (새, 위 저장소들이 선 뒤) | 없음 |

### 10.2 의존 그래프 — 무엇이 무엇보다 먼저 굳어야 하나

```
baseline 계약 ──► Telemetry 봉투 ──► Sensor/MS 의 L1 정규화 ──► State 규약 공유 ──► Health(L4)
      │                                                    │
      │                                                    └──► DC 배선(MS Runtime) ──► Policy(ActionIntent 출력)
      │                                                                                        │
      └──► Action 꼴(ActionIntent · Command · Outcome) ─────────────────────────────────► Guard(L7–L9) ──► Executor ──► Verify(L11)
```

규칙: 화살표의 꼬리가 **계약 동결** 상태가 되기 전에는 머리를 구현하지 않는다. 시퀀싱 엔진은 이 그래프와 §11 의 판정표를 읽는다.

---

## 11. 승인 시험 (§14 of the brief)

판정: **A** = 이 기준선으로 답이 정해진다 · **B** = 미결 질문에 막혀 있다 (그 질문이 풀릴 때까지 구현하지 않는다).

| 물음 | 답 | 판정 |
|---|---|---|
| State 란? | 실체 · 이름마다, 판본 있는 규칙이 Measurement 에서 지은, 지금 참이라고 믿는 값 + 유효성 · 신선도 · 근거 (SEMANTIC §2.3) | A |
| Model 이란? | 판본 있는, 실행 중 읽기만 하는 정의 · 규칙 · 명세의 묶음 | A |
| Relationship 이란? | 유형 있는 간선(주어 · 술어 · 목적어 · 유효 구간 · 근거). 행동이 아니다 | A |
| Decision Context 란? | 한 목적에 대해 State Store 에서 고른 최소 충분 정보의 고정 스냅숏 | A |
| Policy 는 어디에? | L6. DC → Decision. MS 의 Provider Policy, LLM 실행기 | A |
| Action 은 어디에? | L10 Action 저장소 (아직 없음) | **B** (OQ-05 실행기의 주체) |
| Arbitration 은 어디에? | L8 Guard 저장소 안의 명시적 단계 | **B** (OQ-04 A0–A8 매핑) |
| FDIR 은 어디에? | 탐지 · 격리 = L4 · 복구 결정 = L6(목적 recovery) · 제약 = L9 · 검증 = L11 | A |
| Runtime 은 무엇을 소유하나? | 시계 · 일정 · 저장소 접근 · 전송 · 배차 · 원장 쓰기 순서 · 생애. 뜻은 소유하지 않는다 | A |
| 칸마다 소유자는? | SCHEMA §2–§3 | A |
| 무엇이 원 값 · 파생인가? | SEMANTIC §5 | A |
| 무엇이 영속 · 만료하나? | §4.1 · SCHEMA | A |
| 무엇을 보내고 무엇을 다시 짓나? | SCHEMA §4.3 (core 는 보내고, 파생 칸은 읽을 때 다시 계산한다) | A |
| DC 칸마다 왜 필요한가 · 무엇을 뺄 수 있나? | SCHEMA §4.2 | A |
| 신선도를 정하는 것은? | min(소스 TTL, 목적 max_age). TTL 은 Model(운영자 가정) | A |
| 관련성을 정하는 것은? | 목적 명세(Model). 질의형 선택은 아직 없다 | **B** (OQ-06) |
| 관측 → 상태 → 근거 → DC → 결정 | DATA_FLOW §2 | A |
| 결정은 어떻게 묶이나? | L7 → L8 → L9 | **B** (OQ-04) |
| 행동은 어떻게 실행되나? | L10 | **B** (OQ-05) |
| 행동 성공은 어떻게 검증하나? | L11 사후조건 대 관측 | **B** (OQ-11 사후조건을 어디에 적나) |
| 센서가 고장 나면? | DATA_FLOW §6.1 | A |
| 상태가 낡으면? | STALE 은 쓸 수 없다. Guard 가 배차 때 다시 본다 | A |
| Policy 와 Safety 가 다르면? | Guard 가 이긴다 | A |
| 고장이 여럿이면? | DATA_FLOW §6.4 | A |
| 유효한 DC 가 없으면? | 목적의 안전 기본 결정 | **B** (OQ-03) |

**결론: B 가 7 개다. 기준선은 아직 승인될 수 없다.** 다만 A 로 판정된 부분 — 관측 · 측정 · 상태 · DC 의 경계, 그리고 Telemetry 계약 —
은 OQ 와 무관하게 먼저 동결할 수 있다.

## 12. 승인 뒤에 고칠 파일 (지금은 고치지 않는다)

[`DECISION_LOG.md`](DECISION_LOG.md) 끝의 PC 표에 모았다. 각 PC 에 까닭 · 의존 · 위험을 적었다.
