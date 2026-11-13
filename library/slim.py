"""v13: the piece's scene.rml made lighter, nothing on screen changing (the approved rule of 2026-11-13: a delivery
carries only what it uses; the reviewer's hand-finished welcome email was 211 KB against 2.7 MB). p.build runs it last
(p.build(slim=False) keeps everything). From the pieces' slim.py (ask-your-agent, hero3-code v14, manage-hero2).

- The library brings its whole kit: the artboards, view models and fonts MAIN never reaches are dropped. Reached =
  named by id anywhere in what MAIN reaches (data-bind paths too).
- The fonts are cut to the characters the scene uses, plus all of printable ASCII (for an edit in the editor).
  Outlines and the default layout features stay; hinting goes (Rive doesn't use it). Written to slim/.
- The photos (PNG / JPEG) become WebP 90, and their assets say WebP, quality 0.9: the editor's Export for Runtime
  encodes each image again as its asset's `format` says (PNG unless told).
"""
import html
import os
import re
import xml.etree.ElementTree as ET

from fontTools import subset
from PIL import Image

WEBP_Q = 90
ASCII = {chr(c) for c in range(0x20, 0x7F)}


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


def photos(here, text):
    """The JPEG/PNG images as WebP 90 (and WebP in the editor's export)."""
    for f in re.findall(r'<ImageAsset file="([^"]+\.(?:jpe?g|png|JPE?G|PNG))"', text):
        out = os.path.join("slim", os.path.splitext(os.path.basename(f))[0] + ".webp")
        Image.open(os.path.join(here, f)).save(os.path.join(here, out), "WEBP", quality=WEBP_Q, method=6)
        text = text.replace(f'file="{f}"', f'file="{out}" format="webp" quality="{WEBP_Q / 100}"')
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
