"""Loader (DS: page "Loader & progress", 7198:43415).

DS props -> view model "Loader":
  Size: 16 | 24 | 48 | 96   size    0 16px, 1 24px, 2 48px, 3 96px (the DS arc scaled, its stroke too: 0.8 at 16)
  (motion)                  it always turns, one turn per 0.8 s
"""
import os

from kit import El, VM, use, box, icon, choice_layer, spin_layer, machine, component, ART, WHITE

SIZES = (16, 24, 48, 96)

LOADER = VM("loader", "Loader", [("size", "number", 0)])


def build():
    use(LOADER)
    n = "Loader"
    arc = icon(os.path.join(ART, "loader_spinner.svg"), f"{n}.arc", WHITE, x=-8, y=-8)
    spin = El("Node", {}, [arc], name=f"{n}.spin")              # turns about the arc's centre
    scale = El("Node", {"x": 8, "y": 8}, [spin], name=f"{n}.scale")
    body = box(f"{n}.box", [scale], w=16, h=16, layoutWidthScaleType="fixed", layoutHeightScaleType="fixed")
    size_l = choice_layer("Size", "size", tuple(f"{s}px" for s in SIZES), [
        (f"{n}.box", "width", *SIZES), (f"{n}.box", "height", *SIZES),
        (f"{n}.scale", "x", *[s / 2 for s in SIZES]), (f"{n}.scale", "y", *[s / 2 for s in SIZES]),
        (f"{n}.scale", "scaleX", *[s / 16 for s in SIZES]), (f"{n}.scale", "scaleY", *[s / 16 for s in SIZES])])
    return component("Loader", 16, 16, [body], machine([size_l, spin_layer(f"{n}.spin")]),
                     layout={"layoutWidthScaleType": "hug", "layoutHeightScaleType": "hug"})
