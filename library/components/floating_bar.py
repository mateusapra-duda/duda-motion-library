"""VibeFloatingBar: the visual edit's floating bar (product: FloatingElementBar), built only from library components.
Not in the DS (the DS has its icons only); the pilot of the library.

  drag handle      the bar's own part (16x35, three dots), as the product draws it
  edit             CoreButton  SecondaryButton, Grey, Small, "Edit", minWidth 72
  divider          Divider     Vertical, 16 high
  up, down, duplicate, padding, trash, dismiss
                   Icon button Small, Dark: i_arrow_top, i_arrow_bottom, i_duplicate, i_padding, i_trash, i_x

View model "VibeFloatingBar": one property per part, holding that part's own data (paths like bar/up/hover,
bar/edit/label, bar/up/clicked), plus
  open          the bar is shown: in, it fades and rises from 96 % (settle); out, it fades and shrinks to 98 % (duda)
                (the visual edit v02 timing)
  interactive   passed down to every part (their hover and clicks)
"""
from kit import (VM, El, Anim, Layer, use, box, absolute, solid, line, nested, shadow_layers, pose, bool_layer,
                 set_to, machine, component, if_bool, icon_ref, hex_argb, WHITE, FADE)
from components.core_button import CB
from components.divider import DIV
from components.icon_button import IB

ICONS = (("up", "i_arrow_top"), ("down", "i_arrow_bottom"), ("duplicate", "i_duplicate"), ("padding", "i_padding"),
         ("trash", "i_trash"), ("dismiss", "i_x"))
PARTS = (("edit", CB), ("divider", DIV)) + tuple((p, IB) for p, _ in ICONS)
EDGE = hex_argb("#E0E4E6")   # the product's edge: the legacy token Platform/Divider (ds/tokens.json platform_legacy)
DRAG = hex_argb("#FAFBFB")
DOTS = hex_argb("#757575")
# the product's box-shadow: rgba(24,39,75,.08) 0 0 3.94px, rgba(24,39,75,.12) 0 5.63px 9px
SHADOW = [{"x": 0, "y": 0, "blur": 3.94, "color": "#18274b14"}, {"x": 0, "y": 5.63, "blur": 9, "color": "#18274b1f"}]
ARRIVE = 0.333


def part_values(interactive=False):
    """Each part's data as the bar uses it (DS variant values)."""
    vals = {"edit": dict(label="Edit", variant=1, size=0, color=0, minWidth=72, interactive=interactive),
            "divider": dict(variant=2)}
    for p, ic in ICONS:
        vals[p] = dict(icon=icon_ref(ic), size=0, color=4, interactive=interactive)
    return vals


def instance(ref, name, interactive=False, over=None, **bar_values):
    """A new bar's data: its own instance of every part (two bars never share a part), then the bar's instance.
    over: {part: {prop: value}} on top of the bar's part values. Returns the bar instance's ref."""
    refs = {}
    vals = part_values(interactive)
    for p, vm in PARTS:
        refs[p] = vm.inst(f"{ref}.parts.{p}", dict(vals[p], **(over or {}).get(p, {})), name=f"{name} {p}")
    return BAR.inst(ref, dict(refs, interactive=interactive, **bar_values), name=name)


def _default_parts():
    refs = {}
    vals = part_values()
    for p, vm in PARTS:
        refs[p] = vm.inst(f"vmi.bar.default.{p}", vals[p], name=f"VibeFloatingBar {p}")
    return refs


BAR = VM("bar", "VibeFloatingBar", [("open", "boolean", True), ("interactive", "boolean", False)] +
         [(p, f"vm:{vm.key}", None) for p, vm in PARTS])
for _i, (_p, _vm) in enumerate(PARTS):   # the default instance holds the bar's own parts
    BAR.props[2 + _i] = (_p, f"vm:{_vm.key}", f"vmi.bar.default.{_p}")
_default_parts()


def drag_handle(n):
    dots = [El("Shape", {"x": 0, "y": dy}, [El("Ellipse", {"width": 3, "height": 3}), solid(f"{n}.dot{i}", DOTS)],
               name=f"{n}.dot{i}.shape") for i, dy in enumerate((-5, 0, 5))]
    return box(n, [El("Node", {"x": 8, "y": 17.5}, dots, name=f"{n}.dots")], w=16, h=35,
               paints=[solid(f"{n}.fill", DRAG)], layoutWidthScaleType="fixed", layoutHeightScaleType="fixed")


def build():
    use(BAR)
    n = "VibeFloatingBar"
    p = lambda part: (BAR.ref(), BAR.ref(part))   # noqa: E731
    items = [absolute(f"{n}.border", paints=[line(f"{n}.border.stroke", EDGE, 1)], inset=(0.5,) * 4,
                      cornerRadiusTL=3.5),
             drag_handle(f"{n}.drag"),
             nested(f"{n}.edit", "cb", p("edit"), "hug", 26),
             nested(f"{n}.divider", "div", p("divider"), 1, 16)]
    items += [nested(f"{n}.{part}", "ib", p(part), 24, 24) for part, _ in ICONS]
    bar = box(f"{n}.bar", items, h=37, paints=[solid(f"{n}.fill", WHITE)], clip=True, cornerRadiusTL=4,
              flexDirectionValue="row", layoutAlignmentType="centerLeft", gapHorizontal=8, paddingTop=1,
              paddingBottom=1, paddingLeft=1, paddingRight=13, layoutWidthScaleType="hug",
              layoutHeightScaleType="fixed")
    wrap = box(f"{n}.wrap", [bar] + shadow_layers(f"{n}.shadow", SHADOW, 4), layoutWidthScaleType="hug",
               layoutHeightScaleType="hug")
    pop = box(f"{n}.pop", [wrap], origin=(0.5, 1), layoutWidthScaleType="hug", layoutHeightScaleType="hug")

    # open: the visual edit's selection timing (the bar starts 50 ms after the selection box)
    lay = Layer("Open")
    looks = [(f"{n}.pop", "opacity", 0, 1), (f"{n}.pop", "scaleX", 1, 1), (f"{n}.pop", "scaleY", 1, 1)]
    a = Anim("Open in", 0.45)
    a.move(f"{n}.pop", "opacity", 0.05, 0.05 + FADE, 0, 1)
    for ax in ("scaleX", "scaleY"):
        a.move(f"{n}.pop", ax, 0.05, 0.05 + ARRIVE, 0.96, 1, "settle")
    out = Anim("Open out", 0.2)
    out.move(f"{n}.pop", "opacity", 0, FADE, 1, 0)
    for ax in ("scaleX", "scaleY"):
        out.move(f"{n}.pop", ax, 0, FADE, 1, 0.98, "duda")
    lay.state("hidden", pose("Open hidden", looks, 0), lay.go("in", if_bool("open", True)), entry=True)
    lay.state("in", a, lay.go("shown", at_end=True), lay.go("out", if_bool("open", False)))
    lay.state("shown", pose("Open shown", looks, 1), lay.go("out", if_bool("open", False)))
    lay.state("out", out, lay.go("hidden", at_end=True), lay.go("in", if_bool("open", True)))
    lay.enter_if("shown", if_bool("open", True))

    # interactive goes down to the parts (a layer writes it: safe with autoBind on the web)
    inter = Layer("Interactive")
    paths = [(BAR.ref(), BAR.ref(part), vm.ref("interactive")) for part, vm in PARTS if part != "divider"]
    inter.state("off", None, inter.go("on", if_bool("interactive", True)), entry=True,
                actions=[set_to("Boolean", "interactive", False, path=q) for q in paths])
    inter.state("on", None, inter.go("off", if_bool("interactive", False)),
                actions=[set_to("Boolean", "interactive", True, path=q) for q in paths])
    inter.enter_if("on", if_bool("interactive", True))
    return component("VibeFloatingBar", 311, 37, [pop], machine([lay, inter]),
                     layout={"layoutWidthScaleType": "hug", "layoutHeightScaleType": "hug"})
