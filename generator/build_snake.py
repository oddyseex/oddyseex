"""Draws the contribution snake: a row of white squares that follows the zigzag path through the contribution
graph, one column at a time, in the shape of a snake. The output is an animated SVG that works inside a GitHub
README image.

    python3 generator/build_snake.py --login oddyseex --out dist      # real graph (needs GITHUB_TOKEN)
    python3 generator/build_snake.py --mode sample --out /tmp/x       # made-up graph, for previews only

The motion is the plain SVG path animation (animateMotion along one path), the simplest and most widely
supported kind. There is nothing else animated, and no third-party packages are needed.
"""
import argparse
import json
import os
import random
import urllib.request
from pathlib import Path

INK = "#0f0e11"
PAPER = "#ffffff"
LEVELS = ["#1f1d24", "#4a3399", "#6a45d6", "#8956fd", "#b9a0ff"]   # empty, then four strengths of purple
LEVEL_NAMES = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2, "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}

CELL, PITCH, ROWS = 12, 16, 7
PAD = 28
SPEED = 300.0                                # pixels per second along the path
HEAD = 15
BODY = [13, 13, 12.5, 12.5, 12, 11.5, 11, 10, 9, 8, 6.5, 5]   # behind the head, tapering to the tail
STEP = 11.0                                  # distance between the middles of neighbouring squares
SCALE_A, SCALE_B = "#f3edff", "#cbb8ff"      # two flat tones that alternate, like scales
TONGUE = "#ff6b5c"
LEAD = 200                                   # path before and after the graph, off screen, longer than the snake

QUERY = ("query($l:String!){user(login:$l){contributionsCollection{contributionCalendar{weeks{"
         "contributionDays{weekday contributionLevel}}}}}}")


def fetch_weeks(login, token):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"l": login}}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json", "User-Agent": "profile-snake"},
    )
    with urllib.request.urlopen(req, timeout=40) as resp:
        payload = json.load(resp)
    if "errors" in payload:
        raise RuntimeError(payload["errors"])
    weeks = payload["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    return [{d["weekday"]: LEVEL_NAMES.get(d["contributionLevel"], 0) for d in w["contributionDays"]} for w in weeks]


def sample_weeks():
    rnd = random.Random(11)
    out = []
    for _ in range(53):
        week = {}
        for r in range(ROWS):
            v = rnd.random()
            week[r] = 4 if v > .93 else 3 if v > .82 else 2 if v > .66 else 1 if v > .45 else 0
        out.append(week)
    return out


def n(v):
    return ("%.2f" % v).rstrip("0").rstrip(".")


def build(weeks):
    """A snake that hunts: it runs a Manhattan route through the contribution cells instead of sweeping every column,
    eats each one as the head crosses it, and has a head with eyes and a tongue and a scaled, tapering body."""
    cols = len(weeks)
    x_of = lambda c: c * PITCH + CELL / 2
    y_of = lambda r: r * PITCH + CELL / 2

    # visit order: left to right, and inside a column start from the end nearest the snake
    targets, cur = [], None
    for c, week in enumerate(weeks):
        rows = sorted(r for r, v in week.items() if v > 0)
        if cur is not None and rows and abs(rows[-1] - cur) < abs(rows[0] - cur):
            rows.reverse()
        for r in rows:
            targets.append((c, r))
            cur = r
    if not targets:
        targets = [(0, ROWS // 2), (cols - 1, ROWS // 2)]
    # a row for every column: straight to the cells, a slow weave across the empty stretches between them
    import math
    tcols = sorted({c for c, _ in targets})
    first_row = {}
    for c, r in targets:
        first_row.setdefault(c, r)
    keys = sorted(first_row)

    def row_at(c):
        if c in first_row:
            return first_row[c]
        lo = max((k for k in keys if k < c), default=None)
        hi = min((k for k in keys if k > c), default=None)
        if lo is None:
            base = first_row[hi]
        elif hi is None:
            base = first_row[lo]
        else:
            base = first_row[lo] + (first_row[hi] - first_row[lo]) * (c - lo) / (hi - lo)
        near = min(abs(c - k) for k in keys)
        wave = 2.2 * math.sin(c * 2 * math.pi / 10) * min(1.0, near / 3)
        return max(0, min(ROWS - 1, round(base + wave)))

    cx, cy = x_of(0) - LEAD, y_of(row_at(0))
    d = [f"M{n(cx)} {n(cy)}"]
    segs, length = [], 0.0                      # (x1, y1, x2, y2, distance at start)

    def go(tx, ty):
        nonlocal cx, cy, length
        if tx != cx:
            d.append(f"H{n(tx)}")
            segs.append((cx, cy, tx, cy, length)); length += abs(tx - cx); cx = tx
        if ty != cy:
            d.append(f"V{n(ty)}")
            segs.append((cx, cy, cx, ty, length)); length += abs(ty - cy); cy = ty

    stacks = {}
    for c, r in targets:
        stacks.setdefault(c, []).append(r)
    for c in range(cols):
        go(x_of(c), y_of(row_at(c)))
        for r in stacks.get(c, [])[1:]:
            go(x_of(c), y_of(r))
    end = x_of(cols - 1) + LEAD
    d.append(f"H{n(end)}")
    segs.append((cx, cy, end, cy, length)); length += end - cx
    d = "".join(d)
    cycle = length / SPEED

    def eaten_at(c, r):
        """Seconds until the head first crosses the middle of cell (c, r)."""
        px, py = x_of(c), y_of(r)
        for x1, y1, x2, y2, d0 in segs:
            if y1 == y2 == py and min(x1, x2) <= px <= max(x1, x2):
                return (d0 + abs(px - x1)) / SPEED
            if x1 == x2 == px and min(y1, y2) <= py <= max(y1, y2):
                return (d0 + abs(py - y1)) / SPEED
        return None

    W = (cols - 1) * PITCH + CELL
    H = (ROWS - 1) * PITCH + CELL
    vb = (-PAD, -PAD, W + 2 * PAD, H + 2 * PAD)
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb[0]} {vb[1]} {vb[2]} {vb[3]}" '
           f'width="{vb[2]}" height="{vb[3]}" role="img" '
           f'aria-label="A purple snake hunting through my GitHub contribution graph, eating the days">',
           f'<rect x="{vb[0]}" y="{vb[1]}" width="{vb[2]}" height="{vb[3]}" fill="{INK}"/>']
    for c, week in enumerate(weeks):
        for r in range(ROWS):
            if r in week:
                level = week[r]
                attrs = f'x="{c * PITCH}" y="{r * PITCH}" width="{CELL}" height="{CELL}" rx="2"'
                te = eaten_at(c, r) if level > 0 else None
                if te is None or te >= cycle - 0.4:
                    out.append(f'<rect {attrs} fill="{LEVELS[level]}"/>')
                else:
                    kt = f"0;{n(te / cycle)};{n((te + 0.14) / cycle)};{n(1 - 0.2 / cycle)}"
                    out.append(f'<rect {attrs} fill="{LEVELS[level]}"><animate attributeName="fill" calcMode="discrete" '
                               f'values="{LEVELS[level]};#ffffff;{LEVELS[0]};{LEVELS[level]}" keyTimes="{kt}" '
                               f'dur="{n(cycle)}s" repeatCount="indefinite"/></rect>')
    out.append(f'<path id="sp" d="{d}" fill="none"/>')
    lag = STEP / SPEED                                  # each body square follows the one in front
    # body, tail first so the head is drawn on top; start times only count forward from zero, since some viewers ignore negative ones
    for k in range(len(BODY), 0, -1):
        size = BODY[k - 1]
        fill = SCALE_A if k % 2 else SCALE_B
        out.append(f'<rect x="{n(-size / 2)}" y="{n(-size / 2)}" width="{n(size)}" height="{n(size)}" rx="{n(size * 0.32)}" '
                   f'fill="{fill}" stroke="{INK}" stroke-width="1.2">'
                   f'<animateMotion dur="{n(cycle)}s" begin="{n(k * lag)}s" repeatCount="indefinite">'
                   f'<mpath href="#sp"/></animateMotion></rect>')
    hs = HEAD
    out.append(
        f'<g><animateMotion dur="{n(cycle)}s" begin="0s" repeatCount="indefinite" rotate="auto"><mpath href="#sp"/></animateMotion>'
        f'<path d="M{n(hs / 2)} 0 L{n(hs / 2 + 7)} 0 M{n(hs / 2 + 7)} 0 L{n(hs / 2 + 10)} -2.4 M{n(hs / 2 + 7)} 0 L{n(hs / 2 + 10)} 2.4" '
        f'stroke="{TONGUE}" stroke-width="1.3" stroke-linecap="round" fill="none">'
        f'<animate attributeName="opacity" calcMode="discrete" values="1;0;1;0" keyTimes="0;0.25;0.5;0.75" dur="0.7s" repeatCount="indefinite"/></path>'
        f'<rect x="{n(-hs / 2)}" y="{n(-hs / 2)}" width="{hs}" height="{hs}" rx="{n(hs * 0.38)}" fill="{PAPER}" stroke="{INK}" stroke-width="1.2"/>'
        f'<circle cx="{n(hs * 0.16)}" cy="{n(-hs * 0.27)}" r="2" fill="{INK}"/>'
        f'<circle cx="{n(hs * 0.16)}" cy="{n(hs * 0.27)}" r="2" fill="{INK}"/>'
        f'<circle cx="{n(hs * 0.16 + 0.6)}" cy="{n(-hs * 0.27 - 0.5)}" r="0.7" fill="{PAPER}"/>'
        f'<circle cx="{n(hs * 0.16 + 0.6)}" cy="{n(hs * 0.27 - 0.5)}" r="0.7" fill="{PAPER}"/></g>')
    out.append("</svg>")
    return "".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["api", "sample"], default="api")
    ap.add_argument("--login", default="oddyseex")
    ap.add_argument("--out", default="dist")
    a = ap.parse_args()
    weeks = sample_weeks() if a.mode == "sample" else fetch_weeks(a.login, os.environ["GITHUB_TOKEN"])
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "github-snake.svg").write_text(build(weeks), encoding="utf-8")
    print("snake written to", out / "github-snake.svg", "mode:", a.mode)


if __name__ == "__main__":
    main()
