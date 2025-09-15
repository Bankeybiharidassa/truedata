# Batch Updating SVG Backgrounds

This repository's icons use a transparent 256×256 canvas. If a customer later requests a specific background color or opacity, run the helper script to modify all SVGs in one go.

## Usage

```
python scripts/update_background.py --color "#FFFFFF" --opacity 1.0 --input-dir output
```

- `--color` sets the background fill color.
- `--opacity` (optional) specifies fill transparency between `0` (transparent) and `1` (opaque).
- `--input-dir` points to the folder containing the SVG files. Defaults to `output`.

To remove previously applied backgrounds and restore transparency:

```
python scripts/update_background.py --remove --input-dir output
```

The script adds or updates a `<rect id="background">` element at the start of each SVG to represent the background. Removing removes this rectangle entirely.
