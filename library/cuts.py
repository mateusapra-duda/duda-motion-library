"""cuts.py (v14): screen changes, the camera and the scroll, the way the motion designer made them by hand.

    a.cut(src, dst, kind)   one screen gives way to another: "slide" (a match cut by position), "zoom" (into what was
                            clicked, through white), "white" (in place: a panel that stays) or "tabs" (a hero's tabs)
    a.camera_close(...)     a hard cut to a close shot that follows the cursor up to the interface's edge
    a.camera_open(...)      the slow zoom out in the close shot, then the strong 80/80 zoom out
    a.jump_cut(...)         a cut that isn't totally hard: the picture slides off ~23 px and the next comes in on with
                            it (the loop's seam by default; inside the piece with t=, or into a close shot)
    a.scroll(box, dy)       one scroll on his curve, never coming back
    p.stack(name, screens)  the screens a.cut swaps, in one place

The numbers are LEARNINGS sections 8-10 and the pieces he approved (each constant says where).

How it fits in the piece:
- the screens' keys (x / y / scale / opacity) and the cascade go on the piece's one timeline when the action is called;
- what depends on the finished timeline is added when the build finishes (cuts wraps a._finish once): the edges
  (vector bands sampled from a render of the screen at rest, so what shows past the frame continues the screen: rule
  8), the white, the camera's rig (it follows the cursor's keys) and the jump cut's node;
- the cursor at a cut walks across it or vanishes in place; "auto" decides by what the cursor does next (rule 8),
  and a cursor that comes for the new screen after a vanish starts its way in after the cut;
- the kit's speed lint (choreo) skips the cut's frames for the elements the cut moves, as it does for its own match
  cuts, and reports each cut's last step against the match cut's cap.
"""
import copy
import hashlib
import math
import os
import re
import subprocess

import kit
from kit import El
import choreo
from choreo import frame, progress
from common import FPS, RIVE, STEP, secs, Item, _el, _color

# ------------------------------------------------------------------------------------------------ the numbers
REF_W = 1340.0                        # the hero's width (the Vibe page's MAIN): the px below are its px; a piece of
#                                       another width scales them (a 432 px card slides 69 px, not 215)
EXIT = (1.0, 0.0, 1.0, 1.0)           # motion-spec match_cut.exit_ease: accelerating into the cut
SETTLE = (0.0, 0.0, 0.0, 1.0)         # motion-spec ease.settle: the entry, fast out of the cut
KINDS = {
    # LEARNINGS 8; marketing-automation v15.6 / v15.8 (ma-simplified-flow CUT_WAIT 7/60, OUT_PX 215, IN_PX 60,
    # CUT_ENTRY 0.9 s): 40 px looked like a jump, 20 px was "really harsh" (the boss)
    "slide": dict(wait=7, out_px=215.0, out_frames=23, out_ease=EXIT, in_px=60.0, in_frames=54, in_ease=SETTLE,
                  edges=True, cascade=True),
    # LEARNINGS 8: 120 % around the click (Mateus, 2026-11-23; 135 % in v15.7), the rest as ma-simplified-flow
    # (CUT2_WAIT 14, CUT2_FRAMES 23, FLASH, CUT2_IN 0.95, CUT2_SETTLE 54)
    "zoom": dict(wait=14, scale=1.20, out_frames=23, out_ease=EXIT, in_scale=0.95, in_frames=54, in_ease=SETTLE,
                 edges=True, cascade=True),
    # LEARNINGS 8; marketing-automation v05 (DIP_OUT, DIP_HOLD, DIP_IN = 0.15, 0.1, 0.25 s): 9 f, 6 f, 15 f
    "white": dict(wait=7, leave=9, hold=6, come=15, edges=False, cascade=True),
    # LEARNINGS 8; hero-tabs v03 (EXIT, D_EXIT = 20, 26; ENTRY, D_ENTRY = 26, 34; FADE = 10: a veil in the leaving
    # page's body colour closes over the exit's last 10 f, one in the new page's opens over the entry's first 10 f;
    # the page moves against the pill: a tab to the right sends it left)
    "tabs": dict(wait=0, out_px=26.0, out_frames=20, out_ease=EXIT, in_px=34.0, in_frames=26, in_ease=SETTLE,
                 veil=10, edges=True, cascade=False),
}
ZOOM_WHITE = (10, 1, 3, 18)           # the zoom's white, frames from the cut: in from -10, full -1..+3, gone at +18
#                                       (LEARNINGS 8: in over 9 f, full from the cut -1 to +3, leaves over 15 f)
EDGE_INSIDE, EDGE_BEFORE, EDGE_MARGIN = 5, 2, 8     # LEARNINGS 8: copy from 5 px inside, start 2 px before the edge
#                                       (the margin: past the farthest the edge travels, never short by a frame)
EDGE_TOL, EDGE_BANDS = 4, 48          # a band per run of the same colour (0-255 per channel); at most this many
CASCADE_DY, CASCADE_DUR, CASCADE_FADE = 8.0, 0.6, 9   # LEARNINGS 10: rise 8 px, 0.6 s settle, 67 ms apart (STEP
#                                       "list"); design-with-context v04 (his file): each row fades in over 9 f
WALK_MAX = 2.0                        # s: the cursor walks across a cut when its next move comes within this of the
#   cut (he kept it walking at 1.37 s, marketing-automation v15.12 cut 1; 1.38 s, design-with-context v04's zoom;
#   1.55 s, manage-hero2), and vanished when nothing came for 3.6 s (marketing-automation v15.12 cut 2) or ever
#   (build-your-audience v03)
VANISH_AFTER = (5, 8)                 # frames after the press its 3 f fade starts: 8 (his: marketing-automation
#                                       v15.12, build-your-audience v03, the exit 3 f after it is gone), never before
#                                       5 (the press's release); a slide leaves at 7, so it fades from 5
VANISH_FRAMES = 3
NEW_AFTER = 6                         # frames: a cursor that comes for the new screen starts its way in this long
#                                       after the cut (the piece's own slack pulls an entry up to 0.1 s earlier; it
#                                       must never cross the old screen on its way out)
CAMERA = dict(scale=2.5, lead=31, slow=2.4, slow_ease=(0.65, 0.0, 0.8, 0.7), slow_after=1)
#   LEARNINGS 9; marketing-automation v15.12 via ma-simplified-flow v03 (camera: zoom 2.5, cut F - 31, follow_until
#   the arrival, slow 2.4 from the arrival + 1 on (0.65, 0, 0.8, 0.7))
OPEN = dict(lead=25, frames=102, ease=(0.8, 0.0451, 0.2, 1.0), slow_over=40)
#   the 80/80 zoom out with his handle (0.0451), S - 25 -> S + 77 around the send's press S (ma-novo v18.9, his edit);
#   the slow zoom ends 40 f into it (ma-simplified-flow: out S + 25, cut_out S - 15), so the two read as one
JUMP = dict(out_px=23.442, out_frames=27, out_ease=(1.0, 0.0, 1.0, 0.9554), in_px=30.0, in_frames=34, in_ease=SETTLE)
#   marketing-automation v15.12 (his): slides 23.442 px in 27 f; the entry 30 px (his edit in ma-novo v18.5; 60 in
#   v15.12), settling in 34 f, on with the slide's direction (ma-novo v18.5-v18.7: "the goal is not even noticing")
JUMP_8080 = dict(curve=(0.8, 0.0, 0.2, 1.0), frames=84)   # ma-novo v18.9: "use an 80-80 and cut on its peak": the
#                                       first half of an 84 f 80/80, cut on frame 42
SCROLL = dict(ease=(0.857, 0.0, 0.242, 1.0), base=0.9, per_px=0.0015, read=1.0, cursor=6)
#   LEARNINGS 10 (marketing-automation v15.12, his file: 784 px in 124 f, peak ~23 px/f); the duration ~0.9 s + 1.5 ms
#   per px (his five scrolls: 125 px in 68 f ... 784 px in 124 f); the top readable ~1 s first; the cursor shows up
#   6 f before the scroll ends
FIT_TOL, FIT_KEYS = 0.25, 12          # LEARNINGS 9: the camera's track in ~12 cubic keys, error < 1 px (on screen,
#                                       x2.5: 0.25 px on the board)


# ------------------------------------------------------------------------------------------------ small helpers
def _xyxy(b):
    x, y, w, h = b
    return (x, y, x + w, y + h)


def _inter(a, b):
    r = (max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3]))
    return r if r[2] > r[0] + 1e-6 and r[3] > r[1] + 1e-6 else None


def _union(a, b):
    return (min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3]))


def _clamp(v, lo, hi):
    return lo if v < lo else hi if v > hi else v


def _steps(ease, n):
    """The eased progress on each of n frames (n + 1 values, 0 .. 1)."""
    return [progress(ease, i / n) for i in range(n + 1)]


def _peak(ease, n=400):
    """The fastest step of a normalised ease, as a multiple of its mean."""
    best, prev = 0.0, 0.0
    for j in range(1, n + 1):
        v = progress(ease, j / n)
        best, prev = max(best, (v - prev) * n), v
    return best


def _split(e, k):
    """The first part of cubic ease `e` up to x = k, as a normalised cubic (de Casteljau), so the cut part keeps the
    curve's shape (drag.py's, for the 80/80 cut on its peak)."""
    x1, y1, x2, y2 = e
    lo, hi = 0.0, 1.0
    for _ in range(50):
        s = (lo + hi) / 2
        bx = 3 * (1 - s) ** 2 * s * x1 + 3 * (1 - s) * s * s * x2 + s ** 3
        lo, hi = (s, hi) if bx < k else (lo, s)
    s = (lo + hi) / 2
    lerp = lambda a, b: (a[0] + (b[0] - a[0]) * s, a[1] + (b[1] - a[1]) * s)   # noqa: E731
    a1, b1, c1 = lerp((0.0, 0.0), (x1, y1)), lerp((x1, y1), (x2, y2)), lerp((x2, y2), (1.0, 1.0))
    a2, b2 = lerp(a1, b1), lerp(b1, c1)
    sx, sy = lerp(a2, b2)
    return (a1[0] / sx, a1[1] / sy, a2[0] / sx, a2[1] / sy)


def _bands(img, line, a0, a1, along):
    """The colours along one line of a render (a column when along == "y", a row when "x"), from a0 to a1, as bands:
    [(start, end, (r, g, b, a))] relative to a0. One band per run of the same colour; the thin runs an edge's
    anti-aliasing leaves go into the closer neighbour, and at most EDGE_BANDS stay."""
    W, H = img.size
    px = []
    for a in range(int(math.floor(a0)), int(math.ceil(a1))):
        x, y = (line, a) if along == "y" else (a, line)
        px.append(img.getpixel((min(max(int(x), 0), W - 1), min(max(int(y), 0), H - 1))))
    if not px:
        return []

    def dist(c1, c2):
        return max(abs(c1[j] - c2[j]) for j in range(4))
    runs = []
    for i, col in enumerate(px):
        if runs and dist(col, runs[-1][2]) <= EDGE_TOL:
            runs[-1][1] = i + 1
        else:
            runs.append([i, i + 1, col])
    while len(runs) > 1 and (min(r[1] - r[0] for r in runs) < 2 or len(runs) > EDGE_BANDS):
        i = min(range(len(runs)), key=lambda k: runs[k][1] - runs[k][0])
        j = min((k for k in (i - 1, i + 1) if 0 <= k < len(runs)), key=lambda k: dist(runs[i][2], runs[k][2]))
        lo, hi = min(i, j), max(i, j)
        runs[lo:hi + 1] = [[runs[lo][0], runs[hi][1], runs[j][2]]]
    off = math.floor(a0) - a0
    return [(r[0] + off, r[1] + off, r[2]) for r in runs]


def _fit(vals, fa, fb, tol=FIT_TOL, most=FIT_KEYS):
    """Cubic keys for a per-frame curve vals[f] (fa..fb): Hermite segments (Rive's CubicValueInterpolator with its
    time handles at 1/3 and 2/3 is exactly one), a key added where the error is worst until it is under `tol` or
    there are `most` keys. Kinks (the frame stopping at the interface's edge) get a key first, with their own slope
    on each side. Returns ([(f, v, slope in, slope out)], max error)."""
    if fb <= fa:
        return [(fa, vals[fa], 0.0, 0.0)], 0.0

    def d(f):
        return vals[f + 1] - vals[f] if f + 1 <= fb else (vals[f] - vals[f - 1] if f - 1 >= fa else 0.0)
    kinks = [f for f in range(fa + 1, fb) if abs(d(f) - d(f - 1)) > 1.0]
    keys = sorted({fa, fb} | set(kinks[:most - 2]))

    def slopes(f):
        back = vals[f] - vals[f - 1] if f - 1 >= fa else None
        fwd = vals[f + 1] - vals[f] if f + 1 <= fb else None
        if f in kinks or back is None or fwd is None:
            back = fwd if back is None else back
            fwd = back if fwd is None else fwd
            return back or 0.0, fwd or 0.0
        return (back + fwd) / 2, (back + fwd) / 2

    def herm(a, b, f):
        T = b - a
        s = (f - a) / T
        ma, mb = slopes(a)[1], slopes(b)[0]
        return ((2 * s ** 3 - 3 * s * s + 1) * vals[a] + (s ** 3 - 2 * s * s + s) * T * ma
                + (-2 * s ** 3 + 3 * s * s) * vals[b] + (s ** 3 - s * s) * T * mb)
    while True:
        worst, at = 0.0, None
        for a, b in zip(keys, keys[1:]):
            for f in range(a + 1, b):
                e = abs(herm(a, b, f) - vals[f])
                if e > worst:
                    worst, at = e, f
        if worst <= tol or at is None or len(keys) >= most:
            return [(f, vals[f]) + slopes(f) for f in keys], worst
        keys = sorted(keys + [at])


def _keys_of(fitted):
    """Choreo keys for _fit's keys: value handles from the slopes (a flat segment: linear, Rive's value handles need a
    span)."""
    out = []
    for (fa, va, _, ma), (fb, vb, mb, _) in zip(fitted, fitted[1:]):
        T = fb - fa
        if abs(vb - va) < 0.01:
            ease = "linear"
        else:
            ease = ("value", 1 / 3, va + ma * T / 3, 2 / 3, vb - mb * T / 3)
        out.append({"f": fa, "v": va, "ease": ease})
    out.append({"f": fitted[-1][0], "v": fitted[-1][1], "ease": "hold"})
    return out


# ------------------------------------------------------------------------------------------------ placing
class CutPatterns:
    """Placement for cuts."""

    def stack(self, name, screens, w=None, h=None, clip=True):
        """Screens that take turns in one place, for a.cut: a p.free with each at 0,0 (w x h, default the frame). The
        first one is on screen at the start; the others stay hidden until a cut brings them in. Cuts need their
        screens in a p.free (here or your own), so the edges and the white have a box to go in. Give them in the
        tabs' order: a "tabs" cut moves against the pill (to a later screen, the page goes left)."""
        w, h = self.w if w is None else w, self.h if h is None else h
        self.__dict__.setdefault("_cut_stacks", []).append([_el(s).name for s in screens])
        for s in screens[1:]:
            _el(s).attrs["opacity"] = 0.0
        return self.free(name, [(s, 0, 0) for s in reversed(screens)], w, h, clip=clip)


# ------------------------------------------------------------------------------------------------ the actions
class CutActions:
    """a.cut, a.camera_close / a.camera_open / a.jump_cut, a.scroll (see the module's docstring)."""

    # -------------------------------------------------------------- state and hooks
    def _cuts(self):
        st = self.__dict__.get("_cut_st")
        if st is None:
            st = self._cut_st = {"cuts": [], "pending": None, "camera": None, "jumps": [], "rig": set(), "n": 0}
            self._cut_install(st)
        return st

    def _cut_install(self, st):
        """Once per piece: the build's end adds what needs the finished timeline; the lint skips the cuts' frames;
        the cursor's next move decides "auto" (it wraps the piece's own _go, cursor_out and cursor_in)."""
        finish, lint = self._finish, self.c.lint

        def _finish(*args, **kw):
            out = finish(*args, **kw)
            self._cuts_finish()
            return out
        self._finish = _finish
        self.c.lint = lambda: self._cuts_lint(*lint())
        go, out, cin = getattr(self, "_go", None), self.cursor_out, self.cursor_in
        st["cursor_out"] = out
        st["hooked"] = go is not None

        def _undecided():
            pend = st["pending"]
            return (pend if pend is not None and pend.get("verdict") is None and self.visit is pend["visit"]
                    and len(self.visit["points"]) == pend["n"] else None)
        if go is not None:
            def _go(at, t, click, *rest):
                pend = _undecided()
                if pend is None:
                    self._cut_new_visit(at)
                    return go(at, t, click, *rest)
                vis, n = self.visit, len(self.visits)
                saved = (dict(vis), list(vis["points"]))
                t2 = go(at, t, click, *rest)
                if self.visit is vis and t2 - pend["t_cut"] <= WALK_MAX + 1e-6:
                    pend["seen"] = ("walks", t2 - pend["t_cut"], click)
                    return t2
                vis.update(saved[0])       # undo, vanish at the cut, and a new cursor comes for this
                vis["points"][:] = saved[1]
                del self.visits[n:]
                self.visit = vis
                pend["seen"] = ("vanishes", t2 - pend["t_cut"], click)
                self._cut_vanish(pend)
                self._cut_new_visit(at)
                return go(at, t, click, *rest)
            self._go = _go

        def cursor_out(*args, **kw):
            pend = _undecided()
            if pend is not None and not args and kw.get("t") is None and kw.get("vanish") is None:
                pend["seen"] = ("vanishes", None, False)
                return self._cut_vanish(pend)
            return out(*args, **kw)
        self.cursor_out = cursor_out

        def cursor_in(*args, **kw):
            pend = _undecided()
            if pend is not None:
                t_in = kw.get("t", args[1] if len(args) > 1 else None)
                pend["seen"] = ("vanishes", None if t_in is None else t_in - pend["t_cut"], False, "a new cursor")
                self._cut_vanish(pend)
            return cin(*args, **kw)
        self.cursor_in = cursor_in

    def _cut_vanish(self, pend):
        """The cursor of a cut fades in place (3 f) before the exit starts (piece.py's cursor_out(vanish=s))."""
        if self.visit is pend["visit"]:
            self._cut_st["cursor_out"](vanish=pend["t_fade"])
            self._cut_st["new_after"] = pend["t_cut"] + NEW_AFTER / FPS
        return self.now

    def _cut_new_visit(self, at):
        """The next cursor after a vanish starts its way in after the cut (NEW_AFTER), or later if the piece waits.
        It stays set (the piece's dry runs in _aim open and drop visits); once now is past it, it changes nothing."""
        st = self._cut_st
        if self.visit is None and st.get("new_after") is not None and hasattr(self, "_open_visit"):
            # the piece's cursor: in place by default (v14), from the nearest edge on the old one (cursor_in(side))
            side = self._nearest_side(at) if getattr(self, "edge", None) else None
            self._open_visit(side, max(st["new_after"], self.now))

    # -------------------------------------------------------------- where things are
    def _cut_item(self, el):
        return next((it for it in self.p.items.values() if it.wrap is el), None)

    def _cut_rect(self, el, t):
        """(x0, y0, x1, y1) of a box on the board: a placed item, the page, or a p.free slot (it hugs its item)."""
        p = self.p
        if el is p.root:
            return (0.0, 0.0, float(p.w), float(p.h))
        it = self._cut_item(el)
        if it is not None:
            return _xyxy(p.bounds(it, t))
        kids = [k for k in el.children if isinstance(k, El) and k.tag != "LayoutComponentStyle"]
        if len(kids) == 1 and self._cut_item(kids[0]) is not None:
            return _xyxy(p.bounds(self._cut_item(kids[0]), t))
        return None

    def _cut_vis(self, el, t):
        """Where `el` shows at rest: (its rect inside its clipping boxes and the frame, the clip region alone)."""
        p, c = self.p, self.c
        it = self._cut_item(el)
        assert it is not None, f"cut: {el.name} is not a placed item (cut what p.free / p.wrap / p.column... return)"
        clip = (0.0, 0.0, float(p.w), float(p.h))
        cur = c.parent.get(id(el))
        while cur is not None and cur is not p.board:
            if cur.tag == "LayoutComponent" and cur.attrs.get("clip"):
                r = self._cut_rect(cur, t)
                if r is not None:
                    clip = _inter(clip, r) or clip
            cur = c.parent.get(id(cur))
        return _inter(_xyxy(p.bounds(it, t)), clip), clip

    def _cut_origin(self, el, t):
        """The board point `el` scales about (its ComponentOrigin, else its top-left) and its own scale."""
        x0, y0, x1, y1 = _xyxy(self.p.bounds(self._cut_item(el), t))
        o = next((k for k in el.children if isinstance(k, El) and k.tag == "ComponentOrigin"), None)
        ox, oy = (float(o.attrs.get("originX", 0)), float(o.attrs.get("originY", 0))) if o is not None else (0, 0)
        return (x0 + ox * (x1 - x0), y0 + oy * (y1 - y0)), float(el.attrs.get("scaleX") or 1.0)

    def _cut_pscale(self, el):
        """The scale its parents draw it at (offsets are in the parent's units)."""
        return self._scale_of(el.name) / float(el.attrs.get("scaleY") or 1.0)

    def _cut_lca(self, a, b):
        """The box holding both, and the child of it each one is in."""
        c = self.c
        chain = []
        cur = a
        while cur is not None:
            chain.append(cur)
            cur = c.parent.get(id(cur))
        cur, prev = b, None
        while cur is not None and all(cur is not x for x in chain):
            prev, cur = cur, c.parent.get(id(cur))
        assert cur is not None, "cut: the two screens are not on the same board"
        i = next(j for j, x in enumerate(chain) if x is cur)
        return cur, (chain[i - 1] if i else None), prev

    # -------------------------------------------------------------- keys on a screen
    def _cut_move(self, n, mv, origin, s0, ps, entry):
        """One move of a screen (or of an edge riding it), in board px: ("shift", axis, f0, f1, d0, d1, ease) or
        ("zoom", f0, f1, k0, k1, ease, P). On an entry the start is set on f0 (it is hidden before)."""
        c = self.c
        if mv[0] == "shift":
            _, ax, f0, f1, d0, d1, ease = mv
            tr, b = c.track(n, ax), c.base(n, ax)
            if entry:
                tr.set(f0, b + d0 / ps)
            tr.move(f0, f1, b + d1 / ps, ease)
            return
        _, f0, f1, k0, k1, ease, P = mv
        for ax in ("scaleX", "scaleY"):
            tr = c.track(n, ax)
            if entry:
                tr.set(f0, s0 * k0)
            tr.move(f0, f1, s0 * k1, ease)
        for i, ax in enumerate(("x", "y")):
            tr, b = c.track(n, ax), c.base(n, ax)
            if entry:
                tr.set(f0, b + (P[i] - origin[i]) * (1 - k0) / ps)
            tr.move(f0, f1, b + (P[i] - origin[i]) * (1 - k1) / ps, ease)

    def _cut_rest(self, n, f, s0):
        """Back in place on frame f (hidden by then), so the next time it shows it starts from rest."""
        c = self.c
        for ax in ("x", "y", "scaleX", "scaleY"):
            if (n, ax) in c.tracks:
                tr = c.tracks[(n, ax)]
                v = s0 if ax.startswith("scale") else c.base(n, ax)
                if abs(tr.value_at(f) - v) > 1e-9:
                    tr.set(f, v)

    def _cut_show(self, n, f):
        tr = self.c.track(n, "opacity")
        if len(tr.keys) == 1 and tr.keys[0]["v"] > 0:     # its first appearance: hidden until the cut
            tr.keys[0]["v"] = 0.0
        elif f > 0 and tr.value_at(f - 1) > 0.01:
            raise ValueError(f"cut: {n} is already on screen before the cut at {f / FPS:.2f}s")
        tr.set(f, 1.0)

    def _cut_hide(self, n, f):
        tr = self.c.track(n, "opacity")
        assert tr.value_at(max(f - 1, 0)) > 0.01, f"cut: {n} is not on screen at {f / FPS:.2f}s (nothing to cut from)"
        tr.set(f, 0.0)

    # -------------------------------------------------------------- a.cut
    def cut(self, src, dst, kind="slide", t=None, cursor="auto", cascade=None, at=None, dir=None, out_px=None,
            in_px=None, wait=None, edges=None, color=None):
        """Screen `src` gives way to screen `dst` (both in one p.stack or p.free), answering a click: `t` is that
        press (default the latest click since the last cut, else now). Returns the cut's time (and `now` moves there).
          kind "slide": a match cut by position, for a page that changes sideways: `wait` 7 f after the press, src
              travels 215 px in 23 f (1, 0, 1, 1), and dst comes 60 px on, settling in 54 f (0, 0, 0, 1). `dir`: where
              the screens go (left, right, up, down); out_px / in_px: other distances (they scale with the piece's
              width: 215 px is the hero's 1340).
          kind "zoom": a click that goes into the thing clicked: 14 f after the press, src grows to 120 % around the
              click (`at`, default the press point) in 23 f; white comes in over 9 f, full from the cut -1 to +3,
              leaves over 15 f; dst comes from 95 % around the same point, settling in 54 f.
          kind "white": in place (a panel that stays): 7 f after the press, white over src in 0.15 s, 0.1 s of white,
              dst shows as it leaves in 0.25 s.
          kind "tabs": a hero's tabs: src leaves 26 px in 20 f, dst comes 34 px on in 26 f; a veil in src's body
              colour closes over the exit's last 10 f, one in dst's opens over the entry's first 10 f (`color`: one
              colour for both). `dir` defaults to against the pill: left when dst comes after src in their p.stack.
        edges (default on for slide and zoom): what shows past the screen's edge while it moves continues the screen:
          vector bands copied from a render of it at rest, 5 px inside the edge.
        cascade: dst's rows come in after the cut, rising 8 px over 0.6 s, 67 ms apart, top to bottom. None: dst's own
          items (default on but for tabs); a list: those; False: none.
        cursor: "walk" (it stays and moves on over the cut), "vanish" (it fades in place before the exit starts) or
          "auto": it walks when its next move comes within 2 s of the cut, else vanishes; the build log says which."""
        assert kind in KINDS, f"cut kind {kind!r}: one of {', '.join(KINDS)}"
        assert cursor in ("auto", "walk", "vanish"), "cursor: auto, walk or vanish"
        st, p, c, k = self._cuts(), self.p, self.c, KINDS[kind]
        se, de = _el(src), _el(dst)
        ns, nd = se.name, de.name
        press = self.last_press
        since = st["cuts"][-1]["t_cut"] if st["cuts"] else -1.0
        if t is None:
            t = press[1] if press is not None and press[1] > since + 1e-6 else self.now
        from_press = press is not None and abs(press[1] - t) < 1e-6
        fp = frame(t)
        f0 = fp + int(k["wait"] if wait is None else wait)
        scale_w = p.w / REF_W
        sp, dp = self._cut_pscale(se), self._cut_pscale(de)
        (so, ss), (do, ds) = self._cut_origin(se, t), self._cut_origin(de, t)
        rec = {"no": len(st["cuts"]) + 1, "kind": kind, "src": se, "dst": de, "ns": ns, "nd": nd, "fp": fp,
               "f0": f0, "t": t, "moves": {ns: [], nd: []}, "origin": {ns: so, nd: do}, "s0": {ns: ss, nd: ds},
               "edges": k["edges"] if edges is None else edges, "veil": None, "cascade": [], "notes": []}
        if kind in ("slide", "tabs"):
            if dir is None:
                dir = self._cut_dir(se, de) if kind == "tabs" else "left"
            ax, sign = {"left": ("x", -1), "right": ("x", 1), "up": ("y", -1), "down": ("y", 1)}[dir]
            d_out = out_px if out_px is not None else k["out_px"] * scale_w
            d_in = in_px if in_px is not None else k["in_px"] * scale_w
            fc = f0 + k["out_frames"]
            f1 = fc + k["in_frames"]
            rec["moves"][ns].append(("shift", ax, f0, fc, 0.0, sign * d_out, k["out_ease"]))
            rec["moves"][nd].append(("shift", ax, fc, f1, -sign * d_in, 0.0, k["in_ease"]))
            prof = _steps(k["out_ease"], k["out_frames"])
            rec["last_px"] = d_out * (prof[-1] - prof[-2])
            rec["gap"] = {"axis": ax, "sign": sign, "out": d_out, "in": d_in}
            if kind == "tabs":
                n = k["veil"]
                rec["veil"] = [(fc - n, 0.0, "linear"), (fc, 1.0, "linear"), (fc + n, 0.0, "hold")]
        elif kind == "zoom":
            P = at if at is not None else self._cut_press_point(press if from_press else None)
            fc = f0 + k["out_frames"]
            f1 = fc + k["in_frames"]
            rec["moves"][ns].append(("zoom", f0, fc, 1.0, k["scale"], k["out_ease"], P))
            rec["moves"][nd].append(("zoom", fc, f1, k["in_scale"], 1.0, k["in_ease"], P))
            prof = _steps(k["out_ease"], k["out_frames"])
            vis = self._cut_vis(se, t)[0] or (0, 0, p.w, p.h)
            far = max(math.dist(P, q) for q in ((vis[0], vis[1]), (vis[2], vis[1]), (vis[0], vis[3]), (vis[2], vis[3])))
            rec["last_px"] = (k["scale"] - 1) * (prof[-1] - prof[-2]) * far
            rec["P"] = P
            a, full0, full1, b = ZOOM_WHITE
            rec["veil"] = [(fc - a, 0.0, "linear"), (fc - full0, 1.0, "hold"), (fc + full1, 1.0, "linear"),
                           (fc + b, 0.0, "hold")]
        else:   # white, in place
            fc = f0 + k["leave"]
            f1 = fc + k["hold"] + k["come"]
            rec["last_px"] = 0.0
            rec["veil"] = [(f0, 0.0, "linear"), (fc, 1.0, "hold"), (fc + k["hold"], 1.0, "linear"), (f1, 0.0, "hold")]
        rec.update(fc=fc, f1=f1, t_cut=fc / FPS, w0=f0, w1=f1 + 1)
        rec["color"] = _color(color) if color else (None if kind == "tabs" else kit.hex_argb("#FFFFFF"))
        # the screens: src out, dst in on the cut, src back in place once hidden
        for mv in rec["moves"][ns]:
            self._cut_move(ns, mv, so, ss, sp, False)
        self._cut_hide(ns, fc)
        self._cut_rest(ns, fc + 1, ss)
        self._cut_show(nd, fc)
        for mv in rec["moves"][nd]:
            self._cut_move(nd, mv, do, ds, dp, True)
        c.cut_entries.add((nd, fc))
        # the cascade: dst's rows after the cut (white: as the white leaves)
        if cascade is True or (cascade is None and k["cascade"]):
            rows = self._cut_rows(de, fc / FPS)
        else:
            rows = [_el(x) for x in cascade] if cascade else []
        start = fc + (k["hold"] if kind == "white" else 0)
        for i, row in enumerate(rows):
            self._cut_rise(row.name, fc - 1, start + round(i * STEP["list"] * FPS))
        rec["cascade"] = [r.name for r in rows]
        # the cursor
        self._cut_cursor(rec, cursor, press if from_press else None)
        st["cuts"].append(rec)
        self._note(t, f"cut {rec['no']} {kind} {ns} -> {nd} (press {t:.2f}s, cut {fc / FPS:.2f}s)")
        self._note(f1 / FPS, f"cut {rec['no']} settled")
        self.now = fc / FPS
        return self.now

    def _cut_dir(self, se, de):
        """A tabs cut's direction: against the pill (hero-tabs: s = -1 when the new tab comes after the old one)."""
        for names in getattr(self.p, "_cut_stacks", []):
            if se.name in names and de.name in names:
                return "left" if names.index(de.name) > names.index(se.name) else "right"
        return "left"

    def _cut_press_point(self, press):
        if press is None:
            return (self.p.w / 2, self.p.h / 2)
        item, t, where = press
        if item is None:
            return tuple(where) if isinstance(where, (tuple, list)) else (self.p.w / 2, self.p.h / 2)
        return self.p.point(item, where if not isinstance(where, (tuple, list)) or item is not None else None, t)

    def _cut_rows(self, de, t):
        """dst's rows, top to bottom: the items of the box in dst that holds the most of them side by side (a list, a
        form, a grid), leaving out its chrome (anything as wide or as tall as the screen: a bar, a background), which
        stays put: what both screens share must not move (LEARNINGS 8)."""
        p = self.p
        wraps = {id(it.wrap): it for it in p.items.values() if it.wrap is not None}
        x0, y0, x1, y1 = _xyxy(p.bounds(wraps[id(de)], t))

        def kids(el):
            found = []

            def walk(e):
                for ch in e.children:
                    if isinstance(ch, El):
                        if id(ch) in wraps:
                            found.append(wraps[id(ch)])
                        else:
                            walk(ch)
            walk(el)
            return [k for k in found if k.kind not in ("tab", "part")]

        def chrome(it):
            bx0, by0, bx1, by1 = _xyxy(p.bounds(it, t))
            return bx1 - bx0 >= 0.95 * (x1 - x0) or by1 - by0 >= 0.95 * (y1 - y0)
        best, todo = [], [wraps[id(de)]]
        while todo:
            it = todo.pop()
            ks = kids(it.wrap)
            todo += ks
            rows = [k for k in ks if not chrome(k)]
            if len(rows) >= 2 and len(rows) > len(best):
                best = rows
        best.sort(key=lambda it: (round(p.bounds(it, t)[1]), p.bounds(it, t)[0]))
        return [r.wrap for r in best]

    def _cut_rise(self, n, f_hide, f):
        """A row of the new screen: hidden while its screen comes, then it fades in (9 f) while rising 8 px (settle)."""
        c = self.c
        op, y = c.track(n, "opacity"), c.track(n, "y")
        rest = c.base(n, "y")
        op.set(f_hide, 0.0)
        y.set(f_hide, rest + CASCADE_DY)
        op.move(f, f + CASCADE_FADE, 1.0, "linear")
        y.move(f + 1, f + 1 + frame(CASCADE_DUR), rest, SETTLE)
        c.cut_entries.add((n, f + 1))

    # -------------------------------------------------------------- the cursor at a cut
    def _cut_cursor(self, rec, mode, press):
        fp, f0 = rec["fp"], rec["f0"]
        f_fade = (max(fp + VANISH_AFTER[0], min(fp + VANISH_AFTER[1], f0 - VANISH_FRAMES)) if press is not None
                  else f0 - VANISH_FRAMES)
        rec["t_fade"] = f_fade / FPS
        if self.visit is None:
            rec["cursor"] = "no cursor on screen"
            return
        pend = {"visit": self.visit, "n": len(self.visit["points"]), "t_cut": rec["t_cut"], "t_fade": rec["t_fade"],
                "verdict": None, "seen": None, "rec": rec}
        rec["pending"] = pend
        if mode == "vanish":
            rec["cursor"] = f"vanishes at {rec['t_fade']:.2f}s (asked)"
            self._cut_vanish(pend)
            pend["verdict"] = "vanish"
        elif mode == "walk":
            rec["cursor"] = "walks (asked)"
            pend["verdict"] = "walk"
        elif not self._cut_st["hooked"]:      # no cursor hook in this piece.py: it can't wait to see
            rec["cursor"] = f"vanishes at {rec['t_fade']:.2f}s (auto: piece.py has no _go to watch)"
            self._cut_vanish(pend)
            pend["verdict"] = "vanish"
        else:
            self._cut_st["pending"] = pend

    def _cut_verdicts(self):
        for rec in self._cut_st["cuts"]:
            pend = rec.get("pending")
            if pend is None or pend["verdict"] is not None:
                continue
            seen = pend["seen"]
            if seen is None:
                rec["cursor"] = "walks (it was still on screen at the end)"
            elif seen[0] == "walks":
                rec["cursor"] = f"walks (next {'click' if seen[2] else 'move'} {seen[1]:.2f} s after)"
            elif len(seen) > 3:
                rec["cursor"] = (f"vanishes at {rec['t_fade']:.2f}s ({seen[3]} comes in"
                                 + (f" {seen[1]:.2f} s after)" if seen[1] is not None else ")"))
            elif seen[1] is None:
                rec["cursor"] = f"vanishes at {rec['t_fade']:.2f}s (nothing after it)"
            else:
                rec["cursor"] = (f"vanishes at {rec['t_fade']:.2f}s (next {'click' if seen[2] else 'move'} "
                                 f"{seen[1]:.2f} s after; it walks within {WALK_MAX:g} s)")

    # -------------------------------------------------------------- the camera
    def camera_close(self, item=None, t=None, scale=None, ui=None, where=None, lead=None, jump=False):
        """A hard cut to a close shot (2.5x) `lead` frames (31) before the click at `t` (default the latest click),
        while the cursor is still on its way: the camera follows the cursor with the cursor's own easing until the
        frame meets the edge of `ui` (an item, or (x0, y0, x1, y1) on the board; default the frame), and stays there,
        never showing past it. After the arrival, a slow zoom out to 2.4 (0.65, 0, 0.8, 0.7) until a.camera_open.
        With no cursor it frames `item` (default the clicked one), still. jump=True: a jump cut into the close shot
        (a.jump_cut). The cursor sits in the camera, so it grows with it. The camera is editable: `CUT`'s strength
        keys are the cut (LEARNINGS 9). Returns the cut's time."""
        st, p = self._cuts(), self.p
        press = self.last_press
        if t is None:
            assert press is not None, "camera_close: no click to frame (call it after the click, or give t=)"
            t = press[1]
            if item is None:
                item, where = press[0], press[2]
        p.camera_node()
        self._cam_show_inside(t, ui, scale or CAMERA["scale"])
        fp = frame(t)
        lead = CAMERA["lead"] if lead is None else int(lead)
        st["camera"] = {"t": t, "fp": fp, "fc": max(0, fp - lead), "item": item, "where": where,
                        "z": scale or CAMERA["scale"], "ui": ui, "open": None}
        if jump:
            self.jump_cut(t=st["camera"]["fc"] / FPS)
        self._note(st["camera"]["fc"] / FPS, f"camera: cut to {st['camera']['z']}x ({fp - st['camera']['fc']} f "
                                             f"before the click)")
        return st["camera"]["fc"] / FPS

    def _cam_show_inside(self, t, ui, z):
        """v14 (the default cursor, hand.py): when the framed click is the cursor's first stop, it shows ~220 px below
        its target, outside a 2.5x close shot held inside the interface: the close shot would open with no cursor and
        it would come in through the frame's edge at the end. It shows inside the close shot instead, on the side
        with the most room (down first, towards the centre, as its own rule), so the camera follows it."""
        v = self.visit
        if v is None or v.get("style") != "hand":
            return
        reals = [q for q in v["points"] if "at" in q]
        if len(reals) != 1 or abs(reals[0]["t"] - t) > 0.5 / FPS:
            return
        p = self.p
        W, H = float(p.w), float(p.h)
        tx, ty = reals[0]["at"]
        u = ((0.0, 0.0, W, H) if ui is None else _xyxy(p.bounds(ui, t)) if isinstance(ui, Item)
             else tuple(float(x) for x in ui))
        view = []
        for i, (size, c) in enumerate(((W, tx), (H, ty))):
            vw = size / z
            u0, u1 = u[i], u[i + 2]
            v0 = (u0 + u1 - vw) / 2 if vw > u1 - u0 else _clamp(c - vw / 2, u0, u1 - vw)
            view.append((v0, v0 + vw))
        (x0, x1), (y0, y1) = view
        m = 14.0                                  # the tip's room from the close shot's edge
        side = 1.0 if tx < (x0 + x1) / 2 else -1.0
        best = None
        for dx, dy in ((0.45 * side, 1.0), (0.45 * side, -1.0), (side, 0.25), (-side, 0.25)):
            n = math.hypot(dx, dy)
            ux, uy = dx / n, dy / n
            room = min(((x1 - m - tx) / ux) if ux > 0 else ((tx - x0 - m) / -ux) if ux < 0 else 1e9,
                       ((y1 - m - ty) / uy) if uy > 0 else ((ty - y0 - m) / -uy) if uy < 0 else 1e9)
            d = min(220.0, room)
            if best is None or d > best[0] + 20:
                best = (d, (tx + ux * d, ty + uy * d))
        if best[0] < 40:
            return
        v["show"] = (round(best[1][0], 2), round(best[1][1], 2))
        self.notes.append(f"camera: the cursor shows inside the close shot ({best[0]:.0f} px from its target)")

    def camera_open(self, t=None, lead=None, frames=None, ease=None):
        """Back to the whole frame: the strong 80/80 zoom out (0.8, 0.0451, 0.2, 1) over 102 f, from `lead` frames
        (25) before the press at `t` (default the latest click: the send); the slow zoom of the close shot runs 40 f
        into it, so the two read as one. Returns when it ends (it doesn't move `now`)."""
        st = self._cuts()
        cam = st["camera"]
        assert cam is not None, "camera_open: a.camera_close first"
        if t is None:
            t = self.last_press[1] if self.last_press is not None else self.now
        f0 = max(cam["fc"] + 1, frame(t) - (OPEN["lead"] if lead is None else int(lead)))
        f1 = f0 + (OPEN["frames"] if frames is None else int(frames))
        cam["open"] = {"f0": f0, "f1": f1, "ease": tuple(ease or OPEN["ease"])}
        self._note(f1 / FPS, f"camera: back to the whole frame ({f0 / FPS:.2f}-{f1 / FPS:.2f}s)")
        return f1 / FPS

    def _cam_names(self):
        a = self.p.art
        return f"{a}.CUT", f"{a}.CAM_CLOSE", f"{a}.CAM_CLOSE.zoom", f"{a}.CAM_CLOSE.track"

    def _cam_rig(self):
        """CAMERA's Transform constraint CUT on the rig CAM_CLOSE (where the cursor sits in the close shot) > .zoom
        (2.5 -> 2.4) > .track (minus where the camera looks: the cursor's tip, held inside the interface). CUT's
        strength: 0 the whole frame, 1 the close shot; its keys are the cut (hold) and the zoom out."""
        st, p, c = self._cut_st, self.p, self.c
        cam = st["camera"]
        W, H, z, F = float(p.w), float(p.h), float(cam["z"]), c.F
        fc, fp = cam["fc"], cam["fp"]
        tip = getattr(self, "cursor_tip", None)
        tips = {f: tip(f) for f in range(fc, fp + 1)} if tip is not None else {}
        seen = [f for f in range(fc, fp + 1) if tips.get(f) is not None]
        if seen:     # the arrival: from there to the press the tip stays put
            f_arr = seen[-1]
            while f_arr - 1 in tips and tips[f_arr - 1] is not None and math.dist(tips[f_arr - 1], tips[f_arr]) < 0.05:
                f_arr -= 1
            first = tips[seen[0]]
            path = {f: (tips[f] if tips.get(f) is not None else first) for f in range(fc, f_arr + 1)}
            land = path[f_arr]
        else:        # no cursor: the item (or the press point), still
            f_arr = fc
            land = (self.p.point(cam["item"], cam["where"], cam["t"]) if cam["item"] is not None
                    else (W / 2, H / 2))
            path = {fc: land}
        ui = cam["ui"]
        u = ((0.0, 0.0, W, H) if ui is None else _xyxy(p.bounds(ui, cam["t"])) if isinstance(ui, Item)
             else tuple(float(v) for v in ui))
        A, lo, hi = [], [], []
        for i, size in enumerate((W, H)):
            vw = size / z
            u0, u1 = u[i], u[i + 2]
            v0 = (u0 + u1 - vw) / 2 if vw > u1 - u0 else _clamp(land[i] - vw / 2, u0, u1 - vw)
            A.append(z * (land[i] - v0))
            lo.append(u0 + A[i] / z)
            hi.append(max(lo[i], u1 - (size - A[i]) / z))
        track = {f: tuple(_clamp(v[i], lo[i], hi[i]) for i in range(2)) for f, v in path.items()}
        # the slow zoom (after the arrival): the view grows about its centre, held inside the interface
        op = cam["open"]
        zs = CAMERA["slow"]
        fs0 = f_arr + CAMERA["slow_after"]
        fs1 = (op["f0"] + OPEN["slow_over"]) if op else F - 1
        A_s = []
        for i, size in enumerate((W, H)):
            v0 = land[i] - A[i] / z
            cen = v0 + size / z / 2
            vw = size / zs
            u0, u1 = u[i], u[i + 2]
            v0s = (u0 + u1 - vw) / 2 if vw > u1 - u0 else _clamp(cen - vw / 2, u0, u1 - vw)
            A_s.append(zs * (land[i] - v0s))
        n_cut, n_close, n_zoom, n_track = self._cam_names()
        cut = El("TransformConstraint", {"targetId": f"@{n_track}", "strength": 1.0 if fc == 0 else 0.0}, name=n_cut)
        trk = El("Node", {"x": -track[fc][0], "y": -track[fc][1]}, [], name=n_track)
        zoom = El("Node", {"x": 0.0, "y": 0.0, "scaleX": z, "scaleY": z}, [trk], name=n_zoom)
        close = El("Node", {"x": A[0], "y": A[1]}, [zoom], name=n_close)
        p.camera.children.append(cut)
        p.board.children.append(close)
        c.parent[id(cut)], c.parent[id(close)], c.parent[id(zoom)], c.parent[id(trk)] = p.camera, p.board, close, zoom
        for e in (cut, close, zoom, trk):
            c.by[e.name] = e
        st["rig"].update({n_close, n_zoom, n_track})
        # CUT: the cut (hold), the zoom out (cubic), back to frame 0's on the last frame (the loop)
        s = c.track(n_cut, "strength")
        if fc > 0:
            s.set(fc, 1.0)
        if op:
            s.move(op["f0"], op["f1"], 0.0, op["ease"])
        if abs(s.value_at(F) - s.keys[0]["v"]) > 1e-9:
            s.set(F, s.keys[0]["v"])
        # .track: the cursor's tip from the cut to its arrival, in at most 12 cubic keys
        errs = []
        for i, ax in enumerate(("x", "y")):
            vals = {f: -track[f][i] for f in track}
            fitted, err = _fit(vals, fc, f_arr)
            errs.append(err)
            tr = c.track(n_track, ax)
            tr.keys = ([{"f": 0, "v": vals[fc], "ease": "hold"}] if fc > 0 else []) + _keys_of(fitted)
            if F > tr.keys[-1]["f"] and abs(tr.keys[-1]["v"] - tr.keys[0]["v"]) > 1e-9:
                tr.set(F, tr.keys[0]["v"])
        # the slow zoom: .zoom 2.5 -> 2.4 and CAM_CLOSE's place on the same curve
        if fs1 > fs0:
            for n, ax, v0, v1 in ((n_zoom, "scaleX", z, zs), (n_zoom, "scaleY", z, zs), (n_close, "x", A[0], A_s[0]),
                                  (n_close, "y", A[1], A_s[1])):
                tr = c.track(n, ax)
                tr.move(fs0, min(fs1, F - 1), v1, CAMERA["slow_ease"])
                if F > fs1 and abs(v1 - v0) > 1e-9:
                    tr.set(F, v0)
        held = [ax for i, ax in enumerate("xy") if any(abs(track[f][i] - path[f][i]) > 1e-6 for f in track)]
        self.notes.append(
            f"camera: cut to {z:g}x at {fc / FPS:.2f}s ({fp - fc} f before the click), "
            + (f"follows the cursor to its arrival at {f_arr / FPS:.2f}s" if seen else "still on the item (no cursor)")
            + (f", against the interface's edge on {'/'.join(held)}" if held else "")
            + f"; track in {len(c.tracks[(n_track, 'x')].keys)}/{len(c.tracks[(n_track, 'y')].keys)} keys "
              f"(error {max(errs):.2f} px on the board)"
            + (f"; slow zoom {z:g} -> {zs:g} {fs0 / FPS:.2f}-{min(fs1, F - 1) / FPS:.2f}s" if fs1 > fs0 else "")
            + (f"; zoom out {op['f0'] / FPS:.2f}-{op['f1'] / FPS:.2f}s" if op else
               "; no camera_open: it stays close to the loop's end"))
        cam["view"] = {"A": A, "z": z, "u": u, "track": track, "f_arr": f_arr}

    # -------------------------------------------------------------- the jump cut
    def jump_cut(self, t=None, out_px=None, out_frames=None, in_px=None, in_frames=None, dir="left", entry="continue",
                 ease=None, edges=True):
        """A hard cut that isn't "totally hard": the whole picture slides `out_px` (23.4 px) in `out_frames` (27)
        accelerating (1, 0, 1, 0.9554), and after the cut it comes `in_px` (30 px) on with the same direction
        (entry="opposite": from the other side, as in his v15.12), settling in 34 f. t=None: the loop's seam (call
        it last, after the rest: it ends the timeline, the start comes in from the slide); t=s: a cut inside the
        piece (camera_close(jump=True) puts one on the close shot's cut). ease="80-80": the slide is the first half
        of an 84 f 80/80, cut on its peak (ma-novo v18.9). Distances are on screen: inside a close shot (JUMP sits in
        the camera) they are divided by its scale. edges: what shows past the picture's edge (or the interface's, in
        a close shot) continues it."""
        st, p = self._cuts(), self.p
        p.camera_node()
        if ease == "80-80":
            out_ease = _split(JUMP_8080["curve"], 0.5)
            n_out = JUMP_8080["frames"] // 2 if out_frames is None else int(out_frames)
        else:
            out_ease = tuple(ease) if ease else JUMP["out_ease"]
            n_out = JUMP["out_frames"] if out_frames is None else int(out_frames)
        ax, sign = {"left": ("x", -1), "right": ("x", 1), "up": ("y", -1), "down": ("y", 1)}[dir]
        d_out = JUMP["out_px"] if out_px is None else out_px
        d_in = JUMP["in_px"] if in_px is None else in_px
        jp = {"axis": ax, "out": sign * d_out, "in": (-sign if entry == "continue" else sign) * d_in,
              "n_out": n_out, "n_in": JUMP["in_frames"] if in_frames is None else int(in_frames),
              "out_ease": out_ease, "edges": edges, "px": (d_out, d_in)}
        f_at = None if t is None else frame(t)
        if f_at is not None:      # px on screen: JUMP is inside the camera, so a close shot's are z times bigger
            jp["out"] /= self._cam_z_at(f_at - 1)
            jp["in"] /= self._cam_z_at(f_at)
        if t is None:     # the seam: after everything, the slide, then frame 0
            if self.visit is not None:
                self.cursor_out()
            end = max(self.now, self._cursor_end() if self.visits else 0.0)
            fs = frame(end) + n_out + 1
            jp.update(seam=True, f=fs)
            self.reset_at, self.looped, self.loop_exit = fs / FPS, True, p.root
            self.now = fs / FPS
            self._note(fs / FPS, f"jump cut at the seam (slide {(fs - n_out - 1) / FPS:.2f}-{(fs - 1) / FPS:.2f}s)")
        else:
            jp.update(seam=False, f=frame(t))
            self._note(t, "jump cut")
        st["jumps"].append(jp)
        return jp["f"] / FPS

    def _jump_windows(self):
        """Jump cuts close together: an entry still settling when the next slide starts is cut short there (the
        settle has done most of its way in its first frames); two slides can't overlap."""
        F = self.c.F
        ev = sorted(((0 if jp["seam"] else jp["f"]), (F if jp["seam"] else jp["f"]) - jp["n_out"] - 1, jp)
                    for jp in self._cut_st["jumps"])
        slides = sorted((s0, (F if jp["seam"] else jp["f"]) - 1) for _, s0, jp in ev)
        for (a0, a1), (b0, _) in zip(slides, slides[1:]):
            assert b0 > a1, f"jump cuts at {(a1 + 1) / FPS:.2f}s and {(b0 + 1) / FPS:.2f}s: their slides overlap"
        for f_in, _, jp in ev:
            nxt = [s0 for s0, _ in slides if s0 > f_in]
            if nxt and f_in + jp["n_in"] >= nxt[0]:
                jp["short"], jp["n_in"] = jp["n_in"], nxt[0] - f_in - 1

    def _cam_z_at(self, f):
        """The camera's scale at frame f as the actions set it (the close shot from its cut to camera_open)."""
        cam = self._cuts()["camera"]
        if cam is None or f < cam["fc"] or (cam["open"] is not None and f >= cam["open"]["f0"]):
            return 1.0
        return float(cam["z"])

    def _jump_node(self):
        """JUMP: a node inside the camera holding the whole picture (cursors too), slid by the jump cuts."""
        p, c = self.p, self.c
        name = f"{p.art}.JUMP"
        if name in c.by:
            return c.by[name]
        cam = p.camera
        kids = [k for k in cam.children if k.tag != "TransformConstraint"]
        jump = El("Node", {"x": 0.0, "y": 0.0}, kids, name=name)
        cam.children = [jump] + [k for k in cam.children if k.tag == "TransformConstraint"]
        c.parent[id(jump)] = cam
        for k in kids:
            c.parent[id(k)] = jump
        c.by[name] = jump
        self._cut_st["rig"].add(name)
        return jump

    def _jump_keys(self, jp):
        c, F = self.c, self.c.F
        n = self._jump_node().name
        tr = c.track(n, jp["axis"])
        f, no, ni = (F if jp["seam"] else jp["f"]), jp["n_out"], jp["n_in"]
        tr.move(f - no - 1, f - 1, jp["out"], jp["out_ease"])
        if jp["seam"]:     # the start comes in from the slide (frame 0), the end goes back there (frame F)
            tr.keys[0].update({"v": jp["in"]})
            tr.move(0, ni, 0.0, JUMP["in_ease"])
            tr.set(F, jp["in"])
        else:
            tr.set(f, jp["in"])
            tr.move(f, f + ni, 0.0, JUMP["in_ease"])
        self.notes.append(f"jump cut {'at the seam' if jp['seam'] else f'at {f / FPS:.2f}s'}: slides "
                          f"{jp['px'][0]:g} px {f - no - 1}-{f - 1}, in {jp['px'][1]:g} px "
                          f"{'on with it' if jp['out'] * jp['in'] < 0 else 'from the other side'}, settling in {ni} f"
                          + (f" (of {jp['short']}: the next jump's slide starts)" if "short" in jp else ""))

    # -------------------------------------------------------------- the scroll
    def scroll(self, box, dy, t=None, dur=None, ease=None, cursor=False, read=None):
        """Scroll `box` (the content that moves, inside a box that clips it) by dy px (positive: the page goes up,
        showing what's below): one move on his curve (0.857, 0, 0.242, 1), never coming back, ~0.9 s + 1.5 ms per px
        (784 px in ~2.1 s, peaking ~23 px/f), longer if it would pass the text's speed limit. The top stays readable
        ~1 s after its screen comes in (`read` s): an earlier t waits. cursor=True: a cursor comes in 6 f before it
        ends (`now` moves there, for the next click). Returns the end."""
        self._cuts()
        c = self.c
        n = _el(box).name
        ease = tuple(ease or SCROLL["ease"])
        dist = abs(float(dy))
        t = self._t(t)
        read = SCROLL["read"] if read is None else secs(read)
        shown = self._cut_shown_at(_el(box), t)
        if shown is not None and t < shown + read - 1e-6:
            self.notes.append(f"scroll {n}: at {shown + read:.2f}s, not {t:.2f}s (its top readable {read:g} s first)")
            t = shown + read
        cap = choreo.TOKENS["speed_cap_px_per_frame_at_1920"]["text_content"]
        peak = _peak(ease)
        dur = secs(dur) if dur else SCROLL["base"] + SCROLL["per_px"] * dist
        n_f = max(frame(dur), math.ceil(peak * dist / (cap * 0.95)))
        y = c.track(n, "y")
        y0 = y.value_at(frame(t))
        y.move(frame(t), frame(t) + n_f, y0 - float(dy), ease)
        end = (frame(t) + n_f) / FPS
        self._note(t, f"scroll {n} {dy:g} px in {n_f} f (peak {peak * dist / n_f:.1f} px/f)")
        self._note(end, f"scroll {n} ends")
        self.now = end
        if cursor:
            self.cursor_in(t=end - SCROLL["cursor"] / FPS)
        return end

    def _cut_shown_at(self, el, t):
        """When `el` (or a box holding it) last came on screen before t."""
        c, f, best = self.c, frame(t), None
        cur = el
        while cur is not None and cur is not self.p.board:
            tr = c.tracks.get((cur.name, "opacity")) if cur.name else None
            if tr is not None:
                for g in range(f, 0, -1):
                    if tr.value_at(g) > 0.01 and tr.value_at(g - 1) <= 0.01:
                        best = max(best or 0.0, g / FPS)
                        break
            cur = c.parent.get(id(cur))
        return best

    # -------------------------------------------------------------- at the build's end
    def _cuts_finish(self):
        """After the cursors and the duration: the cursor verdicts, the edges and the white, the camera, the jump."""
        st, c = self._cut_st, self.c
        self._cut_verdicts()
        jobs = []
        for rec in st["cuts"]:
            if rec["edges"]:
                rec["gaps"] = self._cut_gaps(rec)
                for g in rec["gaps"]:
                    g["job"] = len(jobs)
                    jobs.append((g["frame"], g["drop"], g["hide"]))
            if rec["veil"] and rec["color"] is None:     # tabs: each screen's body colour, from a render of it
                rec["veil_jobs"] = []
                for el, n, f, entry in ((rec["src"], rec["ns"], rec["f0"] - 1, False),
                                        (rec["dst"], rec["nd"], rec["fc"] + 1, True)):
                    drop = frozenset((n, q) for q in ("x", "y", "scaleX", "scaleY")) if entry else frozenset()
                    rec["veil_jobs"].append((len(jobs), el))
                    jobs.append((f, drop, frozenset(rec["cascade"]) if entry else frozenset()))
        if st["camera"] is not None:
            self._cam_rig()
        self._jump_windows()
        for jp in st["jumps"]:
            if jp["edges"]:
                jp["gaps"] = self._jump_gaps(jp)
                for g in jp["gaps"]:
                    g["job"] = len(jobs)
                    jobs.append((g["frame"], g["drop"], g["hide"]))
        imgs = self._cut_snapshots(jobs) if jobs else []
        for rec in st["cuts"]:
            for g in rec.get("gaps", []):
                self._cut_strip(rec, g, imgs[g["job"]])
            if rec.get("veil_jobs"):
                rec["colors"] = [self._cut_body(imgs[j], el, rec["t"]) for j, el in rec["veil_jobs"]]
            if rec["veil"]:
                self._cut_veil(rec)
            self.notes.append(f"cut {rec['no']} ({rec['kind']} {rec['ns']} -> {rec['nd']}, {rec['t_cut']:.2f}s): "
                              f"cursor {rec.get('cursor', '?')}"
                              + (f"; {len(rec.get('gaps', []))} edge(s)" if rec["edges"] else "")
                              + (f"; cascade of {len(rec['cascade'])}" if rec["cascade"] else "")
                              + "".join(f"; {x}" for x in rec["notes"]))
        for jp in st["jumps"]:
            self._jump_keys(jp)
            for g in jp.get("gaps", []):
                self._jump_strip(jp, g, imgs[g["job"]])
        c._samples = None

    # -------------------------------------------------------------- edges
    def _cut_gaps(self, rec):
        """Where a screen's moving edge would show what's behind it: one per side its displacement uncovers, on the
        sides where the screen reaches its clipping box (a card smaller than its box shows its own edge)."""
        gaps = []
        for n, el, entry in ((rec["ns"], rec["src"], False), (rec["nd"], rec["dst"], True)):
            vis, clip = self._cut_vis(el, rec["t"])
            if vis is None:
                continue
            full = _xyxy(self.p.bounds(self._cut_item(el), rec["t"]))
            reach = [full[0] <= clip[0] + 0.5, full[1] <= clip[1] + 0.5, full[2] >= clip[2] - 0.5,
                     full[3] >= clip[3] - 0.5]
            f_snap = rec["f0"] - 1 if not entry else rec["fc"] + 1
            drop = (frozenset((n, p) for p in ("x", "y", "scaleX", "scaleY")) if entry else frozenset())
            hide = frozenset(rec["cascade"]) if entry else frozenset()
            sides = {}      # side -> how far (board px) the edge goes in, at most
            for mv in rec["moves"][n]:
                if mv[0] == "shift":
                    _, ax, _, _, d0, d1, _ = mv
                    for d in (d0, d1):
                        if abs(d) > 0.01:
                            side = {("x", -1): 2, ("x", 1): 0, ("y", -1): 3, ("y", 1): 1}[(ax, -1 if d < 0 else 1)]
                            sides[side] = max(sides.get(side, 0.0), abs(d))
                else:
                    _, _, _, k0, k1, _, P = mv
                    k = min(k0, k1)
                    if k < 1:
                        for side, edge, i in ((0, full[0], 0), (1, full[1], 1), (2, full[2], 0), (3, full[3], 1)):
                            sides[side] = max(sides.get(side, 0.0), (1 - k) * abs(edge - P[i]))
            for side, d in sorted(sides.items()):
                if reach[side]:
                    gaps.append({"n": n, "el": el, "entry": entry, "side": side, "d": d, "vis": vis, "full": full,
                                 "frame": f_snap, "drop": drop, "hide": hide})
        return gaps

    def _cut_strip(self, rec, g, img):
        """The edge: an absolute box in the screens' box, in front of the screen, with a band of colour per run of
        the screen's last pixels (5 px inside); it rides the screen's moves and shows while the edge is off."""
        p, c = self.p, self.c
        side, vis, full, d = g["side"], g["vis"], g["full"], g["d"]
        lca, ba, bb = self._cut_lca(rec["src"], rec["dst"])
        branch = ba if g["el"] is rec["src"] else bb
        box = self._cut_rect(lca, rec["t"])
        ls = self._scale_of(lca.name) if lca.name in c.by else 1.0
        if box is None or abs(ls - 1.0) > 1e-6:
            rec["notes"].append(f"no edge on {g['n']} (its box isn't a placed item at scale 1)")
            return
        k = min([mv[3] for mv in rec["moves"][g["n"]] if mv[0] == "zoom"] + [1.0])
        reach = (d / k) + EDGE_MARGIN
        if side in (0, 2):     # left / right: bands down a column
            line = vis[0] + EDGE_INSIDE if side == 0 else vis[2] - EDGE_INSIDE - 1
            x0, x1 = (full[0] - reach, vis[0] + EDGE_BEFORE) if side == 0 else (vis[2] - EDGE_BEFORE, full[2] + reach)
            ext = max(sides_d for sides_d in [0.0] + [gg["d"] / k for gg in rec.get("gaps", [])
                                                     if gg["n"] == g["n"] and gg["side"] in (1, 3)])
            y0, y1 = vis[1] - ext - EDGE_MARGIN * (ext > 0), vis[3] + ext + EDGE_MARGIN * (ext > 0)
            bands, along = _bands(img, line, vis[1], vis[3], "y"), "y"
            a0, a1 = vis[1] - y0, vis[3] - y0
        else:                  # top / bottom: bands along a row
            line = vis[1] + EDGE_INSIDE if side == 1 else vis[3] - EDGE_INSIDE - 1
            y0, y1 = (full[1] - reach, vis[1] + EDGE_BEFORE) if side == 1 else (vis[3] - EDGE_BEFORE, full[3] + reach)
            ext = max(sides_d for sides_d in [0.0] + [gg["d"] / k for gg in rec.get("gaps", [])
                                                     if gg["n"] == g["n"] and gg["side"] in (0, 2)])
            x0, x1 = vis[0] - ext - EDGE_MARGIN * (ext > 0), vis[2] + ext + EDGE_MARGIN * (ext > 0)
            bands, along = _bands(img, line, vis[0], vis[2], "x"), "x"
            a0, a1 = vis[0] - x0, vis[2] - x0
        name = f"{p.art}.cut{rec['no']}.{'src' if not g['entry'] else 'dst'}.edge{'LTRB'[side]}"
        rect = (x0, y0, x1, y1)
        el = self._cut_band_box(name, rect, bands, along, a0, a1, (box[0], box[1]))
        if el is None:
            return
        i = next(j for j, ch in enumerate(lca.children) if ch is branch)
        lca.children.insert(i, el)
        self._cut_register(el, lca)
        # it rides the screen: the same moves about the same point, from its own corner
        for mv in rec["moves"][g["n"]]:
            self._cut_move(name, mv, (x0, y0), 1.0, 1.0, g["entry"])
        op = c.track(name, "opacity")
        if g["entry"]:
            mv = rec["moves"][g["n"]][-1]
            f_on, f_off = rec["fc"], mv[3] if mv[0] == "shift" else mv[2]
            op.set(f_on, 1.0)
            op.set(f_off, 0.0)
        else:
            op.set(rec["f0"], 1.0)
            op.set(rec["fc"], 0.0)
            self._cut_rest(name, rec["fc"] + 1, 1.0)
        c.cut_entries.add((name, rec["fc"]))
        rec.setdefault("names", set()).add(name)

    def _cut_band_box(self, name, rect, bands, along, a0, a1, origin):
        """An absolute box at rect (board px; origin: its parent's top-left) holding a rectangle per band. The first
        and last bands run to the box's ends; each band starts 0.5 px under the one before it (drawn over it), so no
        hairline shows between them and every boundary stays exactly where the screen has it."""
        x0, y0, x1, y1 = rect
        w, h = x1 - x0, y1 - y0
        L = h if along == "y" else w
        shapes = []
        for i, (s, e, col) in enumerate(bands):
            if col[3] < 128:
                continue
            s = 0.0 if i == 0 else a0 + s - 0.5
            e = L if i == len(bands) - 1 else a0 + e
            fill = kit.hex_argb("#%02x%02x%02x" % col[:3])
            if along == "y":
                shapes.append(kit.shape_rect(f"{name}.b{i}", w, e - s, fill=fill, x=w / 2, y=(s + e) / 2))
            else:
                shapes.append(kit.shape_rect(f"{name}.b{i}", e - s, h, fill=fill, x=(s + e) / 2, y=h / 2))
        if not shapes:
            return None
        art = El("Node", {}, shapes[::-1], name=f"{name}.art", order="layers")    # bottom -> top: the first band on top
        return kit.absolute(name, [art], inset=(x0 - origin[0], y0 - origin[1], None, None), opacity=0.0, w=w, h=h,
                            layoutWidthScaleType="fixed", layoutHeightScaleType="fixed")

    def _cut_register(self, el, parent):
        c = self.c
        c.parent[id(el)] = parent

        def walk(e):
            if e.name:
                c.by[e.name] = e
            for ch in e.children:
                if isinstance(ch, El):
                    c.parent[id(ch)] = e
                    walk(ch)
        walk(el)

    def _cut_veil(self, rec):
        """The white (tabs: the screens' body colours): a box in front of both screens and their edges, in their box."""
        p, c = self.p, self.c
        lca, ba, bb = self._cut_lca(rec["src"], rec["dst"])
        box = self._cut_rect(lca, rec["t"])
        if box is None:
            rec["notes"].append("no white: the screens' box isn't a placed item")
            return
        vs, clip = self._cut_vis(rec["src"], rec["t"])
        vd, _ = self._cut_vis(rec["dst"], rec["t"])
        r = _union(vs or clip, vd or clip)
        if rec["kind"] == "zoom":     # src grows: the white covers what it covers then, in its clip
            P, s = rec["P"], KINDS["zoom"]["scale"]
            g = vs or clip
            r = _union(r, (P[0] + s * (g[0] - P[0]), P[1] + s * (g[1] - P[1]), P[0] + s * (g[2] - P[0]),
                           P[1] + s * (g[3] - P[1])))
        r = _inter(r, clip) or clip
        fc = rec["fc"]
        if rec.get("colors"):     # tabs: src's colour closes up to the cut, dst's opens from it (hero-tabs)
            (f_a, _, _), _, (f_b, _, _) = rec["veil"]
            parts = [("veilOut", rec["colors"][0], [(f_a, 0.0, "linear"), (fc, 1.0, "hold"), (fc + 1, 0.0, "hold")]),
                     ("veilIn", rec["colors"][1], [(fc - 1, 0.0, "hold"), (fc, 1.0, "linear"), (f_b, 0.0, "hold")])]
            rec["notes"].append("veil " + " -> ".join("#" + kit_hex[2:] for kit_hex in
                                                      (f"{x:08X}" if isinstance(x, int) else str(x)
                                                       for x in rec["colors"])))
        else:
            parts = [("white", rec["color"], rec["veil"])]
        mine = f"{p.art}.cut{rec['no']}."     # over both screens and their edges (the first child draws on top)
        i = min(j for j, ch in enumerate(lca.children) if ch is ba or ch is bb or str(ch.name).startswith(mine))
        for suffix, colour, keys in parts:
            name = f"{p.art}.cut{rec['no']}.{suffix}"
            el = kit.absolute(name, [], paints=[kit.solid(f"{name}.fill", colour)],
                              inset=(r[0] - box[0], r[1] - box[1], None, None), opacity=0.0, w=r[2] - r[0],
                              h=r[3] - r[1], layoutWidthScaleType="fixed", layoutHeightScaleType="fixed")
            lca.children.insert(i, el)
            self._cut_register(el, lca)
            tr = c.track(name, "opacity")
            for f, v, e in keys:
                if e == "hold":
                    tr.set(f, v)
                else:
                    tr._upsert(f, v, e)

    def _cut_body(self, img, el, t):
        """A screen's body colour: the most common one in a render of it at rest (hero-tabs' BODY_BG)."""
        vis, clip = self._cut_vis(el, t)
        r = vis or clip
        crop = img.convert("RGB").crop(tuple(int(round(v)) for v in r))
        n, rgb = max(crop.getcolors(crop.size[0] * crop.size[1]))
        return kit.hex_argb("#%02X%02X%02X" % rgb)

    def _jump_gaps(self, jp):
        """The jump cut's edges: the frame's edge the slide uncovers (in the whole frame), and the interface's edge
        the entry uncovers in the close shot (or the frame's)."""
        st, p, c = self._cut_st, self.p, self.c
        W, H, F = float(p.w), float(p.h), c.F
        f = F if jp["seam"] else jp["f"]
        ax = 0 if jp["axis"] == "x" else 1
        drop = frozenset(k for k in c.tracks if k[0] == p.camera.name or k[0] in st["rig"])
        gaps = []
        strength = c.tracks.get((self._cam_names()[0], "strength"))
        close = lambda g: strength is not None and strength.value_at(g % F if F else g) > 0.5   # noqa: E731
        f_out = f - jp["n_out"] - 1
        if not close(f_out):         # the slide in the whole frame: the frame's far edge
            side = (2 if jp["out"] < 0 else 0) if ax == 0 else (3 if jp["out"] < 0 else 1)
            gaps.append({"what": "out", "side": side, "d": abs(jp["out"]), "view": (0.0, 0.0, W, H),
                         "frame": max(f_out - 1, 1), "drop": drop, "hide": frozenset()})
        f_in = 0 if jp["seam"] else f
        side = (2 if jp["in"] < 0 else 0) if ax == 0 else (3 if jp["in"] < 0 else 1)
        if close(f_in) and st["camera"] and "view" in st["camera"]:
            v = st["camera"]["view"]
            P = v["track"][min(max(f_in, min(v["track"])), max(v["track"]))]
            view = (P[0] - v["A"][0] / v["z"], P[1] - v["A"][1] / v["z"], P[0] + (W - v["A"][0]) / v["z"],
                    P[1] + (H - v["A"][1]) / v["z"])
            u = v["u"]
            edge = [view[0] <= u[0] + 0.5, view[1] <= u[1] + 0.5, view[2] >= u[2] - 0.5, view[3] >= u[3] - 0.5]
            if not edge[side]:
                return gaps         # the interface goes on past the view: nothing to cover
        else:
            view = (0.0, 0.0, W, H)
        gaps.append({"what": "in", "side": side, "d": abs(jp["in"]), "view": view,
                     "frame": f_in + jp["n_in"] + 1, "drop": drop, "hide": frozenset()})
        return gaps

    def _jump_strip(self, jp, g, img):
        """A jump cut's edge: bands in JUMP (it rides the slide), in front of the picture, under the cursors."""
        p, c, F = self.p, self.c, self.c.F
        jump = self._jump_node()
        v, side, d = g["view"], g["side"], g["d"] + EDGE_MARGIN
        if side in (0, 2):
            line = v[0] + EDGE_INSIDE if side == 0 else v[2] - EDGE_INSIDE - 1
            x0, x1 = (v[0] - d, v[0] + EDGE_BEFORE) if side == 0 else (v[2] - EDGE_BEFORE, v[2] + d)
            y0, y1 = v[1], v[3]
            bands, along, a0, a1 = _bands(img, line, v[1], v[3], "y"), "y", 0.0, v[3] - v[1]
        else:
            line = v[1] + EDGE_INSIDE if side == 1 else v[3] - EDGE_INSIDE - 1
            y0, y1 = (v[1] - d, v[1] + EDGE_BEFORE) if side == 1 else (v[3] - EDGE_BEFORE, v[3] + d)
            x0, x1 = v[0], v[2]
            bands, along, a0, a1 = _bands(img, line, v[0], v[2], "x"), "x", 0.0, v[2] - v[0]
        no = next(i for i, j in enumerate(self._cut_st["jumps"]) if j is jp) + 1
        name = f"{p.art}.JUMP.{no}{g['what']}{'LTRB'[side]}"
        box = self._cut_band_box(name, (x0, y0, x1, y1), bands, along, a0, a1, (0.0, 0.0))
        if box is None:
            return
        node = next(k for k in box.children if k.tag == "Node")   # inside a Node, no layout: a Node at the corner
        node.name, node.attrs = name, {"x": x0, "y": y0, "opacity": 0.0}
        kids = jump.children
        i = next((j for j, k in enumerate(kids) if k is self.p.root), len(kids))
        kids.insert(i, node)
        self._cut_register(node, jump)
        self._cut_st["rig"].add(name)
        op = c.track(name, "opacity")
        f = F if jp["seam"] else jp["f"]
        if g["what"] == "out":
            op.set(f - jp["n_out"] - 1, 1.0)
            op.set(f, 0.0)
        elif jp["seam"]:
            op.keys[0]["v"] = 1.0
            op.set(jp["n_in"] + 1, 0.0)
            op.set(F, 1.0)
        else:
            op.set(f, 1.0)
            op.set(f + jp["n_in"] + 1, 0.0)

    # -------------------------------------------------------------- renders of the scene (for the edges)
    def _cut_snapshots(self, jobs):
        """Renders of the board at given frames, without the cursors, the camera, some tracks (`drop`: a screen at
        rest) and some elements (`hide`: a cascade's rows). One CLI build per set of drop/hide; cached by content."""
        from PIL import Image
        p, c = self.p, self.c
        groups = {}
        for i, (f, drop, hide) in enumerate(jobs):
            groups.setdefault((drop, hide), []).append((i, f))
        out = [None] * len(jobs)
        base = os.path.join(p.here, "build", "cuts")
        os.makedirs(base, exist_ok=True)
        link = os.path.join(base, "fonts")
        if not os.path.lexists(link):
            os.symlink(os.path.join(kit.HERE, "fonts"), link)
        for (drop, hide), items in groups.items():
            board = copy.deepcopy(p.board)
            parent, by = {}, {}

            def walk(e):
                for ch in e.children:
                    if isinstance(ch, El):
                        parent[id(ch)] = e
                        if ch.name:
                            by[ch.name] = ch
                        walk(ch)
            walk(board)
            for n in (f"{p.art}.cursors",):
                if n in by:
                    parent[id(by[n])].children.remove(by[n])
            if getattr(p, "camera", None) is not None and p.camera.name in by:
                cam = by[p.camera.name]
                cam.children = [k for k in cam.children if k.tag != "TransformConstraint"]
            by.clear()
            walk(board)
            for n in hide:
                if n in by:
                    by[n].attrs["opacity"] = 0.0
            keep = {k: tr for k, tr in c.tracks.items() if k[0] in by and k[0] not in hide and k not in drop
                    and k[0] != getattr(getattr(p, "camera", None), "name", None)}
            saved, c.tracks = c.tracks, keep
            try:
                kos = c.to_rml()
            finally:
                c.tracks = saved
            tl = El("LinearAnimation", {"fps": FPS, "duration": c.F, "loopValue": None}, kos, name="Snapshot",
                    ref=f"anim.{p.art} snapshot")
            kit.use(p.vm)
            lay = kit.Layer("Main")
            lay.state("run", type("A", (), {"name": f"{p.art} snapshot"}), entry=True)
            board.children.insert(3, tl)
            board.children.append(kit.machine([lay]))
            font = kit.FONT_DIR[0]
            kit.FONT_DIR[0] = "fonts"
            try:
                xml, _ = kit.assemble([board] + p.comps + p.icons, list(kit.VM.all), base=base)
            finally:
                kit.FONT_DIR[0] = font
            h = hashlib.sha256(xml.encode()).hexdigest()[:16]
            d = os.path.join(base, h)
            todo = [(i, f, os.path.join(d, f"f{f}.png")) for i, f in items]
            if any(not os.path.exists(png) for _, _, png in todo):
                os.makedirs(d, exist_ok=True)
                if not os.path.lexists(os.path.join(d, "fonts")):
                    os.symlink(os.path.join(kit.HERE, "fonts"), os.path.join(d, "fonts"))
                kit.FONT_DIR[0] = "fonts"
                try:     # again, with the photos' paths from its own folder
                    xml_d, _ = kit.assemble([board] + p.comps + p.icons, list(kit.VM.all), base=d)
                finally:
                    kit.FONT_DIR[0] = font
                open(os.path.join(d, "scene.rml"), "w").write(xml_d + "\n")
                open(os.path.join(d, "rive.yaml"), "w").write(f'name: snapshot\nmain: "{p.art}"\n')
                for i, f, png in todo:
                    if os.path.exists(png):
                        continue
                    r = subprocess.run([RIVE, d, f"--screenshot={png}", f"--advance={f if f else '1ms'}", "--quiet"],
                                       capture_output=True, text=True, timeout=180)
                    if r.returncode:
                        raise RuntimeError("cut edges: the render failed:\n" + (r.stdout + r.stderr)[-1500:])
            for i, f, png in todo:
                out[i] = Image.open(png).convert("RGBA")
        return out

    # -------------------------------------------------------------- the lint
    def _cuts_lint(self, report, issues):
        """The kit's lint, with the cuts' frames out of the speed check for what the cuts move (as choreo does for
        its own match cuts), the camera's rig out of it (a camera, not content), and a row per cut: its last step
        into the cut against the match cut's cap."""
        st, p, c = self._cut_st, self.p, self.c
        caps = choreo.TOKENS["speed_cap_px_per_frame_at_1920"]
        win = {}
        for rec in st["cuts"]:
            for n in {rec["ns"], rec["nd"]} | rec.get("names", set()):
                win.setdefault(n, set()).update(range(rec["w0"], rec["w1"] + 1))
        glob = set()        # a jump cut moves the whole picture: its frames are out for everything (choreo's cut
        for jp in st["jumps"]:      # windows are, for all movers)
            f = c.F if jp["seam"] else jp["f"]
            glob.update(range(f - jp["n_out"] - 1, f + 1))
            glob.update(range(0, jp["n_in"] + 1) if jp["seam"] else range(f, f + jp["n_in"] + 1))
        rig = tuple(st["rig"]) + (f"{p.art}.JUMP",)
        movers = {n for (n, q) in c.tracks if q in ("x", "y")}
        redo = set(win)
        out = []
        for i in issues:
            m = re.match(r"(\S+) peaks at [\d.]+ px/f > cap", i)
            if m and m.group(1).startswith(rig):
                continue
            if m and (m.group(1) in win or (glob and m.group(1) in movers and not m.group(1).startswith("CURSOR"))):
                redo.add(m.group(1))
                continue
            out.append(i)
        report = [r for r in report if not (r[0] in redo or str(r[0]).startswith(rig))]
        for n in sorted(redo):
            if (n, "x") not in c.tracks and (n, "y") not in c.tracks:
                continue
            peak, at = self._cut_peak(n, win.get(n, set()) | glob)
            cap = caps["text_content"]
            report.append((n, "content", peak, cap, at))
            if peak > cap + 0.5:
                out.append(f"{n} peaks at {peak:.1f} px/f > cap {cap} at {at / FPS:.2f}s (outside its cut)")
        for rec in st["cuts"]:
            report.append((f"cut {rec['no']} {rec['kind']}", "cut", rec["last_px"], caps["match_cut"], rec["fc"]))
            if rec["last_px"] > caps["match_cut"] + 0.5:
                out.append(f"cut {rec['no']}: its last step into the cut is {rec['last_px']:.0f} px/f > cap "
                           f"{caps['match_cut']}")
        return report, out

    def _cut_peak(self, n, skip):
        """choreo's element speed (own moves, on screen, visible), outside the frames in `skip`."""
        c = self.c
        el = c.by[n]
        peak, at = 0.0, 0
        prev = c.to_screen(el, (c.prop(el, "x", 0), c.prop(el, "y", 0)), 0)
        for f in range(1, c.F + 1):
            cur = c.to_screen(el, (c.prop(el, "x", f), c.prop(el, "y", f)), f)
            on = -2 < cur[0] < choreo.W + 2 and -2 < cur[1] < choreo.H + 2
            if f - 1 not in skip and f not in skip and on and c.opacity_chain(el, f) > 0.05:
                sp = math.dist(prev, cur) * choreo.OUT_SCALE
                if sp > peak:
                    peak, at = sp, f
            prev = cur
        return peak, at
