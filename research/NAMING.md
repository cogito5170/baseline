# GA 명칭 체계 (BD-396)

사용자(2026-10-05): "SDK 라고 해도 되는가? MCP · CLI · API 등등 명확한 명칭을 구축해라."

**답: 아니다.** SDK(Software Development Kit)는 개발자가 무엇을 만들 때 가져다 쓰는 라이브러리 · 도구 묶음이다. 사용자가 원하는 것은 추상 과제를 받아 끝까지 달성하는 **실행 시스템**이다. 그래서 전체에는 다른 이름을 쓰고, "SDK" 는 라이브러리 계층에만 쓴다.

## 1. 이름

전체 이름은 **GA**(Goal Achiever, 목적 달성 기계)다. 계층은 아래와 같다.

| 이름 | 무엇 | 형태 | 지금 |
|---|---|---|---|
| GA Engine | 목적을 끝까지 수행하는 기계: 접수 → 계획 → 실행 → 검증 → 통합 → 보고 | 실행 중인 프로세스(`ga do`) | 일부: 풀 · judge · 통합(GA34). 나머지는 GA37–GA41 |
| GA Core | Engine 과 모든 입구가 쓰는 Python 라이브러리(`import ga`) — **SDK 는 이것만 가리킨다** | 패키지 ga-sdk | 있음 |
| GA Protocol | 단계와 세션 사이의 양식: task/1 · work/1 · directive/2 · report/2 · notify/1 · verdict | 명세 + 검사기(ga.forms) | 있음. task/1 은 GA37 |
| GA CLI | 터미널 입구 `ga …` | 실행 파일 | 있음 |
| GA API | 로컬 HTTP + SSE 입구. UI · 데스크톱 · 외부 프로그램이 쓴다 | 127.0.0.1 서버 | GA36 의 ui 서버가 첫 형태 |
| GA MCP | 다른 에이전트(Claude Code · agy · Codex)에 GA 를 도구로 꽂는 입구 | MCP 서버 | 없음(GA41 뒤) |
| GA UI | 브라우저 화면(`ga ui`)과 데스크톱 앱(GA Desktop) | 앱 | GA36. Token 의 IF1 은 Token 제품의 모니터이지 GA UI 가 아니다 |
| GA Backends | 모델 연결(모델 어댑터): agv · claude_cli · codex_cli · gemini_cli · openai_http · anthropic_http | 플러그인 | 6 개 내장 |
| GA Actions | 코드 쪽 능력(편집 적용 · 이름 붙은 명령 · 검색기). 모델은 이름으로만 부른다 | 등록부 | GA38 |
| GA Guards | 예산 · 상한 · 정책(rlo-sdk 에서 온 가드) | Core 안 모듈 | 있음 |

**Engine 의 부품:**
- Intake(접수, GA37)
- Planner(계획기, GA40)
- Executor(실행기, GA38)
- Verifier(검증자, GA39)
- Router · Loop Policy(GA41)
- State Store(상태 저장소, GA37)
- Ledger(토큰 장부)

## 2. 쓰는 규칙

1. **기계 전체는 "GA Engine"(또는 GA)이다.** "SDK 가 달성한다" 라고 쓰지 않는다. 라이브러리를 말할 때만 "GA Core(SDK)" 라고 쓴다.
2. **입구는 넷이고, 모두 같은 Engine 을 부른다.** 입구마다 따로 로직을 두지 않는다.
   - CLI: 사람 · 터미널
   - API: 화면 · 프로그램
   - MCP: 다른 에이전트
   - UI: API 위의 화면
3. **Antigravity 에는 두 이름이 있다.** 모델 연결의 이름은 `agv`(GA Backends 의 하나), 명령 이름은 `agy`(Antigravity CLI)다. 둘을 섞지 않는다.
4. **rlo 는 GA Guards 의 출처다.** 따로 "ga-rlo" 라는 제품 이름을 쓰지 않는다.
5. **baseline 은 GA 의 부품이 아니다.** baseline 은 GA 를 만들고 검증하는 연구 허브다. 지금 baseline 이 손으로 하는 검증 · 재지시는 GA 의 Verifier · Planner 로 옮겨 간다.
6. **이름은 계층이지 패키지가 아니다.** 지금은 패키지 하나(`ga`)와 저장소 하나(ga-sdk)에 모두 들어 있다. 저장소 이름 변경(ga-sdk → ga)은 GitHub 에서 사람이 하는 결정이다. 필요하면 나중에 정한다.

## 3. 이름 사이의 관계

```
사람 ─ GA CLI ─┐
화면 ─ GA UI ─ GA API ─┼─▶ GA Engine ─(GA Protocol 양식)─ Intake → Planner → Executor ⇄ Verifier → 통합 → 보고
에이전트 ─ GA MCP ─┘                        │                      │
                                         GA Backends(모델)     GA Actions(코드 능력) · GA Guards(예산)
                                    (모두 GA Core 라이브러리 위에 구현)
```
