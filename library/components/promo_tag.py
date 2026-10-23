"""Promotional Tag (DS: page "Tags & status", 118669:13683).

DS props -> view model "Promotional Tag":
  Type                    type     0 Default (the text in an orange outline), 1 Premium (green circle), 2 AI (lilac
                                   circle, gradient star), 3 New dot indicator (8 px orange dot)
  the text                label    ("new"; Bold 10/14, as the DS)
"""
import os

from kit import (VM, use, box, absolute, line, text, text_style, hug, icon, shape_ellipse, choice_layer, machine,
                 component, hex_argb, ART)

ORANGE = hex_argb("#f56d41")
TYPES = ("Default", "Premium", "AI", "New dot")

PROMO = VM("promo", "Promotional Tag", [("type", "number", 0), ("label", "string", "new")])


def fixed_box(name, kids, w, h, **st):
    return box(name, kids, w=w, h=h, layoutWidthScaleType="fixed", layoutHeightScaleType="fixed", **st)


def build():
    use(PROMO)
    n = "PromoTag"
    text_style("promoLabel", None, ORANGE, size=10, lh=14, weight=700)
    edge = absolute(f"{n}.edge", paints=[line(f"{n}.edge.stroke", ORANGE, 1)], inset=(0.5,) * 4, cornerRadiusTL=3.5)
    tag = box(f"{n}.text", [edge, text(f"{n}.label", [("promoLabel", "=label")], lp=hug(), wrap=False)],
              flexDirectionValue="row", layoutAlignmentType="center", paddingTop=2, paddingRight=6, paddingBottom=2,
              paddingLeft=6, cornerRadiusTL=4, **hug())
    premium = fixed_box(f"{n}.premium", [icon(os.path.join(ART, "promo_premium.svg"), f"{n}.premium.art", ORANGE)],
                        16, 16, displayValue="none")
    ai = fixed_box(f"{n}.ai", [icon(os.path.join(ART, "promo_ai.svg"), f"{n}.ai.art", ORANGE)], 16, 16,
                   displayValue="none")
    dot = fixed_box(f"{n}.dot", [shape_ellipse(f"{n}.dotShape", 8, fill=ORANGE, x=4, y=4)], 8, 8, displayValue="none")
    body = box(f"{n}.box", [tag, premium, ai, dot], flexDirectionValue="row", layoutAlignmentType="center", **hug())
    parts = (f"{n}.text", f"{n}.premium", f"{n}.ai", f"{n}.dot")
    type_l = choice_layer("Type", "type", TYPES, [
        (f"{p}.style", "displayValue", *["flex" if i == j else "none" for j in range(len(TYPES))])
        for i, p in enumerate(parts)])
    return component("Promotional Tag", 35, 18, [body], machine([type_l]),
                     layout={"layoutWidthScaleType": "hug", "layoutHeightScaleType": "hug"})
