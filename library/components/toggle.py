"""Core Toggle (DS: page "Selection Controls", set 113051:62826).

DS props -> view model "Core Toggle":
  Style: Toggle | Switch      variant     0 Toggle (28x18, the knob carries a check when on), 1 Switch (48x30 pill)
  State: Off/On (Left/Right)  on
  Condition: Disabled         disabled
  (polish, not in the DS)     pressed (the control dips to 92 %); the knob stretches as it travels
  (prototype)                 interactive: a click flips it; clicked fires; click plays a press from outside
"""
from kit import (VM, El, Anim, Layer, use, box, absolute, shape_rect, shape_ellipse, open_path, pose, choice_layer,
                 bool_layer, gate_layer, press_layer, listener, fire, set_to, machine, component, color, if_bool,
                 if_trigger, tick, WHITE)

DARK = color("Backgrounds/bg-dark-color")             # on track, the switch's knob, the check
OFF = color("Background/bg-dark-grey-color")          # off track (#93959A)
EDGE = color("Borders/active-border-color")           # the switch's pill edge (#AEAFB3)
EDGE_OFF = color("Indications/disabled-item-color")   # ... disabled (#C9CACD)
# knob centres (x) off / on: Toggle 15 px knob at 2 / 12; Switch 24 px knob at 3 / 21
TG_X, SW_X = (9.5, 19.5), (15.0, 33.0)
CHECK = [(-3, 0), (-1, 2), (3, -2)]                   # the DS check (6x4, stroke 1.25), on the knob's centre
TRAVEL = 0.25                                         # the knob's travel (duda); the check draws on after it

TOGGLE = VM("toggle", "Core Toggle", [
    ("variant", "number", 0), ("on", "boolean", False), ("disabled", "boolean", False),
    ("pressed", "boolean", False), ("interactive", "boolean", False),
    ("click", "trigger", None), ("clicked", "trigger", None), ("_flip", "trigger", None)])


def build():
    use(TOGGLE)
    n = "CoreToggle"
    tg_knob = El("Node", {"x": TG_X[0], "y": 9}, [
        open_path(f"{n}.check", CHECK, DARK, 1.25, trim_end=0),
        shape_ellipse(f"{n}.tgKnob", 15, fill=WHITE)], name=f"{n}.tgKnobNode")
    # order="layers": children listed bottom to top (in RML the first child draws on top)
    tg_dim = El("Node", {}, [shape_rect(f"{n}.track", 28, 18, 9, fill=OFF, x=14, y=9), tg_knob],
                name=f"{n}.toggleDim", order="layers")
    tg = El("Node", {}, [tg_dim], name=f"{n}.toggleArt")   # Style shows / hides it; Disabled dims the inner node
    sw_knob = shape_ellipse(f"{n}.swKnob", 24, fill=DARK, x=SW_X[0], y=15)
    sw = El("Node", {"opacity": 0}, [shape_rect(f"{n}.pill", 47, 29, 14.5, fill=WHITE, stroke=EDGE, x=24, y=15),
                                     sw_knob], name=f"{n}.switchArt", order="layers")
    hit = absolute(f"{n}.hit", displayValue="none")
    body = box(f"{n}.box", [hit, tg, sw], origin=(0.5, 0.5), w=28, h=18, layoutWidthScaleType="fixed",
               layoutHeightScaleType="fixed")

    variant_l = choice_layer("Style", "variant", ("Toggle", "Switch"), [
        (f"{n}.box", "width", 28, 48), (f"{n}.box", "height", 18, 30),
        (f"{n}.toggleArt", "opacity", 1, 0), (f"{n}.switchArt", "opacity", 0, 1)])
    # on / off: both drawings move together (only one shows); the knob stretches on the way, the track takes the
    # colour, and the Toggle's check draws on once the knob has landed
    rest = [(f"{n}.tgKnobNode", "x", *TG_X), (f"{n}.swKnob", "x", *SW_X),
            (f"{n}.track.fill.color", "colorValue", OFF, DARK), (f"{n}.check.trim", "end", 0, 1)]

    def travel(name, forward):
        a = Anim(name, TRAVEL + (0.22 if forward else 0))
        i0, i1 = (0, 1) if forward else (1, 0)
        a.move(f"{n}.tgKnobNode", "x", 0, TRAVEL, TG_X[i0], TG_X[i1], "duda")
        a.move(f"{n}.swKnob", "x", 0, TRAVEL, SW_X[i0], SW_X[i1], "duda")
        for t, w0, w1 in ((f"{n}.tgKnob.ellipse", 15, 17.5), (f"{n}.swKnob.ellipse", 24, 28)):
            a.move(t, "width", 0, TRAVEL / 2, w0, w1, "duda").move(t, "width", TRAVEL / 2, TRAVEL, w1, w0, "duda")
        a.move(f"{n}.track.fill.color", "colorValue", 0, TRAVEL, (OFF, DARK)[i0], (OFF, DARK)[i1], "duda")
        if forward:
            a.key(f"{n}.check.trim", "end", 0, 0).move(f"{n}.check.trim", "end", TRAVEL - 0.08, TRAVEL + 0.22, 0, 1,
                                                       "settle")
        else:
            a.move(f"{n}.check.trim", "end", 0, 0.1, 1, 0)
        return a
    sw_l = Layer("On")
    sw_l.state("off", pose("Toggle off", rest, 0), sw_l.go("turnOn", if_bool("on", True)), entry=True)
    sw_l.state("turnOn", travel("Toggle turn on", True), sw_l.go("on", at_end=True),
               sw_l.go("turnOff", if_bool("on", False)))
    sw_l.state("on", pose("Toggle on", rest, 1), sw_l.go("turnOff", if_bool("on", False)))
    sw_l.state("turnOff", travel("Toggle turn off", False), sw_l.go("off", at_end=True),
               sw_l.go("turnOn", if_bool("on", True)))
    sw_l.enter_if("on", if_bool("on", True))

    clicks = Layer("Clicks")
    t = tick()
    clicks.state("ready", None, clicks.go("setOn", if_trigger("_flip"), if_bool("on", False)),
                 clicks.go("setOff", if_trigger("_flip"), if_bool("on", True)), entry=True)
    clicks.state("setOn", t, clicks.go("ready", at_end=True), actions=[set_to("Boolean", "on", True)])
    clicks.state("setOff", t, clicks.go("ready", at_end=True), actions=[set_to("Boolean", "on", False)])
    disabled = bool_layer("Disabled", "disabled", [
        (f"{n}.toggleDim", "opacity", 1, 0.4), (f"{n}.swKnob", "opacity", 1, 0.4),
        (f"{n}.pill.stroke.color", "colorValue", EDGE, EDGE_OFF)])
    press = press_layer(f"{n}.box", 0.92)
    layers = [gate_layer([f"{n}.hit"]), variant_l, clicks, sw_l, press, disabled]
    listeners = [listener(f"{n}.hit", "down", set_to("Boolean", "pressed", True), name="press"),
                 listener(f"{n}.hit", "up", set_to("Boolean", "pressed", False), name="release"),
                 listener(f"{n}.hit", "exit", set_to("Boolean", "pressed", False), name="leave"),
                 listener(f"{n}.hit", "click", fire("_flip"), fire("clicked"))]
    return component("Core Toggle", 28, 18, [body], machine(layers, listeners),
                     layout={"layoutWidthScaleType": "hug", "layoutHeightScaleType": "hug"})
