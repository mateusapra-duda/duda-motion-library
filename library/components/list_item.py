"""ListItem (DS: page "Items & cards", 103617:20115).

DS props -> view model "ListItem":
  the texts               title / secondary; Secondary text: showSecondary
  Show Prefix             prefix       an Icon Thumbnail (40): prefixIcon (artboard), prefixTheme (as Icon Thumbnail's
                                       theme: 0 Primary ... 6 Warning)
  Show Suffix             suffix       a small grey icon (24 slot): suffixIcon (artboard, default Icon/i_options)
  Tag                     tag          the "new" promotional tag; tagLabel
  Border                  border       (on by default)
  State                   state        0 Default, 1 Default_Grey, 2 Selected - border, 3 Selected - grey,
                                       4 Selected - primary color, 5 Error, 6 Disabled
                          hover        (DS State Hover: fill #F5F5F7, edge #CFCFD3), over any state
  Alignment               (Center only)
  (not here yet)          On Drag, Moved, Rename, Skeleton, Extra Content
  (prototype)             interactive; clicked
"""
from kit import (VM, use, box, absolute, solid, line, text, text_style, hug, fill_w, nested_icon, choice_layer,
                 bool_layer, gate_layer, hover_listeners, listener, fire, machine, component, icon_ref, hex_argb,
                 color)
from components.icon_thumbnail import thumb, theme_layer, FG

STATES = ("Default", "Default_Grey", "Selected border", "Selected grey", "Selected primary", "Error", "Disabled")
FILL = [hex_argb(c) for c in ("#ffffff", "#f6f6f8", "#ffffff", "#f5f5f7", "#feeee8", "#fee9e9", "#ffffff")]
EDGE = [hex_argb(c) for c in ("#e4e4e6", "#e4e4e6", "#5d6068", "#e4e4e6", "#e4e4e6", "#e4e4e6", "#e4e4e6")]
EDGE_ON = [1, 1, 1, 0, 0, 1, 1]          # the selected grey / primary rows have no edge
SECOND = [hex_argb("#9b9ba2")] * 6 + [hex_argb("#c9cacd")]
ORANGE = hex_argb("#f56d41")
GREY = color("Typography/secondary-text-color")    # the suffix icon (#5D6068)

LI = VM("li", "ListItem", [
    ("title", "string", "Title"), ("secondary", "string", "Secondary text"), ("showSecondary", "boolean", True),
    ("prefix", "boolean", True), ("prefixIcon", "artboard", icon_ref("i_site")), ("prefixTheme", "number", 0),
    ("suffix", "boolean", True), ("suffixIcon", "artboard", icon_ref("i_options")), ("tag", "boolean", False),
    ("tagLabel", "string", "new"), ("border", "boolean", True), ("state", "number", 0), ("hover", "boolean", False),
    ("interactive", "boolean", False), ("clicked", "trigger", None), ("_fg", "color", FG[0]),
    ("_grey", "color", GREY)])


def build():
    use(LI)
    n = "ListItem"
    text_style("liTitle", "Content/Body", color("Typography/primary-text-color"))   # Regular 13/18
    text_style("liSecond", "Content/Body", SECOND[0])
    text_style("liTag", None, ORANGE, size=10, lh=14, weight=700)
    prefix = box(f"{n}.prefix", [thumb(n, "prefixIcon", "_fg")], **hug())
    texts = box(f"{n}.texts", [text(f"{n}.title", [("liTitle", "=title")], lp=fill_w(), overflow="ellipsis",
                                    wrap=False),
                               text(f"{n}.second", [("liSecond", "=secondary")], lp=fill_w(), overflow="ellipsis",
                                    wrap=False)],
                flexDirectionValue="column", layoutAlignmentType="centerLeft", **fill_w())
    tag_edge = absolute(f"{n}.tagEdge", paints=[line(f"{n}.tagEdge.stroke", ORANGE, 1)], inset=(0.5,) * 4,
                        cornerRadiusTL=3.5)
    tag = box(f"{n}.tag", [tag_edge, text(f"{n}.tagText", [("liTag", "=tagLabel")], lp=hug(), wrap=False)],
              flexDirectionValue="row", layoutAlignmentType="center", paddingTop=2, paddingRight=6, paddingBottom=2,
              paddingLeft=6, displayValue="none", **hug())
    suffix = box(f"{n}.suffix", [nested_icon(f"{n}.sfx", "suffixIcon", "_grey", "i_options")],
                 flexDirectionValue="column", layoutAlignmentType="center", w=24, h=24, layoutWidthScaleType="fixed",
                 layoutHeightScaleType="fixed")
    edge = absolute(f"{n}.border", paints=[line(f"{n}.border.stroke", EDGE[0], 1)], inset=(0.5,) * 4,
                    cornerRadiusTL=7.5)
    h_edge = absolute(f"{n}.hoverEdge", paints=[line(f"{n}.hoverEdge.stroke", hex_argb("#cfcfd3"), 1)],
                      inset=(0.5,) * 4, opacity=0, cornerRadiusTL=7.5)
    h_fill = absolute(f"{n}.hoverFill", paints=[solid(f"{n}.hoverFill.fill", hex_argb("#f5f5f7"))], opacity=0,
                      cornerRadiusTL=8)
    hit = absolute(f"{n}.hit", displayValue="none")
    content = box(f"{n}.content", [prefix, texts, tag, suffix], flexDirectionValue="row",
                  layoutAlignmentType="centerLeft", gapHorizontal=12, **fill_w())
    # flow: the content; on top the hit and the edges, under it the hover tile
    body = box(f"{n}.box", [hit, h_edge, edge, content, h_fill], paints=[solid(f"{n}.fill", FILL[0])],
               flexDirectionValue="row", layoutAlignmentType="centerLeft", paddingTop=12, paddingRight=12,
               paddingBottom=12, paddingLeft=12, cornerRadiusTL=8, layoutWidthScaleType="fill",
               layoutHeightScaleType="hug")

    state_l = choice_layer("State", "state", STATES, [
        (f"{n}.fill.color", "colorValue", *FILL), (f"{n}.border.stroke.color", "colorValue", *EDGE),
        (f"{n}.border.style", "displayValue", *["flex" if e else "none" for e in EDGE_ON]),
        (f"{n}.second.liSecond.color", "colorValue", *SECOND),
        (f"{n}.content", "opacity", *[0.4 if s == "Disabled" else 1 for s in STATES])], ms=150)
    layers = [gate_layer([f"{n}.hit"]), theme_layer(n, "prefixTheme", "_fg"), state_l,
              bool_layer("Border", "border", [(f"{n}.border", "opacity", 0, 1)], ms=0),
              bool_layer("Secondary", "showSecondary", [(f"{n}.second.lp", "displayValue", "none", "flex")], ms=0),
              bool_layer("Prefix", "prefix", [(f"{n}.prefix.style", "displayValue", "none", "flex")], ms=0),
              bool_layer("Suffix", "suffix", [(f"{n}.suffix.style", "displayValue", "none", "flex")], ms=0),
              bool_layer("Tag", "tag", [(f"{n}.tag.style", "displayValue", "none", "flex")], ms=0),
              bool_layer("Hover", "hover", [(f"{n}.hoverFill", "opacity", 0, 1), (f"{n}.hoverEdge", "opacity", 0, 1)])]
    listeners = hover_listeners(f"{n}.hit") + [listener(f"{n}.hit", "click", fire("clicked"))]
    return component("ListItem", 419, 64, [body], machine(layers, listeners),
                     layout={"layoutWidthScaleType": "fixed", "layoutHeightScaleType": "hug"})
