#!/usr/bin/env python3
"""Download and restyle SVG icons for e-commerce categories.

The script reads a CSV file describing category taxonomy rows and downloads an
SVG for each row using the svgapi.com JSON API. Every icon is re-styled to the
brand specification and written to ``<output>/<style>/<category>/<Catid>.svg``
alongside a ``manifest.csv`` with metadata useful for validation.

The selected icon for a category is deterministic: a SHA256 hash of ``Catid``
is used to pick one item from the API search results.
"""

import argparse
import csv
import hashlib
import logging
import os
import re
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import requests
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.append(str(SRC_PATH))

from taxonomy.resolver import deepest_category  # noqa: E402
from taxonomy.synonyms import build_queries  # noqa: E402


STYLE_VARIANTS = {
    "classic": {"stroke_color": "#E63B14", "stroke_width": 12},
    "thin": {"stroke_color": "#E63B14", "stroke_width": 8},
    "thick": {"stroke_color": "#E63B14", "stroke_width": 16},
    "blue": {"stroke_color": "#004165", "stroke_width": 12},
    "mono": {"stroke_color": "#000000", "stroke_width": 12},
}

SVG_NS = "http://www.w3.org/2000/svg"
SVGAPI_LIST_URL = "https://api.svgapi.com/v1/{key}/list/"


def configure_logging(out_dir: Path, level: str) -> Path:
    """Configure logging to both STDOUT and ``generation.log`` in ``out_dir``."""

    out_dir.mkdir(parents=True, exist_ok=True)
    log_path = out_dir / "generation.log"

    console_level = getattr(logging, level.upper(), logging.INFO)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)

    file_handler = logging.FileHandler(log_path, mode="w", encoding="utf-8")
    file_handler.setLevel(logging.INFO)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[console_handler, file_handler],
    )
    logging.info("Logging initialised at %s", log_path)
    return log_path


def element_signature(el: ET.Element) -> str:
    """Recursively generate a signature for an element."""
    tag = el.tag.split('}')[-1]
    sig = tag + "".join(f"{k}={el.get(k)}" for k in sorted(el.attrib))
    return sig + "".join(element_signature(c) for c in el)


def slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", name.lower())
    slug = re.sub(r"_+", "_", slug).strip("_")
    return slug or "category"


def iter_search_queries(category: str) -> List[str]:
    """Generate prioritized search queries for ``category``."""

    queries: List[str] = []
    for candidate in build_queries(category):
        sanitized = candidate.strip()
        if sanitized and sanitized not in queries:
            queries.append(sanitized)

    # Add a simplified form without punctuation to avoid API parse errors.
    simplified = re.sub(r"[^a-z0-9 ]+", " ", category.lower()).strip()
    if simplified and simplified not in queries:
        queries.append(simplified)

    if category not in queries:
        queries.append(category)

    lower = category.lower()
    fallback_terms: List[str] = []
    if "baby" in lower:
        fallback_terms.extend(["baby care", "baby icon", "baby"])
    if "kind" in lower or "child" in lower:
        fallback_terms.extend(["child icon", "children toys"])

    for term in fallback_terms:
        if term not in queries:
            queries.append(term)

    universal_fallbacks = ["baby icon", "baby"]
    for term in universal_fallbacks:
        if term not in queries:
            queries.append(term)
    return queries


def fetch_icon_svg(
    category: str,
    catid: str,
    session: requests.Session,
    api_key: str,
    limit: int,
) -> Tuple[str, str, str]:
    """Return SVG data, source URL and title for ``category``.

    Returns empty strings when the lookup fails so the caller can record
    metadata about the missing public icon.
    """

    search_url = SVGAPI_LIST_URL.format(key=api_key)
    queries = iter_search_queries(category)
    for query in queries:
        try:
            response = session.get(
                search_url,
                params={"search": query, "limit": limit},
                timeout=10,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            logging.warning(
                "[svgapi] search failed for '%s' (query '%s'): %s",
                category,
                query,
                exc,
            )
            continue

        try:
            payload = response.json()
        except ValueError as exc:
            logging.warning(
                "[svgapi] invalid JSON for '%s' (query '%s'): %s",
                category,
                query,
                exc,
            )
            continue

        icons = payload.get("icons") or []
        if not icons:
            logging.info("[svgapi] no icons found for '%s' (query '%s')", category, query)
            continue

        idx = int(hashlib.sha256(catid.encode()).hexdigest(), 16) % len(icons)
        selected = icons[idx]
        svg_url = selected.get("url", "")
        if not svg_url:
            logging.warning(
                "[svgapi] missing SVG URL for '%s' (query '%s')",
                category,
                query,
            )
            continue

        try:
            svg_resp = session.get(svg_url, timeout=10)
            svg_resp.raise_for_status()
        except requests.RequestException as exc:
            logging.warning("[svgapi] download failed for '%s': %s", svg_url, exc)
            continue

        title = selected.get("title") or selected.get("slug") or category
        logging.info("[svgapi] using '%s' for '%s' via query '%s'", title, category, query)
        return svg_resp.text, svg_url, title

    logging.info("[svgapi] no icons found for '%s' after trying %d queries", category, len(queries))
    return "", "", ""


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
    primitives: List[str] = []
    for child in list(src_root):
        for attr in ["stroke", "fill", "style", "class", "id"]:
            child.attrib.pop(attr, None)
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
    parser.add_argument(
        "--styles",
        default="classic",
        help="Comma-separated list of style variants to generate",
    )
    parser.add_argument(
        "--api-key",
        default=os.environ.get("SVGAPI_API_KEY", "Ty5WcDa63E"),
        help="SVGAPI key (defaults to example key or SVGAPI_API_KEY env var)",
    )
    parser.add_argument(
        "--search-limit",
        type=int,
        default=50,
        help="Number of results to request per API search",
    )
    parser.add_argument(
        "--log-level",
        default=os.environ.get("ICON_LOG_LEVEL", "INFO"),
        help="Logging level (DEBUG, INFO, WARNING, ERROR)",
    )
    args = parser.parse_args()

    out_root = Path(args.out)
    log_path = configure_logging(out_root, args.log_level)

    logging.info("Reading categories from %s", args.csv)
    with open(args.csv, newline='', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))

    requested_styles: Iterable[str] = [s.strip() for s in args.styles.split(',') if s.strip()]
    styles: Dict[str, Dict[str, int]] = {}
    for style in requested_styles:
        if style not in STYLE_VARIANTS:
            raise SystemExit(f"Unknown style variant '{style}'. Available: {', '.join(STYLE_VARIANTS)}")
        styles[style] = STYLE_VARIANTS[style]

    session = requests.Session()
    logging.info("Writing logs to %s", log_path)
    logging.info("Generating icons for %d categories (%s)", len(rows), ", ".join(styles))

    for style_name, params in styles.items():
        style_dir = out_root / style_name
        style_dir.mkdir(parents=True, exist_ok=True)
        manifest_rows = []
        for row in rows:
            catid = row['Catid']
            category_name = deepest_category(row) or row['Root category'] or 'Unknown'
            category_slug = slugify(category_name)
            logging.debug("Processing %s (%s) for style %s", catid, category_name, style_name)
            svg_raw, source_url, icon_title = fetch_icon_svg(
                category_name,
                catid,
                session,
                args.api_key,
                args.search_limit,
            )
            if not svg_raw:
                manifest_rows.append({
                    'Catid': catid,
                    'category': category_slug,
                    'title_selected': category_name,
                    'concept_notes': 'no public icon found',
                    'primitives_used': '',
                    'path_hash': '',
                    'width': 0,
                    'height': 0,
                    'stroke_width': params['stroke_width'],
                    'color_hex': params['stroke_color'],
                    'validation_passed': 'FALSE',
                    'source_icon': '',
                })
                continue

            try:
                svg_content, primitives, path_hash = restyle_svg(svg_raw, params)
            except ET.ParseError as exc:
                logging.warning("Failed to parse SVG for %s (%s): %s", catid, source_url, exc)
                manifest_rows.append({
                    'Catid': catid,
                    'category': category_slug,
                    'title_selected': category_name,
                    'concept_notes': 'svg parsing failed',
                    'primitives_used': '',
                    'path_hash': '',
                    'width': 0,
                    'height': 0,
                    'stroke_width': params['stroke_width'],
                    'color_hex': params['stroke_color'],
                    'validation_passed': 'FALSE',
                    'source_icon': source_url,
                })
                continue

            cat_dir = style_dir / category_slug
            cat_dir.mkdir(parents=True, exist_ok=True)
            file_path = cat_dir / f"{catid}.svg"
            with open(file_path, 'w', encoding='utf-8') as sf:
                sf.write(svg_content)

            manifest_rows.append({
                'Catid': catid,
                'category': category_slug,
                'title_selected': category_name,
                'concept_notes': f"downloaded from svgapi ({icon_title})",
                'primitives_used': ','.join(primitives),
                'path_hash': path_hash,
                'width': 256,
                'height': 256,
                'stroke_width': params['stroke_width'],
                'color_hex': params['stroke_color'],
                'validation_passed': 'TRUE',
                'source_icon': source_url,
            })

        manifest_path = style_dir / 'manifest.csv'
        fieldnames = [
            'Catid', 'category', 'title_selected', 'concept_notes', 'primitives_used',
            'path_hash', 'width', 'height', 'stroke_width', 'color_hex',
            'validation_passed', 'source_icon'
        ]
        with open(manifest_path, 'w', newline='', encoding='utf-8') as mf:
            writer = csv.DictWriter(mf, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(manifest_rows)
        logging.info("Wrote %s", manifest_path)


if __name__ == "__main__":
    main()

