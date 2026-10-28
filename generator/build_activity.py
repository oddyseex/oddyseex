"""Builds assets/activity.svg (and the phone version) from live GitHub data.

    python3 generator/build_activity.py --mode api --login oddyseex     # real numbers (needs GITHUB_TOKEN)
    python3 generator/build_activity.py --mode blank                    # placeholder dashes, no numbers
    python3 generator/build_activity.py --mode sample --out /tmp/x      # made-up numbers, for previews only

The total on the receipt is GitHub's own contribution count for the last year. The rows above it add up to
that total exactly: the four counted kinds plus one "Private and other" row that holds the remainder.
"""
import argparse
import datetime as dt
import json
import os
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from design import (DISPLAY, INK, LINE, MUTED, ACCENT, PAPER, SOFT, SURFACE, TEXT, TEXT_MED, blots, dots_h, dots_v, num, rect,
                    svg, text, ticket_d, ticket_stack_d, zigzag_bottom)

ASSETS = Path(__file__).resolve().parent.parent / "assets"
API = "https://api.github.com/graphql"


# ------------------------------------------------------------------ data
def gql(query, variables, token):
    req = urllib.request.Request(
        API,
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json", "User-Agent": "profile-activity"},
    )
    with urllib.request.urlopen(req, timeout=40) as resp:
        payload = json.load(resp)
    if "errors" in payload:
        raise RuntimeError(payload["errors"])
    return payload["data"]


CAL = "contributionCalendar{totalContributions weeks{contributionDays{date contributionCount}}}"
Q_USER = "query($l:String!){user(login:$l){createdAt contributionsCollection{totalCommitContributions " \
         "totalIssueContributions totalPullRequestContributions totalPullRequestReviewContributions " + CAL + "}}}"
Q_YEAR = "query($l:String!,$f:DateTime!,$t:DateTime!){user(login:$l){contributionsCollection(from:$f,to:$t){" + CAL + "}}}"


def streaks(counts):
    """counts: {date: n}. Returns (current, longest). A streak still counts if today has nothing yet."""
    days = sorted(counts)
    longest = run = 0
    prev = None
    for d in days:
        date = dt.date.fromisoformat(d)
        if counts[d] > 0:
            run = run + 1 if prev and (date - prev).days == 1 else 1
            longest = max(longest, run)
            prev = date
        else:
            run, prev = 0, None
    today = dt.date.today()
    current, cursor = 0, today
    if counts.get(today.isoformat(), 0) == 0:
        cursor = today - dt.timedelta(days=1)
    while counts.get(cursor.isoformat(), 0) > 0:
        current += 1
        cursor -= dt.timedelta(days=1)
    return current, longest


def fetch(login, token):
    data = gql(Q_USER, {"l": login}, token)["user"]
    last = data["contributionsCollection"]
    cal = last["contributionCalendar"]
    commits = last["totalCommitContributions"]
    prs = last["totalPullRequestContributions"]
    issues = last["totalIssueContributions"]
    reviews = last["totalPullRequestReviewContributions"]
    total = cal["totalContributions"]
    other = max(0, total - (commits + prs + issues + reviews))

    counts = {}
    created = dt.datetime.fromisoformat(data["createdAt"].replace("Z", "+00:00"))
    now = dt.datetime.now(dt.timezone.utc)
    for year in range(created.year, now.year + 1):
        start = max(created, dt.datetime(year, 1, 1, tzinfo=dt.timezone.utc))
        end = min(now, dt.datetime(year, 12, 31, 23, 59, 59, tzinfo=dt.timezone.utc))
        res = gql(Q_YEAR, {"l": login, "f": start.isoformat(), "t": end.isoformat()}, token)["user"]
        for week in res["contributionsCollection"]["contributionCalendar"]["weeks"]:
            for day in week["contributionDays"]:
                counts[day["date"]] = day["contributionCount"]
    current, longest = streaks(counts)
    return {"commits": commits, "pull_requests": prs, "issues": issues, "reviews": reviews, "other": other,
            "total": total, "current_streak": current, "longest_streak": longest,
            "total_all_time": sum(counts.values())}


def sample():
    d = {"commits": 612, "pull_requests": 38, "issues": 21, "reviews": 17, "other": 64}
    d["total"] = sum(d.values())
    d.update(current_streak=14, longest_streak=63, total_all_time=1204)
    return d


def blank():
    return {k: None for k in ("commits", "pull_requests", "issues", "reviews", "other", "total",
                              "current_streak", "longest_streak", "total_all_time")}


def fmt(v):
    return "—" if v is None else f"{v:,}"


# ------------------------------------------------------------------ drawing
def receipt_rows(d):
    rows = [("Commits", d["commits"]), ("Pull requests", d["pull_requests"]),
            ("Issues", d["issues"]), ("Reviews", d["reviews"])]
    if d["other"] is None or d["other"] > 0:
        rows.append(("Private and other", d["other"]))
    return rows


def slip(x, y, w, d, size_row=21, size_group=30, pad=28, row_h=46, total_h=58):
    """The receipt: purple paper, dotted leaders, inverted total row, zigzag bottom."""
    rows = receipt_rows(d)
    top = y + 44
    body_h = 44 + size_group + 14 + len(rows) * row_h + 14 + total_h
    out = []
    cap_g = DISPLAY.cap(size_group)
    ty = y + body_h - total_h
    # one charcoal sheet with a zigzag bottom, inked like the other sections; a dotted rule sets the total apart
    tooth, depth = 16, 10
    n = max(1, int(w // tooth))
    seg = w / n
    sd = f"M{num(x)} {num(y)}H{num(x + w)}V{num(y + body_h)}"
    for i in range(n):
        px = x + w - (i + 1) * seg
        sd += f"L{num(px + seg / 2)} {num(y + body_h + depth)}L{num(px)} {num(y + body_h)}"
    sd += "Z"
    out.append(f'<clipPath id="slipc"><path d="{sd}"/></clipPath><path d="{sd}" fill="{SURFACE}"/>'
               f'<g clip-path="url(#slipc)">{blots(x, y, w, body_h + depth, 33, 0.5)}</g>')
    out.append(dots_h(x + pad, x + w - pad, ty, LINE, r=2.2, pitch=11))
    out.append(text(DISPLAY, "Last year", size_group, x + pad, y + 44 + cap_g - 6, PAPER))
    ry = y + 44 + size_group + 10
    for label, value in rows:
        base = ry + row_h / 2 + TEXT.cap(size_row) / 2
        vtxt = fmt(value)
        out.append(text(TEXT, label, size_row, x + pad, base, PAPER))
        out.append(text(TEXT_MED, vtxt, size_row, x + w - pad, base, PAPER, "end"))
        x1 = x + pad + TEXT.width(label, size_row) + 12
        x2 = x + w - pad - TEXT_MED.width(vtxt, size_row) - 12
        if x2 > x1 + 20:
            out.append(dots_h(x1, x2, base - 4, PAPER, r=2.2, pitch=11))
        ry += row_h
    tb = ty + total_h / 2 + DISPLAY.cap(size_group - 2) / 2
    out.append(text(DISPLAY, "Total", size_group - 2, x + pad, tb, PAPER))
    out.append(text(DISPLAY, fmt(d["total"]), size_group - 2, x + w - pad, tb, PAPER, "end"))
    return "".join(out), body_h + 10


def streak_ticket_wide(x, y, w, h, d):
    col = w / 3
    notches = [x + col, x + 2 * col]
    d_path = ticket_d(x, y, w, h, notches)
    out = [f'<clipPath id="tk"><path d="{d_path}"/></clipPath>',
           f'<path d="{d_path}" fill="{SURFACE}"/>',
           f'<g clip-path="url(#tk)">{blots(x, y, w, h, 31, 0.5)}</g>']
    cells = [("Current streak, days", d["current_streak"]), ("Longest streak, days", d["longest_streak"]),
             ("Contributions, all time", d["total_all_time"])]
    for i, (label, value) in enumerate(cells):
        cx = x + col * i + col / 2
        out.append(text(TEXT, label, 22, cx, y + 54, PAPER if i == 0 else SOFT, "middle"))
        out.append(text(DISPLAY, fmt(value), 104, cx, y + h - 40, PAPER, "middle"))
    for nx in notches:
        out.append(dots_v(nx, y + 36, y + h - 36, LINE, r=3, pitch=14))
    return "".join(out)


def streak_ticket_stack(x, y, w, d, row_h=108):
    h = row_h * 3
    notches = [y + row_h, y + 2 * row_h]
    d_path = ticket_stack_d(x, y, w, h, notches)
    out = [f'<clipPath id="tk"><path d="{d_path}"/></clipPath>',
           f'<path d="{d_path}" fill="{SURFACE}"/>',
           f'<g clip-path="url(#tk)">{blots(x, y, w, h, 32, 0.5)}</g>']
    cells = [("Current streak, days", d["current_streak"]), ("Longest streak, days", d["longest_streak"]),
             ("Contributions, all time", d["total_all_time"])]
    for i, (label, value) in enumerate(cells):
        ry = y + i * row_h
        base = ry + row_h / 2
        out.append(text(TEXT, label, 21, x + 24, base + TEXT.cap(21) / 2, PAPER if i == 0 else SOFT))
        out.append(text(DISPLAY, fmt(value), 76, x + w - 24, base + DISPLAY.cap(76) / 2, PAPER, "end"))
    for ny in notches:
        out.append(dots_h(x + 30, x + w - 30, ny, LINE, r=3, pitch=14))
    return "".join(out), h


def activity(d, mobile=False):
    if mobile:
        W, m = 480, 12
        pad = 24
    else:
        W, m = 1000, 40
        pad = 40
    out = []
    # heading and note
    hsize = 56
    y = m + pad * (0.6 if mobile else 0) + DISPLAY.cap(hsize)
    heading_y = y
    note = "Contributions on my GitHub profile, refreshed every day."
    note_size = 20
    note_lines = TEXT.balanced(note, note_size, (W - 2 * m - 2 * pad) if mobile else 340)
    y += 22 + TEXT.cap(note_size)
    note_ys = []
    for _ in note_lines:
        note_ys.append(y)
        y += note_size * 1.45

    if mobile:
        total_txt = fmt(d["total"])
        tsize = min(210, 100 * (W - 2 * m - 2 * pad) / DISPLAY.width(total_txt, 100, -2))
        y += 26 + DISPLAY.cap(tsize)
        total_y = y
        y += 18 + TEXT.cap(22)
        cap_y = y
        y += 44
        slip_w = W - 2 * m - 2 * pad + 2 * 12
        slip_x = (W - slip_w) / 2
        slip_svg, slip_h = slip(slip_x, y, slip_w, d, size_row=21, pad=24, row_h=46)
        y += slip_h + 40
        tick_svg, tick_h = streak_ticket_stack(m + 0, y, W - 2 * m, d)
        y += tick_h
        H = y + m
        body = [rect(0, 0, W, H, INK), text(DISPLAY, "Activity", hsize, m + pad, heading_y, PAPER)]
        for ln, ly in zip(note_lines, note_ys):
            body.append(text(TEXT, ln, note_size, m + pad, ly, SOFT))
        body.append(text(DISPLAY, total_txt, tsize, m + pad - 4, total_y, ACCENT, track=-2))
        body.append(text(TEXT, "contributions in the last year", 22, m + pad, cap_y, PAPER))
        body.append(slip_svg)
        body.append(tick_svg)
    else:
        slip_w = 400
        slip_x = W - m - slip_w
        slip_svg, slip_h = slip(slip_x, m, slip_w, d)
        slip_bottom = m + slip_h
        total_txt = fmt(d["total"])
        tsize = min(280, 100 * 460 / DISPLAY.width(total_txt, 100, -2))
        cap_y = slip_bottom - 8
        total_y = cap_y - 22 - TEXT.cap(22) - 14
        y_ticket = slip_bottom + 52
        tick_h = 190
        tick_svg = streak_ticket_wide(m, y_ticket, W - 2 * m, tick_h, d)
        H = y_ticket + tick_h + m
        body = [rect(0, 0, W, H, INK), text(DISPLAY, "Activity", hsize, m, heading_y, PAPER)]
        for ln, ly in zip(note_lines, note_ys):
            body.append(text(TEXT, ln, note_size, m, ly, SOFT))
        body.append(text(DISPLAY, total_txt, tsize, m - 6, total_y, ACCENT, track=-2))
        body.append(text(TEXT, "contributions in the last year", 22, m, cap_y, PAPER))
        body.append(slip_svg)
        body.append(tick_svg)
    desc = ("GitHub activity. "
            + ("Numbers are filled in daily from GitHub." if d["total"] is None else
               f"{fmt(d['total'])} contributions in the last year. Current streak {fmt(d['current_streak'])} days, "
               f"longest streak {fmt(d['longest_streak'])} days, {fmt(d['total_all_time'])} contributions all time."))
    return svg(W, H, "".join(body), "Activity", desc)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["api", "blank", "sample"], default="api")
    ap.add_argument("--login", default="oddyseex")
    ap.add_argument("--out", default=str(ASSETS))
    args = ap.parse_args()
    if args.mode == "api":
        token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
        if not token:
            sys.exit("GITHUB_TOKEN is not set")
        data = fetch(args.login, token)
    elif args.mode == "sample":
        data = sample()
    else:
        data = blank()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "activity.svg").write_text(activity(data, False))
    (out / "activity-mobile.svg").write_text(activity(data, True))
    print("activity graphics written to", out, "mode:", args.mode)


if __name__ == "__main__":
    main()
