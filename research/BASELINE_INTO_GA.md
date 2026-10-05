# baseline 을 GA Engine 안으로 (BD-436)

사용자(2026-10-05): "baseline 은 언제 ga engine 안으로 들어가는가? 절차적으로 압축 없이 보고해라." → "VM 서버가 있다. 그곳에서 24 시간 돌릴 생각이다."

## 0. 지금

baseline 은 Claude 클라우드 세션(10-02 시작, 약 3.5 일 동안 CLI 비용 $659.98, cache read 18.6 억, 문맥 255k)이다.
GA 명령은 가져다 쓰기만 하고, 판단과 기록 대부분을 직접 한다.
같은 날 agv 코드 항목은 1 턴에 9–11k 토큰이었다. 비싼 것은 일하는 쪽이 아니라 긴 대화를 다시 읽는 허브다.

## 1. baseline 이 하는 일과 GA 쪽 대응

| # | baseline 이 하는 일 | GA 쪽 | 상태 |
|---|---|---|---|
| 1 | 요청 해석 | ga ask / ga do (GA36·37) | 단순 요청만 |
| 2 | 지시문 설계 | Planner (GA40) | 없음 |
| 3 | 합격 시험 · 참고 구현 · 변이 고르기 | Verifier (GA39) | 없음 |
| 4 | 작업자 띄우기 | ga supervise + 백엔드, agy bridge + ga act | 코드 항목만 |
| 5 | 감시 | ga usage · ga inbox · ga run | 있음(안 써 왔음) |
| 6 | 판정 · 통합 | ga judge --apply | 있음(손 Bash 로 해 왔음) |
| 7 | 판정 결정 · 되돌림 글 | GA42 ga hub 카드 + 작은 모델 | 만드는 중 |
| 8 | 기록(BD · 회차 · 장부 · 세션 목록) | GA42 ga hub | 만드는 중 |
| 9 | 사용자 보고 | GA Console (CON1–3) | 만드는 중 |
| 10 | 막힐 때 판단 | ASK_HUMAN | 사람 · 큰 모델 몫 |

## 2. 단계와 통과 조건

1. **위임 연습.** 판정 · 우편 · 감시를 GA 명령으로만 하고, baseline 은 판단만 덧붙인다. 통과: 연속 5 건, 손으로 한 단계는 빈틈 목록으로 남긴다. 첫 건은 CON2 판정이다. 빈틈:
   - (a) ga judge 는 보고서의 sha 만 판정하고, 허브 쪽 병합 커밋은 따로 시험해야 한다.
   - (b) 변이 목록을 손으로 쓴다.
   - (c) 변이 시험 이름을 모듈 경로로 맞춰야 한다.
2. **GA42 착지 + 그림자 운행.** ga hub 가 결정만 하고 실행하지 않는다(그림자 모드: GA42 rev 2 또는 GA43 에서 추가). baseline 판정과 비교한다. 통과: 연속 10 건에서 잘못 받음 0 건, 불필요한 되돌림 3 건 이하, 되돌림 요청의 핵심이 같다.
3. **판정 넘기기.** ga hub 가 실제로 합치고 기록하고 되돌린다. baseline 은 ASK_HUMAN 만 받는다. 통과: 2 주 또는 20 건 동안 잘못 합친 것 0 건, 기록 꼬임 0 건.
4. **Verifier (GA39).** 바뀐 코드에서 변이를 코드로 만들고(검사 줄 지우기 · 조건 뒤집기 · 상한 늘리기 · 셸 켜기), 합격 시험 초안을 쓴다(빌드 · tsc 항목 필수). 통과: baseline 이 손으로 찾았던 생존 변이(CON1 min-font · weight, GC25, GC18)를 다시 잡는다.
5. **Planner (GA40).** 요청에서 지시문 초안을 만든다. 처음은 그림자로 운행한다. 통과: 연속 10 초안이 ga check 를 통과하고 baseline 이 실질적으로 고친 것이 0 이다. 오늘의 실패(AGA2 데이터 모양, AGA4 tsc, CON1 변이 목록, GA42 그림자 모드)는 모두 계획 쪽이었다.
6. **실행자 전환 · VM 상주.** 큰 작업을 Claude 세션 대신 agy 백엔드의 더 큰 모델로 보낸다. 통과: RW 비교에서 같은 성공률, 더 적은 토큰.
7. **baseline 대기.** 큰 모델 세션은 ASK_HUMAN · 설계 질문에만 불린다. 기록은 ga hub, 보고는 Console 이 한다.

들어가지 않는 것은 사람 승인(guard · 설정 · 훅 · 도구 승격 · 키 · 결제 · 서명), Claude 플랫폼 세션 도구(계정 인증), 제품 방향 결정이다.

## 3. VM 배치 (사용자 VM, 24 시간)

```
VM ─ systemd(사용자 단위, 다시 시작=항상)
     ├─ ga run       hub 모드: ga hub tick 을 S 초마다(단계 2 부터, 처음은 그림자)
     ├─ ga bridge    agy 우편 다리(지금 맥의 bridge.py 를 옮김)
     └─ ga console   127.0.0.1 에만. 맥에서는 ssh -L 로 본다(포트를 밖에 열지 않음)
작업 공간: ~/baseline ~/ga-sdk ~/token (git clone), ~/ga-venv, ~/.ga/(console.json · actions.json · actions-policy.json)
```

- Console 은 0.0.0.0 으로 열지 않는다. 맥에서 `ssh -N -L 8765:127.0.0.1:8765 vm` 으로 연 뒤 `http://127.0.0.1:8765/?t=…` 를 쓴다(일회용 토큰은 그대로).
- 사용자만 하는 일(세션은 손대지 않음):
  - GitHub 쓰기 권한 설정(배포 키 또는 gh 로그인)
  - agy 로그인
  - Token 의 .env 같은 비밀 파일(파일 권한 600)
- 기록 · 로그는 journald 와 ~/.ga/ 아래에 둔다. 비밀처럼 보이는 줄은 가린다(secrets_in).
- 꺼짐 · 재부팅: systemd 가 다시 띄운다. ga hub 는 우편함 커서로 이어서 처리한다. 클라우드 매시 점검(trig_01RsSwQxwd5TuzF6ihnuEE8d)은 단계 3 까지 안전망으로 둔다.
- Token 개발 서비스(api · worker · web)는 Console 이 도는 기계에서 켜진다. VM 에서 돌리면 맥 브라우저는 ssh -L 로 3000 · 8000 도 연다.

## 4. 지시 순서

GA42(진행 중) → GA42 rev 2(그림자 모드 + 빈틈 a–c) → OPS1(VM 배치: systemd 단위 3 개, `ga setup vm` 점검, ssh -L 안내, 비밀 없음) → GA39 → GA40 → RW 비교(실행자 전환).

## 5. VM 조건 (사용자: Oracle Free Tier, GPU 없음)

- 기계는 Ampere A1(ARM aarch64, 최대 4 OCPU · 24 GB)을 권한다. AMD micro(1 GB)로는 Token 스택을 함께 돌리기 어렵다.
- agy CLI 의 linux-arm64 지원은 확인하지 않았다. 지원하지 않으면 bridge 는 맥에 두고, ga run(hub)과 console 만 VM 에서 돌린다(둘은 git 우편함으로 이어진다).
- 유휴 회수(baseline 이 아는 정책, 확인 필요): 7 일 동안 CPU · 네트워크 · (A1) 메모리 사용률이 낮으면 회수될 수 있다. 대응:
  - (a) 종량제 계정 전환은 사용자 결정이다(결제 수단이 필요하고, 세션은 권하거나 진행하지 않는다).
  - (b) VM 은 잃어도 되게 만든다. 상태는 모두 git 에 두고, 설치 스크립트로 다시 세운다(OPS1).
  - 일부러 부하를 만들어 회수를 피하지 않는다.
- GPU 가 없으니 작은 모델은 계속 agv(agy 서비스)다. gpt-oss-20b 를 A1 CPU 로 로컬 실행하는 것은 실험 후보로만 남긴다.

## 6. VM 사실 (사용자 출력, BD-438)

- x86_64(ARM 이 아님), Ubuntu 24.04.4, systemd 255, Python 3.12.3, Node 20, 2 코어, 11 GB, GPU 없음, agy 없음.
- 디스크 45 GB 중 96 % 였다. 사용자가 pip 가 안 도는 것을 확인하고 /tmp 의 pip 임시 폴더를 지워 72 %(13 G 여유)가 됐다(10-05). /tmp 에는 아직 8.8 G 가 남아 있다(nsw_* 등, 사용자 판단).
- 1 차 배치는 VM 에 엔진만 둔다. bridge 와 Token 은 맥에 둔다. 지시는 CMD-OPS1.
