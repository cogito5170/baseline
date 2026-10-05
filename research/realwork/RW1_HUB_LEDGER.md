# RW1 (가) 허브 방식 장부 — Token MVP

작업 하나 = 세션 하나. 숫자는 세션 기록(get_session 의 usage, 세션이 archive 될 때 읽음)에서 그대로 옮긴다. 비용은 CLI 자체 비용(cost_usd)이다.

| 작업 | 역할 | 모델 | 판정 되돌림 | 사람 개입 | input | output | cache read | cache write | cost_usd | 최종 | BD |
|---|---|---|---|---|---|---|---|---|---|---|---|
| CMD-GC0 | arch | Opus | 2(보고 형식) | 3(추가 요청 3 건) | 5,953 | 226,801 | 21,714,078 | 492,410 | 12.36 | 성공 | BD-345 |
| CMD-GC10 | core-backend | Sonnet | 1(보고 change_size, 양식 탓) | 0 | 538 | 6,183 | 1,119,383 | 63,541 | 0.54 | 성공 | BD-347 |
| CMD-DS1 | design | Sonnet | 1(change_size · 통합 merge) | 0 | 544 | 10,676 | 1,427,320 | 68,788 | 0.67 | 성공 | BD-349 |
| CMD-GC11 | infra | Sonnet | 1(commits 형식, 양식 탓) | 0 | 538 | 9,334 | 1,114,908 | 63,393 | 0.57 | 성공 | BD-351 |
| CMD-GC40 | frontend | Sonnet | 1(commits 형식 · 통합 merge) | 0 | 549 | 24,498 | 2,076,371 | 64,416 | 0.92 | 성공 | BD-352 |
| CMD-DS2 | design | Opus | 2(commits 형식 · 통합 merge 경쟁) | 1(baseline 이 순서 지정) | 1,071 | 22,242 | 3,199,359 | 79,176 | 1.72 | 성공 | BD-353 |
