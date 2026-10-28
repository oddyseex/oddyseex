"""Shared tokens and text-to-path helpers for the ODDYSEE profile graphics.

All lettering is converted to vector paths so it looks the same everywhere,
including inside GitHub's README image sandbox where web fonts do not load.
"""
import re
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

HERE = Path(__file__).resolve().parent
FONT_DIR = HERE / "fonts"
LOGO_DIR = HERE / "logos"

# Purple on charcoal, plus white, taken from the ODDYSEE TV banner.
ACCENT = "#8956fd"
INK = "#0f0e11"
SURFACE = "#1a181d"   # charcoal, the stand-in for what used to be white sheets
BLOT = "#08070a"      # ink splatter printed on the charcoal
LINE = "#6d6678"
PAPER = "#ffffff"
DEEP = "#9966cc"    # the softer second purple of the banner
DISC = "#211f25"    # one tone step above the ink
MUTED = "#3a2a66"   # secondary text on paper and purple
SOFT = "#cfc9d6"    # secondary text on ink


def num(v):
    return ("%.2f" % v).rstrip("0").rstrip(".")


class Font:
    def __init__(self, filename):
        self.font = TTFont(str(FONT_DIR / filename))
        self.glyphs = self.font.getGlyphSet()
        self.cmap = self.font.getBestCmap()
        self.upm = self.font["head"].unitsPerEm
        self.cap_height = self.font["OS/2"].sCapHeight

    def cap(self, size):
        return self.cap_height * size / self.upm

    def width(self, text, size, track=0.0):
        scale = size / self.upm
        total = 0.0
        for ch in text:
            total += self.glyphs[self.cmap[ord(ch)]].width * scale + track
        return total - track if text else 0.0

    def d(self, text, size, x, y, track=0.0):
        scale = size / self.upm
        pen = SVGPathPen(self.glyphs, ntos=num)
        cx = x
        for ch in text:
            name = self.cmap[ord(ch)]
            self.glyphs[name].draw(TransformPen(pen, (scale, 0, 0, -scale, cx, y)))
            cx += self.glyphs[name].width * scale + track
        return pen.getCommands()

    def wrap(self, text, size, max_width):
        lines, current = [], ""
        for word in text.split():
            trial = (current + " " + word).strip()
            if self.width(trial, size) <= max_width:
                current = trial
            else:
                lines.append(current)
                current = word
        lines.append(current)
        return lines

    def balanced(self, text, size, max_width):
        """Wrap to the same number of lines as `wrap`, but as even as possible (no lone last word)."""
        count = len(self.wrap(text, size, max_width))
        lo = max(self.width(w, size) for w in text.split())
        hi = max_width
        for _ in range(24):
            mid = (lo + hi) / 2
            if len(self.wrap(text, size, mid)) <= count:
                hi = mid
            else:
                lo = mid
        return self.wrap(text, size, hi)


DISPLAY = Font("barlow-condensed-latin-700-normal.woff")   # Barlow Condensed 700
TEXT = Font("barlow-latin-400-normal.woff")                # Barlow 400
TEXT_MED = Font("barlow-latin-500-normal.woff")            # Barlow 500


def text(font, string, size, x, y, fill, anchor="start", track=0.0):
    w = font.width(string, size, track)
    if anchor == "middle":
        x -= w / 2
    elif anchor == "end":
        x -= w
    return f'<path d="{font.d(string, size, x, y, track)}" fill="{fill}"/>'


def svg(width, height, body, title, desc, css=""):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {num(width)} {num(height)}" '
        f'width="{num(width)}" height="{num(height)}" role="img" aria-labelledby="t d">'
        f"<title id=\"t\">{title}</title><desc id=\"d\">{desc}</desc>"
        f"<style>@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}}}{css}</style>"
        f"{body}</svg>"
    )


def rect(x, y, w, h, fill):
    return f'<rect x="{num(x)}" y="{num(y)}" width="{num(w)}" height="{num(h)}" fill="{fill}"/>'


def stripe(x, y, w, h, bars, first, second):
    """Alternating filled bars, the card's one ornament."""
    bw = w / bars
    out = []
    for i in range(bars):
        out.append(rect(x + i * bw, y, bw, h, first if i % 2 == 0 else second))
    return "".join(out)


def logo(name, x, y, size, mono=None):
    """Embed an official logo file as a nested svg at (x, y) with the given size."""
    src = (LOGO_DIR / f"{name}.svg").read_text()
    vb = re.search(r'viewBox="([^"]+)"', src).group(1)
    inner = re.sub(r"^.*?<svg[^>]*>", "", src, count=1, flags=re.S)
    inner = re.sub(r"</svg>\s*$", "", inner)
    inner = re.sub(r"<title>.*?</title>", "", inner, flags=re.S)
    fill = f' fill="{mono}"' if mono else ""
    return (
        f'<svg x="{num(x)}" y="{num(y)}" width="{num(size)}" height="{num(size)}" '
        f'viewBox="{vb}"{fill}>{inner}</svg>'
    )


def scallop_d(x, y, w, h, r=9, pitch=26):
    """Path data for a sheet whose top and bottom edges are cut into shallow scallops."""
    n = max(1, int(w // pitch))
    seg = w / n
    flat = (seg - 2 * r) / 2
    d = f"M{num(x)} {num(y)}"
    for _ in range(n):
        d += f"h{num(flat)}a{r} {r} 0 0 0 {2 * r} 0h{num(flat)}"
    d += f"V{num(y + h)}"
    for _ in range(n):
        d += f"h{num(-flat)}a{r} {r} 0 0 0 {-2 * r} 0h{num(-flat)}"
    d += "Z"
    return d


def scalloped(x, y, w, h, fill, r=9, pitch=26):
    return f'<path d="{scallop_d(x, y, w, h, r, pitch)}" fill="{fill}"/>'


def blots(x, y, w, h, seed=1, scale=1.0):
    """Ink splatter in the manner of the reference banner: clusters of overlapping circles with drips and specks.
    Meant to be drawn inside a clip path, so blots may overhang the edges."""
    import math
    import random
    rnd = random.Random(seed)
    out = []
    count = max(3, int(w * h / 8500))
    for _ in range(count):
        cx, cy = x + rnd.uniform(-0.02, 1.02) * w, y + rnd.uniform(-0.02, 1.02) * h
        big = rnd.choice([26, 18, 13, 9]) * scale
        R = big * rnd.uniform(0.7, 1.15)
        out.append(f'<circle cx="{num(cx)}" cy="{num(cy)}" r="{num(R)}"/>')
        for _ in range(rnd.randint(3, 6)):
            a = rnd.uniform(0, math.tau)
            dist = R * rnd.uniform(0.5, 0.85)
            out.append(f'<circle cx="{num(cx + math.cos(a) * dist)}" cy="{num(cy + math.sin(a) * dist)}" '
                       f'r="{num(R * rnd.uniform(0.35, 0.65))}"/>')
        for _ in range(rnd.randint(2, 6)):
            a = rnd.uniform(0, math.tau)
            dist = R * rnd.uniform(1.25, 2.6)
            out.append(f'<circle cx="{num(cx + math.cos(a) * dist)}" cy="{num(cy + math.sin(a) * dist)}" '
                       f'r="{num(max(1.2, R * rnd.uniform(0.06, 0.22)))}"/>')
    return f'<g fill="{BLOT}">{"".join(out)}</g>'


_uid = [0]


def surface_rect(x, y, w, h, seed=1, scale=1.0):
    """A charcoal sheet with ink splatter, as a drop-in for a white rectangle."""
    _uid[0] += 1
    cid = f"sf{_uid[0]}"
    return (f'<clipPath id="{cid}"><rect x="{num(x)}" y="{num(y)}" width="{num(w)}" height="{num(h)}"/></clipPath>'
            f'{rect(x, y, w, h, SURFACE)}<g clip-path="url(#{cid})">{blots(x, y, w, h, seed, scale)}</g>')


def surface_path(d, box, seed=1, scale=1.0):
    """The same for any shape; box is (x, y, w, h) of the shape's bounds."""
    _uid[0] += 1
    cid = f"sf{_uid[0]}"
    return (f'<clipPath id="{cid}"><path d="{d}"/></clipPath><path d="{d}" fill="{SURFACE}"/>'
            f'<g clip-path="url(#{cid})">{blots(*box, seed, scale)}</g>')


def halftone(x, y, cols, rows, pitch, rmax, colors, flip_x=False, flip_y=False):
    """A corner of halftone dots that shrink away from the corner, like the dot fields in the reference."""
    out = []
    for i in range(cols):
        for j in range(rows):
            t = (i / cols + j / rows) / 2
            r = rmax * (1 - t) ** 1.3
            if r < 0.7:
                continue
            px = x + (cols - 1 - i if flip_x else i) * pitch
            py = y + (rows - 1 - j if flip_y else j) * pitch
            out.append(f'<circle cx="{num(px)}" cy="{num(py)}" r="{num(r)}" fill="{colors[(i * 3 + j * 5) % len(colors)]}"/>')
    return "".join(out)


def zigzag_bottom(x, y, w, h, fill, tooth=16, depth=10):
    """A slip whose bottom edge is a zigzag."""
    n = max(1, int(w // tooth))
    seg = w / n
    d = f"M{num(x)} {num(y)}H{num(x + w)}V{num(y + h)}"
    for i in range(n):
        px = x + w - (i + 1) * seg
        d += f"L{num(px + seg / 2)} {num(y + h + depth)}L{num(px)} {num(y + h)}"
    d += "Z"
    return f'<path d="{d}" fill="{fill}"/>'


def ticket_d(x, y, w, h, notch_xs, r=16):
    """Path data for a ticket with semicircle notches on the left and right edges and at each x on top and bottom."""
    d = f"M{num(x)} {num(y)}"
    for nx in sorted(notch_xs):
        d += f"L{num(nx - r)} {num(y)}A{r} {r} 0 0 0 {num(nx + r)} {num(y)}"
    d += f"L{num(x + w)} {num(y)}"
    mid = y + h / 2
    d += f"L{num(x + w)} {num(mid - r)}A{r} {r} 0 0 0 {num(x + w)} {num(mid + r)}"
    d += f"L{num(x + w)} {num(y + h)}"
    for nx in sorted(notch_xs, reverse=True):
        d += f"L{num(nx + r)} {num(y + h)}A{r} {r} 0 0 0 {num(nx - r)} {num(y + h)}"
    d += f"L{num(x)} {num(y + h)}"
    d += f"L{num(x)} {num(mid + r)}A{r} {r} 0 0 0 {num(x)} {num(mid - r)}Z"
    return d


def ticket_stack_d(x, y, w, h, notch_ys, r=16):
    """Path data for a tall ticket with semicircle notches on the left and right edges at each y."""
    d = f"M{num(x)} {num(y)}L{num(x + w)} {num(y)}"
    for ny in sorted(notch_ys):
        d += f"L{num(x + w)} {num(ny - r)}A{r} {r} 0 0 0 {num(x + w)} {num(ny + r)}"
    d += f"L{num(x + w)} {num(y + h)}L{num(x)} {num(y + h)}"
    for ny in sorted(notch_ys, reverse=True):
        d += f"L{num(x)} {num(ny + r)}A{r} {r} 0 0 0 {num(x)} {num(ny - r)}"
    d += "Z"
    return d


def dots_h(x1, x2, y, fill, r=2.5, pitch=12):
    n = int((x2 - x1) // pitch)
    return "".join(f'<circle cx="{num(x1 + i * pitch + pitch / 2)}" cy="{num(y)}" r="{r}" fill="{fill}"/>' for i in range(n))


def dots_v(x, y1, y2, fill, r=3, pitch=14):
    n = int((y2 - y1) // pitch)
    return "".join(f'<circle cx="{num(x)}" cy="{num(y1 + i * pitch + pitch / 2)}" r="{r}" fill="{fill}"/>' for i in range(n))
