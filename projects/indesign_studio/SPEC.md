# AI Magazine Studio for Adobe InDesign — minimal spec v0.1

Source: user 10-09 "Task: Implement AI Magazine Studio for Adobe InDesign" (6 phases). Spec side = Claude session
(branch `claude/quirky-cori-7ednzu`); implementation and its tests = VM_LOCAL (alternating Claude / Gemini models).
Location: `projects/indesign_studio/` — `orchestrator/` (Python service), `plugin/` (UXP panel), `contracts/`,
`docs/CAPABILITIES.md`, `tests/`.

## Hard limits (true for every milestone)
- Neither the VM nor the cloud has InDesign. Real DOM behaviour is checked only on the user's machine (a
  `[USER-TASK]` issue). Until then every DOM operation is `documented_unverified`; mocked tests never count as InDesign
  verification.
- No model-generated JavaScript or code is ever executed. The plugin maps a closed set of operation names to fixed
  adapter functions.
- Every API method used must cite its page on developer.adobe.com (UXP for InDesign / InDesign DOM reference). No
  invented methods; an operation without a documented method is `unsupported` and is not implemented.

## Contracts (2020-12, `$id urn:ids:<name>:1`; examples for each)
- `envelope/1`: schema_version, message_id (uuid), job_id, correlation_id, timestamp, status
  (`ok|error|pending`), errors[{code, message, path}], payload_schema, payload.
- `creative_brief/1` (studio's own, separate namespace from magorch), `indesign_edit_spec/1`,
  `indesign_validation_report/1`, `indesign_revision_plan/1`.
- `indesign_edit_spec/1`: `document {document_id, expected_revision}`, `operations[]` each
  `{op_id, op, page_index, ...op fields}`, closed `op` enum. Slice 1: `create_text_frame {bounds_pt [top, left,
  bottom, right] inside the page, text, paragraph_style|null}`. Later: `add_page`, `place_image {asset_id}`,
  `set_text`, `apply_style`, `move_item`. Any op touching existing items needs `content_change_authorized: true`
  to change content. Rejected before mutation: unknown op, extra fields, bounds outside the page or inverted,
  missing fields, asset id not in the asset registry, `expected_revision` != current document revision.
- `indesign_validation_report/1`: structural findings (overflow, missing link, off-page, overlap) and visual findings
  (critic) in separate lists, each with op_id or item id, severity, evidence.
- `indesign_revision_plan/1`: minimal list of new operations with `fixes: [finding ids]`, round number (max 3).

## Orchestrator modules (Python, stdlib + jsonschema)
creative_director (2-3 directions), editorial_designer, spec_compiler, layout_critic, revision_planner,
job_state (persistent, recoverable, operation ids applied exactly once), validation_engine, telemetry (jsonl).
Models via a provider adapter; tests use fakes. Workflow states: requested -> directions -> selected -> compiled ->
validated -> applied -> inspected -> (revision rounds <= 3) -> awaiting_approval -> approved -> exported, or
needs_human_review / rejected / export_failed. Export only after explicit user approval.

## Plugin (UXP)
Panel: connection status, active document summary, spec preview, Apply / Inspect / Revise / Approve / Reject / Export,
operation log, structured errors. Talks to the orchestrator on `http://localhost:<port>` only; manifest declares only
that network domain and no file-system permission beyond what export needs. Document revision = a counter the
adapter keeps in a document label (verify the label API in the docs first; if undocumented, say so).

## Milestones
- IDS-1 vertical slice: CAPABILITIES.md (version matrix + each needed operation: document access, page creation, text
  frame, image placement, overflow, save, PDF export -> doc URL + status), contracts + examples, spec_compiler +
  validation_engine + job_state + a Python mock adapter for `create_text_frame` + inspect report, plugin manifest and
  panel with `create_text_frame` and inspect (unverified), tests: valid/invalid spec, stale revision, duplicate
  op delivery, network failure retry, overflow on the mock, approval gating, export failure.
- IDS-2 images + multi-page + revision loop + export; IDS-3 real InDesign run by the user (USER-TASK), then regression
  tests on the user's existing documents.

## Integration routes (user 10-09 07:0x KST; sources found by the user's `dig` run)

The studio does not drive InDesign itself in the first release. It plugs into one of two existing bridges on the
user's machine and keeps its own role: brief -> candidates -> `indesign_edit_spec/1` -> validation -> report -> approval.
None of the sources below could be opened from the cloud (proxy policy blocks sidekick.eastpole.nl and
helpx.adobe.com; github.com web 403), so every claim about them is **unverified** until checked on the user's machine.

| Route | Bridge (as reported) | Use | Status |
|---|---|---|---|
| A (default) | Sidekick for InDesign: UXP panel (InDesign 2024+) + MCP server `indesign-sidekick` (npx, Node 20+), local only | interactive layout, styles, overset check, screenshots for review | unverified |
| B (batch) | Claude Code + `indd` skill (mindboard/indesign-extendscript-plugins), ExtendScript | many documents from content.md + layout image + todo.md | unverified; conflicts with the no-generated-code rule |
| C (reference) | InDesign built-in AI Assistant (reported as beta, June 2026) | none; not scriptable from outside as far as reported | unverified |

Rules for route A:
- The orchestrator runs as a Claude Code (or Claude Desktop) session with the Sidekick MCP server attached. The
  `sidekick adapter` maps each allowed op of `indesign_edit_spec/1` to exactly one Sidekick MCP tool. The mapping table
  is filled from the server's real `tools/list` output, captured on the user's machine (USER-TASK), never from memory.
- Any Sidekick tool that runs arbitrary script text is excluded from the allow-list.
- After each op batch: inspect (page count, frames, overset text, missing links) -> `indesign_validation_report/1`;
  at most 3 revision rounds; export only after the user approves in the panel or chat.
- Work on a copy of the user's document (`<name>.studio.indd`); the original is never written.

Rules for route B: the `indd` skill makes the model write ExtendScript, which this spec forbids (Hard limits). Default:
route B uses a fixed, reviewed `.jsx` library (one function per allowed op, JSON parameters, run through InDesign's
script runner) instead of the skill. The skill can run as-is only if the user waives the rule for batch mode in
writing, and then only on document copies.

Model ids: the `claude --model claude-3-7-sonnet` line in the source material is out of date; use the current model
chosen in the session (no model id hard-coded in the studio).

Candidates: `../magazine_orchestrator/candidates/MAG-CANDIDATES-001.json` holds 7 magazine candidates, each with a
valid `creative_brief/1`, a target feature profile (SPEC_DIG taxonomy), a style direction and the InDesign document setup
(page, grid, paragraph styles, parent pages) that route A or B creates first.
