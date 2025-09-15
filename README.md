# SVG Icon Generator for E-Commerce Categories

This repository defines the workflow and strict rules for generating **deterministic, styled SVG icons** for e-commerce category taxonomies.  
The system processes CSV input files and outputs clean, validated SVGs plus a manifest per batch.

---

## Brand Style

See [style.md](style.md) for the site's color palette and typography. Icons use the primary brand color (#E63B14).

## System Behavior

- Input: one CSV at a time.  
- Output:
  1. Valid `<svg>` files (`{Catid}.svg`, one per row).  
  2. A `manifest.csv` containing validation metadata.  

⚠️ Everything outside this IO contract is ignored.

---

## Style & Specifications

- **Canvas:** `256×256`, `viewBox="0 0 256 256"`, transparent background  
- **Stroke:**  
  - `stroke="#E63B14"` (brand color)  
  - `stroke-width="12"`  
  - `stroke-linecap="round"`  
  - `stroke-linejoin="round"`  
  - `fill="none"`  
- **Filename:** exact `{Catid}.svg` (no normalization)  
- **Complexity:** 2–6 shapes, clean lines, no noise  
- **Forbidden elements:**  
  - Text, raster images, external refs  
  - `<style>`, CSS, `<script>`, `<defs>`  
  - Gradients, masks, clipPaths, fonts  
- **Deterministic:**  
  - For each `Catid`, the icon is generated with the same internal seed (`seed = SHA256(Catid)`).  
  - Re-runs always produce identical results.

---

## SVGrepo Integration

1. **Query Selection**  
   - For each row, use the lowest non-empty category field as search query on [svgrepo.com](https://www.svgrepo.com).  

2. **Icon Choice**  
   - Select the clearest, simplest icon (paths/lines/circles only).  
   - Reject icons with text, raster, or decorative noise.  
   - If no usable icon exists → generate a new one using deterministic seed.  

3. **Restyling**  
   - Strip all style/attributes not allowed.  
   - Apply stroke and canvas specs.  
   - Rescale and center with ≥16px margin.  
   - Simplify to max 6 shapes.  

4. **Validation**  
   - Must resemble the chosen SVGrepo icon, but strictly in house style.  
   - Add `source_icon` field in manifest (SVGrepo URL or `generated`).

---

## Developer Task

- Process **8 CSVs**, one by one.  
- CSV schema:  
Catid, Root category, Sub category, Sub-sub category, Sub-sub-sub category, Sub-sub-sub-sub category, Sub-sub-sub-sub-sub category

- Output per CSV:  
- `{Catid}.svg` files  
- `manifest.csv` with columns:  

  ```
  Catid, title_selected, concept_notes, primitives_used, path_hash, width, height, stroke_width, color_hex, validation_passed, source_icon
  ```

- Place results in an `output` directory containing all SVGs and `manifest.csv` (no ZIP).

---

## Assistant Workflow (Per Row)

1. Determine subject (lowest non-empty category).  
2. Search SVGrepo and select icon (or generate).  
3. Restyle into spec.  
4. Validate:  
 - Correct viewBox & strokes  
 - No forbidden elements  
 - Unique path-hash within batch  
 - `source_icon` filled  
 - `validation_passed=TRUE`

---

## Output

- For each CSV:  
- One directory "output" containing all `{Catid}.svg` + `manifest.csv`.  
- No extra text, no JSON.

---

## Sanity Checklist

- [ ] `viewBox="0 0 256 256"`  
- [ ] 2–6 vector primitives only  
- [ ] Stroke `12`, round caps & joins, color `#E63B14`  
- [ ] `fill="none"`  
- [ ] Geometry unique within batch  
- [ ] Filename = `Catid.svg`  
- [ ] Manifest line includes `source_icon` + `validation_passed=TRUE`
