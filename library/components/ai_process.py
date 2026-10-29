"""AiProcessIndication (DS: page "AI patterns", 130692:89205): the AI's status line in the chat.

DS props -> view model "AiProcessIndication":
  the text                label        "Thinking...", "Updating the project..." (Regular 14/20, secondary colour)
  State: Thinking         done False   the label shimmers: a band where the text drops to 37 % crosses it every 1.6 s
                                       (the product's AiProcessIndication)
  State: Done - Open      done True    the swap: the star leaves and the label wipes out; `thought` ("Thought for 3s")
                                       wipes in at the same place, without the star, then the chevron (pointing up)
  State: Done and close   chevron      False: done shows no chevron (thought="Done": a status that only says "Done")
  (release notes)         spinner      a turning Loader arc instead of the AI icon ("Updating the project...")
  (v08)                   shown        False: hidden. Turning true (the message is sent) plays the entrance

v08 (Mateus, 2026-10-26): the official copilot motion, from hero-view v10 and his hp_section_3 ("Copilot v1",
"COPILOT ANIMATION 1"), timed in frames at 60 fps:
  entrance  the star 5 frames after `shown`: it turns from 60 degrees and rises 8 px in 35 frames (curve 0,0,0,1),
            appearing in 7; the label wipes in 15 frames after `shown`
  swap      on `done`: the star fades in 6 frames and the label wipes out, left first; 10 frames in, `thought` wipes in;
            24 frames in, the chevron fades in (5 frames)
  wipe      an opacity group with one range (not inverted), all linear: hidden offset -1, falloffFrom 0, falloffTo 0;
            in: offset to 0 in 15 frames, falloffTo to 1 in 15 starting 5 later; out: falloffFrom to 1 in 15, offset
            to 1 in 15 starting 5 later
The poetic licence is Mateus's: the product pushes "Thinking..." down under the answer, the hero keeps it in place.
"""
import math
import os

import kit
from kit import (VM, El, Anim, Layer, use, box, text, text_style, hug, icon, pose, bool_layer, machine, component,
                 color, if_bool, spin_layer, ART, ICONS, ICON_STROKE)

INK2 = color("Typography/secondary-text-color")    # #5D6068
SHIMMER_S = 1.6
F = 1 / 60
STAR_AT, LABEL_AT, TURN, STAR_FADE = 5 * F, 15 * F, 35 * F, 7 * F    # entrance, from `shown`
OUT_FADE, THOUGHT_AT, CHEV_AT, CHEV_FADE = 6 * F, 10 * F, 24 * F, 5 * F   # swap, from `done`
WIPE, WIPE_LAG = 15 * F, 5 * F
kit.EASE["aip_turn"] = (0.0, 0.0, 0.0, 1.0)

AIP = VM("aip", "AiProcessIndication", [("label", "string", "Thinking..."), ("thought", "string", "Thought for 3s"),
                                         ("done", "boolean", False), ("spinner", "boolean", False),
                                         ("chevron", "boolean", True), ("shown", "boolean", True)])

HIDDEN = {"offset": -1.0, "falloffFrom": 0.0, "falloffTo": 0.0}
SHOWN = {"offset": 0.0, "falloffFrom": 0.0, "falloffTo": 1.0}
GONE = {"offset": 1.0, "falloffFrom": 1.0, "falloffTo": 1.0}


def wipe(name, look):
    """hp_section_3's text wipe: an opacity group with one range; `look` is where its range rests."""
    return El("TextModifierGroup", {"modifyOpacity": True}, [El("TextModifierRange", dict(look), name=f"{name}.range")],
              name=name)


def wipe_looks(name, a, b):
    """(target, prop, a, b) for a range resting at look a in one pose and b in the other."""
    return [(f"{name}.range", k, a[k], b[k]) for k in ("offset", "falloffFrom", "falloffTo")]


def wipe_in(anim, t, name):
    anim.move(f"{name}.range", "offset", t, t + WIPE, -1.0, 0.0)
    anim.move(f"{name}.range", "falloffTo", t + WIPE_LAG, t + WIPE_LAG + WIPE, 0.0, 1.0)
    anim.hold(f"{name}.range", "falloffFrom", 0.0)


def wipe_out(anim, t, name):
    anim.move(f"{name}.range", "falloffFrom", t, t + WIPE, 0.0, 1.0)
    anim.move(f"{name}.range", "offset", t + WIPE_LAG, t + WIPE_LAG + WIPE, 0.0, 1.0)
    anim.hold(f"{name}.range", "falloffTo", 1.0)


def build():
    use(AIP)
    n = "AiProcess"
    text_style("aipLabel", "Content/Body 14", INK2)
    band = El("TextModifierRange", {"modifyFrom": -0.36, "modifyTo": 0.36, "falloffFrom": 0, "falloffTo": 0,
                                    "offset": -2, "clamp": False}, name=f"{n}.band")
    shimmer = El("TextModifierGroup", {"modifyOpacity": True, "invertOpacity": True, "opacity": 0.37}, [band],
                 name=f"{n}.shimmer")
    # two wipes on the label (the multiply): one brings it in (entrance), one takes it out (swap)
    label = text(f"{n}.label", [("aipLabel", "=label")], lp=hug(), wrap=False,
                 modifiers=[shimmer, wipe(f"{n}.wipeIn", SHOWN), wipe(f"{n}.wipeOut", SHOWN)])
    star_art = icon(os.path.join(ICONS, "special", "i_ai_assistant.svg"), f"{n}.star.art", INK2,
                    stroke_w=ICON_STROKE, x=-8, y=-8, size=16)
    star = box(f"{n}.star", [El("Node", {"x": 8, "y": 8}, [star_art], name=f"{n}.starTurn")],   # turns on its centre
               w=16, h=16, layoutWidthScaleType="fixed", layoutHeightScaleType="fixed")
    arc = icon(os.path.join(ART, "loader_spinner.svg"), f"{n}.arc", INK2, x=-8, y=-8)
    spin = box(f"{n}.spinBox", [El("Node", {"x": 8, "y": 8}, [El("Node", {}, [arc], name=f"{n}.spin")],
                                   name=f"{n}.spinAt")],
               w=16, h=16, displayValue="none", layoutWidthScaleType="fixed", layoutHeightScaleType="fixed")
    lead = box(f"{n}.lead", [star, spin], flexDirectionValue="row", **hug())
    thought = text(f"{n}.thought", [("aipLabel", "=thought")], lp=hug(), wrap=False,
                   modifiers=[wipe(f"{n}.wipeThought", HIDDEN)])
    chev_art = icon(os.path.join(os.path.dirname(ART), "icons", "arrows", "chevron_bottom.svg"), f"{n}.chev.art",
                    INK2, stroke_w=1.5, x=-8, y=-8)
    chev = box(f"{n}.chev", [El("Node", {"x": 8, "y": 8, "rotation": math.pi}, [chev_art], name=f"{n}.chevTurn")],
               w=16, h=16, opacity=0, layoutWidthScaleType="fixed", layoutHeightScaleType="fixed")
    rows = [box(f"{n}.thinking", [lead, label], flexDirectionValue="row", layoutAlignmentType="centerLeft",
                gapHorizontal=6, **hug()),
            box(f"{n}.thoughtRow", [thought, chev], flexDirectionValue="row", layoutAlignmentType="centerLeft",
                gapHorizontal=6, **hug())]   # "Thought for 3s" where the star was
    body = box(n, rows, layoutTypeValue="stack", layoutAlignmentType="topLeft", paddingTop=2, paddingBottom=2, **hug())

    # the shimmer starts as the label wipes in (15 frames after `shown`) and runs on under the swap's wipe-out (the
    # hero's); a status that starts done keeps its band off the text
    sh = Layer("Shimmer")
    run = Anim("Shimmer run", SHIMMER_S, loop=True)
    run.move(f"{n}.band", "offset", 0, SHIMMER_S, -0.25, 1.25)
    parked = [(f"{n}.band", "offset", -2, -2)]
    wait = Anim("Shimmer wait", LABEL_AT)
    wait.hold(f"{n}.band", "offset", -2)
    sh.state("rest", pose("Shimmer rest", parked, 0), sh.go("wait", if_bool("shown", True), if_bool("done", False)),
             entry=True)
    sh.state("wait", wait, sh.go("run", at_end=True), sh.go("rest", if_bool("shown", False)))
    sh.state("run", run, sh.go("rest", if_bool("shown", False)))
    sh.state("still", pose("Shimmer still", parked, 0), sh.go("rest", if_bool("done", False)))
    sh.enter_if("still", if_bool("done", True))
    sh.enter_if("run", if_bool("shown", True))

    # the entrance (shown): the star turns in and rises, the label wipes in
    turn = f"{n}.starTurn"
    in_looks = [(turn, "rotation", math.radians(60), 0.0), (turn, "y", 16.0, 8.0), (turn, "opacity", 0.0, 1.0),
                (f"{n}.spinAt", "opacity", 0.0, 1.0)] + wipe_looks(f"{n}.wipeIn", HIDDEN, SHOWN)
    entering = Anim("Status in", STAR_AT + TURN)
    entering.move(turn, "rotation", STAR_AT, STAR_AT + TURN, math.radians(60), 0.0, "aip_turn")
    entering.move(turn, "y", STAR_AT, STAR_AT + TURN, 16.0, 8.0, "aip_turn")
    for tg in (turn, f"{n}.spinAt"):
        entering.move(tg, "opacity", STAR_AT, STAR_AT + STAR_FADE, 0.0, 1.0)
    wipe_in(entering, LABEL_AT, f"{n}.wipeIn")
    ins = Layer("Shown")
    ins.state("hidden", pose("Status hidden", in_looks, 0), ins.go("in", if_bool("shown", True)), entry=True)
    ins.state("in", entering, ins.go("on", at_end=True), ins.go("hidden", if_bool("shown", False)))
    ins.state("on", pose("Status shown", in_looks, 1), ins.go("hidden", if_bool("shown", False)))
    ins.enter_if("on", if_bool("shown", True))

    # the swap (done): the star leaves, the label wipes out, the thought wipes in where it was, then the chevron
    done_looks = ([(lead.name, "opacity", 1.0, 0.0), (chev.name, "opacity", 0.0, 1.0)]
                  + wipe_looks(f"{n}.wipeOut", SHOWN, GONE) + wipe_looks(f"{n}.wipeThought", HIDDEN, SHOWN))
    swap = Anim("Status swap", CHEV_AT + CHEV_FADE + 1 * F)
    swap.move(lead.name, "opacity", 0, OUT_FADE, 1.0, 0.0)
    wipe_out(swap, 0, f"{n}.wipeOut")
    wipe_in(swap, THOUGHT_AT, f"{n}.wipeThought")
    swap.move(chev.name, "opacity", CHEV_AT, CHEV_AT + CHEV_FADE, 0.0, 1.0)
    sw = Layer("Done")
    sw.state("off", pose("Status thinking", done_looks, 0), sw.go("swap", if_bool("done", True)), entry=True)
    sw.state("swap", swap, sw.go("on", at_end=True), sw.go("off", if_bool("done", False)))
    sw.state("on", pose("Status thought", done_looks, 1), sw.go("off", if_bool("done", False)))
    sw.enter_if("on", if_bool("done", True))

    layers = [sh, ins, sw,
              bool_layer("Chevron", "chevron", [(f"{n}.chev.style", "displayValue", "none", "flex")], ms=0),
              bool_layer("Spinner", "spinner", [(f"{n}.star.style", "displayValue", "flex", "none"),
                                                (f"{n}.spinBox.style", "displayValue", "none", "flex")], ms=0),
              spin_layer(f"{n}.spin")]
    return component("AiProcessIndication", 160, 24, [body], machine(layers),
                     layout={"layoutWidthScaleType": "hug", "layoutHeightScaleType": "hug"})
