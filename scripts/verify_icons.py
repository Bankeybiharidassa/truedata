#!/usr/bin/env python3
"""Verify generated SVG icons and manifests.

Checks viewBox, stroke attributes, fill, and path hash for each icon.
Usage: python scripts/verify_icons.py output/test
"""
import csv
import hashlib
import os
import sys
import xml.etree.ElementTree as ET

SVG_NS = "http://www.w3.org/2000/svg"

def element_signature(el):
    return el.tag.split('}')[-1] + ''.join(f'{k}={el.get(k)}' for k in sorted(el.attrib))

def verify_style(style_dir: str) -> int:
    manifest_path = os.path.join(style_dir, "manifest.csv")
    with open(manifest_path, newline='', encoding='utf-8') as mf:
        reader = csv.DictReader(mf)
        count = 0
        for row in reader:
            svg_path = os.path.join(style_dir, f"{row['Catid']}.svg")
            tree = ET.parse(svg_path)
            root = tree.getroot()
            assert root.tag == f"{{{SVG_NS}}}svg", f"Root element is not svg in {svg_path}"
            assert root.get("viewBox") == "0 0 256 256"
            assert root.get("width") == "256" and root.get("height") == "256"
            assert root.get("stroke") == row['color_hex']
            assert root.get("stroke-width") == str(row['stroke_width'])
            assert root.get("stroke-linecap") == "round"
            assert root.get("stroke-linejoin") == "round"
            assert root.get("fill") == "none"
            shape_sig = ''.join(element_signature(child) for child in root)
            path_hash = hashlib.sha256(shape_sig.encode()).hexdigest()
            assert path_hash == row['path_hash'], f"Path hash mismatch for {svg_path}"
            count += 1
    return count

def main():
    if len(sys.argv) != 2:
        print("Usage: python scripts/verify_icons.py <output_root>")
        sys.exit(1)
    root_dir = sys.argv[1]
    total = 0
    for style in sorted(os.listdir(root_dir)):
        style_dir = os.path.join(root_dir, style)
        if not os.path.isdir(style_dir):
            continue
        count = verify_style(style_dir)
        print(f"{style}: {count} icons verified")
        total += count
    print(f"Total icons verified: {total}")

if __name__ == "__main__":
    main()
