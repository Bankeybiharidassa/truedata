#!/usr/bin/env python3
"""Batch update background color or transparency for SVG files."""

import argparse
from pathlib import Path
import xml.etree.ElementTree as ET


def update_svg(path: Path, color: str | None, opacity: float | None) -> None:
    """Update or remove the background rectangle in a single SVG file."""
    tree = ET.parse(path)
    root = tree.getroot()

    # search for existing background rect
    bg = None
    for child in list(root):
        if child.tag == "rect" and child.attrib.get("id") == "background":
            bg = child
            break

    if color is None:
        # remove existing background to restore transparency
        if bg is not None:
            root.remove(bg)
    else:
        if bg is None:
            bg = ET.Element(
                "rect",
                {
                    "id": "background",
                    "x": "0",
                    "y": "0",
                    "width": "256",
                    "height": "256",
                },
            )
            root.insert(0, bg)
        bg.set("fill", color)
        if opacity is not None:
            bg.set("fill-opacity", str(opacity))
        elif "fill-opacity" in bg.attrib:
            del bg.attrib["fill-opacity"]

    tree.write(path, encoding="utf-8", xml_declaration=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--color",
        help="Hex color for background, e.g. #FFFFFF",
    )
    group.add_argument(
        "--remove",
        action="store_true",
        help="Remove background rectangle to make SVG transparent",
    )
    parser.add_argument(
        "--opacity",
        type=float,
        help="Optional fill opacity between 0 and 1",
    )
    parser.add_argument(
        "--input-dir",
        default="output",
        help="Directory containing SVG files",
    )
    args = parser.parse_args()

    color = None if args.remove else args.color
    opacity = args.opacity if not args.remove else None

    directory = Path(args.input_dir)
    for svg_path in directory.glob("*.svg"):
        update_svg(svg_path, color, opacity)


if __name__ == "__main__":
    main()
