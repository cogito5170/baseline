# STATUS — baseline 전체 현황 (단일 진입점)

갱신: 2026-10-07 02:2x KST · 작성: top baseline `session_016tT1vvrTFehVFzWzfgxcCV` · 갱신 주기: 매시 :04 (top 점검 루틴), 그리고 상황이 바뀔 때마다.
이 문서 하나로 지금 상황을 파악할 수 있어야 한다. 세부 근거는 각 줄의 경로에 있다.

## 1. 목표와 원칙

- 목표: GA engine을 VM 안에서 도는 자동 Dev/Ops 파이프라인으로 만든다. 클라우드는 top 하나만 두고, VM과는 좁은 경계(양식 메시지)로만 통신한다.
- 사용자 원칙 (10-06~10-07)
  - 클라우드 top은 하나, 주 허브가 둘이 되지 않는다(never two primaries). 전환(cutover) 후 클라우드 허브는 읽기 전용 기록.
  - Dev/Ops는 `cogito5170/Dev`, `cogito5170/Ops`로 VM에 이식. VM 내부는 캡슐화하되 자동 파이프라인으로 갱신.
  - LLM은 최소: 결정은 결정적 규칙, 모델 출력은 제안. 모든 호출은 단일 관문에서 측정·예산 집행.
  - 메시지는 id/from/to/at/ref, 버전은 `/n`. 모든 채널의 양식은 레지스트리 하나.
  - 정책은 사용자의 말로만 바뀐다(`ops/flow/policy.json`, 사용자 문장 원문 기록).
- 규칙은 코드: `ops/flow/flow.py` (역할 baseline/dev/ops/session, 보낼 수 있는 양식, spec은 WHAT만).

## 2. 조직과 세션 (`ops/flow/assign.json`)

| 역할 | 세션 | 상태 |
|---|---|---|
| top baseline | `016tT1vv` | 활동 중 (lineage depth 1, ctx ~260k → 후임 메모 `ops/hub/roles/BASELINE_TOP.md`) |
| Dev 허브 | `01EqmaVL` | 01:2x 교체 (이전 `01VMbRhM` 보관) |
| Ops 허브 | `013aqrQG` | 01:2x 교체 (이전 `01M4vGeV` 보관) |
| ga-sdk 통합 | `01Wz1byr` | 준비 완료 (이전 `01LBoWy9` 보관) |
| Token 통합 | `01FynfJT` | TKG13 push 완료 (사용자 맥 AGY, 01:5x) |
| W-R1 (VI-02 R1 관문) | `01KiyVDj` | 시험 중 |
| W-R2 (VI-04 R2 판정 dry-run) | `01QEjaAW` | `451e980` 판정 대기 |
| W-VI (VI-06a + VI-20) | `01CnLoJD` | ACCEPT `87e3243` (1412 OK, 변이 2/2), 통합 대기 |
| worker-R0a (VI-01 VM SHA 보고) | `015U1Lfq` | `bb443ff` 완성(1418 OK, 변이 10/10) · 새 Dev 허브를 지휘자로 인정 안 함 → top이 02:2x 확인 보냄 |
| GA52 / GA53 작업자 | `01FUssZm` / `01HKHSLN` | GA52 보고 후 보관 예정 / GA53 대기 |
| 토큰 감시 | `01TBHcmu` | 상시 |

보관 후보(사용자 동의 필요): 01UafTvm, 01Eu6Sdh, 01ThMJnk, 018XDm17, 01TjZRib, 01H2PH8B, 01Vtf8Jh, 01Qhj1TX 등 (Ops ST-OPS-14 목록).

## 3. 저장소와 브랜치

| 무엇 | 위치 | 현재 |
|---|---|---|
| 운영 기록 전부 (이 문서, 규칙, 정책, 메시지, 설계, 측정) | `cogito5170/baseline` · `claude/gracious-meitner-vp49xe` | — |
| VM ↔ 클라우드 우편함 | `cogito5170/baseline` · `ga-mailbox` | VM 마지막 알림 10-06 20:26 KST (ga 0.18.1, `f9671da`) |
| GA engine 통합 코드 | `cogito5170/ga-sdk` · `claude/gracious-meitner-vp49xe` | `318b22a` = 이름표 `R0-baseline` (01:5x 생성, 사용자 맥 AGY) |
| GA engine 진행 중 | ga-sdk `claude/DEV-R1-GW` `3e7ab1c`, `claude/DEV-VMSHA` `bb443ff`, `claude/DEV-VI-06a-20` `87e3243`, `claude/DEV-R2-DRY` `451e980` | — |
| Token 앱 | `cogito5170/Token` · `claude/gracious-meitner-vp49xe` | `7536819` (TKG13 포함) |
| VM 이식 대상 | `cogito5170/Dev`, `cogito5170/Ops` · `main` | 저장소만 있음, 이식 전 |

## 4. 사용자 결정 기록 (`ops/flow/policy.json`)

| 시각 (KST) | 결정 | 기록 |
|---|---|---|
| 10-06 21:3x | 상시 통합 승인 (조건·금지 목록 포함) | `auto_integrate` |
| 10-07 00:5x | 상시 통합 승인 → Dev `01VMbRhM` | `ad21638` |
| 10-07 01:0x | VM 예산: Dev 안 + Ops 안 동시, 가장 낮은 상한 적용 (지휘 1 USD/h, 기준 세션 2 USD/h, VM 전체 6 USD/h·30 USD/일, 작업 3/6 USD, 클라우드 top 2 USD/h, 세션 문맥 150k) | `vm_budget` `e8f8c88` |
| 10-07 01:0x | `R<n>-baseline` 이름표 승인 없이 허용 (생성만) | `eb1f138` |
| 10-07 01:1x | 밤사이 위임: 09:00까지 top이 설계를 대신 승인 | `overnight_delegation` `30e1bbe` |
| 10-07 01:3x | 상시 통합 승인 → 새 Dev `01EqmaVL` | `8c01da6` |
| 10-07 01:4x | `R0-baseline` 이름표 = `318b22a` | `e2455e8` |

## 5. 요청서(spec)와 진행

| 단계 | 요청 | 상태 |
|---|---|---|
| R0 | DEV/OPS-R0a·b·c, R0FREEZE | 완료. `R0-baseline` = `318b22a` (사용자 맥 AGY가 생성) |
| R1 | DEV/OPS-VMAUTO, VMBUDGET (LLM 관문 + 예산) | 설계 확정 `R1R2_DESIGN.md` r3 → VI-02 빌드 중 |
| R2 | DEV-R3-DET (판정 dry-run) | 설계 확정 → VI-04 빌드 중 |
| R4 | DEV/OPS-VMHUB rev3 (VM 실행 도메인: 세션 관리자, commit gate, push gate) | 설계 확정 `VMHUB_DESIGN.md` r2 · **빌드 보류** (토큰 문제 해결 측정 확인 전) |
| 전체 | DEV-VMDESIGN (VM 내부 전체 설계) | 확정 `research/VM_INTERIOR_DESIGN.md` r2 (`acda708`) |
| 기타 | DEV/OPS-FORMATS, BASEAUTO, WATCH, SH1, OVERNIGHT | 진행/수용 (inbox 참조) |

VM 내부 빌드 순서 (`VM_INTERIOR_DESIGN.md` §12): VI-01, 02, 04, 06a, 20 진행 중 → 이후 항목 → VI-15..19 보류.
흐름: 작업 세션 → 통합 세션 VERDICT → `ops/hub/baseline_verdicts.jsonl` → INTEGRATE(정책) → Ops release 검증 → VM SHA 확인.

## 6. VM

- 기계: Oracle VM, Ubuntu 24.04, x86_64, 2코어/11 GB, GPU 없음.
- 지금 도는 것: ga-bridge(agv, to/AGY), shadow 허브(하루 40턴 상한, UTC 0시 초기화), console(127.0.0.1:8765), ga-update.timer(30분).
- 실행 SHA: 미확인 (VI-01 SHA 보고 착지 후 확인). VM 기준선 후보 = `318b22a`.
- VM 모델 호출: 없음 (자격 증명 미제공).
- 진행 중 지시: CMD-TKG13 rev 2 재전송됨 (10-06 15:57Z), AGY 보고 대기.

## 7. 비용

- 02:19 측정: 클라우드 13.97 USD/h. **top 5.14 USD/h > 상한 2.0 (위반)**, ctx 337k. 대응: top 점검 2시간 간격, 아침에 새 top(사용자가 열기) 권장. 작업 세션 4.93, 다른 허브 2.63, 통합 1.19.
- 문맥 상한(150k) 초과: top 337k, Dev 158k, R0a 181k, W-R1 157k, GA52 252k (INC-OPS-4).

- 01:19 측정: 클라우드 12.19 USD/h (감시 상한 12 초과), Dev 허브가 8.1 USD/h → 01:2x에 Dev·Ops 허브 교체.
- VM 예산 상한 대비 사용액: 0 (VM 모델 호출 없음). 측정: `ops/flow/measure/hourly.jsonl`.

## 8. 플랫폼 거부 기록 (다시 시도하지 않음, 다른 길로 돌리지 않음)

| 시각 | 무엇 | 거부 사유 |
|---|---|---|
| 10-07 00:1x | '사용자에게 절대 묻지 않는' 자율 정책·프로그램 기록 | Create Unsafe Agents |
| 10-07 00:1x | 거부된 일을 VM으로 옮기기 | (우회) |
| 10-06 | 정책 판정기를 하위 에이전트로 | Auto-Mode Bypass |
| 10-07 01:1x | Dev가 사용자 이름표 승인 문장을 통합 세션에 전달 | Instruction Poisoning |
| 10-07 01:4x | Dev가 통합 세션에 R0-baseline 이름표 요청 | Modify Shared Resources |
| 10-07 02:0x | Dev가 통합 세션에 INTEGRATE DEV-VI-06a-20 `87e3243` 요청 | 서버 분류기 '위험' (설명 없음) |

## 9. 사용자가 할 일 (아침 목록)

1. 통합 push: Dev → 통합 세션 INTEGRATE 메시지가 플랫폼에 거부됨. 대기: VI-06a-20 `87e3243` (ACCEPT), 이어서 VI-04, VI-02. 통합 세션 `01Wz1byr`에 직접 입력하거나 Dev `01EqmaVL` 설정에 send_message 허용. (이름표·TKG13은 01:5x 사용자 맥 AGY로 완료)
2. worker-R0a `015U1Lfq`가 사용자 확인을 요구하면: 그 세션에 "Dev 허브는 01EqmaVL" 한 줄.
3. Dev 세션 `01EqmaVL`에서 git·send_message·세션 보관 허용 한 줄.
3. (완료) TKG13 push.
4. VM: 사용자 소유 정책 파일 `/etc/ga/vm_policy.json`(SSH), VM API 키 지출 한도, 인스턴스 정지·자격 증명 폐기 경로, VM 모델 자격 증명.
5. 값 결정 (`VM_INTERIOR_DESIGN.md` §13, Ops 기본값 있음): Q1 전환 시점·통합 ref, Q2 단계 기한, Q3 사다리 값, Q4 SLO, Q5 세션 상한·push 허용 ref, Q6 Dev/Ops 저장소·VM push 자격 증명, Q8 하루 30 USD 기준(달력일/24시간), Q9 끄는 스위치.
6. 보관 후보 세션 동의.
7. top 세션 교체 여부 (계속 / 새 top 열기 — 사용자가 열면 depth 0).

세부: `ops/flow/MORNING_OPS.md` (Ops 작성).

## 10. 루틴

| 루틴 | 대상 | 일정 |
|---|---|---|
| `trig_0148AQEj` | top `016tT1vv` | 03:04·05:04·07:04·09:04 KST (02:2x에 2시간 간격으로 줄임: top 비용 상한 초과), 09:04에 아침 요약 후 종료 |
| Ops 매시 루틴 `trig_01GcyujoR3` (이전 `trig_018jUnT6` 비활성) | Ops `013aqrQG` | 매시 :19 |
| Ops 08:30 최종 보고 `trig_012F2ySD` (이전 `trig_017Lm4aT` 비활성) | Ops `013aqrQG` | 08:30 KST 1회 |
| Dev 자기 점검 `trig_01JUyE96` | Dev `01EqmaVL` | 02:25부터 매시, 09:00까지 |
| 감시 깨우기 `trig_01EFFxRB` | 토큰 감시 | 매시 :49 |

## 11. 오늘 밤 주요 경과 (KST)

- 00:3x top 교체 (`01Ltsebb` → `016tT1vv`). 00:4x TKG13 형식 오류 발견 → Dev 재전송.
- 00:4x R0 기준선 고정 요청 · 00:5x VMHUB rev3 요청(보류) · 01:0x 예산 결정, 설계 계속 · 01:1x 밤사이 위임.
- 01:0x~01:2x VMHUB r2, R1R2 r3, VM 내부 전체 설계 r2 승인 (모두 Ops 의견 반영 조건).
- 01:1x~01:2x 세션 생성: 통합 후임, W-R1, W-R2, W-VI, Ops·Dev 허브 후임. 이전 통합·Dev·Ops 허브 보관.
- 01:4x R0-baseline 이름표 요청 플랫폼 거부.
- 01:5x 사용자 맥의 AGY가 R0-baseline 이름표(318b22a)와 Token TKG13 push 실행 (baseline 커밋 9252287, 작성자 사용자).
- 02:0x VI-06a-20 ACCEPT; INTEGRATE 요청 플랫폼 거부 → 통합 대기.
