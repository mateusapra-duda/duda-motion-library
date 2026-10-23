"""Tiny RML builder: Python objects -> Rive Markup Language with stable ids and a name registry.

Children are listed bottom-to-top (like Figma/AE layers); the serializer reverses them because
in RML the first declared sibling draws on top.
"""
from xml.sax.saxutils import quoteattr


def argb(hex_rgb, alpha=1.0):
    """'#272b35' (+alpha 0..1) -> 'FF272B35'."""
    h = hex_rgb.lstrip("#")
    if len(h) == 8:  # already AARRGGBB
        return h.upper()
    return f"{round(alpha * 255):02X}{h.upper()}"


def fmt(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, float):
        s = f"{v:.4f}".rstrip("0").rstrip(".")
        return s if s not in ("-0", "") else "0"
    return str(v)


class El:
    def __init__(self, tag, attrs=None, children=None, name=None, order="as_is", ref=None):
        self.tag, self.attrs = tag, dict(attrs or {})
        self.ref = ref  # registry key for elements that can't carry a name (states)
        self.children = list(children or [])
        self.name = name
        self.order = order  # "layers": children given bottom->top, reversed on output
        self.id = None

    def add(self, *els):
        self.children.extend(e for e in els if e is not None)
        return self


class Doc:
    def __init__(self, client="0"):
        self.client, self.n = client, 0
        self.by_name = {}

    def assign(self, el):
        self.n += 1
        el.id = f"{self.client}:{self.n}"
        key = el.ref or el.name
        if key:
            if key in self.by_name:
                raise ValueError(f"duplicate name {key!r}")
            self.by_name[key] = el
        for c in el.children:
            if isinstance(c, El):
                self.assign(c)

    def resolve(self, el):
        """Replace '@name' attribute values with the referenced element id."""
        for k, v in list(el.attrs.items()):
            if isinstance(v, str) and v.startswith("@"):
                el.attrs[k] = self.by_name[v[1:]].id
        for c in el.children:
            if isinstance(c, El):
                self.resolve(c)

    def xml(self, el, indent=0):
        pad = "    " * indent
        attrs = {k: v for k, v in el.attrs.items() if v is not None}
        if el.name:
            attrs["name"] = el.name
        if el.id and el.tag not in ("Rive",):
            attrs["id"] = el.id
        a = "".join(f" {k}={quoteattr(fmt(v))}" for k, v in attrs.items())
        kids = [c for c in el.children if c is not None]
        if el.order == "layers":
            kids = list(reversed(kids))
        if not kids:
            return f"{pad}<{el.tag}{a}/>"
        body = "\n".join(c if isinstance(c, str) else self.xml(c, indent + 1) for c in kids)
        return f"{pad}<{el.tag}{a}>\n{body}\n{pad}</{el.tag}>"


# ---------- paints ----------
def solid(color, name=None):
    return El("SolidColor", {"colorValue": color}, name=name)


def fill(color, name=None, rule=None, feather=None):
    """feather = dict(strength=, offsetY=, offsetX=, inner=)"""
    kids = [solid(color, name=(name + ".color") if name else None)]
    if feather:
        kids.append(El("Feather", feather, name=(name + ".feather") if name else None))
    return El("Fill", {"fillRule": rule}, kids, name=name)


def gradient_fill(stops, start, end, name):
    """stops: [(color, pos)], start/end: (x, y) in the shape's local space."""
    g = El("LinearGradient", {"startX": start[0], "startY": start[1], "endX": end[0], "endY": end[1]},
           [El("GradientStop", {"colorValue": c, "position": p}, name=f"{name}.stop{i}") for i, (c, p) in enumerate(stops)],
           name=f"{name}.grad")
    return El("Fill", {}, [g], name=name)


def gradient_stroke(stops, start, end, width, name):
    g = El("LinearGradient", {"startX": start[0], "startY": start[1], "endX": end[0], "endY": end[1]},
           [El("GradientStop", {"colorValue": c, "position": p}, name=f"{name}.stop{i}") for i, (c, p) in enumerate(stops)],
           name=f"{name}.grad")
    return El("Stroke", {"thickness": width}, [g], name=name)


def stroke(color, width, name=None, cap=None, join=None, trim=None):
    kids = [solid(color, name=(name + ".color") if name else None)]
    if trim:
        kids.append(El("TrimPath", trim, name=(name + ".trim") if name else None))
    return El("Stroke", {"thickness": width, "cap": cap, "join": join}, kids, name=name)


# ---------- shapes ----------
def rect(name, x, y, w, h, r=0, fill_color=None, stroke_color=None, stroke_w=0.0, shadow=None,
         opacity=None, radii=None, extra_paints=None):
    """Top-left anchored rectangle at (x, y). shadow = (color, strength, offx, offy)."""
    ra = {"cornerRadiusTL": r} if r and not radii else {}
    if radii:
        ra = {"linkCornerRadius": False, "cornerRadiusTL": radii[0], "cornerRadiusTR": radii[1],
              "cornerRadiusBR": radii[2], "cornerRadiusBL": radii[3]}
    path = El("Rectangle", {"width": w, "height": h, "originX": 0, "originY": 0, **ra}, name=f"{name}.rect")
    paints = []  # bottom -> top
    if shadow:
        c, s, ox, oy = shadow
        paints.append(fill(c, name=f"{name}.shadow", rule="clockwise",
                           feather={"strength": s, "offsetX": ox or None, "offsetY": oy or None}))
    if fill_color:
        paints.append(fill(fill_color, name=f"{name}.fill"))
    paints += extra_paints or []
    if stroke_color and stroke_w:
        paints.append(stroke(stroke_color, stroke_w, name=f"{name}.stroke"))
    # inside one shape the LAST paint draws on top -> keep bottom->top order as declared
    return El("Shape", {"x": x, "y": y, "opacity": opacity}, [path] + paints, name=name)


def ellipse(name, cx, cy, w, h, fill_color=None, stroke_color=None, stroke_w=0.0, opacity=None):
    path = El("Ellipse", {"width": w, "height": h}, name=f"{name}.ellipse")
    paints = []
    if fill_color:
        paints.append(fill(fill_color, name=f"{name}.fill"))
    if stroke_color and stroke_w:
        paints.append(stroke(stroke_color, stroke_w, name=f"{name}.stroke"))
    return El("Shape", {"x": cx, "y": cy, "opacity": opacity}, [path] + paints, name=name)


def clip_source(name, x, y, w, h, r=0):
    """A paintless rectangle used as a ClippingShape source (top-left anchored)."""
    ra = {"cornerRadiusTL": r} if r else {}
    return El("Shape", {"x": x, "y": y}, [El("Rectangle", {"width": w, "height": h, "originX": 0, "originY": 0, **ra},
                                               name=f"{name}.rect")], name=name)


def clip_ellipse_source(name, cx, cy, d):
    return El("Shape", {"x": cx, "y": cy}, [El("Ellipse", {"width": d, "height": d}, name=f"{name}.ellipse")], name=name)


def clipping(source_name, name=None):
    return El("ClippingShape", {"sourceId": "@" + source_name, "fillRule": "nonZero"}, name=name)


def node(name, children=(), x=0, y=0, opacity=None, scale=None, rotation=None):
    attrs = {"x": x, "y": y, "opacity": opacity}
    if scale is not None:
        attrs["scaleX"] = attrs["scaleY"] = scale
    if rotation is not None:
        attrs["rotation"] = rotation
    return El("Node", attrs, list(children), name=name, order="layers")


# ---------- images ----------
class Assets:
    def __init__(self):
        self.fonts, self.images = {}, {}

    def font(self, key, file, family):
        self.fonts[key] = El("FontAsset", {"file": file}, name=f"font.{key}")
        self.fonts[key].family = family
        return self

    def image(self, key, file, px_w, px_h):
        el = El("ImageAsset", {"file": file}, name=f"img.{key}")
        el.px = (px_w, px_h)
        self.images[key] = el
        return self

    def roots(self):
        return list(self.fonts.values()) + list(self.images.values())


def image(assets, name, key, x, y, w, h=None, opacity=None):
    """Place an image asset with its top-left at (x, y) displayed w wide (h follows aspect unless given)."""
    a = assets.images[key]
    sx = w / a.px[0]
    sy = (h / a.px[1]) if h else sx
    cx, cy = x + a.px[0] * sx / 2, y + a.px[1] * sy / 2
    return El("Image", {"x": cx, "y": cy, "scaleX": sx, "scaleY": sy, "assetId": f"@img.{key}", "opacity": opacity}, name=name)


# ---------- text ----------
WGHT = 2003265652  # 'wght'


def text(assets, name, x, y, runs, styles, width=None, align="left", opacity=None):
    """runs: [(string, style_key)], styles: {key: dict(font=, size=, lh=, ls=, color=, weight=)}"""
    used = []
    for _, sk in runs:
        if sk not in used:
            used.append(sk)
    style_els = []
    for sk in used:
        s = styles[sk]
        f = assets.fonts[s["font"]]
        kids = [fill(s["color"], name=f"{name}.{sk}.fill") if "gradient" not in s else s["gradient"]]
        if s.get("weight"):
            kids.append(El("TextStyleAxis", {"tag": WGHT, "axisValue": s["weight"]}))
        style_els.append(El("TextStylePaint", {"fontSize": s["size"], "lineHeight": s.get("lh"), "letterSpacing": s.get("ls"),
                                               "fontAssetId": f"@font.{s['font']}", "familyName": f.family,
                                               "styleName": "Regular"}, kids, name=f"{name}.{sk}"))
    run_els = [El("TextValueRun", {"styleId": f"@{name}.{sk}", "text": t}, name=f"{name}.run{i}") for i, (t, sk) in enumerate(runs)]
    attrs = {"x": x, "y": y, "opacity": opacity, "alignValue": align}
    if width:
        attrs.update({"width": width, "sizingValue": "autoHeight", "wrapValue": "wrap"})
    return El("Text", attrs, style_els + run_els, name=name)
