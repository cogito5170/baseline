# agy (Antigravity CLI) — 사용자 Mac 에서 확인한 사실 (2026-10-05)

출처: 사용자가 붙여 준 `agy --help` 출력(HUMAN_QUEUE Q5 의 1 번). 키 · 토큰 없음.

- 모델 목록은 플래그가 아니라 **하위 명령** `agy models` 다(`agy --models` 는 오류).
- **이어가기 있음:** `--continue`(-c, 가장 최근 대화), `--conversation <ID>`(ID 로 재개). ga README 의 "agy has no known --resume" 는 고쳐야 한다 → agv 가 매 턴 지시를 다시 보내지 않아도 될 수 있음(토큰 절감).
- `--input-format stream-json`(stdin 으로 NDJSON 한 줄당 한 턴, `--output-format stream-json` 필요).
- `--disable-slash-commands`(print 모드), `--effort low|medium|high|xhigh|max`, `--mode accept-edits|plan`, `--print-timeout`, `--sandbox`, `--json-schema`, `--log-file`, `--add-dir`, `--project`, `--new-project`, `--agent`.
- `--dangerously-skip-permissions` 가 있다. ga 는 이것을 **절대 쓰지 않는다**(GA34 의 bypassPermissions 거부와 같은 원칙).
- 도구를 끄는 플래그는 여전히 보이지 않는다(bare 호출 불가는 그대로).
- 남은 확인: `agy models` 출력 형식과 GPT-OSS 120B 의 slug, `-p "/usage"` 줄 형식, stream-json 한 턴의 원시 줄.

후속(ga-sdk 작업 후보): agv 백엔드가 `--conversation` 으로 이어가기, `--disable-slash-commands` · `--effort` 옵션, 원시 출력 형식 확인 뒤 파서 고정.

## 첫 실측 (2026-10-05, 사용자 Mac)

- `ga supervise --config ga-supervise.json "Reply with the word OK"` → `OK`. ga-sdk 0.6.0(`03e8dae`)의 agv 백엔드가 실제 agy 로 처음 끝까지 돌았다(그전까지는 오프라인 시험뿐).
- 모델 slug · 로그(`.ga-supervise/log.jsonl`) 숫자는 아직 못 받음 — 사용자에게 요청.

## 첫 실측 로그 (사용자가 붙여 준 `.ga-supervise/log.jsonl`, 숫자 · 라벨만)

| 항목 | 값 |
|---|---|
| model / served | `gpt-oss-120b-medium` / `["gpt-oss-120b-medium"]` (일치 → 턴 인정) |
| bare | false (agy 는 도구 끄기 불가) |
| prompt_est (ga 가 보낸 프롬프트 추정) | 86 토큰 |
| provider_prompt_tokens (input) | 11,210 |
| 출력 | 121 (tokens 11,331 − input 11,210) |
| 시간 | 8.243 초 |
| usage_format | openai |
| 결과 | done, model_turns 1, tool_steps 0, failed 0 |

- **agv 고정 오버헤드 실측: 약 11,124 입력 토큰/턴**(11,210 − 86). 지금까지 `--list-backends` 에 "not measured" 였던 값. gemini_cli 11,822(BD-302)와 비슷하고, bare claude_cli(945/1,197)의 약 9–12 배.
- 함의: agv 로 짧은 작업을 여러 턴 돌리면 대부분이 고정 오버헤드다. 이어가기(`--conversation`)로 캐시를 살리거나 턴 수를 줄이는 것이 절감의 핵심(후속 ga 작업 후보).
- slug 는 `gpt-oss-120b-medium`(노력 단계가 slug 에 붙는 꼴, catalog 의 `gemini-3.8-flash-high` 와 같은 규칙). ga catalog 에는 없는 모델이지만 family 규칙(gpt-*)으로 통과했다.

## 고정 비용 줄이기 계획 (BD-362, 사용자: "고정 비용을 고치고 그 다음에 정제")

1. **실측(CMD-AG3, AGY 에게):** 같은 1 턴("Reply with the word OK")을 설정만 바꿔 잰다 — V0 기본 · V1 `--disable-slash-commands` · V2 `--mode plan` · V3 `--sandbox` · V4 도구가 가장 적은 `--agent` · V5 MCP 서버 끔 · V6 `--continue` 둘째 턴(캐시) · V7 한 프로세스 두 턴(stream-json). 최대 10 턴.
2. **고침(CMD-GA35, GA34 통합 뒤):** 가장 싼 조합을 ga agv 백엔드의 기본으로 — 이어가기(`--conversation`)로 같은 작업 안 턴들이 한 대화를 쓰게, 줄인 플래그 · 에이전트, `--list-backends` 의 overhead 를 실측값으로. 오프라인 시험 + AGY 재측정으로 확인.
3. **그 다음 정제:** `prompt.py refine` 앞에 agy 한 턴(뜻 다듬기)을 선택 단계로 넣는다. 그 턴의 실제 입력 토큰을 보고서에 함께 적는다.

## 서버 용량 오류 (2026-10-05 08:20 UTC, 사용자 Antigravity 화면)

- `HTTP 503 UNAVAILABLE`, reason `MODEL_CAPACITY_EXHAUSTED`, domain `cloudcode-pa.googleapis.com`, error_number 2010, model `gpt-oss-120b-medium`: "No capacity available for model … on the server".
- 사용자 쿼터 소진이 아니라 **서버 쪽 일시 용량 부족**. 유료 크레딧과도 무관.
- ga agv 에 필요한 것(GA35 에 넣음): 이 오류를 쿼터 정지(주간 리셋까지 대기)와 구별해 **일시 오류**로 분류 — 짧은 backoff 뒤 1 회 재시도, 그래도 같으면 설정된 대체 모델(같은 family 규칙 안)로 넘기거나 그 턴을 `capacity` 로 실패 처리. 오류 줄은 라벨 · 숫자만 기록.
- 08:33 UTC 같은 대화(Trajectory `fa78aba8…`)에서 같은 오류 재발. 사용자: "다른 프롬프트는 되는데 rules 를 수행하라고 하면 이 오류". 같은 trajectory id 가 두 번 나온 것으로 보아 그 대화가 `gpt-oss-120b-medium` 에 묶여 있고, 그 모델의 서버 용량이 계속 없음. 다른 요청은 다른 대화/모델에서 돌았을 가능성이 큼. 대응: 새 대화에서 다른 모델을 고른 뒤 규칙을 붙인다.

## AG1 · AG2 보고와 AG3 부분 수치 (BD-386, 2026-10-05)

- 모델 목록(`agy models`): gemini-3.8/3.7/3.6-flash-{high,medium,low}, gemini-3.1-pro-{high,low}, claude-sonnet-4-6, claude-opus-4-6-thinking, gpt-oss-120b-medium.
- `/usage`: 주간 버킷 두 개. "Gemini Models" 와 "Claude and GPT models". **gpt-oss 와 Claude 는 같은 버킷을 쓴다.** 그 시점 Gemini 0%, Claude and GPT 78% 남음.
- stream-json: init(conversation_id, model, cwd, **tools 57 개**, permission_mode request-review) → step_update 줄들(text_delta, 마지막에 usage) → result. json: result 한 객체(status, response, duration_seconds, num_turns, usage{input,output,thinking,cache_read,total}).
- 503 MODEL_CAPACITY_EXHAUSTED 의 종료 코드는 **3**(retryable). 30 초 뒤 재시도로 성공.
- `--continue`: 같은 대화를 잇고 usage 를 누적(2 턴 누적 입력 19,896, cache_read 383, 152 초). **이어가기는 고정 비용을 줄이지 않는다** — 둘째 턴도 ≈10k.
- AG3 부분: V0 기본 입력 9,852(cache_read 188, 118 초 — 도중 "Model produced invalid output" 재시도), V1 `--disable-slash-commands` 10,657(효과 없음). `agy agents` · `agy mcp list` 비어 있음(V4 · V5 해당 없음).
- 추정: 고정 비용의 몸통은 도구 57 개 정의. GA35 절감 수단 = 도구를 줄인 에이전트(정의 방법 확인 필요), 이어가기는 아님.

## Antigravity 채팅으로 AGY 를 구동한 비용 (사용자 보고, BD-386)

- 채팅 모델 Sonnet 이 rules 대로 ga 를 셸로 불러 AG1–AG3 를 처리. 셸 명령마다 사용자 동의 필요, Antigravity 터미널 sandbox 가 `~/ga-venv/bin/ga` 실행을 막아(operation not permitted) sandbox 밖 실행을 요청.
- 한 세션 진행 중 주간 쿼터 50% 소모. 원인: 채팅 모델이 매 단계(타이머 · 상태 확인 포함) 대화 전체를 다시 읽음 + 안쪽 agy 턴마다 ≈10k, 둘 다 같은 "Claude and GPT" 버킷.
- Antigravity 는 ga-sdk 로 돌지 않는다. ga 는 거기서 git 처럼 불리는 명령일 뿐이고, ga 의 문맥 상한 · 비용 기록은 ga 가 모델을 직접 부를 때(`ga supervise` · bridge.py)만 적용된다.
- 권고: AGY 작업은 터미널 bridge.py 로(채팅 모델 없음, 도구는 bridge 의 Python 함수라 명령마다 동의 불필요). 채팅은 사람이 직접 묻는 용도로만.


## 요금제 상향 (사용자, 2026-10-05 09:2x UTC, BD-388)

- 사용자가 Antigravity 요금제를 올렸다: 모든 모델 100% 접근. `agy models` 에 Claude 5.5 가 생겼다: claude-opus-5-5-{low,medium,high}, claude-sonnet-5-5-{low,medium,high} (이전 claude-sonnet-4-6 · claude-opus-4-6-thinking 대신). gemini-3.8/3.7/3.6-flash-{high,medium,low}, gemini-3.1-pro-{high,low}, gpt-oss-120b-medium 은 그대로.
- agv family 규칙(gpt-* · claude-* · gemini-*)으로 새 slug 모두 통과한다.
- 대화형 `agy`(인자 없이)는 폴더 신뢰 질문("Antigravity CLI requires permission to read, edit, and execute files here") 뒤 터미널 채팅이 된다. 이것도 Antigravity 채팅과 같은 에이전트다: 입력 한 번 = 모델 턴(도구 57 개 정의 포함 ≈10k 입력), 명령마다 승인.
