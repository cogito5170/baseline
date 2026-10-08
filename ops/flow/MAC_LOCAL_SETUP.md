Paste this once into the interactive agy on the user's Mac. It makes the Mac's agy the executor MAC_LOCAL for the
Claude QA session (issue/1, label QA). Do not change anything else on the Mac.

---

Set up MAC_LOCAL (protocol issue/1). Work in ~/mac_local (create it).

1. git clone -q -b claude/gracious-meitner-vp49xe https://github.com/cogito5170/baseline.git ~/mac_local/baseline
   (or fetch it if present). Read ops/flow/ISSUE_PROTOCOL.md and ops/flow/MAC_LOCAL_PROMPT.md there; copy the second to
   ~/mac_local/prompt.md. Copy ops/flow/mailcheck.py to ~/mac_local/mailcheck.py.
2. gh: install if missing (brew install gh) and check `gh auth status` for github.com account cogito5170 (log in if
   needed; never print a token).
3. Find the real agy binary (`type -P agy`, not a shell function) and check how this Mac's agy runs headless:
   agy -p "Reply with exactly: hello" --output-format json --dangerously-skip-permissions must print JSON with status
   SUCCESS. If a tool still asks for approval in -p mode, add an allow rule under permissions.allow in agy's
   settings.json (report which file and rule) — do not rely on a terminal being open.
4. Make a small check script ~/mac_local/check.sh: every run it asks GitHub whether any open issue with label QA changed
   since the last run (gh issue list -R cogito5170/baseline --label QA --state open --json number,updatedAt; compare
   with ~/mac_local/seen); only when something changed, under a lock (no overlapping runs) and a 30 min limit, run
   <agy absolute path> -p "$(cat ~/mac_local/prompt.md)" --model gemini-3.1-pro-high --output-format json
   --dangerously-skip-permissions, appending to ~/mac_local/agent.log; treat JSON with denied_actions, a non-SUCCESS
   status or an empty response as a failed run in the log.
5. Run it every minute with launchd (~/Library/LaunchAgents/com.cogito.maclocal.plist, StartInterval 60, PATH set to
   include the agy and gh directories, RunAtLoad true) and load it with launchctl. The Mac must be awake for it to run.
6. Show: gh auth status (no token), the plist, check.sh, one manual run of check.sh, and launchctl list | grep maclocal.
