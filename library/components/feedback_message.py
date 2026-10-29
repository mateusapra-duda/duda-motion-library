"""FeedbackMessage (DS: "Push Feedback Message", 154396:213304; the set ".Push Feedback" 160:3624).

A non-disruptive alert after the user acts: top right of the screen, 24 px under the top bar and 24 px from the right
(in a large popup: top centre of it); it goes away on its own in a few seconds (or with its x); no button (the DS
allows a link: not drawn yet); shadow-4.

DS props -> view model "FeedbackMessage":
  State                  variant   0 Info (160:3623), 1 Success (160:3621, 332 x 48), 2 Warning (160:3622),
                                   3 Error (160:3620: a 16 px icon, 46 high), 4 Neutral (4963:23469: white, no icon, 42)
  the text               text      Content/Body 13/18, one line (the DS: min 250, max 600 wide)
  (motion, not in the DS) shown    false: hidden; true: it drops 8 px into place as it fades in (0.5 s, settle);
                                   back to false: it rises as it fades out (0.25 s, duda). a.feedback does both
Layout (Figma): padding 16 / 12, 32 between the content and the x, 8 between the icon and the text, the text 2 px
from the top and bottom (Neutral: 0), radius border-radius-s (4). Icons: the DS validations drawings with their own
colours (art/feedback_*.svg) and the "Functional" 16 px x.
"""
import os

from kit import (VM, Layer, use, box, solid, text, text_style, hug, icon, pose, choice_layer, machine, component,
                 color, if_bool, shadow_layers, ART, DS, WHITE)

INK = color("Typography/primary-text-color")    # #272B35
FILLS = [color("Indications/info-bg-color"), color("Indications/positive-light-color"),
         color("Indications/warning-bg-color"), color("Indications/negative-light-color"), WHITE]
NAMES = ["info", "success", "warning", "error", None]   # art/feedback_<name>.svg
IN_S, OUT_S, DROP = 0.5, 0.25, 8                         # shown: in (settle), out (duda), how far it drops in

FB = VM("fb", "FeedbackMessage", [("text", "string", "This is a success feedback message"),
                                  ("variant", "number", 1), ("shown", "boolean", True)])


def build():
    use(FB)
    n = "FeedbackMessage"
    text_style("fbText", "Content/Body", INK, ls=0.2)    # 13/18; the 0.2 spacing is in the Figma style, not ds/tokens
    icons = []
    for name in NAMES[:4]:
        size = 16 if name == "error" else 24
        art = icon(os.path.join(ART, f"feedback_{name}.svg"), f"{n}.{name}.art", INK, size=size)
        icons.append(box(f"{n}.{name}", [art], w=size, h=size, displayValue="none" if name != "success" else None,
                         layoutWidthScaleType="fixed", layoutHeightScaleType="fixed"))
    # the line 2 px from the top and bottom as a min height (22; Neutral 18): a Rive text line is ~2 px under its lh
    words = box(f"{n}.words", [text(f"{n}.text", [("fbText", "=text")], lp=hug(), wrap=False)],
                flexDirectionValue="row", layoutAlignmentType="centerLeft", minHeight=22, **hug())
    content = box(f"{n}.content", icons + [words], flexDirectionValue="row", layoutAlignmentType="centerLeft",
                  gapHorizontal=8, layoutWidthScaleType="fill", layoutHeightScaleType="hug")
    x = icon(os.path.join(ART, "feedback_x.svg"), f"{n}.x.art", INK)
    close = box(f"{n}.x", [x], w=16, h=16, layoutWidthScaleType="fixed", layoutHeightScaleType="fixed")
    rad = DS["radius"]["border-radius-s"]
    body = box(f"{n}.box", [content, close], paints=[solid(f"{n}.fill", FILLS[1])], flexDirectionValue="row",
               layoutAlignmentType="centerLeft", gapHorizontal=32, paddingLeft=16, paddingRight=16, paddingTop=12,
               paddingBottom=12, cornerRadiusTL=rad, minWidth=250, maxWidth=600, **hug())
    # the shadow under the box (the first child draws on top); `shown` moves and fades the whole
    wrap = box(f"{n}.wrap", [body] + shadow_layers(f"{n}.sh", DS["shadow"]["shadow-4"]["layers"], rad), **hug())

    looks = [(f"{n}.fill.color", "colorValue", *FILLS),
             (f"{n}.words.style", "minHeight", 22, 22, 22, 22, 18)]
    for i, name in enumerate(NAMES[:4]):
        looks.append((f"{n}.{name}.style", "displayValue", *["flex" if j == i else "none" for j in range(5)]))
    variant = choice_layer("Variant", "variant", ["info", "success", "warning", "error", "neutral"], looks)

    # shown: in, it drops into place as it fades in; out, it rises back as it fades
    lay = Layer("Shown")
    pos = [(f"{n}.wrap", "opacity", 0, 1), (f"{n}.wrap", "y", -DROP, 0)]
    lay.state("off", pose("Feedback hidden", pos, 0),
              lay.go("on", if_bool("shown", True), ms=round(IN_S * 1000), ease="settle"), entry=True)
    lay.state("on", pose("Feedback shown", pos, 1),
              lay.go("off", if_bool("shown", False), ms=round(OUT_S * 1000), ease="duda"))
    lay.enter_if("on", if_bool("shown", True))
    return component("FeedbackMessage", 332, 48, [wrap], machine([variant, lay]),
                     layout={"layoutWidthScaleType": "hug", "layoutHeightScaleType": "hug"})
