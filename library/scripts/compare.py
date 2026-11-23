"""Compare poses of a piece with their Figma frames: per pose the mean difference (target <= ~12/255), the share of
pixels off by more than 40/255 (a local error the mean hides: a missing icon, a moved block), a 3 x 3 grid of both
(where it is off), the size of the big texts (ink width in the render against the Figma frame, same place) and an
overlay sheet to look at (Figma | Rive | 50 % mix | difference, flagged texts boxed in red).
Works in any folder: it needs only the piece (build.py run once) and this bundle.

usage: python lib/biblioteca-<v>/scripts/compare.py <piece_dir> <figma.png>[@N] [<figma.png>[@N] ...]
                                                    [--frame N] [--scale 2] [--min-text 20] [--tol 3] [--no-texts]
                                                    [--still capture.png]
  Each pose is a Figma PNG and the frame to capture (60 fps) after "@" (pose.png@240), else --frame (default 0).
  A folder takes every PNG in it. The PNG may be the artboard's size, any multiple or the desktop app's 1024 px
  preview: Figma and Rive are both scaled to the artboard x --scale (default 2), never cropped (a 1 px border around
  the export is trimmed). The capture is the frame 1 ms past its time, at that size with --fit=contain, all poses
  in one CLI session.
  Texts: every Text of the main artboard whose size (font size x the scale of its parents) is >= --min-text px. Its
  box at that frame comes from the CLI (--semantics, on a marked copy of the scene); the ink width inside it is
  compared with the Figma frame's ink at the same place. Over --tol % (default 3) prints "TEXT"; a text that is
  half drawn at that frame (typing, fading) reads small, so pick rest poses.
  --still: compare a PNG you already have (one pose) instead of capturing; the texts are measured only with --frame.
  Writes <piece>/build/compare/<pose>_rive.png and <pose>_overlay.jpg; exit 1 when a pose or a text is off.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

import numpy as np
from PIL import Image, ImageChops, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # python -I leaves the script's folder out
import scene  # noqa: E402

MEAN_OK = 12          # /255, the whole frame
OVER = 40             # a pixel "off": its biggest channel difference
CELL_OVER = 4.0       # % of a 3 x 3 cell's pixels off: look there
INK = 90              # ink: sum of the 3 channels' difference from the box's background


def poses_of(args, frame):
    out = []
    for p in args:
        at = frame
        m = re.match(r"^(.*\.png)@(\d+)$", p, re.I)
        if m:
            p, at = m.group(1), int(m.group(2))
        if os.path.isdir(p):
            for n in sorted(os.listdir(p)):
                if n.lower().endswith(".png"):
                    out.append((os.path.join(p, n), at))
        else:
            out.append((p, at))
    return out


def load_figma(path, aw, ah, size):
    im = Image.open(path).convert("RGB")
    W, H = im.size
    note = ""
    def whole(w, h):                       # w x h is the artboard at a whole scale (1x, 2x, 3x)
        n = round(w / aw)
        return n >= 1 and abs(w - n * aw) < 0.5 and abs(h - n * ah) < 0.5
    if not whole(W, H) and W > 4 and H > 4 and whole(W - 2, H - 2):
        im, note = im.crop((1, 1, W - 1, H - 1)), " (1 px border trimmed)"
    elif abs(W / H - aw / ah) > 0.01:
        note = f" (different proportions: {W}x{H} for an artboard {aw}x{ah}; scaled anyway)"
    return im.resize(size, Image.LANCZOS), note


def text_targets(proj, main, min_px):
    """{marker: (name, words, size px, [text colours], [clip markers])} for the main artboard's Texts at or over
    min_px, and the scene with a SemanticData marker in each and in the boxes that clip them (the CLI then reports
    their boxes: what a clip hides is left out of the measure)."""
    tree = ET.parse(os.path.join(proj, "scene.rml"))
    root = tree.getroot()
    ab = next((a for a in root.iter("Artboard") if a.get("name") == main), None)
    if ab is None:
        return {}, None
    parent = {c: p for p in ab.iter() for c in p}
    out, clips = {}, {}
    for t in ab.iter("Text"):
        sizes = [float(s.get("fontSize", 0)) for s in t.iter("TextStylePaint")]
        if not sizes:
            continue
        s, e = float(t.get("scaleX", 1)), t
        while e in parent and parent[e] is not ab:
            e = parent[e]
            s *= float(e.get("scaleX", 1))
        px = max(sizes) * abs(s)
        if px < min_px:
            continue
        cols = []
        for c in t.iter("SolidColor"):
            v = c.get("colorValue", "")
            if re.fullmatch(r"[0-9A-Fa-f]{8}", v):
                cols.append(tuple(int(v[i:i + 2], 16) for i in (2, 4, 6)))
        mark = f"cmpT{len(out)}"
        cl, e = [], t
        while e in parent and parent[e] is not ab:
            e = parent[e]
            if e.get("clip") == "true" and not any(c.tag == "SemanticData" for c in e):
                if e not in clips:
                    clips[e] = f"cmpC{len(clips)}"
                cl.append(clips[e])
        words = " ".join(r.get("text", "") for r in t.iter("TextValueRun")).replace("\n", " ").strip()
        out[mark] = (t.get("name") or t.get("id"), words[:32] + ("..." if len(words) > 32 else ""), px, cols, cl)
        t.insert(0, ET.Element("SemanticData", {"role": "group", "label": mark}))
    for e, m in clips.items():
        e.insert(0, ET.Element("SemanticData", {"role": "group", "label": m}))
    return out, tree


def marked_copy(proj, tree):
    """A folder that builds like the piece, with the marked scene (the piece's own files are linked, not copied)."""
    tmp = tempfile.mkdtemp(prefix="cmp")
    out = os.path.join(tmp, "p")
    os.makedirs(out)
    for n in os.listdir(proj):
        if n in ("scene.rml", "build") or n.startswith("."):
            continue
        os.symlink(os.path.join(proj, n), os.path.join(out, n))
    tree.write(os.path.join(out, "scene.rml"), encoding="unicode")
    return tmp, out


def capture(cwd, shots, size, sem):
    """One CLI session: each (frame, png, semantics json or None), 1 ms past its frame."""
    cmds, now = ["advance 1ms"], 0
    for f, png, js in sorted(shots):
        if f > now:
            cmds.append(f"advance {f - now}")
            now = f
        cmds.append(f"screenshot {png}")
        if sem and js:
            cmds.append(f"semantics {js}")
    cmds.append("quit")
    r = subprocess.run([scene.rive(), ".", "--commands", f"--viewport={size[0]}x{size[1]}", "--fit=contain",
                        "--quiet"], cwd=cwd, input="\n".join(cmds) + "\n", capture_output=True, text=True,
                       timeout=120 + 10 * len(shots))
    errs = [ln for ln in r.stdout.splitlines() if ln.startswith("err")]
    missing = [png for _, png, _ in shots if not os.path.exists(png)]
    if missing or r.returncode:
        sys.exit("the capture failed: " + "; ".join(errs[:3]) + (r.stderr[-800:] if r.returncode else ""))


def boxes(js):
    out = {}

    def walk(n):
        if n.get("label", "").startswith(("cmpT", "cmpC")):
            b = n.get("bounds")
            if b:                              # null: not laid out / not drawn
                out[n["label"]] = (b["x"], b["y"], b["width"], b["height"])
        for c in n.get("children", []):
            walk(c)
    for r in json.load(open(js)).get("roots", []):
        walk(r)
    return out


def ink(a, box, cols, gap):
    """Ink box (x0, y0, x1, y1) of a text inside box of image array a, None if there is none. With the text's colours
    the ink is what is near them (a text over a photo); without, what differs from the box's border colour. Columns
    of ink further than gap from the biggest run of them are left out (a neighbour, a speck of the photo), and only
    the line with the most ink counts (the next text or line of a paragraph stays out)."""
    x0, y0, x1, y1 = (int(round(v)) for v in box)
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(a.shape[1], x1), min(a.shape[0], y1)
    if x1 - x0 < 3 or y1 - y0 < 3:
        return None
    c = a[y0:y1, x0:x1]
    bg = np.median(np.concatenate([c[0], c[-1], c[:, 0], c[:, -1]]), 0)
    if cols:
        near = np.min([np.abs(c - np.array(k_, float)).max(2) for k_ in cols], 0)
        far = max(max(np.abs(np.array(k_, float) - bg).max() for k_ in cols), 1)
        m = near <= max(20, 0.25 * far)          # the glyphs' cores: a photo's light patches stay out
    else:
        m = np.abs(c - bg).sum(2) > INK
    def biggest(h, thr, g):
        on = np.where(h >= thr)[0]
        if len(on) < 2:
            return None
        runs, start = [], on[0]
        for i in range(1, len(on) + 1):
            if i == len(on) or on[i] - on[i - 1] > g:
                runs.append((start, on[i - 1]))
                if i < len(on):
                    start = on[i]
        return max(runs, key=lambda r: h[r[0]:r[1] + 1].sum())
    rows = biggest(m.sum(1), 1, max(2, 0.13 * gap))     # one line: the next text or line stays out
    if not rows:
        return None
    m = m[rows[0]:rows[1] + 1]
    cols_ = biggest(m.sum(0), max(1, 0.03 * m.shape[0]), gap)
    if not cols_ or cols_[1] - cols_[0] < 2:
        return None
    xs0, xs1 = cols_
    ys = np.where(m[:, xs0:xs1 + 1].sum(1) > 0)[0] + rows[0]
    return x0 + xs0, y0 + ys.min(), x0 + xs1 + 1, y0 + ys.max() + 1


def text_sizes(fig, riv, k, aw, ah, bx, targets, tol):
    """[(flag, line, box at compare scale)] for the marked texts drawn at this pose."""
    F, R = np.asarray(fig, float), np.asarray(riv, float)
    out = []
    for mark, (x, y, w, h) in sorted(bx.items(), key=lambda i: (i[1][1], i[1][0])):
        if not mark.startswith("cmpT"):
            continue
        name, words, px, cols, cl = targets[mark]
        x0, y0, x1, y1 = x - 2, y - 2, x + w + 2, y + h + 2
        for c in cl:                      # what its clipping boxes hide is not drawn
            if c in bx:
                cx, cy, cw, ch = bx[c]
                x0, y0, x1, y1 = max(x0, cx), max(y0, cy), min(x1, cx + cw), min(y1, cy + ch)
        x0, y0, x1, y1 = max(x0, 0), max(y0, 0), min(x1, aw), min(y1, ah)
        if x1 - x0 < 4 or y1 - y0 < 4:
            continue
        clipped = (x0, x1) != (x - 2, x + w + 2)
        gap = 0.9 * px * k
        own = (x0 * k, y0 * k, x1 * k, y1 * k)
        rb = ink(R, own, cols, gap)
        if not rb or rb[2] - rb[0] < 16 * k:
            continue
        rw_ = rb[2] - rb[0]
        px_, py_ = max(8 * k, 0.2 * rw_), 3 * k + 0.15 * (rb[3] - rb[1])
        area = (max(0, rb[0] - px_), max(0, rb[1] - py_), min(aw * k, rb[2] + px_), min(ah * k, rb[3] + py_))
        fb = ink(F, area, cols, gap)
        label = f"{words!r} ({name}, {px:.0f} px)"
        if not fb:
            out.append((False, f"   text {label}: not found in the Figma frame there", None))
            continue
        touch = fb[0] <= area[0] + 1 or fb[2] >= area[2] - 1
        cut = clipped and (rb[0] <= own[0] + 1 or rb[2] >= own[2] - 1)
        rw, fw = rw_ / k, (fb[2] - fb[0]) / k
        rh, fh = (rb[3] - rb[1]) / k, (fb[3] - fb[1]) / k
        d, dh = 100 * (rw / fw - 1), 100 * (rh / fh - 1)
        # one line drawn bigger or smaller is wider AND taller; only wider: part of it hidden, or other ink beside it
        flat = (rh < 1.5 * px and fh < 1.5 * px and abs(rh - fh) < 1.5 and (d * dh < 0 or abs(dh) < abs(d) / 3))
        unsure = (" (unsure: more ink next to it in Figma)" if touch else " (unsure: the text is clipped)" if cut
                  else " (unsure: as tall as in Figma; something covers part of it, or other ink beside it)"
                  if abs(d) > tol and flat else "")
        flag = abs(d) > tol and not unsure
        line = (f"{'TEXT' if flag else '   text'} {label}: Rive {rw:.1f} x {rh:.0f} px, Figma {fw:.1f} x {fh:.0f}"
                f" ({d:+.1f}% wide){unsure}")
        out.append((flag, line, rb))
    return out


def sheet(fig, riv, flagged, path):
    diff = ImageChops.difference(fig, riv).point(lambda v: min(255, v * 3))
    W, H = fig.size
    s = min(1.0, 900 / W)
    tw, th = int(W * s), int(H * s)
    out = Image.new("RGB", (tw * 2, th * 2), "white")
    d = ImageDraw.Draw(out)
    for i, (label, im) in enumerate([("Figma", fig), ("Rive", riv), ("50 % mix", Image.blend(fig, riv, 0.5)),
                                     ("difference x3", diff)]):
        x, y = (i % 2) * tw, (i // 2) * th
        out.paste(im.resize((tw, th)), (x, y))
        for b in flagged:
            d.rectangle([x + b[0] * s - 3, y + b[1] * s - 3, x + b[2] * s + 3, y + b[3] * s + 3], outline="red", width=2)
        d.text((x + 8, y + 6), label, fill="red")
    out.save(path, quality=88)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("proj")
    ap.add_argument("figma", nargs="+")
    ap.add_argument("--frame", type=int)
    ap.add_argument("--scale", type=float, default=2.0)
    ap.add_argument("--min-text", type=float, default=20)
    ap.add_argument("--tol", type=float, default=3.0)
    ap.add_argument("--no-texts", action="store_true")
    ap.add_argument("--still")
    a = ap.parse_args()
    proj = os.path.abspath(a.proj)
    _, main_ab, aw, ah, frames, _ = scene.info(proj)
    poses = poses_of(a.figma, a.frame or 0)
    if a.still and len(poses) != 1:
        sys.exit("--still compares one pose")
    k = a.scale
    size = (round(aw * k), round(ah * k))
    out = os.path.join(proj, "build", "compare")
    os.makedirs(out, exist_ok=True)
    targets, tree = ({}, None) if a.no_texts else text_targets(proj, main_ab, a.min_text)
    sem = bool(targets) and (not a.still or a.frame is not None)
    tmp, cwd = marked_copy(proj, tree) if sem else (None, proj)
    shots, jobs = [], []
    for png, f in poses:
        if f >= frames:
            print(f"note: frame {f} is past the timeline ({frames} frames)")
        stem = os.path.splitext(os.path.basename(png))[0]
        cap = os.path.join(out, f"{stem}_rive.png")
        js = os.path.join(tmp, f"{stem}.json") if sem else None
        if a.still:
            Image.open(a.still).convert("RGB").resize(size, Image.LANCZOS).save(cap)
        else:
            shots.append((f, cap, js))
        jobs.append((png, f, stem, cap, js))
    if a.still and sem:
        shots = [(a.frame, os.path.join(tmp, "still.png"), jobs[0][4])]
    if shots:
        capture(cwd, shots, size, sem)
    bad = 0
    for png, f, stem, cap, js in jobs:
        fig, note = load_figma(png, aw, ah, size)
        riv = Image.open(cap).convert("RGB").resize(size, Image.LANCZOS)
        d = np.abs(np.asarray(fig, dtype=float) - np.asarray(riv, dtype=float))
        mean, over = d.mean(axis=2), d.max(axis=2) > OVER
        W, H = size
        cells = [[(mean[r * H // 3:(r + 1) * H // 3, c * W // 3:(c + 1) * W // 3].mean(),
                   100 * over[r * H // 3:(r + 1) * H // 3, c * W // 3:(c + 1) * W // 3].mean()) for c in range(3)]
                 for r in range(3)]
        hot = any(p > CELL_OVER for row in cells for _, p in row)
        ok = mean.mean() <= MEAN_OK and not hot
        print(f"== {stem} @ " + (f"still {os.path.basename(a.still)}" if a.still else f"frame {f}") + note)
        print(f"mean difference: {mean.mean():.1f}/255, pixels off by > {OVER}: {100 * over.mean():.1f}% "
              f"({'ok' if ok else 'LOOK at the overlay: ' + ('mean over ~12' if mean.mean() > MEAN_OK else 'a local difference')})")
        print(f"by area (mean / % off; top to bottom, left to right; over {CELL_OVER:g}% off = *):")
        for row in cells:
            print("   " + "   ".join(f"{m:5.1f} /{p:5.1f}%{'*' if p > CELL_OVER else ' '}" for m, p in row))
        flagged = []
        if js and os.path.exists(js):
            res = text_sizes(fig, riv, k, aw, ah, boxes(js), targets, a.tol)
            for flag, line, b in res:
                print(line)
                if flag:
                    flagged.append(b)
            if not res:
                print(f"   (no text of {a.min_text:g} px or more drawn at this frame)")
        bad += (not ok) + len(flagged)
        ov = os.path.join(out, f"{stem}_overlay.jpg")
        sheet(fig, riv, flagged, ov)
        print(f"wrote {cap}\n      {ov}")
    if tmp:
        shutil.rmtree(tmp, ignore_errors=True)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
