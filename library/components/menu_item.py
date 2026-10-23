""".MenuListItem / .DropdownItem (DS: page "Menues & Navigation", 140383:36319; page "Inputs & Dropdowns",
154464:60818): one row of a CoreFloatingMenu or a dropdown menu (a 32 px ListItem). A piece builds the whole menu
with p.menu().

DS props -> view model "MenuListItem":
  the text                label        (Regular 14/20)
  the icon                showIcon / icon (artboard, default Icon/i_site)
  State: Hover            hover        (fill #F5F5F7)
  (product)               selected     (fill #F5F5F7 and a check at the end, as a dropdown shows the chosen one)
  (product)               destructive  (the text and icon in the negative colour: Delete)
  (not here yet)          Hierarchy 2nd..4th, the checkbox prefix of a multi-select dropdown
  (prototype)             interactive; clicked
"""
from kit import (VM, use, box, absolute, solid, text, text_style, fill_w, icon_slot, nested_icon, paint_names,
                 bool_layer, match_layer, gate_layer, hover_listeners, listener, fire, machine, component, color,
                 icon_ref, hex_argb, set_to, if_bool)

INK = color("Typography/primary-text-color")
RED = hex_argb("#ac1616")
ICON = color("Typography/primary-text-color")

MI = VM("mi", "MenuListItem", [
    ("label", "string", "List item"), ("showIcon", "boolean", False), ("icon", "artboard", icon_ref("i_site")),
    ("hover", "boolean", False), ("selected", "boolean", False), ("destructive", "boolean", False),
    ("interactive", "boolean", False), ("clicked", "trigger", None), ("_fg", "color", ICON)])


def build():
    use(MI)
    n = "MenuItem"
    text_style("miLabel", "Content/Body 14", INK)       # Regular 14/20
    icon = box(f"{n}.iconWrap", [nested_icon(f"{n}.icon", "icon", "_fg", "i_site")], displayValue="none",
               layoutWidthScaleType="hug", layoutHeightScaleType="hug")
    label = text(f"{n}.label", [("miLabel", "=label")], lp=fill_w(), overflow="ellipsis", wrap=False)
    check = icon_slot(f"{n}.check", "general/i_checkmark", INK, opacity=0)
    fx = absolute(f"{n}.hoverFx", paints=[solid(f"{n}.hoverFx.fill", hex_argb("#f5f5f7"))], opacity=0,
                  cornerRadiusTL=8)
    sel = absolute(f"{n}.selFx", paints=[solid(f"{n}.selFx.fill", hex_argb("#f5f5f7"))], opacity=0, cornerRadiusTL=8)
    hit = absolute(f"{n}.hit", displayValue="none")
    body = box(f"{n}.box", [hit, icon, label, check, fx, sel], paints=[solid(f"{n}.fill", hex_argb("#ffffff"))],
               flexDirectionValue="row", layoutAlignmentType="centerLeft", gapHorizontal=12, paddingLeft=8,
               paddingTop=6, paddingRight=4, paddingBottom=6, cornerRadiusTL=8, h=32, layoutWidthScaleType="fill",
               layoutHeightScaleType="fixed")
    layers = [gate_layer([f"{n}.hit"]),
              bool_layer("Icon", "showIcon", [(f"{n}.iconWrap.style", "displayValue", "none", "flex")], ms=0),
              # the icon takes its colour from the view model, so the state sets it as it starts
              match_layer("Destructive", [("normal", [if_bool("destructive", False)]),
                                          ("destructive", [if_bool("destructive", True)])],
                          [(f"{n}.label.miLabel.color", "colorValue", INK, RED)]
                          + [(p, "colorValue", INK, RED) for p in paint_names(check)],
                          actions={"normal": [set_to("Color", "_fg", ICON)],
                                   "destructive": [set_to("Color", "_fg", RED)]}),
              bool_layer("Selected", "selected", [(f"{n}.selFx", "opacity", 0, 1), (f"{n}.check", "opacity", 0, 1)]),
              bool_layer("Hover", "hover", [(f"{n}.hoverFx", "opacity", 0, 1)])]
    listeners = hover_listeners(f"{n}.hit") + [listener(f"{n}.hit", "click", fire("clicked"))]
    return component("MenuListItem", 192, 32, [body], machine(layers, listeners),
                     layout={"layoutWidthScaleType": "fixed", "layoutHeightScaleType": "hug"})
