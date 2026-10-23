"""Smart_Tag (DS: page "Tags & status", 125960:113167).

DS props -> view model "Smart_Tag":
  the text          label
  Size: 26 | 20     size          0 Small (20), 1 Regular (26)
  Radius: 6px|Full  radius        0 6 px, 1 Full
  Color             color         0 Grey, 1 White, 2 Primary
  Prefix            prefix        shows the prefix icon; prefixIcon (artboard, default Icon/i_site)
  Remove btn        removeButton  the x at the end
  Border            border
  State: Hover      hover; removeHover (the x's own hover)
  (prototype)       interactive; clicked (the tag), removed (its x)
"""
from kit import (VM, use, box, absolute, solid, line, text, text_style, hug, icon_slot, nested_icon, paint_names,
                 match_layer, choice_layer, bool_layer, gate_layer, hover_listeners, listener, fire, set_to, machine,
                 component, color, icon_ref, if_num, argb, WHITE)

P = color("Custom Branding/Primary-color")
COLORS = ("Grey", "White", "Primary")
FILL = [color("Backgrounds/bg-grey-color"), WHITE, color("Custom Branding/primary-12% (hover ghost)")]
TEXT = [color("Typography/secondary-text-color"), color("Typography/secondary-text-color"), P]
EDGE = [color("Borders/border-light-color"), color("Borders/border-light-color"), P]
# hover: black 6 % over the tag; Primary goes from primary 12 % to 40 % (31.8 % more over the 12 %)
HOVER = [argb("#000000", 0.06), argb("#000000", 0.06), argb("#F56D41", 0.318)]
X_HOVER = [argb("#000000", 0.08), argb("#000000", 0.08), argb("#FFFFFF", 0.2)]

TAG = VM("tag", "Smart_Tag", [
    ("label", "string", "Tag"), ("size", "number", 1), ("radius", "number", 0), ("color", "number", 0),
    ("prefix", "boolean", False), ("prefixIcon", "artboard", icon_ref("i_site")), ("removeButton", "boolean", True),
    ("border", "boolean", False), ("hover", "boolean", False), ("removeHover", "boolean", False),
    ("interactive", "boolean", False), ("clicked", "trigger", None), ("removed", "trigger", None),
    ("_fg", "color", TEXT[0])])


def build():
    use(TAG)
    n = "SmartTag"
    text_style("tagLabel", "Headlines/He 3", TEXT[0])
    x_icon = icon_slot(f"{n}.x", "common_actions/i_x", TEXT[0], size=12)
    x_hit = absolute(f"{n}.xHit", displayValue="none")
    x_fx = absolute(f"{n}.xFx", paints=[solid(f"{n}.xFx.fill", X_HOVER[0])], opacity=0, cornerRadiusTL=4)
    remove = box(f"{n}.remove", [x_hit, x_icon, x_fx], layoutTypeValue="stack", layoutAlignmentType="center",
                 w=22, h=22, layoutWidthScaleType="fixed", layoutHeightScaleType="fixed")
    prefix = box(f"{n}.prefix", [nested_icon(f"{n}.icon", "prefixIcon", "_fg", "i_site", size=12)],
                 displayValue="none", **hug())
    label = box(f"{n}.labelWrap", [text(f"{n}.label", [("tagLabel", "=label")], lp=hug(), wrap=False)],
                paddingLeft=4, paddingRight=8, paddingBottom=2, **hug())
    edge = absolute(f"{n}.border", paints=[line(f"{n}.border.stroke", EDGE[0], 1)], inset=(0.5,) * 4, opacity=0,
                    cornerRadiusTL=5.5)
    hit = absolute(f"{n}.hit", displayValue="none")
    fx = absolute(f"{n}.hoverFx", paints=[solid(f"{n}.hoverFx.fill", HOVER[0])], opacity=0, cornerRadiusTL=6)
    # flow order: prefix, label, x (the first child draws on top: the border over everything, the hover tile under)
    body = box(f"{n}.box", [edge, prefix, label, remove, hit, fx], paints=[solid(f"{n}.fill", FILL[0])],
               flexDirectionValue="row", layoutAlignmentType="centerLeft", paddingTop=2, paddingRight=2,
               paddingBottom=2, paddingLeft=8, cornerRadiusTL=6, h=26, layoutWidthScaleType="hug",
               layoutHeightScaleType="fixed")

    x_paints = paint_names(x_icon)
    color_l = choice_layer("Color", "color", COLORS, [
        (f"{n}.fill.color", "colorValue", *FILL), (f"{n}.label.tagLabel.color", "colorValue", *TEXT),
        (f"{n}.border.stroke.color", "colorValue", *EDGE), (f"{n}.hoverFx.fill.color", "colorValue", *HOVER),
        (f"{n}.xFx.fill.color", "colorValue", *X_HOVER)] + [(p, "colorValue", *TEXT) for p in x_paints],
        actions={c: [set_to("Color", "_fg", TEXT[i])] for i, c in enumerate(COLORS)})
    # Size x Radius. 26: pad 2/2/2/8, prefix 16, He 3 13/18, x 22 (radius 4 on hover); 20: pad 0/2/0/8, prefix 12,
    # Tiny Bold 12/18, x 16 (a circle). Full: half the height.
    combos = [("Small 6px", 0, 0), ("Small full", 0, 1), ("Regular 6px", 1, 0), ("Regular full", 1, 1)]
    cases = [(st, [if_num("size", "equal", s), if_num("radius", "equal", r)]) for st, s, r in combos]
    h = [20 if s == 0 else 26 for _, s, _ in combos]
    rad = [6 if r == 0 else hh / 2 for (_, _, r), hh in zip(combos, h)]
    small = [s == 0 for _, s, _ in combos]
    looks = [(f"{n}.box", "height", *h),
             (f"{n}.box.style", "paddingTop", *[0 if sm else 2 for sm in small]),
             (f"{n}.box.style", "paddingBottom", *[0 if sm else 2 for sm in small]),
             (f"{n}.box.style", "cornerRadiusTL", *rad), (f"{n}.hoverFx.style", "cornerRadiusTL", *rad),
             (f"{n}.border.style", "cornerRadiusTL", *[r - 0.5 for r in rad]),
             (f"{n}.label.tagLabel", "fontSize", *[12 if sm else 13 for sm in small]),
             (f"{n}.remove", "width", *[16 if sm else 22 for sm in small]),
             (f"{n}.remove", "height", *[16 if sm else 22 for sm in small]),
             (f"{n}.xFx.style", "cornerRadiusTL", *[8 if sm else 4 for sm in small]),
             (f"{n}.icon.slot", "width", *[12 if sm else 16 for sm in small]),
             (f"{n}.icon.slot", "height", *[12 if sm else 16 for sm in small]),
             (f"{n}.icon.scale", "scaleX", *[0.75 if sm else 1 for sm in small]),
             (f"{n}.icon.scale", "scaleY", *[0.75 if sm else 1 for sm in small])]
    size_l = match_layer("Size", cases, looks)
    prefix_l = bool_layer("Prefix", "prefix", [(f"{n}.prefix.style", "displayValue", "none", "flex")], ms=0)
    remove_l = bool_layer("Remove btn", "removeButton", [(f"{n}.remove.style", "displayValue", "none", "flex")], ms=0)
    border_l = bool_layer("Border", "border", [(f"{n}.border", "opacity", 0, 1)], ms=0)
    hover = bool_layer("Hover", "hover", [(f"{n}.hoverFx", "opacity", 0, 1)])
    x_hover = bool_layer("Remove hover", "removeHover", [(f"{n}.xFx", "opacity", 0, 1)])
    layers = [gate_layer([f"{n}.hit", f"{n}.xHit"]), color_l, size_l, prefix_l, remove_l, border_l, hover, x_hover]
    listeners = (hover_listeners(f"{n}.hit") + hover_listeners(f"{n}.xHit", "removeHover") +
                 [listener(f"{n}.hit", "click", fire("clicked")), listener(f"{n}.xHit", "click", fire("removed"))])
    return component("Smart_Tag", 80, 26, [body], machine(layers, listeners),
                     layout={"layoutWidthScaleType": "hug", "layoutHeightScaleType": "hug"})
