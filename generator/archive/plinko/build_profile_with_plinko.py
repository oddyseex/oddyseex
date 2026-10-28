"""Builds the static profile graphics: hero and loadout (desktop and phone versions).

Run from anywhere:  python3 generator/build_profile.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from design import (ACCENT, DEEP, DISC, DISPLAY, INK, LINE, MUTED, PAPER, SOFT, SURFACE, TEXT, TEXT_MED,
                    dots_h, halftone, logo, num, rect, scallop_d, stripe, surface_path, surface_rect, svg, text)

ASSETS = Path(__file__).resolve().parent.parent / "assets"

# ---------------------------------------------------------------- the board
# A triangular Plinko board. Pucks drop through the pegs and sink into red cups, which light up.
PEG = "#6d6678"        # resting peg
PEG_LIT = "#d9ccff"    # peg for a moment after a puck touches it
CUPS = 9
DROPS = [4, 2, 6, 3, 7, 1]   # which cup each puck falls into, in order
RED, RED_BAND = "#d7262c", "#a51d22"
RED_ON, RED_BAND_ON, RIM_ON = "#ff9a86", "#f06a5a", "#ffe08a"
LOOP = 20.0
GAP = 2.6
FPS = 60


def simulate(seed, G, target_x, steer):
    """One puck from the top to the floor of a bucket. Returns (frames at FPS, peg hits, bucket, seconds)."""
    import math
    import random
    rnd = random.Random(seed)
    k, r, g = G["k"], G["r"], G["g"]
    left, pitch, n = G["left"], G["pitch"], G["n"]
    x = G["cx"] + rnd.uniform(-1, 1) * pitch * 0.1
    y = -2.2 * r
    vx, vy = rnd.uniform(-10, 10) * k, 40 * k
    dt, t, step = 1 / 600, 0.0, 0
    every = round(1 / (dt * FPS))
    frames, hits = [(x, y)], []
    obst = G["pegs"] + G["caps"]
    npegs = len(G["pegs"])
    while t < 9:
        vy += g * dt
        x += vx * dt
        y += vy * dt
        t += dt
        step += 1
        if x < left + r:
            x, vx = left + r, abs(vx) * 0.4
        if x > left + n * pitch - r:
            x, vx = left + n * pitch - r, -abs(vx) * 0.4
        for i, (px, py, pr) in enumerate(obst):
            if abs(y - py) > r + pr or abs(x - px) > r + pr:
                continue
            dx, dy = x - px, y - py
            d = math.hypot(dx, dy)
            if 0 < d < r + pr:
                nx, ny = dx / d, dy / d
                x, y = px + nx * (r + pr), py + ny * (r + pr)
                vn = vx * nx + vy * ny
                if vn < 0:
                    vx -= 1.5 * vn * nx
                    vy -= 1.5 * vn * ny
                    pull = max(-1.0, min(1.0, (target_x - x) / (pitch * 4)))
                    vx += steer * pull * 55 * k + rnd.uniform(-9, 9) * k
                    if i < npegs and vn < -22 * k:
                        hits.append((t, i))
        if y > G["bucket_top"] + 0.5 * r:
            b = max(0, min(n - 1, int((x - left) / pitch)))
            lo = left + b * pitch + G["gap"] / 2 + r
            hi = left + (b + 1) * pitch - G["gap"] / 2 - r
            if x < lo:
                x, vx = lo, abs(vx) * 0.2
            elif x > hi:
                x, vx = hi, -abs(vx) * 0.2
        if y >= G["floor_y"] - r:
            y = G["floor_y"] - r
            frames.append((x, y))
            return frames, hits, max(0, min(n - 1, int((x - left) / pitch))), t
        if step % every == 0:
            frames.append((x, y))
    return None


def flash_anim(attr, base, hits, to, dur_in, dur_out):
    if not hits:
        return ""
    times, vals, last = [0.0], [base], 0.0
    for t0 in sorted(h % LOOP for h in hits):
        if t0 < last + 0.02 or t0 + dur_out > LOOP - 0.01:
            continue
        times += [t0, t0 + dur_in, t0 + dur_out]
        vals += [base, to, base]
        last = t0 + dur_out
    times.append(LOOP)
    vals.append(base)
    kt = ";".join(f"{t / LOOP:.4f}" for t in times)
    return (f'<animate attributeName="{attr}" values="{";".join(vals)}" keyTimes="{kt}" '
            f'dur="{LOOP}s" repeatCount="indefinite"/>')


def plinko(x, y, w, h, mobile=False, k=None):
    """The ink panel as a triangular Plinko board over a row of red cups, centred in the panel."""
    PX, PY, PW, PH = x, y, w, h
    k = k or w / 482
    w = 482 * k
    x, y = PX + (PW - w) / 2, PY + (PH - 536 * k) / 2
    n = CUPS
    pitch = 46 * k
    left = (w - n * pitch) / 2
    cx = left + n * pitch / 2
    r, pr = 10.5 * k, 5.5 * k
    row_h = pitch * 0.866
    top_y = 100 * k
    rows = n - 1
    pegs = []
    for row in range(rows):
        cnt = row + 1
        for i in range(cnt):
            pegs.append((cx + (i - (cnt - 1) / 2) * pitch, top_y + row * row_h, pr))
    cup_top = top_y + (rows - 1) * row_h + 46 * k
    rim_w, rim_h = 38 * k, 6 * k             # a solo cup is about 1.3 times as tall as it is wide
    body_h = 40 * k
    cup_h = rim_h + body_h
    gap = pitch - rim_w                      # space between two rims
    floor_y = cup_top + 2 * r + 6 * k        # puck is fully behind the cup by here
    caps = [(left + i * pitch, cup_top, gap / 2 + k) for i in range(1, n)]
    G = dict(k=k, r=r, g=1000 * k, left=left, pitch=pitch, n=n, cx=cx, pegs=pegs, caps=caps,
             bucket_top=cup_top, floor_y=floor_y, gap=gap)

    chosen = []
    for want in DROPS:
        tx = left + want * pitch + pitch / 2
        found = None
        for steer in (1.0, 1.6, 2.4):
            for seed in range(1, 500):
                res = simulate(seed * 7 + want, G, tx, steer)
                if res and res[2] == want and 2.0 <= res[3] <= 5.0:
                    found = res
                    break
            if found:
                break
        if not found:
            raise SystemExit(f"no drop found for cup {want}")
        chosen.append((want, found))

    peg_hits = {i: [] for i in range(len(pegs))}
    cup_hits = {i: [] for i in range(n)}
    pucks = []
    for j, (want, (frames, hits, b, dur)) in enumerate(chosen):
        start = 0.3 + j * GAP
        for ht, pi in hits:
            peg_hits[pi].append(start + ht)
        cup_hits[b].append(start + dur)
        pucks.append((j, start, start + dur, frames))

    uid = "pb"
    out = [rect(PX, PY, PW, PH, INK),
           f'<clipPath id="{uid}"><rect x="{num(PX)}" y="{num(PY)}" width="{num(PW)}" height="{num(PH)}"/></clipPath>']

    # the triangle the pegs sit in
    m_ = 0.7 * pitch
    apex_y = top_y - (m_ * 2 / pitch) * row_h
    base_r = (rows - 1) + 20 * k / row_h
    base_y = top_y + base_r * row_h
    half = base_r * pitch / 2 + m_
    out.append(f'<path d="M{num(x + cx)} {num(y + apex_y)}L{num(x + cx + half)} {num(y + base_y)}'
               f'L{num(x + cx - half)} {num(y + base_y)}Z" fill="{DISC}"/>')

    for i, (px, py, _) in enumerate(pegs):
        out.append(f'<circle cx="{num(x + px)}" cy="{num(y + py)}" r="{num(pr)}" fill="{PEG}">'
                   f'{flash_anim("fill", PEG, peg_hits[i], PEG_LIT, 0.03, 0.3)}</circle>')

    pk = []
    for j, start, end, frames in pucks:
        fr = [(0.0, frames[0])] + [(start + i / FPS, f) for i, f in enumerate(frames[:-1])] + [(end, frames[-1])] \
            + [(LOOP, frames[-1])]
        clean = [fr[0]]
        for f in fr[1:]:
            if f[0] > clean[-1][0] + 1e-4:
                clean.append(f)
        kt = ";".join(f"{f[0] / LOOP:.4f}" for f in clean)
        vals = ";".join(f"{num(x + f[1][0])} {num(y + f[1][1])}" for f in clean)
        color = ACCENT if j % 2 == 0 else PAPER
        pk.append(f'<circle class="puck" r="{num(r)}" fill="{color}" opacity="0">'
                  f'<animateTransform attributeName="transform" type="translate" values="{vals}" keyTimes="{kt}" '
                  f'dur="{LOOP}s" repeatCount="indefinite"/>'
                  f'<animate attributeName="opacity" values="0;1;0" keyTimes="0;{start / LOOP:.4f};{end / LOOP:.4f}" '
                  f'calcMode="discrete" dur="{LOOP}s" repeatCount="indefinite"/></circle>')
    out.append(f'<g clip-path="url(#{uid})">{"".join(pk)}</g>')

    # red solo cups, drawn after the pucks so a puck sinks in behind the rim
    tw, bw = 34 * k, 21 * k                 # body width just under the rim and at the base
    for i in range(n):
        ccx = x + left + i * pitch + pitch / 2
        ty = y + cup_top
        by = ty + cup_h
        hits = cup_hits[i]

        def lit(attr, base, on):
            return flash_anim(attr, base, hits, on, 0.04, 0.9) if hits else ""

        def side(f):          # half width of the body at fraction f of its height
            return (tw + (bw - tw) * f) / 2

        body_top = ty + rim_h
        out.append(f'<path d="M{num(ccx - side(0))} {num(body_top)}L{num(ccx + side(0))} {num(body_top)}'
                   f'L{num(ccx + side(1))} {num(by)}L{num(ccx - side(1))} {num(by)}Z" fill="{RED}">'
                   f'{lit("fill", RED, RED_ON)}</path>')
        for f0, f1 in ((0.34, 0.46), (0.62, 0.74)):
            y0, y1 = body_top + body_h * f0, body_top + body_h * f1
            out.append(f'<path d="M{num(ccx - side(f0))} {num(y0)}L{num(ccx + side(f0))} {num(y0)}'
                       f'L{num(ccx + side(f1))} {num(y1)}L{num(ccx - side(f1))} {num(y1)}Z" fill="{RED_BAND}">'
                       f'{lit("fill", RED_BAND, RED_BAND_ON)}</path>')
        out.append(f'<rect x="{num(ccx - rim_w / 2)}" y="{num(ty)}" width="{num(rim_w)}" height="{num(rim_h)}" '
                   f'rx="{num(2 * k)}" fill="{PAPER}">{lit("fill", PAPER, RIM_ON)}</rect>')
    return "".join(out), DROPS


CSS_SCENE = "@media (prefers-reduced-motion:reduce){.puck{display:none}}"


# ---------------------------------------------------------------- hero
HERO_LINES = ["BUILD $#!%,", "BREAK $#!%,", "BUILD $#!% AGAIN."]   # grawlix stands in for the swear word


def hero(mobile=False):
    """A compact banner: the line on the left, the Plinko board on the right."""
    foot_h = 0
    W, m = (480, 6) if mobile else (1000, 6)
    if mobile:
        card_w = W - 2 * m
        head_size = min(64, 100 * (card_w - 64) / max(DISPLAY.width(t, 100, -1) for t in HERO_LINES))
        lead = 1.1 * head_size
        block = DISPLAY.cap(head_size) + (len(HERO_LINES) - 1) * lead
        H_card = round(40 + block + 40 + foot_h)
        scene_h = 290
    else:
        H_card = 280
        k = H_card / 536
        panel_w = round(482 * k)
        card_w = W - 3 * m - panel_w

    avail = H_card - foot_h
    card = [surface_rect(m, m, card_w, H_card, seed=7 if not mobile else 8, scale=0.55 if not mobile else 0.5)]
    dots = [ACCENT, DEEP, PAPER]
    card.append(halftone(m + 8, m + H_card - 8 - (6 if not mobile else 5) * (11 if not mobile else 9), 8 if not mobile else 6, 6 if not mobile else 5, 11 if not mobile else 9, 3.4 if not mobile else 2.8, dots, flip_y=True))
    card.append(halftone(m + card_w - 8 - 7 * (11 if not mobile else 9), m + 8, 8 if not mobile else 6, 5 if not mobile else 4, 11 if not mobile else 9, 3.4 if not mobile else 2.8, dots, flip_x=True))

    if mobile:
        cx = m + card_w / 2
        y = m + (avail - block) / 2 + DISPLAY.cap(head_size)
        for t in HERO_LINES:
            card.append(text(DISPLAY, t, head_size, cx, y, PAPER, "middle", -1))
            y += lead
        scene_y = m + H_card + m
        H = scene_y + scene_h + m
        scene, _ = plinko(m, scene_y, card_w, scene_h, True, k=scene_h / 536)
    else:
        cx = m + card_w / 2
        # the three lines are the whole banner: as large as the card's height and width allow, centred
        head_size = min(100 * (card_w - 120) / max(DISPLAY.width(t, 100, -1) for t in HERO_LINES),
                        (avail - 70) / (DISPLAY.cap(1) + (len(HERO_LINES) - 1) * 1.1))
        lead = head_size * 1.1
        block = DISPLAY.cap(head_size) + (len(HERO_LINES) - 1) * lead
        y = m + (avail - block) / 2 + DISPLAY.cap(head_size)
        for t in HERO_LINES:
            card.append(text(DISPLAY, t, head_size, cx, y, PAPER, "middle", -1))
            y += lead
        H = m + H_card + m
        scene, _ = plinko(m + card_w + m, m, W - 3 * m - card_w, H_card, False, k=k)

    body = rect(0, 0, W, H, ACCENT) + "".join(card) + scene
    return svg(W, H, body, "Build $#!%, break $#!%, build $#!% again",
               "Beside the words, an animated triangular Plinko board where pucks drop into red cups that light up when a puck drops in.", CSS_SCENE)


# ---------------------------------------------------------------- loadout
TOOLS = [("3D creation", "blender", None), ("Game engine", "unrealengine", None), ("Code editor", "vscode", None)]
# each language in its own brand colour (hex values from the Simple Icons data)
LANGS = [("lua", ".lua", "#2C2D72"), ("python", ".py", None), ("javascript", ".js", "#F7DF1E"),
         ("swift", ".swift", None), ("kotlin", ".kt", None)]
ALT = {"blender": "Blender", "unrealengine": "Unreal Engine", "vscode": "VS Code", "lua": "Lua", "python": "Python",
       "javascript": "JavaScript", "swift": "Swift", "kotlin": "Kotlin"}


def loadout(mobile=False):
    if mobile:
        W, m = 480, 6
        sheet_x, sheet_w = m, W - 2 * m
        pad = 30
        title_size, group_size, desc_size, note_size = 52, 30, 20, 19
        tile, ltile = 48, 40
    else:
        W, m = 1000, 6
        sheet_w = W - 2 * m
        sheet_x = m
        pad = 150
        title_size, group_size, desc_size, note_size = 58, 34, 22, 21
        tile, ltile = 56, 44
    inner_l, inner_r = sheet_x + pad, sheet_x + sheet_w - pad
    cx = sheet_x + sheet_w / 2

    y = m + 20 + pad * 0.8 + DISPLAY.cap(title_size)
    title_y = y
    y += 26 + TEXT.cap(note_size)
    note_y = y
    y += 60 + DISPLAY.cap(group_size)
    g1_y = y
    y += 30
    tool_rows = []
    for desc, key, mono in TOOLS:
        tool_rows.append((y, desc, key, mono))
        y += tile + 18
    y += -18 + 34 + DISPLAY.cap(group_size)
    g2_y = y
    y += 30
    lang_rows = []
    for key, ext, colour in LANGS:
        lang_rows.append((y, ext, key, colour))
        y += ltile + 14
    sheet_bottom = y - 14 + pad * 0.8
    sheet_top = m
    H = sheet_bottom + m

    body = [rect(0, 0, W, H, ACCENT)]
    d = scallop_d(sheet_x, sheet_top, sheet_w, sheet_bottom - sheet_top)
    body.append(surface_path(d, (sheet_x, sheet_top, sheet_w, sheet_bottom - sheet_top), seed=21, scale=0.55))
    body.append(text(DISPLAY, "LOADOUT", title_size, cx, title_y, PAPER, "middle", -1))
    body.append(text(TEXT, "Tools and languages I work in.", note_size, cx, note_y, SOFT, "middle"))
    body.append(text(DISPLAY, "Tools", group_size, cx, g1_y, PAPER, "middle"))

    def row(ry, size, key, mono, right, backing=False):
        out = [rect(inner_l, ry, size, size, INK)]
        if backing:     # the navy Lua disc disappears on a dark tile, so it sits on a white disc like on lua.org
            out.append(f'<circle cx="{num(inner_l + size / 2)}" cy="{num(ry + size / 2)}" r="{num(size * 0.8 * 0.39)}" fill="{PAPER}"/>')
        out.append(logo(key, inner_l + size * 0.1, ry + size * 0.1, size * 0.8, mono))
        yc = ry + size / 2
        rw = TEXT.width(right, desc_size)
        out.append(text(TEXT, right, desc_size, inner_r, yc + TEXT.cap(desc_size) / 2, SOFT, "end"))
        out.append(dots_h(inner_l + size + 18, inner_r - rw - 18, yc, LINE, r=2.2, pitch=11))
        return out

    for ry, desc, key, mono in tool_rows:
        body += row(ry, tile, key, mono, desc)
    body.append(text(DISPLAY, "Languages", group_size, cx, g2_y, PAPER, "middle"))
    for ry, ext, key, colour in lang_rows:
        body += row(ry, ltile, key, colour, ext, backing=key == "lua")
    alt = "Tools: " + ", ".join(ALT[k] for _, k, _ in TOOLS) + ". Languages: " + ", ".join(ALT[k] for k, _, _ in LANGS) + "."
    return svg(W, H, "".join(body), "Loadout", alt)


def main():
    ASSETS.mkdir(exist_ok=True)
    for name, fn in (("hero", hero), ("loadout", loadout)):
        (ASSETS / f"{name}.svg").write_text(fn(False))
        (ASSETS / f"{name}-mobile.svg").write_text(fn(True))
    print("profile graphics written to", ASSETS)


if __name__ == "__main__":
    main()
