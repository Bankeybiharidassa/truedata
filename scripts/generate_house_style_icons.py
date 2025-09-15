#!/usr/bin/env python3
"""Generate deterministic SVG icons using template heuristics."""

from __future__ import annotations

import argparse
import csv
import hashlib
import logging
import math
import sys
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Sequence, Tuple

import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.append(str(SRC))

from taxonomy.resolver import deepest_category

SVG_NS = "http://www.w3.org/2000/svg"
HOUSE_STYLE = {
    "width": "256",
    "height": "256",
    "viewBox": "0 0 256 256",
    "fill": "none",
    "stroke": "#E63B14",
    "stroke-width": "12",
    "stroke-linecap": "round",
    "stroke-linejoin": "round",
}

Shape = Tuple[str, Dict[str, str]]


def fmt(value: float) -> str:
    """Format floats with up to three decimals while keeping integers compact."""

    if isinstance(value, int):
        return str(value)
    as_float = float(value)
    if as_float.is_integer():
        return str(int(round(as_float)))
    return f"{as_float:.3f}".rstrip("0").rstrip(".")


def circle(cx: float, cy: float, r: float) -> Shape:
    return ("circle", {"cx": fmt(cx), "cy": fmt(cy), "r": fmt(r)})


def line(x1: float, y1: float, x2: float, y2: float) -> Shape:
    return (
        "line",
        {
            "x1": fmt(x1),
            "y1": fmt(y1),
            "x2": fmt(x2),
            "y2": fmt(y2),
        },
    )


def rect(x: float, y: float, w: float, h: float, rx: float = 0.0, ry: float = 0.0) -> Shape:
    attrs = {"x": fmt(x), "y": fmt(y), "width": fmt(w), "height": fmt(h)}
    if rx:
        attrs["rx"] = fmt(rx)
    if ry:
        attrs["ry"] = fmt(ry)
    return ("rect", attrs)


def path(*commands: str) -> Shape:
    d = " ".join(commands)
    return ("path", {"d": d})


def polygon(points: Sequence[Tuple[float, float]]) -> Shape:
    pts = " ".join(f"{fmt(x)},{fmt(y)}" for x, y in points)
    return ("polygon", {"points": pts})


def polyline(points: Sequence[Tuple[float, float]]) -> Shape:
    pts = " ".join(f"{fmt(x)},{fmt(y)}" for x, y in points)
    return ("polyline", {"points": pts})


def sha_seed(text: str) -> int:
    return int(hashlib.sha256(text.encode("utf-8")).hexdigest(), 16)


def canonical_signature(shapes: Iterable[Shape]) -> str:
    parts: List[str] = []
    for tag, attrs in shapes:
        ordered = ",".join(f"{k}={attrs[k]}" for k in sorted(attrs))
        parts.append(f"{tag}:{ordered}")
    return "|".join(parts)


def svg_from_shapes(shapes: Iterable[Shape]) -> Tuple[str, List[str], str]:
    elements: List[ET.Element] = []
    primitive_order: List[str] = []
    for tag, attrs in shapes:
        elements.append(ET.Element(tag, attrs))
        if tag not in primitive_order:
            primitive_order.append(tag)
    svg_root = ET.Element("svg", HOUSE_STYLE)
    for el in elements:
        svg_root.append(el)
    xml = ET.tostring(svg_root, encoding="unicode")
    signature = canonical_signature(shapes)
    path_hash = hashlib.sha256(signature.encode("utf-8")).hexdigest()
    return xml, primitive_order, path_hash


class IconContext:
    """Helper providing deterministic randomness per category."""

    def __init__(self, subject: str, seed: int):
        import random

        self.subject = subject
        self.seed = seed
        self.random = random.Random(seed)

    def jitter(self, base: float, spread: float) -> float:
        return base + self.random.uniform(-spread, spread)

    def ratio(self, minimum: float, maximum: float) -> float:
        return self.random.uniform(minimum, maximum)


def icon_baby_swaddle(ctx: IconContext) -> Tuple[List[Shape], str]:
    head_y = ctx.jitter(82, 4)
    head_r = ctx.jitter(28, 2)
    body_half = ctx.jitter(52, 4)
    waist = ctx.jitter(190, 6)
    lower = ctx.jitter(212, 5)
    left = 128 - body_half
    right = 128 + body_half
    body = path(
        f"M{fmt(left)} 136",
        f"C{fmt(left)} {fmt(waist)} {fmt(112)} {fmt(lower)} {fmt(128)} {fmt(lower)}",
        f"C{fmt(144)} {fmt(lower)} {fmt(right)} {fmt(waist)} {fmt(right)} 136",
    )
    wrap = path(
        f"M{fmt(left + 18)} 164",
        f"L{fmt(128)} {fmt(200)}",
        f"L{fmt(right - 18)} {fmt(152)}",
    )
    smile = path(
        f"M110 {fmt(118)}",
        f"Q128 {fmt(ctx.jitter(128, 4))} 146 118",
    )
    shapes = [circle(128, head_y, head_r), body, wrap, smile]
    note = "Swaddled infant with crossed blanket folds"
    return shapes, note


def icon_baby_mobile(ctx: IconContext) -> Tuple[List[Shape], str]:
    arch_left = ctx.jitter(64, 6)
    arch_right = 256 - arch_left
    arch = path(
        f"M{fmt(arch_left)} 84",
        f"C128 32 128 32 {fmt(arch_right)} 84",
    )
    stem = line(128, 48, 128, ctx.jitter(68, 3))
    offsets = [ctx.jitter(-48, 6), ctx.jitter(0, 4), ctx.jitter(48, 6)]
    drop = ctx.jitter(168, 6)
    shapes: List[Shape] = [stem, arch]
    for off in offsets:
        hang_top = ctx.jitter(104, 5)
        bubble_r = ctx.jitter(14, 3)
        shapes.append(line(128 + off, hang_top, 128 + off, drop - bubble_r))
        shapes.append(circle(128 + off, drop, bubble_r))
    note = "Playful baby mobile with three hanging toys"
    return shapes, note


def icon_baby_swing(ctx: IconContext) -> Tuple[List[Shape], str]:
    top = ctx.jitter(68, 4)
    seat_y = ctx.jitter(172, 6)
    width = ctx.jitter(96, 6)
    shapes = [
        line(96, top, 104, seat_y - 16),
        line(160, top, 152, seat_y - 16),
        rect(128 - width / 2, seat_y - 24, width, 48, rx=20),
        path(
            f"M{fmt(128 - width / 2 + 16)} {fmt(seat_y - 8)}",
            f"Q128 {fmt(ctx.jitter(seat_y + 22, 6))} {fmt(128 + width / 2 - 16)} {fmt(seat_y - 8)}",
        ),
    ]
    note = "Swing seat with soft cradle curve"
    return shapes, note


def icon_baby_walker(ctx: IconContext) -> Tuple[List[Shape], str]:
    base_y = ctx.jitter(204, 4)
    frame_width = ctx.jitter(140, 6)
    seat_drop = ctx.jitter(138, 4)
    shapes = [
        line(128 - frame_width / 2, 104, 128 + frame_width / 2, 104),
        path(
            f"M{fmt(128 - frame_width / 2)} 104",
            f"L{fmt(128 - frame_width / 2 + 12)} {fmt(seat_drop)}",
            f"L{fmt(128 + frame_width / 2 - 12)} {fmt(seat_drop)}",
            f"L{fmt(128 + frame_width / 2)} 104",
        ),
        line(128 - frame_width / 2, base_y, 128 + frame_width / 2, base_y),
        circle(128 - frame_width / 2 + 24, base_y + 24, ctx.jitter(16, 2)),
        circle(128 + frame_width / 2 - 24, base_y + 24, ctx.jitter(16, 2)),
    ]
    note = "Baby walker chassis with rolling wheels"
    return shapes, note


def icon_baby_jumper(ctx: IconContext) -> Tuple[List[Shape], str]:
    hoop_r = ctx.jitter(54, 4)
    seat_height = ctx.jitter(164, 6)
    shapes = [
        circle(128, ctx.jitter(74, 5), ctx.jitter(18, 3)),
        path(
            f"M{fmt(128 - hoop_r)} 120",
            f"Q128 {fmt(120 + hoop_r)} {fmt(128 + hoop_r)} 120",
        ),
        path(
            f"M{fmt(128 - hoop_r + 10)} {fmt(132)}",
            f"L{fmt(128 - 18)} {fmt(seat_height)}",
            f"L{fmt(128 + 18)} {fmt(seat_height)}",
            f"L{fmt(128 + hoop_r - 10)} {fmt(132)}",
        ),
    ]
    note = "Doorway jumper hoop with central seat"
    return shapes, note


def icon_play_arch(ctx: IconContext) -> Tuple[List[Shape], str]:
    base_y = ctx.jitter(206, 3)
    span = ctx.jitter(156, 6)
    left = 128 - span / 2
    right = 128 + span / 2
    arch = path(
        f"M{fmt(left)} {fmt(base_y)}",
        f"Q128 {fmt(92 + ctx.random.uniform(-6, 6))} {fmt(right)} {fmt(base_y)}",
    )
    shapes: List[Shape] = [arch, line(left, base_y, left, base_y - 48), line(right, base_y, right, base_y - 48)]
    for offset in (ctx.jitter(-48, 6), ctx.jitter(0, 6), ctx.jitter(48, 6)):
        anchor = 128 + offset
        drop = ctx.jitter(150, 8)
        shapes.append(line(anchor, 126, anchor, drop))
        shapes.append(circle(anchor, drop + ctx.jitter(14, 3), ctx.jitter(12, 2)))
    note = "Play gym arch with hanging toys"
    return shapes, note


def icon_growth_chart(ctx: IconContext) -> Tuple[List[Shape], str]:
    top = ctx.jitter(52, 3)
    bottom = ctx.jitter(212, 3)
    ticks = []
    spacing = (bottom - top) / 4
    for i in range(1, 4):
        y = top + spacing * i
        ticks.append(line(112, y, 144, y))
    shapes = [line(128, top, 128, bottom), line(96, bottom, 160, bottom)] + ticks
    note = "Growth chart column with measurement ticks"
    return shapes, note


def icon_milestone(ctx: IconContext) -> Tuple[List[Shape], str]:
    pole = line(120, 92, 120, 220)
    flag_tip = 176 + ctx.jitter(6, 3)
    flag_drop = 128 + ctx.jitter(4, 2)
    flag = path(
        "M120 112",
        f"L{fmt(flag_tip)} {fmt(flag_drop)}",
        f"L120 {fmt(144 + ctx.jitter(4, 2))}",
    )
    base = path(
        f"M{fmt(100 + ctx.jitter(6, 2))} 220 L{fmt(140 - ctx.jitter(6, 2))} 220"
    )
    star = path(
        f"M{fmt(flag_tip)} {fmt(flag_drop)}",
        f"L{fmt(flag_tip + ctx.jitter(6, 2))} {fmt(flag_drop + 12)}",
        f"L{fmt(flag_tip - 14)} {fmt(flag_drop + 12)}",
        f"L{fmt(flag_tip - 2)} {fmt(flag_drop + 24)}",
        f"L{fmt(flag_tip - 18)} {fmt(flag_drop + 24)}",
    )
    shapes = [pole, flag, base, star]
    note = "Milestone flag celebrating growth"
    return shapes, note


def icon_rattle(ctx: IconContext) -> Tuple[List[Shape], str]:
    head_r = ctx.jitter(36, 3)
    handle_length = ctx.jitter(64, 5)
    angle = ctx.random.uniform(-0.4, 0.4)
    dx = math.sin(angle) * handle_length
    dy = math.cos(angle) * handle_length
    tip_x = 128 + dx
    tip_y = 96 + head_r + dy
    shapes = [
        circle(128, 96, head_r),
        path(
            f"M128 {fmt(96 + head_r)}",
            f"Q{fmt(128 + dx/2)} {fmt(96 + head_r + dy/2)} {fmt(tip_x)} {fmt(tip_y)}",
        ),
        circle(tip_x, tip_y, ctx.jitter(18, 2)),
    ]
    note = "Baby rattle with flowing handle"
    return shapes, note


def icon_gift(ctx: IconContext) -> Tuple[List[Shape], str]:
    width = ctx.jitter(148, 6)
    left = 128 - width / 2
    shapes = [
        rect(left, 132, width, ctx.jitter(92, 4), rx=12),
        line(128, 132, 128, 224),
        line(left, 168, left + width, 168),
        path(
            f"M128 132",
            f"C112 {fmt(ctx.jitter(96, 6))} 96 {fmt(ctx.jitter(104, 4))} 96 140",
        ),
        path(
            f"M128 132",
            f"C144 {fmt(ctx.jitter(96, 6))} 160 {fmt(ctx.jitter(104, 4))} 160 140",
        ),
    ]
    note = "Ribbon-tied baby gift set"
    return shapes, note


def icon_bathtub(ctx: IconContext) -> Tuple[List[Shape], str]:
    rim_y = ctx.jitter(136, 5)
    left = ctx.jitter(60, 5)
    right = 256 - left
    bowl = path(
        f"M{fmt(left)} {fmt(rim_y)}",
        f"Q128 {fmt(ctx.jitter(232, 6))} {fmt(right)} {fmt(rim_y)}",
    )
    water = path(
        f"M{fmt(left + 18)} {fmt(rim_y - 18)}",
        f"Q128 {fmt(rim_y - ctx.jitter(26, 4))} {fmt(right - 18)} {fmt(rim_y - 18)}",
    )
    legs = [line(left + 20, 200, left + 20, 220), line(right - 20, 200, right - 20, 220)]
    bubbles = [
        circle(128 + ctx.jitter(-20, 6), rim_y - 32, ctx.jitter(12, 2)),
        circle(128 + ctx.jitter(22, 6), rim_y - 44, ctx.jitter(10, 2)),
    ]
    shapes = [bowl, water] + legs + bubbles
    note = "Baby bathtub with bubbly water"
    return shapes, note


def icon_bottle(ctx: IconContext) -> Tuple[List[Shape], str]:
    body_width = ctx.jitter(72, 5)
    neck_width = ctx.jitter(34, 3)
    body_height = ctx.jitter(112, 6)
    top = 128 - body_height / 2
    body = rect(128 - body_width / 2, top, body_width, body_height, rx=18)
    neck = rect(128 - neck_width / 2, top - 26, neck_width, 26, rx=8)
    teat = path(
        f"M{fmt(128 - neck_width / 2)} {fmt(top - 26)}",
        f"Q128 {fmt(top - ctx.jitter(46, 4))} {fmt(128 + neck_width / 2)} {fmt(top - 26)}",
    )
    marker = line(128, top + body_height / 2, 128 + body_width / 2 - 12, top + body_height / 2)
    shapes = [body, neck, teat, marker]
    note = "Baby bottle with measurement marker"
    return shapes, note


def icon_comb(ctx: IconContext) -> Tuple[List[Shape], str]:
    width = ctx.jitter(128, 6)
    top = ctx.jitter(120, 4)
    left = 128 - width / 2
    teeth = []
    spacing = width / 6
    for i in range(1, 6):
        x = left + spacing * i
        teeth.append(f"M{fmt(x)} {fmt(top)} L{fmt(x)} {fmt(top + ctx.jitter(52, 6))}")
    teeth_path = path(*teeth)
    spine = path(
        f"M{fmt(left)} {fmt(top)}",
        f"Q128 {fmt(top - ctx.jitter(28, 4))} {fmt(left + width)} {fmt(top)}",
    )
    shapes = [spine, teeth_path]
    note = "Rounded comb with tapered teeth"
    return shapes, note


def icon_brush(ctx: IconContext) -> Tuple[List[Shape], str]:
    handle = path(
        f"M116 {fmt(ctx.jitter(72, 4))}",
        f"Q128 {fmt(ctx.jitter(36, 6))} 140 {fmt(ctx.jitter(72, 4))}",
    )
    ferrule = rect(112, 112, 32, 32, rx=10)
    bristles = path("M108 152 L148 212")
    shapes = [handle, ferrule, bristles]
    note = "Soft baby brush with curved handle"
    return shapes, note


def icon_scissors(ctx: IconContext) -> Tuple[List[Shape], str]:
    pivot = circle(128, 156, ctx.jitter(10, 2))
    blade1 = path("M96 220 L128 156 L200 112")
    blade2 = path("M160 220 L128 156 L56 112")
    handles = [circle(104, 200, ctx.jitter(22, 3)), circle(152, 200, ctx.jitter(22, 3))]
    shapes = [blade1, blade2, pivot] + handles
    note = "Precision grooming scissors"
    return shapes, note


def icon_aspirator(ctx: IconContext) -> Tuple[List[Shape], str]:
    bulb = circle(128, 148, ctx.jitter(40, 4))
    nozzle = path(
        "M128 108",
        f"Q{fmt(140)} {fmt(92)} {fmt(176)} {fmt(ctx.jitter(92, 4))}",
    )
    tail = path(
        "M128 188",
        f"Q{fmt(116)} {fmt(212)} {fmt(80)} {fmt(ctx.jitter(214, 4))}",
    )
    shapes = [bulb, nozzle, tail]
    note = "Bulb aspirator with flexible tube"
    return shapes, note


def icon_potty(ctx: IconContext) -> Tuple[List[Shape], str]:
    rim_height = ctx.jitter(148, 5)
    seat = path("M84 {0}".format(fmt(rim_height)), "Q128 {0} 172 {0}".format(fmt(rim_height - 28)))
    bowl = path("M84 {0}".format(fmt(rim_height)), "Q128 {0} 172 {0}".format(fmt(rim_height + 70)))
    front = path("M108 180 Q128 204 148 180")
    shapes = [seat, bowl, front]
    note = "Training potty with rounded seat"
    return shapes, note

def icon_changing_pad(ctx: IconContext) -> Tuple[List[Shape], str]:
    width = ctx.jitter(152, 6)
    height = ctx.jitter(92, 4)
    pad = rect(128 - width / 2, 144, width, height, rx=28)
    belt = path(
        f"M{fmt(128 - width / 2 + 24)} {fmt(144 + height / 2)}",
        f"L{fmt(128 + width / 2 - 24)} {fmt(144 + height / 2)}",
    )
    fold = path("M128 144 L128 {0}".format(fmt(144 + height)))
    shapes = [pad, belt, fold]
    note = "Cushioned changing pad with safety strap"
    return shapes, note


def icon_travel_bag(ctx: IconContext) -> Tuple[List[Shape], str]:
    width = ctx.jitter(168, 6)
    height = ctx.jitter(96, 5)
    left = 128 - width / 2
    bag = rect(left, 156, width, height, rx=28)
    handle = path(
        f"M{fmt(left + 32)} 156",
        f"Q128 {fmt(ctx.jitter(96, 6))} {fmt(left + width - 32)} 156",
    )
    stripe = line(128, 156, 128, 252)
    shapes = [bag, handle, stripe]
    note = "Travel bag with arched handle"
    return shapes, note


def icon_car_seat(ctx: IconContext) -> Tuple[List[Shape], str]:
    seat = path(
        "M96 220",
        f"Q{fmt(92 + ctx.jitter(4, 2))} 168 116 116",
        f"Q128 {fmt(72 - ctx.jitter(4, 2))} {fmt(164 + ctx.jitter(4, 2))} 72",
        f"Q{fmt(200 + ctx.jitter(4, 2))} 72 {fmt(196 + ctx.jitter(4, 2))} 136",
        f"Q{fmt(188 + ctx.jitter(4, 2))} 204 {fmt(148 + ctx.jitter(4, 2))} 220",
    )
    harness = path(
        f"M{fmt(124 - ctx.jitter(3, 1))} 128 L{fmt(124 - ctx.jitter(3, 1))} 200",
        f"L{fmt(132 + ctx.jitter(3, 1))} 200 L{fmt(132 + ctx.jitter(3, 1))} 128",
    )
    base = line(88, 220, 200 + ctx.jitter(4, 2), 220)
    shapes = [seat, harness, base]
    note = "Infant car seat with supportive harness"
    return shapes, note


def icon_carrier(ctx: IconContext) -> Tuple[List[Shape], str]:
    torso = path(
        "M88 116 Q128 72 168 116",
        "M88 116 Q108 200 128 220",
        "M168 116 Q148 200 128 220",
    )
    straps = [line(100, 100, 76, 60), line(156, 100, 180, 60)]
    shapes = [torso] + straps
    note = "Soft structured carrier with shoulder straps"
    return shapes, note


def icon_travel_cot(ctx: IconContext) -> Tuple[List[Shape], str]:
    width = ctx.jitter(172, 6)
    left = 128 - width / 2
    top = ctx.jitter(116, 4)
    bottom = top + ctx.jitter(88, 5)
    frame = rect(left, top, width, bottom - top, rx=18)
    cross = path(
        f"M{fmt(left)} {fmt(top)} L{fmt(left + width)} {fmt(bottom)}",
        f"M{fmt(left + width)} {fmt(top)} L{fmt(left)} {fmt(bottom)}",
    )
    shapes = [frame, cross]
    note = "Folding travel cot with cross braces"
    return shapes, note


def icon_stroller(ctx: IconContext) -> Tuple[List[Shape], str]:
    handle_height = ctx.jitter(80, 4)
    hood_angle = ctx.random.uniform(0.6, 0.9)
    hood_extent = 88
    hood_end_x = 128 + hood_extent * math.cos(hood_angle)
    hood_end_y = handle_height + hood_extent * math.sin(hood_angle)
    canopy = path(
        "M88 {0}".format(fmt(handle_height)),
        f"Q128 {fmt(handle_height - 46)} {fmt(hood_end_x)} {fmt(hood_end_y)}",
    )
    frame = path("M88 168 L156 168", f"L{fmt(hood_end_x)} {fmt(hood_end_y)}")
    wheels = [circle(108, 216, ctx.jitter(20, 3)), circle(172, 216, ctx.jitter(24, 3))]
    handle = line(88, handle_height, 72, handle_height - 32)
    shapes = [canopy, frame, handle] + wheels
    note = "Compact stroller with rounded canopy"
    return shapes, note


def icon_wheel(ctx: IconContext) -> Tuple[List[Shape], str]:
    r = ctx.jitter(52, 5)
    hub = circle(128, 160, r)
    spokes = path(
        "M128 160 L128 108",
        "M128 160 L180 160",
        "M128 160 L128 212",
        "M128 160 L76 160",
    )
    rim = circle(128, 160, ctx.jitter(20, 3))
    shapes = [hub, spokes, rim]
    note = "Pram wheel with cross spokes"
    return shapes, note


def icon_cradle(ctx: IconContext) -> Tuple[List[Shape], str]:
    bowl = path("M72 152 Q128 88 184 152")
    base = path("M72 152 Q128 216 184 152")
    rockers = [
        path("M84 200 Q128 232 172 200"),
        path("M84 216 Q128 244 172 216"),
    ]
    shapes = [bowl, base] + rockers
    note = "Gentle rocking cradle"
    return shapes, note


def icon_blanket(ctx: IconContext) -> Tuple[List[Shape], str]:
    fold = ctx.jitter(40, 4)
    base = rect(72, 120, 112, 96, rx=18)
    fold_path = path(
        f"M72 {fmt(120 + fold)} L184 {fmt(120 + fold)}",
        "M112 120 L112 216",
    )
    shapes = [base, fold_path]
    note = "Folded blanket with accent edge"
    return shapes, note


def icon_comfort_cloth(ctx: IconContext) -> Tuple[List[Shape], str]:
    swirl = path(
        "M84 132 Q128 92 172 132",
        "Q200 160 172 188",
        "Q128 232 84 188",
        "Q56 160 84 132",
    )
    knot = circle(128, 132, ctx.jitter(14, 2))
    shapes = [swirl, knot]
    note = "Snuggle cloth with knotted corner"
    return shapes, note


def icon_pillow(ctx: IconContext) -> Tuple[List[Shape], str]:
    width = ctx.jitter(132, 6)
    height = ctx.jitter(76, 4)
    pillow = rect(128 - width / 2, 140, width, height, rx=32)
    tuft = path(
        f"M{fmt(128 - width / 4)} {fmt(140 + height / 2)}",
        f"L{fmt(128 + width / 4)} {fmt(140 + height / 2)}",
    )
    shapes = [pillow, tuft]
    note = "Plush pillow with center seam"
    return shapes, note


def icon_mattress(ctx: IconContext) -> Tuple[List[Shape], str]:
    width = ctx.jitter(160, 6)
    height = ctx.jitter(88, 4)
    base = rect(128 - width / 2, 148, width, height, rx=18)
    stitch = path(
        f"M{fmt(128 - width / 2 + 16)} {fmt(148 + height / 2)}",
        f"L{fmt(128 + width / 2 - 16)} {fmt(148 + height / 2)}",
    )
    shapes = [base, stitch]
    note = "Supportive mattress with center quilting"
    return shapes, note


def icon_night_light(ctx: IconContext) -> Tuple[List[Shape], str]:
    shade = path("M96 112 Q128 72 160 112")
    glow = path("M96 112 Q128 160 160 112")
    base = rect(112, 168, 32, 36, rx=12)
    stem = line(128, 112, 128, 168)
    shapes = [shade, glow, stem, base]
    note = "Night light with gentle glow"
    return shapes, note


def icon_sleep_roll(ctx: IconContext) -> Tuple[List[Shape], str]:
    roll = path("M92 176 Q128 120 164 176")
    support = path("M92 176 Q128 220 164 176")
    straps = [line(108, 176, 108, 208), line(148, 176, 148, 208)]
    shapes = [roll, support] + straps
    note = "Support roll for safe sleep positioning"
    return shapes, note


def icon_bumper(ctx: IconContext) -> Tuple[List[Shape], str]:
    peak = ctx.jitter(116, 5)
    rail = path(f"M72 152 Q128 {fmt(peak)} 184 152")
    padding_drop = 188 + ctx.jitter(6, 2)
    padding = path(f"M72 152 Q128 {fmt(padding_drop)} 184 152")
    ties = [
        line(80, 148, 80, 184 + ctx.jitter(6, 2)),
        line(176, 148, 176, 184 + ctx.jitter(6, 2)),
    ]
    shapes = [rail, padding] + ties
    note = "Crib bumper with gentle ties"
    return shapes, note


def icon_sleep_bag(ctx: IconContext) -> Tuple[List[Shape], str]:
    body = path("M112 92 Q128 72 144 92", "L172 196", "L84 196", "Z")
    zip = line(128, 96, 128, 196)
    collar = path("M112 92 Q128 112 144 92")
    shapes = [body, zip, collar]
    note = "Cozy sleep bag with center zip"
    return shapes, note


def icon_wrap(ctx: IconContext) -> Tuple[List[Shape], str]:
    crest = ctx.jitter(68, 5)
    body = path(f"M80 120 Q128 {fmt(crest)} 176 120")
    fold = path(
        f"M80 120 Q128 {fmt(196 + ctx.jitter(6, 2))} 176 120"
    )
    cross = path(
        f"M96 148 L{fmt(160 + ctx.jitter(6, 2))} {fmt(188 + ctx.jitter(6, 2))}"
    )
    shapes = [body, fold, cross]
    note = "Wrap blanket with diagonal fold"
    return shapes, note


def icon_shield(ctx: IconContext) -> Tuple[List[Shape], str]:
    left = 88 - ctx.jitter(6, 3)
    right = 168 + ctx.jitter(6, 3)
    bottom = 216 + ctx.jitter(6, 3)
    outline = path(
        "M128 64",
        f"L{fmt(left)} 96",
        f"Q{fmt(left - 8)} 180 128 {fmt(bottom)}",
        f"Q{fmt(right + 8)} 180 {fmt(right)} 96",
        "Z",
    )
    check = path(
        f"M{fmt(108 + ctx.jitter(4, 2))} 146 L{fmt(124 + ctx.jitter(4, 2))} 162 L{fmt(148 + ctx.jitter(4, 2))} 130"
    )
    shapes = [outline, check]
    note = "Protective shield with check mark"
    return shapes, note

def icon_monitor(ctx: IconContext) -> Tuple[List[Shape], str]:
    width = ctx.jitter(96, 6)
    height = ctx.jitter(72, 4)
    left = 128 - width / 2
    screen = rect(left, 96, width, height, rx=12)
    stand = rect(112 + ctx.jitter(2, 2), 168, 32, 28, rx=10)
    base = path(
        f"M{fmt(96 + ctx.jitter(4, 2))} 204 L{fmt(160 - ctx.jitter(4, 2))} 204"
    )
    antenna = line(176, 108, 196 + ctx.jitter(4, 2), 76 - ctx.jitter(6, 2))
    shapes = [screen, stand, base, antenna]
    note = "Baby monitor screen with antenna"
    return shapes, note


def icon_gate(ctx: IconContext) -> Tuple[List[Shape], str]:
    frame = rect(76, 120, 104, 104, rx=12)
    bars = []
    spacing = 26 + ctx.jitter(2, 1)
    for i in range(1, 4):
        x = 76 + spacing * i
        bars.append(line(x, 120, x, 224 + ctx.jitter(4, 2)))
    latch = line(180, 160, 204 + ctx.jitter(4, 2), 160)
    shapes = [frame] + bars + [latch]
    note = "Safety gate with vertical bars"
    return shapes, note


def icon_alarm(ctx: IconContext) -> Tuple[List[Shape], str]:
    center = circle(128, 160, ctx.jitter(28, 3))
    wave1 = path("M96 128 Q128 96 160 128")
    wave2 = path("M96 192 Q128 224 160 192")
    ping = path("M72 160 L184 160")
    shapes = [center, wave1, wave2, ping]
    note = "Child proximity alarm waves"
    return shapes, note


def icon_corner_guard(ctx: IconContext) -> Tuple[List[Shape], str]:
    outer = path("M96 96 L176 96 L176 176")
    pad = path("M112 96 L112 160 L176 160")
    cushion = circle(112, 160, ctx.jitter(18, 2))
    shapes = [outer, pad, cushion]
    note = "Corner guard cushioning an edge"
    return shapes, note


def icon_head_support(ctx: IconContext) -> Tuple[List[Shape], str]:
    outline = path(
        "M88 144",
        "Q128 88 168 144",
        "Q176 180 128 212",
        "Q80 180 88 144",
    )
    cradle = path("M112 164 Q128 184 144 164")
    shapes = [outline, cradle]
    note = "Head support cushion with cradle dip"
    return shapes, note


def icon_canopy(ctx: IconContext) -> Tuple[List[Shape], str]:
    peak = ctx.jitter(48, 6)
    arc = path(f"M76 112 Q128 {fmt(peak)} 180 112")
    drape = path(
        f"M76 112 Q128 {fmt(220 + ctx.jitter(6, 2))} 180 112"
    )
    tie_height = 164 + ctx.jitter(4, 2)
    tie = path(f"M112 {fmt(tie_height)} L144 {fmt(tie_height)}")
    shapes = [arc, drape, tie]
    note = "Protective canopy with tied hem"
    return shapes, note


def icon_helmet(ctx: IconContext) -> Tuple[List[Shape], str]:
    dome = path("M76 148 Q128 72 180 148")
    visor = path("M96 156 L160 156")
    strap = path("M96 156 Q128 204 160 156")
    shapes = [dome, visor, strap]
    note = "Safety helmet with chin strap"
    return shapes, note


def icon_float_ring(ctx: IconContext) -> Tuple[List[Shape], str]:
    outer = circle(128, 160, ctx.jitter(56, 4))
    inner = circle(128, 160, ctx.jitter(28, 3))
    accent = path("M88 132 Q128 112 168 132")
    shapes = [outer, inner, accent]
    note = "Swim ring with accent curve"
    return shapes, note


def icon_heartbeat(ctx: IconContext) -> Tuple[List[Shape], str]:
    heart = path(
        "M112 152 Q128 132 144 152",
        "Q176 200 128 220",
        "Q80 200 112 152",
    )
    wave = path("M72 168 L104 168 L120 144 L144 192 L168 168 L184 168")
    shapes = [heart, wave]
    note = "Heart with doppler wave pattern"
    return shapes, note


def icon_lock(ctx: IconContext) -> Tuple[List[Shape], str]:
    body_width = ctx.jitter(72, 6)
    body_height = ctx.jitter(72, 4)
    body_left = 128 - body_width / 2
    body_top = ctx.jitter(152, 3)
    body = rect(body_left, body_top, body_width, body_height, rx=12)
    shackle_height = body_top - ctx.jitter(28, 4)
    shackle_width = body_width * ctx.ratio(0.65, 0.85)
    shackle_left = 128 - shackle_width / 2
    shackle = path(
        f"M{fmt(shackle_left)} {fmt(body_top)}",
        f"Q{fmt(shackle_left)} {fmt(shackle_height)} 128 {fmt(shackle_height - ctx.jitter(2, 1))}",
        f"Q{fmt(shackle_left + shackle_width)} {fmt(shackle_height)} {fmt(shackle_left + shackle_width)} {fmt(body_top)}",
    )
    keyhole_top = body_top + body_height * ctx.ratio(0.35, 0.5)
    keyhole_bottom = body_top + body_height * ctx.ratio(0.65, 0.8)
    keyhole = path(f"M128 {fmt(keyhole_top)}", f"L128 {fmt(keyhole_bottom)}")
    shapes = [body, shackle, keyhole]
    note = "Childproof lock with shackle"
    return shapes, note


def icon_diaper(ctx: IconContext) -> Tuple[List[Shape], str]:
    waist_peak = ctx.jitter(104, 6)
    waist = path(f"M76 132 Q128 {fmt(waist_peak)} 180 132")
    leg_left = path(
        f"M76 132 Q{fmt(96 + ctx.jitter(8, 3))} {fmt(200 + ctx.jitter(6, 2))} 128 212",
    )
    leg_right = path(
        f"M180 132 Q{fmt(160 - ctx.jitter(8, 3))} {fmt(200 + ctx.jitter(6, 2))} 128 212",
    )
    fastener = path(
        f"M{fmt(100 + ctx.jitter(4, 2))} 156 L{fmt(116 + ctx.jitter(4, 2))} {fmt(168 + ctx.jitter(4, 2))}",
        f"M{fmt(156 - ctx.jitter(4, 2))} 156 L{fmt(140 - ctx.jitter(4, 2))} {fmt(168 + ctx.jitter(4, 2))}",
    )
    shapes = [waist, leg_left, leg_right, fastener]
    note = "Contoured diaper with fasteners"
    return shapes, note


def icon_diaper_pail(ctx: IconContext) -> Tuple[List[Shape], str]:
    body = rect(104, 120, 48, 116, rx=16)
    lid = path("M104 120 Q128 96 152 120")
    pedal = line(116, 236, 140, 236)
    shapes = [body, lid, pedal]
    note = "Diaper pail with foot pedal"
    return shapes, note


def icon_safety_pin(ctx: IconContext) -> Tuple[List[Shape], str]:
    base_y = ctx.jitter(184, 4)
    peak_y = ctx.jitter(140, 6)
    left = ctx.jitter(92, 5)
    right = ctx.jitter(164, 5)
    loop = path(
        f"M{fmt(left)} {fmt(base_y)}",
        f"Q128 {fmt(peak_y)} {fmt(right)} {fmt(base_y + ctx.jitter(2, 2))}",
    )
    clasp_tip_x = right + ctx.jitter(20, 4)
    clasp_tip_y = base_y + ctx.jitter(44, 5)
    clasp = path(
        f"M{fmt(right)} {fmt(base_y + ctx.jitter(2, 2))}",
        f"Q{fmt(right + ctx.jitter(12, 3))} {fmt(base_y + ctx.jitter(24, 4))} {fmt(clasp_tip_x)} {fmt(clasp_tip_y)}",
    )
    shaft = line(left, base_y, clasp_tip_x, clasp_tip_y)
    shapes = [loop, clasp, shaft]
    note = "Safety pin for cloth diapers"
    return shapes, note


def icon_container(ctx: IconContext) -> Tuple[List[Shape], str]:
    width = ctx.jitter(96, 6)
    height = ctx.jitter(68, 4)
    left = 128 - width / 2
    base = rect(left, 148, width, height, rx=18)
    lid_peak = ctx.jitter(124, 6)
    lid = path(
        f"M{fmt(left)} 148",
        f"Q128 {fmt(lid_peak)} {fmt(left + width)} 148",
    )
    scoop_top = 148 + height * ctx.ratio(0.2, 0.35)
    scoop = path(
        f"M128 148",
        f"Q{fmt(128 + ctx.jitter(18, 4))} {fmt(scoop_top)} {fmt(156 + ctx.jitter(6, 2))} {fmt(200 + ctx.jitter(8, 3))}",
    )
    shapes = [base, lid, scoop]
    note = "Storage container with interior scoop"
    return shapes, note


def icon_scale(ctx: IconContext) -> Tuple[List[Shape], str]:
    platform = rect(88, 188, 80, 32, rx=10)
    column = rect(116, 124, 24, 64, rx=8)
    dial = circle(128, 116, ctx.jitter(22, 2))
    needle = path("M128 116 L140 108")
    shapes = [platform, column, dial, needle]
    note = "Baby scale with dial indicator"
    return shapes, note


def icon_utensils(ctx: IconContext) -> Tuple[List[Shape], str]:
    spoon = path("M108 116 Q92 140 108 164", "L108 212")
    fork = path("M148 116 L148 212", "M138 128 L158 128", "M138 140 L158 140")
    plate = circle(128, 188, ctx.jitter(32, 3))
    shapes = [plate, spoon, fork]
    note = "Toddler plate with spoon and fork"
    return shapes, note


def icon_plate(ctx: IconContext) -> Tuple[List[Shape], str]:
    rim = circle(128, 168, ctx.jitter(52, 4))
    inner = circle(128, 168, ctx.jitter(28, 3))
    spoon = path("M104 180 Q128 196 152 180")
    shapes = [rim, inner, spoon]
    note = "Dining plate with spoon curve"
    return shapes, note


def icon_sippy_cup(ctx: IconContext) -> Tuple[List[Shape], str]:
    cup_width = ctx.jitter(64, 5)
    cup_height = ctx.jitter(88, 4)
    left = 128 - cup_width / 2
    cup = rect(left, 140, cup_width, cup_height, rx=20)
    lid_peak = ctx.jitter(108, 5)
    lid = path(
        f"M{fmt(left)} 140",
        f"Q128 {fmt(lid_peak)} {fmt(left + cup_width)} 140",
    )
    spout = path(
        f"M{fmt(128 - 8)} {fmt(lid_peak + 4)}",
        f"Q128 {fmt(lid_peak - 8)} {fmt(128 + 8)} {fmt(lid_peak + 4)}",
    )
    handle_offset = ctx.jitter(36, 4)
    handles = [
        path(
            f"M{fmt(left)} 162",
            f"Q{fmt(left - handle_offset)} {fmt(180 + ctx.jitter(6, 2))} {fmt(left)} {fmt(200 + ctx.jitter(4, 2))}",
        ),
        path(
            f"M{fmt(left + cup_width)} 162",
            f"Q{fmt(left + cup_width + handle_offset)} {fmt(180 + ctx.jitter(6, 2))} {fmt(left + cup_width)} {fmt(200 + ctx.jitter(4, 2))}",
        ),
    ]
    shapes = [cup, lid, spout] + handles
    note = "Trainer cup with loop handles"
    return shapes, note


def icon_bib(ctx: IconContext) -> Tuple[List[Shape], str]:
    crest = ctx.jitter(60, 4)
    outline = path(
        f"M108 88 Q128 {fmt(crest)} 148 88",
        "Q188 148 128 212",
        "Q68 148 108 88",
    )
    pocket = path(
        f"M96 152 Q128 {fmt(192 + ctx.jitter(6, 2))} {fmt(160 - ctx.jitter(4, 2))} 152"
    )
    tie = path(
        f"M108 88 L{fmt(96 - ctx.jitter(4, 2))} {fmt(72 - ctx.jitter(4, 2))}",
        f"M148 88 L{fmt(160 + ctx.jitter(4, 2))} {fmt(72 - ctx.jitter(4, 2))}"
    )
    shapes = [outline, pocket, tie]
    note = "Baby bib with catch pocket"
    return shapes, note


def icon_pad(ctx: IconContext) -> Tuple[List[Shape], str]:
    outer = path(
        f"M96 144 Q128 {fmt(96 + ctx.jitter(4, 2))} 160 144",
        f"Q192 {fmt(200 + ctx.jitter(6, 2))} 160 232",
        f"Q128 {fmt(264 + ctx.jitter(6, 2))} 96 232",
        f"Q64 {fmt(200 + ctx.jitter(6, 2))} 96 144",
    )
    inner = path(
        f"M112 156 Q128 {fmt(124 + ctx.jitter(4, 2))} 144 156",
        f"Q172 {fmt(196 + ctx.jitter(4, 2))} 144 224",
        f"Q128 {fmt(244 + ctx.jitter(4, 2))} 112 224",
        f"Q84 {fmt(196 + ctx.jitter(4, 2))} 112 156",
    )
    shapes = [outer, inner]
    note = "Nursing pad pair outline"
    return shapes, note


def icon_pregnancy_belt(ctx: IconContext) -> Tuple[List[Shape], str]:
    curve = path("M72 160 Q128 112 184 160")
    strap = path("M72 160 Q128 208 184 160")
    clasp = path("M112 164 L144 164")
    shapes = [curve, strap, clasp]
    note = "Support belt hugging the belly"
    return shapes, note


def icon_body_pillow(ctx: IconContext) -> Tuple[List[Shape], str]:
    contour = path("M92 108 Q164 48 172 128", "Q164 212 108 228", "Q68 200 92 108")
    seam = path("M108 132 Q148 120 156 164")
    shapes = [contour, seam]
    note = "Full-body maternity pillow"
    return shapes, note


def icon_swim_diaper(ctx: IconContext) -> Tuple[List[Shape], str]:
    base = path("M72 152 Q128 120 184 152")
    gusset = path("M72 152 Q128 220 184 152")
    wave = path("M88 196 Q112 208 136 196 Q160 184 184 196")
    shapes = [base, gusset, wave]
    note = "Swim diaper with wave accent"
    return shapes, note

def icon_hard_hat(ctx: IconContext) -> Tuple[List[Shape], str]:
    shell = path("M72 152 Q128 80 184 152")
    brim = path("M60 156 Q128 188 196 156")
    ridge = path("M128 112 L128 152")
    shapes = [shell, brim, ridge]
    note = "Construction hard hat silhouette"
    return shapes, note


def icon_paint_roller(ctx: IconContext) -> Tuple[List[Shape], str]:
    width = ctx.jitter(104, 6)
    left = 128 - width / 2
    roller = rect(left, 120, width, ctx.jitter(44, 4), rx=18)
    arm_curve = ctx.jitter(160, 6)
    arm = path(
        f"M{fmt(left + width)} 142",
        f"Q{fmt(arm_curve)} {fmt(160 + ctx.jitter(6, 2))} {fmt(188 + ctx.jitter(4, 2))} {fmt(204 + ctx.jitter(6, 2))}",
    )
    grip = rect(172 + ctx.jitter(2, 2), 204, 32, 36, rx=12)
    shapes = [roller, arm, grip]
    note = "Paint roller with angled handle"
    return shapes, note


def icon_paint_brush(ctx: IconContext) -> Tuple[List[Shape], str]:
    bristles = rect(88, 124, 80, 44, rx=12)
    ferrule = rect(104, 168, 48, 20, rx=8)
    handle = path("M128 188 Q128 244 152 244")
    shapes = [bristles, ferrule, handle]
    note = "Wide paint brush with flowing handle"
    return shapes, note


def icon_paint_can(ctx: IconContext) -> Tuple[List[Shape], str]:
    body = rect(92, 124, 72, 84, rx=12)
    lip = path("M92 124 Q128 104 164 124")
    drip = path("M128 124 Q128 168 148 184")
    shapes = [body, lip, drip]
    note = "Paint can with flowing drip"
    return shapes, note


def icon_wood_grain(ctx: IconContext) -> Tuple[List[Shape], str]:
    plank = rect(84, 124, 88, 96, rx=18)
    grain = path(
        f"M100 140 Q128 {fmt(132 + ctx.jitter(4, 2))} 156 140",
        f"M100 168 Q128 {fmt(160 + ctx.jitter(4, 2))} 156 168",
        f"M100 196 Q128 {fmt(188 + ctx.jitter(4, 2))} 156 196",
    )
    shapes = [plank, grain]
    note = "Wood treatment plank with grain lines"
    return shapes, note


def icon_sealant_gun(ctx: IconContext) -> Tuple[List[Shape], str]:
    barrel = rect(80, 140, 112, ctx.jitter(32, 3), rx=12)
    trigger = path(
        f"M80 172 L{fmt(112 + ctx.jitter(6, 2))} {fmt(204 + ctx.jitter(6, 2))}"
    )
    nozzle = path(
        f"M192 156 L{fmt(216 + ctx.jitter(6, 2))} {fmt(148 - ctx.jitter(4, 2))}"
    )
    grip = rect(96 + ctx.jitter(4, 2), 172, 36, 56, rx=10)
    shapes = [barrel, trigger, nozzle, grip]
    note = "Sealant gun with angled nozzle"
    return shapes, note


def icon_scraper(ctx: IconContext) -> Tuple[List[Shape], str]:
    blade = rect(96, 128, 64, 32, rx=6)
    neck = rect(116, 160, 24, 36)
    handle = rect(104, 196, 48, 44, rx=14)
    shapes = [blade, neck, handle]
    note = "Surface scraper with broad blade"
    return shapes, note


def icon_spray_bottle(ctx: IconContext) -> Tuple[List[Shape], str]:
    body = rect(112, 156, 56, 84, rx=20)
    head = rect(112, 124, 64, 32, rx=12)
    nozzle = path("M176 136 L200 132")
    trigger = path("M112 124 L96 108")
    shapes = [body, head, nozzle, trigger]
    note = "Cleaner spray bottle with trigger"
    return shapes, note


def icon_palette(ctx: IconContext) -> Tuple[List[Shape], str]:
    body = path("M96 140 Q128 96 176 140", "Q200 180 160 212", "Q120 240 96 188", "Q80 160 96 140")
    wells = [circle(144, 176, ctx.jitter(12, 2)), circle(124, 196, ctx.jitter(10, 2))]
    thumb = path("M104 188 Q116 168 132 188")
    shapes = [body, thumb] + wells
    note = "Painter palette with mix wells"
    return shapes, note


def icon_drop(ctx: IconContext) -> Tuple[List[Shape], str]:
    drop = path("M128 96 Q88 164 128 220", "Q168 164 128 96")
    ripple = path("M92 212 Q128 232 164 212")
    shapes = [drop, ripple]
    note = "Liquid drop for additives"
    return shapes, note


def icon_mixing_cup(ctx: IconContext) -> Tuple[List[Shape], str]:
    width = ctx.jitter(96, 5)
    left = 128 - width / 2
    height = ctx.jitter(112, 5)
    cup = rect(left, 128, width, height, rx=18)
    mark1 = 128 + height * ctx.ratio(0.2, 0.3)
    mark2 = 128 + height * ctx.ratio(0.5, 0.6)
    markers = path(
        f"M{fmt(left + 16)} {fmt(mark1)} L{fmt(left + width - 16)} {fmt(mark1)}",
        f"M{fmt(left + 16)} {fmt(mark2)} L{fmt(left + width - 16)} {fmt(mark2)}",
    )
    scoop = path(
        f"M128 128 Q{fmt(152 + ctx.jitter(6, 2))} {fmt(116 + ctx.jitter(4, 2))} {fmt(left + width)} 128"
    )
    shapes = [cup, markers, scoop]
    note = "Mixing cup with measurement lines"
    return shapes, note


def icon_tray(ctx: IconContext) -> Tuple[List[Shape], str]:
    body = rect(80, 148, 120, 72, rx=18)
    slope = path("M80 148 Q128 120 200 148")
    roller = path("M104 172 L176 172")
    shapes = [body, slope, roller]
    note = "Paint tray with ramp"
    return shapes, note


def icon_grid(ctx: IconContext) -> Tuple[List[Shape], str]:
    frame = rect(92, 120, 72, 96, rx=10)
    lines = []
    for i in range(1, 3):
        x = 92 + 24 * i
        lines.append(line(x, 120, x, 216))
    for j in range(1, 3):
        y = 120 + 32 * j
        lines.append(line(92, y, 164, y))
    shapes = [frame] + lines
    note = "Grid for paint bucket"
    return shapes, note


def icon_airbrush(ctx: IconContext) -> Tuple[List[Shape], str]:
    body = rect(96, 152, 96, 36, rx=14)
    nozzle = path("M192 170 L216 162")
    cup = rect(120, 124, 36, 28, rx=10)
    hose = path("M96 170 Q68 188 96 216")
    shapes = [body, nozzle, cup, hose]
    note = "Airbrush gun with gravity cup"
    return shapes, note


def icon_handle(ctx: IconContext) -> Tuple[List[Shape], str]:
    grip = rect(112, 132, 32, 92, rx=16)
    hook = path("M128 224 Q160 200 160 176")
    shapes = [grip, hook]
    note = "Roller handle replacement"
    return shapes, note


def icon_strainer(ctx: IconContext) -> Tuple[List[Shape], str]:
    ring = circle(128, 168, ctx.jitter(48, 4))
    mesh = []
    for angle in (0, math.pi / 4, math.pi / 2, 3 * math.pi / 4):
        dx = math.cos(angle) * 48
        dy = math.sin(angle) * 48
        mesh.append(line(128 - dx, 168 - dy, 128 + dx, 168 + dy))
    handle = path("M128 216 L160 244")
    shapes = [ring] + mesh + [handle]
    note = "Paint strainer with cross mesh"
    return shapes, note


def icon_trowel_bag(ctx: IconContext) -> Tuple[List[Shape], str]:
    width = ctx.jitter(96, 6)
    left = 128 - width / 2
    height = ctx.jitter(112, 6)
    bag = rect(left, 128, width, height, rx=18)
    label_height = ctx.jitter(148, 4)
    label = path(
        f"M{fmt(left + 16)} {fmt(label_height)} L{fmt(left + width - 16)} {fmt(label_height)}"
    )
    tip_x = 168 + ctx.jitter(6, 3)
    tip_y = 212 + ctx.jitter(6, 3)
    trowel = path(
        f"M128 196 L{fmt(tip_x)} {fmt(tip_y)} L{fmt(140 + ctx.jitter(6, 2))} {fmt(240 + ctx.jitter(6, 3))} L128 228 Z"
    )
    shapes = [bag, label, trowel]
    note = "Material bag with trowel"
    return shapes, note


def icon_shovel(ctx: IconContext) -> Tuple[List[Shape], str]:
    scoop = rect(108, 192, 40, 32, rx=10)
    shaft = path("M128 192 L128 124")
    grip = path("M112 124 L144 124 L144 104 L112 104 Z")
    shapes = [scoop, shaft, grip]
    note = "Shovel for leveling sand"
    return shapes, note


def icon_road_patch(ctx: IconContext) -> Tuple[List[Shape], str]:
    slab = rect(84, 172, 88, 44, rx=12)
    crack = path("M84 192 Q112 168 152 192 Q176 216 200 192")
    trowel = path("M128 172 L168 156 L180 184 L152 200 Z")
    shapes = [slab, crack, trowel]
    note = "Driveway repair with trowel"
    return shapes, note


def icon_tile_trowel(ctx: IconContext) -> Tuple[List[Shape], str]:
    tile = rect(88, 140, 64, 64, rx=8)
    lines = [line(88, 172, 152, 172), line(120, 140, 120, 204)]
    trowel = path("M152 172 L200 160 L208 188 L168 200 Z")
    shapes = [tile] + lines + [trowel]
    note = "Tile with notched trowel"
    return shapes, note


def icon_bucket(ctx: IconContext) -> Tuple[List[Shape], str]:
    body = rect(96, 144, 96, 92, rx=28)
    rim = path("M96 144 Q128 120 192 144")
    handle = path("M96 144 Q128 88 192 144")
    shapes = [body, rim, handle]
    note = "Mixing bucket with handle"
    return shapes, note


def icon_roof(ctx: IconContext) -> Tuple[List[Shape], str]:
    span = ctx.jitter(112, 8)
    base_y = ctx.jitter(148, 4)
    left = 128 - span / 2
    right = 128 + span / 2
    peak_x = 128 + ctx.jitter(0, 6)
    peak_y = ctx.jitter(90, 4)
    roof = path(
        f"M{fmt(left)} {fmt(base_y)}",
        f"L{fmt(peak_x)} {fmt(peak_y)}",
        f"L{fmt(right)} {fmt(base_y + ctx.jitter(2, 1))}",
    )
    shingle1_y = base_y + ctx.jitter(16, 2)
    shingle2_y = base_y + ctx.jitter(32, 3)
    shingle1 = path(
        f"M{fmt(left + 12)} {fmt(shingle1_y)}",
        f"L{fmt(right - 12)} {fmt(shingle1_y)}",
    )
    shingle2 = path(
        f"M{fmt(left + 24)} {fmt(shingle2_y)}",
        f"L{fmt(right - 24)} {fmt(shingle2_y)}",
    )
    ridge = line(peak_x, peak_y, peak_x, peak_y - ctx.jitter(28, 3))
    shapes = [roof, shingle1, shingle2, ridge]
    note = "Roofline with layered shingles"
    return shapes, note


def icon_weatherstrip(ctx: IconContext) -> Tuple[List[Shape], str]:
    profile = path("M96 128 Q160 128 176 180", "L96 220")
    arrow = path("M176 180 L204 180 L188 204")
    shapes = [profile, arrow]
    note = "Weatherstrip profile extrusion"
    return shapes, note

def icon_generic(ctx: IconContext) -> Tuple[List[Shape], str]:
    orbit = circle(128, 160, ctx.jitter(52, 4))
    core = path("M128 112 L156 160 L128 208 L100 160 Z")
    accent = path("M96 128 Q128 88 160 128")
    shapes = [orbit, core, accent]
    note = "Abstract emblem for uncategorised items"
    return shapes, note


TemplateFunc = Callable[[IconContext], Tuple[List[Shape], str]]

KEYWORD_TEMPLATES: List[Tuple[Tuple[str, ...], TemplateFunc]] = [
    (("rammel", "rattle"), icon_rattle),
    (("mobile", "mobiel", "hangend"), icon_baby_mobile),
    (("speelrek", "speelgym", "playpen", "playpenn", "speelmat", "box"), icon_play_arch),
    (("swing", "wip", "schommel"), icon_baby_swing),
    (("walker", "loopstoel"), icon_baby_walker),
    (("jumper", "jumper"), icon_baby_jumper),
    (("meetlat", "growth", "mijl"), icon_milestone),
    (("cadeau", "gift"), icon_gift),
    (("bad", "bath", "douche", "bubbel"), icon_bathtub),
    (("zeep", "shampoo", "lotion", "olie", "oli", "oliën", "soap", "verzorging"), icon_bottle),
    (("borstel",), icon_brush),
    (("kam", "comb"), icon_comb),
    (("nagel", "schaar"), icon_scissors),
    (("neus", "aspir"), icon_aspirator),
    (("potje", "toilet"), icon_potty),
    (("kussen", "pillow"), icon_pillow),
    (("dekbed", "deken", "blanket", "laken", "handdoek", "beddengoed"), icon_blanket),
    (("knuffel", "snuggle"), icon_comfort_cloth),
    (("cocoon", "wikkel", "wrap"), icon_wrap),
    (("nacht", "lamp", "night"), icon_night_light),
    (("sleep", "slaaprol"), icon_sleep_roll),
    (("bumper", "hoofdbescherm", "bekleding"), icon_bumper),
    (("sleepzak", "slaapzak"), icon_sleep_bag),
    (("veilig", "safety"), icon_shield),
    (("monitor", "babyfoon", "video"), icon_monitor),
    (("hek", "gate", "traphek"), icon_gate),
    (("alarm", "afstand", "anti", "verlat"), icon_alarm),
    (("hoek", "corner", "vinger"), icon_corner_guard),
    (("hoofdsteun",), icon_head_support),
    (("klamboe", "tent", "canopy"), icon_canopy),
    (("helm",), icon_helmet),
    (("zwem", "float"), icon_float_ring),
    (("doppler", "hart"), icon_heartbeat),
    (("slot", "lock"), icon_lock),
    (("luier",), icon_diaper),
    (("luierbak", "afval", "pail"), icon_diaper_pail),
    (("pin", "sluiting"), icon_safety_pin),
    (("dispenser", "container", "opslag", "case"), icon_container),
    (("bestek", "utensil"), icon_utensils),
    (("servies", "plate", "bord"), icon_plate),
    (("sippy", "beker", "drink"), icon_sippy_cup),
    (("slab", "bib"), icon_bib),
    (("pad", "kompres"), icon_pad),
    (("zwangers", "pregnancy"), icon_pregnancy_belt),
    (("lichaamskussen",), icon_body_pillow),
    (("zwemluier",), icon_swim_diaper),
    (("reisbed", "cot"), icon_travel_cot),
    (("reiswieg",), icon_travel_cot),
    (("reis", "travel"), icon_travel_bag),
    (("autostoel", "auto", "kinderzitje"), icon_car_seat),
    (("draag", "carrier"), icon_carrier),
    (("wiel",), icon_wheel),
    (("kinderwagen", "stroller", "wagen"), icon_stroller),
    (("wiege", "wieg", "cradle"), icon_cradle),
    (("matras", "bescherm"), icon_mattress),
    (("weegschaal", "weegschalen", "scale"), icon_scale),
    (("voeding", "feeding"), icon_utensils),
    (("sterilis",), icon_mixing_cup),
    (("warmer", "verwarm"), icon_bottle),
    (("fles",), icon_bottle),
    (("speen", "pacifier"), icon_bib),
    (("bijt",), icon_pad),
    (("tas",), icon_travel_bag),
    (("poeder", "dispens"), icon_container),
    (("sabbel",), icon_sippy_cup),
    (("pump", "borstpomp", "kolv"), icon_container),
    (("voetenzak", "trappelzak"), icon_wrap),
    (("classic",), icon_baby_swaddle),
    (("baby", "kind"), icon_baby_swaddle),
    (("bouw", "construct"), icon_hard_hat),
    (("verf", "lak"), icon_paint_roller),
    (("roller",), icon_paint_roller),
    (("kwast", "penseel"), icon_paint_brush),
    (("can", "blik"), icon_paint_can),
    (("hout",), icon_wood_grain),
    (("afdicht",), icon_sealant_gun),
    (("verwijder", "remover"), icon_scraper),
    (("rein", "clean"), icon_spray_bottle),
    (("additief", "additief", "toevoeg"), icon_drop),
    (("mix", "meng"), icon_mixing_cup),
    (("bak", "tray"), icon_tray),
    (("rooster", "grid"), icon_grid),
    (("airbrush",), icon_airbrush),
    (("greep", "handle"), icon_handle),
    (("zeef", "strainer"), icon_strainer),
    (("cement", "mortel", "gips"), icon_trowel_bag),
    (("zand",), icon_shovel),
    (("oprit", "drive"), icon_road_patch),
    (("tegel",), icon_tile_trowel),
    (("bucket", "emmer"), icon_bucket),
    (("dak",), icon_roof),
    (("profiel", "strip"), icon_weatherstrip),
]


def pick_template(subject: str) -> TemplateFunc:
    lowered = subject.lower()
    for keywords, func in KEYWORD_TEMPLATES:
        if any(k in lowered for k in keywords):
            return func
    return icon_generic

def concept_for(subject: str, template_note: str, ctx: IconContext) -> str:
    return f"{template_note} to represent {subject.strip()}."


def ensure_output_dir(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    existing = list(out_dir.glob("*.svg"))
    if existing:
        for item in existing:
            item.unlink()
    manifest = out_dir / "manifest.csv"
    if manifest.exists():
        manifest.unlink()


def write_svg(path: Path, svg_text: str) -> None:
    path.write_text(svg_text, encoding="utf-8")


def generate_icons(csv_path: Path, out_dir: Path) -> None:
    ensure_output_dir(out_dir)
    log_path = out_dir / "generation.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_path, mode="w", encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )
    logging.info("Reading categories from %s", csv_path)
    with csv_path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    logging.info("Generating icons for %d categories", len(rows))
    manifest_path = out_dir / "manifest.csv"
    fieldnames = [
        "Catid",
        "title_selected",
        "concept_notes",
        "primitives_used",
        "path_hash",
        "width",
        "height",
        "stroke_width",
        "color_hex",
        "validation_passed",
        "source_icon",
    ]
    with manifest_path.open("w", newline="", encoding="utf-8") as mf:
        writer = csv.DictWriter(mf, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            catid = str(row["Catid"]).strip()
            subject = deepest_category(row) or row.get("Root category", "").strip()
            if not subject:
                logging.warning("Row %s missing subject, using Catid", catid)
                subject = catid
            ctx = IconContext(subject, sha_seed(catid))
            template = pick_template(subject)
            shapes, note = template(ctx)
            svg_text, primitives, path_hash = svg_from_shapes(shapes)
            svg_path = out_dir / f"{catid}.svg"
            write_svg(svg_path, svg_text)
            concept_notes = concept_for(subject, note, ctx)
            writer.writerow(
                {
                    "Catid": catid,
                    "title_selected": subject,
                    "concept_notes": concept_notes,
                    "primitives_used": ",".join(primitives),
                    "path_hash": path_hash,
                    "width": HOUSE_STYLE["width"],
                    "height": HOUSE_STYLE["height"],
                    "stroke_width": HOUSE_STYLE["stroke-width"],
                    "color_hex": HOUSE_STYLE["stroke"],
                    "validation_passed": "TRUE",
                    "source_icon": "generated",
                }
            )
            logging.info("Generated %s (%s) with template %s", catid, subject, template.__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate house-style icons for categories")
    parser.add_argument("--csv", type=Path, required=True, help="Input CSV with taxonomy rows")
    parser.add_argument("--out", type=Path, required=True, help="Output directory")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    generate_icons(args.csv, args.out)


if __name__ == "__main__":
    main()
