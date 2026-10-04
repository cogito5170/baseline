# NETWORK SPEC — Distributed Session Network (POL-3, BD-309)

사용자 요구사항 원문(2026-10-04). 이 파일은 바꾸지 않는다 — 해석 · 설계 · 매핑은 [`NETWORK.md`](NETWORK.md)에 둔다.
시점: "모든 것이 마무리 되면"(지금 진행 중인 K18 · GA28 뒤) 최종적으로 ga-sdk 를 이렇게 만든다.

## Distributed Session Network: Baseline → Peer-to-Peer Cognitive Network

### 0. 목적
현재 시스템은 하나의 Baseline이 여러 Session을 관리하는 중앙집중형 구조를 갖고 있다. 이를 다음 단계로 확장한다.
모든 Session을 Baseline 수준의 동등한 인지 노드로 승격시키고, Session 간의 높은 상호 연결도(π)를 형성하여, 개별 Session의 합을 넘어서는 집단적 상태와 판단 능력(collective cognition / emergent global state)을 형성한다.
여기서 목표는 단순히 Session 간 메시지를 증가시키는 것이 아니다. 각 Session이 다른 Session의 상태와 판단을 관측하고, 그 정보가 자신의 상태를 변화시키며, 그 변화가 다시 다른 Session에 전달되는 closed-loop interaction network를 만드는 것이다.

### 1. 기존 시스템을 존중하라
이미 시스템에는 다음과 같은 정보 구조와 교환 방식이 정의되어 있다: Baseline · Session · DecisionContext · Observation · tool/action · Result · Feedback · Context/Prompt Policy · State · Telemetry · 기존 session ↔ baseline communication protocol · 기존 validation / safety / runtime boundary.
이것들을 새로 설계하거나 중복 구현하지 않는다. 이미 정립된 데이터 구조와 통신 방식을 그대로 재사용한다. 새로운 Network layer는 기존 구조 위에 추가되는 orchestration / interaction layer여야 한다.

```text
Existing Protocol
        ↓
Existing Context / Observation / DecisionContext
        ↓
Existing Session Runtime
        ↓
NEW Peer Interaction Network
```

이지, 새로운 데이터 구조 · 새로운 context · 새로운 통신 프로토콜 · 새로운 memory 를 다시 만드는 것이 아니다.

### 2. Baseline의 의미를 변경한다
기존: Baseline이 모든 Session의 상위 판단자였다(Baseline → S1, S2, S3).
새 구조: 모든 Session이 Baseline-level node가 된다(S1 … S5 가 서로 직접 연결). Baseline은 더 이상 유일한 사고 주체가 아니다. 각 Session은 자신의 상태, 관측, 판단, 목표를 가지고 있으며 다른 Session과 직접 상호작용할 수 있다.

### 3. 핵심 개념: Session의 π
각 Session pair에 대해 동적 interaction weight π_ij(t) 를 정의한다. π는 단순한 network connection이 아니라 relevance · information value · state dependency · trust / validity · recent interaction history · uncertainty reduction · task dependency · feedback usefulness 를 종합한 interaction affinity다.

π_ij(t) = F(relevance, dependency, information value, trust, uncertainty, history)

π가 높을수록 S_i는 S_j의 상태와 Observation을 더 적극적으로 참조하고 상호작용한다.

### 4. Dense Potential, Selective Active Communication
모든 Session이 서로 연결될 수 있어야 하지만(∀i,j S_i ↔ S_j 가능), 모든 Session이 항상 모든 Session과 통신하지는 않는다. Potential connectivity: Dense / Active communication: Sparse·selective. 실제 interaction은 π_ij(t) > threshold 이거나 기존 policy가 필요하다고 판단할 때 활성화한다. 단순한 broadcast system이나 message storm을 만들지 않는다.

### 5. Session을 독립적인 인지 노드로 정의한다
각 Session은 최소한 State · Observation · Belief/interpretation · Goal/task context · DecisionContext · Policy · Interaction interface · Action/proposal 을 가진다. 단, 새로 구현하지 말고 현재 repository에 이미 존재하는 대응 구조를 찾아 재사용한다.
다른 Session의 메시지를 받으면 로그에 추가하는 것이 아니라 State_i(t+1) = F_i(State_i(t), Observation_i(t), Message_j→i(t)) 와 같이 자신의 다음 판단에 영향을 줄 수 있어야 한다.

### 6. Collective State를 형성한다
전체 Network를 하나의 동적 시스템으로 본다: **S**(t) = [S_1(t), …, S_N(t)], **S**(t+1) = F(**S**(t), **O**(t), G(t)), G(t) 는 Session interaction graph. 각 Session의 정보가 다른 Session을 변화시키고, 그 변화가 다시 네트워크 전체로 전파되는 feedback loop를 형성한다. 이것을 collective cognition / emergent global state의 공학적 기반으로 취급한다. 인간의 의식과 동일하다고 가정하지 않는다.

### 7. Interaction은 Action과 동일하지 않다
Session 간 interaction(S1 → S2 : information / observation / opinion / request)과 실제 external action(S2 → Tool → Environment)을 구분한다. 다른 Session이 보낸 의견이나 요청이 즉시 외부 Action으로 실행되어서는 안 된다. 필요하다면 기존 DecisionContext / validation / policy / safety mechanism을 통과시킨다.
Session A → Interaction → Session B → State/Belief update → Decision → Existing validation/policy → Action.

### 8. Feedback loop를 적극적으로 활용한다
단방향 pipeline(Baseline → Session → Tool → Result → Baseline)이 아니라 S1 ↔ S2, S3 ↔ S4 … 형태의 반복적인 feedback loop를 허용한다. 예: S1 "A라고 판단" → S2 "내 Observation은 A와 모순" → S1 "uncertainty 증가" → S3 "추가 Observation 필요" → S2 "새 Observation 전달" → S1/S2/S3 "Collective state 업데이트". 네트워크가 단순 message bus가 아니라 상호 상태 갱신 시스템이 되도록 한다.

### 9. Context Explosion을 방지한다
모든 Session에게 모든 메시지를 복사하지 않는다. 기존 Context/Prompt Policy(KEEP · SUMMARIZE · RETRIEVE · DROP)를 적용한다: Raw communication history → Existing context policy → Relevant state → Session. 새로운 memory compression system을 임의로 만들지 않는다.

### 10. Network는 스스로 연결 구조를 변화시킬 수 있어야 한다
π는 고정값이 아니다: π_ij(t) → π_ij(t+1). Repeatedly useful interaction → π 증가 · Irrelevant interaction → π 감소 · Contradictory information → 검증을 위해 interaction 증가 가능 · No information gain → interaction 감소. 최종적으로 self-organizing interaction graph를 목표로 한다.

### 11. 기존 Baseline의 역할
Baseline을 삭제하지 않는다. Central Decision Maker → Network Runtime / Protocol / Safety / Resource Boundary. 책임: protocol integrity · state consistency · validation · safety boundary · resource limits · interaction budget · session lifecycle · conflict resolution · network observability. 정상적인 cognition/decision을 Baseline 하나가 독점하지 않는다.

### 12. 구현 시 가장 먼저 해야 할 일
코드를 바로 대규모 수정하지 않는다. 먼저 repository를 분석하여 1 Session lifecycle · 2 Baseline lifecycle · 3 DecisionContext · 4 Observation · 5 Feedback · 6 Tool/action boundary · 7 Context/Prompt Policy · 8 State management · 9 Validation · 10 기존 Session ↔ Baseline communication · 11 telemetry · 12 현재 테스트 가 어디에 있는지 찾고, Existing Component → New Network Role mapping 을 작성한다. 새로운 abstraction이 정말 필요한 경우에만 추가한다.

### 13. 반드시 기존 구현을 깨뜨리지 않는다
기존 baseline path는 계속 동작해야 한다: Legacy / Baseline Mode 와 Peer Network Mode 를 모두 지원. 기존 테스트가 깨지면 1 원인 분석 2 기존 contract 유지 3 필요한 최소 변경만. 기존 protocol을 새 architecture에 맞추기 위해 임의로 변경하지 않는다.

### 14. 검증해야 할 핵심 지표
"Session끼리 통신했다"를 성공으로 판단하지 않는다. 최소한: Connectivity C = |E_active| / |E_possible| · Interaction usefulness U = useful / total · Information gain(상호작용 전후 uncertainty 감소량) · Context cost(Session당 전달된 context/token 양) · Convergence(반복 interaction 후 collective state 수렴) · Conflict rate(contradictory state 빈도) · Action quality(기존 baseline 방식 대비 실제 task 결과 개선).

### 15. 절대로 가정하지 말 것
높은 communication frequency = intelligence · 높은 π = consciousness · 많은 Session = better cognition · 모든 message 전달 = better context · LLM끼리 대화 = consciousness · emergent behavior 발생 = consciousness — 모두 가정하지 않는다. 먼저 만들고 검증할 것은 Distributed / Collective Cognitive Network 이고, 그 위에서 어떤 emergent property가 나타나는지 실험으로 확인한다.

### 최종 목표
Network Runtime / Protocol / Safety 아래 S1 ↔ S2 ↔ S3 ↔ S4(서로 연결) ↔ Collective State ↔ Existing Context Policy ↔ Decision / Action.
"Baseline이 모든 Session을 생각하게 하는 구조"에서 "모든 Session이 서로를 관측하고 영향을 주며, 네트워크 자체가 하나의 동적 인지 시스템으로 작동하는 구조"로 전환한다. 이 전환은 새로운 통신 규약이 아니라, 이미 구현 · 검증된 Context, Observation, DecisionContext, Feedback, Validation, Telemetry 및 Session communication mechanism 을 최대한 재사용해 구현한다.
