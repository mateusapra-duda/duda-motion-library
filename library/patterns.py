"""v04: the hero pieces' patterns, built from the library and native text (no exports): the Quick Edits panel, the Code
tab (a code editor that writes itself, a file tree), the AI's "Generating... / Done" status, and the Generation
effect (hero_1's square, with hero-view's details). Piece and Actions take them in (piece.py): a piece still imports
only piece.py.

Measures: the Vibe page hero storyboards (Figma 305:12538) at product size (the storyboards draw the product at
0.81); the code editor's colours and stream, hero3-code v04; the Generation effect, hero_1 as hero-view / hero3-code
make it."""
import math
import os
import random
import re

import kit
from kit import El
from common import FPS, SWAP, secs, Item, _el, _color
import choreo
from choreo import frame

# ---------------------------------------------------------------- the code editor
SYNTAX = {"k": "#0033BF", "f": "#785E26", "t": "#268099", "s": "#A31414", "p": "#1F1F24", "c": "#6A737D",
          "ln": "#3D4A73", "caret": "#0033BF"}   # hero3-code (the storyboard's editor); c: comments
KEYWORDS = set("import from export default function return const let var if else for while do switch case break "
               "continue new class extends async await try catch finally throw typeof instanceof in of true false "
               "null undefined this as type interface".split())
TOKEN = re.compile(r"(//.*$)|(\"(?:\\.|[^\"])*\"|'(?:\\.|[^'])*'|`(?:\\.|[^`])*`)|([A-Za-z_$][\w$]*)|(\s+)|(.)")
CARET = "▏"


def highlight(line):
    """A line of JS / JSX -> [(text, kind)]: k keyword, f function call, t a component's tag, s string, c comment,
    p the rest. Spaces join the run before them."""
    runs = []
    for m in TOKEN.finditer(line):
        com, s, word, sp, _ = m.groups()
        tok = m.group(0)
        if com:
            kind = "c"
        elif s:
            kind = "s"
        elif word:
            before = line[:m.start()].rstrip()
            if word in KEYWORDS:
                kind = "k"
            elif before.endswith(("<", "</")) and word[0].isupper():
                kind = "t"
            elif line[m.end():].lstrip().startswith("("):
                kind = "f"
            else:
                kind = "p"
        else:
            kind = runs[-1][1] if sp and runs else "p"
        if runs and runs[-1][1] == kind:
            runs[-1] = (runs[-1][0] + tok, kind)
        else:
            runs.append((tok, kind))
    return runs


def tokens(s):
    """AI-sized chunks: a word, or a run of up to 3 punctuation marks, each carrying the spaces before it."""
    toks = re.findall(r"\s*(?:\w+|[^\w\s]{1,3})", s)
    rest = s[len("".join(toks)):]
    return toks + ([rest] if rest else [])


# ---------------------------------------------------------------- the Generation effect (hero_1)
FX_STOPS = [("00DDF1F9", 0), ("FFDDF1F9", .162), ("FFE6D7F1", .336), ("FFF4BBD2", .503), ("FFF9A84A", .681),
            ("FFF0CE72", .848), ("00F0CE72", 1)]   # stop 2 turns from lavender to light blue during the sweep
SWEEP0 = {"startX": -535.6, "startY": -1582.6, "endX": -105.1, "endY": -234.8}
SWEEP1 = {"startX": 107.4, "startY": 213.6, "endX": 1831.9, "endY": 4515.4}
SWEEP_EASE = [0.588, 0.0, 0.377, 1.0]  # v11: every pass of the example (generation-effect-example.rev, CENA 5 SUPPORT 2)
# frames from the start (hero_1: MINI CARDS / TOP FLAVORS); feathers in px on screen at a 1340 px hero (FEATHER_AT
# scales them for a smaller piece). v14 (Mateus, 2026-11-23: a lighter generation in every piece; the precision research,
# pecas/pesquisa-precisao/3-ajustes-mao.md 7: his hand edits of hero-view v15.1, marketing-automation v14 / v15.1,
# ma-simplified-flow v07.10, ma-novo v05 and lumi-dental-winback v04 all lowered the library's squares): the first
# feather ~0.6x (cards 18 -> 11, panels 16 -> 10; his 7-15), the last 1-2.5 (cards 3 -> 2, panels 0 -> 1.5), the first
# scale 1.08 on cards (was 1.11) and 1.02 on panels (was 1.03), and the big square fades in over 16 frames (his 12-20,
# hero-view v15.1) instead of showing whole on its first frame
GEN = {
    "small": dict(sweep=84, s0=1.08, scale=(13, 44), feather=(11, 2, 13, 42), stop=(37, 84), show=(36, 8), fade=0),
    "big": dict(sweep=131, s0=1.02, scale=(23, 68), feather=(10, 1.5, 23, 68), stop=(58, 131), show=(56, 8),
                fade=16),
}
GEN_VARY = 0.10   # v14: each square's first feather varies up to +-10 % ("vary between them", MA v14), seeded by name
# v11 (Mateus's rule of 2026-11-13, measured in the example): numbers come in #AE68FA and turn to their own colour with a
# Feather 4 -> 0 (26-41 frames, linear) and count 1.5-3 s on (0, 0, 0, 1), ending slowly; a wash at 50 % (scale 110 %,
# Feather 20 -> 3) sweeps the whole area in 217 frames before the blocks. (v11's purples on texts and loose elements are
# gone in v14: LEARNINGS 7, "purple texts on a classic generation" is wrong; `pop_color=` / `color=` keep them.)
PURPLE, LOOSE_PURPLE = "FFAE68FA", "FF8D5DF5"
# v13c (LEARNINGS 7, Mateus's rule of 2026-11-18, lumi-dental-winback v02): a block covers its component with room to
# spare, 5 px more on every side and the component's radius + 5 (a square corner gets 5): at the exact size, the
# block's soft edge let the component's edge show through (dark dashes around the block, on a photo's edge)
ROOM = 5
DETAILS = dict(rows=dict(step=0.083, rise=4, dur=0.5, fade=0.15),      # hero3-code v04 beats.yaml `details`
               pop=dict(lead=0.40, across=0.35, fade=8 / 60, dur=36 / 60, feather=4.0),
               count=dict(dur=2.0, ease=[0.0, 0.0, 0.0, 1.0], dur_color=40 / 60, feather=4.0, spread=(10, 35)),
               loose=dict(fade=20 / 60, dur=40 / 60, feather=4.0))
# v14: the wash's tail could stay faintly in a corner after its sweep (lumi-dental-winback NOTES 2): it fades out
# over `out` frames as the sweep ends (the piece faded it by hand)
WASH = dict(sweep=217, opacity=0.5, scale=1.1, feather=(20, 3, 35, 108), out=18)
# v14, LEARNINGS 7 "Feathers follow the size the piece is shown at": GEN's and WASH's feathers are a 1340 px hero's;
# on the 432 x 264 card (lumi-dental-winback v04-v06, approved 2026-11-18) the squares came to 7.2 -> 1.2 (0.65 of
# v14's card 11 -> 2), the wash to half (10 -> 1.5), the texts and icons 4 -> 2. In between, by the width the piece
# is shown at (p.shown_at; default its artboard's width): the factor at SIZE_REF[0], 1 from SIZE_REF[1]
SIZE_REF = (432, 1340)
FEATHER_AT = {"square": 0.65, "wash": 0.5, "text": 0.5}
# v14, LEARNINGS 7 ("Texts and icons the AI generates", "How a text comes in") as lumi-dental-winback v05-v06 made it
# (approved 2026-11-18): copy comes in letter by letter, a soft front ~6 letters wide at ~45 letters a second (0.4-0.9 s
# a text); the whole text (an icon too) in the classic gradient's orange from the start, its pink over 10 frames after
# max(0.35 s, 60 % of the entrance), held 8, then its own colour over 20, linear; Feather 4 -> 0 over 40, linear (by the
# size shown: 2 on the 432 card). Inside a block they start `lead` s after the block shows, (small card, screen): lumi's
# banner letters as it shows (0), the welcome email's "Welcome." 0.4 s after (LEARNINGS 7: sooner, on a big block, they
# light up hidden under it); the next one in reading order `step` frames later, or, right under the one before (a
# heading's second line), when it ends. Icons come in over `icon_fade` frames. A label that comes in whole
# (letters=False; LEARNINGS 7 "Short labels on interface blocks", a node on a map): opacity over 8 frames, Feather
# 6 -> 0 over 54, the same colour pass
INK = ("FFF9A84A", "FFF4BBD2")       # the classic gradient's orange (its stop .681) and pink (.503)
TEXT_FX = dict(cps=45, d=(0.4, 0.9), soft=6, lead=(0.0, 0.40), step=6, pink_at=(0.35, 0.6), pink=10, hold=8, own=20,
               feather=4.0, feather_dur=40, icon_fade=20, whole=dict(fade=8, feather=6.0, feather_dur=54))
NUMBER = re.compile(r"[\s$€£¥+\-−~≈]*[\d][\d.,\s]*[%kKmMbBxX+]?\s*")   # a text that is a number keeps the purple pop
# v14, LEARNINGS 7 "Photos settle inside their frame" (lumi-dental-winback v04, approved): 112 % -> 100 % over 1.5 s on
# (0.16, 1, 0.3, 1), from `lead` frames before the photo shows under its block; its frame doesn't move. On that curve
# it is 97 % there half way: the generation counts it as landed then (`landed`), so the steps don't wait for its tail
SETTLE = dict(s0=1.12, dur=1.5, ease=[0.16, 1.0, 0.3, 1.0], lead=6, landed=0.5)
SHIMMER_S = 1.6                         # the product's AiProcessIndication shimmer period
# v13 (the approved recipe of 2026-11-13, motion-spec/LEARNINGS.md 19.2; the reviewer's hand-finished welcome email):
# frames from the send. The wash 6 -> 223; the first block 108, the next ones `gap` apart (63 frames, ~1 s); a block's
# pass on (0.42, 0, 0.58, 1); the steps: status at 0, the summary's room 18, the summary 33, the first step 54.
# v14 (LEARNINGS 7, "Top to bottom, big to small"; 19.2 "A small card"): the blocks in reading order (top to bottom,
# left to right in a row: tops within `row` px), each gap varied up to +-`jitter` ("vary the rhythm between blocks, so
# it doesn't look robotic"); the first block and the gaps by the size shown, (small card, screen): lumi-dental-winback's
# 96 and 28 frames (~0.5 s) at 432 px, the welcome email's 108 and 63 (~1 s) from 772 px (`size`; ask-your-agent's card,
# where 19.2 was measured). A loose element takes its place in that order: `after_show` frames after the block above
# it shows (the welcome email's quote at 168, its photo showing at 164; lumi's heading 4 frames after its photo shows),
# but `loose_lead` frames before the block below starts when that is sooner (lumi's logo, between the banner and the
# photo); above every block, `loose_lead` frames after the first starts (the welcome email's name at 111); several
# together `loose_gap` frames apart (2-4). Each block's texts and icons as it shows (no "details" at the end any more)
SCREEN = dict(wash=6, block=(96, 108), gap=(28, 63), ease=[0.42, 0.0, 0.58, 1.0], jitter=0.15, row=12,
              loose_lead=3, loose_gap=3, after_show=4, size=(432, 772))
STEPS_INTRO = dict(room=18, summary=33, first=54)
# v14 (Mateus, 2026-11-23; the blind test, pecas/pesquisa-precisao/4-cego-aya.md: 243 letters at 120 a second took 2 s,
# and the scene settled at 7.6 s instead of 5.5): the answer types as a plain typewriter (LEARNINGS 6: each letter
# whole, no soft front, no feather, no colour pass), ~120 letters a second, never longer than ~1 s in all
REPLY_CPS, REPLY_MAX_S = 120, 1.0
# v14 (LEARNINGS 5, "A prompt"; the Copilot's prompt in the reviewer's hand edits): the text types in over 84 frames on
# (0.1804, 0.0442, 0.2292, 0.676), from 9 frames after the click: one key on the letters shown (a.typewrite for a
# field of your own; piece.py keys the AiPanel's `typed` the same way); the send button presses on its own `send` frames
# after the last letter (ma-novo v18.20B, approved: the typing ends at +124 frames, the press at +169)
PROMPT_TYPE = dict(lead=9, dur=84, ease=[0.1804, 0.0442, 0.2292, 0.676], send=45)
# v14b (the blind test, pecas/pesquisa-precisao/6-cego-aya-v14.md 5.1): the docked Copilot's field as the product draws
# it (ask-your-agent v05-v06, approved 2026-11-09: "the same top, shorter", only "+" and send), at 1x. h: the product's
# ~124 (the approved 100.83 at 0.81: Figma's top 558.21, 12.96 above the frame's bottom); "+" a 16 px icon with no
# outline in a 24 slot, 12 from the left; the 26 px button 12 from the right and the bottom; the placeholder at 12, 14.
# The button (the team's rule of 2026-11-19, the AiPanel's SendBtn): grey #C9CACD with a white arrow while the field is
# empty, orange from the first letter (a hold key, no fade), the orange stop while the Copilot works; at the answer the
# stop fades out and the grey send fades in after it (`swap` s each: the approved's 280-286 and 286-292)
FIELD = dict(h=124.5, r=8, pad=12, ph_top=14, btn=26, plus=24, arrow=13, square=8.1, square_r=2, edge="#EDEDEE",
             active="#CFCFD3", hint="#9B9BA2", off="#C9CACD", on="#F56D41", ink="#272B35", swap=SWAP)
STEP_WEIGHTS = (1.0, 0.82, 1.45)          # the reference's step lengths (33, 27, 48 frames); the last waits longest
STEP_LAST = 2.1                           # (69 frames)


def _hsl(c):
    import colorsys
    c = _argb(c)
    r, g, b = (int(c[i:i + 2], 16) / 255 for i in (2, 4, 6))
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    return h * 360, s, l


def _hex(h, s, l):
    import colorsys
    r, g, b = colorsys.hls_to_rgb((h % 360) / 360, max(0, min(1, l)), max(0, min(1, s)))
    return "#%02X%02X%02X" % tuple(round(v * 255) for v in (r, g, b))


def _mix(a, b, k):
    a, b = _argb(a), _argb(b)
    return "#" + "".join("%02X" % round(int(a[i:i + 2], 16) * (1 - k) + int(b[i:i + 2], 16) * k) for i in (2, 4, 6))


def palette(warm, cool):
    """v13, "The design's colours" (approved 2026-11-13, motion-spec/LEARNINGS.md 7): the generation's tones from the
    design's own gradient, its two ends (a background, a card, a button: any gradient), slightly stronger than in the
    design so they show over it, with a middle tone between them. Measured on the welcome email (#FFFBD6 -> #DCEBFF):
    wash #FFF3B0 #FFE8A3 #E3E0F4 #B9D2F6 #D6E4FB; blocks #B9D2F6 ... #E3E0F4 and #FFE8A3 ... #DCE6F6; texts #907EF1;
    details #F8CD4F then #907EF1. Returns {"wash": 5 colours, "blocks": [5, 5], "text": c, "details": [c, c]}."""
    wh, ws, wl = _hsl(warm)
    ch, cs, cl = _hsl(cool)
    w1, w2 = _hex(wh - 3, ws, wl - 0.07), _hex(wh - 9, ws, wl - 0.10)
    c1, c2 = _hex(ch + 1, cs - 0.21, cl - 0.08), _hex(ch + 3, cs - 0.19, cl - 0.02)
    mid = _hex(ch + 35, 0.50, max(wl, cl) - 0.01)
    text = _hex(ch + 35, 0.81, 0.72)
    detail = _hex(wh - 9, 0.92, 0.64)
    return {"wash": [w1, w2, mid, c1, c2],
            "blocks": [[c1, _mix(c1, c2, 0.5), c2, _mix(c2, mid, 0.5), mid],
                       [w2, _mix(w2, c2, 0.12), _mix(w2, c2, 0.3), _mix(w2, c2, 0.65), c2]],
            "text": text, "details": [detail, text]}


def _stops(colors=None):
    """The 7-stop gradient: the example's (FX_STOPS), or a designer's own 5 colours (as #hex or ARGB) at its positions,
    transparent at both ends."""
    if not colors:
        return list(FX_STOPS)
    cs = [_argb(c) for c in colors]
    assert len(cs) == 5, "colors: the 5 colours in the gradient's order (default #DDF1F9, #E6D7F1, #F4BBD2, #F9A84A, #F0CE72)"
    pos = [p for _, p in FX_STOPS]
    return [("00" + cs[0][2:], pos[0])] + list(zip(cs, pos[1:6])) + [("00" + cs[4][2:], pos[6])]


def _feather_scale(h):
    """hero_1's feather was made for boxes 33+ px tall; a thin one keeps the same look with less."""
    return min(1.0, h * 0.6 / 18)


def _argb(c):
    return c if len(c) == 8 and not c.startswith("#") else _color(c)


def _pinned(e):
    """A box pinned out of the flow (kit.absolute: a card's shadow layers and edge, a hit area)."""
    st = next((c for c in e.children if isinstance(c, El) and c.tag == "LayoutComponentStyle"), None) \
        if e.tag == "LayoutComponent" else None
    return st is not None and st.attrs.get("positionTypeValue") == "absolute"


def _off(e):
    """A box hidden at rest (display none: another variant's part, a hit area)."""
    st = next((c for c in e.children if isinstance(c, El) and c.tag == "LayoutComponentStyle"), None) \
        if e.tag == "LayoutComponent" else None
    return st is not None and st.attrs.get("displayValue") in ("none", 1)


VERTS = ("StraightVertex", "CubicDetachedVertex")


def _contour(path):
    """A PointsPath as a polygon in its own space (each segment in 8 steps along its curve)."""
    vs = [c for c in path.children if isinstance(c, El) and c.tag in VERTS]
    xy = lambda v: (float(v.attrs["x"]), float(v.attrs["y"]))   # noqa: E731

    def handle(v, k):
        if v.tag != "CubicDetachedVertex":
            return xy(v)
        a, d = float(v.attrs.get(f"{k}Rotation") or 0), float(v.attrs.get(f"{k}Distance") or 0)
        return xy(v)[0] + math.cos(a) * d, xy(v)[1] + math.sin(a) * d
    pts = []
    for i, v in enumerate(vs):
        w = vs[(i + 1) % len(vs)]
        p0, c0, c1, p1 = xy(v), handle(v, "out"), handle(w, "in"), xy(w)
        for k in range(8):
            t = k / 8
            u = 1 - t
            pts.append(tuple(u ** 3 * p0[j] + 3 * u * u * t * c0[j] + 3 * u * t * t * c1[j] + t ** 3 * p1[j]
                             for j in (0, 1)))
    return pts


def _area(pts):
    """Signed area, y down: positive = clockwise on screen."""
    return sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1])) / 2


def _in_poly(pt, pts):
    x, y = pt
    inside = False
    for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]):
        if (y0 > y) != (y1 > y) and x < x0 + (y - y0) * (x1 - x0) / (y1 - y0):
            inside = not inside
    return inside


def _reverse(path):
    """The path drawn the other way: its vertices in the other order, each one's in and out swapped."""
    vs = [c for c in path.children if isinstance(c, El) and c.tag in VERTS]
    for v in vs:
        if v.tag == "CubicDetachedVertex":
            at = v.attrs
            at["inRotation"], at["outRotation"] = at.get("outRotation", 0.0), at.get("inRotation", 0.0)
            at["inDistance"], at["outDistance"] = at.get("outDistance", 0.0), at.get("inDistance", 0.0)
    path.children[:] = [c for c in path.children if not (isinstance(c, El) and c.tag in VERTS)] + vs[::-1]


def _wind_clockwise(shape, rule):
    """Turns a shape's contours so the clockwise fill rule fills what `rule` (nonZero / evenOdd) did: under evenOdd
    a contour inside an even number of others winds clockwise, inside an odd number the other way (a hole); under
    nonZero a whole group (an outer contour and those inside it) is turned when its outer contour winds
    anticlockwise."""
    paths = [c for c in shape.children if isinstance(c, El) and c.tag == "PointsPath"]
    polys = [_contour(p_) for p_ in paths]
    areas = [_area(pts) if len(pts) > 2 else 0.0 for pts in polys]
    n = len(paths)
    outer = [[j for j in range(n) if j != i and polys[i] and abs(areas[j]) > abs(areas[i]) and
              _in_poly(polys[i][0], polys[j])] for i in range(n)]
    for i, p_ in enumerate(paths):
        if not areas[i]:
            continue
        if rule == "evenOdd":
            flip = (areas[i] > 0) != (len(outer[i]) % 2 == 0)
        else:
            top = next((j for j in outer[i] if not outer[j]), i)
            flip = areas[top] < 0
        if flip:
            _reverse(p_)


class Patterns:
    """Piece placers (p.quick_edits, p.code_editor, p.file_tree, p.code_panel, p.gen_status, p.asset)."""

    def copilot_panel(self, name, header, chat, field=None, note=None, w=367, h=842, pad=(20, 16, 16, 12),
                      chat_gap=21.2, chat_pad=0, fill="#FFFFFF", edge="#E4E4E7", margin=16):
        """v13.1: the Copilot docked beside a product screen (the email editor, the automation map...), at its 1x
        size (place it at the storyboard's scale in a p.free): `header` on top, the conversation (`chat`: its items
        top to bottom, or one box; it takes the room left and clips), the ChatInput `field` and the disclaimer `note`
        (optional) at the bottom, `w` x `h` and `pad` (left, top, right, bottom) as Figma draws it; `edge`: its 1 px
        left line. The field is always whole in the frame (Mateus, 2026-11-13): when the artboard shows less than the
        panel's `h` (the storyboard cuts the panel), the panel ends at the artboard's bottom edge, the field pinned
        `margin` above it (the panel's side padding, 16: 13 px at 0.81) and the conversation keeps less room; the
        note is then out of the frame. Targets: .chat, .field.
        v14b: `field` defaults to the product's field (p.copilot_field: "Reply to Copilot", 124.5 high, only "+" and
        send); pass p.copilot_field(...) for another placeholder or a prompt to type, or your own box as before. With
        a p.copilot_field, the p.chat_steps / p.chat_reply in `chat` drive it on their own: a.think / a.steps (the
        message sent) turn its button into the orange stop and its edge active, a.reply (with the status swap) brings
        the grey send back and the edge rests."""
        if field is None:
            field = self.copilot_field(f"{name}Field")
        if isinstance(chat, (list, tuple)):
            chat = self._box(f"{name}Chat", list(chat), "column", chat_gap, chat_pad, "topLeft", "fill", "fill",
                             clip=True)
        kids = [header, chat, field] + ([note] if note is not None else [])
        panel = self._box(name, kids, "column", 0, pad, "topLeft", w, h,
                          paints=[kit.solid(f"{self.art}.{name}.fill", _color(fill))] if fill else ())
        if edge:
            self._edge(panel, "left", edge)
        panel.kind, panel.chat, panel.field = "copilotpanel", chat, field
        panel.fit = dict(h=float(h), margin=float(margin), note=note)
        if not hasattr(self, "_fits"):
            self._fits = []
        self._fits.append(panel)
        if getattr(field, "kind", None) == "copilotfield":   # v14b: the answer in the chat drives the field
            ids = set()
            kit.walk(_el(chat), lambda e: ids.add(id(e)))
            for it in self.items.values():
                if it.kind in ("chatsteps", "reply") and id(it.wrap) in ids:
                    it.field = field
        return panel

    def copilot_field(self, name, placeholder="Reply to Copilot", prompt=None, w="fill", h=None):
        """v14b (the blind test, 6-cego-aya-v14.md 5.1; ask-your-agent v05-v06, approved): the docked Copilot's field
        ("Reply to Copilot") as the product draws it, at 1x: `h` the product's 124.5 (100.8 at 0.81; Figma's 176 has a
        row of icons the product doesn't), white, radius 8, a 1 px #EDEDEE edge, the placeholder (Body 14, #9B9BA2) at
        12, 14, and at its foot only "+" (no outline) at the left and the send button at the right. p.copilot_panel
        makes one by default and pins it `margin` above the frame's bottom (in a 0.81 frame cut like the welcome
        email's: 100.8 high, its top at Figma's 558).
        The button follows the team's rule (2026-11-19): grey #C9CACD with a white arrow while the field is empty,
        orange #F56D41 from the first letter typed (a hold key), the orange stop (a white square) while the Copilot
        works. It is keyed for you: a.think / a.steps on the chat's answer (the message sent; from frame 0 when sent
        at 0) turn it into the stop and the edge active (#CFCFD3); a.reply, with the status swap, fades the stop out
        and the grey send in after it (0.1 s each) as the edge rests. `prompt`: a text to type into the field
        (`field.prompt`, a p.text, hidden until typed): a.typewrite(field.prompt, ...) hides the placeholder and
        makes the edge active as it starts, the button orange on the first letter; a.send(field.prompt, t,
        message=bubble) presses the button, flies the text out and shows the stop with the message (+23 frames).
        Targets: .prompt, .placeholder, .button."""
        F = FIELD
        n = f"{self.art}.{name}"
        h = F["h"] if h is None else h
        ph = self.text(f"{name}Ph", placeholder, style="Content/Body 14", color=F["hint"])
        kids = []
        if prompt is not None:
            pr = self.text(f"{name}Prompt", prompt, style="Content/Body 14", color=F["ink"], w="fill")
            kids.append(kit.absolute(f"{n}.promptAt", [pr.wrap], inset=(F["pad"], F["ph_top"], F["pad"], None),
                                     layoutHeightScaleType="hug"))
        kids.append(kit.absolute(f"{n}.phAt", [ph.wrap], inset=(F["pad"], F["ph_top"], None, None), **kit.hug()))
        # the edges: the resting one, and the active one over it (shown while focused or working)
        for key, col, op in (("edgeOn", F["active"], 0.0), ("edge", F["edge"], None)):
            kids.append(kit.absolute(f"{n}.{key}", paints=[kit.line(f"{n}.{key}.s", _color(col))],
                                     inset=(0.5,) * 4, cornerRadiusTL=F["r"] - 0.5, opacity=op))
        # "+" (no outline), centred on the button's row
        plus = self.icon(f"{name}Plus", "i_plus", color=F["ink"], size=16, slot=F["plus"])
        kids.insert(0, kit.absolute(f"{n}.plusAt", [plus.wrap],
                                    inset=(F["pad"], None, None, F["pad"] + (F["btn"] - F["plus"]) / 2), **kit.hug()))
        # the button: the grey disc, the orange disc, the stop's square and the arrow (bottom to top), one look at a
        # time by their opacities (a.think / a.reply / a.typewrite key them)
        b, c = F["btn"], F["btn"] / 2
        arrow = kit.icon(os.path.join(kit.ICONS, f"{kit.ICON_FILES['i_arrow_top']}.svg"), f"{n}.arrow", kit.WHITE,
                         x=c - F["arrow"] / 2, y=c - F["arrow"] / 2, size=F["arrow"])
        kit.walk(arrow, lambda e: e.attrs.update(thickness=kit.ICON_STROKE * 16 / F["arrow"]) if e.tag == "Stroke"
                 else None)     # Figma's arrow: 13 px, its stroke kept at 1.5
        art = El("Node", {}, [
            kit.shape_ellipse(f"{n}.grey", b, fill=_color(F["off"]), x=c, y=c),
            kit.shape_ellipse(f"{n}.orange", b, fill=_color(F["on"]), x=c, y=c, opacity=0.0),
            kit.shape_rect(f"{n}.square", F["square"], F["square"], r=F["square_r"], fill=kit.WHITE, x=c, y=c,
                           opacity=0.0),
            arrow], name=f"{n}.button.art", order="layers")
        btn = self._box(f"{name}Button", [art], "column", 0, 0, "topLeft", b, b, origin=(0.5, 0.5))
        kids.insert(0, kit.absolute(f"{n}.buttonAt", [btn.wrap], inset=(None, None, F["pad"], F["pad"]),
                                    **kit.hug()))
        field = self._box(name, kids, "column", 0, 0, "topLeft", w, h, paints=[kit.solid(f"{n}.fill", kit.WHITE)],
                          cornerRadiusTL=F["r"])
        field.kind = "copilotfield"
        field.placeholder, field.button = ph, btn
        field.prompt = self.items.get(f"{name}Prompt") if prompt is not None else None
        if field.prompt is not None:
            field.prompt.field = field
        field.looks = [(0, "empty")]     # (frame, look): a.think / a.reply / a.typewrite / a.send add to it
        return field

    @staticmethod
    def palette(warm, cool):
        """v13: the generation's colours from the design's own gradient (its two ends): see patterns.palette."""
        return palette(warm, cool)

    def shown_at(self, w):
        """v14 (LEARNINGS 7, "Feathers follow the size the piece is shown at"): the width (css px) the piece is shown
        at on the page, when it isn't its artboard's (a 1340 artboard shown in a 432 card). The generation's feathers
        (squares, wash, texts, icons) scale by it: a 1340 px hero's at 1340 and up, lumi-dental-winback's (approved)
        at 432, in between by the width. Call it before the actions."""
        self.shown_w = float(w)
        return self.shown_w

    # ------------------------------------------------------------ own files
    def asset(self, key, file, quality=None):
        """An image file of the piece (in its folder) for your own drawing: returns its asset id ("@img.<key>") for
        an Image element (p.image places one in a box for you).
        v14: quality (0-100): this photo's WebP quality in the slim .riv, instead of slim.py's 90 (as p.image(quality=):
        a big hero photo can go lower, a screenshot with small text higher)."""
        k = f"{self.key}_{key}"
        kit.image_asset(k, os.path.join(self.here, file))
        if quality is not None:
            import slim                      # here, not at the top: slim is a build step, not every piece runs it
            slim.QUALITY[f"img.{k}"] = quality
        return f"@img.{k}"

    # ------------------------------------------------------------ the code editor
    def code_editor(self, name, code, size=10, lh=17, numbers=True, empty=True, w="fill", h="fill", num_w=24,
                    pad=(8, 12, 16, 12), colors=None):
        """A code editor in JetBrains Mono (size / lh: the hero's 10 / 17), line numbers in a column at its left.
        code: the text (lines; JS / JSX is coloured on its own: keywords, calls, components, strings, comments), or
        a list of lines, each a string or [(text, kind)] (kind k, f, t, s, c, p). empty=True: the file starts empty
        and a.write_code() writes it, line by line (the caret rides the text, each number shows with its line).
        colors: {kind: '#rrggbb'} over the hero's (SYNTAX)."""
        kit.FONTS.setdefault("mono", ("JetBrainsMono-Regular.ttf", "JetBrains Mono"))
        pal = dict(SYNTAX, **(colors or {}))
        lines = code.split("\n") if isinstance(code, str) else list(code)
        lines = [highlight(ln) if isinstance(ln, str) else list(ln) for ln in lines]
        n0 = f"{self.art}.{name}"
        st = {}

        def style(kind):
            if kind not in st:
                st[kind] = kit.text_style(f"{self.key}_{name}_{kind}", None, _color(pal[kind]), size=size, lh=lh,
                                          font="mono")
            return st[kind]
        rows, runs, carets, nums = [], {}, {}, {}
        for i, line in enumerate(lines, 1):
            t = kit.text(f"{n0}.L{i}", [(style(k), "") for _, k in line] + [(style("caret"), "")], lp=kit.hug(),
                         wrap=False)
            names = [f"{n0}.L{i}.run{j}" for j in range(len(line) + 1)]
            if not empty:     # the literal goes in after (a run of code may start with "=", a binding to kit.text)
                for el, (txt, _) in zip((c for c in t.children if c.tag == "TextValueRun"), line):
                    el.attrs["text"] = txt
            runs[i], carets[i] = names[:-1], names[-1]
            self.no_layout.update(names)      # one line, a fixed row: its text never moves anything else
            kids = [t]
            if numbers:
                num = kit.text(f"{n0}.N{i}", [(style("ln"), str(i))], lp=kit.fill_w(), wrap=False, align="right",
                               opacity=0 if empty else None)
                nums[i] = num.name
                kids = [kit.box(f"{n0}.Nb{i}", [num], w=num_w, h=lh, flexDirectionValue="column",
                                layoutAlignmentType="topRight", layoutWidthScaleType="fixed",
                                layoutHeightScaleType="fixed"), t]
            rows.append(kit.box(f"{n0}.row{i}", kids, h=lh, flexDirectionValue="row", layoutAlignmentType="topLeft",
                                gapHorizontal=14, layoutWidthScaleType="fill", layoutHeightScaleType="fixed"))
        ed = self._box(name, rows, "column", 0, pad, "topLeft", w, h, clip=True)
        ed.kind = "code"
        ed.lines, ed.runs, ed.carets, ed.nums, ed.line_done = lines, runs, carets, nums, {}
        return ed

    def file_tree(self, name, entries, w=146, selected=None, row_h=24, style="Content/Body"):
        """The Code tab's file tree: entries top to bottom, two spaces of indent a level; "name/" a folder (a
        chevron), else a file (its icon); "+name": a file not there yet, a.add_file(tree, "name") brings it in (the
        rows below make room). selected: the file shown in the editor (a grey row).
        Targets: tree.rows["App.tsx"] (each row)."""
        ink = kit.color("Typography/primary-text-color")
        ink2 = kit.color("Typography/secondary-text-color")
        k = f"{self.key}_{name}"
        kit.text_style(k, style, ink)
        rows, slots, items, hidden = [], {}, {}, set()
        for i, line in enumerate(entries):
            depth = (len(line) - len(line.lstrip())) // 2
            label = line.strip()
            new = label.startswith("+")
            label = label.lstrip("+ ")
            folder = label.endswith("/")
            label = label.rstrip("/")
            n = f"{self.art}.{name}.r{i}"
            mark = kit.icon_slot(f"{n}.mark", "arrows/chevron_bottom" if folder else "general/i_file", ink2,
                                 size=12 if folder else 14, slot=14)
            txt = kit.text(f"{n}.t", [(k, "")], lp=kit.hug(), wrap=False)
            next(c for c in txt.children if c.tag == "TextValueRun").attrs["text"] = label
            row = self._box(f"{name}Row{i}", [mark, txt], "row", 6, (8 + 12 * depth, 0, 8, 0), "centerLeft", "fill",
                            row_h, cornerRadiusTL=4,
                            paints=[kit.solid(f"{n}.fill", _color("#efeff1") if label == selected else kit.CLEAR)])
            slot = kit.box(f"{n}.slot", [row.wrap], h=0 if new else row_h, clip=True, flexDirectionValue="column",
                           layoutWidthScaleType="fill", layoutHeightScaleType="fixed")
            if new:
                row.wrap.attrs["opacity"] = 0
                hidden.add(label)
            rows.append(slot)
            slots[label], items[label] = slot.name, row
        tree = self._box(name, rows, "column", 0, (4, 4, 4, 4), "topLeft", w, "hug")
        tree.kind = "tree"
        tree.rows, tree.slots, tree.hidden, tree.row_h = items, slots, hidden, row_h
        return tree

    def code_panel(self, name, code, files, file="App.tsx", tree_w=146, w="fill", h="fill", search="Search",
                   selected=None, **editor):
        """The Vibe Code tab: the file tree at the left (a search over it, a line at its right), the open file's tab
        over the editor (p.code_editor(code, **editor); `file` its name). files: p.file_tree entries.
        Targets: panel.tree (tree.rows[...]), panel.editor, panel.search, panel.tab."""
        n = f"{self.art}.{name}"
        find = self.search(f"{name}Search", w=tree_w - 16, placeholder=search)
        tree = self.file_tree(f"{name}Tree", files, w=tree_w, selected=selected or file)
        left = self._box(f"{name}Left", [self._box(f"{name}Find", [find], "column", 0, (8, 8, 8, 4), "topLeft", "fill",
                                                   "hug"), tree], "column", 0, 0, "topLeft", tree_w, "fill",
                         paints=[kit.solid(f"{n}.leftFill", kit.WHITE)])
        self._edge(left, "right", "#e4e4e6")
        tab = self.text(f"{name}File", file, style="Content/Body", color="Typography/primary-text-color")
        head = self._box(f"{name}Head", [kit.icon_slot(f"{n}.fileIcon", "general/i_file",
                                                       kit.color("Typography/secondary-text-color"), size=14), tab],
                         "row", 6, (16, 0, 16, 0), "centerLeft", "fill", 40)
        self._edge(head, "bottom", "#e4e4e6")
        ed = self.code_editor(f"{name}Editor", code, **editor)
        right = self._box(f"{name}Right", [head, ed], "column", 0, 0, "topLeft", "fill", "fill")
        panel = self._box(name, [left, right], "row", 0, 0, "topLeft", w, h,
                          paints=[kit.solid(f"{n}.fill", kit.WHITE)])
        panel.tree, panel.editor, panel.search, panel.tab = tree, ed, find, tab
        return panel

    # ------------------------------------------------------------ Quick Edits (the visual edit's text panel)
    def quick_edits(self, name, content="", heading="H1", font="Inter", weight="Bold", color="#1E1E1E", opacity="100%",
                    size="48", size_unit="px", letter="0", letter_unit="%", line="120", line_unit="%", w=406, h="fill",
                    pending=False):
        """The Quick Edits panel (hero View tab, the storyboard's 04): a 48 px header (QUICK EDITS, pop out, close),
        the Text section (Content: a p.text_area holding `content`), a line, Typography (Headline type, Font, Weight:
        dropdowns; Color: a swatch, its hex and opacity; Font size, Letter, Line: a value and its unit), and the
        footer ("Pending changes", Discard, Apply). pending=False: "Pending changes" shows only when a.show(qe.pending).
        Targets: qe.close, qe.popout, qe.content (the text area: a.type_into(qe.content, "...", replace=True)),
        qe.heading, qe.font, qe.weight, qe.color, qe.size, qe.size_unit, qe.letter, qe.letter_unit, qe.line,
        qe.line_unit, qe.discard, qe.apply, qe.pending."""
        n = f"{self.art}.{name}"
        ink2 = "Typography/secondary-text-color"
        title = self.text(f"{name}Title", "QUICK EDITS", style="Headlines/He 4", color=ink2)
        pop = self.icon_button(f"{name}Pop", icon="i_pop_out", variant=0, size=0, color=4)
        close = self.icon_button(f"{name}Close", icon="i_x", variant=0, size=0, color=4)
        head = self._box(f"{name}Head", [title, kit.box(f"{n}.headGap", h=1, layoutWidthScaleType="fill",
                                                        layoutHeightScaleType="fixed"), pop, close],
                         "row", 8, (24, 12, 16, 12), "centerLeft", "fill", 48)
        self._edge(head, "bottom", "#e4e4e6")

        def section(key, label):
            return self._box(f"{name}{key}", [
                self.text(f"{name}{key}T", label, style="Headlines/He 3"),
                kit.box(f"{n}.{key}Gap", h=1, layoutWidthScaleType="fill", layoutHeightScaleType="fixed"),
                kit.icon_slot(f"{n}.{key}Chev", "arrows/chevron_bottom", kit.color(ink2))],
                "row", 8, 0, "centerLeft", "fill", "hug")
        area = self.text_area(f"{name}Content", w=358, h=126, label="Content", value=content, placeholder="")
        rule = kit.box(f"{n}.rule", paints=[kit.solid(f"{n}.rule.fill", _color("#e4e4e6"))], h=1,
                       layoutWidthScaleType="fill", layoutHeightScaleType="fixed")

        def prop_row(key, label, controls):
            lab = self.text(f"{name}{key}L", label, style="Content/Body")
            cell = self._box(f"{name}{key}Lb", [lab], "row", 0, 0, "centerLeft", 134, 35)
            return self._box(f"{name}{key}Row", [cell] + controls, "row", 8, 0, "centerLeft", "fill", "hug")

        def dd(key, value, wd=200):
            return self.dropdown(f"{name}{key}", w=wd, showLabel=False, value=value)

        def pair(key, value, unit):
            return [self.input(f"{name}{key}", w=108, showLabel=False, value=value), dd(f"{key}Unit", unit, 84)]
        heading_d, font_d, weight_d = dd("Heading", heading), dd("Font", font), dd("Weight", weight)
        swatch = kit.box(f"{n}.swatch", paints=[kit.solid(f"{n}.swatch.fill", _color(color))], w=18, h=18,
                         cornerRadiusTL=3, layoutWidthScaleType="fixed", layoutHeightScaleType="fixed")
        hexv = self.text(f"{name}Hex", color.lstrip("#").upper(), style="Content/Body 14")
        op = self.text(f"{name}Opacity", opacity, style="Content/Body 14", color=ink2)
        col = self._box(f"{name}Color", [swatch, hexv, kit.box(f"{n}.colGap", h=1, layoutWidthScaleType="fill",
                                                               layoutHeightScaleType="fixed"), op],
                        "row", 8, (9, 0, 12, 0), "centerLeft", 200, 35, cornerRadiusTL=6,
                        paints=[kit.solid(f"{n}.colFill", kit.WHITE)])
        col.wrap.children.insert(0, kit.absolute(f"{n}.colEdge", paints=[kit.line(
            f"{n}.colEdge.stroke", kit.color("Borders/border-color"), 1)], inset=(0.5,) * 4, cornerRadiusTL=5.5))
        size_p, letter_p, line_p = pair("Size", size, size_unit), pair("Letter", letter, letter_unit), \
            pair("Line", line, line_unit)
        rows = [prop_row("HeadingP", "Headline type", [heading_d]), prop_row("FontP", "Font", [font_d]),
                prop_row("WeightP", "Weight", [weight_d]), prop_row("ColorP", "Color", [col]),
                prop_row("SizeP", "Font size", size_p), prop_row("LetterP", "Letter", letter_p),
                prop_row("LineP", "Line", line_p)]
        body = self._box(f"{name}Body", [section("Text", "Text"), area, rule, section("Typo", "Typography"),
                                         self._box(f"{name}Props", rows, "column", 16, 0, "topLeft", "fill", "hug")],
                         "column", 16, (24, 20, 24, 20), "topLeft", "fill", "fill", clip=True)
        dot = kit.box(f"{n}.dot", paints=[kit.solid(f"{n}.dot.fill", kit.color("Indications/pending-color"))], w=6,
                      h=6, cornerRadiusTL=3, layoutWidthScaleType="fixed", layoutHeightScaleType="fixed")
        pend = self._box(f"{name}Pending", [dot, self.text(f"{name}PendingT", "Pending changes",
                                                           style="Content/Body", color=ink2)],
                         "row", 6, 0, "centerLeft", "hug", "hug", opacity=None if pending else 0)
        discard = self.button(f"{name}Discard", label="Discard", variant=1, color=0)
        apply = self.button(f"{name}Apply", label="Apply", variant=0, color=0)
        foot = self._box(f"{name}Foot", [pend, kit.box(f"{n}.footGap", h=1, layoutWidthScaleType="fill",
                                                       layoutHeightScaleType="fixed"), discard, apply],
                         "row", 8, (24, 0, 24, 0), "centerLeft", "fill", 65)
        self._edge(foot, "top", "#e4e4e6")
        qe = self._box(name, [head, body, foot], "column", 0, 0, "topLeft", w, h,
                       paints=[kit.solid(f"{n}.fill", kit.WHITE)])
        self._edge(qe, "left", "#ededee")
        qe.close, qe.popout, qe.content, qe.pending = close, pop, area, pend
        qe.heading, qe.font, qe.weight, qe.color = heading_d, font_d, weight_d, col
        (qe.size, qe.size_unit), (qe.letter, qe.letter_unit), (qe.line, qe.line_unit) = size_p, letter_p, line_p
        qe.discard, qe.apply = discard, apply
        return qe

    # ------------------------------------------------------------ the AI's generation status
    def gen_status(self, name, label="Generating...", done="Done", style="Content/Body 14",
                   color="Typography/secondary-text-color"):
        """The AI star and "Generating..." (the hero Code tab's status): a.generating(st) runs the product's shimmer
        over the text (every 1.6 s), a.done(st) turns it to "Done" (the text crossfades, the box closes to the new
        width: placed against a right edge, the star slides toward it)."""
        n = f"{self.art}.{name}"
        k = f"{self.key}_{name}"
        kit.text_style(k, style, _color(color))
        band = El("TextModifierRange", {"modifyFrom": -0.36, "modifyTo": 0.36, "falloffFrom": 0, "falloffTo": 0,
                                        "offset": -2, "clamp": False}, name=f"{n}.band")
        shimmer = El("TextModifierGroup", {"modifyOpacity": True, "invertOpacity": True, "opacity": 0.37}, [band],
                     name=f"{n}.shimmer")
        gen = self._box(f"{name}Gen", [kit.text(f"{n}.genT", [(k, label)], lp=kit.hug(), wrap=False,
                                                modifiers=[shimmer])], "row", 0, 0, "centerLeft", "hug", "hug")
        fin = self._box(f"{name}Done", [kit.text(f"{n}.doneT", [(k, done)], lp=kit.hug(), wrap=False)], "row", 0, 0,
                        "centerLeft", "hug", "hug", opacity=0)
        texts = kit.box(f"{n}.texts", [fin.wrap, gen.wrap], layoutTypeValue="stack", layoutAlignmentType="centerRight",
                        flexDirectionValue="row", **kit.hug())
        st = self._box(name, [self._art(f"{name}.star", "ai_star.svg", 16), texts], "row", 6, 0, "centerLeft",
                       "hug", "hug")
        st.kind = "genstatus"
        st.gen, st.done_t, st.texts, st.band = gen, fin, texts, band.name
        return st

    # ------------------------------------------------------------ the AI's answer in the chat
    def chat_reply(self, name, paragraphs, actions=("i_duplicate", "i_options"), status="Thinking...", gap=24,
                   style="Content/Body 14", color="Typography/primary-text-color", thought=None, buttons=False):
        """The AI's answer as the copilot brings it (v08: Mateus's motion, hero-view v10; in
        p.ai_panel(chat=[ask, reply])). The status stays right under the message: a.think(reply) brings it in (the star
        turns in, "Thinking..." wipes in and shimmers); a.reply(reply) swaps it where it is for "Thought for Xs" (no
        star, a chevron) while the paragraphs open their rooms below it one by one; then the answer's action icons.
        (The product pushes "Thinking..." down under the answer: the hero keeps it in place, Mateus's licence.)
        A paragraph takes no room until it comes. gap: above each paragraph and above the icons (the panel's `gap`).
        thought: the done text (default "Thought for Xs", X the seconds from a.think to a.reply).
        Targets: reply.status (an AiProcessIndication), reply.actions (the icons), reply.paragraphs, reply.bar.
        v13c: the icons are drawn on their own (p.icon), as nothing clicks them; buttons=True makes them Icon buttons
        (for a cursor that hovers or clicks one; the component weighs ~0.17 MB)."""
        n = f"{self.art}.{name}"
        st = self.ai_status(f"{name}Status", label=status, shown=False, **({"thought": thought} if thought else {}))
        paras, slots, lhs = [], [], []
        for i, string in enumerate(paragraphs):
            para = self.chat_ai(f"{name}P{i}", string, style=style, color=color)
            inner = kit.box(f"{n}.roomIn{i}", [para.wrap], paddingTop=gap, flexDirectionValue="column",
                            layoutAlignmentType="topLeft", layoutWidthScaleType="fill", layoutHeightScaleType="hug")
            slots.append(kit.box(f"{n}.room{i}", [inner], h=0, clip=True, flexDirectionValue="column",   # no padding:
                                 layoutAlignmentType="topLeft", layoutWidthScaleType="fill",   # it would hold room
                                 layoutHeightScaleType="fixed"))
            paras.append(para)
            lhs.append(kit.STYLES[f"{self.key}_{name}P{i}"]["lh"])
        acts = [self.icon_button(f"{name}Act{i}", icon=ic, variant=0, size=0, color=1) if buttons else
                self.icon(f"{name}Act{i}", ic) for i, ic in enumerate(actions)]
        bar = self._box(f"{name}Acts", acts, "row", 6, (0, gap, 0, 0), "centerLeft", "hug", "hug", opacity=0)
        reply = self._box(name, [st] + slots + [bar], "column", 0, 0, "topLeft", "fill", "hug")
        reply.kind = "reply"
        reply.status, reply.actions, reply.paragraphs, reply.bar = st, acts, paras, bar
        reply.rooms, reply.gap, reply.lhs = [s.name for s in slots], gap, lhs
        reply.thought, reply.think_t = thought, None
        return reply

    # ------------------------------------------------------------ v10: the Copilot's steps (Marketing Automation)
    def ai_steps(self, name, steps, working=None, gap=8, top=0):
        """The Copilot's steps (v10; the automation storyboard's "Copilot progress"): one AiStep a line, each taking no
        room until a.steps brings it in. gap: between the lines (8); top: above the first. Targets: .rows.
        v11: each line loads with the classic spinner and its text, dark (`working` is no longer used)."""
        from components.ai_step import ROW_H
        n = f"{self.art}.{name}"
        rows, rooms = [], []
        for i, string in enumerate(steps):
            row = self.ai_step(f"{name}S{i}", label=string)
            inner = kit.box(f"{n}.stepIn{i}", [row.wrap], paddingTop=gap if i else top, flexDirectionValue="column",
                            layoutAlignmentType="topLeft", layoutWidthScaleType="fill", layoutHeightScaleType="hug")
            rooms.append(kit.box(f"{n}.step{i}", [inner], h=0, clip=True, flexDirectionValue="column",
                                 layoutAlignmentType="topLeft", layoutWidthScaleType="fill",
                                 layoutHeightScaleType="fixed"))
            rows.append(row)
        st = self._box(name, rooms, "column", 0, 0, "topLeft", "fill", "hug")
        st.kind = "steps"
        st.rows, st.rooms = rows, [r.name for r in rooms]
        st.room_h = [ROW_H + (gap if i else top) for i in range(len(steps))]
        return st

    def chat_steps(self, name, summary, steps, done, status="Thinking...", thought=None, working=None, gap=20,
                   steps_top=14, style="Content/Body", lh=17.55, color="Typography/primary-text-color"):
        """The Copilot's answer while it builds (v10, the automation storyboard, frames 05-06; in a chat column as
        p.chat_reply: chat=[ask, reply]): "Show steps" and its chevron, the summary, then the steps one by one
        (a.steps: each comes in with its spinner turning and turns into its check, the next coming in below). a.reply
        then swaps the summary and the steps for `done` ("Done - ..."), in their place; "Show steps" stays.
        gap: above the summary / done paragraph (the panel's 20); steps_top: between the summary and the steps.
        v13 (approved 2026-11-13, LEARNINGS 6): while the steps load, the top is the status, "✦ Thinking..." (a.think,
        or a.steps' intro, brings it in with the message), even where the Figma frame shows "Show steps" (that frame is
        the folded end state); a.reply swaps it for "Thought for Xs" (`thought`: the text) as the summary and the
        steps make way for `done`.
        Targets: .status (.toggle: the same, for older code), .summary, .done, .steps (a p.ai_steps)."""
        n = f"{self.art}.{name}"
        toggle = self.ai_status(f"{name}Status", label=status, shown=False, **({"thought": thought} if thought else {}))
        paras, rooms = [], []
        for key, string in (("Done", done), ("Sum", summary)):    # done first: it takes the summary's place
            para = self.chat_ai(f"{name}{key}", string, style=style, color=color, lh=lh)
            inner = kit.box(f"{n}.room{key}In", [para.wrap], paddingTop=gap, flexDirectionValue="column",
                            layoutAlignmentType="topLeft", layoutWidthScaleType="fill", layoutHeightScaleType="hug")
            rooms.append(kit.box(f"{n}.room{key}", [inner], h=0, clip=True, flexDirectionValue="column",
                                 layoutAlignmentType="topLeft", layoutWidthScaleType="fill",
                                 layoutHeightScaleType="fixed"))
            paras.append(para)
        lst = self.ai_steps(f"{name}Steps", steps, working=working, top=steps_top)
        reply = self._box(name, [toggle] + rooms + [lst], "column", 0, 0, "topLeft", "fill", "hug")
        reply.kind = "chatsteps"
        reply.toggle, reply.done, reply.summary, reply.steps = toggle, paras[0], paras[1], lst
        reply.status, reply.thought, reply.think_t = toggle, thought, None
        reply.rooms, reply.paragraphs = [r.name for r in rooms], paras
        reply.lhs = [kit.STYLES[f"{self.key}_{name}{key}"]["lh"] for key in ("Done", "Sum")]
        reply.gap = gap
        return reply

    # ------------------------------------------------------------ v10: the automation map's lines
    def flow_link(self, name, h=36, add=True, color="#D4D4D8"):
        """A line down from one node to the next (2 px, `h` tall), with the "+" (add step) on its middle (add=False:
        none). At the nodes' size (the storyboard draws the map at 0.5: h 18 there is 36 here)."""
        n = f"{self.art}.{name}"
        kids = [_bar(f"{n}.line", 10, 0, 2, h, _color(color))]
        if add:
            kids.insert(0, self._plus(f"{name}Plus", (h - 22) / 2, color))
        return self._box(name, kids, "column", 0, 0, "topLeft", 22, h)

    def flow_split(self, name, span, stub=18, drop=76, labels=("NO", "YES"), add=True, color="#D4D4D8"):
        """An If/Else's branches: a stub down from the node, a bar `span` wide (between the two branches' centres),
        a drop of `drop` to each branch with its label (NO / YES) and a "+" (add=False: none). The box is span + 60
        wide; its centre is the node's (place it at the node's centre - (span + 60) / 2)."""
        n = f"{self.art}.{name}"
        w = span + 60
        col = _color(color)
        bars = [((w - 2) / 2, 0, 2, stub), (30, stub, span + 2, 2), (30, stub, 2, drop), (30 + span, stub, 2, drop)]
        kids = []
        for i, (x, y, bw, bh) in enumerate(bars):
            kids.append(_bar(f"{n}.bar{i}", x, y, bw, bh, col))
        k = f"{self.key}_{name}Tag"
        kit.text_style(k, None, _color("#5D6068"), size=16, lh=20, weight=550)
        for i, (lab, cx) in enumerate(zip(labels, (31, 31 + span))):
            tag = kit.box(f"{n}.tag{i}", [kit.text(f"{n}.tag{i}.t", [(k, lab)], lp=kit.hug(), wrap=False)],
                          paints=[kit.solid(f"{n}.tag{i}.fill", _color("#F7F7F8"))], cornerRadiusTL=6, paddingLeft=8,
                          paddingRight=8, paddingTop=2, paddingBottom=2, **kit.hug())
            kids.insert(0, kit.box(f"{n}.tagAt{i}", [tag], w=60, positionTypeValue="absolute", positionLeft=cx - 30,
                                   positionTop=stub + 12, layoutAlignmentType="topCenter", flexDirectionValue="column",
                                   layoutWidthScaleType="fixed", layoutHeightScaleType="hug"))
            if add:
                kids.insert(0, kit.absolute(f"{n}.plusAt{i}", [self._plus(f"{name}Plus{i}", 0, color).wrap],
                                            inset=(cx - 11, stub + 47, None, None)))
        return self._box(name, kids, "column", 0, 0, "topLeft", w, stub + drop)

    def _plus(self, name, y, color):
        """The map's "+" (add step): a 22 px circle, #F7F7F8 with a 1.6 px edge, a 14 px plus; at y in a 22 wide box."""
        n = f"{self.art}.{name}"
        ring = kit.absolute(f"{n}.ring", paints=[kit.line(f"{n}.ring.stroke", _color(color), 1.6)], inset=(0.8,) * 4,
                            cornerRadiusTL=10.2)
        # the storyboard's plus keeps Figma's 1.5 stroke at the map's 0.5: 3 at this size
        disc = kit.box(f"{n}.disc", [ring, kit.icon_slot(f"{n}.plus", "common_actions/i_plus", _color("#272B35"),
                                                         size=14, stroke_w=3 * 16 / 14)],
                       w=22, h=22, paints=[kit.solid(f"{n}.disc.fill", _color("#F7F7F8"))], cornerRadiusTL=11,
                       layoutAlignmentType="center", layoutWidthScaleType="fixed", layoutHeightScaleType="fixed")
        return self._box(name, [kit.absolute(f"{n}.at", [disc], inset=(0, y, None, None))], "column", 0, 0, "topLeft",
                         22, 22 + y)


def _bar(name, x, y, w, h, col):
    """A w x h block of colour at (x, y) in its parent (absolute)."""
    return kit.box(name, [], w=w, h=h, paints=[kit.solid(f"{name}.fill", col)], positionTypeValue="absolute",
                   positionLeft=x, positionTop=y, layoutWidthScaleType="fixed", layoutHeightScaleType="fixed")


class _Rooms:
    """Rooms and their paragraphs, for _room_heights (a p.chat_steps measures one room at a time)."""

    def __init__(self, rooms, paragraphs, lhs):
        self.rooms, self.paragraphs, self.lhs = rooms, paragraphs, lhs


class ActionPatterns:
    """Actions for the patterns, and plain keys made easy (hide, show, text, stream, count, beats)."""

    @staticmethod
    def _list(items):
        return items if isinstance(items, (list, tuple)) else [items]

    def _hidden_at_start(self, n):
        op = self.c.track(n, "opacity")
        if len(op.keys) == 1:     # its first appearance: hidden until then
            op.keys[0]["v"] = 0.0

    # ------------------------------------------------------------ showing and hiding
    def hide(self, items, t=None, dur=SWAP):
        """Items fade out together (dur: the swap's 0.1 s; one state at a time: what replaces them comes after).
        Returns when they are gone (it doesn't move `now`)."""
        t, dur = self._t(t), secs(dur)
        for it in self._list(items):
            self.c.fade(t, _el(it).name, 0.0, dur)
        self._note(t + dur, f"hide {', '.join(_el(i).name for i in self._list(items))}")
        return t + dur

    def show(self, items, t=None, dur="fade"):
        """Items fade in where they are (hidden until then, when it is their first appearance). Returns the end."""
        t, dur = self._t(t), secs(dur)
        for it in self._list(items):
            n = _el(it).name
            self._hidden_at_start(n)
            self.c.fade(t, n, 1.0, dur)
        self._note(t + dur, f"show {', '.join(_el(i).name for i in self._list(items))}")
        return t + dur

    def feedback(self, item, t=None, hold=3.0):
        """A p.feedback (Push Feedback Message, v09) after an action: at t it drops 8 px into place as it fades in
        (0.5 s, settle), stays `hold` s (the DS: a few seconds) and leaves on its own, rising as it fades (0.25 s,
        duda). Returns when it is gone."""
        from components import feedback_message as fm
        t = self._t(t)
        self._key(t, item, "shown", True)
        out = t + fm.IN_S + secs(hold)
        self._key(out, item, "shown", False)
        self._note(t + fm.IN_S, f"feedback {item.key} in")
        self._note(out + fm.OUT_S, f"feedback {item.key} out")
        return out + fm.OUT_S

    # ------------------------------------------------------------ text
    def _runs(self, item):
        out = []
        kit.walk(_el(item), lambda e: out.append(e.name) if e.tag == "TextValueRun" and e.name else None)
        return out

    def _run(self, item):
        runs = self._runs(item)
        assert len(runs) == 1, f"{_el(item).name}: a.text / stream / count work on a p.text (one run of text)"
        return runs[0]

    def text(self, item, value, t=None, fade=False):
        """A p.text changes to `value` at t (a chat renamed, a label edited). fade=True: it fades out (0.1 s), changes,
        and fades back in. Returns when the new text shows."""
        t = self._t(t)
        run = self._run(item)
        if fade:
            n = _el(item).name
            self.c.fade(t, n, 0.0, SWAP)
            self.c.set(t + SWAP, run, "text", value)
            self.c.fade(t + SWAP + 1 / FPS, n, 1.0, kit.FADE)
            end = t + SWAP + 1 / FPS + kit.FADE
        else:
            self.c.set(t, run, "text", value)
            end = t
        self._note(end, f"text {_el(item).name} {value!r}")
        return end

    def stream(self, item, text=None, t=None, cps=80, seed=7):
        """The AI's reply arrives word by word (a p.text / p.chat_ai, empty until t): chunks of a word or a few
        marks, `cps` characters a second with a little jitter. text: what it writes (default: its own text).
        Returns when the last word is in."""
        t = self._t(t)
        run = self._run(item)
        el = self.c.by[run]
        if text is None:
            text = el.attrs.get("text", "")
        if (run, "text") not in self.c.tracks:
            el.attrs["text"] = ""     # empty from the first frame
        self.c.set(t, run, "text", "")
        rnd = random.Random(seed)
        cur, shown, last = t, "", None
        for tok in tokens(text):
            cur += max(1, len(tok.strip())) / cps * rnd.uniform(0.7, 1.3)
            shown += tok
            f = frame(cur)
            if f == last:     # several chunks in one frame: the last one wins
                self.c.track(run, "text").keys[-1]["v"] = shown
            else:
                self.c.set(f / FPS, run, "text", shown)
            last = f
        self._note(last / FPS, f"stream {_el(item).name} ({len(text)} chars)")
        return last / FPS

    def count(self, item, to, t=None, dur=None, ease=None, fmt="{:,}", blur=None, color=PURPLE, start=None):
        """A number counts up to `to` (a p.text): the eased value frame by frame (v11, the example's: 2 s on
        (0, 0, 0, 1), fast then ending slowly, so the count shows; 1.5-3 s fit), coming in #AE68FA and turning to its
        own colour while it sharpens from a Feather of 4 (40 frames, linear). color=None: its own colour all along;
        blur=0: sharp. fmt: how it is written ("{:,}" 1,234; "{}%"; "{:.1f}%" 2.6%: a decimal `to` counts in tenths).
        It starts close to `to` (Mateus's rule, 2026-11-13: a long count, 0 to 3,023, looks linear however soft its
        end): `to` minus 10-35 steps (ones, or tenths for a decimal `to`), random but the same in every build (seeded
        by the item and `to`), never below 0. start=0: from zero; start=<n>: from n."""
        d = DETAILS["count"]
        t, dur = self._t(t), secs(d["dur"] if dur is None else dur)
        run = self._run(item)
        curve = choreo.ease_curve(d["ease"] if ease is None else ease)
        if start is None:
            step = 1 if float(to).is_integer() else 0.1
            gap = random.Random(f"{_el(item).name}:{to}").randint(*d["spread"])
            start = max(0, round(to - gap * step, 1))
        n, prev = max(1, round(dur * FPS)), None
        for f in range(n + 1):
            x = start + (to - start) * choreo.progress(curve, f / n)
            v = fmt.format(round(x) if float(to).is_integer() else x)
            if v != prev:
                self.c.set(t + f / FPS, run, "text", v)
                prev = v
        blur = d["feather"] if blur is None else blur
        busy = lambda nm, prop: len(self.c.track(nm, prop).keys) > 1   # noqa: E731  (a.generate's pops run it)
        if blur:
            for fe in self._feathers(item):
                if busy(fe, "strength"):
                    continue
                self.c.set(t, fe, "strength", blur)
                self.c.move(t + 1 / FPS, fe, "strength", 0.0, d["dur_color"], "linear")
        if color:
            for col in self._colors(item):
                if busy(col, "colorValue"):
                    continue
                own = self.c.track(col, "colorValue").keys[0]["v"]
                self.c.set(t, col, "colorValue", _argb(color))
                self.c.move(t + 1 / FPS, col, "colorValue", own, d["dur_color"], "linear")
        self._note(t + dur, f"count {_el(item).name} to {to}")
        return t + dur

    def _feathers(self, item, shapes=False):
        """A Feather in each text fill of `item` (added once, at 0: sharp), for the light blur of a pop or a count.
        shapes: its icons' and drawings' paints too (v13c: a loose element, a detail)."""
        out = []

        def add(e):
            if e.tag == "Fill" and e.name and e.name.endswith(".fill") and any(
                    c.tag == "SolidColor" for c in e.children if isinstance(c, El)) and \
                    self.c.parent.get(id(e)) is not None and self.c.parent[id(e)].tag == "TextStylePaint":
                fe = next((c for c in e.children if isinstance(c, El) and c.tag == "Feather"), None)
                if fe is None:
                    fe = El("Feather", {"strength": 0.0}, name=f"{e.name[:-5]}.blur")
                    e.children.append(fe)
                    self.c.by[fe.name] = fe
                    self.c.parent[id(fe)] = e
                out.append(fe.name)
        kit.walk(_el(item), add)
        return out + (self._shape_feathers(item) if shapes else [])

    def _shape_feathers(self, item):
        """v13c (lumi-dental-winback NOTES 6): a Feather in each paint of `item`'s vector shapes (icons, a logo: a
        Shape's fills and strokes; not a text's, a box's background or an effect's), added once, sharp. A feathered
        fill draws only under the clockwise rule, so each such shape's contours are turned to wind the way that rule
        fills what its own rule filled (an outline clockwise, a hole inside it the other way): a path drawn
        anticlockwise would vanish (the lumi-dental logo's tooth). A Feather blurs in its shape's own units: under a
        scaled drawing (a 400 px SVG drawn 24 px) the strength a caller keys is scaled back by _fe_k, so the blur
        reads the same on screen as a text's."""
        out = []
        k = self.__dict__.setdefault("_fe_k", {})

        def add(shape, scale):
            if shape.tag != "Shape":
                return
            paints = [c for c in shape.children if isinstance(c, El) and c.tag in ("Fill", "Stroke")]
            if not paints:
                return
            fills = [p_ for p_ in paints if p_.tag == "Fill"]
            if fills and any(p_.attrs.get("fillRule") != "clockwise" for p_ in fills):
                _wind_clockwise(shape, "evenOdd" if fills[0].attrs.get("fillRule") == "evenOdd" else "nonZero")
                for p_ in fills:
                    p_.attrs["fillRule"] = "clockwise"
            for i, p_ in enumerate(paints):
                fe = next((c for c in p_.children if isinstance(c, El) and c.tag == "Feather"), None)
                if fe is None:
                    fe = El("Feather", {"strength": 0.0}, name=f"{p_.name or f'{shape.name}.paint{i}'}.blur")
                    p_.children.append(fe)
                    self.c.by[fe.name] = fe
                    self.c.parent[id(fe)] = p_
                if abs(scale - 1) > 1e-6:
                    k[fe.name] = 1 / scale
                out.append(fe.name)

        def walk(e, scale):
            if e.tag in ("Node", "Shape"):
                scale *= math.sqrt(abs(float(e.attrs.get("scaleX") or 1) * float(e.attrs.get("scaleY") or 1))) or 1
            add(e, scale)
            for c in e.children:
                if isinstance(c, El):
                    walk(c, scale)
        walk(_el(item), 1.0)
        return out

    def _fe(self, name, v):
        """A feather strength in screen points, for this Feather (see _shape_feathers)."""
        return v * self.__dict__.get("_fe_k", {}).get(name, 1.0)

    def _radius(self, item):
        """v13c: the corner radius of what `item` shows (LEARNINGS 7's block takes it + 5): the first round corner
        found from the item inwards while it is one surface (a box holding one thing besides its pinned shadows and
        edges, the image's clip, a drawing's bottom rectangle, a component's own artboard); 0 for a square corner."""
        comps = {getattr(c, "ref", None): c for c in self.p.comps}
        e = _el(item)
        for _ in range(12):
            part = {"LayoutComponent": "LayoutComponentStyle", "Shape": "Rectangle"}.get(e.tag)
            src = next((c for c in e.children if isinstance(c, El) and c.tag == part), None) if part else None
            r = (src.attrs.get("cornerRadiusTL") if src is not None else None) or 0
            if r:
                return float(r)
            if e.tag == "NestedArtboardLayout":       # a component: its own artboard
                e = comps.get(str(e.attrs.get("artboardId", ""))[1:])
                if e is None:
                    return 0.0
                continue
            kids = [c for c in e.children if isinstance(c, El) and c.tag in (
                "LayoutComponent", "NestedArtboardLayout", "Node", "Shape", "Image", "Text") and not _off(c)]
            kids = [c for c in kids if not _pinned(c)] or kids     # its shadows and edges aside
            if len(kids) == 1:
                e = kids[0]
            elif e.tag == "Node" and kids and kids[0].tag == "Shape":
                e = kids[0]                            # a drawing (p.wrap): its bottom shape
            else:
                return 0.0
        return 0.0

    def _colors(self, item):
        out = []
        kit.walk(_el(item), lambda e: out.append(e.name) if e.tag == "SolidColor" and e.name and
                 self.c.parent.get(id(e)) is not None and self.c.parent[id(e)].tag == "Fill" and
                 self.c.parent.get(id(self.c.parent[id(e)])) is not None and
                 self.c.parent[id(self.c.parent[id(e)])].tag == "TextStylePaint" else None)
        return out

    # ------------------------------------------------------------ the AI's answer in the chat
    def _scale_of(self, name):
        """The scale an element is drawn at in the artboard (its own and its parents': a p.vibe_workspace at 0.81)."""
        s, el = 1.0, self.c.by[name]
        while el is not None:
            s *= float(el.attrs.get("scaleY") or 1.0)
            el = self.c.parent.get(id(el))
        return s

    def _room_heights(self, reply, t):
        """Each paragraph's own height (its room is closed: the measure lays the rooms out open, once): its lines times
        its style's line height. The measure gives artboard points (a scaled parent shrinks them) and the glyphs (~2 px
        short a line): v07's rooms opened short (a 4-line paragraph in the hero's 0.81: 57 px for 72)."""
        styles = [next(c for c in self.c.by[r].children if c.tag == "LayoutComponentStyle") for r in reply.rooms]
        saved = [st.attrs.get("layoutHeightScaleType") for st in styles]
        for st in styles:
            st.attrs["layoutHeightScaleType"] = "hug"
        self.p._measured.clear()
        try:
            out = []
            for para, lh in zip(reply.paragraphs, reply.lhs):
                h = self.p.bounds(para, t)[3] / self._scale_of(para.wrap.name)
                out.append(max(1, round(h / lh)) * lh)
            return out
        finally:
            for st, v in zip(styles, saved):
                st.attrs["layoutHeightScaleType"] = v
            self.p._measured.clear()

    def think(self, reply, t=None):
        """The message is sent (at t): the status comes in right under it, the star turning in 5 frames later and
        "Thinking..." wiping in 15 frames later, then shimmering. Returns t. An AiPanel: sent without the click on send
        (stage 1)."""
        t = self._t(t)
        if reply.kind == "aipanel":
            if getattr(reply, "sent_t", None) is not None:   # v14: already sent (a.send, or the cursor on send)
                return reply.sent_t
            self._key(t, reply, "stage", 1)
            self._note(t, f"sent {reply.key}")
            return t
        self._key(t, reply.status, "shown", True)
        reply.think_t = t
        self._note(t, f"think {reply.key}")
        if getattr(reply, "field", None) is not None:     # v14b: the Copilot works: its field shows the stop
            self._field(reply.field, t, "working")
        return t

    def _field(self, field, t, look):
        """v14b: a p.copilot_field takes `look` at t (nothing when it already has it):
          focus    the edge turns active (0.1 s) and the placeholder goes (a hold key): the typing starts
          typing   the button turns orange, the arrow on it (hold keys): the first letter is in
          working  the button turns into the orange stop (hold keys; from frame 0 when t is 0) and the edge is
                   active: the message is sent, the Copilot works
          rest     the stop fades out (0.1 s), then the grey send fades in (0.1 s), and the edge rests (0.1 s): the
                   answer comes (the approved ask-your-agent's 280-286 / 286-292)
        The placeholder never comes back once the typing took it (LEARNINGS 5)."""
        f0 = frame(t)
        before = [lk for fr, lk in field.looks if fr <= f0]
        now = before[-1] if before else "empty"
        if now == look or (look == "focus" and now in ("typing", "working")):
            return
        n, d = _el(field).name, FIELD["swap"]
        at = f0 / FPS

        def key(part, v, fade=False, t_=at):
            name, tr = f"{n}.{part}", self.c.track(f"{n}.{part}", "opacity")
            fr = frame(t_)
            prev, nxt = [k for k in tr.keys if k["f"] <= fr], [k for k in tr.keys if k["f"] > fr]
            rests = nxt[0]["v"] if prev and nxt and prev[-1]["ease"] != "hold" else tr.value_at(fr)
            if abs(rests - v) < 1e-6:      # already there (or a fade running there)
                return
            if fade and frame(t_) > 0:
                self.c.fade(t_, name, v, d)
            else:
                self.c.set(t_, name, "opacity", v)
        if look in ("focus", "typing", "working"):
            key("edgeOn", 1.0, fade=True)
        if look == "focus":
            self.c.set(at, _el(field.placeholder).name, "opacity", 0.0)
        elif look == "typing":
            key("orange", 1.0)
            key("grey", 0.0)
        elif look == "working":
            for part, v in (("orange", 1.0), ("grey", 0.0), ("arrow", 0.0), ("square", 1.0)):
                key(part, v)
        elif look == "rest":
            key("edgeOn", 0.0, fade=True)
            key("orange", 0.0, fade=True)
            key("square", 0.0, fade=True)
            key("grey", 1.0, fade=True, t_=at + d)
            key("arrow", 1.0, fade=True, t_=at + d)
        field.looks.append((f0, look))
        field.looks.sort(key=lambda x: x[0])
        self._note(at, f"field {field.key}: {look}")

    def reply(self, reply, t=None, step=0.27, then=0.083, stream=False, cps=REPLY_CPS, thought=None, typewriter=True,
              max_s=REPLY_MAX_S):
        """The answer of a p.chat_reply starts at t. 9 frames before, the status swaps where it is: the star fades and
        "Thinking..." wipes out, "Thought for Xs" wipes in (10 frames later; X: the seconds since a.think, or
        `thought`, the whole text), then its chevron. From t each paragraph's room opens below (0.25 s, duda) and
        the paragraph types in (v14, LEARNINGS 6: a plain typewriter, each letter whole, no front, no feather, no
        colour pass): `cps` letters a second (120), the whole answer never longer than `max_s` (1 s: a long answer
        types faster), each paragraph's room opening 0.25 s before its first letter. `then` s after the last
        letter, the action icons fade in below (0.15 s). Returns when they show.
        typewriter=False: v13's paragraphs, whole, rising 4 px, `step` s apart; stream=True: word by word (cps).
        An AiPanel (p.ai_panel): its paragraphs (reply, reply2, reply3) the same way, by its stage and its
        reveal1..3. A p.chat_steps: the summary and the steps make way for the done paragraph, typed."""
        t = self._t(t)
        thought = thought or getattr(reply, "thought", None)
        if reply.kind == "aipanel":
            return self._panel_reply(reply, t, secs(step), secs(then), thought, typewriter and not stream, cps, max_s)
        if reply.kind == "chatsteps":
            return self._steps_done(reply, t, typewriter and not stream, cps, max_s)
        if thought or reply.think_t is not None:
            self._key(reply.think_t or 0.0, reply.status, "thought",
                      thought or f"Thought for {max(1, round(t - reply.think_t))}s")
        self._key(max(0.0, t - 9 / FPS), reply.status, "done", True)
        if getattr(reply, "field", None) is not None:     # v14b: with the status, the stop turns back into send
            self._field(reply.field, max(0.0, t - 9 / FPS), "rest")
        tt, last = t, t
        heights = self._room_heights(reply, t)
        if typewriter and not stream:
            lens = self._type_lengths([self._chars(p_) for p_ in reply.paragraphs], cps, max_s)
            tt = t + 0.25
            for para, room, h, d in zip(reply.paragraphs, reply.rooms, heights, lens):
                self.c.move(tt - 0.25, room, "height", float(h + reply.gap), 0.25, "duda")
                tt = self.typewrite(para, tt, dur=d)
            last = tt
        else:
            for i, (para, room) in enumerate(zip(reply.paragraphs, reply.rooms)):
                h = heights[i] + reply.gap
                self.c.move(tt, room, "height", float(h), 0.25, "duda")
                if stream:
                    last = self.stream(para, t=tt + 0.25, cps=cps)
                    tt = last + 0.1
                else:
                    self.enter(para, tt + 0.25, dy=4, dur=0.5)
                    last = tt + 0.25 + 0.5
                    tt += step
        t1 = last + secs(then)
        self.show(reply.bar, t1, 0.15)
        self._note(t1 + 0.15, f"reply {reply.key}: {len(reply.paragraphs)} paragraph(s)")
        return t1 + 0.15

    @staticmethod
    def _type_lengths(counts, cps=REPLY_CPS, max_s=REPLY_MAX_S):
        """v14: how long each paragraph types (s, whole frames): `cps` letters a second, faster when the whole answer
        would take longer than `max_s`."""
        rate = max(cps, sum(counts) / max_s) if max_s else cps
        return [max(1, round(n / rate * FPS)) / FPS for n in counts]

    def typewrite(self, item, t=None, cps=REPLY_CPS, dur=None, ease="linear", soft=0):
        """v14 (LEARNINGS 5, 6 and 19.2): a p.text (a p.chat_ai, a prompt in a field of your own, a caption) types in
        from t, letter by letter, with ONE key: its reveal (a text modifier's offset, a fraction of the text) goes
        from nothing to all, so each letter shows whole as the offset passes it, never half-drawn. `cps` letters a
        second (120, the answer's pace) or over `dur` s; ease: the key's curve ("linear"; a prompt typed in a field:
        dur=PROMPT_TYPE["dur"] / 60, ease=PROMPT_TYPE["ease"], from PROMPT_TYPE["lead"] frames after the click).
        soft=6: a soft front that many letters wide (the generated copy's) instead of whole letters. Hidden from
        frame 0 until t. Returns when the last letter is in.
        v14b: a p.copilot_field's prompt (field.prompt): as the typing starts the placeholder goes and the edge turns
        active; on the first letter the send button turns orange."""
        t = self._t(t)
        n = max(1, self._chars(item))
        d = max(1, round((secs(dur) if dur is not None else n / cps) * FPS)) / FPS
        rn, _ = self._reveal(item, soft)
        self.c.move(t, rn, "offset", 1.0, d, ease)
        self._claimed().add(_el(item).name)
        field = getattr(item, "field", None)
        if field is not None:
            self._field(field, t, "focus")
            tr = self.c.track(rn, "offset")
            first = next(f for f in range(frame(t), frame(t + d) + 1) if tr.value_at(f) >= 0.5 / n)
            self._field(field, first / FPS, "typing")
        self._note(t + d, f"typewrite {_el(item).name} ({n} letters)")
        return t + d

    def send(self, item, t=None, message=None):
        """v14 (LEARNINGS 5, "Sending"): the send, pressed on its own (no cursor: the cursor clicked the field and
        left). An AiPanel: its send button presses, the typed prompt rises 10.3 px in 45 frames on (0.8, 0, 0.2, 1)
        and fades out between +16 and +26 frames, and 23 frames after the press the message comes in (5 frames,
        20 px in 30) with "Thinking..." (stage 1): as when the cursor presses its send (a.click(panel.part("send"))).
        A field of your own (p.copilot_panel): `item` is the typed text, flying out the same way, and `message`
        (the bubble, or the row holding it) comes in at +23 frames as a.sent brings it. Returns when the message
        comes (it doesn't move `now`): a.think / a.steps / a.generate_screen start from there.
        v14b: a p.copilot_field (or its .prompt): its button presses (0.9, as the AiPanel's) and turns into the
        orange stop as the message comes."""
        from components import ai_panel as aip
        t = frame(self._t(t)) / FPS
        if getattr(item, "kind", None) == "aipanel":
            return self._panel_send(item, t)
        field = item if getattr(item, "kind", None) == "copilotfield" else getattr(item, "field", None)
        if field is not None:
            assert field.prompt is not None, f"{field.key}: give p.copilot_field a prompt= to type and send"
            item = field.prompt
            b = _el(field.button).name
            for ax in ("scaleX", "scaleY"):    # the AiPanel's press: down in 3 frames, back from 0.1 s to 0.4 s
                self.c.move(t, b, ax, aip.FLY["press"], kit.PRESS, "duda_strong")
                self.c.move(t + 0.1, b, ax, 1.0, 0.3, "duda")
        fl = aip.FLY
        n = _el(item).name
        y0 = self.c.base(n, "y")
        self.c.move(t, n, "y", y0 - fl["rise"], fl["dur"] / FPS, list(fl["ease"]))
        self.c.move(t + fl["fade"][0] / FPS, n, "opacity", 0.0, (fl["fade"][1] - fl["fade"][0]) / FPS, "linear")
        tm = t + fl["message"] / FPS
        if message is not None:
            self.sent(message, tm)
        if field is not None:
            self._field(field, tm, "working")
        self._note(tm, f"send {n}")
        return tm

    def _panel_send(self, panel, t):
        """v14 (LEARNINGS 5): the send on an AiPanel (piece.py calls it when the cursor presses send; a.send without
        the cursor): stage 0.5 at t (the button presses, the typed prompt flies out of the field: its Send layer),
        stage 1 FLY["message"] (23) frames later (the message and "Thinking..."). Returns that time."""
        from components import ai_panel as aip
        t = frame(t) / FPS
        tm = t + aip.FLY["message"] / FPS
        self._key(t, panel, "stage", aip.SEND_STAGE)
        self._key(tm, panel, "stage", 1)
        panel.sent_t = tm
        self._note(tm, f"sent {panel.key}")
        return tm

    def steps(self, item, t=None, each=0.8, finish=True, intro=True, until=None):
        """Runs a p.ai_steps or a p.chat_steps from t (v10). chat_steps (intro=True): "Show steps" fades in and the
        summary's room opens (0.25 s, duda), the summary entering into it (rising 4 px, 0.5 s); then the steps. Each
        line comes in with its spinner turning (rising 4 px, 0.33 s), its room opening below the one before just ahead
        of it (0.25 s); `each` s later the spinner fades out (3 frames) and the check fades in (3 frames), and the next
        line comes in as the check lands (v11, Mateus 2026-11-13). finish=False: the last keeps loading. Returns when
        the last is done (or in).
        v13 (approved 2026-11-13, LEARNINGS 6 and 19.2): on a p.chat_steps, `t` is when the message is sent: the
        status ("✦ Thinking...") comes in then (if a.think hasn't brought it), the summary's room opens 18 frames
        later, the summary enters at 33 and the first step at 54. `each`: one length, or a list (one per step: the
        product's take 0.2-4 s). until=s: the steps follow the generation: their lengths spread unevenly (the last
        the longest, as the reference's 33 / 27 / 48 / 69 frames) so the last check lands at s (a.generate_screen's
        end): no spinner turns alone waiting for it."""
        from components.ai_step import SWAP_END
        t = self._t(t)
        lst = item
        if item.kind == "chatsteps":
            lst = item.steps
            if intro:
                if item.think_t is None:
                    self.think(item, t)
                si = STEPS_INTRO
                h = self._room_heights(_Rooms(item.rooms[1:], item.paragraphs[1:], item.lhs[1:]), t)[0]
                self.c.move(t + si["room"] / FPS, item.rooms[1], "height", float(h + item.gap), 0.25, "duda")
                self.enter(item.summary, t + si["summary"] / FPS, dy=4, dur=0.5)
                t += si["first"] / FPS - 0.25
        n = len(lst.rows)
        if until is not None:
            w = [STEP_WEIGHTS[i % len(STEP_WEIGHTS)] for i in range(n - 1)] + [STEP_LAST]
            room = until - (t + 0.25) - n * SWAP_END
            assert room > 0.2 * n, f"a.steps(until={until:.2f}): no room for {n} steps from {t + 0.25:.2f}"
            each = [room * x / sum(w) for x in w]
        each = [secs(e) for e in each] if isinstance(each, (list, tuple)) else [secs(each)] * n
        assert len(each) >= n, f"each: one length per step ({n})"
        end, t_in = t, t + 0.25
        for i, (row, room) in enumerate(zip(lst.rows, lst.rooms)):
            self.c.move(t_in - 0.25, room, "height", float(lst.room_h[i]), 0.25, "duda")
            self.enter(row, t_in, dy=4, dur=0.333)
            end = t_in + 0.333
            if finish or i < n - 1:
                td = frame(t_in + each[i]) / FPS
                self._key(td, row, "done", True)
                end = td + SWAP_END
                t_in = end
        self._note(end, f"steps {item.key}: {len(lst.rows)}")
        return end

    def _steps_done(self, reply, t, typewriter=True, cps=REPLY_CPS, max_s=REPLY_MAX_S):
        """a.reply on a p.chat_steps: at t the status swaps for "Thought for Xs" and the summary and the steps fade
        out (0.1 s), then their rooms close while the done paragraph's opens where the summary was (0.25 s, duda);
        21 frames after the swap the paragraph types in (v14, LEARNINGS 6: a plain typewriter, 120 letters a second,
        at most 1 s; typewriter=False: whole, rising 4 px). This is the approved ask-your-agent's timing (v12-v13:
        the swap and the fold at 280 frames, the answer at 301). Returns when the last letter is in."""
        t = self._t(t)
        if getattr(reply, "think_t", None) is not None:     # v13: "✦ Thinking..." -> "Thought for Xs" in place
            self._key(reply.think_t, reply.status, "thought",
                      reply.thought or f"Thought for {max(1, int(t - reply.think_t))}s")
            self._key(t, reply.status, "done", True)
        if getattr(reply, "field", None) is not None:     # v14b: with the status, the stop turns back into send
            self._field(reply.field, t, "rest")
        self.hide([reply.summary] + reply.steps.rows, t)
        t1 = t + SWAP
        for room in [reply.rooms[1]] + reply.steps.rooms:
            self.c.move(t1, room, "height", 0.0, 0.25, "duda")
        h = self._room_heights(_Rooms(reply.rooms[:1], reply.paragraphs[:1], reply.lhs[:1]), t1)[0]
        self.c.move(t1, reply.rooms[0], "height", float(h + reply.gap), 0.25, "duda")
        if typewriter:
            d = self._type_lengths([self._chars(reply.done)], cps, max_s)[0]
            end = self.typewrite(reply.done, t1 + 0.25, dur=d)
        else:
            self.enter(reply.done, t1 + 0.25, dy=4, dur=0.5)
            end = t1 + 0.75
        self._note(end, f"done {reply.key}")
        return end

    def _sent_at(self, panel, t):
        """When the AiPanel's message was sent: its stage last turned 1 before t (None: not on the timeline)."""
        name = f"drv.{panel.key}.stage"
        if name not in self.driver_of:
            return None
        keys = [k for k in self.c.tracks[(name, "propertyValue")].keys if k["f"] <= frame(t) and k["v"] == 1]
        return keys[-1]["f"] / FPS if keys else None

    def _panel_reply(self, panel, t, step, then, thought=None, typewriter=True, cps=REPLY_CPS, max_s=REPLY_MAX_S):
        """Stage 2 (the status swap) 9 frames before t, so the first paragraph comes in at t, as a p.chat_reply.
        "Thought for Xs": X the seconds since it was sent, unless the placement or `thought` gives the text.
        v14 (typewriter): the panel's `typewriter` is on and each paragraph types by its reveal1..3 (one key each,
        linear), as a.reply types a p.chat_reply's: its room opens 0.25 s before its first letter, the next
        paragraph's as the one before types; stage 5 (the action bar) `then` s after the last letter."""
        from components import ai_panel as aip
        paras = [p for p in aip.REPLIES if panel.value(p)]
        assert paras, f"{panel.key} has no reply (p.ai_panel(..., reply=...))"
        sent = self._sent_at(panel, t)
        if thought:
            self._key(sent or 0.0, panel, "thought", thought)
        elif sent is not None and "thought" not in panel.inst[2]:
            self._key(sent, panel, "thought", f"Thought for {max(1, round(t - sent))}s")
        t0 = max(0.0, t - aip.SWAP_LEAD)
        if typewriter:
            panel.inst[2]["typewriter"] = True
            lens = self._type_lengths([len(panel.value(p)) for p in paras], cps, max_s)
            ts = t0 + aip.SWAP_LEAD + aip.PARA_IN[0]
            for i, d in enumerate(lens):
                prop = f"reveal{aip.REPLIES.index(paras[i]) + 1}"
                panel.inst[2][prop] = 0.0
                self._key(ts - aip.SWAP_LEAD - aip.PARA_IN[0], panel, "stage", 2 + i)
                self.c.move(frame(ts) / FPS, self._driver(panel, prop), "propertyValue", 1.0, d, "linear")
                ts = frame(ts) / FPS + d
            t1 = ts + then
        else:
            for i, _ in enumerate(paras):
                self._key(t0 + step * i, panel, "stage", 2 + i)
            t1 = t0 + step * (len(paras) - 1) + aip.SWAP_LEAD + sum(aip.PARA_IN) + then
        self._key(t1, panel, "stage", 5)
        self._note(t1 + 0.15, f"reply {panel.key}: {len(paras)} paragraph(s)")
        return t1 + 0.15

    # ------------------------------------------------------------ the code editor and the tree
    def write_code(self, editor, t=None, speeds=((1, 240), (12, 100)), pauses=None, newline=2, caret_hold=0.3,
                   seed=7):
        """The AI writes the file into a p.code_editor (empty=True): chunk by chunk (a word or a few marks), each
        line's number showing as it starts, the caret riding the end of the line being written. speeds: (from line,
        characters a second), the hero's: 240, then 100 from line 12; newline: a new line costs that many characters;
        pauses: {line: s} holds after a line. Returns when the last line is done (editor.line_done[n]: when line n
        is, to place other beats on the code)."""
        t = self._t(t)
        rnd = random.Random(seed)
        sp = sorted(speeds)
        pauses = pauses or {}
        cur, caret, last = t, None, {}
        for n, line in enumerate(editor.lines, 1):
            cps = [c for f, c in sp if f <= n][-1]
            if n > 1:
                cur += newline / cps
            f = frame(cur)
            if n in editor.nums:
                self.c.set(f / FPS, editor.nums[n], "opacity", 1.0)
            if caret is not None:
                self.c.set(f / FPS, caret, "text", "")
            caret = editor.carets[n]
            self.c.set(f / FPS, caret, "text", CARET)
            full = "".join(x for x, _ in line)
            shown = 0
            for tok in tokens(full):
                cur += len(tok.strip()) / cps * rnd.uniform(0.7, 1.3)
                shown += len(tok)
                f = frame(cur)
                start = 0
                for run, (x, _) in zip(editor.runs[n], line):
                    v = x[:max(0, min(len(x), shown - start))]
                    start += len(x)
                    if last.get(run, "") != v:
                        self.c.set(f / FPS, run, "text", v)
                        last[run] = v
            editor.line_done[n] = frame(cur) / FPS
            cur += pauses.get(n, 0.0)
        end = frame(cur) / FPS
        self.c.set(end + caret_hold, caret, "text", "")
        self._note(end, f"write_code {editor.key}: {len(editor.lines)} lines")
        return end

    def add_file(self, tree, label, t=None):
        """A new file arrives in a p.file_tree ("+name" there): the rows below make room (0.33 s), the file slides in
        from the left (0.5 s, settle). Returns when it has landed."""
        t = self._t(t)
        assert label in tree.hidden, f"{label!r} is not a new file of {tree.key} (mark it \"+{label}\")"
        self.c.move(t, tree.slots[label], "height", float(tree.row_h), 0.333, "duda")
        row = tree.rows[label].wrap.name
        self.c.enter(t + 0.1, row, dx=-6.0, dy=0.0, dur=0.5, ease="settle")
        self._note(t + 0.6, f"add_file {label}")
        return t + 0.6

    # ------------------------------------------------------------ the AI's status
    def generating(self, status, t=None):
        """A p.gen_status (or AiProcessIndication-like text of your own) starts shimmering at t, until a.done(status)
        (or the end). Returns t."""
        t = self._t(t)
        self.statuses.append([status, t, None])
        self._note(t, f"generating {status.key}")
        return t

    def done(self, status, t=None):
        """The status turns to "Done": "Generating..." fades out (0.1 s), "Done" fades in, the box closes to its
        width (0.33 s, duda). Returns when it has settled."""
        t = self._t(t)
        run = next((s for s in self.statuses if s[0] is status and s[2] is None), None)
        if run:
            run[2] = t
        w_gen = self.p.bounds(status.gen, t)[2]
        w_done = self.p.bounds(status.done_t, t)[2]
        st = next(c for c in status.texts.children if c.tag == "LayoutComponentStyle")
        st.attrs["layoutWidthScaleType"] = "fixed"
        status.texts.attrs["width"] = w_gen
        self.c.track(status.texts.name, "width").keys[0]["v"] = float(w_gen)
        self.c.fade(t, status.gen.wrap.name, 0.0, 0.1)
        self.c.fade(t + 0.083, status.done_t.wrap.name, 1.0, 0.15)
        self.c.move(t + 0.1, status.texts.name, "width", float(w_done), 0.333, "duda")
        self._note(t + 0.433, f"done {status.key}")
        return t + 0.433

    def _close_statuses(self, end):
        """The shimmer passes of every a.generating(), up to its a.done() (or `end`)."""
        for status, t0, t1 in self.statuses:
            band = status.band
            t1 = end if t1 is None else t1
            t = t0
            while t < t1 - 2 / FPS:
                seg = min(SHIMMER_S, t1 - t)
                # it lands a frame before the next pass's set (a key on the same frame would replace it)
                self.c.set(t, band, "offset", -0.25)
                self.c.move(t + 1 / FPS, band, "offset", round(-0.25 + 1.5 * (seg - 1 / FPS) / SHIMMER_S, 4),
                            seg - 2 / FPS, "linear")
                t += seg

    # ------------------------------------------------------------ the Generation effect
    def _shown_x(self):
        """v14: where the piece's shown width sits between a small card (0: SIZE_REF[0], 432) and a hero (1:
        SIZE_REF[1], 1340): p.shown_at's width, else the artboard's."""
        w = float(getattr(self.p, "shown_w", None) or self.p.w)
        lo, hi = SIZE_REF
        return max(0.0, min(1.0, (w - lo) / (hi - lo)))

    def _size_k(self, kind):
        """v14 (LEARNINGS 7, "Feathers follow the size the piece is shown at"): the factor on a hero's feathers for
        `kind` ("square", "wash", "text"): FEATHER_AT[kind] on a small card, 1 on a hero, in between by the width."""
        return FEATHER_AT[kind] + (1 - FEATHER_AT[kind]) * self._shown_x()

    def _by_size(self, card, screen, ref=None):
        """A number that goes from its small card value to its screen value with the shown width (frames, gaps):
        the card's at ref[0] (432) and below, the screen's from ref[1] (SCREEN["size"]: 772, the welcome email)."""
        lo, hi = ref or SCREEN["size"]
        w = float(getattr(self.p, "shown_w", None) or self.p.w)
        return card + (screen - card) * max(0.0, min(1.0, (w - lo) / (hi - lo)))

    def generate(self, item, t=None, kind=None, squares=None, rows=None, pops=None, clip=None, radius=None, colors=None,
                 pop_color=PURPLE, ease=None, room=ROOM, feather=None, content=True, letters=True, ink=None):
        """The AI builds `item` (hero_1's Generation effect, as the hero pieces make it): a square over it, filled
        with the 7-stop gradient and feathered, grows to 100 % while the gradient sweeps through; when the square
        shows it (frame 36 small, 56 big) the item fades in under it (8 frames), and then what is inside it.
        v14 (Mateus, 2026-11-23; LEARNINGS 7) the content comes in on its own, without the piece's patches: every
        p.text, p.icon and p.image inside the item (the item itself when it is one), in reading order (top to
        bottom, left to right in a row), from 0.4 s after the square shows it (as it shows it on a 432 px card),
        ~6 frames apart (a little uneven):
          texts   letter by letter (a text modifier: opacity per letter, a soft front 6 letters wide), ~45 letters a
                  second, 0.4-0.9 s a text; a heading's second line when the first ends. The whole text in the
                  classic gradient's orange #F9A84A from the start, its pink #F4BBD2 over 10 frames after
                  max(0.35 s, 60 % of its entrance), held 8, then its own colour over 20, linear; Feather 4 -> 0 over
                  40 frames (by the size shown). letters=False: whole (opacity over 8 frames, Feather 6 -> 0 over 54:
                  short labels on interface blocks, a node on a map). A number (a text that is only a number: "3,412",
                  "+12%", "$40k") keeps v11's pop: #AE68FA over 8 frames, its own over 36, Feather 4 -> 0 (a.count
                  then counts it)
          icons   fade in over 20 frames with the texts' colour and feather
          photos  settle inside their frame: 112 % -> 100 % over 1.5 s on (0.16, 1, 0.3, 1), from 6 frames before
                  the square shows them; the frame doesn't move
        content=False: none of it (your own beats); content=[items]: those only. ink: the two colours of the texts'
        pass (default the classic orange and pink; a.generate_screen(gradient=) gives the design's).
          rows   items inside it come in one after the other (83 ms apart), rising 4 px
          pops   v11's texts in one colour (`pop_color`, #AE68FA) instead of letter by letter
        colors: the gradient's 5 colours when the designer drew their own in Figma (default the example's: #DDF1F9,
        #E6D7F1, #F4BBD2, #F9A84A, #F0CE72); the sweep runs on (0.588, 0, 0.377, 1), as every pass in the example.
        kind: "small" / "big" (default by height: big from 100 px); squares: [(dx, dy, w, h[, radius])] from the
        item's top-left, or items, instead of one square on the whole item; clip: an item (or (x, y, w, h[, r]))
        the squares are cut to (a window with round corners). The item starts hidden. Returns when all has landed.
        ease: the pass's curve (default (0.588, 0, 0.377, 1); a.generate_screen's blocks: (0.42, 0, 0.58, 1)).
        v13: the squares stay hidden until t (before, a corner could show from frame 0).
        v13c (LEARNINGS 7): a square covers its item (or each item in `squares`) with `room` px more on every side
        (5) and the item's corner radius + `room`, read from the item (its box, its image's clip, a component's own
        card; a square corner: 5). radius: the item's radius, when you know better than the reading. A square given
        as numbers (dx, dy, w, h[, r]) is drawn as given (r defaults to the item's radius + room).
        v14, lighter (Mateus, 2026-11-23): a card's square from 108 % with Feather 11 -> 2, a panel's from 102 % with
        Feather 10 -> 1.5, fading in over 16 frames; each square's first feather a little different (+-10 %); all
        feathers by the size the piece is shown at (p.shown_at: ~0.65 of these on a 432 px card).
        feather=(start, end): the squares' own feather, in px as drawn (no size factor, no variation)."""
        t0 = self._t(t)
        fx_n = len(self.p.effects)
        x, y, w, h = self.p.bounds(item, t0 + 0.6)     # where it is when the square shows it
        kind = kind or ("big" if h >= 100 else "small")
        g = GEN[kind]
        stops = _stops(colors)
        r_item = self._radius(item) if radius is None else radius
        boxes = []
        for sq in (squares or [item]):
            if isinstance(sq, Item):
                bx, by_, bw, bh = self.p.bounds(sq, t0 + 0.6)
                r = r_item if sq is item else self._radius(sq)
                boxes.append((bx - room, by_ - room, bw + 2 * room, bh + 2 * room, r + room))
            else:
                boxes.append((x + sq[0], y + sq[1], sq[2], sq[3], sq[4] if len(sq) > 4 else r_item + room))
        ks = self._size_k("square")
        kids, ends_fe = [], []
        for i, (bx, by_, bw, bh, r) in enumerate(boxes):
            nm = f"{self.p.art}.fx{fx_n}.{i}"
            if feather is None:
                fs = _feather_scale(bh) * ks
                vary = 1 + GEN_VARY * random.Random(nm).uniform(-1, 1)
                f0, f1 = g["feather"][0] * fs * vary, g["feather"][1] * fs
            else:
                f0, f1 = feather
            ends_fe.append(round(f1, 3))
            grad = El("LinearGradient", dict(SWEEP0), [El("GradientStop", {"colorValue": c, "position": p},
                                                          name=f"{nm}.stop{j}") for j, (c, p) in enumerate(stops)],
                      name=f"{nm}.grad")
            paint = El("Fill", {"fillRule": "clockwise"},   # a feathered fill draws only under the clockwise rule
                       [grad, El("Feather", {"strength": round(f0, 3)}, name=f"{nm}.feather")], name=f"{nm}.fill")
            rect = El("Rectangle", {"width": bw, "height": bh, "cornerRadiusTL": r or None}, name=f"{nm}.rect")
            kids.append(El("Shape", {"x": bx + bw / 2, "y": by_ + bh / 2, "scaleX": g["s0"], "scaleY": g["s0"],
                                     "opacity": 0.0 if g["fade"] else None}, [rect, paint], name=nm))
        if clip is not None:
            cx, cy, cw, ch = self.p.bounds(clip, t0 + 0.6) if isinstance(clip, Item) else clip[:4]
            cr = clip[4] if isinstance(clip, tuple) and len(clip) > 4 else 0
            src = f"{self.p.art}.fx{fx_n}.clip"
            kids.append(El("Shape", {"x": cx, "y": cy}, [El("Rectangle", {
                "width": cw, "height": ch, "originX": 0, "originY": 0, "cornerRadiusTL": cr or None},
                name=f"{src}.rect")], name=src))
            kids.append(El("ClippingShape", {"sourceId": f"@{src}", "fillRule": "nonZero"}, name=f"{src}.cut"))
        self._fx_add(kids, fx_n, t0)
        span = lambda a, z: (z - a) / FPS   # noqa: E731
        for i, _ in enumerate(boxes):
            nm = f"{self.p.art}.fx{fx_n}.{i}"
            if g["fade"]:
                self.c.move(t0, nm, "opacity", 1.0, g["fade"] / FPS, "linear")
            for k, v in SWEEP1.items():
                self.c.move(t0, f"{nm}.grad", k, v, span(0, g["sweep"]), ease or SWEEP_EASE)
            a, z = g["scale"]
            for ax in ("scaleX", "scaleY"):
                self.c.move(t0 + a / FPS, nm, ax, 1.0, span(a, z), "linear")
            _, _, a, z = g["feather"]
            self.c.move(t0 + a / FPS, f"{nm}.feather", "strength", ends_fe[i], span(a, z), "linear")
            a, z = g["stop"]
            self.c.move(t0 + a / FPS, f"{nm}.stop2", "colorValue", stops[1][0], span(a, z), "linear")
        show = t0 + g["show"][0] / FPS
        n = _el(item).name
        self._hidden_at_start(n)
        self.c.fade(show, n, 1.0, g["show"][1] / FPS)
        ends = [t0 + g["sweep"] / FPS]
        d = DETAILS
        row_t = {}
        for i, r in enumerate(self._list(rows or [])):
            rt = show + i * d["rows"]["step"]
            rn = _el(r).name
            row_t[rn] = rt
            self._hidden_at_start(rn)
            self.c.enter(rt, rn, dy=d["rows"]["rise"], dur=d["rows"]["dur"], ease="settle", fade=d["rows"]["fade"])
            ends.append(rt + d["rows"]["dur"])
        pop = d["pop"]
        claimed = self._claimed()
        for p_ in self._list(pops or []):
            claimed.add(_el(p_).name)
            px = self.p.bounds(p_, show)[0]
            owner = next((rn for rn in row_t if self._inside(p_, rn)), None)
            tp = frame(row_t.get(owner, show) + pop["lead"] + pop["across"] * max(0.0, px - x) / max(w, 1)) / FPS
            ends.append(self._number_in(p_, tp, t0, pop_color, lead=0.0))
        if content is True:
            found = self._content_of(item)
        else:
            found = self._list(content) if content else []
        ends.append(self._cascade(found, show + self._by_size(*TEXT_FX["lead"]), TEXT_FX["step"], ink=ink,
                                  letters=letters, block=item, settle_at=show - SETTLE["lead"] / FPS, hide_from=t0))
        end = max(ends)
        self._note(end, f"generate {n} ({kind}, {len(boxes)} square(s))")
        return end

    # v14: what the AI generates inside a block or as a loose element (LEARNINGS 7) ---------------------------------
    def _claimed(self):
        """The items whose entrance the generation has already keyed (each one comes in once)."""
        return self.__dict__.setdefault("_gen_claimed", set())

    def _content_of(self, item, kinds=("text", "icon", "image")):
        """The p.text, p.icon and p.image items inside `item` (and the item itself when it is one)."""
        ids = set()
        kit.walk(_el(item), lambda e: ids.add(id(e)))
        return [it for it in self.p.items.values() if it.kind in kinds and it.wrap is not None and id(it.wrap) in ids]

    def _reading_order(self, items, t):
        """[(bounds, item)] top to bottom, left to right in a row (tops within SCREEN["row"] px)."""
        boxes = sorted(((self.p.bounds(it, t), it) for it in items), key=lambda b: (b[0][1], b[0][0]))
        rows = []
        for b in boxes:
            if rows and abs(b[0][1] - rows[-1][0][0][1]) <= SCREEN["row"]:
                rows[-1].append(b)
            else:
                rows.append([b])
        return [b for r in rows for b in sorted(r, key=lambda b: b[0][0])]

    @staticmethod
    def _next_line(a, b):
        """b is the next line of the same heading as a (LEARNINGS 7: "a two-line heading line by line"): right
        under it (less than half a line between; a measured line can overlap the next by a quarter: its glyphs),
        the same height within 20 %, overlapping across."""
        ax, ay, aw, ah = a
        bx, by_, bw, bh = b
        gap = by_ - (ay + ah)
        return -0.25 * ah <= gap < 0.5 * ah and abs(bh - ah) <= 0.2 * ah and min(ax + aw, bx + bw) > max(ax, bx)

    def _text_el(self, item):
        found = []
        kit.walk(_el(item), lambda e: found.append(e) if e.tag == "Text" else None)
        assert found, f"{_el(item).name}: no text in it (a.typewrite and the generation type a p.text)"
        return found[0]

    def _chars(self, item):
        return sum(len(str(self.c.by[r].attrs.get("text") or "")) for r in self._runs(item))

    def _reveal(self, item, soft=0):
        """v14 (LEARNINGS 19.2, "Letter by letter in Rive"): the text's letter-by-letter reveal, a TextModifierGroup
        (modifyOpacity) with one TextModifierRange, modifyFrom = falloffFrom = -10, falloffTo = 0, modifyTo = w
        (a soft front: w = min(0.5, soft / letters); 0: each letter whole, a typewriter): all hidden at offset -w
        (from frame 0), all shown at 1, each letter as the offset passes it (a fraction of the text: it takes
        fractions, one key types it). One per text. Returns (the range's name, w)."""
        t_el = self._text_el(item)
        rn = f"{t_el.name}.front"
        if rn in self.c.by:
            return rn, float(self.c.by[rn].attrs.get("modifyTo") or 0.0)
        n = max(1, self._chars(item))
        w = round(min(0.5, soft / n), 4) if soft else 0.0
        rng = El("TextModifierRange", {"modifyFrom": -10.0, "falloffFrom": -10.0, "falloffTo": 0.0, "modifyTo": w,
                                       "offset": -w}, name=rn)
        grp = El("TextModifierGroup", {"modifyOpacity": True}, [rng], name=f"{t_el.name}.reveal")
        t_el.children.append(grp)
        self.c.by[grp.name], self.c.by[rn] = grp, rng
        self.c.parent[id(grp)], self.c.parent[id(rng)] = t_el, grp
        return rn, w

    def _ink_colors(self, item):
        """The colours a generation pass tints: `item`'s texts' and shapes' (not a text's dim layer)."""
        return [c for c in self._paint_colors(item) if not c.endswith(".dim")]

    def _ink_pass(self, item, t, d, ink=None):
        """v14 (LEARNINGS 7, lumi-dental-winback v05-v06): the whole of `item` changes colour: the gradient's orange
        from t, its pink over 10 frames after max(0.35 s, 60 % of d), held 8, then its own colour over 20, linear
        (each colour keeps its own alpha). A colour keyed already (a hover, a count) is left alone. Returns the
        end."""
        fx = TEXT_FX
        c0, c1 = (_argb(c) for c in (ink or INK))
        t1 = frame(t + max(fx["pink_at"][0], fx["pink_at"][1] * d)) / FPS
        t2 = t1 + (fx["pink"] + fx["hold"]) / FPS
        for col in self._ink_colors(item):
            tr = self.c.track(col, "colorValue")
            if len(tr.keys) > 1:
                continue
            own = tr.keys[0]["v"]
            self.c.set(t, col, "colorValue", own[:2] + c0[2:])
            self.c.move(t1, col, "colorValue", own[:2] + c1[2:], fx["pink"] / FPS, "linear")
            self.c.move(t2, col, "colorValue", own, fx["own"] / FPS, "linear")
        return t2 + fx["own"] / FPS

    def _blur_pass(self, item, t, v, dur, shapes=False, ease="linear"):
        """A Feather of `v` (screen px) at t on `item`'s texts (shapes: and its icons' and drawings' paints),
        sharpening to 0 over `dur` s from the next frame. A feather keyed already is left alone. Returns the end."""
        for fe in self._feathers(item, shapes=shapes):
            if len(self.c.track(fe, "strength").keys) > 1:
                continue
            self.c.set(t, fe, "strength", round(self._fe(fe, v), 3))
            self.c.move(t + 1 / FPS, fe, "strength", 0.0, dur, ease)
        return t + 1 / FPS + dur

    def _letters(self, item, t, ink=None):
        """A text the AI writes (LEARNINGS 7, "How a text comes in"): letter by letter with a soft front, its colour
        and feather passes. Returns (its entrance, its end)."""
        fx = TEXT_FX
        n = max(1, self._chars(item))
        d = frame(min(fx["d"][1], max(fx["d"][0], n / fx["cps"]))) / FPS
        rn, _ = self._reveal(item, fx["soft"])
        self.c.move(t, rn, "offset", 1.0, d, "linear")
        e1 = self._ink_pass(item, t, d, ink)
        e2 = self._blur_pass(item, t, fx["feather"] * self._size_k("text"), fx["feather_dur"] / FPS)
        return d, max(t + d, e1, e2)

    def _whole(self, item, t, ink=None, shown=False, shapes=False, fade=None, feather=None, feather_dur=None):
        """A label (letters=False) or an icon comes in whole: opacity over `fade` frames (unless it is shown
        already: the block itself), the colour pass, the feather. Returns (its entrance, its end)."""
        wf = TEXT_FX["whole"]
        fade = (wf["fade"] if not shapes else TEXT_FX["icon_fade"]) if fade is None else fade
        if feather is None:
            feather = wf["feather"] if not shapes else TEXT_FX["feather"]
        if feather_dur is None:
            feather_dur = wf["feather_dur"] if not shapes else TEXT_FX["feather_dur"]
        n = _el(item).name
        if not shown:
            self._hidden_at_start(n)
            self.c.fade(t, n, 1.0, fade / FPS)
        d = max(fade, 24) / FPS          # the pink after 0.35 s, as a short text's (lumi's mark: d 0.4)
        e1 = self._ink_pass(item, t, d, ink)
        e2 = self._blur_pass(item, t, feather * self._size_k("text"), feather_dur / FPS, shapes=shapes)
        return fade / FPS, max(t + fade / FPS, e1, e2)

    def _number_in(self, item, t, hide_from, color=PURPLE, lead=0.0):
        """v11's pop (LEARNINGS 7, "numbers #AE68FA -> their own, with feather 4 -> 0"): the number is see-through
        from `hide_from`, fades in in `color` over 8 frames at t, then turns to its own colour over 36, sharpening
        from a Feather of 4 (by the size shown). Returns the end."""
        pop = DETAILS["pop"]
        pc = _argb(color or PURPLE)
        t = t + lead
        for col in self._colors(item):
            tr = self.c.track(col, "colorValue")
            if len(tr.keys) > 1:
                continue
            own = tr.keys[0]["v"]
            self.c.set(hide_from, col, "colorValue", "00" + pc[2:])
            self.c.move(t, col, "colorValue", pc, pop["fade"], "linear")
            self.c.move(t + pop["fade"], col, "colorValue", own, pop["dur"], "linear")
        k = self._size_k("text")
        for fe in self._feathers(item):
            if len(self.c.track(fe, "strength").keys) > 1:
                continue
            self.c.set(hide_from, fe, "strength", round(pop["feather"] * k, 3))
            self.c.move(t + pop["fade"], fe, "strength", 0.0, pop["dur"], "linear")
        return t + pop["fade"] + pop["dur"]

    def _settle(self, item, t):
        """v14 (LEARNINGS 7, "Photos settle inside their frame"): the p.image's picture from 112 % (from frame 0) to
        100 % over 1.5 s on (0.16, 1, 0.3, 1), from t; its frame (the clip) doesn't move. Returns the end."""
        img = f"{_el(item).name}.img"
        s = SETTLE
        if img not in self.c.by or any(len(self.c.track(img, ax).keys) > 1 for ax in ("scaleX", "scaleY")):
            return t
        for ax in ("scaleX", "scaleY"):
            self.c.set(0.0, img, ax, s["s0"])
            self.c.move(frame(t) / FPS, img, ax, 1.0, s["dur"], s["ease"])
        return frame(t) / FPS + s["dur"] * s["landed"]

    def _content_in(self, item, t, ink=None, letters=True, shown=False, hide_from=0.0):
        """One generated element at t, by kind. Returns (its entrance, its end)."""
        if item.kind == "text":
            runs = self._runs(item)
            txt = "".join(str(self.c.by[r].attrs.get("text") or "") for r in runs)
            if txt.strip() and NUMBER.fullmatch(txt):
                end = self._number_in(item, t, hide_from)
                return DETAILS["pop"]["fade"], end
            if letters:
                return self._letters(item, t, ink)
            return self._whole(item, t, ink, shown=shown)
        if item.kind == "icon":
            return self._whole(item, t, ink, shown=shown, shapes=True)
        if item.kind == "image":
            if not shown:
                n = _el(item).name
                self._hidden_at_start(n)
                self.c.fade(t, n, 1.0, TEXT_FX["icon_fade"] / FPS)
            return TEXT_FX["icon_fade"] / FPS, self._settle(item, t)
        return self._whole(item, t, ink, shown=shown, shapes=True)     # anything else (a component, a drawing)

    def _cascade(self, items, t, step, ink=None, letters=True, block=None, settle_at=None, hide_from=0.0):
        """Generated elements one after another from t (LEARNINGS 7): in reading order, each `step` frames after
        the one before (a little uneven: +-SCREEN["jitter"]), a heading's next line when the line above ends.
        Inside a block (settle_at given) its photos settle with the block instead of taking a turn. Each element
        comes in once (an element claimed already is left out). Returns the end."""
        claimed = self._claimed()
        items = [it for it in items if _el(it).name not in claimed]
        if not items:
            return t
        claimed.update(_el(it).name for it in items)
        rnd = random.Random(f"{_el(items[0]).name}:cascade")
        ends, prev = [t], None
        for b, it in self._reading_order(items, t):
            shown = it is block
            if it.kind == "image" and settle_at is not None:
                ends.append(self._settle(it, settle_at))
                continue
            if prev is None:
                ti = t
            elif it.kind == "text" and prev[1].kind == "text" and self._next_line(prev[0], b):
                ti = prev[2] + prev[3]
            else:
                ti = prev[2] + step * rnd.uniform(1 - SCREEN["jitter"], 1 + SCREEN["jitter"]) / FPS
            ti = frame(ti) / FPS
            d, end = self._content_in(it, ti, ink, letters, shown, hide_from)
            ends.append(end)
            prev = (b, it, ti, d)
        return max(ends)

    def _fx_add(self, kids, fx_n, t0=0.0):
        """The effect's shapes, in a group of their own on the effects layer (over the scene), hidden until t0."""
        group = El("Node", {"x": 0, "y": 0, "opacity": 0.0 if t0 > 0 else 1.0}, kids, name=f"{self.p.art}.fx{fx_n}")
        self.p.fx.children.append(group)
        self.p.effects.append(group)
        self.c.parent[id(group)] = self.p.fx

        def reg(e, par):
            if e.name:
                self.c.by[e.name] = e
            for c in e.children:
                if isinstance(c, El):
                    self.c.parent[id(c)] = e
                    reg(c, e)
        reg(group, self.p.fx)
        if t0 > 0:
            self.c.set(0.0, group.name, "opacity", 0.0)
            self.c.set(t0, group.name, "opacity", 1.0)
        return group

    def wash(self, area=None, t=None, colors=None, opacity=None, radius=0, feather=None):
        """The anticipation wash (v11, Mateus's rule of 2026-11-13, the example's "BG 14"): before the blocks, the
        7-stop gradient sweeps the whole area at 50 % (drawn 110 % and cut to the area), sharpening from a Feather of
        20 to 3, in 217 frames on (0.588, 0, 0.377, 1). area: an item or (x, y, w, h) (default: the main artboard);
        colors: as a.generate's; opacity: 0.5 (on a cream background 0.75 reads better: ask-your-agent v03). The first
        blocks can start while it sweeps (in the example ~0.3 s in). Returns when the sweep ends.
        v14: its feather by the size the piece is shown at (half on a 432 px card: 10 -> 1.5; feather=(start, end):
        your own, as drawn); its tail fades out over 18 frames as the sweep ends (it could stay faintly in a corner:
        lumi-dental-winback faded it by hand)."""
        t0 = self._t(t)
        fx_n = len(self.p.effects)
        if area is None:
            x, y, w, h = 0.0, 0.0, float(self.p.w), float(self.p.h)
        elif isinstance(area, Item):
            x, y, w, h = self.p.bounds(area, t0)
        else:
            x, y, w, h = area[:4]
        wd = WASH
        k = self._size_k("wash")
        f0, f1 = (wd["feather"][0] * k, wd["feather"][1] * k) if feather is None else feather
        nm = f"{self.p.art}.fx{fx_n}.wash"
        sx, sy = w / 682.5, h / 620.5          # the example's sweep was drawn for a 682.5 x 620.5 area
        k0 = {"startX": -535.6 * sx, "startY": -1582.6 * sy, "endX": -214.6 * sx, "endY": -334.2 * sy}
        k1 = {"startX": 107.4 * sx, "startY": 213.6 * sy, "endX": 1831.9 * sx, "endY": 4515.4 * sy}
        stops = _stops(colors)
        grad = El("LinearGradient", {k: round(v, 2) for k, v in k0.items()},
                  [El("GradientStop", {"colorValue": c, "position": p}, name=f"{nm}.stop{j}")
                   for j, (c, p) in enumerate(stops)], name=f"{nm}.grad")
        paint = El("Fill", {"fillRule": "clockwise"},
                   [grad, El("Feather", {"strength": round(float(f0), 3)}, name=f"{nm}.feather")], name=f"{nm}.fill")
        rect = El("Rectangle", {"width": w, "height": h, "cornerRadiusTL": radius or None}, name=f"{nm}.rect")
        src = f"{nm}.clip"
        kids = [El("Shape", {"x": x + w / 2, "y": y + h / 2, "scaleX": wd["scale"], "scaleY": wd["scale"],
                             "opacity": wd["opacity"] if opacity is None else opacity}, [rect, paint], name=nm),
                El("Shape", {"x": x, "y": y}, [El("Rectangle", {"width": w, "height": h, "originX": 0, "originY": 0,
                                                                "cornerRadiusTL": radius or None}, name=f"{src}.rect")],
                   name=src),
                El("ClippingShape", {"sourceId": f"@{src}", "fillRule": "nonZero"}, name=f"{src}.cut")]
        group = self._fx_add(kids, fx_n, t0)
        dur = wd["sweep"] / FPS
        for k_, v in k1.items():
            self.c.move(t0, f"{nm}.grad", k_, round(v, 2), dur, SWEEP_EASE)
        _, _, a, z = wd["feather"]
        self.c.move(t0 + a / FPS, f"{nm}.feather", "strength", round(float(f1), 3), (z - a) / FPS, "linear")
        self.c.fade(t0 + dur, group.name, 0.0, wd["out"] / FPS)
        self._note(t0 + dur, f"wash ({w:g} x {h:g})")
        return t0 + dur

    def loose(self, items, t=None, stagger=None, color=None, fade=None, lead=1 / 60, dur=None, feather=None,
              feather_dur=None, letters=True, ink=None):
        """Loose elements, with no block under them (a logo, a menu, an avatar, a name; LEARNINGS 7). v14: as the
        texts and icons inside a block: their p.text letter by letter (letters=False: whole), their p.icon over 20
        frames, their p.image fading in and settling, in reading order from t, `stagger` s apart (2-4 frames:
        SCREEN["loose_gap"], 3), a heading's next line when the line above ends; all in the gradient's orange ->
        pink -> their own colour, with the feather (LEARNINGS 7: no purple on a classic generation). An item that
        is a box or a drawing of your own with paints outside those (a divider, a badge's fill) also fades in over
        20 frames at t, its paints in the same passes. Returns when the last has landed.
        color=: v11-v13's single tint instead (#8D5DF5 was the default): each item fades in over 20 frames while
        its texts and shapes come in `color` and turn to their own (`dur`, 40 frames), sharpening from a Feather of
        4 (`feather`, `feather_dur`); `lead`, `fade` as before."""
        t0 = self._t(t)
        if color is not None:
            return self._loose_tint(items, t0, 3 / 60 if stagger is None else stagger, color, fade, lead, dur,
                                    feather, feather_dur)
        step = SCREEN["loose_gap"] if stagger is None else secs(stagger) * FPS
        claimed = self._claimed()
        found, wraps = [], []
        for it in self._list(items):
            inner = [c for c in self._content_of(it) if _el(c).name not in claimed]
            found += [c for c in inner if c not in found]
            if it.kind not in ("text", "icon", "image"):
                wraps.append((it, inner))
        end = self._cascade(found, t0, step, ink=ink, letters=letters)
        for it, inner in wraps:     # its own paints, outside its texts, icons and photos
            names = set()
            for c in inner:
                kit.walk(_el(c), lambda e: names.add(e.name) if e.name else None)
            own = [c for c in self._ink_colors(it) if c not in names and len(self.c.track(c, "colorValue").keys) == 1]
            if inner and not own:     # nothing of its own to bring in (a group of texts and icons)
                continue
            claimed.add(_el(it).name)
            n = _el(it).name
            self._hidden_at_start(n)
            self.c.fade(t0, n, 1.0, TEXT_FX["icon_fade"] / FPS)
            end = max(end, self._ink_pass(it, t0, 0.4, ink),
                      self._blur_pass(it, t0, TEXT_FX["feather"] * self._size_k("text"),
                                      TEXT_FX["feather_dur"] / FPS, shapes=True))
        self._note(end, f"loose {len(self._list(items))} item(s)")
        return end

    def _loose_tint(self, items, t0, stagger, color, fade, lead, dur, feather, feather_dur):
        """v11-v13's loose elements, in one colour (a.loose(..., color=))."""
        d = dict(DETAILS["loose"])
        d.update({k: v for k, v in (("fade", fade), ("dur", dur), ("feather", feather)) if v is not None})
        fdur = d["dur"] if feather_dur is None else feather_dur
        pc = _argb(color)
        end = t0
        for i, it in enumerate(self._list(items)):
            ti = t0 + i * stagger
            n = _el(it).name
            self._claimed().add(n)
            self._hidden_at_start(n)
            self.c.fade(ti, n, 1.0, d["fade"])
            for col in self._paint_colors(it):
                own = self.c.track(col, "colorValue").keys[0]["v"]
                self.c.set(ti, col, "colorValue", own[:2] + pc[2:])
                self.c.move(ti + lead, col, "colorValue", own, d["dur"], "linear")
            for fe in self._feathers(it, shapes=True):
                self.c.set(ti, fe, "strength", self._fe(fe, d["feather"]))
                self.c.move(ti + 1 / FPS, fe, "strength", 0.0, fdur, "linear")
            end = ti + max(d["fade"], lead + d["dur"], fdur)
        self._note(end, f"loose {len(self._list(items))} item(s)")
        return end

    def sent(self, item, t=None, dy=20):
        """v13.1 (LEARNINGS 6 and 19.2): the user's message, just sent (its bubble, or the row holding it): it appears
        in 5 frames (opacity, linear) and rises `dy` px in 30 frames on (0, 0, 0, 1), both from t (frame 0 when the
        piece opens on the send). Hidden until then. Returns t. (a.send brings it 23 frames after the press, with
        the typed text flying out of the field.)"""
        t = self._t(t)
        n = _el(item).name
        f0 = frame(t)
        self._hidden_at_start(n)
        y0 = self.c.base(n, "y")
        if f0 == 0:
            self.c.track(n, "y").keys[0]["v"] = y0 + dy
        else:     # the frame before, while still hidden
            self.c.set((f0 - 1) / FPS, n, "y", y0 + dy)
        self.c.move(f0 / FPS, n, "y", y0, 30 / FPS, [0.0, 0.0, 0.0, 1.0])
        self.c.fade(f0 / FPS, n, 1.0, 5 / FPS)
        self._note(f0 / FPS + 0.5, f"sent {n}")
        return t

    def generate_screen(self, blocks, area=None, t=None, loose=(), details=(), gradient=None, colors=None, gap=None,
                        opacity=None, clip=None, letters=True, order=True):
        """v13, the approved recipe (motion-spec/LEARNINGS.md 19.2): the AI generates a whole screen (an email, a
        site, a page, a dashboard) while the Copilot loads. t: when the message is sent (as a.steps' / a.think's).
        v14 (LEARNINGS 7, "Top to bottom, big to small"; 19.2 "A small card"), with no patches in the piece:
          - 6 frames in, the wash sweeps the whole `area` (an item or (x, y, w, h); to frame 223, its tail fading);
          - `blocks` in reading order (top to bottom, left to right in a row; order=False: as listed): the first
            108 frames in (96 on a 432 px card), the next ones `gap` s apart (63 frames, ~1 s; ~0.5 s, 28 frames,
            on a small card), each gap a little uneven (+-15 %); each from its gradient square (a.generate: the
            biggest block as a panel, 1.02 -> 1 in a 131-frame pass, the others as cards, 1.08 -> 1 in 84, as
            19.2's photo and crystal; the pass on (0.42, 0, 0.58, 1)), its
            texts, icons and photos coming in as it shows (a.generate's content: letter by letter, orange -> pink
            -> own, photos settling); a block can be (item, {a.generate's keywords: rows, pops, squares, kind,
            content, letters...}). A block inside another keeps its own content. v14b: a block given plain whose
            centre falls inside a bigger block (a badge on the hero photo) starts with it: it joins that block's
            `rows` (rising 4 px as the block shows, its texts in the block's cascade) instead of taking a ~1 s slot
            of its own, so [hero, badge, crystal] times as [(hero, {"rows": [badge]}), crystal] (the last check at
            260 instead of 313 in the welcome email); given with keywords, (badge, {...}), it keeps its own slot;
          - `loose`, elements with no block (a logo, a name, a heading under the photo): each at its place in the
            same order: under a block as it shows it (4 frames later), but 3 frames before the next block starts
            when that comes sooner; above every block 3 frames after the first starts (the welcome email: the
            name at 111, the quote at 168; lumi-dental-winback: the heading under the photo 4 frames after it
            shows); together in reading order 2-4 frames apart (a.loose);
          - `details` (v13: last of all) are now content: each goes with the block it sits over (its centre inside
            the block), else with the loose ones.
        Colours: gradient=(warm, cool), the two ends of the design's own gradient (a background, a card, a button):
        the wash, the blocks and the texts' pass take their tones from it (p.palette; the wash at 75 %); colors= a
        palette of your own (a dict as p.palette returns); neither: the library's classic gradient. clip: what the
        squares are cut to (default none). letters=False: every text whole (an interface's short labels). Fit the
        timing to the screen with `gap`. Returns the end of the generation: give it to a.steps(until=) so the last
        check lands there; the answer ~25 frames later."""
        t0 = self._t(t)
        S, f = SCREEN, (lambda n: n / FPS)
        pal = colors if colors is not None else (palette(*gradient) if gradient else None)
        op = opacity if opacity is not None else (0.75 if pal else None)
        ink = pal["details"] if pal else None
        ends = [self.wash(area, t=t0 + f(S["wash"]), colors=pal["wash"] if pal else None, opacity=op)]
        g = f(self._by_size(*S["gap"])) if gap is None else secs(gap)
        first = t0 + f(round(self._by_size(*S["block"])))
        bl = [b if isinstance(b, tuple) else (b, {}) for b in self._list(blocks)]
        at = first + 0.6
        bl = self._nest(bl, at, t0)
        if order:
            pos = {id(it): i for i, (_, it) in enumerate(self._reading_order([b[0] for b in bl], at))}
            bl.sort(key=lambda b: pos[id(b[0])])
        rnd = random.Random(f"{self.p.art}:screen:{len(bl)}")
        starts, ts = [], first
        for i in range(len(bl)):
            if i:
                ts += g * rnd.uniform(1 - S["jitter"], 1 + S["jitter"])
            starts.append(frame(ts) / FPS)
        # each element inside a block goes with its innermost block; a detail with the block it sits over
        areas = [self.p.bounds(it, at) for it, _ in bl]
        big = max(range(len(bl)), key=lambda j: areas[j][2] * areas[j][3]) if bl else -1
        kinds = [kw.get("kind") or ("big" if j == big else "small") for j, (_, kw) in enumerate(bl)]
        content = [[] for _ in bl]
        claimed = self._claimed()
        seen, block_ids = set(), [self._ids(it) for it, _ in bl]
        for i, (it, kw) in enumerate(bl):
            for c in self._content_of(it):
                if id(c) in seen or _el(c).name in claimed:
                    continue
                homes = [j for j in range(len(bl)) if id(c.wrap) in block_ids[j]]
                home = min(homes, key=lambda j: areas[j][2] * areas[j][3])
                content[home].append(c)
                seen.add(id(c))
        loose = list(self._list(loose))
        for d in self._list(details):
            dx, dy_, dw, dh = self.p.bounds(d, at)
            cx, cy = dx + dw / 2, dy_ + dh / 2
            homes = [j for j, (bx, by_, bw, bh) in enumerate(areas) if bx <= cx <= bx + bw and by_ <= cy <= by_ + bh]
            if homes:
                home = min(homes, key=lambda j: areas[j][2] * areas[j][3])
                content[home] += [c for c in (self._content_of(d) or [d]) if id(c) not in seen]
            else:
                loose.append(d)
        for i, (it, kw) in enumerate(bl):
            kw = dict(kw)
            kw.setdefault("kind", kinds[i])
            kw.setdefault("ease", S["ease"])
            kw.setdefault("clip", clip)
            kw.setdefault("letters", letters)
            kw.setdefault("ink", ink)
            if pal:
                kw.setdefault("colors", pal["blocks"][i % len(pal["blocks"])])
            kw.setdefault("content", content[i])
            ends.append(self.generate(it, t=starts[i], **kw))
        # the loose elements at their place in the order
        slots = {}
        if loose:
            order_ = self._reading_order([b[0] for b in bl] + loose, at)
            idx = {id(it): j for j, (_, it) in enumerate(order_)}
            for it in loose:
                above = [i for i, (b, _) in enumerate(bl) if idx[id(b)] < idx[id(it)]]
                below = [i for i, (b, _) in enumerate(bl) if idx[id(b)] > idx[id(it)]]
                if above:     # as the block above shows it, and before the block below starts
                    ta = starts[above[-1]] + f(GEN[kinds[above[-1]]]["show"][0] + S["after_show"])
                    if below:
                        ta = max(starts[above[-1]], min(ta, starts[below[0]] - f(S["loose_lead"])))
                elif below:   # above every block: just after the first one starts
                    ta = starts[below[0]] + f(S["loose_lead"])
                else:
                    ta = first
                slots.setdefault(frame(ta), []).append(it)
        for fr, its in sorted(slots.items()):
            ends.append(self.loose(its, t=fr / FPS, letters=letters, ink=ink))
        end = frame(max(ends)) / FPS
        self._note(end, f"generate_screen: {len(starts)} block(s), {len(loose)} loose")
        return end

    def _nest(self, bl, at, t0):
        """v14b (the blind test, 6-cego-aya-v14.md 5.2): a block given plain whose centre falls inside a bigger block
        (a badge on the hero photo) is no block of its own: it joins the bigger block's `rows` (it rises 4 px and
        fades in as that block shows, its texts in that block's cascade), as the approved ask-your-agent's
        (hero, {"rows": [badge]}), instead of taking a whole ~1 s slot of the rhythm (the blind copy's last check came
        at 313 instead of 260). It goes to the smallest block holding it, up to one that is no one's row; several in
        reading order, after the rows given. A block given with its own keywords, (item, {...}), keeps its own slot.
        bl: [(item, keywords)]; returns it without the nested ones."""
        box = {id(it): self.p.bounds(it, at) for it, _ in bl}
        size = lambda it: box[id(it)][2] * box[id(it)][3]   # noqa: E731

        def holder(it):
            x, y, w, h = box[id(it)]
            cx, cy = x + w / 2, y + h / 2
            hs = [b for b, _ in bl if b is not it and size(b) > size(it) and
                  box[id(b)][0] <= cx <= box[id(b)][0] + box[id(b)][2] and
                  box[id(b)][1] <= cy <= box[id(b)][1] + box[id(b)][3]]
            return min(hs, key=size) if hs else None
        parent = {id(it): h for it, kw in bl if not kw for h in [holder(it)] if h is not None}
        if not parent:
            return bl
        joined = {}
        for it, _ in bl:
            if id(it) in parent:
                top = parent[id(it)]
                while id(top) in parent:
                    top = parent[id(top)]
                joined.setdefault(id(top), []).append(it)
        out = []
        for it, kw in bl:
            if id(it) in parent:
                continue
            if id(it) in joined:
                kids = [k for _, k in self._reading_order(joined[id(it)], at)]
                kw = dict(kw, rows=list(self._list(kw.get("rows") or [])) + kids)
                self._note(t0, f"generate_screen: {', '.join(_el(k).name for k in kids)} inside {_el(it).name}: "
                               f"its rows")
            out.append((it, kw))
        return out

    def _ids(self, item):
        ids = set()
        kit.walk(_el(item), lambda e: ids.add(id(e)))
        return ids

    def _paint_colors(self, item):
        """Every SolidColor of `item` that a colour can tint: its texts' fills and its shapes' fills and strokes (not
        the effects' own)."""
        out = []
        kit.walk(_el(item), lambda e: out.append(e.name) if e.tag == "SolidColor" and e.name and
                 self.c.parent.get(id(e)) is not None and self.c.parent[id(e)].tag in ("Fill", "Stroke") else None)
        return out

    def _inside(self, item, name):
        found = []
        target = _el(item)
        root = self.c.by.get(name)
        if root is not None:
            kit.walk(root, lambda e: found.append(1) if e is target else None)
        return bool(found)

    # ------------------------------------------------------------ your own beats
    def beats(self, beats):
        """Your own beats on the same timeline (the kit's beat sheet: {"t", "do": move / set / fade / enter / exit /
        pop..., "target": an element's name, ...}). They don't move `now`."""
        choreo.run_beats(self.c, beats)
        for b in beats:
            self._note((b.get("t") or 0) + (b.get("dur") or 0), f"beat {b.get('do')} {b.get('target', '')}")
