"""Convert simple SVG path data (Figma exports: absolute M/L/H/V/C/Z) into RML PointsPath vertices.

Returns plain dicts so the caller decides placement; coordinates can be mirrored/offset/scaled.
"""
import math
import re

from rml import El

TOKEN = re.compile(r"[MLHVCZmlhvcz]|-?\d*\.?\d+(?:e-?\d+)?")


def parse(d):
    """-> list of subpaths; each subpath = list of segments [('M',p) | ('L',p) | ('C',c1,c2,p)] + closed flag."""
    toks = TOKEN.findall(d)
    subpaths, cur, i, cmd, pos, start = [], None, 0, None, (0.0, 0.0), (0.0, 0.0)

    def num():
        nonlocal i
        v = float(toks[i])
        i += 1
        return v

    while i < len(toks):
        t = toks[i]
        if re.match(r"[A-Za-z]", t):
            cmd = t
            i += 1
            if cmd in "Zz":
                if cur is not None:
                    cur["closed"] = True
                    pos = start
                continue
        rel = cmd.islower()
        c = cmd.upper()
        if c == "M":
            p = (num(), num())
            if rel:
                p = (pos[0] + p[0], pos[1] + p[1])
            cur = {"segs": [("M", p)], "closed": False}
            subpaths.append(cur)
            pos = start = p
            cmd = "l" if rel else "L"
        elif c == "L":
            p = (num(), num())
            if rel:
                p = (pos[0] + p[0], pos[1] + p[1])
            cur["segs"].append(("L", p))
            pos = p
        elif c == "H":
            x = num()
            p = (pos[0] + x if rel else x, pos[1])
            cur["segs"].append(("L", p))
            pos = p
        elif c == "V":
            y = num()
            p = (pos[0], pos[1] + y if rel else y)
            cur["segs"].append(("L", p))
            pos = p
        elif c == "C":
            pts = [(num(), num()) for _ in range(3)]
            if rel:
                pts = [(pos[0] + x, pos[1] + y) for x, y in pts]
            cur["segs"].append(("C", pts[0], pts[1], pts[2]))
            pos = pts[2]
    return subpaths


def to_vertices(sub, tf=lambda p: p):
    """Vertices with in/out handles (absolute points, after transform tf)."""
    verts = []
    for seg in sub["segs"]:
        if seg[0] in ("M", "L"):
            verts.append({"p": tf(seg[1]), "in": None, "out": None})
        else:
            verts[-1]["out"] = tf(seg[1])
            verts.append({"p": tf(seg[3]), "in": tf(seg[2]), "out": None})
    if sub["closed"] and len(verts) > 1:
        a, b = verts[0], verts[-1]
        if math.dist(a["p"], b["p"]) < 1e-3:
            a["in"] = b["in"]
            verts.pop()
    return verts


def points_path(name, verts, origin=(0.0, 0.0), closed=True):
    """RML PointsPath with vertices relative to origin."""
    kids = []
    for i, v in enumerate(verts):
        x, y = v["p"][0] - origin[0], v["p"][1] - origin[1]
        if v["in"] is None and v["out"] is None:
            kids.append(El("StraightVertex", {"x": x, "y": y}))
            continue
        attrs = {"x": x, "y": y}
        for k, h in (("in", v["in"]), ("out", v["out"])):
            if h is not None:
                dx, dy = h[0] - v["p"][0], h[1] - v["p"][1]
                attrs[f"{k}Rotation"] = math.atan2(dy, dx)
                attrs[f"{k}Distance"] = math.hypot(dx, dy)
            else:
                attrs[f"{k}Rotation"], attrs[f"{k}Distance"] = 0.0, 0.0
        kids.append(El("CubicDetachedVertex", attrs))
    return El("PointsPath", {"isClosed": closed}, kids, name=name)
