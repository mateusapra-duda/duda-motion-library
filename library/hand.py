"""hand.py (v14): the cursor built the motion designer's way, the library's default cursor.

Mateus decided on 2026-11-23 that his cursor becomes the library's default (the proposal in brief.md "For the next
version", the precision research, pecas/pesquisa-precisao/3-ajustes-mao.md). It is the recipe of his approved cursors
(LEARNINGS section 3; pecas/yir-prompt/hand_cursor.py and its five copies, now in one place):

- ONE Follow Path per cursor, with few vertices (where it shows, each stop, the turn of a typing arc) and distance
  keys only where it stops or where one curve hands over to the next at the same speed.
- It shows IN PLACE (a 3 f fade, already moving), ~220 px below its first target, on the side towards the frame's
  centre, never crossing the frame's edge; it fades out in 3 f, 8 f after its last press, where it rests.
- Show -> first stop: one curve (0, 0, 0.2514, 1), >= 38 f (his retouch, build-your-audience v04/v05).
- Stop -> stop: one curve (0.6, 0, 0.25, 1), 0.85 s + 1 ms per px (his v07.10; LEARNINGS 3). A typing arc passes its
  turn with no key there.
- A press starts 5 f before the stop (7 f on a field); the next move sets off 2 f after the stop; the press is
  1 -> 0.85 in 3 f and back in 3 f, linear.
- A long wait doesn't park: it creeps (~12 px/s) towards the next target and hands over to the glide at the same
  speed. Much longer (> 3 s more than the glide needs): it vanishes and another cursor shows in place.
- The path runs from 0.1 % to 99.9 % (at the exact ends Follow Path can draw it at the other end for a frame) and the
  last key holds (a linear last key slides it back at the loop).
- The speed ceiling is a share of the frame (2.4 % of its width per frame: ~31 px/f at 1300 px; his peaks 18-26):
  a glide or an entry too fast for it gets longer.

The geometry here is the path; the schedule is the Actions' (piece.py), which decides each stop's time.
"""
import math

import kit
from kit import El

FPS = kit.FPS
ENTER = (0.0, 0.0, 0.2514, 1.0)        # show -> first stop, one curve (LEARNINGS 3)
ENTER_MIN = 38                         # frames (his entries: 38-42)
GLIDE = (0.6, 0.0, 0.25, 1.0)          # stop -> stop, one curve (v07.10 scene 3)
GLIDE_S, GLIDE_PER_PX = 0.85, 0.001    # a move from rest: 0.85 s + 1 ms per px (LEARNINGS 3)
GLIDE_MIN = 0.8                        # a glide may be squeezed to 0.8x its natural time to meet a set time
GLIDE_STRETCH = 1.35                   # ... or stretched to 1.35x; beyond, it creeps first
PRESS_LEAD, FIELD_LEAD = 5, 7          # the press starts this many frames before the stop (a field: 7)
LEAVE_AFTER = 2                        # the next move sets off this many frames after the stop
FADE = 3                               # frames to show / to vanish
VANISH_AFTER = 8                       # it starts to vanish this many frames after its last press
PRESS_SCALE, PRESS_IN, PRESS_OUT = 0.85, 3, 3
CREEP = 12.0                           # px/s while it waits (tokens: cursor.creep_px_per_s)
CREEP_CURVE = (0.3, 0.0, 0.7, 1.0)     # a short creep onto the spot it then presses (a hover's linger)
SHORT = 24                             # px: a leg this short is a creep, not a glide
LONG_WAIT = 3.0                        # s of wait beyond the glide: it vanishes and a new cursor shows for the next
CAP = 0.024                            # speed ceiling, a share of the frame's width per frame (31 px/f at 1300)
SHOW_DIST = 220                        # it shows ~200-250 px below its first target...
SHOW_SIDE = 0.45                       # ... and this share of it towards the frame's centre
BOTTOM_ROOM = 65                       # its tip stays >= 65 px above the frame's bottom edge
EDGE_ROOM = 40                         # ... and >= 40 px inside the other edges where it shows
BOW = 0.08                             # a light arc (8 % of the chord), rising towards the target
ARC_BOW = 0.22                         # the typing arc's bulge (the pattern's turn), a share of the chord
START, END = 0.001, 0.999              # the ride's ends on the path (LEARNINGS 3)
RELEASE = 8                            # frames after the press: a popup / menu the click opens starts here
RESULT = 5                             # ... a fold or another result of the click


def ease_peak(e, n=400):
    """Peak slope of a normalised cubic-bezier timing curve (progress per unit time)."""
    from choreo import progress
    best, prev = 0.0, 0.0
    for j in range(1, n + 1):
        v = progress(e, j / n)
        best = max(best, (v - prev) * n)
        prev = v
    return best


PEAK = {"enter": ease_peak(ENTER), "glide": ease_peak(GLIDE)}


def cap_px(w):
    return CAP * w


def entry_frames(d, w):
    """Frames from showing to the first stop over d px: >= 38, and slow enough for the ceiling."""
    return max(ENTER_MIN, math.ceil(d * PEAK["enter"] / (cap_px(w) * 0.92)))


def glide_frames(d, w):
    """Frames of a glide over d px: 0.85 s + 1 ms per px, and slow enough for the ceiling."""
    natural = round((GLIDE_S + GLIDE_PER_PX * d) * FPS)
    return max(natural, math.ceil(d * PEAK["glide"] / (cap_px(w) * 0.92)))


def show_point(target, w, h):
    """Where a cursor shows for its first target: ~220 px below it, towards the frame's centre, inside the frame
    (its tip >= 65 px above the bottom). A target near the bottom: it shows beside it instead."""
    tx, ty = target
    side = 1 if tx < w / 2 else -1
    room = h - BOTTOM_ROOM - ty
    if room >= 120:
        dy = min(SHOW_DIST, room)
        dx = side * SHOW_DIST * SHOW_SIDE
    else:   # no room below: beside it, a little below if it can
        dy = max(0.0, min(60.0, room))
        dx = side * SHOW_DIST
    x = min(max(tx + dx, EDGE_ROOM), w - EDGE_ROOM)
    y = min(max(ty + dy, EDGE_ROOM), h - BOTTOM_ROOM)
    return (round(x, 2), round(y, 2))


def _unit(v):
    n = math.hypot(*v)
    return (v[0] / n, v[1] / n) if n > 1e-9 else (0.0, 0.0)


def bow_normal(a, b, w):
    """The side a leg bows to: upwards (it 'already rises towards the target'); a vertical leg bows towards the
    frame's centre."""
    d = (b[0] - a[0], b[1] - a[1])
    n1, n2 = (-d[1], d[0]), (d[1], -d[0])
    n = n1 if n1[1] < n2[1] else n2
    if abs(_unit(n)[1]) < 0.2:      # (nearly) vertical: towards the centre
        cx = w / 2 - (a[0] + b[0]) / 2
        n = n1 if n1[0] * cx >= 0 else n2
    return _unit(n)


def arc_turn(p, q, side=None, w=None):
    """The turn of the typing arc between the field p and the next target q: off the chord's middle by ARC_BOW of
    its length (a short chord: >= 60 px), to `side` ("down", "up", "right", "left"; default: down, or right when q
    is below p: the empty side of a form)."""
    d = (q[0] - p[0], q[1] - p[1])
    L = max(math.hypot(*d), 1.0)
    off = max(ARC_BOW * L, 60.0)
    n1, n2 = _unit((-d[1], d[0])), _unit((d[1], -d[0]))
    if side is None:
        side = "right" if abs(d[1]) > abs(d[0]) else "down"
    pick = {"down": lambda n: n[1], "up": lambda n: -n[1], "right": lambda n: n[0], "left": lambda n: -n[0]}[side]
    n = n1 if pick(n1) >= pick(n2) else n2
    return (round((p[0] + q[0]) / 2 + n[0] * off, 2), round((p[1] + q[1]) / 2 + n[1] * off, 2))


def leg_curve(a, b, w, flip=False):
    """The four points of a leg from a to b: a light bow (BOW of the chord) upwards, or the other way."""
    d = (b[0] - a[0], b[1] - a[1])
    nrm = bow_normal(a, b, w)
    if flip:
        nrm = (-nrm[0], -nrm[1])
    h = BOW * math.hypot(*d) / 0.75          # a cubic whose two handles are off by h bows 0.75 h
    return (a, (a[0] + d[0] / 3 + nrm[0] * h, a[1] + d[1] / 3 + nrm[1] * h),
            (a[0] + 2 * d[0] / 3 + nrm[0] * h, a[1] + 2 * d[1] / 3 + nrm[1] * h), b)


def crossings(seg, boxes, n=48):
    """How many of `boxes` (x, y, w, h) the leg `seg` passes over (its ends' own boxes excluded)."""
    a, b = seg[0], seg[3]

    def has(box, q):
        return box[0] <= q[0] <= box[0] + box[2] and box[1] <= q[1] <= box[1] + box[3]
    hits = 0
    for box in boxes:
        if has(box, a) or has(box, b):
            continue
        if any(has(box, _bez(seg, j / n)) for j in range(1, n)):
            hits += 1
    return hits


def _bez(s, u):
    (x0, y0), (x1, y1), (x2, y2), (x3, y3) = s
    m = 1 - u
    return (m ** 3 * x0 + 3 * m * m * u * x1 + 3 * m * u * u * x2 + u ** 3 * x3,
            m ** 3 * y0 + 3 * m * m * u * y1 + 3 * m * u * u * y2 + u ** 3 * y3)


class Path:
    """An open cubic path through `pts` (each (x, y, kind): "stop", "turn" (a smooth turn, no key) or "end"), each
    leg bowing lightly upwards; the arc-length table for positions and distances."""

    def __init__(self, pts, w, n=160, flip=()):
        """flip: indices of the legs that bow the other way (one that would pass over another control)."""
        self.pts = pts
        P = [(x, y) for x, y, _ in pts]
        k = len(P)
        hin, hout = [None] * k, [None] * k
        kinds = [kd for _, _, kd in pts]
        for i in range(k - 1):
            a, b = P[i], P[i + 1]
            d = (b[0] - a[0], b[1] - a[1])
            L = math.hypot(*d)
            if "turn" in (kinds[i], kinds[i + 1]):     # into / out of a turn: straight thirds (the turn sets its own)
                hout[i] = (a[0] + d[0] / 3, a[1] + d[1] / 3)
                hin[i + 1] = (a[0] + 2 * d[0] / 3, a[1] + 2 * d[1] / 3)
                continue
            _, hout[i], hin[i + 1], _ = leg_curve(a, b, w, i in flip)
        for i in range(1, k - 1):       # a turn: smooth, its tangent along the arc's chord (no key, no stop there)
            if kinds[i] == "turn":
                tan = _unit((P[i + 1][0] - P[i - 1][0], P[i + 1][1] - P[i - 1][1]))
                l0, l1 = math.dist(P[i - 1], P[i]) / 3, math.dist(P[i], P[i + 1]) / 3
                hin[i] = (P[i][0] - tan[0] * l0, P[i][1] - tan[1] * l0)
                hout[i] = (P[i][0] + tan[0] * l1, P[i][1] + tan[1] * l1)
        hin[0], hout[-1] = P[0], P[-1]
        self._build(P, hin, hout, n)

    def _build(self, P, hin, hout, n):
        k = len(P)
        self.hin, self.hout, self.P = hin, hout, P
        self.segs = [(P[i], hout[i], hin[i + 1], P[i + 1]) for i in range(k - 1)]
        self.table, self.at_vertex = [], [0.0]
        for s in self.segs:
            for j in range(0 if not self.table else 1, n + 1):
                pt = _bez(s, j / n)
                self.table.append((self.table[-1][0] + math.dist(self.table[-1][1], pt) if self.table else 0.0, pt))
            self.at_vertex.append(self.table[-1][0])
        self.length = max(self.table[-1][0], 1e-6)
        self.s = [min(END, max(START, v / self.length)) for v in self.at_vertex]

    def leg_px(self, i):
        """Length of the leg from vertex i to vertex i + 1."""
        return self.at_vertex[i + 1] - self.at_vertex[i]

    def pos(self, s):
        want = max(0.0, min(1.0, s)) * self.length
        lo, hi = 0, len(self.table) - 1
        while hi - lo > 1:
            mid = (lo + hi) // 2
            lo, hi = (mid, hi) if self.table[mid][0] < want else (lo, mid)
        (l0, p0), (l1, p1) = self.table[lo], self.table[hi]
        u = 0 if l1 == l0 else (want - l0) / (l1 - l0)
        return (p0[0] + (p1[0] - p0[0]) * u, p0[1] + (p1[1] - p0[1]) * u)

    def vertices(self):
        """The path's vertices for RML (CubicDetachedVertex: in/out handles as angle + distance)."""
        out = []
        for i, (x, y) in enumerate(self.P):
            a = {"x": round(x, 3), "y": round(y, 3)}
            for side, hnd in (("in", self.hin[i]), ("out", self.hout[i])):
                dx, dy = hnd[0] - x, hnd[1] - y
                if math.hypot(dx, dy) > 1e-6:
                    a[f"{side}Rotation"] = round(math.atan2(dy, dx), 6)
                    a[f"{side}Distance"] = round(math.hypot(dx, dy), 3)
                else:
                    a[f"{side}Rotation"], a[f"{side}Distance"] = 0.0, 0.0
            out.append(("CubicDetachedVertex", a))
        return out


class RmlPath(Path):
    """A cursor's path read back from its RML vertices: a cursor a piece (or drag.py) built itself, for the checks."""

    def __init__(self, shape, n=160):
        pp = next(c for c in shape.children if isinstance(c, El) and c.tag == "PointsPath")
        P, hin, hout = [], [], []
        for v in (c for c in pp.children if isinstance(c, El) and c.tag.endswith("Vertex")):
            a = {k: float(x) for k, x in v.attrs.items() if isinstance(x, (int, float))}
            x, y = a.get("x", 0.0), a.get("y", 0.0)
            if v.tag == "CubicDetachedVertex":
                ri, di, ro, do = a.get("inRotation", 0), a.get("inDistance", 0), a.get("outRotation", 0), \
                    a.get("outDistance", 0)
            elif v.tag in ("CubicAsymmetricVertex", "CubicMirroredVertex"):
                r = a.get("rotation", 0)
                di = a.get("inDistance", a.get("distance", 0))
                do = a.get("outDistance", a.get("distance", 0))
                ri, ro = r + math.pi, r
            else:
                ri = di = ro = do = 0.0
            P.append((x, y))
            hin.append((x + math.cos(ri) * di, y + math.sin(ri) * di))
            hout.append((x + math.cos(ro) * do, y + math.sin(ro) * do))
        self.pts = [(x, y, "stop") for x, y in P]
        self._build(P, hin, hout, n)


class Cursor:
    """One cursor: its path and its keys (distance, opacity, press scale), in frames."""

    def __init__(self, name, path):
        self.name, self.path = name, path
        self.dist = [{"f": 0, "v": START, "ease": "hold"}]
        self.opacity = [{"f": 0, "v": 0.0, "ease": "hold"}]
        self.scale = []
        self.presses, self.stops = [], []
        self.f_show = self.f_gone = None

    # ------------------------------------------------------------ keys
    def _key(self, f, v):
        self.dist = [k for k in self.dist if k["f"] != f] + [{"f": f, "v": v, "ease": "hold"}]
        self.dist.sort(key=lambda k: k["f"])
        return next(k for k in self.dist if k["f"] == f)

    def show(self, f):
        self.f_show = f
        self.opacity += [{"f": f, "v": 0.0, "ease": "linear"}, {"f": f + FADE, "v": 1.0, "ease": "hold"}]
        if f == 0:
            self.opacity = [{"f": 0, "v": 0.0, "ease": "linear"}, {"f": FADE, "v": 1.0, "ease": "hold"}]

    def vanish(self, f):
        self.f_gone = f + FADE
        self.opacity += [{"f": f, "v": 1.0, "ease": "linear"}, {"f": f + FADE, "v": 0.0, "ease": "hold"}]

    def press(self, f):
        self.presses.append(f)
        self.scale += [{"f": f, "v": 1.0, "ease": "linear"}, {"f": f + PRESS_IN, "v": PRESS_SCALE, "ease": "linear"},
                       {"f": f + PRESS_IN + PRESS_OUT, "v": 1.0, "ease": "hold"}]

    @staticmethod
    def _curve(a0, s1, curve, v0=None, v1=None, n=None):
        """a0's ease: a cubic in value space from a0 to s1 on `curve`; v0 / v1 (distance per frame): the start / end
        slope forced to that speed (a hand-over at the same speed)."""
        x1, y1, x2, y2 = curve
        d = s1 - a0["v"]
        if v0 is not None and d:
            y1 = v0 * x1 * n / d
        if v1 is not None and d:
            y2 = 1 - v1 * (1 - x2) * n / d
        a0["ease"] = ("value", x1, a0["v"] + y1 * d, x2, a0["v"] + y2 * d)

    def enter(self, f0, f1, s0, s1):
        a0 = self._key(f0, s0)
        self._key(f1, s1)
        self._curve(a0, s1, ENTER)

    def glide(self, f0, f1, s0, s1, v0=None, curve=GLIDE):
        a0 = self._key(f0, s0)
        self._key(f1, s1)
        self._curve(a0, s1, curve, v0=v0, n=f1 - f0)

    def creep(self, f0, f1, s0, s1):
        """From rest, easing into a creep that ends at its mean x 1.25 (the glide takes over at that speed).
        Returns the end speed (distance per frame)."""
        a0 = self._key(f0, s0)
        self._key(f1, s1)
        v1 = 1.25 * (s1 - s0) / max(f1 - f0, 1)
        self._curve(a0, s1, (0.35, 0.0, 0.7, 0.7), v1=v1, n=f1 - f0)
        return v1

    def hold_until(self, f0, f1, s):
        """Still between two keys (the 2 f after a stop): hold keys."""
        self._key(f0, s)

    # ------------------------------------------------------------ into the scene
    def elements(self, p):
        """The cursor's node (the library's Cursor artboard, nested, riding the path) and its path shape."""
        n = self.name
        follow = El("FollowPathConstraint", {"targetId": f"@{n}.path", "orient": False}, name=f"{n}.follow")
        nest = El("NestedArtboard", {"artboardId": "@art.cursor", "dataBindPathIds": (
            f"vm.{p.key}", f"vm.{p.key}.cursor")}, [El("NestedStateMachine", {"animationId": "@sm.cursor"},
                                                       name=f"{n}.machine")], name=f"{n}.art")
        node = El("Node", {"x": 0, "y": 0, "opacity": 0, "scaleX": p.cursor_scale, "scaleY": p.cursor_scale},
                  [nest, follow], name=n)
        shape = El("Shape", {"x": 0, "y": 0}, [El("PointsPath", {"isClosed": False}, [
            El(t, dict(a)) for t, a in self.path.vertices()], name=f"{n}.pathpts")], name=f"{n}.path")
        return node, shape

    def tracks(self, cursor_scale):
        sc = cursor_scale
        scale = [{"f": 0, "v": sc, "ease": "hold"}] + [dict(k, v=k["v"] * sc) for k in self.scale]
        op = sorted(self.opacity, key=lambda k: k["f"])
        return [(self.name, "opacity", op), (self.name, "scaleX", scale), (self.name, "scaleY", scale),
                (f"{self.name}.follow", "distance", self.dist)]

    # ------------------------------------------------------------ where it is (hovers, lints)
    def _value(self, keys, f):
        from choreo import progress
        prev = keys[0]
        for k in keys:
            if k["f"] > f:
                if prev["ease"] == "hold" or prev["f"] == f:
                    return prev["v"]
                u = (f - prev["f"]) / (k["f"] - prev["f"])
                return prev["v"] + (k["v"] - prev["v"]) * progress(prev["ease"], u, prev["v"], k["v"])
            prev = k
        return prev["v"]

    def s_at(self, f):
        return self._value(self.dist, f)

    def tip(self, f):
        return self.path.pos(self.s_at(f))

    def alpha(self, f):
        return self._value(sorted(self.opacity, key=lambda k: k["f"]), f)
