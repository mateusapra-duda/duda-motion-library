"""checks.py (v14): build-time checks beyond the speed lints. Fast: they read the piece's tree, its timeline and the
scene.rml the build just wrote (and the layouts the build already measured); nothing is rendered.

    issues, notes = checks.run(p, a)     # p.build calls it right after the lints: issues fail the build

What each check looks at (its name in brackets; `checks.allow(name)` in a piece's build.py turns its issues into notes,
for an exception the motion designer approved):
- [rml] a loose `.rml` in the piece folder besides `scene.rml` (a copy of an old scene, a frozen version): the Rive CLI
  builds every `.rml` it finds, so the scene breaks (duplicate ids) without a clear message. ISSUE. Keep copies as
  `.rml.txt` (LEARNINGS 17).
- [weight] objects per artboard and vertices of the piece's own drawing (the library's components apart): the editor
  chokes on tens of thousands (LEARNINGS 14, 16: the marketing automation component played stuttering at 32k objects,
  fine at 2.5k; create-automation's MAIN froze at 66k). Note over 10k objects in one artboard or 8k vertices; ISSUE
  over 40k objects in one artboard.
- [outlines] text drawn as outlines (Figma's SVG draws every letter as a path): groups of 8 or more small closed paths.
  Note from 100 letters: use native text, one per line (LEARNINGS 16). A logo's few letters stay below it.
- [hidden] elements that never show (opacity 0, display none, a parent faded out) the whole timeline, and still cost:
  note, the biggest first.
- [offframe] placed items that sit outside the artboard (or outside the clipped box they are in) in every layout the
  build measured, and never move: note.
- [offscene] a screen (a part of 150+ objects) hidden by opacity for 1 s or more while it stays on (display): note,
  key it display none while hidden (LEARNINGS 16). The screens of an a.cut get it on their own (v14b).
- [layoutfade] the lints' blind spot: they multiply the opacity of Nodes, Shapes, Texts and Images only, so a fade on a
  layout box (a.enter, a.hide, a.show key the item's box) is invisible to them. Here the chain includes layout boxes:
  a speed over the cap while the box is faded out (a false OVER: not on screen) and a 'settle' (fast start) on
  something visible through its box (the lint misses it) are notes; a box held half-faded (5-95 %) for 0.5 s or more
  is a note too: Rive fades each layer of a group on its own, so what it covers shows through (LEARNINGS 16). The
  frames a.cut moves its own boxes in (its screens, edges and cascade, around each cut) are left out (v14b).
- [hairline] (v15e) a line under 1 px on screen (a stroke, or a painted box or rectangle that thin, times the scale of
  everything above it) that shows for 0.5 s or more while its scene zooms or slides slowly (0.02-2 px a frame): each
  frame it falls whole on a pixel row (bright) or across two (dim), a flicker a still never shows (LEARNINGS 12, 13;
  ma-novo-social v10). Note, with the fix: 1.5 px or more on screen with the opacity down in proportion (thickness x
  opacity the same), and the check: scripts/hairline.py renders ~30 frames and reads the line's brightness across
  them. a.cut's own frames are left out (brief); the inside of nested artboards (components, remap scenes) is not
  seen.
- [cursorstart] (v16) a cursor still when it shows: from its first visible frame, it must move 1.5 px a frame or more
  (at a 1340 px piece) within 0.15 s, the arrow, a drag's hand and a thrown file's hand alike (LEARNINGS 3; the blind
  review of 2026-11-26: "a mãozinha aparece parada"; his own file throw starts slow for 0.10 s, the library's cursor
  ~0.03 s, the round that drew the complaint 0.38 s). ISSUE: start it already on its way.
- [slim] what each image became in this build (lossy WebP for photos, lossless for sharp ones, kept as it was) and
  its size before and after: note (LEARNINGS 14; slim.QUALITY overrides one image).

Standalone, on any built piece (the scene-only checks: rml, weight, outlines):
    .venv/bin/python -I lib/<bundle>/checks.py pecas/<piece>
"""
import fnmatch
import os
import re
import sys
import xml.etree.ElementTree as ET

LIMITS = {
    "artboard_note": 10000,     # objects in one artboard (the library's components excluded)
    "artboard_issue": 40000,    # create-automation v01: 66k in MAIN, "mt travado"; manage-hero2's 20k page opened fine
    "verts_note": 8000,         # vertices of the piece's own drawing (~25k opened, but slowly)
    "letters_note": 100,        # letters drawn as outlines (marketing automation v06: 2,273, 92 % of its vertices)
    "screen_objects": 150,      # a "screen" for [offscene]
    "offscene_s": 1.0,
    "halffade_s": 0.5,
    "hairline_px": 1.0,         # on screen (LEARNINGS 13: under 1 px flickers in a zoom or a slow slide)
    "hairline_fix_px": 1.5,
    "slow_px": (0.02, 2.0),     # px a frame: moving, but slowly (a faster move blurs the flicker away)
    "hairline_s": 0.5,
    "cursor_slow_px": 1.5,      # px a frame at a 1340 px piece: under it the cursor reads as still
    "cursor_still_s": 0.15,     # his file throw: 0.10 s slow; the complaint: 0.30-0.38 s
}
EPS = 1 / 255                   # invisible
VERT = ("StraightVertex", "CubicDetachedVertex", "CubicMirroredVertex", "CubicAsymmetricVertex")
DRAWS = ("Shape", "Text", "Image", "NestedArtboardLayout", "NestedArtboard")
PAINTS = ("Fill", "Stroke")
LAYOUT = ("LayoutComponent", "NestedArtboardLayout")
ALLOWED = set()


def allow(*names):
    """Turn the issues of these checks into notes (an approved exception): checks.allow("weight")."""
    ALLOWED.update(names)


def run(piece, actions):
    """(issues, notes): issues fail the build, notes are printed."""
    out = {"issues": [], "notes": []}

    def report(check, text, issue=False):
        if issue and check not in ALLOWED:
            out["issues"].append(f"[{check}] {text}")
        else:
            out["notes"].append(f"[{check}] {text}" + (" (allowed)" if issue else ""))
    for fn in (loose_rml, weight):
        try:
            fn(piece.here, report)
        except Exception as e:   # a check must never break a build that is otherwise fine
            out["notes"].append(f"[checks] {fn.__name__} skipped: {e!r}")
    if actions is not None:
        try:
            Timeline(piece, actions).run(report)
        except Exception as e:
            out["notes"].append(f"[checks] timeline checks skipped: {e!r}")
    slim = sys.modules.get("slim")     # what each image became in this build (slim.photos fills LOG)
    for f, what, before, after in getattr(slim, "LOG", None) or []:
        report("slim", f"{f}: {what}, {before / 1024:.0f} -> {after / 1024:.0f} KB")
    return out["issues"], out["notes"]


# ------------------------------------------------------------------ files
def _excludes(here):
    """What the Rive CLI never reads as a source (rive docs project/rive-yaml): `exclude`, the output folder
    (output.dir, default build) and the logs."""
    try:
        yml = open(os.path.join(here, "rive.yaml")).read()
    except OSError:
        yml = ""
    m = re.search(r"^exclude:\s*\n((?:[ \t]+-[ \t]*.+\n?)+)", yml, re.M)
    ex = [x.split(" #")[0].strip().strip("\"'").rstrip("/") for x in re.findall(r"-[ \t]*(.+)", m.group(1))] \
        if m else []
    out = re.search(r"^output:\s*\n[ \t]+dir:[ \t]*\"?([^\"\n]+)", yml, re.M)
    ex.append(out.group(1).strip().rstrip("/") if out else "build")
    ex += [x.strip().strip("\"'") for x in re.findall(r"^[ \t]+(?:file|problems):[ \t]*(.+)$", yml, re.M)]
    return ex


def loose_rml(here, report):
    """[rml] every .rml the Rive CLI would build besides scene.rml (names starting with "." are never read)."""
    ex = _excludes(here)
    found = []
    for d, dirs, files in os.walk(here):
        rel_d = os.path.relpath(d, here)
        dirs[:] = [x for x in dirs if not x.startswith(".")
                   and not any(_under(os.path.normpath(os.path.join(rel_d, x)), e) for e in ex)]
        for f in files:
            rel = os.path.normpath(os.path.join(rel_d, f))
            if f.endswith(".rml") and not f.startswith(".") and rel != "scene.rml" \
                    and not any(_under(rel, e) for e in ex):
                found.append(rel)
    if found:
        report("rml", f"{len(found)} loose .rml in the piece folder ({', '.join(sorted(found)[:4])}): the Rive CLI "
                      "builds every .rml it finds and the scene breaks (duplicate ids); rename to .rml.txt or add the "
                      "folder to rive.yaml's exclude", issue=True)


def _under(rel, pattern):
    return rel == pattern or rel.startswith(pattern + os.sep) or fnmatch.fnmatch(rel, pattern)


# ------------------------------------------------------------------ the scene (weight, outlines)
def library_artboards():
    try:
        import library
        return {n for n, _ in library.COMPONENTS} | {"Cursor"}
    except Exception:
        return set()


def scene_stats(path):
    """Objects per top-level artboard, the own drawing's vertices and texts, and the letter outlines."""
    root = ET.parse(path).getroot()
    lib = library_artboards()
    arts = []
    for ab in root.findall("Artboard"):
        name = ab.get("name") or "?"
        n = sum(1 for _ in ab.iter())
        v = sum(1 for e in ab.iter() if e.tag in VERT)
        own = name not in lib and not name.startswith("Icon/")
        arts.append(dict(name=name, objects=n, verts=v, own=own, texts=sum(1 for e in ab.iter() if e.tag == "Text")))
    groups = []
    for parent in root.iter():
        subs = []
        for sh in parent:
            if sh.tag != "Shape":
                continue
            sx, sy = abs(float(sh.get("scaleX", 1))), abs(float(sh.get("scaleY", 1)))
            for pp in sh:
                if pp.tag == "PointsPath" and pp.get("isClosed") == "true":
                    xs = [float(v.get("x", 0)) * sx for v in pp if v.tag in VERT]
                    ys = [float(v.get("y", 0)) * sy for v in pp if v.tag in VERT]
                    if xs and max(xs) - min(xs) <= 40 and max(ys) - min(ys) <= 40:
                        subs.append(len(xs))
        if len(subs) >= 8:      # an icon has a few; a word has one per letter (and more for o, e, a...)
            groups.append((parent.get("name") or parent.tag, len(subs), sum(subs)))
    return dict(total=sum(1 for _ in root.iter()), artboards=arts, glyph_groups=groups)


def weight(here, report):
    """[weight] [outlines] from the scene.rml the build wrote."""
    path = os.path.join(here, "scene.rml")
    if not os.path.exists(path):
        return
    st = scene_stats(path)
    own = [a for a in st["artboards"] if a["own"]]
    verts = sum(a["verts"] for a in own)
    big = sorted((a for a in st["artboards"] if a["objects"] > LIMITS["artboard_note"]), key=lambda a: -a["objects"])
    for a in big:
        issue = a["objects"] > LIMITS["artboard_issue"]
        report("weight", f"artboard {a['name']!r}: {a['objects']:,} objects ({a['verts']:,} vertices, {a['texts']} "
                         f"texts): {'the editor freezes' if issue else 'the editor slows down'} over ~"
                         f"{LIMITS['artboard_issue'] if issue else LIMITS['artboard_note']:,}; native text, plates "
                         "(a still part as a 2x image, with the OK) or display none off-scene (LEARNINGS 14, 16)",
               issue=issue)
    if verts > LIMITS["verts_note"] and not big:
        report("weight", f"the piece's own drawing has {verts:,} vertices (over {LIMITS['verts_note']:,}): look for "
                         "text as outlines and masks that cut nothing (LEARNINGS 16)")
    letters = sum(g[1] for g in st["glyph_groups"])
    if letters >= LIMITS["letters_note"]:
        top = sorted(st["glyph_groups"], key=lambda g: -g[2])[:4]
        share = sum(g[2] for g in st["glyph_groups"]) / max(1, sum(a["verts"] for a in st["artboards"]))
        report("outlines", f"~{letters:,} letters drawn as outlines in {len(st['glyph_groups'])} groups ({share:.0%} "
                           f"of the vertices; {', '.join(f'{n} {k}' for n, k, _ in top)}): native text, one per line "
                           "(p.text / p.font; LEARNINGS 16)")


# ------------------------------------------------------------------ the timeline
class Timeline:
    """Visibility over the whole timeline, with layout boxes and display in the opacity chain."""

    def __init__(self, piece, actions):
        import numpy as np
        self.np, self.p, self.a, self.c = np, piece, actions, actions.c
        self.F = self.c.F
        self.parent, self.size, self.order = {}, {}, []
        self.skip = set()
        for el in (getattr(piece, "drivers", None), getattr(piece, "overlay", None), getattr(piece, "fx", None)):
            if el is not None:
                self.skip.add(id(el))
        self._walk(piece.board, None)
        self.op, self.disp, self.lay = {}, {}, {}   # chains: opacity, display, and the choreo one (no layout boxes)
        ones = np.ones(self.F + 1)
        self._chain(piece.board, ones, ones, ones)

    def _walk(self, el, parent):
        self.parent[id(el)] = parent
        self.order.append(el)
        n = 1
        for c in el.children:
            if hasattr(c, "tag") and id(c) not in self.skip:
                if el.tag in ("NestedArtboardLayout", "NestedArtboard"):
                    n += 1      # its machine: the component's own objects live in its artboard
                    continue
                n += self._walk(c, el)
        self.size[id(el)] = n
        return n

    def series(self, name, prop, base):
        tr = self.c.tracks.get((name, prop)) if name else None
        if tr is None:
            return None if base is None else self.np.full(self.F + 1, float(base))
        # displayValue: 0 / "flex" shown, 1 / "none" off (v14b: the strings were read the other way round)
        return self.np.array([float(v) if not isinstance(v, str) else {"flex": 0.0, "none": 1.0}.get(v, 0.0)
                              for v in tr.sample(self.F)])

    def _own(self, el):
        np = self.np
        bound = any(getattr(c, "tag", "") == "DataBindContext" and c.attrs.get("propertyKey") == 18
                    for c in el.children)
        base = el.attrs.get("opacity")
        op = self.series(el.name, "opacity", 1.0 if bound or base is None else base)
        disp = np.ones(self.F + 1)
        style = next((c for c in el.children if getattr(c, "tag", "") == "LayoutComponentStyle"), None)
        if style is not None:
            d = self.series(style.name, "displayValue", None)
            if d is not None:
                disp = (np.abs(d - 1) > 1e-6).astype(float)
            elif style.attrs.get("displayValue") in ("none", 1):
                disp = np.zeros(self.F + 1)
        return op, disp

    def _chain(self, el, op, disp, lay):
        own_op, own_disp = self._own(el)
        self.op[id(el)] = op = op * own_op
        self.disp[id(el)] = disp = disp * own_disp
        self.lay[id(el)] = lay = lay * own_op if el.tag in ("Node", "Shape", "Text", "Image") else lay
        if el.tag in ("NestedArtboardLayout", "NestedArtboard"):
            return
        for c in el.children:
            if hasattr(c, "tag") and id(c) not in self.skip:
                self._chain(c, op, disp, lay)

    def vis(self, el):
        return self.op[id(el)] * self.disp[id(el)]

    def draws(self, el):
        if el.tag in DRAWS:
            return el.tag != "Shape" or any(getattr(c, "tag", "") in PAINTS for c in el.children)
        if el.tag == "LayoutComponent" and any(getattr(c, "tag", "") in PAINTS for c in el.children):
            return True
        return any(self.draws(c) for c in el.children if hasattr(c, "tag") and id(c) not in self.skip)

    def layers(self, el):
        """How many things it draws (a box's own paint, each shape, text, image, component)."""
        n = 1 if (el.tag in DRAWS and el.tag != "Shape") or any(getattr(c, "tag", "") in PAINTS for c in el.children) \
            else 0
        if el.tag in ("NestedArtboardLayout", "NestedArtboard"):
            return n
        return n + sum(self.layers(c) for c in el.children if hasattr(c, "tag") and id(c) not in self.skip)

    def label(self, el):
        n = el.name or el.tag
        return n[len(self.p.art) + 1:] if n.startswith(self.p.art + ".") else n

    def run(self, report):
        self.hidden(report)
        self.offscene(report)
        self.layoutfade(report)
        self.offframe(report)
        self.hairline(report)
        self.cursorstart(report)

    # [cursorstart]
    def _cursors(self):
        """Every cursor as (name, tip(f), alpha(f)): the piece's (a._tip_list: the arrows, a drag's hand) and the
        hands on a THROW*.follow path, which light no hovers, so they are not in that list."""
        a = self.a
        out = [(n, tip, alpha) for n, tip, alpha, *_ in (getattr(a, "_tip_list", None) or [])]
        known = {o[0] for o in out}
        import hand
        for name, el in list(self.c.by.items()):
            if not (name.startswith("THROW") and name.endswith(".follow")) or name[:-7] in known:
                continue
            n = name[:-7]
            dtr, otr, shape = self.c.tracks.get((name, "distance")), self.c.tracks.get((n, "opacity")), \
                self.c.by.get(f"{n}.path")
            if dtr is None or shape is None:
                continue
            path = hand.RmlPath(shape)
            out.append((n, lambda f, pth=path, d=dtr: pth.pos(d.value_at(f)),
                        (lambda f, o=otr: o.value_at(f)) if otr is not None else (lambda f: 1.0)))
        return out

    def cursorstart(self, report):
        import math
        F = self.F
        slow = LIMITS["cursor_slow_px"] * self.p.w / 1340.0
        need = int(round(LIMITS["cursor_still_s"] * 60))
        bad = []
        for n, tip, alpha in self._cursors():
            f = 0
            while f <= F:
                while f <= F and alpha(f) <= 0.05:        # hidden
                    f += 1
                if f > F:
                    break
                f0, still = f, 0
                while f < F and alpha(f + 1) > 0.05 and math.dist(tip(f), tip(f + 1)) < slow:
                    still += 1
                    f += 1
                if still > need:
                    bad.append((n, f0, still))
                while f <= F and alpha(f) > 0.05:         # on to its next showing
                    f += 1
        for n, f0, still in bad:
            report("cursorstart", f"{n} shows still at {f0 / 60:.2f}s: under {slow:.1f} px a frame for "
                                  f"{still / 60:.2f}s (max {LIMITS['cursor_still_s']:g} s). A cursor is on its way when "
                                  "it shows (LEARNINGS 3)", issue=True)

    # [hidden]
    def hidden(self, report):
        found = []
        live = set()          # v15b: a live hover's layers show by the visitor's mouse, not the timeline
        for it in getattr(self.p, "live", ()):
            live |= set(it.hoverable["layers"]) | {i.wrap.name for i in it.hoverable["rise"]}
        for el in self.order:
            par = self.parent[id(el)]
            if el is self.p.board or par is None or not el.name or el.tag in ("LayoutComponentStyle",) or \
                    el.name in live:
                continue
            if self.vis(el).max() < EPS <= self.vis(par).max() and self.draws(el):
                found.append((self.size[id(el)], self.label(el)))
        if found:
            found.sort(reverse=True)
            report("hidden", f"{len(found)} part(s) never show and still cost ({sum(s for s, _ in found):,} objects): "
                             + ", ".join(f"{n} ({s})" for s, n in found[:6])
                             + ("..." if len(found) > 6 else "") + ": remove them, or show them")

    # [offscene]
    def offscene(self, report):
        found = []
        for el in self.order:
            par = self.parent[id(el)]
            if par is None or el is self.p.board or self.size[id(el)] < LIMITS["screen_objects"] or not el.name:
                continue
            gone = (self.op[id(el)] < EPS) & (self.disp[id(el)] > 0.5)
            gone_par = (self.op[id(par)] < EPS) & (self.disp[id(par)] > 0.5)
            own = gone & ~gone_par           # hidden by its own fade, not its parent's
            s = own[:-1].sum() / 60
            if s >= LIMITS["offscene_s"] and self.vis(el).max() >= EPS:
                found.append((s, self.size[id(el)], self.label(el)))
        for s, size, n in sorted(found, reverse=True)[:5]:
            report("offscene", f"{n} ({size} objects) is hidden by opacity for {s:.1f} s but stays on: key its "
                               "display none while hidden (a.c.set(t, '<box>.style', 'displayValue', 1); LEARNINGS 16)")

    # [layoutfade]
    def layoutfade(self, report):
        np, c = self.np, self.c
        boxes = [el for el in self.order if el.tag in LAYOUT and el.name and (el.name, "opacity") in c.tracks
                 and len(c.tracks[(el.name, "opacity")].keys) > 1]
        if not boxes:
            return
        under = {}
        for b in boxes:
            stack = [b]
            while stack:
                e = stack.pop()
                under.setdefault(id(e), []).append(b)
                stack += [k for k in e.children if hasattr(k, "tag") and id(k) not in self.skip]
        try:
            import choreo
            caps = choreo.TOKENS["speed_cap_px_per_frame_at_1920"]
            settle = choreo.ease_curve("settle")
            out = choreo.OUT_SCALE
        except Exception:
            return
        movers = {n for (n, p) in c.tracks if p in ("x", "y")}
        by = {el.name: el for el in self.order if el.name}
        # v14b: what a.cut moves on its own around a cut (its screens back in place while hidden, their edges, the
        # cascade's rows) is its business, not a false OVER (cuts.py's lint skips the same frames)
        cut_win = self.a._cut_windows(cascade=True) if hasattr(self.a, "_cut_windows") else {}
        for n in sorted(movers):
            el = by.get(n)
            if el is None or id(el) not in under:
                continue
            mine, theirs = self.vis(el), self.lay[id(el)]
            skip = cut_win.get(n, set())
            peak, at, prev = 0.0, 0, c.to_screen(el, (c.prop(el, "x", 0), c.prop(el, "y", 0)), 0)
            for f in range(1, self.F + 1):
                cur = c.to_screen(el, (c.prop(el, "x", f), c.prop(el, "y", f)), f)
                if f in skip or f - 1 in skip:
                    prev = cur
                    continue
                if theirs[f] > 0.05 >= mine[f]:
                    sp = ((cur[0] - prev[0]) ** 2 + (cur[1] - prev[1]) ** 2) ** 0.5 * out
                    if sp > peak:
                        peak, at = sp, f
                prev = cur
            cap = caps["text_content"]
            if peak > cap + 0.5:
                box = next((b for b in under[id(el)] if self.vis(b)[at] <= 0.05), under[id(el)][0])
                whose = "its own layout box" if box is el else f"layout box {self.label(box)}"
                report("layoutfade", f"{self.label(el)} moves {peak:.0f} px/f at {at / 60:.2f}s while a fade on "
                                     f"{whose} hides it: not on screen, so a speed OVER there is false (the lints "
                                     "don't see fades on layout boxes)")
        for (n, p), tr in c.tracks.items():
            el = by.get(n)
            if el is None or p not in ("x", "y", "scaleX", "scaleY"):
                continue
            for i, k in enumerate(tr.keys[:-1]):
                if k["ease"] != settle or (n, k["f"]) in c.cut_entries:
                    continue
                own = c.tracks.get((n, "opacity"))
                if own is not None and own.value_at(max(0, k["f"] - 1)) > 0.1:
                    continue        # the lint already reports it
                dist = abs(tr.keys[i + 1]["v"] - k["v"]) * (1 if p in ("x", "y") else 100)
                if self.vis(el)[max(0, k["f"] - 1)] > 0.1 and dist > 60:
                    report("layoutfade", f"{self.label(el)}.{p}: 'settle' (fast start) at {k['f'] / 60:.2f}s on "
                                         f"something visible ({dist:.0f} px): start it hidden, or 'duda' (MOTION: "
                                         "rest to rest; the lint misses it, it reads only the element's own opacity)")
        windows = {}     # (start, length) -> boxes: boxes fading together make one note
        for b in boxes:
            o = self.op[id(b)]
            half = (o > 0.05) & (o < 0.95)
            run_, best, at = 0, 0, 0
            for f, h in enumerate(half):
                run_ = run_ + 1 if h else 0
                if run_ > best:
                    best, at = run_, f - run_ + 1
            if best / 60 >= LIMITS["halffade_s"] and self.layers(b) >= 2:
                seg = o[at:at + best]
                med = float(self.np.median(seg))
                held = (self.np.abs(seg - med) < 0.05).mean() >= 0.6
                kind = f"held at ~{med:.0%}" if held else f"a slow fade, {seg.max():.0%} -> {seg.min():.0%}"
                windows.setdefault((at, best, kind), []).append(b)
        for (at, best, kind), bs in sorted(windows.items()):
            names = [self.label(b) for b in bs if not any(x is not b and id(x) in {id(y) for y in under[id(b)]}
                                                         for x in bs)]
            report("layoutfade", f"{', '.join(names[:5])}{'...' if len(names) > 5 else ''} half-faded for "
                                 f"{best / 60:.1f} s from {at / 60:.2f}s ({kind}): Rive fades each layer of a group on "
                                 "its own, so what it covers shows through (LEARNINGS 16), and opacity is a cut or a "
                                 "fade <= 167 ms (MOTION); fade it faster, or veil it")

    # [offframe]
    def offframe(self, report):
        p = self.p
        if not getattr(p, "_measured", None):   # no cursor aimed: measure the first layout (cached in build/measure)
            try:
                p._measure(0.0)
            except Exception:
                pass
        states = list(getattr(p, "_measured", {}).values())
        if not states:
            return
        keyed = {n for (n, prop) in self.c.tracks if prop in ("x", "y", "width", "height", "scaleX", "scaleY",
                                                              "displayValue", "positionLeft", "positionTop")}
        keyed |= {n[:-6] for n in keyed if n.endswith(".style")}
        clips = {it.wrap.name for it in p.items.values() if it.wrap is not None and it.wrap.attrs.get("clip")}
        found = []
        for key, it in p.items.items():
            if it.wrap is None or it.wrap is getattr(p, "root", None):
                continue
            chain, e = [], it.wrap
            while e is not None:
                chain.append(e)
                e = self.parent.get(id(e))
            if any(x.name in keyed for x in chain if x.name):
                continue        # it moves or resizes: the measured layouts don't tell where it goes
            if all(self._outside(st, it.wrap.name, [x.name for x in chain[1:] if x.name in clips]) for st in states
                   if it.wrap.name in st):
                if any(it.wrap.name in st for st in states) and id(it.wrap) in self.op \
                        and self.vis(it.wrap).max() >= EPS:
                    found.append((self.size[id(it.wrap)], key))
        if found:
            found.sort(reverse=True)
            report("offframe", f"{len(found)} placed item(s) sit outside the frame (or their clipped box) in every "
                               f"layout measured and never move: {', '.join(k for _, k in found[:6])}"
                               + ("..." if len(found) > 6 else "") + ": remove them or display none")

    # [hairline] (v15e)
    def _thin(self, el):
        """The thinnest painted dimension of `el` itself, in its own px (None: nothing thin): a stroke's thickness, a
        painted box's or rectangle's fixed width or height."""
        kids = [k for k in el.children if hasattr(k, "tag")]
        out = []
        for k in kids:
            if k.tag == "Stroke" and k.attrs.get("thickness") is not None:
                out.append(float(k.attrs["thickness"]))
        fill = any(k.tag == "Fill" for k in kids)
        if el.tag == "LayoutComponent" and fill:
            out += [float(v) for v in (el.attrs.get("width"), el.attrs.get("height"))
                    if isinstance(v, (int, float)) and 0 < v]
        if el.tag == "Shape" and fill:
            for k in kids:
                if k.tag == "Rectangle":
                    out += [float(v) for v in (k.attrs.get("width"), k.attrs.get("height"))
                            if isinstance(v, (int, float)) and 0 < v]
        return min(out) if out else None

    def hairline(self, report):
        np, F = self.np, self.F
        lo, hi = LIMITS["slow_px"]
        need = int(round(LIMITS["hairline_s"] * 60))
        reach = 0.5 * min(self.p.w, self.p.h)       # a part's typical distance from a zoom's pivot
        win = self.a._cut_windows(cascade=True) if hasattr(self.a, "_cut_windows") else {}
        found = []
        # v16: inside the component artboards it nests too (the ma-novo-social line that flickered was in one); their
        # parts take the nest's scale, motion and visibility, and their own static scale and opacity
        arts = {"@" + el.ref: el for el in list(getattr(self.p, "comps", None) or [])
                if getattr(el, "ref", None)}

        def walk(el, sc, mv, skip, inner=None, where="", depth=0):
            static = lambda prop: np.full(F + 1, float(el.attrs.get(prop, 1.0) if isinstance(
                el.attrs.get(prop, 1.0), (int, float)) else 1.0))
            sx = self.series(el.name, "scaleX", el.attrs.get("scaleX", 1.0) or 1.0) if inner is None else static("scaleX")
            sy = self.series(el.name, "scaleY", el.attrs.get("scaleY", 1.0) or 1.0) if inner is None else static("scaleY")
            own = np.minimum(np.abs(sx), np.abs(sy))
            nsc = sc * own
            dv = np.zeros(F + 1)
            for prop in ("x", "y"):
                tr = self.series(el.name, prop, None) if el.name and inner is None else None
                if tr is not None:
                    dv[1:] = np.maximum(dv[1:], np.abs(np.diff(tr)) * sc[1:])
            ds = np.zeros(F + 1)
            ds[1:] = np.abs(np.diff(nsc)) / np.maximum(nsc[1:], 1e-6) * reach * nsc[1:]
            nmv = mv + dv + ds
            nskip = skip | win.get(el.name, set())
            t = self._thin(el)
            if inner is not None:
                o = el.attrs.get("opacity", 1.0)
                inner = inner * (float(o) if isinstance(o, (int, float)) else 1.0)
            if t is not None and el.name:
                px = t * nsc
                vis = self.vis(el) if inner is None else inner
                ok = (px < LIMITS["hairline_px"]) & (vis > 0.05) & (nmv > lo) & (nmv < hi)
                if nskip:
                    ok[list(f for f in nskip if 0 <= f <= F)] = False
                run, best = 0, (0, 0)
                for f in range(F + 1):
                    run = run + 1 if ok[f] else 0
                    if run > best[0]:
                        best = (run, f)
                if best[0] >= need:
                    f1 = best[1]
                    f0 = f1 - best[0] + 1
                    found.append((float(px[f0:f1 + 1].min()), t, f0, f1, where + self.label(el)))
            if el.tag in ("NestedArtboardLayout", "NestedArtboard"):
                art = arts.get(el.attrs.get("artboardId"))
                if art is not None and depth < 4:
                    v = self.vis(el) if inner is None else inner
                    for k in art.children:
                        if hasattr(k, "tag"):
                            walk(k, nsc, nmv, nskip, v, f"{where}{self.label(el)} > ", depth + 1)
                return
            for k in el.children:
                if hasattr(k, "tag") and id(k) not in self.skip:
                    walk(k, nsc, nmv, nskip, inner, where, depth)

        ones = np.ones(F + 1)
        walk(self.p.board, ones, np.zeros(F + 1), set())
        if found:
            found.sort()
            fix = LIMITS["hairline_fix_px"]
            report("hairline", f"{len(found)} line(s) under {LIMITS['hairline_px']:g} px on screen while the scene "
                               "zooms or slides slowly: " + ", ".join(
                                   f"{n} ({px:.2f} px, {f0 / 60:.2f}-{f1 / 60:.2f} s)" for px, t, f0, f1, n in found[:6])
                   + ("..." if len(found) > 6 else "") + f": it flickers (a still never shows it). Make it {fix:g} px "
                   f"or more on screen with its opacity down in proportion (thickness x opacity the same; LEARNINGS 13),"
                   " or check it: scripts/hairline.py <piece> --at <s> --col <x> --rows <y0>:<y1>")

    def _outside(self, st, name, clip_names):
        x, y, w, h = st[name]
        if w <= 0 or h <= 0:
            return False
        x0, y0, x1, y1 = 0.0, 0.0, float(self.p.w), float(self.p.h)
        for cn in clip_names:
            if cn in st:
                cx, cy, cw, ch = st[cn]
                x0, y0, x1, y1 = max(x0, cx), max(y0, cy), min(x1, cx + cw), min(y1, cy + ch)
        return x + w <= x0 + 0.5 or x >= x1 - 0.5 or y + h <= y0 + 0.5 or y >= y1 - 0.5


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    here = os.path.abspath(sys.argv[1])
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    out = {"issues": [], "notes": []}

    def report(check, text, issue=False):
        out["issues" if issue else "notes"].append(f"[{check}] {text}")
    loose_rml(here, report)
    weight(here, report)
    st = scene_stats(os.path.join(here, "scene.rml"))
    print(f"scene.rml: {st['total']:,} objects; " + ", ".join(f"{a['name']} {a['objects']:,}" for a in
                                                            sorted(st["artboards"], key=lambda a: -a["objects"])[:6]))
    for i in out["issues"]:
        print("CHECK:", i)
    for n in out["notes"]:
        print("note:", n)
    if not out["issues"] and not out["notes"]:
        print("checks: clean")
    sys.exit(1 if out["issues"] else 0)


if __name__ == "__main__":
    main()
