"""social.py (v15e): a social video (1:1 and 4:5) cut from a hero that is already built, with the designers' opening
and end cards. From ma-novo-social v18 (2026-11-25, 18 versions with Mateus and the boss): its social.py,
bg_social.py and backdrop_xl.py, generalised (APRENDIZADOS part B, items 1, 2 and 6).

    v = Social("pecas/ma-novo", "pecas/my-social", nest={"4x5": "MAIN 4x5"})        # the hero's folder, the output's
    v.opening("Grow your clients with\\nnative Marketing\\nAutomation", hero_in=170)  # the hero comes in at f170
    v.play((950, 984), (0, 828))                         # stretches of the hero's MAIN Timeline, in order
    m = lambda M: v.frame_of(M, 1)                       # MAIN frame (of the 2nd stretch) -> frame of the video
    v.shot(0, {"1x1": (490.05, 461.55, 318.9), "4x5": (490.05, 572.69, 318.9)})   # (cx, cy, width) in MAIN px
    v.move(m(110), m(212), {"1x1": (347.5, 319, 604), "4x5": (347.5, 394.5, 604)})  # the hero's zoom-out (matrix blend)
    v.slide(m(429), {"1x1": (1006, 319, 604), "4x5": (945.5, 318.59, 488.83)})     # match cut by position
    v.end_card("duda.co/marketing-automation", at=m(800), room=(673, -168, 1356, 776))   # centred zoom cut + end card
    v.build()                                            # scene.rml (+ rive.yaml) and build/social.json
(the whole ma-novo-social v18, with its clip, overlay and worlds: QUICKSTART "A social video from a hero").

What it writes (one Rive project, in `out`):
- scene.rml = the hero's scene (its MAIN, and any artboard a format or an overlay nests, made components) followed by
  one artboard per format, "SOCIAL 1x1" (1080x1080) and "SOCIAL 4x5" (1080x1350), each with one "Timeline" and
  "State Machine 1" (layer "Main"). Draw order, top first: OPEN (logo + headline), END (logo + URL), VEIL (the
  format's background image), CAM.z -> CAM.k -> CAM.p -> HERO (overlays, then HERO.main = the nested MAIN, clipped).
- social/: the backgrounds (scripts/social_bg.py at each format's own size, lossless WebP) and the two fonts cut to
  the characters used (Cal Sans SemiBold and Duda Sans from the library's fonts/).
- the hero's own font and image files, copied (same relative paths).
- build/social.json: the frames of every cut and move, per format, for the render (music on a cut).
- rive.yaml if missing (main: the first format's artboard).

The camera (APRENDIZADOS B2): CAM.z holds the frame centre (the hero's arrival 1.04 -> 1); CAM.k is the scale
(frame width / framing width); CAM.p is (-cx, -cy) in MAIN px. A framing is (cx, cy, width) in MAIN px; its height
follows the format. Moves blend the scale and the offset (k, -k*c) on the curve, never the framing's width: that is
the hero's own zoom (a matrix blend), a zoom about one fixed point. Rules it keeps:
- a product scene holds still after its arrival; a constant zoom is only an explicit `Zoom` on a shot;
- the cards zoom out at 1 %/s to their last frame (`rate ** ((last - f) / 60)`), times their arrival;
- every zoom cut scales about the frame centre (cuts.ZOOM_CENTER; tokens match_cut.zoom pivot frame_centre) and
  needs room around the frame for its exit: else it raises "no room for a centred zoom".

Timing is one for all formats (the cuts land on the same frames, so one music edit fits all); framings, clips and
the nested artboard can differ by format: any argument marked "per format" takes a value or {format: value}.
"""
import importlib.util
import json
import math
import os
import re
import shutil

import kit  # noqa: F401  (puts the tools on the path: svg2rml)
from svg2rml import parse as _svg_parse, to_vertices as _svg_vertices
from cuts import EXIT, SETTLE, ZOOM_CENTER, KINDS, OPEN as HERO_ZOOM_OUT, REF_W

FPS = 60
HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "fonts")
CAL_FILE, DUDA_FILE = "CalSans-SemiBold.ttf", "LabelSansVF.ttf"   # Cal Sans SemiBold (static) and Duda Sans (wght)
WGHT = 2003265652                                               # 'wght'
DUDA_E = (0.75, 0, 0.25, 1)                                     # tokens ease.duda
HERO_MOVE = HERO_ZOOM_OUT["ease"]                               # the hero's zoom-out curve (0.8 0.0451 0.2 1, 102 f)

# The designers' social posts (Figma i6SoOBQMUCQm6FP76rbPrY; the approved opening = frame "banner" 2075:5867, 1:1):
# the logo alone at the top (70.785 tall, its top at 70/1080 of the frame's height, centred), the headline centred in
# the frame, Cal Sans SemiBold 95.08/109.62 in a 974 box, white; the end card: the logo centred over the URL in Duda
# Sans 350, 44/50. The 4:5 has no frame of its own: the same sizes, the logo at the same fraction of the height
# (87.5 px), its end card measured by eye in ma-novo-social v07-v18.
FORMATS = {
    "1x1": dict(W=1080, H=1080, logo_top=70 / 1080, logo_h=70.785, head_w=974, head_size=95.0773, head_lh=109.6186,
                end_logo=(508, 84), link_size=44, link_lh=50, link_gap=32, link_w=984),
    "4x5": dict(W=1080, H=1350, logo_top=70 / 1080, logo_h=70.785, head_w=974, head_size=95.0773, head_lh=109.6186,
                end_logo=(641, 88), link_size=44, link_lh=50, link_gap=34, link_w=984),
}
LOGO = "FFF07C5A"            # the coral badge (duda.co "duda brand.svg" = Figma "Brand/Logo")
INK = "FFFFFFFF"             # the cards' text and the logo's letters
BG = "FFFFFFFF"              # the artboard behind everything (never seen when the framings stay in their world)
# Rive draws Cal Sans lower than Figma for the same text box top (ma-novo-social v08, v09, v16: the first line's
# pixel rows against the Figma PNG). No simple formula: (size, line height) -> px to move the headline up.
CAL_TEXT_DY = [(85.0, 98.0, 20.0), (95.0773, 109.6186, 22.7), (107.09, 123.468, 26.0)]
# the opening's words (tokens closing_words, as approved in v18): 4 frames apart, each fading in over 9 frames and
# rising 5 px (3 px at 680 -> 1080) on settle over 30
WORDS = dict(first=10, step=4, fade=9, rise=5, settle=30)
LOGO_IN = dict(fade=9, rise=10, settle=40)
# the opening gives way to the hero (v07-v18): its logo and headline leave 10 frames before the hero comes in (fade 10,
# 24 px up on duda over 20); the hero comes in under the card's background, which dissolves over 12 frames (the
# white headline must be gone before: no double exposure over a white hero), while CAM.z settles 1.04 -> 1 in 50
REVEAL = dict(lead=10, fade=10, rise=24, rise_frames=20, veil=12, arrive=1.04, arrive_frames=50)
CARD_RATE = 1.01             # the cards' slow zoom-out: 1 %/s (Mateus, v12/v16: 2 %/s was "forte demais")
END_FRAMES = 162             # the end card, from the cut to the last frame (2.7 s; v14-v18)
SPEED_CAP = dict(text=30, logo=40)   # tokens speed_cap_px_per_frame_at_1920 (text_content, chips_icons)
RATIO_MAX = 1.2              # tokens match_cut.zoom.entry_speed_ratio_max
NO_ROOM = "no room for a centred zoom: drop the transition or extend the backdrop"

LOGO_SVG = (51.6379, 23.0)
LOGO_PATHS = [   # the badge, then the letters (d, u, d, a); evenOdd: the letters are holes in the badge
    "M48.9809 23H2.65782C1.18991 23 0 21.8153 0 20.3539V2.64612C0 1.18468 1.18991 0 2.65782 0H48.9801C50.448 0 51.6379 1.18468 51.6379 2.64612V20.3539C51.6379 21.8153 50.448 23 48.9809 23Z",
    "M34.0648 5.00757V9.86066C33.279 9.28632 32.4121 8.94636 31.3644 8.94636C28.7459 8.94636 26.616 11.0669 26.616 13.6739C26.616 16.2808 28.7459 18.4014 31.3644 18.4014C32.4121 18.4014 33.2782 18.0614 34.0648 17.4871V18.2158H36.455V5.00757H34.0648ZM31.5773 16.1768C30.1905 16.1768 29.0625 15.0537 29.0625 13.6731C29.0625 12.2924 30.1905 11.1693 31.5773 11.1693C32.964 11.1693 34.0921 12.2924 34.0921 13.6731C34.0921 15.0537 32.964 16.1768 31.5773 16.1768Z",
    "M12.6658 5.00757V9.86066C11.8801 9.28632 11.0131 8.94636 9.96544 8.94636C7.34699 8.94636 5.21704 11.0669 5.21704 13.6739C5.21704 16.2808 7.34699 18.4014 9.96544 18.4014C11.0131 18.4014 11.8793 18.0614 12.6658 17.4871V18.2158H15.0561V5.00757H12.6658ZM10.1784 16.1768C8.7916 16.1768 7.66355 15.0537 7.66355 13.6731C7.66355 12.2924 8.7916 11.1693 10.1784 11.1693C11.5651 11.1693 12.6932 12.2924 12.6932 13.6731C12.6932 15.0537 11.5651 16.1768 10.1784 16.1768Z",
    "M38.0382 10.2935L38.8737 11.923C39.8419 11.2742 40.7586 10.9063 41.8264 10.9063C43.962 10.9063 43.9837 12.5461 43.9837 12.5461C43.9837 12.5461 42.8074 12.4829 41.8754 12.5013C40.6269 12.5285 37.9297 12.9428 37.9297 15.5554C37.9297 17.3208 39.314 18.4207 41.2142 18.4207C43.1505 18.4207 43.9017 17.7183 44.0825 17.4024L44.0914 18.2471H46.4174V12.8709C46.4174 11.0958 45.2138 8.90967 41.8835 8.90967C39.866 8.90967 38.6351 9.83437 38.0382 10.2935ZM41.5219 16.6185C40.9788 16.6185 40.0741 16.4833 40.0741 15.4562C40.0741 14.7083 40.97 14.3123 41.8658 14.2939C42.834 14.2755 43.9829 14.2939 43.9829 14.2939C43.9837 15.9337 42.6082 16.6185 41.5219 16.6185Z",
    "M18.9736 14.0521C18.9736 15.0744 19.806 15.9039 20.8336 15.9039H20.9364C21.9632 15.9039 22.7964 15.0752 22.7964 14.0521C22.7964 12.8802 22.7964 9.50854 22.7964 9.50854H25.1987V18.2188H22.8864L22.8832 17.1022C22.6301 17.4661 21.8957 18.1924 20.3081 18.1924C19.2202 18.1924 18.0729 17.6357 17.4784 16.9566C16.8878 16.2814 16.5881 15.2839 16.5881 13.9921V9.50854H18.9736V14.0521V14.0521Z",
]


# ------------------------------------------------------------------------------------------------- small helpers
def ease(e, x):
    """Cubic-bezier e = (x1, y1, x2, y2) at progress x in [0, 1] (None: linear)."""
    x = min(1.0, max(0.0, x))
    if e is None:
        return x
    x1, y1, x2, y2 = e
    bz = lambda a, b, s: 3 * (1 - s) ** 2 * s * a + 3 * (1 - s) * s * s * b + s ** 3
    lo, hi = 0.0, 1.0
    for _ in range(60):
        mid = (lo + hi) / 2
        if bz(x1, x2, mid) < x:
            lo = mid
        else:
            hi = mid
    return bz(y1, y2, (lo + hi) / 2)


def g(v):
    return f"{v:.6g}" if isinstance(v, float) else str(v)


def esc(s):
    return s.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;").replace("\n", "&#10;")


def text_dy(size, lh):
    """Px to move a Cal Sans headline up so Rive matches Figma (measured: 85/98 20, 95/110 22.7, 107/123 26),
    interpolated on the size (the three share a line height of ~1.153 x the size). Returns (dy, how)."""
    for s, h, d in CAL_TEXT_DY:
        if abs(s - size) < 1e-3 and abs(h - lh) < 1e-3:
            return d, "measured"
    pts = sorted((s, d) for s, _, d in CAL_TEXT_DY)
    a, b = (pts[0], pts[1]) if size < pts[1][0] else (pts[1], pts[2])
    d = a[1] + (b[1] - a[1]) * (size - a[0]) / (b[0] - a[0])
    how = "interpolated" if pts[0][0] <= size <= pts[-1][0] else "EXTRAPOLATED"
    if abs(lh / size - 1.153) > 0.02:
        how += f", line height {lh / size:.3f} x the size (the table's is 1.153)"
    return d, how


class Ids:
    def __init__(self, pre):
        self.pre, self.n = pre, 0

    def __call__(self):
        self.n += 1
        return f"{self.pre}:{self.n}"


class Keys:
    """obj id -> prop -> [(frame, value, ease)]; ease None = linear, 'hold', or a cubic (x1, y1, x2, y2)."""

    def __init__(self):
        self.k = {}

    def add(self, obj, prop, frame, value, e=None):
        self.k.setdefault(obj, {}).setdefault(prop, []).append((frame, value, e))

    def track(self, obj, prop, vals, cuts=(), eps=1e-6, f0=0, spans=()):
        """Keys for a value sampled on every frame from f0: a hold key where it then stays (or jumps at a cut),
        linear keys along a move, thinned where the straight line between two keys stays within eps of every frame
        between them (exact on whole frames to eps). spans: [(a, b, ease)] frames where the value is exactly one
        cubic ease from a to b: two keys there (a cubic at a), as the piece keyed its slide exit (exact between
        frames too, and two keys to move in the editor)."""
        n = len(vals)
        same = lambda a, b: abs(a - b) <= 1e-9 * max(1.0, abs(a))
        moving = [not same(vals[i], vals[i + 1]) and (f0 + i + 1) not in cuts for i in range(n - 1)] + [False]
        jump = lambda i: not moving[i - 1] and not same(vals[i], vals[i - 1])     # a hold that ends on a new value
        must = {0} | {i for i in range(1, n) if moving[i] != moving[i - 1] or (f0 + i) in cuts or jump(i)}
        keep = sorted(must)
        out = []
        for j, a in enumerate(keep):
            out.append(a)
            if not moving[a]:
                continue
            end = keep[j + 1] if j + 1 < len(keep) else n - 1
            i = a
            while i < end:                       # greedy: the farthest b whose line fits every frame in between
                b = i + 1
                while b + 1 <= end and all(abs(vals[i] + (vals[b + 1] - vals[i]) * (k - i) / (b + 1 - i) - vals[k])
                                           <= eps for k in range(i + 1, b + 1)):
                    b += 1
                if b < end:
                    out.append(b)
                i = b
        eases = {}
        for a, b, e in spans:
            a, b = a - f0, b - f0
            ok = 0 <= a < b < n and all(abs(vals[a] + (vals[b] - vals[a]) * ease(e, (k - a) / (b - a)) - vals[k])
                                        <= 1e-6 * max(1.0, abs(vals[k])) for k in range(a, b + 1))
            if ok and a in out and b in out:
                out = [i for i in out if not a < i < b]
                eases[a] = e
        for i in sorted(set(out)):
            self.add(obj, prop, f0 + i, vals[i], eases.get(i, None if moving[i] else "hold"))

    def rml(self, nid, ind):
        out = []
        for obj, props in self.k.items():
            out.append(f'{ind}<KeyedObject objectId="{obj}" id="{nid()}">')
            for prop, ks in props.items():
                out.append(f'{ind}    <KeyedProperty property="{prop}" id="{nid()}">')
                ks = sorted(ks, key=lambda x: x[0])
                frames = [f for f, _, _ in ks]
                assert len(frames) == len(set(frames)), (obj, prop, frames)
                for f, v, e in ks:
                    if e is None or e == "hold":
                        it = "linear" if e is None else "hold"
                        out.append(f'{ind}        <KeyFrameDouble value="{g(float(v))}" interpolationType="{it}" '
                                   f'frame="{f}" id="{nid()}"/>')
                    else:
                        x1, y1, x2, y2 = e
                        out.append(f'{ind}        <KeyFrameDouble value="{g(float(v))}" interpolationType="cubic" '
                                   f'frame="{f}" id="{nid()}">')
                        out.append(f'{ind}            <CubicEaseInterpolator x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
                                   f'id="{nid()}"/>')
                        out.append(f'{ind}        </KeyFrameDouble>')
                out.append(f'{ind}    </KeyedProperty>')
            out.append(f'{ind}</KeyedObject>')
        return "\n".join(out)


def logo_rml(nid, ind, letters=False):
    """The logo's paths, centred on 0,0 in its svg units: all of them = the badge with the letters as holes
    (evenOdd); letters=True = only the letters (white). The two shapes don't overlap, so the logo fades cleanly as
    two layers over a coloured background (ma-novo-social v07)."""
    tf = lambda p: (p[0] - LOGO_SVG[0] / 2, p[1] - LOGO_SVG[1] / 2)
    out = []
    for d in (LOGO_PATHS[1:] if letters else LOGO_PATHS):
        for sub in _svg_parse(d):
            out.append(f'{ind}<PointsPath isClosed="true" id="{nid()}">')
            for v in _svg_vertices(sub, tf):
                x, y = v["p"]
                if v["in"] is None and v["out"] is None:
                    out.append(f'{ind}    <StraightVertex x="{g(x)}" y="{g(y)}" id="{nid()}"/>')
                    continue
                a = {"x": x, "y": y}
                for k in ("in", "out"):
                    h = v[k]
                    a[f"{k}Rotation"] = 0.0 if h is None else math.atan2(h[1] - y, h[0] - x)
                    a[f"{k}Distance"] = 0.0 if h is None else math.hypot(h[0] - x, h[1] - y)
                attrs = " ".join(f'{k}="{g(float(val))}"' for k, val in a.items())
                out.append(f'{ind}    <CubicDetachedVertex {attrs} id="{nid()}"/>')
            out.append(f"{ind}</PointsPath>")
    return "\n".join(out)


def _logo_node(nid, ind, name, y, k):
    i2, i3 = ind + " " * 4, ind + " " * 8
    return (f'{ind}<Node y="{g(y)}" scaleX="{g(k)}" scaleY="{g(k)}" opacity="0" name="{name}" id="{{ID}}">\n'
            f'{i2}<Shape name="{name}.shape" id="{nid()}">\n{logo_rml(nid, i3)}\n'
            f'{i3}<Fill fillRule="evenOdd" name="{name}.fill" id="{nid()}">\n'
            f'{i3}    <SolidColor colorValue="{LOGO}" name="{name}.color" id="{nid()}"/>\n{i3}</Fill>\n{i2}</Shape>\n'
            f'{i2}<Shape name="{name}.letters" id="{nid()}">\n{logo_rml(nid, i3, letters=True)}\n'
            f'{i3}<Fill fillRule="evenOdd" name="{name}.letters.fill" id="{nid()}">\n'
            f'{i3}    <SolidColor colorValue="{INK}" name="{name}.letters.color" id="{nid()}"/>\n{i3}</Fill>\n'
            f'{i2}</Shape>\n{ind}</Node>')


def _load_script(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, "scripts", f"{name}.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ------------------------------------------------------------------------------------------------- the camera
class Zoom:
    """A zoom inside a shot, only when asked (a product scene holds still after its arrival; APRENDIZADOS A).
    Eased: the framing's width x `factor` from f0 to f1 on `ease` (the hero's close-up: 2.5 -> 2.4 is factor 2.5/2.4
    on cuts.CAMERA["slow_ease"]). Constant: `rate` per second, geometric, from f0 to f1 (None: to the shot's end).
    `pivot`: the point of the frame that stays put, as fractions of the frame ((0.5, 0.5) = the centre, (1, 1) = the
    bottom-right corner)."""

    def __init__(self, f0, f1=None, factor=None, ease=None, rate=None, pivot=(0.5, 0.5)):
        assert (factor is None) != (rate is None), "Zoom: give factor (eased, f0 -> f1) or rate (per second)"
        assert rate is not None or f1 is not None, "Zoom: an eased zoom needs f1"
        self.f0, self.f1, self.factor, self.ease, self.rate, self.pivot = f0, f1, factor, ease, rate, pivot

    def at(self, f):
        if f <= self.f0:
            return 1.0
        if self.rate is not None:
            last = f if self.f1 is None else min(f, self.f1)
            return self.rate ** ((last - self.f0) / FPS)
        return 1 + (self.factor - 1) * ease(self.ease, (f - self.f0) / (self.f1 - self.f0))


class Shot:
    """A framing (cx, cy, width) in MAIN px for one format, with an optional Zoom; `world` = (x0, y0, x1, y1), the
    MAIN px that may show (the build checks every frame of the shot against it)."""

    def __init__(self, framing, W, H, zoom=None, world=None):
        self.c, self.W, self.H, self.zoom, self.world = tuple(framing), W, H, zoom, world

    def at(self, f):
        cx, cy, w = self.c
        if self.zoom is None:
            return self.c
        z = self.zoom.at(f)
        h = w * self.H / self.W
        px, py = self.zoom.pivot
        Px, Py = cx - w / 2 + px * w, cy - h / 2 + py * h
        return (Px + (0.5 - px) * w * z, Py + (0.5 - py) * h * z, w * z)


def blend(a, b, s, W):
    """The hero's zoom between two framings: scale k = W / width and offset -k * c, both linear in s (a matrix blend:
    a zoom about one fixed point), never the framing's width."""
    k0, k1 = W / a[2], W / b[2]
    k = k0 + (k1 - k0) * s
    bx = -k0 * a[0] + (-k1 * b[0] + k0 * a[0]) * s
    by = -k0 * a[1] + (-k1 * b[1] + k0 * a[1]) * s
    return (-bx / k, -by / k, W / k)


def _inside(fr, world, W, H, tol=1e-6):
    cx, cy, w = fr
    h = w * H / W
    x0, y0, x1, y1 = world
    return (cx - w / 2 >= x0 - tol and cx + w / 2 <= x1 + tol and cy - h / 2 >= y0 - tol and cy + h / 2 <= y1 + tol)


# ------------------------------------------------------------------------------------------------- the video
class Social:
    """A social video cut from a built hero. hero: the hero's folder (scene.rml) or its .rml file; out: the folder to
    write (not the hero's); formats: names of FORMATS, or {name: dict(W=, H=, ...)} (a format of your own gets the
    1x1's card sizes scaled to its width: check its cards); nest: per format, the artboard each format nests
    (default "MAIN", e.g. {"4x5": "MAIN 4x5"} for a taller copy of the hero); patch: fn(text) -> text, run on the
    hero's scene before it is written (hold a property, move a block: what only this video needs)."""

    def __init__(self, hero, out, formats=("1x1", "4x5"), nest="MAIN", patch=None, prefix="SOCIAL"):
        src = os.path.join(hero, "scene.rml") if os.path.isdir(hero) else hero
        assert os.path.exists(src), f"no hero scene at {src}"
        self.src_dir, self.out = os.path.dirname(os.path.abspath(src)), os.path.abspath(out)
        assert self.src_dir != self.out, "write the social video in a folder of its own, not in the hero's"
        self.text = open(src, encoding="utf-8").read()
        if patch:
            self.text = patch(self.text)
        if isinstance(formats, dict):
            self.F = {}
            for k, v in formats.items():
                base = dict(FORMATS.get(k, FORMATS["1x1"]))
                if k not in FORMATS:
                    s = v["W"] / 1080
                    base.update(logo_h=70.785 * s, head_w=974 * s, head_size=95.0773 * s, head_lh=109.6186 * s,
                                link_size=44 * s, link_lh=50 * s, link_gap=32 * s, link_w=984 * s, end_logo=None)
                base.update(v)
                self.F[k] = base
        else:
            self.F = {k: dict(FORMATS[k]) for k in formats}
        for k, F in self.F.items():
            F["name"] = f"{prefix} {k}"
            F["nest"] = self._per(nest, k)
            F["main"] = self._artboard(F["nest"])
            assert f'name="{F["name"]}"' not in self.text, f"the hero already has an artboard {F['name']!r}"
        self.notes, self.issues = [], []
        self.open = self.end = None
        self.stretches = []          # [(m0, m1, first frame)]
        self.cam = {k: [] for k in self.F}
        self.clips = {k: [] for k in self.F}
        self.overlays, self.hide = [], None
        self.cut_log = []

    # ---- reading the hero
    def _artboard(self, name):
        m = re.search(r'<Artboard [^>]*name="%s"[^>]*>' % re.escape(name), self.text)
        assert m, f"no artboard {name!r} in the hero's scene"
        tag = m.group(0)
        attr = lambda a, d=None: (re.search(rf' {a}="([^"]*)"', tag) or [None, d])[1]
        body = self.text[m.end():]
        nxt = body.find("<Artboard ")
        tl = re.search(r'<LinearAnimation [^>]*name="Timeline"[^>]*>', body[:nxt if nxt >= 0 else None])
        assert tl, f"artboard {name!r} has no LinearAnimation named \"Timeline\""
        t = tl.group(0)
        return dict(name=name, tag=tag, id=attr("id"), W=float(attr("width")), H=float(attr("height")),
                    ox=float(attr("originX", 0)), oy=float(attr("originY", 0)), vm=attr("viewModelId"),
                    vmi=attr("viewModelInstanceId"), tl=re.search(r' id="([^"]+)"', t).group(1),
                    frames=int(re.search(r'duration="(\d+)"', t).group(1)),
                    fps=int((re.search(r'fps="(\d+)"', t) or [None, 60])[1]))

    def _per(self, v, k):
        return v[k] if isinstance(v, dict) else v

    # ---- the timeline
    def opening(self, headline, hero_in, rate=CARD_RATE, dy=None):
        """The opening card from frame 0: the logo, then the headline word by word (give the lines with \\n), both
        zooming out at `rate` per second (None: still) until the card's background has dissolved into the hero. The
        hero comes in at `hero_in`; the logo and headline leave REVEAL["lead"] frames before it. dy: the headline's
        Rive-vs-Figma shift (default text_dy(); measure it against the Figma PNG). Returns hero_in."""
        assert hero_in >= 60, "the opening needs a second at least"
        self.open = dict(text=headline, hero_in=hero_in, rate=rate, dy=dy)
        self.cut_log.append(dict(frame=hero_in, kind="reveal", what="opening card -> hero (the background dissolves "
                                 f"over {REVEAL['veil']} f, the hero settles {REVEAL['arrive']} -> 1)"))
        return hero_in

    def play(self, *stretches):
        """The hero's MAIN Timeline as stretches (m0, m1) of its frames (m1 not included), played one after another
        from the hero's in frame (opening(hero_in=)); the last one runs on to the cut to the end card."""
        assert self.open, "call opening() first: the hero's stretches start at its hero_in"
        f = self.open["hero_in"]
        for m0, m1 in stretches:
            assert 0 <= m0 < m1, (m0, m1)
            for F in self.F.values():
                assert m1 <= F["main"]["frames"], f"stretch {m0}-{m1} past {F['nest']}'s {F['main']['frames']} frames"
            self.stretches.append((m0, m1, f))
            f += m1 - m0

    def frame_of(self, M, stretch=None):
        """The video frame where MAIN frame M plays (in the given stretch, else the first that holds it)."""
        for k, (m0, m1, f) in enumerate(self.stretches):
            if (stretch is None or stretch == k) and m0 <= M < m1:
                return f + M - m0
        raise ValueError(f"MAIN frame {M} is in no stretch {self.stretches}")

    def main_at(self, f):
        """The MAIN frame shown at video frame f (None before the hero or after the last stretch)."""
        for m0, m1, a in self.stretches:
            if a <= f < a + m1 - m0:
                return m0 + f - a
        return None

    def _shot(self, k, framing, zoom, world):
        F = self.F[k]
        fr = self._per(framing, k)
        wd = self._per(world, k) if world is not None else (0, 0, F["main"]["W"], F["main"]["H"])
        return Shot(fr, F["W"], F["H"], self._per(zoom, k), wd)

    def shot(self, f, framing, zoom=None, world=None):
        """The camera on `framing` (per format: (cx, cy, width) in MAIN px) from frame f: a hard cut, or the first
        framing (from frame 0, whatever f). zoom: an explicit Zoom (per format); world: per format, the MAIN px it may
        show (default: the nested artboard)."""
        for k in self.F:
            self.cam[k].append(dict(kind="shot", f=f, shot=self._shot(k, framing, zoom, world)))
        if any(len(c) > 1 for c in self.cam.values()):
            self.cut_log.append(dict(frame=f, kind="cut", what="hard cut"))

    def move(self, f0, f1, framing, ease=HERO_MOVE, zoom=None, world=None):
        """One camera move from the current shot (still running, its zoom too) to `framing`, f0 -> f1, on `ease`
        (default the hero's zoom-out curve): scale and offset blended, a zoom about one fixed point."""
        for k in self.F:
            self.cam[k].append(dict(kind="move", f=f0, f1=f1, ease=ease, shot=self._shot(k, framing, zoom, world)))
        self.cut_log.append(dict(frame=f0, kind="move", to=f1, what=f"camera move over {f1 - f0} f"))

    def slide(self, f, framing, direction="left", out_px=None, in_px=None, zoom=None, world=None):
        """A match cut by position (cuts.KINDS["slide"]): from frame f the frame slides out (23 f, accelerating,
        reaching its full 215 px at 1340 = 173 px at 1080 on the last frame before the cut); the new shot comes in
        60 px (48 at 1080) back and settles in 54 f, the content moving the same way (`direction`: where the content
        goes). Returns the cut frame."""
        K = KINDS["slide"]
        cut = f + K["out_frames"] + 1
        sgn = 1 if direction == "left" else -1
        assert direction in ("left", "right")
        for k, F in self.F.items():
            px_o = self._per(out_px, k) if out_px is not None else K["out_px"] * F["W"] / REF_W
            px_i = self._per(in_px, k) if in_px is not None else K["in_px"] * F["W"] / REF_W
            self.cam[k].append(dict(kind="slide", f=f, cut=cut, out=sgn * px_o, inn=sgn * px_i,
                                    shot=self._shot(k, framing, zoom, world)))
        self.cut_log.append(dict(frame=cut, kind="slide", exit=f, what="match cut by position"))
        return cut

    def zoom_cut(self, f, framing, direction="out", pivot="centre", room=None, zoom=None, world=None):
        """A zoom cut between two shots of the hero about the frame centre (cuts.ZOOM_CENTER): from frame f the shot
        scales 7 % (93 % "out", 107 % "in") in 20 f on (1 0 1 1), reaching it on the last frame before the cut; a dry
        cut at that peak; the new shot comes in 5 % away from rest and settles in 35 f. room: per format, the MAIN px
        the exit may show (default the shot's world); with no room around the frame it raises. Returns the cut."""
        cut = self._zoom_check(f, direction, pivot)
        for k in self.F:
            self.cam[k].append(dict(kind="zoom", f=f, cut=cut, dir=direction, room=self._room(room, k),
                                    shot=self._shot(k, framing, zoom, world)))
        self.cut_log.append(dict(frame=cut, kind="zoom", exit=f, what=f"zoom-{direction} cut about the frame centre"))
        return cut

    def _zoom_check(self, f, direction, pivot):
        if pivot not in ("centre", "center", "frame_centre", (0.5, 0.5)):
            raise ValueError("a zoom cut scales about the frame centre (tokens match_cut.zoom pivot frame_centre; "
                             f"Mateus 2026-11-25), not {pivot!r}")
        assert direction in ("in", "out"), direction
        return f + ZOOM_CENTER["out_frames"] + 1

    def _room(self, room, k):
        return self._per(room, k) if room is not None else None

    def end_card(self, url, at, frames=END_FRAMES, rate=CARD_RATE, pivot="centre", room=None):
        """From frame `at` the hero leaves by the zoom-out cut about the frame centre (cuts.ZOOM_CENTER: 93 % in 20 f
        on (1 0 1 1), reaching it on the last frame before the cut; a dry cut at that peak) and the end card comes in
        whole (background, logo, URL) 105 % -> 100 % in 35 f (settle), then zooms out at `rate` per second to its
        last frame. room: per format, the MAIN px the exit may show (default the shot's world); with no room around
        the frame it raises. Returns the cut frame; the video ends `frames` after it."""
        cut = self._zoom_check(at, "out", pivot)
        for k in self.F:
            self.cam[k].append(dict(kind="end", f=at, cut=cut, dir="out", room=self._room(room, k)))
        self.end = dict(url=url, at=at, cut=cut, frames=frames, rate=rate)
        self.cut_log.append(dict(frame=cut, kind="zoom", exit=at, what="zoom-out cut about the frame centre -> end card"))
        return cut

    def overlay(self, artboard, at, show, hide=None, offset=0):
        """Another artboard of the hero's scene nested over MAIN inside the camera, its top-left at `at` (MAIN px),
        drawn from frame `show` (to `hide`), its Timeline following MAIN's: its frame = MAIN's + offset (a larger copy
        of a scene, so the camera can pull back past MAIN's edge: ma-novo-social's "Site and phone XL")."""
        a = self._artboard(artboard)
        self.overlays.append(dict(a=a, at=at, show=show, hide=hide, offset=offset))

    def hide_main(self, f):
        """MAIN stops drawing from frame f (an overlay covers the frame, or the end card)."""
        self.hide = f

    def clip(self, f, rects):
        """MAIN's clip from frame f: rects (per format), a union of (x0, y0, x1, y1) in MAIN px. Keep the same number
        of rects in every call (a (0, 0, 0, 0) rect draws nothing)."""
        for k in self.F:
            self.clips[k].append((f, [tuple(r) for r in self._per(rects, k)]))

    # ---- evaluation
    def duration(self):
        assert self.end, "call end_card() first"
        return self.end["cut"] + self.end["frames"]

    def framings(self, k):
        """(cx, cy, width) of format k on every frame, its cut frames, and the frames that leave their world:
        [(frame, framing, world, what)]. A move blends the running shot (its zoom too) into the next; an exit
        (slide or zoom) works on the running shot, live; after the end card's cut the camera holds (the card
        covers it)."""
        F, W, H = self.F[k], self.F[k]["W"], self.F[k]["H"]
        D = self.duration()
        evs = sorted(self.cam[k], key=lambda e: e["f"])
        assert evs and evs[0]["kind"] == "shot", "the first camera call is shot()"
        assert all(e["kind"] != "end" for e in evs[:-1]), "end_card() is the camera's last event"
        done_at = lambda e: e["f1"] if e["kind"] == "move" else e.get("cut", e["f"])
        out, cuts, bad = [], set(), []
        cur, entry, i = evs[0]["shot"], None, 1
        exit_c = None
        self.spans = [(e["f"], e["cut"] - 1, KINDS["slide"]["out_ease"]) for e in evs if e["kind"] == "slide"]
        for f in range(D):
            while i < len(evs) and evs[i]["kind"] != "end" and f >= done_at(evs[i]):
                e = evs[i]
                cur, entry = e["shot"], (e if e["kind"] in ("slide", "zoom") else None)
                if e["kind"] != "move":
                    cuts.add(done_at(e))
                i += 1
            nxt = evs[i] if i < len(evs) and f >= evs[i]["f"] else None
            if nxt and nxt["kind"] == "end" and f >= nxt["cut"]:
                out.append(out[-1])
                continue
            fr, world, what = cur.at(f), cur.world, "shot"
            if entry is not None and entry["kind"] == "slide":
                S = KINDS["slide"]
                if f < entry["cut"] + S["in_frames"]:
                    u = ease(S["in_ease"], (f - entry["cut"]) / S["in_frames"])
                    fr = (fr[0] - entry["inn"] * (1 - u) * fr[2] / W, fr[1], fr[2])
            elif entry is not None and entry["kind"] == "zoom":
                Z = ZOOM_CENTER
                if f < entry["cut"] + Z["in_frames"]:
                    u = ease(Z["in_ease"], (f - entry["cut"]) / Z["in_frames"])
                    fr = (fr[0], fr[1], fr[2] / (1 + (1 if entry["dir"] == "out" else -1) * Z["in_"] * (1 - u)))
            if nxt and nxt["kind"] == "move":
                fr = blend(fr, nxt["shot"].at(f), ease(nxt["ease"], (f - nxt["f"]) / (nxt["f1"] - nxt["f"])), W)
                world, what = nxt["shot"].world, "move"
            elif nxt and nxt["kind"] == "slide":
                S = KINDS["slide"]
                p = ease(S["out_ease"], (f - nxt["f"]) / S["out_frames"])
                fr = (fr[0] + nxt["out"] * p * fr[2] / W, fr[1], fr[2])
                world, what = None, "slide"     # the slide shows what lies beside the shot, on purpose
            elif nxt and nxt["kind"] in ("zoom", "end"):
                Z = ZOOM_CENTER
                if f == nxt["f"]:
                    exit_c = fr[:2]
                if math.dist(fr[:2], exit_c) > 1e-6:
                    raise ValueError(f"{F['name']} f{f}: the shot's centre moves during the zoom cut's exit; a zoom "
                                     "cut scales about the frame centre (hold the shot, or a Zoom about its centre)")
                p = ease(Z["out_ease"], (f - nxt["f"]) / Z["out_frames"])
                fr = (fr[0], fr[1], fr[2] / (1 + (-1 if nxt["dir"] == "out" else 1) * Z["out"] * p))
                world, what = nxt["room"] or cur.world, "exit"
            out.append(fr)
            if world is not None and not _inside(fr, world, W, H):
                bad.append((f, fr, world, what))
        return out, cuts, bad

    # ---- writing
    def build(self, slim=True):
        """Write out/scene.rml (the hero + the social artboards), the backgrounds and fonts, build/social.json and
        rive.yaml if missing. Prints a line per format, the NOTEs and the LINTs; returns the info dict."""
        assert self.open and self.stretches and self.end, "opening(), play() and end_card() first"
        os.makedirs(os.path.join(self.out, "social"), exist_ok=True)
        os.makedirs(os.path.join(self.out, "build"), exist_ok=True)
        text = self._hero_copy()
        used = {int(p) for p in re.findall(r'id="(\d+):\d+"', text)}
        pre = max(used) + 1
        pres = {k: pre + 1 + i for i, k in enumerate(self.F)}
        nid0 = Ids(pre)
        assets = []
        for a in self._nested():
            if not re.search(rf'<ComponentAsset artboardId="{re.escape(a["id"])}"', text):
                assets.append(f'<ComponentAsset artboardId="{a["id"]}" name="{esc(a["name"])}" id="{nid0()}"/>')
        bg = _load_script("social_bg")
        fonts = {"cal": (CAL_FILE, "Cal Sans", nid0()), "duda": (DUDA_FILE, "Duda Sans", nid0())}
        chars = set(chr(c) for c in range(0x20, 0x7F)) | set(self.open["text"]) | set(self.end["url"])
        for key, (file, fam, fid) in fonts.items():
            dst = os.path.join(self.out, "social", file)
            if slim:
                from fontTools import subset
                opts = subset.Options()
                opts.hinting = False
                font = subset.load_font(os.path.join(FONTS, file), opts)
                sub = subset.Subsetter(opts)
                sub.populate(text="".join(sorted(chars)))
                sub.subset(font)
                subset.save_font(font, dst, opts)
            else:
                shutil.copyfile(os.path.join(FONTS, file), dst)
            assets.append(f'<FontAsset file="social/{file}" name="{fam}" id="{fid}"/>')
        bgs = {}
        for k, F in self.F.items():
            file = f"social/bg_{F['W']}x{F['H']}.webp"
            if not os.path.exists(os.path.join(self.out, file)):
                bg.write(F["W"], F["H"], os.path.join(self.out, file))
            bgs[k] = nid0()
            assets.append(f'<ImageAsset file="{file}" format="webp" width="{F["W"]}" height="{F["H"]}" '
                          f'name="social_bg_{k}" id="{bgs[k]}"/>')
        arts, info = [], {}
        x = -200
        for k, F in self.F.items():
            x -= F["W"] + 200
            rml, inf = self._artboard_rml(k, F, Ids(pres[k]), fonts, bgs[k], x)
            arts.append(rml)
            info[k] = inf
        i = text.rindex("</Artboard>") + len("</Artboard>")
        text = text[:i] + "\n" + "\n".join(arts) + text[i:]
        j = text.rindex("</Rive>")
        text = text[:j] + "".join(f"    {a}\n" for a in assets) + text[j:]
        open(os.path.join(self.out, "scene.rml"), "w", encoding="utf-8").write(text)
        yml = os.path.join(self.out, "rive.yaml")
        if not os.path.exists(yml):
            first = next(iter(self.F.values()))["name"]
            open(yml, "w").write(f'name: {os.path.basename(self.out)}\nmain: "{first}"\nexclude:\n  - build\n'
                                 f'  - renders\n  - versions\n')
        D = self.duration()
        log = sorted(self.cut_log, key=lambda c: c["frame"])
        for c in log:
            c["seconds"] = round(c["frame"] / FPS, 4)
        out = dict(fps=FPS, frames=D, seconds=round(D / FPS, 4), cuts=log,
                   formats={k: dict(artboard=F["name"], W=F["W"], H=F["H"], nest=F["nest"], **info[k])
                            for k, F in self.F.items()})
        json.dump(out, open(os.path.join(self.out, "build", "social.json"), "w"), indent=1)
        for k in self.F:
            self._hairlines(k)
        for k, F in self.F.items():
            inf = info[k]
            print(f"{F['name']} {F['W']}x{F['H']}: nests {F['nest']!r}; hero in f{self.open['hero_in']}; "
                  f"stretches {', '.join(f'MAIN {a}-{b - 1} at f{f}' for a, b, f in self.stretches)}; "
                  f"cuts {', '.join(f'f{c['frame']} {c['kind']}' for c in log)}; zoom cut entry/exit speed "
                  f"{inf['entry_ratio']:.2f}; {D} frames ({D / FPS:.2f} s)")
        for n in self.notes:
            print("NOTE:", n)
        for n in self.issues:
            print("LINT:", n)
        return out

    # ---- [hairline] (v16)
    def _thin_parts(self, art_id, sc=1.0, path="", depth=0):
        """The thin painted parts the artboard `art_id` draws, the artboards it nests included: [(label, thickness in
        the nesting artboard's px)]: a stroke, a painted box or rectangle's width or height (as checks.py [hairline]).
        Parts hidden with nothing keying them back (opacity 0, display none) are left out."""
        import xml.etree.ElementTree as ET
        if not hasattr(self, "_xml"):
            root = ET.fromstring(self.text)
            self._xml = {a.get("id"): a for a in root.iter("Artboard")}
            self._keyed = set(re.findall(r'objectId="([^"]+)"', self.text))
        def num(v, d):
            try:
                return float(v) if v not in (None, "") else d
            except ValueError:
                return d
        out = []

        def walk(el, sc, path):
            kids = list(el)
            keyed = el.get("id") in self._keyed
            style = next((c for c in kids if c.tag == "LayoutComponentStyle"), None)
            if not keyed and num(el.get("opacity"), 1.0) <= 0.05:
                return
            if style is not None and style.get("displayValue") in ("none", "1") and style.get("id") not in self._keyed:
                return
            sc = sc * min(abs(num(el.get("scaleX"), 1.0)), abs(num(el.get("scaleY"), 1.0)))
            t = [num(c.get("thickness"), 1.0) for c in kids if c.tag == "Stroke" and c.get("isVisible") != "false"]
            if any(c.tag == "Fill" and c.get("isVisible") != "false" for c in kids):
                boxes = [el] if el.tag == "LayoutComponent" else [c for c in kids if c.tag == "Rectangle"] \
                    if el.tag == "Shape" else []
                t += [num(b.get(d), 0.0) for b in boxes for d in ("width", "height") if num(b.get(d), 0.0) > 0]
            if t:
                out.append((path + (el.get("name") or el.tag), min(t) * sc))
            if el.tag in ("NestedArtboard", "NestedArtboardLayout"):
                if depth < 4 and el.get("artboardId") in self._xml:
                    out.extend(self._thin_parts(el.get("artboardId"), sc, f"{path}{el.get('name') or 'nest'} > ",
                                                depth + 1))
                return
            if el.tag in ("Node", "LayoutComponent", "Shape", "Solo"):
                for c in kids:
                    walk(c, sc, path)

        art = self._xml.get(art_id)
        for c in (list(art) if art is not None else []):
            walk(c, sc, path)
        return out

    def _hairlines(self, k):
        """[hairline] for format k: a line under 1 px on the video (its thickness x the camera's scale) while the camera
        moves slowly flickers (LEARNINGS 13; ma-novo-social v10: a 0.5 px line in the nested "Site and phone XL"
        under scene 3's slow zoom-out). Looks inside the nested MAIN, the overlays and every artboard they nest. Not
        seen: the hero's own animation (checks.py covers it when the hero builds) and where the part is (a part out of
        the framing is noted too)."""
        from checks import LIMITS
        F = self.F[k]
        fr = self.framings(k)[0]
        W, H = F["W"], F["H"]
        lo, hi = LIMITS["slow_px"]
        need = int(round(LIMITS["hairline_s"] * FPS))
        reach = 0.5 * min(W, H)
        ks = [W / f[2] for f in fr]
        speed = [0.0] + [ks[f] * math.dist(fr[f][:2], fr[f - 1][:2]) + abs(ks[f] - ks[f - 1]) / ks[f] * reach
                         for f in range(1, len(fr))]
        end = self.end["cut"]
        shows = [(F["main"]["id"], self.open["hero_in"], min(self.hide or end, end), F["nest"])]
        shows += [(o["a"]["id"], o["show"], min(o["hide"] or end, end), o["a"]["name"]) for o in self.overlays]
        found = []
        for art_id, f0, f1, label in shows:
            for name, t in self._thin_parts(art_id):
                run, best = 0, (0, 0)
                for f in range(max(1, f0), min(f1, len(fr))):
                    ok = t * ks[f] < LIMITS["hairline_px"] and lo < speed[f] < hi
                    run = run + 1 if ok else 0
                    if run > best[0]:
                        best = (run, f)
                if best[0] >= need:
                    a, b = best[1] - best[0] + 1, best[1]
                    found.append((min(t * ks[f] for f in range(a, b + 1)), f"{label} > {name}", a, b))
        if found:
            found.sort()
            self.notes.append(
                f"[hairline] {F['name']}: {len(found)} line(s) under {LIMITS['hairline_px']:g} px on the video while the "
                "camera moves slowly: " + ", ".join(f"{n} ({px:.2f} px, {a / FPS:.2f}-{b / FPS:.2f} s)"
                                                    for px, n, a, b in found[:6])
                + ("..." if len(found) > 6 else "") + f": if it is in the frame it flickers (a still never shows it). "
                f"Make it {LIMITS['hairline_fix_px']:g} px or more on the video with its opacity down in proportion "
                "(patch=, LEARNINGS 13), or check it: scripts/hairline.py <out> --at <s> --col <x> --rows <y0>:<y1>")

    def _nested(self):
        """The hero's artboards the video nests (each format's, the overlays'), once each."""
        seen = {}
        for a in [F["main"] for F in self.F.values()] + [o["a"] for o in self.overlays]:
            seen.setdefault(a["id"], a)
        return list(seen.values())

    def _hero_copy(self):
        """The hero's scene for the video: the nested artboards made components; its font and image files copied."""
        t = self.text
        for a in self._nested():
            if 'isComponent="true"' not in a["tag"]:
                assert t.count(a["tag"]) == 1, a["name"]
                t = t.replace(a["tag"], a["tag"].replace("<Artboard ", '<Artboard isComponent="true" ', 1))
        for m in set(re.findall(r'<(?:FontAsset|ImageAsset|AudioAsset)[^>]* file="([^"]+)"', t)):
            src = os.path.normpath(os.path.join(self.src_dir, m))
            rel = m if not (os.path.isabs(m) or os.path.normpath(m).startswith("..")) else \
                os.path.join("hero", os.path.basename(m))
            dst = os.path.join(self.out, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            if os.path.exists(src) and (not os.path.exists(dst) or os.path.getmtime(dst) < os.path.getmtime(src)
                                        or os.path.getsize(dst) != os.path.getsize(src)):
                shutil.copyfile(src, dst)
            elif not os.path.exists(src):
                self.notes.append(f"the hero's file {m!r} is missing at {src}")
            if rel != m:
                t = t.replace(f'file="{m}"', f'file="{rel}"')
        return t

    def _artboard_rml(self, k, F, nid, fonts, bg_id, ab_x):
        W, H, name = F["W"], F["H"], F["name"]
        cx, cy = W / 2, H / 2
        D = self.duration()
        K = Keys()
        o, e = self.open, self.end
        hero_in = o["hero_in"]
        ids = {n: nid() for n in ("ab", "fill", "col", "open", "logo", "head", "head_t", "head_ts", "head_fill",
                                  "head_col", "end", "logo2", "link", "link_t", "link_ts", "link_fill", "link_col",
                                  "link_axis", "link_run", "veil", "camz", "camk", "camp", "hero", "main_n",
                                  "clipping", "nest", "remap", "clip_s", "la", "sm", "lay", "entry", "tr", "st",
                                  "anys", "ex")}
        I = ids
        # ---- the opening card
        words = re.findall(r"\S+\s*", o["text"])
        n_lines = o["text"].count("\n") + 1
        dy, how = (o["dy"], "given") if o["dy"] is not None else text_dy(F["head_size"], F["head_lh"])
        if how != "measured":
            self.notes.append(f"{name}: the headline's text_dy {dy:.1f} px for Cal Sans {F['head_size']:g}/"
                              f"{F['head_lh']:g} is {how}: measure it against the Figma PNG (the first line's pixel "
                              "rows) and pass opening(dy=)")
        self._fit(k, o["text"], CAL_FILE, F["head_size"], F["head_w"], "the headline")
        self._fit(k, e["url"], DUDA_FILE, F["link_size"], F["link_w"], "the URL")
        logo_k = F["logo_h"] / LOGO_SVG[1]
        lo_open = F["logo_top"] * H + F["logo_h"] / 2 - cy
        head_y = -n_lines * F["head_lh"] / 2 + dy
        L = LOGO_IN
        K.add(I["logo"], "opacity", 0, 0)
        K.add(I["logo"], "opacity", L["fade"], 1, "hold")
        K.add(I["logo"], "y", 0, lo_open + L["rise"], SETTLE)
        K.add(I["logo"], "y", L["settle"], lo_open, "hold")
        groups = [(nid(), nid(), nid()) for _ in words]          # run, group, range
        for i, (_, gid, _) in enumerate(groups):
            f = WORDS["first"] + WORDS["step"] * i
            K.add(gid, "opacity", 0, 0, "hold")
            K.add(gid, "opacity", f, 0)
            K.add(gid, "opacity", f + WORDS["fade"], 1, "hold")
            K.add(gid, "y", 0, WORDS["rise"], "hold")
            K.add(gid, "y", f, WORDS["rise"], SETTLE)
            K.add(gid, "y", f + WORDS["settle"], 0, "hold")
        last_word = WORDS["first"] + WORDS["step"] * (len(words) - 1) + WORDS["settle"]
        exit0 = hero_in - REVEAL["lead"]
        if last_word > exit0:
            self.issues.append(f"{name}: the headline's last word lands at f{last_word}, after the card leaves "
                               f"(f{exit0}): bring hero_in later")
        f_open_end = hero_in + REVEAL["veil"]
        rate = o["rate"] or 1.0
        open_scale = [rate ** ((f_open_end - f) / FPS) for f in range(f_open_end + 1)]
        if rate != 1.0:
            for p in ("scaleX", "scaleY"):
                K.track(I["open"], p, open_scale)
        K.add(I["open"], "opacity", 0, 1, "hold")
        K.add(I["open"], "opacity", exit0, 1)
        K.add(I["open"], "opacity", exit0 + REVEAL["fade"], 0, "hold")
        K.add(I["open"], "y", 0, cy, "hold")
        K.add(I["open"], "y", exit0, cy, DUDA_E)
        K.add(I["open"], "y", exit0 + REVEAL["rise_frames"], cy - REVEAL["rise"], "hold")
        # ---- the background (the opening's and the end card's): dissolves into the hero, back at the cut
        K.add(I["veil"], "opacity", 0, 1, "hold")
        K.add(I["veil"], "opacity", hero_in, 1)
        K.add(I["veil"], "opacity", hero_in + REVEAL["veil"], 0, "hold")
        K.add(I["veil"], "opacity", e["cut"], 1, "hold")
        for p in ("scaleX", "scaleY"):
            K.add(I["camz"], p, 0, REVEAL["arrive"], "hold")
            K.add(I["camz"], p, hero_in, REVEAL["arrive"], SETTLE)
            K.add(I["camz"], p, hero_in + REVEAL["arrive_frames"], 1.0, "hold")
        # ---- the camera
        frs, cuts, bad = self.framings(k)
        for f, fr, world, kind in bad:
            if kind == "exit":
                raise ValueError(f"{NO_ROOM} ({name} f{f}: framing x {fr[0] - fr[2] / 2:.1f}-{fr[0] + fr[2] / 2:.1f}, "
                                 f"y {fr[1] - fr[2] * H / W / 2:.1f}-{fr[1] + fr[2] * H / W / 2:.1f} past {world})")
        if bad:
            f, fr, world, kind = bad[0]
            self.issues.append(f"{name}: the framing leaves its world on {len(bad)} frame(s), first f{f} ({kind}): x "
                               f"{fr[0] - fr[2] / 2:.1f}-{fr[0] + fr[2] / 2:.1f}, y {fr[1] - fr[2] * H / W / 2:.1f}-"
                               f"{fr[1] + fr[2] * H / W / 2:.1f}, world {world}")
        cuts = set(cuts) | {e["cut"]}
        ks = [W / w for _, _, w in frs]
        K.track(I["camk"], "scaleX", ks, cuts, eps=3e-7)
        K.track(I["camk"], "scaleY", ks, cuts, eps=3e-7)
        K.track(I["camp"], "x", [-c for c, _, _ in frs], cuts, eps=1e-4, spans=self.spans)
        K.track(I["camp"], "y", [-c for _, c, _ in frs], cuts, eps=1e-4)
        # ---- MAIN's clip
        clips = sorted(self.clips[k])
        if clips:
            n = len(clips[0][1])
            assert all(len(r) == n for _, r in clips), "clip(): the same number of rects in every call"
            rect_ids = [nid() for _ in range(n)]
            for f, rects in clips:
                for rid, (x0, y0, x1, y1) in zip(rect_ids, rects):
                    for p, v in (("x", x0), ("y", y0), ("width", x1 - x0), ("height", y1 - y0)):
                        K.add(rid, p, f, v, "hold")
        # ---- MAIN's time: the stretches
        main = F["main"]
        LEN = main["frames"]
        tkeys = self._time_keys(lambda M: M / LEN, start=None)
        for f, v, it in tkeys:
            K.add(I["remap"], "time", f, v, it)
        if self.hide is not None:
            K.add(I["main_n"], "opacity", 0, 1, "hold")
            K.add(I["main_n"], "opacity", self.hide, 0, "hold")
        ov_rml = []
        i6 = " " * 24
        for ov in self.overlays:
            a = ov["a"]
            n_id, ne_id, rm_id = nid(), nid(), nid()
            K.add(n_id, "opacity", 0, 0 if ov["show"] > 0 else 1, "hold")
            if ov["show"] > 0:
                K.add(n_id, "opacity", ov["show"], 1, "hold")
            if ov["hide"]:
                K.add(n_id, "opacity", ov["hide"], 0, "hold")
            fn = lambda M, ov=ov, a=a: (M + ov["offset"]) / a["frames"]
            tk = self._time_keys(fn, start=ov["show"])
            for f, v, it in tk:
                assert -1e-9 <= v <= 1 + 1e-9, f"overlay {a['name']}: its time leaves its Timeline at f{f} ({v:.4f})"
                K.add(rm_id, "time", f, v, it)
            x0 = ov["at"][0] + a["ox"] * a["W"]
            y0 = ov["at"][1] + a["oy"] * a["H"]
            ov_rml.append(f'{i6}<Node opacity="{0 if ov["show"] > 0 else 1}" name="HERO.{esc(a["name"])}" id="{n_id}">\n'
                          f'{i6}    <NestedArtboard artboardId="{a["id"]}" x="{g(float(x0))}" y="{g(float(y0))}" '
                          f'name="{esc(a["name"])}" id="{ne_id}">\n'
                          f'{i6}        <NestedRemapAnimation animationId="{a["tl"]}" time="{g(float(tk[0][1]))}" '
                          f'name="Time" id="{rm_id}"/>\n{i6}    </NestedArtboard>\n{i6}</Node>')
        # ---- the end card
        if F.get("end_logo"):
            ly, lh_ = F["end_logo"]
        else:     # the logo + gap + the URL's ink (~0.72 x its size) centred on the frame
            lh_ = 84 * W / 1080
            ly = cy - (lh_ + F["link_gap"] + 0.72 * F["link_size"]) / 2 + lh_ / 2
            self.notes.append(f"{name}: no approved end card for this format: the logo + URL block is centred by "
                              "formula, check it")
        lo_end, k_end = ly - cy, lh_ / LOGO_SVG[1]
        link_top = ly + lh_ / 2 + F["link_gap"] - cy
        for obj in (I["logo2"], I["link"]):
            K.add(obj, "opacity", 0, 0, "hold")
            K.add(obj, "opacity", e["cut"], 1, "hold")
        erate = e["rate"] or 1.0

        def end_scale(f):
            u = ease(ZOOM_CENTER["in_ease"], (f - e["cut"]) / ZOOM_CENTER["in_frames"])
            return erate ** ((D - 1 - f) / FPS) * (1 + ZOOM_CENTER["in_"] * (1 - u))
        exit_w = [w for _, _, w in frs[e["at"]:e["cut"]]]
        rates = [math.log(b / a) for a, b in zip(exit_w[-5:], exit_w[-4:])]
        ratio = math.log(end_scale(e["cut"]) / end_scale(e["cut"] + 1)) / (sum(rates) / 4)
        if ratio > RATIO_MAX:
            self.issues.append(f"{name}: the end card comes in faster than the exit leaves ({ratio:.2f} > {RATIO_MAX})")
        f_end = D - 1 if erate != 1.0 else e["cut"] + ZOOM_CENTER["in_frames"]
        es = [end_scale(f) for f in range(e["cut"], f_end + 1)]
        for obj in (I["end"], I["veil"]):
            for p in ("scaleX", "scaleY"):
                if obj == I["veil"] and rate != 1.0:
                    K.track(obj, p, open_scale)
                else:
                    K.add(obj, p, 0, 1, "hold")
                K.track(obj, p, es, f0=e["cut"], eps=1e-6)
        self._speeds(k, F, open_scale, exit0, lo_open, head_y, n_lines, es, lo_end, link_top)
        # ---- the RML
        i5, i6r = " " * 20, " " * 24
        runs_x = "\n".join(f'{i5}<TextValueRun styleId="{I["head_ts"]}" text="{esc(t)}" name="OPEN.w{j}" id="{r}"/>'
                           for j, (t, (r, _, _)) in enumerate(zip(words, groups)))
        groups_x = "\n".join(
            f'{i5}<TextModifierGroup modifyOpacity="true" invertOpacity="true" modifyTranslation="true" opacity="0" '
            f'y="{WORDS["rise"]}" name="OPEN.w{j}.in" id="{gid}">\n'
            f'{i6r}<TextModifierRange runId="{r}" name="OPEN.w{j}.range" id="{rid}"/>\n{i5}</TextModifierGroup>'
            for j, (r, gid, rid) in enumerate(groups))
        logo1 = _logo_node(nid, " " * 12, "OPEN.logo", lo_open + L["rise"], logo_k).replace("{ID}", I["logo"])
        logo2 = _logo_node(nid, " " * 12, "END.logo", lo_end, k_end).replace("{ID}", I["logo2"])
        f0 = frs[0]
        vm = (f' viewModelId="{main["vm"]}"' if main["vm"] else "") + \
             (f' viewModelInstanceId="{main["vmi"]}"' if main["vmi"] else "")
        clip_x = ""
        clipping = ""
        if clips:
            clipping = f'                            <ClippingShape sourceId="{I["clip_s"]}" id="{I["clipping"]}"/>\n'
            rx = "\n".join(f'                        <Rectangle x="{g(float(x0))}" y="{g(float(y0))}" '
                           f'width="{g(float(x1 - x0))}" height="{g(float(y1 - y0))}" originX="0" originY="0" '
                           f'name="HERO.clip.r{j}" id="{rid}"/>'
                           for j, (rid, (x0, y0, x1, y1)) in enumerate(zip(rect_ids, clips[0][1])))
            clip_x = f'                    <Shape name="HERO.clip" id="{I["clip_s"]}">\n{rx}\n                    </Shape>\n'
        mx, my = main["ox"] * main["W"], main["oy"] * main["H"]
        cal, duda = fonts["cal"][2], fonts["duda"][2]
        rml = f"""    <Artboard defaultStateMachineId="{I['sm']}"{vm} clip="true" width="{W}" height="{H}" x="{ab_x}" y="0" name="{name}" id="{I['ab']}">
        <Fill name="{name}.fill" id="{I['fill']}">
            <SolidColor colorValue="{BG}" name="{name}.fill.color" id="{I['col']}"/>
        </Fill>
        <Node x="{g(cx)}" y="{g(cy)}" name="OPEN" id="{I['open']}">
{logo1}
            <Node y="{g(head_y)}" name="OPEN.head" id="{I['head']}">
                <Text alignValue="center" sizingValue="autoHeight" width="{g(float(F['head_w']))}" x="{g(-F['head_w'] / 2)}" name="OPEN.headline" id="{I['head_t']}">
                    <TextStylePaint fontSize="{g(float(F['head_size']))}" lineHeight="{g(float(F['head_lh']))}" letterSpacing="0" fontAssetId="{cal}" familyName="Cal Sans" styleName="Regular" name="OPEN.style" id="{I['head_ts']}">
                        <Fill name="OPEN.headline.fill" id="{I['head_fill']}">
                            <SolidColor colorValue="{INK}" name="OPEN.headline.color" id="{I['head_col']}"/>
                        </Fill>
                    </TextStylePaint>
{runs_x}
{groups_x}
                </Text>
            </Node>
        </Node>
        <Node x="{g(cx)}" y="{g(cy)}" name="END" id="{I['end']}">
{logo2}
            <Node y="{g(link_top)}" opacity="0" name="END.url" id="{I['link']}">
                <Text alignValue="center" sizingValue="autoHeight" width="{g(float(F['link_w']))}" x="{g(-F['link_w'] / 2)}" name="END.url.t" id="{I['link_t']}">
                    <TextStylePaint fontSize="{g(float(F['link_size']))}" lineHeight="{g(float(F['link_lh']))}" fontAssetId="{duda}" familyName="Duda Sans" styleName="Regular" name="END.url.style" id="{I['link_ts']}">
                        <Fill name="END.url.fill" id="{I['link_fill']}">
                            <SolidColor colorValue="{INK}" name="END.url.color" id="{I['link_col']}"/>
                        </Fill>
                        <TextStyleAxis tag="{WGHT}" axisValue="350" id="{I['link_axis']}"/>
                    </TextStylePaint>
                    <TextValueRun styleId="{I['link_ts']}" text="{esc(e['url'])}" name="END.url.run" id="{I['link_run']}"/>
                </Text>
            </Node>
        </Node>
        <Image assetId="{bg_id}" x="{g(cx)}" y="{g(cy)}" name="VEIL" id="{I['veil']}"/>
        <Node x="{g(cx)}" y="{g(cy)}" scaleX="{g(REVEAL['arrive'])}" scaleY="{g(REVEAL['arrive'])}" name="CAM.z" id="{I['camz']}">
            <Node scaleX="{g(W / f0[2])}" scaleY="{g(W / f0[2])}" name="CAM.k" id="{I['camk']}">
                <Node x="{g(-f0[0])}" y="{g(-f0[1])}" name="CAM.p" id="{I['camp']}">
                    <Node name="HERO" id="{I['hero']}">
{chr(10).join(ov_rml)}{chr(10) if ov_rml else ''}                        <Node name="HERO.main" id="{I['main_n']}">
{clipping}                            <NestedArtboard artboardId="{main['id']}" x="{g(float(mx))}" y="{g(float(my))}" name="{esc(main['name'])}" id="{I['nest']}">
                                <NestedRemapAnimation animationId="{main['tl']}" time="{g(float(tkeys[0][1]))}" name="Time" id="{I['remap']}"/>
                            </NestedArtboard>
                        </Node>
                    </Node>
{clip_x}                </Node>
            </Node>
        </Node>
        <LinearAnimation fps="{FPS}" duration="{D}" loopValue="loop" name="Timeline" id="{I['la']}">
{K.rml(nid, ' ' * 12)}
        </LinearAnimation>
        <StateMachine name="State Machine 1" id="{I['sm']}">
            <StateMachineLayer name="Main" id="{I['lay']}">
                <EntryState y="-120" id="{I['entry']}">
                    <StateTransition stateToId="{I['st']}" id="{I['tr']}"/>
                </EntryState>
                <AnimationState animationId="{I['la']}" x="160" y="-120" id="{I['st']}"/>
                <AnyState y="60" id="{I['anys']}"/>
                <ExitState y="200" id="{I['ex']}"/>
            </StateMachineLayer>
        </StateMachine>
    </Artboard>"""
        return rml, dict(entry_ratio=ratio, exit_rates=rates)

    def _time_keys(self, fn, start=None):
        """Remap keys (frame, value, interp) for a Timeline that follows MAIN through the stretches; fn: MAIN frame ->
        the remap's time; start: the first frame it matters (held before)."""
        keys = []
        for m0, m1, a in self.stretches:
            b = a + m1 - 1 - m0
            s = a if start is None else max(a, start)
            if s > b:
                continue
            M = m0 + s - a
            if s == b:
                keys.append((s, fn(M), "hold"))
            else:
                keys.append((s, fn(M), None))
                keys.append((b, fn(m1 - 1), "hold"))
        assert keys, "the overlay shows after the last stretch"
        if keys[0][0] > 0:
            keys.insert(0, (0, keys[0][1], "hold"))
        return keys

    def _fit(self, k, text, file, size, box, what):
        try:
            from PIL import ImageFont
            font = ImageFont.truetype(os.path.join(FONTS, file), size)
            for line in text.split("\n"):
                w = font.getlength(line.strip())
                if w > box:
                    raise ValueError(f"{self.F[k]['name']}: {what}'s line {line.strip()!r} is {w:.0f} px wide, its box "
                                     f"{box:g}: Rive would wrap it (break it with \\n or shorten it)")
                if w > 0.97 * box:
                    self.notes.append(f"{self.F[k]['name']}: {what}'s line {line.strip()!r} fills {w / box:.0%} of "
                                      "its box: check it doesn't wrap")
        except ImportError:
            pass

    def _speeds(self, k, F, open_scale, exit0, lo_open, head_y, n_lines, es, lo_end, link_top):
        """The cards' peak speeds (logo and text corners on screen) against the speed caps."""
        W, H = F["W"], F["H"]
        cy = H / 2
        rate = W / 1920
        cap_t, cap_l = SPEED_CAP["text"] * rate, SPEED_CAP["logo"] * rate
        o = self.open
        sc = lambda f: open_scale[min(f, len(open_scale) - 1)]
        oy = lambda f: cy - REVEAL["rise"] * ease(DUDA_E, (f - exit0) / REVEAL["rise_frames"]) if f > exit0 else cy
        ly = lambda f: lo_open + LOGO_IN["rise"] * (1 - ease(SETTLE, f / LOGO_IN["settle"]))
        half = F["head_w"] / 2
        peaks = {}
        last = exit0 + REVEAL["fade"]
        for what, pts in (("opening logo", lambda f: [(0, ly(f))]),
                          ("opening headline", lambda f: [(sx * half, head_y + sy * n_lines * F["head_lh"])
                                                          for sx in (-1, 1) for sy in (0, 1)])):
            pk = 0.0
            for f in range(1, last):
                a = [(W / 2 + sc(f - 1) * x, oy(f - 1) + sc(f - 1) * y) for x, y in pts(f - 1)]
                b = [(W / 2 + sc(f) * x, oy(f) + sc(f) * y) for x, y in pts(f)]
                pk = max(pk, max(math.dist(p, q) for p, q in zip(a, b)))
            peaks[what] = pk
        url_w = F["link_w"] / 2
        for what, pts in (("end logo", [(0, lo_end)]), ("end URL", [(-url_w, link_top), (url_w, link_top)])):
            pk = max((math.dist((x * es[i], y * es[i]), (x * es[i + 1], y * es[i + 1])) for i in range(len(es) - 1)
                      for x, y in pts), default=0.0)
            peaks[what] = pk
        for what, pk in peaks.items():
            cap = cap_l if "logo" in what else cap_t
            if pk > cap:
                self.issues.append(f"{F['name']}: {what} peaks at {pk:.1f} px/f > cap {cap:.1f}")
        self.notes.append(f"{F['name']}: card speeds (px/f) " + ", ".join(f"{w} {v:.1f}" for w, v in peaks.items())
                          + f" (caps: text {cap_t:.1f}, logo {cap_l:.1f})")
