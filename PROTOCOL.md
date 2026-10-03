# PROTOCOL — baseline ↔ 세션 전달 규약 (baseline-1.0, 2026-10-02)

세션은 서로 직접 지시하지 않는다. **모든 요청 · 보고 · 지시는 baseline 을 거친다**(허브 하나, 바퀴살 여럿).
같은 것을 두 세션이 짓는 일(2026-10-02 liveness 가 실제로 그랬다)을 막기 위해서다.

```
   [Telemetry 세션] ─보고─┐                      ┌─지시─► [Telemetry 세션]
   [Sensor 세션]    ─보고─┤                      ├─지시─► [Sensor 세션]
   [DC 세션]        ─보고─┼──► baseline ──판단──┼─지시─► [DC 세션]
   [MS 세션]        ─보고─┘   (이 저장소 + 이 세션)  └─지시─► [MS 세션]
                                   │
                         통합: 저장소마다 claude/gracious-meitner-vp49xe
```

## 1. 통로

| 방향 | 통로 | 꼴 |
|---|---|---|
| 세션 → baseline (보고 · 질문 · 다른 세션에 대한 요청) | **cogito5170/baseline 의 이슈, 세션마다 하나.** 제목 머리 `[Telemetry]` #1 · `[MS]` #2 · `[Sensor]` #3 · `[DC]` #4 · `[Action]` #6 · `[Guard]` #7 · `[Health]` #9 · `[SDK]` #11 · `[GA]` #12 · `[AMP]` #14 · `[GR]` #15 · `[gentleMonster_gemini]` #16. 보고 하나 = 댓글 하나. **새 이슈를 열지 않는다.** 저장소 안의 보고 파일(`inbox/` 등)은 쓰지 않는다 | §2 의 보고 꼴 |
| **보고 뒤 깨우기** | 댓글을 올린 **바로 뒤** baseline 세션에 세션 메시지 한 줄: Claude Code Remote 의 `send_message`, `session_id = session_013GnrUQPpcfK4ea1a1Y6SuY`, 내용 = `[<세션>] 보고 <댓글 링크>`. baseline 은 그 메시지로 깨어나 판단 · 지시한다 | 놓치면 baseline 의 1 시간 안전망이 잡는다 |
| baseline → 세션 (판단 · 지시) | 그 세션의 이슈에 **댓글** + 세션을 깨우는 **세션 메시지**(댓글을 가리키는 한 줄) | §3 의 지시 꼴 |
| 구속력 있는 결정 | 이 저장소의 `claude/gracious-meitner-vp49xe` — DECISION_LOG(BD) · BASELINE §13 · 이 문서 | 이슈 댓글은 결정의 전달이다. 결정의 원본은 이 저장소다 |
| 세션 ↔ 세션 | **기본은 없다.** 다른 세션의 일이 필요하면 자기 이슈에 `요청: <대상 세션> …` 으로 적는다. baseline 이 소유 세션에 지시로 옮긴다. **정말 필요할 때만 교신을 허용한다(§1a).** | §1a |

MS 세션이 이 저장소의 자기 브랜치(`claude/eloquent-turing-m33zjw`, `MS/` 폴더)에 남긴 보고 파일은 그대로 기록으로 둔다. 다음 보고부터는 이슈로 한다.

## 1a. 세션 간 교신 (BD-133, 사용자 결정 2026-10-02)

**원칙.** 모든 자식 세션은 기본적으로 baseline 하나와만 통신한다.
- 세션끼리의 교신은 **정말 필요할 때만** 허용한다. 예: 상대가 소유한 interface 의 뜻을 확인할 때, 재현에 필요한 사실을 물을 때.
- **교신 자체는 action 이 아니다.** 교신으로 알게 된 것을 근거로 코드 · 계약 · 소유 파일을 바꾸지 않는다. 묻고 답하는 것까지만 한다.
- 교신은 **반드시 baseline 에 보고**한다. 그러면 baseline 이 최종 평가를 하고, 필요한 지시를 **각 세션에** 내린다. 행동은 그 지시로만 시작한다.

**보고 꼴.** 교신을 시작한 세션이 교신 직후 자기 이슈에 댓글을 쓴다. 받은 세션은 다음 보고에 한 줄을 적는다.

```
[<세션>] 교신 <상대 세션>
왜 필요했나: (baseline 을 거치면 안 되는 까닭)
물은 것 / 받은 것: (사실만)
이것으로 하고 싶은 것: (제안 — 아직 하지 않았다)
```

**통합.** 교신만을 근거로 한 커밋, 곧 어떤 지시(`CMD-…`)에도 속하지 않는 변경은 baseline 이 통합하지 않는다. 그 변경은 보고에서 Proposal 로 다룬다.

## 2. 보고 꼴 (세션 → baseline)

```
[<세션>] <한 줄>
처리한 지시: CMD-xx ✅ · CMD-yy ⏸(까닭)            ← 받은 지시마다 하나
커밋: <저장소>@<브랜치> <sha> …
시험: 몇 개 통과 · 변이 · 실데이터 대조(있으면)
확인하지 못한 것:
묻는 것 / 요청: <대상 세션> …
```

## 3. 지시 꼴 (baseline → 세션)

```
CMD-<세션 머리글자><번호>  <목표 한 줄 — 방법은 세션이 정한다>
  왜: 무엇을 개선하나 (근거: BD-xx / PC-xx / 보고의 어느 줄)
  범위 · 제약: 손대도 되는 것 · 지켜야 할 interface
  끝난 기준: 무엇이 달라지면 성공이고 어떻게 확인하나(기존 metric · 시험 우선)
  순서: 앞에 끝나야 하는 지시
```

baseline 의 확인 댓글은 결과를 **성공 · 부분 성공 · 실패 · 막힘 · 정보 부족** 으로 가르고, 계획("하겠다")과 결과("했고 측정됐다")를 섞지 않는다.
다음 interaction 은 continue · refine · verify · handoff · change direction · **wait** 중에서 고른다 — 할 일이 없으면 지시하지 않는다.
참고: [`GUIDANCE.md`](GUIDANCE.md)(사용자 제공).

머리글자: T = Telemetry · S = Sensor · D = DC · M = MS. 번호는 세션마다 1 부터.

## 4. 통합 규칙

1. 세션은 **자기 브랜치에만** 푸시한다.
2. 세션은 새 일을 시작할 때마다 **통합 브랜치를 먼저 합친다**:
   `git fetch origin claude/gracious-meitner-vp49xe && git merge origin/claude/gracious-meitner-vp49xe` (각 저장소에서).
3. baseline 은 프롬프트마다 모든 저장소 · 브랜치 · 이슈를 다시 읽는다. 세션 브랜치를 통합 브랜치로 합치고, 시험을 옆 저장소와 함께 돌리고, 결과를 §13 에 적는다.
4. PR · 기본 브랜치로의 합치기는 세션이 하지 않는다. 통합 브랜치가 단계를 마치면 baseline 이 사용자에게 묻고 한다.

## 5. 소유 — 파일 하나에 세션 하나 (BD-45)

| 저장소 · 경로 | 소유 세션 | 비고 |
|---|---|---|
| Telemetry `*` | **Telemetry** (`jolly-einstein`) | L0 사건 이름 · 꼴 · 수집기의 유일한 주인 |
| Sensor `llmsensor/telemetry/*` · `schema/*` | **Telemetry** | L0 ↔ Sensor 꼴 v3 경계(`l0.py` · compat) |
| Sensor `llmsensor/sensing/*` · `llmsensor/state/*` (아래 제외) · `sensors/*` · `verifier.py` · 그 밖 | **Sensor** (`nice-wright`) | **L1 팩 전부**(liveness · recovery · dependency · action_outcome 포함) · 규칙 · 엔진 |
| Sensor `llmsensor/state/export.py` (state-export 계약) · `tests/test_state_export.py` | **DC** (`nifty-volta`) | 그 계약을 지었고 유일한 소비자가 DC 다 (BD-56) |
| DC `*` | **DC** (`nifty-volta`) | |
| MS `ms/l0.py` · `tests/test_l0.py` | **Telemetry** | MS 안의 L0 Recorder 배선 |
| MS 그 밖 `*` | **MS** (`eloquent-turing`) | `runtime.py` 의 `state_reader` 이음매 포함 |
| action `*` | **Action** (새 세션) | 꼴 ActionIntent · ActionCommand · ActionOutcome · 실행기 (BD-25). 통로 baseline#6 |
| guard `*` | **Guard** (새 세션) | Validate · Arbitrate · Guard (BD-07 · BD-24). shadow 먼저, enforce 는 OQ-17 뒤. 통로 baseline#7 |
| health `*` | **Health** (새 세션) | ASSESS 진단 · 격리 · VERIFY (BD-22). 통로 baseline#9 |
| rlo-SDK `*` | **SDK** (새 세션) | 일곱 패키지를 조립하는 SDK 입구 · 훅 어댑터 (BD-119). 지시 머리글자 `CMD-K`. 통로 baseline#11 |
| ~~rlo-SDK 브랜치 `claude/ga-trial-k9`~~ | ~~GA~~ | 예외 끝(BD-147): `326592c` 로 통합됨. rlo-SDK 는 다시 SDK 세션 소유 |
| ga-SDK `*` (아래 제외) | **GA** (새 세션) | 허브 지시-보고 고리 SDK (BD-131). 지시 머리글자 `CMD-GA`. 통로 baseline#12 |
| ga-SDK `METHOD.md` | **baseline** | 명세. 바꿀 곳은 #12 에 `요청:` |
| amp `*` | **AMP** (`determined-gates`) | Token Amplifier 구현 · 실험. ga 허브 운영자. 지시 머리글자 `CMD-AMP`. 통로 baseline#14 (BD-150) |
| baseline `AMP.md` | **baseline** | 명세. 바꿀 곳은 #14 에 `요청:` |
| ga_rlo `*` | **GR** (세션은 사용자가 만듦) | ga-SDK · rlo-SDK 결합층. 지시 머리글자 `CMD-GR`. 통로 baseline#15 (BD-164) |
| baseline `GA_RLO.md` | **baseline** | 명세. 바꿀 곳은 #15 에 `요청:` |
| gentleMonster_gemini `*` | **GMG** (`sleepy-cori`) | ga_rlo 검증 과제의 결과물. 지시 머리글자 `CMD-GMG`. 통로 baseline#16 (BD-167). gentleMonster · well_used_gemini 는 읽기만(허브 구성 때 다시 정함) |
| baseline `*` | **baseline** (이 세션) | |

소유하지 않은 파일을 고쳐야 하면 고치지 말고 이슈에 `요청:` 으로 적는다.
