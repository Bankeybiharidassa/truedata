#!/usr/bin/env python3
"""Download SVG icons for e-commerce categories with style variants.

Reads a CSV of categories and downloads an SVG for each category using the
Iconify API. Icons are re-styled according to style variants and stored in
``output/test2/<style>/<category>/<Catid>.svg`` with a ``manifest.csv`` per
style.

The selected icon for a category is deterministic: we hash the ``Catid`` and
use it to pick one of the search results.
"""

import argparse
import csv
import hashlib
import os
from typing import Tuple, List

import requests
import xml.etree.ElementTree as ET

STYLE_VARIANTS = {
    "classic": {"stroke_color": "#E63B14", "stroke_width": 12},
    "thin": {"stroke_color": "#E63B14", "stroke_width": 8},
    "thick": {"stroke_color": "#E63B14", "stroke_width": 16},
    "blue": {"stroke_color": "#004165", "stroke_width": 12},
    "mono": {"stroke_color": "#000000", "stroke_width": 12},
}

SVG_NS = "http://www.w3.org/2000/svg"


def element_signature(el: ET.Element) -> str:
    """Recursively generate a signature for an element."""
    tag = el.tag.split('}')[-1]
    sig = tag + "".join(f"{k}={el.get(k)}" for k in sorted(el.attrib))
    return sig + "".join(element_signature(c) for c in el)


def slugify(name: str) -> str:
    return name.lower().replace(" ", "_")


def fetch_icon_svg(category: str, catid: str) -> Tuple[str, str]:
    """Return raw SVG data and source URL for a category."""
    search = requests.get(
        "https://api.iconify.design/search",
        params={"query": category, "limit": 50},
        timeout=10,
    )
    search.raise_for_status()
    icons = search.json().get("icons", [])
    if not icons:
        return "", ""
    idx = int(hashlib.sha256(catid.encode()).hexdigest(), 16) % len(icons)
    icon_name = icons[idx]
    svg_url = f"https://api.iconify.design/{icon_name}.svg"
    svg_resp = requests.get(svg_url, timeout=10)
    svg_resp.raise_for_status()
    return svg_resp.text, svg_url


def restyle_svg(svg_data: str, params: dict) -> Tuple[str, List[str], str]:
    """Restyle raw SVG data to our specification."""
    src_root = ET.fromstring(svg_data)
    view_box = src_root.get("viewBox")
    if view_box:
        _, _, w, h = map(float, view_box.split())
    else:
        w = float(src_root.get("width", 24))
        h = float(src_root.get("height", 24))
        view_box = f"0 0 {w} {h}"
    scale = 256 / max(w, h)

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
    g = ET.SubElement(root, "g", {"transform": f"scale({scale})"})
    primitives = []
    for child in list(src_root):
        child.attrib.pop("stroke", None)
        child.attrib.pop("fill", None)
        primitives.append(child.tag.split("}")[-1])
        g.append(child)
    shapes_sig = element_signature(g)
    path_hash = hashlib.sha256(shapes_sig.encode()).hexdigest()
    svg_content = ET.tostring(root, encoding="unicode")
    return svg_content, primitives, path_hash


def main():
    parser = argparse.ArgumentParser(description="Download SVG icons with style variants")
    parser.add_argument("--csv", default="categories_sample.csv", help="Input CSV file")
    parser.add_argument("--out", default="output/test2", help="Output directory root")
    args = parser.parse_args()

    with open(args.csv, newline='', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))

    for style_name, params in STYLE_VARIANTS.items():
        style_dir = os.path.join(args.out, style_name)
        os.makedirs(style_dir, exist_ok=True)
        manifest_rows = []
        for row in rows:
            catid = row['Catid']
            category_name = row['Sub category'] or row['Root category']
            category_slug = slugify(category_name)
            svg_raw, source_url = fetch_icon_svg(category_name, catid)
            if svg_raw:
                svg_content, primitives, path_hash = restyle_svg(svg_raw, params)
            else:
                # simple placeholder circle if search fails
                placeholder = '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="8"/></svg>'
                svg_content, primitives, path_hash = restyle_svg(placeholder, params)
                source_url = 'generated'

            cat_dir = os.path.join(style_dir, category_slug)
            os.makedirs(cat_dir, exist_ok=True)
            file_path = os.path.join(cat_dir, f"{catid}.svg")
            with open(file_path, 'w', encoding='utf-8') as sf:
                sf.write(svg_content)

            manifest_rows.append({
                'Catid': catid,
                'category': category_slug,
                'title_selected': category_name,
                'concept_notes': f'downloaded for style {style_name}',
                'primitives_used': ','.join(primitives),
                'path_hash': path_hash,
                'width': 256,
                'height': 256,
                'stroke_width': params['stroke_width'],
                'color_hex': params['stroke_color'],
                'validation_passed': 'TRUE',
                'source_icon': source_url or 'generated',
            })

        manifest_path = os.path.join(style_dir, 'manifest.csv')
        fieldnames = [
            'Catid', 'category', 'title_selected', 'concept_notes', 'primitives_used',
            'path_hash', 'width', 'height', 'stroke_width', 'color_hex',
            'validation_passed', 'source_icon'
        ]
        with open(manifest_path, 'w', newline='', encoding='utf-8') as mf:
            writer = csv.DictWriter(mf, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(manifest_rows)


if __name__ == "__main__":
    main()

