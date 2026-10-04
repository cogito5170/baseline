# NETWORK — Distributed Session Network 설계 (POL-3, BD-309)

요구사항 원문: [`NETWORK_SPEC.md`](NETWORK_SPEC.md). 이 문서는 그 12절("코드보다 먼저 분석")의 결과다 — 기존 구성요소 → 새 네트워크 역할 매핑, 정말 없는 것만 추린 최소 추가, 단계, 지표, 결정할 것.
분석 기준(2026-10-04): ga-sdk `6e15f57`(ga 0.2.0) · rlo-sdk `d190d95`(0.10.0) · DC · MS · Sensor · Telemetry · guard · action · health 로컬 사본 · `SEMANTIC_MODEL.md` · `PROTOCOL.md`.

## 0. 한 줄 결론

필요한 부품의 대부분이 이미 있다. **세션 사이 전송(ga mail), 새 것만 읽기(ga inbox), 메시지 검증(ga check · R6), 노드 한 턴(GA29 fresh + ctxpack), 상태 갱신 규칙(Sensor StateEngine), 의견의 무권한 규칙(Opinion · Proposal), 문맥 정책(MS KEEP/SUMMARIZE/RETRIEVE/DROP), 행동 경계(DC → Arbiter → Guard → Action), 예산(Governor · ctxbudget), 관측(L0)** 이 있다.
정말 없는 것은 넷이다: **(1) π(상호작용 가중치) (2) 노드가 스스로 도는 한 걸음(node step) (3) 세션을 실체로 다루는 데이터(엔티티 · 관계 · Purpose) (4) 메시지를 기록하는 L0 사건.** 새 통신 규약 · 새 메모리 · 새 context 는 만들지 않는다.

## 1. 기존 구성요소 → 새 네트워크 역할

| # | 12절 항목 | 기존 구성요소(위치) | 오늘 | 네트워크 역할 |
|---|---|---|---|---|
| 1 | Session lifecycle | ga `Session` 설정(config.py:64) · `Runner`/`TurnRequest`/`TurnResult`(adapters/base.py) · Headless/AgentSDK/Remote Runner · fresh 모드(GA29) | 허브가 지시를 보낼 때만 한 턴 | **노드 = Session + Runner**. 한 걸음 = fresh 한 턴 |
| 2 | Baseline lifecycle | ga `Hub.tick`(hub.py:741): 받기 → 통합 → 재현 → 판정 → 기록 → 다음 | 단일 루프 · 단일 판정자 | **Network Runtime**: 통합(R1b) · 판정 · 관문 · 예산 · 기록만. 생각은 노드가 함 |
| 3 | DecisionContext | DC `DecisionContext`(dc/model.py:300) · builder(Select→Filter→Validate→Freeze) · `Purpose`(purpose.py:78) · sources/bridge | 목적 하나에 대한 동결된 스냅숏, `Validity.uncertain` | 노드마다 결정마다 DC 하나 그대로. 동료 상태는 DC source 하나로 들어와 같은 검증을 받음 |
| 4 | Observation | Sensor `Observation`(llmsensor/state/model.py:75) · L0 envelope(telemetry/event.py) | 출처 · basis 를 가진 사실 | **동료 j 의 메시지 수신 = 관측된 사실**("j 가 X 라고 보냈다", source=session:j) |
| 5 | Feedback | MS `runtime.feedback`/`evaluation`(runtime.py:285) · usage_model SESSION(answer_reliability · correction_rate …) · Verifier | 결과 → Telemetry → 파생 State → 정책 조정 | **π 갱신의 재료**: 메시지가 상태를 바꿨나, 그 결정이 검증을 통과했나 |
| 6 | Tool/action boundary | MS Arbiter A0–A8(arbiter.py:47) · guard `_guard`(fail-closed) · action ActionIntent(`dc_id`) · executor · rlo hooks · ga bash_guard · sandbox | 막기만 하고 넓히지 않음 | 그대로. **동료 메시지는 Action 이 아니다** — 행동은 늘 이 길을 지남(A2: 본 적 없는 주장으로는 행동 불가) |
| 7 | Context/Prompt Policy | MS `ContextPolicy`(context.py:161, KEEP · COMPRESS · SUMMARIZE · RETRIEVE · DROP · DEFER) · AdaptiveContext · ga ctxpack(상한 · 우선순위 · 기록되는 drop) · rlo ctxbudget | QueryResult 행 + 예산 → 최소 문맥 | **동료 메시지 흐름에 그대로 적용**: 메시지를 MS 그래프 행으로 ingest → ContextPolicy → ctxpack 의 peer 구획 |
| 8 | State management | Sensor `State`/`StateEngine`(engine.py:21, 규칙 소유 · evidence · lifecycle) · state-export/2 · ga 노드 state.md(GA29) · hub state.json(단일 작성자) | 규칙만 State 를 씀 | **State_i 와 F_i = 기존 규칙 집합**. 동료에게 공개하는 꼴 = state-export/2. 허브 ledger 는 허브만 씀 |
| 9 | Validation | ga check · forms validate · R1–R13(R6 비밀) · gates 7 · DC Validate · MS ingest(묶이지 않은 입력은 격리) · pspec check | 형식 · 규칙 · 비밀 · 근거 | 모든 동료 메시지가 보내기 전(ga check · R6)과 받은 뒤(MS ingest · DC Validate) 두 번 검사 |
| 10 | Session ↔ Baseline 통신 | ga forms(directive/2 · report/2 · verdict/1 · notify/1 · **exchange/1** from+to) · **git Mailbox `ga mail`(to/sender, 이미 any-to-any)** · `ga inbox`(since 커서) · dump_wire · PROTOCOL §1a(세션 사이 대화는 기본 끔 · 행동 아님 · baseline 에 보고) | 허브 중심 사용, 전송은 이미 P2P 가능 | **동료 전송 = ga mail + ga inbox 그대로**. 꼴은 기존 form(관측 · 의견은 아래 §2.3) |
| 11 | Telemetry | Telemetry L0 catalog(닫힌 스키마, 해석어 금지) · ga l0.run_end(턴마다) · usage(l0_usage) · tokmon | 턴 · 토큰 · 도구 | 노드 · 간선 관측. **누가→누구 사건이 없음**(§2.4) |
| 12 | 현재 시험 | ga ~530(허브 루프 · 형식 · 규칙 · 채널 · 실행기 · fresh) · rlo 258+ · DC/MS/Sensor/Telemetry 각자 | 허브 모드 계약을 고정 | **Legacy 모드 회귀 바닥**: 모든 기존 시험이 Peer 모드 도입 뒤에도 그대로 통과 |

## 2. 정말 없는 것 — 최소 추가(데이터 먼저, 코드는 그 다음)

### 2.1 노드 한 걸음(node step) — ga
없음: 세션은 허브가 지시를 보낼 때만 돈다. 추가: `ga node step <me>` = **기존 부품의 조합**
`ga inbox mail:<me>`(새 것만) → MS ingest + ContextPolicy(동료 메시지 행 → 최소 문맥) → ctxpack(기존 구획 + `peer` 구획, 상한 그대로) → fresh 한 턴(GA29) → 답 검사(report/2 + state + 선택적 동료 메시지들) → state.md · 동료 메시지는 `ga mail send`(ga check · R6) · 행동은 기존 경계로.
노드는 `.ga/nodes/<me>/` 에만 쓴다 — 허브의 state.json · RecordStore(단일 작성자, R9)는 건드리지 않음.

### 2.2 π_ij — MS/Sensor 의 파생 State(새 저장소 아님)
없음: 가중치 · 신뢰 · 이웃 · 라우팅 전혀 없음. 추가: π 를 **노드 i 의 파생 State**(MS usage_model 의 '창 Measurement → 파생 band' 꼴 그대로)로 둔다. 재료(모두 기존 신호에서):
- usefulness: j 의 메시지 뒤 i 의 State 전이가 있었나(StateEngine transition 로그), 그 결정이 Verifier/판정을 통과했나
- information gain: 메시지 전후 i 의 DC `Validity.uncertain` · `missing_required` 개수 변화
- trust/validity: j 가 보낸 관측 중 DC Validate 에서 INVALID/STALE 된 비율(Sensor reading OK/SUSPECT/FAULT/UNKNOWN 틀; UNKNOWN = 증거 0)
- relevance/dependency: i 의 Purpose 가 요구하는 StateRef 와 j 가 공개한 state-export 의 겹침
- history: 시간 감쇠(엔진은 now 를 인자로 받음 — 결정론 유지)
활성화: π_ij > θ 이거나 기존 정책(Purpose 의 required 가 비었음 · 모순 감지)이 요구할 때만 보냄. 간선 예산 = rlo Governor(분당 메시지 · 토큰)를 간선 키로. **L0 에는 π 를 쓰지 않는다**(L0 는 해석어 금지) — π 는 State 에, L0 에는 사실(보냄 · 받음 · 바이트 · 토큰)만.

### 2.3 세션을 실체로 — 데이터 추가(코드 변경 최소)
- Sensor `EntityType` 에 `session`, 관계 술어 `informs` · `contradicts`(SEMANTIC_MODEL §4 의 보류 항목을 여는 것 — 언어 변경이라 baseline 결정)
- DC `Purpose` `peer_interaction`(PURPOSES 에 데이터로; 행동 consult · send · skip)
- MS Model binding `PeerMessage`(데이터) — 메시지가 MS 그래프 행이 되어야 ContextPolicy 를 탈 수 있음
- action `AUTHOR_KINDS` 에 `peer`(동료 때문에 생긴 의도를 구분) — 작은 계약 변경
- 메시지 꼴: 새 schema 대신 기존 `exchange/1`(from · to 가 이미 있음)을 쓰되 BD-133 '보고된 사실, 행동 아님' 의미 그대로; 본문은 Observation 참조(evidence id) 또는 Opinion. 부족하면 exchange/2 하나만(baseline 결정)

### 2.4 메시지 L0 사건 — Telemetry 계약 추가
`peer.message.sent` · `peer.message.received`(from, to, msg_id, in_reply_to, bytes, tokens_est) — 닫힌 catalog 에 두 줄 추가(해석어 없음). 이것으로 C · 문맥 비용 · 수렴 측정 가능.

## 3. 핵심 규칙(충돌 정리)

1. **메시지는 State 를 직접 쓰지 않는다.** 요구사항의 State_i(t+1)=F_i(State_i, O_i, M_j→i) 는 이렇게 지킨다: M_j→i 는 (a) "j 가 X 를 보냈다"는 관측된 사실과 (b) X 자체(j 의 관측이면 evidence 참조, 해석이면 Opinion → Proposal)로 들어가고, **i 의 기존 규칙 F_i 가** 그 관측으로 State 를 바꾼다. SEMANTIC_MODEL §2.18(의견은 권한 없음) · DC I7 과 충돌하지 않는다.
2. **상호작용 ≠ 행동.** 동료의 요청은 i 의 DC → Arbiter → Guard → Action 을 지나야만 행동이 된다(spec §7). Arbiter A2 가 '본 적 없는 주장'으로 행동하는 것을 막는다.
3. **같은 증거 두 번 세기 금지.** 여러 동료를 거쳐 온 같은 관측은 evidence/Observation id 로 하나로(Sensor fusion 코드가 이미 '독립 아니면 과신' 경고).
4. **Legacy 모드 불변.** Peer 모드는 설정으로만 켜고 기본은 끔(PROTOCOL §1a 그대로). R1/R1b(지시 없는 변경은 통합 안 함) 유지 — 동료 메시지는 지시가 아니다. 허브 채널에 동료 꼴이 섞이지 않게 전송을 분리(ga mail).
5. **Baseline 의 새 역할**(spec §11): 통합 · 판정(코드 변경의 받아들임) · 관문 7(새 세션 = 사람) · 비밀 · 예산(노드 · 간선) · 수명 · 모순이 수렴하지 않을 때만 중재 · 관측(tokmon + L0 간선). 정상적인 판단은 노드가.

## 4. 단계

| 단계 | 내용 | 맡는 곳 | 끝 조건 |
|---|---|---|---|
| P0 | 이 문서(매핑) | baseline | 사용자 확인 |
| P1 데이터 | EntityType session · 술어 · Purpose peer_interaction · MS PeerMessage binding · AUTHOR_KINDS peer · L0 peer.message.* | Sensor · DC · MS · action · Telemetry(각자 fresh 세션) | 각 저장소 기존 시험 그대로 + 새 데이터 시험 |
| P2 전송 · 한 걸음 | `ga node step` = inbox → MS ContextPolicy → ctxpack peer 구획 → fresh 턴 → mail send; `.ga/nodes/<me>/` | GA | Legacy 시험 전부 통과 + 가짜 노드 3 개 왕복 시험 |
| P3 π | π 를 파생 State 로(usefulness · info gain · trust · relevance · 감쇠), 임계 · 간선 예산 | MS · Sensor(+ rlo Governor) | 고정 시나리오에서 π 증가/감소 규칙 시험(spec §10 네 경우) |
| P4 실험 | 정답이 있는 과제에서 Legacy(중앙) 대 Peer(N=3–5, haiku) | baseline 이 설계 · 판정 | §5 지표 표 |

## 5. 지표(spec §14) — 어디서 재나

| 지표 | 정의 | 출처 |
|---|---|---|
| Connectivity C | 활성 간선 / 가능 간선(창 안) | L0 peer.message.* |
| Usefulness U | 쓸모 있던 상호작용 / 전체 — '쓸모' = 받은 뒤 State 전이 있음 그리고 그 결정이 검증 통과 | StateEngine 전이 로그 + Verifier/판정 |
| Information gain | 상호작용 전후 DC Validity.uncertain · missing_required 감소 | DC 스냅숏 쌍 |
| Context cost | 노드당 받은 문맥 토큰(peer 구획) · 호출당 문맥 | ctxpack 기록 · L0 run.end · tokmon |
| Convergence | 같은 StateRef 에 대한 노드들의 값이 반복 뒤 같아지는가(걸음 수) | state-export/2 비교 |
| Conflict rate | `contradicts` 관계 · 같은 키 다른 값 발생 빈도 | Sensor 관계 · export 비교 |
| Action quality | 같은 과제의 정답 대비 결과(Legacy 대 Peer) | 과제 검사기 |

비용도 지표다: Peer 모드는 노드 수만큼 턴이 늘어난다. 토큰 절감(BD-290 · 296)과 충돌하지 않게 간선 예산과 fresh 모드를 기본으로 하고, P4 에서 '토큰당 결과'를 같이 본다. spec §15 대로 높은 C · 많은 메시지 · 창발적 행동을 지능이나 의식의 증거로 보지 않는다.

## 6. 사용자 결정이 필요한 것

1. 규칙 3.1(메시지는 State 를 직접 쓰지 않고, 관측 + 의견으로 들어가 기존 규칙이 갱신) — spec §5 의 해석으로 받아들일지
2. 언어 · 계약 변경 넷: Sensor EntityType `session` · 술어 `informs`/`contradicts`, action `AUTHOR_KINDS` `peer`, Telemetry L0 `peer.message.*`
3. PROTOCOL §1a: Peer 모드에서만 세션 사이 대화를 켬(기본은 계속 끔)
4. 시작 시점: spec 대로 K18 · GA28 뒤 P1 부터. P4 실험의 노드 수 · 모델(haiku 권장) · 비용 상한
