# CMD-ACTR1: ga act: kept reads, outline for long files, per-turn trace in act/1

You are working in a git worktree of cogito5170/ga-sdk (base vm/G4-INT = c6f3f97). This is a prose spec from baseline
(policy spec_split.no_code_from_baseline): you design and write the code yourself.

## Goal
ga act should let a cheap model work inside a large file. Three changes, rules R1-R3 in the docstring of tests/test_act_reads.py: R1 NEED results stay in the card on every later turn of the item (today Act keeps them for the next card only), re-served from the current files, dropped oldest first when the card is over its cap, at most 8. R2 NEED file on a file over 150 lines without 'lines a-b' answers with an outline (names of top-level defs/classes and methods with their line numbers) plus a hint to ask for lines. R3 Result.to_dict adds 'trace', one row per model turn (turn, card_tokens, actions as '<KIND> <arg>', applied, rejected, dropped). Where things are: class Act in ga/act/loop.py (units, _act, _run, Result), ga/act/retrieve.py (file_slice, symbol), ga/act/card.py (build, the drop order).

The full rules are the docstring of `tests/test_act_reads.py` (baseline's acceptance test). Read it first, then read the files you need.

## Rules
- Edit only: ga/act/loop.py, ga/act/retrieve.py, ga/act/card.py.
- Do not edit, rename or delete any test file. `tests/test_act_reads.py` is baseline's and must stay byte-identical.
- Keep every existing test green.

## Done when
This command, run from the worktree root, passes with 0 failures:

    ~/ga-venv/bin/python -m pytest -q -p no:cacheprovider tests/test_act_reads.py tests/test_ga38.py tests/test_ga41.py tests/test_ga45.py tests/test_ga47.py tests/test_act_isolation.py --deselect tests/test_ga38.py::Loop::test_ts_fixture_seeded_bug_fixed

Run it yourself, read the failures, fix, and repeat until it passes. Then stop and print a short summary
(files changed, what each change does, the final test line). Do not commit or push; the operator does that.
