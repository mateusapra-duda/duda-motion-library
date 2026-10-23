"""piece.py: a library piece in a few lines. Place components, lay them out, script the cursor and the states with
ready-made actions, and build: "State Machine 1" with `play` (restart) and, for a hero tab, `tabChange`.
QUICKSTART.md is the whole manual; this file is the implementation.

How it works (the "drivers" pattern): the piece has ONE timeline. The cursor, entrances and reflows are keyed on
elements of the piece; a component's state (hover, pressed, focused, typed, loading, a message...) is keyed on a
driver, a custom property of the piece (`drv.<slot>.<prop>`, card "Drivers" on the artboard) bound into the
component's view model through the piece's view model. Drivers work with autoBind on the web (2.45.0), and the motion
designer sees and edits every state change as a key on the same timeline.

The actions sit on the kit's choreography (tools/choreo.py, tools/cursorpath.py, motion-spec tokens), so the cursor
paths, typing pattern, press timing and the speed limits come from there, and the kit's lints run on every build.
Positions for the cursor come from a measure pass: the CLI lays the scene out and reports every placement's bounds
(semantics), at the state the scene is in at that moment (a removed tag reflows the row).
"""
import copy
import hashlib
import json
import math
import os
import random
import shutil
import subprocess
import sys

import kit
from kit import El
import library
from components.icon_button import IB
from components.core_button import CB
from components.divider import DIV
from components.smart_tag import TAG
from components.core_input import CI, TYPED_ALL, MSG_ROOM
from components.cursor import CURSOR
from components import floating_bar as fb
import choreo
from choreo import Choreo, frame, progress
from cursorpath import Visit

RIVE = os.path.expanduser("~/.rive/bin/rive")
FPS = kit.FPS
TOK = choreo.TOKENS
LEAD = TOK["cursor"]["press_lead_frames"] / FPS      # a press starts this long before the cursor stops
HOVER_LEAD = TOK["cursor"]["hover_lead_ms"] / 1000   # hover comes on this long before the press
SWAP = kit.SWAP                                       # one state at a time: the outgoing state's fade
DRIVER = {"boolean": ("CustomPropertyBoolean", 245), "number": ("CustomPropertyNumber", 243),
          "string": ("CustomPropertyString", 246), "color": ("CustomPropertyColor", 836)}
STEP = {"tight": TOK["stagger"]["tight"] / 1000, "list": TOK["stagger"]["list"] / 1000,
        "loose": TOK["stagger"]["loose"] / 1000}


def secs(v):
    """Seconds, from a number or a duration token name (motion-spec tokens: press, release, fade, short, medium,
    panel, long, transition, gradient_sweep, read_hold)."""
    if isinstance(v, str):
        assert v in kit.DUR, f"{v!r} is not a duration token ({', '.join(kit.DUR)})"
        return kit.DUR[v]
    return v


class Item:
    """Something placed in the piece: a component (vm set) or a box / text (vm None). `wrap` is the layout box the
    piece animates (entrances, removal); `path` leads from the piece's view model to the component's."""

    def __init__(self, piece, key, kind, wrap, vm=None, path=None, inst=None, parent=None):
        self.p, self.key, self.kind, self.wrap = piece, key, kind, wrap
        self.vm, self.path, self.inst, self.parent = vm, path, inst, parent

    @property
    def name(self):
        return self.wrap.name if self.wrap is not None else self.parent.name

    def part(self, name):
        """A part of a floating bar (edit, up, down, duplicate, padding, trash, dismiss), as a target."""
        assert self.kind == "bar", "only a bar has parts"
        vm = dict(fb.PARTS)[name]
        return Item(self.p, f"{self.key}.{name}", "part", None, vm, self.path + (fb.BAR.ref(name),),
                    self.p.bar_parts[self.key][name], parent=self)

    def value(self, prop):
        """The placement's own value of `prop` (or the view model default)."""
        return self.inst[2].get(prop, next(d for n, _, d in self.vm.props if n == prop))

    def __repr__(self):
        return f"<{self.kind} {self.key}>"


def _el(x):
    return x.wrap if isinstance(x, Item) else x


class Piece:
    def __init__(self, name="MAIN", w=1340, h=638, bg="#FFFFFF", here=None, cursor_scale=1.0):
        """One artboard `name` (w x h) with its own view model; bg: a '#rrggbb' or a DS colour token name."""
        self.here = here or os.path.dirname(os.path.abspath(sys.argv[0]))
        self.art, self.w, self.h, self.key = name, w, h, name.lower()
        self.bg = kit.hex_argb(bg) if bg.startswith("#") else kit.color(bg)
        self.cursor_scale = cursor_scale
        kit.FONT_DIR[0] = os.path.relpath(os.path.join(kit.HERE, "fonts"), self.here)
        self.icons, self.comps = library.library()
        self.props, self.items, self.bar_parts = [], {}, {}
        self.root, self.a = None, None
        self._measured = {}

    # ------------------------------------------------------------ placing components
    def _place(self, slot, kind, vm, comp, values, w="hug", h="hug", origin=None):
        assert slot not in self.items, f"slot {slot!r} is used twice"
        values = {k: kit.icon_ref(v) if vm.kind(k) == "artboard" and v and not v.startswith("art.") else v
                  for k, v in values.items()}
        ref = vm.inst(f"vmi.{vm.key}.{self.key}.{slot}", values, name=f"{self.art} {slot}")
        self.props.append((slot, f"vm:{vm.key}", ref))
        path = (f"vm.{self.key}", f"vm.{self.key}.{slot}")
        nest = kit.nested(f"{self.art}.{slot}.c", comp, path, "fill" if w != "hug" else "hug",
                          "fill" if h != "hug" else "hug")
        size = {}
        for ax, v in (("Width", w), ("Height", h)):
            size[f"layout{ax}ScaleType"] = "fixed" if isinstance(v, (int, float)) else v
        wrap = kit.box(f"{self.art}.{slot}", [nest], w=w if isinstance(w, (int, float)) else 0,
                       h=h if isinstance(h, (int, float)) else 0, origin=origin, marginRight=0, **size)
        item = Item(self, slot, kind, wrap, vm, path, vm.instances[-1])
        self.items[slot] = item
        return item

    def button(self, slot, **props):
        """CoreButton. props: label, variant (0 Primary, 1 Secondary, 2 Text), size, color, showLeftIcon,
        leftIcon ("i_plus"), showRightIcon, rightIcon, minWidth, and any state."""
        return self._place(slot, "button", CB, "cb", props)

    def icon_button(self, slot, **props):
        """Icon button. props: icon ("i_send"), variant (0 Icon, 1 Box), size (0 Small 24, 1 Large 32), color..."""
        return self._place(slot, "ib", IB, "ib", props)

    def input(self, slot, w=320, **props):
        """CoreInput, `w` points wide. props: label, showLabel, placeholder, value, message, showMessage, theme,
        size, and the states (focused, error, success, warning, readOnly, disabled)."""
        return self._place(slot, "input", CI, "ci", props, w=w)

    def tag(self, slot, **props):
        """Smart_Tag. props: label, size (0 Small 20, 1 Regular 26), radius, color (0 Grey, 1 White, 2 Primary),
        prefix, prefixIcon, removeButton, border."""
        return self._place(slot, "tag", TAG, "tag", props, origin=(0.5, 0.5))

    def divider(self, slot, w=240, **props):
        """Divider: variant 0 With text (label), 1 No text, 2 Vertical (give h instead of w)."""
        vertical = props.get("variant") == 2
        return self._place(slot, "divider", DIV, "div", props, w=1 if vertical else w,
                           h=props.pop("h", 24) if vertical else 18)

    def bar(self, slot, **props):
        """VibeFloatingBar (open, and per part: over={"trash": {"hover": True}}). Its parts are targets:
        bar.part("trash")."""
        assert slot not in self.items
        over = props.pop("over", None)
        ref = fb.instance(f"vmi.bar.{self.key}.{slot}", f"{self.art} {slot}", False, over, **props)
        self.props.append((slot, "vm:bar", ref))
        path = (f"vm.{self.key}", f"vm.{self.key}.{slot}")
        nest = kit.nested(f"{self.art}.{slot}.c", "bar", path, "hug", "hug")
        wrap = kit.box(f"{self.art}.{slot}", [nest], marginRight=0, **kit.hug())
        inst = fb.BAR.instances[-1]
        self.bar_parts[slot] = {p: next(i for i in vm.instances if i[1] == f"{ref}.parts.{p}") for p, vm in fb.PARTS}
        item = Item(self, slot, "bar", wrap, fb.BAR, path, inst)
        self.items[slot] = item
        return item

    # ------------------------------------------------------------ text and layout
    def text(self, name, string, style="Headlines/He 1", color="Typography/primary-text-color"):
        """A line of text in a DS text style and colour token (one line: its box is exactly its line height)."""
        k = f"{self.key}_{name}"
        kit.text_style(k, style, kit.color(color))
        t = kit.text(f"{self.art}.{name}.t", [(k, string)], lp=kit.hug(), wrap=False)
        wrap = kit.box(f"{self.art}.{name}", [t], h=kit.STYLES[k]["lh"], layoutWidthScaleType="hug",
                       layoutHeightScaleType="fixed", flexDirectionValue="row", layoutAlignmentType="centerLeft")
        item = Item(self, name, "text", wrap)
        self.items[name] = item
        return item

    def _box(self, name, kids, direction, gap, pad, align, w, h, paints=(), **st):
        size = {"layoutWidthScaleType": "fixed" if isinstance(w, (int, float)) else w,
                "layoutHeightScaleType": "fixed" if isinstance(h, (int, float)) else h}
        g = {"gapVertical": gap} if direction == "column" else {"gapHorizontal": gap}
        pads = pad if isinstance(pad, (tuple, list)) else (pad,) * 4     # left, top, right, bottom
        box = kit.box(f"{self.art}.{name}", [_el(k) for k in kids], w=w if isinstance(w, (int, float)) else 0,
                      h=h if isinstance(h, (int, float)) else 0, paints=paints, flexDirectionValue=direction,
                      layoutAlignmentType=align, paddingLeft=pads[0], paddingTop=pads[1], paddingRight=pads[2],
                      paddingBottom=pads[3], marginRight=0, **g, **size, **st)
        item = Item(self, name, "box", box)
        self.items[name] = item
        return item

    def column(self, name, kids, gap=16, pad=0, align="topLeft", w="hug", h="hug"):
        """A vertical stack. align: topLeft, topCenter, center, centerLeft...; w / h: "hug", "fill" or points."""
        return self._box(name, kids, "column", gap, pad, align, w, h)

    def row(self, name, kids, gap=8, pad=0, align="centerLeft", w="hug", h="hug"):
        return self._box(name, kids, "row", gap, pad, align, w, h)

    def card(self, name, kids, w=380, pad=24, gap=16, align="topLeft"):
        """A white DS card: radius 8, 1 px border-light edge, shadow-1 (DS "Cards"). `kids` stack in a column."""
        r = kit.radius("border-radius-m")
        n = f"{self.art}.{name}"
        edge = kit.absolute(f"{n}.edge", paints=[kit.line(f"{n}.edge.s", kit.color("Borders/border-light-color"))],
                            inset=(0.5,) * 4, cornerRadiusTL=r - 0.5)
        pads = pad if isinstance(pad, (tuple, list)) else (pad,) * 4
        inner = kit.box(f"{n}.body", [edge] + [_el(k) for k in kids], w=w, paints=[kit.solid(f"{n}.fill", kit.WHITE)],
                        flexDirectionValue="column", layoutAlignmentType=align, gapVertical=gap,
                        paddingLeft=pads[0], paddingTop=pads[1], paddingRight=pads[2], paddingBottom=pads[3],
                        cornerRadiusTL=r, layoutWidthScaleType="fixed", layoutHeightScaleType="hug")
        # the shadow layers come after the body, so they draw under it (the first child draws on top)
        shadow = kit.shadow_layers(f"{n}.sh", kit.DS["shadow"]["shadow-1"]["layers"], r)
        wrap = kit.box(n, [inner] + shadow, marginRight=0, **kit.hug())
        item = Item(self, name, "box", wrap)
        self.items[name] = item
        return item

    def layout(self, root, align="center", pad=0):
        """What the artboard shows: `root` placed in the frame (align: center, topCenter, topLeft...)."""
        pads = pad if isinstance(pad, (tuple, list)) else (pad,) * 4
        self.root = kit.box(f"{self.art}.page", [_el(root)], flexDirectionValue="column", layoutAlignmentType=align,
                            paddingLeft=pads[0], paddingTop=pads[1], paddingRight=pads[2], paddingBottom=pads[3],
                            layoutWidthScaleType="fill", layoutHeightScaleType="fill")

    # ------------------------------------------------------------ the artboard
    def actions(self):
        """The choreography: returns an Actions on one timeline (call after layout())."""
        assert self.root is not None, "call p.layout(root) first"
        assert self.a is None, "one Actions per piece"
        self.props += [("cursor", "vm:cursor", CURSOR.inst(f"vmi.cursor.{self.key}", {}, name=f"{self.art} cursor")),
                       ("play", "trigger", None), ("tabChange", "trigger", None)]
        self.vm = kit.VM(self.key, f"{self.art} view model", self.props)
        kit.use(self.vm)
        self.overlay = El("Node", {"x": 0, "y": 0}, [], name=f"{self.art}.cursors")
        self.drivers = El("CustomPropertyGroup", {"x": 0, "y": self.h + 40}, [], name="Drivers")
        self.board = El("Artboard", {"defaultStateMachineId": f"@sm.{self.key}", "viewModelId": f"@{self.vm.ref()}",
                                     "viewModelInstanceId": f"@vmi.{self.key}", "styleId": f"@{self.art}Art.style",
                                     "width": self.w, "height": self.h, "clip": True, "x": 0, "y": 0},
                         [kit.style(f"{self.art}Art"), kit.solid(f"{self.art}Art.fill", self.bg),
                          El("FocusData", {"canFocus": False}), self.drivers, self.overlay, self.root],
                         name=self.art, ref=f"art.{self.key}")
        choreo.configure({"design": [self.w, self.h], "output": [self.w, self.h]})
        self.a = Actions(self)
        return self.a

    def _by(self):
        by = {}
        kit.walk(self.board, lambda e: by.__setitem__(e.name, e) if e.name else None)
        return by

    def _parent_of(self, el):
        found = []

        def walk(e):
            for c in e.children:
                if isinstance(c, El):
                    if c is el:
                        found.append(e)
                    walk(c)
        walk(self.board)
        return found[0] if found else None

    # ------------------------------------------------------------ measure (where things are, for the cursor)
    def bounds(self, item, t=0.0):
        """(x, y, w, h) of a placed item in artboard points, as laid out at time t."""
        item = item.parent if item.kind == "part" else item
        return self._measure(t)[item.wrap.name]

    def _measure(self, t):
        a = self.a
        f = frame(t)
        elem = {}   # (element name, prop) -> value at t (widths, displays, margins: layout)
        for (n, p), tr in a.c.tracks.items():
            if n.startswith("drv.") or p in ("opacity", "scaleX", "scaleY", "distance", "rotation"):
                continue
            elem[(n, p)] = tr.value_at(f)
        insts = {}  # driver values at t, written into the placements' data
        for name, (item, prop) in a.driver_of.items():
            insts[(item.inst[1], prop)] = a.c.tracks[(name, "propertyValue")].value_at(f)
        state = json.dumps([sorted(map(list, elem.items())), sorted(map(list, insts.items()))], default=str)
        if state in self._measured:
            return self._measured[state]
        # the measure scene: the piece without its timeline, drivers or cursors, a marker on every placement
        board = copy.deepcopy(self.board)
        by = {}
        kit.walk(board, lambda e: by.__setitem__(e.name, e) if e.name else None)
        board.children = [c for c in board.children if c.name not in ("Drivers", f"{self.art}.cursors")]
        for (n, p), v in elem.items():
            by[n].attrs[p] = {0: "flex", 1: "none"}.get(v, v) if p == "displayValue" else v
        for it in self.items.values():
            w = by[it.wrap.name]
            w.children.insert(0, El("SemanticData", {"role": "group", "label": it.wrap.name},
                                    name=f"{it.wrap.name}.measure"))
        lay = kit.Layer("Measure")
        lay.state("idle", None, entry=True)
        board.children.append(kit.machine([lay]))
        saved = []
        for (ref, prop), v in insts.items():
            for vm in kit.VM.all.values():
                for inst in vm.instances:
                    if inst[1] == ref:
                        saved.append((inst[2], prop, inst[2].get(prop, KeyError)))
                        inst[2][prop] = v
        font = kit.FONT_DIR[0]
        kit.FONT_DIR[0] = "fonts"
        try:
            xml, _ = kit.assemble([board] + self.comps + self.icons, list(kit.VM.all))
        finally:
            kit.FONT_DIR[0] = font
            for d, prop, old in saved:
                if old is KeyError:
                    d.pop(prop, None)
                else:
                    d[prop] = old
        out = os.path.join(self.here, "build", "measure")
        os.makedirs(out, exist_ok=True)
        if not os.path.exists(os.path.join(out, "fonts")):
            os.symlink(os.path.join(kit.HERE, "fonts"), os.path.join(out, "fonts"))
        cache_f = os.path.join(out, "cache.json")
        cache = json.load(open(cache_f)) if os.path.exists(cache_f) else {}
        h = hashlib.sha256(xml.encode()).hexdigest()
        if h not in cache:
            open(os.path.join(out, "scene.rml"), "w").write(xml + "\n")
            open(os.path.join(out, "rive.yaml"), "w").write(f'name: measure\nmain: "{self.art}"\n')
            r = subprocess.run([RIVE, out, "--semantics=-", "--advance=2", "--quiet"], capture_output=True, text=True,
                               timeout=120)
            if r.returncode:
                raise RuntimeError("measure failed:\n" + (r.stdout + r.stderr)[-1500:])
            found = {}

            def walk(node):
                b = node.get("bounds")
                if b:
                    found[node["label"]] = (b["x"], b["y"], b["width"], b["height"])
                for c in node.get("children", []):
                    walk(c)
            for root in json.loads(r.stdout)["roots"]:
                walk(root)
            cache[h] = found
            json.dump(cache, open(cache_f, "w"))
        self._measured[state] = {k: tuple(v) for k, v in cache[h].items()}
        return self._measured[state]

    def point(self, item, where=None, t=0.0):
        """Where the cursor aims on `item` at time t: "center" (default; an input's default is "field"), "field" (an
        input's text field), "remove" (a tag's x), or (dx, dy) from the centre."""
        x, y, w, h = self.bounds(item, t)
        if item.kind == "part":   # a part of the floating bar: its slot along the bar (1 + 16 handle + 8 gap...)
            names = [p for p, _ in fb.PARTS]
            i = names.index(item.key.split(".")[-1])
            x0 = x + 1 + 16 + 8
            cx = x0 + 36 if i == 0 else x0 + 72 + 8 + 1 + 8 + 12 + 32 * (i - 2)
            return (cx, y + h / 2)
        cx, cy = x + w / 2, y + h / 2
        if where is None and item.kind == "input":
            where = "field"
        if where in (None, "center"):
            return (cx, cy + (1 if item.kind in ("button", "ib") else 0))
        if where == "field":     # measured from the bottom: [label] field [message room]
            assert item.kind == "input"
            field = 35 if self.a.state_at(item, "size", t) == 0 else 25
            room = MSG_ROOM if self.a.state_at(item, "showMessage", t) else 0
            return (x + min(0.3 * w, 90), y + h - room - field / 2)
        if where == "remove":
            assert item.kind == "tag"
            return (x + w - (13 if item.value("size") == 1 else 10), cy)
        return (cx + where[0], cy + where[1])

    # ------------------------------------------------------------ build
    def build(self, tabs=False):
        """Write scene.rml (and rive.yaml if missing), print the timeline and the lints. tabs=True: a hero tab (the
        timeline plays once, fires `tabChange` at its end, `play` restarts it); otherwise the timeline loops.
        Exits 1 when a lint fails. `python build.py --stills 1.2 3.4` also renders those times to build/stills/."""
        a = self.a
        a._finish(tabs)
        c = a.c
        kit.use(self.vm)
        # the timeline: every key the actions made (elements, drivers, cursors)
        tl = El("LinearAnimation", {"fps": FPS, "duration": c.F, "loopValue": None if tabs else "loop"},
                c.to_rml(), name="Timeline", ref=f"anim.{self.art} timeline")
        run = type("A", (), {"name": f"{self.art} timeline"})
        lay = kit.Layer("Main")
        if tabs:
            fire = kit.tick()
            lay.state("run", run, lay.go("run2", kit.if_trigger("play")), lay.go("end", at_end=True), entry=True)
            lay.state("end", fire, lay.go("run2", at_end=True), lay.go("run2", kit.if_trigger("play")),
                      actions=[kit.fire("tabChange")])
            lay.state("run2", run, lay.go("run", kit.if_trigger("play")), lay.go("end2", at_end=True))
            lay.state("end2", fire, lay.go("run", at_end=True), lay.go("run", kit.if_trigger("play")),
                      actions=[kit.fire("tabChange")])
        else:
            lay.state("run", run, lay.go("run2", kit.if_trigger("play")), entry=True)
            lay.state("run2", run, lay.go("run", kit.if_trigger("play")))
        board = copy.deepcopy(self.board)
        board.children.insert(3, tl)
        board.children.append(kit.machine([lay]))
        xml, doc = kit.assemble([board] + self.comps + self.icons, list(kit.VM.all))
        open(os.path.join(self.here, "scene.rml"), "w").write(xml + "\n")
        yml = os.path.join(self.here, "rive.yaml")
        if not os.path.exists(yml):
            lib = os.path.relpath(kit.HERE, self.here)
            open(yml, "w").write(f'name: {os.path.basename(self.here)}\nmain: "{self.art}"\nexclude:\n  - build\n'
                                 f'  - {lib}/icons\n  - {lib}/ds\n')
        issues = a._report(tabs)
        print(f"wrote scene.rml: {self.art} {self.w}x{self.h}, {c.F} frames ({c.F / FPS:.2f} s, "
              f"{'plays once, then tabChange' if tabs else 'loops'}), {len(a.driver_of)} drivers, "
              f"{len(a.visits)} cursor visit(s)")
        if "--stills" in sys.argv:
            ts = [float(x) for x in sys.argv[sys.argv.index("--stills") + 1:] if not x.startswith("--")]
            self.stills(ts)
        if issues:
            print(f"LINT FAILED ({len(issues)})")
            sys.exit(1)
        print("lints: clean")

    def stills(self, times):
        """Render the piece at these times (seconds) to build/stills/ (frame N at 60 fps is --advance=N+1), plus a
        contact sheet build/stills/sheet.png."""
        out = os.path.join(self.here, "build", "stills")
        os.makedirs(out, exist_ok=True)
        files = []
        for t in times:
            n = frame(t)
            p = os.path.join(out, f"t{t:05.2f}_f{n}.png")
            r = subprocess.run([RIVE, self.here, f"--screenshot={p}", f"--advance={n + 1}", "--quiet"],
                               capture_output=True, text=True, timeout=120)
            if r.returncode:
                raise RuntimeError(r.stdout[-800:] + r.stderr[-800:])
            files.append((f"{t:.2f} s (frame {n})", p))
        try:
            from PIL import Image, ImageDraw
            ims = [(lab, Image.open(p).convert("RGB")) for lab, p in files]
            s = 0.5 if self.w > 900 else 1.0
            cw, ch = int(self.w * s), int(self.h * s)
            cols = 2 if len(ims) > 1 else 1
            sheet = Image.new("RGB", (cols * (cw + 12) + 12, ((len(ims) + cols - 1) // cols) * (ch + 30) + 12),
                              (240, 240, 242))
            d = ImageDraw.Draw(sheet)
            for i, (lab, im) in enumerate(ims):
                x, y = 12 + (i % cols) * (cw + 12), 12 + (i // cols) * (ch + 30)
                d.text((x, y), lab, fill=(30, 30, 30))
                sheet.paste(im.resize((cw, ch)), (x, y + 18))
            sheet.save(os.path.join(out, "sheet.png"))
            print("stills:", out, "(sheet.png)")
        except ImportError:
            print("stills:", out)


class Actions:
    """The choreography of one piece, on one timeline. Times are seconds; `t=None` means "now" (`a.now`), and
    every action moves `now` to when it is done, so a sequence reads top to bottom with no arithmetic."""

    def __init__(self, piece):
        self.p = piece
        self.c = Choreo(piece.board, piece._by(), 1.0)
        self.c.parent[id(piece.overlay)] = piece.board
        self.now = 0.0
        self.visits, self.visit = [], None      # cursor visits; the open one
        self.driver_of = {}                     # driver name -> (item, prop)
        self.focus = None                       # the input that holds the focus
        self.log, self.messages, self.end = [], [], 0.0
        self.looped, self.loop_exit, self.issues = False, None, []

    # ------------------------------------------------------------ time
    def _t(self, t):
        return self.now if t is None else t

    def at(self, t):
        """Move `now` to t."""
        self.now = t
        return t

    def wait(self, s):
        """Let s seconds (or a duration token: "read_hold") pass (the cursor, if on screen, waits aside or leaves on
        its own: it never parks)."""
        self.now += secs(s)
        return self.now

    hold = wait   # a reading hold: every message the viewer must read stays >= 1 s

    def _note(self, t, what):
        self.log.append((t, what))
        self.end = max(self.end, t)

    # ------------------------------------------------------------ drivers (component states on the timeline)
    def _driver(self, item, prop):
        assert item.vm is not None, f"{item} has no view model"
        kind = item.vm.kind(prop)
        assert kind in DRIVER, f"{item.vm.name}.{prop} is {kind}: set it when placing, not on the timeline"
        name = f"drv.{item.key}.{prop}"
        if name not in self.driver_of:
            tag, pkey = DRIVER[kind]
            v0 = item.value(prop)
            el = El(tag, {"propertyValue": v0}, [El("DataBindContext", {
                "sourcePathIds": item.path + (item.vm.ref(prop),), "propertyKey": pkey, "direction": True})], name=name)
            self.p.drivers.children.append(el)
            self.c.by[name] = el
            self.driver_of[name] = (item, prop)
            tr = self.c.track(name, "propertyValue")
            tr.keys[0]["v"] = float(v0) if kind == "number" else v0
        return name

    def _key(self, t, item, prop, value):
        name = self._driver(item, prop)
        kind = item.vm.kind(prop)
        if kind == "artboard":
            value = kit.icon_ref(value)
        self.c.set(t, name, "propertyValue", float(value) if kind == "number" else value)

    def state_at(self, item, prop, t):
        name = f"drv.{item.key}.{prop}"
        if name in self.driver_of:
            return self.c.tracks[(name, "propertyValue")].value_at(frame(t))
        return item.value(prop)

    def set(self, item, t=None, **props):
        """Set component properties at t (a key on each one's driver): a.set(email, error=True)."""
        t = self._t(t)
        for k, v in props.items():
            self._key(t, item, k, v)
        self._note(t, f"set {item.key} {props}")
        return t

    # ------------------------------------------------------------ elements: entrances and exits
    def enter(self, item, t=None, dy=8, dur=0.6):
        """Arrive and settle: fades in while rising `dy` px into place (settle curve, it starts invisible)."""
        t, dur = self._t(t), secs(dur)
        n = _el(item).name
        op = self.c.track(n, "opacity")
        if len(op.keys) == 1:     # its first appearance: hidden until it enters
            op.keys[0]["v"] = 0.0
        self.c.enter(t, n, dy=dy, dur=dur)
        self._note(t + dur, f"enter {n}")
        return t

    def stagger(self, items, t=None, step="list", dy=8, dur=0.6):
        """Several items entering one after another (step: "tight" 17 ms, "list" 67 ms, "loose" 83 ms, or s)."""
        t, dur = self._t(t), secs(dur)
        s = STEP.get(step, step)
        for i, it in enumerate(items):
            self.enter(it, t + i * s, dy, dur)
        return t

    def exit(self, item, t=None, dy=-6, dur=None):
        """Leaves: fades out (the fade token) while moving `dy` px."""
        t = self._t(t)
        n = _el(item).name
        dur = secs(dur) or kit.SHORT
        self.c.exit(t, n, dy=dy, dur=dur, fade=kit.FADE)
        self._note(t + dur, f"exit {n}")
        return t + dur

    # ------------------------------------------------------------ the cursor
    def cursor_in(self, side="right", t=None):
        """A cursor enters from off-frame (side: right, left, bottom, top), already moving, toward the next target.
        Without it, the first click brings one in from the right."""
        assert self.visit is None, "a cursor is already on screen (cursor_out first)"
        self.visit = {"name": f"CURSOR{len(self.visits) + 1}", "side": side, "enter": None, "points": [],
                      "leave": None, "start": self._t(t) if t is not None else None, "last": None}
        return self.now

    def _off(self, side, toward):
        x, y = toward
        W, H = self.p.w, self.p.h
        return {"right": (W + 70, min(H + 40, y + 140)), "left": (-70, min(H + 40, y + 140)),
                "bottom": (min(W + 40, x + 160), H + 70), "top": (min(W + 40, x + 120), -70)}[side]

    def _nearest_side(self, pt):
        x, y = pt
        d = {"right": self.p.w - x, "left": x, "bottom": self.p.h - y, "top": y}
        return min(d, key=d.get)

    def cursor_out(self, side=None):
        """The cursor leaves the frame right after its last action, accelerating (side: default the nearest)."""
        v = self.visit
        if v is None:
            return self.now
        last = v["points"][-1]["at"]
        side = side or self._nearest_side(last)
        v["leave"] = {"right": (self.p.w + 80, last[1] + 120), "left": (-80, last[1] + 120),
                      "bottom": (last[0] + 120, self.p.h + 80), "top": (last[0] + 120, -80)}[side]
        self.visits.append(v)
        self.visit = None
        return self.now

    @staticmethod
    def _travel(a, b):
        return Visit.move_ms(type("V", (), {"tok": TOK["cursor"], "dpx": choreo.DPX})(), math.dist(a, b) * 1.03) / 1000

    def _go(self, at, t, click):
        """Add a cursor point (a click: t = press time; a pass: t = pass time). Returns the time used."""
        if self.visit is None:
            self.cursor_in("right")
        v = self.visit
        if not v["points"]:
            start = v["start"] if v["start"] is not None else self.now
            v["enter"] = self._off(v["side"], at)
            natural = start + self._travel(v["enter"], at) - (LEAD if click else 0)
            t = natural if t is None else max(t, natural - 0.1)
        else:
            prev = v["points"][-1]
            depart = prev["t"] + (LEAD + 2 / FPS if prev.get("click") else 0) + prev.get("pause", 0)
            travel = self._travel(prev["at"], at)
            natural = max(depart, self.now) + travel - (LEAD if click else 0)
            if t is None:
                t = natural
            gap = t - (depart + travel - (LEAD if click else 0))
            if gap > 0.6:
                if prev.get("click") and click and gap <= 1.4:
                    v["points"].append({"aside": True})     # waits aside: drifts off and swoops back
                else:   # a long wait: it leaves, and a cursor comes back for this
                    self.cursor_out()
                    side = self._nearest_side(at)
                    self.cursor_in(side, t=t - self._travel(self._off(side, at), at) + (LEAD if click else 0))
                    return self._go(at, t, click)
            t = max(t, depart + 0.7 * travel - (LEAD if click else 0))
        pt = {"at": (round(at[0], 2), round(at[1], 2)), "t": round(t, 4)}
        if click:
            pt["click"] = True
        v["points"].append(pt)
        return t

    # ------------------------------------------------------------ interactions
    def _reacts(self, item, t, press=True):
        """The control's reaction to a press at t: hover before it, the press, and its own result."""
        vm = item.vm
        props = {n for n, _, _ in vm.props} if vm else set()
        if "hover" in props:
            self._key(t - HOVER_LEAD, item, "hover", True)
        if press and "pressed" in props:
            self._key(t, item, "pressed", True)
            self._key(t + kit.PRESS, item, "pressed", False)
        if self.focus is not None and self.focus is not item:     # a press anywhere else blurs the field
            self._key(t, self.focus, "focused", False)
            self.focus = None
        if item.kind == "input":
            self._key(t, item, "focused", True)
            self.focus = item

    def _unhover(self, item, t):
        if item.vm and "hover" in {n for n, _, _ in item.vm.props}:
            self._key(t, item, "hover", False)

    def click(self, item, t=None, where=None, loading=None):
        """The cursor goes to `item` and clicks it: hover ~150 ms before, the press on the press frame (scale 0.96 /
        0.9 from the component), the cursor's own press, the result on the press frame (an input takes the focus).
        loading=s: the button shows its spinner from the press for s seconds. Returns the press time."""
        tp = self._t(t) if t is not None else None
        at = self.p.point(item, where, self.now if tp is None else tp)
        t = self._go(at, tp, True)
        self._reacts(item, t)
        depart = t + LEAD + 2 / FPS
        self._unhover(item, depart + 0.1)
        self.visit["last"] = (item, t, where)
        self._note(t, f"click {item.key}")
        self.now = depart
        loading = secs(loading)
        if loading:
            self._key(t, item, "loading", True)
            self._key(t + loading, item, "loading", False)
            self._note(t + loading, f"loading {item.key} {loading:g}s")
            self.now = t + loading
        return t

    def move_to(self, item, t=None, where=None, hold=0.0):
        """The cursor passes over `item` (no click); hold=s: it lingers there softly (a "thought"), hovering it."""
        tp = self._t(t) if t is not None else None
        hold = secs(hold)
        at = self.p.point(item, where, self.now if tp is None else tp)
        t = self._go(at, tp, False)
        if hold:
            self.visit["points"][-1]["pause"] = hold
        if item.vm and "hover" in {n for n, _, _ in item.vm.props}:
            self._key(max(0.0, t - 0.1), item, "hover", True)
            self._key(t + hold + 0.15, item, "hover", False)
        self._note(t, f"move to {item.key}")
        self.now = t + hold
        return t

    def hover(self, item, hold=0.6, t=None, where=None):
        """move_to with a soft linger: the control shows its hover while the cursor creeps over it."""
        return self.move_to(item, t, where, hold)

    def type_into(self, item, text, then=None, then_where=None, cps=None):
        """Duda's typing pattern. The cursor has just clicked `item` (it clicks it first if not); typing starts
        150 ms after that click, and the cursor drifts aside on one arc and swoops to `then`, clicking it as the last
        character lands (then_where: where on it, as in click). Without `then` the cursor leaves while the text is
        typed. Returns when the text is done."""
        assert item.kind == "input"
        v = self.visit
        if not (v and v["last"] and v["last"][0] is item and v["points"][-1].get("click")):
            self.click(item, where="field")
        t0 = self.visit["last"][1]
        start = t0 + 0.15
        n = len(text)
        if then is not None:
            natural = start + n / (cps or 16)
            t1 = min(max(natural, t0 + 1.45), t0 + 2.1)        # the pattern's window (reference x1 to x1.45)
            at = self.p.point(then, then_where, t1)
            self.visit["points"] += [{"aside": True}, {"at": (round(at[0], 2), round(at[1], 2)), "t": t1, "click": True}]
            tp = t1
            self._reacts(then, tp)
            self._unhover(then, tp + LEAD + 2 / FPS + 0.1)
            self.visit["last"] = (then, tp, then_where)
            until = tp
            self.now = tp + LEAD + 2 / FPS
            self._note(tp, f"click {then.key}")
        else:
            self.cursor_out()
            until = start + n / (cps or 14)
            self.now = until
        # the value is the text from the start; `typed` shows it one character at a time (human jitter)
        cur = item.value("value")
        assert cur in ("", text), f"{item.key} already holds {cur!r}"
        item.inst[2]["value"] = text
        item.inst[2]["typed"] = 0
        assert f"drv.{item.key}.typed" not in self.driver_of, f"{item.key} is typed into twice"
        rnd = random.Random(sum(map(ord, text)))
        jit = [rnd.uniform(0.6, 1.4) + (0.6 if ch in ",.:;" else 0) for ch in text]
        k = (until - start) / sum(jit)
        tt = start
        for i in range(n):
            tt += jit[i] * k
            self._key(min(tt, until), item, "typed", i + 1)
        self._key(until + 2 / FPS, item, "typed", TYPED_ALL + 1)
        self._note(until, f"typed {text!r} into {item.key}")
        return until

    def remove(self, tag, t=None):
        """The cursor clicks a tag's x: the tag fades and shrinks a little on the press, then the row closes the gap
        smoothly (one state at a time; no jump). Returns when the row has settled."""
        assert tag.kind == "tag"
        v = self.visit
        if v and v["last"] and v["last"][0] is tag and v["last"][2] == "remove" and t is None:
            tp = v["last"][1]       # the cursor has just pressed its x (type_into ... then_where="remove")
        else:
            tp = self.click(tag, t, where="remove")
        self._key(tp - HOVER_LEAD, tag, "removeHover", True)
        n = tag.wrap.name
        x, y, w, h = self.p.bounds(tag, tp)
        par = self.p._parent_of(tag.wrap)
        pst = next(c for c in par.children if c.tag == "LayoutComponentStyle")
        gap = pst.attrs.get("gapHorizontal", 0) or 0
        # the wrapper holds the tag's measured width from the start, so the width can close
        st = next(c for c in tag.wrap.children if c.tag == "LayoutComponentStyle")
        st.attrs["layoutWidthScaleType"] = "fixed"
        tag.wrap.attrs["width"] = w
        self.c.track(n, "width").keys[0]["v"] = float(w)
        self.c.fade(tp, n, 0.0, SWAP)
        for ax in ("scaleX", "scaleY"):
            self.c.move(tp, n, ax, 0.92, SWAP, "duda")
        t1 = tp + SWAP
        dur = kit.SHORT
        peak = Visit_peak(choreo.ease_curve("duda"))
        cap = TOK["speed_cap_px_per_frame_at_1920"]["text_content"]
        while (w + gap) * peak / (dur * FPS) * choreo.OUT_SCALE > cap:
            dur += 1 / FPS
        self.c.move(t1, n, "width", 0.0, dur, "duda")
        mr = self.c.track(f"{n}.style", "marginRight")
        mr.keys[0]["v"] = 0.0
        self.c.move(t1, f"{n}.style", "marginRight", -float(gap), dur, "duda")
        t2 = t1 + dur + 1 / FPS
        disp = self.c.track(f"{n}.style", "displayValue")
        disp.keys[0]["v"] = 0
        self.c.set(t2, f"{n}.style", "displayValue", 1)
        self.c.set(t2, f"{n}.style", "marginRight", 0.0)
        self._key(t1, tag, "hover", False)
        self._key(t1, tag, "removeHover", False)
        self._note(t2, f"removed {tag.key} (row closes {w + gap:.0f} px in {dur:.2f} s)")
        return t2

    def message(self, item, text, kind=None, t=None):
        """An input's message under the field (kind: None info, "error", "success", "warning"). A message already
        shown leaves first (0.1 s), the new one arrives after: one state at a time. Returns when it is shown."""
        t = self._t(t)
        if self.state_at(item, "showMessage", t):
            self._key(t, item, "showMessage", False)
            t += SWAP + 1 / FPS
        flags = {"error": kind == "error", "success": kind == "success", "warning": kind == "warning"}
        for k, v in flags.items():
            if self.state_at(item, k, t) != v or v:
                self._key(t, item, k, v)
        self._key(t, item, "message", text)
        self._key(t, item, "showMessage", True)
        self.messages.append((item, t))
        self._note(t, f"message {item.key} {kind or 'info'}: {text!r}")
        self.now = t
        return t

    # ------------------------------------------------------------ the loop
    def loop(self, exit=None, hold=None):
        """End the loop cleanly: `exit` (the card or panel that entered at the start) leaves, everything goes back to
        its first frame while it is hidden, and >= 8 still frames close the loop. Call it last. Whatever changed
        outside `exit` would jump back on screen: the build fails it."""
        hold = 8 / FPS if hold is None else secs(hold)
        if self.visit is not None:
            self.cursor_out()
        t = max(self.now, self._cursor_end())
        if exit is not None:
            n = _el(exit).name
            assert self.c.track(n, "opacity").keys[0]["v"] == 0.0, f"{n} must enter at the start (a.enter) to exit"
            t = self.exit(exit, t)
        self.loop_exit = _el(exit) if exit is not None else None
        self.reset_at = t + 1 / FPS
        self.now = self.reset_at + hold
        self.looped = True
        return self.now

    def _cursor_end(self):
        end = 0.0
        for v in self.visits:
            last = v["points"][-1]
            end = max(end, last["t"] + 1.2)
        return end

    # ------------------------------------------------------------ build
    def _finish(self, tabs):
        if self.visit is not None:
            self.cursor_out()
        c = self.c
        for v in self.visits:     # the cursors: a Follow Path each, riding it a nested library Cursor
            name = v["name"]
            geo = Visit(name, v["enter"], copy.deepcopy(v["points"]), v["leave"], choreo.PT)
            follow = El("FollowPathConstraint", {"targetId": f"@{name}.path", "orient": False}, name=f"{name}.follow")
            nest = El("NestedArtboard", {"artboardId": "@art.cursor", "dataBindPathIds": (
                f"vm.{self.p.key}", f"vm.{self.p.key}.cursor")}, [El("NestedStateMachine", {
                    "animationId": "@sm.cursor"}, name=f"{name}.machine")], name=f"{name}.art")
            node = El("Node", {"x": 0, "y": 0, "opacity": 0, "scaleX": self.p.cursor_scale,
                               "scaleY": self.p.cursor_scale}, [nest, follow], name=name)
            shape = geo.path_shape()
            self.p.overlay.children[:0] = [node]
            self.p.overlay.children.append(shape)
            for e in (node, shape):
                c.parent[id(e)] = self.p.overlay
                kit.walk(e, lambda x: c.by.__setitem__(x.name, x) if x.name else None)
            c.cursor_visit(name, v["enter"], copy.deepcopy(v["points"]), v["leave"])
            self.end = max(self.end, c.visits[name].t_out or 0)
        dur = max(self.now, self.end) if self.looped else max(self.now, self.end) + 0.5
        if self.looped and self.end > self.reset_at:
            raise ValueError(f"something still happens at {self.end:.2f}s, after the loop's exit ({self.reset_at:.2f}s)")
        c.duration, c.F = dur, frame(dur)
        c._samples = None
        if self.looped:   # back to the first frame while hidden
            fr = frame(self.reset_at)
            hidden = set()
            if self.loop_exit is not None:
                kit.walk(self.loop_exit, lambda e: hidden.add(e.name) if e.name else None)
            jumps = []
            for (n, p), tr in c.tracks.items():
                if tr.value_at(fr) != tr.keys[0]["v"] and not any(k["f"] > fr for k in tr.keys):
                    tr.set(fr, tr.keys[0]["v"])
                    if n in self.driver_of:
                        it = self.driver_of[n][0]
                        n = (it.parent if it.kind == "part" else it).wrap.name
                    if n not in hidden and not n.startswith("CURSOR"):
                        jumps.append(f"{n}.{p}" if not n.startswith(self.p.art) else n)
            if jumps:
                self.issues.append(f"loop: {', '.join(sorted(set(jumps)))} jump back to the first frame on screen; "
                                   f"loop(exit=...) the card or panel that holds them (it must enter at the start)")

    def _report(self, tabs):
        c = self.c
        report, issues = c.lint()
        issues += self.issues
        if not tabs:
            issues += [f"loop: {b}" for b in c.check_loop()]
        for item, t in self.messages:     # a message the viewer must read stays >= 1 s
            tr = c.tracks[(f"drv.{item.key}.showMessage", "propertyValue")]
            off = next((k["f"] / FPS for k in tr.keys if k["f"] > frame(t) and not k["v"]), c.F / FPS)
            if off - t < 1.0 - 1e-6 and off < c.F / FPS:
                issues.append(f"message on {item.key} at {t:.2f}s is shown only {off - t:.2f}s (reading: >= 1 s)")
        print("timeline:")
        for t, what in sorted(self.log, key=lambda x: x[0]):
            print(f"  {t:6.2f}s  {what}")
        for line in c.log:
            print("  ", line)
        print("speed lint (px/frame, cap):")
        for n, kind, peak, cap, at in sorted(report, key=lambda r: -r[2] / r[3])[:8]:
            print(f"   {'OVER' if peak > cap + 0.5 else 'ok  '} {peak:6.1f}/{cap:<3} {kind:8s} {n} @ {at / FPS:.2f}s")
        for i in issues:
            print("LINT:", i)
        return issues


def Visit_peak(e):
    """Peak speed of a normalised ease, as a multiple of its mean."""
    best, prev = 0.0, 0.0
    for j in range(1, 401):
        v = progress(e, j / 400)
        best = max(best, (v - prev) * 400)
        prev = v
    return best
