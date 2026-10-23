"""Core Checkbox (DS: page "Selection Controls", set 83:2315).

DS props -> view model "Core Checkbox":
  State: Empty | On | Partial   state       0 Empty, 1 On, 2 Partial
  Condition: Disabled           disabled
  (polish, not in the DS)       pressed (dips to 88 %); the box fills and the check draws on (200 ms, duda)
  (prototype)                   interactive: a click toggles Empty <-> On (Partial -> On); clicked fires;
                                click plays a press from outside
"""
from kit import (VM, El, Layer, use, box, absolute, shape_rect, open_path, choice_layer, bool_layer, gate_layer,
                 press_layer, listener, fire, set_to, machine, component, color, if_num, if_trigger, tick, WHITE)

DARK = color("Backgrounds/bg-dark-color")
EDGE = color("Indications/disabled-item-color")    # the empty box's edge (#C9CACD)
CHECK = [(4.25, 8), (6.75, 10.5), (11.75, 5.5)]    # DS "Vector" 7.5x5 at (4, 6), stroke 1.25
DASH = [(5, 8), (11, 8)]                           # DS Partial: 6 px at y 8
MS = 200

CHECKBOX = VM("checkbox", "Core Checkbox", [
    ("state", "number", 0), ("disabled", "boolean", False), ("pressed", "boolean", False),
    ("interactive", "boolean", False), ("click", "trigger", None), ("clicked", "trigger", None),
    ("_flip", "trigger", None)])


def build():
    use(CHECKBOX)
    n = "CoreCheckbox"
    art = El("Node", {}, [
        shape_rect(f"{n}.empty", 15, 15, 3.5, fill=WHITE, stroke=EDGE, x=8, y=8),
        shape_rect(f"{n}.fill", 16, 16, 4, fill=DARK, x=8, y=8, opacity=0),
        open_path(f"{n}.check", CHECK, WHITE, 1.25, trim_end=0),
        open_path(f"{n}.dash", DASH, WHITE, 1.25, trim_end=0)], name=f"{n}.art", order="layers")
    hit = absolute(f"{n}.hit", displayValue="none")
    body = box(f"{n}.box", [hit, art], origin=(0.5, 0.5), w=16, h=16, layoutWidthScaleType="fixed",
               layoutHeightScaleType="fixed")
    state_l = choice_layer("State", "state", ("Empty", "On", "Partial"), [
        (f"{n}.fill", "opacity", 0, 1, 1), (f"{n}.check.trim", "end", 0, 1, 0), (f"{n}.dash.trim", "end", 0, 0, 1)],
        ms=MS)
    clicks = Layer("Clicks")
    t = tick()
    clicks.state("ready", None, clicks.go("check", if_trigger("_flip"), if_num("state", "notEqual", 1)),
                 clicks.go("clear", if_trigger("_flip"), if_num("state", "equal", 1)), entry=True)
    clicks.state("check", t, clicks.go("ready", at_end=True), actions=[set_to("Number", "state", 1)])
    clicks.state("clear", t, clicks.go("ready", at_end=True), actions=[set_to("Number", "state", 0)])
    disabled = bool_layer("Disabled", "disabled", [(f"{n}.box", "opacity", 1, 0.4)])
    press = press_layer(f"{n}.box", 0.88)
    layers = [gate_layer([f"{n}.hit"]), state_l, clicks, press, disabled]
    listeners = [listener(f"{n}.hit", "down", set_to("Boolean", "pressed", True), name="press"),
                 listener(f"{n}.hit", "up", set_to("Boolean", "pressed", False), name="release"),
                 listener(f"{n}.hit", "exit", set_to("Boolean", "pressed", False), name="leave"),
                 listener(f"{n}.hit", "click", fire("_flip"), fire("clicked"))]
    return component("Core Checkbox", 16, 16, [body], machine(layers, listeners),
                     layout={"layoutWidthScaleType": "hug", "layoutHeightScaleType": "hug"})
