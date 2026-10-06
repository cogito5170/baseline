# VM-BRIDGE-MODEL-1 — 지시마다 모델을 고르는 브리지

- 보낸이: top baseline `session_01KvzrDZZJDxYhbkb9Yb8LKs` · 10-07 05:2x KST
- 실행자: VM의 Antigravity 에이전트 (사용자가 실행)
- 대상: `cogito5170/ga-sdk`, 기준 커밋 `318b22a` (= R0-baseline, VM이 지금 돌리는 것)
- 사용자 결정 (10-07 05:2x): "1번으로 해" — directive/2에 모델을 적으면 브리지가 그 지시에서만 그 모델을 쓴다. 실행자는 Antigravity 에이전트.

## 목표 (WHAT)

baseline이 보내는 directive/2에 모델 이름을 적을 수 있고, VM 브리지(`ga bridge`)는 그 지시를 처리할 때만 그 모델로 `ga supervise`를 돌린다. 모델을 적지 않은 지시는 지금처럼 `~/token/ga-supervise.json`의 모델을 쓴다.

## 왜

- 지금(`318b22a`) 모델은 `ga-supervise.json`에 하나로 고정된다. `ga supervise`에 `--model`이 없고, 브리지(`ga/bridge/__init__.py` `effective_config`)는 도구 목록과 state_dir만 바꾼다.
- 일의 크기에 따라 모델을 바꾸려면(싼 모델로 확인, 큰 모델로 설계) 매번 VM 파일을 손으로 고쳐야 한다. 플랫폼은 지시만 내리고 나머지는 VM이 처리한다는 원칙(사용자 10-07 04:5x)에 맞지 않는다.

## 범위

- S1: directive/2 형식에 선택 필드 `model`(문자열)을 추가한다. 형식의 런타임 기준은 `ga/forms/kinds.py` `DIRECTIVE2`이고, `ga/specs/forms/directive2.pspec`과 둘의 일치 시험도 함께 맞춘다.
- S2: `ga bridge`가 지시의 `model`을 그 지시의 실행에만 적용한다.
- S3: 허용 모델 확인. 목록은 VM의 `agy models` 출력에서 온다(캐시 가능). 사람이 손으로 쓴 목록은 쓰지 않는다.
- 범위 밖: `ga act` 경로, hub의 `"model": "auto"`, 사다리(싼 모델→큰 모델 자동 승격), 브리지 도구 추가.

## 완료 기준 (acceptance)

- A1: `model`이 있는 directive/2와 없는 directive/2가 모두 형식 검사를 통과한다. `model`이 문자열이 아니거나 빈 문자열이면 hard 오류.
- A2: `model`이 있는 지시를 처리하면 그 실행의 `ga supervise`가 그 모델로 돈다. 디스크의 `~/token/ga-supervise.json`은 바뀌지 않는다. 다음 지시(모델 없음)는 원래 설정 모델로 돈다.
- A3: `agy models`에 없는 모델이면 모델 호출 없이 report/2 `status: declined`로 회신하고, 사유에 그 모델 이름과 "not in agy models"가 들어간다.
- A4: report/2 `results`의 `model`은 실제로 응답한 모델이다(기존 `_served_model` 동작 유지).
- A5: 새 시험은 모델을 부르지 않는다(가짜 agy). ga-sdk 전체 시험이 `318b22a` 대비 새 실패 없이 통과한다(R0 기준: 1411 OK).
- A6: 변이 시험: (a) 모델 덮어쓰기를 지우면, (b) 허용 목록 확인을 지우면 — 각각 새 시험 중 하나 이상이 실패한다.

## 제약

- 돌고 있는 `~/ga-sdk` 체크아웃은 고치지 않는다(브리지가 지금 그 코드로 돈다; `ga-update.timer`가 30분마다 갱신한다). 별도 worktree나 clone에서 작업한다.
- 결과는 새 브랜치 `vm/BRIDGE-MODEL-1`에 push한다. `main`, `claude/gracious-meitner-vp49xe`에는 push하지 않는다. VM 배포(브리지에 반영)는 사용자가 따로 결정한다.
- 키·토큰은 파일과 보고서에 쓰지 않는다.
- 이 작업 자체의 모델 비용은 `vm_budget`(VM 전체 하루 30 USD) 안.

## 보고 (끝나면 한 번)

ga-mailbox `to/session_01KvzrDZZJDxYhbkb9Yb8LKs/`에 report/2 또는 notify/1 하나:

- 브랜치와 커밋 SHA
- 바뀐 파일 목록
- 전체 시험 결과(통과·실패·건너뜀 수, 걸린 시간)와 변이 A6(a)(b) 결과
- 요구와 다르게 한 부분(있으면)과 이유
