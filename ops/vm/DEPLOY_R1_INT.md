# VM 배포: 그룹 1 통합 (vm/R1-INT)

- 사용자 결정 (10-07 10:5x KST): 다음 작업 = 그룹 1 통합 (`research/VM_INTERIOR_DESIGN.md` §12).
- 코드: `cogito5170/ga-sdk` 브랜치 `vm/R1-INT` = `19dc227` = `vm/BRIDGE-ACT-1`(`d314c95`) + ACCEPT 4개 병합(충돌 없음):
  - VI-06a + VI-20 `87e3243` (notify/1 `alert`, bridge unit = `ga bridge`)
  - VI-01 `bb443ff` (VM이 ga-sdk SHA를 바뀔 때·물을 때 보고, R0 시험 결과)
  - VI-02 `3e7ab1c` (`ga/llm` 게이트웨이 핵심: 상한·원장·정지; 아직 호출 지점에 연결 안 됨 = VI-03)
  - VI-04 `451e980` (`ga verdict --dry-run`, 재현 2/70 일치)
- 시험 (클라우드, 10-07 11:0x KST): 전체 1431 passed / 53 skipped / 실패 0 (`318b22a` 1363 + 브리지 15 + 그룹 1 53). 의존성 핀 변경 없음(pip 재설치 불필요).
- VM 로컬 수정(`vm/local-wip-1007`, 10-06 17:53~18:47Z)은 그룹 1과 같은 파일 12개를 고쳤다(ga/llm/gateway.py, ga/verdict.py, act/loop, act/route, gemini, hub, intake/engine, net/node, plan/draft, vm/core, __main__, ga/llm/__init__). 검토·시험 안 된 수작업이라 실행 코드는 `vm/R1-INT`로 바꾸고 로컬 수정은 이름표로만 남긴다(삭제 아님).

## VM에서

```bash
cd ~/ga-sdk
git status --short                                    # 출력이 없어야 함 (있으면 멈추고 알려 주세요)
git branch -f vm/deployed-before-r1int HEAD           # 지금 돌고 있는 상태 보관 (로컬 수정 + 브리지)
git fetch origin vm/R1-INT
git checkout -B claude/gracious-meitner-vp49xe origin/vm/R1-INT
git log -1 --oneline                                  # 19dc227 Merge ... DEV-R2-DRY ...
~/ga-venv/bin/python -m unittest tests.test_vm_bridge_act tests.test_vm_bridge_model tests.test_ga36_bridge tests.test_r1_gateway tests.test_verdict tests.test_vmsha 2>&1 | tail -3
git push origin HEAD:claude/gracious-meitner-vp49xe   # 통합 브랜치를 맞춤 → 이후 ga-update 자동 갱신 재개. 거부되면 건너뛰고 알려 주세요
systemctl --user restart ga-bridge ga-console
systemctl --user status ga-bridge --no-pager | head -3
```

되돌리기: `git checkout -B claude/gracious-meitner-vp49xe vm/deployed-before-r1int && systemctl --user restart ga-bridge ga-console`

## 배포 뒤 확인 (baseline이 우편함으로)

1. CMD-PING 형식의 읽기 전용 지시 → 회신 met (브리지 정상).
2. VI-01: VM이 새 SHA(`19dc227`)를 notify/1로 알리는지(ga-update 다음 실행 때) — 우편함 확인.
