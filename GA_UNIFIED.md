# GA_UNIFIED — rlo Autonomy 전체를 품은 하나의 ga (ga-unified-1 rev 1, 2026-10-03)

> 사용자 결정(BD-206): ① **하나의 ga** — 사용자는 ga 하나만 설치한다. rlo 일곱 층 코드는 지금 저장소에 두고 sha 고정 의존으로 끌어온다(소유 유지). ga_rlo 의 잇는 코드는 ga 안으로 옮기고 ga_rlo 는 정리한다. ② **설계서 먼저, 그다음 턴 안 ReAct.** ③ **가드만이 아니라 Autonomy 전체를 ga 와 배선한다.** ReAct 는 반드시 들어간다.
> 소유자는 baseline. 무엇을 해야 하는지만 정한다. 어떻게는 짓는 세션이 정한다(GUIDANCE 13). 이 문서는 GA_RLO.md(BD-164, 결합층)를 대신한다 — P1 의 "결합층" 을 "하나의 ga" 로 바꾸고, 나머지 원칙은 이어받는다.

## 0. 왜 — 감지는 있는데 대응이 없다

2026-10-03 AMP · W1 에서 rlo 는 문제를 **알고 있었다.** 그러나 가드만 썼기 때문에 막고 끝났고, 사람이 와야 풀렸다(BD-194 · 197).

| 일 | rlo 가 이미 알던 것 | 일어난 일 | 대응이 있었다면 |
|---|---|---|---|
| ReadNotifications 가 A1 | 규칙 · 허용된 도구 목록(action) | 사람이 풀 때까지 멈춤 | 같은 목적의 허용 도구(issue_read 로 통로 읽기)로 스스로 돈다 |
| 쉰 뒤 D | Sensor: 건강이 낡음 | 사람에게 물음(K10 뒤 힌트만) | 읽기 한 번 → 다시 시도 |
| 막혀도 조용함 | Telemetry 의 거부 기록 | 작업 컨테이너 안에만 | ga 보고 · 알림에 신호로 실려 허브가 본다 |
| AMP ↔ W1 서로 기다림 | Sensor 로 정체를 잴 수 있음 | baseline 이 손으로 찾음 | 허브가 VERIFY 로 "보고가 창 안에 오지 않음" 을 잡고 대안을 낸다 |

## 1. 원칙

- **U-P1 하나의 ga, 코드는 고정 의존.** 사용자 입구는 `ga` 하나. rlo-sdk[sensor] 를 sha 로 고정해 의존한다. rlo 층의 코드를 복사하지 않는다.
- **U-P2 고칠 곳은 주인에게.** rlo 층의 빈자리는 SDK 세션(rlo-SDK)이, ga 는 GA 가, ga 안의 rlo 배선 모듈은 GR 이 고친다. 우회하지 않고 `요청:` 으로 올린다.
- **U-P3 ReAct 는 넓히지 않는다.** 대안은 **닫힌 표**에서만 고른다. 허가(grant)를 늘리지 않는다. 허가 · 가드 변경 · 배포는 사람 몫(HUMAN_QUEUE, BD-205)이고, 기다리는 동안 멈추지 않는다.
- **U-P4 라벨만 흐른다.** 층 사이와 세션 사이로는 수와 라벨만 흐른다(`[A-Za-z0-9_.:+-]{1,40}`). 원문 · 경로 · 비밀값은 흐르지 않는다.
- **U-P5 구조가 먼저(GA_RLO P5 유지).** 명령 내용 · 쓰는 곳 · 네트워크는 샌드박스 · 격리 · bash_guard 가 맡는다.

## 2. 세 고리

```
                 ┌──────────── 허브 고리 (ga tick = Autonomy.handle) ────────────┐
 사람 ── HUMAN_QUEUE      세계(MS) = 세션 · 지시 · 저장소 · 사람 몫          │
                 │  Telemetry ← ga 사건      Sensor → 세션 상태(건강 · 진척 · 정체)   │
                 │  DC(목적: 보내기 · 통합 · 판정 · 올리기) → Guard → 실행기 → VERIFY │
                 └───────────────▲──────────────────────────────┬──────────────┘
                                 │ 보고 · 알림 + 신호(라벨)          │ 지시 · 알림
                 ┌───────────────┴──────── 통신 고리 ──────────────▼──────────────┐
                 │ report/notify 에 signals: 거부 수 · 규칙 · 실행 건강 · 정체 · 자원     │
                 └───────────────▲──────────────────────────────┬──────────────┘
                 ┌───────────────┴──────── 턴 고리 (작업 세션) ──────▼──────────────┐
                 │ 도구 호출 → rlo.hooks(Telemetry → Sensor → DC → Guard)            │
                 │   막히면 → ReAct: 까닭 → 닫힌 대안표 → 대안 → 다시 판정(상한) → 허브로 │
                 └──────────────────────────────────────────────────────────────┘
```

## 3. 배선 — rlo 층이 ga 의 어디에 붙나

| rlo 층 | ga 의 자리 | 무엇이 흐르나 |
|---|---|---|
| Telemetry | ga 의 L0 sink(허브 · Runner 공통) | ga 사건: 지시 보냄 · 알림 · 보고 받음 · 머리 검사 · 통합 · 시험 · 판정 · 사람 몫 올림/끝남 · 작업 세션의 가드 기록 줄 · 세션 상태(list_sessions 요약) |
| Sensor | 허브의 세션 상태 | 세션마다 execution_health · progress_state · completion_state · 정체(마지막 보고 뒤 시간) · 거부 수/규칙. 지시마다 기다림/답함 |
| MS 세계 | ga 의 세계 명세 | 실체: 세션 · 지시(rev) · 저장소(통합 머리) · 사람 몫. 관측 = Sensor 상태 |
| DC | ga 의 결정 목적 | `hub_dispatch`(보내기 · 다시 알림) · `integrate` · `judge` · `escalate` — 결정마다 필요한 상태와 신선도 |
| action | ga 의 연산을 `action-spec/1` 로 | send_directive · renotify · request_header_fix (external) · integrate_ff · run_tests · record (local) · post_verdict (external) · enqueue_human (local) · **permit · push_guard · deploy = 사람 전용(어떤 grant 로도 열지 않음)** |
| guard | 허브 연산의 enforce | 허가는 위 external 중 운영자가 정한 것만. 사람 전용은 늘 거부 → ReAct 가 enqueue_human 으로 돈다 |
| health | 허브 연산의 VERIFY | send_directive → 창 안에 보고 · renotify → 세션 상태가 바뀜 · integrate → 통합 머리에서 시험 통과 · enqueue_human → 끝남으로 옮겨짐 |
| LLM | MS LLMProvider | ga 의 Judge(llm_judge) 를 공급자로. 판정 · 의도에만, 대안 선택에는 쓰지 않는다(닫힌 표) |

## 4. ReAct — 닫힌 대안표 (반드시)

막힘(가드 거부 · VERIFY 실패 · 입력 오류)마다 **(층, 규칙, 원인) → 대안 하나** 를 표에서 찾는다. 대안을 한 번 해 보고 다시 판정한다. **같은 막힘은 두 번까지.** 그 뒤 한 단계 위로 올린다(작업 세션 → 허브 → HUMAN_QUEUE). 올릴 때는 신호와 함께 올린다.

| 막힘 | 원인(라벨) | 대안 | 넘으면 |
|---|---|---|---|
| A1 | 모형에 없는 도구, 같은 목적의 허용 도구가 있음 | 그 도구로(예: ReadNotifications → 통로 issue_read) | 허브: 모형 보강 제안 → 사람 몫(G) |
| A1 | 대체 없음 | 하지 않고 통로에 보고 | 허브 → 사람 몫(G) |
| A4 | 모르는 인자 | 명세에 없는 인자를 빼고 한 번 | 허브: 모형 보강 제안 |
| A7 | 허가 없음 | 다시 하지 않는다 | 사람 몫(G) · 다른 일 계속 |
| D | 낡음만(stale-only) | 읽기 호출 한 번 → 다시 | 허브 |
| D | 모름(앞 호출 결과 없음 · 나란히) | 앞 결과를 기다린 뒤 한 번 | 허브 |
| 입력 오류 | 호스트 입력이 깨짐 | 다시 하지 않는다 | 허브(호스트 결함) |
| VERIFY | 지시 뒤 창 안에 보고 없음 | 세션 상태 읽기 → 다시 알림 한 번 | need_input 이면 원인 분류 → baseline 이 풀거나 사람 몫 |
| VERIFY | 통합 뒤 시험 실패 | 통합 되돌리지 않고 판정 `실패` · 고침 지시 | — |

- **작업 세션(Claude Code 훅)** 에서는 훅이 막기만 할 수 있으므로, 거부 까닭에 **표의 대안을 기계가 읽는 꼴로** 싣는다(`alternative: {tool, args_hint}` · `escalate_after: 2`). 모형이 그것을 따른다. 따랐는지는 Telemetry 로 잰다.
- **ga 자신의 Runner(Agent SDK)** 와 **허브** 에서는 ga 가 표를 직접 돈다.

## 5. 통신의 신호

- `report/2` 와 `notify/1` 에 선택 칸 `signals` 를 더한다(라벨만): `{guard: {deny: n, rules: [..]}, execution_health, progress_state, stalled_s, react: {tried: n, escalated: bool}}`.
- 허브는 세션이 말하지 않아도 이 신호와 자기 Sensor 로 판단한다. 머리 검사(PROTOCOL §3a)는 그대로.

## 6. 단계 · 주인 · 끝난 기준

| 단계 | 일 | 주인 | 끝난 기준 |
|---|---|---|---|
| U1 (먼저) | **턴 안 ReAct**: 거부 까닭에 닫힌 대안(§4 표의 작업 세션 칸) · 되풀이 상한 · 올리기 신호 | rlo-SDK(SDK) + ga_rlo remote 프리셋 · doctor(GR) | 오늘 W1 의 네 사례를 재생해 대안대로 풀린다(A1 → issue_read · D 낡음 → 읽기 뒤 통과 · A7 → 올림 · 입력 오류 → 올림). 대안이 grant 를 넓히는 길은 시험이 막는다 |
| U2 | **하나의 ga**: ga-sdk 가 rlo-sdk[sensor] 를 고정 의존 · ga_rlo 코드가 ga 안 모듈로(경로 소유: GR) · ga_rlo 동결 | GA + GR | 빈 venv 에 ga 한 줄 설치로 rlo 까지 · `ga rlo …` 입구 · ga_rlo 시험이 ga 안에서 통과 |
| U3 | **통신 신호**: Telemetry L0 sink · signals 칸 · 허브의 세션 Sensor | GA(꼴 · 허브) + SDK(Sensor 어댑터) | 오늘의 AMP ↔ W1 정체가 재생에서 허브 신호로 잡힌다 |
| U4 | **허브 Autonomy**: ga 세계 명세 · 연산의 action-spec · DC 목적 · VERIFY 창 · 사람 전용 연산 | GA + SDK(빈자리) | 가짜 세션들로 한 바퀴: 보냄 → 창 안 보고 없음 → 다시 알림 → 사람 몫. 사람 전용 연산은 어떤 설정으로도 실행되지 않음 |
| U5 | **검증**: gentleMonster 허브를 하나의 ga 로(GA_RLO §7 을 이어받음) | 허브 세션 | 실제 프로젝트에서 baseline 이 손으로 하던 지시 · 통합 · 판정 · 기록 · 다시 알림을 ga 가 한다 |

### rlo 쪽 빈자리(SDK 에 `요청:`)

- **R-a 목적 꽂기**: DC 내장 목적만 쓸 수 있다(README "새 목적을 꽂는 자리는 아직 없다"). ga 의 결정 목적을 꽂을 자리.
- **R-b Sensor 의 `$run.*` 어댑터**: `run_state=` 에 Sensor 어댑터가 아직 없다. 세션 상태를 결정 문맥으로.
- **R-c 거부 까닭의 대안 꼴**: §4 의 기계가 읽는 대안 칸(U1).
- **R-d (U4)** 세계 모형에 "에이전트 허브" 예시 명세.

## 7. 하지 않는 것

- rlo 층 코드를 ga 로 복사하지 않는다(소유 · 이력 · 시험을 지킨다).
- ReAct 로 허가를 넓히지 않는다. 자유 추론으로 대안을 만들지 않는다.
- 사람 전용 연산(permit · 가드 push · 배포)을 자동으로 하지 않는다.
- 원문 · 비밀값을 신호에 싣지 않는다.

## 8. Gemini 확장도 ga 를 쓴다 (BD-217)

- 분당 한도(RPM) 제어부 — 속도 관리자 · model/tool 단계표 · 다시 보내기 — 는 rlo 에 한 번 짓고(CMD-K12), well_used_gemini · gentleMonster_gemini 가 ga-sdk 를 깔아 Gemini 를 LLM 공급자로 꽂아 쓴다.
- 확장의 OOM 같은 Gemini CLI 쪽 문제는 확장에서 푼다(CMD-WUG1 A).
- 대가: 확장에 Python 3.10+ · 설치에 GitHub 접근.
- **`ga gemini` 감독자(BD-221):** 사용자는 Gemini CLI 대화창이 아니라 ga 와 말한다. Gemini(고정 gemini-3-flash-preview)는 지시(닫힌 단계 목록)만 내고, rlo Scheduler 가 MCP 도구를 병렬로 돌린다. 할당량에 닿으면 재개 시각 · 지금 · 다음을 보이고 상태를 저장한 뒤 자동 재개. 턴마다 짧게 사는 headless CLI 라 Node heap 이 쌓이지 않는다.
