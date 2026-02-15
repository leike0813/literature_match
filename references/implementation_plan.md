# Implementation plan (developer reference)

This is a developer-only reference for the literature-match skill. It is not part of the published skill bundle.

## 0) Goals and non-goals

### Goals

- Input: a Markdown document (`doc_path`) containing a References section.
- Input: a Zotero Better BibTeX library export (`library.betterbibtexjson`), fetched from a local endpoint or loaded from a cached file.
- Output: `match_result.json` that is machine-consumable, traceable, reviewable, and stable.
- Matching strategy (fixed layering):
  1) extract structured refs with line traceability
  2) deterministic match: DOI → arXiv → URL
  3) TF‑IDF retrieval to get topK candidates (title-first, year/author light weighting)
  4) LLM/human adjudication only for `needs_llm` refs, only inside candidates

### Non-goals

- Do not modify the input Markdown (no `[[citekey]]` insertion).
- Do not write back to Zotero (no tagging/collections).
- Do not ship an LLM API integration (keys/cost are out of scope).

## 1) Repository layout (current)

The published skill bundle lives under `literature-match/` and uses `scripts/` for code.

```
literature-match/                  # Publishable skill bundle
  SKILL.md
  scripts/
    cli.py
    match_pipeline.py
    bbt_library.py
    refs_extracted.py
    normalize.py
    retrieval_tfidf.py
    apply_llm_decisions.py
references/                        # Developer reference (this file)
src/                               # Development copy of the pipeline
tests/
examples/
artifacts/
```

Notes:

- The skill spec expects executable code under `scripts/`.
- The `src/` directory is for local development and tests only.
- `mypy.ini` ignores sklearn missing stubs; run mypy against `literature-match/scripts/`.

## 2) Artifacts and contracts

The pipeline uses three JSON artifacts:

1. `refs_extracted.json` (agent → code)
2. `match_result.json` (code → agent → code; final deliverable)
3. `llm_decisions.json` (agent → code)

### 2.1 `refs_extracted.json` (agent output; schema tolerant)

Canonical shape (what we ask the agent to produce):

```json
{
  "meta": {
    "doc_path": "path/to/input.md",
    "generated_at": "YYYY-MM-DDTHH:MM:SSZ",
    "reference_section": {"line_start": 0, "line_end": 0, "title": "References"},
    "warnings": []
  },
  "refs": [
    {
      "ref_id": "12",
      "line_start": 120,
      "line_end": 121,
      "raw_text": "…",
      "parsed": {
        "doi": null,
        "url": null,
        "arxiv": null,
        "year": null,
        "title_guess": null,
        "author_guess": null
      }
    }
  ]
}
```

Tolerant parsing rules (code accepts):

- `refs` may appear under `refs`, `references`, or `items`.
- `meta` may be missing; defaults to `warnings=[]`.
- Per-ref:
  - Accept object or string refs.
  - Accept `line_start/line_end`, `start_line/end_line`, `line_range: [start, end]`, or `lines: {start, end}`.
  - Coerce numeric strings for line numbers.
  - If `raw_text` is missing but `raw_lines[]` exists, join lines.
  - Skip refs with no `raw_text` and warn.

### 2.2 `match_result.json` (deliverable)

- `refs[]` always exists (may be empty).
- `refs[].candidates[]` always exists (may be empty).
- Candidate fields are always present (empty string/list/null as needed).

### 2.3 `llm_decisions.json`

- Only `needs_llm` refs should appear.
- `citekey` must be one of the provided candidates or `null`.

## 3) Agent instruction design (skill)

Two agent steps remain in `literature-match/SKILL.md`:

1. **Reference extraction** → `refs_extracted.json` (semantic, line-traceable).
2. **LLM adjudication** → `llm_decisions.json` (only for `needs_llm` refs).

Both prompts default to writing JSON outputs to `artifacts/<doc_stem>/` to avoid chat truncation.

## 4) CLI workflow (published skill)

Run from repo root, using the `DataProcessing` conda env.

### 4.1 Build initial `match_result.json`

```bash
conda run --no-capture-output -n DataProcessing \
  python literature-match/scripts/cli.py match \
  --refs-extracted artifacts/<doc_stem>/refs_extracted.json \
  --library-cache examples/example_entry.library.betterbibtexjson
```

### 4.2 Apply decisions

```bash
conda run --no-capture-output -n DataProcessing \
  python literature-match/scripts/cli.py apply-decisions \
  --match-result artifacts/<doc_stem>/match_result.json \
  --llm-decisions artifacts/<doc_stem>/llm_decisions.json
```

## 5) Tests (developer)

Tests live in `tests/` and exercise tolerant parsing, normalization, and the end-to-end pipeline against the cached example.

```bash
conda run --no-capture-output -n DataProcessing \
  python -m unittest discover -s tests -p "test_*.py" -v
```

## 6) Release checklist (developer)

- `literature-match/` contains `SKILL.md` + `scripts/` only.
- `SKILL.md` frontmatter name matches folder name (`literature-match`).
- Agent prompts write artifacts into `artifacts/<doc_stem>/`.
- `mypy.ini` present; `mypy literature-match/scripts` is clean.
