"""CoreDropdown, Type Text (DS: page "Inputs & Dropdowns", 151100:187097; the field .TextDropdown 151091:183681).
The menu that opens under it is a p.menu() of the piece (DS .CoreDropdwonMenu 154464:68205).

DS props -> view model "CoreDropdown":
  the label               label / showLabel      (Regular 13/18, 8 px over the field)
  the chosen text         value; placeholder     (Regular 14/20; the placeholder while value is empty)
  Prefix content          prefix / prefixIcon    (a 16 px icon before the text)
  Open                    open                   (the edge darkens, the chevron turns over: 200 ms, duda)
  State                   disabled, error        (Empty / Active are the value being empty or not; Focus is open)
  (not here yet)          MultiSelect, Color, Icon, Text Groups types; Read-only
"""
import os

from kit import (VM, use, box, absolute, solid, line, text, text_style, hug, fill_w, nested_icon, icon, match_layer,
                 bool_layer, machine, component, color, icon_ref, if_bool, if_text, hex_argb, El, ICONS, WHITE)

INK = color("Typography/primary-text-color")
HINT = hex_argb("#9b9ba2")
EDGE, EDGE_ON, RED = hex_argb("#e2e2e4"), hex_argb("#cfcfd3"), hex_argb("#ac1616")
CHEV = color("Typography/secondary-text-color")

DD = VM("dd", "CoreDropdown", [
    ("label", "string", "Label"), ("showLabel", "boolean", True), ("value", "string", ""),
    ("placeholder", "string", "Select"), ("prefix", "boolean", False), ("prefixIcon", "artboard", icon_ref("i_site")),
    ("open", "boolean", False), ("disabled", "boolean", False), ("error", "boolean", False),
    ("_fg", "color", INK)])


def build():
    use(DD)
    n = "Dropdown"
    text_style("ddLabel", "Content/Body", INK)          # Regular 13/18
    text_style("ddValue", "Content/Body 14", INK)       # Regular 14/20
    text_style("ddPh", "Content/Body 14", HINT)
    label = box(f"{n}.labelRow", [text(f"{n}.label", [("ddLabel", "=label")], lp=hug(), wrap=False)],
                paddingBottom=8, **fill_w())
    prefix = box(f"{n}.prefix", [nested_icon(f"{n}.icon", "prefixIcon", "_fg", "i_site")], displayValue="none",
                 **hug())
    area = box(f"{n}.area", [text(f"{n}.value", [("ddValue", "=value")], lp=fill_w(), overflow="ellipsis", wrap=False),
                             text(f"{n}.ph", [("ddPh", "=placeholder")], lp=fill_w(), overflow="ellipsis",
                                  wrap=False)], layoutTypeValue="stack", layoutAlignmentType="centerLeft", **fill_w())
    # the chevron turns about its centre: a Node at the slot's centre holds the icon drawn around it
    art = icon(os.path.join(ICONS, "arrows", "chevron_bottom.svg"), f"{n}.chev.art", CHEV, stroke_w=1.5, x=-8, y=-8)
    chev = box(f"{n}.chev", [El("Node", {"x": 8, "y": 8}, [art], name=f"{n}.chevTurn")], w=16, h=16,
               layoutWidthScaleType="fixed", layoutHeightScaleType="fixed")
    edge = absolute(f"{n}.border", paints=[line(f"{n}.border.stroke", EDGE, 1)], inset=(0.5,) * 4,
                    cornerRadiusTL=5.5)
    field = box(f"{n}.field", [edge, prefix, area, chev], paints=[solid(f"{n}.field.fill", WHITE)], clip=True,
                flexDirectionValue="row", layoutAlignmentType="centerLeft", gapHorizontal=8, paddingLeft=8,
                paddingRight=8, cornerRadiusTL=6, h=35, layoutWidthScaleType="fill", layoutHeightScaleType="fixed")
    col = box(f"{n}.col", [label, field], flexDirectionValue="column", layoutAlignmentType="topLeft",
              layoutWidthScaleType="fill", layoutHeightScaleType="hug")

    edge_l = match_layer("Edge", [("rest", [if_bool("error", False), if_bool("open", False)]),
                                  ("open", [if_bool("error", False), if_bool("open", True)]),
                                  ("error", [if_bool("error", True)])],
                         [(f"{n}.border.stroke.color", "colorValue", EDGE, EDGE_ON, RED)], ms=200)
    turn = bool_layer("Open", "open", [(f"{n}.chevTurn", "rotation", 0, 3.14159)], ms=200)
    filled = match_layer("Value", [("empty", [if_text("value", "equal")]), ("filled", [if_text("value", "notEqual")])],
                         [(f"{n}.value", "opacity", 0, 1), (f"{n}.ph", "opacity", 1, 0)])
    layers = [edge_l, turn, filled,
              bool_layer("Label", "showLabel", [(f"{n}.labelRow.style", "displayValue", "none", "flex")], ms=0),
              bool_layer("Prefix", "prefix", [(f"{n}.prefix.style", "displayValue", "none", "flex")], ms=0),
              bool_layer("Disabled", "disabled", [(f"{n}.field", "opacity", 1, 0.4)])]
    return component("CoreDropdown", 240, 61, [col], machine(layers),
                     layout={"layoutWidthScaleType": "fixed", "layoutHeightScaleType": "hug"})
