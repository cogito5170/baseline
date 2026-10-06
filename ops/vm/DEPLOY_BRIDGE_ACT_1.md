# VM 배포: ga bridge 코드 작업 + 지시별 모델 (VM-BRIDGE-ACT-1 · VM-BRIDGE-MODEL-1)

- 코드: `cogito5170/ga-sdk` 브랜치 `vm/BRIDGE-ACT-1` = `865bf0c` (기준 `318b22a` 위 2커밋: ACT-1 `93059db`, MODEL-1 `865bf0c`)
- 시험 (클라우드, 10-07 05:5x KST): 새 시험 15개 + 기존 브리지 24개 = 39 OK. 전체: 기준 318b22a 1363 passed / 53 skipped; 브랜치 1378 passed (1363 + 새 15) / 53 skipped, 실패 0 — judge 10개 실패는 로컬 editable 설치의 `ga_sdk.egg-info`+PYTHONPATH 때문이었고 PYTHONPATH 없이 다시 돌려 42개 모두 통과.
- 변이: ACT 분기·push·실패 회신, 모델 덮어쓰기·허용 확인·act 모델 전달 — 6개 모두 시험이 잡음.

## VM에서 (터미널을 열 수 있을 때, 한 번)

```bash
cd ~/ga-sdk
git status --short                                   # 출력이 없어야 함 (있으면 멈추고 알려 주세요)
git fetch origin vm/BRIDGE-ACT-1
git merge --ff-only origin/vm/BRIDGE-ACT-1           # 318b22a -> 865bf0c
git log -1 --oneline                                 # 865bf0c VM-BRIDGE-MODEL-1 ...
~/ga-venv/bin/python -m unittest tests.test_vm_bridge_act tests.test_vm_bridge_model tests.test_ga36_bridge   # Ran 39 tests ... OK
git push origin HEAD:claude/gracious-meitner-vp49xe  # 통합 브랜치에도 올려 둠 (아래 '왜' 참고)
systemctl --user restart ga-bridge
systemctl --user status ga-bridge --no-pager | head -5   # active (running)
```

왜 통합 브랜치에 push하나: VM의 `ga-update.timer`는 30분마다 `~/ga-sdk`를 `origin/claude/gracious-meitner-vp49xe`로 fast-forward한다. 이 커밋이 VM에만 있으면 지금은 문제없지만, 나중에 통합 브랜치가 앞으로 가면 fast-forward가 막혀 자동 갱신이 멈춘다. push가 거부되면(VM에 그 권한이 없으면) 그 줄만 건너뛰고 알려 주세요.

## 터미널 없이 하는 길

`vm/BRIDGE-ACT-1`이 GitHub에서 `claude/gracious-meitner-vp49xe`로 병합되면(fast-forward), VM의 `ga-update.timer`가 30분 안에 받아서 다시 설치하고 바뀐 서비스(ga-bridge)를 재시작한다. 이 경우 위 명령은 필요 없다.

## 배포 뒤 확인 (baseline이 우편함으로)

1. 코드 작업 없는 지시 → 지금처럼 ga supervise (CMD-PING5와 같은 회신).
2. `"model": "gemini-3.7-flash-low"`가 있는 지시 → 회신 results의 model이 그 이름.
3. 없는 모델 이름 → 모델 호출 없이 declined, 사유 "not in agy models".
4. ```` ```ga-act ```` 블록이 있는 작은 지시(Token 저장소) → ga act가 고치고 `agv/<id>-r1` push, 회신에 commits.

## 설정 (선택)

브리지가 ga-sdk 자체도 고치게 하려면 `/home/ubuntu/agy-bridge.json`의 `act`에 `"repos": {"ga-sdk": {"path": "/home/ubuntu/ga-sdk", "repo_name": "cogito5170/ga-sdk"}}`를 넣는다(지시의 ga-act 블록에 `"repo": "ga-sdk"`). 지금은 넣지 않아도 된다(기본은 `act.repo` = ~/token).
