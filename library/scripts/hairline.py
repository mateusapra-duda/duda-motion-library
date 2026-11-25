"""Does a thin line flicker? (v15e, LEARNINGS 13) Renders ~30 frames in a row and reads the line's brightness across
them: a line under ~1 px on screen, in a zoom or a slow slide, falls whole on a pixel row in one frame (bright) and
across two in the next (dim), a flicker no still shows. checks.py's [hairline] note says which line and when.

usage: python lib/biblioteca-<v>/scripts/hairline.py <piece_dir> --at <s> (--col X --rows Y0:Y1 | --row Y --cols X0:X1)
                                                     [--frames 30] [--scale 1]
  --col X --rows Y0:Y1: a column of pixels crossing a horizontal line (--row/--cols for a vertical one), in the main
  artboard's px; the span must hold that one line and plain background (the line may move inside it).
  --scale: render size as a multiple of the artboard (the video's: 2 for render_mp4's default).
Per frame: the line's peak (its brightest difference from the span's background, 0-255), where it is, and how much
of it there is (the sum, which stays put while the line only moves). The verdict is the peak's swing across the
frames: FLICKERS over 30/255 (the ma-novo-social line that flickered swung ~100; its fix, 1.2 px at 25 %, ~20, and
ran smooth). The fix: 1.5 px or more on screen, the opacity down in proportion.
"""
import argparse
import os
import shutil
import sys
import tempfile

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # python -I leaves the script's folder out
import render_mp4  # noqa: E402
import scene  # noqa: E402

SWING = 30


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("proj")
    ap.add_argument("--at", type=float, required=True)
    ap.add_argument("--frames", type=int, default=30)
    ap.add_argument("--col", type=float)
    ap.add_argument("--rows")
    ap.add_argument("--row", type=float)
    ap.add_argument("--cols")
    ap.add_argument("--scale", type=float, default=1.0)
    a = ap.parse_args()
    assert (a.col is not None and a.rows) or (a.row is not None and a.cols), "--col X --rows Y0:Y1, or --row Y --cols X0:X1"
    from PIL import Image
    proj = os.path.abspath(a.proj)
    _, _, aw, ah, total, fps = scene.info(proj)
    w, h = round(aw * a.scale), round(ah * a.scale)
    f0 = round(a.at * fps)
    frames = [f for f in range(f0, f0 + a.frames) if f < total]
    tmp = tempfile.mkdtemp(prefix="hairline")
    try:
        missing, errs = render_mp4.capture(scene.rive(), proj, tmp, frames, w, h,
                                           None if (w, h) == (aw, ah) else "contain")
        if missing:
            sys.exit(f"{len(missing)} frames failed: {errs[:3]}")
        rows = []
        for f in frames:
            im = np.asarray(Image.open(f"{tmp}/f{f:05d}.png").convert("L"), dtype=float)
            if a.col is not None:
                y0, y1 = (round(float(v) * a.scale) for v in a.rows.split(":"))
                prof = im[y0:y1, round(a.col * a.scale)]
                base = y0
            else:
                x0, x1 = (round(float(v) * a.scale) for v in a.cols.split(":"))
                prof = im[round(a.row * a.scale), x0:x1]
                base = x0
            d = np.abs(prof - np.median(prof))
            i = int(np.argmax(d))
            rows.append((f, float(d[i]), (base + i) / a.scale, float(d.sum())))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    peaks = np.array([r[1] for r in rows])
    sums = np.array([r[3] for r in rows])
    for f, pk, pos, sm in rows:
        print(f"  f{f:5d}  peak {pk:6.1f}  at {pos:8.2f}  sum {sm:7.1f}")
    swing = float(peaks.max() - peaks.min())
    verdict = "FLICKERS" if swing > SWING else "steady"
    print(f"{len(rows)} frames from {a.at:.2f} s: peak {peaks.min():.0f}-{peaks.max():.0f} (swing {swing:.0f}/255, "
          f"{swing / max(peaks.mean(), 1e-6) * 100:.0f} % of its mean), sum {sums.min():.0f}-{sums.max():.0f}: "
          f"{verdict}" + (" (make it 1.5 px or more on screen, the opacity down in proportion)"
                          if verdict == "FLICKERS" else ""))
    sys.exit(1 if verdict == "FLICKERS" else 0)


if __name__ == "__main__":
    main()
