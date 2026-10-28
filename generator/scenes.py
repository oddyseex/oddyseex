"""Animated hero panels that go with "Build $#!%, break $#!%, build $#!% again".

Each scene draws into the rectangle (x, y, w, h) on the hero's right-hand side and loops forever with plain SVG
animation (SMIL). Start times only count forward from zero, because some viewers ignore negative ones. All text is
converted to paths, so no fonts are needed. Flat colours only.

    buildlog(x, y, w, h, mobile)   a terminal that builds, crashes in a splat of ink, and builds again
    pixelicon(x, y, w, h, mobile)  a pixel-art controller that falls together, glitches, shatters and rebuilds
"""
import random

from design import (BLOT, DISPLAY, INK, LINE, PAPER, SOFT, SURFACE, ACCENT, TEXT, TEXT_MED, blots, num, rect, text)

CRASH = "#ff6b5c"        # error red, lifted so it reads on charcoal
_ids = [0]


def _id(prefix):
    _ids[0] += 1
    return f"{prefix}{_ids[0]}"


def _t(v, T):
    return ("%.4f" % (v / T)).rstrip("0").rstrip(".") or "0"


def window(a, b, T):
    """Opacity switch: hidden, visible from a to b seconds, hidden again, repeating every T seconds."""
    return (f'<animate attributeName="opacity" calcMode="discrete" values="0;1;0" '
            f'keyTimes="0;{_t(a, T)};{_t(b, T)}" dur="{num(T)}s" repeatCount="indefinite"/>')


def shown(a, b, T, inner):
    return f'<g opacity="0">{window(a, b, T)}{inner}</g>'


def typed(font, string, size, x, y, fill, a, b, T, hold_until):
    """Text that is typed out between a and b seconds and stays visible until hold_until."""
    cid = _id("ty")
    steps = [font.width(string[:i], size) for i in range(len(string) + 1)]
    full = steps[-1] + 2
    n = len(string)
    times = [a + (b - a) * i / n for i in range(n + 1)]
    kt = ["0"] + [_t(t, T) for t in times]
    vals = ["0"] + [num(s if i else 0) for i, s in enumerate(steps)]
    anim = (f'<animate attributeName="width" calcMode="discrete" values="{";".join(vals)}" '
            f'keyTimes="{";".join(kt)}" dur="{num(T)}s" repeatCount="indefinite"/>')
    clip = (f'<clipPath id="{cid}"><rect x="{num(x - 1)}" y="{num(y - size)}" width="0" height="{num(size * 1.4)}">{anim}'
            f'</rect></clipPath>')
    return clip + shown(a, hold_until, T, f'<g clip-path="url(#{cid})">{text(font, string, size, x, y, fill)}</g>')


def bar(x, y, w, h, fill, a, b, T, gone, colour_change=None, frac=1.0):
    """A progress bar that fills linearly between a and b seconds and is gone at `gone`."""
    anim_w = (f'<animate attributeName="width" values="0;0;{num(w * frac)};{num(w * frac)}" '
              f'keyTimes="0;{_t(a, T)};{_t(b, T)};1" dur="{num(T)}s" repeatCount="indefinite"/>')
    anim_c = ""
    if colour_change:
        t, c = colour_change
        anim_c = (f'<animate attributeName="fill" calcMode="discrete" values="{fill};{c};{fill}" '
                  f'keyTimes="0;{_t(t, T)};{_t(gone, T)}" dur="{num(T)}s" repeatCount="indefinite"/>')
    inner = (f'<rect x="{num(x)}" y="{num(y)}" width="{num(w)}" height="{num(h)}" fill="{INK}"/>'
             f'<rect x="{num(x)}" y="{num(y)}" width="0" height="{num(h)}" fill="{fill}">{anim_w}{anim_c}</rect>')
    return shown(a - 0.05, gone, T, inner)


def shake(at, T, amp, inner):
    kt = ["0", at, at + 0.06, at + 0.12, at + 0.18, at + 0.26, at + 0.34, 1 * T]
    vals = ["0 0", "0 0", f"{-amp} {amp * .3}", f"{amp} {-amp * .3}", f"{-amp * .7} 0", f"{amp * .5} {amp * .2}", "0 0", "0 0"]
    kts = ";".join(_t(float(k), T) if i not in (0, 7) else ("0" if i == 0 else "1") for i, k in enumerate(kt))
    return (f'<g><animateTransform attributeName="transform" type="translate" values="{";".join(vals)}" '
            f'keyTimes="{kts}" dur="{num(T)}s" repeatCount="indefinite"/>{inner}</g>')


# ------------------------------------------------------------------ the build log
def buildlog(x, y, w, h, mobile=False):
    T = 12.0
    p = 20 if not mobile else 28
    fs = 19 if not mobile else 22               # log text
    big = 44 if not mobile else 56               # headline in the log
    cid = _id("bl")
    iw = w - 2 * p
    lead = fs * 1.85
    x0 = x + p
    yA = y + p + TEXT.cap(fs) + (6 if not mobile else 8)
    yB1 = yA + lead
    yB2 = yB1 + lead * 0.85
    bar_y = yB2 + (16 if not mobile else 20)
    bar_h = 12 if not mobile else 16
    big_y = bar_y + bar_h + (24 if not mobile else 28) + DISPLAY.cap(big)
    sub_y = big_y + lead * 0.9

    parts = [f'<clipPath id="{cid}"><rect x="{num(x)}" y="{num(y)}" width="{num(w)}" height="{num(h)}"/></clipPath>',
             rect(x, y, w, h, SURFACE)]
    body = []

    def run(first_line, a, hold, lines_at):
        out = [shown(a, hold, T, text(TEXT_MED, ">", fs, x0, yA, ACCENT)),
               typed(TEXT_MED, first_line, fs, x0 + TEXT_MED.width("> ", fs), yA, PAPER, a + 0.1, a + 0.9, T, hold)]
        out.append(shown(lines_at[0], hold, T, text(TEXT, "compiling 57 files", fs, x0, yB1, SOFT)))
        out.append(shown(lines_at[1], hold, T, text(TEXT, "linking", fs, x0, yB2, SOFT)))
        return "".join(out)

    # first attempt, until the crash at 4.1 s
    body.append(run("build", 0.3, 6.1, (1.3, 2.0)))
    body.append(bar(x0, bar_y, iw, bar_h, ACCENT, 1.4, 4.0, T, 6.1, colour_change=(4.1, CRASH)))
    crash = [shown(4.1, 6.1, T, text(DISPLAY, "$#!% BROKE.", big, x0, big_y, CRASH, "start", -1)),
             shown(4.5, 6.1, T, text(TEXT, "exit code 1", fs, x0, sub_y, SOFT))]
    body.append(shake(4.1, T, 3.2 if not mobile else 5, "".join(crash)))
    # second attempt
    body.append(run("build again", 6.6, 11.4, (7.7, 8.2)))
    body.append(bar(x0, bar_y, iw, bar_h, ACCENT, 8.3, 10.0, T, 11.4))
    body.append(shown(10.1, 11.4, T, text(DISPLAY, "IT WORKS.", big, x0, big_y, PAPER, "start", -1)))
    body.append(shown(10.5, 11.4, T, text(TEXT, "for now.", fs, x0, sub_y, SOFT)))
    # the ink splat that lands with the crash, drawn over the error
    splat = (f'<g opacity="0"><animate attributeName="opacity" calcMode="discrete" values="0;1;0" '
             f'keyTimes="0;{_t(4.1, T)};{_t(6.1, T)}" dur="{num(T)}s" repeatCount="indefinite"/>'
             f'{blots(x + w * 0.35, y + h * 0.5, w * 0.65, h * 0.5, 5, 1.0 if not mobile else 1.2)}</g>')
    parts.append(f'<g clip-path="url(#{cid})">{splat}{"".join(body)}</g>')
    return "".join(parts)


# ------------------------------------------------------------------ the pixel controller
GRID_W, GRID_H = 18, 11


def _controller():
    """A pixel-art game controller as {(col, row): colour-key}: shaded body, grips, d-pad, sticks, buttons and an LED."""
    g = {}
    for r in range(1, 7):
        for c in range(1, 17):
            if (r == 1 and (c < 3 or c > 14)) or (r == 6 and (c < 2 or c > 15)):
                continue
            g[(c, r)] = "hi" if r == 1 else "low" if r >= 5 else "body"
    for r in range(7, 10):
        for c in list(range(2, 6)) + list(range(12, 16)):
            if r == 9 and c in (2, 15):
                continue
            g[(c, r)] = "grip" if r < 9 else "grip_low"
    for c, r in [(5, 2), (4, 3), (5, 3), (6, 3), (5, 4)]:                     # d-pad
        g[(c, r)] = "dark"
    for c, r in [(7, 5), (8, 5), (7, 6), (8, 6), (10, 5), (11, 5), (10, 6), (11, 6)]:   # sticks
        g[(c, r)] = "stick"
    for c, r in [(8, 3), (9, 3)]:                                                 # select and start
        g[(c, r)] = "dark"
    for c, r in [(8, 2), (9, 2)]:                                                 # the LED
        g[(c, r)] = "led"
    for c, r, k in [(13, 2, "hot"), (12, 3, "accent"), (14, 3, "accent"), (13, 4, "hot")]:   # buttons
        g[(c, r)] = k
    return g


COLOURS = {"hi": PAPER, "body": "#ece6ff", "low": "#d3c7f7", "grip": "#c3b4f0", "grip_low": "#a995e6",
           "dark": "#2b2833", "stick": "#3a3545", "led": "#2b2833", "accent": ACCENT, "hot": CRASH}


def pixelicon(x, y, w, h, mobile=False):
    T = 6.0
    rnd = random.Random(7)
    cell = min((w - 40) / GRID_W, (h - 56) / GRID_H)
    cell = max(6.0, cell)
    gap = max(0.6, cell * 0.04)
    ox = x + (w - GRID_W * cell) / 2
    oy = y + (h - GRID_H * cell) / 2 - cell * 0.2
    colours = COLOURS
    cid = _id("pi")
    out = [f'<clipPath id="{cid}"><rect x="{num(x)}" y="{num(y)}" width="{num(w)}" height="{num(h)}"/></clipPath>',
           rect(x, y, w, h, SURFACE)]
    cells = _controller()
    items = []
    cx_mid, cy_mid = GRID_W / 2, GRID_H / 2
    for (c, r), key in sorted(cells.items()):
        px, py = ox + c * cell, oy + r * cell
        drop = h * 0.9 + rnd.uniform(0, h * 0.4)
        start = 0.25 + ((c * 0.9 + (GRID_H - r) * 0.35) / (GRID_W + GRID_H)) * 1.35 + rnd.uniform(0, 0.18)
        land = start + 0.38
        # shatter: fly out from the middle, then fall
        ang = rnd.uniform(-3.14, 3.14)
        dx = (c - cx_mid) * cell * rnd.uniform(1.2, 2.4) + rnd.uniform(-1, 1) * cell * 2
        dy1 = (r - cy_mid) * cell * rnd.uniform(0.6, 1.6) - cell * rnd.uniform(1, 3.5)
        dy2 = dy1 + h * rnd.uniform(0.45, 0.85)
        brk = 3.6 + rnd.uniform(0, 0.12)
        gone = brk + 1.0
        gx = 0.0
        # glitch: a few rows slip sideways for a moment
        if r in (2, 5, 8):
            gx = cell * (1.5 if r == 5 else -1.2)
        fill = colours[key]
        times = [0, start, land, 2.75, 2.82, 2.9, 2.97, brk, brk + 0.45, gone, T]
        tx = [0, 0, 0, 0, gx, 0, gx * .6 if gx else 0, 0, dx * .6, dx, dx]
        ty = [-drop, -drop, 0, 0, 0, 0, 0, 0, dy1, dy2, dy2]
        vals = ";".join(f"{num(a)} {num(b)}" for a, b in zip(tx, ty))
        ktimes = ";".join(_t(t, T) if 0 < t < T else ("0" if t == 0 else "1") for t in times)
        op_vals = "0;0;1;1;0;0"
        op_kt = f"0;{_t(start, T)};{_t(start + 0.04, T)};{_t(brk + 0.5, T)};{_t(gone, T)};1"
        spin = rnd.uniform(-240, 240)
        items.append(
            f'<g opacity="0">'
            f'<animate attributeName="opacity" values="{op_vals}" keyTimes="{op_kt}" dur="{num(T)}s" repeatCount="indefinite"/>'
            f'<animateTransform attributeName="transform" type="translate" values="{vals}" keyTimes="{ktimes}" '
            f'dur="{num(T)}s" repeatCount="indefinite"/>'
            f'<g transform="translate({num(px + cell / 2)} {num(py + cell / 2)})">'
            f'<g><animateTransform attributeName="transform" type="rotate" values="0;0;{num(spin)};{num(spin)}" '
            f'keyTimes="0;{_t(brk, T)};{_t(gone, T)};1" dur="{num(T)}s" repeatCount="indefinite"/>'
            f'<rect x="{num(-cell / 2 + gap / 2)}" y="{num(-cell / 2 + gap / 2)}" width="{num(cell - gap)}" '
            f'height="{num(cell - gap)}" fill="{fill}"/></g></g></g>')
    # a flicker of the error colour across the body while it glitches
    flick = (f'<g opacity="0"><animate attributeName="opacity" calcMode="discrete" values="0;0.9;0;0.9;0" '
             f'keyTimes="0;{_t(2.75, T)};{_t(2.82, T)};{_t(2.9, T)};{_t(2.97, T)}" dur="{num(T)}s" repeatCount="indefinite"/>'
             f'<rect x="{num(ox + cell * 2)}" y="{num(oy + cell * 3.4)}" width="{num(cell * 14)}" height="{num(cell * .8)}" fill="{CRASH}"/></g>')
    # the splat where it broke
    splat = (f'<g opacity="0"><animate attributeName="opacity" calcMode="discrete" values="0;1;0" '
             f'keyTimes="0;{_t(3.65, T)};{_t(5.3, T)}" dur="{num(T)}s" repeatCount="indefinite"/>'
             f'{blots(x, y + h * 0.1, w, h * 0.9, 12, 0.8 if not mobile else 1.0)}</g>')
    out.append(f'<g clip-path="url(#{cid})">{splat}{"".join(items)}{flick}</g>')
    return "".join(out)


# ------------------------------------------------------------------ the hybrid: controller above, build log beneath
def hybrid(x, y, w, h, mobile=False):
    """The pixel controller builds while a build log runs beside it. It glitches, the log says $#!%...., the controller
    shatters and rebuilds, and the log says COMPLETE while the LED lights up."""
    T = 12.0
    rnd = random.Random(11)
    cid = _id("hy")
    side = mobile                                                         # wide panel: controller left, log right
    p = 16 if not mobile else 22
    if side:
        cell = min((w * 0.56) / GRID_W, (h - 2 * p) / GRID_H)
        ox, oy = x + p, y + (h - GRID_H * cell) / 2
        lx = ox + GRID_W * cell + 22
        lw = x + w - p - lx
    else:
        log_h = TEXT.cap(15.5) + 15.5 * 1.6 * 1.8 + 12 + 10 + 16 + DISPLAY.cap(34)
        cell = min((w - 2 * p) / GRID_W, (h - 2 * p - 24 - log_h) / GRID_H)
        stack = GRID_H * cell + 24 + log_h
        ox, oy = x + (w - GRID_W * cell) / 2, y + (h - stack) / 2
        lx, lw = x + p, w - 2 * p
    gap = max(0.6, cell * 0.04)
    fs = 15.5 if not mobile else 17
    big = 34 if not mobile else 36
    lead = fs * 1.6
    # the log's lines, top to bottom
    if side:
        block = TEXT.cap(fs) + lead * 2.2 + 18 + DISPLAY.cap(big) + 20
        top = y + (h - block) / 2
        yA = top + TEXT.cap(fs)
    else:
        yA = oy + GRID_H * cell + 24 + TEXT.cap(fs)
    yB1, yB2 = yA + lead, yA + lead * 1.8
    bar_y = yB2 + (12 if not mobile else 14)
    bar_h = 10 if not mobile else 12
    big_y = bar_y + bar_h + (16 if not mobile else 18) + DISPLAY.cap(big)

    out = [f'<clipPath id="{cid}"><rect x="{num(x)}" y="{num(y)}" width="{num(w)}" height="{num(h)}"/></clipPath>',
           rect(x, y, w, h, SURFACE)]
    out.append(blots(x, y, w, h, 9, 0.5))                              # the same quiet splatter as the other cards
    # the splat that lands when it breaks, behind everything else
    out.append(f'<g opacity="0"><animate attributeName="opacity" calcMode="discrete" values="0;1;0" '
               f'keyTimes="0;{_t(3.7, T)};{_t(6.1, T)}" dur="{num(T)}s" repeatCount="indefinite"/>'
               f'{blots(x + w * 0.1, y + h * 0.2, w * 0.9, h * 0.8, 21, 1.0 if not mobile else 1.15)}</g>')

    # ---- the controller, cell by cell
    cells = _controller()
    items = []
    cxm, cym = GRID_W / 2, GRID_H / 2
    for (c, r), key in sorted(cells.items()):
        px, py = ox + c * cell, oy + r * cell
        drop1 = h * 0.8 + rnd.uniform(0, h * 0.3)
        drop2 = h * 0.8 + rnd.uniform(0, h * 0.3)
        s1 = 0.9 + ((c * 0.9 + (GRID_H - r) * 0.4) / (GRID_W + GRID_H)) * 1.5 + rnd.uniform(0, 0.15)
        l1 = s1 + 0.38
        s2 = 6.7 + (((GRID_W - c) * 0.9 + r * 0.4) / (GRID_W + GRID_H)) * 1.4 + rnd.uniform(0, 0.15)
        l2 = s2 + 0.38
        brk = 3.75 + rnd.uniform(0, 0.12)
        fly = brk + 0.5
        gone = brk + 1.15
        dx = (c - cxm) * cell * rnd.uniform(1.2, 2.3) + rnd.uniform(-1, 1) * cell * 2
        dy1 = (r - cym) * cell * rnd.uniform(0.6, 1.5) - cell * rnd.uniform(1, 3.2)
        dy2 = dy1 + h * rnd.uniform(0.4, 0.8)
        gx = cell * (1.5 if r == 5 else -1.2) if r in (2, 5, 8) else 0.0
        spin = rnd.uniform(-240, 240)
        t = [0, s1, l1, 3.0, 3.07, 3.14, 3.21, brk, fly, gone, s2, l2, 11.8, T]
        tx = [0, 0, 0, 0, gx, 0, gx * .6, 0, dx * .6, dx, 0, 0, 0, 0]
        ty = [-drop1, -drop1, 0, 0, 0, 0, 0, 0, dy1, dy2, -drop2, 0, 0, 0]
        kt = ";".join("0" if i == 0 else "1" if i == len(t) - 1 else _t(v, T) for i, v in enumerate(t))
        vals = ";".join(f"{num(a)} {num(b)}" for a, b in zip(tx, ty))
        ot = [0, s1, s1 + 0.04, fly, gone, s2, s2 + 0.04, 11.3, 11.8, T]
        ov = [0, 0, 1, 1, 0, 0, 1, 1, 0, 0]
        okt = ";".join("0" if i == 0 else "1" if i == len(ot) - 1 else _t(v, T) for i, v in enumerate(ot))
        rt = [0, brk, gone, s2 - 0.1, s2 - 0.09, T]
        rv = [0, 0, spin, spin, 0, 0]
        rkt = ";".join("0" if i == 0 else "1" if i == len(rt) - 1 else _t(v, T) for i, v in enumerate(rt))
        fill = COLOURS[key]
        led = ""
        if key == "led":
            led = (f'<animate attributeName="fill" calcMode="discrete" values="{fill};{CRASH};{fill};{ACCENT}" '
                   f'keyTimes="0;{_t(3.3, T)};{_t(6.2, T)};{_t(8.8, T)}" dur="{num(T)}s" repeatCount="indefinite"/>')
        items.append(
            f'<g opacity="0"><animate attributeName="opacity" values="{";".join(str(v) for v in ov)}" keyTimes="{okt}" '
            f'dur="{num(T)}s" repeatCount="indefinite"/>'
            f'<animateTransform attributeName="transform" type="translate" values="{vals}" keyTimes="{kt}" dur="{num(T)}s" repeatCount="indefinite"/>'
            f'<g transform="translate({num(px + cell / 2)} {num(py + cell / 2)})"><g>'
            f'<animateTransform attributeName="transform" type="rotate" values="{";".join(num(v) for v in rv)}" keyTimes="{rkt}" dur="{num(T)}s" repeatCount="indefinite"/>'
            f'<rect x="{num(-cell / 2 + gap / 2)}" y="{num(-cell / 2 + gap / 2)}" width="{num(cell - gap)}" height="{num(cell - gap)}" fill="{fill}">{led}</rect>'
            f'</g></g></g>')
    ccx, ccy = ox + GRID_W * cell / 2, oy + GRID_H * cell / 2
    pop = (f'<g transform="translate({num(ccx)} {num(ccy)})"><g><animateTransform attributeName="transform" type="scale" '
           f'values="1;1;1.09;1;1" keyTimes="0;{_t(8.85, T)};{_t(9.0, T)};{_t(9.3, T)};1" dur="{num(T)}s" repeatCount="indefinite"/>'
           f'<g transform="translate({num(-ccx)} {num(-ccy)})">{"".join(items)}</g></g></g>')
    # sparks when it works
    sparks = []
    for i in range(10):
        ang = i / 10 * 6.2832 + rnd.uniform(-.2, .2)
        import math
        dist = cell * rnd.uniform(5, 8)
        sz = cell * rnd.uniform(0.35, 0.6)
        col = [PAPER, ACCENT, "#d3c7f7"][i % 3]
        sparks.append(
            f'<g opacity="0"><animate attributeName="opacity" values="0;0;1;0;0" keyTimes="0;{_t(8.85, T)};{_t(8.9, T)};{_t(9.7, T)};1" dur="{num(T)}s" repeatCount="indefinite"/>'
            f'<animateTransform attributeName="transform" type="translate" values="0 0;0 0;{num(math.cos(ang) * dist)} {num(math.sin(ang) * dist * 0.8)};{num(math.cos(ang) * dist)} {num(math.sin(ang) * dist * 0.8)}" '
            f'keyTimes="0;{_t(8.85, T)};{_t(9.7, T)};1" dur="{num(T)}s" repeatCount="indefinite"/>'
            f'<rect x="{num(ccx - sz / 2)}" y="{num(ccy - sz / 2)}" width="{num(sz)}" height="{num(sz)}" fill="{col}"/></g>')

    # ---- the log
    def run(first, a, hold, at):
        o = [shown(a, hold, T, text(TEXT_MED, ">", fs, lx, yA, ACCENT)),
             typed(TEXT_MED, first, fs, lx + TEXT_MED.width("> ", fs), yA, PAPER, a + 0.1, a + 0.8, T, hold),
             shown(at[0], hold, T, text(TEXT, "compiling 57 files", fs, lx, yB1, SOFT)),
             shown(at[1], hold, T, text(TEXT, "linking", fs, lx, yB2, SOFT))]
        return "".join(o)
    log = [run("build", 0.3, 6.1, (1.1, 1.8)),
           bar(lx, bar_y, lw, bar_h, ACCENT, 0.9, 3.3, T, 6.1, colour_change=(3.4, CRASH), frac=0.7),
           typed(DISPLAY, "$#!%....", big, lx, big_y, CRASH, 3.5, 4.3, T, 6.1),
           run("build again", 6.3, 11.8, (7.2, 7.7)),
           bar(lx, bar_y, lw, bar_h, ACCENT, 6.9, 8.7, T, 11.8),
           typed(DISPLAY, "COMPLETE", big, lx, big_y, PAPER, 8.8, 9.4, T, 11.8)]
    body = pop + "".join(sparks) + "".join(log)
    out.append(f'<g clip-path="url(#{cid})">{shake(3.4, T, 2.6 if not mobile else 3.6, body)}</g>')
    return "".join(out)
