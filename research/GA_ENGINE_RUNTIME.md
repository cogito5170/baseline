# GA Engine 런타임 전환 — 원칙을 프롬프트에서 구조로 (BD-473 설계안, 10-06 21:1x KST)

사용자 지시: 원칙을 문서에 넣고 끝내지 말고, 프롬프트가 원칙을 읽지 않아도 파이프라인이 자동으로 실행되게 구조를 바꾼다.

## 1. 현재 ga-sdk 내부 구조 (claude/gracious-meitner-vp49xe f9671da, 0.18.1)

| 층 | 모듈 (줄 수) | 하는 일 |
|---|---|---|
| 입구 | `__main__` (737), ask (1120), ui (315), console (1903) | CLI · 자연어 입구 · 브라우저 UI · 운영 콘솔(API+SSE) |
| 접수 · 계획 | intake (1238), plan (808, shadow) | 자연어 → task/1, 요청 → directive/2 초안 |
| 실행 | act (1909: card · fmt · apply · commands · retrieve · route · loop), backends (1041), gemini (1215) | 작업 1건을 worktree 에서 고정 행동 형식 + 상태 카드로 수행, 모델 사다리(route) |
| 다리 | bridge (440), mailbox (298), inbox (138), wire (159), forms (960) | directive → ga supervise(agv/agy) → report/2, git 메일함, 양식 검사 |
| 판정 · 검증 | judge (744), verify (621: mutate · items), rules (291), gates (152) | 시험 실행 · 기존 실패 구분 · 변이 생성 · 규칙 R1–R13 · 사람 관문 |
| 허브 | hub (1956), records (177), prompts (215), config (302) | 받기 → 통합 → 재현 → 판정 → 기록 → 다음 선택 (shadow 모드 포함) |
| 운영 | vm (900), events (423), l0 (83), runlog (144), ctxpack (198) | systemd 서비스 · 자가 업데이트 · 이벤트 흐름 · 텔레메트리 |
| 자율 | rlo (2255, GR 소유), net (2349) | rlo Autonomy(Guard · VERIFY) · 피어 노드 런타임 |

이미 코드로 있는 것: 양식 검사, 판정(judge), 변이 생성(verify), 고정 카드 실행 루프(act), 모델 사다리(route), 메일함, 이벤트, VM 서비스, rlo Guard.

## 2. 지금의 절차: baseline → ga-sdk → agv (TKG 예)

```
[baseline 허브 = Claude 세션, 모델]
 1. 결함 발견(통합 세션에 red check 요청) → directive/2 + bridge item(json: 파일 · 시험 · 명령) 작성 → commit
 2. ga mail send --to AGY  → ga-mailbox 브랜치 to/AGY/<ts>-baseline-<id>.md
[VM = 코드]
 3. ga bridge(서비스): to/AGY 읽기 → 허브 directive 만 수락 → Token worktree(base 브랜치)
 4. ga act (agv backend = agy CLI, gemini flash; route 가 ledger 로 시작 rung 선택)
      상태 카드 → 모델이 EDIT/RUN/DONE 형식으로 답 → 코드가 적용 · 시험 실행 → done_when 통과까지(상한 · 진전 감지)
 5. agv/<id>-r<rev> 브랜치 push, report/2 → to/baseline
 6. ga hub tick --shadow (60초 타이머): ga judge + 모델 결정 1턴 → shadow 행 → to/baseline-shadow
[baseline 허브 + Token 통합 세션 = Claude 세션 2개, 모델]
 7. 허브가 보고를 읽고 통합 세션에 VERDICT 요청(ancestor · 허용 파일 · 시험 동일성 · 전체 suite · 변이 · revert)
 8. 허브가 diff 직접 검토 + 변이 추가 → ACCEPT → INTEGRATE(merge, 사용자 push 승인) → verdicts.jsonl · 게이트 재채점
ga-sdk 자체 변경(GA5x)은 agv 가 아니라 Claude 작업 세션 + ga-sdk 통합 세션이 같은 7–8 을 한다.
```

## 3. 구조적 문제 — 원칙이 프롬프트 안에 있다

1. **지휘가 모델이다.** 1 · 7 · 8 의 순서 · 우선순위 · 묶음 · 재시도는 허브 모델이 STATE.md 규칙을 읽고 따를 때만 지켜진다.
   허브 문맥이 자라고(이번 세션 250k), 인계 · 계보 깊이(O6) · 사람 요청이 생긴다.
2. **결정적인 일을 모델이 한다.** VERDICT(7)는 ancestor · diff · suite · 변이 · revert — 전부 코드로 결정되는데 Claude 세션
   두 개(허브 + 통합)가 토큰을 쓰며 한다. ga judge · ga verify 가 이미 있는데 연결이 안 됐다.
3. **모델 호출 입구가 여럿이다.** act · hub._decide · plan · intake · gemini 가 각자 backend 를 부른다. 묶음 · 측정 · rung ·
   예산을 한 곳에서 강제할 수 없다 → "토큰 고리"는 프롬프트 권고에 머문다.
4. **이벤트가 아니라 시간과 사람이 깨운다.** 60초 타이머, 매시 루틴, 사람의 push 승인.

## 4. 설계안 — 4개의 구조 변경

### A. 단일 LLM 관문 `ga.llm` (모든 모델 호출의 유일한 입구)
- act · hub decide · plan · intake · ops 가 backend 를 직접 부르지 못한다(정적 검사 시험이 `backends.create` 직접 호출을 실패로 만든다).
- 관문이 강제: **묶음 창**(같은 tick 의 요청을 모아 고정 틀 + 항목 목록 1회 호출) · **rung 선택**(ledger 의 승률 · 비용) ·
  **예산**(일 · 작업 · 항목당 토큰 상한, 넘으면 호출 거절 + alert) · **측정**(input/output/cache/항목당 → ledger) ·
  **재최적화**(카드 축소 → 싼 rung → 큰 묶음 → 반복 결정의 규칙 승격, 다음 측정이 나빠지면 되돌림) · **규칙 캐시**(같은
  증거 지문에 같은 답 N 회 → 다음부터 모델 0회).
- 원칙 1 · 4 · 5 가 프롬프트가 아니라 이 함수의 동작이 된다.

### B. 결정적 판정을 런타임으로: `ga verdict` (통합 세션 대체)
- judge(시험 · 기존 실패 구분) + verify.mutate(diff 에서 변이 자동 생성) + revert 검사 + ancestor/허용 파일/시험 동일성을
  하나의 코드 경로로. 출력 verdict/1. 모델 0회.
- 생존 변이 → 틀에 맞춘 SEND_BACK 자동 생성(O4). 판정 통과 → 정책이 허용하면 자동 통합.
- 사람 관문은 정책 파일 하나: `policy.json` 의 `auto_integrate: {repos, conditions}` 를 사용자가 한 번 승인(사람만 바꿀 수
  있는 파일, gates.py G7). 이후 매 push 승인이 사라진다(O10).

### C. 파이프라인 상태 기계 `ga devops run` (허브 모델 대체)
- 작업 1건 = 상태 기계: `PLANNED → DISPATCHED → ACTING → REPORTED → VERDICT → (SEND_BACK ↺ | INTEGRATED) → DEPLOYED → OBSERVED`.
  전이는 전부 코드, 상태는 파일(고정 크기). 메일함 · git push 이벤트로 깨어난다(systemd path unit / fetch 훅, 폴링 없음).
- **Dev 워커**(코드): 디스패치(독립 작업 병렬, files 소유 · after 의존 — net/ 재사용) · act · verdict · 통합 순서 · 버전 배정.
- **Ops 워커**(코드): GA57 ga ops tick — 관측 · rule/1 · action-spec/1 · rlo Guard · VERIFY · alert/1 · DORA/SLO 계산.
- **DevOps 스케줄러**(코드): 오류 예산이 남았으면 Dev 우선, 소진되면 Ops 안정화 우선. 우선순위 · 동시 실행 수 · 예산은
  policy.json. DevOps_baseline · Dev_baseline · Ops_baseline 은 이 세 코드 구성요소의 이름이 된다.

### D. 모델 세션은 "승격 처리기"로만
- 상태 기계가 막힐 때(사다리 꼭대기, 같은 실패 2회, 새 설계 필요)만 관문이 강한 모델을 부르고, 그래도 안 되면 Claude
  세션 하나를 고정 카드와 함께 연다(hard-task cooperate). 허브 세션이 상시로 떠 있을 필요가 없다 → 문맥 · 인계 · 계보 문제 소멸.
- baseline 저장소는 기록(directive · verdict · BD · DORA)과 정책의 집. 사람은 정책 승인 · 자격 증명 · 비용에만.

## 5. 원칙 → 구조 대응

| 원칙 | 강제하는 구조 |
|---|---|
| LLM 최소 · 토큰 최적화 · 묶음 · 측정 · 재최적화 | A 관문 (우회 금지 시험) |
| 사용자 최소 | B policy.json 1회 승인, D 승격 처리기 |
| runtime 우선 | B · C 가 VM 서비스 |
| power | 이벤트 구동(path unit · fetch 훅), 타이머 · 폴링 제거 |
| memory | 고정 크기 상태 파일 · 카드, 세션 기록 재생 없음 |
| velocity | C Dev 워커 병렬 디스패치(파일 소유 · 의존) |
| autonomy | C Ops 워커 + rlo Guard · VERIFY |
| hard-task cooperate | D 승격 사다리: 규칙 → 싼 모델 → 강한 모델 → Claude 세션 → 사람 |
| semantic 통신 | forms 검사기: notify/1 · alert/1 · verdict/1 만 통과, 산문 거절 |

## 6. 단계 (작은 배치, 각 단계가 독립 착지)

1. **R1 관문**: `ga.llm` + 우회 금지 시험 + ledger 측정 + 묶음 창. act · hub decide 를 관문으로 옮김. (GA57 S4/S6 을 여기로 흡수)
2. **R2 ga verdict**: judge + verify.mutate + revert + 동일성 → verdict/1, 생존 변이 SEND_BACK 틀. 통합 세션과 결과를 나란히
   비교(shadow) → 10건 일치하면 통합 세션 은퇴.
3. **R3 policy.json + 자동 통합**: 사용자 1회 승인. push 승인 제거.
4. **R4 ga devops run**: 상태 기계 + Dev/Ops 워커 + 스케줄러, 이벤트 구동. 허브 세션은 승격 처리기로.
5. **R5 정리**: 매시 루틴 · 감시 세션 · 통합 세션 은퇴, 상황판은 상태 파일을 그대로 표시.

진행 중인 GA52–GA57 은 그대로 착지시키고(R1 의 재료), GA57 은 R1 의 관문 위로 옮긴다.
