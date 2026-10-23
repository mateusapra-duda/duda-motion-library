"""Core Radio Button (DS: page "Selection Controls", set 83:2318).

DS props -> view model "Core Radio Button":
  Selected: On | Off      selected
  Disabled                disabled
  (polish, not in the DS) pressed (dips to 88 %); the dot grows in (200 ms, duda)
  (prototype)             interactive: a click selects it (a radio never unselects itself); clicked fires;
                          click plays a press from outside
"""
from kit import (VM, El, use, box, absolute, shape_ellipse, bool_layer, gate_layer, press_layer, listener, fire,
                 set_to, machine, component, color, WHITE)

DARK = color("Backgrounds/bg-dark-color")
EDGE = color("Indications/disabled-item-color")

RADIO = VM("radio", "Core Radio Button", [
    ("selected", "boolean", False), ("disabled", "boolean", False), ("pressed", "boolean", False),
    ("interactive", "boolean", False), ("click", "trigger", None), ("clicked", "trigger", None)])


def build():
    use(RADIO)
    n = "CoreRadio"
    dot = El("Node", {"x": 9, "y": 9, "scaleX": 0, "scaleY": 0}, [shape_ellipse(f"{n}.dot", 6, fill=WHITE)],
             name=f"{n}.dotNode")
    art = El("Node", {}, [shape_ellipse(f"{n}.ring", 17, fill=WHITE, stroke=EDGE, x=9, y=9),
                          shape_ellipse(f"{n}.fill", 17, fill=DARK, stroke=EDGE, x=9, y=9, opacity=0), dot],
             name=f"{n}.art", order="layers")
    hit = absolute(f"{n}.hit", displayValue="none")
    body = box(f"{n}.box", [hit, art], origin=(0.5, 0.5), w=18, h=18, layoutWidthScaleType="fixed",
               layoutHeightScaleType="fixed")
    sel = bool_layer("Selected", "selected", [(f"{n}.fill", "opacity", 0, 1), (f"{n}.dotNode", "scaleX", 0, 1),
                                              (f"{n}.dotNode", "scaleY", 0, 1)], ms=200)
    disabled = bool_layer("Disabled", "disabled", [(f"{n}.box", "opacity", 1, 0.4)])
    press = press_layer(f"{n}.box", 0.88)
    layers = [gate_layer([f"{n}.hit"]), sel, press, disabled]
    listeners = [listener(f"{n}.hit", "down", set_to("Boolean", "pressed", True), name="press"),
                 listener(f"{n}.hit", "up", set_to("Boolean", "pressed", False), name="release"),
                 listener(f"{n}.hit", "exit", set_to("Boolean", "pressed", False), name="leave"),
                 listener(f"{n}.hit", "click", set_to("Boolean", "selected", True), fire("clicked"))]
    return component("Core Radio Button", 18, 18, [body], machine(layers, listeners),
                     layout={"layoutWidthScaleType": "hug", "layoutHeightScaleType": "hug"})
