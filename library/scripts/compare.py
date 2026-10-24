"""Compare a frame of a piece with its Figma frame: the capture, the mean difference (target <= ~12/255), a 3 x 3
grid of differences (where it is off) and an overlay sheet to look at (Figma | Rive | 50 % mix | difference).
Works in any folder: it needs only the piece (build.py run once) and this bundle.

usage: python lib/biblioteca-<v>/scripts/compare.py <piece_dir> <figma.png> [--frame N] [--still capture.png]
  The Figma PNG is the storyboard frame exported at the artboard's size (1x) or any multiple of it; the capture is
  made at the PNG's size. --frame: the frame at 60 fps (default 0; a still pose: build it with that pose first).
  --still: compare a PNG you already have instead of capturing.
  Writes <piece>/build/compare/<figma name>_rive.png and _overlay.jpg.
"""
import argparse
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageChops, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # python -I leaves the script's folder out
import scene  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("proj")
    ap.add_argument("figma")
    ap.add_argument("--frame", type=int, default=0)
    ap.add_argument("--still")
    a = ap.parse_args()
    proj = os.path.abspath(a.proj)
    fig = Image.open(a.figma).convert("RGB")
    W, H = fig.size
    stem = os.path.splitext(os.path.basename(a.figma))[0]
    out = os.path.join(proj, "build", "compare")
    os.makedirs(out, exist_ok=True)
    cap = os.path.join(out, f"{stem}_rive.png")
    if a.still:
        Image.open(a.still).convert("RGB").resize((W, H)).save(cap)
    else:
        _, _, w, h, _, _ = scene.info(proj)
        if abs(W / H - w / h) > 0.01:
            print(f"note: the Figma PNG is {W}x{H}, the artboard {w}x{h}: different proportions")
        r = subprocess.run([scene.rive(), ".", f"--screenshot={cap}", f"--advance={a.frame + 1}", f"--viewport={W}x{H}"],
                           cwd=proj, capture_output=True, text=True, timeout=180)
        if not os.path.exists(cap):
            sys.exit("the capture failed:\n" + (r.stdout + r.stderr)[-1500:])
    riv = Image.open(cap).convert("RGB").resize((W, H))
    d = np.abs(np.asarray(fig, dtype=float) - np.asarray(riv, dtype=float)).mean(axis=2)
    print(f"mean difference: {d.mean():.1f}/255 ({'ok' if d.mean() <= 12 else 'over ~12: look at the overlay'})")
    print("by area (top to bottom, left to right):")
    for r_ in range(3):
        cells = [d[r_ * H // 3:(r_ + 1) * H // 3, c * W // 3:(c + 1) * W // 3].mean() for c in range(3)]
        print("   " + "  ".join(f"{v:5.1f}" for v in cells))
    diff = ImageChops.difference(fig, riv).point(lambda v: min(255, v * 3))
    tiles = [("Figma", fig), ("Rive", riv), ("50 % mix", Image.blend(fig, riv, 0.5)), ("difference x3", diff)]
    s = min(1.0, 900 / W)
    tw, th = int(W * s), int(H * s)
    sheet = Image.new("RGB", (tw * 2, th * 2), "white")
    for i, (label, im) in enumerate(tiles):
        x, y = (i % 2) * tw, (i // 2) * th
        sheet.paste(im.resize((tw, th)), (x, y))
        ImageDraw.Draw(sheet).text((x + 8, y + 6), label, fill="red")
    ov = os.path.join(out, f"{stem}_overlay.jpg")
    sheet.save(ov, quality=88)
    print(f"wrote {cap}\n      {ov}")


if __name__ == "__main__":
    main()
