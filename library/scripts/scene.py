"""What the scripts need to know about a piece built with the library: its name, its main artboard (size) and its
timeline (frames, fps), read from rive.yaml and scene.rml. Also where the rive and ffmpeg binaries are."""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "vendor"))
import bins  # noqa: E402


def info(proj):
    """(name, main artboard, width, height, frames, fps) of the piece in `proj` (built: scene.rml must exist)."""
    yml = open(os.path.join(proj, "rive.yaml")).read()
    name = re.search(r"^name:\s*\"?([^\"\n]+)\"?", yml, re.M).group(1).strip()
    main = re.search(r"^main:\s*\"?([^\"\n]+)\"?", yml, re.M).group(1).strip()
    s = open(os.path.join(proj, "scene.rml")).read()
    tag = re.search(r'<Artboard [^>]*name="%s"[^>]*>' % re.escape(main), s)
    if not tag:
        sys.exit(f"no artboard {main!r} in scene.rml: build the piece first")
    w = float(re.search(r' width="([\d.]+)"', tag.group(0)).group(1))
    h = float(re.search(r' height="([\d.]+)"', tag.group(0)).group(1))
    body = s[tag.end():]
    nxt = body.find("<Artboard ")
    anim = re.search(r'<LinearAnimation [^>]*name="Timeline"[^>]*>', body[:nxt if nxt >= 0 else None])
    frames = int(re.search(r'duration="(\d+)"', anim.group(0)).group(1)) if anim else 1
    fps = int(re.search(r'fps="(\d+)"', anim.group(0)).group(1)) if anim else 60
    return name, main, round(w), round(h), frames, fps


def rive():
    return bins.rive()


def ffmpeg():
    return bins.ffmpeg()
