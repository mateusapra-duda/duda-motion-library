"""What piece.py and patterns.py share: time tokens, colours and the placed Item (a piece imports only piece.py)."""
import os

import kit
from components import floating_bar as fb
import choreo

RIVE = os.path.expanduser("~/.rive/bin/rive")
TAB_PARTS = {"pills": "PillTabs.tab", "coretabs": "CoreTabs.tab"}    # placement kind -> its tabs' names
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

    def tab(self, i):
        """Tab i of a Pill_Tabs or Core Tabs (0 = the first), as a target: a.click(tabs.tab(1)) selects the second."""
        assert self.kind in TAB_PARTS, "only Pill_Tabs and Core Tabs have tabs"
        item = Item(self.p, f"{self.key}.tab{i}", "tab", None, parent=self)
        item.index = i
        return item

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


def _color(c):
    """A DS colour token name or '#rrggbb' / '#rrggbbaa' -> ARGB."""
    if c.startswith("#"):
        return kit.hex_argb(c[:7]) if len(c) == 7 else kit.argb(c[:7], int(c[7:9], 16) / 255)
    return kit.color(c)


FIT = {"fill": 0, "contain": 1, "cover": 2, "fitWidth": 3, "fitHeight": 4, "none": 5, "scaleDown": 6}
