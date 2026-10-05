# GA Console — 설계 (BD-428)

사용자(2026-10-05): "지금은 터미널에서 사용하기 너무 불편하다. linux 명령어와 너가 해놓은 작업들이나 브랜치들이 섞여서 내가 일일이 너에게 물어보는 것이 귀찮다. token 과 같이(로그인은 필요없다) 작동할 수 있는 console 을 만들어라. UI/UX 적으로 보기 편하게, 디자인 frontend 는 gentleMonster repo 를 참고해서 프론트엔드를 동적으로. baseline 은 ga-sdk 를 활용해서 세션들을 만들고 작업을 시작해라."

## 1. 무엇인가

**GA Console** 은 GA Engine 을 위한 운영 화면이다(NAMING: GA UI 의 확장, GA API 위에 선다). 맥에서 `ga console` 한 줄로 브라우저가 열린다.

- 로그인은 없다. 127.0.0.1 에서만 열리고, 접근은 일회용 토큰으로 한다(GA36 ga ui 와 같은 보안).
- 사용자가 지금 baseline 에게 묻는 것을 화면이 대답한다:

| 화면 | 사용자가 묻던 것 | 보여 주는 것 |
|---|---|---|
| 지금 | "통신하고 있나?" "반응이 갔나?" | bridge 가 살아 있는지 · 마지막 확인 시각, 우편함 최근 메시지, 진행 중인 agv 작업과 턴마다 토큰(실시간) |
| 작업 | "AG10 이 뭔데?" | 지시 하나하나: 보낸 때 · 상태(보냄 → 도는 중 → 보고 → 판정 · 통합 · 되돌림) · 결과 · 관련 결정(BD) · 쉬운 한 줄 설명 |
| 브랜치 | "브랜치들이 섞인다" | 저장소별 통합 머리, claude/* · agv/* 브랜치, 통합됐는지, 마지막 변경, 사람이 읽는 이름 |
| 서비스 | "API 가 왜 안 떴지?" | Token 의 api · worker · web 을 버튼으로 켜고 끄기, 각각 상태(health) · 로그, `.env` 자동 불러오기 |
| 토큰 | "얼마나 썼지?" | agv 턴 장부 · 작업별 토큰 · 오늘 사용량 · 허브(RW1) 장부 |
| 묻기 | 자연어 질문 | ga ask / ga do 상자(비용 먼저 · 확인 뒤 실행) |
| 결정 | "왜 이렇게 됐지?" | DECISION_LOG 의 BD 를 검색 · 시간순 |

## 2. 디자인 — gentleMonster 문법

gentleMonster 의 원칙을 그대로 따른다(`docs/FRONTEND_ENGINE.md`, `gentle_monster/apps/worldplan`).

- 종이 · 잉크 · 머리카락 선, 하나의 뜨거운 강조색이다(GM red #D9480F, 화면 픽셀의 0.3–4%).
- 큰 활자 마스트헤드와 빈 공간 한가운데 하나의 주인공이 있다. 그 순간 가장 중요한 것 하나를 크게 보인다. 예: "bridge 살아 있음 · 12 초 전".
- 움직임은 유전자다. 살아 있는 것만 숨 쉬듯 움직인다(도는 작업, 들어오는 메시지). reduced-motion 에서는 절대 움직이지 않는다.
- 빌드가 없다. 정적 파일(index.html · app.css · app.js · tokens.css)과 DTCG tokens.json 으로 만들고, 외부 요청은 0 이다.
- 판정은 코드다(gentleMonster `apps/check` 의 V 를 이 화면에). 375 · 1440 px 에서 넘침이 없어야 하고, 렌더된 대비가 WCAG 를 넘어야 하며, 다음도 모두 만족해야 한다:
  - 폰 최소 글자 12 px
  - 외부 요청 0
  - JS 오류 0
  - 접근 가능한 이름
  - 제목 순서
  - reduced-motion
  - 무게
- 한국어 쉬운 낱말을 쓴다. 기술 용어는 한 번 풀어 쓴다(예: "통합 = 공용 브랜치에 합침").

## 3. 구조

```
맥 브라우저 ── GA Console 화면(정적, 동적 갱신: SSE) ── GA API(`ga console` 서버, 127.0.0.1, 토큰)
                                                        ├─ 읽기: ~/baseline(지시 · 결정 · 우편함 · 장부), git 저장소들, bridge 상태
                                                        ├─ 서비스 관리: Token api · worker · web(argv 고정, 셸 없음, .env 는 이름만 · 값은 화면에 안 나옴)
                                                        └─ ga ask / do / bridge(GA36 · GA37 엔진)
```

설정은 `~/.ga/console.json` 하나다. `ga console init` 이 맥의 지금 배치(~/baseline, ~/token, ~/ga-sdk-check, ~/agy-bridge.json)로 기본값을 쓴다.

## 4. 작업(ga-sdk 로 세션 생성 — GA Protocol directive/2, 지시 하나 = 세션 하나)

| id | 맡음 | 모델 | 무엇 | 순서 |
|---|---|---|---|---|
| CMD-CON1 | design | Opus | 토큰(DTCG) · 화면 문법 · 골든 화면(가짜 데이터 HTML) · V 판정 스크립트 | 지금 |
| CMD-CON2 | GA API | Opus | `ga console` 서버 · 수집기 · 서비스 관리 · SSE · 보안 | 지금(CON1 과 나란히) |
| CMD-CON3 | frontend | Opus | 정적 화면 7 개를 API 에 연결, 동적 갱신, V 판정 통과 | CON1 · CON2 뒤 |

API 계약은 CON2 지시문에 고정한다. CON3 은 그 계약과 CON1 의 골든 화면으로 만든다.
