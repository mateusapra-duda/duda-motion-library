"""CoreInput (DS: page "Inputs", .CoreInput 146738:17158, with .label 153539:30840 and .Messaging 146738:16899).
The typing and the live field come from pecas/ui-controls v02 (Text Input).

DS props -> view model "CoreInput":
  Label / the label text        showLabel / label; required: a red asterisk after it; labelIcon: an info icon after it
  placeholder, value            placeholder / value; typed: how much of `value` shows (a piece types it with a timeline
                                or a layer: 0 = nothing, 3 = three characters; 999 = all of it, caret at the end)
  Messaging / the message       showMessage / message
  Theme: White | Grey           theme      0 White, 1 Grey
  Size: Default | Compact       size       0 Default (field 35), 1 Compact (field 25)
  State                         focused, disabled, readOnly, error, success, warning (booleans; Empty and Active are
                                the value being empty or not)
  (prototype)                   interactive: a real text field (type in it), two-way bound to `value`
"""
from kit import (VM, El, Anim, Layer, use, bind, key, box, absolute, solid, line, text, text_style, hug, fill_w,
                 icon_slot, paint_names, pose, match_layer, choice_layer, bool_layer, gate_layer, set_to, machine,
                 component, color, if_bool, if_num, if_text, listener, argb, swap_layer, STYLES, FONTS, WHITE, FADE,
                 SHORT, HOVER_MS)

INK = color("Typography/primary-text-color")
HINT = color("Typography/hint-color")
RED = color("Indications/negative-color")
GREEN = color("Indications/positive-color")
AMBER = color("Indications/warning-color")
BORDER = color("Borders/border-color")
FOCUS = color("Borders/active-border-color")
TYPED_ON = 0.5     # `typed` from which the first character shows
TYPED_ALL = 998    # `typed` at or above it: the whole value, caret at its end (the default, 999)
BLINK_S = 1.0
# the message row's height as v01 laid it out (measured: 4 + the Tiny line as Rive sizes a one-line hug text, 15.27;
# the DS line is 18). The room under the field opens to exactly this, so v02 lays out like v01
MSG_ROOM = 19.2732

CI = VM("ci", "CoreInput", [
    ("label", "string", "Label"), ("showLabel", "boolean", True), ("required", "boolean", False),
    ("labelIcon", "boolean", False), ("placeholder", "string", "Placeholder"),
    ("value", "string", ""), ("typed", "number", 999), ("message", "string", "Message"),
    ("showMessage", "boolean", False), ("theme", "number", 0), ("size", "number", 0),
    ("focused", "boolean", False), ("disabled", "boolean", False), ("readOnly", "boolean", False),
    ("error", "boolean", False), ("success", "boolean", False), ("warning", "boolean", False),
    ("interactive", "boolean", False)])


def build():
    use(CI)
    n = "CoreInput"
    text_style("ciLabel", "Content/Body", INK)
    text_style("ciReq", "Content/Body", RED)
    text_style("ciValue", "Content/Body 14", INK)
    text_style("ciPh", "Content/Body 14", HINT)
    text_style("ciCaret", "Content/Body 14", INK, font="caret")
    STYLES["ciCaret"]["weight"] = None   # the caret font has no weight axis
    text_style("ciMsg", "Content/Tiny", HINT)

    typed, caret_typed, caret_end, ph, typing_layers = typing(n, "ciValue", "ciPh", "ciCaret",
                                                              ph_also=[f"{n}.livePh"])
    area = box(f"{n}.area", [caret_typed, caret_end, typed, ph], layoutTypeValue="stack",
               layoutAlignmentType="centerLeft", **fill_w())
    # Prototype: a real one-line field, two-way bound to `value` (copilot v02 pattern)
    st = STYLES["ciValue"]
    field_in = El("TextInput", {"multiline": False}, [
        El("TextStyle", {"fontSize": st["size"], "lineHeight": st["lh"], "fontAssetId": "@font.duda",
                         "familyName": FONTS["duda"][1], "styleName": "Regular"},
           [El("TextStyleAxis", {"tag": 2003265652, "axisValue": st["weight"]})], name=f"{n}.live.font"),
        El("TextInputText", {}, [solid(f"{n}.live.text.fill", INK)], name=f"{n}.live.text"),
        El("TextInputSelection", {}, [solid(f"{n}.live.selection.fill", argb("#0A84FF", 0.3))],
           name=f"{n}.live.selection"),
        El("TextInputCursor", {}, [solid(f"{n}.live.cursor.fill", INK)], name=f"{n}.live.cursor"),
        El("FocusData", {"canFocus": False}, name=f"{n}.live.focus"),
        El("DataBindContext", {"sourcePathIds": (CI.ref(), CI.ref("value")), "propertyKey": key("TextInput", "text"),
                               "twoWay": True, "sourceToTargetRunsFirst": True}),
    ], name=f"{n}.liveInput")
    live_ph = absolute(f"{n}.livePh", [text(f"{n}.livePh.text", [("ciPh", "=placeholder")], lp=hug(), wrap=False)],
                       inset=(0, 0, None, None), **hug())
    live = box(f"{n}.live", [box(f"{n}.liveWrap", [field_in], intrinsicallySizedValue=True, **fill_w()), live_ph],
               flexDirectionValue="column", layoutAlignmentType="topLeft", displayValue="none", **fill_w())
    # the field's status icon (DS: Error validations/i_error, Success general/i_checkmark, 16, at the right)
    st_err = icon_slot(f"{n}.stError", "validations/i_error", RED)
    st_ok = icon_slot(f"{n}.stOk", "general/i_checkmark", GREEN)
    status = box(f"{n}.status", [st_err, st_ok], layoutTypeValue="stack",
                 w=16, h=16, layoutWidthScaleType="fixed", layoutHeightScaleType="fixed")
    hit = absolute(f"{n}.hit", displayValue="none")
    edge = absolute(f"{n}.border", paints=[line(f"{n}.border.stroke", BORDER, 1)], inset=(0.5,) * 4,
                    cornerRadiusTL=5.5)
    ro = absolute(f"{n}.roFill", paints=[solid(f"{n}.roFill.fill", color("Backgrounds/bg-grey-color"))], opacity=0,
                  cornerRadiusTL=6)
    fld = box(f"{n}.field", [hit, edge, area, live, status, ro], paints=[solid(f"{n}.field.fill", WHITE)],
              clip=True, flexDirectionValue="row", layoutAlignmentType="centerLeft", gapHorizontal=8, paddingLeft=8,
              paddingRight=8, cornerRadiusTL=6, h=35, layoutWidthScaleType="fill", layoutHeightScaleType="fixed")
    label = label_row(n, "ciLabel", "ciReq")
    # .Messaging: 4 px under the field, a 12 px icon, 4 px gap, Tiny 12/18
    m_info = icon_slot(f"{n}.mInfo", "common_actions/i_info_circle", HINT, size=12)
    m_err = icon_slot(f"{n}.mErr", "common_actions/i_x", RED, size=12)
    m_ok = icon_slot(f"{n}.mOk", "general/i_checkmark", GREEN, size=12)
    m_icons = box(f"{n}.mIcon", [m_info, m_err, m_ok], layoutTypeValue="stack", w=12, h=12,
                  layoutWidthScaleType="fixed", layoutHeightScaleType="fixed")
    msg = box(f"{n}.msg", [m_icons, text(f"{n}.msgText", [("ciMsg", "=message")], lp=fill_w(), overflow="ellipsis",
                                         wrap=False)],
              opacity=0, flexDirectionValue="row", layoutAlignmentType="centerLeft", gapHorizontal=4, paddingTop=4,
              **fill_w())
    # the message's room opens and closes smoothly (no reflow in one frame): a clipping box whose height animates
    msg_room = box(f"{n}.msgRoom", [msg], h=0, clip=True, flexDirectionValue="column", layoutAlignmentType="topLeft",
                   layoutWidthScaleType="fill", layoutHeightScaleType="fixed")
    col = box(f"{n}.col", [label, fld, msg_room], flexDirectionValue="column", layoutAlignmentType="topLeft",
              layoutWidthScaleType="fill", layoutHeightScaleType="hug")

    # the edge: error > success > warning > focus > rest (DS: Focus active-border, Error negative, Success positive,
    # Warning warning)
    F, T = False, True
    edge_cases = [("rest", [if_bool("error", F), if_bool("success", F), if_bool("warning", F), if_bool("focused", F)]),
                  ("focus", [if_bool("error", F), if_bool("success", F), if_bool("warning", F),
                             if_bool("focused", T)]),
                  ("error", [if_bool("error", T)]),
                  ("success", [if_bool("error", F), if_bool("success", T)]),
                  ("warning", [if_bool("error", F), if_bool("success", F), if_bool("warning", T)])]
    m_cols = (HINT, HINT, RED, GREEN, HINT)
    edge_l = match_layer("Validation", edge_cases, [
        (f"{n}.border.stroke.color", "colorValue", BORDER, FOCUS, RED, GREEN, AMBER),
        (f"{n}.msgText.ciMsg.color", "colorValue", *m_cols)]
        + [(p, "colorValue", HINT, HINT, HINT, HINT, AMBER) for p in paint_names(m_info)], ms=HOVER_MS)
    # the status and message icons swap one at a time (the outgoing one fades in 0.1 s, the next starts on its last
    # visible frame), never cross-faded; the status slot keeps its place, so nothing reflows
    icon_ls = [
        swap_layer("Error icon", [if_bool("error", T)], [[if_bool("error", F)]],
                   arrive=[(f"{n}.stError", "opacity", 0, 1), (f"{n}.mErr", "opacity", 0, 1)]),
        swap_layer("Success icon", [if_bool("error", F), if_bool("success", T)],
                   [[if_bool("error", T)], [if_bool("success", F)]],
                   arrive=[(f"{n}.stOk", "opacity", 0, 1), (f"{n}.mOk", "opacity", 0, 1)]),
        swap_layer("Info icon", [if_bool("error", F), if_bool("success", F)],
                   [[if_bool("error", T)], [if_bool("success", T)]], arrive=[(f"{n}.mInfo", "opacity", 0, 1)])]
    theme_l = choice_layer("Theme", "theme", ("White", "Grey"), [
        (f"{n}.field.fill.color", "colorValue", WHITE, color("Backgrounds/bg-grey-color")),
        (f"{n}.border", "opacity", 1, 0)])
    size_l = choice_layer("Size", "size", ("Default", "Compact"), [
        (f"{n}.field", "height", 35, 25), (f"{n}.field.style", "cornerRadiusTL", 6, 4),
        (f"{n}.roFill.style", "cornerRadiusTL", 6, 4), (f"{n}.border.style", "cornerRadiusTL", 5.5, 3.5),
        (f"{n}.typed.ciValue", "fontSize", 14, 13), (f"{n}.typed.ciValue", "lineHeight", 20, 18),
        (f"{n}.ph.ciPh", "fontSize", 14, 13), (f"{n}.ph.ciPh", "lineHeight", 20, 18),
        (f"{n}.caretTyped.ciCaret", "fontSize", 14, 13), (f"{n}.caretEnd.ciCaret", "fontSize", 14, 13)])

    # .Messaging: its room opens (duda), then it arrives (fade + 4 px up, settle); leaving, it fades, then the room
    # closes. What sits under the field moves smoothly, and the message is never drawn in a room too small for it
    room = MSG_ROOM
    m_l = Layer("Message")
    m_in = Anim("Message in", 0.25 + SHORT)
    m_in.move(f"{n}.msgRoom", "height", 0, 0.25, 0, room, "duda")
    m_in.key(f"{n}.msg", "opacity", 0, 0).move(f"{n}.msg", "opacity", 0.15, 0.15 + FADE, 0, 1)
    m_in.key(f"{n}.msg", "y", 0, 4).move(f"{n}.msg", "y", 0.15, 0.15 + SHORT, 4, 0, "settle")
    m_looks = [(f"{n}.msg", "opacity", 0, 1), (f"{n}.msg", "y", 0, 0), (f"{n}.msgRoom", "height", 0, room)]
    m_out = Anim("Message out", 0.1 + 0.25)
    m_out.move(f"{n}.msg", "opacity", 0, 0.1, 1, 0)
    m_out.key(f"{n}.msgRoom", "height", 0, room).move(f"{n}.msgRoom", "height", 0.1, 0.35, room, 0, "duda")
    m_l.state("off", pose("Message off", m_looks, 0), m_l.go("in", if_bool("showMessage", True)), entry=True)
    m_l.state("in", m_in, m_l.go("on", at_end=True), m_l.go("out", if_bool("showMessage", False)))
    m_l.state("on", pose("Message on", m_looks, 1), m_l.go("out", if_bool("showMessage", False)))
    m_l.state("out", m_out, m_l.go("off", at_end=True), m_l.go("in", if_bool("showMessage", True)))
    m_l.enter_if("on", if_bool("showMessage", True))

    ph_l, mode, caret = typing_layers()
    label_l = bool_layer("Label", "showLabel", [(f"{n}.labelRow.style", "displayValue", "none", "flex")], ms=0)
    label_ls = label_layers(n)
    ro_l = bool_layer("Read-only", "readOnly", [(f"{n}.roFill", "opacity", 0, 1),
                                                (f"{n}.typed.ciValue.color", "colorValue", INK,
                                                 color("Typography/secondary-text-color"))])
    # DS Disabled: the label in the hint colour, the field at 40 %
    disabled = bool_layer("Disabled", "disabled", [(f"{n}.field", "opacity", 1, 0.4),
                                                   (f"{n}.label.ciLabel.color", "colorValue", INK, HINT)])
    proto_looks = [(f"{n}.area.style", "displayValue", "flex", "none"),
                   (f"{n}.live.style", "displayValue", "none", "flex"), (f"{n}.live.focus", "canFocus", False, True)]
    gate = gate_layer([f"{n}.hit"], extra_off=proto_looks)
    layers = [gate, edge_l, *icon_ls, theme_l, size_l, m_l, ph_l, mode, caret, label_l, *label_ls, ro_l, disabled]
    on_field = [El("StateMachineListener", {"targetId": f"@{n}.liveInput"},
                   [El("ListenerInputType", {"listenerTypeValue": k})] + acts, name=f"field {k}")
                for k, acts in (("focus", [set_to("Boolean", "focused", True)]),
                                ("blur", [set_to("Boolean", "focused", False)]))]
    listeners = ([El("StateMachineListener", {"targetId": f"@{n}.liveInput"},
                     [El("ListenerInputTypeKeyboard", {"listenerTypeValue": "keyboard"}),
                      El("ListenerInputTypeText", {"listenerTypeValue": "textInput"})], name="field keys")] +
                 on_field + [listener(f"{n}.hit", "down", El("FocusActionTarget", {"targetId": f"@{n}.liveInput"}),
                                      name="press field")])
    return component("CoreInput", 240, 61, [col], machine(layers, listeners),
                     layout={"layoutWidthScaleType": "fixed", "layoutHeightScaleType": "hug"})


def label_row(n, s_label, s_req):
    """The DS .label: the label text, then (when the view model asks) a red asterisk (a required field) and a 16 px
    info icon in the hint colour. Elements <n>.labelRow, .label, .req, .labelInfo."""
    lab = text(f"{n}.label", [(s_label, "=label")], lp=hug(), wrap=False)
    req = text(f"{n}.req", [(s_req, "*")], lp=hug(displayValue="none"), wrap=False)
    info = icon_slot(f"{n}.labelInfo", "common_actions/i_info_circle", HINT, displayValue="none")
    return box(f"{n}.labelRow", [lab, req, info], flexDirectionValue="row", layoutAlignmentType="centerLeft",
               gapHorizontal=2, paddingBottom=8, **fill_w())


def label_layers(n):
    """The asterisk and the info icon of label_row() follow `required` and `labelIcon` (current view model)."""
    return [bool_layer("Required", "required", [(f"{n}.req.lp", "displayValue", "none", "flex")], ms=0),
            bool_layer("Label icon", "labelIcon", [(f"{n}.labelInfo.style", "displayValue", "none", "flex")], ms=0)]


def typing(n, s_value, s_ph, s_caret, ph_also=(), wrap=False):
    """A field's typing, shared by every field: the typed value, the two carets and the placeholder (texts named
    <n>.typed, .caretTyped, .caretEnd, .ph, in text styles s_value / s_ph / s_caret), and the layers that run them
    (placeholder, caret place, caret blink) from the current view model's value, typed, placeholder and focused.
    ph_also: more elements that hide with the placeholder. wrap: the texts wrap at the field's width (Text Area; the
    caret font has Duda Sans' advances, so the caret texts wrap as the value does). Returns (typed, caret_typed,
    caret_end, ph, layers): call layers() where the layers go in the build order."""
    lp = fill_w if wrap else hug
    typed = text(f"{n}.typed", [(s_value, "=value")], lp=lp(), wrap=wrap, modifiers=[
        El("TextModifierGroup", {"modifyOpacity": True, "invertOpacity": True, "opacity": 0}, [
            El("TextModifierRange", {"typeValue": 1, "modifyFrom": 0, "modifyTo": 100000, "falloffFrom": 0,
                                     "falloffTo": 100000},
               [bind("typed", key("TextModifierRange", "modifyFrom")),
                bind("typed", key("TextModifierRange", "falloffFrom"))], name=f"{n}.typed.rest")],
           name=f"{n}.typed.hide")])
    # the caret font draws every glyph as a bar at its left edge, with Duda Sans' advances (copilot learning):
    # caretTyped shows the bar of glyph `typed` (the next one to be typed); caretEnd the bar after the whole value
    rng = [bind("typed", key("TextModifierRange", "modifyFrom")),
           bind("typed", key("TextModifierRange", "falloffFrom")),
           bind("typed", key("TextModifierRange", "modifyTo"), converter="conv.plus1"),
           bind("typed", key("TextModifierRange", "falloffTo"), converter="conv.plus1")]
    caret_typed = text(f"{n}.caretTyped", [(s_caret, "=value"), (s_caret, "|")], lp=lp(), wrap=wrap, modifiers=[
        El("TextModifierGroup", {"modifyOpacity": True, "opacity": 1}, [
            El("TextModifierRange", {"typeValue": 1, "modifyFrom": 0, "modifyTo": 1, "falloffFrom": 0,
                                     "falloffTo": 1}, rng, name=f"{n}.caretTyped.pick")],
           name=f"{n}.caretTyped.only")])
    caret_end = text(f"{n}.caretEnd", [(s_caret, "=value"), (s_caret, "|")], lp=lp(displayValue="none"),
                     wrap=wrap, modifiers=[El("TextModifierGroup", {"modifyOpacity": True, "opacity": 1}, [
                         El("TextModifierRange", {"modifyFrom": 0, "modifyTo": 1, "falloffFrom": 0, "falloffTo": 1,
                                                  "runId": f"@{n}.caretEnd.run1"}, name=f"{n}.caretEnd.pick")],
                         name=f"{n}.caretEnd.only")])
    ph = text(f"{n}.ph", [(s_ph, "=placeholder")], lp=lp(), wrap=wrap)
    def layers():
        """The layers (placeholder, caret place, caret blink); call it where they go in the build order."""
        def shown():
            return [if_num("typed", "greaterThanOrEqual", TYPED_ON), if_text("value", "notEqual", converter="conv.trim")]
        ph_l = Layer("Placeholder")
        ph_looks = [(t, "opacity", 1, 0) for t in (f"{n}.ph",) + tuple(ph_also)]
        ph_l.state("empty", pose("Placeholder shown", ph_looks, 0), ph_l.go("filled", *shown()), entry=True)
        ph_l.state("filled", pose("Placeholder hidden", ph_looks, 1),
                   ph_l.go("empty", if_num("typed", "lessThan", TYPED_ON)),
                   ph_l.go("empty", if_text("value", "equal", converter="conv.trim")))
        ph_l.enter_if("filled", *shown())

        mode = Layer("Caret place")
        mode_looks = [(f"{n}.caretTyped.lp", "displayValue", "flex", "none"),
                      (f"{n}.caretEnd.lp", "displayValue", "none", "flex")]
        mode.state("typing", pose("Caret at typed", mode_looks, 0),
                   mode.go("end", if_num("typed", "greaterThanOrEqual", TYPED_ALL)), entry=True)
        mode.state("end", pose("Caret at end", mode_looks, 1), mode.go("typing", if_num("typed", "lessThan", TYPED_ALL)))
        mode.enter_if("end", if_num("typed", "greaterThanOrEqual", TYPED_ALL))

        # the caret blinks while the field waits (empty, or the whole value shown) and stays on while typing
        caret = Layer("Caret")
        c_looks = [(f"{n}.caretTyped", "opacity", 0, 1), (f"{n}.caretEnd", "opacity", 0, 1)]
        blink = Anim("Caret blink", BLINK_S, loop=True)
        for c in (f"{n}.caretTyped", f"{n}.caretEnd"):
            blink.hold(c, "opacity", 1).key(c, "opacity", BLINK_S / 2, 0)

        def idle():
            return [if_num("typed", "lessThan", TYPED_ON)], [if_num("typed", "greaterThanOrEqual", TYPED_ALL)]
        caret.state("off", pose("Caret off", c_looks, 0),
                    *[caret.go("blink", if_bool("focused", True), *c) for c in idle()],
                    caret.go("solid", if_bool("focused", True)), entry=True)
        caret.state("blink", blink, caret.go("off", if_bool("focused", False)),
                    caret.go("solid", if_num("typed", "greaterThanOrEqual", TYPED_ON),
                             if_num("typed", "lessThan", TYPED_ALL)))
        caret.state("solid", pose("Caret on", c_looks, 1), caret.go("off", if_bool("focused", False)),
                    *[caret.go("blink", *c) for c in idle()])
        return [ph_l, mode, caret]
    return typed, caret_typed, caret_end, ph, layers
