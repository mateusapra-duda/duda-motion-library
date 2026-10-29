"""FlowNode (Marketing Automation, v10): a step on the automation map. Figma FwDTS5Q6g5BKw3WOrEHImL, "Automation /
Flow node" (1:2659, "automation map step card; set icon tile fill per step type") and "Automation / Wait step"
(1:2667, "a compact pill"), as used in "MA - Create automation with one email" (1:8997, frames 06 and 07).

View model "FlowNode":
  type       0 Start trigger, 1 Add/Remove label, 2 Update field, 3 Send email, 4 If/Else, 5 End: the card
             (325 x 93: the icon tile, the title, the "..." menu, the subtitle); 6 Wait: the pill (221 x 42: the clock
             tile, the title, a smaller "..."). The tile's colour and icon follow the type; Start trigger and End have
             no menu (as in the storyboard)
  title      "Send email" (Medium 16/1.35), subtitle "Welcome to ..." (Regular 16/1.35, one line, an ellipsis)
  hover      the edge darkens to #D4D4D8 and the shadow grows a little (not in the storyboard: a licence)
  selected   frame 07: a 1.5 px #3B82F6 edge over the grey one
Sizes are the components' own (the storyboard draws them at 0.5: the canvas at 62 % of the UI at 0.81). Nothing in it
moves: the piece brings the nodes in with the Generation effect, the block itself still.
"""
from kit import (VM, use, box, solid, line, text, text_style, hug, icon_slot, absolute, choice_layer, bool_layer,
                 machine, component, shadow_layers, HOVER_MS)

INK = "FF272B35"
EDGE, EDGE_HOVER, BLUE = "FFE4E4E7", "FFD4D4D8", "FF3B82F6"
TYPES = ["Start trigger", "Add/Remove label", "Update field", "Send email", "If/Else", "End", "Wait"]
TILES = ["FFD4F25A", "FFF1ECFB", "FFF1ECFB", "FFA7E8F6", "FFF4F4F5", "FFD4F25A", "FFF4F4F5"]
GLYPHS = ["automation/i_lightning", "automation/i_label", "automation/i_content", "automation/i_email",
          "automation/i_split", "general/i_checkmark", "automation/i_clock"]
MENU = [False, True, True, True, True, False, True]
SUBTITLES = ["Contact created", "Add label: New subscriber", "Set Lifecycle stage: Subscriber",
             'Welcome to {{company | default: "melo"}}!', "If Link clicked", "Completed: reached the goal", ""]
WAIT = 6
CARD_W, CARD_H, PILL_W, PILL_H, RAD = 325, 93, 221, 42, 8
ICON_STROKE_18 = 1.5 * 16 / 18     # the map's icons: 1.5 at 18 px (the DS draws 1.5 on a 16 grid)

FN = VM("fn", "FlowNode", [("title", "string", "Send email"), ("subtitle", "string", SUBTITLES[3]),
                           ("type", "number", 3), ("hover", "boolean", False), ("selected", "boolean", False)])


def _edges(n):
    """The grey edge (hover darkens it) and the blue one of `selected` over it."""
    grey = absolute(f"{n}.edge", paints=[line(f"{n}.edge.stroke", EDGE, 1)], inset=(0.5,) * 4,
                    cornerRadiusTL=RAD - 0.5)
    blue = absolute(f"{n}.ring", paints=[line(f"{n}.ring.stroke", BLUE, 1.5)], inset=(0.75,) * 4, opacity=0,
                    cornerRadiusTL=RAD - 0.75)
    return [blue, grey]


def _shadow(n, y, blur, alpha):
    return shadow_layers(n, [{"x": 0, "y": y, "blur": blur, "spread": 0, "color": f"#000000{alpha}"}], RAD)


def build():
    use(FN)
    n = "FlowNode"
    text_style("fnTitle", None, INK, size=16, lh=21.6, weight=550)
    text_style("fnSub", None, INK, size=16, lh=21.6, weight=350)

    # the card: tile, title, menu over the subtitle
    glyphs = [icon_slot(f"{n}.g{i}", g, INK, size=18, stroke_w=ICON_STROKE_18,
                        displayValue=None if i == 3 else "none") for i, g in enumerate(GLYPHS[:6])]
    tile = box(f"{n}.tile", glyphs, w=36, h=36, paints=[solid(f"{n}.tile.fill", TILES[3])], cornerRadiusTL=6,
               layoutAlignmentType="center", layoutWidthScaleType="fixed", layoutHeightScaleType="fixed")
    title = text(f"{n}.title", [("fnTitle", "=title")], lp=dict(layoutWidthScaleType="fill",
                                                                layoutHeightScaleType="hug"),
                 overflow="ellipsis", wrap=False)
    menu = icon_slot(f"{n}.menu", "automation/i_menu_dots", INK, size=16)
    head = box(f"{n}.head", [tile, title, menu], flexDirectionValue="row", layoutAlignmentType="centerLeft",
               gapHorizontal=10, layoutWidthScaleType="fill", layoutHeightScaleType="hug")
    sub = text(f"{n}.sub", [("fnSub", "=subtitle")], lp=dict(layoutWidthScaleType="fill", layoutHeightScaleType="hug"),
               overflow="ellipsis", wrap=False)
    card = box(f"{n}.card", _edges(f"{n}.card") + [head, sub], w=CARD_W, h=CARD_H,
               paints=[solid(f"{n}.card.fill", "FFFFFFFF")], flexDirectionValue="column", layoutAlignmentType="topLeft",
               gapVertical=12, paddingLeft=12, paddingRight=12, paddingTop=12, paddingBottom=14, cornerRadiusTL=RAD,
               layoutWidthScaleType="fixed", layoutHeightScaleType="fixed")

    # the Wait pill: the clock tile, the title, a smaller "..."
    clock = icon_slot(f"{n}.clock", GLYPHS[WAIT], INK, size=14, stroke_w=1.5 * 16 / 14)
    ptile = box(f"{n}.ptile", [clock], w=26, h=26, paints=[solid(f"{n}.ptile.fill", TILES[WAIT])], cornerRadiusTL=4,
                layoutAlignmentType="center", layoutWidthScaleType="fixed", layoutHeightScaleType="fixed")
    ptitle = text(f"{n}.ptitle", [("fnTitle", "=title")], lp=dict(layoutWidthScaleType="fill",
                                                                  layoutHeightScaleType="hug"),
                  overflow="ellipsis", wrap=False)
    more = icon_slot(f"{n}.more", "automation/i_more", INK, size=14)
    pill = box(f"{n}.pill", _edges(f"{n}.pill") + [ptile, ptitle, more], w=PILL_W, h=PILL_H,
               paints=[solid(f"{n}.pill.fill", "FFFFFFFF")], flexDirectionValue="row", layoutAlignmentType="centerLeft",
               gapHorizontal=10, paddingLeft=8, paddingRight=12, paddingTop=8, paddingBottom=8, cornerRadiusTL=RAD,
               displayValue="none", layoutWidthScaleType="fixed", layoutHeightScaleType="fixed")

    # the shadows under each (the first child draws on top): the storyboard's drop shadows, and hover's a bit larger
    lifted = _shadow(f"{n}.shHover", 2, 8, "14")
    for el in lifted:
        el.attrs["opacity"] = 0
    wrap = box(f"{n}.wrap", [card, pill] + _shadow(f"{n}.sh", 1, 2, "14") + lifted, **hug())

    looks = [(f"{n}.tile.fill.color", "colorValue", *TILES[:6], TILES[3]),
             (f"{n}.menu.style", "displayValue", *["flex" if m else "none" for m in MENU]),
             (f"{n}.card.style", "displayValue", *["flex"] * 6, "none"),
             (f"{n}.pill.style", "displayValue", *["none"] * 6, "flex")]
    for i in range(6):
        looks.append((f"{n}.g{i}.style", "displayValue", *["flex" if j == i else "none" for j in range(6)], "none"))
    kind = choice_layer("Type", "type", ["trigger", "label", "field", "email", "split", "end", "wait"], looks)
    shadow_hover = [(el.name, "opacity", 0, 1) for el in lifted]
    hover = bool_layer("Hover", "hover", [(f"{n}.card.edge.stroke.color", "colorValue", EDGE, EDGE_HOVER),
                                          (f"{n}.pill.edge.stroke.color", "colorValue", EDGE, EDGE_HOVER)]
                       + shadow_hover, ms=HOVER_MS)
    sel = bool_layer("Selected", "selected", [(f"{n}.card.ring", "opacity", 0, 1), (f"{n}.pill.ring", "opacity", 0, 1)],
                     ms=0)
    return component("FlowNode", CARD_W, CARD_H, [wrap], machine([kind, hover, sel]),
                     layout={"layoutWidthScaleType": "hug", "layoutHeightScaleType": "hug"})
