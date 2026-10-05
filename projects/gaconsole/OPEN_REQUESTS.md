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

