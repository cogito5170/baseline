# GA_RLO — ga-SDK 와 rlo-SDK 를 한 입구로 (ga_rlo-1 rev 1, 2026-10-03)

> 사용자 결정(BD-164)에 따른 명세다. 소유자는 baseline 이다.
> 무엇을 **해야 하는지**만 정한다. 어떻게 지을지는 짓는 세션(GR)이 정한다(GUIDANCE 13).
> 근거: ga-SDK METHOD rev 15(§4c 1–7), rlo-SDK 0.5.0(stage-8), 실사용 검증(BD-145–148), AMP 권한 막힘(BD-154 · 160 · 161 · 163).

## 0. 한 줄과 원칙

**ga 가 일을 굴리고 기록 · 판정한다. rlo 가 그 안의 모형 턴을 지킨다. 둘을 한 번에 설치하고 한 번에 설정한다.**

- **P1 결합층이다(사용자 결정).** ga_rlo 는 두 SDK 를 고정된 판으로 **의존**하고, 둘을 잇는 코드만 가진다. 두 SDK 의 코드를 복사하지 않는다.
- **P2 고칠 곳은 주인에게.** 잇는 데 ga 나 rlo 의 변경이 필요하면 ga_rlo 안에서 우회하지 않는다. baseline 에 `요청:` 으로 올린다. ga-SDK 는 GA, rlo-SDK 는 SDK 세션이 고친다.
- **P3 닫는 쪽으로만.** ga_rlo 는 허가를 넓히지 않는다. 가드는 `allow` 를 내지 않고, 막거나 손대지 않는다. 허락 기록(`ga permit`)은 사람이 남긴다(METHOD §4c 5).
- **P4 감시 대상은 모형 턴이다.** 가드는 작업 턴의 전용 설정에만 건다. 사람의 설정(`~/.claude`)과 허브 세션에는 걸지 않는다(§4c 7).
- **P5 구조가 먼저다.** rlo 는 도구 단위 · 상태 단위로 판정한다. 명령 내용 · 쓰는 곳 · 네트워크는 ga 의 샌드박스 · 격리 · bash_guard 가 맡는다(BD-163). ga_rlo 는 둘 다 켜진 설정만 기본으로 낸다.

## 1. 층

```
사용자 ── ga permit(허락) · 게이트 답
  │
ga 허브 ── 지시 · 통합 · 재현 · 판정 · 기록 (ga-SDK)
  │  Runner(헤드리스 · Agent SDK) + 샌드박스 + clone 격리
  ▼
작업 턴 ── 도구 호출마다: ga bash_guard → rlo.hooks(Guard, enforce)   (rlo-SDK)
  │                         Telemetry → Sensor → DC → Guard
  ▼
rlo 판정 기록 ──► ga 턴 증거(diag) · 회차 근거 note      ← ga_rlo 가 잇는 곳
```

## 2. 1 단계(P1)에서 지을 것

| # | 이름 | 하는 일 |
|---|---|---|
| G1 | 가드 프리셋 | rlo 행동 모형(`cc_tools_model.json` 에서 시작)과 grant 로 ga 설정의 `runner.guards` 항목(rlo.hooks 명령 · 모드 · 기록 경로)을 만든다. 작업 턴 기본값: enforce, grant 는 Bash 하나, 모형에 없는 도구(Agent · WebFetch …)는 A1 로 막힘(BD-163) |
| G2 | 증거 다리 | rlo 판정 기록(JSONL)과 Sensor 상태(실행 건강 · 정체 · 자원)를 턴마다 **수와 라벨로** 줄여 ga 의 턴 증거에 싣는다. 원문 · 비밀값은 싣지 않는다 |
| G3 | `ga-rlo init` | ga 설정(Runner · 샌드박스 require · 가드 · Judge · 예산)과 rlo 모형 파일을 한 번에 쓴다. `ga permit` 명령은 **출력만** 하고 실행하지 않는다 |
| G4 | `ga-rlo doctor` | 실행 전 점검. 두 SDK 의 판이 고정과 같은가, 모형이 `action-model/1` 로 읽히는가, 기록된 transcript 재생에서 정상 일이 막히지 않는가, 가드 명령이 실행 가능한가, 허락 기록이 있는가, 샌드박스가 있는가. 하나라도 어긋나면 실패(닫는 쪽) |
| G5 | 한 입구 | `ga-rlo` 명령 하나로 `ga` 와 `rlo.hooks` 의 하위 명령을 그대로 넘긴다 |
| G6 | 문서 | 세 환경의 빠른 시작: 로컬 CLI · 클라우드 세션 · 직접 돌리는 호스트(Agent SDK). 클라우드 세션에서는 바깥 권한 검사가 앞에 있다는 한계를 적는다 |

G1 은 ga 의 `runner.guards`(CMD-GA17)가 통합된 뒤에 끝난다. 그 전에는 G2–G6 을 먼저 짓는다.

## 3. 판 고정

- `ga-sdk @ git+https://github.com/cogito5170/ga-SDK@<sha>`: GA17 통합 머리. 그 전에는 `41a248a`.
- `rlo-sdk[sensor] @ git+https://github.com/cogito5170/rlo-SDK@a152e14bc84dc282f66bb3426a12a70934fc530d`(stage-8).
- 두 SDK 를 한 venv 에 설치했을 때 충돌이 없다(baseline 확인, 2026-10-03, `pip check` 정상).
- 판 목록은 한 곳에 두고, 시험이 `pyproject.toml` 과 같은지 본다(rlo `test_versions` 와 같은 방식).

## 4. 끝난 기준(P1)

1. 빈 venv 에 `pip install "git+…ga_rlo@<sha>"` 한 줄로 설치되고, 빈 디렉터리에서 `ga-rlo --help` · `ga-rlo doctor` 가 돈다(Bundle (b) · import_check).
2. **가짜 Runner 로 끝까지 한 바퀴:** `ga-rlo init` → 가짜 작업 턴(막힐 도구 하나가 든 transcript) → `ga tick`. 회차 기록에 rlo 의 거부 수와 라벨이 들어 있다.
3. 시험과 변이: 가드가 빠지면 · enforce 가 shadow 로 바뀌면 · grant 가 넓어지면 · 사람 설정에 가드가 들어가면 시험이 잡는다.
4. 실제 모형 호출은 하지 않는다. 실제 한 턴 확인은 사용자의 허락을 받은 뒤 따로 지시한다.

## 5. 다음 단계(사용자 결정 뒤)

| 단계 | 하는 일 | 근거 |
|---|---|---|
| P2 | 대응 단계 1–2: 막을 때 할 수 있는 길을 까닭에 싣기 · 결정적 대안표(제안만) · 되풀이 상한 → 게이트 6 | 사용자 질문(대안 ReAct) |
| P3 | 라벨(FIDES 꼴): 도구 결과의 출처 라벨 · 출구 규칙 · 제어 평면 쓰기 차단 · Runner 를 통한 에이전트 생성과 라벨 물림 | 사용자 질문(FIDES) |
| P4 | 직접 돌리는 호스트: Agent SDK 위에서 ga_rlo 가 바깥 검사 자리를 맡는다 | 사용자 질문(바깥 보안 요원) |

P2–P4 는 rlo 층(Telemetry · Sensor · Guard)을 고쳐야 하므로 SDK 세션의 일이 섞인다. 각 단계 앞에서 사용자에게 묻는다.

## 6. 하지 않는 것

- 두 SDK 의 코드를 복사하거나 고쳐 쓰지 않는다.
- 허락을 대신 만들지 않는다. 사람의 설정을 고치지 않는다.
- 바깥 실행 환경의 권한 검사를 피하는 길을 만들지 않는다.
- 비밀값 · 원문 대화를 기록하지 않는다.
