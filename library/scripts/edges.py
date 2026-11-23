"""Edges and seams at ~5x: the thin line that shows only when the editor is zoomed in (LEARNINGS 12). Renders key
frames of a piece at ~5x and looks across every edge where one is likely: images, boxes that clip, nested components,
filled blocks (where two of them meet: a seam) and the artboard's border. A line lighter or darker than both sides of
an edge and at most ~1.6 px wide (at 1x) is a SUSPECT. Writes crops of what it found to a contact sheet to look at.
Works in any folder: it needs only the piece (build.py run once) and this bundle.

usage: python lib/biblioteca-<v>/scripts/edges.py <piece_dir> [--frames 0,240,719] [--max 8] [--region x,y,w,h ...]
                                                  [--zoom 5.3] [--all] [--keep] [--out DIR]
  --frames: the frames to look at (60 fps; each taken 1 ms past its time). Default: the first, the last, the hard
  cuts of the main timeline (a hold key that changes a value) and the middle of the two longest rests, --max in all.
  --zoom: 5.3 by default, not 5: at a whole zoom every edge at a multiple of 0.2 px lands on a pixel boundary and a
  seam there does not show (the editor's zoom is anything).
  --region x,y,w,h (artboard px): also crop that area at each frame (a place you want to see, found or not).
  --all: put every edge looked at in the sheet, not just the suspects and the images' edges.
  --keep: keep the full zoomed frames (big PNGs) in the output folder.
  Writes <piece>/build/edges/ (or --out): report.txt, sheet_f<N>.jpg per frame; exit 1 when something is suspect.
How to fix a line it finds (LEARNINGS 12): never a 1 px seam; a vector band in the background's colour that enters
>= 1 px into the content (e.g. 4 px wide over the image's edge), or the next block overlapping by 1 px. Check again.
"""
import argparse
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # python -I leaves the script's folder out
import scene  # noqa: E402

LINE = 8            # levels (0-255) a line must stand out from both sides
WIDE = 1.6          # px at 1x: wider than this is a border someone drew, not a hairline
NEAR = 1.2          # px at 1x: how far from the box's edge the line may sit
SIDE = (2.0, 3.2)   # px at 1x: where each side's plateau is read
CROP = 32           # px at 1x around the edge's middle, in the sheet
MIN_LEN = 10        # px: shorter edges are left out
OPACITY, DISPLAY = 18, 596    # property keys: opacity, LayoutComponentStyle displayValue (1 = none)


def mark(proj, main):
    """The scene with a SemanticData marker in each element worth a look; {marker: (kind, name, stroked, corner
    radius)} and, for
    those in the main artboard, what hides them: {marker: ([(id, opacity)], [(style id, display)])}."""
    tree = ET.parse(os.path.join(proj, "scene.rml"))
    root = tree.getroot()
    marks, chains = {}, {}
    ab = next((a for a in root.iter("Artboard") if a.get("name") == main), None)
    parent = {c: q for q in ab.iter() for c in q} if ab is not None else {}

    def add(e, kind):
        if any(c.tag == "SemanticData" for c in e):
            return
        m = f"edg{len(marks)}"
        stroked = any(c.tag == "Stroke" for c in e)
        rad = max([float(c.get(k, 0)) for c in [e] + [c for c in e if c.tag in ("Rectangle", "LayoutComponentStyle")]
                   for k in ("cornerRadiusTL", "cornerRadius")] + [0])
        marks[m] = (kind, (e.get("name") or e.get("id") or e.tag).replace("MAIN.", ""), stroked, rad)
        if e in parent:
            ops, styles, x = [], [], e
            while x is not None and x is not ab:
                ops.append((x.get("id"), float(x.get("opacity", 1))))
                st = next((c for c in x if c.tag == "LayoutComponentStyle"), None)
                if st is not None:
                    styles.append((st.get("id"), float(st.get("displayValue", 0))))
                x = parent.get(x)
            chains[m] = (ops, styles)
        e.insert(0, ET.Element("SemanticData", {"role": "group", "label": m}))

    for e in root.iter():
        kids = {c.tag for c in e}
        if e.tag == "Image":
            add(e, "image")
        elif e.tag in ("NestedArtboardLayout", "NestedArtboard"):
            add(e, "nested")
        elif e.tag == "LayoutComponent":
            if "Stroke" in kids:
                add(e, "line")          # a border someone drew (CoreInput.border)
            elif e.get("clip") == "true":
                add(e, "clip")
            elif "Fill" in kids:
                add(e, "block")
        elif e.tag == "Shape":
            r = next((c for c in e if c.tag == "Rectangle"), None)
            if r is None:
                continue
            thin = min(float(r.get("width", 0)), float(r.get("height", 0))) < 3
            soft = any(f.tag == "Feather" for c in e if c.tag == "Fill" for f in c)
            if thin or soft or any(c.tag == "Stroke" for c in e):
                add(e, "line")          # drawn on purpose (a line, an outline, a soft shadow): what it leaves on
            elif any(c.tag == "Fill" for c in e):   # an edge is meant
                add(e, "block")
    return marks, chains, tree


def timeline_keys(proj, main):
    """{(object id, property key): [(frame, value, hold)]} of the main artboard's Timeline."""
    names = {"opacity": OPACITY, "displayValue": DISPLAY}
    root = ET.parse(os.path.join(proj, "scene.rml")).getroot()
    ab = next((a for a in root.iter("Artboard") if a.get("name") == main), None)
    anim = None if ab is None else next((a for a in ab.iter("LinearAnimation") if a.get("name") == "Timeline"), None)
    out = {}
    for ko in ([] if anim is None else anim.iter("KeyedObject")):
        for kp in ko:
            k = kp.get("propertyKey")
            k = int(k) if k and k.isdigit() else names.get(kp.get("property"))
            if k in (OPACITY, DISPLAY):
                out[(ko.get("objectId"), k)] = [(float(f.get("frame", 0)), float(f.get("value", 0)),
                                                f.get("interpolationType") in ("hold", "0"))
                                               for f in kp if f.tag.startswith("KeyFrame")]
    return out


def value_at(keys, f, default):
    """A keyed value at frame f (straight line between keys: enough to tell 0 from not 0)."""
    if not keys:
        return default
    if f <= keys[0][0]:
        return keys[0][1]
    for (f0, v0, hold), (f1, v1, _) in zip(keys, keys[1:]):
        if f0 <= f < f1:
            return v0 if hold else v0 + (v1 - v0) * (f - f0) / (f1 - f0)
    return keys[-1][1]


def shown(chain, keys, f):
    """Is a marked element of the main artboard drawn at frame f (no ancestor at opacity 0 or display none)?"""
    ops, styles = chain
    if any(value_at(keys.get((i, DISPLAY)), f, d) == 1 for i, d in styles):
        return False
    o = 1.0
    for i, d in ops:
        o *= value_at(keys.get((i, OPACITY)), f, d)
    return o > 0.02


def key_frames(proj, main, frames, most):
    """First, last, the hard cuts of the main artboard's Timeline (hold keys changing a value) and the middle of the
    two longest stretches between them (the rests, where the finished screen stays longest)."""
    root = ET.parse(os.path.join(proj, "scene.rml")).getroot()
    ab = next((a for a in root.iter("Artboard") if a.get("name") == main), None)
    cuts = set()
    anim = None if ab is None else next((a for a in ab.iter("LinearAnimation") if a.get("name") == "Timeline"), None)
    if anim is not None:
        for kp in anim.iter("KeyedProperty"):
            ks = [k for k in kp if k.tag.startswith("KeyFrame")]
            for a, b in zip(ks, ks[1:]):
                if a.get("interpolationType") == "hold" and a.get("value") != b.get("value"):
                    f = int(float(b.get("frame", 0)))
                    if 0 < f < frames - 1:
                        cuts.add(f)
    cuts = sorted(cuts)
    room = max(0, most - 4)
    if len(cuts) > room:
        cuts = [cuts[round(i * (len(cuts) - 1) / max(1, room - 1))] for i in range(room)] if room else []
    out = sorted({0, frames - 1, *cuts})
    for _ in range(2 if most >= 4 else 0):
        g = max(zip(out, out[1:]), key=lambda g: g[1] - g[0])
        if g[1] - g[0] > 1:
            out = sorted(set(out) | {(g[0] + g[1]) // 2})
    return out


def capture(cwd, frames, size, tmp):
    cmds, now = ["advance 1ms"], 0
    for f in frames:
        if f > now:
            cmds.append(f"advance {f - now}")
            now = f
        cmds += [f"screenshot {tmp}/f{f:05d}.png", f"semantics {tmp}/f{f:05d}.json"]
    cmds.append("quit")
    r = subprocess.run([scene.rive(), ".", "--commands", f"--viewport={size[0]}x{size[1]}", "--fit=contain",
                        "--quiet"], cwd=cwd, input="\n".join(cmds) + "\n", capture_output=True, text=True,
                       timeout=180 + 60 * len(frames))
    if r.returncode or any(not os.path.exists(f"{tmp}/f{f:05d}.png") for f in frames):
        errs = [ln for ln in r.stdout.splitlines() if ln.startswith("err")]
        sys.exit("the capture failed: " + "; ".join(errs[:3]) + r.stderr[-800:])


def boxes(js):
    out = []

    def walk(n):
        if n.get("label", "").startswith("edg"):
            b = n.get("bounds")
            if b:                              # null: not laid out / not drawn
                out.append((n["label"], b["x"], b["y"], b["width"], b["height"]))
        for c in n.get("children", []):
            walk(c)
    for r in json.load(open(js)).get("roots", []):
        walk(r)
    return out


def drawn_lines(bx, marks):
    """The edges of what was drawn on purpose (thin boxes and rectangles, outlines, soft shadows): (orient, pos, lo,
    hi, name)."""
    out = []
    for m, x, y, w, h in bx:
        kind, name = marks[m][:2]
        if kind == "line" or min(w, h) < 3:
            out += [("v", x, y, y + h, name), ("v", x + w, y, y + h, name), ("h", y, x, x + w, name),
                    ("h", y + h, x, x + w, name)]
    return out


def explained(orient, pos, lo, hi, lines):
    """The drawn line lying on this edge, if any."""
    for o, p, a, b, name in lines:
        if o == orient and abs(p - pos) <= NEAR + 0.5 and min(hi, b) - max(lo, a) >= 0.5 * min(hi - lo, b - a):
            return name
    return None


def edges_of(bx, marks, aw, ah):
    """Edges (orient, pos, lo, hi, [(kind, name, side, stroked)]), coincident ones merged; the artboard's border."""
    raw = []
    for m, x, y, w, h in bx:
        kind, name, stroked, rad = marks[m]
        if w < 3 or h < 3 or kind == "line":
            continue
        for orient, pos, lo, hi, side in (("v", x, y, y + h, "left"), ("v", x + w, y, y + h, "right"),
                                          ("h", y, x, x + w, "top"), ("h", y + h, x, x + w, "bottom")):
            lim = ah if orient == "v" else aw
            lo, hi = max(lo, 0), min(hi, lim)
            if hi - lo < MIN_LEN or pos < 0 or pos > (aw if orient == "v" else ah):
                continue
            raw.append([orient, pos, lo, hi, [(kind, name, side, stroked, rad)]])
    for orient, pos, lim in (("v", 0, ah), ("v", aw, ah), ("h", 0, aw), ("h", ah, aw)):
        raw.append([orient, pos, 0, lim, [("border", "artboard", "", False, 0)]])
    raw.sort(key=lambda e: (e[0], e[1], e[2]))
    out = []
    for e in raw:
        o = out[-1] if out else None
        if o and o[0] == e[0] and abs(o[1] - e[1]) <= 0.5 and e[2] <= o[3] - MIN_LEN:
            o[2], o[3] = min(o[2], e[2]), max(o[3], e[3])
            o[4] += [t for t in e[4] if t not in o[4]]
        else:
            out.append(e)
    return out


def profile(L, orient, pos, lo, hi, z):
    """The brightness across the edge, from -SIDE[1] to +SIDE[1] px (1x) at the zoomed size: one row per sample
    along it (every 2 px)."""
    r = int(round(SIDE[1] * z))
    c = int(round(pos * z))
    step = max(1, int(z * 2))
    along = range(int((lo + 2) * z), int((hi - 2) * z), step)
    if orient == "v":
        if c - r < 0 or c + r >= L.shape[1]:
            return None
        rows = [L[a, c - r:c + r + 1] for a in along if 0 <= a < L.shape[0]]
    else:
        if c - r < 0 or c + r >= L.shape[0]:
            return None
        rows = [L[c - r:c + r + 1, a] for a in along if 0 <= a < L.shape[1]]
    return np.array(rows, float) if rows else None


def border_profile(L, orient, pos, lo, hi, z):
    """At the artboard's border: brightness from the border inwards, 0 to SIDE[1] px."""
    r = int(round(SIDE[1] * z))
    step = max(1, int(z * 2))
    along = [a for a in range(int((lo + 2) * z), int((hi - 2) * z), step)]
    if orient == "v":
        rows = [L[a, :r] if pos == 0 else L[a, -r:][::-1] for a in along if 0 <= a < L.shape[0]]
    else:
        rows = [L[:r, a] if pos == 0 else L[-r:, a][::-1] for a in along if 0 <= a < L.shape[1]]
    return np.array(rows, float) if rows else None


def judge(rows, z, border=False):
    """(verdict, how much a line stands out, the step between the two sides) of the rows across an edge; verdict
    'light' or 'dark' (a line all along it), or None."""
    if rows is None or len(rows) < 2:
        return None, 0, 0
    p = np.median(rows, 0)
    if border:
        n = max(1, int(round(0.6 * z)))
        band, inside = p[:n].mean(), p[int(SIDE[0] * z):].mean()
        d = band - inside
        flat = np.abs(p[int(SIDE[0] * z):] - inside).max() < LINE
        return (("light" if d > 0 else "dark"), abs(d), 0) if abs(d) > LINE and flat else (None, abs(d), 0)
    r = len(p) // 2
    near = int(round(NEAR * z))
    s0 = int(round(SIDE[0] * z))
    left, right = p[:r - s0 + 1], p[r + s0:]
    if not len(left) or not len(right):
        return None, 0, 0
    a, b = left.mean(), right.mean()
    mid = p[r - near:r + near + 1]
    hi_, lo_ = mid.max() - max(a, b), min(a, b) - mid.min()
    for kind, d, top in (("light", hi_, mid.max()), ("dark", lo_, mid.min())):
        if d > LINE:
            half = (top + (max(a, b) if kind == "light" else min(a, b))) / 2
            core = (p > half) if kind == "light" else (p < half)
            width = core[r - s0:r + s0 + 1].sum() / z
            flat = max(np.ptp(left), np.ptp(right)) < max(LINE, d)    # each side even enough to tell a line
            ra, rb_ = rows[:, :r - s0 + 1].mean(1), rows[:, r + s0:].mean(1)
            rm = rows[:, r - near:r + near + 1]
            each = (rm.max(1) - np.maximum(ra, rb_)) if kind == "light" else (np.minimum(ra, rb_) - rm.min(1))
            along = (each > LINE / 2).mean() >= 0.7      # a seam runs the whole edge; text crossing it does not
            if width <= WIDE and flat and along:
                return kind, d, abs(a - b)
    return None, max(hi_, lo_, 0), abs(a - b)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("proj")
    ap.add_argument("--frames")
    ap.add_argument("--max", type=int, default=8)
    ap.add_argument("--region", action="append", default=[])
    ap.add_argument("--zoom", type=float, default=5.3)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--keep", action="store_true")
    ap.add_argument("--out")
    a = ap.parse_args()
    proj = os.path.abspath(a.proj)
    _, main_ab, aw, ah, frames, _ = scene.info(proj)
    g = math.gcd(aw, ah)                 # a zoom that makes both sides whole: no half-covered pixel at the border
    z = max(1, round(a.zoom * g)) / g
    if z == int(z) and g > 1:
        z += 1 / g                       # not a whole zoom (see --zoom)
    size = (round(aw * z), round(ah * z))
    ab_box = (0, 0) + size
    keys = sorted({int(f) for f in a.frames.split(",")}) if a.frames else key_frames(proj, main_ab, frames, a.max)
    out = os.path.abspath(a.out or os.path.join(proj, "build", "edges"))
    os.makedirs(out, exist_ok=True)
    marks, chains, tree = mark(proj, main_ab)
    keys_ = timeline_keys(proj, main_ab)
    tmp = tempfile.mkdtemp(prefix="edges")
    cwd = os.path.join(tmp, "p")
    os.makedirs(cwd)
    for n in os.listdir(proj):
        if n not in ("scene.rml", "build") and not n.startswith("."):
            os.symlink(os.path.join(proj, n), os.path.join(cwd, n))
    tree.write(os.path.join(cwd, "scene.rml"), encoding="unicode")
    print(f"frames {keys} at {size[0]}x{size[1]} ({z:g}x), {len(marks)} elements marked...")
    capture(cwd, keys, size, tmp)
    regions = [tuple(float(v) for v in r.split(",")) for r in a.region]
    lines, suspects = [], 0
    for f in keys:
        img = Image.open(f"{tmp}/f{f:05d}.png").convert("RGB").crop(ab_box)
        L = np.asarray(img.convert("L"))
        found = []
        bx = [b for b in boxes(f"{tmp}/f{f:05d}.json") if b[0] not in chains or shown(chains[b[0]], keys_, f)]
        lines_ = drawn_lines(bx, marks)
        for orient, pos, lo, hi, who in edges_of(bx, marks, aw, ah):
            border = who[0][0] == "border" and len(who) == 1
            on_border = pos in (0, aw if orient == "v" else ah)
            if on_border and not border:
                continue                       # the border's own check covers it
            trim = max(t[4] for t in who)       # rounded corners: only the straight part of the edge
            p = (border_profile if border else profile)(L, orient, pos, lo + trim, hi - trim, z)
            verdict, d, step = judge(p, z, border)
            if verdict == "dark" and not border and all(t[3] for t in who if t[0] != "border"):
                verdict = None                 # a stroke someone drew
            meant = explained(orient, pos, lo, hi, lines_) if verdict and not border else None
            if meant:
                verdict, who = None, who + [("drawn line", meant, "", True, 0)]
            kinds = {t[0] for t in who}
            show = verdict or a.all or "image" in kinds
            if p is None or (not verdict and d < 2 and step < 4 and not a.all):
                continue                       # nothing there: the same on both sides
            found.append((bool(verdict), verdict, d, orient, pos, lo, hi, who, show))
        found.sort(key=lambda e: (not e[0], -e[2]))
        n_s = sum(1 for e in found if e[0])
        suspects += n_s
        lines.append(f"== frame {f}: {len(found)} edges with something across them, {n_s} suspect")
        crops = []
        for i, (sus, verdict, d, orient, pos, lo, hi, who, show) in enumerate(found):
            names = ", ".join(f"{k} {n}" + (f" {s}" if s else "") for k, n, s, *_ in who[:3]) + \
                (f" +{len(who) - 3}" if len(who) > 3 else "")
            where = f"{'x' if orient == 'v' else 'y'}={pos:.1f} ({lo:.0f}-{hi:.0f})"
            tag = f"SUSPECT {verdict} line" if sus else "ok"
            if sus or show:
                lines.append(f"   {tag:20s} +{d:4.0f}  {where:22s} {names}")
            if show and len(crops) < 48:
                mid = (lo + hi) / 2
                cx, cy = (pos, mid) if orient == "v" else (mid, pos)
                crops.append((f"#{i} {tag} {where}", names, cx, cy, sus))
        for j, (x, y, w, h) in enumerate(regions):
            crops.append((f"region {j} {x:g},{y:g},{w:g},{h:g}", "", x + w / 2, y + h / 2, False, (w, h)))
        if crops:
            sheet(img, crops, z, os.path.join(out, f"sheet_f{f:05d}.jpg"), f)
            lines.append(f"   sheet: {os.path.join(out, f'sheet_f{f:05d}.jpg')}")
        if a.keep:
            shutil.copy(f"{tmp}/f{f:05d}.png", os.path.join(out, f"f{f:05d}_{z:g}x.png"))
    shutil.rmtree(tmp, ignore_errors=True)
    lines.append(f"{suspects} suspect edge(s)" + (": look at the sheets, fix with a band (LEARNINGS 12), run again"
                                                  if suspects else ""))
    rep = os.path.join(out, "report.txt")
    open(rep, "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))
    print(f"wrote {rep}")
    sys.exit(1 if suspects else 0)


def sheet(img, crops, z, path, frame, cols=4):
    t = int(CROP * z)
    cell = 300
    rows = (len(crops) + cols - 1) // cols
    s = Image.new("RGB", (cols * (cell + 8) + 8, rows * (cell + 40) + 30), (236, 236, 238))
    d = ImageDraw.Draw(s)
    d.text((8, 8), f"frame {frame}: crops of {CROP} px (1x) at {z:g}x; red = suspect", fill=(30, 30, 30))
    for i, c in enumerate(crops):
        label, names, cx, cy, sus = c[:5]
        w, h = (c[5] if len(c) > 5 else (CROP, CROP))
        box = (int((cx - w / 2) * z), int((cy - h / 2) * z), int((cx + w / 2) * z), int((cy + h / 2) * z))
        im = Image.new("RGB", (box[2] - box[0], box[3] - box[1]), (128, 128, 128))   # grey: outside the artboard
        im.paste(img.crop((max(0, box[0]), max(0, box[1]), min(img.width, box[2]), min(img.height, box[3]))),
                 (max(0, -box[0]), max(0, -box[1])))
        if max(im.size) > cell:
            im.thumbnail((cell, cell), Image.LANCZOS)
        x, y = 8 + (i % cols) * (cell + 8), 30 + (i // cols) * (cell + 40)
        s.paste(im, (x, y + 30))
        if sus:
            d.rectangle([x - 2, y + 28, x + im.size[0] + 1, y + 31 + im.size[1]], outline=(220, 30, 30), width=3)
        d.text((x, y + 2), label[:48], fill=(200, 20, 20) if sus else (30, 30, 30))
        d.text((x, y + 15), names[:48], fill=(90, 90, 90))
    s.save(path, quality=90)


if __name__ == "__main__":
    main()
