# LOCAL-DISPATCHER-1 — baseline review of build b3fa20d (branch vm/local-dispatcher), 10-08 KST

Verdict: **do not install yet.** Read by baseline against LOCAL-DISPATCHER-1.md. Fix the blocking items, push to the same
branch, baseline re-reads before install. Prose only (baseline writes no code).

## Blocking (installing as is would do damage or answer nothing)

B1 **Replays every old directive.** The handled record starts empty and the mail's id/rev are looked for as
   "Directive ID:" / "Rev:" lines, which no mail has. The head is the JSON object in the first ```ga block
   (`id`, `rev`, `after`). On first start all 8 mails in to/LOCAL/ (LOC1..LOC9, incl. LOC3's merge into vm/ACT1-INT)
   would be run again. Read id/rev/after from the ga block; on first start treat a directive as handled when
   to/baseline/ already holds a LOCAL reply whose `handled` names that id and rev.
B2 **rev is always 1**, so a rev 2 mail of an id is never run (its key equals rev 1's). Follows from B1.
B3 **Every reply would be declined:** mailcheck is run as ops/flow/mailcheck.py inside the ga-mailbox checkout, but
   ga-mailbox holds only to/. Take mailcheck.py (and the nocode.py it imports, if any) from branch
   claude/gracious-meitner-vp49xe, refreshed on each poll.
B4 **The fallback reply is not valid report/2 and can be invalid JSON:** reason/stdout text is pasted into the JSON
   unescaped (quotes, newlines from mailcheck output); `items` is empty though each done_when id needs an entry (state
   `na` is fine); `results` is empty though model/tokens/turns/seconds are required. Build it as data and serialize, then
   run mailcheck on it too.
B5 **Model is never passed to agy.** "Pro"/"Flash" is only a label; `agy -p` runs with its default. And the read-only
   test matches words like "change", "git", "write" — "read only: change nothing" contains "change" — so every mail
   counts as Pro. Decide from the head's `scope` (a scope text starting "read only") and pass the model with agy's own
   model option (check `agy --help` on the VM).
B6 **agy invocation unverified:** the prompt is piped on stdin to `agy -p` with a comment "I don't know agy exact flags".
   Check on the VM how agy -p takes its prompt and run one real directive by hand before the service is enabled.

## Must fix (spec items not met)

M1 Not concurrent: the two directives of a poll run one after the other and polling stops while agy runs, so a ping
   waits behind a 30-min job (spec 2: at most 2 at once).
M2 Reply text is the whole stdout; report/2 must start with the ga block. Cut what precedes it.
M3 Lost replies: each poll hard-resets the checkout to origin; a reply commit whose push failed 3 times is wiped while
   the record says done. Keep it marked "unpushed" and retry; record the reply file name.
M4 No token numbers at all (spec 5, CMD-LOC7): read usage from agy/agv output or session files; if none, JSON null +
   logged list of places checked.
M5 Context: no previous-rev reply, no `after` replies, no session resume, notes file never appended (spec 2, 3).
M6 Handled record lacks the agy session id and reply file (spec 6). Order uses file mtime, which is equal after a clone;
   use the UTC timestamp in the file name, and honour `after`.
M7 Service: Restart=on-failure (spec says restart always), log never rotates, stop line repeats on every start.
M8 install.sh needs `loginctl enable-linger` to succeed without sudo, or say so; it must only run on the VM (it ran on
   the Mac by mistake and failed harmlessly at mkdir /home/ubuntu).

## Acceptance stays A1..A6 of LOCAL-DISPATCHER-1.md.
