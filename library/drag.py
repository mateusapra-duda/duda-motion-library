"""v12: pick and drop (Mateus's recipe of 2026-11-13, motion-spec/LEARNINGS.md 19.1; references
reference/exemplos-mateus/exemplo-de-widget-drop.rev = REF 1 and exemplo-de-drop-widget-2actions.rev = REF 2).

The rule for any pick and drop: the arrow turns into the closed hand on the frame it takes the thing (a hard swap, no
press scale: the closed hand is the press) and the hand vanishes where it lets go (2 frames, to 0). The thing itself
follows the cursor (its place stays empty), lifts and casts a soft shadow, and on the drop it shrinks a little and
fades. Path and curves of REF 2 up to the grab, REF 1 from there on.

  p.drop_slot(name, new)       where a widget dropped into a site opens: a zero-height room in the site's column,
                               holding the new section (cut by the opening) and the blue line
  a.drag(item, to=None, at=None, plus=None, panel=None, over=None)
                               the generic gesture: a cursor of its own comes in already moving, (clicks `plus`, the
                               panel slides in,) grabs `item`, drags it to `to` / `at`, drops it
  a.drop_widget(card, slot, site=..., panel=..., plus=None, intro=[...])
                               the whole recipe: the drag, the site making room, the section opening from the line,
                               its intro; close_up=True: the rare cut to the close-up
"""
import bisect
import copy
import math
import os

import kit
from kit import El
from common import FPS, HOVER_LEAD, Item

BLUE = "#2A84EE"
HAND = os.path.join(kit.ART, "hand_grab.svg")
ARROW_H = 26.5                  # the library Cursor's arrow, tip to tail
HAND_H = 1.15 * ARROW_H         # the closed hand, ~1.15x the arrow (REF 1)
HAND_VB = (73.0, 78.0)          # hand_grab.svg's viewBox

# The recipe's numbers, frames at 60 fps (motion-spec/LEARNINGS.md 19.1)
DRAG = dict(
    appear=2,                                                  # the cursor fades in while it already moves
    to_plus=(37, 172, [0.379, 0.0, 0.246, 1.0]),               # REF 2: frames, path length, curve
    panel_in=(42, [0.8, 0.0, 0.2, 1.0]),                       # the panel slides in from behind the left bar
    to_card=(93, 408, 52, 0.67, [0.478, 0.0, 0.346, 0.817], [0.777, 0.347, 0.299, 1.0]),   # two legs, one speed
    to_card_open=(28, 195, [0.0, 0.0, 0.175, 1.0]),           # REF 1: the panel already open
    hold=3,                                                    # still after the grab
    lift=(8, -6.5, -7.0, [0.0, 0.0, 0.0, 1.0]),                # up and left
    shadow=dict(fade_in=10, fade_out=7, blur=20, x=4, y=4, color="#0000001A"),
    drag=(88, [0.596, 0.0, 0.152, 1.0]),                       # out horizontally, an arc, lands vertically
    badge=dict(size=21, fade=2),                               # the blue "+" when the card is over the site
    shrink=(10, 0.9, [0.736, 0.0, 1.0, 1.0]), fade_last=5, vanish=2,
)
ROOM = dict(
    close=(58, [0.551, 0.0, 0.151, 1.0]),                      # the panel closes, the site follows and scrolls
    scroll=124,
    push=(33, 50, [0.637, 0.0, 0.338, 1.0]),                   # the section below goes down
    line=(3.7, 4, 24),                                         # thickness, fade-in frames, frames before the drop
    open=(60, [0.8, 0.0, 0.2, 1.0]), side=54,                  # from inside the line; +54 px each side
    outline_out=(27, 4),                                       # the blue outline fades mid-opening
    intro=dict(at=27, rise=40, dur=50, ease=[0.0, 0.0, 0.205, 1.0], fade=5, part=4, item=12, image_fade=12,
               image_drift=(150, 1.06, [0.0, 0.0, 0.148, 1.0])),
)
CLOSE_UP = dict(scale=2.1, hold=70, after=51, ease=[0.0, 0.0, 0.0, 0.92], line=(30, 7),
                back=(1.07, 58, [0.0, 0.0, 0.0, 1.0]))


def F(n):
    return n / FPS


def _fr(t):
    return int(round(t * FPS))


def _bez(p0, c1, c2, p3, t):
    u = 1 - t
    return tuple(u ** 3 * p0[k] + 3 * u * u * t * c1[k] + 3 * u * t * t * c2[k] + t ** 3 * p3[k] for k in (0, 1))


def _ease(e, x):
    """y of a normalised cubic ease at x."""
    x1, y1, x2, y2 = e
    lo, hi = 0.0, 1.0
    for _ in range(40):
        s = (lo + hi) / 2
        bx = 3 * (1 - s) ** 2 * s * x1 + 3 * (1 - s) * s * s * x2 + s ** 3
        lo, hi = (s, hi) if bx < x else (lo, s)
    s = (lo + hi) / 2
    return 3 * (1 - s) ** 2 * s * y1 + 3 * (1 - s) * s * s * y2 + s ** 3


def _bulge(a, b, amount, up=True):
    """A cubic from a to b whose middle bows `amount` x the chord off it (up=True: toward the top of the frame)."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    nx, ny = -dy, dx
    if (ny > 0) == up and ny != 0:
        nx, ny = -nx, -ny
    k = amount * 4 / 3          # a cubic's middle sits at 3/4 of its handles' offset
    return (a, (a[0] + dx / 3 + nx * k, a[1] + dy / 3 + ny * k), (a[0] + 2 * dx / 3 + nx * k, a[1] + 2 * dy / 3 + ny * k), b)


def _unit(v):
    d = math.hypot(*v) or 1.0
    return (v[0] / d, v[1] / d)


class _Path:
    """One path for the whole gesture, as the approved cursors are made: cubic legs [(p0, c1, c2, p3)]."""

    def __init__(self, legs):
        self.legs = legs
        self.lens, self.pts, self.ends = [0.0], [legs[0][0]], []
        total, prev = 0.0, legs[0][0]
        for leg in legs:
            for i in range(1, 401):
                q = _bez(*leg, i / 400)
                total += math.dist(prev, q)
                self.lens.append(total)
                self.pts.append(q)
                prev = q
            self.ends.append(total)
        self.total = total

    def frac(self, i):
        """The share of the path at the end of leg i."""
        return self.ends[i] / self.total

    def at(self, d):
        s = d * self.total
        i = min(max(bisect.bisect_left(self.lens, s), 1), len(self.lens) - 1)
        l0, l1 = self.lens[i - 1], self.lens[i]
        k = 0.0 if l1 == l0 else (s - l0) / (l1 - l0)
        p0, p1 = self.pts[i - 1], self.pts[i]
        return (p0[0] + (p1[0] - p0[0]) * k, p0[1] + (p1[1] - p0[1]) * k)

    def shape(self, name):
        verts, n = [], len(self.legs)
        for i in range(n + 1):
            p = self.legs[i][0] if i < n else self.legs[-1][3]
            a = {"x": round(p[0], 3), "y": round(p[1], 3)}
            for k, h in (("in", self.legs[i - 1][2] if i > 0 else None), ("out", self.legs[i][1] if i < n else None)):
                if h is None or math.dist(h, p) < 1e-6:
                    a[f"{k}Rotation"], a[f"{k}Distance"] = 0.0, 0.0
                else:
                    a[f"{k}Rotation"] = math.atan2(h[1] - p[1], h[0] - p[0])
                    a[f"{k}Distance"] = math.dist(h, p)
            verts.append(El("CubicDetachedVertex", a))
        return El("Shape", {"x": 0, "y": 0}, [El("PointsPath", {"isClosed": False}, verts, name=f"{name}.pathpts")],
                  name=f"{name}.path")


def _style_of(el):
    return next((c for c in el.children if isinstance(c, El) and c.tag == "LayoutComponentStyle"), None)


class DragPatterns:
    """Piece helpers (mixed into Piece)."""

    def drop_slot(self, name, new, line_w=None, color=BLUE, line=None):
        """Where a widget dropped into a site opens (a.drop_widget): put it in the site's column between the two
        sections. It starts 0 high (the site looks untouched); it holds `new`, the section the widget becomes (cut by
        the opening, so it only shows from the drop), and the blue line (`color`, ~3.7 px) the width of the site's
        content: `line_w` (default: the section's width - 108, so the opening, +54 px each side, ends on its edges)."""
        th = ROOM["line"][0] if line is None else line
        n = f"{self.art}.{name}"
        outline = kit.absolute(f"{n}.line", paints=[kit.line(f"{n}.line.stroke", kit.hex_argb(color), th)],
                               inset=(th / 2,) * 4, opacity=0.0)
        opening = kit.box(f"{n}.open", [outline, _el(new)], w=line_w or 100, h=0, clip=True,
                          layoutWidthScaleType="fixed", layoutHeightScaleType="fixed", layoutAlignmentType="center",
                          flexDirectionValue="column")
        # a 1-px mark on the slot's top edge: what the measure reads (the slot's own bounds take in the section
        # that overflows it)
        mark = kit.absolute(f"{n}.mark", inset=(0, 0, 0, None), layoutHeightScaleType="fixed")
        mark.attrs["height"] = 1
        self.items[f"{name}.mark"] = Item(self, f"{name}.mark", "box", mark)
        item = self._box(name, [mark, opening], "column", 0, 0, "center", "fill", 0)
        item.kind = "dropslot"
        item.mark = self.items[f"{name}.mark"]
        item.open, item.outline, item.new, item.line_w, item.thick = f"{n}.open", f"{n}.line", new, line_w, th
        return item


def _el(x):
    return x.wrap if isinstance(x, Item) else x


class DragActions:
    """Actions (mixed into Actions)."""

    # ------------------------------------------------------------ the cursor of a drag
    def _grab_cursor(self, name):
        p = self.p
        hw = HAND_H * HAND_VB[0] / HAND_VB[1]
        hand = kit.icon(HAND, f"{name}.hand.art", kit.WHITE, x=4.8 - hw / 2, y=0.0, size=hw)
        hand_n = El("Node", {"opacity": 0.0}, [hand], name=f"{name}.hand")
        nest = El("NestedArtboard", {"artboardId": "@art.cursor", "dataBindPathIds": (
            f"vm.{p.key}", f"vm.{p.key}.cursor")}, [El("NestedStateMachine", {"animationId": "@sm.cursor"},
                                                        name=f"{name}.machine")], name=f"{name}.art")
        follow = El("FollowPathConstraint", {"targetId": f"@{name}.path", "orient": False}, name=f"{name}.follow")
        node = El("Node", {"x": 0, "y": 0, "opacity": 0, "scaleX": p.cursor_scale, "scaleY": p.cursor_scale},
                  [hand_n, nest, follow], name=name)
        return node

    def _add(self, parent, el, first=False):
        if first:
            parent.children.insert(0, el)
        else:
            parent.children.append(el)
        self.c.parent[id(el)] = parent

        def reg(e):
            if e.name:
                self.c.by[e.name] = e
            for k in e.children:
                if isinstance(k, El):
                    self.c.parent[id(k)] = e
        kit.walk(el, reg)

    def _ghost(self, name, card, box, tip, radius):
        """The card that follows the cursor: a copy of `card` (its own place empties), with its shadow and badge,
        held by the cursor (a Translation constraint, as in REF 1)."""
        x, y, w, h = box
        src = _el(card)
        names = set()
        kit.walk(src, lambda e: names.add(e.name) if e.name else None)
        cp = copy.deepcopy(src)
        pre = f"{name}.c."

        def ren(e):
            if e.name:
                e.name = pre + e.name
            for k, v in list(e.attrs.items()):
                if isinstance(v, str) and v.startswith("@") and v[1:] in names:
                    e.attrs[k] = "@" + pre + v[1:]
        kit.walk(cp, ren)
        st = _style_of(cp)
        if st is not None:
            for k in list(st.attrs):
                if k.startswith(("position", "margin")):
                    del st.attrs[k]
            st.attrs["layoutWidthScaleType"] = st.attrs["layoutHeightScaleType"] = "fixed"
            # out of the flow: a layout under a plain Node still joins the artboard's root layout, and in the flow it
            # would take room there and push the whole scene aside
            st.attrs.update({"positionTypeValue": "absolute", "positionLeft": 0, "positionTop": 0})
        cp.attrs.update({"width": w, "height": h, "x": None, "y": None, "opacity": None})
        sh = DRAG["shadow"]
        shadow = kit.shadow_layers(f"{name}.shadow", [{"x": sh["x"], "y": sh["y"], "blur": sh["blur"],
                                                       "color": sh["color"]}], radius)
        for s in shadow:
            s.attrs["opacity"] = 0.0
        bs = DRAG["badge"]["size"]
        plus = [kit.absolute(f"{name}.badge.{k}", paints=[kit.solid(f"{name}.badge.{k}.fill", kit.WHITE)],
                             inset=ins, layoutWidthScaleType="fixed", layoutHeightScaleType="fixed")
                for k, ins in (("h", (bs / 2 - 4.5, bs / 2 - 0.85, None, None)),
                               ("v", (bs / 2 - 0.85, bs / 2 - 4.5, None, None)))]
        plus[0].attrs.update({"width": 9, "height": 1.7})
        plus[1].attrs.update({"width": 1.7, "height": 9})
        badge = kit.absolute(f"{name}.badge", plus, paints=[kit.solid(f"{name}.badge.fill", kit.hex_argb(BLUE))],
                             inset=(None, 2 - bs / 2, 2 - bs / 2, None), opacity=0.0, origin=(0.5, 0.5),
                             layoutWidthScaleType="fixed", layoutHeightScaleType="fixed", cornerRadiusTL=bs / 2)
        badge.attrs.update({"width": bs, "height": bs})
        i = next((j for j, k in enumerate(cp.children) if isinstance(k, El) and k.tag not in (
            "LayoutComponentStyle", "ComponentOrigin", "Fill", "Stroke")), len(cp.children))
        cp.children[i:i] = [badge]          # on top
        cp.children += shadow               # at the bottom
        at = El("Node", {"x": -w / 2, "y": -h / 2}, [cp], name=f"{name}.at")
        sc = El("Node", {"x": w / 2, "y": h / 2}, [at], name=f"{name}.scale")
        lift = El("Node", {}, [sc], name=f"{name}.lift")
        ghost = El("Node", {"x": x - tip[0], "y": y - tip[1], "opacity": 0.0},
                   [lift, El("TranslationConstraint", {"targetId": f"@{name}", "offset": True, "strength": 1.0},
                             name=f"{name}.hold")], name=f"{name}.ghost")
        self._add(self.p.fx, ghost, first=True)
        return dict(ghost=ghost.name, lift=lift.name, scale=sc.name, badge=badge.name,
                    shadow=[s.name for s in shadow])

    @staticmethod
    def _radius(card):
        st = _style_of(_el(card))
        r = st.attrs.get("cornerRadiusTL") if st is not None else None
        return float(r) if r else 8.0

    def _drag(self, item, t, plus, panel, over, where, target, cut=False, badge=True):
        """The gesture. target(t_drop, (ox, oy, w, h)) gives where the cursor's tip lets go, from the card centre's
        offset to the tip (lift included) and its size. Returns its times and names."""
        p, c = self.p, self.c
        if self.visit is not None:
            self.cursor_out()
        self._grabs = getattr(self, "_grabs", 0) + 1
        name = f"GRAB{self._grabs}"
        f0 = _fr(self._t(t))
        node = self._grab_cursor(name)
        self._add(p.overlay, node, first=True)
        D = DRAG
        # ---- times
        if plus is not None:
            fP = f0 + D["to_plus"][0]
            fG = fP + 1 + D["to_card"][0]
        else:
            fP, fG = None, f0 + D["to_card_open"][0]
        fS = fG + D["hold"]
        fE = fS + D["drag"][0]
        fD = fE - 1
        # ---- the panel slides in at the click on "+"
        pw = p.bounds(panel, 0)[2] if panel is not None else 0.0
        if plus is not None and panel is not None:
            pn = _el(panel).name
            c.track(pn, "x").keys[0]["v"] = c.base(pn, "x") - pw
            c.move(F(fP + 1), pn, "x", c.base(pn, "x"), F(D["panel_in"][0]), D["panel_in"][1])
        # ---- where
        box = p.bounds(item, F(fG))
        G = p.point(item, where, F(fG))
        if plus is not None:
            P = p.point(plus, None, F(fP))
            S = (P[0] + D["to_plus"][1] * 0.69, P[1] + D["to_plus"][1] * 0.72)
            legs = [_bulge(S, P, 0.12, up=False), _bulge(P, G, 0.06, up=True)]
        else:
            S = (G[0] + D["to_card_open"][1] * 0.85, G[1] + D["to_card_open"][1] * 0.53)
            legs = [_bulge(S, G, 0.08, up=True)]
        lx, ly = D["lift"][1], D["lift"][2]
        off = (box[0] + box[2] / 2 - G[0] + lx, box[1] + box[3] / 2 - G[1] + ly, box[2], box[3])
        T = target(F(fD), off)
        dx, dy = T[0] - G[0], T[1] - G[1]
        if abs(dy) > 20:     # out horizontally, an arc, landing vertically
            legs.append((G, (G[0] + 0.55 * dx, G[1]), (T[0], T[1] - 0.55 * dy), T))
        else:
            legs.append(_bulge(G, T, 0.1, up=True))
        path = _Path(legs)
        self._add(p.overlay, path.shape(name))
        # ---- the ride: distance keys, few and only where it stops or where one curve hands over to the next
        fl = f"{name}.follow"
        dG = path.frac(len(legs) - 2)
        if plus is not None:
            n1, _, f1, share, e1, e2 = D["to_card"]
            dP = path.frac(0)
            c.move(F(f0), fl, "distance", dP, F(D["to_plus"][0]), D["to_plus"][2])
            dM = dP + share * (dG - dP)
            c.move(F(fP + 1), fl, "distance", dM, F(f1), e1)
            c.move(F(fP + 1 + f1), fl, "distance", dG, F(n1 - f1), e2)
            c.click(F(fP - 1), name)                  # an ordinary press on "+" (0.85, 3 + 3 frames)
            self._reacts(plus, F(fP), press=True)
            if plus.vm is not None and "selected" in {n for n, _, _ in plus.vm.props}:
                self._key(F(fP), plus, "selected", True)
        else:
            c.move(F(f0), fl, "distance", dG, F(D["to_card_open"][0]), D["to_card_open"][2])
        n_drag, e_drag = D["drag"]
        fc = None
        if cut:     # the rare close-up: cut at the drag's peak speed, then it slows down to the drop
            k = max(range(1, n_drag), key=lambda i: _ease(e_drag, i / n_drag) - _ease(e_drag, (i - 1) / n_drag))
            fc = fS + k
            dc = dG + (0.999 - dG) * _ease(e_drag, k / n_drag)
            # the first part on the standard curve, cut where it is fastest (its keys: one curve split in two)
            c.move(F(fS), fl, "distance", dc, F(k), _split(e_drag, k / n_drag))
            fD = fc + CLOSE_UP["after"]
            fE = fD + 1
            c.move(F(fc), fl, "distance", 0.999, F(fE - fc), CLOSE_UP["ease"])
        else:
            c.move(F(fS), fl, "distance", 0.999, F(n_drag), e_drag)
        # ---- the cursor: shows already moving, the hand on the grab, vanishes where it lets go
        c.move(F(f0), name, "opacity", 1.0, F(D["appear"]), "linear")
        c.set(F(fG), f"{name}.art", "opacity", 0.0)
        c.set(F(fG), f"{name}.hand", "opacity", 1.0)
        c.move(F(fD), name, "opacity", 0.0, F(D["vanish"]), "linear")
        vm_props = {n for n, _, _ in item.vm.props} if isinstance(item, Item) and item.vm else set()
        if "hover" in vm_props:             # the widget's hover as the cursor gets there
            self._key(F(fG) - HOVER_LEAD, item, "hover", True)
            self._key(F(fG + D["lift"][0]), item, "hover", False)
        # ---- the card: a copy follows the cursor, the original's place empties
        g = self._ghost(name, item, box, G, self._radius(item))
        c.set(F(fG), _el(item).name, "opacity", 0.0)
        c.set(F(fG), g["ghost"], "opacity", 1.0)
        nl, _, _, el_ = D["lift"]
        c.move(F(fG), g["lift"], "x", lx, F(nl), el_)
        c.move(F(fG), g["lift"], "y", ly, F(nl), el_)
        sh = D["shadow"]
        for s in g["shadow"]:
            c.move(F(fG), s, "opacity", 1.0, F(sh["fade_in"]), "linear")
            c.move(F(fD - 3), s, "opacity", 0.0, F(sh["fade_out"]), "linear")
        # ---- over the drop area: the blue "+" badge (elastic 0.7 -> 1 in 10 frames)
        edge = None          # where the card passes from the panel into the drop area
        if panel is not None:
            bx = p.bounds(panel, F(fG))
            edge = bx[0] + bx[2]
        elif over is not None:
            edge = p.bounds(over, F(fG))[0]
        fX = fS + 22
        if edge is not None:
            for f in range(fS, fE + 1):
                d = dG + (0.999 - dG) * _ease(e_drag, (f - fS) / n_drag) if fc is None or f <= fc else 0.999
                if path.at(d)[0] + off[0] + off[2] / 2 > edge:     # the card's right edge, where the badge is
                    fX = f
                    break
        if badge:
            b = g["badge"]
            c.move(F(fX), b, "opacity", 1.0, F(D["badge"]["fade"]), "linear")
            for ax in ("scaleX", "scaleY"):
                c.set(F(fX), b, ax, 0.7)
                c.move(F(fX + 1), b, ax, 1.12, F(4), [0.2, 0.6, 0.4, 1.0])
                c.move(F(fX + 5), b, ax, 0.97, F(3), [0.4, 0.0, 0.6, 1.0])
                c.move(F(fX + 8), b, ax, 1.0, F(2), [0.4, 0.0, 0.6, 1.0])
        # ---- the drop: it shrinks to 90 % and fades in the last 5 frames
        ns, s1, es = D["shrink"]
        for ax in ("scaleX", "scaleY"):
            c.move(F(fD - 1), g["scale"], ax, s1, F(ns), es)
        c.move(F(fD - 1 + ns - D["fade_last"]), g["ghost"], "opacity", 0.0, F(D["fade_last"]), "linear")
        self._note(F(fD - 1 + ns), f"drag {_el(item).name}: grab {F(fG):.2f}s, drop {F(fD):.2f}s")
        return dict(name=name, start=f0, plus=fP, grab=fG, drag=fS, cross=fX, drop=fD, end=fE, cut=fc, tip=T,
                    box=box, pw=pw)

    # ------------------------------------------------------------ actions
    def drag(self, item, to=None, t=None, at=None, plus=None, panel=None, over=None, where=None, badge=None):
        """Pick `item` up and drop it on `to` (an item: the card's centre lands on its centre) or `at` (x, y): the
        rule for any pick and drop (Mateus, 2026-11-13). A cursor of its own comes in already moving (the one on
        screen leaves first): with `plus` (and `panel`), it first clicks "+" and the panel slides in from behind the
        left bar (REF 2); then it goes to `item` and takes it: the arrow turns into the closed hand (a hard swap),
        3 frames still, the copy that follows the cursor lifts up-left with a soft shadow, the place stays empty.
        It drags out horizontally, arcs and lands vertically (88 frames); over `over` (default: past the panel) a
        blue "+" badge pops on the card (badge=False: none). On the drop the card shrinks to 90 % and fades, the
        hand vanishes there. Returns the drop time; `now` moves to it."""
        assert to is not None or at is not None, "drag where? (to=an item, or at=(x, y))"

        def target(td, off):
            if at is not None:
                cx, cy = at
            else:
                cx, cy = self.p.point(to, None, td)
            return (cx - off[0], cy - off[1])
        info = self._drag(item, t, plus, panel, over, where, target,
                          badge=(over is not None or panel is not None) if badge is None else badge)
        self.last_drag = info
        self.now = F(info["drop"] + DRAG["vanish"])
        return F(info["drop"])

    def drop_widget(self, card, slot, site=None, panel=None, plus=None, t=None, slide=None, scroll=None,
                    intro=(), close_up=False, fit=True, where=None):
        """Mateus's recipe (LEARNINGS 19.1): drag a widget from the side panel into the site. `card` the widget in
        the panel, `slot` a p.drop_slot in the site's column, `site` the site's content (it scrolls inside its
        view), `panel` the widget panel, `plus` the "+" that opens it (then the panel starts closed, behind the left
        bar). The drag as a.drag; when the card gets over the site, the panel closes and the site scrolls ~124 px in
        58 frames (slide: the site also moves left the panel's width, REF 1, when it sits beside the panel; default
        when there's no `plus`); the section below goes down 33 px; 24 frames before the drop the blue line shows
        where the widget goes. On the drop the new section opens from inside the line (it grows to the section's
        height and 54 px each side, cutting the section, 1 s on (0.8, 0, 0.2, 1)), the site scrolling with it so the
        section ends at the top of the view (fit=False: no extra scroll); the outline fades mid-opening. `intro`:
        the section's items in reading order (an item, or a tuple of its parts 4 frames apart; 12 frames between
        items), each rising 40 px with a 5-frame fade from 27 frames after the drop; an image fades in 12 frames
        and settles slowly. close_up=True: the rare variation, a cut to the close-up (2.1x) at the drag's peak
        speed and back (107 % -> 100 %). Returns the drop time; `now` moves to the end of the intro."""
        p, c, R = self.p, self.c, ROOM
        assert getattr(slot, "kind", None) == "dropslot", "slot: a p.drop_slot(...)"
        scroll = R["scroll"] if scroll is None else scroll
        slide = plus is None if slide is None else slide
        pw = p.bounds(panel, 0)[2] if panel is not None else 0.0
        # the section and the line, at rest
        nx, ny, nw, nh = p.bounds(slot.new, 0)
        line_w = slot.line_w or max(40.0, nw - 2 * R["side"])
        c.track(slot.open, "width").keys[0]["v"] = float(line_w)
        c.by[slot.open].attrs["width"] = line_w
        sx, sy, sw, _ = p.bounds(slot.mark, 0)
        push = R["push"][0]
        lcx = sx + sw / 2 - (pw if slide and panel is not None else 0.0)
        lcy = sy - scroll + push / 2

        def target(td, off):     # the card lands centred on the line, its bottom 10 px above it
            return (lcx - off[0], lcy - 10 - off[3] / 2 - off[1])
        info = self._drag(card, t, plus, panel, site, where, target, cut=close_up)
        self.last_drag = info
        fX, fD = info["cross"], info["drop"]
        # ---- the panel closes, the site follows and scrolls
        nc, ec = R["close"]
        f1 = min(fX - 3, fD - nc)          # done before the drop (the drop scrolls the site again)
        if panel is not None:
            pn = _el(panel).name
            c.move(F(f1), pn, "x", c.now(pn, "x", F(f1)) - pw, F(nc), ec)
        if plus is not None and plus.vm and "selected" in {n for n, _, _ in plus.vm.props}:
            self._key(F(f1), plus, "selected", False)
        if site is not None:
            sn = _el(site).name
            if slide and panel is not None:
                c.move(F(f1), sn, "x", c.base(sn, "x") - pw, F(nc), ec)
            c.move(F(f1), sn, "y", c.base(sn, "y") - scroll, F(nc), ec)
        # ---- the section below makes room, the blue line shows where it goes
        c.move(F(min(fX + 2, fD - R["push"][1])), _el(slot).name, "height", float(push), F(R["push"][1]), R["push"][2])
        th, nfade, before = R["line"]
        fl = fD - before
        c.set(F(fl), slot.open, "height", float(th))
        if close_up:
            rise, nf = CLOSE_UP["line"]
            c.set(F(fl), slot.open, "y", c.base(slot.open, "y") + rise)
            c.move(F(fl + 1), slot.open, "y", c.base(slot.open, "y"), F(nf), [0.0, 0.0, 0.205, 1.0])
            c.move(F(fl), slot.outline, "opacity", 1.0, F(nf), "linear")
        else:
            c.move(F(fl), slot.outline, "opacity", 1.0, F(nfade), "linear")
        # ---- the drop: the section opens from inside the line
        no, eo = R["open"]
        c.move(F(fD), _el(slot).name, "height", float(nh), F(no), eo)
        c.move(F(fD), slot.open, "height", float(nh), F(no), eo)
        c.move(F(fD), slot.open, "width", float(line_w + 2 * R["side"]), F(no), eo)
        oa, of = R["outline_out"]
        c.move(F(fD + oa), slot.outline, "opacity", 0.0, F(of), "linear")
        if site is not None and fit:     # the site scrolls with it: the section ends at the top of the view
            top = p.bounds(site, 0)[1]
            extra = max(0.0, (sy - scroll) - top)
            if extra:
                c.move(F(fD), sn, "y", c.base(sn, "y") - scroll - extra, F(no), eo)
        # ---- the close-up (rare): a cut at the drag's peak speed, ~70 frames at 2.1x, back to 107 % -> 100 %
        if close_up:
            self._close_up(info["cut"], (lcx, lcy))
        # ---- the intro of the new section
        I = R["intro"]
        f = fD + I["at"]
        end = fD + no
        for entry in intro:
            parts = entry if isinstance(entry, (list, tuple)) else [entry]
            for j, it in enumerate(parts):
                fi = f + j * I["part"]
                n = _el(it).name
                c.track(n, "opacity").keys[0]["v"] = 0.0
                if getattr(it, "kind", None) == "image":
                    c.move(F(fi), n, "opacity", 1.0, F(I["image_fade"]), "linear")
                    img = next((k.name for k in _el(it).children if isinstance(k, El) and k.tag == "Image"), None)
                    nd, s0, ed = I["image_drift"]
                    if img:
                        for ax in ("scaleX", "scaleY"):
                            c.set(F(fi), img, ax, s0)
                            c.move(F(fi + 1), img, ax, 1.0, F(nd), ed)
                    end = max(end, fi + 1 + nd)
                else:     # 40 px below and hidden from the start (no jump), it rises into place
                    y0 = c.base(n, "y")
                    c.track(n, "y").keys[0]["v"] = y0 + I["rise"]
                    c.move(F(fi), n, "y", y0, F(I["dur"]), I["ease"])
                    c.move(F(fi), n, "opacity", 1.0, F(I["fade"]), "linear")
                    end = max(end, fi + I["dur"])
            f += I["item"]
        self._note(F(end), f"drop_widget {_el(card).name} -> {_el(slot).name}")
        self.now = F(end)
        return F(fD)

    def _close_up(self, fc, at):
        """The rare cut to the close-up: the scene at 2.1x around the drop for ~70 frames, then a hard cut back to
        the open shot at 107 %, settling to 100 % in 58 frames on (0, 0, 0, 1). A camera over the whole artboard."""
        p, c, C = self.p, self.c, CLOSE_UP
        cam = p.camera_node()
        W, H = p.w, p.h
        s = C["scale"]
        x, y = W / 2 - s * at[0], H / 2 - s * at[1]
        x = min(0.0, max(W - s * W, x))
        y = min(0.0, max(H - s * H, y))
        for prop, v in (("scaleX", s), ("scaleY", s), ("x", x), ("y", y)):
            c.set(F(fc), cam, prop, v)
        fb = fc + C["hold"]
        sb, nb, eb = C["back"]
        for prop, v0, v1 in (("scaleX", sb, 1.0), ("scaleY", sb, 1.0), ("x", W / 2 * (1 - sb), 0.0),
                             ("y", H / 2 * (1 - sb), 0.0)):
            c.set(F(fb), cam, prop, v0)
            c.move(F(fb + 1), cam, prop, v1, F(nb), eb)


def _split(e, k):
    """The first part of cubic ease `e` up to x=k, as a normalised cubic (de Casteljau on the curve's
    parameter that gives x=k), so the cut part keeps the standard curve's shape."""
    x1, y1, x2, y2 = e
    lo, hi = 0.0, 1.0
    for _ in range(50):
        s = (lo + hi) / 2
        bx = 3 * (1 - s) ** 2 * s * x1 + 3 * (1 - s) * s * s * x2 + s ** 3
        lo, hi = (s, hi) if bx < k else (lo, s)
    s = (lo + hi) / 2
    p0, p1, p2, p3 = (0.0, 0.0), (x1, y1), (x2, y2), (1.0, 1.0)
    lerp = lambda a, b: (a[0] + (b[0] - a[0]) * s, a[1] + (b[1] - a[1]) * s)   # noqa: E731
    a1, b1 = lerp(p0, p1), lerp(p1, p2)
    a2 = lerp(a1, b1)
    c1 = lerp(p2, p3)
    b2 = lerp(b1, c1)
    end = lerp(a2, b2)
    sx, sy = end
    return [a1[0] / sx, a1[1] / sy, a2[0] / sx, a2[1] / sy]
