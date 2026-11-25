"""social_bg.py (v15e): the background of the designers' social posts (Figma i6SoOBQMUCQm6FP76rbPrY, "banner"
2068:5713), drawn at any size W x H: never crop one format from another (ma-novo-social v08: the 1:1 cut from the 4:5
had the wrong gradient angle). From ma-novo-social's bg_social.py.

- A CSS linear gradient #3A7384 (6.18 %) -> #77ABAF (103.06 %). Its angle depends on the frame's aspect: Figma keeps
  the gradient in the frame's own (normalised) space, so the CSS angle is 180 - atan(K * H / W), K from the 1:1 frame
  (167.48 deg); that gives the 4:5 banner's 164.48 deg too (the script prints the check).
- A #3A7384 rectangle 2583 x 1541 rotated 29 deg with a 150 px blur over the bottom-left (px of a 1080-wide frame,
  from its top-left; another width scales the whole drawing).
- A per-channel colour fit to the Figma render, then a fine grain (2.4/255, seed 7), as in the Figma render: it also
  keeps H.264 from banding the gradient.
Saved as lossless WebP.

usage: .venv/bin/python -I <lib>/scripts/social_bg.py W H out.webp [--seed 7]
       (social.py calls write(W, H, path) for each format it builds)
"""
import argparse
import math

import numpy as np
from PIL import Image, ImageFilter

REF_W = 1080
ANGLE_1X1 = 167.47773082292497            # Figma's CSS for the 1:1 frame ("Section 3" 2069:5825)
ANGLE_4X5 = 164.48385150447177            # ...and for the 4:5 banner (2068:5713): the check of angle()
K = math.tan(math.radians(180 - ANGLE_1X1))
C0, C1 = np.array([58, 115, 132.]), np.array([119, 171, 175.])
STOPS = (0.061775, 1.0306)
BLOB = dict(w=2583.01, h=1541, rot=29, cx=-1454 + 3006.236 / 2, cy=520 + 2599.949 / 2, sigma=150)
# per-channel fit (scale, offset) of the model to the Figma render (mean error = the grain, ~2/255)
FIT = [(0.984, 10.08), (0.9833, 8.29), (0.9834, 7.83)]
GRAIN = 2.4


def angle(W, H):
    """The CSS gradient angle (deg) of the banner's gradient in a W x H frame."""
    return 180 - math.degrees(math.atan(K * H / W))


def field(W, H):
    """The background without grain, float RGB (H, W, 3): drawn at 1080 wide (the designers' px), scaled to W."""
    Wr = REF_W
    Hr = H if W == REF_W else round(H * REF_W / W)
    th = math.radians(angle(W, H))
    dx, dy = math.sin(th), -math.cos(th)
    L = abs(Wr * dx) + abs(Hr * dy)
    yy, xx = np.mgrid[0:Hr, 0:Wr].astype(float)
    t = ((xx + .5 - Wr / 2) * dx + (yy + .5 - Hr / 2) * dy) / L + 0.5
    u = np.clip((t - STOPS[0]) / (STOPS[1] - STOPS[0]), 0, 1)[..., None]
    grad = C0 + (C1 - C0) * u
    S, pad = 4, 150
    h, w = Hr // S + 2 * pad, Wr // S + 2 * pad
    Y, X = np.mgrid[0:h, 0:w].astype(float)
    X, Y = (X - pad) * S, (Y - pad) * S
    r = np.radians(BLOB["rot"])
    xr = (X - BLOB["cx"]) * np.cos(r) + (Y - BLOB["cy"]) * np.sin(r)
    yr = -(X - BLOB["cx"]) * np.sin(r) + (Y - BLOB["cy"]) * np.cos(r)
    inside = ((np.abs(xr) <= BLOB["w"] / 2) & (np.abs(yr) <= BLOB["h"] / 2)).astype(np.uint8) * 255
    al = np.asarray(Image.fromarray(inside).filter(ImageFilter.GaussianBlur(BLOB["sigma"] / S))).astype(float)
    al = al[pad:pad + Hr // S + 1, pad:pad + Wr // S + 1]
    al = np.asarray(Image.fromarray(al.astype(np.uint8)).resize((Wr, Hr), Image.BILINEAR)).astype(float)[..., None] / 255
    out = grad * (1 - al) + C0 * al
    for k, (s, o) in enumerate(FIT):
        out[..., k] = out[..., k] * s + o
    if (Wr, Hr) != (W, H):
        out = np.stack([np.asarray(Image.fromarray(out[..., k].astype(np.float32), "F").resize((W, H), Image.BICUBIC))
                        for k in range(3)], axis=-1)
    return out


def write(W, H, path, seed=7):
    """Draw the background at W x H, add the grain and save it as lossless WebP. Returns the angle used."""
    rng = np.random.default_rng(seed)
    img = field(W, H) + rng.normal(0, GRAIN, (H, W, 1))
    Image.fromarray(img.round().clip(0, 255).astype(np.uint8)).save(path, "WEBP", lossless=True, method=6)
    return angle(W, H)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("W", type=int)
    ap.add_argument("H", type=int)
    ap.add_argument("out")
    ap.add_argument("--seed", type=int, default=7)
    a = ap.parse_args()
    ang = write(a.W, a.H, a.out, a.seed)
    print(f"wrote {a.out}: {a.W}x{a.H}, gradient {ang:.4f} deg, lossless WebP "
          f"(check: 4:5 by the formula {angle(1080, 1350):.5f} deg, Figma {ANGLE_4X5:.5f})")


if __name__ == "__main__":
    main()
