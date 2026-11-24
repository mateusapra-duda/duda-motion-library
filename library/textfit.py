"""textfit.py: which font, weight, size and letter spacing redraw a text that Figma's SVG export outlined.

Figma's SVG export draws every text as glyph outlines: thousands of paths that make the Rive editor crawl. fit()
tries the fonts the piece has (kit.FONTS keys: the library's "duda" and any p.font) against the outlines, so
fromfigma.py can put a native Rive text in their place. The layer's name is the text (Figma names a text layer by its
content); a layer named otherwise ("Text_3") needs its text given (figma_screen(texts=...)).

    fit("Automations", polys, keys=("duda",)) -> dict(font, wght, size, ls, lines=[(string, x, baseline)],
                                                     boxes=[(x0, y0, x1, y1)], score, pieces) or None

Merged from the pieces' copies (create-automation, marketing-automation-motion, ma-simplified-flow: the same file).
v15: the fonts come from kit.FONTS; Duda Sans is tried at the library's weights only (350, 550, 700); the outline is
filled nonzero, pixel centres in (the pieces' copies filled even-odd); pieces() tells a layer name that isn't the text
(fromfigma.py keeps the outline then, and p.figma_sheet() lists it: create-automation drew "Status" for "Active").
"""
import functools
import math
import os
import re

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

import kit

WEIGHTS = {"duda": (350, 550, 700)}          # the DS weights (ds/tokens.json: Regular, Medium, Bold)
VARIABLE = (300, 400, 500, 600, 700, 800)     # any other variable font
SS = 4                                        # raster supersampling for the fit


def font_file(key):
    """The file of font `key` (kit.FONTS: the library's own in fonts/, a piece's own by its path)."""
    v = kit.FONTS[key]
    return v[2] if len(v) > 2 else os.path.join(kit.HERE, "fonts", v[0])


@functools.lru_cache(maxsize=None)
def weights(key):
    """The weights to try: None for a static font (one weight)."""
    try:
        ImageFont.truetype(font_file(key), 20).get_variation_axes()
    except OSError:
        return (None,)
    return WEIGHTS.get(key, VARIABLE)


# ---------------------------------------------------------------- path data -> polygons
def subpaths(d):
    """Absolute M/L/H/V/C/Q/Z path data (Figma's) as flattened polygons."""
    toks = re.findall(r"[MLHVCQZmlhvcqz]|-?\d*\.?\d+(?:e-?\d+)?", d)
    out, cur, pt, i, cmd = [], [], (0.0, 0.0), 0, None

    def num():
        nonlocal i
        i += 1
        return float(toks[i - 1])
    while i < len(toks):
        if toks[i].isalpha():
            cmd = toks[i]
            i += 1
            if cmd in "Zz":
                if cur:
                    out.append(cur)
                cur = []
                continue
        if cmd == "M":
            if cur:
                out.append(cur)
            pt = (num(), num())
            cur = [pt]
            cmd = "L"
        elif cmd == "L":
            pt = (num(), num())
            cur.append(pt)
        elif cmd == "H":
            pt = (num(), pt[1])
            cur.append(pt)
        elif cmd == "V":
            pt = (pt[0], num())
            cur.append(pt)
        elif cmd in "CQ":
            ps = [pt] + [(num(), num()) for _ in range(3 if cmd == "C" else 2)]
            for k in range(1, 7):
                t = k / 6
                if cmd == "C":
                    a = [(1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t * t, t ** 3]
                else:
                    a = [(1 - t) ** 2, 2 * (1 - t) * t, t * t]
                cur.append((sum(w * p[0] for w, p in zip(a, ps)), sum(w * p[1] for w, p in zip(a, ps))))
            pt = ps[-1]
        else:
            raise ValueError(f"path command {cmd}")
    if cur:
        out.append(cur)
    return [s for s in out if len(s) > 2]


def bbox(polys):
    xs = [p[0] for s in polys for p in s]
    ys = [p[1] for s in polys for p in s]
    return min(xs), min(ys), max(xs), max(ys)


def raster(polys, box, ss=SS, over=4):
    """Nonzero mask of the polygons over box (x0, y0, x1, y1): each pixel filled when its centre is inside, drawn
    `over` times finer and averaged down. Nonzero, as Figma draws them: a glyph's overlapping strokes stay filled,
    and two contours that only touch (the stem of a "u" drawn apart from its bowl) stay one piece."""
    import numpy as np
    x0, y0, x1, y1 = box
    size = (max(1, math.ceil((x1 - x0) * ss)), max(1, math.ceil((y1 - y0) * ss)))
    w, h = size[0] * over, size[1] * over
    k = ss * over
    ax, ay, bx, by = [], [], [], []
    for s in polys:
        if len(s) < 3:
            continue
        for (px, py), (qx, qy) in zip(s, s[1:] + s[:1]):
            ax.append((px - x0) * k), ay.append((py - y0) * k), bx.append((qx - x0) * k), by.append((qy - y0) * k)
    acc = np.zeros((h, w + 1), np.int32)
    if ax:
        ax, ay, bx, by = (np.array(v, np.float64) for v in (ax, ay, bx, by))
        keep = ay != by
        ax, ay, bx, by = ax[keep], ay[keep], bx[keep], by[keep]
        up = np.where(by > ay, 1, -1)
        r0 = np.ceil(np.minimum(ay, by) - 0.5).astype(np.int64)        # the rows whose centre the edge crosses
        r1 = np.ceil(np.maximum(ay, by) - 0.5).astype(np.int64)
        n = np.maximum(r1 - r0, 0)
        if n.sum():
            idx = np.repeat(np.arange(len(n)), n)
            rows = r0[idx] + np.arange(n.sum()) - np.repeat(np.cumsum(n) - n, n)
            yc = rows + 0.5
            xc = ax[idx] + (yc - ay[idx]) * (bx[idx] - ax[idx]) / (by[idx] - ay[idx])
            cols = np.clip(np.ceil(xc - 0.5), 0, w).astype(np.int64)
            ok = (rows >= 0) & (rows < h)
            np.add.at(acc, (rows[ok], cols[ok]), up[idx][ok])
    filled = np.cumsum(acc, axis=1)[:, :w] != 0
    m = Image.fromarray((filled * 255).astype(np.uint8), "L")
    return m.resize(size, Image.BOX).point(lambda v: 255 if v >= 128 else 0).convert("1")


def score(target, drawn, ss=SS, size=12.0):
    """How well drawn redraws target, forgiving half a pixel (more on big type): min(precision, recall) against the
    other grown."""
    grow = ImageFilter.MaxFilter(2 * max(ss // 2, round(0.03 * size * ss)) + 1)
    t, d = target.convert("L"), drawn.convert("L")
    tg, dg = t.filter(grow), d.filter(grow)
    nt, nd = t.histogram()[-1], d.histogram()[-1]
    if not nt or not nd:
        return 0.0
    rec = ImageChops.multiply(t, dg).histogram()[-1] / nt
    prec = ImageChops.multiply(d, tg).histogram()[-1] / nd
    return min(rec, prec)


# ---------------------------------------------------------------- fonts
@functools.lru_cache(maxsize=None)
def font(key, wght, size):
    f = ImageFont.truetype(font_file(key), size)
    if wght is not None:
        axes = f.get_variation_axes()
        f.set_variation_by_axes([wght if a["name"] in (b"Weight", "Weight") else
                                 min(max(size, a["minimum"]), a["maximum"]) for a in axes])
    return f


def ink(key, wght, size, s):
    """The text's ink box at the pen origin (0, baseline 0)."""
    return font(key, wght, size).getbbox(s, anchor="ls")


def width(key, wght, size, s, ls):
    """Ink width of s at size with letter spacing ls (px between glyphs)."""
    b = ink(key, wght, 100, s)
    return (b[2] - b[0]) * size / 100 + ls * max(len(s) - 1, 0)


def draw(key, wght, size, s, x, baseline, box, ls=0.0, ss=SS):
    f = font(key, wght, round(size * ss * 8) / 8)
    x0, y0, x1, y1 = box
    m = Image.new("L", (max(1, math.ceil((x1 - x0) * ss)), max(1, math.ceil((y1 - y0) * ss))), 0)
    dr = ImageDraw.Draw(m)
    if not ls:
        dr.text(((x - x0) * ss, (baseline - y0) * ss), s, font=f, fill=255, anchor="ls")
    else:
        for k, ch in enumerate(s):
            px = x + f.getlength(s[:k]) / ss + k * ls
            dr.text(((px - x0) * ss, (baseline - y0) * ss), ch, font=f, fill=255, anchor="ls")
    return m.point(lambda v: 255 if v >= 128 else 0).convert("1")


# ---------------------------------------------------------------- lines
def lines_of(polys):
    """Glyph contours grouped into text lines by their vertical overlap."""
    rows = []
    for b, s in sorted(((bbox([s]), s) for s in polys), key=lambda t: (t[0][1] + t[0][3]) / 2):
        cy = (b[1] + b[3]) / 2
        for r in rows:
            if r["y0"] - 1 <= cy <= r["y1"] + 1:
                r["polys"].append(s)
                r["y0"], r["y1"] = min(r["y0"], b[1]), max(r["y1"], b[3])
                break
        else:
            rows.append({"y0": b[1], "y1": b[3], "polys": [s]})
    # rows that are only dots, accents, quotes or commas join the nearest real row (the one below first)
    tall = max(r["y1"] - r["y0"] for r in rows)
    big = [r for r in rows if r["y1"] - r["y0"] >= 0.45 * tall]
    for r in rows:
        if r in big:
            continue
        near = min(big, key=lambda b: max(b["y0"] - r["y1"], r["y0"] - b["y1"], 0) + (0 if b["y0"] >= r["y0"] else 0.5))
        near["polys"] += r["polys"]
        near["y0"], near["y1"] = min(near["y0"], r["y0"]), max(near["y1"], r["y1"])
    big.sort(key=lambda r: r["y0"])
    return [r["polys"] for r in big]


def split_words(content, widths, measure):
    """Break content into len(widths) lines whose measured widths best match the ink widths."""
    words = content.split()
    out, k = [], 0
    for n, w in enumerate(widths):
        if n == len(widths) - 1:
            out.append(" ".join(words[k:]))
            break
        best, best_j = None, k + 1
        for j in range(k + 1, len(words) - (len(widths) - n - 1) + 1):
            e = abs(measure(" ".join(words[k:j])) - w)
            if best is None or e < best:
                best, best_j = e, j
        out.append(" ".join(words[k:best_j]))
        k = best_j
    return out


def content_of(name):
    """The text a layer name stands for: Figma's repeat suffix (_2) off, its UTF-8 read back (’ as â\\x80\\x99)."""
    content = re.sub(r"_\d+$", "", name).strip()
    try:
        content = content.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        pass
    return content


def pieces(mask):
    """How many separate pieces of ink a 1-bit mask has (4-connected): a layer name that isn't the text shows up
    here. A badge named "Status" whose text is "Active" scores 0.82 (the score alone passes it), but "Active" is 7
    pieces of ink (the i's dot) and "Status" 6. Counting glyph contours can't tell: Figma keeps some overlaps."""
    w, h = mask.size
    px = mask.tobytes()                       # mode "1": rows packed 8 pixels a byte, padded to whole bytes
    stride = (w + 7) // 8
    parent = []

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    prev = []                                 # runs of the row above: (start, end, label)
    for y in range(h):
        row = px[y * stride:(y + 1) * stride]
        runs, x = [], 0
        while x < w:
            if row[x >> 3] & (0x80 >> (x & 7)):
                s = x
                while x < w and row[x >> 3] & (0x80 >> (x & 7)):
                    x += 1
                lab = len(parent)
                parent.append(lab)
                for ps, pe, pl in prev:
                    if ps < x and pe > s:     # overlaps the run above: the same piece
                        ra, rb = find(lab), find(pl)
                        if ra != rb:
                            parent[ra] = rb
                runs.append((s, x, lab))
            else:
                x += 1
        prev = runs
    return len({find(i) for i in range(len(parent))})


# ---------------------------------------------------------------- the fit
def fit(content, polys, keys=("duda",), min_score=0.75):
    """content: the text; polys: its contours (output space). None when no font redraws it."""
    if not re.search(r"[A-Za-z0-9]", content or "") or not polys:
        return None
    if len(content) <= 3:                             # "px", "0": too short to tell the fonts apart
        keys = keys[:1]
    if len(polys) < max(1, len(re.sub(r"\s", "", content)) // 3):     # far fewer contours than letters
        return None
    rows = lines_of(polys)
    rboxes = [bbox(r) for r in rows]
    if len(rows) > len(content.split()):
        return None
    x0, y0, x1, y1 = bbox(polys)
    box = (x0 - 2, y0 - 2, x1 + 2, y1 + 2)
    target = raster(polys, box)
    cands = []
    for key in keys:
        for wght in weights(key):
            # first guess: the size from the tallest line against the whole text's ink, no spacing
            n = max(range(len(rows)), key=lambda q: rboxes[q][3] - rboxes[q][1])
            strings, ls = [content], 0.0
            size = 0.0
            for rnd in range(3):        # lines <-> size and spacing, a few rounds (spacing only at the end)
                if len(rows) > 1:
                    if not size:
                        hb = ink(key, wght, 100, content)
                        size = 100 * (rboxes[n][3] - rboxes[n][1]) / max(hb[3] - hb[1], 1e-6)
                    strings = split_words(content, [b[2] - b[0] for b in rboxes],
                                          lambda t: width(key, wght, size, t, ls))
                if any(not t for t in strings):
                    break
                # size from the tallest line's ink height, spacing from its width
                n = max(range(len(rows)), key=lambda q: rboxes[q][3] - rboxes[q][1])
                b100 = ink(key, wght, 100, strings[n])
                if b100[3] - b100[1] <= 0:
                    break
                size = 100 * (rboxes[n][3] - rboxes[n][1]) / (b100[3] - b100[1])
                if rnd == 2 or len(rows) == 1:
                    w0 = (b100[2] - b100[0]) * size / 100
                    ls = ((rboxes[n][2] - rboxes[n][0]) - w0) / max(len(strings[n]) - 1, 1)
            if not size or any(not t for t in strings) or abs(ls) > 0.06 * size:
                continue
            lines = []
            for t, rb in zip(strings, rboxes):
                bi = ink(key, wght, 100, t)
                lines.append((t, rb[0] - bi[0] * size / 100, rb[3] - bi[3] * size / 100))
            m = Image.new("1", target.size, 0)
            for t, x, base in lines:
                m = ImageChops.logical_or(m, draw(key, wght, size, t, x, base, box, ls))
            cands.append({"font": key, "wght": wght, "size": size, "ls": ls, "lines": lines, "boxes": rboxes,
                          "score": score(target, m, size=size),
                          "ink": m.histogram()[-1] / max(target.histogram()[-1], 1)})
    if not cands:
        return None
    # the score (half a pixel forgiven) says it is this text and picks the font; the amount of ink, the weight
    top = max(cands, key=lambda c: c["score"])
    best = min((c for c in cands if c["font"] == top["font"] and c["score"] >= top["score"] - 0.08),
               key=lambda c: abs(c["ink"] - 1))
    if best["score"] < min_score:
        return None
    ps = max(8, math.ceil(48 / max(rboxes[0][3] - rboxes[0][1], 1)))  # finer for small type: letters stay apart
    drawn = Image.new("1", raster(polys, box, ss=ps, over=1).size, 0)
    for t, x, base in best["lines"]:
        drawn = ImageChops.logical_or(drawn, draw(best["font"], best["wght"], best["size"], t, x, base, box,
                                                  best["ls"], ss=ps))
    best["pieces"] = (pieces(raster(polys, box, ss=ps, over=1)), pieces(drawn))     # (the outline's, the font's)
    return best
