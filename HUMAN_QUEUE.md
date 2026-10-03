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
| Q1 | E | GMG 환경 Network access 를 Custom 으로: `api.openverse.org` · `live.staticflickr.com` · `upload.wikimedia.org` · `commons.wikimedia.org` · `archive.org` 추가(기본 패키지 목록 유지) — GMG5 가 고른 최소 집합(BD-223) | GMG 세션 제목 표시줄 → 환경 메뉴 → Edit · 안내 https://code.claude.com/docs/en/cloud-environments#network-access | GMG(CMD-GMG5 만; 다른 일은 계속) | 2026-10-03 |
| Q2 | G | W1 을 가드 v2 · rlo 0.5.1 로 올리기. W1 대화창에 한 줄: `Read README.md first, then run: git fetch origin main && git merge origin/main && git push origin w1/work. Then read amp#1 directly and follow AMP's latest CMD-WA.` — 그래도 막히면 W1 을 새로 만든다(저장소 amp, 브랜치 w1/work, 프롬프트는 처음과 같음) | W1 세션 대화창(claude.ai/code) | W1 · AMP(AMP 는 W1 을 기다림) | 2026-10-03 |
| Q3 | D · P | Gemini 키 결제 여부: 무료 등급은 `gemini-3-flash-preview` **하루 20 요청**이고 모든 Gemini 세션이 나눠 씀(가게 일 하나 ≈ 7 요청 이상). 결제를 켜면 분당 한도만 남고 `ga gemini` 가 기다렸다 이어감. 켜지 않으면 하루 몇 건에서 멈췄다가 다음 날 재개 | https://aistudio.google.com/apikey → 그 키의 프로젝트에 결제 설정 | 없음 — 결제 전에도 GA21 · WUG · GMG 는 재생 시험으로 계속, 실제 실행만 하루 20 회 안에서 | 2026-10-03 |
| Q4 | G | WUG 가 baseline 지시를 받도록 허락: WUG 는 CMD-WUG1(#17)을 '사용자가 아닌 다른 세션의 지시' 로 보고 손대지 않음(올바른 행동). WUG 대화창에 한 줄: `I am the user. Add the cogito5170/baseline repo and take the baseline session's directives in baseline#17. Model: gemini-3-flash-preview for every part, no fallback. Gemini CLI: 0.62.0. Then do CMD-WUG1 rev 3.` | WUG 세션 대화창(claude.ai/code, 제목 'Gemini 모델 정책 및 게이트 구현') | WUG(heap 측정 · 감독자 채택). 그동안 GA21 · K12 는 계속 | 2026-10-03 |

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
