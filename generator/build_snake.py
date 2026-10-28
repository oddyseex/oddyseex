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
LEVEL_NAMES = {"NONE": 0, "FIRST_QUARTER": 1, "SECOND_QUARTER": 2, "THIRD_QUARTER": 3, "FOURTH_QUARTER": 4}

CELL, PITCH, ROWS = 12, 16, 7
PAD = 28
SPEED = 140.0                                # pixels per second along the path
SIZES = [12, 12, 11, 10, 9, 8, 7]            # head first; the squares shrink toward the tail
LEAD = 130                                   # path before and after the graph, off screen, longer than the snake

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
    return [{d["weekday"]: LEVEL_NAMES[d["contributionLevel"]] for d in w["contributionDays"]} for w in weeks]


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
    cols = len(weeks)
    x_of = lambda c: c * PITCH + CELL / 2
    top, bottom = CELL / 2, (ROWS - 1) * PITCH + CELL / 2

    # one straight zigzag: down the first column, step right, up the next, and so on
    d = [f"M{n(x_of(0))} {n(top - LEAD)}V{n(bottom)}"]
    length = LEAD + (bottom - top)
    for c in range(1, cols):
        d.append(f"H{n(x_of(c))}V{n(top if c % 2 == 1 else bottom)}")
        length += PITCH + (bottom - top)
    d.append(f"V{n((bottom if (cols - 1) % 2 == 0 else top) + (LEAD if (cols - 1) % 2 == 0 else -LEAD))}")
    length += LEAD
    d = "".join(d)
    cycle = length / SPEED
    lag = PITCH / SPEED                              # each square follows the one in front one cell later

    W = (cols - 1) * PITCH + CELL
    H = (ROWS - 1) * PITCH + CELL
    vb = (-PAD, -PAD, W + 2 * PAD, H + 2 * PAD)
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb[0]} {vb[1]} {vb[2]} {vb[3]}" '
           f'width="{vb[2]}" height="{vb[3]}" role="img" '
           f'aria-label="A snake of squares winding through my GitHub contribution graph">',
           f'<rect x="{vb[0]}" y="{vb[1]}" width="{vb[2]}" height="{vb[3]}" fill="{INK}"/>']
    for c, week in enumerate(weeks):
        for r in range(ROWS):
            if r in week:
                out.append(f'<rect x="{c * PITCH}" y="{r * PITCH}" width="{CELL}" height="{CELL}" rx="2" '
                           f'fill="{LEVELS[week[r]]}"/>')
    out.append(f'<path id="sp" d="{d}" fill="none"/>')
    # tail first, so the head is drawn on top. Start times count forward from zero: some viewers ignore negative ones and the snake never moves.
    for k in range(len(SIZES) - 1, -1, -1):
        size = SIZES[k]
        begin = k * lag
        out.append(f'<rect x="{n(-size / 2)}" y="{n(-size / 2)}" width="{size}" height="{size}" rx="2" fill="{PAPER}">'
                   f'<animateMotion dur="{n(cycle)}s" begin="{n(begin)}s" repeatCount="indefinite">'
                   f'<mpath href="#sp"/></animateMotion></rect>')
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
