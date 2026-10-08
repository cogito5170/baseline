# LOCAL-DISPATCHER-1 — a real LOCAL dispatcher on the VM (spec, prose only)

Written by baseline (top `01BofKvz`) 10-08 06:4x KST. User decision 10-08: option 1 (build a real dispatcher).
Hand this to the external model that builds VM tooling. Baseline writes no code (policy `spec_split.no_code_from_baseline`);
this file says WHAT and the checks baseline will run, not how.

## Why

- `/home/ubuntu/poll_mailbox_daemon.py` (task-207) is a mock: line 34 says it does not execute agy. It printed
  "Spawning fresh agy session" and nothing ran. The replies LOC1..LOC5 and LOC3 were written by an interactive agy
  conversation (brain `7b47fe6f…`) that watched that log. When the user closed that conversation (10-08 06:1x KST),
  mail stopped being handled: CMD-LOC7, CMD-LOC8 and CMD-LOC9 in `to/LOCAL/` are unanswered.
- It had no record of handled mail, ran inside an agy task (died with the conversation), and could not measure tokens.
- Goal: mail to `to/LOCAL/` gets answered by a real, separate agy run per directive, with no interactive conversation
  open, surviving logout and restarts, at a predictable token cost per directive.

## What the dispatcher must do

1. **Poll.** Every 30 s fetch branch `ga-mailbox` of cogito5170/baseline into its own checkout (not one the ga bridge
   uses). New work = files in `to/LOCAL/` whose (directive id, rev) has no entry in the handled record (item 6).
   Never read or write `to/AGY/`, `to/claude/`; never sign as AGY.
2. **One real agy run per directive.** For each new directive start a separate non-interactive `agy -p` process.
   - A new directive id starts a fresh agy session.
   - A higher rev of an id already handled resumes the agy session of the earlier rev, if agy can resume a session;
     otherwise a fresh session that is given the earlier rev's reply (item 3).
   - Model rule: Pro for a directive that changes files, branches or the VM (its scope is not "read only"); Flash for
     read-only directives. Record which model ran.
   - Order: directives are taken oldest first; a directive listed in another's `after` field runs first. At most 2 agy
     runs at once (a value in a config file), so a short read-only directive (a ping) is not stuck behind a long one.
   - Per-directive time limit (config, default 30 min). On timeout the run is stopped and still gets a reply (item 4).
3. **What each run is given, in this order** (the fixed part first and byte-identical every time, so the model's prompt
   cache applies):
   a. a fixed instruction file: the LOCAL role, the report/2 format and its rules (copy them from
      `ops/flow/LOCAL_FORMAT.md` on branch `claude/gracious-meitner-vp49xe`), "evidence = the command you ran and what it
      printed", "never paste secrets";
   b. a notes file of lasting VM facts (`~/local_notes.md`: where ga-sdk and the baseline checkouts are, known failing
      tests such as `tests/test_ga38.py::Loop::test_ts_fixture_seeded_bug_fixed`, branch rules). The run may append at most
      a few short lines of new lasting facts at its end; nothing else is carried between directives;
   c. for a rev > 1: the reply to the previous rev; for each id in `after`: that directive's reply;
   d. the directive mail itself, unchanged.
   No other history is given: context continuity comes from (b) and (c), not from a long-running conversation.
4. **Replies.** The reply file `to/baseline/<UTC ts>-LOCAL-<ID>.md` is the agy run's own report/2 output, committed and
   pushed to `ga-mailbox` by the dispatcher. The dispatcher never invents report content. If the run crashed, timed out
   or printed no valid report/2, the dispatcher writes a short report/2 itself with `status: "declined"`, a `reason`
   naming what happened, the exit code and the last lines of the run's output as evidence, and a blocker of kind
   `other`. Every reply must pass `python3 ops/flow/mailcheck.py --report <file>` (on branch
   `claude/gracious-meitner-vp49xe`) before it is pushed; on a push conflict, fetch, rebase the one reply commit, retry.
5. **Tokens.** `results` of every reply carry `model`, `input_tokens`, `output_tokens`, `cached_tokens`, `turns`,
   `seconds` as numbers taken from agy/agv's own usage output or session files (see CMD-LOC7). Only when agy exposes no
   usage at all: JSON `null` (not the string "null"), and the dispatcher's log says which sources it checked.
6. **Handled record.** A file outside the mailbox checkout lists per (id, rev): mail file, start and end time, model,
   agy session id, exit status, reply file. It is written when a run starts (so a restart does not start the same
   directive twice) and updated when it ends. A run that was cut off by a restart is restarted once, then answered as
   declined.
7. **Service.** Runs as a systemd user service (`ga-local.service`), restarts on failure, starts at boot, keeps running
   after the user logs out (lingering on). Stopping or restarting the service must not kill agy runs already in progress,
   or, if it does, item 6 restarts them. Log to a file that rotates. A one-line stop command is written in the log
   header.
8. **Retire the mock.** `poll_mailbox_daemon.py` and the helper scripts `send_loc*.py`, `scratch_report.py`,
   `send_report.py` are no longer used for LOCAL replies (keep or archive them, but nothing runs them).

## Acceptance (baseline checks these from the mailbox and the VM's reply evidence)

- A1 With no interactive agy conversation open, the pending CMD-LOC9 (ping) gets a valid report/2 reply within 3 minutes
  of the service starting; its evidence shows the dispatcher pid and uptime from `systemctl --user status ga-local`.
- A2 CMD-LOC7 and CMD-LOC8 get valid replies (met, unmet or declined — not silence).
- A3 A reply's `results` carry numeric token fields, or the documented reason they are null (item 5).
- A4 `systemctl --user restart ga-local` while a directive is running: that directive still gets exactly one reply, and
  no directive is answered twice (checked by baseline sending two small directives back to back).
- A5 After the user logs out of SSH, a new directive still gets a reply.
- A6 The first reply after go-live lists, in its free text, the paths of the dispatcher, its config, the fixed
  instruction file, the notes file, the handled record and the log.

## Out of scope

The ga bridge (`ga-bridge.service`, `to/AGY/`), ga-hub, ga-console and ga-update stay as they are.
