# Action List

## Confirmed Decisions
- Use a single CSV file for now as long as it follows the specified format.
- Each CSV must contain exactly the columns defined in AGENTS.md (`Catid` through `Sub-sub-sub-sub-sub category`).
- `concept_notes` should contain short descriptive notes for operator verification.
- Icons from SVGrepo are free to use without retained rights; record the source URL.
- Translate Dutch category terms to English for SVGrepo searches unless translation produces a word-like icon.
- `title_selected` stores the lowest non-empty category name used for the SVGrepo search.
- `primitives_used` is a comma-separated list of SVG primitives present in the final icon (`path`, `circle`, `rect`, `line`, `polyline`, `polygon`).
- `path_hash` is the SHA-256 hash of the concatenated `d` attributes from all paths in the SVG.
- When generating custom icons, ensure they communicate meaning with simple, recognizable shapes, using 2–6 primitives and the specified stroke style.
- Output files are stored directly in an `output` directory; no ZIP packaging is required.
- GitHub accepts `.svg` files but blocks files larger than 100 MiB; ensure individual files stay below this limit.
- For web research, retrieve pages using `curl` with the `https://r.jina.ai/` prefix (or text-based tools like `lynx`) to access clean text for citation.

- Brand color palette and typography captured in style.md (primary #E63B14, secondary #004165, text #5E6A71, font Source Sans Pro).
- `generate_icons.py` can create five style variants per category for test evaluation.

## Items Needing Clarification
- Confirm whether an external storage solution (e.g., Google Drive) is required if repository artifacts approach GitHub's 100 MiB file limit.
