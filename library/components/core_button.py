"""CoreButton (DS: page "Buttons", 126717:80997) with its three types: PrimaryButton (3:2158), SecondaryButton
(569:6680) and TextButton (569:6898).

DS props -> view model "CoreButton":
  Type                       variant        0 PrimaryButton, 1 SecondaryButton, 2 TextButton ("type" is a Luau keyword)
  Size                       size           0 Small (26), 1 Regular (32), 2 Large (40); TextButton: Small 18, Regular 20
  Color                      color          by type, in the DS order:
                                              Primary   0 Brand, 1 Dark, 2 Upgrade, 3 Destructive
                                              Secondary 0 Grey, 1 Light transparent, 2 Upgrade, 3 Dark transparent
                                              Text      0 Brand, 1 Secondary, 2 Dark, 3 Light
  Text                       label
  Left Icon / Show Left Icon     leftIcon (artboard) / showLeftIcon
  Right Icon / Show Right Icon   rightIcon (artboard) / showRightIcon
  State                      hover, selected, focused, disabled, loading (booleans); pressed (polish)
  (product)                  minWidth: the button never gets narrower (the floating bar's Edit is 72)
  (prototype)                interactive, clicked, click (as in Icon button)
"""
from kit import (VM, El, use, box, absolute, solid, line, text, text_style, hug, icon_slot, nested_icon,
                 paint_names, pose, match_layer, bool_layer, gate_layer, press_layer, hover_listeners, listener, fire,
                 set_to, machine, component, color, icon_ref, bind_style, if_bool, if_num, argb, hex_argb, swap_layer,
                 spin_layer, CLEAR, WHITE)

P = color("Custom Branding/Primary-color")
BLACK = lambda a: argb("#000000", a)    # noqa: E731
WHITE_A = lambda a: argb("#FFFFFF", a)  # noqa: E731
TYPES = ("Primary", "Secondary", "Text")
COLOR_NAMES = {0: ("Brand", "Dark", "Upgrade", "Destructive"),
               1: ("Grey", "Light transparent", "Upgrade", "Dark transparent"),
               2: ("Brand", "Secondary", "Dark", "Light")}
# (fill, hover tile, selected tile, focus ring, text, text on hover), read from the DS variants (Regular size).
# A tile is drawn over the fill, so a see-through hover is the extra that makes the DS value
# (Light transparent: white 10 % -> 20 % is 11.1 % more; Dark transparent: black 4 % -> 8 % is 4.17 % more).
LOOK = {
    (0, 0): (P, BLACK(0.10), BLACK(0.30), color("Custom Branding/primary-40% (disabled)"), WHITE, WHITE),
    (0, 1): (color("Custom Branding/dark-primary-color"), BLACK(0.10), BLACK(0.30),
             color("Backgrounds/bg-bold-grey-color"), WHITE, WHITE),
    # Upgrade Selected: positive-med under black 30 % (DS), drawn as the colour it makes
    (0, 2): (color("Indications/positive-color"), BLACK(0.10), hex_argb("#184C35"),
             color("Indications/positive-subtle-color"), WHITE, WHITE),
    (0, 3): (color("Indications/negative-color"), color("Indications/negative-med-color"),
             color("Indications/negative-dark-color"), color("Indications/negative-subtle-color"), WHITE, WHITE),
    (1, 0): (color("Backgrounds/bg-med-grey-color"), color("Backgrounds/bg-bold-grey-color"),
             color("Backgrounds/bg-bold-grey-color"), color("Borders/border-color"),
             color("Typography/primary-text-color"), color("Typography/primary-text-color")),
    (1, 1): (color("Backgrounds/bg-white-10-opacity"), WHITE_A(0.111), WHITE_A(0.111),
             color("Borders/border-dark-color"), WHITE, WHITE),
    (1, 2): (color("Indications/positive-light-color"), color("Indications/positive-subtle-color"),
             color("Indications/positive-subtle-color"), color("Indications/positive-subtle-color"),
             color("Indications/positive-color"), color("Indications/positive-color")),
    (1, 3): (color("Backgrounds/bg-black-4-opacity"), BLACK(0.0417), BLACK(0.0417), color("Borders/border-color"),
             argb("#000000"), argb("#000000")),
    # TextButton: no fill; hover changes the text (Brand: black 8 % over it, Dark: white 20 %, Light: black 20 %)
    (2, 0): (CLEAR, CLEAR, CLEAR, color("Borders/border-color"), P, hex_argb("#E1643C")),
    (2, 1): (CLEAR, CLEAR, CLEAR, color("Borders/border-color"), color("Typography/secondary-text-color"),
             color("Typography/primary-text-color")),
    (2, 2): (CLEAR, CLEAR, CLEAR, color("Borders/border-color"), color("Typography/primary-text-color"),
             hex_argb("#52555D")),
    (2, 3): (CLEAR, CLEAR, CLEAR, color("Borders/border-color"), WHITE, hex_argb("#CCCCCC")),
}

CB = VM("cb", "CoreButton", [
    ("label", "string", "Button"), ("variant", "number", 0), ("size", "number", 1), ("color", "number", 0),
    ("showLeftIcon", "boolean", False), ("leftIcon", "artboard", icon_ref("i_plus")),
    ("showRightIcon", "boolean", False), ("rightIcon", "artboard", icon_ref("i_arrow_right")),
    ("minWidth", "number", 0),
    ("hover", "boolean", False), ("pressed", "boolean", False), ("selected", "boolean", False),
    ("focused", "boolean", False), ("disabled", "boolean", False), ("loading", "boolean", False),
    ("interactive", "boolean", False), ("click", "trigger", None), ("clicked", "trigger", None),
    ("_fg", "color", WHITE), ("_fgHover", "color", WHITE)])


def build():
    use(CB)
    n = "CoreButton"
    text_style("cbLabel", "Headlines/He 2", WHITE)
    text_style("cbHover", "Headlines/He 2", WHITE)

    def side(s, default):
        # the icon twice: as it rests and in its hover colour (only TextButton changes it), cross-faded on hover
        return box(f"{n}.{s}", [nested_icon(f"{n}.{s}Hover", f"{s}Icon", "_fgHover", default),
                                nested_icon(f"{n}.{s}Base", f"{s}Icon", "_fg", default)],
                   layoutTypeValue="stack", displayValue="none", w=16, h=16, layoutWidthScaleType="fixed",
                   layoutHeightScaleType="fixed")
    label = box(f"{n}.labelWrap", [text(f"{n}.labelHover", [("cbHover", "=label")], lp=hug(), wrap=False,
                                        opacity=0),
                                   text(f"{n}.label", [("cbLabel", "=label")], lp=hug(), wrap=False)],
                layoutTypeValue="stack", layoutAlignmentType="center", paddingLeft=2, paddingRight=2, **hug())
    content = box(f"{n}.content", [side("left", "i_plus"), label, side("right", "i_arrow_right")],
                  flexDirectionValue="row", layoutAlignmentType="center", gapHorizontal=2, **hug())
    spin = icon_slot(f"{n}.spinner", "common_actions/i_spinner", WHITE, origin=(0.5, 0.5))
    spin_wrap = absolute(f"{n}.spinWrap", [spin], opacity=0, layoutTypeValue="stack", layoutAlignmentType="center")
    fx = lambda part: absolute(f"{n}.{part}", paints=[solid(f"{n}.{part}.fill", CLEAR)], opacity=0,  # noqa: E731
                               cornerRadiusTL=6)
    # DS Focus: a 2 px stroke outside the button (a 2 px stroke centred 1 px out)
    ring = absolute(f"{n}.ring", paints=[line(f"{n}.ring.stroke", CLEAR, 2)], inset=(-1,) * 4, opacity=0,
                    cornerRadiusTL=7)
    hit = absolute(f"{n}.hit", displayValue="none")
    body = box(f"{n}.box", [hit, ring, content, spin_wrap, fx("hoverFx"), fx("selectedFx")],
               paints=[solid(f"{n}.fill", P)], origin=(0.5, 0.5), flexDirectionValue="row",
               layoutAlignmentType="center", cornerRadiusTL=6, paddingTop=6, paddingBottom=6, paddingLeft=8,
               paddingRight=8, minWidth=0, **hug())
    bind_style(body, "minWidth", "minWidth")   # (the style needs a minWidth in points for the bind to take)

    # Type x Color: one look per pair (12), and the icon colours for the nested icons
    cases, rows, acts = [], [], {}
    for (v, c), look in LOOK.items():
        st = f"{TYPES[v]} {COLOR_NAMES[v][c]}"
        cases.append((st, [if_num("variant", "equal", v), if_num("color", "equal", c)]))
        rows.append(look)
        acts[st] = [set_to("Color", "_fg", look[4]), set_to("Color", "_fgHover", look[5])]
    spin_paints = paint_names(spin)
    looks = [(f"{n}.fill.color", "colorValue", *[r[0] for r in rows]),
             (f"{n}.hoverFx.fill.color", "colorValue", *[r[1] for r in rows]),
             (f"{n}.selectedFx.fill.color", "colorValue", *[r[2] for r in rows]),
             (f"{n}.ring.stroke.color", "colorValue", *[r[3] for r in rows]),
             (f"{n}.label.cbLabel.color", "colorValue", *[r[4] for r in rows]),
             (f"{n}.labelHover.cbHover.color", "colorValue", *[r[5] for r in rows])]
    looks += [(p, "colorValue", *[r[4] for r in rows]) for p in spin_paints]
    look_l = match_layer("Type and color", cases, looks, actions=acts)

    # Size x (TextButton or not): paddings, corner, text size. DS: Small 26 (pad 4/6 + 2 around the text, He 4
    # 12/18), Regular 32 (pad 6/8 + 2, He 2 14/20), Large 40 (pad 10/12 + 2, radius 8); TextButton: no padding,
    # the height of its line
    sizes = [("Small", 0, False, (4, 6, 6, 12, 18)), ("Regular", 1, False, (6, 8, 6, 14, 20)),
             ("Large", 2, False, (10, 12, 8, 14, 20)), ("Text small", 0, True, (0, 0, 4, 12, 18)),
             ("Text regular", 1, True, (0, 0, 4, 14, 20))]
    s_cases = []
    for st, sz, is_text, _ in sizes:
        conds = [if_num("variant", "equal" if is_text else "notEqual", 2)]
        if is_text and sz == 1:
            conds.append(if_num("size", "notEqual", 0))   # TextButton has no Large: Large reads as Regular
        else:
            conds.append(if_num("size", "equal", sz))
        s_cases.append((st, conds))
    vals = [v for *_, v in sizes]
    s_looks = [(f"{n}.box.style", "paddingTop", *[v[0] for v in vals]),
               (f"{n}.box.style", "paddingBottom", *[v[0] for v in vals]),
               (f"{n}.box.style", "paddingLeft", *[v[1] for v in vals]),
               (f"{n}.box.style", "paddingRight", *[v[1] for v in vals])]
    for part in ("box", "hoverFx", "selectedFx"):
        s_looks.append((f"{n}.{part}.style", "cornerRadiusTL", *[v[2] for v in vals]))
    s_looks.append((f"{n}.ring.style", "cornerRadiusTL", *[v[2] + 1 for v in vals]))
    for st in ("label.cbLabel", "labelHover.cbHover"):
        s_looks += [(f"{n}.{st}", "fontSize", *[v[3] for v in vals]), (f"{n}.{st}", "lineHeight", *[v[4] for v in vals])]
    size_l = match_layer("Size", s_cases, s_looks)

    left = bool_layer("Left icon", "showLeftIcon", [(f"{n}.left.style", "displayValue", "none", "flex")], ms=0)
    right = bool_layer("Right icon", "showRightIcon", [(f"{n}.right.style", "displayValue", "none", "flex")], ms=0)
    hover = bool_layer("Hover", "hover", [(f"{n}.hoverFx", "opacity", 0, 1), (f"{n}.labelHover", "opacity", 0, 1),
                                          (f"{n}.leftHover.slot", "opacity", 0, 1),
                                          (f"{n}.rightHover.slot", "opacity", 0, 1)])
    selected = bool_layer("Selected", "selected", [(f"{n}.selectedFx", "opacity", 0, 1)])
    focus = bool_layer("Focus", "focused", [(f"{n}.ring", "opacity", 0, 1)])
    disabled = bool_layer("Disabled", "disabled", [(f"{n}.box", "opacity", 1, 0.4)])
    # loading: the label leaves, then the spinner arrives on its last visible frame (one state at a time); the
    # button keeps its width (polish: the DS Loading variant is 40 wide, which would jump the layout)
    load = swap_layer("Loading", [if_bool("loading", True)], [[if_bool("loading", False)]],
                      leave=[(f"{n}.content", "opacity", 1, 0)], arrive=[(f"{n}.spinWrap", "opacity", 0, 1)])
    spin_l = spin_layer(f"{n}.spinner")
    press = press_layer(f"{n}.box", 0.96)
    layers = [gate_layer([f"{n}.hit"]), look_l, size_l, left, right, hover, selected, focus, press, load, spin_l,
              disabled]
    listeners = hover_listeners(f"{n}.hit", press="pressed") + [listener(f"{n}.hit", "click", fire("clicked"))]
    return component("CoreButton", 120, 32, [body], machine(layers, listeners),
                     layout={"layoutWidthScaleType": "hug", "layoutHeightScaleType": "hug"})
