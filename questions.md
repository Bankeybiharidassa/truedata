# Questions

1. Where will the eight CSV files come from? Should we convert `category_tree_report.xlsx` into these CSVs, and if so, how should they be split and named?
2. Should each CSV contain the exact columns listed in the README (`Catid` through `Sub-sub-sub-sub-sub category`), or are additional fields expected?
3. For `title_selected` in `manifest.csv`, is this the lowest non-empty category name used for the SVGrepo search, or something else?
4. What level of detail is expected in `concept_notes` within the manifest—short keywords or full sentences describing the icon concept?
5. How should `primitives_used` be formatted (e.g., comma-separated list of shapes like `path,circle`)?
6. What exactly should `path_hash` be computed from (e.g., SHA256 of the entire SVG content, only the `d` attribute, etc.)?
7. Are there licensing or attribution requirements when using icons from SVGrepo, beyond recording the source URL in `manifest.csv`?
8. When no suitable SVGrepo icon exists and we generate one, is there a preferred algorithm or style guideline beyond the deterministic seed and general spec?
9. Categories in the provided spreadsheet appear to be in Dutch—should SVGrepo searches use these Dutch terms, or should they be translated to English first?
10. Where should the resulting ZIP packages (SVGs + `manifest.csv`) be stored, and should they be committed to the repository or delivered separately?
