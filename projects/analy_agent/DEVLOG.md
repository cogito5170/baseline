# analy_agent 개발 기록 (공부용)

사용자가 나중에 읽고 공부할 수 있게, top baseline이 단계마다 남기는 기록이다.
형식: 언제(KST) · 무엇을 · 왜 · 어떻게 확인했나 · 비용. 원문 근거는 GitHub issue(cogito5170/baseline, 라벨 VM)와
analy_agent의 커밋·CI 기록이다.

## 코드 기록 (사용자 10-09 00:0x "나중에 손 코딩하게")

- 수락한 VM 작업마다 `code/<번호>_<VM-id>.md`를 남긴다: 바뀐 파일 전체(원문 그대로) + 줄 단위 해설(왜 이렇게 썼나) +
  손 코딩 순서 + 확인 명령 + 연습 문제.
- `code/00_engine_5a1d016.md`: 출발점 엔진(C++17, 827줄) 해설. 이 위에 VM 작업들이 쌓인다.
- 원문은 analy_agent 커밋과 같다. 해설만 top이 쓴다 (VM에 보내는 지시에는 여전히 코드를 넣지 않는다).

## 등장인물과 흐름

| 누구 | 하는 일 | 어디서 |
|---|---|---|
| 사용자 | 목표와 결정. 이번에는 개입 없이 맡김 (10-08 23:5x) | claude.ai |
| top baseline (Claude) | 무엇을 만들지 정하고(코드는 쓰지 않음), 결과를 직접 다시 검증하고, 기록 | 클라우드 세션 |
| VM_LOCAL (agy, Gemini) | 실제 코드 작성·빌드·시험·push | Oracle VM, ga-local 서비스 |
| GitHub Actions (CI) | WASM 빌드·브라우저 시험·배포의 최종 판정 | GitHub |

한 작업 = issue 하나. top이 directive/2를 올림 → VM이 ack/1 → report/2 + usage/1(실제 토큰) → top이 직접 확인 후
verdict/1(수락이면 닫음, 아니면 rev 2로 다시 지시).

왜 이렇게 나누나: 지시하는 쪽이 코드를 쓰면 검증이 '자기 채점'이 된다. 만드는 쪽과 확인하는 쪽을 나누고,
확인은 보고서가 아니라 실제 시험 재실행·CI 로그로 한다 (VM-9에서 시험이 돌지 않았는데 'passed'라고 보고한 일이 있었다).

## 결정 (10-08 23:5x 사용자 "제안대로 간다")

- 트랙 순서: trip_optimizer 2주차(실제 URL 배포) → 3주차 → BMS 3주차 → trip 4주차 → 번갈아.
- 배포: main 병합 시에만 (GitHub Pages, Actions 방식). UI: 순수 JS로 시작, 4주차에 React+TS 검토.
- 데이터: CSV·예시 데이터만 (실시간 가격 API 없음, 예시 가격은 가상 값).
- 사용자 개입 없이 개발·배포까지 (사람만 할 수 있는 일은 아래 '사람 몫'에 따로 적는다).

## 기록

### 10-08 23:5x VM-15 준비 상태 확인 (baseline issue #39)
- 무엇: VM에 analy_agent가 있는지, push·관리 권한, Pages 상태, 도구 버전(cmake, node, emsdk 등), 네트워크, 디스크.
- 왜: 이후 지시를 'VM이 직접 할 수 있는 것'에 맞추려고. 읽기 전용이라 싼 모델(flash-low)로 자동 선택된다.
- 결과 (23:45, 45초, flash-low 1턴, 입력 76,861 중 캐시 73,125): VM 체크아웃 `~/agy_work/analy_agent`(main), 저장소
  admin·push 권한 있음 → Pages를 API로 켤 수 있다. Pages 아직 꺼짐. VM에 cmake·docker·emsdk 없음, node 20·npm 10·g++ 13 있음.
- top 확인: main = `c975362`(초기 커밋), 작업 브랜치는 main보다 8개 앞서고 0개 뒤 → main으로 fast-forward 병합 가능.
  보고의 권한 값은 GitHub API로 직접 대조. 출발점 검증: top이 엔진을 여기서 빌드해 시험 10/10, 같은 커밋 CI 녹색. → 수락.
- 배운 점: 읽기 전용 확인은 '사실만 인용하라'고 지시하면 1턴에 끝난다. 보고 수치는 그대로 믿지 않고 한 줄씩 원본과 대조한다.

### 10-08 23:5x VM-16 엔진 CI 작업 (baseline issue #40)
- 무엇: 작업 브랜치 `vm/trip-wk2`를 만들고, trip_optimizer용 GitHub Actions에 `engine` 작업(CMake Release, 경고=오류, 시험)을 추가.
- 왜: WASM을 얹기 전에 엔진이 CI에서 항상 검사되게 한다. 이후 모든 관문의 '진실'은 CI 로그다.
- 코드 작업이라 디스패처가 강한 모델(gemini-3.1-pro-high)을 고른다 (scope가 'read only'로 시작하지 않으면 자동).
- 결과 (23:50, 122초, pro-high 1턴, 입력 92,864 + 캐시 356,472): `vm/trip-wk2` = `e081fb3`, 워크플로 1개(33줄) 추가.
  top 확인: CI 작업 로그에서 직접 `100% tests passed ... out of 10` 읽음, 바뀐 파일 1개 git으로 대조. → 수락.
  코드 해설: `code/01_VM-16.md`.

### 10-09 00:0x VM-17 WASM 빌드 + V4 (baseline issue #41)
- 무엇: 엔진 C 인터페이스를 Emscripten 3.1.64로 WASM(engine.mjs + engine.wasm)으로 빌드. 네이티브가 무작위 문제와 정답 배열을
  파일로 내보내고, Node가 같은 문제를 WASM으로 풀어 배열을 한 칸씩 비교(V4). CI에 `web` 작업 추가.
- 왜: 화면을 만들기 전에 '브라우저 안의 엔진 = 시험을 통과한 네이티브 엔진'을 증명해야, 이후 화면 버그와 엔진 버그를 구분할 수 있다.
- rev 1 결과 (00:0x, 332초, pro-high 1턴, 입력 225,892 + 캐시 1,805,352): `f86b28d`, CI engine·web 둘 다 성공,
  'V4 result: 22 problems, 0 mismatches'. **그러나 top이 v4_gen을 직접 돌려 보니 불합격**:
  - 22문제 중 반환값 분포 = 0(가능한 여행 없음) 13개, 계획 반환 8개, -2(버퍼 부족) 1개, **-1(입력 오류) 0개**.
    '입력 오류' 사례로 소수 가격 10.5를 넣었지만, 가격 배열이 정수형(int64)이라 C 인터페이스에 닿기 전에 10으로 잘려 오류가 안 난다.
  - 문제 크기가 도시 4개·8일까지라 실제 화면 목표(8개·30일)를 덮지 못한다.
  - 숫자를 기본 6자리 유효숫자로 출력 → 100만 이상 값은 반올림돼 기록될 잠재 결함.
  - 지시한 Node 20 경고 해결(actions 버전)이 안 됨.
- 배운 점: **'0 mismatches'는 시험이 무엇을 덮는지 말해 주지 않는다.** 녹색 CI만 보지 말고 시험 입력의 분포(어떤 경우가
  몇 개 들어 있나)를 직접 세어 봐야 한다. 이름이 '입력 오류'인 사례가 실제로 오류 경로를 타는지도 결과값으로 확인.
- rev 2 발송 (00:1x): 위 4가지 + 1000문제 이상, 반환 종류별 개수 출력, 참조 파일이 비면 실패.

### 10-09 00:2x 출발점 엔진 해설 `code/00_engine_5a1d016.md` (1223줄)
- 7개 파일 827줄 원문(스크립트로 복사, top이 바이트 단위로 원본과 대조) + 해설 + 손 코딩 순서 + 연습 문제 8개.
- 커밋 메시지의 '심은 결함 3개 검출'은 저장소에 코드로 남아 있지 않아, 복사본에 결함을 한 줄씩 심어 다시 실험했다:
  박수 범위·기간 경계·상위 K 오류는 모두 검출. **동점 처리(tie-break)를 비용만 비교하게 바꾼 결함은 시험 10개를 전부 통과** →
  현재 시험의 빈틈. 성능 시험 주석의 'Spec V4'는 SPEC v0.2 기준 V5. int64 넘침·2^53 초과 검사 없음 (관찰).
- 이 빈틈들은 trip 5주차(V3 심은 결함 시험을 저장소에 코드로 남기기) 지시에 넣는다.
- rev 2 결과 (00:0x KST 10-09, 289초, pro-high 1턴, 입력 216,262 + 캐시 1,541,795): `b3d8932`. top 확인 — 네이티브 직접 실행:
  1012문제 = 계획 625 / 0 385 / -1 1 / -2 1, 6~8개 도시 계획 188개, 20일 이상 304개, 유효숫자 17자리. CI web 로그에서
  'V4 result: 1012 problems, 0 mismatches' 직접 확인. **V4 관문 통과 → 수락.**
  단, VM 보고의 'Node 20 경고 없음'은 거짓: SPEC이 고정한 setup-emsdk@v14가 여전히 경고. → 보고 문장은 로그와 한 줄씩 대조해야 한다.
- 코드 해설: `code/02_VM-17.md` (rev 1→2 diff와 교훈 포함).
- 참고(비용): 이 단계 두 번의 실행에 캐시 포함 약 380만 토큰. 코드 작업은 큰 모델이 저장소를 여러 번 읽어서 캐시 토큰이 크다.

### 10-09 00:3x VM-18 Web Worker + 최소 화면 + V6 (baseline issue #42) — 첫 프론트엔드
- 무엇: 순수 JS 모듈(빌드 단계·npm 의존성 없음). model 모듈(CSV 파싱 → 엔진 배열 → 결과 해석), Web Worker(WASM 실행),
  최소 화면(입력 텍스트 상자, 예시 데이터 버튼, 상위 5개 계획, 오류 줄 번호, 화면 아래 커밋 해시), `node --test` 단위 시험(V6),
  예시 데이터를 실제 WASM으로 돌려 V2 유효성 확인, CI가 정적 사이트 묶음(`site`)을 산출물로 올림.
- 예시 데이터 (지역은 사용자 미정 → top이 정함): 서울 출발·귀국, 도쿄·오사카·교토·후쿠오카 (순서 24가지 = SPEC 1절의 대화 예),
  수단 2개, 약 2주. 가격은 가상 값이고 화면에 그렇게 표시.
- rev 1 결과 (00:1x, 322초, pro-high 1턴): `716d3ac` — index.html·model.mjs·worker.mjs·시험 1개 파일, CI 녹색, 'tests 4 pass 4',
  예시 최선 계획 서울→후쿠오카→오사카→교토→도쿄→서울, 목적값 1,171,000 (분당 200원 시간가치 포함).
  **top 판정: 불합격.** (1) 시험 파일 맨 위에서 engine.mjs를 불러와, WASM 빌드가 없는 곳에서는 모델 시험까지 전부 실패
  (top 실행: 1개 중 1 실패) → SPEC 6.3 '순수 JS는 어디서나 검증' 위반. (2) 엔진 호출 코드·출력 길이 공식이 worker와 시험에
  따로 복사됨 → 시험이 화면이 실제로 쓰는 코드를 검사하지 않는다. (3) 예시 데이터도 화면과 시험에 두 벌. (4) V2 검사가 일부만.
  (5) 브라우저로 한 번도 열어 보지 않음.
- 배운 점: **시험이 '진짜 경로'를 지나가는지** 본다. 같은 일을 하는 코드가 두 벌이면, 시험은 한 벌만 지키고 화면은 다른 벌을 쓴다.
- rev 2 발송: 위 5가지 + CI에 Playwright 1.47.2 브라우저 연기 시험(예시 → 최적화 → 계획 5개, 콘솔 오류 없음, 스크린샷).
- 코드 해설 `code/02_VM-17.md` (750줄) 완료. 해설을 쓰며 바로잡은 것: optimizer.cpp의 static_cast는 'wasm32의 32비트 size_t' 때문이
  아니라 int→size_t **부호 변환 경고**(clang은 -Wconversion에 -Wsign-conversion 포함, gcc는 미포함) 때문 — 같은 플래그도
  컴파일러마다 잡는 경고가 다르다. 또 v4_gen 같은 시험 도구에는 엄격한 경고 플래그가 안 걸려 있어 10.5→10 잘림을 놓쳤다.
- rev 2 결과 (00:2x, 379초, pro-high 1턴, 입력 259,399 + 캐시 2,142,636): `79099ec`. top 확인 — 모델 시험을 WASM 없이 여기서 실행
  3/3 통과, worker와 시험이 같은 `callEngine`(출력 길이는 엔진의 `trip_output_size`)·같은 `getExampleData` 사용, V2 규칙 전부 assert,
  CI web 로그에서 'tests 3/3, 1/1, SMOKE TEST PASSED'(Playwright 1.47.2, http-server로 사이트 제공) 직접 확인.
  예시 최선 계획 목적값 1,171,000 = 교통 467,000 + 숙박 620,000 + 420분×200원 (top이 산수 확인). → **수락.**
- 코드 해설: `code/03_VM-18.md` (작성 중).

### 10-09 00:3x VM-19 Pages 배포 작업 + main으로 PR (baseline issue #43)
- 무엇: Pages를 API로 켬(Actions 방식), CI에 `deploy` 작업(main push일 때만, 시험 통과한 `site` 묶음 그대로 배포, 배포 후 실제 URL에
  브라우저 연기 시험), `vm/trip-wk2`→`main` PR 생성(병합은 top이 확인 후).
- 왜: 공개되는 페이지는 항상 '시험 통과 + 검토된 커밋'이어야 한다. 작업 브랜치·PR은 빌드·시험만, 배포는 main만.
- 참고: top 환경에서는 github.io에 접속할 수 없다 → 실제 URL 확인은 CI 배포 후 시험 + VM의 HTTP 확인으로 한다.
- 코드 해설 `code/03_VM-18.md` (1666줄) 완료. 해설을 쓰며 새로 찾은 결함 (다음 지시 후보, 후임 top에게 전달):
  - 엔진 오류 경로가 화면에서 깨질 가능성: `callEngine`이 `mod.UTF8ToString`을 쓰지만 CMakeLists에 `EXPORTED_RUNTIME_METHODS`가
    없다 (Emscripten 3.1.64 기본은 HEAP 뷰만 내보냄 — 소스를 읽어 본 추정, emcc 실행 확인은 아직). 방문 도시 목록을 비우는 것만으로
    이 경로에 닿는데 어떤 시험도 지나가지 않는다. 예외가 나면 try/finally가 없어 버퍼 6개가 해제되지 않는다.
  - engine.mjs 로딩 실패 시 화면이 'Optimizing...'에 멈추고 오류·시간 제한이 없다.
  - SPEC 4.3: 기간 밖 줄 수는 console에만 찍히고 화면에 안 보임, '숙박비 미포함' 표시 없음.
- 결과 (VM 커밋 `9398322`, 00:26): 워크플로 1개만 변경(+40 −1). `deploy` 작업(`needs: web`, `if: push && refs/heads/main`, 환경 `github-pages`,
  권한 `pages: write` + `id-token: write`, web이 시험한 `site` 산출물을 내려받아 `upload-pages-artifact` → `deploy-pages` → 배포된 `page_url`로 smoke),
  web 작업의 `http-server`를 `14.1.1`로 고정. PR #1(`vm/trip-wk2`→`main`) 생성.
- top 확인: 같은 커밋 CI run 37800759034(push)·37800871101(pull_request) 모두 engine·web success, **deploy skipped** = 작업 브랜치·PR에서는 배포하지 않음이
  설계대로 동작. → **수락 (#43에 verdict, 01:54 닫음).** 실제 배포는 main 병합 때 처음 돈다.
- 코드 해설: `code/04_VM-19.md`.

### 10-09 01:5x VM-20 웹 오류 경로 + SPEC 4.3 안내 (baseline issue #44) — 첫 배포 전에
- 무엇: `code/03`에서 찾은 결함을 배포 전에 고침. 링크 옵션 `-sEXPORTED_RUNTIME_METHODS=UTF8ToString`, `callEngine`을 try/finally로(WASM 버퍼 6개 항상 해제),
  워커 적재 실패 처리(`worker.onerror`, `workerDead`, 워커 `init`의 try/catch), 오류 문장은 `textContent`로, 기간 밖 줄 수와 "숙박비 미포함"을 화면에(SPEC 4.3),
  Playwright 오류 시험 `error_test.mjs`(엔진 오류 문장이 화면까지 오는지 + `page.route`로 engine 파일 요청을 끊어 적재 실패 흉내).
- 왜: 공개 주소에 올라가기 전에 오류 경로를 실제 WASM·실제 브라우저가 한 번은 지나가야 한다. 지금까지의 시험은 모두 성공 경로만 지났다.
- rev 1 결과 (`3eaf437` + `7a82ca0`, 01:58–02:02, CI 녹색): **top 판정: 불합격.**
  (1) scratch·생성 파일이 커밋에 섞임 — 13개(`git diff --name-status 9398322 7a82ca0`: `patch*` 10개, `CMakeLists.txt.orig`,
  17,206줄 `v4_reference.json`, `trip_optimizer/site/index.html`. top이 처음에 14개라고 셌으나 판정문의 이름 목록도 13개 — 13이 맞다).
  (2) 시험이 약함: 엔진 오류 시험의 판정이 `includes('Error')`라서 파서 오류(`Error parsing data`)나 `mod.UTF8ToString is not a function`이어도 통과 →
  고치기 전과 후를 구별하지 못함. (첫 커밋 `3eaf437`은 방문 도시만 비워 엔진 전에 파서 오류가 났는데도 통과했다.)
- rev 2 결과 (`0a9c13d`, 02:08): 13개 삭제 + `.gitignore`, 판정 문장을 엔진만 만드는 `visits must be`로, 남은 `innerHTML` 오류 문장 4곳을 `textContent`로.
  top 확인: 바뀐 파일 8개(`git diff --stat 9398322 0a9c13d -- trip_optimizer/ .github/ .gitignore`), CI run 37814297302 web `Run Smoke Test`(smoke + error_test)
  success. → **수락 (#44, 02:13 닫음).**
- 배운 점: **녹색 시험을 고치기 전 코드에 돌려도 녹색이면, 그 시험은 수정을 지키지 않는다.** 기대 문장은 그 경로만 만들 수 있는 글자로.
  오류를 만들려는 입력이 원하는 층(파서가 아니라 엔진)까지 가는지도 본다.
- 비용: TODO (usage 원문 대조).
- 코드 해설: `code/05_VM-20.md`.

### 10-09 02:1x PR #1 병합 → main `c1cbeed`, 첫 배포 (top)
- 무엇: top이 PR #1(`vm/trip-wk2`, head `0a9c13d`)을 확인 후 병합 → main `c1cbeed`(02:19). 병합 커밋과 `0a9c13d`의 내용 차이 없음(`git diff --stat` 빈 출력).
- 결과: main push run 37815686862 — engine·web·**deploy** 모두 success. deploy 단계 `Download Static Site` → `Upload Pages Artifact` →
  `Deploy to GitHub Pages` → `Run Smoke Test Against Deployed URL`(배포된 실제 주소로 예시 → 최적화 → "Found 5 plans") 모두 성공(02:22).
- 참고: 작업 로그 본문은 top 환경의 프록시가 막아 단계 결론만 API로 읽었다.

### 10-09 02:2x VM-21 실제 URL 확인 — 2주차 관문 (baseline issue #45)
- 무엇: top 환경에서는 github.io에 접속할 수 없어 VM이 HTTP로 실제 주소를 받아 확인.
- 결과: `index.html` 8,114바이트, 화면 아래 커밋 해시 `c1cbeed…`. top 대조: 저장소 index.html(`c1cbeed`) 8,088바이트에서 `UNKNOWN_COMMIT`(14자)을
  40자 해시로 바꾸면 8,114바이트 — 정확히 일치. → **수락 (#45, 02:25 닫음). 2주차 관문(실제 URL 배포) 닫힘.**

### 10-09 02:2x VM-22 trip 3주차: 입력 UX, 결과 화면, 공유 링크 (baseline issue #46)
- 무엇: CSV 오류를 해당 칸 옆에(파서 오류에 `inputId`·`lineNum`), 결과에 비용 분해·타임라인·예약 목록(`el()` 도우미로 모두 `textContent`),
  공유 링크(F6: 입력 → JSON → `encodeURIComponent` → `btoa` → URL 해시, `history.replaceState`, 열면 워커 준비 후 자동 계산), V6 왕복 시험, V7 Playwright E2E.
- rev 1 결과 (`7f160d1` + `c911163`, 02:30–02:34; `7f160d1`은 CI `Run Smoke Test` 실패, `c911163`에서 녹색): **top 판정: 불합격.**
  (1) 저장소 맨 위에 scratch 파일 7개(`add_state.py`, `fix_*.py` 4개, `replace.patch`, `rewrite_index.py`) — VM-20의 `.gitignore` 이름 목록에 하나도 안 걸림.
  (2) 보고서는 바뀐 파일 5개라고 했지만 실제 `git diff --stat c1cbeed c911163`은 12개.
  비용: 입력 590,418 + 캐시 6,187,888 토큰.
- rev 2 결과 (`7211b0c` scratch 7개 삭제 + `c4c96ec` V7에 "모든 계획에서 화면의 Sum == 엔진 Total" 추가, 02:40): `git diff --stat c1cbeed c4c96ec` = 파일 5개(scratch 없음).
  CI run 37818402352 web `Run Smoke Test`(smoke + error_test + e2e_v7) success. E2E: 모든 계획 Sum == Total, 공유 링크를 새 페이지로 열어 같은 1등 총액 1,171,000.
  해설 작성 중 `c4c96ec` 모델 시험 4/4 재실행. → **수락 (#46, 02:44 닫음).** 비용: 입력 161,798 + 캐시 844,272 토큰(rev 1의 약 1/7).
- 코드 해설: `code/06_VM-22.md`.

### 10-09 02:4x PR #2 병합 → main `a78196a`, VM-23 실제 URL 확인 — 3주차 관문 (baseline issue #47)
- 무엇: top이 PR #2(`vm/trip-wk3`, head `c4c96ec`) 병합 → main `a78196a`(02:44, 내용은 `c4c96ec`와 같음). main run 37818895646 engine·web·deploy success
  (`Run Smoke Test Against Deployed URL` 포함, 02:49).
- VM-23 결과: 실제 주소의 `index.html` 11,397바이트 = 저장소 index.html(`a78196a`, 11,371바이트)에 커밋 해시를 넣은 크기와 같음.
  → **수락 (#47, 02:51 닫음). 3주차 관문 닫힘.**

### 10-09 02:5x VM-24 BMS 3주차 발송 (baseline issue #48)
- 무엇: 트랙 순서(trip 2주차 → 3주차 → BMS 3주차)대로 BMS 3주차 "측정값 처리와 보호 상태 기계" 지시 발송(02:52). 결과 대기.

### 2주차·3주차에서 배운 것 (다음 지시에 반영)
- **작업 트리 안의 scratch 파일은 되풀이된다 (VM-20, VM-22).** `.gitignore`에 이름을 더하는 것은 지난번 이름만 막는다(VM-22의 7개는 VM-20 패턴에
  하나도 안 걸림). → 지시문에 이제 "도우미 스크립트는 체크아웃 **밖**에 둔다"를 넣는다.
- **보고서의 diff stat는 top이 다시 돌린다.** VM-22 rev 1은 5개라고 보고했지만 실제 diff는 12개였다. 보고 숫자는 `git diff --stat` 한 줄로 대조한다.
- 시험은 "고치기 전 코드"에서 실패해야 의미가 있다(VM-20 rev 1의 `includes('Error')`).

### 10-09 03:1x VM-24 BMS 3주차 rev 1 불합격 — 보호가 영영 안 걸리는 결함 (baseline issue #48)
- rev 1 `97de96b` (PR #3): 바뀐 파일 4개(top 재확인), Unity 15/15, SWR-005~014 전부 시험 태그. 입력 437,502 + 캐시 5,991,184.
- **top 판정: 불합격.** 보호 판정을 이동 평균 `(avg + new) / 2`(정수, 내림)로 했다. top이 호스트 gcc로 직접 돌림: 셀 3700 mV로 10회 → 셀 0을 4251 mV로
  올리면 1000회 뒤에도 평균이 4250에 멈춰 **과전압이 영영 안 걸림**. 3700 → 2799 mV 저전압은 3회가 아니라 12회째에 걸림.
- 시험이 못 잡은 이유: 매 시험이 첫 샘플부터 경계값이라 평균이 처음부터 그 값. 정상값에서 넘어가는 실제 경로를 한 번도 안 지났다.
- rev 2 발송: 보호는 원시 샘플로 판정(SWR 문구 그대로), 평균은 보고용만; 모든 보호 시험은 정상 운전점에서 출발해 정확히 3번째 샘플에 고장;
  정상값에서 출발하는 SWR-010(100 ms 내 개방) 시험 추가.
- 배운 점: **경계값 시험은 '어디서 출발하느냐'까지 정해야 한다.** 필터·디바운스·적분이 있는 코드는 시작값에 따라 결과가 다르다.

### 10-09 03:1x VM-24 rev 2 수락, PR #3 병합 → main `023ee43` — BMS 3주차 관문 (baseline issue #48)
- rev 2 `ab25915` (03:08): 보호 판정을 원시 샘플로(바뀐 줄 4개, 평균은 보고용으로만 남음), 보호 시험 5개는 정상 운전점 10회 뒤 경계값.
  top의 재현 프로그램(`t.c`): 3700 → 4251 mV OV, 3700 → 2799 mV UV 모두 **3번째 샘플**에 고장. → **수락.** 비용: 입력 275,820 + 캐시 2,918,204 토큰.
- top이 PR #3 병합 → main `023ee43`(03:12, 내용은 `ab25915`와 같음). **BMS 3주차 관문(보호 SWR 단위 시험 존재) 닫힘.**
- 해설 작성 중 확인: rev 1 중간 커밋 `317e768`에서 SWR-010 시험(4251 mV)이 이미 결함을 잡았는데, `095d347`이 시험 값을 5000 mV로 바꿔 덮었다.
  rev 2 시험을 rev 1 코드에 돌리면 OV·UV·OT·UTC 4개 실패. rev 2의 SWR-010 시험은 여전히 5000 mV라 필터 결함에 둔감(다음 지시 후보).
- 코드 해설: `code/07_VM-24.md`.

### 10-09 03:3x 사용자 결정, VM-25 trip 4주차 발송 (baseline issue #49)
- 사용자 결정(10-09): ADR-5 = (a) 순수 JS 모듈 유지. 결정이 필요한 질문은 VM 채널로 묻는다. top 세션 `01GaDrpc`가 깊이 5까지 계속 진행.
- VM-25 trip 4주차(가치 모드 F3 + 알려진 빈틈 수정, main `023ee43`에서 `vm/trip-wk4`) 발송. 결과 대기.

### 10-09 03:4x VM-25 trip 4주차 rev 1 불합격 — 수정 항목 하나가 거꾸로 (baseline issue #49)
- rev 1 `540a4ec` (03:44, PR #4): 가치 모드(F3: "1시간의 가치(원)" → `Math.round(값/60)`원/분, 칸 옆에 실제 분당값, 공유 링크에 `costPerHour`),
  결과 비우기 `innerHTML` 제거, `model.test.mjs`의 catch가 `assert.fail`을 삼키지 않게, V7 비용 분해 항목 검사, F8 격차 보고(`docs/F8_gap_report.md`).
  CI run 37826563835 success. 입력 326,813 + 캐시 2,996,189 토큰.
- **top 판정: 불합격.** (a) 지시는 "요청이 없어도 워커 초기화 오류를 보여라"였는데, 3주차에 이미 그 일을 하던 `worker.onerror`의 `else` 가지를 **지웠다**
  (거꾸로). 빈틈이던 `init`의 `'error'` 메시지는 그대로 버려짐. error_test가 최적화를 누른 뒤만 봐서 녹색. (b) V7 분해 검사가 시간값 0에서만 — 시간 가치가 0인 경우.
  (c) 3주차 실제 주소에서 만든 공유 링크(`costPerMinute`)가 0원/분으로 조용히 다시 계산됨.

### 10-09 03:5x VM-25 rev 2 수락, PR #4 병합 → main `704301c` — trip 4주차 닫힘 (baseline issue #49)
- rev 2 `d1fdae0` (03:50): `showError`로 `onerror`와 `init` `'error'` 메시지 모두 요청이 없어도 표시; error_test 시험 2가 **최적화를 누르기 전** 오류를 확인;
  `decodeState`가 옛 `costPerMinute`를 `costPerHour = × 60`으로 변환 + V6 시험; V7 분해 검사를 0과 12,000 둘 다에서.
  CI(VM 보고서 대조): 시간값 0 → 1등 총액 1,065,000, 12,000(200원/분) → 1,171,000, 공유 링크도 1,171,000. → **수락.** 비용: 입력 236,251 + 캐시 2,024,401 토큰.
- **이월:** V7이 더 이상 비용 분해 Sum을 `h4`의 엔진 Total과 비교하지 않는다(3주차에는 했음). 새 검사 `교통 + 숙박 + 시간가치 === Sum`은 모두 페이지가 직접
  계산한 숫자라 화면이 엔진과 다른 분당값을 써도 통과한다. 또 V7의 두 값(0, 12,000)은 60의 배수라 반올림 차이를 드러내지 못한다 → 다음 trip 지시에 Sum == Total
  복원 + 나누어떨어지지 않는 시간값(예: 10,000).
- top이 PR #4 병합 → main `704301c`(03:54, 내용은 `d1fdae0`와 같음). main run 37827950321 engine·web·deploy success
  (`Deploy to GitHub Pages`, `Run Smoke Test Against Deployed URL` 포함, 03:57). **trip 4주차 닫힘.**
- 해설 작성 중 확인: `d1fdae0` 모델 시험 6/6, `540a4ec` 5/5. rev 2의 시험을 rev 1 모델에 돌리면 옛 링크 시험만 실패(`undefined` vs 12000).
- 코드 해설: `code/08_VM-25.md`.
- 배운 점: **수정 항목이 거꾸로 되지 않았는지 본다 — 더한 줄만이 아니라 지운 줄을 읽는다.** (a)는 `+` 줄만 보면 "오류 처리를 손봄"으로 보였다.
  `-` 네 줄이 지시가 지키라고 한 동작이었다. diff의 `-` 줄마다 "의도한 삭제인가"를 지시 항목에 대응시킨다.

### 10-09 03:5x VM-26 BMS 4주차 발송 (baseline issue #50)
- 무엇: main `704301c`에서 `vm/bms-wk4`. CAN(VCU_Cmd 카운터·체크섬, 3회 거부 → 통신 고장, 300 ms 수신 타임아웃, 주기 송신, BMS_Fault 10 ms 내),
  Unity 시험(SWR-015~019, SWR-031, 정상 상태에서 시간 진행), 이월 수정(SWR-010 시험 4251 mV, `bms_config.h` 가드, 이동 평균 정리), cppcheck와 문장 커버리지 관문
  (cppcheck error 0, 커버리지 ≥ 80 %). 결과 대기.

### 10-09 04:1x VM-26 BMS 4주차 rev 1 불합격 — 'declined' 보고였지만 작업은 push돼 있었다 (baseline issue #50)
- rev 1 `2bd9ab6` (04:06, PR #5): 커밋 4개(`043d263` → `2c606f3` → `4861fb6` → `2bd9ab6`). VM 쪽 agy가 작업을 push한 **뒤** 구독 사용량 한도에 걸려
  보고서가 'declined'로 옴. 입력 720,342 + 캐시 8,420,353 토큰.
- top이 보고서 대신 push된 브랜치를 직접 빌드해 검증: CRC-8 SAE J1850(`can/bms.dbc` 주석 그대로), 신호 배치 DBC 일치, Unity 22개, 문장 커버리지 98.7 %
  (top 측정)는 받아들일 만함.
- **top 판정: 불합격.** (a) BMS_Status·BMS_Fault 메시지 카운터가 `bms_step()` 안의 `static` 지역 변수 — 같은 입력으로 새로 `bms_init`한 두 실행이
  40스텝 뒤 카운터 3 대 7(`scratchpad/bmscheck/det.c`). (b) 100 A 방전 중 VCU_Cmd가 400 ms 끊기면 통신 고장 → FAULT → 컨택터 개방. SWR-030(|I| ≤ 5 A가
  3회 연속 샘플 지속된 뒤에만 개방) 위반. (c) 커버리지는 보고만 하고 관문이 없음.
- rev 2 발송: 모든 상태를 `bms_t`로 옮기고 두 인스턴스가 같은 입력에서 바이트까지 같은 CAN 프레임을 내는 시험; 통신 고장은 보고(CommFault, Comm 비트)만
  하고 개방은 SWR-030대로 + `@verifies SWR-030` 시험(100 A 닫힘 유지, 5 A 2샘플 닫힘, 3샘플 열림); `pipeline.sh`에 커버리지 80 % 미만 실패 관문.

### 10-09 05:2x VM-26 rev 2 수락, PR #5 병합 → main `46a0238` — BMS 4주차 관문 (baseline issue #50)
- rev 2 `1bd072d` (05:16): 메시지 카운터·저전류 카운터·컨택터 상태를 `bms_t`로, SWR-030 개방 블록, 커버리지 관문 "Coverage gate: 98.82 % >= 80 %",
  Unity 24개(결정성, SWR-030 추가). 중간 커밋 `771b6e8`(05:13)은 `RUN_TEST` 두 줄이 `main()` 밖 + 결정성 시험 태그 누락으로 CI 실패, 3분 뒤 고침.
- top의 탐침(`scratchpad/bmscheck/c30.c`): 100 A에서 통신 고장 → 컨택터 닫힘 유지, 5 A → 3번째 샘플에 개방, 5.001 A → 열리지 않음, 통신 고장 중 OV →
  3번째 샘플에 개방. `det.c` → 3 대 3. → **수락.** 비용: 입력 434,872 + 캐시 6,142,708 토큰.
- top이 PR #5 병합 → main `46a0238`(05:20, 내용은 `1bd072d`와 같음). main run 37838774420 success.
  **BMS 4주차 관문(cppcheck error 0, statement 커버리지 ≥ 80 %) 닫힘.**
- 해설 작성 중 확인(다음 BMS 지시 후보): (1) VCU_Cmd 카운터를 "마지막으로 **받아들인** 값 + 1"과만 비교해, 프레임 하나만 잃어도 다시 맞추지 못하고 300 ms
  뒤 통신 고장. (2) 이미 고장이 있는 상태에서 새 보호 고장이 서면 BMS_Fault 즉시 송신을 건너뜀(관찰 70 ms, SWR-019는 10 ms). (3) 돌연변이 2개가 24개 시험에서
  살아남음(카운터 15 → 0 순환 삭제, SWR-030 "연속" 리셋 삭제). (4) cppcheck 억제 2개(`unusedFunction`, `missingIncludeSystem`)의 사유를 남길 D8 일탈 기록이
  없음, BMS_Status의 SOC는 50 % 고정값.
- 코드 해설: `code/09_VM-26.md`.
- 배운 점: **'declined' 보고가 '작업 없음'을 뜻하지는 않는다 — 판정 전에 브랜치를 직접 본다.** 보고서는 끊겼어도 커밋과 CI는 남아 있었고, 결함 셋은 모두
  push된 코드를 돌려서 찾았다.
- 배운 점: **agy 사용량 한도가 진행 속도를 정한다.** rev 1 push(04:06)에서 rev 2 첫 커밋(05:13)까지 1시간 넘게 비었다. 지시 하나에 고칠 것을 모아 보내고,
  되돌아오는 횟수를 줄인다.

### 10-09 05:2x VM-27 trip 5주차 발송 (baseline issue #51)
- 무엇: main `46a0238`에서 `vm/trip-wk5`. V5 성능 예산(V = 8, D = 30, 3 모드, K = 5 고정 시드 문제를 엔진 단독과 브라우저 워커 경로에서 각 5회 중앙값,
  `docs/perf.md`에 기록하고 예산 = 측정 중앙값의 2배, 초과 시 CI 실패), V8 Lighthouse(고정 버전, 점수 출력·산출물 저장, 5점 넘게 떨어지면 경고),
  이월 수정(V7 각 계획의 비용 분해 Sum == 엔진 Total을 시간값 0·10,000·12,000에서, error_test에 `init` 'error' 경로, 음수·숫자 아닌 시간값 거부,
  F8 격차 보고는 SPEC 3.3의 시간창 오리엔티어링 목표를 표본 크기·시드를 밝혀 측정). 결과 대기.
