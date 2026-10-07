# CMD-ACTB1: ga bridge: per-directive max_turns and a ## turns section in the report

You are working in a git worktree of cogito5170/ga-sdk (base vm/G4-INT = c6f3f97). This is a prose spec from baseline
(policy spec_split.no_code_from_baseline): you design and write the code yourself.

## Goal
The bridge's code-work path should let each directive set the ga act turn cap and should mail back the per-turn trace. Rules B1-B3 in the docstring of tests/test_bridge_act_turns.py: B1 the ga-act block may carry max_turns, an int 1-30 (else item_spec raises ValueError), passed to ga act as --max-turns. B2 without it: the config's act.max_turns, else 20. B3 report() adds a '## turns' section after '## ga act result' with one line per trace row in the given form, cut to 4000 characters; no trace, no section; the report/2 head is unchanged. Where things are: ga/bridge/act.py (SPEC_KEYS, item_spec, act_argv, report).

The full rules are the docstring of `tests/test_bridge_act_turns.py` (baseline's acceptance test). Read it first, then read the files you need.

## Rules
- Edit only: ga/bridge/act.py.
- Do not edit, rename or delete any test file. `tests/test_bridge_act_turns.py` is baseline's and must stay byte-identical.
- Keep every existing test green.

## Done when
This command, run from the worktree root, passes with 0 failures:

    ~/ga-venv/bin/python -m pytest -q -p no:cacheprovider tests/test_bridge_act_turns.py tests/test_vm_bridge_act.py

Run it yourself, read the failures, fix, and repeat until it passes. Then stop and print a short summary
(files changed, what each change does, the final test line). Do not commit or push; the operator does that.
