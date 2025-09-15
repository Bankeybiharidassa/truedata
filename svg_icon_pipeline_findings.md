# Truedata – SVG Icon Pipeline Findings

Status: draft for PR discussion • Scope: analysis of current behavior vs. README contract • Audience: maintainers

---

## 1) Executive Summary
The current pipeline **behaves as if the SVGrepo lookup is disabled or never called** and/or the **deepest-category resolver selects the wrong field**. As a result, icons often appear **seed‌g‌en‌era‌ted and semantically unrelated** to their categories, and `manifest.csv` lines tend to show `generated` (or empty) for `source_icon`. Validation focuses on style/structure and **does not fail on missing semantics**, so batches pass while category→icon fidelity is poor.

---

## 2) What We Expected (from README contract)
- For each CSV row:
  1) Determine **lowest non-empty category** (deepest subject).
  2) Query **svgrepo.com** with that subject; select a **simple, clean** candidate icon.
  3) **Restyle** strictly to house rules (stroke/width/caps/joins/fill/viewBox/centering/margins/max 6 shapes).
  4) **Validate** and write a manifest row including a **`source_icon` URL** (or `generated` if no suitable icon exists).
- Determinism: identical results for repeated runs (seed = `SHA256(Catid)`).

---

## 3) What We Observe in Results
- Many icons do **not reflect** their category subject.
- `manifest.csv` frequently contains `generated` or empty `source_icon` → suggests **SVGrepo lookup is not producing usable hits** or is **never executed**.
- Validation passes because checks are mainly **syntactic/style-based** (viewBox, strokes, forbidden elements), not semantic.
- Recent testing of the Iconify-based fallback showed network calls can hang until manually interrupted, indicating unstable access to public icon sources.

---

## 4) Likely Root Causes (prioritized)
1. **Deepest Category Resolver bug**
   - Grabs the **first** non-empty category or a concatenation of columns → noisy queries → no useful SVGrepo matches → fallback to generator.
2. **SVGrepo Search disabled or always failing**
   - Feature flag off (e.g., `SVGREPO_ENABLED=0`), missing dependency, network block, or overstrict pre-filters rejecting all candidates **before** restyling.
3. **Over-rejecting before restyle**
   - Filtering out icons containing any extra attributes (e.g., fills/styles) instead of **stripping** them; should accept candidates and then normalize.
4. **Manifest writer does not enforce `source_icon`**
   - Allows empty/`generated` without logging why lookup failed, hiding the real issue.

---

## 5) Impact
- **Category→Icon mismatch** reduces usability and credibility.
- **Manifest lacks traceability** (`concept_notes`/`source_icon`), hindering QA and audits.
- Re-runs stay deterministic yet **consistently wrong** semantically.

---

## 6) Action Plan (fix-first order)
### A) Correct the subject resolver
```python
# expected behavior: pick deepest non-empty category
CATEGORY_ORDER = [
    "Sub-sub-sub-sub-sub category",
    "Sub-sub-sub-sub category",
    "Sub-sub-sub category",
    "Sub-sub category",
    "Sub category",
    "Root category",
]

def deepest_category(row: dict) -> str:
    for col in CATEGORY_ORDER:
        v = (row.get(col) or "").strip()
        if v:
            return v
    return (row.get("Root category") or "").strip()
```

### B) Ensure SVGrepo search actually runs

* Add an **explicit toggle**: `SVGREPO_ENABLED=1` (default ON for CI; allow OFF for offline/dev).
* Log, per row: `query`, `candidates_found`, `chosen_url`, and **reject reasons** for skipped candidates.

### C) Restyle instead of pre-rejecting

* Accept candidates with fills/styles/other attributes and **normalize** them:

  * `stroke="#E63B14"`, `stroke-width="12"`, `stroke-linecap="round"`, `stroke-linejoin="round"`, `fill="none"`.
  * `viewBox="0 0 256 256"`, content centered with ≥16px margin.
  * Simplify to ≤6 shapes post-normalization.

### D) Strengthen manifest writing & validation

* `source_icon` is **mandatory** when search path is taken; fallback must state `generated` with a **reason** in `concept_notes`.
* Add `concept_notes` (e.g., `subject=..., decision=svgrepo|generated, reason=no_hits|rejected_3_due_to_text|best_of_5`).
* `path_hash`: compute over **normalized** geometry (consistent sort + rounded floats) to ensure batch uniqueness.

---

## 7) Suggested Interfaces (stubs)

### SVGrepo search (synchronous, HTML or API)

```python
def svgrepo_search(query: str, max_candidates: int = 10) -> list[dict]:
    """Return a list of candidates: [{"title": str, "url": str, "svg": str}]"""
    # implement HTTP request + parse; fall back to HTML scraping if no API
    # IMPORTANT: do not over-filter here; pass to restyler
    ...
```

### Restyle & Normalize

```python
def restyle_to_house_style(svg_text: str) -> str:
    """Strip forbidden elements/attrs, set stroke/fill/linecaps/joins,
    rescale to 256×256 with ≥16px margin, reduce to ≤6 shapes."""
    ...
```

### Manifest writer

```python
def write_manifest_row(csv_writer, row, *,
                       title_selected: str,
                       primitives_used: list[str],
                       path_hash: str,
                       w: int = 256,
                       h: int = 256,
                       stroke_width: int = 12,
                       color_hex: str = "#E63B14",
                       validation_passed: bool = True,
                       source_icon: str = "generated",
                       concept_notes: str = ""):
    csv_writer.writerow({
        "Catid": row["Catid"],
        "title_selected": title_selected,
        "concept_notes": concept_notes,
        "primitives_used": ",".join(primitives_used),
        "path_hash": path_hash,
        "width": w,
        "height": h,
        "stroke_width": stroke_width,
        "color_hex": color_hex,
        "validation_passed": str(validation_passed).upper(),
        "source_icon": source_icon,
    })
```

---

## 8) Logging (what we need to see in a dry-run)

```text
[row 12] subject="cordless drill"  (from Sub-sub-sub category)
[svgrepo] query="cordless drill" candidates=7 rejected=3(text),1(too_many_paths), chosen=https://www.svgrepo.com/svg/.../drill-line
[restyle] stripped attrs → stroke=#E63B14, fill=none, width=12, round caps/joins; shapes=4
[normalize] viewBox=0 0 256 256, margin=20px, centered
[validate] forbidden=none; path_hash=9f1e... OK
[manifest] source_icon=https://www.svgrepo.com/svg/.../drill-line; validation_passed=TRUE
```

If we never see `candidates>0` or a `chosen=URL`, the search step is **broken or disabled**.

---

## 9) Validation Additions

* Fail if `source_icon` is empty **and** decision path was `svgrepo`.
* Warn if `primitives_used` > 6.
* Enforce filename `Catid.svg` (no normalization).
* Enforce deterministic output:

  * rerun test on a small sample → SVG bytes and `manifest.csv` identical.

---

## 10) Minimal Test Protocol (pre-commit)

1. **Unit**: deepest resolver returns expected subjects for crafted rows.
2. **Integration**: 10-row sample with SVGrepo enabled; assert ≥70% rows have `source_icon` URL.
3. **Determinism**: double-run diff on SVG+manifest (expect byte-identical).
4. **Semantics spot-check**: 5 random rows → human confirms icon matches category.

---

## 11) Config Suggestions

* `.env` / settings:

  * `SVGREPO_ENABLED=1`
  * `SVGREPO_TIMEOUT_SEC=10`
  * `SVGREPO_MAX_CANDIDATES=12`
  * `RESTYLE_MAX_SHAPES=6`
  * `MARGIN_MIN_PX=16`
  * `HOUSE_COLOR_HEX=#E63B14`

---

## 12) Next Steps

* Implement A–D, add logs, run on a 20-row sample, attach new `manifest.csv` and 3 representative SVGs to PR for review.
* If queries still fail, add a small **synonym map** for common taxonomy terms (e.g., "fasteners" → "screw bolt nut").

## 13) Public icon access test (2024-08-??)

- `scripts/generate_icons.py` initially failed because the `requests` package was missing.
- After installing `requests`, Iconify API calls succeeded and produced manifest entries with public icon URLs.
- Direct requests to `svgrepo.com` failed with `ProxyError('Tunnel connection failed: 403 Forbidden')`.

---

*Prepared for Codex/GitHub integration – paste into an issue or PR as reference.*

