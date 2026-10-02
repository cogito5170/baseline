# OPEN QUESTIONS (baseline-1.0 — 승인 2026-10-02)

## 현황

사용자는 2026-10-02 에 "권고안대로 결정" 했다. 그래서 **24 개 가운데 22 개가 결정되었다.** 결정은 [`DECISION_LOG.md`](DECISION_LOG.md)
BD-21–BD-42 에 있다. 아래 큰 표는 그 결정의 **근거 기록**으로 남긴다(선택지 · 권고).

| OQ | 결정 | OQ | 결정 | OQ | 결정 |
|---|---|---|---|---|---|
| 01 | BD-21 | 09 | BD-29 | 18 | BD-37 |
| 02 | BD-22 | 10 | BD-30 | 20 | BD-38 (확인할 일은 남음) |
| 03 | BD-23 | 11 | BD-31 | 21 | BD-39 |
| 04 | BD-24 | 12 | BD-32 | 22 | BD-40 |
| 05 | BD-25 | 13 | BD-33 | 23 | BD-41 |
| 06 | BD-26 | 14 | BD-34 | 24 | BD-42 |
| 07 | BD-27 | 15 | BD-35 | **17** | **OPEN** |
| 08 | BD-28 | 16 | BD-36 | **19** | **OPEN** |

### 남은 미결 둘 — 승인을 막지 않는 까닭과 막는 것

| OQ | 무엇을 정해야 하나 | 왜 기준선 승인을 막지 않나 | 무엇을 막나 · 언제까지 |
|---|---|---|---|
| **OQ-17** 안전 동작 순서 | 안전 동작이 여럿 요구될 때 고르는 **전순서**. 예: STOP > HOLD/WAIT > ESCALATE | 의미는 정해져 있다: "Model 에 판본 있는 전순서를 두고, Guard 는 그 순서에서 가장 앞선 것을 고른다"(DATA_FLOW §6.4). 남은 것은 순서의 **값**이다. 값은 문턱과 같은 Model 의 운영자 가정이다 | **Guard 를 enforce 로 켜기 전**(PC-10 의 둘째 단계). shadow 에서는 순서 없이 기록만 한다 |
| **OQ-19** 인코딩 · "표준 라이브러리만" 규칙 | (a) 규칙을 지킨다 → JSON 이나 자체 바이너리 (b) 의존성을 허용한다 → CBOR · MessagePack · Protobuf 도 후보 | 인코딩은 순서상 스키마 **다음**이다(§15 of the brief). 기준선은 일부러 고르지 않았다(BD-18) | **부품 사이에 프로세스를 넘는 전송이 처음 생길 때**. 그 전까지는 지금처럼 정준 JSON(해시용)만 쓴다 |

---

## 근거 기록 — 결정 전의 선택지와 권고 (바꾸지 않는다)

| # | 물음 | 선택지 | 권고 | BLOCKS |
|---|---|---|---|---|
| OQ-01 | **CR 의 자리.** 사용자는 2026-10-02 에 "CR = decision context construction rule, DC 와 Policy 사이" 로 정했다. 이 기준선은 DC 를 "결정에 필요한 최소 충분 정보" 로 정의한다. 두 정의가 겹친다 | (a) CR 은 DC 를 받아 **LLM 에게 그리는** 어댑터다(Policy 실행기 쪽). 새 정보를 더하지 않는다 (b) CR 이 DC 의 한 종류다(LLM 정책용 DC 를 짓는다) (c) 지금처럼 CR 이 그래프를 직접 질의한다 | (a). 대신 OQ-06 으로 DC 가 질의형 선택을 맡는다. (c)는 BV-07 | PC-05 · CR v2(사용자 순서 ④) |
| OQ-02 | Assessment(ASSESS) · Verify(VERIFY)를 **Health 저장소**로 따로 둘까, Sensor 안에 둘까 | (a) 새 Health 저장소 (b) Sensor `state/` 옆 (c) MS 안 | (a). 진단이 Sensor 판정기 · MS 품질 상태에 흩어진 것을 한 곳으로 모은다. 다만 (b)도 경계(규칙 소유)만 지키면 된다 | PC-06 |
| OQ-03 | **유효한 DC 가 없을 때의 안전 기본 결정**은 목적마다 무엇인가 | MS: 모름 = 고정 정책 · Sensor 참조 정책: 완료 상태를 모르면 ESCALATE | 목적마다 Model 에 `default_decision` 을 판본으로 적는다. 행동을 바꾸지 않는 쪽(KEEP · STAY · 고정)을 기본으로 하고, 실행 제어만 ESCALATE | 승인 §11 "유효한 DC 가 없으면" |
| OQ-04 | **A0–A8 을 어디로.** 사용자 계획: Validate = A0 · A4 / Arbitrate = A1 · A2 · A3 · A5 · A8 / Guard = A6 · A7 | 이 기준선 제안: Validate = A0–A4 (의도가 꼴이 맞고 **자기 DC 안에서** 근거가 있나) / Arbitrate = 후보 사이 선택(지금은 해당 규칙 없음) / Guard = A5 · A6 · A7 · A8 (**지금** 상태 기준의 허가 · 낡음 · 되풀이) | 기준선 제안. 까닭: A5(맥락 뒤 상태 바뀜)와 A8(되풀이)은 "무엇을 고르나" 가 아니라 "지금 해도 되나" 다 | PC-10 · 승인 §11 |
| OQ-05 | **우리 정책의 행동을 누가 실행하나** (Sensor 세션의 S6 물음과 같은 물음) | (a) 새 Action 저장소의 실행기 (b) MS `tools.py` 를 그대로 (c) Claude Code 훅(PreToolUse)을 실행 경계로 (사용자 순서 ⑧) | (a)로 꼴(Intent · Command · Outcome)을 정한다. 첫 실행기는 (b)를 옮긴 것과 (c)의 shadow. Sensor 는 행동 기록을 내지 않는다(DATA_FLOW §7) | PC-19 · `action_state` · 승인 §11 |
| OQ-06 | DC 가 **질의형 선택**(조건에 맞는 실체 행들 — MS `StateQuery`)을 맡을까 | (a) DC 목적에 질의를 적는다 (b) CR 이 계속 그래프를 본다 | (a) | OQ-01 · 승인 §11 "관련성" |
| OQ-07 | 실체 관계를 누가 쓰나 | 관측에서(ESTIMATE) · 구조 선언(Runtime) · 둘 다 | 둘 다. 간선에 `basis`(OBSERVED · DECLARED)를 붙인다 | — |
| OQ-08 | **저장소 사이 의존 방향 · 정준 텔레메트리 계약의 집** | (a) Telemetry 저장소가 정준 꼴을 갖고 Sensor · MS 가 따른다 (b) Sensor v3 가 곧 정준 (c) 각자 두고 대응표만 | (a). 내용은 Sensor v3 를 바탕으로, MS 의 자기 관측 칸을 더한다(SCHEMA §5) | PC-02 · PC-05 |
| OQ-09 | Sensor StateEngine 과 MS StateManager 를 합칠까 | 합침 · 의미 규약만 공유 | 지금은 **의미 규약만** 공유한다(유효성 · 신선도 · 근거). 합치기는 PC-02 · PC-05 뒤에 다시 본다 | — |
| OQ-10 | 목적 · 행동 이름 (`context_policy` 대 `manage_context`, `KEEP_PROVIDER` 대 `STAY_PROVIDER`, `WAIT` 의 유무) | DC 이름 · Sensor 이름 · 새 이름 | DC 이름 + Sensor 의 `WAIT` · `execution_interruption` · `quality_state` 를 더함 | PC-15 |
| OQ-11 | 행동의 **사후조건**과 검증 시간 창을 어디에 적나 | ActionSpec(Model) · 도구 정의(MS `ToolSpec`) | ActionSpec 에. MS ToolSpec 은 그 투영 | 승인 §11 "검증" |
| OQ-12 | **실체 id 이름공간** · 계정 실체 | `<유형>:<범위>:<지역>` 등 | 요금 한도는 `account:*` 실체 (Sensor 조사) | PC-02 · PC-20 |
| OQ-13 | 시간 기준 | MS 는 초, Sensor · DC 는 ms | 경계에서 ms + `time_base` | PC-12 |
| OQ-14 | 진단 가설과 `supports` 관계를 둘까 | 지금 · 나중 | 나중(고장 모드 모형이 선 뒤) | — |
| OQ-15 | `execution_health` 같은 건강 성격 상태의 소유 규칙을 ASSESS 로 옮길까 | 옮김 · ESTIMATE 에 둠 | 이름 · 값은 그대로 두고 소유 층 표시만 ASSESS 로 | — |
| OQ-16 | **신뢰도 표현.** Q 는 보정 전에는 확률이 아니라 순서 점수다(SWE-bench: 보정 Q 0.73 대 토큰 수 0.71, 차 구간이 0 을 걸침) | `confidence{kind, value}` 칸 · 없음 | 칸을 두되 `kind=ordinal` 은 Guard · 정책이 문턱으로 쓰지 못하게 한다 | — |
| OQ-17 | 안전 동작의 순서 (STOP · HOLD/WAIT · ESCALATE …) | — | 사용자 결정 | DATA_FLOW §6.4 |
| OQ-18 | 결정 재사용 열쇠 | digest 그대로(as_of 포함) · as_of 를 뺀 core 해시 | 따로 둔다 | PC-07 |
| OQ-19 | 인코딩과 "표준 라이브러리만" 규칙 | 규칙 유지(JSON · 자체 바이너리) · 의존성 허용 | 규칙을 먼저 정한다. 인코딩은 그다음 | — |
| OQ-20 | NASA · Microsoft 원문 확인 | 네트워크 허용 후 확인 · 사용자가 원문 제공 | 원문을 확인하기 전까지 BASELINE §0 의 원칙은 "인용" 표시를 유지한다 | — |
| OQ-21 | **`resource_state` — 예산이 없으면 UNKNOWN 으로? 실행 중 비용으로도 판정?** (Sensor 세션 S7) | 아래 평가 | 아래 평가 | PC-03 |
| OQ-22 | **"시퀀싱 엔진" 의 뜻** | (a) 개발 순서 관리자: 저장소 · 세션의 일을 순서대로 지시하고 결과를 받아 다시 정한다 (b) 런타임 실행층(executive): 실행 중 명령 순서를 관리한다 | 사용자 글("병렬로 작업해서 순서가 바뀐다", "스케줄링 → 지시 → 피드백")은 (a)로 읽힌다. (b)라면 Runtime(EXECUTE 배차)의 일이고 Action 이 먼저다 | BD-20 |
| OQ-23 | 영속성: 모든 상태가 메모리에만 있다. 재시작하면? | 사건 재생 · 스냅숏 | Observation Log + Model 판본으로 재생 (State 는 다시 짓는다) | — |
| OQ-24 | Decision Ledger 는 어느 저장소의 것인가 | MS(Runtime) · Action · 따로 | Runtime(MS)이 쓰기 순서를 갖고, 꼴은 baseline 계약 | PC-11 |

---

## OQ-21 평가 — `resource_state` 를 바꿔도 되나 (Sensor 세션의 S7) → BD-39 로 채택

### (1) 예산이 없으면 UNKNOWN? — **권고: 바꾸지 않는다(NOT_APPLICABLE 유지).** 단, 예산이 반드시 있어야 하는 배치라면 다른 길로 잡는다.

| 근거 | 내용 |
|---|---|
| 뜻 | UNKNOWN = "판정할 **근거**가 없다(알 수 있었는데 모른다)". NOT_APPLICABLE = "이 배치에서 **정의되지 않는다**"(`Sensor/docs/STATE_LIFECYCLE.md` §1 이 예로 "예산 없음" 을 든다). 예산은 근거가 아니라 그 상태를 **정의하는 문턱**이다(BD-10). 문턱이 없으면 상태가 정의되지 않는다 |
| 실측 영향 | 기본 설정에서 301/301 실행이 NOT_APPLICABLE 이었다(`STATE_MODEL.md` §4). UNKNOWN 으로 바꾸면 **모든 결정 문맥에 영원히 풀리지 않는 불확실성 하나**가 붙는다. 그러면 UNKNOWN 의 신호 가치가 떨어진다 — "모른다" 가 "알 필요가 없다" 와 섞인다 |
| DC 동작 | DC 저장소에서 `resource_state` 는 두 목적 모두 **선택**이다(`required=False`). UNKNOWN 이 되어도 `complete` 는 바뀌지 않고 `uncertain` 목록만 늘어난다. Sensor DC 에서는 N/A 면 `omitted` 로 빠지던 것이 UNKNOWN 으로 남는다. 얻는 정보가 없다 |
| 진짜 걱정 | "예산이 있는데 설정이 빠졌다" 면 그것은 resource_state 의 불확실성이 아니라 **설정 고장**이다 → ASSESS 의 `config.conformance` 같은 건강 상태로 잡아야 한다. 예산이 필수인 배치는 Model 에 "필수" 로 적고, 없으면 그 고장 상태가 선다 |
| 함께 고칠 것 | **예산의 주인이 셋이다**: Sensor `StateConfig.cost_budget_usd` · MS `config.token_budget`(관측으로 들어옴, BV-03) · DC 의 요청 제약 `max_cost_usd`. 같은 실행에 두 값이 다르면 resource_state 와 Guard 의 판단이 갈린다. 먼저 주인을 하나로 정한다(BD-13) |

### (2) 실행 중에도 비용으로 판정? — **권고: 받아들인다. 조건 다섯 개와 함께.**

| 근거 · 조건 | 내용 |
|---|---|
| 근거 | 단가표로 계산한 비용이 런타임 보고 비용과 **정확히 같았다**(Anthropic 두 모형, `Sensor/docs/MS_SENSING.md` §5). 지표 `call_cost` · `cost_estimate` · `cost_estimate_error` 가 이미 있다(`llmsensor/sensing/cost/`) |
| 조건 1 — 근거 종류 | 토큰(OBSERVED) × 단가(PROVIDER_DECLARED)의 산술이다. ESTIMATE 가 아니다 → DC 가 기본으로 받는다. 상태의 근거 참조는 `cost_estimate` 지표 id + **단가표 판본**이다 |
| 조건 2 — 대체 | 실행 끝의 보고 비용이 오면 그것이 이긴다. 계산값은 "대체됨" 으로 표시한다(생각 토큰 추정과 같은 규약). 차이는 `cost_estimate_error` 로 남긴다 |
| 조건 3 — 단가 없는 호출 | 단가가 없는 모형이 하나라도 있으면 합은 모른다. 다만 **부분 합은 하한이다**(단가 ≥ 0). 그래서 `부분 합 ≥ 예산` 이면 **BUDGET_EXHAUSTED 는 증명된다**(DEFINITIONAL). WITHIN_BUDGET 은 합이 완전할 때만 낸다. 이렇게 하면 D3(`<synthetic>` 때문에 세션 전체가 None)에서도 소진은 잡힌다 |
| 조건 4 — 범위 | 단가표가 확인된 공급자 · 모형만. OpenAI · Gemini 는 실제 응답으로 확인하지 않았다 → 그 호출은 단가 없음(조건 3) |
| 조건 5 — 판본 | `resource-state-v2` 로 판본을 올린다. 옛 상태와 섞이지 않게 `rule_version` 으로 가른다. D3 고침(PC-20)을 먼저 하거나 같이 한다 |
| 비대칭 하나 | 비용은 줄지 않는다. 그래서 실행 중 `BUDGET_EXHAUSTED` 는 이후에도 참이다 → `permanent` 로 둘 수 있다. `WITHIN_BUDGET` 은 언제든 뒤집힐 수 있다 → 보통의 TTL |
