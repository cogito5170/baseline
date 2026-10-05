# Token 작업자 요청 (소유 범위 밖이라 그 작업에서 못 한 것)

다음 해당 작업의 지시에 붙여 보낸다. 반영되면 줄을 지우고 BD 를 단다.

| 출처 | 요청 | 보낼 곳 |
|---|---|---|
| CMD-GC13 | backend/app/main.py 에 HTTPException(detail={code,message}) → `{code,message}` 본문 예외 처리기 | backend/app/main.py 소유 작업 — 로드맵에 아직 없음, 작은 core-backend 정리 작업으로 묶을 것 |
| CMD-GC13 | GC15 뒤 `router.set_audit_recorder(audit.api.record)` 배선, 시작 시 `open_pool` | GC15 (소유 확장으로 붙여 보냄) |
| CMD-GC14 | `identity/api.py`(current_user 재수출) 추가 뒤 workspace 의 fallback 제거 | GC15 (소유 확장으로 붙여 보냄) |
| CMD-FE1 | 갤러리 라우트(frontend/src/app/**)와 components.css 전역 @import | GC41 |
| CMD-GC13 | 로그인 속도 제한이 프로세스 메모리 — 다중 프로세스면 공유 안 됨(MVP 한계로 기록) | 운영 단계 |
| CMD-GC0 | baseline 요청 9 건(l0-telemetry 공급자 usage 파서 · 비밀 스크러버 · 호출별 시각/CLI 비용 · router 통계 내보내기 · Codex/Gemini 수집기 · turn.started/턴 중 이벤트 · L0 시각 · 풀 판정 · usage.json 원자적 쓰기) | ga-sdk / l0-telemetry 후속(GA34 이후) |
| CMD-GC20 | Upload.job_id 를 채울 ingestion enqueuer 훅 | GC22 |
| CMD-GC21 | openapi Comparison 에 선택적 범위(P10/P90) 필드 — 계약 변경 | 다음 contract 작업 |
| CMD-GC31 | estimation 의 HTTP 경로 · PG 저장소 미구현, 정가 비용 MAPE 104.5%(기준선 92.7%보다 나쁨) | 후속 consulting 작업 |
| CMD-GC32 | openapi: 추천 → Proposal 경로 | 다음 contract 작업 |
| CMD-GC22 | 워커 프로세스의 도메인 이벤트가 api 프로세스에 닿지 않음 — domain_events 아웃박스 전달 경로 결정 | 후속 core-backend/infra 작업(아키텍처) |
| CMD-GC22 | 워커 사망으로 남은 claim 회수(claimed_at 기준) | 후속 ingestion 작업 |
| CMD-GC30 · GC22 · GC13 | 앱 시작 시 배선: advisor.wiring.subscribe(), source enqueuer, audit recorder, open_pool | 마무리 조립 작업(GC19 신설 예정) |
| CMD-GC33 | usage.api.prices() · main.py 에 simulation 라우터 마운트 · advisor.submit_proposal 실제 배선 | 마무리 조립 작업(GC19) · 후속 usage 작업(GC24) |
| CMD-GC23 | 작업 세션에서 고정 버전 l0-telemetry · rlo-sdk pip 설치가 sandbox 에 막힘 → baseline 이 같은 sha 로 대신 시험 | 환경 설정(사람) 또는 baseline 대리 검증 유지 |
| CMD-GC34 | quota.api.list_budgets(ws) | 마무리 조립 작업(GC19) |
| CMD-GC19 | estimation · integration · run 도메인의 HTTP 라우터 없음 → openapi 22 경로 미마운트 | 후속(GC25 신설: 남은 라우터) |
| CMD-GC19 | report 내보내기에 uuid 가 아닌 id → 500(404 여야) | GC25 에 묶음 |
| CMD-GC19 | API · 워커 두 프로세스 사이 이벤트 전달(아웃박스) 미검증 · 미구현, quota 경보 평가 시점 | 후속 아키텍처 작업 |
| CMD-IF1 | frontend: next.config 에 정적 export(`output:"export"`, trailingSlash, images.unoptimized)를 환경 변수로 켜기 — 지금은 desktop 빌드 스크립트가 복사본에서 덮어씀 | 후속 frontend 작업 |
| CMD-IF1 | frontend: `window.gaDesktop` 이 있으면 /live 에서 로그인 리디렉션 생략(크롬 없이) → preload 의 placeholder 우회 제거 | 후속 frontend 작업 + IF 후속 |
| CMD-IF1 | frontend: /live 가 `window.gaDesktop.sidecarUrl` 을 읽기(지금은 URL 쿼리 api) | 후속 frontend 작업 |
| CMD-IF1 | desktop 시험이 추적 파일 tests/electron-window.png 를 매 실행 덮어씀 → test-results 로 | IF 후속(설치 파일 electron-builder 와 함께) |
