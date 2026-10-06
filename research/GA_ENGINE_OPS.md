# GA Engine 운영 자율 — rlo 고리 위의 문제 해결 엔진 (BD-472 초안, 10-06 20:5x KST)

사용자 지시(10-06 20:4x): 운영 이상을 "적고 넘어가지" 말고 스스로 고친다. 엔진은 적정 LLM 선택 · 토큰 최적화 ·
노드와 baseline 의 협업 구조를 갖고, rlo-sdk(ga/rlo 로 이미 ga-sdk 안)의 철학 위에서 돈다.

## 1. rlo 의 철학 = 닫힌 고리

rlo `Autonomy`: 관측(Sensor · Telemetry) → 세계 모형(MS, 문턱) → 결정 문맥(DC) → 결정(LLM) → Guard → 실행기 → VERIFY(창 안에서
사후조건 확인) → health. 행동은 `action-spec/1`(name · risk · preconditions · postcondition · window_ms)로 선언되고,
Guard 가 위험 등급으로 막으며, 실행 뒤에는 반드시 VERIFY 가 닫는다.

지금 ga 운영은 이 고리의 앞 절반(관측 · 기록)만 있고 뒤 절반(행동 · VERIFY · 승격)이 없다. 그래서 이상은
`res.plan.append(...)` · ASK_HUMAN · "대기"로 끝나고, 사람이나 baseline 모델이 손으로 닫는다.

## 2. 점검: 열린 고리 (10-06 기준)

| # | 이상 | 지금 동작 | 고리를 닫는 행동 (코드 우선) |
|---|---|---|---|
| O1 | hub 일일 한도 도달 (16:18~ shadow 정지) | `plan` 에 "waits", 알림 없음 | 무료 판정은 세지 않음 + baseline-ops 경보 1회 (**CMD-GA56 진행 중**) |
| O2 | shadow: judge success 인데 결정이 전부 ASK_HUMAN, 모델 호출 0 (TKG1-8, served/input 없음) | 기록만; 게이트 0/10 영구 | 결정 턴 실패를 분류(backend 오류 · 시간 초과 · 양식) → 사다리 다음 rung 으로 1회 재시도 → 그래도 실패면 경보에 원인 표기 |
| O3 | 작업자 환경에서만 실패하는 시험 (GA53: 10건, 통합 세션에선 통과) | 작업자가 "base 도 실패"라 적고 끝 | judge 의 기존 실패 구분을 작업자 보고에도 강제: 같은 환경에서 base 를 돌려 차집합만 보고 |
| O4 | 변이 생존 (GA52 d5 · h5) | 허브 모델이 손으로 SEND_BACK 작성 | 생존 변이 → 틀에 맞춘 SEND_BACK(파일 · 줄 · 기대 동작) 자동 생성, 모델 0턴 |
| O5 | 세션 문맥 > 150k (통합 세션 203k → 238k) | 감시가 알리고 허브가 손으로 교체 | 후임 프롬프트를 상태 파일에서 코드가 조립 → 새 세션 · 보관 · "hub is now" 자동 |
| O6 | 세션 계보 깊이 7/8 (이 허브) | 아무도 안 봄 | 다음 허브는 깊이를 끊어 시작해야 함(아래 4.3). 깊이 ≥ limit-1 이면 경보 |
| O7 | 작업자 시작 base 어긋남 (GA49) | 허브가 손으로 merge-base 확인 | verdict 코드가 ancestor 아니면 자동 SEND_BACK("re-merge <head>") |
| O8 | relay 가 `<` `>` 를 `&lt;` `&gt;` 로 바꿈 | 수신 세션이 추측 | 변이는 파일(sha 고정 경로)로만 전달, 본문엔 id 만 |
| O9 | 콘솔 서비스 'starting' 고착 | 표시만 | CMD-GA53 S3 (진행 중) |
| O10 | 통합 push 마다 사용자 승인 | 사람 대기 | 유일하게 남길 사람 관문. 상시 승인 한 줄(이미 제안) 또는 VM 측 통합(stage 3) |

## 3. 설계: ga ops 고리

```
관측(코드, 0토큰) ── 메일함 · 세션 메타(get_session) · shadow/ledger · VM notify · 시험 결과
   │  rule/1: 조건 → 이상 종류 + 증거 (예: cap_reached, decide_no_model, ctx_over, base_drift, mut_survived)
   ▼
결정 ── 1순위: 규칙표가 행동을 바로 고름 (모델 0턴)
        2순위: 증거 카드(≤1.5k 토큰, 고정 크기) + 싼 모델 1턴 → 행동 이름 하나
        3순위: 강한 모델 1–2턴 (재계획 · 새 directive 초안)
   ▼
Guard (rlo guard, 위험 등급) ── low: 바로 실행 / medium: 실행 + 보고 / high(push · 권한 · 비용): 사람
   ▼
실행기 ── action-spec/1 로 선언된 운영 행동: retry_next_rung, alert_ops, send_back_template, successor_session,
          rebase_request, rerun_on_base, raise_cap_once(예산 안), open_worker(directive)
   ▼
VERIFY ── 창(window_ms) 안에 사후조건 확인: 예) "다음 tick 에 shadow 행이 생겼다", "새 세션 ack 가 왔다".
          실패 → 같은 이상으로 다시 들어오되 사다리 한 칸 위로. 같은 실패 2회 = blocked 보고(무한 재시도 없음).
```

### 3.1 토큰 원칙 (AUTONOMY_MACHINE §3 을 운영에 적용)
- 탐지 · 분류 · 대부분의 행동은 코드. 이번 세션에서 허브 모델이 손으로 한 일(cap 원인 찾기, SEND_BACK 문장, 후임
  프롬프트)은 전부 규칙 + 틀로 대체 가능하다.
- 모델이 필요한 경우만 고정 크기 증거 카드로 1턴. 대화 기록을 싣지 않는다.
- 모델 사다리: 규칙(0) → flash 급(분류 · 짧은 문장) → pro/opus 급(새 directive · 설계). GA51 의 "served rung" 기록을
  운영 결정에도 쓴다.

### 3.2 노드와 baseline 의 협업
- **노드(VM)**: 자기 관측에 대해 low-risk 행동을 enforce 로 직접 한다(재시도 · rung 변경 · 경보). 결과는 `alert/1`
  (종류 · 증거 · 한 행동 · VERIFY 결과)로 baseline-ops 에 1통.
- **baseline 허브**: 여러 저장소에 걸친 행동(directive 발행 · 통합 · 세션 교체)과 VERIFY 실패의 승격을 맡는다.
  사람에게는 Guard 가 high 로 막은 것만, 원인과 함께 간다.
- 같은 규칙표(rule/1)와 행동 명세(action-spec/1)를 양쪽이 공유한다 → 어느 쪽이 처리해도 결과가 같다.

## 4. 단계

1. **CMD-GA56** (진행 중): O1.
2. **CMD-GA57 ops 고리 핵심**: `ga ops tick` — rule/1 표 · action-spec/1 운영 행동 · rlo Guard(shadow → enforce) ·
   VERIFY 창 · alert/1. 첫 규칙: O1 · O2 · O7 · O4. 노드에서 hub tick 뒤에 같이 돈다. (Opus 설계 + Sonnet 구현)
3. **baseline 쪽**: 매시 루틴이 같은 규칙표를 읽고 O3 · O5 · O6 · O8 을 코드로 처리(ops/hub/rules.json + 작은 스크립트).
4. stage 3(허브가 VM 에서 판정 · 통합)과 합치면 O10 도 사람 관문이 "상시 승인" 하나로 준다.

### 4.3 O6 세션 계보
이 허브는 깊이 7, 한도 8. 여기서 만든 허브는 깊이 8 이 되어 작업자를 더 만들 수 없다. 이음매 후보:
(a) 사용자가 claude.ai 에서 새 허브 세션 하나를 직접 연다(1회, 깊이 0) — 확실함.
(b) create_new_session_on_fire 루틴으로 새 허브를 연다 — 지금까지 fresh 세션에는 claude-code-remote 도구가 없었다
    (10-06 15:49 실패). 재확인 필요.
다음 인계 전에 (b) 를 시험하고, 안 되면 (a) 를 사용자에게 한 번 요청한다.

## 5. 토큰 고리 (사용자 10-06 20:5x — 모든 자동화의 최우선 원칙)

1. **호출 최소:** 규칙으로 되면 모델 0회. 모델이 필요하면 그 tick 의 모든 건을 모은다.
2. **묶음 1회 호출:** 병렬로 생긴 건(여러 이상 · 여러 보고 · 여러 판정)은 하나의 고정 프롬프트 틀 + 항목 목록으로
   한 번에 보낸다. 답도 항목 id 별 한 줄. 틀이 고정이라 앞부분은 캐시를 탄다.
3. **매 호출 측정:** input · output · cache_read · cache_write · 항목 수 · 항목당 토큰 · rung 을 원장(ledger)에 남긴다.
4. **평가 → 재최적화:** 측정 뒤 코드가 평가한다 — 항목당 토큰이 기준보다 크면 (a) 증거 카드 축소 (b) 더 싼 rung
   (c) 묶음 크기 증가 (d) 반복되는 결정은 규칙으로 승격(모델 제거). 바꾼 뒤 다시 재고, 나빠지면 되돌린다.
5. 이 고리 자체도 rlo 의 VERIFY 로 닫는다: "최적화 뒤 항목당 토큰이 줄었다"가 사후조건.
