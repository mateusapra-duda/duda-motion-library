"""kit.py: the library's build helpers, in one module.

Copied (and generalised) from the best versions in the four component builds (pecas/ui-controls/build.py, which
already merged copilot / workspace / visual-edit learnings, and pecas/ui-controls/icons.py). Nothing here imports from
another piece. Values come from the Duda Design System tokens (ds/tokens.json) and the team's motion tokens
(motion-spec/tokens.json), read at build time.

A component module builds with these helpers:
    VM(...)             its view model (props in DS names)
    use(vm)             the view model the next elements bind to
    box/absolute/text/icon_slot/solid/line...   the drawing
    Anim / pose / Layer / bool_layer / gate_layer / listener...   the state machine
    component(...)      the component artboard (isComponent, "State Machine 1", bound to its VM)
and assemble(...) writes the RML.
"""
import copy
import json
import math
import os
import re
import sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
# a released bundle (dist/vNN/biblioteca) carries frozen copies of the tools in vendor/ and of the motion tokens in
# motion-spec/ (where the vendored choreo.py looks for them); the working library uses the repo's own
VENDOR = os.path.join(HERE, "vendor")
sys.path.insert(0, VENDOR if os.path.isdir(VENDOR) else os.path.join(ROOT, "tools"))
from rml import Doc, El, argb  # noqa: E402
from svg2rml import parse, points_path, to_vertices  # noqa: E402
from rive_schema import load  # noqa: E402

SCHEMA = load()
FPS = 60
ICONS = os.path.join(HERE, "icons")
ART = os.path.join(HERE, "art")       # drawings with their own colours (art/README.md)


def key(tag, prop):
    return SCHEMA["types"][tag][prop]


# ================================================================ tokens
DS = json.load(open(os.path.join(HERE, "ds", "tokens.json")))
MOTION = json.load(open(os.path.join(HERE, "motion-spec", "tokens.json") if os.path.isdir(VENDOR)
                       else os.path.join(ROOT, "motion-spec", "tokens.json")))


def hex_argb(h):
    """'#rrggbb' or '#rrggbbaa' (the DS writes alpha last) -> 'AARRGGBB'."""
    h = h.lstrip("#")
    if len(h) == 8:
        return argb("#" + h[:6], int(h[6:], 16) / 255)
    return argb("#" + h)


def color(name, alpha=None):
    """A DS colour by its token name. Where the DS has two generations of a token (the newer one is in the newer
    components and in the storyboards), the newer wins (Mateus, 2026-10-22). 'Backgrounds/x' and 'Background/x' are
    the same token in the two generations."""
    c = DS["color"]
    alias = name.replace("Backgrounds/", "Background/")
    for table, n in ((c["semantic_newer"], name), (c["semantic_newer"], alias), (c["component"], name),
                     (c["semantic"], name)):
        if n in table:
            v = hex_argb(table[n])
            break
    else:
        fam, _, step = name.partition("-")
        v = hex_argb(c["primitive"][fam][name])
    if alpha is not None:
        v = f"{round(alpha * 255):02X}{v[2:]}"
    return v


def space(name):
    return DS["spacing"][name]


def radius(name):
    return DS["radius"][name]


ICON_STROKE = DS["stroke"]["Stroke 1-50"]          # 1.5: the DS icon rule (Mateus, 2026-10-22)

# motion tokens (motion-spec/tokens.json): curves by name, durations in seconds
EASE = {k: tuple(v["bezier"]) for k, v in MOTION["ease"].items() if isinstance(v.get("bezier"), list)}
EASE["strong"] = EASE["duda_strong"]
DUR = {k: v / 1000 for k, v in MOTION["duration"].items()}
PRESS, FADE, SHORT, MEDIUM, PANEL = DUR["press"], DUR["fade"], DUR["short"], DUR["medium"], DUR["panel"]
SWAP = MOTION["state_swap"]["fade_out_ms"] / 1000   # one state at a time: the outgoing state fades this long
HOVER_MS = round(FADE * 1000)       # hover in and out: the fade token
RELEASE_MS = round(SHORT * 1000)    # a press lets go softly

WHITE = argb("#FFFFFF")
CLEAR = argb("#FFFFFF", 0.0)
BLACK0 = argb("#000000", 0.0)


# ================================================================ view models
VM_TAGS = {"string": "String", "number": "Number", "boolean": "Boolean", "trigger": "Trigger", "color": "Color",
           "artboard": "Artboard"}
BIND_KEY = {"Boolean": 634, "String": 635, "Number": 636, "Color": 638, "Trigger": 686, "Artboard": 823}
VALUE_KEY = {"Boolean": 593, "Number": 575, "String": 561, "Color": 555}   # ViewModelInstance<X>.propertyValue
CUR = None   # the view model the elements being built bind to


class VM:
    """A view model. props: (name, kind, default); kind is string | number | boolean | trigger | color | artboard |
    vm:<key> (holds an instance of another view model) | list:<key> (default: a list of instance refs).
    A name starting with "_" is internal (no componentProps)."""
    all = {}

    def __init__(self, k, name, props):
        assert k not in VM.all, k
        self.key, self.name, self.props = k, name, props
        self.instances = []
        VM.all[k] = self

    def ref(self, prop=None):
        return f"vm.{self.key}" + (f".{prop}" if prop else "")

    def kind(self, prop):
        return next(k for n, k, _ in self.props if n == prop)

    def inst(self, ref, values=None, name=None):
        """Another exported instance (a host's data for one placement); returns its ref."""
        unknown = set(values or {}) - {n for n, _, _ in self.props}
        assert not unknown, f"{self.name}: no {unknown}"
        self.instances.append((name or ref, ref, dict(values or {})))
        return ref

    def values(self, ref, values):
        out = []
        for n, kind, default in self.props:
            v = values.get(n, default)
            attrs = {"viewModelPropertyId": f"@{self.ref(n)}"}
            if kind.startswith("vm:"):
                attrs["propertyValue"] = f"@{v}"
                out.append(El("ViewModelInstanceViewModel", attrs, ref=f"{ref}.{n}"))
            elif kind.startswith("list:"):
                vm = VM.all[kind[5:]]
                items = [El("ViewModelInstanceListItem", {"viewModelId": f"@{vm.ref()}", "viewModelInstanceId": f"@{r}"})
                         for r in (v or [])]
                out.append(El("ViewModelInstanceList", attrs, items, ref=f"{ref}.{n}"))
            elif kind == "artboard":
                attrs["propertyValue"] = f"@{v}" if v else None
                out.append(El("ViewModelInstanceArtboard", attrs, ref=f"{ref}.{n}"))
            else:
                if kind != "trigger":
                    attrs["propertyValue"] = v
                out.append(El(f"ViewModelInstance{VM_TAGS[kind]}", attrs, ref=f"{ref}.{n}"))
        return out

    def el(self):
        props = []
        for n, kind, _ in self.props:
            public = None if n.startswith("_") else 1
            if kind.startswith("vm:"):
                props.append(El("ViewModelPropertyViewModel", {"viewModelReferenceId": f"@vm.{kind[3:]}",
                                                               "componentProps": public}, name=n, ref=self.ref(n)))
            elif kind.startswith("list:"):
                props.append(El("ViewModelPropertyList", {"componentProps": public}, name=n, ref=self.ref(n)))
            else:
                props.append(El(f"ViewModelProperty{VM_TAGS[kind]}", {"componentProps": public}, name=n,
                                ref=self.ref(n)))
        insts = [El("ViewModelInstance", {"exports": True}, self.values(f"vmi.{self.key}", {}), name="Default",
                    ref=f"vmi.{self.key}")]
        insts += [El("ViewModelInstance", {"exports": True}, self.values(ref, vals), name=name, ref=ref)
                  for name, ref, vals in self.instances]
        return El("ViewModel", {"defaultInstanceId": f"@vmi.{self.key}"}, props + insts, name=self.name,
                  ref=self.ref())


def use(vm):
    global CUR
    CUR = vm


def bind(prop, pkey, converter=None, write=False, ref=None, path=None):
    """A bind to `prop` of the current view model, or along `path` (refs: view model, property, sub-property...)."""
    attrs = {"sourcePathIds": path or (CUR.ref(), CUR.ref(prop)), "propertyKey": pkey}
    if converter:
        attrs["converterId"] = f"@{converter}"
    if write:
        attrs["direction"] = True
    return El("DataBindContext", attrs, ref=ref)


CONVERTERS = [
    # +1 on a character index: a range ending one glyph after `typed` selects exactly that glyph (the caret)
    El("DataConverterRangeMapper", {"minInput": 0, "maxInput": 1, "minOutput": 1, "maxOutput": 2}, name="Plus one",
       ref="conv.plus1"),
    El("DataConverterStringTrim", {"trimType": 3}, name="Trim", ref="conv.trim"),
]


# ================================================================ fonts and text
FONTS = {"duda": ("LabelSansVF.ttf", "Duda Sans"), "caret": ("DudaSansCaret.ttf", "Duda Sans Caret")}
FONT_DIR = ["fonts"]   # where the font files are, relative to the project that builds (a piece sets its own)
STYLES = {}
# a piece's own files (photos, a client's fonts): key -> absolute path, written relative to the project that builds
IMAGES = {}


def own_font(k, path, family):
    """Register a font file of the piece's own (a client's typeface): text styles use it with font=k."""
    FONTS[k] = (os.path.basename(path), family, os.path.abspath(path))
    return k


def image_asset(k, path):
    """Register an image file (png, jpg, webp) as asset `img.<k>`."""
    assert os.path.exists(path), f"no image {path}"
    IMAGES[k] = os.path.abspath(path)
    return k


def text_style(k, ds_name, col, **over):
    """Register text style `k`: the DS text style `ds_name` (Headlines/He 2...) in colour `col` (ARGB). `over`
    replaces any of size, lh, weight, ls, font (a key of FONTS); ds_name None needs size and lh."""
    t = DS["textStyle"][ds_name] if ds_name else {}
    base = dict(size=t.get("size"), lh=t.get("lineHeight"), weight=t.get("weight"), ls=t.get("letterSpacing"))
    base.update({k2: v for k2, v in over.items() if v is not None})
    assert base["size"] and base["lh"], f"text style {k}: size and lh"
    STYLES[k] = dict(base, color=col)
    return k


def text(name, runs, lp=None, overflow=None, wrap=True, modifiers=(), opacity=None, align=None):
    """runs: [(style, literal or '=prop')]. lp: LayoutParticipant attrs (None: not in the flow).
    A style with dim=True gets a second fill (black, alpha keyed) over its colour: CSS brightness() on text."""
    kids = []
    if lp is not None:
        kids.append(El("LayoutParticipant", lp, name=f"{name}.lp"))
    used = []
    for st, _ in runs:
        if st not in used:
            used.append(st)
    for st in used:
        s = STYLES[st]
        font = s.get("font", "duda")
        paint = [El("Fill", {}, [El("SolidColor", {"colorValue": s["color"]}, name=f"{name}.{st}.color")],
                    name=f"{name}.{st}.fill")]
        if s.get("dim"):
            paint.append(El("Fill", {}, [El("SolidColor", {"colorValue": BLACK0}, name=f"{name}.{st}.dim")],
                            name=f"{name}.{st}.dimfill"))
        if s.get("weight") and (font == "duda" or len(FONTS[font]) > 2):   # variable fonts: the weight axis
            paint.append(El("TextStyleAxis", {"tag": 2003265652, "axisValue": s["weight"]}))
        kids.append(El("TextStylePaint", {"fontSize": s["size"], "lineHeight": s["lh"], "fontAssetId": f"@font.{font}",
                                          "letterSpacing": s.get("ls"), "familyName": FONTS[font][1],
                                          "styleName": "Regular"}, paint, name=f"{name}.{st}"))
    for i, (st, v) in enumerate(runs):
        run_kids = [bind(v[1:], key("TextValueRun", "text"))] if v.startswith("=") else []
        kids.append(El("TextValueRun", {"styleId": f"@{name}.{st}", "text": "" if run_kids else v}, run_kids,
                       name=f"{name}.run{i}"))
    kids += list(modifiers)
    attrs = {"opacity": opacity, "wrapValue": "wrap" if wrap else "noWrap", "overflowValue": overflow,
             "alignValue": align}
    if lp is None:
        attrs["sizingValue"] = "autoWidth"
    return El("Text", attrs, kids, name=name)


# ================================================================ layout
def hug(**kw):
    return dict({"layoutWidthScaleType": "hug", "layoutHeightScaleType": "hug"}, **kw)


def fill_w(**kw):
    return dict({"layoutWidthScaleType": "fill", "layoutHeightScaleType": "hug"}, **kw)


def fixed(w, h, **kw):
    return dict({"layoutWidthScaleType": "fixed", "layoutHeightScaleType": "fixed"}, w=w, h=h, **kw)


UNITS = ("padding", "margin", "gap", "positionLeft", "positionRight", "positionTop", "positionBottom", "minWidth",
         "maxWidth", "minHeight", "maxHeight")


def style(name, **kw):
    attrs = {}
    for k, v in kw.items():
        attrs[k] = v
        if k.startswith(UNITS) and not k.endswith(("UnitsValue", "TypeValue")) and f"{k}UnitsValue" not in kw:
            attrs[k + "UnitsValue"] = "points"
    return El("LayoutComponentStyle", attrs, name=f"{name}.style")


def box(name, children=(), w=0, h=0, paints=(), clip=False, opacity=None, x=None, y=None, origin=None, **st):
    """A LayoutComponent. children in flow order; for overlapping children the first one draws on top.
    paints bottom -> top."""
    kids = [style(name, **st)]
    if origin:
        kids.append(El("ComponentOrigin", {"originX": origin[0], "originY": origin[1]}))
    kids += list(paints) + [c for c in children if c is not None]
    return El("LayoutComponent", {"width": w, "height": h, "styleId": f"@{name}.style", "clip": clip,
                                  "opacity": opacity, "x": x, "y": y}, kids, name=name)


def solid(name, col):
    return El("Fill", {}, [El("SolidColor", {"colorValue": col}, name=f"{name}.color")], name=name)


def line(name, col, w=1.0):
    return El("Stroke", {"thickness": w}, [El("SolidColor", {"colorValue": col}, name=f"{name}.color")], name=name)


def absolute(name, children=(), paints=(), inset=(0, 0, 0, 0), opacity=None, origin=None, **st):
    """A box pinned to its parent's edges (left, top, right, bottom; None leaves an edge free). An axis pinned at
    both ends stretches between them only when it hugs (copilot learning)."""
    l, t, r, b = inset
    pos = {}
    for k, v in (("positionLeft", l), ("positionTop", t), ("positionRight", r), ("positionBottom", b)):
        if v is not None:
            pos[k] = v
    if l is not None and r is not None:
        st["layoutWidthScaleType"] = "hug"
    if t is not None and b is not None:
        st["layoutHeightScaleType"] = "hug"
    return box(name, children, paints=paints, opacity=opacity, origin=origin, positionTypeValue="absolute", **pos,
               **st)


def shape_rect(name, w, h, r=0, fill=None, stroke=None, stroke_w=1.0, x=0.0, y=0.0, opacity=None):
    """A rectangle centred on (x, y) inside a Node (fill / stroke: ARGB). The stroke is centred on the edge, as in
    Rive: for a DS 'inside' stroke, draw it 1 px smaller."""
    kids = [El("Rectangle", {"width": w, "height": h, "cornerRadiusTL": r or None}, name=f"{name}.rect")]
    if fill is not None:
        kids.append(solid(f"{name}.fill", fill))
    if stroke is not None:
        kids.append(line(f"{name}.stroke", stroke, stroke_w))
    return El("Shape", {"x": x, "y": y, "opacity": opacity}, kids, name=name)


def shape_ellipse(name, d, fill=None, stroke=None, stroke_w=1.0, x=0.0, y=0.0, opacity=None):
    """A circle of diameter d centred on (x, y)."""
    kids = [El("Ellipse", {"width": d, "height": d}, name=f"{name}.ellipse")]
    if fill is not None:
        kids.append(solid(f"{name}.fill", fill))
    if stroke is not None:
        kids.append(line(f"{name}.stroke", stroke, stroke_w))
    return El("Shape", {"x": x, "y": y, "opacity": opacity}, kids, name=name)


def open_path(name, pts, col, width, trim_end=1.0):
    """An open stroke through pts (a check mark, a dash), round caps, trimmed so it can draw on (`<name>.trim` end)."""
    verts = [El("StraightVertex", {"x": x, "y": y}) for x, y in pts]
    return El("Shape", {}, [
        El("PointsPath", {"isClosed": False}, verts, name=f"{name}.path"),
        El("Stroke", {"thickness": width, "cap": "round", "join": "round"}, [
            El("SolidColor", {"colorValue": col}, name=f"{name}.color"),
            El("TrimPath", {"start": 0, "end": trim_end, "offset": 0, "modeValue": 1}, name=f"{name}.trim")],
           name=f"{name}.stroke")], name=name)


def icon_slot(name, svg, col, size=16, slot=None, stroke_w=None, **st):
    """A DS icon (icons/<category>/<name>.svg) at `size`, centred in a fixed slot (a Node keeps the art as drawn).
    The DS draws on a 16 grid with a 1.5 stroke; a 12 px icon is the same drawing scaled (so its stroke scales too,
    as in Figma)."""
    slot = slot or size
    off = (slot - size) / 2
    art = icon(os.path.join(ICONS, f"{svg}.svg"), f"{name}.art", col, stroke_w=stroke_w or ICON_STROKE, x=off, y=off,
               size=size)
    return box(name, [art], w=slot, h=slot, layoutWidthScaleType="fixed", layoutHeightScaleType="fixed", **st)


def paint_names(el):
    """The SolidColor names inside an element (to key an icon's colour)."""
    out = []

    def walk_(e):
        if e.tag == "SolidColor" and e.name:
            out.append(e.name)
        for c in e.children:
            if isinstance(c, El):
                walk_(c)
    walk_(el)
    return out


def shadow_layers(name, layers, rad):
    """DS shadow layers (x, y, blur, spread, colour '#rrggbbaa') as feathered fills behind a box."""
    out = []
    for i, lay in enumerate(layers):
        n = f"{name}.s{i}"
        f = El("Fill", {"fillRule": "clockwise"}, [
            El("SolidColor", {"colorValue": hex_argb(lay["color"])}, name=f"{n}.color"),
            El("Feather", {"strength": lay["blur"], "offsetX": lay.get("x") or None, "offsetY": lay["y"]},
               name=f"{n}.feather")], name=f"{n}.fill")
        s = -lay.get("spread", 0)
        out.append(absolute(n, paints=[f], inset=(s, s, s, s), cornerRadiusTL=rad))
    return out


# ================================================================ animations
KF = {"double": "KeyFrameDouble", "Color": "KeyFrameColor", "bool": "KeyFrameBool", "uint": "KeyFrameUint",
      "uint8": "KeyFrameUint", "String": "KeyFrameString", "Id": "KeyFrameId", "callback": "KeyFrameCallback"}
ENUMS = {"flex": 0, "none": 1}   # displayValue
ANIMS = []


class Anim:
    """One timeline. Targets are element names; `prop` is looked up on the element's own tag."""

    def __init__(self, name, seconds, loop=False):
        self.name = f"{CUR.name} · {name}" if CUR else name
        self.frames, self.loop = max(1, round(seconds * FPS)), loop
        self.tracks = {}
        ANIMS.append(self)

    def key(self, target, prop, t, value, ease="hold"):
        self.tracks.setdefault((target, prop), []).append((round(t * FPS), value, ease))
        return self

    def hold(self, target, prop, value):
        return self.key(target, prop, 0, value)

    def move(self, target, prop, t0, t1, v0, v1, ease="linear"):
        self.key(target, prop, t0, v0, ease)
        return self.key(target, prop, t1, v1)

    def el(self, by_name):
        kos = {}
        for (target, prop), keys in self.tracks.items():
            el = by_name[target]
            pkey = key(el.tag, prop)
            ptype = SCHEMA["keys"][str(pkey)]["type"]
            tag = KF[ptype]
            kfs, seen = [], {}
            for f, v, ease in sorted(keys, key=lambda k: k[0]):
                seen[f] = (v, ease)   # a later key on the same frame wins
            for f, (v, ease) in sorted(seen.items()):
                attrs = {"frame": f}
                if ptype != "callback":
                    attrs["value"] = ENUMS.get(v, v) if isinstance(v, str) and ptype not in ("String", "Color") else v
                kids = []
                if tag in ("KeyFrameDouble", "KeyFrameColor"):
                    if ease in ("hold", "linear"):
                        attrs["interpolationType"] = ease
                    else:
                        attrs["interpolationType"] = "cubic"
                        e = EASE[ease]
                        kids.append(El("CubicEaseInterpolator", {"x1": e[0], "y1": e[1], "x2": e[2], "y2": e[3]}))
                kfs.append(El(tag, attrs, kids))
            kos.setdefault(target, []).append(El("KeyedProperty", {"propertyKey": pkey}, kfs))
        return El("LinearAnimation", {"fps": FPS, "duration": self.frames, "loopValue": "loop" if self.loop else None},
                  [El("KeyedObject", {"objectId": f"@{t}"}, props) for t, props in kos.items()],
                  name=self.name, ref=f"anim.{self.name}")


def pose(name, looks, which):
    """A one-frame timeline holding looks[i][which] for every (target, prop, *values)."""
    a = Anim(name, 1 / FPS)
    for t, p, *vals in looks:
        a.hold(t, p, vals[which])
    return a


# ================================================================ state machines
def _cmp(bindable, pkey, prop, path=None, converter=None):
    return El("TransitionPropertyViewModelComparator", {},
              [El(bindable, {}, [bind(prop, pkey, path=path, converter=converter)])])


def if_bool(prop, value=True, path=None):
    return El("TransitionViewModelCondition", {}, [_cmp("BindablePropertyBoolean", 634, prop, path),
                                                   El("TransitionValueBooleanComparator", {"value": value})])


def if_num(prop, op, value, path=None):
    return El("TransitionViewModelCondition", {"opValue": op}, [_cmp("BindablePropertyNumber", 636, prop, path),
                                                                El("TransitionValueNumberComparator", {"value": value})])


def if_trigger(prop, path=None):
    return El("TransitionViewModelCondition", {"opValue": 1}, [_cmp("BindablePropertyTrigger", 686, prop, path),
                                                               El("TransitionValueTriggerComparator", {})])


def if_text(prop, op, value="", converter=None, path=None):
    return El("TransitionViewModelCondition", {"opValue": op},
              [_cmp("BindablePropertyString", 635, prop, path, converter),
               El("TransitionValueStringComparator", {"value": value or None})])


def set_to(kind, prop, value, path=None):
    """An action (a listener's, or a state's as it starts): prop = value. kind: Boolean, String, Number, Color,
    Artboard (value: an artboard ref)."""
    if kind == "Artboard":
        value = f"@{value}"
    return El("ListenerViewModelChange", {}, [El(f"BindableProperty{kind}", {"propertyValue": value},
                                                 [bind(prop, BIND_KEY[kind], write=True, path=path)])])


def fire(prop, path=None):
    return El("ListenerViewModelChange", {}, [El("BindablePropertyTrigger", {}, [bind(prop, 686, write=True,
                                                                                       path=path)])])


def transition(to_ref, conds=(), ms=0, ease=None, at_end=False):
    attrs = {"stateToId": f"@{to_ref}", "duration": ms or None}
    kids = list(conds)
    if ms and ease:
        attrs["interpolationType"] = "cubic"
        e = EASE[ease]
        kids.append(El("CubicEaseInterpolator", {"x1": e[0], "y1": e[1], "x2": e[2], "y2": e[3]}))
    if at_end:
        attrs.update({"enableExitTime": True, "exitTimeIsPercetange": True, "exitTime": 100})
    return El("StateTransition", attrs, kids)


class Layer:
    def __init__(self, name):
        self.name, self.p = name, f"{CUR.key}:{name}"
        self.states, self.any, self.entry, self.entry_ifs = [], [], None, []

    def go(self, to, *conds, ms=0, ease=None, at_end=False):
        return transition(f"{self.p}.{to}", conds, ms, ease, at_end)

    def state(self, ref, anim, *transitions, entry=False, actions=()):
        """anim None: a state that only runs its actions (as it starts) and moves on."""
        x, y = 160 + 220 * (len(self.states) % 4), -120 + 140 * (len(self.states) // 4)
        attrs = {"x": x, "y": y}
        if anim:
            attrs.update({"animationId": f"@anim.{anim.name}", "reset": True})
        else:
            attrs["stateName"] = ref
        self.states.append(El("AnimationState", attrs, list(actions) + list(transitions), ref=f"{self.p}.{ref}"))
        if entry:
            self.entry = f"{self.p}.{ref}"
        return self

    def enter_if(self, to, *conds):
        """The machine starts straight in `to` when conds hold (a component placed already on, checked, open...)."""
        self.entry_ifs.append(transition(f"{self.p}.{to}", conds))
        return self

    def from_any(self, *transitions):
        self.any += transitions
        return self

    def el(self):
        return El("StateMachineLayer", {}, [
            El("EntryState", {"x": 0, "y": -120}, self.entry_ifs + [El("StateTransition",
                                                                       {"stateToId": f"@{self.entry}"})]),
            *self.states,
            El("AnyState", {"x": 0, "y": 60}, list(self.any)),
            El("ExitState", {"x": 0, "y": 200})], name=self.name, ref=f"layer.{self.p}")


def bool_layer(name, prop, looks, ms=HOVER_MS, ease="duda", ms_off=None):
    """Two resting looks, off and on, blended both ways: looks = [(target, prop, off, on)]."""
    lay = Layer(name)
    off, on = pose(f"{name} off", looks, 0), pose(f"{name} on", looks, 1)
    ms_off = ms if ms_off is None else ms_off
    return (lay.state("off", off, lay.go("on", if_bool(prop, True), ms=ms, ease=ease), entry=True)
            .state("on", on, lay.go("off", if_bool(prop, False), ms=ms_off, ease=ease))
            .enter_if("on", if_bool(prop, True)))


def match_layer(name, cases, looks, actions=None, ms=0, ease="duda"):
    """One look per case, a case being the conditions that pick it (a DS variant, or a mix of them: variant x color).
    No enums (the frame-0 trap): every case is a state, entered straight from the entry when its conditions hold, and
    every state goes to any other whose conditions hold. The cases must exclude one another.
    cases: [(state, [conditions])]; looks: [(target, prop, value for case 0, value for case 1, ...)];
    actions: {state: [actions run as the state starts]} (a view model value the look needs, such as an icon colour)."""
    lay = Layer(name)
    actions = actions or {}
    for i, (st, _) in enumerate(cases):
        others = [lay.go(o, *copy.deepcopy(conds), ms=ms, ease=ease if ms else None)
                  for j, (o, conds) in enumerate(cases) if j != i]
        lay.state(st, pose(f"{name} {st}", looks, i), *others, entry=i == 0, actions=actions.get(st, ()))
        if i:
            lay.enter_if(st, *copy.deepcopy(cases[i][1]))
    return lay


def choice_layer(name, prop, options, looks, actions=None, ms=0, ease="duda"):
    """A number property choosing one of len(options) looks (a DS variant: size, color...)."""
    return match_layer(name, [(o, [if_num(prop, "equal", i)]) for i, o in enumerate(options)], looks, actions, ms,
                       ease)


def gate_layer(hits, extra_off=()):
    """Interactive: the hit boxes (and the listeners on them) exist only with `interactive` on and `disabled` off.
    A piece leaves `interactive` off, so a visitor's mouse never changes it."""
    looks = [(f"{h}.style", "displayValue", "none", "flex") for h in hits] + list(extra_off)
    lay = Layer("Interactive")
    has_disabled = any(n == "disabled" for n, _, _ in CUR.props)
    dis = [if_bool("disabled", False)] if has_disabled else []
    lay.state("off", pose("Interactive off", looks, 0),
              lay.go("on", if_bool("interactive", True), *dis), entry=True)
    lay.state("on", pose("Interactive on", looks, 1), lay.go("off", if_bool("interactive", False)),
              *([lay.go("off", if_bool("disabled", True))] if has_disabled else []))
    return lay.enter_if("on", if_bool("interactive", True), *([if_bool("disabled", False)] if has_disabled else []))


def swap_layer(name, on, offs, leave=(), arrive=()):
    """One state at a time (MOTION.md, State swaps): turning on, what `leave`s fades out in SWAP (0.1 s) and what
    `arrive`s starts on its last visible frame; turning off runs the other way. Never both on screen.
    on: the conditions (all) that turn it on; offs: a list of condition lists, any of which turns it off.
    leave / arrive: [(target, prop, value when off, value when on[, ease])] (ease defaults to linear)."""
    lay = Layer(name)
    lead = (round(SWAP * FPS) - 1) / FPS     # the outgoing state's last visible frame
    looks = [(t, p, a, b) for t, p, a, b, *_ in list(leave) + list(arrive)]

    def anim(nm, first, then, forward):
        a = Anim(f"{name} {nm}", lead + SWAP)
        for group, t0 in ((first, 0.0), (then, lead)):
            for t, p, off, onv, *e in group:
                v0, v1 = (off, onv) if forward else (onv, off)
                a.key(t, p, 0, v0)
                a.move(t, p, t0, t0 + SWAP, v0, v1, e[0] if e else "linear")
        return a
    a_in, a_out = anim("in", leave, arrive, True), anim("out", arrive, leave, False)
    ms = round(SWAP * 1000)
    lay.state("off", pose(f"{name} off", looks, 0), lay.go("in", *copy.deepcopy(on)), entry=True)
    lay.state("in", a_in, lay.go("on", at_end=True), *[lay.go("out", *copy.deepcopy(c), ms=ms) for c in offs])
    lay.state("on", pose(f"{name} on", looks, 1), *[lay.go("out", *copy.deepcopy(c)) for c in offs])
    lay.state("out", a_out, lay.go("off", at_end=True), lay.go("in", *copy.deepcopy(on), ms=ms))
    return lay.enter_if("on", *copy.deepcopy(on))


def spin_layer(target, period=0.8):
    """A spinner that always turns (one turn per `period`), so a loading state can fade it in and out without a jump
    in its angle."""
    lay = Layer("Spin")
    a = Anim("Spin", period, loop=True)
    a.move(target, "rotation", 0, period, 0, 6.2832)
    return lay.state("turn", a, entry=True)


def tick():
    """An empty one-frame timeline: an action state waits on it so a trigger is not seen twice."""
    return Anim("tick", 1 / FPS)


LISTENERS = [0]


def listener(target, kind, *actions, name=None):
    LISTENERS[0] += 1
    return El("StateMachineListenerSingle", {"targetId": f"@{target}", "listenerTypeValue": kind}, list(actions),
              name=name or f"{kind} {target}", ref=f"listener.{LISTENERS[0]}")


def hover_listeners(target, prop="hover", press=None):
    out = [listener(target, "enter", set_to("Boolean", prop, True), name=f"{prop} in"),
           listener(target, "exit", set_to("Boolean", prop, False),
                    *([set_to("Boolean", press, False)] if press else []), name=f"{prop} out")]
    if press:
        out += [listener(target, "down", set_to("Boolean", press, True), name="press"),
                listener(target, "up", set_to("Boolean", press, False), name="release")]
    return out


def machine(layers, listeners=()):
    return El("StateMachine", {}, [lay.el() for lay in layers] + list(listeners), name="State Machine 1",
              ref=f"sm.{CUR.key}")


def press_layer(target, scale, prop="pressed", trigger="click"):
    """Press: in fast (press token, strong), back softly (release, duda); `trigger` plays a whole press (for a
    timeline or a piece's script)."""
    looks = [(target, "scaleX", 1, scale), (target, "scaleY", 1, scale)]
    lay = Layer("Press")
    click = Anim("Press click", 0.4)
    for p in ("scaleX", "scaleY"):
        click.move(target, p, 0, PRESS, 1, scale, "strong").key(target, p, 0.1, scale, "duda").key(target, p, 0.4, 1)
    lay.state("up", pose("Press up", looks, 0), lay.go("down", if_bool(prop, True), ms=round(PRESS * 1000),
                                                       ease="strong"),
              lay.go("click", if_trigger(trigger)), entry=True)
    lay.state("down", pose("Press down", looks, 1), lay.go("up", if_bool(prop, False), ms=RELEASE_MS, ease="duda"))
    lay.state("click", click, lay.go("up", at_end=True), lay.go("click2", if_trigger(trigger)))
    lay.state("click2", click, lay.go("up", at_end=True), lay.go("click", if_trigger(trigger)))
    return lay


# ================================================================ artboards
COMPONENTS = []        # (artboard El, vm) in build order
ART_POS = {"x": 0, "y": -1400}


def component(art_name, w, h, kids, sm, size_props=(), layout=None, gap=120):
    """A component artboard bound to the current view model (its own "State Machine 1"); `size_props` bind the
    artboard's width/height to the view model properties of the same name."""
    binds = [bind(p, key("Artboard", p)) for p in size_props]
    x = ART_POS["x"]
    ART_POS["x"] += max(w, 120) + gap
    st = style(f"{art_name}Art", **(layout or {}))
    art = El("Artboard", {"isComponent": True, "defaultStateMachineId": f"@sm.{CUR.key}",
                          "viewModelId": f"@{CUR.ref()}", "viewModelInstanceId": f"@vmi.{CUR.key}",
                          "styleId": f"@{art_name}Art.style", "width": w, "height": h, "clip": False,
                          "x": x, "y": ART_POS["y"]},
             [st, El("FocusData", {"canFocus": False})] + binds + list(kids) + [sm], name=art_name,
             ref=f"art.{CUR.key}")
    COMPONENTS.append((art, CUR))
    return art


def nested(name, comp, path, w="fill", h="fill", sm=True):
    """A component placed in a layout: its data is the view model instance at `path` (host view model, property).
    w / h: a number (points), "fill" (the room the layout gives it) or "hug" (its own content)."""
    attrs = {"artboardId": f"@art.{comp}", "dataBindPathIds": path}
    for axis, v in (("Width", w), ("Height", h)):
        num = isinstance(v, (int, float))
        attrs[f"instance{axis}"] = v if num else 100
        attrs[f"instance{axis}UnitsValue"] = "percent" if v == "fill" else "points"
        attrs[f"instance{axis}ScaleType"] = "fixed" if num else v
    kids = [El("NestedStateMachine", {"animationId": f"@sm.{comp}"}, name=f"{name} machine")] if sm else []
    return El("NestedArtboardLayout", attrs, kids, name=name)


def host_artboard(vm, name, w, h, kids, sm, x, y, bg=None):
    """A top-level artboard (not a component) bound to its own host view model (one host VM per artboard: outside
    the editor every artboard uses its view model's default instance)."""
    return El("Artboard", {"defaultStateMachineId": f"@sm.{vm.key}", "viewModelId": f"@{vm.ref()}",
                           "viewModelInstanceId": f"@vmi.{vm.key}", "styleId": f"@{name}Art.style",
                           "width": w, "height": h, "clip": True, "x": x, "y": y},
              [style(f"{name}Art"), solid(f"{name}Art.fill", bg or WHITE), El("FocusData", {"canFocus": False})]
              + list(kids) + [sm], name=name, ref=f"art.{vm.key}")


def bind_style(el, attr, prop, converter=None):
    """Bind a layout style value of box `el` (minWidth, gap...) to `prop` of the current view model."""
    st = next(c for c in el.children if isinstance(c, El) and c.tag == "LayoutComponentStyle")
    st.children.append(bind(prop, key("LayoutComponentStyle", attr), converter))
    return el


# ================================================================ icons as components (Figma's instance swap)
# Every DS icon is a tiny component artboard, "Icon/<DS name>", bound to the "Icon" view model (its colour). A
# component that shows an icon places one with nested_icon(): which icon comes from an artboard property of its view
# model, and the colour from a colour property. Tested in the CLI and in @rive-app/webgl2 2.45.0 (feature_tests.py).
ICON = VM("icon", "Icon", [("color", "color", color("Icons/icon-dark-color"))])
ICON_FILES = {}   # DS name -> "category/name" (the svg under icons/)
for _cat in sorted(os.listdir(ICONS)):
    if os.path.isdir(os.path.join(ICONS, _cat)):
        for _f in sorted(os.listdir(os.path.join(ICONS, _cat))):
            if _f.endswith(".svg"):
                ICON_FILES[_f[:-4]] = f"{_cat}/{_f[:-4]}"


def icon_ref(name):
    assert name in ICON_FILES, f"no icon {name!r} in icons/"
    return f"art.icon.{name}"


def icon_artboards():
    """One 16x16 component artboard per DS icon, every paint bound to Icon.color. No state machine: nothing in an
    icon moves on its own (its parent animates the placement)."""
    arts = []
    use(ICON)
    for i, (n, svg) in enumerate(ICON_FILES.items()):
        art = icon(os.path.join(ICONS, f"{svg}.svg"), f"Icon.{n}.art", ICON.props[0][2], stroke_w=ICON_STROKE, size=16)
        walk(art, lambda e: e.children.append(bind("color", key("SolidColor", "colorValue")))
             if e.tag == "SolidColor" else None)
        arts.append(El("Artboard", {"isComponent": True, "viewModelId": f"@{ICON.ref()}",
                                    "viewModelInstanceId": f"@vmi.{ICON.key}", "styleId": f"@Icon.{n}Art.style",
                                    "width": 16, "height": 16, "clip": False,
                                    "x": (i % 12) * 40, "y": -1600 - (i // 12) * 40},
                       [style(f"Icon.{n}Art"), art], name=f"Icon/{n}", ref=icon_ref(n)))
    return arts


def nested_icon(name, art_prop, color_prop, default, size=16):
    """A DS icon placed by data: the icon is the artboard in `art_prop` (an artboard property of the current view
    model) and its colour follows `color_prop` (a colour property of the same view model). `size` 12 draws the 16 px
    icon at 0.75, as Figma scales a 16 px icon into a 12 px slot (its stroke too)."""
    # exported: a stateful placement's own instance is dropped at export otherwise (rive inspect)
    tint = El("ViewModelInstance", {"viewModelId": f"@{ICON.ref()}", "exports": True}, [
        El("ViewModelInstanceColor", {"viewModelPropertyId": f"@{ICON.ref('color')}",
                                      "propertyValue": ICON.props[0][2]},
           [El("DataBindContext", {"sourcePathIds": (CUR.ref(), CUR.ref(color_prop)),
                                   "propertyKey": VALUE_KEY["Color"]})], name=f"{name}.tint")],
        name=f"{name}.data")
    nest = El("NestedArtboardLayout", {"artboardId": f"@{icon_ref(default)}", "isStateful": True, "instanceWidth": 16,
                                       "instanceHeight": 16, "instanceWidthScaleType": "fixed",
                                       "instanceHeightScaleType": "fixed"},
              [El("DataBindContext", {"sourcePathIds": (CUR.ref(), CUR.ref(art_prop)),
                                      "propertyKey": key("NestedArtboard", "artboardId")}), tint], name=name)
    if size == 16:
        return box(f"{name}.slot", [nest], **fixed(16, 16))
    inner = box(f"{name}.scale", [nest], origin=(0, 0), positionTypeValue="absolute", positionLeft=0, positionTop=0,
                **fixed(16, 16))
    inner.attrs.update({"scaleX": size / 16, "scaleY": size / 16})
    return box(f"{name}.slot", [inner], **fixed(size, size))


# ================================================================ output
def walk(el, fn):
    fn(el)
    for c in el.children:
        if isinstance(c, El):
            walk(c, fn)


def _anim_home(anim, arts):
    """The artboard whose state machine plays `anim`."""
    for art in arts:
        found = []
        walk(art, lambda e: found.append(1) if e.tag == "AnimationState" and
             e.attrs.get("animationId") == f"@anim.{anim.name}" else None)
        if found:
            return art
    return None


def assemble(artboards, vms, client="0", converters=True, namespace="", external=None, base=None):
    """The RML for `artboards` (component artboards get their ComponentAsset) and the view models `vms` (keys),
    with every timeline placed in the artboard that holds its targets. Works on copies, so the same elements can be
    assembled twice (the library scene and a dist bundle). Returns (xml, doc).
    For a project of several .rml files (one document): `client` numbers this file's ids ("2" -> 2:1, 2:2...),
    `namespace` prefixes the names the editor lists (artboards, component assets, view models: "Library / "), and
    `external` = {name or ref: id} lets "@name" references point at elements another .rml of the same project
    defines (an id such as "1:42"). `base`: the folder the RML is written to (a piece's own images and fonts are
    written relative to it; default the working folder)."""
    arts = copy.deepcopy(artboards)
    vm_els = [VM.all[k].el() for k in vms]
    base = base or os.getcwd()

    def font_file(f, own=None):
        return os.path.relpath(own, base) if own else f"{FONT_DIR[0]}/{f}"
    fonts = [El("FontAsset", {"file": font_file(*v[:1], *v[2:])}, name=v[1], ref=f"font.{k}") for k, v in FONTS.items()]
    fonts += [El("ImageAsset", {"file": os.path.relpath(p, base)}, name=f"img.{k}") for k, p in IMAGES.items()]
    assets = [El("ComponentAsset", {"artboardId": f"@{a.ref}"}, name=a.name) for a in arts
              if a.attrs.get("isComponent")]
    convs = copy.deepcopy(CONVERTERS) if converters else []
    root = El("Rive", {"version": 1, "kind": "fragment"}, fonts + convs + vm_els + arts + assets)
    by = {}
    walk(root, lambda e: by.__setitem__(e.ref or e.name, e) if (e.ref or e.name) else None)
    owner = {}
    for art in arts:
        walk(art, lambda e, a=art: owner.__setitem__(e.ref or e.name, a) if (e.ref or e.name) else None)
    for a in ANIMS:
        targets = [t for t, _ in a.tracks]
        art = owner.get(targets[0]) if targets else _anim_home(a, arts)
        if art is None:
            continue   # a timeline of an artboard that is not in this document
        art.children.append(a.el(by))
    doc = Doc(client)
    doc.assign(root)
    for n, i in (external or {}).items():   # elements of another .rml in the same project (what is defined here wins)
        doc.by_name.setdefault(n, type("External", (), {"id": i, "name": n})())

    def paths(e):
        for k in ("sourcePathIds", "dataBindPathIds"):
            v = e.attrs.get(k)
            if isinstance(v, tuple):
                e.attrs[k] = "-".join(doc.by_name[n].id for n in v)
    walk(root, paths)
    doc.resolve(root)
    if namespace:   # after resolve: references are ids by now, so renaming cannot break them
        walk(root, lambda e: setattr(e, "name", namespace + e.name) if e.name and e.tag in (
            "Artboard", "ComponentAsset", "ViewModel") else None)
    return doc.xml(root), doc


# ================================================================ icons (pecas/ui-controls/icons.py, as is)
# SVG -> RML Node of native vector shapes. Reads relative commands, arcs, smooth curves, <circle>/<rect>, round caps
# and joins; every path is normalised to absolute M/L/C/Z before svg2rml.
NS = "{http://www.w3.org/2000/svg}"
TOK = re.compile(r"[MmLlHhVvCcSsQqTtAaZz]|[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")


def _arc_to_cubics(p0, rx, ry, phi, large, sweep, p1):
    """SVG elliptical arc -> list of cubic segments (c1, c2, end), the standard endpoint-to-centre conversion."""
    if p0 == p1:
        return []
    if rx == 0 or ry == 0:
        return [(p0, p1, p1)]
    rx, ry = abs(rx), abs(ry)
    cp, sp = math.cos(math.radians(phi)), math.sin(math.radians(phi))
    dx, dy = (p0[0] - p1[0]) / 2, (p0[1] - p1[1]) / 2
    x1, y1 = cp * dx + sp * dy, -sp * dx + cp * dy
    lam = x1 * x1 / (rx * rx) + y1 * y1 / (ry * ry)
    if lam > 1:
        rx, ry = rx * math.sqrt(lam), ry * math.sqrt(lam)
    num = rx * rx * ry * ry - rx * rx * y1 * y1 - ry * ry * x1 * x1
    den = rx * rx * y1 * y1 + ry * ry * x1 * x1
    co = math.sqrt(max(0.0, num / den)) * (-1 if large == sweep else 1)
    cx1, cy1 = co * rx * y1 / ry, -co * ry * x1 / rx
    cx = cp * cx1 - sp * cy1 + (p0[0] + p1[0]) / 2
    cy = sp * cx1 + cp * cy1 + (p0[1] + p1[1]) / 2

    def ang(ux, uy, vx, vy):
        a = math.atan2(ux * vy - uy * vx, ux * vx + uy * vy)
        return a
    t1 = ang(1, 0, (x1 - cx1) / rx, (y1 - cy1) / ry)
    dt = ang((x1 - cx1) / rx, (y1 - cy1) / ry, (-x1 - cx1) / rx, (-y1 - cy1) / ry)
    if not sweep and dt > 0:
        dt -= 2 * math.pi
    elif sweep and dt < 0:
        dt += 2 * math.pi
    n = max(1, math.ceil(abs(dt) / (math.pi / 2) - 1e-9))
    d = dt / n
    k = 4 / 3 * math.tan(d / 4)
    out = []

    def pt(t):
        x, y = rx * math.cos(t), ry * math.sin(t)
        return (cp * x - sp * y + cx, sp * x + cp * y + cy)

    def deriv(t):
        x, y = -rx * math.sin(t), ry * math.cos(t)
        return (cp * x - sp * y, sp * x + cp * y)
    for i in range(n):
        a, b = t1 + i * d, t1 + (i + 1) * d
        pa, pb, da, db = pt(a), pt(b), deriv(a), deriv(b)
        out.append(((pa[0] + k * da[0], pa[1] + k * da[1]), (pb[0] - k * db[0], pb[1] - k * db[1]), pb))
    out[-1] = (out[-1][0], out[-1][1], p1)
    return out


def parse_path(d):
    """Any SVG path -> subpaths in svg2rml's format: {'segs': [('M', p) | ('L', p) | ('C', c1, c2, p)], 'closed'}."""
    toks = TOK.findall(d)
    i, cmd = 0, None
    pos = start = (0.0, 0.0)
    last_c2 = last_q = None
    subs, cur = [], None

    def num():
        nonlocal i
        v = float(toks[i])
        i += 1
        return v

    def flag():
        # arc flags may be written without separators ("a.5.5 0 01 1 1"): take one digit at a time
        nonlocal i
        t = toks[i]
        if len(t) > 1 and t[0] in "01" and not t.startswith(("0.", "1.")):
            toks[i] = t[1:]
            return int(t[0])
        i += 1
        return int(float(t))

    while i < len(toks):
        if re.match(r"[A-Za-z]", toks[i]):
            cmd = toks[i]
            i += 1
            if cmd in "Zz":
                if cur:
                    cur["closed"] = True
                pos = start
                last_c2 = last_q = None
                continue
        rel, c = cmd.islower(), cmd.upper()

        def P(x, y):
            return (pos[0] + x, pos[1] + y) if rel else (x, y)
        if c == "M":
            pos = start = P(num(), num())
            cur = {"segs": [("M", pos)], "closed": False}
            subs.append(cur)
            cmd = "l" if rel else "L"
            last_c2 = last_q = None
            continue
        if cur is None or cur["closed"]:
            # drawing after Z continues from the subpath's start
            cur = {"segs": [("M", pos)], "closed": False}
            subs.append(cur)
        if c == "L":
            p = P(num(), num())
            cur["segs"].append(("L", p))
            last_c2 = last_q = None
        elif c == "H":
            x = num()
            p = (pos[0] + x if rel else x, pos[1])
            cur["segs"].append(("L", p))
            last_c2 = last_q = None
        elif c == "V":
            y = num()
            p = (pos[0], pos[1] + y if rel else y)
            cur["segs"].append(("L", p))
            last_c2 = last_q = None
        elif c == "C":
            c1, c2, p = P(num(), num()), P(num(), num()), P(num(), num())
            cur["segs"].append(("C", c1, c2, p))
            last_c2, last_q = c2, None
        elif c == "S":
            c1 = (2 * pos[0] - last_c2[0], 2 * pos[1] - last_c2[1]) if last_c2 else pos
            c2, p = P(num(), num()), P(num(), num())
            cur["segs"].append(("C", c1, c2, p))
            last_c2, last_q = c2, None
        elif c in "QT":
            if c == "Q":
                q = P(num(), num())
            else:
                q = (2 * pos[0] - last_q[0], 2 * pos[1] - last_q[1]) if last_q else pos
            p = P(num(), num())
            c1 = (pos[0] + 2 / 3 * (q[0] - pos[0]), pos[1] + 2 / 3 * (q[1] - pos[1]))
            c2 = (p[0] + 2 / 3 * (q[0] - p[0]), p[1] + 2 / 3 * (q[1] - p[1]))
            cur["segs"].append(("C", c1, c2, p))
            last_q, last_c2 = q, None
        elif c == "A":
            rx, ry, phi = num(), num(), num()
            large, sweep = flag(), flag()
            p = P(num(), num())
            for c1, c2, e in _arc_to_cubics(pos, rx, ry, phi, large, sweep, p):
                cur["segs"].append(("C", c1, c2, e))
            last_c2 = last_q = None
        pos = cur["segs"][-1][-1]
    return subs


def _ellipse_d(cx, cy, rx, ry):
    return (f"M{cx - rx} {cy}A{rx} {ry} 0 1 0 {cx + rx} {cy}A{rx} {ry} 0 1 0 {cx - rx} {cy}Z")


def _rect_d(x, y, w, h, rx):
    if not rx:
        return f"M{x} {y}H{x + w}V{y + h}H{x}Z"
    return (f"M{x + rx} {y}H{x + w - rx}A{rx} {rx} 0 0 1 {x + w} {y + rx}V{y + h - rx}A{rx} {rx} 0 0 1 {x + w - rx} {y + h}"
            f"H{x + rx}A{rx} {rx} 0 0 1 {x} {y + h - rx}V{y + rx}A{rx} {rx} 0 0 1 {x + rx} {y}Z")


def _num_attr(v, default):
    if v is None:
        return default
    m = re.search(r"var\(--d-icon-stroke-width,\s*([\d.]+)\)", v)
    if m:
        return None   # the CSS variable: the caller's stroke width
    return float(v)


def _svg_color(v):
    """An SVG colour as '#rrggbb': names (white, black) and the short #rgb form too."""
    v = {"white": "#ffffff", "black": "#000000"}.get(v.strip().lower(), v.strip())
    if len(v) == 4 and v.startswith("#"):
        v = "#" + "".join(ch * 2 for ch in v[1:])
    return v


def icon(path, name, color, stroke_w=1.25, x=0.0, y=0.0, size=None):
    """The icon at its viewBox size (or scaled to `size`), top-left at (x, y), every paint in `color` (ARGB) unless
    the SVG paints with its own colour or gradient. Returns a Node."""
    root = ET.parse(path).getroot()
    vb = [float(v) for v in root.get("viewBox").split()]
    scale = (size / vb[2]) if size else 1.0
    grads = {}
    for g in root.iter(NS + "linearGradient"):
        stops = [(argb(_svg_color(s.get("stop-color", "#000000")), float(s.get("stop-opacity", "1"))),
                  float(s.get("offset", "0"))) for s in g.findall(NS + "stop")]
        grads[g.get("id")] = (tuple(float(g.get(k, "0")) for k in ("x1", "y1", "x2", "y2")), stops)
    for g in root.iter(NS + "radialGradient"):   # drawn round: an elliptical one takes its mean radius
        stops = [(argb(_svg_color(s.get("stop-color", "#000000")), float(s.get("stop-opacity", "1"))),
                  float(s.get("offset", "0"))) for s in g.findall(NS + "stop")]
        cx, cy, r = (float(g.get(k, d)) for k, d in (("cx", "0.5"), ("cy", "0.5"), ("r", "0.5")))
        m = [float(v) for v in re.findall(r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?",
                                          g.get("gradientTransform", "matrix(1 0 0 1 0 0)"))]
        a, b, c, d, e, f = m if len(m) == 6 else (1, 0, 0, 1, 0, 0)
        ox, oy = a * cx + c * cy + e, b * cx + d * cy + f
        rad = r * (math.hypot(a, b) + math.hypot(c, d)) / 2
        grads[g.get("id")] = ((ox, oy, ox + rad, oy), stops, "radial")
    skip = set()
    for m in root.iter():
        if m.tag in (NS + "defs", NS + "mask", NS + "clipPath") or m.get("filter"):
            skip.update(m.iter())
    inherited_fill = root.get("fill")
    shapes, n = [], 0
    for el in root.iter():
        if el in skip:
            continue
        tag = el.tag[len(NS):]
        if tag == "path":
            d = el.get("d")
        elif tag == "rect":
            d = _rect_d(float(el.get("x", 0)), float(el.get("y", 0)), float(el.get("width")), float(el.get("height")),
                        float(el.get("rx", 0)))
        elif tag == "circle":
            r = float(el.get("r"))
            d = _ellipse_d(float(el.get("cx", 0)), float(el.get("cy", 0)), r, r)
        elif tag == "ellipse":
            d = _ellipse_d(float(el.get("cx", 0)), float(el.get("cy", 0)), float(el.get("rx")), float(el.get("ry")))
        else:
            continue
        n += 1
        sname = f"{name}.p{n}"
        paths = [points_path(f"{sname}.sub{j}", to_vertices(sp), closed=sp["closed"]) for j, sp in enumerate(parse_path(d))]
        paints = []
        f = el.get("fill", inherited_fill if tag != "path" or el.get("stroke") is None else el.get("fill"))
        if f is None and el.get("stroke") is None:
            f = "currentColor"
        rule = "evenOdd" if el.get("fill-rule") == "evenodd" else None
        if f and f.startswith("url(#"):
            if f[5:-1] not in grads:     # a paint this reader doesn't know (a pattern): leave the shape out
                continue
            (x1, y1, x2, y2), stops, *kind = grads[f[5:-1]]
            g = El("RadialGradient" if kind else "LinearGradient", {"startX": x1, "startY": y1, "endX": x2, "endY": y2},
                   [El("GradientStop", {"colorValue": c, "position": o}) for c, o in stops])
            paints.append(El("Fill", {"fillRule": rule}, [g], name=f"{sname}.fill"))
        elif f and f != "none":
            c = color if f == "currentColor" else argb(_svg_color(f), float(el.get("fill-opacity", "1")))
            paints.append(El("Fill", {"fillRule": rule}, [El("SolidColor", {"colorValue": c}, name=f"{sname}.fc")],
                             name=f"{sname}.fill"))
        s = el.get("stroke")
        if s and s != "none":
            w = _num_attr(el.get("stroke-width"), 1.0)
            w = stroke_w if w is None else w
            if s.startswith("url(#") and s[5:-1] in grads:    # a gradient stroke (the Loader's arc)
                (x1, y1, x2, y2), stops = grads[s[5:-1]]
                sp = El("LinearGradient", {"startX": x1, "startY": y1, "endX": x2, "endY": y2},
                        [El("GradientStop", {"colorValue": c, "position": o}) for c, o in stops])
            else:
                sp = El("SolidColor", {"colorValue": color if s == "currentColor" else argb(_svg_color(s))},
                        name=f"{sname}.sc")
            paints.append(El("Stroke", {"thickness": w, "cap": el.get("stroke-linecap"), "join": el.get("stroke-linejoin")},
                             [sp], name=f"{sname}.stroke"))
        shapes.append(El("Shape", {"x": 0, "y": 0}, paths + paints, name=sname))
    attrs = {"x": x - vb[0] * scale, "y": y - vb[1] * scale}
    if scale != 1.0:
        attrs.update({"scaleX": scale, "scaleY": scale})
    return El("Node", attrs, shapes, name=name, order="layers")
