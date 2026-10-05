# 최종 보고 — ga-SDK: 토큰을 아끼는 분산 세션 네트워크 (POL-3)

2026-10-05 · baseline 허브 · 기준 커밋 ga-sdk `5e8ef4b` (ga 0.5.0) · 근거 기록 `DECISION_LOG.md` BD-296~333, `FINAL_TASK.md` §6

## 0. 연구 질문

- **Q1.** 여러 LLM 세션이 함께 일할 때 토큰 · 쿼터가 어디서 새는가, 그리고 도구(코드)로 막을 수 있는가?
- **Q2.** 가운데 LLM 허브가 모든 판정 · 지시를 하는 구조(A)를, 가운데를 코드로 바꾼 구조(B)나 세션끼리 직접 잇는 구조(C, "④")로 바꾸면 정답률을 잃지 않고 토큰을 줄일 수 있는가?
- **Q3.** "단 한 번의 호출이라도 프로젝트 파일을 대량으로 주입(수만~수십만 토큰)하거나 무거운 모델을 쓰면 쿼터가 크게 소모된다"는 설명은 측정으로도 맞는가? (Haiku 4.5 · Sonnet 5.5)

## 1. 연구 결과의 요약

1. **토큰의 대부분은 '다시 읽기'였다.** 오래 사는 세션은 매 호출마다 쌓인 대화 전체(25만~77만 토큰)를 다시 읽었고, 측정한 토큰의 약 98%가 캐시 재읽기였다. 해결책은 환경 변수가 아니라 도구였다: 매 턴을 새 호출로 시작하고(fresh), 필요한 것만 상한 안에서 골라 담는 문맥 꾸러미(ctxpack)를 만들었다. 같은 과제에서 비용 −53%, 호출당 최대 문맥 40k → 22k.
2. **파일을 통째로 넣는 것이 가장 비쌌다 (Q3 확인).** 같은 과제 · 같은 모델에서 저장소 파일을 통째로 넣으면(호출당 11만~13만 토큰) 필요한 것만 넣을 때보다 쿼터가 Haiku 25~47배, Sonnet 60~63배였고, 정답률은 같거나 낮았다(5/5→5/5, 4/5 vs 5/5). 즉 대량 주입은 비용만 늘리고 결과를 사지 못했다.
3. **"무거운 모델 = 늘 비쌈"은 절반만 맞았다.** 문맥이 클 때 Sonnet은 Haiku의 약 1.8~2.3배였다. 그러나 문맥이 작고 반복될 때는 Sonnet이 캐시 읽기(0.1배 가격) 덕에 맞힌 과제당 오히려 더 쌌다(5개 과제 중 4개). 모델 단가보다 문맥 크기와 캐시 적중이 쿼터를 더 크게 좌우했다.
4. **구조가 가장 큰 지렛대였다 (Q2).** 세션끼리 직접 잇는 C는 LLM 허브 A보다 맞힌 과제당 토큰이 절반 이하(Haiku 3,776 vs 8,117 · Sonnet 2,408 vs 5,833), 정답률은 같거나 높았고(15/15 vs 14/15 · 15/15), 같은 정보를 다시 넣는 횟수가 1/10(0.33 vs 3.2~3.7)이었다. 이미 State에 있는 답은 도구 · 동료 호출 0회로, 근거가 없으면 추측 대신 UNKNOWN으로 답했다(두 모델 모두 3/3).
5. **운영에서도 같은 결과가 나왔다.** "지시 하나 = 새 세션 하나"로 바꾼 뒤 작업 세션 한 개 비용이 $60~$430(장기 세션)에서 $0.4~$3.3으로 내려갔다.

**한 줄 답:** 쿼터를 가장 크게 줄이는 것은 싼 모델을 고르는 일이 아니라, 필요한 문맥만 골라 넣고 이미 아는 것을 다시 읽지 않게 하는 구조다.

## 2. 연구의 의의 및 시사점

### 학문적 시사점

- **"상호작용이 많을수록 똑똑하다"는 가정을 측정으로 대체했다.** 집단 인지 · 다중 에이전트 연구는 연결도와 메시지 수를 성과의 근거로 쓰는 경우가 많다. 이 연구는 사양(spec §15)대로 그것을 공로로 세지 않고, 맞힌 과제당 토큰 · 반복 정보 · UNKNOWN 정확도 같은 결과 지표로 비교했다. C는 메시지를 더 쓰면서도 토큰을 줄였는데, 그 까닭은 연결이 많아서가 아니라 State를 재사용하고 중복을 없앴기 때문이다.
- **메시지를 '사실'과 '의견'으로 나눈 상태 갱신 규칙을 실제로 구현해 검증했다.** 다른 세션의 메시지는 곧바로 State를 바꾸지 못하고 "j가 X를 보냈다"는 사실로 들어오며, 자신의 규칙(수용 · 모순 시 불확실 · 근거 중복 제거)만이 State를 바꾼다. 모순 과제(T3)에서 이 규칙이 근거로 확정된 값 또는 UNKNOWN을 냈다.
- **비용 측정 방법론을 보탰다.** 같은 호출을 API 정가 환산과 실행기 자체 비용으로 나란히 재 보니 약 1.9배 차이가 났다(실행기의 숨은 내부 호출). 에이전트 비용 연구는 공급자 usage 하나만 보면 과소 추정할 수 있다.

### 실무적 · 정책적 시사점

- **저장소를 통째로 프롬프트에 넣지 말 것.** 수십 배 쿼터를 쓰고 정답률은 오르지 않았다. 문맥 상한(예: 호출당 2만 토큰 이하)을 도구로 강제하는 것이 효과적이다.
- **장기 대화 세션 대신 '짧은 새 세션 + 파일로 된 상태'로 운영할 것.** 상태는 STATE.md · state.json 같은 파일에, 보고는 짧은 머리 한 줄로.
- **모델 선택은 문맥 크기와 함께 정할 것.** 큰 문맥 작업은 Haiku, 작고 반복되는 프롬프트는 Sonnet이 맞힌 과제당 쌀 수 있다. ga의 라우터는 과제 · 모델별 '맞힌 답당 토큰'을 학습해 고른다.
- **판정은 LLM이 아니라 스크립트로.** 설치 · 시험 · 변이 검사 · 기록을 `ga judge`가 결정적으로 하므로 판정 비용은 0 토큰이고, LLM은 '판단이 필요한 항목'만 본다.
- **권한 경계는 도구로 지켜졌다.** 다른 세션을 거쳐 온 승인은 승인으로 인정되지 않았고(guard 저장소 push는 사용자가 해당 세션에서 직접 허락한 뒤에야 진행), 키 · 결제 · 남의 설정에는 어떤 세션도 손대지 않았다. 조직에서 여러 에이전트를 돌릴 때 그대로 쓸 수 있는 운영 원칙이다.

## 3. 연구의 한계점

- **표본이 작다.** 과제 5종 × 3회 × 노드 3개, 유효 실행 100번(bulk 대조는 과제당 1회). 비율의 방향은 뚜렷하지만 신뢰구간을 낼 만한 크기는 아니다.
- **과제가 인위적이다.** 정답이 정해진 작은 과제(이미지 내용, 함수+시험, 값 모순, 이미 아는 답, 근거 없음)만 썼다. 긴 실제 개발 작업에서 같은 배율이 나온다는 보장은 없다.
- **쿼터의 진짜 가중치를 모른다.** 구독 쿼터의 토큰 가중치는 공개되지 않아 API 정가 환산과 CLI 자체 비용 두 대용치를 썼고, 둘은 약 1.9배 차이가 난다. 결론은 두 측정의 방향이 같을 때만 단정했다.
- **모델 · 환경이 한정적이다.** Claude Haiku 4.5와 Sonnet 5.5, 클라우드 세션과 `claude -p` 한 실행기만 측정했다. GPT · Gemini(agv) 백엔드는 구현 · 오프라인 시험만 했고 실측하지 않았다.
- **캐시 효과가 섞여 있다.** Sonnet이 작은 문맥에서 싼 것은 캐시 적중 때문이며, 실행 순서와 캐시 수명에 따라 달라질 수 있다.
- **실험 설계에 실수가 있었다.** 1차에서 호출 상한을 구조 A의 호출 수(실행당 3회)에 맞게 잡지 못했고, T2 시험 파일 결함으로 1차 T2가 무효였다. 2차에서 고치고 다시 돌려 100/100을 채웠지만, 처음부터 기준 답 시험이 있었다면 막을 수 있었다.
- **안전 훅은 아직 관찰 모드다.** 문맥 예산 훅은 shadow로만 시험했고, 세션 안에서 설치하는 방식은 권한 검사에 막혔다(세션 시작 전에 설치해야 함 — 사용자 결정 대기).

## 4. 향후 연구 방향

1. **규모를 키운 재현.** 과제 수 · 반복 수 · 노드 수를 늘리고(예: 노드 5~10, 과제 20종 이상), 실제 저장소의 긴 작업(버그 수정 · 리팩터링)으로 바꿔 배율의 신뢰구간을 낸다.
2. **다른 모델 계열 실측.** agv(GPT · Claude · Gemini)와 HTTP 백엔드로 같은 실험을 돌려, 모델 계열마다 캐시 · 고정 오버헤드가 쿼터에 주는 영향을 비교한다.
3. **실제 쿼터와의 대조.** 구독 사용량 화면이나 공급자 사용량 API와 두 대용치를 나란히 기록해, 어느 쪽이 실제 쿼터에 가까운지 정한다.
4. **라우터 학습의 장기 효과.** '맞힌 답당 토큰'을 학습하는 라우터가 시간이 지나며 비용을 얼마나 더 줄이는지, 잘못 낮은 단계로 떨어지는 실패는 얼마나 생기는지 잰다.
5. **네트워크 동역학.** π(상호작용 가중치)의 변화, 수렴 속도, 모순 비율, 정보 이득을 긴 실행에서 재고, 연결 구조가 스스로 바뀌는 것이 성과에 실제로 도움이 되는지 검증한다(사양 §10 · §14).
6. **안전 훅을 enforce로.** 세션 시작 전 설치(환경 설정 스크립트)로 문맥 예산 훅을 강제 모드로 켜고, 예산 정지 → 체크포인트 → 새 턴 이어가기가 실제 운영에서 정답률을 해치지 않는지 본다.

## 5. 스펙 (ga-SDK 0.5.0)

### 5.1 구성 요소와 고정 버전

모든 저장소의 통합 브랜치는 `claude/gracious-meitner-vp49xe`.

| 패키지 | 저장소 | 커밋 | 버전 | 역할 |
|---|---|---|---|---|
| ga-sdk | cogito5170/ga-sdk | `5e8ef4b` | 0.5.0 | 허브 · 노드 런타임, CLI, 판정, 백엔드 플러그인, FINAL_TASK 실험 도구 |
| rlo-sdk | cogito5170/rlo-SDK | `0d92a3d` | 0.11.1 | 플러그인 레지스트리, 문맥 예산 훅, pspec, guard 연결 |
| l0-telemetry | cogito5170/Telemetry | `f6c7ae2` | 0.2.0 | L0 사건 기록(`llm.response`, `peer.message.*`) |
| llmsensor | cogito5170/Sensor | `ff17bdd` | 0.2.1 | 관측 · State 규칙의 기준(`state.peer`) |
| dc | cogito5170/DC | `7e0ac14` | 0.2.0 | DecisionContext, `peer_interaction` 목적 |
| ms | cogito5170/MS | `1f1018e` | 0.3.1 | 문맥 정책(KEEP/SUMMARIZE/RETRIEVE/DROP), `ms.network`(π · 활성화) |
| action-contract | cogito5170/action | `9d6729f` | 0.2.0 | 행동 계약(동료 요청이 곧바로 행동이 되지 않게) |
| guard · health | cogito5170/guard · health | `3f7b235` · `798e7ad` | 0.1.1 | 도구 호출 가드 · 사후 검증 |

- ga 핵심은 표준 라이브러리만 쓴다(Python ≥ 3.10). 네트워크 · 키 · 내장 쿼터 없음.
- `pip install ga-sdk`는 rlo-sdk[sensor]를 sha로 고정해 함께 설치한다. `ga-sdk[net]`은 NET 다섯 패키지를 같은 sha로 명시 고정한다. 둘을 한 venv에 설치해도 해석 충돌이 없고 `pip check`가 깨끗하다(BD-328 · 331).

### 5.2 동작 방식

- **두 모드.** 허브 모드(기본, 기존 동작 그대로)와 피어 모드(`ga-config/1`의 `network.mode = "peer"`).
- **fresh 턴.** 매 턴 새 호출. 프롬프트는 `ctxpack/1`: 지시 머리 → 세션 상태 파일 → 커서 이후 받은 메시지의 머리 → refs의 해당 줄 순서로 담고, `pack_max_tokens`를 넘으면 낮은 순위부터 버리고 버린 것을 기록한다. 지시 머리가 상한을 넘으면 턴을 열지 않는다.
- **턴의 끝.** 답에는 `report/2` 하나와 ```` ```state ```` 블록이 있어야 한다. ga가 둘을 검사한 뒤 보고를 올리고 상태 파일을 쓰며, 그다음에야 커서를 옮긴다. 검사를 통과하지 못한 답은 실패한 턴이고, 다시 시도하지 않는다.
- **피어 노드 한 걸음** (`ga node step <이름>`):
  1. ga mail에서 받은 메시지를 읽는다.
  2. 노드 자신의 규칙만 State를 바꾼다. 메시지는 근거가 있는 관측, 또는 의견(제안)으로 들어온다.
  3. `peer_interaction` 결정을 내린다(consult / send / skip). send는 π ≥ θ이거나, 요청이 열려 있거나, 모순 검증이 필요할 때만 한다. 간선마다 예산(rpm · tpm)이 있다.
  4. 최대 한 번의 fresh 턴을 연다.
  5. 결과를 ga mail로 보내고 L0에 기록한다.
- **이미 아는 답.** 이미 State에 VALID로 있는 답은 턴 없이 답한다.
- **라우터.** 백엔드 카탈로그(가격 · 능력 · effort)에서 조건을 만족하는 가장 싼 항목을 고른다. 검사에 실패하면 한 단계 올리고, 세 번 연속 성공하면 한 단계 내린다. '맞힌 답당 토큰'을 학습한다. 실제로 응답한 모델이 다르면 그 턴은 실패다.
- **예산 정지.** 문맥 예산 훅이 멈추면 체크포인트로 처리한다. 상태를 남기고 새 fresh 턴에서 이어 간다. 같은 상태로 두 번 연속 멈추면 판단이 필요한 항목이 된다.
- **백엔드 플러그인** (`ga.backends`): agv(GPT · Claude · Gemini), gemini_cli, claude_cli, codex_cli, openai_http, anthropic_http. 계획 호출은 가능한 곳에서 bare 호출(도구 끔, 시스템 프롬프트 교체)이다. 키는 설정이 가리키는 환경 변수에서만 읽는다.
- **메시지 꼴.** directive/2, report/2, verdict/1, notify/1, ga-plan/1, ctxpack/1, final-task-metrics/1. 전송은 축약한 머리 한 줄만 보내고, 사람이 읽을 글은 `ga render`로 만든다.
- **판정** (`ga judge`):
  1. `ga check`로 꼴을 검사한다.
  2. fast-forward가 되는지 확인한다.
  3. 빈 venv에 설치하고 `pip list` · `pip check`를 본다.
  4. 새 clone에서 네트워크를 막고 시험을 돌린다. 실패한 시험은 이름을 적고, base에서도 빨갛던 것은 원래 있던 실패로 표시한다.
  5. 무작위로 고른 변이를 넣어 시험이 잡는지 본다.
  6. 판정 초안과 기록 줄을 낸다.

  종료 코드는 0 clean, 1 judgement, 2 error, 3 apply refused.

### 5.3 FINAL_TASK 측정 정의 (`final-task-metrics/1`)

input_tokens · output_tokens · total_tokens · tool_calls · peer_messages · context_items_used / available · repeated_information, 여기에 result_correct · unknown_correct · quota_usd(usage × 정가, cache 쓰기 1.25× · 읽기 0.1×) · quota_cli_usd(`claude -p` total_cost_usd) · max_call_input · max_call_share · quota_per_correct.

## 6. 사용법

### 6.1 설치

```sh
python3 -m venv .venv && . .venv/bin/activate
pip install "ga-sdk @ git+https://github.com/cogito5170/ga-sdk@5e8ef4b"          # 핵심 (+ rlo-sdk[sensor])
pip install "ga-sdk[net] @ git+https://github.com/cogito5170/ga-sdk@5e8ef4b"     # 피어 모드에서 실제 NET 패키지
pip install "ga-sdk[http] @ git+https://github.com/cogito5170/ga-sdk@5e8ef4b"    # openai_http · anthropic_http 백엔드
pip check
python -c "import ga, ga.net.real as r; print(ga.__version__, r.source())"       # 0.5.0 net
```

claude-code-remote 같은 원격 환경 없이 로컬 컴퓨터에서 그대로 돈다.

### 6.2 허브 모드 (기존 방식, 코드 허브)

```sh
ga prompt <세션>                 # 세션 첫 프롬프트
ga send directive.md             # 지시 보내기 (directive/2)
ga post --channel <세션> --from <세션> report.md
ga tick                          # 받기 → 통합(ff) → 재현 → 판정 → 기록 → 다음 고르기; 새 것이 없으면 아무것도 안 씀
ga run --every 300               # 주기 실행 (cron 대신)
```

fresh 턴은 `ga.json`에서 세션에 `"context": "fresh", "pack_max_tokens": 20000`을 주면 된다. 문맥 예산 훅은 `runner.context_budget: {"soft":120000,"hard":150000,"mode":"shadow"}`로 켠다.

### 6.3 아무 모델로 감독 루프 (`ga supervise`)

```sh
ga supervise --list-backends                                   # 불러온 백엔드와 고정 오버헤드
ga supervise --backend claude_cli --config ga-supervise.json "할 일"
ga supervise --backend agv --config agv.json "할 일"            # model: gpt-* / claude-* / gemini-*
ga supervise --token-report conv.json                          # 오프라인 토큰 보고
```

`ga-supervise.json` 예시입니다. 키는 파일에 적지 않고, 키를 담은 환경 변수의 이름만 `key_env`에 적습니다.

```json
{"schema":"ga-supervise/1","backend":"anthropic_http","model":"claude-haiku-4-5-20251001","options":{"key_env":"ANTHROPIC_API_KEY"}}
```

### 6.4 피어 모드 (④ 구조)

`ga.json`에 `network` 항목을 추가합니다.

```json
"network": {"mode": "peer", "mailbox": "<git 저장소 경로>", "theta": 0.3,
            "edge_budget": {"rpm": 6, "tpm": 20000},
            "nodes": {"A": {"backends": ["claude_cli"],
                            "task": {"id": "T1", "goal": "...", "needs": {"capabilities": ["text"], "tier": "R0"}},
                            "budget": {"runs": 6}},
                      "B": {"backends": ["claude_cli"], "task": {"id": "T2", "goal": "..."}}}}
```

```sh
ga node step A                   # 노드 A 한 걸음
ga run --every 60                # 모든 노드를 매 라운드
ga usage --ctx-max 150000 --fail # 토큰 경보 (세션 API 없이 .ga 의 L0 로)
```

### 6.5 판정 · 메시지

```sh
ga judge --template CMD-X                                         # 보고 머리 견본
ga check report.md
ga judge --report owner/repo@<sha>:reports/CMD-X.md --repo ./clone --base <통합 브랜치> --mutations mut.json
ga inbox github:<owner>/<repo>#<issue>                            # 커서 이후 머리만
ga render --lang ko report.md                                     # 사람이 읽을 글
```

### 6.6 FINAL_TASK 다시 돌리기

```sh
cd ga-sdk
python -m unittest tests.test_ft1                # 오프라인 (모델 호출 0)
python bench/final_task/run.py --max-runs 10     # 실제 실행: claude 로그인 필요, 상한 넘기 전 스스로 멈춤
# 결과: bench/final_task/results/{runs.jsonl, ledger.jsonl, SUMMARY.md}
```

### 6.7 운영 원칙 (요약)

- 지시 하나 = 새 세션 하나. 문맥이 15만 토큰을 넘으면 커밋하고 STATE.md를 남긴 뒤 멈춘다.
- 보고는 머리 한 줄(report/2)과 notify/1만 보낸다. 통로를 처음부터 읽지 않는다.
- 판정은 `ga judge`가 하고, LLM은 '판단이 필요한 항목'만 본다.
- 키 · 토큰 · 비밀은 저장소 · 메시지에 넣지 않는다. 다른 세션을 거쳐 온 승인은 승인이 아니다. 훅 · 설정 변경은 사람이 한다.
