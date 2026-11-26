"""photo.py (v16): one photo cut into parts, for p.photo (patterns.py) and the generation's photo pass.

The blind review of 2026-11-26 (P4): "the product images and the word SOLÉA inside the site should have a colour
effect too", and the praised round drew the hero in layers (the background, the letters, the bottles on top), "a
more complex animation than animating everything together". A design often has that hero as ONE photo; this cuts it:

- each part (a bottle, the big word) is a rectangle or a polygon in the photo's own pixels, optionally keyed to its
  colour inside that shape (key="light": only the white letters of a word, not the wall between them), less what
  the parts listed after it (in front of it) cover;
- the plate (v16a): the photo with every part OUT OF FOCUS in it (each part blurred on its own over what is behind
  it, like depth of field), so each part comes in by coming into focus: never a hole. v16 took the parts out and
  filled the holes from around them: the fills showed as soft smudges on the wall for ~30 frames before the objects
  came in, and through them while they faded in (the manager's review of 2026-11-26);
- each part: a layer that turns the state before it (the parts before it sharp, it and the ones after it out of
  focus) into the state after it, exactly and in register (nothing scales); the last state is the photo itself;
- ink twins (made when the generation runs, in its own colours): a near-white or near-black part (letters) cannot
  be saturated, so it gets the texts' colour pass instead: a copy of its mask in the pass's orange and pink.

Only numpy and Pillow. Files go to <piece>/build/photo/ (named by a hash of the source and the parts, made once).
"""
import hashlib
import json
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

VERSION = 7
FOCUS = 0.012       # v16a: the plate's out-of-focus blur, a fraction of the photo's long side (~29 px on a 2400 px
#                     photo, ~8 px on screen for a hero ~650 px wide): a part reads as itself, soft, before its turn
GROW = 16           # px (source): behind a part, the photo is filled from around it over its mask grown this much
#                     (seen only through its blurred edge). v16a: 16 (v16: 8): a polygon traced ~6 px inside the
#                     object (round C's pump) left its dark edge in the fill's soft rim, a sharp 1 px line through
#                     the blur
GRAIN = 4           # px (source): that fill gets the photo's grain finer than this (grain())
EPS = 1.5 / 255     # v16a: a part's layer covers where its state differs from the one before it by more than this
EDGE = 1.0          # px (source): a part's edge softness (its mask blurred this much)
NEUTRAL = 0.10      # a part whose mean chroma (max - min channel, 0-1) is below this is neutral: an ink pass, not
#                     a saturation pass (white or black letters stay white or black under a saturation layer)
TWIN_SCALE = 0.5    # the ink twins at half the source's resolution (they are soft and fade out)
TWIN_BLUR = 2.0     # px (source): the ink twins' softness (the texts' Feather 4 -> 0 as it starts, at 2x)


def _smooth(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3 - 2 * x)


def _shape_mask(size, spec):
    """A part's shape (rect (x, y, w, h) or polygon [(x, y), ...]) as a float mask, anti-aliased (4x)."""
    w, h = size
    k = 4
    im = Image.new("L", (w * k, h * k), 0)
    d = ImageDraw.Draw(im)
    if _is_rect(spec):
        x, y, rw, rh = spec
        d.rectangle([x * k, y * k, (x + rw) * k - 1, (y + rh) * k - 1], fill=255)
    else:
        d.polygon([(px * k, py * k) for px, py in spec], fill=255)
    im = im.resize((w, h), Image.BOX)
    return np.asarray(im).astype(np.float32) / 255.0


def _is_rect(spec):
    return isinstance(spec, (tuple, list)) and len(spec) == 4 and all(isinstance(v, (int, float)) for v in spec)


def norm(spec):
    """A part as {"shape": rect or polygon, "key": None | "light" | "dark" | "#rrggbb", "anchor": "bottom" | "center"}."""
    if isinstance(spec, dict):
        shape = spec.get("rect") or spec.get("poly") or spec.get("box")
        if spec.get("box") is not None:          # (x0, y0, x1, y1)
            x0, y0, x1, y1 = spec["box"]
            shape = (x0, y0, x1 - x0, y1 - y0)
        assert shape is not None, "a photo part: rect=(x, y, w, h), box=(x0, y0, x1, y1) or poly=[(x, y), ...]"
        return {"shape": [tuple(p) for p in shape] if not _is_rect(shape) else tuple(shape),
                "key": spec.get("key"), "anchor": spec.get("anchor"), "tol": spec.get("tol")}
    assert _is_rect(spec) or (isinstance(spec, (list, tuple)) and len(spec) >= 3), \
        "a photo part: (x, y, w, h), [(x, y), ...] or a dict"
    return {"shape": tuple(spec) if _is_rect(spec) else [tuple(p) for p in spec], "key": None, "anchor": None,
            "tol": None}


def _key_mask(rgb, key, tol=None):
    """Inside a part's shape, the pixels of its own colour: "light" (white letters: the darkest channel high and
    little chroma), "dark", or '#rrggbb' (within tol of it)."""
    mx, mn = rgb.max(2), rgb.min(2)
    if key == "light":
        lo, hi = tol or (0.78, 0.92)
        return _smooth((mn - lo) / (hi - lo)) * _smooth((0.25 - (mx - mn)) / 0.15)
    if key == "dark":
        lo, hi = tol or (0.22, 0.35)
        return _smooth((hi - mx) / (hi - lo))
    c = np.array([int(key[i:i + 2], 16) / 255 for i in (1, 3, 5)], dtype=np.float32)
    d = np.sqrt(((rgb - c) ** 2).sum(2))
    lo, hi = tol or (0.08, 0.18)
    return _smooth((hi - d) / (hi - lo))


def _blur(mask, r):
    if r <= 0:
        return mask
    im = Image.fromarray((np.clip(mask, 0, 1) * 255).astype(np.uint8))
    return np.asarray(im.filter(ImageFilter.GaussianBlur(r))).astype(np.float32) / 255.0


def _grow(mask, r):
    if r <= 0:
        return mask
    im = Image.fromarray((np.clip(mask, 0, 1) * 255).astype(np.uint8))
    return np.asarray(im.filter(ImageFilter.MaxFilter(2 * int(r) + 1))).astype(np.float32) / 255.0


def _down(a):
    h, w = a.shape[:2]
    a = np.pad(a, ((0, h % 2), (0, w % 2)) + ((0, 0),) * (a.ndim - 2), mode="edge")
    return (a[0::2, 0::2] + a[1::2, 0::2] + a[0::2, 1::2] + a[1::2, 1::2]) / 4


def _up(a, shape):
    h, w = shape[:2]
    im = [Image.fromarray(a[..., i].astype(np.float32), mode="F").resize((w, h), Image.BILINEAR)
          for i in range(a.shape[2])]
    return np.stack([np.asarray(x) for x in im], 2)


def fill(rgb, known):
    """The holes (known 0) filled from their surroundings: a push-pull pyramid (premultiplied box averages down,
    each level over the one below it on the way up). rgb HxWx3 0-1, known HxW 0-1."""
    levels = []
    i_, k_ = rgb * known[..., None], known.copy()
    while min(i_.shape[:2]) > 2:
        levels.append((i_, k_))
        i_, k_ = _down(i_), _down(k_)
    col = i_ / np.maximum(k_, 1e-6)[..., None]
    if (k_ <= 1e-6).any():
        col[k_ <= 1e-6] = (rgb * known[..., None]).sum((0, 1)) / max(known.sum(), 1e-6)
    for i_, k_ in reversed(levels):
        u = _up(col, i_.shape)
        kk = np.clip(k_ * 4, 0, 1)[..., None]          # a quarter known is enough to trust a level's own colour
        own = i_ / np.maximum(k_, 1e-6)[..., None]
        col = own * kk + u * (1 - kk)
    return col


def _box(a, r):
    """A box blur of radius r (twice: close to a Gaussian), on HxW or HxWxC floats."""
    for _ in range(2):
        for ax in (0, 1):
            n = a.shape[ax]
            c = np.cumsum(np.pad(a, [(r + 1, r) if i == ax else (0, 0) for i in range(a.ndim)], mode="edge"),
                          axis=ax)
            a = (np.take(c, np.arange(2 * r + 1, 2 * r + 1 + n), axis=ax) -
                 np.take(c, np.arange(0, n), axis=ax)) / (2 * r + 1)
    return a


def grain(rgb, known, hole, r=GRAIN):
    """The photo's fine grain (what a blur of radius r takes away) copied into the hole from known pixels nearby
    (the nearest of a few offsets, out to the far side of a big hole): a smooth fill on a textured wall reads as a
    ghost of what was cut out."""
    detail = rgb - _box(rgb, r)
    energy = _box(np.abs(detail).mean(2), 4 * r)
    calm = (energy <= np.percentile(energy[known > 0.99], 50)) & (known > 0.99)   # a wall's grain, not an edge
    calm = _box(calm.astype(np.float32), 2 * r) > 0.999
    detail = np.clip(detail, -0.04, 0.04)
    out = np.zeros_like(rgb)
    need = hole > 0.004
    got = np.zeros(hole.shape, bool)
    for d in (16, 32, 64, 128, 256, 512, 1024):
        for dx, dy in ((d, 0), (-d, 0), (0, d), (0, -d)):
            ok = np.roll(calm, (-dy, -dx), (0, 1))
            take = need & ~got & ok
            if take.any():
                out[take] = np.roll(detail, (-dy, -dx), (0, 1))[take]
                got |= take
    return out


def _over(base, rgb_pm, a):
    """`base` (HxWx3) under a premultiplied layer (rgb_pm HxWx3, a HxW)."""
    return base * (1 - a[..., None]) + rgb_pm


def _states(rgb, masks):
    """v16a: the plate and one layer per part (rgb, alpha), so that part i fading in over the plate and the parts
    before it turns state i-1 into state i, exactly. State i: the parts up to i sharp, the ones after it out of
    focus (each blurred on its own, premultiplied, over what is behind it: depth of field, not a blurred photo), and
    the photo's own pixels wherever no part still out of focus reaches; the last state is the photo itself. Behind
    the parts, the photo filled from around them (seen only through a blurred part's soft edge). Returns
    (plate, [(rgb, alpha)], blur radius)."""
    H, W = masks[0].shape
    R = max(1.0, FOCUS * max(W, H))
    r = max(1, int(round(R / 0.816)))           # two box passes of radius r: a Gaussian of sigma ~0.816 r
    hole = _blur(_grow(np.maximum.reduce(masks), GROW), 1.0)
    bg = fill(rgb, 1 - hole) + grain(rgb, 1 - hole, hole)
    bg = rgb * (1 - hole[..., None]) + bg * hole[..., None]
    sharp = [(rgb * m[..., None], m) for m in masks]
    soft = [(_box(rgb * m[..., None], r), np.clip(_box(m, r), 0, 1)) for m in masks]
    n = len(masks)
    reach = []                                     # where the parts after i, out of focus, still change anything
    for i in range(n + 1):
        u = np.maximum.reduce([soft[j][1] for j in range(i, n)]) if i < n else np.zeros((H, W), np.float32)
        reach.append(_blur(_grow((u > 0.002).astype(np.float32), 3), 1.0))
    states = []
    for i in range(n + 1):
        x = bg
        for j in range(n):
            x = _over(x, *(sharp[j] if j < i else soft[j]))
        k = reach[i]
        states.append(rgb * (1 - k[..., None]) + x * k[..., None])
    layers = []
    for i in range(1, n + 1):
        d = (np.abs(states[i] - states[i - 1]).max(2) > EPS).astype(np.float32)
        a = _blur(_grow(d, 3), 1.0)
        a[d > 0] = 1.0
        layers.append((states[i], a))
    return states[0], layers, R


def prepare(here, key, src, parts):
    """Cuts `src` (a path) into a plate and parts. parts: {name: spec} back to front. Returns {"size": (w, h),
    "plate": path, "parts": [{"name", "file", "box": (x0, y0, x1, y1) source px, "anchor": (x, y) source px,
    "neutral": bool, "mask": path (the part's alpha, for its ink twins)}]}. Made once (build/photo/<key>_<hash>)."""
    names = list(parts)
    specs = [norm(parts[n]) for n in names]
    data = open(src, "rb").read()
    h = hashlib.sha1(data + json.dumps([VERSION, names, specs], default=str).encode()).hexdigest()[:10]
    out = os.path.join(here, "build", "photo")
    os.makedirs(out, exist_ok=True)
    meta_f = os.path.join(out, f"{key}_{h}.json")
    try:
        meta = json.load(open(meta_f))
        if all(os.path.exists(p) for p in [meta["plate"]] + [q["file"] for q in meta["parts"]]):
            return meta
    except (OSError, ValueError, KeyError):
        pass
    im = Image.open(src)
    im.load()
    rgb = np.asarray(im.convert("RGB")).astype(np.float32) / 255.0
    W, H = im.size
    masks = []
    for sp in specs:
        m = _shape_mask((W, H), sp["shape"])
        if sp["key"]:
            m = m * _key_mask(rgb, sp["key"], sp["tol"])
        masks.append(m)
    # each part less what the parts in front of it cover (listed after it)
    front = np.zeros((H, W), np.float32)
    for i in range(len(masks) - 1, -1, -1):
        m = masks[i] * (1 - front)
        front = np.maximum(front, masks[i])
        masks[i] = _blur(m, EDGE) if EDGE else m
    meta = {"size": [W, H], "parts": []}
    plate, layers, R = _states(rgb, masks)
    pf = os.path.join(out, f"photo_{key}_plate_{h}.png")
    Image.fromarray((np.clip(plate, 0, 1) * 255 + 0.5).astype(np.uint8)).save(pf, optimize=True)
    meta["plate"] = pf
    meta["focus"] = round(R, 2)
    for n, sp, m, (lrgb, al) in zip(names, specs, masks, layers):
        assert (m > 1 / 255).any(), f"photo part {n!r}: nothing inside its shape (or its key)"
        ys, xs = np.nonzero((al > 1 / 255) | (m > 1 / 255))
        x0, y0 = max(0, xs.min() - 2), max(0, ys.min() - 2)
        x1, y1 = min(W, xs.max() + 3), min(H, ys.max() + 3)
        a = m[y0:y1, x0:x1]                       # its own shape: the ink twins and its chroma
        cut = np.dstack([lrgb[y0:y1, x0:x1], al[y0:y1, x0:x1]])
        f = os.path.join(out, f"photo_{key}_{_slug(n)}_{h}.png")
        Image.fromarray((np.clip(cut, 0, 1) * 255 + 0.5).astype(np.uint8), "RGBA").save(f, optimize=True)
        mf = os.path.join(out, f"photo_{key}_{_slug(n)}_{h}_mask.png")
        Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8), "L").save(mf, optimize=True)
        wsum = max(a.sum(), 1e-6)
        sub = rgb[y0:y1, x0:x1]
        chroma = float(((sub.max(2) - sub.min(2)) * a).sum() / wsum)
        anchor = sp["anchor"] or ("center" if sp["key"] else "bottom")
        x0, y0, x1, y1 = int(x0), int(y0), int(x1), int(y1)
        ax = (x0 + x1) / 2
        ay = float(y1) if anchor == "bottom" else (y0 + y1) / 2
        meta["parts"].append({"name": n, "file": f, "mask": mf, "box": [x0, y0, x1, y1],
                              "anchor": [ax, ay], "neutral": chroma < NEUTRAL, "chroma": round(chroma, 3)})
    json.dump(meta, open(meta_f + ".tmp", "w"), indent=1)
    os.replace(meta_f + ".tmp", meta_f)
    return meta


def ink_twin(mask_file, colour, out_dir=None):
    """A part's ink twin: its mask (softened by TWIN_BLUR, at TWIN_SCALE) filled with `colour` (ARGB 'FFrrggbb' or
    '#rrggbb'). Returns (path, scale it was made at)."""
    c = colour[-6:]
    out_dir = out_dir or os.path.dirname(mask_file)
    f = os.path.join(out_dir, f"{os.path.splitext(os.path.basename(mask_file))[0][:-5]}_ink{c.lower()}.png")
    if not os.path.exists(f):
        m = Image.open(mask_file).convert("L")
        w, h = max(1, round(m.width * TWIN_SCALE)), max(1, round(m.height * TWIN_SCALE))
        m = m.filter(ImageFilter.GaussianBlur(TWIN_BLUR)).resize((w, h), Image.LANCZOS)
        rgb = tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))
        im = Image.new("RGBA", (w, h), rgb + (0,))
        im.putalpha(m)
        im.save(f, optimize=True)
    return f, TWIN_SCALE


def _slug(s):
    return "".join(ch if ch.isalnum() else "_" for ch in str(s)).strip("_").lower() or "part"
