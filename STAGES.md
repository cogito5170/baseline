# STAGES — 단계 마감 기록

각 단계가 끝날 때 저장소들의 통합 브랜치(`claude/gracious-meitner-vp49xe`)의 머리를 여기 고정한다.
태그는 이 세션이 밀 수 없어(GitHub 403 — 세션은 지정 브랜치만 밀 수 있다) **바뀌지 않는 커밋 sha 로** 적는다.
사용자가 원하면 아래 sha 에 같은 이름의 태그를 달 수 있다(명령은 맨 아래).

## stage-1 — 2026-10-02 (통합 33 회차, 사용자 결정)

| 저장소 | 커밋 | 시험 |
|---|---|---|
| Telemetry | `70b4febc47a809cb7aeeeb1e77b9e0f414efc362` | 65 |
| Sensor | `10bb7addfb1605d312c5615df75765a22a980d2f` | 225 |
| MS | `0fc211dfe13b720fbb80541c1c50fda4e986acf4` | 172 |
| DC | `1387318353f4a827e7b0012bb9b2735c4c99ec55` | 104 |

- 시험은 네 저장소를 옆에 두고(통합 머리) 돌렸다. 모두 초록, 건너뜀 없음.
- Sensor 의 L0 의존은 Telemetry `70b4feb` 에 고정됐다(BD-68 · BD-92). `pip install` 이 그 커밋을 받음을 확인했다(`direct_url.json` `commit_id`).
- 이 단계에서 선 것: L0 사건 · 수집기 셋(실기록 대조) · L1 팩(liveness · recovery · dependency · runtime_actions · 시간 초과 처분 · 요금 한도 창) · 상태 내보내기 계약 `/2` · DC 질의형 선택 · 안전 기본 결정(BD-76 · BD-84 · BD-88) · MS CR `cr-3` · 결정 기록 분리.
- 다음 단계로 넘어간 것: F2b 측정(사용자 결정, 실행 중) · Action · Guard · Health 저장소 · OQ-17 · OQ-19.

## stage-2 — 2026-10-02 (통합 47 회차, 사용자 결정, BD-105)

| 저장소 | 커밋 | 시험 |
|---|---|---|
| Telemetry | `d60d5915b9fc7182c2ba9a3b20b30865b4507884` | 70 |
| Sensor | `10bb7addfb1605d312c5615df75765a22a980d2f` | 225 |
| MS | `2cb7e613c67c875137a884fd1084bf3db9555c8f` | 185 |
| DC | `ce3a0bc300f61242354ad919fd4108bd948f3f91` | 105 |
| action | `443f8eb810ce3cb9677cdc9f564ff79790f9c2ec` | 25 |
| guard | `6e4ad5630996b49e9c6a5cba38423fb173b91073` | 81 |
| health | `a07d833cf21a8b280a8ba939a21691a3215feab3` | 26 |

- 시험은 일곱 저장소를 모두 옆에 두고(통합 머리) 돌렸다. 모두 초록, 건너뜀 없음. MS 는 guard 를 빼고도 185 초록. Guard 의 MS 대조 68,688 비교 다름 0.
- guard · health 의 action 의존은 `action@443f8eb` 에 고정돼 있다.
- 이 단계에서 선 것: 계약 동결 넷 — `action-contract/1`(BD-96) · `verification-record/1`(BD-101) · `guard-result/1` · `validation-result/1`(BD-102) · MS ActionIntent shadow(BD-97 · BD-100) · Guard shadow 를 MS 런타임에 배선(Arbiter 와 다름 0, BD-103 · BD-104) · Health 경계(BD-99) · F2b 판정(BD-94) · L0 실기록 고침(T12–T16).
- 다음 단계로 넘어간 것: 실행기(BD-107) · 행동 명세의 집(BD-100 보류) · MS 도구 실행의 `action.*` 전환(BD-97 Q3) · Sensor 의 `action.result` 읽기 · Health VERIFY 배선 · Guard enforce(OQ-17 값은 BD-106) · OQ-19 · Gemini 확인 사전등록.

## stage-3 — 2026-10-02 (통합 66 회차, 사용자 결정, BD-118)

| 저장소 | 커밋 | 시험 |
|---|---|---|
| Telemetry | `89d2887768a1f230860ea6323870a747fd4323ef` | 72 |
| Sensor | `a073e7741a33dcaaa81ba0227ad6fee71bde0d30` | 246 |
| MS | `74a8585f77cb999f6b4c562b6b90ce3218682ae9` | 212 |
| DC | `b55ff044c992f7ca3fb9ddeb807839be5ae8dd06` | 108 |
| action | `2f4791e5c33df6cf19d41f139d95d74e4b86b42e` | 68 |
| guard | `be871b9d89fe77badeef901caaa75edc1848f13c` | 93 |
| health | `afcff3960694f58978afec2cdde62cac9e27830f` | 36 |

- 일곱을 옆에 두고(통합 머리) 돌렸다. 모두 초록, 건너뜀 0. MS 는 guard 없이도 212 초록. guard MS 대조 68,688 비교 다름 0 · 모드 다름 0.
- 고정된 의존: Sensor → Telemetry `89d2887` · MS · guard · health → action `3995fdb`(패키지 코드는 `2f4791e` 와 같다).
- 이 단계에서 선 것: 실행기 설계(BD-108) · `action-spec/1` · `action-model/1` 동결(BD-109) · 술어 · 인자 한 벌(F1 끝) · `action.dispatch.args_sig`(T17) · Sensor S6 `action_state` · export 의 `action:` 실체(D16) · MS DC 길 실행이 실행기로(BD-113, 한 실행 한 사건) · 런타임 VERIFY(BD-115) · Guard enforce 배선(BD-116 · BD-117, 기본 shadow).
- 다음 단계로 넘어간 것: 안전 동작을 실행기 행동으로(알릴 수단이 정해질 때, BD-114) · `$run.*` 런타임 배선(소비자가 생길 때, BD-115) · 상대 비교 술어 · `outcome_ref` · OQ-19 · Gemini 확인 사전등록.

## stage-4 — 2026-10-02 (통합 88 회차, 사용자 결정, BD-128) — SDK

| 저장소 | 커밋 | 시험 |
|---|---|---|
| rlo-SDK | `d313414429ca097b02a545da92bbef9138927844` (`rlo-sdk 0.4.0`) | 62 |
| Telemetry | `6b9dd42aebdd4e2b49d9a0c7b42a6cb46b891d0b` | 75 |
| Sensor | `97961e98e6e55b87ea1bbb8483bb99269e5e3900` | 255 |
| MS | `19d850e978f83853edca3ebefdf5c362906ee44c` | 215 |
| DC | `526f2fb487934d1d5c1a930f54ea65de493f34cb` | 116 |
| action | `c27840a299c35417ecba52967dfdfe8f861a93c9` | 68 |
| guard | `be871b9d89fe77badeef901caaa75edc1848f13c` | 93 |
| health | `afcff3960694f58978afec2cdde62cac9e27830f` | 36 |

- 여덟을 옆에 두고(통합 머리) 돌렸다. 모두 초록(rlo-SDK 건너뜀 2 = 설치 메타데이터 시험, 설치 환경에서 돈다).
- **설치 한 줄**: `pip install "rlo-sdk[sensor] @ git+https://github.com/cogito5170/rlo-SDK@d313414429ca097b02a545da92bbef9138927844"` — baseline 이 빈 가상환경에서 재현: `python -m rlo.example`(shadow · enforce VERIFIED) · `python -m rlo.example_hooks` · MBA-frontend 와 함께 탐침 27/27.
- rlo-SDK 의 고정: Telemetry `35e8119` · action `3995fdb` — 위 표의 `6b9dd42` · `c27840a` 와 **패키지 코드가 같다**(탐침 · 시험 · 문서만 다름). 한 배포는 한 판으로만 들어온다(BD-121).
- 이 단계에서 선 것: SDK 설계(BD-120) · `rlo.Autonomy`(MS Runtime 감싸기, DC 길만, guard · health 필수) · Claude Code 훅(PreToolUse 에서 transcript 다시 거둠, 지금 호출 빼고 평가, 목적 `agent_tool_call`, enforce 만 deny · `"allow"` 없음, BD-122 · 123 · 124) · `install-hook / uninstall-hook` · MBA-frontend 와 나란히(BD-125) · 토큰 절약 아이디어 안 들임(BD-127).
- 다음으로 넘어간 것: 실제 Claude Code · Agent SDK 실행으로 훅 확인 · 적응 맥락 재검토 조건(BD-127) · 안전 동작 실행기 행동(BD-114) · API(OQ-19 · OQ-23) · PyPI.

## stage-5 — 2026-10-02 (통합 98 회차, 사용자 결정, BD-136) — 방법론 SDK

| 저장소 | 커밋 | 시험 |
|---|---|---|
| ga-SDK | `90aa9a54cd9065887b8804c7346646ff42542af6` (`ga` 0.1, METHOD method-1 rev 5) | 76 |
| rlo-SDK | `c6b2f95122f4828ff341b7d140579543936cc34c` (`rlo-sdk 0.4.1`) | 65 |
| Telemetry · Sensor · MS · DC · action · guard · health | stage-4 와 같다 | stage-4 와 같다 |

- ga-SDK 는 표준 라이브러리만 쓴다. Python 3.10–3.13 에서 초록이다(GA 보고). baseline 은 3.11 에서 76 OK 를 재현했고, 빈 venv 에 설치한 뒤 `python -m ga` 가 도는 것을 확인했다. R1b 를 끈 변이는 시험 2 개가 잡았다.
- METHOD §9 검증 1 은 stage-2–4 의 22 저장소×단계 시험 수가 모두 일치했다. 검증 2(엇갈림)와 검증 3(고정 충돌)도 섰다.
- rlo-SDK 0.4.1 은 stage-4 뒤 K7(실제 Claude Code 훅 확인) · K8(예시 모형에 Edit · Grep)을 더한 판이다. 시험 65 · 변이 48/48 이다.
- 이 단계에서 선 것:
  - 방법론 명세 METHOD(BD-131–135): 형식 · 고리 · 어댑터 · Runner · 규칙 hard/soft · 게이트 일곱 · 실패 사례 F1–F8 · 교신 원칙 R1/R1b
  - SESSION_GUIDANCE 원문 보관
  - PROTOCOL §1a 교신 원칙(BD-133)
  - ga 0.1 로컬판: 파일 우편함 · 수동 Runner · worktree · pre-push
- 다음으로 넘어간 것:
  - ga 2판: 헤드리스 Runner(CMD-GA2) → LLM Judge → Agent SDK → GitHub · 원격
  - 기록을 허브 저장소에 커밋하는 일
  - 로컬에서 남의 브랜치에 직접 커밋하는 것을 막는 훅
  - Bundle (b) 시험 분리
  - rlo 의 Glob 등 도구 측정

### 태그를 달려면 (사용자 컴퓨터에서)

```
gh api repos/cogito5170/Telemetry/git/refs -f ref=refs/tags/stage-1 -f sha=70b4febc47a809cb7aeeeb1e77b9e0f414efc362
gh api repos/cogito5170/Sensor/git/refs    -f ref=refs/tags/stage-1 -f sha=10bb7addfb1605d312c5615df75765a22a980d2f
gh api repos/cogito5170/MS/git/refs        -f ref=refs/tags/stage-1 -f sha=0fc211dfe13b720fbb80541c1c50fda4e986acf4
gh api repos/cogito5170/DC/git/refs        -f ref=refs/tags/stage-1 -f sha=1387318353f4a827e7b0012bb9b2735c4c99ec55

gh api repos/cogito5170/Telemetry/git/refs -f ref=refs/tags/stage-2 -f sha=d60d5915b9fc7182c2ba9a3b20b30865b4507884
gh api repos/cogito5170/Sensor/git/refs    -f ref=refs/tags/stage-2 -f sha=10bb7addfb1605d312c5615df75765a22a980d2f
gh api repos/cogito5170/MS/git/refs        -f ref=refs/tags/stage-2 -f sha=2cb7e613c67c875137a884fd1084bf3db9555c8f
gh api repos/cogito5170/DC/git/refs        -f ref=refs/tags/stage-2 -f sha=ce3a0bc300f61242354ad919fd4108bd948f3f91
gh api repos/cogito5170/action/git/refs    -f ref=refs/tags/stage-2 -f sha=443f8eb810ce3cb9677cdc9f564ff79790f9c2ec
gh api repos/cogito5170/guard/git/refs     -f ref=refs/tags/stage-2 -f sha=6e4ad5630996b49e9c6a5cba38423fb173b91073
gh api repos/cogito5170/health/git/refs    -f ref=refs/tags/stage-2 -f sha=a07d833cf21a8b280a8ba939a21691a3215feab3

gh api repos/cogito5170/Telemetry/git/refs -f ref=refs/tags/stage-3 -f sha=89d2887768a1f230860ea6323870a747fd4323ef
gh api repos/cogito5170/Sensor/git/refs    -f ref=refs/tags/stage-3 -f sha=a073e7741a33dcaaa81ba0227ad6fee71bde0d30
gh api repos/cogito5170/MS/git/refs        -f ref=refs/tags/stage-3 -f sha=74a8585f77cb999f6b4c562b6b90ce3218682ae9
gh api repos/cogito5170/DC/git/refs        -f ref=refs/tags/stage-3 -f sha=b55ff044c992f7ca3fb9ddeb807839be5ae8dd06
gh api repos/cogito5170/action/git/refs    -f ref=refs/tags/stage-3 -f sha=2f4791e5c33df6cf19d41f139d95d74e4b86b42e
gh api repos/cogito5170/guard/git/refs     -f ref=refs/tags/stage-3 -f sha=be871b9d89fe77badeef901caaa75edc1848f13c
gh api repos/cogito5170/health/git/refs    -f ref=refs/tags/stage-3 -f sha=afcff3960694f58978afec2cdde62cac9e27830f

gh api repos/cogito5170/rlo-SDK/git/refs    -f ref=refs/tags/stage-4 -f sha=d313414429ca097b02a545da92bbef9138927844
gh api repos/cogito5170/Telemetry/git/refs -f ref=refs/tags/stage-4 -f sha=6b9dd42aebdd4e2b49d9a0c7b42a6cb46b891d0b
gh api repos/cogito5170/Sensor/git/refs    -f ref=refs/tags/stage-4 -f sha=97961e98e6e55b87ea1bbb8483bb99269e5e3900
gh api repos/cogito5170/MS/git/refs        -f ref=refs/tags/stage-4 -f sha=19d850e978f83853edca3ebefdf5c362906ee44c
gh api repos/cogito5170/DC/git/refs        -f ref=refs/tags/stage-4 -f sha=526f2fb487934d1d5c1a930f54ea65de493f34cb
gh api repos/cogito5170/action/git/refs    -f ref=refs/tags/stage-4 -f sha=c27840a299c35417ecba52967dfdfe8f861a93c9
gh api repos/cogito5170/guard/git/refs     -f ref=refs/tags/stage-4 -f sha=be871b9d89fe77badeef901caaa75edc1848f13c
gh api repos/cogito5170/health/git/refs    -f ref=refs/tags/stage-4 -f sha=afcff3960694f58978afec2cdde62cac9e27830f

gh api repos/cogito5170/ga-SDK/git/refs     -f ref=refs/tags/stage-5 -f sha=90aa9a54cd9065887b8804c7346646ff42542af6
gh api repos/cogito5170/rlo-SDK/git/refs    -f ref=refs/tags/stage-5 -f sha=c6b2f95122f4828ff341b7d140579543936cc34c
```
