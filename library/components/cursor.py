"""Cursor: the Vibe page storyboards' arrow (Figma "Vector 27"; not a DS component). Port of pecas/ui-controls v02.

View model "Cursor":
  color, outline      the arrow and its edge (the storyboards' blue and white)
  shadow, shadowColor an optional soft shadow (off: the storyboards have none); shadowColor's alpha is its strength
  click (trigger)     the motion-spec click: 85 % in 3 frames and back in 3, linear
The artboard's origin is the arrow's tip: a piece places (and scales) the cursor by its tip.
"""
from kit import (VM, El, Anim, Layer, use, bind, key, style, pose, bool_layer, machine, if_trigger, argb, parse,
                 points_path, to_vertices, COMPONENTS, ART_POS, WHITE, FPS)

CURSOR = VM("cursor", "Cursor", [("color", "color", argb("#508AF6")), ("outline", "color", WHITE),
                                 ("shadow", "boolean", False), ("shadowColor", "color", argb("#000000", 0.2)),
                                 ("click", "trigger", None)])
# (name, feather strength, offset x, offset y, opacity): the far one at half the strength
SHADOW = (("near", 4, 0.5, 1.5, 1.0), ("far", 9, 2.5, 6, 0.5))
PATH = ("M4.40137 0.861326C2.39866 -0.259764 0.02986 1.57148 0.610351 3.79199L5.86426 23.8867C6.42393 26.0276 "
        "9.22968 26.5386 10.5078 24.7324L15.1113 18.2246C15.3226 17.9262 15.632 17.7111 15.9853 17.6172L22.2187 "
        "15.9619C24.4791 15.3615 24.8628 12.3163 22.8223 11.1738L4.40137 0.861326Z")
STROKE = 1.04136
PRESS = (0.85, 3, 3)


def _outline():
    """Points along the outline (cubics sampled), for the tip and the bounds."""
    pts = []
    for seg in parse(PATH)[0]["segs"]:
        if seg[0] in ("M", "L"):
            pts.append(seg[1])
            continue
        p0, (c1, c2, p3) = pts[-1], seg[1:]
        for i in range(1, 201):
            t = i / 200
            u = 1 - t
            pts.append(tuple(u ** 3 * p0[k] + 3 * u * u * t * c1[k] + 3 * u * t * t * c2[k] + t ** 3 * p3[k]
                             for k in (0, 1)))
    return pts


def build():
    use(CURSOR)
    n = "Cursor"
    pts = _outline()
    tip = min(pts, key=lambda q: q[0] + q[1])
    pad = STROKE / 2 + 1
    x0, y0 = min(q[0] for q in pts) - tip[0] - pad, min(q[1] for q in pts) - tip[1] - pad
    x1, y1 = max(q[0] for q in pts) - tip[0] + pad, max(q[1] for q in pts) - tip[1] + pad
    w, h = round(x1 - x0, 2), round(y1 - y0, 2)
    fill = El("Fill", {}, [El("SolidColor", {"colorValue": CURSOR.props[0][2]},
                              [bind("color", key("SolidColor", "colorValue"))], name=f"{n}.fill.color")],
              name=f"{n}.fill")
    edge = El("Stroke", {"thickness": STROKE}, [
        El("SolidColor", {"colorValue": WHITE}, [bind("outline", key("SolidColor", "colorValue"))],
           name=f"{n}.stroke.color")], name=f"{n}.stroke")
    verts = to_vertices(parse(PATH)[0])
    shape = El("Shape", {"x": 0, "y": 0}, [points_path(f"{n}.outline", verts, origin=tip), fill, edge],
               name=f"{n}.shape")
    # a feathered fill only draws with the "clockwise" rule on a clockwise path; this one runs the other way, so the
    # shadow copies run it backwards
    back = [{"p": v["p"], "in": v["out"], "out": v["in"]} for v in reversed(verts)]
    shades = []
    for s, strength, ox, oy, op in SHADOW:
        s = f"{n}.shadow.{s}"
        paint = El("Fill", {"fillRule": "clockwise"}, [
            El("SolidColor", {"colorValue": argb("#000000", 0.2)},
               [bind("shadowColor", key("SolidColor", "colorValue"))], name=f"{s}.color"),
            El("Feather", {"strength": strength, "offsetX": ox, "offsetY": oy}, name=f"{s}.feather")],
            name=f"{s}.fill")
        shades.append(El("Shape", {"x": 0, "y": 0, "opacity": op}, [points_path(f"{s}.path", back, origin=tip), paint],
                         name=s))
    shadow = El("Node", {"x": 0, "y": 0, "opacity": 0}, shades, name=f"{n}.shadow")
    press = El("Node", {"x": 0, "y": 0}, [shape, shadow], name=f"{n}.press")
    s, down, up = PRESS
    looks = [(f"{n}.press", "scaleX", 1), (f"{n}.press", "scaleY", 1)]
    click = Anim("Click", (down + up) / FPS)
    for p in ("scaleX", "scaleY"):
        click.move(f"{n}.press", p, 0, down / FPS, 1, s).move(f"{n}.press", p, down / FPS, (down + up) / FPS, s, 1)
    lay = Layer("Click")
    lay.state("rest", pose("Rest", looks, 0), lay.go("click", if_trigger("click")), entry=True)
    lay.state("click", click, lay.go("rest", at_end=True), lay.go("click2", if_trigger("click")))
    lay.state("click2", click, lay.go("rest", at_end=True), lay.go("click", if_trigger("click")))
    sm = machine([lay, bool_layer("Shadow", "shadow", [(f"{n}.shadow", "opacity", 0, 1)], ms=0)])
    x = ART_POS["x"]
    ART_POS["x"] += 120 + 120
    art = El("Artboard", {"isComponent": True, "defaultStateMachineId": f"@sm.{CURSOR.key}",
                          "viewModelId": f"@{CURSOR.ref()}", "viewModelInstanceId": f"@vmi.{CURSOR.key}",
                          "styleId": f"@{n}Art.style", "width": w, "height": h, "originX": round(-x0 / w, 5),
                          "originY": round(-y0 / h, 5), "clip": False, "x": x, "y": ART_POS["y"]},
             [style(f"{n}Art"), press, sm], name="Cursor", ref=f"art.{CURSOR.key}")
    COMPONENTS.append((art, CURSOR))
    return art
