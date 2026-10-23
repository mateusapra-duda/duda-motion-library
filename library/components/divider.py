"""Divider (DS: page "Stractural assets", 31938:90917): With text (138:3953), No text (138:3954), Vertical (52091:51351).

DS props -> view model "Divider":
  Type          variant   0 With text, 1 No text, 2 Vertical
  the text      label     "EARLIER"
The line is 1 px of Borders/border-color; the placement gives the length (a vertical one: 1 wide, as tall as it is
placed).
"""
from kit import VM, use, box, solid, text, text_style, hug, choice_layer, machine, component, color

DIV = VM("div", "Divider", [("variant", "number", 0), ("label", "string", "EARLIER")])


def build():
    use(DIV)
    n = "Divider"
    text_style("divLabel", "Content/Body", color("Typography/hint-color"))
    rule = lambda part: box(f"{n}.{part}", paints=[solid(f"{n}.{part}.fill", color("Borders/border-color"))],  # noqa
                            h=1, layoutWidthScaleType="fill", layoutHeightScaleType="fixed")
    across = box(f"{n}.across", [rule("lineA"), text(f"{n}.label", [("divLabel", "=label")], lp=hug(), wrap=False),
                                 rule("lineB")],
                 flexDirectionValue="row", layoutAlignmentType="center", gapHorizontal=8,
                 layoutWidthScaleType="fill", layoutHeightScaleType="fill")
    down = box(f"{n}.down", [box(f"{n}.lineV", paints=[solid(f"{n}.lineV.fill", color("Borders/border-color"))],
                                 w=1, layoutWidthScaleType="fixed", layoutHeightScaleType="fill")],
               flexDirectionValue="row", layoutAlignmentType="center", displayValue="none",
               layoutWidthScaleType="fill", layoutHeightScaleType="fill")
    root = box(f"{n}.root", [across, down], layoutWidthScaleType="fill", layoutHeightScaleType="fill")
    looks = [(f"{n}.across.style", "displayValue", "flex", "flex", "none"),
             (f"{n}.down.style", "displayValue", "none", "none", "flex"),
             (f"{n}.label.lp", "displayValue", "flex", "none", "none"),
             (f"{n}.lineB.style", "displayValue", "flex", "none", "none")]
    lay = choice_layer("Type", "variant", ("With text", "No text", "Vertical"), looks)
    return component("Divider", 240, 18, [root], machine([lay]))
