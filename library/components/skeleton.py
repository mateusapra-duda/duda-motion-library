"""Skeleton: the loading placeholder of the Duda dashboard (my.duda.co, the Performance pages: AEO Highlights,
Visibility, Traffic..., seen 2026-10-23). A grey block (Backgrounds/bg-med-grey #EDEDEE) that a soft light band
crosses every 1.4 s, the product's shimmer. Not a DS component: made for the AEO report pieces (v06).

View model "Skeleton":
  circle     a round block (a dot, an avatar); else radius 4
  shimmer    the band crosses (on by default); off: a still block
The block fills its placement (p.skeleton(w, h)). The band is 60 % of the block's width and crosses from -60 % to
100 % (layout positions in percent), so a bar of any width shimmers alike.
"""
from kit import (El, VM, Anim, Layer, use, box, color, argb, pose, bool_layer, machine, component, if_bool)

PERIOD = 1.4            # the product's shimmer
BAND = 60               # % of the block's width
GREY = color("Backgrounds/bg-med-grey-color")

SKEL = VM("skel", "Skeleton", [("circle", "boolean", False), ("shimmer", "boolean", True)])


def build():
    use(SKEL)
    n = "Skeleton"
    # the band is 3 blocks tall and centred, so its feather softens only its sides (the block clips it); an empty
    # hug box has no height, even with top and bottom set; a feathered fill draws only under the clockwise rule
    glow = El("Fill", {"fillRule": "clockwise"}, [
        El("SolidColor", {"colorValue": argb("#FFFFFF", 0.65)}, name=f"{n}.band.fill.color"),
        El("Feather", {"strength": 18}, name=f"{n}.band.feather")], name=f"{n}.band.fill")
    band = box(f"{n}.band", paints=[glow], w=BAND, h=300, positionTypeValue="absolute", positionLeft=-BAND,
               positionLeftUnitsValue="percent", positionTop=-100, positionTopUnitsValue="percent",
               widthUnitsValue="percent", heightUnitsValue="percent", layoutWidthScaleType="fixed",
               layoutHeightScaleType="fixed")
    block = box(f"{n}.block", [band], paints=[El("Fill", {}, [El("SolidColor", {"colorValue": GREY},
                                                                 name=f"{n}.block.fill.color")], name=f"{n}.block.fill")],
                clip=True, cornerRadiusTL=4, layoutWidthScaleType="fill", layoutHeightScaleType="fill")
    circle = bool_layer("Circle", "circle", [(f"{n}.block.style", "cornerRadiusTL", 4, 999)], ms=0)

    lay = Layer("Shimmer")
    a = Anim("Shimmer", PERIOD, loop=True)
    a.hold(f"{n}.band", "opacity", 1)
    a.move(f"{n}.band.style", "positionLeft", 0, PERIOD, -BAND, 100)
    still = pose("Shimmer off", [(f"{n}.band", "opacity", 0, 0)], 0)
    lay.state("on", a, lay.go("off", if_bool("shimmer", False)), entry=True)
    lay.state("off", still, lay.go("on", if_bool("shimmer", True)))
    lay.enter_if("off", if_bool("shimmer", False))
    return component("Skeleton", 120, 16, [block], machine([circle, lay]))
