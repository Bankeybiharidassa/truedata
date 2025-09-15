# Action List

## Confirmed Decisions
- Use a single CSV file for now as long as it follows the specified format.
- Each CSV must contain exactly the columns defined in AGENTS.md (`Catid` through `Sub-sub-sub-sub-sub category`).
- `concept_notes` should contain short descriptive notes for operator verification.
- Icons from SVGrepo are free to use without retained rights; record the source URL.
- Translate Dutch category terms to English for SVGrepo searches unless translation produces a word-like icon.

## Items Needing Clarification
- **title_selected**: Clarify whether this field should store the lowest non-empty category name used for SVGrepo search.
- **primitives_used**: Establish a standard format, e.g., a comma-separated list of primitives (`path,circle`).
- **path_hash**: Decide the hashing method, such as SHA256 of the SVG's path data or the entire file content.
- **Custom icon generation**: Specify algorithm/style guidelines for generating icons when no suitable SVGrepo icon exists to ensure consistency.
- **Artifact storage**: Confirm whether generated SVG/manifest ZIPs can be stored in the repository or require external storage (e.g., Google Drive) and define any needed interfaces.
