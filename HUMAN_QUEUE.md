# HUMAN_QUEUE — 사람만 할 수 있는 일 (BD-205)

> 사용자 결정(2026-10-03): 사람 확인은 남기되 **자동 시스템은 기다리지 않는다**.
> baseline 은 사람 몫을 여기에 올리고, 그 일에 묶이지 않은 다른 일을 계속 굴린다.
> 각 항목은 아이폰에서도 끝낼 수 있게 **링크 하나 + 할 일 한 줄**로 쓴다. Mac 터미널을 요구하지 않는다.

## 왜 사람인가 (닫힌 목록)

| 종류 | 까닭 |
|---|---|
| G 가드 · 세션 설정 | AI 가 다른 AI 의 가드 · 권한을 바꾸는 일은 분류기가 사람에게 남긴다(BD-183 · 196). 감시가 의미 있으려면 이 고리는 사람이어야 한다 |
| E 환경 설정 | 클라우드 환경의 네트워크 · 비밀값 · 저장소 연결은 사용자 설정에서만 바뀐다 |
| P 개인 자료 · 계정 | 본인 사진 · 계정 자격 · 결제 |
| D 사용자 결정 | 배포(게이트 1) · 예산 · 방향 |

## 대기 중

| # | 종류 | 할 일 | 링크 | 기다리는 세션 | 올린 때 |
|---|---|---|---|---|---|
| Q1 | E | 기존 환경은 Network access 를 바꿀 수 없음(사용자 확인: Custom 은 만들 때만) → **새 환경 하나 만들기**: 이름 `gmg-net`, Network access = Custom, Allowed domains 에 `api.openverse.org` · `live.staticflickr.com` · `upload.wikimedia.org` · `commons.wikimedia.org` · `archive.org`(기본 패키지 목록 유지), 비밀값 없음. 만들면 baseline 이 그 환경에 GMG5 전용 세션을 만들어 넘긴다(GMG 세션은 그대로) | claude.ai/code → 새 세션 화면의 환경 메뉴 → 새 환경 · 안내 https://code.claude.com/docs/en/cloud-environments#network-access | GMG5 만 | 2026-10-03 |
| Q5 | P | agy 실행 결과: 실행 명령이 'Gemini 3 Flash' 에 해당하는 agy 모델을 못 찾아 멈춤(설계대로 — 모델은 사용자가 고름). **그 위에 나온 모델 목록 줄들과 `/usage` 줄을 이 채팅에 붙여넣기**(또는 Mac 에서 `agy models` 한 줄 실행 결과). baseline 이 고를 후보를 권하고, 고른 뒤 `export GENTLEMONSTER_AGY_MODEL=<이름>` 한 줄 | Mac 터미널의 직전 출력 | GMG7 마무리 · GA23 | 2026-10-03 |

## 끝남

| # | 종류 | 할 일 | 결과 |
|---|---|---|---|
| — | G | W1 가드 v1 을 amp main 에 | `714c00b` (BD-189) |
| — | G | W1 가드 v2(알림 읽기 · send_message) | `344a604` (BD-194) |
| — | G | W1 가드 rlo 0.5.1 PIN | `36ca54d` (BD-204) |
| — | P | 사진 14 장 비공개 저장소 | `gm-photos@780f412` (BD-191 · 193) |

## 규칙

1. 사람 몫이 생기면 baseline 은 여기에 올리고, 통로에 "사람 몫 Qn 대기" 한 줄만 남기고, **그 일에 묶이지 않은 일을 계속한다.** 세션에게 "사람을 기다려라" 만 지시하지 않는다 — 기다리는 동안 할 수 있는 일을 함께 준다.
2. 가드 변경은 ga_rlo 가 만든 판으로 **묶어서** 올린다(GR2 · GR3). 한 줄짜리는 GitHub 웹 편집 링크(`https://github.com/<owner>/<repo>/edit/main/<path>`)와 바꿀 줄을 그대로 준다.
3. 끝나면 baseline 이 결과(커밋 · 확인)를 적어 '끝남' 으로 옮긴다. 매시 안전망이 이 표를 본다.
| Q4 | G | WUG 가 baseline 지시를 받도록 허락 | 사용자가 16:21 에 WUG 대화창에 한 줄(같은 줄이 실수로 GMG 에도 감 → baseline 이 GMG 에 정정, BD-241). WUG 는 CMD-WUG1 rev 3 시작, 보고는 send_message 로 baseline 에 |
| Q2 | G | W1 가지에 main 병합 | 사용자가 AMP 대화창에서 허락 → w1/work 714c00b→36ca54d(가드 v2 모형 · 허락 바로 적용, rlo 는 0.5.0 그대로 — 새 세션 없이는 SessionStart 가 안 돎) (BD-242) |
| Q3 | D | Gemini API 키 결제 | 사용자 결정: 켜지 않는다 — 무료 하루 20 요청 유지(BD-242) |
