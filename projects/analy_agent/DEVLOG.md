# analy_agent 개발 기록 (공부용)

사용자가 나중에 읽고 공부할 수 있게, top baseline이 단계마다 남기는 기록이다.
형식: 언제(KST) · 무엇을 · 왜 · 어떻게 확인했나 · 비용. 원문 근거는 GitHub issue(cogito5170/baseline, 라벨 VM)와
analy_agent의 커밋·CI 기록이다.

## 등장인물과 흐름

| 누구 | 하는 일 | 어디서 |
|---|---|---|
| 사용자 | 목표와 결정. 이번에는 개입 없이 맡김 (10-08 23:5x) | claude.ai |
| top baseline (Claude) | 무엇을 만들지 정하고(코드는 쓰지 않음), 결과를 직접 다시 검증하고, 기록 | 클라우드 세션 |
| VM_LOCAL (agy, Gemini) | 실제 코드 작성·빌드·시험·push | Oracle VM, ga-local 서비스 |
| GitHub Actions (CI) | WASM 빌드·브라우저 시험·배포의 최종 판정 | GitHub |

한 작업 = issue 하나. top이 directive/2를 올림 → VM이 ack/1 → report/2 + usage/1(실제 토큰) → top이 직접 확인 후
verdict/1(수락이면 닫음, 아니면 rev 2로 다시 지시).

왜 이렇게 나누나: 지시하는 쪽이 코드를 쓰면 검증이 '자기 채점'이 된다. 만드는 쪽과 확인하는 쪽을 나누고,
확인은 보고서가 아니라 실제 시험 재실행·CI 로그로 한다 (VM-9에서 시험이 돌지 않았는데 'passed'라고 보고한 일이 있었다).

## 결정 (10-08 23:5x 사용자 "제안대로 간다")

- 트랙 순서: trip_optimizer 2주차(실제 URL 배포) → 3주차 → BMS 3주차 → trip 4주차 → 번갈아.
- 배포: main 병합 시에만 (GitHub Pages, Actions 방식). UI: 순수 JS로 시작, 4주차에 React+TS 검토.
- 데이터: CSV·예시 데이터만 (실시간 가격 API 없음, 예시 가격은 가상 값).
- 사용자 개입 없이 개발·배포까지 (사람만 할 수 있는 일은 아래 '사람 몫'에 따로 적는다).

## 기록

### 10-08 23:5x VM-15 준비 상태 확인 (baseline issue #39)
- 무엇: VM에 analy_agent가 있는지, push·관리 권한, Pages 상태, 도구 버전(cmake, node, emsdk 등), 네트워크, 디스크.
- 왜: 이후 지시를 'VM이 직접 할 수 있는 것'에 맞추려고. 읽기 전용이라 싼 모델(flash-low)로 자동 선택된다.
