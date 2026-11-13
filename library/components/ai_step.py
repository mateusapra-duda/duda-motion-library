"""AiStep (v11): one line of the Copilot's steps, under "Show steps" (Marketing Automation, Figma FwDTS5Q6g5BKw3WOrEHImL,
"Copilot progress" 1:9309 in frame 05). The steps list is p.ai_steps / p.chat_steps, run by a.steps.

Mateus's rule (2026-11-13, every Copilot; reference/exemplos-mateus/Loading-correto.rev): a step loads with the classic
spinner, never the AI star, even where Figma draws the star. The "✦ Thinking..." status above keeps its star.

View model "AiStep":
  label     "Adding welcome email": the step (Regular 13/1.35, primary text), dark from the start, no shimmer
  done      the swap: the spinner fades out in 3 frames, still turning, then the check fades in over the next 3
            (never both at once)
The spinner: a 270° arc (the DS Loader's) in one colour with a trail, #272B35 from 100 % at its head to 12 %, its stroke
1.5 at 16 (1.22 at 13), round caps, turning clockwise, linear, one turn per 0.8 s.
The line itself doesn't move: the list opens its room and brings it in (a.steps).
"""
import os

from kit import VM, El, Layer, use, box, text, text_style, hug, icon, icon_slot, pose, machine, component, if_bool, \
    spin_layer, Anim, ART

INK = "FF272B35"
ROW_H = 17.3          # 14 in the storyboard at 0.81
GLYPH = 13
SPIN_OUT, CHECK_IN = 3 / 60, 3 / 60
SWAP_END = SPIN_OUT + CHECK_IN
SPIN_TURN = 0.8

AST = VM("ast", "AiStep", [("label", "string", "Adding welcome email"), ("done", "boolean", False)])


def build():
    use(AST)
    n = "AiStep"
    text_style("astLabel", None, INK, size=13, lh=17.55, weight=350)
    half = GLYPH / 2
    arc = icon(os.path.join(ART, "step_spinner.svg"), f"{n}.spin.art", INK, x=-half, y=-half, size=GLYPH)
    spin = El("Node", {"x": half, "y": half}, [El("Node", {}, [arc], name=f"{n}.spin")], name=f"{n}.spinAt")
    check = icon_slot(f"{n}.check", "general/i_checkmark", INK, size=GLYPH, stroke_w=1.5 * 16 / GLYPH,
                      opacity=0)                                                                  # 1.5 at 13
    glyph = box(f"{n}.glyph", [spin, check], w=GLYPH, h=GLYPH, layoutWidthScaleType="fixed",
                layoutHeightScaleType="fixed")
    label = text(f"{n}.label", [("astLabel", "=label")], lp=hug(), wrap=False)
    row = box(f"{n}.row", [glyph, label], flexDirectionValue="row", layoutAlignmentType="centerLeft",
              gapHorizontal=6, minHeight=ROW_H, **hug())

    looks = [(f"{n}.spinAt", "opacity", 1.0, 0.0), (f"{n}.check", "opacity", 0.0, 1.0)]
    swap = Anim("Step swap", SWAP_END + 1 / 60)
    swap.move(f"{n}.spinAt", "opacity", 0, SPIN_OUT, 1.0, 0.0)
    swap.move(f"{n}.check", "opacity", SPIN_OUT, SPIN_OUT + CHECK_IN, 0.0, 1.0)
    sw = Layer("Done")
    sw.state("off", pose("Step working", looks, 0), sw.go("swap", if_bool("done", True)), entry=True)
    sw.state("swap", swap, sw.go("on", at_end=True), sw.go("off", if_bool("done", False)))
    sw.state("on", pose("Step done", looks, 1), sw.go("off", if_bool("done", False)))
    sw.enter_if("on", if_bool("done", True))
    return component("AiStep", 180, ROW_H, [row], machine([spin_layer(f"{n}.spin", SPIN_TURN), sw]),
                     layout={"layoutWidthScaleType": "hug", "layoutHeightScaleType": "hug"})
