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
- GitHub accepts `.svg` files but blocks files larger than 100 MiB; keep ZIP artifacts under this limit or plan for external storage if larger.
- For web research, retrieve pages using `curl` with the `https://r.jina.ai/` prefix (or text-based tools like `lynx`) to access clean text for citation.

## Items Needing Clarification
- Confirm whether a Google Drive or other external storage interface is required when ZIP packages approach GitHub's 100 MiB file limit.
