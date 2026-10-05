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
