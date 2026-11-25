"""backdrop_xl.py (v15e): a photo made larger by mirroring, so the camera can pull back past a scene's edge (a slow
zoom-out, a centred zoom cut) with the original untouched in the middle. From ma-novo-social's backdrop_xl.py (v06,
v13, v15: the right square's blurred photo).

- The photo is padded by mirroring (L, T, R, B px on each side).
- Only the new part is blurred (GaussianBlur 14): its weight ramps from 0 at the original's edge to 1 at 24 px out,
  so the mirror's fold softens and the original stays pixel-exact.
- Saved lossless (WebP): a lossy save would change the original's pixels too (PIL and Rive decode lossy WebP
  differently: up to 7/255 in ma-novo-social v06).
- It prints the max difference inside the original region, read back from the file: it must be 0 (exit 1 if not).
Then give the scene's image the new size and move what sits on it by (L, T).

usage: .venv/bin/python -I <lib>/scripts/backdrop_xl.py <src image> <dst.webp> L T R B [--blur 14] [--ramp 24]
"""
import argparse
import sys

import numpy as np
from PIL import Image, ImageFilter


def extend(src, dst, L, T, R, B, blur=14.0, ramp=24.0):
    """Write the extended photo; returns (its size (w, h), the max difference inside the original region)."""
    im = np.asarray(Image.open(src).convert("RGB")).astype(np.float32)
    h, w, _ = im.shape
    pad = np.pad(im, ((T, B), (L, R), (0, 0)), mode="symmetric")
    soft = np.asarray(Image.fromarray(pad.clip(0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(blur)))
    yy, xx = np.mgrid[0:h + T + B, 0:w + L + R]
    dx = np.maximum(np.maximum(L - xx, xx - (L + w - 1)), 0)
    dy = np.maximum(np.maximum(T - yy, yy - (T + h - 1)), 0)
    wgt = np.clip(np.hypot(dx, dy) / ramp, 0, 1)[..., None]      # 0 inside the original, 1 from `ramp` px out
    out = pad * (1 - wgt) + soft.astype(np.float32) * wgt
    Image.fromarray(out.round().clip(0, 255).astype(np.uint8)).save(dst, "WEBP", lossless=True, method=6)
    back = np.asarray(Image.open(dst).convert("RGB")).astype(np.int16)[T:T + h, L:L + w]
    return (w + L + R, h + T + B), int(np.abs(back - im.astype(np.int16)).max())


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("src")
    ap.add_argument("dst")
    for k in ("L", "T", "R", "B"):
        ap.add_argument(k, type=int)
    ap.add_argument("--blur", type=float, default=14.0)
    ap.add_argument("--ramp", type=float, default=24.0)
    a = ap.parse_args()
    assert a.dst.lower().endswith(".webp"), "the extension is saved as lossless WebP: give a .webp"
    size, diff = extend(a.src, a.dst, a.L, a.T, a.R, a.B, a.blur, a.ramp)
    print(f"wrote {a.dst}: {size[0]}x{size[1]} (pad L{a.L} T{a.T} R{a.R} B{a.B}, blur {a.blur:g}, ramp {a.ramp:g} px); "
          f"max diff inside the original region: {diff}")
    if diff:
        sys.exit(1)


if __name__ == "__main__":
    main()
