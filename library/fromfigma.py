"""fromfigma.py (v15): a Figma screen, from its SVG export, as a Rive scene in vector with native text.

    scr = p.figma_screen("home", "figma/vec/win03.svg", layer="Screen – Automations list", frame=(1166, 729),
                         drop=["New Automation"], parts=["Table"], plates=["Sidebar"])

Figma's SVG export of a node carries the node and its ancestors in one coordinate system. The layer `layer` (the
group whose `id` is Figma's layer name; repeats get _2, _3...) is converted to Rive shapes: paths, rectangles,
ellipses and lines; solid and gradient paints; clips and masks as ClippingShapes; drop shadows and layer blurs as
Feathers; image fills as Images (only the part of the photo that can show, at most 2x). On top of that:
- **native text**: Figma outlines every text. Each outlined text whose layer name is its text is redrawn with the
  piece's fonts (textfit.py: font, weight, size, spacing, one native Text per line on its baseline). A name is
  trusted only when the font draws as many pieces of ink as the outline has (a badge named "Status" showing "Active"
  scores well but has one piece more). What no font redraws stays outlined (`p.figma_sheet()` shows those, to name
  them with `texts=`). A dot grid (rows of tiny squares) becomes one dashed line per row.
- **light**: masks that cut nothing visible are left out (an inside border becomes the band it shows, an AI star's
  blurred extras go), shapes wholly outside `visible` are not drawn, clips that cut only outside it are dropped.
- **parts**: layers that become their own items (a box at their Figma place, on top of the rest), so the actions
  can animate them: `a.generate(scr.parts["Table"])`, `a.enter`, `p.hoverable`. Their texts are text items, so a
  generation types them in letter by letter.
- **plates**: still layers (that only move or fade whole) drawn as 2x images, rendered by the Rive CLI from the same
  vectors (on white and on black: the transparency is the difference), lossless WebP, in their place in the layer
  order. `plates=True`: the whole screen.

Merged from the pieces' copies: vecsvg.py + nativetext.py + textfit.py (create-automation, marketing-automation-motion,
ma-simplified-flow, manage-hero2), vec.py (hero-view and its five card siblings: recolor, skip), plates.py
(hero-tabs: the plates' capture).
"""
import base64
import copy
import functools
import hashlib
import io
import json
import math
import os
import re
import subprocess
import xml.etree.ElementTree as ET

from PIL import Image

import kit
from kit import El, argb
import textfit
from common import Item, RIVE

NS = "{http://www.w3.org/2000/svg}"
HREF = "{http://www.w3.org/1999/xlink}href"
NAMED = {"white": "#FFFFFF", "black": "#000000"}
INHERITED = ("fill", "fill-opacity", "fill-rule", "stroke", "stroke-opacity", "stroke-width", "stroke-linecap",
             "stroke-linejoin")
SKIP = ("defs", "mask", "clipPath", "pattern", "filter", "linearGradient", "radialGradient", "image", "use", "title",
        "desc", "metadata")
K = 0.5522847498                 # cubic handle of a quarter circle
HAIRLINE = 1.0                   # thinnest divider line, px: Rive draws a thinner one lighter than Figma does
MARGIN = 64.0                    # visible="auto": the box and this much around it (a cut's travel)
LH = 1.3                         # native text: line height (one text per line: it only sets the box)
MIN_SIZE = 6.0                   # smaller text stays outlined (the outline draws it better)
PLATE_SCALE = 2
I2 = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)


# ---------------------------------------------------------------- affine 2D: (a, b, c, d, e, f) as in SVG
def mul(m, n):
    """m after n."""
    a, b, c, d, e, f = m
    a2, b2, c2, d2, e2, f2 = n
    return (a * a2 + c * b2, b * a2 + d * b2, a * c2 + c * d2, b * c2 + d * d2, a * e2 + c * f2 + e, b * e2 + d * f2 + f)


def ap(m, p):
    return (m[0] * p[0] + m[2] * p[1] + m[4], m[1] * p[0] + m[3] * p[1] + m[5])


def scale_of(m):
    return math.sqrt(abs(m[0] * m[3] - m[1] * m[2]))


def axis_aligned(m):
    return abs(m[1]) < 1e-9 and abs(m[2]) < 1e-9 and m[0] > 0 and m[3] > 0


def shift(dx, dy):
    return (1.0, 0.0, 0.0, 1.0, dx, dy)


def parse_transform(s):
    m = I2
    for fn, args in re.findall(r"(\w+)\s*\(([^)]*)\)", s or ""):
        v = [float(x) for x in re.findall(r"-?\d*\.?\d+(?:e-?\d+)?", args)]
        if fn == "matrix":
            t = tuple(v)
        elif fn == "translate":
            t = (1, 0, 0, 1, v[0], v[1] if len(v) > 1 else 0)
        elif fn == "scale":
            t = (v[0], 0, 0, v[1] if len(v) > 1 else v[0], 0, 0)
        elif fn == "rotate":
            r = math.radians(v[0])
            t = (math.cos(r), math.sin(r), -math.sin(r), math.cos(r), 0, 0)
            if len(v) == 3:
                t = mul(mul((1, 0, 0, 1, v[1], v[2]), t), (1, 0, 0, 1, -v[1], -v[2]))
        else:
            raise ValueError(f"transform {fn}")
        m = mul(m, t)
    return m


# ---------------------------------------------------------------- colours and attributes
def color(s, alpha=1.0):
    """'#rgb' / '#rrggbb' / white / black / rgba(r, g, b, a) -> ARGB, or None for none."""
    s = (s or "").strip()
    if not s or s == "none" or s.startswith("url("):
        return None
    s = NAMED.get(s, s)
    m = re.match(r"rgba?\(([^)]*)\)", s)
    if m:
        v = [float(x) for x in m.group(1).split(",")]
        a = v[3] if len(v) > 3 else 1.0
        return argb("#%02X%02X%02X" % tuple(round(x) for x in v[:3]), a * alpha)
    h = s.lstrip("#")
    if len(h) == 3:
        h = "".join(ch * 2 for ch in h)
    return argb("#" + h, alpha)


def attrs_of(e):
    """An element's presentation attributes, its style="" included. Some exports repeat each colour as
    `fill:#hex;fill:color(display-p3 ...)`: the sRGB hex is kept (the P3 one is the same colour)."""
    a = dict(e.attrib)
    for kv in (a.pop("style", "") or "").split(";"):
        if ":" in kv:
            k, v = kv.split(":", 1)
            if v.strip().startswith("color("):
                continue
            a[k.strip()] = v.strip()
    return a


def num(a, k, default=0.0):
    v = a.get(k)
    if v in (None, ""):
        return default
    return float(re.match(r"-?\d*\.?\d+(?:e-?\d+)?", str(v)).group(0))


def slug(s):
    """A layer name as a piece name part: letters and digits."""
    return re.sub(r"[^A-Za-z0-9]", "", textfit.content_of(s).title())[:24] or "Part"


# ---------------------------------------------------------------- geometry: subpaths of vertices, in output coords
def ellipse_subpath(cx, cy, rx, ry):
    pts = [(cx + rx, cy), (cx, cy + ry), (cx - rx, cy), (cx, cy - ry)]
    segs = [("M", pts[0])]
    for i in range(4):
        p0, p1 = pts[i], pts[(i + 1) % 4]
        t0 = [(0, ry), (-rx, 0), (0, -ry), (rx, 0)][i]
        t1 = [(-rx, 0), (0, -ry), (rx, 0), (0, ry)][i]
        segs.append(("C", (p0[0] + t0[0] * K, p0[1] + t0[1] * K), (p1[0] - t1[0] * K, p1[1] - t1[1] * K), p1))
    return {"segs": segs, "closed": True}


def rect_subpath(x, y, w, h, r):
    if not r:
        return {"segs": [("M", (x, y)), ("L", (x + w, y)), ("L", (x + w, y + h)), ("L", (x, y + h))], "closed": True}
    r = min(r, w / 2, h / 2)
    k = r * (1 - K)
    return {"segs": [("M", (x + r, y)), ("L", (x + w - r, y)), ("C", (x + w - k, y), (x + w, y + k), (x + w, y + r)),
                     ("L", (x + w, y + h - r)), ("C", (x + w, y + h - k), (x + w - k, y + h), (x + w - r, y + h)),
                     ("L", (x + r, y + h)), ("C", (x + k, y + h), (x, y + h - k), (x, y + h - r)),
                     ("L", (x, y + r)), ("C", (x, y + k), (x + k, y), (x + r, y))], "closed": True}


class Geo:
    """One element's outline: a Rive primitive (rect / ellipse, when the transform keeps it upright) or subpaths of
    vertices; both in output coordinates. bbox counts the handles (a little generous)."""

    def __init__(self, kind, data, bbox, closed=True):
        self.kind, self.data, self.bbox, self.closed = kind, data, bbox, closed

    def shrunk(self, d):
        """The outline d px smaller on every side (a shadow's spread; negative: bigger)."""
        if self.kind == "rect":
            x, y, w, h, r = self.data
            return Geo("rect", (x + d, y + d, w - 2 * d, h - 2 * d, max(0.0, r - d)), self.bbox)
        if self.kind == "ellipse":
            cx, cy, w, h = self.data
            return Geo("ellipse", (cx, cy, w - 2 * d, h - 2 * d), self.bbox)
        x0, y0, x1, y1 = self.bbox
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        kx = (x1 - x0 - 2 * d) / max(x1 - x0, 1e-6)
        ky = (y1 - y0 - 2 * d) / max(y1 - y0, 1e-6)
        f = lambda p: None if p is None else (cx + (p[0] - cx) * kx, cy + (p[1] - cy) * ky)  # noqa: E731
        subs = [[{"p": f(v["p"]), "in": f(v["in"]), "out": f(v["out"])} for v in vs] for vs in self.data]
        return Geo("path", subs, self.bbox, self.closed)

    def clockwise(self):
        """Feathered fills draw with the clockwise rule: turn each subpath clockwise (y down)."""
        if self.kind != "path":
            return self
        out = []
        for vs in self.data:
            area = sum(a["p"][0] * b["p"][1] - b["p"][0] * a["p"][1] for a, b in zip(vs, vs[1:] + vs[:1]))
            out.append(vs if area >= 0 else [{"p": v["p"], "in": v["out"], "out": v["in"]} for v in reversed(vs)])
        return Geo("path", out, self.bbox, self.closed)

    def els(self, name):
        if self.kind == "rect":
            x, y, w, h, r = self.data
            return [El("Rectangle", {"x": x, "y": y, "width": w, "height": h, "originX": 0, "originY": 0,
                                     "cornerRadiusTL": r or None}, name=name)]
        if self.kind == "ellipse":
            cx, cy, w, h = self.data
            return [El("Ellipse", {"x": cx, "y": cy, "width": w, "height": h}, name=name)]
        closed = self.closed if isinstance(self.closed, list) else [self.closed] * len(self.data)
        return [kit.points_path(f"{name}.{i}" if len(self.data) > 1 else name, vs, closed=c)
                for i, (vs, c) in enumerate(zip(self.data, closed))]


def bbox_of(points):
    xs, ys = [p[0] for p in points], [p[1] for p in points]
    return (min(xs), min(ys), max(xs), max(ys))


def union(a, b):
    if a is None:
        return b
    if b is None:
        return a
    return (min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3]))


def intersect(a, b):
    r = (max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3]))
    return r if r[0] < r[2] and r[1] < r[3] else None


def grow(b, d):
    return None if b is None else (b[0] - d, b[1] - d, b[2] + d, b[3] + d)


def geometry(e, m):
    """-> Geo of a path / rect / circle / ellipse / line (its own transform included), or None."""
    tag, a = e.tag.replace(NS, ""), attrs_of(e)
    m = mul(m, parse_transform(a.get("transform")))
    if tag == "rect":
        x, y, w, h = num(a, "x"), num(a, "y"), num(a, "width"), num(a, "height")
        r = num(a, "rx", num(a, "ry"))
        if axis_aligned(m):
            (x0, y0), (x1, y1) = ap(m, (x, y)), ap(m, (x + w, y + h))
            return Geo("rect", (x0, y0, x1 - x0, y1 - y0, r * m[0]), (x0, y0, x1, y1))
        sub = rect_subpath(x, y, w, h, r)
    elif tag in ("circle", "ellipse"):
        cx, cy = num(a, "cx"), num(a, "cy")
        rx = num(a, "r") if tag == "circle" else num(a, "rx")
        ry = num(a, "r") if tag == "circle" else num(a, "ry")
        if axis_aligned(m):
            c = ap(m, (cx, cy))
            w, h = 2 * rx * m[0], 2 * ry * m[3]
            return Geo("ellipse", (c[0], c[1], w, h), (c[0] - w / 2, c[1] - h / 2, c[0] + w / 2, c[1] + h / 2))
        sub = ellipse_subpath(cx, cy, rx, ry)
    elif tag == "line":
        p0, p1 = ap(m, (num(a, "x1"), num(a, "y1"))), ap(m, (num(a, "x2"), num(a, "y2")))
        vs = [{"p": p0, "in": None, "out": None}, {"p": p1, "in": None, "out": None}]
        return Geo("path", [vs], bbox_of([p0, p1]), closed=False)
    elif tag == "path":
        subs = kit.parse_path(a.get("d", ""))
        pairs = [(kit.to_vertices(s, lambda p: ap(m, p)), s["closed"]) for s in subs]
        pairs = [(vs, c) for vs, c in pairs if len(vs) > 1]
        if not pairs:
            return None
        verts = [vs for vs, _ in pairs]
        pts = [q for vs in verts for v in vs for q in (v["p"], v["in"], v["out"]) if q is not None]
        # each subpath its own: an icon's open stroke and its closed ring in one path
        return Geo("path", verts, bbox_of(pts), closed=[c for _, c in pairs])
    else:
        return None
    vs = kit.to_vertices(sub, lambda p: ap(m, p))
    pts = [q for v in vs for q in (v["p"], v["in"], v["out"]) if q is not None]
    return Geo("path", [vs], bbox_of(pts))


# ---------------------------------------------------------------- masks the editor pays for every frame
def hv_rect(d):
    """(x0, y0, x1, y1) when d is one rectangle drawn with absolute M/H/V/Z only, else None."""
    if not d or re.search(r"[^MHVZ\d.\s,e-]", d) or d.count("M") != 1:
        return None
    pts, cmd = [], None
    for t in re.findall(r"[MHVZ]|-?\d*\.?\d+(?:e-?\d+)?", d):
        if t in "MHVZ":
            cmd = t
            continue
        if cmd == "M":
            pts.append(("x", float(t)))
            cmd = "M2"
            continue
        if cmd == "M2":
            pts.append(("y", float(t)))
            cmd = "H"
            continue
        pts.append(("x" if cmd == "H" else "y", float(t)))
    poly, cx, cy = [], None, None
    for k, v in pts:
        if k == "x":
            cx = v
        else:
            cy = v
        if cx is not None and cy is not None:
            poly.append((cx, cy))
    if len(poly) < 4:
        return None
    xs, ys = [p[0] for p in poly], [p[1] for p in poly]
    box = (min(xs), min(ys), max(xs), max(ys))
    area = abs(sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(poly, poly[1:] + poly[:1]))) / 2
    return box if abs(area - (box[2] - box[0]) * (box[3] - box[1])) < 1e-3 else None


def simplify_masks(svg):
    """Figma's masks the converter would turn into Rive clips (the editor redraws each one every frame):
    - an inside border (a thin band masked by its panel's rectangle): the band cut to what shows;
    - a shape masked by its own outline with blurred extras in it (the AI star's four points): the shape alone."""
    done = 0
    for el in list(svg.root.iter()):
        ref = el.get("mask")
        mask = svg.ref(ref) if ref else None
        if mask is None:
            continue
        shapes = [c for c in mask if c.tag in (NS + "path", NS + "rect")]
        if len(shapes) != 1:
            continue
        ms = shapes[0]
        mr = hv_rect(ms.get("d")) if ms.tag == NS + "path" else (
            None if ms.get("rx") or ms.get("transform") else
            (num(ms.attrib, "x"), num(ms.attrib, "y"), num(ms.attrib, "x") + num(ms.attrib, "width"),
             num(ms.attrib, "y") + num(ms.attrib, "height")))
        if el.tag == NS + "path" and mr and not el.get("stroke") and hv_rect(el.get("d")):
            er = hv_rect(el.get("d"))
            x0, y0, x1, y1 = max(er[0], mr[0]), max(er[1], mr[1]), min(er[2], mr[2]), min(er[3], mr[3])
            if x1 > x0 and y1 > y0:
                el.set("d", f"M{x0:.4f} {y0:.4f}H{x1:.4f}V{y1:.4f}H{x0:.4f}Z")
                del el.attrib["mask"]
                done += 1
            continue
        kids = list(el)
        small = num(mask.attrib, "width", 99) <= 24 and num(mask.attrib, "height", 99) <= 24     # an icon's piece
        if el.tag == NS + "g" and small and kids and kids[0].tag == NS + "path" and ms.tag == NS + "path" \
                and kids[0].get("d") == ms.get("d") and len(kids) > 1 and all(k.get("filter") for k in kids[1:]):
            for k in kids[1:]:
                el.remove(k)
            del el.attrib["mask"]
            done += 1
    svg.simplified = done


# ---------------------------------------------------------------- the document
class Svg:
    """One SVG export. Layers are found by their `id` (Figma's layer name; repeats get _2, _3...)."""

    def __init__(self, file):
        self.file = file
        self.root = ET.parse(file).getroot()
        self.ids, self.parent = {}, {}
        for p in self.root.iter():
            for c in p:
                self.parent[c] = p
        for e in self.root.iter():
            if e.get("id"):
                self.ids.setdefault(e.get("id"), e)
        simplify_masks(self)

    def size(self):
        a = self.root.attrib
        if a.get("width") and a.get("height"):
            return num(a, "width"), num(a, "height")
        vb = [float(v) for v in a["viewBox"].split()]
        return vb[2], vb[3]

    def chain(self, e):
        """The transform from the root to e's parent, and the presentation attributes e inherits."""
        chain, p = [], e
        while p in self.parent:
            p = self.parent[p]
            chain.append(p)
        m, style = I2, {}
        for p in reversed(chain):
            a = attrs_of(p)
            if p is not self.root:
                m = mul(m, parse_transform(a.get("transform")))
            style.update({k: a[k] for k in INHERITED if k in a})
        return m, style

    def layer(self, name):
        """(element, transform from the root, inherited style) of layer `name`: its id, or the one layer whose id
        ends with `name` (Figma's en dashes come through as mojibake: "Screen – List" finds "Screen â\\x80\\x93
        List")."""
        e = self.ids.get(name) or self.ids.get(name.replace("–", "â\u0080\u0093"))
        if e is None:
            hits = [k for k in self.ids if self.ids[k].tag == NS + "g" and
                    (k.endswith(name) or textfit.content_of(k) == name)]
            assert len(hits) == 1, f"{os.path.basename(self.file)}: no single layer {name!r} ({hits[:5]})"
            e = self.ids[hits[0]]
        return (e,) + self.chain(e)

    def ref(self, s):
        mm = re.match(r"url\(#([^)]+)\)", s or "")
        return self.ids.get(mm.group(1)) if mm else None

    def frame_origin(self, size):
        """Where the export's (0, 0) is in a frame of `size` (w, h) whose clip the export carries (Figma exports a
        node with its ancestors: the frame's rect, often in a clipPath, moved where the frame starts)."""
        for e in self.root.iter(NS + "rect"):
            a = attrs_of(e)
            if abs(num(a, "width") - size[0]) < 0.01 and abs(num(a, "height") - size[1]) < 0.01:
                m, _ = self.chain(e)
                x, y = ap(mul(m, parse_transform(a.get("transform"))), (num(a, "x"), num(a, "y")))
                return -x, -y
        raise ValueError(f"{os.path.basename(self.file)}: no {size[0]:g} x {size[1]:g} frame rect")

    def add_rect(self, layer, x, y, w, h, fill, index=None):
        """A plain rect into a layer (export coordinates): what Figma's export leaves out (a one-side border)."""
        g = layer if isinstance(layer, ET.Element) else self.layer(layer)[0]
        r = ET.Element(NS + "rect", {"x": str(x), "y": str(y), "width": str(w), "height": str(h), "fill": fill})
        g.insert(len(g) if index is None else index, r)


@functools.lru_cache(maxsize=None)
def load(file):
    """Each export parsed once (page exports are MBs, most of it embedded photos)."""
    return Svg(file)


# ---------------------------------------------------------------- native text (the hook the converter calls)
class Texts:
    """Outlined texts -> native Rive text: one Text per line, on its baseline, in the font textfit finds."""

    def __init__(self, here, fonts, texts=None, keep=()):
        for k in fonts:
            assert k in kit.FONTS, f"font {k!r}: register it first with p.font({k!r}, 'fonts/<file>', '<Family>')"
        self.fonts, self.texts, self.keep = tuple(fonts), dict(texts or {}), set(keep)
        self.cache_f = os.path.join(here, "build", "figma", "textfit.json")
        ver = hashlib.md5(open(textfit.__file__, "rb").read()).hexdigest()
        try:
            self.fits = json.load(open(self.cache_f))
        except (OSError, ValueError):
            self.fits = {}
        if self.fits.get("_v") != ver:
            self.fits = {"_v": ver}
        self.stats = {"texts": 0, "lines": 0, "kept": 0, "dots": 0}

    def save(self):
        os.makedirs(os.path.dirname(self.cache_f), exist_ok=True)
        json.dump(self.fits, open(self.cache_f, "w"))

    def _fit(self, content, polys, key):
        k = f"{key}|{content}|{','.join(self.fonts)}"
        if k not in self.fits:
            r = textfit.fit(content, polys, self.fonts)
            self.fits[k] = r and {**r, "lines": [list(x) for x in r["lines"]], "boxes": [list(b) for b in r["boxes"]]}
        r = self.fits[k]
        return r if r and r["size"] >= MIN_SIZE else None

    def __call__(self, e, m, st, conv, alpha=1.0):
        """-> (els, bbox) for an outlined text (or a dot grid), or None to keep the outline."""
        lid = e.get("id") or ""      # "": Figma leaves a text with mixed styles (a link in it) unnamed
        fill = st.get("fill", "black")
        a = attrs_of(e)
        if lid in self.keep or fill.startswith("url(") or st.get("stroke") not in (None, "none") \
                or a.get("transform") or not axis_aligned(m):
            return None
        d = a.get("d") or ""
        col = color(fill, num(st, "fill-opacity", 1.0) * num(a, "opacity", 1.0) * alpha)
        if not d or col is None:
            return None
        if conv.recolor:
            col = conv.recolor(e, col)
        polys = [[ap(m, p) for p in sp] for sp in textfit.subpaths(d)]
        if not polys:
            return None
        box = textfit.bbox(polys)
        if conv.cull and not intersect(box, conv.cull):
            return [], None
        if dot_grid_like(polys):
            self.stats["dots"] += len(polys)
            return dot_grid(polys, col, conv.name(lid)), box
        key = hashlib.md5(f"{lid}|{d}|{m}".encode()).hexdigest()
        given = (lid and self.texts.get(lid)) or self.texts.get(key[:8])
        if given:                    # the text given (a layer named otherwise: "Text_3", "Status" showing "Active")
            r = self._fit(given, polys, key)
        elif not lid:                # unnamed: an icon, or a text the sheet lists when it looks like one
            x0, y0, x1, y1 = box
            if len(polys) >= 8 and y1 - y0 <= 40 and x1 - x0 >= 3 * (y1 - y0):
                self.stats["kept"] += 1
                KEPT.append((key[:8], "(unnamed)", polys))
            return None
        else:                        # the layer's name, when the font draws as many pieces of ink as the outline
            r = self._fit(textfit.content_of(lid), polys, key)
            if r and r["pieces"][0] != r["pieces"][1]:
                r = None
        if not r:
            self.stats["kept"] += 1
            if len(polys) >= 4 and not lid.startswith("Vector"):
                KEPT.append((key[:8], lid, polys))
            return None
        size, ls = round(r["size"], 2), round(r["ls"], 3)
        sk = f"fig_{r['font']}_{r['wght']}_{size}_{ls}_{col}".replace(".", "p").replace("-", "m")
        if sk not in kit.STYLES:
            kit.text_style(sk, None, col, size=size, lh=round(size * LH, 2), weight=r["wght"], ls=ls or None,
                           font=r["font"])
        n = conv.name(lid)
        self.stats["texts"] += 1
        self.stats["lines"] += len(r["lines"])
        if conv.items is not None:    # a part: each line a text item, placed by the piece (conv.items)
            for k, ((s, x, base), b) in enumerate(zip(r["lines"], r["boxes"])):
                conv.items.append((f"{n}.l{k}", sk, s, x, base, b))
            return [], box
        els = []
        for k, (s, x, base) in enumerate(r["lines"]):
            els.append(line_text(f"{n}.l{k}", sk, s, x, base))
        return els, box


KEPT = []        # (key, layer id, contours) of the outlines no font redraws, for p.figma_sheet()


class Lit:
    """A text that starts with "@" (rml reads "@..." as a reference to resolve)."""

    def __init__(self, s):
        self.s = s

    def __str__(self):
        return self.s


def line_text(name, sk, s, x, base):
    """One native line: a Text on its baseline at (x, base)."""
    t = kit.text(name, [(sk, s)], lp=None, wrap=False)
    t.attrs.update({"x": round(x, 3), "y": round(base, 3), "originValue": "baseline"})
    for c in t.children:
        if c.tag == "TextValueRun" and str(c.attrs.get("text", "")).startswith("@"):
            c.attrs["text"] = Lit(c.attrs["text"])
    return t


def dot_grid_like(polys):
    if len(polys) < 50:
        return False
    sides = {round(b[2] - b[0], 1) for b in (textfit.bbox([s]) for s in polys)}
    return len(sides) == 1 and all(len(s) <= 5 for s in polys)


def dot_grid(polys, fill, name):
    """Rows of equal squares at a steady pitch -> one dashed line per row."""
    boxes = [textfit.bbox([s]) for s in polys]
    side = boxes[0][2] - boxes[0][0]
    xs = sorted({round(b[0], 3) for b in boxes})
    ys = sorted({round((b[1] + b[3]) / 2, 3) for b in boxes})
    pitch = xs[1] - xs[0]
    length = round((xs[-1] - xs[0]) / pitch + 1) * pitch       # whole pitches: each row starts in step
    paths = [El("PointsPath", {"isClosed": False}, [El("StraightVertex", {"x": xs[0], "y": y}),
                                                    El("StraightVertex", {"x": round(xs[0] + length, 4), "y": y})],
                name=f"{name}.row{k}") for k, y in enumerate(ys)]
    stroke = El("Stroke", {"thickness": round(side, 4), "cap": "butt"}, [
        El("SolidColor", {"colorValue": fill}),
        El("DashPath", {}, [El("Dash", {"length": round(side, 4)}, name=f"{name}.on"),
                            El("Dash", {"length": round(pitch - side, 4)}, name=f"{name}.off")], name=f"{name}.dash")],
        name=f"{name}.stroke")
    return [El("Shape", {}, paths + [stroke], name=name)]


# ---------------------------------------------------------------- the converter
class Conv:
    """SVG elements -> Rive elements (bottom to top) in the output's coordinates.
    drop: layer ids (or a function e -> True) left out; swap: {layer id: fn(e, m) -> (els, bbox)} drawn instead (a
    plate); text: the native text hook (Texts); cull: shapes wholly outside it are not drawn; visible: clips that
    cut only outside it are left out; recolor(e, argb) -> argb; items: a list that collects a part's text lines."""

    def __init__(self, svg, prefix, here, drop=(), swap=None, text=None, cull=None, visible=None, recolor=None,
                 register_image=None, items=None):
        self.svg, self.prefix, self.here = svg, prefix, here
        self.drop_fn = drop if callable(drop) else None
        self.drop = set() if callable(drop) else set(drop)
        self.swap, self.text, self.cull, self.visible = dict(swap or {}), text, cull, visible
        self.recolor, self.items = recolor, items
        self.register_image = register_image or kit.image_asset
        self.n, self.dropped, self.swapped = 0, set(), set()
        self.stats = {"shapes": 0, "clips": 0, "noop_clips": 0, "images": 0, "shadows": 0, "blurs": 0, "culled": 0}

    def name(self, label=None):
        self.n += 1
        label = re.sub(r"[^\w &/.,()+-]", "", textfit.content_of(label or ""))[:40]
        return f"{self.prefix}{self.n}" + (f" {label}" if label else "")

    # ------------------------------------------------------------ paints
    def gradient(self, g, m, opacity):
        a = attrs_of(g)
        gm = mul(m, parse_transform(a.get("gradientTransform")))
        assert a.get("gradientUnits") == "userSpaceOnUse", "objectBoundingBox gradient"
        stops = []
        for s in g.iter(NS + "stop"):
            sa = attrs_of(s)
            col = color(sa.get("stop-color", "#000"), num(sa, "stop-opacity", 1.0) * opacity)
            if col is None:      # Figma's clear stop ("stop-color:none" in its style): its attribute's colour
                col = color(s.get("stop-color", "#000"), num(sa, "stop-opacity", 1.0) * opacity)
            stops.append(El("GradientStop", {"colorValue": col, "position": num(sa, "offset")}))
        if g.tag == NS + "linearGradient":
            p0, p1 = ap(gm, (num(a, "x1"), num(a, "y1"))), ap(gm, (num(a, "x2"), num(a, "y2")))
            return El("LinearGradient", {"startX": p0[0], "startY": p0[1], "endX": p1[0], "endY": p1[1]}, stops)
        # radial: Figma writes cx=0 cy=0 r=1 and puts the ellipse in gradientTransform; Rive's is a circle
        c = ap(gm, (num(a, "cx"), num(a, "cy")))
        r = num(a, "r", 1.0)
        rx = math.dist(c, ap(gm, (num(a, "cx") + r, num(a, "cy"))))
        ry = math.dist(c, ap(gm, (num(a, "cx"), num(a, "cy") + r)))
        rad = (rx + ry) / 2
        return El("RadialGradient", {"startX": c[0], "startY": c[1], "endX": c[0] + rad, "endY": c[1]}, stops)

    def paint(self, e, kind, value, op, m, st, feather=None):
        """A Fill or Stroke El for value ('#hex' or url(#gradient)), or None."""
        if not value or value == "none":
            return None
        g = self.svg.ref(value)
        if g is not None:
            if g.tag not in (NS + "linearGradient", NS + "radialGradient"):
                return None
            ink = self.gradient(g, m, op)
        else:
            c = color(value, op)
            if c is None:
                return None
            if self.recolor:
                c = self.recolor(e, c)
            ink = El("SolidColor", {"colorValue": c})
        kids = [ink] + ([El("Feather", feather)] if feather else [])
        if kind == "fill":
            rule = "clockwise" if feather else ("evenOdd" if st.get("fill-rule") == "evenodd" else None)
            return El("Fill", {"fillRule": rule}, kids)
        caps = {"round": "round", "square": "square"}
        joins = {"round": "round", "bevel": "bevel"}
        return El("Stroke", {"thickness": num(st, "stroke-width", 1.0) * scale_of(m),
                             "cap": caps.get(st.get("stroke-linecap")), "join": joins.get(st.get("stroke-linejoin"))},
                  kids)

    # ------------------------------------------------------------ clips and masks
    def clip_source(self, shapes, label, rule=None):
        n = self.name(label)
        kids = []
        for i, g in enumerate(shapes):
            kids += g.els(f"{n}.p{i}")
        return [El("ClippingShape", {"sourceId": "@" + n, "fillRule": rule or "nonZero"}), El("Shape", {}, kids, name=n)]

    def unseen(self, geos, content, tol=1.5):
        """A clip that cuts nothing anyone sees: the content, where it can show (self.visible), inside it give or
        take tol px; a round one only when the content is clear of its corners."""
        if not self.visible or content is None or len(geos) != 1:
            return False
        v = self.visible
        c = (max(content[0], v[0]), max(content[1], v[1]), min(content[2], v[2]), min(content[3], v[3]))
        if c[2] <= c[0] or c[3] <= c[1]:
            return True
        g = geos[0]
        b = g.bbox
        if not (c[0] >= b[0] - tol and c[1] >= b[1] - tol and c[2] <= b[2] + tol and c[3] <= b[3] + tol):
            return False
        upright = (g.kind == "rect" and not g.data[4]) or (
            g.kind == "path" and len(g.data) == 1 and len(g.data[0]) <= 5
            and all(v_["in"] is None and v_["out"] is None for v_ in g.data[0])
            and len({round(v_["p"][0], 2) for v_ in g.data[0]}) == 2
            and len({round(v_["p"][1], 2) for v_ in g.data[0]}) == 2)
        if upright:
            return True
        if g.kind == "rect":           # round corners: content clear of them cuts nothing either
            x, y, w, h, r = g.data

            def clear(px, py, cx, cy):
                dx, dy = abs(px - cx), abs(py - cy)
                return dx >= r or dy >= r or (r - dx) ** 2 + (r - dy) ** 2 <= r * r
            return all(clear(px, py, cx, cy) for (px, py), (cx, cy) in
                       zip([(c[0], c[1]), (c[2], c[1]), (c[0], c[3]), (c[2], c[3])],
                           [(x, y), (x + w, y), (x, y + h), (x + w, y + h)]))
        return False

    @staticmethod
    def is_noop(shapes, content):
        """A clip that cuts nothing: one upright rectangle around all of the content, clear of its round corners."""
        if content is None or len(shapes) != 1 or shapes[0].kind != "rect":
            return False
        x, y, w, h, r = shapes[0].data
        e = 0.01
        inside = content[0] >= x - e and content[1] >= y - e and content[2] <= x + w + e and content[3] <= y + h + e
        if not inside or not r:
            return inside
        return (content[0] >= x + r - e and content[2] <= x + w - r + e) or \
               (content[1] >= y + r - e and content[3] <= y + h - r + e)

    def clip_geos(self, el, m):
        geos, holes = [], False
        default = attrs_of(el).get("fill")
        for c in el.iter():
            if c is el or c.tag.replace(NS, "") not in ("path", "rect", "circle", "ellipse"):
                continue
            g = geometry(c, m)
            if g is None:
                continue
            f = attrs_of(c).get("fill", default)
            if el.tag == NS + "mask" and color(f) == argb("#000000"):
                holes = True                   # black in a mask cuts a hole: inside a white shape, evenOdd does it
            geos.append(g)
        return geos, ("evenOdd" if holes else None)

    # ------------------------------------------------------------ effects
    @staticmethod
    def effects(flt):
        """A <filter> -> (shadows [(dx, dy, blur, spread, ARGB)], blur): Figma's drop shadows and layer blur.
        Noise (feTurbulence, Figma's grain) and the rest are left out."""
        shadows, blur, cur = [], 0.0, {}
        for fe in flt:
            t, a = fe.tag.replace(NS, ""), attrs_of(fe)
            if t == "feMorphology" and a.get("in") == "SourceAlpha":
                r = num(a, "radius")
                cur = {"spread": -r if a.get("operator") == "erode" else r}
            elif t == "feColorMatrix" and a.get("in") == "SourceAlpha":
                cur = {"spread": 0.0}
            elif t == "feOffset":
                cur.update(dx=num(a, "dx"), dy=num(a, "dy"))
            elif t == "feGaussianBlur":
                if a.get("in") is None and "spread" in cur:
                    cur["blur"] = 2 * num(a, "stdDeviation")     # Figma's blur = 2 x stdDeviation = the DS's feather
                elif a.get("in") in (None, "shape", "SourceGraphic"):
                    blur = 2 * num(a, "stdDeviation")
            elif t == "feColorMatrix" and a.get("type") == "matrix" and "spread" in cur:
                v = [float(x) for x in a["values"].split()]
                cur["color"] = argb("#%02X%02X%02X" % tuple(round(255 * v[i]) for i in (4, 9, 14)), v[18])
                shadows.append(cur)
                cur = {}
        return shadows, blur

    # ------------------------------------------------------------ the walk
    def walk(self, e, m, style, fx):
        """-> (els bottom to top, bbox) for element e (fx: the blur and the opacity it is drawn with)."""
        tag = e.tag.replace(NS, "")
        if tag in SKIP:
            return [], None
        lid = e.get("id")
        if lid in self.drop or (self.drop_fn and self.drop_fn(e)):
            self.dropped.add(lid)
            return [], None
        if lid in self.swap:
            self.swapped.add(lid)
            return self.swap[lid](e, m)
        a = attrs_of(e)
        st = dict(style)
        st.update({k: a[k] for k in INHERITED if k in a})
        flt = self.svg.ref(a.get("filter"))
        shadows, blur = self.effects(flt) if flt is not None else ([], 0.0)
        fx2 = dict(fx)
        if blur:
            fx2["blur"] = blur
        if tag in ("g", "svg"):
            fx2["op"] = fx.get("op", 1.0) * num(a, "opacity", 1.0)
            m2 = mul(m, parse_transform(a.get("transform"))) if tag == "g" else m
            out, box = [], None
            for c in e:
                els, b = self.walk(c, m2, st, fx2)
                out += els
                box = union(box, b)
        else:
            m2 = m
            got = None
            if self.text and tag == "path" and not fx2.get("blur"):
                got = self.text(e, m, st, self, fx.get("op", 1.0) if self.items is not None else 1.0)
            if got is not None:
                out, box = got
            else:
                out, box = self.shape(e, m, st, fx2, a)
        if shadows and out:
            first = next((x for x in e.iter() if x.tag.replace(NS, "") in ("path", "rect", "circle", "ellipse")), None)
            g = geometry(first, m2 if tag == "g" else m) if first is not None else None
            if g is not None:
                out = self.shadow_shapes(g, shadows, m2, lid) + out
                box = union(box, grow(g.bbox, max(s["blur"] + abs(s.get("dx", 0)) + abs(s.get("dy", 0))
                                                  for s in shadows)))
        return self.wrap(e, a, m2, out, box)

    def wrap(self, e, a, m, out, box):
        """A Node around out when e has an opacity, a clip-path or a mask."""
        if not out:
            return out, box
        op = num(a, "opacity", 1.0)
        clip = []
        for key in ("clip-path", "mask"):
            ref = self.svg.ref(a.get(key))
            if ref is None:
                continue
            geos, rule = self.clip_geos(ref, m)
            if not geos:
                continue
            if self.is_noop(geos, box) or self.unseen(geos, box):
                self.stats["noop_clips"] += 1
                continue
            clip += self.clip_source(geos, f"{e.get('id') or ''} {key}".strip(), rule)
            self.stats["clips"] += 1
            if box is not None and not rule and len(geos) == 1:          # what shows is inside the clip
                g = geos[0].bbox
                box = (max(box[0], g[0]), max(box[1], g[1]), min(box[2], g[2]), min(box[3], g[3]))
        if op >= 0.999 and not clip:
            return out, box
        return [El("Node", {"opacity": op if op < 0.999 else None}, out + clip, name=self.name(e.get("id")),
                   order="layers")], box

    def shadow_shapes(self, g, shadows, m, label):
        out = []
        for s in shadows:
            gs = g.shrunk(-s.get("spread", 0.0) * scale_of(m)).clockwise()
            n = self.name(f"{label} shadow")
            f = El("Fill", {"fillRule": "clockwise"}, [El("SolidColor", {"colorValue": s["color"]}),
                                                      El("Feather", {"strength": s["blur"] * scale_of(m),
                                                                     "offsetX": s.get("dx", 0) * m[0] or None,
                                                                     "offsetY": s.get("dy", 0) * m[3] or None})])
            out.append(El("Shape", {}, gs.els(f"{n}.path") + [f], name=n))
            self.stats["shadows"] += 1
        return out

    def shape(self, e, m, st, fx, a):
        g = geometry(e, m)
        if g is None:
            return [], None
        op = num(a, "opacity", 1.0)
        fill_v, stroke_v = st.get("fill", "black"), st.get("stroke")
        pat = self.svg.ref(fill_v)
        if pat is not None and pat.tag == NS + "pattern":
            return self.image_fill(e, m, g, pat, op * num(st, "fill-opacity", 1.0))
        feather = {"strength": fx["blur"] * scale_of(m)} if fx.get("blur") else None
        if feather:
            g = g.clockwise()
            self.stats["blurs"] += 1
        if e.tag == NS + "line" and stroke_v and num(st, "stroke-width", 1.0) * scale_of(m) < HAIRLINE:
            st = {**st, "stroke-width": str(HAIRLINE / scale_of(m))}
        paints = [self.paint(e, "fill", fill_v, num(st, "fill-opacity", 1.0), m, st, feather),
                  self.paint(e, "stroke", stroke_v, num(st, "stroke-opacity", 1.0), m, st)]
        paints = [p for p in paints if p is not None]
        if not paints:
            return [], None
        sw = num(st, "stroke-width", 1.0) * scale_of(m) / 2 if stroke_v and stroke_v != "none" else 0.0
        box = grow(g.bbox, sw + (feather["strength"] if feather else 0.0))
        if self.cull and not intersect(box, self.cull):
            self.stats["culled"] += 1
            return [], None
        n = self.name(e.get("id"))
        self.stats["shapes"] += 1
        return [El("Shape", {"opacity": op if op < 0.999 else None}, g.els(f"{n}.path") + paints, name=n)], box

    def image_fill(self, e, m, g, pat, op):
        """A shape filled with an image (Figma's image fill: a pattern in the shape's bounding box): the photo as a
        Rive Image, cut by the shape."""
        use = pat.find(NS + "use")
        im = self.svg.ref(f"url({use.get(HREF)})") if use is not None else None
        assert im is not None and attrs_of(pat).get("patternContentUnits") == "objectBoundingBox", "pattern kind"
        pm = parse_transform(use.get("transform"))
        a = attrs_of(e)
        em = mul(m, parse_transform(a.get("transform")))
        if e.tag == NS + "rect":
            bx, by, bw, bh = num(a, "x"), num(a, "y"), num(a, "width"), num(a, "height")
        else:
            inv = geometry(e, I2).bbox
            bx, by, bw, bh = inv[0], inv[1], inv[2] - inv[0], inv[3] - inv[1]
        W, H = num(attrs_of(im), "width"), num(attrs_of(im), "height")
        full = mul(em, mul((bw, 0, 0, bh, bx, by), pm))      # image px -> bbox units -> user space -> output
        assert abs(full[1]) < 1e-9 and abs(full[2]) < 1e-9, "rotated image fill"
        (x0, y0), (x1, y1) = ap(full, (0, 0)), ap(full, (W, H))
        flip = (x1 < x0, y1 < y0)                  # a mirrored photo (matrix(-1 0 0 1 ...))
        x0, x1 = sorted((x0, x1))
        y0, y1 = sorted((y0, y1))
        show = intersect((x0, y0, x1, y1), g.bbox)                      # what of the photo can show: only that is kept
        if self.cull:
            show = show and intersect(show, self.cull)
        if not show:
            return [], None
        key, px, (ox0, oy0, ox1, oy1) = self.save_image(im, (x0, y0, x1, y1), show, flip)
        n = self.name(e.get("id"))
        img = El("Image", {"assetId": f"@img.{key}", "x": (ox0 + ox1) / 2, "y": (oy0 + oy1) / 2,
                           "scaleX": (ox1 - ox0) / px[0], "scaleY": (oy1 - oy0) / px[1],
                           "opacity": op if op < 0.999 else None}, name=n)
        self.stats["images"] += 1
        box = (ox0, oy0, ox1, oy1)
        if self.is_noop([g], box):
            return [img], box
        self.stats["clips"] += 1
        return [El("Node", {}, [img] + self.clip_source([g], f"{e.get('id')} clip"), name=self.name(e.get("id")),
                   order="layers")], g.bbox

    def save_image(self, im, full, show, flip=(False, False)):
        """The part of the embedded image that can show, at most 2x its size on screen, in build/figma/img/.
        -> asset key, its px size, the box it covers (whole source px)."""
        data = base64.b64decode(im.get(HREF).split(",", 1)[1])
        src = Image.open(io.BytesIO(data))
        if flip[0]:
            src = src.transpose(Image.FLIP_LEFT_RIGHT)
        if flip[1]:
            src = src.transpose(Image.FLIP_TOP_BOTTOM)
        x0, y0, x1, y1 = full
        kx, ky = src.width / (x1 - x0), src.height / (y1 - y0)
        u0, v0 = max(0, math.floor((show[0] - x0) * kx)), max(0, math.floor((show[1] - y0) * ky))
        u1, v1 = min(src.width, math.ceil((show[2] - x0) * kx)), min(src.height, math.ceil((show[3] - y0) * ky))
        box = (x0 + u0 / kx, y0 + v0 / ky, x0 + u1 / kx, y0 + v1 / ky)
        tw = min(u1 - u0, math.ceil(2 * (box[2] - box[0])))
        th = min(v1 - v0, math.ceil(2 * (box[3] - box[1])))
        digest = hashlib.sha1(data + bytes(flip)).hexdigest()[:10]
        key = f"fig_{digest}_{u0}_{v0}_{u1}_{v1}_{tw}x{th}"
        crop = src.convert("RGBA").crop((u0, v0, u1, v1))
        alpha = crop.getextrema()[3][0] < 255
        out_dir = os.path.join(self.here, "build", "figma", "img")
        path = os.path.join(out_dir, f"{key}.{'png' if alpha else 'jpg'}")
        if not os.path.exists(path):
            os.makedirs(out_dir, exist_ok=True)
            out = crop.convert("RGBA" if alpha else "RGB").resize((tw, th), Image.LANCZOS)
            out.save(path, **({"optimize": True} if alpha else {"quality": 92, "subsampling": 0}))
        self.register_image(key, path)
        return key, (tw, th), box


# ---------------------------------------------------------------- plates: still parts as 2x images
def render_plate(here, els, box, images, scale=PLATE_SCALE):
    """Rive draws `els` (output coordinates, back to front) on white and on black at `scale`; the difference gives
    the transparency. -> (png path, (x, y) top-left in output coordinates, (px w, px h)), cached by content."""
    x0, y0 = math.floor(box[0]) - 2, math.floor(box[1]) - 2
    w, h = math.ceil(box[2]) + 2 - x0, math.ceil(box[3]) + 2 - y0
    out_dir = os.path.join(here, "build", "figma", "plates")
    proj = os.path.join(out_dir, "_render")
    os.makedirs(proj, exist_ok=True)

    def scene(bg):
        assets = [El("ImageAsset", {"file": os.path.relpath(p, proj)}, name=f"img.{k}") for k, p in images.items()]
        art = El("Artboard", {"width": w, "height": h, "clip": True},
                 [El("Fill", {}, [El("SolidColor", {"colorValue": bg})]),
                  El("Node", {"x": -x0, "y": -y0}, copy.deepcopy(els), order="layers", name="plate")], name="PLATE")
        root = El("Rive", {"version": 1, "kind": "fragment"}, assets + [art])
        doc = kit.Doc("0")
        doc.assign(root)
        doc.resolve(root)
        return doc.xml(root)
    white = scene("FFFFFFFF")
    digest = hashlib.sha1(f"{white}|{scale}|{x0},{y0}".encode()).hexdigest()[:16]
    png, meta = os.path.join(out_dir, f"plate_{digest}.webp"), os.path.join(out_dir, f"plate_{digest}.json")
    if os.path.exists(png) and os.path.exists(meta):
        return png, tuple(json.load(open(meta))["at"]), Image.open(png).size
    import numpy as np
    shots = {}
    open(os.path.join(proj, "rive.yaml"), "w").write('name: plate\nmain: "PLATE"\n')
    for bg, xml in (("white", white), ("black", scene("FF000000"))):
        open(os.path.join(proj, "scene.rml"), "w").write(xml + "\n")
        shot = os.path.join(proj, f"{bg}.png")
        r = subprocess.run([RIVE, proj, f"--screenshot={shot}", "--artboard=PLATE", f"--viewport={w * scale}x{h * scale}",
                            "--fit=contain", "--advance=1", "--quiet"], capture_output=True, text=True, timeout=180)
        if r.returncode or not os.path.exists(shot):
            raise RuntimeError("plate render failed:\n" + (r.stdout + r.stderr)[-1500:])
        shots[bg] = np.asarray(Image.open(shot).convert("RGB"), dtype=np.float32)
    W, B = shots["white"], shots["black"]
    a = np.clip(1 - (W - B).mean(axis=2) / 255, 0, 1)
    C = np.clip(B / np.maximum(a, 1 / 255)[..., None], 0, 255)
    rgba = np.dstack([C, a * 255]).round().astype(np.uint8)
    ys, xs = np.nonzero(rgba[..., 3] > 0)
    if not len(xs):
        raise RuntimeError("plate render: nothing drawn")
    l, t, r_, b_ = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
    Image.fromarray(rgba[t:b_, l:r_]).save(png, "WEBP", lossless=True, quality=100, method=6)
    at = (x0 + l / scale, y0 + t / scale)
    json.dump({"at": at}, open(meta, "w"))
    return png, at, (int(r_ - l), int(b_ - t))


def plate_el(here, name, els, box, images, scale=PLATE_SCALE):
    """An Image in place of `els` (their 2x render), registered as an asset."""
    png, (x, y), (pw, ph) = render_plate(here, els, box, images, scale)
    key = os.path.splitext(os.path.basename(png))[0]
    kit.image_asset(key, png)
    return El("Image", {"assetId": f"@img.{key}", "x": x + pw / scale / 2, "y": y + ph / scale / 2,
                        "scaleX": 1 / scale, "scaleY": 1 / scale}, name=name), (x, y, x + pw / scale, y + ph / scale)


# ---------------------------------------------------------------- the piece's call
class FigmaPatterns:
    """p.figma_screen and p.figma_sheet (mixed into Piece)."""

    def figma_screen(self, name, src, layer=None, w=None, h=None, frame=None, origin=(0.0, 0.0), drop=(), parts=(),
                     plates=(), fonts=("duda",), texts=None, keep=(), native=True, visible="auto", edit=None,
                     recolor=None):
        """A Figma screen from its SVG export (a file in the piece folder) as one item: vectors, native text, the
        photos as images. Place it like any item (p.free, p.stack, p.layout); the actions animate it (a.enter,
        a.cut between two screens) and its `parts` (a.generate, a.enter, p.hoverable).

        layer: the layer to draw (its name as Figma has it; None: the whole export). w, h: the item's box (default:
        the frame's size, else the export's). frame=(w, h): the export carries a frame of that size (Figma exports a
        node with its ancestors): the box's (0, 0) is that frame's top-left. origin: else, where the export's (0, 0)
        sits in the box. drop: layers left out (the library draws them: a button, a field); a function e -> True
        too. parts: layers that become their own items (scr.parts[layer]), on top of the rest, their texts text
        items (a generation types them in). plates: still layers drawn as 2x images (True: the whole screen).
        fonts: the font keys native text may use (the library's "duda"; a client's after p.font(key, ...)).
        texts: {layer name or sheet key: "its text"} for texts not named by their text, unnamed ones (a text with
        a link in it) and look-alikes (a badge named "Status" showing "Active"): p.figma_sheet() shows them. keep:
        text layers left outlined. native=False: every text stays outlined. visible: (x0, y0, x1, y1) in the box
        where the screen can ever show; what lies wholly outside is not drawn, a clip that cuts only outside it is
        left out ("auto": the box and 64 px around it; None: keep all). edit: fn(svg) that changes the export first
        (on a fresh copy: svg.add_rect for a one-side border Figma leaves out). recolor: fn(element, ARGB) -> ARGB."""
        path = src if os.path.isabs(src) else os.path.join(self.here, src)
        svg = load(path)
        if edit:
            svg = Svg(path)
            edit(svg)
        if layer is None:
            root, m, style = svg.root, I2, {}
        else:
            root, m, style = svg.layer(layer)
        if frame is not None:
            origin = svg.frame_origin(frame)
            w, h = w or frame[0], h or frame[1]
        if w is None or h is None:
            sw, sh = svg.size()
            w, h = w or sw, h or sh
        m = mul(shift(*origin), m)
        if visible == "auto":
            visible = (-MARGIN, -MARGIN, w + MARGIN, h + MARGIN)
        text = Texts(self.here, fonts, texts, keep) if native else None
        art = f"{self.art}.{name}"
        stats = {}

        def count(c):
            for k, v in c.stats.items():
                stats[k] = stats.get(k, 0) + v

        # plates: each drawn as an image where the layer is (keeps the layer order)
        plate_ids = set() if plates is True else {svg.layer(pl)[0].get("id") for pl in plates}

        def plate_swap(e, mm):
            imgs = {}
            sub = Conv(svg, f"{art}.plate.", self.here, drop=drop, cull=visible, visible=visible, recolor=recolor,
                       register_image=lambda k, p: imgs.__setitem__(k, p))
            els, box = sub.walk(e, mm, svg.chain(e)[1], {})
            if not els:
                return [], None
            el, box = plate_el(self.here, f"{art}.plate{len(stats.setdefault('plate_list', []))}", els, box, imgs)
            stats["plate_list"].append(box)
            return [el], box
        swap = {pid: plate_swap for pid in plate_ids}

        # the parts: their own items, on top of the rest
        part_ids = {svg.layer(pt)[0].get("id"): pt for pt in parts}
        drops = (lambda e: drop(e) or e.get("id") in part_ids) if callable(drop) else set(drop) | set(part_ids)
        dropped = set()
        if plates is True:
            base_els, box = plate_swap(root, m)
        else:
            conv = Conv(svg, f"{art}.", self.here, drop=drops, swap=swap, text=text, cull=visible, visible=visible,
                        recolor=recolor)
            base_els, box = conv.walk(root, m, style, {})
            count(conv)
            dropped |= conv.dropped
        base = [El("Node", {}, base_els, name=f"{art}.art", order="layers")] if base_els else []
        part_items = {}
        placed = []
        for pid, pname in part_ids.items():
            e, pm, pst = svg.layer(pid)
            lines = []
            pc = Conv(svg, f"{art}_{slug(pname)}.", self.here, drop=drop, swap=swap, text=text, cull=visible,
                      visible=visible, recolor=recolor, items=lines)
            pels, pbox = pc.walk(e, mul(shift(*origin), pm), pst, {})
            count(pc)
            dropped |= pc.dropped
            assert pbox is not None, f"{name}: part {pname!r} draws nothing"
            x0, y0 = math.floor(pbox[0]), math.floor(pbox[1])
            pw, ph = math.ceil(pbox[2]) - x0, math.ceil(pbox[3]) - y0
            iname = f"{name}_{slug(pname)}"
            while iname in self.items:
                iname += "x"
            kids = [El("Node", {"x": -x0, "y": -y0}, pels, name=f"{self.art}.{iname}.art", order="layers")]
            titems = []
            for k, (ln, sk, s, x, base_y, b) in enumerate(lines):
                tname = f"{iname}T{k}"
                bx, by = math.floor(b[0]), math.floor(b[1])
                t = line_text(f"{self.art}.{tname}.t", sk, s, x - bx, base_y - by)
                tw = kit.absolute(f"{self.art}.{tname}", [El("Node", {}, [t], name=f"{self.art}.{tname}.n")],
                                  inset=(bx - x0, by - y0, None, None), layoutWidthScaleType="fixed",
                                  layoutHeightScaleType="fixed")
                tw.attrs.update(width=math.ceil(b[2]) - bx, height=math.ceil(b[3]) - by)
                ti = Item(self, tname, "text", tw)
                self.items[tname] = ti
                titems.append(ti)
            radius = self._figma_radius(e, pm, svg, pbox)
            item = self.wrap(iname, [ti.wrap for ti in titems] + kids, w=pw, h=ph)
            if radius:
                st = next(c for c in item.wrap.children if c.tag == "LayoutComponentStyle")
                st.attrs["cornerRadiusTL"] = radius
            item.texts = titems
            part_items[pname] = item
            placed.append((item, x0, y0))
        missing = set() if callable(drop) or plates is True else set(drop) - dropped
        assert not missing, f"{name}: no layer {sorted(missing)} to leave out"
        if text is not None:
            text.save()
            for k, v in text.stats.items():
                stats[k] = stats.get(k, 0) + v
        if placed:
            inner = self.wrap(f"{name}Base", base, w=w, h=h)
            scr = self.free(name, [(inner, 0, 0)] + placed, w=w, h=h, clip=False)
        else:
            scr = self.wrap(name, base, w=w, h=h)
        scr.parts, scr.figma = part_items, stats
        n_pl = len(stats.pop("plate_list", []))
        stats["plates"] = n_pl
        print(f"figma {name}: {stats.get('shapes', 0)} shapes, {stats.get('texts', 0)} native texts "
              f"({stats.get('lines', 0)} lines), {stats.get('kept', 0)} outlined, {stats.get('images', 0)} images, "
              f"{n_pl} plates, {stats.get('clips', 0)} clips ({stats.get('noop_clips', 0)} left out), "
              f"{stats.get('culled', 0)} off-screen shapes not drawn")
        return scr

    @staticmethod
    def _figma_radius(e, m, svg, box):
        """A part's corner radius: its first shape's, when that is a rect as big as the part (a card's background)."""
        first = next((x for x in e.iter() if x.tag.replace(NS, "") in ("rect", "path")), None)
        if first is None:
            return 0.0
        g = geometry(first, svg.chain(first)[0])         # export coordinates: only its size and radius are read
        if g is None or g.kind != "rect":
            return 0.0
        gx0, gy0, gx1, gy1 = g.bbox
        if (gx1 - gx0) * (gy1 - gy0) < 0.9 * (box[2] - box[0]) * (box[3] - box[1]):
            return 0.0
        return round(g.data[4], 2)

    def figma_sheet(self, scale=3, width=1400):
        """build/figma/kept_<n>.png: the outlined texts no font redrew (not icons), big, each with its key and layer
        name: read the texts of layers named otherwise ("Text_3") and give them as figma_screen(texts={key: ...})."""
        from PIL import ImageDraw
        seen, tiles = set(), []
        for k, lid, polys in KEPT:
            if k in seen:
                continue
            seen.add(k)
            x0, y0, x1, y1 = textfit.bbox(polys)
            mm = textfit.raster(polys, (x0 - 1, y0 - 1, x1 + 1, y1 + 1), ss=scale, over=2)
            tile = Image.new("L", (max(mm.width, 260), mm.height + 16), 255)
            tile.paste(mm.convert("L").point(lambda v: 255 - v), (0, 16))
            ImageDraw.Draw(tile).text((2, 2), f"{k}  {textfit.content_of(lid)[:30]}", fill=120)
            tiles.append(tile)
        out = os.path.join(self.here, "build", "figma")
        os.makedirs(out, exist_ok=True)
        for f in os.listdir(out):                  # an older sheet would list texts already named
            if f.startswith("kept_") and f.endswith(".png"):
                os.remove(os.path.join(out, f))
        pages, y, page = [], 0, []
        for t in tiles:
            if y + t.height > 1600 and page:
                pages.append(page)
                page, y = [], 0
            page.append(t)
            y += t.height + 6
        if page:
            pages.append(page)
        for i, pg in enumerate(pages):
            im = Image.new("L", (min(width, max(t.width for t in pg)), sum(t.height + 6 for t in pg)), 255)
            yy = 0
            for t in pg:
                im.paste(t.crop((0, 0, min(t.width, im.width), t.height)), (0, yy))
                yy += t.height + 6
            im.save(os.path.join(out, f"kept_{i}.png"))
        print(f"figma sheets: {len(pages)} pages, {len(tiles)} outlined texts in build/figma/")
        return len(tiles)
