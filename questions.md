# Questions

1. Where will the eight CSV files come from? Should we convert `category_tree_report.xlsx` into these CSVs, and if so, how should they be split and named?
     no need to create at this stage 8 csv files. we can make 1 csv file, as long it is within the specs of the csv files itself
3. Should each CSV contain the exact columns listed in the README (`Catid` through `Sub-sub-sub-sub-sub category`), or are additional fields expected?
    Follow the lineup as described in AGENTS.md, since this is the raw customer question/prompt. at this stage not more expected
4. For `title_selected` in `manifest.csv`, is this the lowest non-empty category name used for the SVGrepo search, or something else?
    Good question. In the end we wish to have an icon per line in the xls, so we can import this into a new backend. we wish to have original url, svg itself and the name as described in the readme/agents.md
6. What level of detail is expected in `concept_notes` within the manifest—short keywords or full sentences describing the icon concept? 
    short descriptive notes for operator to verify thought line
7. How should `primitives_used` be formatted (e.g., comma-separated list of shapes like `path,circle`)? 
    No idea. suggestions?
8. What exactly should `path_hash` be computed from (e.g., SHA256 of the entire SVG content, only the `d` attribute, etc.)?
     No idea. suggestions?
9. Are there licensing or attribution requirements when using icons from SVGrepo, beyond recording the source URL in `manifest.csv`?
    yes. free to use without retained rights
10. When no suitable SVGrepo icon exists and we generate one, is there a preferred algorithm or style guideline beyond the deterministic seed and general spec?
    Do you have suggestions? We need to obey the customer wish of icon per category. all with same look/feel, but relevant to the category. icon should give clear recognicion of the category
11. Categories in the provided spreadsheet appear to be in Dutch—should SVGrepo searches use these Dutch terms, or should they be translated to English first?
    I would also use english translated words, as long the icon is not an reassemblence of a word.
12. Where should the resulting ZIP packages (SVGs + `manifest.csv`) be stored, and should they be committed to the repository or delivered separately?
    We have to check if we can store svg files in github, if this is prohibited due "active content" filters, I'll supply a googledrive link to write to. In that case you have to create an interface to google drive too.
    
