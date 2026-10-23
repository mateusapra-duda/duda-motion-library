"""Status (DS: page "Tags & status", 24151:89445).

DS props -> view model "Status":
  the text                label
  Color                   color        0 Neutral, 1 Positive, 2 Pending, 3 Dark Grey, 4 Yellow, 5 Negative, 6 Blue,
                                       7 Purple
  Border                  border
  Hover                   hover        (the fill takes the border's colour)
  Dropdown                dropdown     the chevron at the end (on by default, as in the DS)
  Unread indication       unread       the 8 px orange dot on the top-right corner
  (prototype)             interactive; clicked
"""
from kit import (VM, use, box, absolute, solid, line, text, text_style, hug, icon_slot, paint_names, shape_ellipse,
                 choice_layer, bool_layer, gate_layer, hover_listeners, listener, fire, machine, component, hex_argb)

COLORS = ("Neutral", "Positive", "Pending", "Dark Grey", "Yellow", "Negative", "Blue", "Purple")
# per colour: fill, text, border (= the hover fill), chevron
LOOKS = {"Neutral": ("#f5f5f7", "#5d6068", "#e4e4e6", "#5d6068"),
         "Positive": ("#e0f5ec", "#236c4b", "#c1ebd8", "#236c4b"),
         "Pending": ("#fef2ee", "#ae4d2e", "#fcd2c4", "#ae4d2e"),
         "Dark Grey": ("#e4e4e6", "#42454e", "#aeafb3", "#5d6068"),
         "Yellow": ("#ffecc8", "#ae4d2e", "#ffd788", "#ae4d2e"),
         "Negative": ("#fee9e9", "#ac1616", "#fbbaba", "#ac1616"),
         "Blue": ("#d9e9fc", "#174983", "#bdd9fa", "#174983"),
         "Purple": ("#f4effe", "#6442ae", "#dccdfc", "#6442ae")}
FILL, INK, EDGE, CHEV = ([hex_argb(LOOKS[c][i]) for c in COLORS] for i in range(4))
DOT = hex_argb("#f56d41")

STATUS = VM("status", "Status", [
    ("label", "string", "Status"), ("color", "number", 0), ("border", "boolean", False), ("hover", "boolean", False),
    ("dropdown", "boolean", True), ("unread", "boolean", False), ("interactive", "boolean", False),
    ("clicked", "trigger", None)])


def build():
    use(STATUS)
    n = "Status"
    text_style("statusLabel", "Headlines/He 4", INK[0])    # Medium 12/18
    label = box(f"{n}.labelWrap", [text(f"{n}.label", [("statusLabel", "=label")], lp=hug(), wrap=False)],
                paddingLeft=2, paddingRight=2, **hug())
    chev = icon_slot(f"{n}.chev", "arrows/chevron_bottom", CHEV[0])
    edge = absolute(f"{n}.border", paints=[line(f"{n}.border.stroke", EDGE[0], 1)], inset=(0.5,) * 4, opacity=0,
                    cornerRadiusTL=3.5)
    fx = absolute(f"{n}.hoverFx", paints=[solid(f"{n}.hoverFx.fill", EDGE[0])], opacity=0, cornerRadiusTL=4)
    dot = absolute(f"{n}.dot", [shape_ellipse(f"{n}.dotShape", 8, fill=DOT, x=4, y=4)], inset=(None, -3, -3, None),
                   opacity=0, w=8, h=8, layoutWidthScaleType="fixed", layoutHeightScaleType="fixed")
    hit = absolute(f"{n}.hit", displayValue="none")
    # flow: label, chevron (the dot and the edge draw on top, the hover tile under the text)
    body = box(f"{n}.box", [hit, dot, edge, label, chev, fx], paints=[solid(f"{n}.fill", FILL[0])],
               flexDirectionValue="row", layoutAlignmentType="centerLeft", paddingTop=2, paddingRight=6,
               paddingBottom=2, paddingLeft=6, cornerRadiusTL=4, h=22, layoutWidthScaleType="hug",
               layoutHeightScaleType="fixed")

    color_l = choice_layer("Color", "color", COLORS, [
        (f"{n}.fill.color", "colorValue", *FILL), (f"{n}.label.statusLabel.color", "colorValue", *INK),
        (f"{n}.border.stroke.color", "colorValue", *EDGE), (f"{n}.hoverFx.fill.color", "colorValue", *EDGE)]
        + [(p, "colorValue", *CHEV) for p in paint_names(chev)])
    dropdown = bool_layer("Dropdown", "dropdown", [(f"{n}.chev.style", "displayValue", "none", "flex")], ms=0)
    border = bool_layer("Border", "border", [(f"{n}.border", "opacity", 0, 1)], ms=0)
    unread = bool_layer("Unread", "unread", [(f"{n}.dot", "opacity", 0, 1)])
    hover = bool_layer("Hover", "hover", [(f"{n}.hoverFx", "opacity", 0, 1)])
    layers = [gate_layer([f"{n}.hit"]), color_l, dropdown, border, unread, hover]
    listeners = hover_listeners(f"{n}.hit") + [listener(f"{n}.hit", "click", fire("clicked"))]
    return component("Status", 76, 22, [body], machine(layers, listeners),
                     layout={"layoutWidthScaleType": "hug", "layoutHeightScaleType": "hug"})
