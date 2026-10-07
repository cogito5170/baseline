# VM: agy direct bridge (ga 없이 baseline ↔ agy)

사용자 10-07 19:0x: "vm agy랑 Ga 없이 통신해", "bridge만 설계해", "bridge.py 참고해".
코드: `ops/agy_bridge/direct_bridge.py` (표준 라이브러리 + git + agy만; ga 패키지·ga bridge 안 씀). 시험: `ops/agy_bridge/test_direct_bridge.py` (가짜 agy, 로컬 git, 4 passed).

- baseline → VM: 우편함 `ga-mailbox`의 `to/AGY-direct/*.md` (```agy-task``` JSON + 산문 프롬프트; `ops/flow/agytask.py`가 만듦)
- VM → baseline: `to/baseline-direct/*.md` (```agy-result``` JSON: status done/stop/declined, 이유, sha, 브랜치, 시험 줄 + agy 출력 끝부분)
- 작업마다: `~/wt-direct-<ID>` 작업 폴더(기존 `~/ga-sdk`는 안 건드림) → 시험 파일 넣기 → agy 실행 → 시험 파일 바이트 동일·허용 파일만 변경·pytest 통과 확인 → `agv/<ID>-r<rev>` push. 하나라도 어긋나면 push 없이 stop 회신.
- 기존 ga-bridge는 그대로 둡니다(같이 돌아도 서로 다른 폴더만 읽음).

## 설치 (VM에 ssh 접속한 뒤, 한 번)

```bash
mkdir -p ~/agy-direct ~/.config/systemd/user && git -C ~/baseline fetch -q origin claude/gracious-meitner-vp49xe && for f in direct_bridge.py agy-direct.example.json; do git -C ~/baseline show origin/claude/gracious-meitner-vp49xe:ops/agy_bridge/$f > ~/agy-direct/$f; done && cp -n ~/agy-direct/agy-direct.example.json ~/agy-direct.json && python3 ~/agy-direct/direct_bridge.py --config ~/agy-direct.json --once && printf '[Unit]\nDescription=agy direct bridge (no ga)\n[Service]\nExecStart=/usr/bin/python3 %%h/agy-direct/direct_bridge.py --config %%h/agy-direct.json\nRestart=always\nRestartSec=30\nEnvironment=PATH=%%h/.local/bin:/usr/local/bin:/usr/bin:/bin\n[Install]\nWantedBy=default.target\n' > ~/.config/systemd/user/agy-direct.service && systemctl --user daemon-reload && systemctl --user enable --now agy-direct && systemctl --user status agy-direct --no-pager | head -3
```

기대: `--once`가 오류 없이 끝나고(처음엔 할 일 없음), 마지막에 `active (running)`.
`agy`가 `~/.local/bin` 등 다른 곳에 있으면 `which agy` 결과 폴더를 Environment PATH에 넣어야 합니다.
로그: `journalctl --user -u agy-direct -f` · 끄기: `systemctl --user disable --now agy-direct`
