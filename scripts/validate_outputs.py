#!/usr/bin/env python3
"""Validate SVG outputs for style and basic semantic hints.

Usage:
    python scripts/validate_outputs.py output/test output/test2

The script scans each provided directory. If the directory directly
contains a ``manifest.csv`` it will validate the icons in that folder.
Otherwise each immediate subdirectory containing a ``manifest.csv`` is
processed. A consolidated ``validation_report.csv`` is written to the
current working directory.
"""
from __future__ import annotations

import csv
import hashlib
import pathlib
import re
import sys
from collections import defaultdict
from typing import Dict, Iterable, List, Tuple

STYLE = {
    "stroke": "#E63B14",
    "stroke-width": "12",
    "stroke-linecap": "round",
    "stroke-linejoin": "round",
    "fill": "none",
    "viewBox": "0 0 256 256",
}

FORBIDDEN_TAGS = {"style", "script", "defs", "mask", "clipPath"}
FORBIDDEN_ATTRS = {"class", "style"}

# Semantic hint keywords per token; extend as the taxonomy grows
SEM_HINTS: Dict[str, List[str]] = {
    "drill": ["drill", "tool", "bit"],
    "screw": ["screw", "bolt", "nut"],
    "laptop": ["laptop", "computer"],
}

SVG_TAG = re.compile(r"<svg[^>]*>", re.I)
ATTR = lambda k: re.compile(rf"\b{k}=['\"]([^'\"]+)['\"]", re.I)
CLEAN_TAG = re.compile(r"</?([a-zA-Z0-9:-]+)[^>]*>")


def check_style(svg_text: str) -> Tuple[bool, List[str]]:
    """Return (ok, errors) for style compliance."""
    m = SVG_TAG.search(svg_text)
    if not m:
        return False, ["no <svg> tag"]
    head = m.group(0)
    errors: List[str] = []
    vb_match = ATTR("viewBox").search(head)
    if not vb_match or vb_match.group(1) != STYLE["viewBox"]:
        errors.append("bad viewBox")
    for k, v in STYLE.items():
        if k == "viewBox":
            continue
        if f"{k}='{v}'" not in svg_text and f"{k}=\"{v}\"" not in svg_text:
            errors.append(f"missing/incorrect {k}")
    for tag in FORBIDDEN_TAGS:
        if re.search(rf"</?{tag}\b", svg_text, re.I):
            errors.append(f"forbidden tag: {tag}")
    for attr in FORBIDDEN_ATTRS:
        if re.search(rf"\s{attr}=", svg_text, re.I):
            errors.append(f"forbidden attr: {attr}")
    return (not errors), errors


def path_hash(svg_text: str) -> str:
    """Compute a stable hash for geometry."""
    norm = re.sub(r"(-?\d+\.\d{3})\d+", r"\1", svg_text)
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()[:16]


def semantic_hint_ok(subject: str, svg_text: str):
    tokens = re.findall(r"[a-z0-9]+", subject.lower())
    for t in tokens:
        for hint in SEM_HINTS.get(t, []):
            if re.search(rf"\b{hint}\b", svg_text, re.I):
                return True
    return None  # unknown


def load_manifest(p: pathlib.Path) -> Dict[str, Dict[str, str]]:
    man: Dict[str, Dict[str, str]] = {}
    mf = p / "manifest.csv"
    if mf.exists():
        with mf.open("r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                man[row.get("Catid", "")] = row
    return man


def process_dir(base: pathlib.Path,
                report: List[Dict[str, str]],
                dup_hashes: defaultdict) -> None:
    man = load_manifest(base)
    for svg in base.glob("*.svg"):
        catid = svg.stem
        svg_text = svg.read_text("utf-8", errors="ignore")
        ok_style, errs = check_style(svg_text)
        ph = path_hash(svg_text)
        dup_hashes[ph].append(str(svg))
        subject = man.get(catid, {}).get("title_selected") or man.get(catid, {}).get("concept_notes") or ""
        sem = semantic_hint_ok(subject, svg_text)
        report.append({
            "dir": str(base),
            "catid": catid,
            "subject": subject,
            "style_ok": ok_style,
            "style_errors": ";".join(errs),
            "path_hash": ph,
            "sem_match": {True: "PASS", False: "FAIL", None: "UNKNOWN"}[sem if sem is not None else None],
            "source_icon": man.get(catid, {}).get("source_icon", ""),
        })


def iter_target_dirs(paths: Iterable[pathlib.Path]) -> Iterable[pathlib.Path]:
    for root in paths:
        if (root / "manifest.csv").exists():
            yield root
        else:
            for child in sorted(root.iterdir()):
                if child.is_dir() and (child / "manifest.csv").exists():
                    yield child


def main(argv: List[str]) -> None:
    if not argv:
        argv = ["output/test", "output/test2"]
    bases = list(iter_target_dirs(map(pathlib.Path, argv)))
    report: List[Dict[str, str]] = []
    dup_hashes: defaultdict = defaultdict(list)
    for base in bases:
        process_dir(base, report, dup_hashes)
    for h, files in dup_hashes.items():
        if len(files) > 1:
            print("DUPLICATE_GEOMETRY:", h, files)
    if report:
        with open("validation_report.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(report[0].keys()))
            writer.writeheader()
            writer.writerows(report)
        print("Wrote validation_report.csv with", len(report), "rows")
    else:
        print("No icons processed")


if __name__ == "__main__":
    main(sys.argv[1:])
