# magorch reference analysis — `dig` dump -> MagazineFeatureProfile · minimal spec v0.1

Source: user 10-09 message ("dig 기반 매거진 특징 추출 파이프라인", taxonomy, draft-07 schema, system prompt).
Purpose in magorch: turn existing magazines (web pages) into machine-readable profiles that the style taxonomist
cites as `reference_publications` (a magazine name alone is never a design spec). VM writes code AND tests.

## Contracts (VM writes both, 2020-12, `$id urn:magorch:<name>:1`, in `contracts/` + one example each)
- `dig_dump/1` = the user's INPUT SPECIFICATION: `source {url, fetched_at}`, `head` (meta/OpenGraph/title),
  `json_ld` (list), `cms_json` (`__NEXT_DATA__` / `__PRELOADED_STATE__`, may be null), `dom_stats {character_count,
  image_count, image_area_px|null, text_area_px|null, headings[{level,text}], blockquotes, figures, figcaptions,
  qa_blocks, list_items, outlinks[]}`, `body_sample {top, middle, bottom}` (each <= 200 chars), `captured_values
  {vol_no[], prices[], barcodes[], disclosures[], dates[]}`.
- `magazine_feature_profile/1` = the user's MagazineFeatureProfile with these fixes:
  `sponsored_flag` (the few-shot output says `sponsoredflag`, which fails the user's own schema); add
  `disclosure_detected`, `media_format`, `access_gate` (in the taxonomy, missing from the schema); `cadence` may be
  null (unknown is not IRREGULAR); `vertical` keeps `OTHER`; `estimated_read_time_min` with `read_time_basis`
  (language + rate used); `evidence` = map field -> `{method: "rule"|"input"|"llm", source: string}` for every
  non-null classified field; `source` = the dig_dump url + its sha256.

## Rules (deterministic code, not the model)
- `visual_density_score = min(1, image_count*150 / (character_count/5 + image_count*150))` (user example: 820 chars,
  18 images -> 0.94). When `image_area_px` and `text_area_px` exist also report `visual_to_text_ratio`.
- `layout_archetype`, first match wins: PICTORIAL_LOOKBOOK (score >= 0.65; the taxonomy says 0.65, the prompt says
  70 % — use 0.65, configurable) -> INTERVIEW_QA (>= 3 Q/A blocks or interviewer tokens) -> CURATION_ROUNDUP
  (numbered list >= 3 items with external links) -> FEATURE_DEEP_DIVE (>= 3,000 chars and >= 3 subheadings) ->
  COVER_STORY (cover/lead flag in head, json_ld or cms_json) -> EDITORIAL_ESSAY.
- `commercial_intent`: disclosure regex (`협찬`, `광고`, `제작지원`, `Sponsored`, `AD` only as a standalone token —
  never inside ADD/ADIDAS) -> SPONSORED_NATIVE + sponsored_flag; else affiliate params in outlinks (`tag=`, `aff=`,
  `partner=`, `utm_medium=affiliate`) -> AFFILIATE_COMMERCE; else EDITORIAL_PURE. BRAND_CATALOG only from the model
  with evidence.
- Vol/No: `Vol\.\s*(\d+)` -> volume_number, `No\.\s*(\d+)` -> issue_number, json_ld `volumeNumber`/`issueNumber`
  integers; a string like "Vol. 320" in `issueNumber` is a volume, recorded with evidence.
- Read time: Korean 500 chars/min, English 230 words/min (constants in the profile's `read_time_basis`).
- The model (provider adapter, fake in tests) fills only `vertical`, `target_audience`, `voice`, `jargon_density`,
  and `cadence` when metadata lacks it; each needs evidence from the dump, else null. The model never overrides a
  rule field. The user's few-shot output sets cadence MONTHLY and audience AFFLUENT_LUXURY with no evidence in its
  input — under the NO HALLUCINATION rule those are null; fix the example accordingly.

## Extractor
`magorch.reference.extract(html, url) -> dig_dump/1` with stdlib `html.parser` (the stand-in when `dig` is not
installed; `dig` is not in any of the user's repos, so a `dig` adapter only maps its output to `dig_dump/1`).
Respect robots.txt when fetching; keep only features and <= 200-char samples, never full article text.
`magorch.reference.profile(dump, classifier=None) -> magazine_feature_profile/1`. CLI: `python3 -m magorch reference <file.html|url>`.

## Tests (VM writes, `tests/test_reference.py`, offline)
4 synthetic HTML fixtures written for the tests (lookbook, interview, sponsored roundup with affiliate links, 3,000+ char
deep dive) -> expected archetype, intent, flags, score; the user's example numbers (0.94); `ADIDAS`/`ADD` not flagged;
`sponsoredflag` rejected by the schema; model output without evidence becomes null; every profile validates.
