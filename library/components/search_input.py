"""SearchInput (DS: page "Inputs", SearchInput).

DS props -> view model "SearchInput":
  placeholder, value      placeholder ("Search by") / value; typed: how much of `value` shows (as in CoreInput: a
                          piece types it; 999 = all of it)
  State: Focus            focused (the caret blinks; the edge darkens; the x shows)
  State: Value            the value shown (the edge stays dark and the x stays)
  State: Disabled         disabled (the content at 40 %)
  (not here yet)          interactive: no real text field yet (CoreInput has one)
"""
from kit import (VM, use, box, absolute, solid, line, text_style, fill_w, icon_slot, match_layer,
                 bool_layer, machine, component, color, if_bool, if_num, if_text, STYLES, WHITE, HOVER_MS)
from components.core_input import typing, TYPED_ON

INK = color("Typography/primary-text-color")   # the value (#272B35)
HINT = color("grey-500")                       # the placeholder (#9B9BA2, as the DS component)
ICON = color("grey-600")                       # the search and x icons (#5D6068)
EDGE = color("grey-300")                       # #E2E2E4
EDGE_ON = color("grey-400")                    # focused or filled: #CFCFD3

SEARCH = VM("search", "SearchInput", [
    ("placeholder", "string", "Search by"), ("value", "string", ""), ("typed", "number", 999),
    ("focused", "boolean", False), ("disabled", "boolean", False)])


def build():
    use(SEARCH)
    n = "SearchInput"
    text_style("siValue", "Content/Body", INK)
    text_style("siPh", "Content/Body", HINT)
    text_style("siCaret", "Content/Body", INK, font="caret")
    STYLES["siCaret"]["weight"] = None   # the caret font has no weight axis
    typed, caret_typed, caret_end, ph, typing_layers = typing(n, "siValue", "siPh", "siCaret")
    area = box(f"{n}.area", [caret_typed, caret_end, typed, ph], layoutTypeValue="stack",
               layoutAlignmentType="centerLeft", **fill_w())
    glass = icon_slot(f"{n}.glass", "common_actions/i_search", ICON)
    clear = icon_slot(f"{n}.clear", "common_actions/i_x", ICON, size=14, slot=16, opacity=0)
    # the x keeps its place when hidden: nothing reflows as it shows
    content = box(f"{n}.content", [glass, area, clear], flexDirectionValue="row", layoutAlignmentType="centerLeft",
                  gapHorizontal=8, **fill_w())
    edge = absolute(f"{n}.border", paints=[line(f"{n}.border.stroke", EDGE, 1)], inset=(0.5,) * 4,
                    cornerRadiusTL=16.5)
    field = box(f"{n}.field", [edge, content], paints=[solid(f"{n}.field.fill", WHITE)], clip=True,
                flexDirectionValue="row", layoutAlignmentType="centerLeft", paddingLeft=16, paddingRight=16,
                cornerRadiusTL=17, h=34, layoutWidthScaleType="fill", layoutHeightScaleType="fixed")

    filled = [if_num("typed", "greaterThanOrEqual", TYPED_ON), if_text("value", "notEqual", converter="conv.trim")]
    cases = [("rest", [if_bool("focused", False), if_num("typed", "lessThan", TYPED_ON)]),
             ("rest empty", [if_bool("focused", False), if_num("typed", "greaterThanOrEqual", TYPED_ON),
                             if_text("value", "equal", converter="conv.trim")]),
             ("focus", [if_bool("focused", True)]),
             ("filled", [if_bool("focused", False)] + filled)]
    edge_l = match_layer("Edge", cases, [(f"{n}.border.stroke.color", "colorValue", EDGE, EDGE, EDGE_ON, EDGE_ON),
                                         (f"{n}.clear", "opacity", 0, 0, 1, 1)], ms=HOVER_MS)
    ph_l, mode, caret = typing_layers()
    disabled = bool_layer("Disabled", "disabled", [(f"{n}.content", "opacity", 1, 0.4)])
    return component("SearchInput", 248, 34, [field], machine([edge_l, ph_l, mode, caret, disabled]),
                     layout={"layoutWidthScaleType": "fixed", "layoutHeightScaleType": "hug"})
