"""AiPanel (DS: AiPanel with ChatInput, AiProcessIndication, UserChatInput, AiChatOutput, AiOutputActionBar,
InitialSuggestions): the Duda AI chat, docked (the Vibe editor's chat, 406 wide, a line at its left) or floating (the
Copilot, 368 wide, rounded, with a shadow and its own toolbar). v05: the copilot component (pecas/copilot v04) moved
into the library: the same layout, states and timings (measured on the product, my.duda.co 2026-10-21; details from
the Figma storyboards), with the DS colours, icons and stroke, and the reply as the product brings it.

View model "AiPanel":
  texts          title, titleAfter (the chat's name once the reply is in), greeting, subtitle, chip1..chip4, showMore,
                 placeholder, placeholderAfter, prompt (typed into the field, then the user's bubble), status
                 ("Thinking..."), thought, reply, reply2, reply3 (the answer's paragraphs; an empty one is left out),
                 build (the mode button), disclaimer, link
  copilot        false: docked (Vibe). true: floating (Copilot)
  hidden         closed: docked, it slides out to the right; floating, it shrinks into its corner button and fades
                 (0.4 s, the product's curves). Back to false opens it, the suggestions cascading in
  typed          how much of `prompt` is typed into the field (0 nothing); the send button turns orange from 1
  focused        the field's border darkens; the caret blinks while the field is empty
  stage          the conversation: 0 nothing sent (the greeting and the suggestions); 1 sent (the bubble; under it the
                 star turns in and "Thinking..." wipes in and shimmers; the stop button); 2, 3, 4 each paragraph of the
                 reply comes in below the status (2 also swaps it where it is for `thought`, "Thought for 3s", without
                 the star, then its chevron: the paragraphs wait the swap's 9 frames); 5 done (the action bar comes in
                 under the reply, the chat is renamed: floating already 1.1 s after sending). v08: Mateus's copilot
                 motion (hero-view v10); the product pushes "Thinking..." down under the answer instead
  figmaActions   Figma: like, dislike, copy, undo, more (the product: copy, more)
  hover<Control> each control's hover (also from the mouse): Chip1..4, Float, Options, Expand, Plus, Tool, At, Mic,
                 Send, Like, Dislike, Copy, Undo, More
  interactive    the prototype: a real text field (`draft`, two-way), clicks, Enter, a corner button that reopens it
  triggers       open / close (hidden false / true), send (stage 1), respond (stage 2.. 5 at the product's pace),
                 reset (stage 0, the field emptied)
The placement gives the size (p.ai_panel(slot, w=406, h=...)).
"""
import math
import os

import kit
from kit import (VM, El, Anim, Layer, use, bind, key, box, solid, line, absolute, set_to, fire, if_bool, if_num,
                 if_trigger, if_text, hover_listeners, machine, component, color, argb, icon, ICONS, ICON_STROKE,
                 FPS, WHITE, CLEAR, SWAP)
from components.ai_process import (wipe, wipe_in, wipe_out, wipe_looks, HIDDEN, SHOWN, GONE, STAR_AT, LABEL_AT, TURN,
                                   STAR_FADE, OUT_FADE, THOUGHT_AT, CHEV_AT, CHEV_FADE)

PREFIX = "AiPanel."      # every element of the component is named AiPanel.<name>
INK = color("Typography/primary-text-color")
INK2 = color("Typography/secondary-text-color")
MUTED = color("Typography/hint-color")
LINE = color("Borders/border-light-color")
LINE_FOCUS = color("Borders/active-border-color")
SOFT = color("Backgrounds/bg-grey-color")
THUMB = color("Backgrounds/bg-med-grey-color")
OFF = color("Indications/disabled-item-color")
ORANGE = color("Custom Branding/Primary-color")
HOVER = argb("#000000", 0.08)     # icon button hover (IconButton dark)
SELECT = argb("#0A84FF", 0.3)     # prototype: selected text in the field (the browser's highlight)

HEADER_H = 48            # .AiChatPanelsHeader: 12 + 24 + 12
INPUT_MIN_H = 32         # ChatInput "Input area": 12 + one 20 px line
TOOL_DIVIDER_H = 18      # CoreDivider vertical in the input actions
STATUS_PAD = 2           # Chat Status Indication: 2 above and below the line
DOCKED_W, FLOATED_W, DEFAULT_H = 406, 368, 720

for _k, _v in {"panel": (0.44, 0.0, 0.02, 1.0),        # chatPopupMoveIn / DockedSlideIn
               "panel_out": (0.26, 0.26, 0.0, 1.0),    # chatPopupFadeOut
               "in_out": (0.42, 0.0, 0.58, 1.0),       # CSS ease-in-out (chatPopupFadeIn)
               "out": (0.0, 0.0, 0.58, 1.0)}.items():  # CSS ease-out
    kit.EASE[f"aip_{_k}"] = _v
OPEN_S = 0.4
STAGGER = (0.25, 0.05)   # InitialSuggestions: first item at 0.25 s, then +50 ms each
SHIMMER_S = 1.6          # AiProcessIndication shimmer period
BLINK_S = 1.0            # ChatInput caret blink
TITLE_COPILOT_S = 1.1    # floating: the chat is renamed this long after sending, while it still thinks
THINK_S = 2.5            # prototype: from sending to the reply
ROOM_S = 0.25            # a paragraph's room opens (the conversation glides to its new place)
PARA_IN = (0.25, 0.5)    # then the paragraph comes in: from, how long (4 px up, fading in)
STEP_S = 0.27            # respond: the next paragraph this long after the last one
THEN_S = 0.083           # respond: the action bar comes in this long after the last paragraph is in
SWAP_LEAD = 9 / 60       # v08: the status swap starts this long before the first paragraph (hero-view v10)

TEXTS = [
    ("title", "New chat"), ("titleAfter", "Studio HQ client project dashboard"), ("greeting", "Hello,"),
    ("subtitle", "How can I help you today?"), ("chip1", "What Copilot can do"), ("chip2", "Create a new site"),
    ("chip3", "Create a new client"), ("chip4", "Get template recommendations"), ("showMore", "Show more"),
    ("placeholder", "Describe your idea..."), ("placeholderAfter", "Describe your idea..."),
    ("prompt", "Build Studio HQ, a private dashboard for my team to track client projects, who they're assigned to, "
               "and their status, with a shared weekly schedule."),
    ("status", "Thinking..."), ("thought", "Thought for 3s"),
    ("reply", "Studio HQ is ready! Here's what I built: a personal greeting with today's date, team stats, a My "
              "Projects table with status tags and a shared weekly schedule."),
    ("reply2", "Need changes? Click any element to edit."), ("reply3", ""),
    ("build", "Build"), ("disclaimer", "Copilot is AI and can make mistakes."), ("link", "Learn more"),
]
REPLIES = ("reply", "reply2", "reply3")
HOVERS = ["Chip1", "Chip2", "Chip3", "Chip4", "Float", "Options", "Expand", "Plus", "Tool", "At", "Mic", "Send",
          "Like", "Dislike", "Copy", "Undo", "More"]
CLICKS = ["_send", "_chip1", "_chip2", "_chip3", "_chip4", "_close", "_open"]   # prototype: what a click asks for
AIP = VM("aipanel", "AiPanel", [(n, "string", v) for n, v in TEXTS] + [
    ("draft", "string", ""), ("copilot", "boolean", False), ("hidden", "boolean", False), ("typed", "number", 0),
    ("focused", "boolean", False), ("stage", "number", 0),
    ("figmaActions", "boolean", False), ("interactive", "boolean", False)] +
    [(f"hover{h}", "boolean", False) for h in HOVERS] +
    [(t, "trigger", None) for t in ["open", "close", "send", "respond", "reset"] + CLICKS])
# the parts a piece aims the cursor at (p.ai_panel(...).part("send")): part -> (element, hover property)
PARTS = {"send": ("SendBtn", "hoverSend"), "field": ("InputArea", None), "plus": ("PlusBtn", "hoverPlus"),
         "tool": ("ToolBtn", "hoverTool"), "mic": ("MicBtn", "hoverMic"), "build": ("BuildBtn", None),
         "options": ("OptionsBtn", "hoverOptions"), "collapse": ("ExpandBtn", "hoverExpand"),
         "float": ("FloatBtn", "hoverFloat"), "at": ("AtBtn", "hoverAt"), "copy": ("CopyBtn", "hoverCopy"),
         "more": ("MoreBtn", "hoverMore"), "like": ("LikeBtn", "hoverLike"), "dislike": ("DislikeBtn", "hoverDislike"),
         "undo": ("UndoBtn", "hoverUndo"), "showMore": ("ShowMore", None),
         **{f"chip{i}": (f"Chip{i}", f"hoverChip{i}") for i in range(1, 5)}}
# the DS icons it draws (icons/<category>/<name>.svg); v05 added the product's like, dislike, floating_panel and the
# suggestions' binoculars, new_site, user, template
ICON = {"floating_panel": "general/i_floating_panel", "chevron": "arrows/chevron_bottom", "options": "general/i_options",
        "expand": "arrows/i_common_expand", "ai": "special/i_ai_assistant", "like": "general/i_like",
        "dislike": "general/i_dislike", "copy": "common_actions/i_duplicate", "undo": "common_actions/i_undo",
        "arrow_top": "arrows/i_arrow_top", "cursor": "general/i_cursor", "plus": "common_actions/i_plus",
        "at": "general/i_at", "mic": "general/i_mic", "binoculars": "general/i_binoculars",
        "new_site": "general/i_new_site", "user": "general/i_user", "template": "general/i_template"}


# ---------------------------------------------------------------- text (heights as in the browser)
FONT_ASCENT, FONT_DESCENT = 0.960, 0.253
STYLES = {
    "aipTitle": dict(size=16, lh=22, weight=550, color=INK),
    "aipH": dict(size=18, lh=24, weight=550, color=INK),
    "aipSub": dict(size=14, lh=20, weight=350, color=MUTED),
    "aipChip": dict(size=14, lh=20, weight=350, color=INK),
    "aipSmall": dict(size=12, lh=18, weight=550, color=INK2),
    "aipBuild": dict(size=12, lh=18, weight=550, color=INK),
    "aipBubble": dict(size=14, lh=20, weight=350, color=INK),
    "aipBody": dict(size=14, lh=20, weight=350, color=INK),
    "aipStatus": dict(size=14, lh=20, weight=350, color=INK2),
    "aipInput": dict(size=14, lh=20, weight=350, color=INK),
    "aipPh": dict(size=14, lh=20, weight=350, color=MUTED),
    "aipCaret": dict(size=14, lh=20, color=INK, font="caret"),
    "aipMini": dict(size=11, lh=16, weight=550, color=MUTED),
    "aipUnder": dict(size=11, lh=16, color=MUTED, font="under"),
}


def _leading(st):
    s = STYLES[st]
    return s["lh"] - (FONT_ASCENT + FONT_DESCENT) * s["size"]


def above(st):
    """Rive starts a text's box at its first line's ascent and splits the leading by ascent : descent; the browser
    puts half the leading above. A box around the text adds the difference on top..."""
    return round(_leading(st) / 2, 2)


def below(st):
    """...and this under it, so the block measures lines x lineHeight (copilot v04 NOTES: 14/20 measures 20, not 17.6)."""
    return round(_leading(st) * (FONT_ASCENT / (FONT_ASCENT + FONT_DESCENT) - 0.5), 2)


def text(*a, **kw):
    return kit.text(*a, **kw)


def hug(**kw):
    return kit.hug(**kw)


def fill_w(**kw):
    return kit.fill_w(**kw)


def _style_of(b):
    return next(c for c in b.children if isinstance(c, El) and c.tag == "LayoutComponentStyle")


def glide(b):
    """The box eases to its new place when the conversation reflows (ROOM_S, the duda curve): a paragraph opening its
    room pushes what is under it down smoothly."""
    e = kit.EASE["duda"]
    st = _style_of(b)
    st.attrs.update(animationStyleType="custom", interpolationType="cubic", interpolationTime=ROOM_S)
    st.children.append(El("CubicEaseInterpolator", {"x1": e[0], "y1": e[1], "x2": e[2], "y2": e[3]}))
    return b


# ---------------------------------------------------------------- parts
def hover_bg(name, radius=6, col=HOVER):
    """IconButton::before: the tile that appears behind a control on hover."""
    return absolute(f"{name}.hover", paints=[solid(f"{name}.hover.fill", col)], opacity=0, cornerRadiusTL=radius)


def icon_slot(name, ic, col=INK, size=16, slot=None, flip=False):
    """A DS icon at its size, centred in a fixed slot. flip: turned 180 degrees (the chevron pointing up)."""
    slot = slot or size
    off = (slot - size) / 2
    art = icon(os.path.join(ICONS, f"{ICON[ic]}.svg"), f"{name}.art", col, stroke_w=ICON_STROKE, x=off, y=off,
               size=size)
    if flip:   # about the art's top-left corner, so it moves by its size to land in the same square
        art.attrs.update({"rotation": math.pi, "x": art.attrs["x"] + size, "y": art.attrs["y"] + size})
    return box(name, [art], w=slot, h=slot, layoutWidthScaleType="fixed", layoutHeightScaleType="fixed")


def icon_button(name, ic, col=INK, display=None):
    """IconButton small: 24x24, radius 6, the hover tile behind the 16 px icon."""
    art = icon(os.path.join(ICONS, f"{ICON[ic]}.svg"), f"{name}.art", col, stroke_w=ICON_STROKE, x=4, y=4, size=16)
    return box(name, [art, hover_bg(name)], w=24, h=24, layoutWidthScaleType="fixed", layoutHeightScaleType="fixed",
               displayValue=display)


def divider(name, h):
    return box(name, w=1, h=h, paints=[solid(f"{name}.fill", LINE)], layoutWidthScaleType="fixed",
               layoutHeightScaleType="fixed")


def spacer(name):
    return box(name, w=0, h=1, layoutWidthScaleType="fill", layoutHeightScaleType="fixed")


def header():
    title_lp = dict(hug(), maxWidth=204)
    return box("Header", [
        icon_button("FloatBtn", "floating_panel", display="none"),
        box("TitleBtn", [
            text("TitleA", [("aipTitle", "=title")], lp=dict(title_lp), overflow="ellipsis", wrap=False),
            text("TitleB", [("aipTitle", "=titleAfter")], lp=dict(title_lp, displayValue="none"), overflow="ellipsis",
                 wrap=False),
            icon_slot("TitleChev", "chevron"),
        ], flexDirectionValue="row", layoutAlignmentType="centerLeft", gapHorizontal=8, **hug()),
        spacer("HeaderSpacer"),
        box("Actions", [icon_button("OptionsBtn", "options"), divider("HeaderDivider", 18),
                        icon_button("ExpandBtn", "expand")],
            flexDirectionValue="row", layoutAlignmentType="centerLeft", gapHorizontal=6, **hug()),
    ], h=HEADER_H, flexDirectionValue="row", layoutAlignmentType="centerLeft", gapHorizontal=8, paddingLeft=16,
        paddingRight=16, layoutWidthScaleType="fill", layoutHeightScaleType="fixed")


def chip(i, ic):
    n = f"Chip{i}"
    grad = El("Fill", {}, [El("LinearGradient", {"startX": 0, "startY": 0, "endX": 0, "endY": 24}, [
        El("GradientStop", {"colorValue": argb("#D6F6FF"), "position": 0}),
        El("GradientStop", {"colorValue": argb("#E0D3FF"), "position": 1})])], name=f"{n}.thumb.grad")
    thumb = box(f"{n}.thumb", [
        icon(os.path.join(ICONS, f"{ICON[ic]}.svg"), f"{n}.icon", INK, stroke_w=ICON_STROKE, x=4, y=4, size=16),
        absolute(f"{n}.thumb.hover", paints=[grad], opacity=0, cornerRadiusTL=6),
    ], w=24, h=24, paints=[solid(f"{n}.thumb.fill", THUMB)], cornerRadiusTL=6, layoutWidthScaleType="fixed",
        layoutHeightScaleType="fixed")
    return box(n, [thumb, text(f"{n}.label", [("aipChip", f"=chip{i}")], lp=hug(), overflow="ellipsis", wrap=False)],
               h=38, paints=[solid(f"{n}.fill", SOFT), line(f"{n}.border", CLEAR)], flexDirectionValue="row",
               layoutAlignmentType="centerLeft", gapHorizontal=12, paddingLeft=7, paddingRight=7, cornerRadiusTL=8,
               layoutWidthScaleType="fill", layoutHeightScaleType="fixed")


def empty_state():
    """InitialSuggestions: the greeting, four suggestions, "Show more"."""
    return box("Empty", [
        box("Hello", [text("Greeting", [("aipH", "=greeting")], lp=hug(), align="center"),
                      text("Subtitle", [("aipSub", "=subtitle")], lp=hug(), align="center")],
            flexDirectionValue="column", layoutAlignmentType="topCenter", gapVertical=2 + below("aipH") + above("aipSub"),
            paddingTop=above("aipH"), paddingBottom=below("aipSub"), **hug()),
        box("Chips", [chip(1, "binoculars"), chip(2, "new_site"), chip(3, "user"), chip(4, "template"),
                      box("ShowMore", [text("ShowMore.label", [("aipSmall", "=showMore")], lp=hug(), wrap=False),
                                       icon_slot("ShowMore.chev", "chevron", col=INK2, size=14), hover_bg("ShowMore")],
                          flexDirectionValue="row", layoutAlignmentType="centerLeft", gapHorizontal=4, marginTop=4,
                          paddingTop=above("aipSmall"), paddingBottom=below("aipSmall"), **hug())],
            flexDirectionValue="column", layoutAlignmentType="topLeft", gapVertical=8, marginTop=24, **fill_w()),
    ], flexDirectionValue="column", layoutAlignmentType="topCenter", paddingTop=56, paddingLeft=24, paddingRight=24,
        **fill_w())


def shimmer_group(name):
    """AiProcessIndication.shimmer: a band where the text drops to 37 %, crossing it every 1.6 s."""
    return El("TextModifierGroup", {"modifyOpacity": True, "invertOpacity": True, "opacity": 0.37}, [
        El("TextModifierRange", {"modifyFrom": -0.36, "modifyTo": 0.36, "falloffFrom": 0, "falloffTo": 0,
                                 "offset": -0.4, "clamp": False}, name=f"{name}.band")], name=name)


def messages():
    """The user's bubble, then the output: the head (the status, and "Thought for 3s" in the same place), the reply's
    paragraphs (each its own room, hidden until its stage) and the action bar."""
    star_art = icon(os.path.join(ICONS, f"{ICON['ai']}.svg"), "Status.star.art", INK2, stroke_w=ICON_STROKE, x=-8,
                    y=-8, size=16)
    status = box("Status", [
        box("Status.star", [El("Node", {"x": 8, "y": 8}, [star_art], name="Status.turn")], w=16, h=16,   # turns on
            layoutWidthScaleType="fixed", layoutHeightScaleType="fixed"),                              # its centre
        text("Status.text", [("aipStatus", "=status")], lp=hug(), wrap=False,
             modifiers=[shimmer_group("Status.shimmer"), wipe("Status.wipeIn", HIDDEN), wipe("Status.wipeOut", SHOWN)]),
    ], flexDirectionValue="row", layoutAlignmentType="centerLeft", gapHorizontal=6,
        paddingTop=STATUS_PAD + above("aipStatus"), paddingBottom=STATUS_PAD + below("aipStatus"), **hug())
    chev_art = icon(os.path.join(ICONS, f"{ICON['chevron']}.svg"), "Thought.chev.art", INK2, stroke_w=ICON_STROKE,
                    x=-8, y=-8, size=16)
    thought = box("Thought", [
        text("Thought.text", [("aipStatus", "=thought")], lp=hug(), wrap=False, modifiers=[wipe("Thought.wipe", HIDDEN)]),
        box("Thought.chev", [El("Node", {"x": 8, "y": 8, "rotation": math.pi}, [chev_art], name="Thought.turn")],
            w=16, h=16, opacity=0, layoutWidthScaleType="fixed", layoutHeightScaleType="fixed"),   # open: up
    ], flexDirectionValue="row", layoutAlignmentType="centerLeft", gapHorizontal=6,
        paddingTop=STATUS_PAD + above("aipStatus"), paddingBottom=STATUS_PAD + below("aipStatus"), **hug())
    head = box("Head", [status, thought], layoutTypeValue="stack", layoutAlignmentType="topLeft", **fill_w())
    bar = box("ActionBar", [
        icon_button("LikeBtn", "like", col=INK2, display="none"),
        icon_button("DislikeBtn", "dislike", col=INK2, display="none"),
        icon_button("CopyBtn", "copy", col=INK2),
        icon_button("UndoBtn", "undo", col=INK2, display="none"),
        icon_button("MoreBtn", "options", col=INK2),
    ], flexDirectionValue="row", layoutAlignmentType="centerLeft", gapHorizontal=6, displayValue="none", opacity=0,
        **hug())
    paras = [glide(box(f"Para{i}", [text(f"Para{i}.text", [("aipBody", f"={prop}")], lp=fill_w())],
                       flexDirectionValue="column", layoutAlignmentType="topLeft", paddingTop=above("aipBody"),
                       paddingBottom=below("aipBody"), displayValue="none", opacity=0, **fill_w()))
             for i, prop in enumerate(REPLIES, 1)]
    bubble = box("Bubble", [text("Bubble.text", [("aipBubble", "=prompt")], lp=hug())],
                 paints=[solid("Bubble.fill", SOFT)], cornerRadiusTL=8, cornerRadiusTR=8, cornerRadiusBR=0,
                 cornerRadiusBL=8, linkCornerRadius=False, paddingTop=8 + above("aipBubble"),
                 paddingBottom=8 + below("aipBubble"), paddingLeft=12, paddingRight=12, **hug())
    return box("Messages", [
        box("UserRow", [bubble], flexDirectionValue="column", layoutAlignmentType="topRight", paddingLeft=40,
            **fill_w()),
        box("Output", [head] + paras + [bar], flexDirectionValue="column", layoutAlignmentType="topLeft",
            gapVertical=12, **fill_w()),
    ], flexDirectionValue="column", layoutAlignmentType="topLeft", gapVertical=24, paddingTop=40, paddingBottom=24,
        paddingLeft=24, paddingRight=24, displayValue="none", **fill_w())


def body():
    """The conversation keeps its latest message in view, as the product scrolls to the bottom: the body packs to
    the bottom, and a spacer after the page takes the room left (a short page still starts at the top)."""
    return box("Body", [empty_state(), messages(), box("BodyRest", w=1, h=0, layoutWidthScaleType="fixed",
                                                         layoutHeightScaleType="fill")],
               clip=True, flexDirectionValue="column", layoutAlignmentType="bottomLeft", layoutWidthScaleType="fill",
               layoutHeightScaleType="fill")


def input_field():
    """ChatInput. The field is a stack: before sending, the typed text (revealed up to `typed`), its caret and the
    placeholder; after sending, the placeholder again with a caret at its start; in the prototype, a real field."""
    lp_fill = fill_w()
    typed = text("Typed", [("aipInput", "=prompt")], lp=lp_fill, modifiers=[
        El("TextModifierGroup", {"modifyOpacity": True, "invertOpacity": True, "opacity": 0}, [
            El("TextModifierRange", {"typeValue": 1, "modifyFrom": 0, "modifyTo": 100000, "falloffFrom": 0,
                                     "falloffTo": 100000},
               [bind("typed", key("TextModifierRange", "modifyFrom")),
                bind("typed", key("TextModifierRange", "falloffFrom"))], name="Typed.rest")], name="Typed.hide")])

    def caret(name, prop, bound, lp=lp_fill):
        rng = [bind("typed", key("TextModifierRange", "modifyFrom")),
               bind("typed", key("TextModifierRange", "falloffFrom")),
               bind("typed", key("TextModifierRange", "modifyTo"), converter="conv.plus1"),
               bind("typed", key("TextModifierRange", "falloffTo"), converter="conv.plus1")] if bound else []
        return text(name, [("aipCaret", f"={prop}"), ("aipCaret", "|")], lp=lp, wrap=lp is lp_fill, modifiers=[
            El("TextModifierGroup", {"modifyOpacity": True, "opacity": 1}, [
                El("TextModifierRange", {"typeValue": 1, "modifyFrom": 0, "modifyTo": 1, "falloffFrom": 0,
                                         "falloffTo": 1}, rng, name=f"{name}.pick")], name=f"{name}.only")])
    before = box("BeforeSend", [caret("CaretA", "prompt", True), typed,
                                text("PlaceholderA", [("aipPh", "=placeholder")], lp=lp_fill)],
                 layoutTypeValue="stack", layoutAlignmentType="topLeft", **fill_w())
    # a stack inside a stack does not hand its width down, so the after-send layer sits over the area, pinned
    after = absolute("AfterSend", [caret("CaretB", "placeholderAfter", False, lp=hug()),
                                   text("PlaceholderB", [("aipPh", "=placeholderAfter")], lp=hug(), wrap=False)],
                     inset=(16, 12 + above("aipInput"), 16, None), opacity=0, layoutTypeValue="stack",
                     layoutAlignmentType="topLeft")
    st = STYLES["aipInput"]
    field = El("TextInput", {}, [
        El("TextStyle", {"fontSize": st["size"], "lineHeight": st["lh"], "fontAssetId": "@font.duda",
                         "familyName": kit.FONTS["duda"][1], "styleName": "Regular"},
           [El("TextStyleAxis", {"tag": 2003265652, "axisValue": st["weight"]})], name="LiveInput.font"),
        El("TextInputText", {}, [solid("LiveInput.text.fill", st["color"])], name="LiveInput.text"),
        El("TextInputSelection", {}, [solid("LiveInput.selection.fill", SELECT)], name="LiveInput.selection"),
        El("TextInputCursor", {}, [solid("LiveInput.cursor.fill", INK)], name="LiveInput.cursor"),
        El("FocusData", {"canFocus": False}, name="LiveInput.focus"),   # focusable only in the prototype
        El("DataBindContext", {"sourcePathIds": (AIP.ref(), AIP.ref("draft")), "propertyKey": key("TextInput", "text"),
                               "twoWay": True, "sourceToTargetRunsFirst": True}),
    ], name="LiveInput")
    live_ph = absolute("LivePh", [text("LivePhA", [("aipPh", "=placeholder")], lp=hug(), wrap=False),
                                  text("LivePhB", [("aipPh", "=placeholderAfter")],
                                       lp=dict(hug(), displayValue="none"), wrap=False)],
                       inset=(0, 0, None, None), **hug())
    live = box("LiveField", [box("LiveWrap", [field], intrinsicallySizedValue=True, **fill_w()), live_ph],
               flexDirectionValue="column", layoutAlignmentType="topLeft", displayValue="none", **fill_w())
    area = box("InputArea", [after, before, live], flexDirectionValue="column", layoutAlignmentType="topLeft",
               paddingTop=12 + above("aipInput"), paddingBottom=below("aipInput"), paddingLeft=16, paddingRight=16,
               minHeight=INPUT_MIN_H, **fill_w())

    def darken(n):
        """AiButton:hover is brightness(0.9): black at 10 % over the whole button, icon included."""
        return absolute(f"{n}.hover", paints=[solid(f"{n}.hover.fill", argb("#000000", 0.1))], opacity=0,
                        cornerRadiusTL=13)
    send = box("SendBtn", [
        absolute("StopBtn", [darken("StopBtn"),
                             box("StopBtn.square", w=8, h=8, paints=[solid("StopBtn.square.fill", WHITE)],
                                 cornerRadiusTL=1.6, layoutWidthScaleType="fixed", layoutHeightScaleType="fixed")],
                 paints=[solid("StopBtn.fill", ORANGE)], opacity=0, cornerRadiusTL=13, layoutAlignmentType="center"),
        absolute("ActiveWrap", [absolute("SendActive", [darken("SendActive"),
                                                        icon_slot("SendActive.arrow", "arrow_top", col=WHITE)],
                                         paints=[solid("SendActive.fill", ORANGE)], opacity=0, cornerRadiusTL=13,
                                         layoutAlignmentType="center")]),
        icon_slot("SendOff.arrow", "arrow_top", col=WHITE),
    ], w=26, h=26, paints=[solid("SendBtn.fill", OFF)], cornerRadiusTL=13, layoutAlignmentType="center",
        layoutWidthScaleType="fixed", layoutHeightScaleType="fixed")
    tool = box("ToolBtn", [icon_slot("ToolBtn.icon", "cursor"), icon_slot("ToolBtn.chev", "chevron", size=14),
                           hover_bg("ToolBtn")],
               flexDirectionValue="row", layoutAlignmentType="centerLeft", gapHorizontal=4, paddingLeft=4,
               paddingRight=4, h=24, layoutWidthScaleType="hug", layoutHeightScaleType="fixed")
    build_btn = box("BuildBtn", [text("BuildBtn.label", [("aipBuild", "=build")], lp=hug(), wrap=False),
                                 icon_slot("BuildBtn.chev", "chevron", size=14), hover_bg("BuildBtn")],
                    flexDirectionValue="row", layoutAlignmentType="centerLeft", gapHorizontal=4,
                    paddingTop=above("aipBuild"), paddingBottom=below("aipBuild"), **hug())
    toolbar = box("Toolbar", [
        box("LeftTools", [icon_button("PlusBtn", "plus"),
                          box("ToolDividerBox", [divider("ToolDivider", TOOL_DIVIDER_H)], marginLeft=4, marginRight=4,
                              **hug()),
                          tool, icon_button("AtBtn", "at", display="none")],
            flexDirectionValue="row", layoutAlignmentType="centerLeft", gapHorizontal=2, paddingTop=8,
            paddingBottom=12, paddingLeft=12, paddingRight=4, **hug()),
        spacer("ToolSpacer"),
        box("RightTools", [build_btn, divider("BuildDivider", TOOL_DIVIDER_H), icon_button("MicBtn", "mic"), send],
            flexDirectionValue="row", layoutAlignmentType="centerRight", gapHorizontal=8, paddingTop=8,
            paddingBottom=12, paddingLeft=4, paddingRight=12, **hug()),
    ], flexDirectionValue="row", layoutAlignmentType="centerLeft", **fill_w())
    return box("InputBox", [area, toolbar], paints=[line("InputBox.border", LINE)], cornerRadiusTL=8,
               flexDirectionValue="column", layoutAlignmentType="topLeft", **fill_w())


def footer():
    runs = [("aipMini", "=disclaimer"), ("aipMini", " "), ("aipMini", "=link")]
    under = text("LinkLine", [("aipUnder", "=disclaimer"), ("aipUnder", " "), ("aipUnder", "=link")], lp=hug(),
                 wrap=False, modifiers=[
                     El("TextModifierGroup", {"modifyOpacity": True, "opacity": 1}, [
                         El("TextModifierRange", {"modifyFrom": 0, "modifyTo": 1, "falloffFrom": 0, "falloffTo": 1,
                                                  "runId": "@LinkLine.run2"}, name="LinkLine.range")],
                        name="LinkLine.only")])
    return box("Footer", [
        input_field(),
        box("Disclaimer", [text("Disclaimer.text", runs, lp=hug(), wrap=False),
                           absolute("LinkLineBox", [under], inset=(0, above("aipMini"), None, None), **hug())],
            flexDirectionValue="row", layoutAlignmentType="topLeft", paddingTop=above("aipMini"),
            paddingBottom=below("aipMini"), **fill_w()),
    ], flexDirectionValue="column", layoutAlignmentType="topLeft", gapVertical=4, paddingTop=16, paddingLeft=16,
        paddingRight=16, paddingBottom=12, **fill_w())


def panel():
    edge = absolute("Edge", paints=[solid("Edge.fill", LINE)], inset=(0, 0, None, 0), w=1, layoutWidthScaleType="fixed")
    # maxWidth/maxHeight (percent) are what the floating open animates: the box grows from the 20x20 button
    return box("Panel", [edge, header(), body(), footer()], paints=[solid("Panel.fill", WHITE)], clip=True,
               flexDirectionValue="column", layoutAlignmentType="topLeft", paddingLeft=1, layoutWidthScaleType="fill",
               layoutHeightScaleType="fill", maxWidth=100, maxWidthUnitsValue="percent", maxHeight=100,
               maxHeightUnitsValue="percent")


def shadow():
    """Floating: two soft shadows (rgba(24,39,75,.06) 0 5.6 18 -2.25 and rgba(24,39,75,.08) 0 3.4 7.9 -3.4)."""
    def layer(n, a, blur, oy, spread):
        f = El("Fill", {"fillRule": "clockwise"}, [
            El("SolidColor", {"colorValue": argb("#18274B", a)}, name=f"{n}.color"),
            El("Feather", {"strength": blur, "offsetY": oy}, name=f"{n}.feather")], name=f"{n}.fill")
        return absolute(n, paints=[f], inset=(-spread, -spread, -spread, -spread), cornerRadiusTL=8)
    s = absolute("Shadow", [layer("Shadow.a", 0.08, 7.875, 3.375, -3.375), layer("Shadow.b", 0.06, 18, 5.625, -2.25)],
                 opacity=0)
    return absolute("ShadowWrap", [s], origin=(1, 0))   # scales from the top-right, as the reveal


def launcher():
    """Prototype only: once closed, a button in the corner it grows from opens it again."""
    btn = box("Launcher", [icon_slot("Launcher.icon", "ai")], w=32, h=32,
              paints=[solid("Launcher.fill", WHITE), line("Launcher.border", LINE)], cornerRadiusTL=8,
              layoutAlignmentType="center", layoutWidthScaleType="fixed", layoutHeightScaleType="fixed",
              displayValue="none")
    return absolute("LauncherWrap", [btn], inset=(None, 8, 8, None), displayValue="none", **hug())


# ---------------------------------------------------------------- state machine
def ge(v):
    return if_num("stage", "greaterThanOrEqual", v)


def lt(v):
    return if_num("stage", "lessThan", v)


def has(prop, converter=None):
    return if_text(prop, "notEqual", converter=converter)


def blank(prop, converter=None):
    return if_text(prop, "equal", converter=converter)


def copy_to(src, dst, converter=None):
    """dst = src (strings), through the converter (the read context's id tells the action where the value comes from)."""
    ref = f"read.aip.{src}.{dst}"
    return El("ListenerViewModelChange", {"fromViewModelProperty": True, "fromDataBindId": f"@{ref}"}, [
        El("BindablePropertyString", {}, [bind(src, 635, converter=converter, ref=ref), bind(dst, 635, write=True)])])


def two(name, looks, which_off=0, which_on=1):
    off, on = Anim(f"{name} off", 0.1), Anim(f"{name} on", 0.1)
    for t, p, a, b in looks:
        off.hold(t, p, a)
        on.hold(t, p, b)
    return off, on


def variant_layer():
    looks = [("art.aipanel", "clip", True, False), ("Panel.style", "cornerRadiusTL", 0, 8),
             ("Panel.style", "paddingLeft", 1, 0), ("Shadow", "opacity", 0, 1),
             ("Edge.style", "displayValue", "flex", "none"), ("FloatBtn.style", "displayValue", "none", "flex"),
             ("ToolBtn.style", "displayValue", "flex", "none"), ("AtBtn.style", "displayValue", "none", "flex"),
             ("BuildBtn.style", "displayValue", "flex", "none"), ("BuildDivider.style", "displayValue", "flex", "none"),
             ("MicBtn.style", "displayValue", "flex", "none")]
    vibe, cop = two("Variant", looks)
    lay = Layer("Variant")
    return (lay.state("docked", vibe, lay.go("floating", if_bool("copilot", True)), entry=True)
            .state("floating", cop, lay.go("docked", if_bool("copilot", False)))
            .enter_if("floating", if_bool("copilot", True)))


def actions_layer():
    """figmaActions: the Figma's action bar (like, dislike, copy, undo, more) instead of the product's (copy, more)."""
    looks = [(f"{b}.style", "displayValue", "none", "flex") for b in ("LikeBtn", "DislikeBtn", "UndoBtn")]
    product, figma = two("Action bar", looks)
    lay = Layer("Action bar")
    return (lay.state("product", product, lay.go("figma", if_bool("figmaActions", True)), entry=True)
            .state("figma", figma, lay.go("product", if_bool("figmaActions", False))))


SLIDE = 420          # docked: how far right the panel sits when closed (its 406 px and a margin)
REVEAL_FROM = (20 / FLOATED_W, 20 / DEFAULT_H)   # floating: the 20x20 Copilot button it grows from (fraction)
STAGGERED = ["Greeting", "Subtitle", "Chip1", "Chip2", "Chip3", "Chip4", "ShowMore", "Messages"]


def stagger(a):
    first, step = STAGGER
    for i, n in enumerate(STAGGERED):
        a.move(n, "opacity", first + step * i, first + step * i + OPEN_S, 0, 1, "aip_in_out")
        a.key(n, "opacity", 0, 0)


def grow(a, frm, to, seconds=0.0):
    """Floating: the box's size as a fraction of the panel's (top-right anchored), the shadow scaled along."""
    for i, axis in enumerate("XY"):
        prop = ("maxWidth", "maxHeight")[i]
        if seconds:
            a.move("Panel.style", prop, 0, seconds, frm[i] * 100, to[i] * 100, "aip_panel")
            a.move("ShadowWrap", f"scale{axis}", 0, seconds, frm[i], to[i], "aip_panel")
        else:
            a.hold("Panel.style", prop, to[i] * 100).hold("ShadowWrap", f"scale{axis}", to[i])


def panel_pose(a, x=0, op=1, reveal=1, shadow_op=1, closed=False):
    a.hold("Panel", "x", x).hold("Panel", "opacity", op).hold("ShadowWrap", "opacity", shadow_op)
    a.hold("Launcher.style", "displayValue", "flex" if closed else "none")
    size = (1, 1) if reveal == 1 else REVEAL_FROM
    grow(a, size, size)


def panel_layer():
    """Open and close follow `hidden` (the open / close triggers set it)."""
    end = STAGGER[0] + STAGGER[1] * (len(STAGGERED) - 1) + OPEN_S
    shown = Anim("Panel shown", 0.1)
    panel_pose(shown)
    for n in STAGGERED:
        shown.hold(n, "opacity", 1)
    open_d = Anim("Panel open (docked)", end)
    panel_pose(open_d)
    open_d.move("Panel", "x", 0, OPEN_S, SLIDE, 0, "aip_panel")
    stagger(open_d)
    open_f = Anim("Panel open (floating)", end)
    panel_pose(open_f)
    open_f.move("Panel", "opacity", 0, OPEN_S, 0, 1, "aip_in_out").move("ShadowWrap", "opacity", 0, OPEN_S, 0, 1,
                                                                        "aip_in_out")
    grow(open_f, REVEAL_FROM, (1, 1), OPEN_S)
    stagger(open_f)
    close_d = Anim("Panel close (docked)", OPEN_S)
    panel_pose(close_d)
    close_d.move("Panel", "x", 0, OPEN_S, 0, SLIDE, "aip_panel")
    close_d.key("Launcher.style", "displayValue", OPEN_S, "flex")
    hidden_d = Anim("Panel hidden (docked)", 0.1)
    panel_pose(hidden_d, x=SLIDE, closed=True)
    close_f = Anim("Panel close (floating)", OPEN_S)
    panel_pose(close_f)
    close_f.move("Panel", "opacity", 0, OPEN_S, 1, 0, "aip_panel_out").move("ShadowWrap", "opacity", 0, OPEN_S, 1, 0,
                                                                            "aip_panel_out")
    grow(close_f, (1, 1), REVEAL_FROM, OPEN_S)
    close_f.key("Launcher.style", "displayValue", OPEN_S, "flex")
    hidden_f = Anim("Panel hidden (floating)", 0.1)
    panel_pose(hidden_f, op=0, reveal=0, shadow_op=0, closed=True)

    lay = Layer("Open close")
    hid, opened = (lambda: if_bool("hidden", True)), (lambda: if_bool("hidden", False))
    docked, floating = (lambda: if_bool("copilot", False)), (lambda: if_bool("copilot", True))
    lay.state("shown", shown, lay.go("closeDocked", hid(), docked()), lay.go("closeFloating", hid(), floating()),
              entry=True)
    lay.state("openDocked", open_d, lay.go("shown", at_end=True), lay.go("closeDocked", hid()))
    lay.state("openFloating", open_f, lay.go("shown", at_end=True), lay.go("closeFloating", hid()))
    lay.state("closeDocked", close_d, lay.go("hiddenDocked", at_end=True), lay.go("openDocked", opened()))
    lay.state("hiddenDocked", hidden_d, lay.go("openDocked", opened(), docked()),
              lay.go("hiddenFloating", floating()))
    lay.state("closeFloating", close_f, lay.go("hiddenFloating", at_end=True), lay.go("openFloating", opened()))
    lay.state("hiddenFloating", hidden_f, lay.go("openFloating", opened(), floating()),
              lay.go("hiddenDocked", docked()))
    lay.enter_if("hiddenFloating", hid(), floating())
    lay.enter_if("hiddenDocked", hid(), docked())
    return lay


FLOW = {  # (target, prop): (idle, waiting for the reply, done)
    ("Empty.style", "displayValue"): ("flex", "none", "none"),
    ("Messages.style", "displayValue"): ("none", "flex", "flex"),
    ("Bubble", "opacity"): (0, 1, 1),
    ("BeforeSend", "opacity"): (1, 0, 0),
    ("AfterSend", "opacity"): (0, 1, 1),
    ("StopBtn", "opacity"): (0, 1, 0),
    ("ActiveWrap", "opacity"): (1, 0, 1),    # done: orange again once a follow-up is typed (Input layer)
    ("LivePhA.lp", "displayValue"): ("flex", "none", "none"),
    ("LivePhB.lp", "displayValue"): ("none", "flex", "flex"),
    ("ActionBar.style", "displayValue"): ("none", "none", "flex"),
    ("ActionBar", "opacity"): (0, 0, 1),
}


def flow_pose(a, which, t=0.0):
    i = {"idle": 0, "wait": 1, "done": 2}[which]
    for (tg, p), vals in FLOW.items():
        a.key(tg, p, t, vals[i])


def shimmer(a, t0, t1):
    """The band's centre runs from a quarter-width before the text to a quarter after it, every 1.6 s."""
    t = t0
    while t < t1 - 1e-6:
        seg = min(SHIMMER_S, t1 - t)
        a.move("Status.shimmer.band", "offset", t, t + seg, -0.25, -0.25 + 1.5 * seg / SHIMMER_S)
        t += seg


def flow_layer():
    """idle -> send -> thinking (the paragraphs come in meanwhile, their own layers) -> finish -> done, by `stage`."""
    idle = Anim("Flow idle", 0.1)
    flow_pose(idle, "idle")
    sending = Anim("Flow send", LABEL_AT)   # the shimmer starts as "Thinking..." wipes in (the Head layer)
    flow_pose(sending, "wait")
    sending.move("Bubble", "opacity", 0, 0.12, 0, 1, "aip_out")
    sending.hold("Status.shimmer.band", "offset", -2)
    thinking = Anim("Flow thinking", SHIMMER_S, loop=True)
    flow_pose(thinking, "wait")
    shimmer(thinking, 0, SHIMMER_S)
    # the action bar comes in under the reply ("Thought for 3s" stays at the top)
    finish = Anim("Flow finish", 0.25)
    flow_pose(finish, "wait")
    finish.key("StopBtn", "opacity", 0, 0).key("ActiveWrap", "opacity", 0, 1)
    finish.key("ActionBar.style", "displayValue", 0, "flex")
    finish.move("ActionBar", "opacity", 0, 0.15, 0, 1, "aip_out")
    done = Anim("Flow done", 0.1)
    flow_pose(done, "done")
    lay = Layer("Flow")
    lay.state("idle", idle, lay.go("send", ge(1)), entry=True)
    lay.state("send", sending, lay.go("thinking", at_end=True), lay.go("idle", lt(1)))
    lay.state("thinking", thinking, lay.go("finish", ge(5)), lay.go("idle", lt(1)))
    lay.state("finish", finish, lay.go("done", at_end=True), lay.go("idle", lt(1)), lay.go("send", lt(5)))
    lay.state("done", done, lay.go("idle", lt(1)), lay.go("send", lt(5)))   # a follow-up: stage back to 1
    lay.enter_if("done", ge(5))
    lay.enter_if("thinking", ge(1))
    return lay


def paragraph_layer(i, prop):
    """Paragraph i comes in at stage i + 1, after the status swap's lead (SWAP_LEAD): its room opens below the one
    before (ROOM_S), then the text rises 4 px and fades in. An empty paragraph stays out."""
    n = f"Para{i}"
    off = Anim(f"Paragraph {i} off", 0.1)
    off.hold(f"{n}.style", "displayValue", "none").hold(n, "opacity", 0).hold(n, "y", 4)
    t0, t1 = SWAP_LEAD + PARA_IN[0], SWAP_LEAD + sum(PARA_IN)
    arrive = Anim(f"Paragraph {i} in", t1)
    arrive.hold(f"{n}.style", "displayValue", "flex")
    arrive.key(n, "opacity", 0, 0).move(n, "opacity", t0, t1, 0, 1, "duda")
    arrive.key(n, "y", 0, 4).move(n, "y", t0, t1, 4, 0, "settle")
    on = Anim(f"Paragraph {i} on", 0.1)
    on.hold(f"{n}.style", "displayValue", "flex").hold(n, "opacity", 1).hold(n, "y", 0)
    lay = Layer(f"Paragraph {i}")
    lay.state("off", off, lay.go("in", ge(i + 1), has(prop)), entry=True)
    lay.state("in", arrive, lay.go("on", at_end=True), lay.go("off", lt(i + 1)), lay.go("off", blank(prop)))
    lay.state("on", on, lay.go("off", lt(i + 1)), lay.go("off", blank(prop)))
    lay.enter_if("on", ge(i + 1), has(prop))
    return lay


def head_layer():
    """v08, Mateus's copilot motion (hero-view v10, his hp_section_3), as the AiProcessIndication: sent (stage 1), the
    star turns in under the bubble (5 frames later: from 60 degrees and 8 px lower, in 35 frames) and "Thinking..."
    wipes in (15 frames later); the reply (stage 2) swaps it in place: the star fades (6 frames) and "Thinking..."
    wipes out, `thought` wipes in 10 frames later, its chevron 24 frames later."""
    turn = "Status.turn"
    ins = [(turn, "rotation", math.radians(60), 0.0), (turn, "y", 16.0, 8.0), (turn, "opacity", 0.0, 1.0)] + \
        wipe_looks("Status.wipeIn", HIDDEN, SHOWN)
    dones = [("Status.star", "opacity", 1.0, 0.0), ("Thought.chev", "opacity", 0.0, 1.0)] + \
        wipe_looks("Status.wipeOut", SHOWN, GONE) + wipe_looks("Thought.wipe", HIDDEN, SHOWN)

    def still(name, i, d):
        a = Anim(name, 0.1)
        for tg, p, *v in ins:
            a.hold(tg, p, v[i])
        for tg, p, *v in dones:
            a.hold(tg, p, v[d])
        return a
    entering = Anim("Head in", STAR_AT + TURN)
    for tg, p, *v in dones:
        entering.hold(tg, p, v[0])
    entering.move(turn, "rotation", STAR_AT, STAR_AT + TURN, math.radians(60), 0.0, "aip_turn")
    entering.move(turn, "y", STAR_AT, STAR_AT + TURN, 16.0, 8.0, "aip_turn")
    entering.move(turn, "opacity", STAR_AT, STAR_AT + STAR_FADE, 0.0, 1.0)
    wipe_in(entering, LABEL_AT, "Status.wipeIn")
    swap = Anim("Head swap", CHEV_AT + CHEV_FADE + 1 / FPS)
    for tg, p, *v in ins:
        swap.hold(tg, p, v[1])
    swap.move("Status.star", "opacity", 0, OUT_FADE, 1.0, 0.0)
    wipe_out(swap, 0, "Status.wipeOut")
    wipe_in(swap, THOUGHT_AT, "Thought.wipe")
    swap.move("Thought.chev", "opacity", CHEV_AT, CHEV_AT + CHEV_FADE, 0.0, 1.0)
    lay = Layer("Head")
    lay.state("off", still("Head off", 0, 0), lay.go("in", ge(1)), entry=True)
    lay.state("in", entering, lay.go("thinking", at_end=True), lay.go("swap", ge(2)), lay.go("off", lt(1)))
    lay.state("thinking", still("Head thinking", 1, 0), lay.go("swap", ge(2)), lay.go("off", lt(1)))
    lay.state("swap", swap, lay.go("thought", at_end=True), lay.go("off", lt(1)), lay.go("in", lt(2)))
    lay.state("thought", still("Head thought", 1, 1), lay.go("off", lt(1)), lay.go("in", lt(2)))
    lay.enter_if("thought", ge(2))
    lay.enter_if("thinking", ge(1))
    return lay


def title_layer():
    """The chat is renamed (title -> titleAfter): floating 1.1 s after sending, while it still thinks; docked with the
    action bar. Only the first message renames it: a follow-up keeps the new name."""
    def pose(name, after, seconds=0.1):
        a = Anim(name, seconds)
        a.hold("TitleA.lp", "displayValue", "none" if after else "flex")
        a.hold("TitleB.lp", "displayValue", "flex" if after else "none")
        return a
    lay = Layer("Title")
    lay.state("a", pose("Title a", False), lay.go("sent", ge(1)), entry=True)
    lay.state("sent", pose("Title sent", False, TITLE_COPILOT_S), lay.go("b", if_bool("copilot", True), at_end=True),
              lay.go("b", ge(5)), lay.go("a", lt(1)))
    lay.state("b", pose("Title b", True), lay.go("a", lt(1)))
    lay.enter_if("b", ge(5))
    return lay


TYPED_ON = 0.5   # `typed` from which the first character shows


def input_layer():
    """The placeholder and the orange send button: typing once `typed` has text before sending, or `draft` (the real
    field) has text."""
    looks = [("PlaceholderA", "opacity", 1, 0), ("LivePh", "opacity", 1, 0), ("SendActive", "opacity", 0, 1)]
    empty, typing = two("Input", looks)
    trim = "conv.trim"
    lay = Layer("Input")
    lay.state("empty", empty, lay.go("typing", if_num("typed", "greaterThanOrEqual", TYPED_ON), lt(1)),
              lay.go("typing", has("draft", trim)), entry=True)
    lay.state("typing", typing, lay.go("empty", ge(1), blank("draft", trim)),
              lay.go("empty", if_num("typed", "lessThan", TYPED_ON), blank("draft", trim)))
    return lay


def focus_layer():
    off, solid_, blink = Anim("Focus off", 0.1), Anim("Focus typing", 0.1), Anim("Focus caret blink", BLINK_S, True)
    for a, border, caret in ((off, LINE, 0), (solid_, LINE_FOCUS, 1), (blink, LINE_FOCUS, 1)):
        a.hold("InputBox.border.color", "colorValue", border)
        a.hold("CaretA", "opacity", caret).hold("CaretB", "opacity", caret)
    blink.key("CaretA", "opacity", BLINK_S / 2, 0).key("CaretB", "opacity", BLINK_S / 2, 0)
    lay = Layer("Focus")
    lay.state("off", off, lay.go("blink", if_bool("focused", True), if_num("typed", "lessThan", TYPED_ON)),
              lay.go("typing", if_bool("focused", True), if_num("typed", "greaterThanOrEqual", TYPED_ON)), entry=True)
    lay.state("blink", blink, lay.go("typing", if_num("typed", "greaterThanOrEqual", TYPED_ON)),
              lay.go("off", if_bool("focused", False)))
    lay.state("typing", solid_, lay.go("blink", if_num("typed", "lessThan", TYPED_ON)),
              lay.go("off", if_bool("focused", False)))
    return lay


def commands_layer(tick):
    """The triggers set the values every other layer follows: open / close -> hidden, send -> stage 1,
    reset -> stage 0 and an empty field."""
    lay = Layer("Commands")
    cmds = {"open": [set_to("Boolean", "hidden", False)], "close": [set_to("Boolean", "hidden", True)],
            "send": [set_to("Number", "stage", 1)],
            "reset": [set_to("Number", "stage", 0), set_to("String", "draft", "")]}
    lay.state("ready", None, *[lay.go(c, if_trigger(c)) for c in cmds], entry=True)
    for c, acts in cmds.items():
        lay.state(c, tick, lay.go("ready", at_end=True), actions=acts)
    return lay


def respond_layer(tick):
    """respond: each paragraph at its stage, STEP_S apart (the empty ones skipped); THEN_S after the last one is in,
    stage 5."""
    step, then = Anim("Respond step", STEP_S), Anim("Respond then", SWAP_LEAD + sum(PARA_IN) + THEN_S)
    lay = Layer("Respond")
    lay.state("ready", None, lay.go("p1", if_trigger("respond")), entry=True)
    lay.state("p1", step, lay.go("p2", has("reply2"), at_end=True), lay.go("hold", blank("reply2"), at_end=True),
              actions=[set_to("Number", "stage", 2)])
    lay.state("p2", step, lay.go("p3", has("reply3"), at_end=True), lay.go("hold", blank("reply3"), at_end=True),
              actions=[set_to("Number", "stage", 3)])
    lay.state("p3", tick, lay.go("hold", at_end=True), actions=[set_to("Number", "stage", 4)])
    lay.state("hold", then, lay.go("done", at_end=True))
    lay.state("done", tick, lay.go("ready", at_end=True), actions=[set_to("Number", "stage", 5)])
    return lay.from_any(lay.go("ready", if_trigger("reset")))


def prototype_layer():
    """`interactive`: the real field (focusable) and the reopen button, in place of the animated typing."""
    looks = [("BeforeSend.style", "displayValue", "flex", "none"), ("AfterSend.style", "displayValue", "flex", "none"),
             ("LiveField.style", "displayValue", "none", "flex"), ("LauncherWrap.style", "displayValue", "none", "flex"),
             ("LiveInput.focus", "canFocus", False, True)]
    off, on = two("Prototype", looks)
    lay = Layer("Interactive")
    return (lay.state("off", off, lay.go("on", if_bool("interactive", True)), entry=True)
            .state("on", on, lay.go("off", if_bool("interactive", False))))


def clicks_layer():
    """Prototype: what a click or Enter asks for (the `_` triggers), only while `interactive` is on. Sending copies the
    field into `prompt`, empties it and fires `send`; THINK_S later the reply comes by itself (`respond`). Nothing is
    taken while the reply is on its way. A suggestion fills the field and focuses it, as in the product."""
    on = lambda: if_bool("interactive", True)   # noqa: E731
    trim = "conv.trim"
    lay = Layer("Clicks")
    lay.state("ready", None, lay.go("send", if_trigger("_send"), on(), has("draft", trim)),
              lay.go("clear", if_trigger("_send"), on(), blank("draft", trim)),
              *[lay.go(f"chip{i}", if_trigger(f"_chip{i}"), on()) for i in range(1, 5)], entry=True)
    lay.state("send", None, lay.go("thinking"),
              actions=[copy_to("draft", "prompt", trim), set_to("String", "draft", ""), fire("send")])
    lay.state("thinking", Anim("Prototype thinking", THINK_S), lay.go("respond", at_end=True))
    lay.state("respond", None, lay.go("answering"), actions=[fire("respond")])
    lay.state("answering", None, lay.go("ready", ge(5)))
    lay.state("clear", None, lay.go("ready"), actions=[set_to("String", "draft", "")])   # Enter on a blank field
    for i in range(1, 5):
        lay.state(f"chip{i}", None, lay.go("ready"),
                  actions=[copy_to(f"chip{i}", "draft"), El("FocusActionTarget", {"targetId": "@LiveInput"})])
    lay.state("reset", None, lay.go("ready"))
    return lay.from_any(lay.go("reset", if_trigger("reset")))


def doors_layer():
    """Prototype: » closes the panel, the corner button opens it again. Its own layer, so it works mid-reply."""
    on = lambda: if_bool("interactive", True)   # noqa: E731
    lay = Layer("Open clicks")
    return (lay.state("ready", None, lay.go("close", if_trigger("_close"), on()),
                      lay.go("open", if_trigger("_open"), on()), entry=True)
            .state("close", None, lay.go("ready"), actions=[fire("close")])
            .state("open", None, lay.go("ready"), actions=[fire("open")]))


def prototype_listeners():
    """Clicks and Enter only ask (the `_` triggers); the layers decide. The field gets its keys and text while it holds
    focus and reports its focus in `focused`. Pressing the input box focuses the field, pressing the conversation lets
    go of it."""
    def click(target, trig):
        return El("StateMachineListenerSingle", {"targetId": f"@{target}", "listenerTypeValue": "click"},
                  [fire(trig)], name=f"click {target}")

    def on_field(kind, *actions):
        return El("StateMachineListener", {"targetId": "@LiveInput"},
                  [El("ListenerInputType", {"listenerTypeValue": kind})] + list(actions), name=f"field {kind}")
    keys = [El("KeyboardInput", {"keyType": k, "keyPhase": 4}) for k in ("enter", "kpEnter")]
    out = ([click("SendBtn", "_send")] + [click(f"Chip{i}", f"_chip{i}") for i in range(1, 5)] +
            [click("ExpandBtn", "_close"), click("Launcher", "_open"),
             El("StateMachineListener", {"targetId": "@LiveInput"},
                [El("ListenerInputTypeKeyboard", {"listenerTypeValue": "keyboard"}),
                 El("ListenerInputTypeText", {"listenerTypeValue": "textInput"})], name="field keys"),
             on_field("focus", set_to("Boolean", "focused", True)),
             on_field("blur", set_to("Boolean", "focused", False)),
             El("StateMachineListenerSingle", {"targetId": "@InputArea", "listenerTypeValue": "down"},
                [El("FocusActionTarget", {"targetId": "@LiveInput"})], name="press field"),
             El("StateMachineListenerSingle", {"targetId": "@Body", "listenerTypeValue": "down"},
                [El("FocusActionClear", {})], name="press conversation"),
             # Enter sends: the multiline field takes the press (a line break, trimmed when sending); the release
             # reaches the artboard. Shift+Enter is not matched, so it only breaks the line.
             El("StateMachineListener", {"targetId": "@art.aipanel"},
                [El("ListenerInputTypeKeyboard", {"listenerTypeValue": "keyboard"}, keys), fire("_send")],
                name="Enter sends")])
    for e in out:   # names repeat across the library's components: the refs keep them apart
        e.ref = f"aip.{e.name}"
    return out


HOVER_LOOK = {  # hover name: (listener target, [(target, prop, off, on)])
    **{f"Chip{i}": (f"Chip{i}", [(f"Chip{i}.border.color", "colorValue", CLEAR, LINE_FOCUS),
                                 (f"Chip{i}.thumb.hover", "opacity", 0, 1)]) for i in range(1, 5)},
    **{h: (f"{h}Btn", [(f"{h}Btn.hover", "opacity", 0, 1)])
       for h in ("Float", "Options", "Expand", "Plus", "Tool", "At", "Mic", "Like", "Dislike", "Copy", "Undo", "More")},
    "Send": ("SendBtn", [("SendActive.hover", "opacity", 0, 1), ("StopBtn.hover", "opacity", 0, 1)]),
}


def hover_layers():
    layers, listeners = [], []
    for h, (target, looks) in HOVER_LOOK.items():
        name = f"hover{h}"
        off, on = two(name, looks)
        lay = Layer(name)
        layers.append(lay.state("off", off, lay.go("on", if_bool(name, True)), entry=True)
                      .state("on", on, lay.go("off", if_bool(name, False))))
        listeners += hover_listeners(target, name)
    return layers, listeners


# ---------------------------------------------------------------- the component
def _namespace(art, anims):
    """Prefix every element name of the component (not the state machine's) with PREFIX, and the references to them
    (styles, targets, keyed objects): the component sits in one document with the rest of the library."""
    names = set()

    def rename(e):
        if e.tag == "StateMachine":
            return
        if e.name and not e.ref:
            names.add(e.name)
            e.name = PREFIX + e.name
        for c in e.children:
            if isinstance(c, El):
                rename(c)
    for c in art.children:
        if isinstance(c, El):
            rename(c)

    def refs(e):
        for k, v in e.attrs.items():
            if isinstance(v, str) and v.startswith("@") and v[1:] in names:
                e.attrs[k] = "@" + PREFIX + v[1:]
    kit.walk(art, refs)
    for a in anims:
        a.tracks = {((PREFIX + t) if t in names else t, p): v for (t, p), v in a.tracks.items()}


def build():
    use(AIP)
    kit.FONTS.setdefault("under", ("DudaSansUnderline.ttf", "Duda Sans Underline"))
    kit.STYLES.update(STYLES)
    n0 = len(kit.ANIMS)
    tick = kit.tick()
    hl, listeners = hover_layers()
    # the prototype's layers and the commands come first: a trigger they fire, a value they set, is seen by the
    # layers after them in the same frame
    layers = ([prototype_layer(), clicks_layer(), doors_layer(), commands_layer(tick), respond_layer(tick),
               variant_layer(), actions_layer(), panel_layer(), flow_layer()] +
              [paragraph_layer(i, p) for i, p in enumerate(REPLIES, 1)] +
              [head_layer(), title_layer(), input_layer(), focus_layer()] + hl)
    sm = machine(layers, listeners + prototype_listeners())
    art = component("AiPanel", DOCKED_W, DEFAULT_H, [launcher(), panel(), shadow()], sm,
                    layout={"layoutAlignmentType": "topRight"})
    art.attrs["clip"] = True
    _namespace(art, kit.ANIMS[n0:])
    return art
