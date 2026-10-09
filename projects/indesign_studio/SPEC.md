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
