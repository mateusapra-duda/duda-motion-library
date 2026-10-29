"""AiStep (v10): one line of the Copilot's steps, under "Show steps" (Marketing Automation, Figma FwDTS5Q6g5BKw3WOrEHImL,
"Copilot progress" 1:9309 in frame 05). The steps list is p.ai_steps / p.chat_steps, run by a.steps.

View model "AiStep":
  label     "Adding welcome email": the step, once done (Regular 13/1.35, primary text, after a 13 px check)
  working   "Working...": while it runs (the same size in #A0A3AA, after the purple AI star), shimmering as the
            AiProcessIndication's label does (a band where it drops to 37 % crosses it every 1.6 s)
  done      the state swap, timed as the AiProcessIndication's (v08): the star fades in 6 frames and "Working..." wipes
            out; 10 frames in, the check fades in and the label wipes in where they were
The line itself doesn't move: the list opens its room and brings it in (a.steps).
"""
import os

from kit import (VM, El, Anim, Layer, use, box, text, text_style, hug, icon, icon_slot, pose, machine, component,
                 if_bool, ART)
from components.ai_process import (HIDDEN, SHOWN, GONE, SHIMMER_S, OUT_FADE, THOUGHT_AT, STAR_FADE, WIPE, WIPE_LAG,
                                   wipe, wipe_looks, wipe_in, wipe_out)

INK, MUTED = "FF272B35", "FFA0A3AA"
ROW_H = 17.3          # 14 in the storyboard at 0.81
SWAP_END = THOUGHT_AT + WIPE_LAG + WIPE

AST = VM("ast", "AiStep", [("label", "string", "Adding welcome email"), ("working", "string", "Working..."),
                           ("done", "boolean", False)])


def build():
    use(AST)
    n = "AiStep"
    text_style("astLabel", None, INK, size=13, lh=17.55, weight=350)
    text_style("astWorking", None, MUTED, size=13, lh=17.55, weight=350)
    band = El("TextModifierRange", {"modifyFrom": -0.36, "modifyTo": 0.36, "falloffFrom": 0, "falloffTo": 0,
                                    "offset": -2, "clamp": False}, name=f"{n}.band")
    shimmer = El("TextModifierGroup", {"modifyOpacity": True, "invertOpacity": True, "opacity": 0.37}, [band],
                 name=f"{n}.shimmer")
    working = text(f"{n}.working", [("astWorking", "=working")], lp=hug(), wrap=False,
                   modifiers=[shimmer, wipe(f"{n}.wipeOut", SHOWN)])
    # the purple AI star (special/i_ai_star: 10.8 in a 13 slot), its own colours
    star_art = icon(os.path.join(ART, "ai_star_purple.svg"), f"{n}.star.art", INK, x=1.1, y=1.1, size=10.8)
    star = box(f"{n}.star", [star_art], w=13, h=13, layoutWidthScaleType="fixed", layoutHeightScaleType="fixed")
    check = icon_slot(f"{n}.check", "general/i_checkmark", INK, size=13, stroke_w=1.5 * 16 / 13, opacity=0)  # 1.5 at 13
    label = text(f"{n}.label", [("astLabel", "=label")], lp=hug(), wrap=False, modifiers=[wipe(f"{n}.wipeIn", HIDDEN)])
    rows = [box(f"{n}.run", [star, working], flexDirectionValue="row", layoutAlignmentType="centerLeft",
                gapHorizontal=6, minHeight=ROW_H, **hug()),
            box(f"{n}.doneRow", [check, label], flexDirectionValue="row", layoutAlignmentType="centerLeft",
                gapHorizontal=6, minHeight=ROW_H, **hug())]
    body = box(f"{n}.body", rows, layoutTypeValue="stack", layoutAlignmentType="topLeft", **hug())

    # the shimmer runs until the swap, and stays off once done
    sh = Layer("Shimmer")
    run = Anim("Shimmer run", SHIMMER_S, loop=True)
    run.move(f"{n}.band", "offset", 0, SHIMMER_S, -0.25, 1.25)
    parked = [(f"{n}.band", "offset", -2, -2)]
    sh.state("run", run, sh.go("still", if_bool("done", True)), entry=True)
    sh.state("still", pose("Shimmer still", parked, 0), sh.go("run", if_bool("done", False)))
    sh.enter_if("still", if_bool("done", True))

    looks = ([(star.name, "opacity", 1.0, 0.0), (check.name, "opacity", 0.0, 1.0)]
             + wipe_looks(f"{n}.wipeOut", SHOWN, GONE) + wipe_looks(f"{n}.wipeIn", HIDDEN, SHOWN))
    swap = Anim("Step swap", SWAP_END + 1 / 60)
    swap.move(star.name, "opacity", 0, OUT_FADE, 1.0, 0.0)
    wipe_out(swap, 0, f"{n}.wipeOut")
    swap.move(check.name, "opacity", THOUGHT_AT, THOUGHT_AT + STAR_FADE, 0.0, 1.0)
    wipe_in(swap, THOUGHT_AT, f"{n}.wipeIn")
    sw = Layer("Done")
    sw.state("off", pose("Step working", looks, 0), sw.go("swap", if_bool("done", True)), entry=True)
    sw.state("swap", swap, sw.go("on", at_end=True), sw.go("off", if_bool("done", False)))
    sw.state("on", pose("Step done", looks, 1), sw.go("off", if_bool("done", False)))
    sw.enter_if("on", if_bool("done", True))
    return component("AiStep", 180, ROW_H, [body], machine([sh, sw]),
                     layout={"layoutWidthScaleType": "hug", "layoutHeightScaleType": "hug"})
