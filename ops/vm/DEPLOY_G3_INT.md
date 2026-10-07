# VM 배포: 그룹 3 통합 (vm/G3-INT)

- 코드: `cogito5170/ga-sdk` 브랜치 `vm/G3-INT` = `222ca6a` = 통합 `0547772`(그룹 2, VM 배포 중) 위에 VM이 ga act로 만든 3개 (충돌 없음, ff 가능):
  - VI-04b `5613211` (CMD-VIB4 rev 2): 그림자 허브 판단 = `ga verdict` (모델 호출 0; 비그림자 허브는 그대로)
  - VI-10a `8a4eac4` (CMD-VIJ10 rev 2): journal/1 형식(레지스트리) + `ga/vm/journal.py` fold
  - VI-10b `222ca6a` (CMD-VIM10): `ga/vm/machine.py` 상태 기계 T1-T11 (그림자, 세션 없음, T2-T4는 would_do)
- 작업 모델 전부 gemini-3.7-flash-medium (policy spec_split). baseline 시험·기존 시험 수정본 5개·registry.json은 원본과 바이트 동일.
- 시험 (클라우드, 10-07 14:1x KST, pytest): 전체 1484 passed / 56 skipped / 실패 0 (그룹 2 1452 + 그룹 3 32). 의존성 핀 변경 없음.
- 아직 어떤 서비스에도 연결 안 됨: journal/machine은 코드만, 그림자 허브는 다음 tick부터 모델 대신 ga verdict로 판단.

## VM에서 (VM에 ssh 접속한 뒤)

```bash
cd ~/ga-sdk && test -z "$(git status --short)" && git log -1 --oneline \
 && git branch -f vm/deployed-before-g3int HEAD \
 && git fetch origin vm/G3-INT \
 && git checkout -B claude/gracious-meitner-vp49xe origin/vm/G3-INT \
 && git log -1 --oneline \
 && ~/ga-venv/bin/python -m pytest -q -p no:cacheprovider tests/test_vi04b_shadow_verdict.py tests/test_vi10a_journal.py tests/test_vi10b_machine.py tests/test_ga42_shadow.py tests/test_verdict.py tests/test_forms.py tests/test_vm_bridge_act.py \
 && git push origin HEAD:claude/gracious-meitner-vp49xe \
 && systemctl --user restart ga-bridge ga-console \
 && systemctl --user status ga-bridge --no-pager | head -3 \
 || echo "STOPPED: 위 마지막 출력을 붙여 주세요"
```

기대: 첫 `git log` `0547772`, 두 번째 `222ca6a`, pytest 실패 0.
되돌리기: `git checkout -B claude/gracious-meitner-vp49xe vm/deployed-before-g3int && systemctl --user restart ga-bridge ga-console`
