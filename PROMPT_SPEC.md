# PROMPT SPEC — 우리 프롬프트 언어 `prompt-spec/1` (BD-291, POL-2)

목적은 **토큰을 줄이는 것**이다(BD-290). 프롬프트를 손으로 쓴 `str.format` 글 대신, 의미를 선언한 파일 하나(`*.pspec`)로 정의한다.
파일 하나에서 세 가지가 나온다.

| 나오는 것 | 함수 | 하는 일 |
|---|---|---|
| 프롬프트 글 | `compile(spec, section, values, mode)` | `verbatim` = 지금 글과 바이트 같음(옮기며 잃는 것이 없다는 증명) · `compact` = 토큰을 줄인 글 |
| 출력 검사기 | `check(spec, answer, values)` | 같은 `out` 선언에서 나온다 → 프롬프트와 파서가 어긋날 수 없음 |
| 토큰 보고 | `tokens(text)` | 오프라인 추정 `ceil(utf-8 bytes / 4)`. 실제 값은 Telemetry 의 공급자 사용량 |

참조 구현(원형): [`ops/pspec/pspec.py`](ops/pspec/pspec.py), 예: [`ops/pspec/gemini-plan.pspec`](ops/pspec/gemini-plan.pspec), 측정: [`ops/pspec/run.py`](ops/pspec/run.py).
제품 코드는 SDK 가 rlo-sdk 에 짓는다(CMD-K15). 이 원형은 문법과 기대 결과를 고정하는 기준이다.

## 1. 파일 꼴

```
spec gemini-plan/1
goal Direct a controller that runs tool steps; each turn answers with one closed step list.
in tools   : Model           @operator once
in task    : DecisionContext @operator once
in results : Observation     @runtime  turn
in ask     : Opinion         @model    turn
let max_steps = 16
let id = /^[A-Za-z0-9_-]{1,12}$/
out ga-gemini-plan/1
  schema : "ga-gemini-plan/1"
  steps? : [{id: id new, tool: key(tools), args?: {}, after?: [id seen]}] <= max_steps
  next?  : {prompt: str+, after?: [id seen]} | null
  say?   : str
--- once
...
--- turn
...
```

- 머리 줄 끝에 `#` 주석을 달 수 없다(줄 전체가 `#` 로 시작하는 줄만 주석). `in` 줄은 `이름 : SEMANTIC_MODEL 낱말 @근거 once|turn`, `out` 아래 들여쓴 줄은 칸, `--- 이름` 은 템플릿 구역(BD-292 P4).
- `in` 은 입력마다 **뜻**(SEMANTIC_MODEL §1 낱말: Observation · Measurement · State · Evidence · Model · DecisionContext · Opinion)과 **근거**(observed · runtime · provider · operator · model · label · estimate), 그리고 **언제 보내는지**(`once` 대화당 한 번 · `turn` 턴마다)를 적는다. 모르는 낱말 · 근거는 적재 오류.
- 입력이 빠지면 컴파일 오류. 모델의 답은 늘 Opinion 이다(권위 없음) — 판정은 `check` 와 그 뒤의 결정론 규칙이 한다.

## 2. 템플릿 문법 (Jinja 비슷, 최소)

| 꼴 | 뜻 |
|---|---|
| `{{ a.b }}` · `{{ a\|json }}` · `\|cap:N` · `\|rstrip:" "` | 값 · 거르개 |
| `{% for x in xs %}…{% else %}…{% end %}` | 반복(dict 는 키 순서로 정렬해 돎 — 순서에 기대지 않음) · else = 비었을 때 |
| `{% if a %}…{% else %}…{% end %}` | 조건 |
| `{% v %}…{% c %}…{% end %}` | **토큰 스위치**: verbatim 글 \| compact 글 |
| `{{ out }}` · `{{ out_schema }}` | 출력 꼴 한 줄(compact 서명) · 스키마 이름 |
| `{% use once %}` | 다른 구역 넣기 |

- 템플릿이 쓰는 이름은 입력 · `let` · `out` · `out_schema` · 반복 변수(와 그 속성)뿐이다. 그 밖의 이름(오타 `{{ tsk }}` 등)은 적재 오류다(BD-292 P3).
- 중괄호 하나는 그냥 글자다 → JSON 예시를 이스케이프 없이 쓴다(f-string 과 다른 점).
- 파일 끝 줄바꿈은 프롬프트에 들어가지 않는다.

## 3. 출력 꼴 타입

`"lit"` · `str` · `str+`(빈칸 아닌 글) · `int` · `{}`(아무 객체) · `key(<in>)`(그 입력의 키 중 하나) · `id new`(`let id` 정규식에 **통째로** 맞음(fullmatch) · 겹치지 않음) · `id seen`(**앞 객체들**의 id — 자기 객체의 id 는 아직 없음, 그래서 `{"id":"a","after":["a"]}` 는 거부) · `[T] <= N` · `{a: T, b?: T}`(모르는 칸 거부) · `T | null`.
compact 서명은 같은 선언에서 나온다: `{"schema":"ga-gemini-plan/1","steps"?:[{"id":id,"tool":tools,...}]≤16,...}`.

## 4. 원형 측정 (baseline, 2026-10-04, `python3 ops/pspec/run.py`, ga-sdk `438a34a`)

| 확인 | 결과 |
|---|---|
| verbatim 이 ga 의 지금 글과 바이트 같음 — `protocol()` · 첫 턴 · `--resume` 턴 · agy(--resume 없음) 턴, 도구 표 3 가지 | 모두 같음 |
| `check` 가 ga `check_plan` 과 받음/거부가 같음 — 사례 17(잘못된 schema · 표 밖 도구 · 겹친 id · 긴 id · 앞에 없는 after · 자기를 가리키는 after · 17 단계 · 모르는 칸 · 빈 next.prompt …) | 17/17 (BD-292 뒤; 처음 16/16) |
| 모르는 낱말 · 모르는 근거 · 빠진 입력 | 모두 오류 |
| dict 순서 바뀜 | 같은 글 |
| 8 턴 대화 토큰(추정) — Gemini(--resume) | 646 → 447 (**−31%**), 첫 턴 245 → 161 |
| 8 턴 대화 토큰(추정) — agy(--resume 없음, 턴마다 전문 다시) | 2263 → 1574 (**−30%**) |

추정은 바이트/4 라 실제 토크나이저와 다르다. 실제 절감은 T2 가 Telemetry 사용량으로 다시 잰다. 남은 큰 몫은 agy 가 턴마다 고정 부분을 다시 보내는 것 — 기억이 없는 호스트라 compact 로 줄일 뿐 없앨 수는 없다.

제품: rlo-sdk `6bc76c7`(0.9.0) `rlo.pspec` — 위 결과를 12/12 · 16/16 · 같은 토큰 수로 맞춤(BD-292). P1 · P2 · P3 는 다음 SDK 커밋에서 들어간다.

## 5. 원형이 하지 않는 것(SDK 몫)

시험 묶음 · 변이 시험 · 오류 위치(줄 · 열) · 거르개 · 타입 확장 규칙 · Telemetry 연결 · 버전 판본 · 성능. 문법과 위 결과(§4)는 바꾸지 않는다 — 바꾸려면 baseline 에 제안한다.
