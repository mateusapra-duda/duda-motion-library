"""Tooltip (DS: page "Popups & Tooltips", 153020:28706).

DS props -> view model "Tooltip":
  the text                text
  Logic: Max 200 | Hug    hug        False: wraps at 200 px (DS default); True: one line, as wide as the text
  (polish, not in the DS) shown      the tooltip fades in and grows from 96 % (fade token, duda); out it only fades
"""
from kit import (VM, use, box, solid, text, text_style, hug, bool_layer, machine, component, color, WHITE, HOVER_MS)

INK = color("Typography/primary-text-color")    # the tooltip's fill, #272B35

TIP = VM("tip", "Tooltip", [("text", "string", "This is a tooltip."), ("hug", "boolean", False),
                            ("shown", "boolean", True)])


def build():
    use(TIP)
    n = "Tooltip"
    text_style("tipText", "Content/Tiny", WHITE)    # 12/18
    body = box(f"{n}.box", [text(f"{n}.text", [("tipText", "=text")], lp=hug())], origin=(0.5, 1),
               paints=[solid(f"{n}.fill", INK)], flexDirectionValue="column", layoutAlignmentType="topLeft",
               paddingTop=6, paddingRight=12, paddingBottom=6, paddingLeft=12, cornerRadiusTL=8, maxWidth=200,
               **hug())
    # Hug: no 200 px limit (the text still wraps at a line break)
    hug_l = bool_layer("Hug text", "hug", [(f"{n}.box.style", "maxWidth", 200, 4000)], ms=0)
    shown = bool_layer("Shown", "shown", [(f"{n}.box", "opacity", 0, 1), (f"{n}.box", "scaleX", 0.96, 1),
                                          (f"{n}.box", "scaleY", 0.96, 1)], ms=HOVER_MS, ms_off=100)
    return component("Tooltip", 200, 30, [body], machine([hug_l, shown]),
                     layout={"layoutWidthScaleType": "hug", "layoutHeightScaleType": "hug"})
