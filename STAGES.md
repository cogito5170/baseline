# STAGES — 단계 마감 기록

각 단계가 끝날 때 네 저장소 통합 브랜치(`claude/gracious-meitner-vp49xe`)의 머리를 여기 고정한다.
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

### 태그를 달려면 (사용자 컴퓨터에서)

```
gh api repos/cogito5170/Telemetry/git/refs -f ref=refs/tags/stage-1 -f sha=70b4febc47a809cb7aeeeb1e77b9e0f414efc362
gh api repos/cogito5170/Sensor/git/refs    -f ref=refs/tags/stage-1 -f sha=10bb7addfb1605d312c5615df75765a22a980d2f
gh api repos/cogito5170/MS/git/refs        -f ref=refs/tags/stage-1 -f sha=0fc211dfe13b720fbb80541c1c50fda4e986acf4
gh api repos/cogito5170/DC/git/refs        -f ref=refs/tags/stage-1 -f sha=1387318353f4a827e7b0012bb9b2735c4c99ec55
```
