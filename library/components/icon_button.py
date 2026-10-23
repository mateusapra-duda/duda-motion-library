"""Icon button (DS: page "Buttons", set 756:8239).

DS props -> view model "Icon button":
  Icon (instance swap)          icon            artboard, an "Icon/<name>" component (default Icon/i_plus)
  Type: Icon | Box              variant         0 Icon, 1 Box ("type" is a Luau keyword, so the editor refuses it)
  Size: Large 32 | Small 24     size            0 Small (24), 1 Large (32)
  Color                         color           0 Primary, 1 Grey, 2 Dark grey, 3 Light, 4 Dark
  Border                        border
  State                         hover, selected, focused, disabled, loading, hoverAnimated (booleans: in Rive the
                                states combine); pressed (polish, not in the DS)
  (prototype)                   interactive: hit area and listeners only when on; clicked fires on a click;
                                click plays a whole press (for a timeline or a piece's script)
"""
from kit import (VM, El, Anim, Layer, use, box, absolute, solid, line, icon_slot, nested_icon, paint_names, pose,
                 choice_layer, bool_layer, gate_layer, press_layer, hover_listeners, listener, fire, set_to, machine,
                 component, color, icon_ref, if_bool, swap_layer, spin_layer, CLEAR, FADE, HOVER_MS)

COLORS = ("Primary", "Grey", "Dark grey", "Light", "Dark")
# the icon, by color (DS: Primary #F56D41, Grey and Dark grey #5D6068, Light white, Dark #272B35)
ICON_COLOR = [color("Custom Branding/Primary-color"), color("Icons/icon-color"), color("Icons/icon-color"),
              color("Icons/icon-light-color"), color("Icons/icon-dark-color")]
# the tile behind the icon on hover (and Selected), by color
HOVER = [color("Custom Branding/primary-12% (hover ghost)"), color("Backgrounds/bg-med-grey-color"),
         color("Backgrounds/bg-bold-grey-color"), color("Backgrounds/bg-white-10-opacity"),
         color("Backgrounds/bg-black-4-opacity")]
# Type=Box: the tile at rest (Dark: black 4 %, hover 8 % = this + the hover tile)
TILE = [color("Custom Branding/primary-12% (hover ghost)"), color("Backgrounds/bg-grey-color"),
        color("Backgrounds/bg-med-grey-color"), color("Backgrounds/bg-white-10-opacity"),
        color("Backgrounds/bg-black-4-opacity")]
SPINNER = [color("Icons/icon-color")] * 3 + [color("Icons/icon-light-color"), color("Icons/icon-color")]
SPIN_S = 0.8   # one turn of the loading spinner

IB = VM("ib", "Icon button", [
    ("icon", "artboard", icon_ref("i_plus")), ("variant", "number", 0), ("size", "number", 1), ("color", "number", 0),
    ("border", "boolean", False),
    ("hover", "boolean", False), ("pressed", "boolean", False), ("selected", "boolean", False),
    ("focused", "boolean", False), ("disabled", "boolean", False), ("loading", "boolean", False),
    ("hoverAnimated", "boolean", False), ("interactive", "boolean", False),
    ("click", "trigger", None), ("clicked", "trigger", None),
    ("_iconColor", "color", ICON_COLOR[0])])


def build():
    use(IB)
    n = "IconButton"
    r = 6   # DS: radius 6 in every size
    glyph = box(f"{n}.glyph", [nested_icon(f"{n}.icon", "icon", "_iconColor", "i_plus")], origin=(0.5, 0.5),
                w=16, h=16, layoutWidthScaleType="fixed", layoutHeightScaleType="fixed")
    spin = icon_slot(f"{n}.spinner", "common_actions/i_spinner", SPINNER[0], origin=(0.5, 0.5))
    spin_wrap = absolute(f"{n}.spinWrap", [spin], opacity=0, layoutTypeValue="stack", layoutAlignmentType="center")
    fx = lambda part, col: absolute(f"{n}.{part}", paints=[solid(f"{n}.{part}.fill", col)], opacity=0,  # noqa: E731
                                    cornerRadiusTL=r)
    ring = absolute(f"{n}.ring", paints=[line(f"{n}.ring.stroke", color("Borders/border-color"), 2)], opacity=0,
                    cornerRadiusTL=r)                              # DS Focus: a 2 px stroke on the edge (centre)
    edge = absolute(f"{n}.border", paints=[line(f"{n}.border.stroke", color("Borders/border-color"), 1)],
                    inset=(0.5,) * 4, opacity=0, cornerRadiusTL=r - 0.5)   # DS Border: 1 px inside
    hit = absolute(f"{n}.hit", displayValue="none")
    body = box(f"{n}.box", [hit, ring, edge, glyph, spin_wrap, fx("hoverFx", HOVER[0]), fx("selectedFx", HOVER[0]),
                            fx("tile", TILE[0])],
               origin=(0.5, 0.5), layoutTypeValue="stack", layoutAlignmentType="center", cornerRadiusTL=r,
               w=32, h=32, layoutWidthScaleType="fixed", layoutHeightScaleType="fixed")

    spin_paints = paint_names(spin)
    color_l = choice_layer("Color", "color", COLORS, [
        (f"{n}.hoverFx.fill.color", "colorValue", *HOVER), (f"{n}.selectedFx.fill.color", "colorValue", *HOVER),
        (f"{n}.tile.fill.color", "colorValue", *TILE)] + [(p, "colorValue", *SPINNER) for p in spin_paints],
        actions={c: [set_to("Color", "_iconColor", ICON_COLOR[i])] for i, c in enumerate(COLORS)})
    size_l = choice_layer("Size", "size", ("Small", "Large"), [(f"{n}.box", "width", 24, 32),
                                                               (f"{n}.box", "height", 24, 32)])
    variant_l = choice_layer("Type", "variant", ("Icon", "Box"), [(f"{n}.tile", "opacity", 0, 1)])
    border_l = bool_layer("Border", "border", [(f"{n}.border", "opacity", 0, 1)], ms=0)

    # hover: the tile fades in (DS); with hoverAnimated the icon also nods (DS "Hover Animated": the product's
    # IconButton.animate, 0.4 s: 110 % and -8 deg at the middle, back to rest)
    hover_looks = [(f"{n}.hoverFx", "opacity", 0, 1)]
    hover = Layer("Hover")
    pulse = Anim("Hover pulse", 0.4)
    pulse.move(f"{n}.hoverFx", "opacity", 0, FADE, 0, 1)
    for p, v in (("scaleX", 1.1), ("scaleY", 1.1), ("rotation", -0.1396)):
        rest = 0 if p == "rotation" else 1
        pulse.move(f"{n}.glyph", p, 0, 0.2, rest, v, "settle").move(f"{n}.glyph", p, 0.2, 0.4, v, rest, "duda")
    hover.state("off", pose("Hover off", hover_looks, 0),
                hover.go("pulse", if_bool("hover", True), if_bool("hoverAnimated", True)),
                hover.go("on", if_bool("hover", True), ms=HOVER_MS, ease="duda"), entry=True)
    hover.state("on", pose("Hover on", hover_looks, 1),
                hover.go("off", if_bool("hover", False), ms=HOVER_MS, ease="duda"))
    hover.state("pulse", pulse, hover.go("on", at_end=True),
                hover.go("off", if_bool("hover", False), ms=HOVER_MS, ease="duda"))
    hover.enter_if("on", if_bool("hover", True))

    selected = bool_layer("Selected", "selected", [(f"{n}.selectedFx", "opacity", 0, 1)])
    focus = bool_layer("Focus", "focused", [(f"{n}.ring", "opacity", 0, 1)])
    disabled = bool_layer("Disabled", "disabled", [(f"{n}.box", "opacity", 1, 0.4)])
    # loading: the icon leaves (fades, shrinks to 80 %), then the spinner arrives on its last visible frame (DS: the
    # spinner in place of the icon; one state at a time)
    load = swap_layer("Loading", [if_bool("loading", True)], [[if_bool("loading", False)]],
                      leave=[(f"{n}.glyph", "opacity", 1, 0), (f"{n}.glyph", "scaleX", 1, 0.8, "duda"),
                             (f"{n}.glyph", "scaleY", 1, 0.8, "duda")],
                      arrive=[(f"{n}.spinWrap", "opacity", 0, 1)])
    spin_l = spin_layer(f"{n}.spinner", SPIN_S)

    press = press_layer(f"{n}.box", 0.9)
    layers = [gate_layer([f"{n}.hit"]), color_l, size_l, variant_l, border_l, hover, selected, focus, press, load,
              spin_l, disabled]
    listeners = hover_listeners(f"{n}.hit", press="pressed") + [listener(f"{n}.hit", "click", fire("clicked"))]
    return component("Icon button", 32, 32, [body], machine(layers, listeners),
                     layout={"layoutWidthScaleType": "hug", "layoutHeightScaleType": "hug"})
