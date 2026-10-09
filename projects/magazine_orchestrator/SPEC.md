# magorch — Magazine Generation Orchestration System · SPEC v0.1

Source: the user's "SYSTEM BUILD DIRECTIVE: Magazine Generation Orchestration System" (10-09, Korean prompt with JSON
examples). This file is the WHAT. Contracts are in `contracts/` (JSON Schema 2020-12, examples in `contracts/examples/`).
Acceptance tests in `tests/` written by the spec side must not be edited by the implementer. User 10-09: the spec side
keeps its spec minimal; from M2 on the VM writes the tests too, against the spec, and the spec side verifies them.
Reference analysis (`dig`): SPEC_DIG.md.

## 0. Who does what (user 10-09: "토큰 절감을 위해 VM과 역할을 분배하여라")

| Party | Does | Never does |
|---|---|---|
| Spec session (Claude, this repo, branch `claude/quirky-cori-7ednzu`) | spec, contracts, acceptance tests, VM directives, verification (reruns the tests itself, reads the diff), merge of accepted work into its branch | write the implementation |
| VM_LOCAL (agy on the Oracle VM; issue channel label `VM`, ids `CMD-MAG<n>`) | the code under `projects/magazine_orchestrator/magorch/`, the agent prompts, fixtures, sample project, README, pushes to `vm/magazine-m<n>` | edit `tests/` or `contracts/`; merge |
| User | creative decisions at approval gates, merges outside this branch | — |

When the implementer finds a contract that is wrong, it reports it in the report (`proposals`); the spec side changes
the contract and the tests in a new revision.

## 1. Implementation plan (increments, each one VM directive, each gated by its tests)

| Milestone | Builds | Gate (spec-side tests) |
|---|---|---|
| **M1 core** | contract validation, artifact store, dependency graph, scheduler (concurrency, retries, timeouts, repair, idempotency, cancellation, persistence), revision propagation, QA-finding routing, lifecycle state machine, event log | spec-side `test_contracts`, `test_store`, `test_dependencies`, `test_failures`, `test_revisions`; VM-written `test_lifecycle` (every row of §4.5 allowed + one refused case each) |
| M2 agents | versioned prompts for 10 roles, provider adapters (scripted fixture, Anthropic Messages, agy CLI: last two labelled unverified until run), brief → editorial ∥ style → design system, research against a recorded source corpus, articles and assets in parallel, orchestrator with approval gates and autonomous mode | `test_agents`, `test_orchestrator` (written after M1 is accepted, against M1's real API) |
| M3 assembly | layout composer (HTML from templates + design tokens), overflow measurement in headless Chromium, PDF renderer, QA editor (all categories in qa_report/1), partial revision loop, publication gate, publication_manifest | `test_layout`, `test_qa`, `test_publication` |
| M4 sample | project `MAG-2026-001` end to end (16 pages, ko, pdf) with every intermediate artifact, a scripted revision cycle, reproduce command, README (install, configure, run, validate, limitations) | `test_sample` |
| M5 ops | provider swap per role, token/cost recording from real provider responses, reproducibility check (re-run from recorded artifacts gives identical hashes for deterministic stages) | `test_reproduce` |

## 2. Directory

```
projects/magazine_orchestrator/
  SPEC.md                 this file (spec side)
  contracts/              *.schema.json + examples/ (spec side)
  tests/                  acceptance tests (spec side), stdlib unittest, run from this directory
  magorch/                the package (VM)
    contracts.py store.py graph.py engine.py lifecycle.py events.py      (M1)
    agents/ providers/ orchestrator.py prompts/                           (M2)
    layout/ render.py qa.py publish.py                                    (M3)
    __main__.py  (CLI)                                                    (M2-M4)
  projects/MAG-2026-001/  sample project (M4)
  README.md               (M4)
```

Runtime: Python 3.10+, stdlib + `jsonschema` (with `referencing`) only for M1. Later milestones may use Jinja2 and
a headless Chromium found at run time (`MAGORCH_CHROMIUM`, else `chromium`, else `/opt/pw-browsers/chromium*`); if no
renderer is found the render step fails honestly (project not published). No network in tests.

Run the gate: `cd projects/magazine_orchestrator && python3 -m unittest discover -s tests -v`.

## 3. Contracts

`common` (shared $defs, `urn:magorch:common:1`), `magazine_project/1`, `creative_brief/1`, `style_specification/1`,
`design_system/1`, `editorial_plan/1`, `agent_task/1`, `agent_result/1`, `artifact_manifest/1`, `qa_report/1`,
`publication_manifest/1`, `orchestration_plan/1`. M2/M3 add `article/1`, `research_dossier/1`, `asset_manifest/1`,
`layout/1` (spec side writes them before the M2/M3 directive).

Every schema's `$id` is `urn:magorch:<name>:<major>`; a document names its contract in its `schema` field
(`"<name>/<major>"`). Rules that matter beyond field shapes:
- `status` (work finished), `validation_status` (schema), `review_status` (content/QA) and `approval_status` (user or
  orchestrator) are separate fields everywhere. Producing an artifact never approves it.
- `confidence` in a style classification is `null` unless `confidence_method` says how it was obtained.
- A failed blocking or major QA check must name `affected_artifact_id`, `recommended_agent`, `recommended_action` and
  `evidence`. `publication_decision: approved` requires `status: passed` and zero blocking issues.
- Creative content carries a reader-facing `fiction_label`; factual content needs research.

## 4. M1 API (what the acceptance tests import)

### 4.1 `magorch.contracts`
- `ContractError(ValueError)` with attribute `errors: list[str]`; each string starts with the JSON path of the error
  (e.g. `$.constraints.max_attempts: ...`).
- `validate(doc, schema=None) -> None` — schema defaults to `doc["schema"]`; unknown or missing schema name raises
  `ContractError`. All schemas in `contracts/` are registered (cross-file `$ref` to `urn:magorch:common:1` resolves).
- `register(name, schema) -> None` — adds an extra contract at run time (`name` like `"note/1"`); used by tests and by
  later milestones. Registering an existing name with a different schema raises `ContractError`.
- `names() -> list[str]` — every registered contract name.

### 4.2 `magorch.store.ArtifactStore(root)`
Append-only, versioned, on disk under `root` (survives a new instance on the same root).
- `put(artifact_id, artifact_type, payload, *, produced_by, inputs=(), media_type="application/json", approval_required=True) -> dict`
  returns `{"artifact_id", "version"}`. Version = previous + 1 (first is 1). If `payload` (a dict) has a `schema`
  key it is validated first and a failure raises `ContractError` and stores nothing. If the payload has
  `artifact_id`/`version` keys they must equal the id and the assigned version (the engine sets them before calling
  put). `payload` may also be `bytes` (rendered files) — then `media_type` is required and no schema check runs.
  `inputs` = list of `{"artifact_id", "version"}`.
- `get(artifact_id, version=None)` — deep copy of the payload (latest when version is None); `KeyError` if absent.
  Mutating the returned object never changes the store.
- `latest_version(artifact_id) -> int | None`.
- `record(artifact_id, version) -> dict` — one `artifact_manifest/1` entry (sha256 of the stored bytes, path relative
  to the project directory = parent of root, produced_by, inputs, validation_status, approval_status, created_at).
- `approve(artifact_id, version, by)` / `reject(artifact_id, version, by, note="")` — approval only; never touches
  the payload. `approval_status(artifact_id, version) -> str` (initially `pending`, or `not_required` when put with
  `approval_required=False`).
- `manifest(project_id) -> dict` — a valid `artifact_manifest/1` with every version of every artifact.
- Stored files are never rewritten; a second write to an existing (id, version) is impossible through the API.

### 4.3 `magorch.engine.Engine(project_dir, agents, *, max_concurrent=4, validators=None, project_id=None)`
The deterministic orchestration core. Agents propose; the engine validates and writes.
- `agents: dict[agent_role, callable]`. An agent is called as `agent(task, inputs)` where `task` is the
  `agent_task/1` document for this attempt (with `attempt`, `status: "running"`, inputs bound to concrete versions,
  and `repair_context` / `revision_notes` when present) and `inputs` maps artifact_id -> deep copy of the payload.
  It returns a dict `{"artifacts": [{"artifact_id", "artifact_type", "payload"}], "issues": [...],
  "unresolved_questions": [...], "provenance": {...partial provenance: model_provider, model_id, prompt_*, tokens}}`.
  Only `artifacts` is required. An exception is a failed attempt.
- `engine.store` — the `ArtifactStore` at `project_dir/artifacts`.
- `add_task(task) -> task_id` — validates `agent_task/1` (raises `ContractError`). Unknown dependency ids raise
  `PlanError` (from `magorch.graph`) at `run()` time at the latest; a dependency cycle raises `PlanError` when the
  task closing the cycle is added. Re-adding an identical task is a no-op; same id with different content raises
  `ContractError`.
- `run() -> dict[task_id, status]` — dispatches every task whose dependencies all `succeeded` (and stale tasks) with
  at most `max_concurrent` agents in flight (threads), until nothing is runnable. Returns when every task is in a
  final or blocked state; it never waits for a timed-out agent thread to finish.
- Input binding: an input ref with `version: null` binds at dispatch to the store's latest version; a missing input
  artifact fails the task without retry (`failure_reason` starts with `missing_input`).
- Output handling per attempt: every returned artifact payload is validated against `output_contract.schema` (after
  the engine sets `artifact_id`/`version` keys when the schema has them); `output_contract.artifact_ids`, when given,
  must equal the returned ids. Invalid output -> nothing stored, the next attempt gets
  `repair_context.errors` (the contract error strings). Exception or invalid output or timeout
  (`constraints.timeout_seconds`, wall clock) counts one attempt; after `max_attempts` the task ends `failed`
  (`timed_out` if the last attempt timed out). A late result from a timed-out attempt is discarded (never stored).
- Task statuses: `pending`, `ready`, `running`, `succeeded`, `failed`, `timed_out`, `blocked` (a dependency ended
  failed/timed_out/cancelled/blocked; the agent is never called), `cancelled`, `stale`.
- `status(task_id)`, `result(task_id)` -> latest `agent_result/1` dict (valid against the contract) or None.
  `result.provenance.input_versions` = the bound inputs; `attempts` = attempts used.
- Idempotency: a task that `succeeded` is not re-run by a later `run()` unless it became `stale`.
  `idempotency_key` = sha256 of (agent_role, objective, output_contract, bound input versions, revision_notes).
- `cancel(task_id)` — pending/ready -> `cancelled`; dependents -> `blocked` on the next `run()`. Cancelling a running
  task discards its result when it arrives.
- Persistence/recovery: task table and results under `project_dir/state/`; `Engine(project_dir, agents)` on the same
  directory restores them; a task found `running` on load becomes `ready` (crash recovery).
- Revision propagation (wave rule): `revise_artifact(artifact_id, payload, *, artifact_type, reason, inputs=())`
  stores a new version with `produced_by = "orchestrator:revision"` and marks `stale` every succeeded task whose
  bound inputs include that artifact at an older version. When a stale task re-runs and stores new output versions,
  its consumers become stale in turn. Consumers of an artifact whose version did not change are not touched.
- `constraints.on_upstream_change`: `rerun` (default) calls the agent again; `revalidate` calls
  `validators[agent_role](task, inputs, previous_result) -> list[str]` instead: empty list -> task `succeeded`
  again with the new input versions recorded and its outputs unchanged (no new versions); non-empty -> the agent is
  re-run with the messages as `repair_context.errors`.
- `route_findings(qa_report) -> list[task_id]` — validates `qa_report/1`; for every failed check with severity
  `blocking`, finds the task whose latest result produced `affected_artifact_id`, appends a `revision_notes` entry
  (`finding_id` = check_id, message, recommended_action, report_id) and marks it `stale`. A task may be revised this
  way at most `constraints.revision_limit` times; one more makes it `failed` with
  `failure_reason` starting `revision_limit` (escalation) and it is not in the returned list. Upstream-change re-runs
  do not count against the limit. Findings whose artifact has no producing task are returned to the caller via
  `engine.unrouted` (list of check ids).
- Events: `project_dir/events.jsonl`, one JSON object per line with `ts`, `event`, and `task_id`/`artifact_id` where
  relevant. Event names at least: `task_added`, `task_dispatched`, `task_succeeded`, `task_failed`, `task_retry`,
  `task_timed_out`, `task_blocked`, `task_cancelled`, `artifact_stored`, `artifact_revised`, `task_stale`,
  `task_revalidated`, `finding_routed`, `escalated`. `engine.events()` returns them as a list.
- Agents never touch the store or the task table; the engine passes deep copies.

### 4.4 `magorch.graph`
`PlanError(ValueError)`; `topological_order(edges: dict[node, list[dep]]) -> list[node]` (deterministic: ties by
name); cycle -> `PlanError` naming the cycle; `descendants(edges, node) -> set`.

### 4.5 `magorch.lifecycle`
`PHASES` = intake, brief_normalization, editorial_planning, style_specification, design_system,
content_and_asset_production, layout_assembly, qa, revision, final_render, published; terminal `failed`, `cancelled`.
`advance(project, to, *, reason="") -> dict` returns a new `magazine_project/1` (input untouched) with `status = to`,
`revision + 1`, and a `history` entry; raises `TransitionError` otherwise. Allowed moves and guards (fields of the
project document):

| to | from | guard |
|---|---|---|
| brief_normalization | intake | — |
| editorial_planning | brief_normalization | creative_brief.approval_status = approved |
| style_specification | editorial_planning | creative_brief approved (style may run in parallel with editorial) |
| design_system | style_specification | style_specification approved |
| content_and_asset_production | design_system | editorial_plan approved and design_system.status = produced |
| layout_assembly | content_and_asset_production, revision | design_system.status = produced |
| qa | layout_assembly | layout.status = produced |
| revision | qa | quality.blocking_issues > 0 and revision_cycles.count < revision_cycles.max; increments count |
| content_and_asset_production | revision | — |
| final_render | qa | quality.blocking_issues = 0 and quality.last_report_id not null |
| published | final_render | publication.status = rendered, quality.publication_approved = true, blocking_issues = 0 |
| failed, cancelled | any non-terminal | — |

Nothing leaves `published`, `failed` or `cancelled`. The result must validate as `magazine_project/1`.

## 5. Later milestones (outline; the spec side details each before its directive)

- Agents (M2): each role = prompt file `magorch/prompts/<role>.md` with front matter `prompt_id`, `version`
  (semver), `output_schema`; the provider gets the prompt, the task JSON and references to inputs (never whole
  project history). Providers: `scripted` (fixture responses keyed by task id and attempt; provenance
  `model_provider: "scripted_fixture"`, `verified: false`), `anthropic` (Messages API over HTTPS, key from
  `ANTHROPIC_API_KEY`), `agy` (CLI). Unverified providers say so in provenance and in the publication manifest.
  Design system architect, layout composer, renderer and the mechanical QA checks are deterministic code.
  Research uses a recorded source corpus (URL, title, publisher, access date, excerpt); a claim is `verified` only if
  its support quote is found in a source excerpt; sources are never invented. Assets record origin
  (`user_provided`, `licensed`, `generated`, `placeholder`); a placeholder is never final and blocks publication.
- Assembly (M3): QA inspects the assembled proof (HTML measured in Chromium: overflow per page, missing assets,
  folios, TOC page numbers vs layout, colours outside tokens, font families over the limit, chart source lines,
  fiction labels on page, claim/source links, repeated words) and the final PDF (page count, text present, file hash).
- Autonomy: `approval_gated` stops at creative_brief, editorial_plan, style_specification and publication
  (`awaiting_approval`); `autonomous` approves them as `orchestrator:autonomous` and records that.

## 6. Acceptance-criteria map (directive §8 -> test)

| Criterion | Test |
|---|---|
| natural-language brief -> valid project | test_orchestrator (M2) |
| style = independent attributes | test_contracts (style schema), test_agents (M2) |
| every dispatched task satisfies its schema | test_dependencies.test_dispatched_tasks_are_valid |
| dependencies prevent premature execution | test_dependencies |
| concurrent independent work | test_dependencies.test_parallel_* |
| invalid results rejected / repaired | test_failures.test_invalid_output_* |
| failed agent never advances to publication | test_failures, test_lifecycle |
| design-token update -> dependent revalidation | test_revisions.test_design_token_update_* |
| QA findings traceable to the artifact | test_revisions.test_route_findings_*, test_contracts (qa rules) |
| final output has no blocking errors | test_publication (M3) |
| reproducible sample | test_sample, test_reproduce (M4, M5) |

## 7. Honesty rules for every milestone

No claim without a test or a command output. Mock and scripted parts are labelled in code, provenance and README.
No invented sources, quotes, statistics or model names; unknown values are `null`.
