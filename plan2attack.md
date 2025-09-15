# Plan to Generate One SVG per Category

## Overview
This document outlines the approach to ensure every category in the e-commerce taxonomy has exactly one deterministic SVG icon in house style. When no suitable icon exists, a new one will be generated consistent with existing icons.

## Steps
1. **Collect Categories**
   - Parse input CSVs or `category_tree_report.xlsx` to obtain all `Catid` values and their most specific category names.
   - Ensure each category is processed once.

2. **Determine Search Query**
   - For each row, identify the lowest non-empty category field.
   - Translate Dutch terms to English when needed for search clarity.

3. **Search SVGrepo**
   - Use the selected category name as query on svgrepo.com.
   - Prefer simple icons built from paths/lines/circles without text or decorative clutter.

4. **Select or Generate Icon**
   - **If a suitable SVGrepo icon exists:**
     - Download and record its URL.
     - Restyle it to match the repository specifications (stroke `#E63B14`, width `12`, round caps/joins, no fills, 256×256 viewBox, ≤6 primitives).
   - **If no icon is found:**
     - Generate an original icon seeded with `SHA256(Catid)` to guarantee determinism.
     - Use 2–6 primitives that clearly convey the category concept and match the overall visual tone of existing icons.

5. **Validation & Saving**
   - Verify: correct viewBox, stroke attributes, no forbidden elements, ≤6 primitives, unique `path_hash` within batch.
   - Save icon as `{Catid}.svg` in the `output` directory.
   - Append a row to `manifest.csv` with required metadata including `source_icon` (`URL` or `generated`).

6. **Consistency Check**
   - After processing all categories, ensure there is exactly one SVG file per `Catid` and that every manifest entry references an existing file.

7. **Updates & Logs**
   - Maintain documentation (`README.md`, `AGENTS.md`, `actionlist.md`, `questions.md`) as processes evolve.
   - Record any uncertainties or required clarifications in `questions.md`.

## Result
Following these steps will produce a fully populated `output` directory containing one validated SVG per category and a comprehensive `manifest.csv` for operator review.
