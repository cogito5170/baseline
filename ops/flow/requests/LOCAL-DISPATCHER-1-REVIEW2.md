# LOCAL-DISPATCHER-1 — baseline review 2 of build 4d74a97 (branch vm/local-dispatcher), 10-08 KST

Verdict: **still do not install.** B1–B4 and the agy call (B6) are fixed, and the first-start seeding was checked against
the real mailbox: it marks LOC1–LOC5 handled and leaves LOC7, LOC8, LOC9 pending, as intended. But as written, no
directive would ever reach agy. Prose only (baseline writes no code).

## Blocking

R1 **Every directive crashes before agy runs.** In directive/2 the head's `scope` is a list of objects
   (`[{"id": "S1", "text": "read only: change nothing"}]`), not a string; the read-only test calls a string method
   on it. The exception happens inside the worker thread and is never logged (the future's result is never read), the
   record stays "running", the next poll restarts it once, it crashes again, and the third poll answers it "declined:
   cut off by restart". Result: LOC7/8/9 all declined, agy never called. Read the read-only flag from the first scope
   item's `text`; log every worker exception and answer that directive declined with the traceback tail.
R2 **Double answers after a restart.** The "running and already restarted once → answer declined" branch does not check
   whether that directive is running right now in this process. After a service restart the re-run directive is
   "running, restarts 1" for its whole run, so the next poll writes a declined reply while agy is still working, and
   agy's real reply follows: two replies for one directive (fails A4). Only directives not active in this process may be
   treated as cut off.

## Must fix

R3 **Code lands in the mailbox branch.** Checking mailcheck.py / nocode.py out of the other branch into the ga-mailbox
   checkout stages them, and the next reply commit pushes ops/flow/*.py into ga-mailbox. Keep those two files outside
   the mailbox checkout (or out of the index) so a reply commit holds only its reply file.
R4 **"unpushed" is still lost (M3).** The next poll hard-resets the checkout to origin, which deletes the unpushed
   reply commit and its file; the retry then finds no file and the directive stays "unpushed" for ever. Keep a copy of
   the reply outside the checkout and re-commit it from there. A failed rebase must abort the rebase, not raise out of
   the thread.
R5 **results shape.** LOCAL_FORMAT.md defines `results` as a list of `{"name": ..., "value": ...}` with names `model`,
   `input_tokens`, `output_tokens`, `cached_tokens`, `turns`, `seconds`; the build writes one object with keys
   `tokens_in`/`tokens_out` and no cached tokens, and the fallback writes the string "None" as model. baseline's token
   ledger reads only the defined shape. Fallback `items` must use the directive's done_when ids (D1, D2, …), not the
   directive id.
R6 **Related-reply lookup is a filename substring:** for rev > 1 of CMD-LOC1 it also attaches every CMD-LOC1x reply.
   Match the reply's `handled[].id` exactly (and for rev > 1 only that id's earlier revs).

## Before saying it is ready

Run the dispatcher itself (not only agy) once by hand on the VM against the real mailbox in a dry mode that runs agy but
does not push, and show for CMD-LOC9: the model chosen, the agy command line (prompt elided), the reply text it would
push, and `mailcheck.py --report` on it. Then install.
