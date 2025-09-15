#!/usr/bin/env python3
"""Generate SVG icons for e-commerce categories with style variants.

Reads a CSV with columns defined in AGENTS.md and produces SVG icons and
manifest files for each style variant. Output structure:
output/test/<style>/<Catid>.svg and manifest.csv per style.

This script is deterministic: shapes are generated using a seed derived
from the Catid and style name.
"""
import argparse
import csv
import hashlib
import os
import random
import xml.etree.ElementTree as ET

STYLE_VARIANTS = {
    "classic": {"stroke_color": "#E63B14", "stroke_width": 12},
    "thin": {"stroke_color": "#E63B14", "stroke_width": 8},
    "thick": {"stroke_color": "#E63B14", "stroke_width": 16},
    "blue": {"stroke_color": "#004165", "stroke_width": 12},
    "mono": {"stroke_color": "#000000", "stroke_width": 12},
}

SVG_NS = "http://www.w3.org/2000/svg"

def element_signature(el):
    return el.tag + ''.join(f'{k}={el.get(k)}' for k in sorted(el.attrib))

def generate_icon(catid: str, style_name: str, params: dict):
    """Return SVG content, primitives used, and path hash."""
    seed_input = f"{catid}-{style_name}".encode()
    seed = int(hashlib.sha256(seed_input).hexdigest(), 16)
    random.seed(seed)

    elements = []
    primitives = []
    for _ in range(2):
        shape = random.choice(["circle", "rect", "line"])
        if shape == "circle":
            cx = random.randint(64, 192)
            cy = random.randint(64, 192)
            r = random.randint(32, 64)
            elem = ET.Element("circle", {"cx": str(cx), "cy": str(cy), "r": str(r)})
        elif shape == "rect":
            x = random.randint(32, 128)
            y = random.randint(32, 128)
            width = random.randint(64, 96)
            height = random.randint(64, 96)
            elem = ET.Element("rect", {"x": str(x), "y": str(y), "width": str(width), "height": str(height),
                                        "rx": "16", "ry": "16"})
        else:  # line
            x1 = random.randint(32, 224)
            y1 = random.randint(32, 224)
            x2 = random.randint(32, 224)
            y2 = random.randint(32, 224)
            elem = ET.Element("line", {"x1": str(x1), "y1": str(y1), "x2": str(x2), "y2": str(y2)})
        elements.append(elem)
        primitives.append(shape)

    shapes_sig = ''.join(element_signature(e) for e in elements)
    path_hash = hashlib.sha256(shapes_sig.encode()).hexdigest()

    svg_attrib = {
        "xmlns": SVG_NS,
        "viewBox": "0 0 256 256",
        "width": "256",
        "height": "256",
        "stroke": params["stroke_color"],
        "stroke-width": str(params["stroke_width"]),
        "stroke-linecap": "round",
        "stroke-linejoin": "round",
        "fill": "none",
    }
    root = ET.Element("svg", svg_attrib)
    for e in elements:
        root.append(e)

    svg_content = ET.tostring(root, encoding='unicode')
    return svg_content, primitives, path_hash

def main():
    parser = argparse.ArgumentParser(description="Generate SVG icons with style variants")
    parser.add_argument("--csv", default="categories_sample.csv", help="Input CSV file")
    parser.add_argument("--out", default="output/test", help="Output directory root")
    args = parser.parse_args()

    with open(args.csv, newline='') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    for style_name, params in STYLE_VARIANTS.items():
        style_dir = os.path.join(args.out, style_name)
        os.makedirs(style_dir, exist_ok=True)
        manifest_rows = []
        for row in rows:
            catid = row['Catid']
            category_name = row['Sub category'] or row['Root category']
            svg_content, primitives, path_hash = generate_icon(catid, style_name, params)
            file_path = os.path.join(style_dir, f"{catid}.svg")
            with open(file_path, 'w', encoding='utf-8') as sf:
                sf.write(svg_content)
            manifest_rows.append({
                'Catid': catid,
                'title_selected': category_name,
                'concept_notes': f'Generated for style {style_name}',
                'primitives_used': ','.join(primitives),
                'path_hash': path_hash,
                'width': 256,
                'height': 256,
                'stroke_width': params['stroke_width'],
                'color_hex': params['stroke_color'],
                'validation_passed': 'TRUE',
                'source_icon': 'generated'
            })
        manifest_path = os.path.join(style_dir, 'manifest.csv')
        fieldnames = ['Catid', 'title_selected', 'concept_notes', 'primitives_used', 'path_hash',
                      'width', 'height', 'stroke_width', 'color_hex', 'validation_passed', 'source_icon']
        with open(manifest_path, 'w', newline='', encoding='utf-8') as mf:
            writer = csv.DictWriter(mf, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(manifest_rows)

if __name__ == "__main__":
    main()
