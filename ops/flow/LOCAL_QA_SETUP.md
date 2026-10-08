Paste this once into the interactive agy on the VM (it switches LOCAL from the mailbox to QA issues).

---

Set up LOCAL to talk to the Claude QA session over GitHub issues (protocol qa/1). Do not change anything else.

1. Read: git -C ~/ld-fix fetch -q origin claude/gracious-meitner-vp49xe, then git show of
   ops/flow/QA_PROTOCOL.md and ops/flow/LOCAL_QA_PROMPT.md on that branch. Save the second to ~/local_qa_prompt.md.
2. GitHub API access for posting comments and labels on cogito5170/baseline: check `gh auth status`. If gh is missing
   or logged out, use the token git already uses for pushing (git credential fill for github.com) to log gh in
   (gh auth login --with-token), or install gh first. Show `gh auth status` (no token in the output).
3. Make sure the labels exist: QA, qa:todo, qa:doing, qa:review, qa:blocked, qa:done (create missing ones).
4. Replace the LOCAL cron line (the one using ~/local_agent_prompt.md) with one that, every minute, asks GitHub whether
   any open issue with label QA changed since the last check (a cheap request, ETag or updated_at; no agy call when
   nothing changed) and only then runs, under the same flock, timeout and wrapper as now:
   ~/auto-agy-p.exp -p "$(cat ~/local_qa_prompt.md)" --model gemini-3.1-pro-high --output-format json
   --dangerously-skip-permissions, appending to ~/local_agent.log. Keep PATH at the top of the crontab. No % characters
   in the crontab line (cron treats % as a newline); put the check in a small script file if needed.
5. Keep the old mailbox cron line commented out (not deleted) until CMD-LOC10 has its reply in ga-mailbox; then
   delete it.
6. Show: crontab -l, the check script, and the first log lines after a manual run of the check.
