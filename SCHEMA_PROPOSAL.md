# SCHEMA PROPOSAL — 의미 칸 · 소유 · 생애 · 최소성 (인코딩은 정하지 않는다)

(baseline-1.0, 승인 2026-10-02 — 파일 이름은 그대로 둔다) **이 문서는 직렬화 형식을 고르지 않는다.** 순서: 의미 → 의존 → 생애 → 접근 → 맥락 선택 → (그다음에야) 인코딩.

표의 약어: **R/O** 필수(Required) / 선택(Optional) · **Der** 파생 가능? (예면 무엇에서) · **Mut** 바뀜(I 불변 · A 덧붙이기 · M 소유자만 바꿈) ·
**Life** 생애 · **Fresh** 신선도 요구 · **Prov** 출처 · **Conf** 신뢰도 · **Cost** 크기 · 비용.

## 1. 원칙

1. 칸마다 **소유자는 하나**다. 소유자가 없는 칸은 두지 않는다.
2. 파생할 수 있는 칸은 정준 기록에 두지 않는다. 읽을 때 계산한다(투영). 다만 **해시가 덮는 칸은 정준 칸뿐**이다.
3. 위층은 아래층의 값을 **참조**한다. 복사하지 않는다(Evidence 는 id).
4. 시각은 모두 ms + `time_base`. '지금' 은 Runtime 이 준다.
5. "모름" 은 칸이 비어 있는 것이 아니라 `status=UNKNOWN` 이다. null 의 뜻은 둘로 가른다: 보고된 null · 못 봄.

## 2. 객체별 칸

### 2.1 Observation (OBSERVE) — 소유: 수집기 · 쓰는 곳: Observation Log

| 칸 | 뜻 | R/O | Der | Mut | Life | Prov · Conf | Cost |
|---|---|---|---|---|---|---|---|
| `obs_id` | `<record_id>#<field>` | R | 아니오 | I | 보존 기간 | — | 작음 |
| `entity_id` | 관측이 **주장하는** 실체 | R | 아니오 | I | | | |
| `field` | 정준 필드 이름 (§5) | R | 아니오 | I | | | 사전으로 압축 가능 |
| `value` | 스칼라 | R (null 가능) | 아니오 | I | | | |
| `reported_null` | 원천이 null 로 보고했나 | R | 아니오 | I | | | 1 bit |
| `observed_at` · `time_base` | 시각 · 기준 | O (없으면 UNTIMED) | 아니오 | I | | | |
| `source` · `collector_version` | 원천 · 수집기 판본 | R | 아니오 | I | | Prov | |
| `basis` | OBSERVED · ESTIMATE · PROVIDER_DECLARED · EXTERNAL_LABEL | R | 아니오 | I | | Conf (종류) | |

`unobserved` 는 Observation 이 아니라 **Telemetry 레코드의 칸**이다(그 레코드에서 못 본 칸 목록).

### 2.2 Telemetry 레코드 (OBSERVE 전송) — 소유: 수집기

| 칸 | R/O | 비고 |
|---|---|---|
| `schema` (꼴 판본) · `kind` (model_call · tool_call · run · **action_outcome**(새) · **self**(자율 부품의 자기 관측, 새)) | R | MS RunRecord 는 `self` 의 한 사례다 |
| `record_id` | R | 멱등 열쇠 |
| `run_id` · `session_id` · `source` | R | |
| 관측 칸들 | R (모든 칸이 늘 있다, Sensor v2 규약) | |
| `unobserved` · `reported_null` | R | null 인 칸은 둘 중 정확히 한 목록에 |
| `decision_ref` | O | 결정 **내용**은 싣지 않는다 (BV-04) |
| `extensions.<provider>` | O | 공급자 고유 값. 상태로 펴지 않는다(MS 원칙 10) |

### 2.3 Measurement (MEASURE) — 소유: MEASURE · Measurement Ledger

`metric_id` · `entity_id` · `name` · `value` · `status`(DERIVED · UNKNOWN · INVALID) · `basis` · `inputs`(obs/metric id = `derived_from`) ·
`definition_version` · `computed_at` · `reason`(사람용). **Der: 예** — Observation Log + 정의 판본에서 언제든 다시 짓는다 → 영속은 선택.

### 2.4 State (ESTIMATE · ASSESS) — 소유: 그 상태 이름의 규칙 하나 · State Store

| 칸 | 뜻 | R/O | Der | Mut | Fresh | 비고 |
|---|---|---|---|---|---|---|
| `entity_id` · `name` | 열쇠 | R | 아니오 | I | | |
| `value` | 값 집합 안의 범주 값 | R (UNKNOWN 이면 null) | — | M | | |
| `status` | §SEMANTIC 3 | R | 아니오 | M | | |
| `basis` | 근거 종류 | R | Model 의 규칙에서 | I (규칙 판본마다) | | |
| `rule_id` · `rule_version` · `config_version` | | R | 아니오 | M | | |
| `evidence` | Measurement/State id 목록 | R (usable 이면) | 아니오 | M | | 참조만 |
| `observed_at` | **값을 정한 근거**의 관측 시각(BD-57) — 값을 정하지 않은 근거의 새 시각으로 신선해지지 않는다 | O | 근거에서 | M | TTL 의 기준 | MS 는 입력 중 **가장 이른** 시각을 쓴다(설정 포함) → BV-03 과 함께 고친다 |
| `since` · `updated_at` · `seq` | 전이 시각 · 계산 시각 · 횟수 | R | 아니오 | M | | |
| `permanent` | 끝난 일의 사실 | R | 아니오 | M (한 번만 참) | 낡지 않음 | |
| `confidence` | `{kind: none · ordinal · calibrated, value}` | O | — | M | | **새 칸 제안** — Q 같은 점수에만 (BD-36) |
| `reason` | 사람용 한 줄 | O | — | M | | DC 에는 싣지 않는다 (§4.2) |

TTL 은 State 의 칸이 아니다 — Model(운영자 가정)에 있다. STALE 은 저장하지 않고 질의 때 판정한다(Sensor 규약).

### 2.5 Evidence (출처 연결) · Relationship

- Evidence: `ref` · `level`(OBSERVATION · METRIC · STATE) · `name` · (`observed_at`). 값은 싣지 않는다(지금 Sensor `Evidence.value` 는 값을 복사한다 → 빼는 것이 PC-09).
- Relationship: `subject` · `predicate`(SEMANTIC §4 채택 목록만) · `object` · `valid_from` · `valid_to | last_seen` · `basis` · `evidence`. 소유: ESTIMATE(관측) 또는 Runtime(선언) — BD-27.

### 2.6 행동 계열 (DECIDE–VERIFY) — 지금 없는 꼴. 제안만

| 객체 | 소유 | 칸 (요지) | Mut | 영속 |
|---|---|---|---|---|
| ActionIntent | DECIDE | `intent_id` · `dc_id` · `policy@ver` · `action`(ActionSpec 이름) · `target` · `args` · `rationale` · `used_keys` · `author_kind`(rule · llm · human) | I | 원장 |
| ValidationResult | VALIDATE | `intent_id` · `ok` · `rule` · `reasons` | I | 원장 |
| ArbitrationResult | ARBITRATE | `candidates` · `selected` · `rule@ver` · `reasons` | I | 원장 |
| GuardResult | GUARD | `intent_id` · `verdict`(ALLOW · DENY · SAFE_ACTION) · `mode`(shadow · enforce) · `rule` · `state_refs`(본 **지금** 상태) · `reasons` | I | 원장 |
| ActionCommand | GUARD → EXECUTE | `command_id` · `intent_id` · `action` · `target` · `args` · `issued_at` · `deadline` | I | 원장 |
| ActionOutcome | EXECUTE | Telemetry `kind=action_outcome`: `command_id` · `result` 관측 칸들 · `error` | I | Observation Log |
| Verification | VERIFY | State `action_state` on 실체 `action:<command_id>` · 값 VERIFIED · NOT_VERIFIED · PENDING · UNKNOWN · 근거 = 사후조건이 본 State id | M | State Store |
| DecisionRecord | 각 단계가 자기 절 | `dc_id` · intent[] · validation[] · arbitration · guard · command · outcome_ref · verification_ref | A | **영속** |

## 3. 소유 요약 — "Data" 승인 물음

| 객체 | producer | owner | consumer | mutability | lifetime | freshness | persistence | derivation | source |
|---|---|---|---|---|---|---|---|---|---|
| Observation | 수집기 | Observation Log | MEASURE · 감사 | I | 보존 정책 | 시각 그대로 | **영속 · 원본** | 없음 (raw) | 원천 |
| Measurement | MEASURE | Measurement Ledger | ESTIMATE · ASSESS | A | 실행 | 입력을 따름 | 선택 | Obs + 정의 판본 | 관측 |
| State | ESTIMATE/ASSESS 규칙 | State Store | CONTEXTUALIZE · GUARD · VERIFY | M (소유 규칙) · 이력 A | 실행/세션 · permanent | TTL (Model) | 스냅숏 선택 | 재생으로 다시 짓기 | Measurement |
| Relationship | ESTIMATE · Runtime | Relationship Store | CONTEXTUALIZE · ASSESS | A + 구간 닫기 | 유효 구간 | last_seen | 선택 | 관측분은 재생 | 관측 · 선언 |
| Model 정의 | 사람 | Registry | 모두 | 판본마다 I | 배치 | — | **영속** | — | 사람 |
| DecisionContext | CONTEXTUALIZE | DC Store | DECIDE–GUARD · 원장 | I | 원장 보존 | as_of 고정 | 원장과 함께 | State 이력 + as_of | State |
| Decision 계열 | DECIDE–VERIFY | Ledger | 재현 · 감사 | A | 원장 보존 | — | **영속** | 아니오 | — |
| Cache | 그 단계 | 그 단계 | 그 단계 | 버림 | 아무 때나 | — | 아니오 | 예 | — |

**영속하는 것:** Observation · Model · Ledger. **만료하는 것:** State(TTL → STALE, 값은 남는다) · 캐시. **보내는 것:** Observation(텔레메트리) ·
DC core · 결정 계열. **다시 짓는 것:** Measurement · State(재생) · DC 의 파생 칸 · 근거 사슬(explain).

## 4. Decision Context — 정의와 최소성

### 4.1 꼴: core 와 provenance 로 가른다 (BD-08, PC-07)

```
DecisionContext
  core          ← Policy 가 읽는 것. 보낸다
    id, digest            내용 해시 (core + provenance 전부를 덮는다)
    purpose@version
    as_of                 {source: now_ms}
    subject               {role: entity | entities}
    states                {key: [value_or_null, status]}      value 는 usable 일 때만, 아니면 null
    constraints           [(name, op, value, source)]
    actions               [available action names]
  provenance    ← 감사 · 재현 · explain. 같은 저장소에 두고 id 로 가리킨다. 보통은 보내지 않는다
    per state: basis, rule_id@ver, evidence_refs, observed_at, source_status, issues, permanent
    capabilities (입력 기록), missing capability per action
    builder version, source versions
  (투영 — 저장하지 않는다)
    age_ms = as_of − observed_at · freshness · required · validity.{usable, uncertain, not_applicable, missing_required, complete}
```

### 4.2 칸마다 아홉 물음

물음: ① 왜 필요한가 ② 어느 정책이 쓰나 ③ 없으면 어떻게 되나 ④ 다른 칸에서 파생되나 ⑤ 더 작은 꼴이 되나 ⑥ 신선도 요구 ⑦ 신뢰도 요구
⑧ 캐시할 수 있나 ⑨ 계속 보내지 않고 사건으로 보낼 수 있나. → **판정**.

| 칸 | ① | ② | ③ | ④ | ⑤ | ⑥ | ⑦ | ⑧ | ⑨ | 판정 |
|---|---|---|---|---|---|---|---|---|---|---|
| `purpose@version` | 어느 명세로 지었나 | 모두 | 해석 불가 | 아니오 | 목적 id (정수 사전) | — | — | 예 | — | **core** |
| `id` · `digest` | 결정과 묶기 · 변조 탐지 | 원장 · 재현 | 재현 불가 | digest 는 내용에서 | id = digest 앞 16 자 → **둘 중 하나** | — | — | 예 | — | core (digest 하나만 저장, id 는 투영) |
| `as_of` | 신선도의 기준 · 재현 | Guard | 나이 판정 불가 | 아니오 | 소스마다 하나 | — | — | — | — | core |
| `subject` | 역할 → 실체 | 행동 대상 · Guard | 대상 모름 | 요청에서 | — | — | — | — | 요청마다 | core |
| state `value` (usable 일 때) | 결정의 입력 | 모두 | 모름 → 기본 결정 | 아니오 | 범주 값 → 정수 사전 가능 | 목적 max_age · TTL | basis 가 목적 허용 목록 안 | digest 단위로 | **예** — 값 · 유효성이 바뀔 때만 | **core** |
| state `status` | usable/모름/낡음 구분 | 모두 (UNKNOWN 과 STALE 을 다르게 다룰 수 있어야) | 모름의 종류를 잃는다 | 일부 | 3 bit | — | — | 예 | 예 | **core** |
| state `value` (쓸 수 없을 때) | 설명 | 없음 | 없음 | — | — | — | — | — | — | **provenance** (지금은 core 에 있다 — DC `StateView.value`) |
| `freshness` | | 없음 | 없음 | **예**: age · ttl · permanent 에서 | — | | | | | 투영 (`permanent` 만 provenance 에) |
| `age_ms` | | Guard 가 쓸 수 있다 | 없음 | **예**: as_of − observed_at | | | | | | 투영 |
| `ttl_ms` | 적용 TTL 기록 | 없음 | 없음 | 원칙상 Model 판본 + 목적 판본에서 — 그러나 DC 는 소스의 Model 을 다시 읽지 않는다 | | | | | | **provenance(입력 기록)** — BD-61 |
| `required` | complete 계산 | 없음 | 없음 | **예**: 목적 명세 | | | | | | 투영 |
| `basis` · `rule_id@ver` | 권위 검사 · 재현 | Validate(빌드 때) | 권위 검사 불가 | 아니오 | 판본 사전 | | ESTIMATE 거절 | 예 | 규칙 판본이 바뀔 때만 | provenance |
| `evidence_refs` | 되짚기 (I5) | 없음 (감사) | 되짚을 수 없음 | 아니오 | id 만. 사슬 전체를 복사하지 않는다 | | | 예 | | provenance |
| `reason` | 사람용 | **없음** (정책은 해석하지 않는다 — DC 문서) | 없음 | explain 에서 다시 만든다 | — | | | | | **뺀다** — 원 수치가 새어 든다(I1) · 크기가 core 보다 크다(§4.4) |
| `issues` · `source_status` | 왜 강등됐나 | 없음 | 감사 불가 | 아니오 | 코드만 | | | | | provenance |
| `constraints` | 넘으면 안 되는 선 | 정책(범위 안에서 고르기) · **Guard(평가)** | 선을 모름 | 아니오 (요청 입력) | — | 요청마다 | — | 요청 단위 | 요청마다 | core |
| `capabilities` | 가능 행동의 입력 | 없음 (actions 로 이미 반영) | — | — | — | | | | | provenance |
| `actions` (가능) | 고를 수 있는 것 | 모두 | 고를 수 없음 | **예**: 목적 명세 × 능력 | 이름만 | — | — | 능력이 같으면 같다 | 능력이 바뀔 때만 | core (이름만) · `missing` 은 provenance |
| `validity.*` | 요약 | 정책 · Guard 가 complete 를 본다 | — | **예**: states + 목적 명세 | | | | | | 투영 |
| `provenance.builder/purpose/source versions` | 재현 | 재현 | 재현 불가 | 아니오 | 판본 문자열 | | | | | provenance |

**빼는 것은 의미가 아니라 중복이다.** 위 판정으로 빠지는 칸은 모두 (a) 파생되거나 (b) 정책이 읽지 않는다. 의미상 필요한 칸
(값 · 유효성 · 제약 · 가능 행동 · 근거 참조)은 core 나 provenance 어딘가에 **반드시 한 번** 남는다.

### 4.3 보내는 것과 다시 짓는 것

- **보낸다:** core (정책 · Guard 쪽으로). 결정 기록에는 `dc digest` 만.
- **같은 저장소에 두고 가리킨다:** provenance.
- **다시 짓는다:** 투영 칸 전부. explain(사슬 전체)은 State 이력 + Evidence 에서.
- **같은 digest 면 다시 쓴다:** 가리키는 키들의 (값, 유효성)이 그대로이고 as_of 만 바뀌면? → as_of 가 digest 에 들어가므로 digest 가 달라진다.
  결정 재사용 열쇠는 **as_of 를 뺀 core** 의 해시로 따로 둔다 (BD-37).

### 4.4 잰 것 (2026-10-02, 이 세션 · 스크래치패드에서만 · 저장소 무변경)

DC 저장소 빌더로 Sensor §40 시연 상태 + MS 세션 상태(표본 3)에서 목적 넷을 지었다. 바이트 = 정준 JSON(UTF-8, 구분자 압축).

| 목적 | 상태 수 | DC 전체 | 정책이 읽는 core | 비율 | `reason` 합 | `evidence_refs` 합 |
|---|---|---|---|---|---|---|
| context_policy | 7 | 5,634 | 549 | 9.7 % | 457 | 286 |
| prompt_policy | 7 | 5,144 | 521 | 10.1 % | 446 | 164 |
| provider_selection | 5 | 4,401 | 455 | 10.3 % | 417 | 280 |
| execution_control | 10 | 7,205 | 779 | 10.8 % | 625 | 725 |

같은 상태에서: Sensor `decision/context` 의 explain 사슬(문맥마다 복사)은 6,122 · 11,242 · 18,215 · 22,243 바이트다(목적 넷). Sensor
`engine.decision_context()` 는 1,436 바이트다. MS `snapshot()` 은 236 바이트지만 유효성 · 신선도 · 근거가 없다.

읽는 법: **정책이 읽는 것은 DC 의 약 10 % 다.** `reason` 문자열만으로 core 와 거의 같은 크기다. 근거 사슬을 문맥마다 복사하면 DC 보다
몇 배 크다. 그래서 최적화의 첫 수는 인코딩이 아니라 **core/provenance 분리 · reason 빼기 · 사슬은 참조로**다. 이 수치는 시연 입력 하나에서 잰 것이다.
분포가 아니다.

## 5. 텔레메트리 이름 대응 — 초안 (Sensor 세션의 요청에 대한 답)

**먼저 고칠 함정.** 같은 잎 이름 `input_tokens` 가 **뜻이 다르다.**

| 이름 | 어디 | 뜻 | 근거 |
|---|---|---|---|
| `model_call.input_tokens` → 정준 `tokens.input_uncached` | Sensor v3 | Anthropic 식: **캐시 제외** | `Sensor/llmsensor/state/normalize.py` CANONICAL · `SENSOR_LAYER.md` Q8 |
| `tokens.input_tokens` | MS RunRecord | OTel GenAI 식: **캐시 읽기 포함 전체**, 실행 안의 호출 합 | `MS/ms/run_telemetry.py` 머리말 · MS README "Provider" 표 |

그래서 대응은 **이름이 아니라 뜻으로** 한다. 아래는 지금 두 저장소에 실제로 있는 칸만 대 본 것이다. 새 이름을 하나 더 만들지 않는다.
정준 이름 후보는 Sensor 의 것이다. 관측 어휘가 가장 넓고(후보 71 · 레코드 셋), null 의 두 뜻을 이미 가른다.

| 뜻 | Sensor 정준 (v3) | MS RunRecord (ms-run-telemetry-2) | OTel GenAI | 변환 |
|---|---|---|---|---|
| 캐시 제외 입력 (호출) | `tokens.input_uncached` | — (`input_tokens − cached_input_tokens`, 합으로만) | — | MS 는 실행 합만 있다 → 호출 단위로는 대응 없음 |
| 캐시 읽기 | `tokens.cache_read` | `tokens.cached_input_tokens` (실행 합) | `gen_ai.usage.cache_read.input_tokens`(확인 안 함) | 합 ↔ 합 |
| 캐시 쓰기 | `tokens.cache_write` (+ 5m/1h) | `extensions.claude` 에만 | — | MS 는 상태로 펴지 않는다 |
| 전체 입력 (캐시 포함) | 파생 `context_tokens` = uncached + read + write | `tokens.input_tokens` | `gen_ai.usage.input_tokens` | MS 는 캐시 **쓰기**도 더한다(Claude 어댑터 `input + cache_read + cache_creation`) → Sensor `context_tokens` 와 같은 정의. 확인할 것 |
| 출력 (생각 포함) | `tokens.output` | `tokens.output_tokens` | `gen_ai.usage.output_tokens` | 같음 (Gemini 는 어댑터가 생각을 더한다) |
| 생각 토큰 | `tokens.reasoning` | `extensions.*` | — | |
| 맥락 몫 | — | `tokens.context_tokens` (**추정**: 입력 × 글자 비율) | — | **이름이 Sensor 의 `context_tokens` 와 같고 뜻이 다르다** → MS 쪽을 `context_share_tokens_est` 로 |
| 실행 지연 | 지표 `end_to_end_latency` · `run.run_duration_ms` | `latency.total_ms` (요청 하나의 벽시계) | — | 범위가 다르다(실행 대 요청) |
| 첫 조각 | `first_chunk_ms` · `run.ttft_ms` | `latency.ttft_ms` | `gen_ai.server.time_to_first_token` | |
| 비용 | `run.cost_usd` (보고) · 지표 `cost_estimate` (단가표) | `cost.usd` + `cost.source`(provider · price_table) | — | MS 는 출처를 칸으로 가진다 → 정준 Observation 의 `basis` 로 |
| API 오류 | `runtime.api_error_status` | — | `error.type` | |
| 요금 한도 | `runtime.rate_limit_utilization` · `rate_limit_status` · `rate_limit_threshold` | — | — | 실체는 **계정** (BD-32) |
| 도구 실패 | `tool.is_error` · `timed_out` · `interrupted` | `outcome.tool_success` (실행 합) | — | 단위가 다르다 |
| 정책 실행기 자기 관측 | — | `interaction.llm_calls` · `retries` · `arbiter_denies` · `proposal_invalid` · `context_retrievals` · `non_progress_rounds` | — | **Sensor 에 없다** → 정준 꼴 `kind=self` 로 새로 (이름은 MS 것을 그대로) |
| 사람 고침 | — | `outcome.user_correction` | — | `kind=self`, source=user |
| 과업 성공 | `quality_state` 의 외부 라벨 | `outcome.task_success` (평가가 채움) | — | 둘 다 EXTERNAL_LABEL |
| 예산 | (설정 `cost_budget_usd`) | `config.token_budget` 등 (신호로 들어옴) | — | **관측이 아니다** → 대응표에서 뺀다 (BV-03) |

정준 이름 집합의 집은 **Telemetry 저장소**로 정했다(BD-28). 그 저장소는 이미 섰고(`jolly-einstein`), Sensor v3 로 되짓는 `compat` 을 갖는다. 이 표는 그 저장소의 이름과 MS RunRecord 를 맞대는 **초안**이다. Sensor 쪽에서 대응표를 만든다면 이 표의 열을
그대로 쓰고, "변환" 열의 "확인할 것" 을 녹음 응답으로 확인하는 시험을 붙이는 것이 첫 일이다.

## 6. 자료 구조 최적화 전략 (인코딩은 마지막)

| 단계 | 할 일 | 이 저장소들에서의 구체 |
|---|---|---|
| 1 의미 | 객체마다 뜻 하나 | DUP-01–13 정리 |
| 2 의존 | 무엇이 무엇에서 나오나 | `derived_from` · `depends_on` 그래프 (Sensor `Registry.graph()` 를 기준으로) |
| 3 생애 | 일시 · 영속 | §3 표 |
| 4 접근 | 누가 얼마나 자주 읽나 | 정책: DC core 만, 결정마다. 감사: provenance, 드물게. Guard: 지금 상태 몇 개, 배차마다 |
| 5 맥락 선택 | 다음 부품에 실제로 무엇을 보내나 | §4 — core 만 보낸다 (전체의 ~10 %) |
| 6 인코딩 | 위가 굳은 뒤에만 | 아래 기준으로 평가한다. **지금 고르지 않는다** |

인코딩 평가 기준 (OQ-19):

| 기준 | 왜 | 메모 |
|---|---|---|
| 해시용 정준화 | DC id 는 내용 해시다. 같은 내용 → 같은 바이트여야 한다 | 지금 정준화 규칙이 둘이다(DUP-09). 전송 형식과 해시용 정준 형식은 **따로 둘 수 있다** |
| 꼴 진화 | 판본을 올려 칸을 더한다(Sensor v2 → v3 는 덧붙이기만) | |
| 의존성 0 규칙 | 세 저장소 모두 "표준 라이브러리만" | JSON 말고는 CBOR · MessagePack · Protobuf 모두 의존성이 생긴다. 이 규칙을 지킬지가 먼저다 |
| 사람이 읽기 | 감사 · 디버깅 | |
| 크기 | 범주 값 사전 · id 사전 | §4.4: 인코딩 전에 중복을 빼는 것이 이득이 더 크다 |
| 공유 메모리 | 같은 프로세스 안의 부품 사이 | 지금은 모두 한 프로세스다 — 직렬화가 필요 없는 경로가 많다 |

## 7. 크기 · 비용 메모

- 범주 값 · 유효성 · 근거 종류 · 규칙 id 는 닫힌 집합이다 → 사전(정수)으로 줄 수 있다. 이것은 인코딩 단계의 일이다.
- Evidence 사슬은 상태 수 × 지표 수 × 관측 수로 자란다(Sensor explain 6–22 KB). **참조로만** 둔다.
- 결정 원장은 영속이고 결정마다 자란다. DC 는 core digest 로 가리키고 provenance 는 한 번만 저장한다.
