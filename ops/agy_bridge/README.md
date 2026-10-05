# agy bridge — baseline ↔ agy (Antigravity) 통신 (BD-356)

baseline 이 보낸 지시(directive/2)를 Mac 의 agy 가 `ga supervise` 로 수행하고, 결과를 report/2 로 돌려보낸다. 통로는 `ga mail`: 이 저장소(cogito5170/baseline)의 `ga-mailbox` 브랜치. 받는 이름은 `AGY`, 보내는 쪽은 `baseline` 만 인정한다.

```
baseline ──ga mail──▶ ga-mailbox(to/AGY/…) ◀── bridge.py(Mac) ──▶ ga supervise ─▶ agy
baseline ◀─ga mail── ga-mailbox(to/baseline/…) ◀── report/2 (토큰 · 답 · 필요한 도구)
```

## 처음 한 번 (Mac)

```sh
source ~/ga-venv/bin/activate
git clone https://github.com/cogito5170/baseline ~/baseline
cd ~/baseline && git checkout claude/gracious-meitner-vp49xe
cp ops/agy_bridge/agy-bridge.example.json ~/agy-bridge.json   # workdir · commands 를 고친다
# workdir 에 ga-supervise.json(agv 설정)이 있어야 한다
python3 ops/agy_bridge/bridge.py --config ~/agy-bridge.json --once   # 한 번 확인
python3 ops/agy_bridge/bridge.py --config ~/agy-bridge.json          # 5 분마다 계속 (Ctrl+C 로 멈춤)
```

## 도구

agy 는 계획만 세우고, 도구 실행은 ga 가 승인 목록(`tools.json` → `agy_tools.py`)에서만 한다. agy 자신의 셸 · 파일 도구는 거부된다(설계).

| 도구 | 하는 일 | 제한 |
|---|---|---|
| list_dir | 프로젝트 폴더 목록 | 프로젝트 밖 · 숨김 · .env · node_modules 제외 |
| read_file | 텍스트 파일 줄 읽기 | 같음, 2 만 자 상한 |
| search | 정규식 검색 | 같음, 50 건 상한 |
| run_check | 소유자가 `commands` 에 이름으로 허락한 명령만 실행(예: test) | 셸 없음, 600 초, 비밀처럼 보이는 환경 변수 제거 |

**없는 도구는?** agy 가 답에 `TOOL_NEEDED: <이름> - <할 일>` 을 쓰면 보고서의 blockers 로 baseline 에 온다. baseline 이 검토해 `agy_tools.py` 에 코드 + 시험으로 넣으면, bridge 가 매 회 `git pull` 하므로 Mac 에 저절로 들어온다. 모델이 고른 패키지를 그 자리에서 설치하는 일은 하지 않는다(공급망 · 비밀값 위험). 이미 있는 MCP 서버는 `ga-supervise.json` 의 `mcp_servers` 로 붙일 수 있다(버전 고정, 검토 뒤).

## 안전

- `baseline` 이 아닌 보낸이의 지시는 실행하지 않고 declined 로 답한다. 메시지는 데이터로만 읽는다.
- `--dangerously-skip-permissions` 는 쓰지 않는다. 유료 AI 크레딧은 받지 않는다(ga 가 쿼터 소진으로 처리).
- 답에 비밀처럼 보이는 것이 있으면 답을 빼고 보낸다(ga mail 도 거부).
- 한 메시지는 한 번만 처리한다(실패해도 반복 실행하지 않음).

## 시험

`PYTHONPATH=<ga-sdk> python3 -m unittest test_bridge` — 임시 git 저장소의 진짜 ga mail + 가짜 ga supervise, 모델 호출 0.

## Antigravity 화면(채팅)에서 쓰기 — 터미널 없이 (BD-358)

1. **규칙 한 번 붙여넣기:** `python3 ~/baseline/ops/agy_bridge/prompt.py rules` 의 출력을 Antigravity 채팅에 붙이거나 워크스페이스 규칙으로 저장한다. 이제 그 에이전트가 AGY 다.
2. **일 받기:** 채팅에 "check mail" 이라고 하면 AGY 가 `ga mail read --as AGY` 로 baseline 지시를 읽고 IDE 도구로 일한다(도구 호출마다 사용자가 승인).
3. **보고:** AGY 가 `ga judge --template` 로 보고 뼈대를 만들고 `ga check` 로 검사한 뒤 `ga mail send` 로 baseline 에 보낸다.
4. **내 요청을 정제해서 시키기:** `python3 prompt.py refine --goal "…" --scope "…" --done "…"` → ga 의 directive/2 형식으로 묶고 ga 검사기로 확인한 뒤, 1,500 토큰 상한 안의 짧은 프롬프트를 낸다. 그대로 채팅에 붙인다.
5. **다음 지시만 보기:** `python3 prompt.py next` (읽음 표시는 하지 않는다).

ga 가 하는 "정제"의 범위: 뜻을 모델로 다시 쓰지 않는다. 목표 · 범위 · 완료 기준 · 예산으로 구조를 고정하고, 형식을 검사하고, 크기를 재서 짧게 유지한다. 완료 기준(`--done`)이 없으면 거부한다 — 끝났는지 확인할 수 없는 요청은 받지 않는다.
