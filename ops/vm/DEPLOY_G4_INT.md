# VM 배포: ISO-1 + 그룹 4 통합 (vm/G4-INT)

- 코드: `cogito5170/ga-sdk` 브랜치 `vm/G4-INT` = `c6f3f97` = 통합 `222ca6a`(그룹 3, VM 배포 중) 위에 VM이 ga act로 만든 5개 (충돌 없음, ff 가능):
  - ISO-1 `cec66f2` (CMD-ISO1 rev 2): ga act 시험 격리 (`GA_ACT_ISOLATE`: 작업 폴더에 없는 ga 모듈을 배포본에서 불러오지 않음)
  - VI-11a `eaf5c67` (CMD-VIR11): `ga/vm/ops_rules.py` rule/1 O1 O2 O4 O7 + action-spec/1 + Guard (순수 코드)
  - VI-11b `256566d` (CMD-VIV11): `ga/vm/ops_verify.py` VERIFY (window_ms 안 postcondition, 한 단계 위, 두 번 = BLOCKED)
  - VI-12 `310bd04` (CMD-VID12): `ga/vm/dora.py` journal에서 DORA 지표 + slo.json 검사(파일 없으면 생략)
  - VI-11c `c6f3f97` (CMD-VIT11): `ga ops tick` (그림자: 관찰 → 규칙 → Guard → VERIFY → 알림 파일; 메일 없음, 모델 0, 세션 없음)
- 작업 모델 전부 gemini-3.7-flash-medium, 각 1턴 (1,707~4,434 토큰). baseline 시험 5개는 원본과 바이트 동일, VIT11 결과는 baseline 증명 트리와 동일.
- 시험 (클라우드, 10-07 KST, pytest): 전체 __SUITE__. 의존성 핀 변경 없음.
- 아직 어떤 서비스에도 연결 안 됨: `ga ops tick`은 수동 실행 명령만 추가(타이머 없음).

## VM에서 (VM에 ssh 접속한 뒤)

```bash
cd ~/ga-sdk && test -z "$(git status --short)" && git log -1 --oneline \
 && git branch -f vm/deployed-before-g4int HEAD \
 && git fetch origin vm/G4-INT \
 && git checkout -B claude/gracious-meitner-vp49xe origin/vm/G4-INT \
 && git log -1 --oneline \
 && ~/ga-venv/bin/python -m pytest -q -p no:cacheprovider tests/test_act_isolation.py tests/test_vi11a_rules.py tests/test_vi11b_verify.py tests/test_vi11c_tick.py tests/test_vi12_dora.py tests/test_vi04b_shadow_verdict.py tests/test_vi10a_journal.py tests/test_vi10b_machine.py tests/test_forms.py tests/test_vm_bridge_act.py \
 && git push origin HEAD:claude/gracious-meitner-vp49xe \
 && systemctl --user restart ga-bridge ga-console \
 && systemctl --user status ga-bridge --no-pager | head -3 \
 || echo "STOPPED: 위 마지막 출력을 붙여 주세요"
```

기대: 첫 `git log` `222ca6a`, 두 번째 `c6f3f97`, pytest 실패 0.
되돌리기: `git checkout -B claude/gracious-meitner-vp49xe vm/deployed-before-g4int && systemctl --user restart ga-bridge ga-console`
