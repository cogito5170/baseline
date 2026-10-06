# VM-BRIDGE-ACT-1 — 브리지 메일로 코드 작업까지 (ga bridge에 ga act 경로)

- 보낸이: top baseline `session_01KvzrDZZJDxYhbkb9Yb8LKs` · 10-07 05:4x KST
- 실행자: VM의 Antigravity 에이전트 또는 사용자 SSH (처음 한 번은 쓰기 권한이 있는 쪽)
- 대상: `cogito5170/ga-sdk`, 기준 커밋 `318b22a` (VM이 지금 돌리는 것)
- 사용자 결정 (10-07 05:4x): "1번으로 하고, 브리지 메일로 코드 작업까지 자동을 할 수 있게 일단 해봐"
- 변경 (사용자 10-07 05:4x "처음 한번은 내가 터미널 열리면 할테니깐 수정 다 하고 터미널 명령어만 줘"): 구현은 top이 ga-sdk 브랜치 `vm/BRIDGE-ACT-1`에 한다(ACT-1 `93059db`, MODEL-1 `865bf0c`). 사용자는 VM에서 배포 명령만 실행한다.
- 순서: 이 요구가 VM-BRIDGE-MODEL-1보다 먼저다. 이것이 VM에 배포되면 VM-BRIDGE-MODEL-1부터는 브리지 메일(`to/AGY/`)로 보낼 수 있다.

## 목표 (WHAT)

`to/AGY/`로 온 directive/2가 코드 작업이면, VM 브리지(`ga bridge`)가 사람 손 없이 `ga act`로 별도 worktree에서 고치고, 시험하고, 브랜치로 push하고, report/2로 결과(커밋, patch, 시험)를 회신한다. 코드 작업이 아닌 지시는 지금처럼 `ga supervise`(읽기 전용 도구)로 처리한다.

## 왜

- 지금(`318b22a`) `ga bridge`는 모든 지시를 `ga supervise`로 돌리고, 그 도구는 `list_dir`·`read_file`·`search`·`run_check`뿐이다(`ga/bridge/tools.py`). 브리지 메일로는 코드를 고칠 수 없다. 10-07 05:14 CMD-PING5로 브리지→모델 경로는 확인됐다.
- 같은 기능이 baseline 쪽 브리지에는 이미 있다: `cogito5170/baseline` `ops/agy_bridge/bridge.py` + `act_runner.py` (BD-424 item 파일 → `ga act`, BD-457 `agv/<id>-r<rev>` push, BD-463 repo 선택). VM 브리지 설정 `/home/ubuntu/agy-bridge.json`에는 `act` 블록(repo ~/token, agv, gpt-oss-120b-medium, agent ga-act, max_turns 10, timeout_s 3600)이 이미 있다 — 빠진 것은 코드뿐이다.

## 범위

- S1: `ga bridge`가 코드 작업 지시를 알아보고 `ga act`로 보낸다. 무엇을 코드 작업으로 볼지(item 파일, directive 안의 필드 등)는 실행자가 정하되, 기존 baseline 브리지의 item 파일 방식(`<mailbox_repo>/ops/agy_bridge/items/<directive id>.json`)과 호환되면 좋다.
- S2: 작업은 브리지 설정 `act.repo` 체크아웃 옆의 별도 worktree에서 한다. 사용자의 체크아웃과 돌고 있는 서비스는 건드리지 않는다.
- S3: 결과 커밋은 `agv/<id>-r<rev>` 브랜치로 push한다(force 없음). 비밀처럼 보이는 patch는 push·회신하지 않는다.
- S4: report/2에 상태, served model, 턴, 토큰, 바뀐 파일, 커밋(repo/branch/sha), patch(상한 있음)를 넣는다.
- 범위 밖: 지시별 모델 지정(VM-BRIDGE-MODEL-1), commit/push gate(VI-15..19), VM 배포 방식 변경.

## 완료 기준 (acceptance)

- A1: item이 있는 directive/2 → `ga act` 실행 → 시험 통과 시 report/2 `items[].state: met`, `commits`에 push된 브랜치와 SHA.
- A2: item이 없는 directive/2 → 지금과 같은 `ga supervise` 경로, 회신 형식 변화 없음 (CMD-PING5와 같은 지시로 확인).
- A3: `ga act`가 실패·시간 초과·시험 미통과로 끝나면 report/2 `unmet`과 `blockers`에 이유가 온다. **회신 없이 끝나는 경우가 없다**(지금 `not answered`로 로그만 남는 경로 포함: 실패도 report/2로 회신).
- A4: 새 시험은 모델을 부르지 않는다(가짜 `ga act`/임시 git 저장소). ga-sdk 전체 시험이 `318b22a` 대비 새 실패 없이 통과한다(R0: 1411 OK).
- A5: 변이 시험: (a) act 경로 분기를 지우면, (b) push를 지우면, (c) 실패 시 회신을 지우면 — 각각 새 시험 하나 이상이 실패한다.

## 실행 순서 (사용자 10-07 05:3x)

1. 먼저 `ga act`로 할 수 있는 일을 전부 한다: 범위를 작은 item으로 나누고, 각 item의 완료 기준을 시험 명령으로 고정한다.
2. `ga act`가 끝내지 못한 item만 에이전트 자신(모델)이 처리한다.
3. 보고에 item별로 `ga act`가 한 것(served model, 턴, 토큰)과 에이전트가 직접 한 것을 나눠 적는다.

## 제약

- 돌고 있는 `~/ga-sdk` 체크아웃은 고치지 않는다. 별도 worktree나 clone에서 작업한다.
- 결과는 새 브랜치 `vm/BRIDGE-ACT-1`에 push한다. `main`, `claude/gracious-meitner-vp49xe`에는 push하지 않는다. VM 배포(브리지 재시작 포함)는 사용자가 따로 결정한다.
- 키·토큰은 파일과 보고서에 쓰지 않는다. 모델 비용은 `vm_budget`(VM 전체 하루 30 USD) 안.

## 보고 (끝나면 한 번)

ga-mailbox `to/session_01KvzrDZZJDxYhbkb9Yb8LKs/`에 report/2 또는 notify/1 하나: 브랜치와 SHA, 바뀐 파일, 전체 시험 결과(통과·실패·건너뜀, 시간), 변이 A5 결과, 요구와 다르게 한 부분과 이유, 배포하려면 VM에서 할 명령.
