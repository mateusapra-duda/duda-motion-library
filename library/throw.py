"""v16: a file thrown into an input (LEARNINGS 19.3), the motion designer's own animation copied as it is: the first
curated example of the library (an approved animation copied, not deduced from a rule).

Source: his `header_(example).rev` ("DROPPING THE IMAGE"), as the Migration Page v05 copied it
(pecas/migration-page/tools/hand.py; v05.2's 9-frame drop zone and v05.4's bigger hand are his later requests).
Frames below count from S, the frame the hand shows (his 175).

    a.drop_file(file, into=field, zone=drop, result=[thumb])

- The hand shows already moving, holding the file by its bottom edge, in the middle; hand and file fade in over 4 f.
- They travel his short path, 141 px from below-right of the drop point to it (his "CAMINHO CURSOR 2": it sets off
  to the left and curves up into the drop), in 54 f on his curve (0.42, 0, 0.1235, 1): it leaves already moving,
  peaks a quarter of the way and settles slowly. 141 px is at a 1340 px hero; another width scales it.
- Hand and file grow from 90 % to 100 % on the way (his two curves: x (0.4587, 0, 0.0608, 1) in 53 f, y
  (0.42, 0, 0.2339, 1) in 54 f).
- The hand opens at S + 48/49 (a 1-frame swap), 5 f before it stops; the file shrinks to 82 % from S + 47 to S + 58
  on (1, 0, 0.97, 0.964); the open hand and the file fade out from S + 54 to S + 58.
- zone (the input's drop highlight, drawn by the piece, hidden at rest): in over S..S+9 (his v05.2 request: the
  fade token), out over S+49..S+61, linear.
- result (what the drop puts in the input: the file's thumbnail, a chip): in as the Migration Page v05 does it, its
  opacity over S+56..S+82 (linear) and its scale 125 % -> 100 % over S+57..S+127 on (0, 0.74, 0.199, 1).

When to use which (LEARNINGS 19): a file, an image or a screenshot that comes from outside the frame already held,
into an input or a drop area: a.drop_file (this). Picking up something that is on screen (a widget in the panel, a
card, a row) and carrying it somewhere: a.drag / a.drop_widget (19.1: the cursor goes to it, takes it, lifts it).
"""
import copy
import math
import os

import kit
from kit import El
from common import FPS, _el

ART_OPEN = os.path.join(kit.ART, "hand_open.svg")
ART_HELD = os.path.join(kit.ART, "hand_held.svg")
REF_W = 1340.0

THROW = dict(
    fade=4,                                          # hand + file fade in (his 175 -> 179)
    path=(130.22705, 54.768559, 48.261711),          # his path: start - drop (px), the start vertex's handle
    ride=(54, (0.42, 0.0, 0.12348623, 1.0)),         # 175 -> 229, his cubicValue (0.42, 1, 0.1235, 0) on 1 -> 0
    grow_x=(0.9, 0.99949938, 53, (0.458745, 0.0, 0.060822655, 1.0)),
    grow_y=(0.9, 1.0, 54, (0.42, 0.0, 0.2338827, 1.0)),
    open=48,                                         # closed -> open over 48 -> 49 (his 223 -> 224)
    shrink=(47, 58, 0.82, (1.0, 0.0, 0.97017199, 0.96443045)),   # his 222 -> 233, 0.3333 -> 0.2733
    gone=(54, 58),                                   # the open hand and the file fade (his 229 -> 233)
    zone_in=(0, 9), zone_out=(49, 61),               # Migration Page v05.2 (his request; his own: 0 -> 4)
    result=dict(fade=(56, 82), scale=(57, 127, 1.25, (0.0, 0.74, 0.199, 1.0))),   # Migration Page v05, 79 -> 150
    hand=1.25,                                       # the open hand's height / the arrow's (v05.4: 0.56 at 1.05)
    hold=0.203,                                      # the hand's centre above the file's bottom edge, x its height
    held_off=(0.807, 4.5),                           # the held hand's centre from the open one's (his PNG px)
)
OPEN_VB, HELD_VB = (61.0, 62.0), (56.0, 52.0)       # the traced SVGs' viewBoxes (his PNGs' pixels)
ARROW_H = 26.5


def _F(n):
    return n / FPS


class ThrowActions:
    """a.drop_file (mixed into Actions)."""

    def drop_file(self, file, into=None, at=None, t=None, zone=None, result=(), side="right", dist=None):
        """The motion designer's file thrown into an input (module doc; LEARNINGS 19.3). `file`: an item the piece
        drew anywhere (an image, a card): it is the model and stays hidden; a copy travels in the hand. into: the
        item whose centre the file's centre lands on (an input, its drop area), or at=(x, y). t: when the hand shows
        (default now). zone: the drop highlight (an item, hidden at rest) that shows while the file comes. result:
        items the drop puts in the input (hidden at rest), in from S + 56. side: "right" (from below-right, his) or
        "left" (mirrored). dist: the path's length in px instead of his 141 (at a 1340 px hero). It is the scene's
        cursor (one cursor per scene, LEARNINGS 3): what comes after in this scene happens without one. Returns the
        frame time the hand opens; `now` moves to when hand and file are gone (S + 58)."""
        assert into is not None or at is not None, "drop where? (into=an item, or at=(x, y))"
        p, c, T = self.p, self.c, THROW
        if self.visit is not None:          # the arrow on screen leaves first (a thrown file comes from outside)
            self.cursor_out()
            self.notes.append("drop_file: the cursor on screen vanished first (the file comes in held, from outside)")
        S = round(self._t(t) * FPS)
        self._throws = getattr(self, "_throws", 0) + 1
        name = f"THROW{self._throws}"
        fd = S + T["ride"][0]
        D = at if at is not None else p.point(into, None, _F(fd))
        k = (dist / math.hypot(*T["path"][:2])) if dist else p.w / REF_W
        sx = 1.0 if side == "right" else -1.0
        S0 = (D[0] + sx * T["path"][0] * k, D[1] + T["path"][1] * k)
        c1 = (S0[0] - sx * T["path"][2] * k, S0[1])
        # the path, start -> drop (his runs drop -> start with the distance going 1 -> 0: the same curve)
        verts = [El("CubicDetachedVertex", {"x": round(S0[0], 3), "y": round(S0[1], 3), "inRotation": 0.0,
                                            "inDistance": 0.0, "outRotation": math.atan2(c1[1] - S0[1], c1[0] - S0[0]),
                                            "outDistance": math.dist(c1, S0)}),
                 El("CubicDetachedVertex", {"x": round(D[0], 3), "y": round(D[1], 3), "inRotation": 0.0,
                                            "inDistance": 0.0, "outRotation": 0.0, "outDistance": 0.0})]
        path = El("Shape", {"x": 0, "y": 0}, [El("PointsPath", {"isClosed": False}, verts, name=f"{name}.pathpts")],
                  name=f"{name}.path")
        self._add(p.overlay, path)
        # the file's copy, centred on the node
        x, y, w, h = p.bounds(file, 0)
        src = _el(file)
        names = set()
        kit.walk(src, lambda e: names.add(e.name) if e.name else None)
        cp = copy.deepcopy(src)
        pre = f"{name}.f."

        def ren(e):
            if e.name:
                e.name = pre + e.name
            for kk, v in list(e.attrs.items()):
                if isinstance(v, str) and v.startswith("@") and v[1:] in names:
                    e.attrs[kk] = "@" + pre + v[1:]
        kit.walk(cp, ren)
        st = next((ch for ch in cp.children if isinstance(ch, El) and ch.tag == "LayoutComponentStyle"), None)
        if st is not None:
            st.attrs.update({"positionTypeValue": "absolute", "positionLeft": 0, "positionTop": 0})
        cp.attrs.update({"width": w, "height": h, "x": None, "y": None, "opacity": None})
        if src.tag == "Image":
            cp.attrs.update({"x": 0, "y": 0})
            held = El("Node", {}, [cp], name=f"{name}.file.at")
        else:
            held = El("Node", {"x": -w / 2, "y": -h / 2}, [cp], name=f"{name}.file.at")
        shrink = El("Node", {}, [held], name=f"{name}.file")
        # the hand: open and held, at the file's bottom edge, in the middle
        sh = T["hand"] * ARROW_H * p.cursor_scale / OPEN_VB[1]        # px per his PNG px
        ho = h / 2 - T["hold"] * OPEN_VB[1] * sh
        open_ = kit.icon(ART_OPEN, f"{name}.open.art", kit.WHITE, x=-OPEN_VB[0] * sh / 2, y=-OPEN_VB[1] * sh / 2,
                         size=OPEN_VB[0] * sh)
        held_ = kit.icon(ART_HELD, f"{name}.held.art", kit.WHITE, x=-HELD_VB[0] * sh / 2, y=-HELD_VB[1] * sh / 2,
                         size=HELD_VB[0] * sh)
        n_open = El("Node", {"x": 0, "y": ho, "opacity": 0.0}, [open_], name=f"{name}.open")
        n_held = El("Node", {"x": T["held_off"][0] * sh, "y": ho + T["held_off"][1] * sh}, [held_],
                    name=f"{name}.held")
        grow = El("Node", {"scaleX": T["grow_x"][0], "scaleY": T["grow_y"][0]}, [n_open, n_held, shrink],
                  name=f"{name}.grow")
        node = El("Node", {"x": 0, "y": 0, "opacity": 0.0},
                  [grow, El("FollowPathConstraint", {"targetId": f"@{name}.path", "orient": False, "distance": 0.0},
                            name=f"{name}.follow")], name=name)
        self._add(p.overlay, node, first=True)
        c.set(0, _el(file).name, "opacity", 0.0)                       # the model never shows
        # ---- the ride
        n_ride, e_ride = T["ride"]
        c.move(_F(S), f"{name}.follow", "distance", 1.0, _F(n_ride), list(e_ride))
        c.move(_F(S), name, "opacity", 1.0, _F(T["fade"]), "linear")
        g0x, g1x, nx, ex = T["grow_x"]
        g0y, g1y, ny, ey = T["grow_y"]
        c.move(_F(S), f"{name}.grow", "scaleX", g1x, _F(nx), list(ex))
        c.move(_F(S), f"{name}.grow", "scaleY", g1y, _F(ny), list(ey))
        # ---- the drop: the hand opens, the file shrinks, both go
        fo = S + T["open"]
        c.set(_F(fo + 1), f"{name}.held", "opacity", 0.0)          # a hard swap (hold keys): his 223 -> 224
        c.set(_F(fo + 1), f"{name}.open", "opacity", 1.0)
        a0, a1, s1, es = T["shrink"]
        for ax in ("scaleX", "scaleY"):
            c.move(_F(S + a0), f"{name}.file", ax, s1, _F(a1 - a0), list(es))
        g0, g1 = T["gone"]
        c.move(_F(S + g0), f"{name}.open", "opacity", 0.0, _F(g1 - g0), "linear")
        c.move(_F(S + g0), f"{name}.file", "opacity", 0.0, _F(g1 - g0), "linear")
        if zone is not None:
            zn = _el(zone).name
            c.set(0, zn, "opacity", 0.0)
            c.move(_F(S + T["zone_in"][0]), zn, "opacity", 1.0, _F(T["zone_in"][1] - T["zone_in"][0]), "linear")
            c.move(_F(S + T["zone_out"][0]), zn, "opacity", 0.0, _F(T["zone_out"][1] - T["zone_out"][0]), "linear")
        R = T["result"]
        r0, r1, sc, er = R["scale"]
        for it in self._list(result):
            el = _el(it)
            rn = el.name
            c.set(0, rn, "opacity", 0.0)
            c.move(_F(S + R["fade"][0]), rn, "opacity", 1.0, _F(R["fade"][1] - R["fade"][0]), "linear")
            for ax in ("scaleX", "scaleY"):
                s1 = float(el.attrs.get(ax) or 1.0)
                c.set(_F(S + R["fade"][0]), rn, ax, s1 * sc)      # (still hidden: the loop starts as it ends)
                c.move(_F(S + r0), rn, ax, s1, _F(r1 - r0), list(er))
            if not any(isinstance(ch, El) and ch.tag == "ComponentOrigin" for ch in el.children):
                _, _, rw, rh = p.bounds(it, _F(S + r0))      # it grows from its top-left: keep its centre put
                for ax, d in (("x", rw), ("y", rh)):
                    b = c.base(rn, ax)
                    c.set(_F(S + R["fade"][0]), rn, ax, b + (1 - sc) * d / 2)
                    c.move(_F(S + r0), rn, ax, b, _F(r1 - r0), list(er))
        self._cursor_scene_used(_F(S))
        self._note(_F(S), f"drop_file {getattr(file, 'key', name)} (his header: {math.dist(S0, D):.0f} px in "
                          f"{n_ride} f, opens at +{T['open']})")
        self.now = _F(S + g1)
        return _F(fo)
