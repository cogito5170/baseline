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
