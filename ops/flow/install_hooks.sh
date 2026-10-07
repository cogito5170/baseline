#!/bin/sh
# Installs the no-code gate and the directive/2 form gate (ops/flow/mailcheck.py) (policy spec_split.no_code_from_baseline) as git hooks of this clone. The hooks are shared
# by every worktree of the clone, including the ga-mailbox worktree: a commit that adds/changes to/AGY/*.md mail
# carrying code (edit lists, code in goals, non-test files) is refused. Run once per new container (BASELINE_TOP start).
set -e
root=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
hooks=$(cd "$root" && cd "$(git rev-parse --git-common-dir)" && pwd)/hooks
cat > "$hooks/pre-commit" <<HOOK
#!/bin/sh
files=\$(git diff --cached --name-only --diff-filter=AM -- 'to/AGY/*.md')
[ -z "\$files" ] && exit 0
tmp=\$(mktemp -d); rc=0
for f in \$files; do git show ":\$f" > "\$tmp/\$(basename "\$f")"; done
python3 "$root/ops/flow/nocode.py" "\$tmp"/*.md || { rc=1; echo "BLOCKED by ops/flow/nocode.py: baseline sends no code (policy spec_split.no_code_from_baseline)" >&2; }
python3 "$root/ops/flow/mailcheck.py" "\$tmp"/*.md || { rc=1; echo "BLOCKED by ops/flow/mailcheck.py: directive/2 form (the VM would decline it)" >&2; }
rm -rf "\$tmp"
exit \$rc
HOOK
chmod +x "$hooks/pre-commit"
echo "installed $hooks/pre-commit"
