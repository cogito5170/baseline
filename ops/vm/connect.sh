#!/usr/bin/env bash
# One-time: make this VM the host for the agy bridge and GA Console, so baseline works through the mailbox alone
# (BD-455, user 2026-10-06: "연결될 수 있는 길 하나만 만들고 나머지는 알아서"). Run on the VM as the login user.
# No sudo, no secret is read or written. Safe to run again: every step is idempotent.
set -uo pipefail
PY="$HOME/ga-venv/bin/python"
step() { printf '\n== %s\n' "$*"; }
die() { printf '\n!! %s\n' "$*"; exit 1; }

step "1/5 ga 갱신 (ga-sdk, baseline 을 앞으로 감기만)"
"$PY" -m ga vm install || die "ga vm install 실패 — 위 출력을 보세요"
"$PY" -m ga vm install --full || echo "(--full 이 남긴 일은 위에 출력됨: PostgreSQL · Token .env — 브리지에는 필요 없음)"

step "2/5 브리지 설정 ~/agy-bridge.json (없을 때만 만듦)"
if [ ! -f "$HOME/agy-bridge.json" ]; then
  cat > "$HOME/agy-bridge.json" <<EOF
{
 "name": "AGY", "hub": "baseline", "every_s": 120, "turn_timeout_s": 1800, "pull": true,
 "mailbox_repo": "$HOME/baseline", "workdir": "$HOME/token",
 "act": {"repo": "$HOME/token", "backend": "agv", "model": "gpt-oss-120b-medium",
         "options": {"agent": "ga-act"}, "max_turns": 10, "timeout_s": 3600}
}
EOF
  echo "만듦: $HOME/agy-bridge.json"
else
  echo "이미 있음 (그대로 둠)"
fi

step "3/5 GitHub push 권한 (브리지가 답장을 push 함)"
if ! git -C "$HOME/baseline" push --dry-run origin HEAD:refs/heads/ga-push-probe >/dev/null 2>&1; then
  die "push 권한이 없습니다. 직접 한 번: sudo apt install -y gh && gh auth login && gh auth setup-git  — 그 다음 이 스크립트를 다시 실행"
fi
echo "push OK"

step "4/5 Mac 브리지에서 넘겨받기 (Mac 브리지는 꺼 두세요: 둘이 켜져 있으면 같은 지시를 두 번 합니다)"
"$PY" -m ga vm bridge-adopt || die "bridge-adopt 실패"
"$PY" -m ga vm enable-bridge --yes || die "enable-bridge 실패 — 위 출력을 보세요"

step "5/5 상태"
"$PY" -m ga vm status
systemctl --user --no-pager status ga-bridge 2>&1 | head -6
echo
echo "끝. 이제 baseline 이 우편함으로 이 VM 의 브리지에 일을 보냅니다. 이 창은 닫아도 됩니다."
