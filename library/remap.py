"""remap.py (v15): the piece as nested artboards on time remaps, so the motion designer can slide, swap or retime a
scene or an element in the Rive editor by moving two keys instead of hundreds.

p.build(..., remap={...}) builds the piece as always (one choreography, the lints, the checks), then rewrites
scene.rml in this structure (the frames stay the same):

  MAIN           the frame: its background, "State Machine 1" (layer "Main": play / tabChange), the view model, and ONE
                 "Timeline" that only plays the scenes:
                 - "Scenes", a Solo holding one nest per scene: only the active one draws. Its "active" property has a
                   hold key where each scene takes over (the cut frame): that is the scene's in point (and the last
                   one's out point);
                 - per scene, "<scene> time" (0 -> 1, linear, from the frame before the scene shows to the frame the
                   next one takes over): drag both keys to move the scene, bring them closer to speed it up;
                 - the cursor visits that cross from one scene to another (see the cursor rule), over everything.
    <scene>      one artboard per scene: a copy of the piece with only what shows in its stretch (its screens, its
                 cursor visits, its effects), its own "Timeline" from 0 with its keys, and the drivers of the
                 components it shows. A scene is cut at each a.cut (or at the times given).
      <element>  inside a scene, each item asked for: an artboard the item's size, nested in the item's place (it
                 moves with its screen), with its own "Timeline" from the frame before it first changes to its last
                 change: its keys, its drivers and its Generation effects. The scene plays it by remap: "<element>
                 time" in the scene's Timeline.

    remap = {"scenes": ["Home", "Settings"]}            one scene per stretch between two a.cut (cuts + 1 names)
            {"scenes": [("Intro", 0), ("Editor", 3.2)]} or the second each scene starts
            {"scenes": [("Intro", 0), ("Editor", 3.2, 0.5)]}   ... with an overlap: both draw for 0.5 s (a
                                                        crossfade of your own; the library's cuts don't overlap)
            {"scenes": None}                            the whole piece as one scene: MAIN nests it (the
                                                        smooth-play wrap of ma-simplified-flow's wrapmain.py)
            "elements": {"Home": [card]}                items that get an artboard of their own, by scene; an
                                                        element sits in a p.free (x, y) or is a screen of a p.stack
            "cursor": "main" | "scene"                  an override of the cursor rule: every visit on MAIN, or
                                                        each visit copied into every scene it shows in

The cursor rule (per visit: one cursor_in ... cursor_out): a visit that shows inside one scene only lives in that
scene (it moves, and is retimed, with it); a visit that shows in more than one (it walks across a cut) or during an
overlap lives on MAIN, over the Solo, keyed on MAIN's Timeline. The build log says where each one went and why.

An overlap (two scenes drawn in the same frames): the Solo keeps the earlier scene through it and switches when it
ends; a second nest of the later scene, "<scene> (overlap)", outside the Solo, shows by opacity during the overlap
only (hold keys), with the same time keys (move "<scene> time" and "<scene> (overlap) time" together). What shows
during the overlap is drawn once: by the earlier scene if it showed before the overlap, else by the later one; what
shows on both sides of it is drawn by both there (the log names it). The overlap nest goes above or below the Solo as
the later scene's parts were in the flat build.

Timing (how the frames stay the same):
- a remap's `time` is a fraction of the nested Timeline: 0 at its first key, 1 at its last; the keys are exactly 0
  and 1 (no lead: a lead of 1/100 frame put ~100 hold keys a frame early in hero3-code v06);
- a scene's Time starts one frame before it shows, so on its first visible frame it has already been applied once
  (a remap whose time never left its first value showed the setup pose), and ends on the frame the next scene takes
  over (ending on its last visible frame held its motion there for a frame: up to 216/255 off in a slide cut);
- each remap's resting value is 0.0001 for the same reason (before MAIN's Timeline first runs);
- an element that never changes gets a 1-frame Timeline (a 0-frame one is not a timeline);
- the Solo's keys and the overlap's opacity are hold keys on MAIN's own Timeline: they land on the same frames as the
  flat build.

Not yet: a piece with live hovers (p.hoverable(live=True)): their listeners and layers sit on MAIN's state machine.

The key helpers (value at a frame, a curve cut in two) are ma-simplified-flow's scenes.py (2026-11-06).
"""
import copy
import os
import re
import xml.etree.ElementTree as ET

import numpy as np

from common import FPS

OPACITY, DISPLAY, REMAP_TIME, SOLO_ACTIVE = "18", "596", "202", "296"
DRAWN = {"Node", "LayoutComponent", "Shape", "Image", "Text", "NestedArtboard", "NestedArtboardLayout", "Solo"}
LAYOUT_PARENTS = {"Artboard", "LayoutComponent", "NestedArtboardLayout"}
STATIC_TIME = "0.0001"


# ------------------------------------------------------------------------- keys (from ma-simplified-flow scenes.py)
def _bez(p0, p1, p2, p3, u):
    a = [(1 - u) * x + u * y for x, y in zip(p0, p1)]
    b = [(1 - u) * x + u * y for x, y in zip(p1, p2)]
    c = [(1 - u) * x + u * y for x, y in zip(p2, p3)]
    d = [(1 - u) * x + u * y for x, y in zip(a, b)]
    e = [(1 - u) * x + u * y for x, y in zip(b, c)]
    s = [(1 - u) * x + u * y for x, y in zip(d, e)]
    return (p0, a, d, s), (s, e, c, p3)


def _u_at(p0, p1, p2, p3, t):
    lo, hi = 0.0, 1.0
    for _ in range(60):
        u = (lo + hi) / 2
        if _bez(p0, p1, p2, p3, u)[0][3][0] < t:
            lo = u
        else:
            hi = u
    return (lo + hi) / 2


class Key:
    """One keyframe: frame, value, how it goes to the next one, and a cubic's controls as absolute points."""

    def __init__(self, el, nxt):
        self.el, self.f = el, float(el.get("frame", 0))
        self.kind = el.tag
        self.interp = el.get("interpolationType", "hold")
        self.v = el.get("value", el.get("colorValue"))
        if self.kind == "KeyFrameDouble":
            self.v = float(self.v or 0)
        self.c = None
        sub = next(iter(el), None)
        if sub is not None and nxt is not None and self.kind == "KeyFrameDouble":
            v0, v1 = self.v, float(nxt.get("value", 0))
            x1, y1, x2, y2 = (float(sub.get(k)) for k in ("x1", "y1", "x2", "y2"))
            if sub.tag == "CubicEaseInterpolator":
                y1, y2 = v0 + y1 * (v1 - v0), v0 + y2 * (v1 - v0)
            self.c = ((0.0, v0), (x1, y1), (x2, y2), (1.0, v1))


def _color_lerp(a, b, t):
    a, b = int(a, 16), int(b, 16)
    return "".join(f"{round(((a >> s) & 255) * (1 - t) + ((b >> s) & 255) * t):02X}" for s in (24, 16, 8, 0))


def keys_of(kp):
    els = sorted((e for e in kp if e.tag.startswith("KeyFrame")), key=lambda e: float(e.get("frame", 0)))
    return [Key(e, els[i + 1] if i + 1 < len(els) else None) for i, e in enumerate(els)]


def value_at(keys, f):
    if f <= keys[0].f:
        return keys[0].v
    for a, b in zip(keys, keys[1:]):
        if a.f <= f < b.f:
            t = (f - a.f) / (b.f - a.f)
            if a.kind not in ("KeyFrameDouble", "KeyFrameColor") or a.interp in ("hold", "0"):
                return a.v
            if a.kind == "KeyFrameColor":
                return _color_lerp(a.v, b.v, t)
            if a.c is None:
                return a.v + (b.v - a.v) * t
            return _bez(*a.c, _u_at(*a.c, t))[0][3][1]
    return keys[-1].v


def _num(x):
    s = f"{x:.6f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def _key_el(proto, f, v, interp, ctrl, nid):
    e = ET.Element(proto.tag)
    e.set("frame", str(int(round(f))))
    e.set("value", _num(v) if isinstance(v, float) else str(v))
    if "interpolationType" in proto.attrib:
        e.set("interpolationType", "3" if ctrl else interp)
    e.set("id", nid())
    if ctrl:
        _, (x1, y1), (x2, y2), _ = ctrl
        ET.SubElement(e, "CubicValueInterpolator", {"x1": _num(x1), "y1": _num(y1), "x2": _num(x2), "y2": _num(y2),
                                                      "id": nid()})
    return e


def _norm(ctrl):
    (x0, v0), (x1, y1), (x2, y2), (x3, v3) = ctrl
    w = x3 - x0
    return (0.0, v0), ((x1 - x0) / w, y1), ((x2 - x0) / w, y2), (1.0, v3)


def trim(kp, lo, hi, nid):
    """KeyedProperty kp keeps only frames lo..hi, shifted to start at 0; a curve crossing an edge is cut there with
    the same motion (a cubic split at the edge, a line stays a line)."""
    keys = keys_of(kp)
    out = []
    if lo < keys[0].f:
        out.append((0.0, keys[0].v, "hold", None, keys[0].el, True))
    for i, k in enumerate(keys):
        nxt = keys[i + 1] if i + 1 < len(keys) else None
        a, b = k.f, (nxt.f if nxt else float("inf"))
        if b <= lo or a > hi:
            continue
        if a == hi:
            out.append((hi - lo, k.v, "hold", None, k.el, True))
            continue
        s, e = max(a, lo), min(b, hi)
        cut = s > a or (e < b and k.c is not None)
        ctrl = None
        if k.c and nxt and cut:
            piece = k.c
            if e < b:
                piece = _bez(*piece, _u_at(*piece, (e - a) / (b - a)))[0]
            if s > a:
                piece = _bez(*piece, _u_at(*piece, (s - a) / (b - a)))[1]
            ctrl = _norm(piece)
        out.append((s - lo, value_at(keys, s) if s > a else k.v, k.interp, ctrl, k.el, cut))
    if not out:
        out.append((0.0, keys[-1].v, "hold", None, keys[-1].el, True))
    last = out[-1]
    if last[2] not in ("hold", "0") and keys[-1].f > hi and last[0] < hi - lo:
        out.append((hi - lo, value_at(keys, hi), "hold", None, last[4], True))
    for el in [e for e in kp if e.tag.startswith("KeyFrame")]:
        kp.remove(el)
    for f, v, interp, ctrl, proto, cut in out:
        if cut:
            kp.append(_key_el(proto, f, v, interp, ctrl, nid))
        else:
            proto.set("frame", str(int(round(f))))
            kp.append(proto)


def _prop(kp):
    return kp.get("propertyKey") or kp.get("property")


# ------------------------------------------------------------------------- the flat piece, read once
class Source:
    def __init__(self, root, name):
        self.root = root
        self.art = next(a for a in root if a.tag == "Artboard" and a.get("name") == name)
        self.tl = next(x for x in self.art if x.tag == "LinearAnimation" and x.get("name") == "Timeline")
        self.F = int(self.tl.get("duration"))
        self.up = {c: p for p in self.art.iter() for c in p}
        self.byid = {e.get("id"): e for e in self.art.iter() if e.get("id")}
        self.byname = {e.get("name"): e for e in self.art.iter() if e.get("name")}
        self.tracks = {}       # (object id, property) -> keys
        for ko in self.tl:
            for kp in ko:
                self.tracks[(ko.get("objectId"), _prop(kp))] = keys_of(kp)
        self.vis, self.disp, self.ink = {}, {}, {}
        self._visibility(self.art, np.ones(self.F + 1, bool))

    def series(self, oid, prop, static):
        keys = self.tracks.get((oid, prop))
        if not keys:
            return [static] * (self.F + 1)
        return [value_at(keys, f) for f in range(self.F + 1)]

    def _visibility(self, el, parent):
        """vis[id]: the frames el is shown (it and every group above it opaque and displayed); disp[id]: the frames
        its own layout style is displayed (display none takes it out of the layout); ink[id]: the frames something
        in it paints (a text, an image, a nested artboard, a shape or box with a fill or a stroke). Returns ink."""
        ink_all = np.zeros(self.F + 1, bool)
        for ch in el:
            i = ch.get("id")
            if ch.tag not in DRAWN or not i:
                continue
            op = np.array([float(v) > 0.001 for v in self.series(i, OPACITY, float(ch.get("opacity", 1)))])
            d = np.ones(self.F + 1, bool)
            st = ch.get("styleId")
            if st and st in self.byid:
                d = np.array([str(v) != "1" for v in self.series(st, DISPLAY, self.byid[st].get("displayValue", "0"))])
            self.disp[i] = d
            self.vis[i] = parent & op & d
            paints = ch.tag in ("Text", "Image", "NestedArtboard", "NestedArtboardLayout") or any(
                k.tag in ("Fill", "Stroke") for k in ch)
            ink = self._visibility(ch, self.vis[i]) | (self.vis[i] if paints else False)
            self.ink[i] = ink
            ink_all |= ink
        return ink_all

    def changes(self, ids, lo, hi):
        """The frames in lo+1..hi where any keyed property of these objects changes."""
        out = set()
        for (oid, _), keys in self.tracks.items():
            if oid in ids:
                prev = value_at(keys, lo)
                for f in range(lo + 1, hi + 1):
                    v = value_at(keys, f)
                    if v != prev:
                        out.add(f)
                    prev = v
        return out


def _subtree_ids(el):
    return {x.get("id") for x in el.iter() if x.get("id")}


def _participates(el, style):
    """el takes room in its parent's layout (taking it out would move what is around it)."""
    if el.tag == "LayoutComponent":
        return style is None or style.get("positionTypeValue") != "absolute"
    if el.tag == "NestedArtboardLayout":
        return True
    return any(k.tag == "LayoutParticipant" for k in el)


def _copy_with_ids(el, prefix):
    """A deep copy with ids prefix:1, prefix:2...; references inside it follow (ma-simplified-flow scenes.py)."""
    c = copy.deepcopy(el)
    n, ids = [0], {}
    for x in c.iter():
        if x.get("id"):
            n[0] += 1
            ids[x.get("id")] = f"{prefix}:{n[0]}"
    for x in c.iter():
        for k, v in x.attrib.items():
            if k == "id":
                x.set(k, ids[v])
            elif v in ids:
                x.set(k, ids[v])
            elif "-" in v and any(q in ids for q in v.split("-")):
                x.set(k, "-".join(ids.get(q, q) for q in v.split("-")))
    return c, ids


class _Ids:
    def __init__(self, prefix):
        self.prefix, self.n = prefix, 0

    def __call__(self):
        self.n += 1
        return f"{self.prefix}:{self.n}"


def _keys_el(parent, oid, prop, keys, nid):
    """A KeyedObject with one property: keys = [(frame, value, interp)]."""
    ko = ET.SubElement(parent, "KeyedObject", {"objectId": oid, "id": nid()})
    kp = ET.SubElement(ko, "KeyedProperty", {"propertyKey": prop, "id": nid()})
    for f, v, it in keys:
        a = {"frame": str(f), "value": str(v)}
        if it:
            a["interpolationType"] = it
        a["id"] = nid()
        ET.SubElement(kp, "KeyFrameDouble", a)
    return ko


def _remap_keys(parent, remap_id, t0, t1, nid):
    keys = [(t0, 0, "linear"), (t1, 1, "hold")] if t1 > t0 else [(t0, 0, "hold")]
    return _keys_el(parent, remap_id, REMAP_TIME, keys, nid)


def _id_keys(parent, oid, prop, keys, nid):
    """A KeyedObject with one id property (a Solo's active child): keys = [(frame, id)], hold."""
    ko = ET.SubElement(parent, "KeyedObject", {"objectId": oid, "id": nid()})
    kp = ET.SubElement(ko, "KeyedProperty", {"propertyKey": prop, "id": nid()})
    for f, v in keys:
        ET.SubElement(kp, "KeyFrameId", {"frame": str(f), "value": v, "interpolationType": "hold", "id": nid()})
    return ko


def _paints(el):
    return el.tag in ("Text", "Image", "NestedArtboard", "NestedArtboardLayout") or any(
        k.tag in ("Fill", "Stroke") for k in el)


# ------------------------------------------------------------------------- the split
def _scenes(piece, spec):
    """names, start frames, overlap frames (the first scene: 0, 0)."""
    scenes = spec.get("scenes", None)
    if scenes is None:
        return [piece.art.title() if piece.art != "MAIN" else "Piece"], [0], [0]
    if all(isinstance(s, str) for s in scenes):
        st = piece.a.__dict__.get("_cut_st") or {"cuts": []}
        cuts = [rec["fc"] for rec in st["cuts"]]
        assert len(cuts) == len(scenes) - 1, (f"remap: {len(scenes)} scenes need {len(scenes) - 1} a.cut, the piece "
                                              f"has {len(cuts)} (or give each scene its start: (name, s))")
        return list(scenes), [0] + cuts, [0] * len(scenes)
    names = [s[0] for s in scenes]
    starts = [round(s[1] * FPS) for s in scenes]
    ovs = [round(s[2] * FPS) if len(s) > 2 else 0 for s in scenes]
    assert starts[0] == 0 and ovs[0] == 0, "remap: the first scene starts at 0, with no overlap"
    for k in range(1, len(names)):
        assert starts[k] > starts[k - 1] + ovs[k - 1], (f"remap: {names[k]} starts before {names[k - 1]} has taken "
                                                        f"over (its start, plus its overlap)")
    return names, starts, ovs


def _above(up, a, b):
    """Element a draws above element b in the flat build (the first child draws on top; a child above its parent)."""
    pa, pb = [a], [b]
    while pa[-1] in up:
        pa.append(up[pa[-1]])
    while pb[-1] in up:
        pb.append(up[pb[-1]])
    if a in pb:
        return False
    if b in pa:
        return True
    common = next(x for x in pa if x in pb)
    ca, cb = pa[pa.index(common) - 1], pb[pb.index(common) - 1]
    kids = list(common)
    return kids.index(ca) < kids.index(cb)


def split(piece, spec):
    """Rewrite piece.here/scene.rml as MAIN > Solo of scenes > elements (see the module docstring). Returns the
    report lines."""
    path = os.path.join(piece.here, "scene.rml")
    text = open(path).read()
    tree = ET.ElementTree(ET.fromstring(text))
    root = tree.getroot()
    src = Source(root, piece.art)
    F = src.F
    used = {int(m) for m in re.findall(r'id="(\d+):', text)}
    free = (p for p in range(50, 1000) if p not in used)
    override = spec.get("cursor")
    assert override in (None, "auto", "main", "scene"), 'remap: "cursor" is "main" or "scene" (an override)'
    names, starts, ovs = _scenes(piece, spec)
    n = len(names)
    report, notes = [], []

    # ---- the windows (MAIN frames). Scene k shows from its start s; the Solo has it from on = s + its overlap (the
    # overlap nest draws it before that) to the frame before the next one's `on`; its "core" is the stretch only it
    # draws. Its Timeline runs from the frame before it shows to the frame the next one takes over.
    win = []
    for k in range(n):
        s, on = starts[k], starts[k] + ovs[k]
        nxt_s = starts[k + 1] if k + 1 < n else F + 1
        nxt_on = starts[k + 1] + ovs[k + 1] if k + 1 < n else F + 1
        win.append(dict(name=names[k], start=s, on=on, ov=ovs[k], core=(on, nxt_s - 1), pre=(s, on - 1),
                        show=(s, min(nxt_on - 1, F)), tl=(max(s - 1, 0), min(nxt_on, F)),
                        out=nxt_on if k + 1 < n else None))

    art = src.art
    cursors = src.byname.get(f"{piece.art}.cursors")
    effects = src.byname.get(f"{piece.art}.effects")
    drivers = next((x for x in art if x.tag == "CustomPropertyGroup" and x.get("name") == "Drivers"), None)

    def inks(i, rng):
        a, b = rng
        return b >= a and bool(src.ink[i][a:b + 1].any())

    # ---- the cursor rule, per visit: in the one scene it shows in, else on MAIN (over the Solo)
    units, partner, place = [], {}, {}       # visit ids, visit -> the ids it needs (its path), visit -> k | "main"
    if cursors is not None:
        kids = [c for c in cursors if c.tag in DRAWN and c.get("id")]
        for c in kids:
            if not src.ink[c.get("id")].any():
                continue
            units.append(c)
            refs = {v for x in c.iter() for v in x.attrib.values() if v in src.byid}
            partner[c.get("id")] = set().union(*[_subtree_ids(p) for p in kids if p.get("id") in refs]) \
                if refs else set()
        units.sort(key=lambda c: int(np.flatnonzero(src.ink[c.get("id")])[0]))
        for c in units:
            i = c.get("id")
            fr = np.flatnonzero(src.ink[i])
            a, b = int(fr[0]), int(fr[-1])
            inside = [k for k in range(n) if win[k]["core"][0] <= a and b <= win[k]["core"][1]]
            shown = [win[k]["name"] for k in range(n) if inks(i, win[k]["show"])]
            if override == "main":
                place[i], why = "main", "the cursor override"
            elif override == "scene":
                place[i], why = "scenes", "the cursor override: a copy in each scene it shows in"
            elif inside:
                place[i], why = inside[0], f"all its frames are inside {win[inside[0]]['name']}"
            else:
                cut = next((w["start"] for w in win[1:] if a < w["start"] <= b), None)
                lap = [w for w in win[1:] if w["ov"] and inks(i, w["pre"])]
                place[i] = "main"
                why = (f"it shows during the overlap into {lap[0]['name']}" if lap else
                       f"it crosses from {shown[0]} to {shown[-1]} (the cut at frame {cut})")
            where = "MAIN" if place[i] == "main" else ("its scenes" if place[i] == "scenes" else win[place[i]]["name"])
            report.append(f"  cursor {c.get('name')}: frames {a}-{b} -> {where} ({why})")
    main_cursor_ids = set()
    for c in units:
        if place[c.get("id")] == "main":
            main_cursor_ids |= _subtree_ids(c) | partner[c.get("id")]
    not_in = [set() for _ in range(n)]       # the visits (and paths) each scene leaves out
    for c in units:
        i = c.get("id")
        for k in range(n):
            if place[i] != "scenes" and place[i] != k:
                not_in[k] |= {i} | {p for p in partner[i] if p in src.vis}

    # ---- what each scene keeps: everything that paints in its stretch; what doesn't paint goes when that can't move
    # anything else (out of a layout, absolutely placed, or not displayed). In an overlap, a part is drawn by the
    # earlier scene if it showed before it, else by the later one.
    def keep_for(k):
        w = win[k]
        prev = win[k - 1]["core"] if k else None
        keep = set()

        def walk(el):
            for ch in el:
                i = ch.get("id")
                if ch.tag not in DRAWN or not i or i in not_in[k]:
                    continue
                shows = inks(i, w["core"]) or (w["ov"] and inks(i, w["pre"]) and not inks(i, prev))
                st = src.byid.get(ch.get("styleId"))
                a, b = w["show"]
                in_flow = (el.tag in LAYOUT_PARENTS and _participates(ch, st) and bool(src.disp[i][a:b + 1].any()))
                if shows or in_flow:
                    keep.add(i)
                    walk(ch)
        walk(art)
        # what a kept part points at stays (a cursor's path, a clip's source)
        while True:
            more = set()
            for i in list(keep):
                el = src.byid[i]
                for v in [v for x in [el] + [c for c in el if c.tag not in DRAWN] for v in x.attrib.values()]:
                    if v in src.byid and v not in keep and src.byid[v].tag in DRAWN:
                        more |= _subtree_ids(src.byid[v]) & set(src.vis)
                        e = src.up.get(src.byid[v])
                        while e is not None and e is not art:
                            more.add(e.get("id"))
                            e = src.up.get(e)
            more -= keep
            if not more:
                return keep
            keep |= more
    keeps = [keep_for(k) for k in range(n)]

    # ---- the elements: items with an artboard of their own, in their scene
    elems = []      # dicts: scene index, name, el id, holder id, box, owned fx ids, driver ids
    for k, w in enumerate(win):
        for item in (spec.get("elements") or {}).get(w["name"], []):
            el = src.byname[item.wrap.name]
            i = el.get("id")
            assert i in keeps[k], f"remap: element {item.key!r} doesn't show in scene {w['name']!r}"
            holder = src.up[el]
            hst = src.byid.get(holder.get("styleId"))
            drawn = [c for c in holder if c.tag in DRAWN]
            assert holder.tag == "LayoutComponent" and hst is not None and hst.get("positionTypeValue") == \
                "absolute" and drawn == [el], (f"remap: element {item.key!r} must sit alone in a p.free slot (x, y) "
                                               f"or be a screen of a p.stack (a flex layout would move around it)")
            a, b = w["show"]
            f_vis = next((f for f in range(a, b + 1) if src.vis[i][f]), a)
            box = piece.bounds(item, f_vis / FPS)
            elems.append(dict(k=k, name=item.key[:1].upper() + item.key[1:], el=el, id=i, holder=holder, box=box,
                              sub=_subtree_ids(el), fx=set(), drv=set()))

    # Generation effects go with the element they cover (each square's centre inside its box) in the scene they play
    # in (all their keys inside its stretch)
    if effects is not None:
        for g in [x for x in effects if x.tag in DRAWN]:
            cs = [(float(s.get("x", 0)), float(s.get("y", 0))) for s in g if s.tag == "Shape" and any(
                p.tag in ("Fill", "Stroke") for p in s)]
            if not cs:
                continue
            best = None
            moves = src.changes(_subtree_ids(g), 0, F)     # it plays in the element's scene, not just over its place
            for e in elems:
                lo, hi = win[e["k"]]["tl"]
                if g.get("id") not in keeps[e["k"]] or not moves or not all(lo < f <= hi for f in moves):
                    continue
                x, y, bw, bh = e["box"]
                if all(x - 1 <= cx <= x + bw + 1 and y - 1 <= cy <= y + bh + 1 for cx, cy in cs):
                    if best is None or bw * bh < best["box"][2] * best["box"][3]:
                        best = e
            if best is not None:
                best["fx"].add(g.get("id"))
                for k in range(n):      # it is the element's: no copy of it (done, see-through) in the other scenes
                    if k != best["k"]:
                        keeps[k] -= _subtree_ids(g)
        for k in range(n):
            if not any(x.get("id") in keeps[k] for x in effects if x.tag in DRAWN):
                keeps[k].discard(effects.get("id"))

    # ---- the drivers: each with the scene (or element, or MAIN's cursor) showing the component it drives
    owner = {}      # driver id -> ("scene", k) | ("elem", index) | ("main",)
    comps = [(x.get("dataBindPathIds"), x.get("id")) for x in art.iter() if x.get("dataBindPathIds")]
    for d in (list(drivers) if drivers is not None else []):
        ctx = next((x for x in d if x.tag == "DataBindContext"), None)
        pathv = ctx.get("sourcePathIds", "") if ctx is not None else ""
        slot = "-".join(pathv.split("-")[:2])
        cids = {cid for p, cid in comps if p == slot}
        if cids & main_cursor_ids:
            owner[d.get("id")] = ("main",)      # it drives a cursor visit that lives on MAIN
            continue
        homes = [k for k in range(n) if cids & keeps[k]]
        ch = src.changes({d.get("id")}, 0, F)
        if len(homes) > 1:
            homes = [k for k in homes if all(win[k]["tl"][0] < f <= win[k]["tl"][1] for f in ch)]
        if len(homes) != 1:
            owner[d.get("id")] = ("main",)
            notes.append(f"{d.get('name')} stays on MAIN's Timeline (its component shows in "
                         f"{'no' if not homes else 'more than one'} scene)")
            continue
        k = homes[0]
        lost = sorted(f for f in ch if not win[k]["tl"][0] < f <= win[k]["tl"][1])
        if lost:
            notes.append(f"{d.get('name')} goes with {win[k]['name']}: its change(s) at frame(s) "
                         f"{', '.join(map(str, lost))} fall outside it, where its component no longer shows")
        e = next((j for j, e in enumerate(elems) if e["k"] == k and cids & e["sub"]), None)
        owner[d.get("id")] = ("elem", e) if e is not None else ("scene", k)
        if e is not None:
            elems[e]["drv"].add(d.get("id"))

    # ---- each element's span (MAIN frames, inside its scene's Timeline): from the frame before it first changes
    # to its last change; a still one gets one frame
    for e in elems:
        lo, hi = win[e["k"]]["tl"]
        fx_ids = set().union(*[_subtree_ids(src.byid[g]) for g in e["fx"]]) if e["fx"] else set()
        ch = src.changes(e["sub"] | fx_ids | e["drv"], lo, hi)
        s = max(min(ch) - 1, lo) if ch else lo
        t = max(ch) if ch else s + 1
        e.update(span=(s, max(t, s + 1)), fx_ids=fx_ids)

    # ---- the overlaps: which way the later scene's nest goes (above or below the Solo), what both draw
    laps = {}
    for k in range(1, n):
        w = win[k]
        if not w["ov"]:
            continue
        a, b = w["pre"]

        def painting(ids):
            return [src.byid[i] for i in ids if i in src.ink and _paints(src.byid[i]) and inks(i, (a, b))]
        inc = painting(keeps[k] - keeps[k - 1])
        out = painting(keeps[k - 1] - keeps[k])
        both = painting(keeps[k] & keeps[k - 1])
        up_votes = sum(_above(src.up, x, y) for x in inc[:60] for y in out[:60])
        votes = len(inc[:60]) * len(out[:60])
        above = up_votes * 2 >= votes
        laps[k] = above
        line = (f"  overlap {win[k - 1]['name']} -> {w['name']}: frames {a}-{b} both draw; \"{w['name']} (overlap)\" "
                f"shows there (opacity 1 at {a}, 0 at {b + 1}) {'above' if above else 'below'} the Solo, which "
                f"switches to {w['name']} at frame {w['on']}; move \"{w['name']} time\" and \"{w['name']} (overlap) "
                f"time\" together")
        report.append(line)
        if votes and 0 < up_votes < votes:
            notes.append(f"overlap {w['name']}: {votes - up_votes if above else up_votes} of {votes} pairs of parts "
                         f"were the other way round in the flat build (the nest goes {'above' if above else 'below'})")
        if both:
            notes.append(f"overlap {w['name']}: {len(both)} part(s) show on both sides of it and are drawn by both "
                         f"scenes there ({', '.join(x.get('name') for x in both[:3])}"
                         f"{'...' if len(both) > 3 else ''}): a see-through one doubles")

    # ---- build the artboards: elements first (the scenes nest them by their final ids)
    W, H = int(float(art.get("width"))), int(float(art.get("height")))
    out_arts, comp_assets = [], []
    scene_nests = [[] for _ in range(n)]     # per scene: (element remap id, span)

    def timeline(keep_ids, lo, hi, nid, name="Timeline"):
        tl = ET.Element("LinearAnimation", {"fps": str(FPS), "duration": str(hi - lo), "name": name, "id": nid()})
        for ko in src.tl:
            if ko.get("objectId") in keep_ids:
                c = copy.deepcopy(ko)
                for kp in c:
                    trim(kp, lo, hi, nid)
                tl.append(c)
        return tl

    elem_report = []
    for j, e in enumerate(elems):
        k = e["k"]
        s, t = e["span"]
        nid = _Ids(next(free))
        x, y, bw, bh = e["box"]
        hx = float(src.byid[e["holder"].get("styleId")].get("positionLeft", 0))
        hy = float(src.byid[e["holder"].get("styleId")].get("positionTop", 0))
        ox, oy = x, y      # the holder's place on the board: the element's box (it sits at 0, 0 in a p.free slot)
        style = ET.Element("LayoutComponentStyle", {"name": f"{e['name']}Art.style", "id": nid()})
        ea = ET.Element("Artboard", {"isComponent": "true", "viewModelId": art.get("viewModelId"),
                                     "viewModelInstanceId": art.get("viewModelInstanceId"), "styleId": style.get("id"),
                                     "width": _num(bw), "height": _num(bh), "clip": "false",
                                     "x": str(j * 600), "y": str(2 * (H + 160)), "name": e["name"], "id": nid()})
        ea.append(style)
        ea.append(timeline(e["sub"] | e["fx_ids"] | e["drv"], s, t, nid))
        if e["drv"]:
            grp = ET.SubElement(ea, "CustomPropertyGroup", {"x": "0", "y": str(int(bh) + 40), "name": "Drivers",
                                                            "id": nid()})
            for d in drivers:
                if d.get("id") in e["drv"]:
                    grp.append(copy.deepcopy(d))
        if e["fx"]:
            fxn = ET.SubElement(ea, "Node", {"x": _num(-ox), "y": _num(-oy), "name": f"{e['name']}.effects",
                                             "id": nid()})
            for g in effects:
                if g.get("id") in e["fx"]:
                    fxn.append(copy.deepcopy(g))
        hold = copy.deepcopy(e["holder"])
        for c in list(hold):
            if c.tag in DRAWN:
                hold.remove(c)
        hold.set("name", f"{e['name']}.at")
        hst = copy.deepcopy(src.byid[e["holder"].get("styleId")])
        hst.set("positionLeft", "0")
        hst.set("positionTop", "0")
        hst.set("name", f"{e['name']}.at.style")
        hst.set("id", nid())
        hold.set("styleId", hst.get("id"))
        hold.set("id", nid())
        for c in list(hold):
            if c.tag == "LayoutComponentStyle":
                hold.remove(c)
        hold.insert(0, hst)
        hold.append(copy.deepcopy(e["el"]))
        ea.append(hold)
        ea2, _ = _copy_with_ids(ea, nid.prefix)
        tl_id = next(x for x in ea2 if x.tag == "LinearAnimation").get("id")
        out_arts.append(ea2)
        comp_assets.append((ea2.get("id"), e["name"]))
        e.update(art_id=ea2.get("id"), tl_id=tl_id, place=(hx, hy))
        elem_report.append(f"  element {e['name']} (in {win[k]['name']}): frames {s}-{t} of MAIN, "
                           f"{sum(1 for x in ea2.iter('KeyedObject'))} keyed objects, box {_num(bw)}x{_num(bh)}"
                           + (f", {len(e['fx'])} Generation effect(s)" if e["fx"] else "")
                           + (f", {len(e['drv'])} driver(s)" if e["drv"] else ""))

    nests, scene_report = [], []
    for k, w in enumerate(win):
        lo, hi = w["tl"]
        nid = _Ids(next(free))
        sa = copy.deepcopy(art)
        up = {c: p for p in sa.iter() for c in p}
        byid = {x.get("id"): x for x in sa.iter() if x.get("id")}
        for x in [x for x in sa if x.tag in ("StateMachine", "Fill") or (x.tag == "LinearAnimation" and
                                                                           x.get("name") != "Timeline")]:
            sa.remove(x)

        def drop(el):     # what this scene doesn't keep goes, with all it holds
            for x in list(el):
                if x.tag in DRAWN and x.get("id") in src.vis and x.get("id") not in keeps[k]:
                    el.remove(x)
                else:
                    drop(x)
        drop(sa)
        cur = byid.get(cursors.get("id")) if cursors is not None else None
        if cur is not None and cur in up and not any(x.tag in DRAWN for x in cur):
            up[cur].remove(cur)     # its visits all live elsewhere
        # the elements of this scene: each replaced by its nest, in its place
        mine = [e for e in elems if e["k"] == k]
        gone = set()
        for e in mine:
            el = byid[e["id"]]
            holder = up[el]
            ne = ET.Element("NestedArtboard", {"artboardId": e["art_id"], "x": "0", "y": "0", "name": e["name"],
                                               "id": nid()})
            rm = ET.SubElement(ne, "NestedRemapAnimation", {"animationId": e["tl_id"], "time": STATIC_TIME,
                                                            "name": f"{e['name']} time", "id": nid()})
            holder.insert(list(holder).index(el), ne)
            holder.remove(el)
            gone |= e["sub"]
            for g in e["fx"]:
                gx = byid[g]
                up[gx].remove(gx)
                gone |= _subtree_ids(gx)
            scene_nests[k].append((rm.get("id"), e["span"]))
        fxl = byid.get(effects.get("id")) if effects is not None else None
        if fxl is not None and fxl in up and not any(x.tag in DRAWN for x in fxl):
            up[fxl].remove(fxl)     # its effects all went with the elements
        # the drivers: only this scene's
        grp = next((x for x in sa if x.tag == "CustomPropertyGroup" and x.get("name") == "Drivers"), None)
        if grp is not None:
            for d in list(grp):
                if owner.get(d.get("id")) != ("scene", k):
                    grp.remove(d)
            if not len(grp):
                sa.remove(grp)
        left = {x.get("id") for x in sa.iter() if x.get("id")} - gone
        tl = next(x for x in sa if x.tag == "LinearAnimation")
        sa.remove(tl)
        tl2 = timeline(left, lo, hi, nid)
        tl2.set("id", tl.get("id"))
        for rid, (s, t) in scene_nests[k]:
            _remap_keys(tl2, rid, s - lo, t - lo, nid)
        sa.insert(1, tl2)
        sa.attrib.pop("defaultStateMachineId", None)
        attrs = {"isComponent": "true"}
        attrs.update(sa.attrib)
        sa.attrib.clear()
        sa.attrib.update(attrs)
        sa.set("name", w["name"])
        sa.set("x", str(k * (W + 200)))
        sa.set("y", str(H + 160))
        sa2, _ = _copy_with_ids(sa, nid.prefix)
        out_arts.insert(k, sa2)
        comp_assets.insert(k, (sa2.get("id"), w["name"]))
        nests.append((w, sa2.get("id"), next(x for x in sa2 if x.tag == "LinearAnimation").get("id")))
        objs = sum(1 for _ in sa2.iter())
        visits = [c.get("name") for c in units if c.get("id") in keeps[k]]
        scene_report.append(f"  scene {w['name']}: active in the Solo from frame {w['on']}"
                            + (f" (drawn from {w['start']} by its overlap nest)" if w["ov"] else "")
                            + f", Time {lo}-{hi}, {sum(1 for x in sa2.iter('KeyedObject'))} keyed objects, "
                            f"{objs:,} objects" + (f", {len(mine)} element(s)" if mine else "")
                            + (f", cursor {', '.join(visits)}" if visits else ""))

    # ---- MAIN: the background, the state machine, the view model, the cursor visits that cross scenes, the Solo
    nid = _Ids(next(free))
    keep_main = set()
    for x in [x for x in art if x.tag in DRAWN]:
        if x is cursors and main_cursor_ids:
            for c in [c for c in x if c.tag in DRAWN and c.get("id") not in main_cursor_ids]:
                x.remove(c)
            keep_main |= _subtree_ids(x)
            continue
        art.remove(x)
    if drivers is not None:
        for d in list(drivers):
            if owner.get(d.get("id")) != ("main",):
                drivers.remove(d)
            else:
                keep_main.add(d.get("id"))
        if not len(drivers):
            art.remove(drivers)
    for ko in list(src.tl):
        if ko.get("objectId") not in keep_main:
            src.tl.remove(ko)
    at = list(art).index(src.tl) + 1
    if drivers is not None and drivers in list(art):
        at = list(art).index(drivers) + 1
    if cursors is not None and cursors in list(art):
        at = list(art).index(cursors) + 1

    def nest(w, aid, tid, name, opacity=None):
        a = {"artboardId": aid, "x": "0", "y": "0"}
        if opacity is not None:
            a["opacity"] = opacity
        ne = ET.Element("NestedArtboard", dict(a, name=name, id=nid()))
        rm = ET.SubElement(ne, "NestedRemapAnimation", {"animationId": tid, "time": STATIC_TIME,
                                                        "name": f"{name} time", "id": nid()})
        _remap_keys(src.tl, rm.get("id"), w["tl"][0], w["tl"][1], nid)
        return ne

    if n == 1:
        w, aid, tid = nests[0]
        art.insert(at, nest(w, aid, tid, w["name"]))
    else:
        solo = ET.Element("Solo", {"name": "Scenes", "id": nid()})
        kids = [nest(w, aid, tid, w["name"]) for w, aid, tid in nests]
        for ne in kids:
            solo.append(ne)
        solo.set("activeComponentId", kids[0].get("id"))
        _id_keys(src.tl, solo.get("id"), SOLO_ACTIVE, [(w["on"], ne.get("id")) for (w, _, _), ne in
                                                       zip(nests, kids)], nid)
        above, below = [], []
        for k, (w, aid, tid) in enumerate(nests):
            if w["ov"]:
                ov = nest(w, aid, tid, f"{w['name']} (overlap)", opacity="0")
                _keys_el(src.tl, ov.get("id"), OPACITY, [(0, 0, "hold"), (w["start"], 1, "hold"),
                                                         (w["on"], 0, "hold")], nid)
                (above if laps[k] else below).append(ov)
        for ne in above[::-1] + [solo] + below:
            art.insert(at, ne)
            at += 1

    i = list(root).index(art) + 1
    for a in out_arts:
        root.insert(i, a)
        i += 1
    for aid, name in comp_assets:
        ET.SubElement(root, "ComponentAsset", {"artboardId": aid, "name": name, "id": nid()})
    ET.indent(tree, space="    ")
    xml = ET.tostring(root, encoding="unicode").replace(" />", "/>")
    open(path, "w", encoding="utf-8").write(xml + "\n")
    on_main = sum(1 for c in units if place[c.get("id")] == "main")
    head = (f"remap: MAIN plays {n} scene(s) by time remap"
            + f" ({', '.join(names)})"
            + (f", the Solo \"Scenes\" keyed at frame(s) {', '.join(str(w['on']) for w in win)}" if n > 1 else "")
            + f"; {len(elems)} element(s) in their own artboards; {len(units)} cursor visit(s), {on_main} on MAIN")
    return [head] + scene_report + elem_report + report + [f"  NOTE: {x}" for x in notes]
