# VM 배포: 그룹 2 통합 (vm/G2-INT)

- 코드: `cogito5170/ga-sdk` 브랜치 `vm/G2-INT` = `0547772` = 통합 `19dc227`(그룹 1, VM 배포 중) + VM이 ga act로 만든 4개 병합(충돌 없음, ff 가능):
  - VI-03 `5eed06e` (CMD-VI3 rev 2: `ga/llm/sites.json`, 모델 호출 지점 8곳의 "규칙으로 안 되는 이유" 표)
  - VI-07 `c7be8cb` (`ga llm report --status` → status/1)
  - VI-06 `5363e91` (`ga/forms/registry.json`·`registry.py`, kinds.py 열거값을 레지스트리에서 읽음, `docs/FORMS.md` 생성)
  - VI-05 `dfd5bb1` (CMD-VI5 rev 2: `ga/watch.py` 감시 핵심 — 규칙·임계값·하루 한 번 알림, 모델 호출 0)
- baseline 수용 시험 4개는 VM 모델이 고치지 않았음(baseline 원본과 바이트 동일). registry.json도 baseline 제공본 그대로.
- 시험 (클라우드, 10-07 12:1x KST, pytest): 전체 1452 passed / 56 skipped / 실패 0 (그룹 1 1431 + 그룹 2 21). 의존성 핀 변경 없음.
- `ga/watch.py`는 아직 어떤 서비스·타이머에도 연결되지 않음 (그룹 3 이후).

## VM에서

```bash
cd ~/ga-sdk
git status --short                                    # 출력이 없어야 함 (있으면 멈추고 알려 주세요)
git branch -f vm/deployed-before-g2int HEAD           # 지금 상태 보관 (19dc227 이어야 함)
git fetch origin vm/G2-INT
git checkout -B claude/gracious-meitner-vp49xe origin/vm/G2-INT
git log -1 --oneline                                  # 0547772 Merge ... agv/CMD-VI5-r2 ...
~/ga-venv/bin/python -m pytest -q -p no:cacheprovider tests/test_vi03_sites.py tests/test_vi05_watch.py tests/test_vi06_registry.py tests/test_vi07_status.py tests/test_forms.py tests/test_r1_gateway.py tests/test_vm_bridge_act.py 2>&1 | tail -3
git push origin HEAD:claude/gracious-meitner-vp49xe   # ff. 거부되면 건너뛰고 알려 주세요
systemctl --user restart ga-bridge ga-console
systemctl --user status ga-bridge --no-pager | head -3
```

되돌리기: `git checkout -B claude/gracious-meitner-vp49xe vm/deployed-before-g2int && systemctl --user restart ga-bridge ga-console`

## 배포 뒤 확인 (baseline이 우편함으로)

1. 읽기 전용 지시 1건 → met (브리지 정상, 새 kinds.py가 레지스트리에서 열거값을 읽어도 형식 검사 정상).
2. `ga llm report --status` 결과를 회신에 담게 하는 지시 1건 (VI-07 동작 확인).
