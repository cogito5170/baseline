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
| CMD-GC12 | core-backend | Sonnet | 3(commits 형식 · healthz skip · 통합 merge 2 회) | 1(순서 지정) | 2,096 | 13,312 | 3,168,631 | 57,756 | 1.00 | 성공 | BD-354 |
| CMD-GC13 | core-backend | Sonnet | 0 | 0 | 28 | 15,461 | 1,093,430 | 51,040 | 0.58 | 성공 | BD-355 |
| CMD-GC14 | core-backend | Sonnet | 0 | 0 | 28 | 14,592 | 1,127,600 | 56,568 | 0.60 | 성공 | BD-357 |
| CMD-FE1 | frontend | Sonnet | 1(check 재현 — devDeps 누락) | 1(소유 확장) | 570 | 22,213 | 3,227,818 | 109,113 | 1.31 | 성공 | BD-359 |
| CMD-RN1 | core-backend | Sonnet | 0 | 0 | 30 | 27,604 | 1,274,504 | 67,581 | 0.80 | 성공 | BD-360 |
| CMD-GC20 | ingestion-analytics | Sonnet | 1(통합 merge) | 0 | 542 | 14,351 | 1,505,589 | 83,739 | 0.78 | 성공 | BD-361 |
| CMD-GC43 | frontend | Sonnet | 1(통합 merge) | 1(순서 지정) | 548 | 11,350 | 1,663,366 | 75,703 | 0.75 | 성공 | BD-362 |
| CMD-GC15 | core-backend | Sonnet | 1(통합 merge) | 1(순서 · 소유 확장) | 576 | 20,183 | 3,233,357 | 97,232 | 1.24 | 성공 | BD-363 |
| CMD-GC21 | ingestion-analytics | Sonnet | 1(통합 merge) | 1(순서 지정) | 1,084 | 48,673 | 4,665,502 | 145,079 | 2.00 | 성공 | BD-364 |
| CMD-GC42 | frontend | Sonnet | 1(통합 merge) | 1(순서 지정) | 1,084 | 27,974 | 3,566,674 | 108,024 | 1.43 | 성공 | BD-365 |
| CMD-DS3 | design | Opus | 1(통합 merge) | 1(순서 · 소유 확장) | 6,275 | 18,251 | 2,722,288 | 75,124 | 1.54 | 성공 | BD-366 |
| CMD-GC41 | frontend | Sonnet | 2(변이 생존 → 시험 보강 · 통합 merge) | 1(순서 지정) | 1,074 | 21,940 | 2,942,397 | 98,100 | 1.20 | 성공 | BD-367 |
| CMD-GC16 | core-backend | Sonnet | 1(소유 확장 · 통합 merge) | 1(소유 확장) | 554 | 16,866 | 2,041,156 | 84,253 | 0.92 | 성공 | BD-368 |
| CMD-GC17 | core-backend | Sonnet | 1(통합 merge) | 1(순서 지정) | 1,061 | 17,480 | 2,326,033 | 61,506 | 0.89 | 성공 | BD-369 |
| CMD-GC32 | consulting | Sonnet | 1(통합 merge) | 1(순서 지정) | 1,078 | 25,643 | 3,267,969 | 103,508 | 1.33 | 성공 | BD-370 |
| CMD-GC31 | consulting | Sonnet | 2(누설 시험 보강 · 통합 merge) | 1(순서 지정) | 1,064 | 19,034 | 2,313,186 | 88,332 | 1.01 | 성공 | BD-371 |
| CMD-GC22 | ingestion-analytics | Sonnet | 2(경계 위반 · 통합 merge) | 1(소유 확장) | 1,086 | 39,125 | 4,398,242 | 103,786 | 1.69 | 성공 | BD-372 |
| CMD-GC30 | consulting | Sonnet | 0 | 0 | 60 | 38,488 | 3,115,447 | 127,023 | 1.52 | 성공 | BD-373 |
| CMD-GC34 | consulting | Sonnet | 0 | 0 | 34 | 13,709 | 1,341,263 | 81,561 | 0.73 | 성공 | BD-375 |
| CMD-GC33 | consulting | Sonnet | 2(통합 merge 2 회) | 0 | 572 | 34,093 | 3,389,578 | 117,869 | 1.49 | 성공 | BD-376 |
| CMD-GC23 | ingestion-analytics | Sonnet | 3(튜플 · OpenAI 중첩 키 · 통합 merge) | 1(baseline 대리 검증 — 의존성 설치 불가) | 1,586 | 22,489 | 3,078,681 | 91,196 | 1.21 | 성공(보고 머리는 baseline 판정으로 대체) | BD-377 |
| CMD-GC24 | ingestion-analytics | Sonnet | 0 | 0 | 58 | 25,744 | 3,183,205 | 124,284 | 1.39 | 성공 | BD-379 |
| CMD-FE2 | frontend | Opus | 1(통합 merge) | 0 | 622 | 58,875 | 7,676,443 | 130,359 | 3.76 | 성공 | BD-381 |
| CMD-GC19 | core-backend | Sonnet | 0 | 0 | 78 | 36,194 | 4,766,307 | 147,674 | 1.91 | 성공 | BD-383 |
| CMD-IF1 | infra | Sonnet | 0 | 0 | 6,372 | 28,519 | 5,534,946 | 121,934 | 1.89 | 성공 | BD-385 |
| CMD-GC25 | core-backend | Sonnet | 1(baseline 변이 생존 2 → 시험 추가) | 0 | 148 | 66,739 | 11,589,496 | 195,056 | 3.77 | 성공 | BD-389 |
| CMD-GC18 | core-backend | Opus | 2(변이 생존 1 → 시험 추가 · 통합 merge 순서 대기) | 1(baseline 이 착지 순서 지정) | 6,973 | 48,860 | 7,395,692 | 151,070 | 3.69 | 성공 | BD-390 |
| CMD-IF2 | infra | Sonnet | 0 | 0 | 82 | 32,463 | 4,288,600 | 121,866 | 1.67 | 성공 | BD-399 |
| CMD-FE3 | frontend | Sonnet | 0 | 0 | 62 | 15,292 | 2,840,026 | 88,527 | 1.08 | 성공 | BD-403 |
| CMD-GC50 | infra | Sonnet | 0 | 0 | 82 | 31,144 | 4,203,890 | 118,992 | 1.63 | 성공 | BD-423 |
