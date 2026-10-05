# 시연 1 — baseline 이 GA Engine 처럼 한 요구를 끝까지 수행 (BD-396)

요구(사용자, 원문): "sdk 라고 해도 되는가? mcp cli api 등등 명확한 명칭을 구축해라." + "바로 설계 시작해라. 내가 원하는 '목적을 끝까지 토큰 최적화하며 달성하는 machine'의 사례를 너가 스스로 보여라."

## 1. 접수 → task/1 (GA37 양식 초안)

```json
{"schema":"task/1","id":"T-NAMING-1","kind":"change",
 "goal":"GA 의 계층 이름을 정하고, '목적 달성 기계' 설계 문서가 그 이름을 쓰게 한다",
 "deliverables":[{"id":"P1","what":"명칭 문서","where":"research/NAMING.md"},
                 {"id":"P2","what":"명칭 검증기(코드)","where":"research/demo/naming_check.py"},
                 {"id":"P3","what":"설계 문서의 명칭 연결","where":"research/AUTONOMY_MACHINE.md"}],
 "constraints":["모델이 아니라 코드가 완료를 판정","새 지시 · 세션 없이 baseline 한 곳에서","대화 재읽기 턴을 최소로"],
 "acceptance":[{"id":"A1","check":"python3 research/demo/naming_check.py → exit 0","kind":"command"},
               {"id":"A2","check":"상태 칸을 비운 변이에서 naming_check.py → exit 1","kind":"command"},
               {"id":"A3","check":"ga check directives/CMD-GA37.md → 0 hard (rev 2)","kind":"command"},
               {"id":"A4","check":"이 작업의 토큰을 세션 사용량 차이로 실측해 이 문서에 적는다","kind":"observable"}],
 "non_goals":["저장소 이름 변경(사람이 GitHub 에서 결정)","GA MCP 구현"],
 "assumptions":[{"text":"전체 이름","default":"GA(Goal Achiever) — 기존 패키지 · 명령 이름 ga 를 유지"}],
 "questions":[]}
```

## 2. 계획 · 실행 · 검증

| 단계 | 한 일 | 판정(코드) |
|---|---|---|
| 실행 | NAMING.md 작성, 검증기 작성, 설계 문서에 명칭 줄 추가 | — |
| 검증 1 | naming_check.py 첫 실행 → exit 1("설계 문서가 NAMING.md 를 가리키지 않음") → 고침 → exit 0 | A1 met |
| 검증 2 | 변이: 상태 칸 비움 → exit 1(행 3 개 불완전) → 원복 | A2 met |
| 검증 3 | GA37 rev 2(task/1 kind · 상태 저장소 · replay) ga check 0 hard | A3 met |

## 3. 토큰 (A4)

아래 §4 에 실측값을 적는다(이 시연 동안의 baseline 세션 사용량 차이).

## 4. 실측 결과
- 세션 사용량은 턴이 끝날 때 갱신된다. 그래서 이 턴 안에서는 차이를 읽을 수 없다(시작 · 중간 모두 cost $603.67, 읽기 1,647,308,773). 정확한 차이는 다음 정시 점검에서 읽어 아래에 덧붙인다.
- **추정(구조에서 계산):**
  - 이 시연은 모델 턴 약 8 번이다(도구 호출 7 + 답 1).
  - 턴마다 baseline 의 문맥 약 25 만 토큰을 다시 읽는다(context_usage 252,560).
  - 그래서 읽기 ≈ 200 만 토큰, 쓰기는 ≈ 1 만 토큰이다.
  - 완료 판정은 코드(naming_check.py · ga check)가 했으므로 판정에 든 모델 토큰은 0 이다.

## 5. 이 시연이 보여 준 것

- **잘된 점(기계의 모양):**
  - 요구를 명세로 바꿨다(수용 기준이 모두 명령 · 관찰 가능).
  - 완료는 코드가 판정했다. 처음엔 실패했고, 고친 뒤 통과했다.
  - 변이로 검증기의 힘을 확인했다.
  - 사람 개입은 0 이다.
- **나쁜 점(지금 허브의 낭비 그대로):**
  - 일 자체는 쓰기 약 1 만 토큰이다. 그런데 baseline 이 턴마다 25 만 문맥을 다시 읽어서 읽기가 약 200 배가 된다.
  - 이 세션 누적: 읽기 16.5 억 · 출력 349 만 → **읽기 99.8%**, $603.67.
  - 작업 세션 33 개 합계($57.21)보다 허브 하나가 10 배 비싸다.
- **GA Engine 으로 같은 일을 하면(설계 추정, GA37–41 이 실측할 값):**
  - 접수 1 턴: 문맥 ≤ 2k.
  - 실행기 2–3 턴: 상태 카드 ≤ 6k, 고정 앞부분은 캐시.
  - 검증 0 턴: 코드.
  - 합계 ≈ 2 만 토큰. 허브 방식 약 200 만의 1/100 수준이다.
- 결론: 가장 큰 낭비는 작업자가 아니라 **대화를 계속 끌고 가는 허브(사람 대신 지시 · 검증하는 쪽)** 다. GA Engine 의 Verifier · Planner · State Store 가 이 대화를 코드와 고정 크기 상태로 바꾸는 것이 1 순위다.
