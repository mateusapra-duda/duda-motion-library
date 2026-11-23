"""v13: the piece's scene.rml made lighter, nothing on screen changing (the approved rule of 2026-11-13: a delivery
carries only what it uses; the reviewer's hand-finished welcome email was 211 KB against 2.7 MB). p.build runs it last
(p.build(slim=False) keeps everything). From the pieces' slim.py (ask-your-agent, hero3-code v14, manage-hero2).

- The library brings its whole kit: the artboards, view models and fonts MAIN never reaches are dropped. Reached =
  named by id anywhere in what MAIN reaches (data-bind paths too).
- The fonts are cut to the characters the scene uses, plus all of printable ASCII (for an edit in the editor).
  Outlines and the default layout features stay; hinting goes (Rive doesn't use it). Written to slim/.
- v14, the images by kind (LEARNINGS 14: photos in WebP Q 85-90, avatars lossless). A photo becomes lossy WebP 90
  and its asset says webp, quality 0.9. A sharp image (an avatar or small image, a flat / UI capture, an image with
  transparency or few colours) becomes lossless WebP and its asset says png: lossy WebP blurs colour edges (4:2:0),
  and the editor's Export for Runtime encodes each image again as its asset's `format` says (PNG unless told), so
  png is how it stays lossless there too. A source that is already WebP is kept as it is (no second loss); its asset
  says webp 0.9 (lossy source) or png (lossless source). Anything else in doubt: whichever of the two encodings is
  smaller, lossless winning up to 15 % heavier.
- Per image, `QUALITY[<asset name or file name>]`: "lossless", "lossy" (Q 90), a number (lossy at that Q, 1-100) or
  "keep" (the file as it is). The asset name is "img.<artboard key>_<name>" for p.image (img.main_photo).
  `LOG` lists what each image became (the build's checks print it).
"""
import html
import os
import re
import xml.etree.ElementTree as ET

from fontTools import subset
from PIL import Image

WEBP_Q = 90
ASCII = {chr(c) for c in range(0x20, 0x7F)}
QUALITY = {}        # asset name ("img.main_photo") or file name ("photo.jpg") -> "lossless" | "lossy" | 1-100 | "keep"
LOG = []            # (file, what it became, bytes before, bytes after)
SMALL = 160         # px: an image this small (its longest side) is an avatar or an icon: lossless
FLAT = 0.6          # share of the pixels in its 16 commonest colours from which an image is flat (UI, a capture)


def reachable(root):
    """The top-level elements MAIN reaches, following every id an attribute names."""
    byid, owner = {}, {}
    for top in root:
        for el in top.iter():
            if "id" in el.attrib:
                byid[el.attrib["id"]] = el
                owner[el.attrib["id"]] = top
    main = next(a for a in root if a.tag == "Artboard" and a.attrib.get("name") == "MAIN")
    seen, todo = set(), [main]
    while todo:
        top = todo.pop()
        if id(top) in seen:
            continue
        seen.add(id(top))
        for el in top.iter():
            for k, v in el.attrib.items():
                if k != "id":
                    todo += [owner[r] for r in re.findall(r"\d+:\d+", v) if r in byid and id(owner[r]) not in seen]
    return seen


def prune(text):
    """The scene without the top-level elements MAIN doesn't reach (one per 4-space line, as rml.py writes them)."""
    root = ET.fromstring(text)
    keep = reachable(root)
    kept_ids = {t.attrib.get("id") for t in root if id(t) in keep}
    # a kept component keeps its ComponentAsset (nothing names the asset), so the editor lists it as a component
    keep |= {id(t) for t in root if t.tag == "ComponentAsset" and t.attrib.get("artboardId") in kept_ids}
    drop = {t.attrib["id"] for t in root if id(t) not in keep}
    lines, out, i = text.split("\n"), [], 0
    while i < len(lines):
        m = re.match(r'^    <(\w+)\b.*\bid="([^"]+)"', lines[i])
        if m and m.group(2) in drop:
            if not lines[i].rstrip().endswith("/>"):
                while not lines[i].startswith(f"    </{m.group(1)}>"):
                    i += 1
            i += 1
            continue
        out.append(lines[i])
        i += 1
    return "\n".join(out), len(drop)


def cut_fonts(here, text):
    chars = set(ASCII)
    for v in re.findall(r'="([^"]*)"', text):
        chars |= set(html.unescape(v))
    for f in re.findall(r'<FontAsset file="([^"]+)"', text):
        out = os.path.join("slim", os.path.basename(f))
        opts = subset.Options()
        opts.hinting = False
        font = subset.load_font(os.path.join(here, f), opts)
        sub = subset.Subsetter(opts)
        sub.populate(text="".join(sorted(chars)))
        sub.subset(font)
        subset.save_font(font, os.path.join(here, out), opts)
        text = text.replace(f'file="{f}"', f'file="{out}"')
    return text


def webp_lossless(path):
    """True when a .webp file is lossless (VP8L), False when lossy (VP8), from its RIFF chunks."""
    data = open(path, "rb").read(4096)
    i = 12
    while i + 8 <= len(data):
        tag = data[i:i + 4]
        if tag in (b"VP8L", b"VP8 "):
            return tag == b"VP8L"
        size = int.from_bytes(data[i + 4:i + 8], "little")
        i += 8 + size + (size & 1)
    return False


def kind(im):
    """("sharp" | "photo", why) of an image."""
    if max(im.size) <= SMALL:
        return "sharp", f"small ({im.size[0]}x{im.size[1]})"
    if im.mode in ("RGBA", "LA", "P") and im.convert("RGBA").getextrema()[3][0] < 250:
        return "sharp", "transparency"
    thumb = im.convert("RGB")
    if thumb.width * thumb.height > 640 * 640:
        thumb = thumb.resize((640, max(1, round(640 * thumb.height / thumb.width))), Image.NEAREST)
    colors = thumb.getcolors(maxcolors=1 << 16)
    if colors is not None and len(colors) <= 256:
        return "sharp", f"{len(colors)} colours"
    if colors is not None:
        top = sum(c for c, _ in sorted(colors, reverse=True)[:16]) / (thumb.width * thumb.height)
        if top >= FLAT:
            return "sharp", f"flat ({top:.0%} in 16 colours)"
    return "photo", ""


def _cache(here, data=None):
    """slim/.images.json: each image's decision, so a build doesn't encode it again (the name starts with a dot: the
    Rive CLI doesn't read it)."""
    import json
    path = os.path.join(here, "slim", ".images.json")
    if data is not None:
        json.dump(data, open(path, "w"), indent=0)
        return data
    try:
        return json.load(open(path))
    except (OSError, ValueError):
        return {}


def _asset_attrs(tag, file, fmt, q=None):
    attrs = f'file="{file}" format="{fmt}"' + (f' quality="{q}"' if q is not None else "")
    return re.sub(r'file="[^"]*"(?: format="[^"]*")?(?: quality="[^"]*")?', attrs, tag, count=1)


def photos(here, text):
    """Each image by its kind (module doc): photos lossy WebP 90, sharp ones lossless; their assets say how the
    editor's export encodes them again (webp 0.9, or png for the lossless)."""
    LOG.clear()
    done = {}
    for tag in re.findall(r'<ImageAsset [^>]*>', text):
        m = re.search(r'file="([^"]+)"', tag)
        name = (re.search(r' name="([^"]*)"', tag) or [None, ""])[1]
        if not m:
            continue
        f = m.group(1)
        if f in done:           # the same file under another asset: the same encoding
            text = text.replace(tag, _asset_attrs(tag, *done[f]))
            continue
        src = os.path.join(here, f)
        ext = os.path.splitext(f)[1].lower()
        if ext not in (".png", ".jpg", ".jpeg", ".webp") or not os.path.exists(src):
            continue
        want = QUALITY.get(name, QUALITY.get(os.path.basename(f), QUALITY.get(f)))
        before = os.path.getsize(src)
        im = Image.open(src)
        im.load()
        if want == "keep" or (ext == ".webp" and want is None):
            lossless = webp_lossless(src) if ext == ".webp" else ext == ".png"
            new = _asset_attrs(tag, f, "png" if lossless else ("webp" if ext == ".webp" else "jpeg"),
                               None if lossless else WEBP_Q / 100)
            LOG.append((f, f"kept ({'lossless' if lossless else 'lossy'} {ext[1:]})", before, before))
            done[f] = (f, "png" if lossless else ("webp" if ext == ".webp" else "jpeg"),
                       None if lossless else WEBP_Q / 100)
            text = text.replace(tag, new)
            continue
        out = os.path.join("slim", os.path.splitext(os.path.basename(f))[0] + ".webp")
        dst = os.path.join(here, out)
        stamp = f"{f}|{os.path.getmtime(src)}|{before}|{want}"
        cache = _cache(here)
        if stamp in cache and os.path.exists(dst):      # decided and encoded in an earlier build
            k, why, q = cache[stamp]
        else:
            rgb = im if im.mode in ("RGB", "RGBA") else im.convert("RGBA" if "A" in im.getbands() or im.mode == "P"
                                                                     else "RGB")
            if want in ("lossless", "lossy") or isinstance(want, (int, float)):
                why, k = "asked", "sharp" if want == "lossless" else "photo"
                q = int(want) if isinstance(want, (int, float)) else WEBP_Q
            else:
                k, why = kind(im)
                q = WEBP_Q
            if k == "photo" and want is None:   # in doubt (a photo of flat things): lossless if it costs <= 15 % more
                import io
                a, b = io.BytesIO(), io.BytesIO()
                rgb.save(a, "WEBP", lossless=True, method=4)
                rgb.save(b, "WEBP", quality=q, method=4)
                if a.tell() <= 1.15 * b.tell():
                    k, why = "sharp", f"lossless costs {a.tell() / max(1, b.tell()) - 1:+.0%}"
            if k == "sharp":
                rgb.save(dst, "WEBP", lossless=True, method=6)
            else:
                rgb.save(dst, "WEBP", quality=q, method=6)
            cache[stamp] = (k, why, q)
            _cache(here, cache)
        done[f] = (out, "png") if k == "sharp" else (out, "webp", q / 100)
        new = _asset_attrs(tag, *done[f])
        what = f"lossless WebP ({why}; the editor's export: png)" if k == "sharp" else \
            f"lossy WebP {q}" + (f" ({why})" if why else "")
        LOG.append((f, what, before, os.path.getsize(dst)))
        text = text.replace(tag, new)
    return text


def run(here):
    """Slims here/scene.rml in place; returns how many top-level elements were dropped."""
    path = os.path.join(here, "scene.rml")
    text = open(path).read()
    os.makedirs(os.path.join(here, "slim"), exist_ok=True)
    text, dropped = prune(text)
    text = photos(here, cut_fonts(here, text))
    open(path, "w").write(text)
    return dropped
