"""Text Area (DS: page "Inputs", Text Area 80799:13404, `.text area` 126:2496): a field of several lines, with the
same .label as CoreInput. Quick Edits' Content field (hero storyboards: 358 x 100 under its label).

DS props -> view model "Text Area":
  Label / the label text        showLabel / label; required (a red asterisk), labelIcon (an info icon)
  placeholder, value            placeholder / value; typed: how much of `value` shows (as CoreInput: 0 nothing,
                                999 all of it with the caret at the end). The lines wrap at the field's width
  State                         focused, disabled, readOnly (Empty / Active are the value being empty or not)
  (the corner)                  resize: the resize handle at the bottom right (on by default, as in the product)
The placement gives the size (p.text_area(slot, w=, h=)): the label on top, the field takes the rest.
"""
import os

from kit import (VM, use, box, absolute, solid, line, text_style, fill_w, icon, bool_layer, machine,
                 component, color, STYLES, WHITE, ART)
from components.core_input import label_row, label_layers, typing

INK = color("Typography/primary-text-color")
HINT = color("Typography/hint-color")
RED = color("Indications/negative-color")
BORDER = color("Borders/border-color")
FOCUS = color("Borders/active-border-color")

TA = VM("ta", "Text Area", [
    ("label", "string", "Label"), ("showLabel", "boolean", True), ("required", "boolean", False),
    ("labelIcon", "boolean", False), ("placeholder", "string", "Placeholder"), ("value", "string", ""),
    ("typed", "number", 999), ("focused", "boolean", False), ("disabled", "boolean", False),
    ("readOnly", "boolean", False), ("resize", "boolean", True)])


def build():
    use(TA)
    n = "TextArea"
    text_style("taLabel", "Content/Body", INK)
    text_style("taReq", "Content/Body", RED)
    text_style("taValue", "Content/Body 14", INK)
    text_style("taPh", "Content/Body 14", HINT)
    text_style("taCaret", "Content/Body 14", INK, font="caret")
    STYLES["taCaret"]["weight"] = None   # the caret font has no weight axis
    typed, caret_typed, caret_end, ph, typing_layers = typing(n, "taValue", "taPh", "taCaret", wrap=True)
    area = box(f"{n}.area", [caret_typed, caret_end, typed, ph], layoutTypeValue="stack",
               layoutAlignmentType="topLeft", **fill_w())
    edge = absolute(f"{n}.border", paints=[line(f"{n}.border.stroke", BORDER, 1)], inset=(0.5,) * 4,
                    cornerRadiusTL=5.5)
    ro = absolute(f"{n}.roFill", paints=[solid(f"{n}.roFill.fill", color("Backgrounds/bg-grey-color"))], opacity=0,
                  cornerRadiusTL=6)
    grip = icon(os.path.join(ART, "resize.svg"), f"{n}.grip.art", HINT, stroke_w=1.0, size=8)
    handle = absolute(f"{n}.grip", [grip], inset=(None, None, 3, 3), w=8, h=8, layoutWidthScaleType="fixed",
                      layoutHeightScaleType="fixed")
    fld = box(f"{n}.field", [handle, edge, area, ro], paints=[solid(f"{n}.field.fill", WHITE)], clip=True,
              flexDirectionValue="column", layoutAlignmentType="topLeft", paddingLeft=8, paddingRight=8, paddingTop=8,
              paddingBottom=8, cornerRadiusTL=6, layoutWidthScaleType="fill", layoutHeightScaleType="fill")
    col = box(f"{n}.col", [label_row(n, "taLabel", "taReq"), fld], flexDirectionValue="column",
              layoutAlignmentType="topLeft", layoutWidthScaleType="fill", layoutHeightScaleType="fill")

    ph_l, mode, caret = typing_layers()
    layers = [bool_layer("Focus", "focused", [(f"{n}.border.stroke.color", "colorValue", BORDER, FOCUS)]),
              ph_l, mode, caret,
              bool_layer("Label", "showLabel", [(f"{n}.labelRow.style", "displayValue", "none", "flex")], ms=0),
              *label_layers(n),
              bool_layer("Resize", "resize", [(f"{n}.grip", "opacity", 0, 1)], ms=0),
              bool_layer("Read-only", "readOnly", [(f"{n}.roFill", "opacity", 0, 1),
                                                   (f"{n}.typed.taValue.color", "colorValue", INK,
                                                    color("Typography/secondary-text-color"))]),
              bool_layer("Disabled", "disabled", [(f"{n}.field", "opacity", 1, 0.4),
                                                  (f"{n}.label.taLabel.color", "colorValue", INK, HINT)])]
    return component("Text Area", 358, 126, [col], machine(layers),
                     layout={"layoutWidthScaleType": "fixed", "layoutHeightScaleType": "fixed"})
