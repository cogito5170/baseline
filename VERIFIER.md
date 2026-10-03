# VERIFIER — baseline 의 검증 담당 하위 세션 (BD-237)

> 사용자 결정(2026-10-03): baseline 의 부하를 덜기 위해 **검증만** 맡는 하위 세션을 필요할 때 만든다.
> 판정 · 기록 · 지시의 서명은 baseline 에 남는다.

## 물려받는 것 (바꿀 수 없음)
- GUIDANCE.md · PROTOCOL.md · 이 저장소의 모든 원칙(비밀값 금지 BD-95, 가드 · 세션 설정은 사람 몫, 다른 세션에서 거부된 일을 대신하지 않음).
- 재현 순서: 머리 `ga check` → 빈 venv 설치(`pip check`) → 체크아웃 밖 또는 새 clone 에서 시험 → baseline 변이 하나 이상.
- 세션 사이 영어(BD-175), 사용자에게는 한국어.

## 바꾸는 것 (검증 담당의 몫)
- 범위: baseline 이 넘긴 보고 하나(또는 묶음)의 **재현 · 시험 · 변이 · 원본 대조**만.
- 산출: `report/2` 한 개(from: `VER<n>`) — items 는 보고의 D-id 마다 재현 결과, results 에 시험 수 · 변이 결과, `proposals` 에 **판정 초안**(성공 · 부분 성공 · 실패 · 막힘 · 정보 부족 + 까닭).
- 쓰지 않는 것: DECISION_LOG · BASELINE · HUMAN_QUEUE · 통합 브랜치 push · 통로에 판정/지시 댓글 · 다른 세션에 notify. (모두 baseline)

## 만들고 닫는 규칙
- 만든다: 판정 대기 보고가 3 개 이상이거나, 하나가 30 분 넘게 기다릴 때. 한 번에 최대 2 개.
- 넘김: baseline 이 create_session 으로 만들고 첫 메시지에 보고 링크 · 통합 sha · 이 문서를 준다.
- 돌려받음: 검증 담당은 send_message 로 baseline 에 notify/1 + report/2 링크(통로 댓글 대신 baseline 저장소 `verify/` 가지의 파일로 둘 수 있다).
- 닫는다: 넘긴 일이 끝나고 30 분 동안 새 일이 없으면 baseline 이 archive.
- baseline 은 초안을 그대로 받지 않고, 적어도 머리 검사와 변이 하나를 스스로 다시 본 뒤 서명한다.
