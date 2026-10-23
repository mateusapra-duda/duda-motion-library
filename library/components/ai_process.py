"""AiProcessIndication (DS: page "AI patterns", 130692:89205): the AI's status line in the chat.

DS props -> view model "AiProcessIndication":
  the text                label        "Thinking...", "Thought for 3s", "Updating the project..." (Regular 14/20,
                                       secondary colour)
  State: Thinking         done False   the label shimmers: a band where the text drops to 37 % crosses it every 1.6 s
                                       (the product's AiProcessIndication)
  State: Done - Open      done True    the label sits still, a chevron after it
  State: Done and close   chevron      False: done shows no chevron (a status that only says "Done", hero Code tab)
  (release notes)         spinner      a turning Loader arc instead of the AI icon ("Updating the project...")
"""
import math
import os

from kit import (VM, El, Anim, Layer, use, box, text, text_style, hug, icon, icon_slot, pose, bool_layer, match_layer,
                 machine, component, color, if_bool, spin_layer, ART)

INK2 = color("Typography/secondary-text-color")    # #5D6068
SHIMMER_S = 1.6

AIP = VM("aip", "AiProcessIndication", [("label", "string", "Thinking..."), ("done", "boolean", False),
                                         ("spinner", "boolean", False), ("chevron", "boolean", True)])


def build():
    use(AIP)
    n = "AiProcess"
    text_style("aipLabel", "Content/Body 14", INK2)
    band = El("TextModifierRange", {"modifyFrom": -0.36, "modifyTo": 0.36, "falloffFrom": 0, "falloffTo": 0,
                                    "offset": -2, "clamp": False}, name=f"{n}.band")
    shimmer = El("TextModifierGroup", {"modifyOpacity": True, "invertOpacity": True, "opacity": 0.37}, [band],
                 name=f"{n}.shimmer")
    label = text(f"{n}.label", [("aipLabel", "=label")], lp=hug(), wrap=False, modifiers=[shimmer])
    star = icon_slot(f"{n}.star", "special/i_ai_assistant", INK2)
    arc = icon(os.path.join(ART, "loader_spinner.svg"), f"{n}.arc", INK2, x=-8, y=-8)
    spin = box(f"{n}.spinBox", [El("Node", {"x": 8, "y": 8}, [El("Node", {}, [arc], name=f"{n}.spin")],
                                   name=f"{n}.spinAt")],
               w=16, h=16, displayValue="none", layoutWidthScaleType="fixed", layoutHeightScaleType="fixed")
    chev_art = icon(os.path.join(os.path.dirname(ART), "icons", "arrows", "chevron_bottom.svg"), f"{n}.chev.art",
                    INK2, stroke_w=1.5, x=-8, y=-8)
    chev = box(f"{n}.chev", [El("Node", {"x": 8, "y": 8, "rotation": math.pi}, [chev_art], name=f"{n}.chevTurn")],
               w=16, h=16, displayValue="none", layoutWidthScaleType="fixed", layoutHeightScaleType="fixed")
    body = box(n, [star, spin, label, chev], flexDirectionValue="row", layoutAlignmentType="centerLeft",
               gapHorizontal=6, paddingTop=2, paddingBottom=2, **hug())

    # the shimmer runs while thinking; done parks the band off the text
    lay = Layer("Shimmer")
    run = Anim("Shimmer run", SHIMMER_S, loop=True)
    run.move(f"{n}.band", "offset", 0, SHIMMER_S, -0.25, 1.25)
    still = pose("Shimmer still", [(f"{n}.band", "offset", -2, -2)], 0)
    lay.state("run", run, lay.go("still", if_bool("done", True)), entry=True)
    lay.state("still", still, lay.go("run", if_bool("done", False)))
    lay.enter_if("still", if_bool("done", True))
    layers = [lay,
              match_layer("Done", [("plain", [if_bool("done", False)]), ("still", [if_bool("chevron", False),
                                                                                      if_bool("done", True)]),
                                   ("open", [if_bool("chevron", True), if_bool("done", True)])],
                          [(f"{n}.chev.style", "displayValue", "none", "none", "flex")]),
              bool_layer("Spinner", "spinner", [(f"{n}.star.style", "displayValue", "flex", "none"),
                                                (f"{n}.spinBox.style", "displayValue", "none", "flex")], ms=0),
              spin_layer(f"{n}.spin")]
    return component("AiProcessIndication", 160, 24, [body], machine(layers),
                     layout={"layoutWidthScaleType": "hug", "layoutHeightScaleType": "hug"})
