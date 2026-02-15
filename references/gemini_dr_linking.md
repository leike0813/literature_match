# Gemini DR → Obsidian Linking (Agent Guide)

> Developer reference: the publishable skill uses `literature-match/scripts/gemini_dr_link.py` for Gemini DR linking.

This guide is for converting a **Gemini DR** Markdown report into an Obsidian-friendly version by:

1) Replacing in-body numeric citations (by `ref_id`) with `[[citekey]]` links (matched refs only).
2) Appending `[[citekey]]` after each corresponding entry in the **Works cited** section (matched refs only).
3) Inserting a new **Reference** section *before* **Works cited** that lists **unique matched works** in **Harvard** style, each ending with `[[citekey]]`.

This is intentionally agent-driven (not a pure script), because Gemini DR documents contain both:
- sentence-ending numeric citations (should be converted), and
- numbered lists/section numbering (must NOT be converted).

---

## Inputs

- `doc_path` (Gemini DR Markdown), e.g. `examples/example_entry.md` (UTF-8).
- `match_result.json`, which MUST include:
  - `refs[]` with `ref_id`, `line_start`, `line_end`, `raw_text`
  - `refs[].match.status` and `refs[].match.citekey`
  - `refs[].candidates[]` (for title/year/authors/doi/url)

## Output

- A modified Markdown document.
- Recommended output path: add `_processed` suffix (do not overwrite source unless explicitly required), e.g. `examples/example_entry_processed.md`.

---

## Core rules (strict)

### R1) Only convert matched refs

Use only refs where:
- `refs[i].match.status == "matched"`
- `refs[i].match.citekey` is a non-empty string

Ignore all other refs (`needs_review`, `unmatched`, missing citekey).

### R2) Replace in-body citations by `ref_id`

Gemini DR’s citation markers are typically **numbers at sentence end**, e.g.:
- `... 提供了宝贵的经验和思路 61。`

The canonical transformation is:
- `... 提供了宝贵的经验和思路 [[<citekey>]]。`

### R3) Do NOT replace non-citation numbers

Do not convert:
- list numbering at start of line: `1. ...`, `2. ...`
- section numbering: `### 2.1 ...`
- ordinal numbers inside technical text
- years / arXiv IDs / figure numbers

When uncertain whether a number is a citation or structural numbering: **do not replace it**.

### R4) Works cited: append link per entry

In the Works cited section, for each matched `ref_id`, append a trailing `[[citekey]]` to that reference entry.

### R5) Add “Reference” section (Harvard, deduped)

Insert a new section titled `#### **Reference**` immediately **before** the `#### **Works cited**` heading.

In this section:
- Include each matched work **once** (dedupe by `citekey`).
- Use a Harvard-like format.
- Use an unordered list (`- ...`).
- Append `[[citekey]]` at the end of each entry.
- Sort entries by **author/year** (see details below).

---

## Procedure (step-by-step)

### Step 1) Build the matched map: `ref_id -> citekey`

From `match_result.json`:

- For each `ref` in `refs[]`:
  - if `ref.match.status == "matched"` and `ref.match.citekey` is not empty:
    - record `ref_id -> citekey`

Also build a **unique** ordered set of citekeys (dedupe by citekey).

### Step 2) Locate the “Works cited” heading

Find the Works cited section heading in the Markdown. Common patterns:
- `#### **Works cited**`
- `## References`
- `### Works cited`

Use the heading that is actually followed by a numbered bibliography list.

Record the insertion point: right before the Works cited heading line.

### Step 3) Insert the “Reference” section (Harvard + `[[citekey]]`)

#### 3.1 Choose metadata source per citekey

For each `citekey`:
- Prefer using the candidate object from `match_result.json` where `candidate.citekey == citekey`.
- If multiple refs map to the same citekey, choose any one candidate consistently (first occurrence is fine).

Minimum fields (best-effort):
- `authors[]` (list of `"Family, Given"` or similar)
- `year` (string)
- `title` (string)
- `doi` or `url` (string)

#### 3.2 Harvard-like formatting template (best-effort)

Use this template (omit unknown parts):

- `Author (Year) 'Title'. doi: DOI. [[citekey]]`
- If DOI absent but URL present: `Author (Year) 'Title'. Available at: URL. [[citekey]]`

Author rules:
- If `authors[]` empty: use `Anon.`
- If 1 author: `Family, I.`
- If 2 authors: `Family, I. and Family, I.`
- If ≥3 authors: `Family, I. et al.`

Initials:
- From given names, use first letters (e.g., “Isaac” → “I.”, “Jian Dong” → “J.D.”).

Year rules:
- If missing/empty: use `n.d.`

Title rules:
- If missing/empty: use `Untitled`

#### 3.3 Sorting (author/year)

Sort the Reference entries by:
1) `first_author_family` (case-insensitive; `Anon.` last)
2) `year` numeric ascending; `n.d.` last
3) `title` (case-insensitive)

#### 3.4 Insert section

Insert exactly:

```
#### **Reference**

- <Harvard entry> [[citekey]]
- ...

```

immediately before the Works cited heading.

### Step 4) Replace in-body citation markers with `[[citekey]]`

Goal: in the **main body** (i.e., not inside Works cited), replace citation markers matching ref IDs.

Recommended heuristic for Gemini DR:
- Replace only when a ref_id appears as a standalone token near sentence end, e.g.:
  - ` ... 51。`
  - ` ... 51，`
  - ` ... 51;`
  - ` ... 51)`

Do not replace:
- `1. ...` (start-of-line list numbering)
- `### 2.1 ...` (headings)

When the text contains multiple citations:
- Example: `... 18, 19。`
- Convert only the matched ones:
  - `... [[ck18]], [[ck19]]。`
- Keep unmatched numbers unchanged.

### Step 5) Works cited: append `[[citekey]]` to each matched entry

In Works cited:
- Each entry typically starts with `"{ref_id}. "` (e.g., `51. ...`).
- For each matched ref_id:
  - Find the corresponding entry by its `ref_id`.
  - Append a trailing ` [[citekey]]` to the end of that entry (last line if wrapped).
  - Do not duplicate if it already exists.

Prefer `line_start/line_end` from `match_result.json` when editing multi-line entries:
- Append to `line_end`.

---

## Validation checklist (must pass)

- Body: every *citation-style* use of a matched `ref_id` is replaced with `[[citekey]]`.
- Body: numbered lists/headings remain unchanged (no accidental conversion).
- Works cited: each matched entry has exactly one appended `[[citekey]]`.
- New section: `#### **Reference**` exists immediately before Works cited.
- Reference section: no duplicate citekeys; unordered list; Harvard-like formatting; sorted by author/year.

---

## Recommended agent output behavior

To avoid output truncation, write the modified Markdown directly to disk and only output a small confirmation payload, e.g.:

```json
{"written_path":"examples/example_entry_processed.md","matched_citekeys_count":0,"body_replacements":0,"works_cited_appends":0}
```
