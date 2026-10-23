"""piece.py: a library piece in a few lines. Place components, lay them out, script the cursor and the states with
ready-made actions, and build: "State Machine 1" with `play` (restart) and, for a hero tab, `tabChange`.
QUICKSTART.md is the whole manual; this file is the implementation.

How it works (the "drivers" pattern): the piece has ONE timeline. The cursor, entrances and reflows are keyed on
elements of the piece; a component's state (hover, pressed, focused, typed, loading, a message...) is keyed on a
driver, a custom property of the piece (`drv.<slot>.<prop>`, card "Drivers" on the artboard) bound into the
component's view model through the piece's view model. Drivers work with autoBind on the web (2.45.0), and the motion
designer sees and edits every state change as a key on the same timeline.

The actions sit on the kit's choreography (tools/choreo.py, tools/cursorpath.py, motion-spec tokens), so the cursor
paths, typing pattern, press timing and the speed limits come from there, and the kit's lints run on every build.
Positions for the cursor come from a measure pass: the CLI lays the scene out and reports every placement's bounds
(semantics), at the state the scene is in at that moment (a removed tag reflows the row).
"""
import copy
import hashlib
import json
import math
import os
import random
import shutil
import subprocess
import sys

import kit
from kit import El
import library
from components.icon_button import IB
from components.core_button import CB
from components.divider import DIV
from components.smart_tag import TAG
from components.core_input import CI, TYPED_ALL, MSG_ROOM
from components.cursor import CURSOR
from components import ai_panel as aip
from components import floating_bar as fb
from components.toggle import TOGGLE
from components.checkbox import CHECKBOX
from components.radio import RADIO
from components.pill_tabs import PILL
from components.search_input import SEARCH
from components.status import STATUS
from components.promo_tag import PROMO
from components.tooltip import TIP
from components.loader import LOADER
from components.icon_thumbnail import THUMB
from components.core_tabs import CTABS
from components.list_item import LI
from components.menu_item import MI
from components.dropdown import DD
from components.ai_process import AIP
from components.text_area import TA
import choreo
from choreo import Choreo, frame, progress
from cursorpath import Visit

from common import (RIVE, TAB_PARTS, FPS, TOK, LEAD, HOVER_LEAD, SWAP, DRIVER, STEP, secs, Item,  # noqa: F401
                    _el, _color, FIT)
from patterns import Patterns, ActionPatterns

PARTS = {"Pill_Tabs": "PillTabs.tab", "Core Tabs": "CoreTabs.tab",   # component -> the parts the measure reports
         "VibeFloatingBar": "VibeFloatingBar.slot.", "AiPanel": aip.PREFIX}
BAR_PARTS = {p for p, _ in fb.PARTS} | {el for el, _ in aip.PARTS.values()}
# keys that never change a layout: the measure pass leaves them out (fewer layouts to measure)
NO_LAYOUT = {"opacity", "scaleX", "scaleY", "distance", "rotation", "offset", "colorValue", "strength", "startX",
             "startY", "endX", "endY", "position", "modifyFrom", "modifyTo", "falloffFrom", "falloffTo"}
DRV_NO_LAYOUT = {"hover", "pressed", "focused", "removeHover", "hoverAnimated", "typed", "shown",   # states, same
                 "stage", "hidden"}


def _probed(comp):
    """For the measure pass: a copy of a component artboard with a semantics marker on each of its parts (a tab, a
    part of the floating bar)."""
    prefix = PARTS.get(comp.name)
    if not prefix:
        return comp
    comp = copy.deepcopy(comp)

    def part(name):
        rest = name[len(prefix):] if name and name.startswith(prefix) else None
        return rest is not None and (rest.isdigit() or rest in BAR_PARTS)
    kit.walk(comp, lambda e: e.children.insert(1, El("SemanticData", {"role": "group", "label": f"part:{e.name}"}))
             if part(e.name) else None)
    return comp


class Piece(Patterns):
    def __init__(self, name="MAIN", w=1340, h=638, bg="#FFFFFF", here=None, cursor_scale=1.0, cursor_shadow=False):
        """One artboard `name` (w x h) with its own view model; bg: a '#rrggbb' or a DS colour token name, None
        (or "transparent"): see-through (the page shows behind the artboard). cursor_shadow: the cursor's soft
        shadow (the storyboards draw it)."""
        self.here = here or os.path.dirname(os.path.abspath(sys.argv[0]))
        self.art, self.w, self.h, self.key = name, w, h, name.lower()
        self.bg = kit.CLEAR if bg in (None, "transparent") else _color(bg)
        self.cursor_scale, self.cursor_shadow = cursor_scale, cursor_shadow
        self.no_layout = set()          # elements whose keys never change a layout (code lines...)
        self.effects = []               # Generation effects: their shapes go over the scene, under the cursors
        kit.FONT_DIR[0] = os.path.relpath(os.path.join(kit.HERE, "fonts"), self.here)
        self.icons, self.comps = library.library()
        self.props, self.items, self.bar_parts = [], {}, {}
        self.root, self.a = None, None
        self.colls = []                 # p.collapsible()s, for their opening height
        self._measured = {}

    # ------------------------------------------------------------ placing components
    def _place(self, slot, kind, vm, comp, values, w="hug", h="hug", origin=None):
        assert slot not in self.items, f"slot {slot!r} is used twice"
        values = {k: kit.icon_ref(v) if vm.kind(k) == "artboard" and v and not v.startswith("art.") else v
                  for k, v in values.items()}
        ref = vm.inst(f"vmi.{vm.key}.{self.key}.{slot}", values, name=f"{self.art} {slot}")
        self.props.append((slot, f"vm:{vm.key}", ref))
        path = (f"vm.{self.key}", f"vm.{self.key}.{slot}")
        nest = kit.nested(f"{self.art}.{slot}.c", comp, path, "fill" if w != "hug" else "hug",
                          "fill" if h != "hug" else "hug")
        size = {}
        for ax, v in (("Width", w), ("Height", h)):
            size[f"layout{ax}ScaleType"] = "fixed" if isinstance(v, (int, float)) else v
        wrap = kit.box(f"{self.art}.{slot}", [nest], w=w if isinstance(w, (int, float)) else 0,
                       h=h if isinstance(h, (int, float)) else 0, origin=origin, marginRight=0, **size)
        item = Item(self, slot, kind, wrap, vm, path, vm.instances[-1])
        self.items[slot] = item
        return item

    def button(self, slot, **props):
        """CoreButton. props: label, variant (0 Primary, 1 Secondary, 2 Text), size, color, showLeftIcon,
        leftIcon ("i_plus"), showRightIcon, rightIcon, minWidth, and any state."""
        return self._place(slot, "button", CB, "cb", props)

    def icon_button(self, slot, **props):
        """Icon button. props: icon ("i_send"), variant (0 Icon, 1 Box), size (0 Small 24, 1 Large 32), color..."""
        return self._place(slot, "ib", IB, "ib", props)

    def input(self, slot, w=320, **props):
        """CoreInput, `w` points wide. props: label, showLabel, placeholder, value, message, showMessage, theme,
        size, and the states (focused, error, success, warning, readOnly, disabled)."""
        return self._place(slot, "input", CI, "ci", props, w=w)

    def tag(self, slot, **props):
        """Smart_Tag. props: label, size (0 Small 20, 1 Regular 26), radius, color (0 Grey, 1 White, 2 Primary),
        prefix, prefixIcon, removeButton, border."""
        return self._place(slot, "tag", TAG, "tag", props, origin=(0.5, 0.5))

    def toggle(self, slot, **props):
        """Core Toggle. props: variant (0 Toggle 28x18, 1 Switch 48x30), on, disabled. a.click flips it."""
        return self._place(slot, "toggle", TOGGLE, "toggle", props)

    def checkbox(self, slot, **props):
        """Core Checkbox (16x16). props: state (0 Empty, 1 On, 2 Partial), disabled. a.click checks / clears it."""
        return self._place(slot, "checkbox", CHECKBOX, "checkbox", props)

    def radio(self, slot, **props):
        """Core Radio Button (18x18). props: selected, disabled. a.click selects it (a.set(other, selected=False)
        for the one it replaces)."""
        return self._place(slot, "radio", RADIO, "radio", props)

    def search(self, slot, w=248, **props):
        """SearchInput, `w` points wide (DS 248). props: placeholder ("Search by"), value, focused, disabled.
        a.type_into(search, "...") types into it (it clicks it first)."""
        return self._place(slot, "search", SEARCH, "search", props, w=w)

    def status(self, slot, **props):
        """Status. props: label, color (0 Neutral, 1 Positive, 2 Pending, 3 Dark Grey, 4 Yellow, 5 Negative, 6 Blue,
        7 Purple), border, dropdown (the chevron, on by default), unread (the orange dot), hover."""
        return self._place(slot, "status", STATUS, "status", props, origin=(0.5, 0.5))

    def promo(self, slot, **props):
        """Promotional Tag. props: type (0 Default: the text in an orange outline, 1 Premium, 2 AI, 3 New dot),
        label ("new")."""
        return self._place(slot, "promo", PROMO, "promo", props, origin=(0.5, 0.5))

    def tooltip(self, slot, **props):
        """Tooltip. props: text, hug (one line; default: wraps at 200), shown (True; place it with shown=False and
        a.set(tip, shown=True) to bring it in)."""
        return self._place(slot, "tooltip", TIP, "tip", props)

    def loader(self, slot, **props):
        """Loader (it always turns). props: size (0 16, 1 24, 2 48, 3 96)."""
        return self._place(slot, "loader", LOADER, "loader", props)

    def dropdown(self, slot, w=240, **props):
        """CoreDropdown (Type Text), `w` points wide. props: label, showLabel, value, placeholder ("Select"), prefix,
        prefixIcon, open, disabled, error. a.click opens / closes it (the chevron turns); its menu is a p.menu()."""
        return self._place(slot, "dropdown", DD, "dd", props, w=w)

    def ai_status(self, slot, **props):
        """AiProcessIndication: the AI's status line. props: label ("Thinking..."), done (still, a chevron after it),
        spinner (a turning arc instead of the AI icon), chevron (False: done shows no chevron). While not done, the
        label shimmers on its own."""
        return self._place(slot, "aistatus", AIP, "aip", props)

    def text_area(self, slot, w=358, h=126, **props):
        """Text Area: a field of several lines under its label, w x h points (the label takes 26 of h). props: label,
        showLabel, required, labelIcon, placeholder, value, resize (the corner handle), focused, disabled, readOnly.
        a.type_into(area, "...") types into it (the lines wrap at the field's width)."""
        return self._place(slot, "textarea", TA, "ta", props, w=w, h=h)

    def core_tabs(self, slot, **props):
        """Core Tabs (labels with a 2 px line under the selected one, a divider under the row). props: count (2..6),
        selected (0 = the first tab), label1..label6. Its tabs are targets: tabs.tab(i)."""
        return self._place(slot, "coretabs", CTABS, "ctabs", props)

    def thumb(self, slot, **props):
        """Icon Thumbnail. props: icon ("i_site"), theme (0 Primary, 1 Secondary, 2 Grey, 3 Highlight, 4 Display,
        5 Error, 6 Warning), size (0 40, 1 36, 2 24, 3 16), circle, disabled."""
        return self._place(slot, "thumb", THUMB, "thumb", props)

    def list_item(self, slot, w=419, **props):
        """ListItem, `w` points wide. props: title, secondary, showSecondary, prefix, prefixIcon, prefixTheme,
        suffix, suffixIcon ("i_options"), tag, tagLabel, border, state (0 Default, 1 Default_Grey, 2 Selected - border,
        3 Selected - grey, 4 Selected - primary, 5 Error, 6 Disabled), hover (the cursor hovers it on its own)."""
        return self._place(slot, "listitem", LI, "li", props, w=w)

    def pill_tabs(self, slot, w="hug", **props):
        """Pill_Tabs. props: count (2..6), selected (0 = the first tab), label1..label6, fill (the tabs share `w`
        points), icons, icon1..icon6. Its tabs are targets: tabs.tab(i)."""
        if props.get("fill"):
            assert isinstance(w, (int, float)), "fill=True needs a width (w=...)"
        return self._place(slot, "pills", PILL, "pill", props, w=w)

    def divider(self, slot, w=240, **props):
        """Divider: variant 0 With text (label), 1 No text, 2 Vertical (give h instead of w). A horizontal one sits
        in an 18 pt row; h=1 makes the row just the line (No text), for lists and panels."""
        vertical = props.get("variant") == 2
        return self._place(slot, "divider", DIV, "div", props, w=1 if vertical else w,
                           h=props.pop("h", 24) if vertical else props.pop("h", 18))

    def bar(self, slot, style="ds", **props):
        """VibeFloatingBar (open, and per part: over={"trash": {"hover": True}}). Its parts are targets:
        bar.part("trash"). style "ds": the DS / product bar (Edit, up, down, duplicate, padding, trash, close);
        "storyboard": the Vibe page storyboards' bar ("Edit Design", left, right, ..., a menu in place of close)."""
        assert slot not in self.items
        assert style in ("ds", "storyboard"), style
        over = props.pop("over", None) or {}
        if style == "storyboard":
            over = {p: dict(fb.STORYBOARD.get(p, {}), **over.get(p, {})) for p in set(fb.STORYBOARD) | set(over)}
        ref = fb.instance(f"vmi.bar.{self.key}.{slot}", f"{self.art} {slot}", False, over, **props)
        self.props.append((slot, "vm:bar", ref))
        path = (f"vm.{self.key}", f"vm.{self.key}.{slot}")
        nest = kit.nested(f"{self.art}.{slot}.c", "bar", path, "hug", "hug")
        wrap = kit.box(f"{self.art}.{slot}", [nest], marginRight=0, **kit.hug())
        inst = fb.BAR.instances[-1]
        self.bar_parts[slot] = {p: next(i for i in vm.instances if i[1] == f"{ref}.parts.{p}") for p, vm in fb.PARTS}
        item = Item(self, slot, "bar", wrap, fb.BAR, path, inst)
        self.items[slot] = item
        return item

    # ------------------------------------------------------------ text and layout
    def text(self, name, string, style="Headlines/He 1", color="Typography/primary-text-color", w=None, font=None,
             size=None, lh=None, weight=None, ls=None, align=None):
        """Text in a DS text style and colour (a token name or '#rrggbb'). One line by default (its box is exactly
        its line height); w=points: a paragraph that wraps at that width ("fill": at its parent's width;
        align: left, center, right).
        A client's typeface: p.font(...) first, then font=, size=, lh= (and style=None)."""
        k = f"{self.key}_{name}"
        kit.text_style(k, style, _color(color), font=font, size=size, lh=lh, weight=weight, ls=ls)
        if w is None:
            t = kit.text(f"{self.art}.{name}.t", [(k, string)], lp=kit.hug(), wrap=False)
            wrap = kit.box(f"{self.art}.{name}", [t], h=kit.STYLES[k]["lh"], layoutWidthScaleType="hug",
                           layoutHeightScaleType="fixed", flexDirectionValue="row", layoutAlignmentType="centerLeft")
        else:
            t = kit.text(f"{self.art}.{name}.t", [(k, string)], lp=kit.fill_w(), wrap=True, align=align)
            size = {"layoutWidthScaleType": "fill"} if w == "fill" else {"w": w, "layoutWidthScaleType": "fixed"}
            wrap = kit.box(f"{self.art}.{name}", [t], layoutHeightScaleType="hug", flexDirectionValue="column",
                           layoutAlignmentType="topLeft", **size)
        item = Item(self, name, "text", wrap)
        self.items[name] = item
        return item

    def font(self, key, file, family):
        """A client's typeface (a .ttf / .otf in the piece folder; one file per weight): p.text(..., font=key).
        The keys "duda", "caret" and "mono" are the library's own."""
        assert key not in ("duda", "caret", "mono"), f"font key {key!r} is the library's own: pick another"
        kit.own_font(key, os.path.join(self.here, file), family)
        return key

    def image(self, name, file, w, h, fit="cover", radius=0, align=(0.5, 0.5)):
        """A photo or screenshot (a file in the piece folder) in a w x h box: fit "cover" fills it and crops (Figma's
        Fill), "contain" fits it whole (Fit), "fill" stretches. radius: rounded corners (it clips)."""
        k = f"{self.key}_{name}"
        kit.image_asset(k, os.path.join(self.here, file))
        img = El("Image", {"assetId": f"@img.{k}", "fit": FIT[fit], "alignmentX": align[0] * 2 - 1,
                           "alignmentY": align[1] * 2 - 1}, name=f"{self.art}.{name}.img")
        wrap = kit.box(f"{self.art}.{name}", [img], w=w, h=h, clip=True, layoutWidthScaleType="fixed",
                       layoutHeightScaleType="fixed", marginRight=0, cornerRadiusTL=radius or None)
        item = Item(self, name, "image", wrap)
        self.items[name] = item
        return item

    def wrap(self, name, els, w="hug", h="hug"):
        """Your own drawing (kit or tools/rml.py elements: shapes, paths, gradients) as a placed item, so the
        actions can target it (enter, exit, a.key, the cursor). w / h: "hug", "fill" or points."""
        els = els if isinstance(els, (list, tuple)) else [els]
        return self._box(name, els, "column", 0, 0, "topLeft", w, h, origin=(0.5, 0.5))   # presses scale from the centre

    def free(self, name, kids, w, h, clip=True, radius=0):
        """A w x h box where each child sits where Figma has it: kids = [(item, x, y)] or (item, x, y, scale),
        back to front (the first one is the background).
        Children may overflow the box (clip=False shows it). `scale` shrinks or grows a child from its top-left
        corner (the product UI at 0.73 in a storyboard): the cursor aims at the scaled child. radius: round corners
        on the box, its clip included (a window: what is inside, library parts too, is cut round)."""
        boxes = []
        for i, kid in enumerate(kids):
            it, x, y = kid[:3]
            s = kid[3] if len(kid) > 3 else 1.0
            el = _el(it)
            if s != 1.0:
                el.attrs["scaleX"] = el.attrs["scaleY"] = s
            boxes.append(kit.absolute(f"{self.art}.{name}.at{i}", [el], inset=(x, y, None, None), origin=None,
                                      layoutWidthScaleType="hug", layoutHeightScaleType="hug"))
        # kids go back to front, as you list layers bottom-up; in Rive the first child draws on top
        return self._box(name, boxes[::-1], "column", 0, 0, "topLeft", w, h, clip=clip, cornerRadiusTL=radius or None)

    def _box(self, name, kids, direction, gap, pad, align, w, h, paints=(), **st):
        size = {"layoutWidthScaleType": "fixed" if isinstance(w, (int, float)) else w,
                "layoutHeightScaleType": "fixed" if isinstance(h, (int, float)) else h}
        g = {"gapVertical": gap} if direction == "column" else {"gapHorizontal": gap}
        pads = pad if isinstance(pad, (tuple, list)) else (pad,) * 4     # left, top, right, bottom
        box = kit.box(f"{self.art}.{name}", [_el(k) for k in kids], w=w if isinstance(w, (int, float)) else 0,
                      h=h if isinstance(h, (int, float)) else 0, paints=paints, flexDirectionValue=direction,
                      layoutAlignmentType=align, paddingLeft=pads[0], paddingTop=pads[1], paddingRight=pads[2],
                      paddingBottom=pads[3], marginRight=0, **g, **size, **st)
        item = Item(self, name, "box", box)
        self.items[name] = item
        return item

    def column(self, name, kids, gap=16, pad=0, align="topLeft", w="hug", h="hug"):
        """A vertical stack. align: topLeft, topCenter, center, centerLeft...; w / h: "hug", "fill" or points."""
        return self._box(name, kids, "column", gap, pad, align, w, h)

    def row(self, name, kids, gap=8, pad=0, align="centerLeft", w="hug", h="hug"):
        return self._box(name, kids, "row", gap, pad, align, w, h)

    def card(self, name, kids, w=380, pad=24, gap=16, align="topLeft", shadow="shadow-1", border=True,
             fill="Backgrounds/bg-white-color", radius="border-radius-m", h="hug", title=None, action=None):
        """A DS card: white, radius 8, 1 px border-light edge, shadow-1 (DS "Cards"). `kids` stack in a column.
        shadow: "shadow-1".."shadow-5" or None; border: False drops the edge; fill: a token or '#rrggbb';
        radius: a DS radius name or points; w: points or "hug"; h: "hug" or points.
        title: the DS card header (Bold 16/22) on top; action: a text button at its right ("See all", with a
        chevron), a target as card.action."""
        action_btn = None
        if title is not None:
            gap_el = kit.box(f"{self.art}.{name}.headGap", h=1, layoutWidthScaleType="fill",
                             layoutHeightScaleType="fixed")
            head = [self.text(f"{name}Title", title, style="Headlines/He 1"), gap_el]
            if action:
                action_btn = self.button(f"{name}Action", label=action, variant=2, size=0, color=1, showRightIcon=True,
                                         rightIcon="chevron_right")
                head.append(action_btn)
            kids = [self.row(f"{name}Head", head, gap=8, w="fill")] + list(kids)
        r = kit.radius(radius) if isinstance(radius, str) else radius
        n = f"{self.art}.{name}"
        edge = [kit.absolute(f"{n}.edge", paints=[kit.line(f"{n}.edge.s", kit.color("Borders/border-light-color"))],
                             inset=(0.5,) * 4, cornerRadiusTL=r - 0.5)] if border else []
        pads = pad if isinstance(pad, (tuple, list)) else (pad,) * 4
        inner = kit.box(f"{n}.body", edge + [_el(k) for k in kids], w=w if isinstance(w, (int, float)) else 0,
                        h=h if isinstance(h, (int, float)) else 0, paints=[kit.solid(f"{n}.fill", _color(fill))],
                        flexDirectionValue="column", layoutAlignmentType=align, gapVertical=gap,
                        paddingLeft=pads[0], paddingTop=pads[1], paddingRight=pads[2], paddingBottom=pads[3],
                        cornerRadiusTL=r, layoutWidthScaleType="fixed" if isinstance(w, (int, float)) else w,
                        layoutHeightScaleType="fixed" if isinstance(h, (int, float)) else "hug")
        # the shadow layers come after the body, so they draw under it (the first child draws on top)
        shadow = kit.shadow_layers(f"{n}.sh", kit.DS["shadow"][shadow]["layers"], r) if shadow else []
        wrap = kit.box(n, [inner] + shadow, marginRight=0, **kit.hug())
        item = Item(self, name, "box", wrap)
        item.action = action_btn
        self.items[name] = item
        return item

    # ------------------------------------------------------------ DS patterns built from the piece's own content
    def menu(self, name, entries, w=268):
        """A CoreFloatingMenu (DS 140395:53574) or a dropdown's menu: white, radius 12, an edge, shadow-5, items 32 px
        apart by 2. entries, top to bottom: "Label" (a MenuListItem), {"label": ..., "icon": "i_edit",
        "destructive": True, "selected": True} (an item with its props), "-" (a divider), "# Title" (a section
        title). Returns the menu (enter / exit it); menu.entries are its items, in order (targets: hover, click)."""
        n = f"{self.art}.{name}"
        rows, items = [], []
        k = f"{self.key}_{name}_title"
        kit.text_style(k, "Display/Display 4", kit.hex_argb("#9b9ba2"))
        for i, e in enumerate(entries):
            if e == "-":
                rule = kit.box(f"{n}.rule{i}", paints=[kit.solid(f"{n}.rule{i}.fill", kit.hex_argb("#e2e2e4"))], h=1,
                               layoutWidthScaleType="fill", layoutHeightScaleType="fixed")
                rows.append(kit.box(f"{n}.ruleRow{i}", [rule], flexDirectionValue="column", paddingTop=4,
                                    paddingBottom=8, **kit.fill_w()))
            elif isinstance(e, str) and e.startswith("# "):
                t = kit.text(f"{n}.title{i}.t", [(k, e[2:])], lp=kit.hug(), wrap=False)
                rows.append(kit.box(f"{n}.title{i}", [t], paddingLeft=8, paddingRight=8, paddingTop=4, paddingBottom=8,
                                    **kit.fill_w()))
            else:
                props = {"label": e} if isinstance(e, str) else dict(e)
                if "icon" in props:
                    props.setdefault("showIcon", True)
                it = self._place(f"{name}{i}", "menuitem", MI, "mi", props, w="fill")
                rows.append(it)
                items.append(it)
        body = kit.box(f"{n}.items", [_el(r) for r in rows], flexDirectionValue="column", layoutAlignmentType="topLeft",
                       gapVertical=2, paddingLeft=8, paddingRight=8, **kit.fill_w())
        menu = self.card(name, [body], w=w, pad=(0, 12, 0, 12), gap=0, shadow="shadow-5", radius=12)
        menu.entries = items
        return menu

    def collapsible(self, name, title, kids, w=400, open=False, icon=None, card=True, gap=16):
        """A Collapsible (DS 126909:22890): a header (an optional 16 px DS icon, the title in Medium 13/18, a chevron)
        over `kids`, which unfold and fold (the body's height and the chevron together): a.click(c.header) with the
        cursor, a.open(c) / a.close(c) without it. card=True: white, radius 8, an edge, padding 24 (DS With Card)."""
        n = f"{self.art}.{name}"
        ink = kit.color("Typography/primary-text-color")
        k = f"{self.key}_{name}_title"
        kit.text_style(k, "Headlines/He 3", ink)
        head = [kit.icon_slot(f"{n}.icon", kit.ICON_FILES[icon], ink)] if icon else []
        head.append(kit.box(f"{n}.titleWrap", [kit.text(f"{n}.title.t", [(k, title)], lp=kit.hug(), wrap=False)],
                            **kit.fill_w()))
        art = kit.icon(os.path.join(kit.ICONS, kit.ICON_FILES["chevron_bottom"] + ".svg"), f"{n}.chev.art",
                       kit.color("Typography/secondary-text-color"), x=-8, y=-8)
        turn = El("Node", {"x": 8, "y": 8, "rotation": math.pi if open else 0}, [art], name=f"{n}.chevTurn")
        head.append(kit.box(f"{n}.chev", [turn], w=16, h=16, layoutWidthScaleType="fixed",
                            layoutHeightScaleType="fixed"))
        header = self._box(f"{name}Header", head, "row", 12, 0, "centerLeft", "fill", "hug")
        # the body hangs in the clip, out of its flow, so a closed clip doesn't squeeze it
        inner = self._box(f"{name}Body", kids, "column", gap, (0, 32 if card else 16, 0, 0), "topLeft", "hug", "hug",
                          positionTypeValue="absolute", positionLeft=0, positionTop=0, positionRight=0)
        clip = kit.box(f"{n}.clip", [_el(inner)], h=0, clip=True, flexDirectionValue="column",
                       layoutAlignmentType="topLeft", layoutWidthScaleType="fill", layoutHeightScaleType="fixed")
        if card:
            coll = self.card(name, [header, clip], w=w, pad=24, gap=0, shadow=None)
        else:
            coll = self._box(name, [header, clip], "column", 0, 0, "topLeft", w, "hug")
        coll.header, coll.body, coll.clip, coll.turn, coll.is_open = header, inner, f"{n}.clip", f"{n}.chevTurn", open
        coll.folds, header.coll = [], coll
        self.colls.append(coll)
        return coll

    def table(self, name, header, rows, widths, w="hug"):
        """A DS table (Table Header / Table Cell): a grey header row (Medium 13/18, secondary colour) over white rows,
        a 1 px line under each. header: the column titles; rows: lists of cells, each a string (Regular 13/18; "**Duda"
        is bold) or placed items (one, or a list: a thumb and a text...). widths: points or "fill" per column.
        Returns the table; table.rows are the row boxes (enter, stagger, a.key them)."""
        n = f"{self.art}.{name}"
        ks = {s: f"{self.key}_{name}_{s}" for s in ("head", "cell", "bold")}
        kit.text_style(ks["head"], "Headlines/He 3", kit.color("Typography/secondary-text-color"))
        kit.text_style(ks["cell"], "Content/Body", kit.color("Typography/primary-text-color"))
        kit.text_style(ks["bold"], "Content/Body Bold", kit.color("Typography/primary-text-color"))

        def cell(cid, content, wd, pad):
            if isinstance(content, str):
                st = "bold" if content.startswith("**") else "cell"
                kids = [kit.text(f"{cid}.t", [(ks[st], content.lstrip("*"))], lp=kit.hug(), wrap=False)]
            else:
                kids = [_el(c) for c in (content if isinstance(content, (list, tuple)) else [content])]
            size = {"w": wd, "layoutWidthScaleType": "fixed"} if isinstance(wd, (int, float)) else \
                {"layoutWidthScaleType": "fill"}
            return kit.box(cid, kids, flexDirectionValue="row", layoutAlignmentType="centerLeft", gapHorizontal=12,
                           paddingLeft=pad[0], paddingTop=pad[1], paddingRight=pad[2], paddingBottom=pad[3],
                           layoutHeightScaleType="hug", **size)
        heads = [kit.box(f"{n}.h{i}", [kit.text(f"{n}.h{i}.t", [(ks["head"], h)], lp=kit.hug(), wrap=False)],
                         flexDirectionValue="row", layoutAlignmentType="centerLeft", paddingLeft=16, paddingTop=8,
                         paddingRight=16, paddingBottom=8, layoutHeightScaleType="hug",
                         **({"w": wd, "layoutWidthScaleType": "fixed"} if isinstance(wd, (int, float))
                            else {"layoutWidthScaleType": "fill"}))
                 for i, (h, wd) in enumerate(zip(header, widths))]
        head_row = kit.box(f"{n}.head", heads, paints=[kit.solid(f"{n}.head.fill", kit.hex_argb("#f6f6f8"))],
                           flexDirectionValue="row", layoutAlignmentType="centerLeft", cornerRadiusTL=6,
                           **kit.fill_w())
        row_items = []
        for j, cells in enumerate(rows):
            cs = [cell(f"{n}.r{j}c{i}", c, wd, (16, 12, 16, 12)) for i, (c, wd) in enumerate(zip(cells, widths))]
            row = self._box(f"{name}Row{j}", cs, "row", 0, 0, "centerLeft", "fill", "hug",
                            paints=[kit.solid(f"{n}.r{j}.fill", kit.hex_argb("#ffffff"))])
            row.wrap.children.append(kit.absolute(f"{n}.r{j}.line", paints=[kit.solid(f"{n}.r{j}.line.fill",
                                                                                      kit.hex_argb("#e4e4e6"))],
                                                  inset=(0, None, 0, 0), h=1, layoutHeightScaleType="fixed"))
            row_items.append(row)
        table = self._box(name, [head_row] + row_items, "column", 0, 0, "topLeft", w, "hug")
        table.rows = row_items
        return table

    def overlay(self, name, w=None, h=None, radius=0):
        """The DS Overlay (#0C101C at 60 %), the artboard's size (or w x h): under a modal, with p.free. radius: round
        corners (over a window with round corners)."""
        return self._box(name, [], "column", 0, 0, "topLeft", w or self.w, h or self.h,
                         paints=[kit.solid(f"{self.art}.{name}.fill", kit.argb("#0c101c", 0.6))],
                         cornerRadiusTL=radius or None)

    def modal(self, name, title, kids, w=480, primary="Save", secondary="Cancel", help=False, close=True, gap=24,
              icon=None, primary_icon=None, title_style="Headlines/He 2 Bold"):
        """A Core modal (DS 47562:12908; shadow-5, radius 12): header (an optional 16 px icon, the title in the DS
        modal title He 2 Bold 14/20, as the product draws it; help and close icon buttons), body (`kids`, padding
        24), footer (secondary + primary buttons; None drops one, both None drop the footer; primary_icon: an icon
        after the primary's label, "chevron_right"). w: 480 S, 740 M, 1000 L, 1356 XL.
        Targets: modal.primary, modal.secondary, modal.close."""
        n = f"{self.art}.{name}"
        edge = kit.hex_argb("#e4e4e6")
        ink = kit.color("Typography/primary-text-color")
        head = ([kit.icon_slot(f"{n}.titleIcon", kit.ICON_FILES[icon], ink)] if icon else []) + [
            self.text(f"{name}Title", title, style=title_style),
            kit.box(f"{n}.headGap", h=1, layoutWidthScaleType="fill", layoutHeightScaleType="fixed")]
        help_b = self.icon_button(f"{name}Help", icon="i_info_circle", variant=1, size=0, color=4) if help else None
        close_b = self.icon_button(f"{name}Close", icon="i_x", variant=1, size=0, color=4) if close else None
        head += [b for b in (help_b, close_b) if b]
        header = self._box(f"{name}Header", head, "row", 8, (24, 16, 24, 16), "centerLeft", "fill", "hug")
        header.wrap.children.append(kit.absolute(f"{n}.headLine", paints=[kit.solid(f"{n}.headLine.fill", edge)],
                                                 inset=(0, None, 0, 0), h=1, layoutHeightScaleType="fixed"))
        body = self._box(f"{name}Body", kids, "column", gap, 24, "topLeft", "fill", "hug")
        parts = [header, body]
        sec_b = self.button(f"{name}Secondary", label=secondary, variant=1, color=0) if secondary else None
        pri_b = self.button(f"{name}Primary", label=primary, variant=0, color=0,
                            **({"showRightIcon": True, "rightIcon": primary_icon} if primary_icon else {})) \
            if primary else None
        if sec_b or pri_b:
            footer = self._box(f"{name}Footer", [b for b in (sec_b, pri_b) if b], "row", 8, (24, 16, 24, 16),
                               "centerRight", "fill", "hug")
            footer.wrap.children.append(kit.absolute(f"{n}.footLine", paints=[kit.solid(f"{n}.footLine.fill", edge)],
                                                     inset=(0, 0, 0, None), h=1, layoutHeightScaleType="fixed"))
            parts.append(footer)
        modal = self.card(name, parts, w=w, pad=0, gap=0, shadow="shadow-5", border=False, radius=12)
        modal.primary, modal.secondary, modal.close = pri_b, sec_b, close_b
        return modal

    def item_card(self, name, value, label, icon=None, theme=1, info=True, trend=None, w=226):
        """An Item Card, horizontal (DS "Item Card": the KPI card of the release notes): the value (SemiBold 24/28)
        and an optional trend ("+12%", positive colour), a label (Medium 13/18, secondary colour) with an info icon,
        an Icon Thumbnail (36, theme as p.thumb) at the right; white, radius 8, an edge."""
        n = f"{self.art}.{name}"
        top = [self.text(f"{name}Value", value, style=None, color="#1e1e1e", size=24, lh=28, weight=600)]
        if trend:
            top.append(self.text(f"{name}Trend", trend, style="Headlines/He 4", color="Indications/positive-color"))
        bottom = [self.text(f"{name}Label", label, style="Headlines/He 3", color="Typography/secondary-text-color")]
        if info:
            bottom.append(kit.icon_slot(f"{n}.info", "common_actions/i_info_circle",
                                        kit.color("Typography/secondary-text-color")))
        texts = self.column(f"{name}Texts", [self.row(f"{name}Top", top, gap=8, align="bottomLeft"),
                                             self.row(f"{name}Bottom", bottom, gap=4)], gap=8)
        gap_el = kit.box(f"{n}.gap", h=1, layoutWidthScaleType="fill", layoutHeightScaleType="fixed")
        thumb = self.thumb(f"{name}Thumb", icon=icon or "i_site", theme=theme, size=1)
        content = self.row(f"{name}Row", [texts, gap_el, thumb], gap=16, align="topLeft", w="fill")
        return self.card(name, [content], w=w, pad=16, gap=0, shadow=None)

    # ------------------------------------------------------------ the Vibe editor, built from library components
    # Product measures (my.duda.co, 2026-10-22, pecas/vibe-workspace and pecas/copilot); details of the same UI from
    # the Figma (release notes "Vibe MCP oct 2026", 16:90808, and the hero storyboards).
    def _edge(self, box_item, side, col="#e4e4e6"):
        """A 1 px line on one side of a placed box (top, bottom, left, right), drawn over its content."""
        n = f"{box_item.wrap.name}.{side}Edge"
        inset = {"top": (0, 0, 0, None), "bottom": (0, None, 0, 0), "left": (0, 0, None, 0),
                 "right": (None, 0, 0, 0)}[side]
        size = {"h": 1, "layoutHeightScaleType": "fixed"} if side in ("top", "bottom") else \
            {"w": 1, "layoutWidthScaleType": "fixed"}
        box_item.wrap.children.insert(0, kit.absolute(n, paints=[kit.solid(f"{n}.fill", _color(col))], inset=inset,
                                                      **size))

    def _art(self, name, file, size, w=None, h=None):
        """One of the library's own drawings (art/), `size` wide, centred in a w x h box."""
        n = f"{self.art}.{name}"
        art = kit.icon(os.path.join(kit.ART, file), f"{n}.art", kit.WHITE, size=size)
        return kit.box(n, [art], w=w or size, h=h or size, layoutWidthScaleType="fixed", layoutHeightScaleType="fixed")

    def vibe_topbar(self, name, project="Project Name", tabs=("Canvas", "Code", "Manage"), tab=0, w="fill",
                    comments=True):
        """The Vibe editor's top bar: 60 tall, white, a line under it. Left: the menu, the Duda Vibe logo, the
        project's name; centre: the tabs (Pill_Tabs, 80 each; tabs=None: none); right: comments (comments=False: no),
        share, Preview, Publish, the AI button, home.
        Targets: bar.menu, bar.tabs (bar.tabs.tab(i)), bar.comments, bar.share, bar.preview, bar.publish, bar.ai,
        bar.home."""
        menu = self.icon_button(f"{name}Menu", icon="i_hamburger", variant=0, size=1, color=4)
        word = self._art(f"{name}.word", "vibe_word.svg", 41.2, 41.2, 24)
        brand = self._box(f"{name}Brand", [self._art(f"{name}.logo", "logo_duda.svg", 72, 72, 32), word], "row", 6, 0,
                          "centerLeft", "hug", "hug")
        left = self._box(f"{name}Left", [menu, brand, self.divider(f"{name}Div", variant=2, h=18),
                                         self.text(f"{name}Project", project, style="Headlines/He 2")],
                         "row", 12, 0, "centerLeft", "fill", "hug", flexBasis=0, flexBasisUnitsValue="points")
        pills = self.pill_tabs(f"{name}Tabs", w=80 * len(tabs) + 4, fill=True, count=len(tabs), selected=tab,
                               **{f"label{i + 1}": t for i, t in enumerate(tabs)}) if tabs else None
        share = self.icon_button(f"{name}Share", icon="i_share_file", variant=1, size=1, color=4)
        preview = self.button(f"{name}Preview", label="Preview", variant=1, size=1, color=3)
        publish = self.button(f"{name}Publish", label="Publish", variant=0, size=1, color=1)
        ai = self.wrap(f"{name}Ai", [kit.box(f"{self.art}.{name}Ai.tile", [self._art(f"{name}Ai.star", "ai_star.svg",
                                                                                     16)],
                                             paints=[kit.solid(f"{self.art}.{name}Ai.fill", kit.argb("#000000", .04))],
                                             w=32, h=32, cornerRadiusTL=6, flexDirectionValue="column",
                                             layoutAlignmentType="center", layoutWidthScaleType="fixed",
                                             layoutHeightScaleType="fixed")])
        home = self.icon_button(f"{name}Home", icon="i_home", variant=1, size=1, color=4)
        talk = self.icon_button(f"{name}Comments", icon="i_site_comments", variant=0, size=1, color=4) \
            if comments else None
        right = self._box(f"{name}Right", [b for b in (talk, share, preview, publish, ai) if b] +
                          [self.divider(f"{name}Div2", variant=2, h=18), home],
                          "row", 12, 0, "centerRight", "fill", "hug", flexBasis=0, flexBasisUnitsValue="points")
        bar = self._box(name, [left] + ([pills] if pills else []) + [right], "row", 8, (16, 0, 16, 0), "centerLeft",
                        w, 60,
                        paints=[kit.solid(f"{self.art}.{name}.fill", kit.WHITE)])
        self._edge(bar, "bottom", "#e2e2e4")
        bar.menu, bar.tabs, bar.share, bar.preview, bar.publish, bar.ai, bar.home = (menu, pills, share, preview,
                                                                                     publish, ai, home)
        bar.comments = talk
        return bar

    def canvas_header(self, name, page="Home", w="fill", compact=False):
        """The bar over the Vibe canvas: 48 tall, white. Refresh and the page's name (a menu) at the left; the device
        at the right. compact=True: the storyboards' denser bar (36 tall, the page as a Small text button).
        Targets: head.refresh, head.page, head.device."""
        refresh = self.icon_button(f"{name}Refresh", icon="i_refresh", variant=0, size=0, color=1)
        page_b = self.button(f"{name}Page", label=page, variant=2, size=0 if compact else 1, color=2,
                             showRightIcon=True, rightIcon="chevron_bottom")
        n = f"{self.art}.{name}"
        device = self._box(f"{name}Device", [
            kit.icon_slot(f"{n}.desktop", "devices/i_desktop", kit.color("Typography/primary-text-color")),
            kit.icon_slot(f"{n}.devChev", "arrows/chevron_bottom", kit.color("Typography/secondary-text-color"),
                          size=14)], "row", 6, 4, "centerLeft", "hug", "hug", origin=(0.5, 0.5))
        head = self._box(name, [self._box(f"{name}Left", [refresh, page_b], "row", 8, 0, "centerLeft", "hug", "hug"),
                                device], "row", 0, (12, 4, 12, 4) if compact else (16, 8, 16, 8),
                         "spaceBetweenCenter", w, 36 if compact else 48, paints=[kit.solid(f"{n}.fill", kit.WHITE)])
        head.refresh, head.page, head.device = refresh, page_b, device
        return head

    def vibe_rail(self, name, icons=("i_edit", "i_add_widget", "i_color_palette", "-", "i_version"), selected=None,
                  h="fill", learn=True):
        """VibePanelsMenu: the rail at the Vibe editor's right, 58 wide, white, a line at its left: 46 px items 2
        apart, each a Large Dark Icon button; "-" is a divider. selected: the index of the open panel's item.
        learn: a divider and the learning centre (the cap) after the icons, as the product has them.
        Targets: rail.buttons (the Icon buttons, in order; None for a divider)."""
        n = f"{self.art}.{name}"
        items, buttons = [], []
        if learn and "i_learn" not in icons:
            icons = tuple(icons) + ("-", "i_learn")
        for i, ic in enumerate(icons):
            if ic == "-":
                line = kit.box(f"{n}.rule{i}", paints=[kit.solid(f"{n}.rule{i}.fill", kit.hex_argb("#e4e4e6"))], h=1,
                               layoutWidthScaleType="fill", layoutHeightScaleType="fixed")
                items.append(kit.box(f"{n}.ruleRow{i}", [line], paddingTop=3, paddingBottom=3,
                                     flexDirectionValue="column", **kit.fill_w()))
                buttons.append(None)
                continue
            b = self.icon_button(f"{name}{i}", icon=ic, variant=0, size=1, color=4, selected=i == selected)
            items.append(self._box(f"{name}Item{i}", [b], "row", 0, 0, "center", 46, 46))
            buttons.append(b)
        rail = self._box(name, items, "column", 2, (6, 6, 6, 0), "topLeft", 58, h,
                         paints=[kit.solid(f"{n}.fill", kit.WHITE)])
        self._edge(rail, "left")
        rail.buttons = buttons
        return rail

    def chat_user(self, name, string, fill="#f6f6f8", color="Typography/primary-text-color", style="Content/Body 14",
                  lh=None, weight=None, pad=(12, 8)):
        """UserChatInput: the user's message in a bubble at the right (radius 8, the corner by the panel's edge
        square), as wide as its text up to the chat's width less 40. pad: (sides, top and bottom)."""
        n = f"{self.art}.{name}"
        k = f"{self.key}_{name}"
        kit.text_style(k, style, _color(color), lh=lh, weight=weight)
        t = kit.text(f"{n}.t", [(k, string)], lp=kit.hug(), wrap=True)
        bubble = kit.box(f"{n}.bubble", [t], paints=[kit.solid(f"{n}.fill", _color(fill))], cornerRadiusTL=8,
                         cornerRadiusTR=8, cornerRadiusBR=0, cornerRadiusBL=8, linkCornerRadius=False,
                         paddingLeft=pad[0], paddingRight=pad[0], paddingTop=pad[1], paddingBottom=pad[1],
                         maxWidth=100, maxWidthUnitsValue="percent", flexDirectionValue="column", **kit.hug())
        return self._box(name, [bubble], "column", 0, (40, 0, 0, 0), "topRight", "fill", "hug")

    def chat_ai(self, name, string, style="Content/Body 14", color="Typography/primary-text-color", lh=None,
                weight=None):
        """AiChatOutput: the AI's answer, a paragraph across the chat."""
        return self.text(name, string, style=style, color=color, w="fill", lh=lh, weight=weight)

    def ai_panel(self, name, title="New chat", chat=None, w=None, h="fill", placeholder=None, mode=None, gap=24,
                 title_menu=True, prompt=None, reply=None, floating=False, **props):
        """AiPanel, the component (v05): the Vibe chat docked (w 406) or, floating=True, the Copilot (w 368, rounded,
        a shadow). prompt: the user's message (a.type_into(panel, ...) types it; else it is just there once sent);
        reply: the answer, a text or up to 3 paragraphs; mode: the mode button ("Build"); placeholder; any other
        AiPanel property (titleAfter: the chat's name once answered, greeting, subtitle, chip1..chip4, status,
        disclaimer, link, showThought, figmaActions, hidden...). The actions: a.type_into(panel, text),
        a.click(panel.part("send")) sends (stage 1: the bubble, "Thinking..."), a.reply(panel) brings the answer
        paragraph by paragraph and then the action bar; a.set(panel, hidden=True) closes it (False opens it).
        Parts (cursor targets): panel.part("send" | "field" | "plus" | "tool" | "mic" | "build" | "options" |
        "collapse" | "chip1".."chip4" | "showMore"; floating: "float", "at").
        chat=[...]: the v04 panel instead, a free conversation of your own items (below)."""
        if chat is not None:
            return self._ai_panel_free(name, title, chat, w or 406, h, placeholder or "Ask anything", mode or "Plan",
                                       gap, title_menu)
        vals = dict(title=title, copilot=floating, placeholder=placeholder or "Describe your idea...",
                    build=mode or "Build")
        vals["placeholderAfter"] = props.pop("placeholderAfter", vals["placeholder"])
        if prompt is not None:
            vals["prompt"] = prompt
        if reply is not None:
            paras = [reply] if isinstance(reply, str) else list(reply)
            assert 1 <= len(paras) <= 3, "reply: a text or up to 3 paragraphs"
            vals.update(zip(aip.REPLIES, paras + [""] * (3 - len(paras))))
        vals.update(props)
        return self._place(name, "aipanel", aip.AIP, "aipanel", vals, w=w or (aip.FLOATED_W if floating else
                                                                              aip.DOCKED_W), h=h)

    def _ai_panel_free(self, name, title, chat, w, h, placeholder, mode, gap, title_menu):
        """AiPanel, docked (the Vibe chat): a 48 px header (the title, its menu chevron (.ChatName; title_menu=False:
        none), options, collapse), the conversation (`chat`: p.chat_user, p.chat_ai, p.ai_status..., top to bottom,
        `gap` apart), the ChatInput (placeholder, +, the cursor tool, the mode, the mic, send) and the disclaimer.
        White, a line at its left.
        Targets: panel.options, panel.collapse, panel.input (the field), panel.plus, panel.send; panel.chat is the
        conversation box, panel.title the title (a.text(panel.title, "...") renames the chat), panel.content its
        header, conversation and input (a.hide(panel.content) leaves the white panel: another panel takes its place)."""
        n = f"{self.art}.{name}"
        options = self.icon_button(f"{name}Options", icon="i_options", variant=0, size=0, color=4)
        collapse = self.icon_button(f"{name}Collapse", icon="i_common_expand", variant=0, size=0, color=4)
        title_t = self.text(f"{name}Title", title, style="Headlines/He1 Half")
        name_row = self._box(f"{name}Name", [title_t] + ([kit.icon_slot(
            f"{n}.titleChev", "arrows/chevron_bottom", kit.color("Typography/secondary-text-color"))]
            if title_menu else []), "row", 4, 0, "centerLeft", "hug", "hug")
        head = self._box(f"{name}Head", [
            name_row,
            kit.box(f"{n}.headGap", h=1, layoutWidthScaleType="fill", layoutHeightScaleType="fixed"),
            self._box(f"{name}Ctl", [options, self.divider(f"{name}CtlDiv", variant=2, h=18), collapse], "row", 6, 0,
                      "centerLeft", "hug", "hug")], "row", 8, (16, 12, 16, 12), "centerLeft", "fill", 48)
        talk = self._box(f"{name}Chat", list(chat), "column", gap, (24, 40, 24, 24), "topLeft", "fill", "fill",
                         clip=True)
        # ChatInput (DS 136758:...; the copilot v04's measures): the field over its actions
        ph = self.text(f"{name}Ph", placeholder, style="Content/Body 14", color="#9b9ba2")
        area = self._box(f"{name}Area", [ph], "column", 0, (16, 12, 16, 0), "topLeft", "fill", "hug", minHeight=44)
        plus = self.icon_button(f"{name}Plus", icon="i_plus", variant=0, size=0, color=4)
        tool = self.icon_button(f"{name}Tool", icon="i_cursor", variant=0, size=0, color=4)
        mode_b = self.button(f"{name}Mode", label=mode, variant=2, size=0, color=2, showRightIcon=True,
                             rightIcon="chevron_bottom")
        mic = self.icon_button(f"{name}Mic", icon="i_mic", variant=0, size=0, color=4)
        send = self.wrap(f"{name}Send", [kit.box(f"{n}.sendDot", [
            kit.icon_slot(f"{n}.sendArrow", "arrows/i_arrow_top", kit.WHITE)],
            paints=[kit.solid(f"{n}.sendDot.fill", kit.hex_argb("#e2e2e4"))], w=26, h=26, cornerRadiusTL=13,
            flexDirectionValue="column", layoutAlignmentType="center", layoutWidthScaleType="fixed",
            layoutHeightScaleType="fixed")])
        acts = self._box(f"{name}Acts", [
            self._box(f"{name}ActsL", [plus, self.divider(f"{name}ActDiv", variant=2, h=18), tool], "row", 6, 0,
                      "centerLeft", "hug", "hug"),
            self._box(f"{name}ActsR", [mode_b, self.divider(f"{name}ActDiv2", variant=2, h=18), mic, send], "row", 8,
                      0, "centerRight", "hug", "hug")], "row", 0, (12, 8, 12, 12), "spaceBetweenCenter", "fill", "hug")
        field = self._box(f"{name}Input", [area, acts], "column", 0, 0, "topLeft", "fill", "hug",
                          paints=[kit.solid(f"{n}.inputFill", kit.WHITE)], cornerRadiusTL=8)
        field.wrap.children.insert(0, kit.absolute(f"{n}.inputEdge", paints=[kit.line(f"{n}.inputEdge.stroke",
                                                                                       kit.hex_argb("#ededee"), 1)],
                                                   inset=(0.5,) * 4, cornerRadiusTL=7.5))
        note = self.text(f"{name}Note", "AI can make mistakes. Learn more", style="Content/Mini", color="#93959a")
        foot = self._box(f"{name}Foot", [field, note], "column", 4, (16, 0, 16, 12), "topLeft", "fill", "hug")
        panel = self._box(name, [head, talk, foot], "column", 0, 0, "topLeft", w, h,
                          paints=[kit.solid(f"{n}.fill", kit.WHITE)])
        self._edge(panel, "left", "#ededee")
        panel.options, panel.collapse, panel.input, panel.plus, panel.send = options, collapse, field, plus, send
        panel.chat, panel.title, panel.content = talk, title_t, [head, talk, foot]
        return panel

    def vibe_workspace(self, name, canvas=(), panel=None, w=1440, h=900, topbar=None, rail=None, page="Home",
                       canvas_fill="#ffffff", radius=0, fill="#f6f6f8", compact=False):
        """The Vibe editor's window: the top bar over the canvas (a white stage 24 in from the edges: the canvas
        header over `canvas`, your items: the site), the docked panel (a p.ai_panel, a p.quick_edits, a list of
        them: stacked in one place, the later ones on top; or None) and the rail.
        topbar / rail: your own p.vibe_topbar / p.vibe_rail (else the defaults). fill: the window's colour (#F6F6F8;
        None: see-through, your own background shows), its corners `radius` round. compact: the canvas header's
        compact size.
        Targets: ws.topbar, ws.canvas_head, ws.rail, ws.panel (the first panel); ws.stage is the canvas box."""
        n = f"{self.art}.{name}"
        top = topbar or self.vibe_topbar(f"{name}Top")
        head = self.canvas_header(f"{name}CanvasHead", page=page, compact=compact)
        panels = list(panel) if isinstance(panel, (list, tuple)) else ([panel] if panel else [])
        if len(panels) > 1:   # one place, several panels: the stack draws its first child on top
            panel = self._box(f"{name}Panels", panels[::-1], "column", 0, 0, "topLeft", "hug", "fill",
                              layoutTypeValue="stack")
        elif panels:
            panel = panels[0]
        stage = self._box(f"{name}Stage", [head] + list(canvas), "column", 0, 0, "topLeft", "fill", "fill", clip=True,
                          paints=[kit.solid(f"{n}.stageFill", _color(canvas_fill))], cornerRadiusTL=8,
                          cornerRadiusTR=8, cornerRadiusBL=0, cornerRadiusBR=0, linkCornerRadius=False)
        main = self._box(f"{name}Main", [stage], "column", 0, (24, 24, 24, 0), "topLeft", "fill", "fill")
        side = rail or self.vibe_rail(f"{name}Rail")
        body = self._box(f"{name}Body", [main] + ([panel] if panel else []) + [side], "row", 0, 0, "topLeft",
                         "fill", "fill")
        win = self._box(name, [top, body], "column", 0, 0, "topLeft", w, h, clip=True,
                        paints=[kit.solid(f"{n}.fill", kit.CLEAR if fill is None else _color(fill))],
                        cornerRadiusTL=radius or None)
        win.topbar, win.canvas_head, win.rail, win.stage = top, head, side, stage
        win.panel = panels[0] if panels else None
        win.panels = panels
        return win

    def layout(self, root, align="center", pad=0):
        """What the artboard shows: `root` placed in the frame (align: center, topCenter, topLeft...)."""
        pads = pad if isinstance(pad, (tuple, list)) else (pad,) * 4
        self.root = kit.box(f"{self.art}.page", [_el(root)], flexDirectionValue="column", layoutAlignmentType=align,
                            paddingLeft=pads[0], paddingTop=pads[1], paddingRight=pads[2], paddingBottom=pads[3],
                            layoutWidthScaleType="fill", layoutHeightScaleType="fill")

    # ------------------------------------------------------------ the artboard
    def actions(self):
        """The choreography: returns an Actions on one timeline (call after layout())."""
        assert self.root is not None, "call p.layout(root) first"
        assert self.a is None, "one Actions per piece"
        cur = {"shadow": True} if self.cursor_shadow else {}
        self.props += [("cursor", "vm:cursor", CURSOR.inst(f"vmi.cursor.{self.key}", cur, name=f"{self.art} cursor")),
                       ("play", "trigger", None), ("tabChange", "trigger", None)]
        self.vm = kit.VM(self.key, f"{self.art} view model", self.props)
        kit.use(self.vm)
        self.overlay = El("Node", {"x": 0, "y": 0}, [], name=f"{self.art}.cursors")
        self.fx = El("Node", {"x": 0, "y": 0}, [], name=f"{self.art}.effects")   # over the scene, under the cursors
        self.drivers = El("CustomPropertyGroup", {"x": 0, "y": self.h + 40}, [], name="Drivers")
        self.board = El("Artboard", {"defaultStateMachineId": f"@sm.{self.key}", "viewModelId": f"@{self.vm.ref()}",
                                     "viewModelInstanceId": f"@vmi.{self.key}", "styleId": f"@{self.art}Art.style",
                                     "width": self.w, "height": self.h, "clip": True, "x": 0, "y": 0},
                         [kit.style(f"{self.art}Art"), kit.solid(f"{self.art}Art.fill", self.bg),
                          El("FocusData", {"canFocus": False}), self.drivers, self.overlay, self.fx, self.root],
                         name=self.art, ref=f"art.{self.key}")
        choreo.configure({"design": [self.w, self.h], "output": [self.w, self.h]})
        self.a = Actions(self)
        for c in self.colls:     # an open collapsible starts at its body's full height
            if c.is_open:
                self.a.c.set(0, c.clip, "height", float(self.bounds(c.body, 0)[3]))
        return self.a

    def _by(self):
        by = {}
        kit.walk(self.board, lambda e: by.__setitem__(e.name, e) if e.name else None)
        return by

    def _parent_of(self, el):
        found = []

        def walk(e):
            for c in e.children:
                if isinstance(c, El):
                    if c is el:
                        found.append(e)
                    walk(c)
        walk(self.board)
        return found[0] if found else None

    # ------------------------------------------------------------ measure (where things are, for the cursor)
    def bounds(self, item, t=0.0):
        """(x, y, w, h) of a placed item in artboard points, as laid out at time t."""
        if item.kind == "tab":
            return self._measure(t)[f"{item.parent.wrap.name}/{TAB_PARTS[item.parent.kind]}{item.index + 1}"]
        if item.kind == "part" and item.parent.kind == "aipanel":   # a control of the AiPanel
            return self._measure(t)[f"{item.parent.wrap.name}/{aip.PREFIX}{aip.PARTS[item.pname][0]}"]
        if item.kind == "part":   # each part of the floating bar where it is (its labels may be longer)
            return self._measure(t)[f"{item.parent.wrap.name}/VibeFloatingBar.slot.{item.key.split('.')[-1]}"]
        return self._measure(t)[item.wrap.name]

    def _measure(self, t):
        a = self.a
        f = frame(t)
        elem = {}   # (element name, prop) -> value at t (widths, displays, margins: layout)
        for (n, p), tr in a.c.tracks.items():
            if n.startswith("drv.") or p in NO_LAYOUT or n in self.no_layout:
                continue
            elem[(n, p)] = tr.value_at(f)
        insts = {}  # driver values at t, written into the placements' data
        for name, (item, prop) in a.driver_of.items():
            if prop not in DRV_NO_LAYOUT and not prop.startswith("hover"):
                insts[(item.inst[1], prop)] = a.c.tracks[(name, "propertyValue")].value_at(f)
        state = json.dumps([sorted(map(list, elem.items())), sorted(map(list, insts.items()))], default=str)
        if state in self._measured:
            return self._measured[state]
        # the measure scene: the piece without its timeline, drivers or cursors, a marker on every placement
        board = copy.deepcopy(self.board)
        by = {}
        kit.walk(board, lambda e: by.__setitem__(e.name, e) if e.name else None)
        board.children = [c for c in board.children if c.name not in ("Drivers", f"{self.art}.cursors",
                                                                        f"{self.art}.effects")]
        for (n, p), v in elem.items():
            by[n].attrs[p] = {0: "flex", 1: "none"}.get(v, v) if p == "displayValue" else v
        for it in self.items.values():
            w = by[it.wrap.name]
            w.children.insert(0, El("SemanticData", {"role": "group", "label": it.wrap.name},
                                    name=f"{it.wrap.name}.measure"))
        lay = kit.Layer("Measure")
        lay.state("idle", None, entry=True)
        board.children.append(kit.machine([lay]))
        saved = []
        for (ref, prop), v in insts.items():
            for vm in kit.VM.all.values():
                for inst in vm.instances:
                    if inst[1] == ref:
                        saved.append((inst[2], prop, inst[2].get(prop, KeyError)))
                        inst[2][prop] = v
        out = os.path.join(self.here, "build", "measure")
        os.makedirs(out, exist_ok=True)
        font = kit.FONT_DIR[0]
        kit.FONT_DIR[0] = "fonts"
        try:
            xml, _ = kit.assemble([board] + [_probed(c) for c in self.comps] + self.icons, list(kit.VM.all),
                                  base=out)
        finally:
            kit.FONT_DIR[0] = font
            for d, prop, old in saved:
                if old is KeyError:
                    d.pop(prop, None)
                else:
                    d[prop] = old
        if not os.path.exists(os.path.join(out, "fonts")):
            os.symlink(os.path.join(kit.HERE, "fonts"), os.path.join(out, "fonts"))
        cache_f = os.path.join(out, "cache.json")
        cache = json.load(open(cache_f)) if os.path.exists(cache_f) else {}
        h = hashlib.sha256(xml.encode()).hexdigest()
        if h not in cache:
            open(os.path.join(out, "scene.rml"), "w").write(xml + "\n")
            open(os.path.join(out, "rive.yaml"), "w").write(f'name: measure\nmain: "{self.art}"\n')
            r = subprocess.run([RIVE, out, "--semantics=-", "--advance=2", "--quiet"], capture_output=True, text=True,
                               timeout=120)
            if r.returncode:
                raise RuntimeError("measure failed:\n" + (r.stdout + r.stderr)[-1500:])
            found = {}

            def walk(node, owner=None):
                b, label = node.get("bounds"), node.get("label")
                if label and label.startswith("part:"):   # a part inside a placement: "<placement>/<part>"
                    label = f"{owner}/{label[5:]}"
                if b:
                    found[label] = (b["x"], b["y"], b["width"], b["height"])
                for c in node.get("children", []):
                    walk(c, owner if node.get("label", "").startswith("part:") else node.get("label"))
            for root in json.loads(r.stdout)["roots"]:
                walk(root)
            cache[h] = found
            json.dump(cache, open(cache_f, "w"))
        self._measured[state] = {k: tuple(v) for k, v in cache[h].items()}
        return self._measured[state]

    def point(self, item, where=None, t=0.0):
        """Where the cursor aims on `item` at time t: "center" (default; an input's default is "field"), "field" (an
        input's text field), "remove" (a tag's x), or (dx, dy) from the centre."""
        x, y, w, h = self.bounds(item, t)
        cx, cy = x + w / 2, y + h / 2
        if item.kind in ("tab", "part"):
            return (cx, cy)
        if where is None and item.kind == "textarea":     # inside the field, near its first line
            top = 26 if item.value("showLabel") else 0
            return (x + min(0.3 * w, 90), y + top + min(18, (h - top) / 2))
        if where is None and item.kind == "dropdown":     # the field, under the label
            return (x + min(0.3 * w, 90), y + h - 17.5)
        if where is None and item.kind == "input":
            where = "field"
        if where in (None, "center"):
            return (cx, cy + (1 if item.kind in ("button", "ib") else 0))
        if where == "field":     # measured from the bottom: [label] field [message room]
            assert item.kind == "input"
            field = 35 if self.a.state_at(item, "size", t) == 0 else 25
            room = MSG_ROOM if self.a.state_at(item, "showMessage", t) else 0
            return (x + min(0.3 * w, 90), y + h - room - field / 2)
        if where == "remove":
            assert item.kind == "tag"
            return (x + w - (13 if item.value("size") == 1 else 10), cy)
        return (cx + where[0], cy + where[1])

    # ------------------------------------------------------------ build
    def build(self, tabs=False, duration=None):
        """Write scene.rml (and rive.yaml if missing), print the timeline and the lints. tabs=True: a hero tab (the
        timeline plays once, fires `tabChange` at its end, `play` restarts it); otherwise the timeline loops.
        duration=s: the timeline is exactly s seconds (a hero tab: tabChange at s); without it, it ends 0.5 s after
        the last action (or with the loop's seam). Anything still moving after s fails the build.
        Exits 1 when a lint fails. `python build.py --stills 1.2 3.4` also renders those times to build/stills/."""
        a = self.a
        a._finish(tabs, duration)
        c = a.c
        kit.use(self.vm)
        # the timeline: every key the actions made (elements, drivers, cursors)
        tl = El("LinearAnimation", {"fps": FPS, "duration": c.F, "loopValue": None if tabs else "loop"},
                c.to_rml(), name="Timeline", ref=f"anim.{self.art} timeline")
        run = type("A", (), {"name": f"{self.art} timeline"})
        lay = kit.Layer("Main")
        if tabs:
            fire = kit.tick()
            lay.state("run", run, lay.go("run2", kit.if_trigger("play")), lay.go("end", at_end=True), entry=True)
            lay.state("end", fire, lay.go("run2", at_end=True), lay.go("run2", kit.if_trigger("play")),
                      actions=[kit.fire("tabChange")])
            lay.state("run2", run, lay.go("run", kit.if_trigger("play")), lay.go("end2", at_end=True))
            lay.state("end2", fire, lay.go("run", at_end=True), lay.go("run", kit.if_trigger("play")),
                      actions=[kit.fire("tabChange")])
        else:
            lay.state("run", run, lay.go("run2", kit.if_trigger("play")), entry=True)
            lay.state("run2", run, lay.go("run", kit.if_trigger("play")))
        board = copy.deepcopy(self.board)
        board.children.insert(3, tl)
        board.children.append(kit.machine([lay]))
        xml, doc = kit.assemble([board] + self.comps + self.icons, list(kit.VM.all), base=self.here)
        open(os.path.join(self.here, "scene.rml"), "w").write(xml + "\n")
        yml = os.path.join(self.here, "rive.yaml")
        if not os.path.exists(yml):
            lib = os.path.relpath(kit.HERE, self.here)
            open(yml, "w").write(f'name: {os.path.basename(self.here)}\nmain: "{self.art}"\nexclude:\n  - build\n'
                                 f'  - {lib}/icons\n  - {lib}/ds\n')
        issues = a._report(tabs)
        print(f"wrote scene.rml: {self.art} {self.w}x{self.h}, {c.F} frames ({c.F / FPS:.2f} s, "
              f"{'plays once, then tabChange' if tabs else 'loops'}), {len(a.driver_of)} drivers, "
              f"{len(a.visits)} cursor visit(s)")
        if "--stills" in sys.argv:
            ts = [float(x) for x in sys.argv[sys.argv.index("--stills") + 1:] if not x.startswith("--")]
            self.stills(ts)
        if issues:
            print(f"LINT FAILED ({len(issues)})")
            sys.exit(1)
        print("lints: clean")

    def stills(self, times):
        """Render the piece at these times (seconds) to build/stills/ (frame N at 60 fps is --advance=N+1), plus a
        contact sheet build/stills/sheet.png."""
        out = os.path.join(self.here, "build", "stills")
        os.makedirs(out, exist_ok=True)
        files = []
        for t in times:
            n = frame(t)
            p = os.path.join(out, f"t{t:05.2f}_f{n}.png")
            r = subprocess.run([RIVE, self.here, f"--screenshot={p}", f"--advance={n + 1}", "--quiet"],
                               capture_output=True, text=True, timeout=120)
            if r.returncode:
                raise RuntimeError(r.stdout[-800:] + r.stderr[-800:])
            files.append((f"{t:.2f} s (frame {n})", p))
        try:
            from PIL import Image, ImageDraw
            ims = [(lab, Image.open(p).convert("RGB")) for lab, p in files]
            s = 0.5 if self.w > 900 else 1.0
            cw, ch = int(self.w * s), int(self.h * s)
            cols = 2 if len(ims) > 1 else 1
            sheet = Image.new("RGB", (cols * (cw + 12) + 12, ((len(ims) + cols - 1) // cols) * (ch + 30) + 12),
                              (240, 240, 242))
            d = ImageDraw.Draw(sheet)
            for i, (lab, im) in enumerate(ims):
                x, y = 12 + (i % cols) * (cw + 12), 12 + (i // cols) * (ch + 30)
                d.text((x, y), lab, fill=(30, 30, 30))
                sheet.paste(im.resize((cw, ch)), (x, y + 18))
            sheet.save(os.path.join(out, "sheet.png"))
            print("stills:", out, "(sheet.png)")
        except ImportError:
            print("stills:", out)


class Actions(ActionPatterns):
    """The choreography of one piece, on one timeline. Times are seconds; `t=None` means "now" (`a.now`), and
    every action moves `now` to when it is done, so a sequence reads top to bottom with no arithmetic.
    `a.c` is the timeline itself (the kit's choreo): keys of your own there (a.c.set / move / fade / enter,
    a.beats(...)) are not actions, so they don't move `now`."""

    def __init__(self, piece):
        self.p = piece
        self.c = Choreo(piece.board, piece._by(), 1.0)
        self.c.parent[id(piece.overlay)] = piece.board
        self.c.parent[id(piece.fx)] = piece.board
        self.now = 0.0
        self.statuses = []                      # p.gen_status()es: their shimmer runs until done
        self.visits, self.visit = [], None      # cursor visits; the open one
        self.driver_of = {}                     # driver name -> (item, prop)
        self.focus = None                       # the input that holds the focus
        self.log, self.messages, self.end = [], [], 0.0
        self.looped, self.loop_exit, self.issues = False, None, []

    # ------------------------------------------------------------ time
    def _t(self, t):
        return self.now if t is None else t

    def at(self, t):
        """Move `now` to t."""
        self.now = t
        return t

    def wait(self, s):
        """Let s seconds (or a duration token: "read_hold") pass (the cursor, if on screen, waits aside or leaves on
        its own: it never parks)."""
        self.now += secs(s)
        return self.now

    hold = wait   # a reading hold: every message the viewer must read stays >= 1 s

    def _note(self, t, what):
        self.log.append((t, what))
        self.end = max(self.end, t)

    # ------------------------------------------------------------ drivers (component states on the timeline)
    def _driver(self, item, prop):
        assert item.vm is not None, f"{item} has no view model"
        kind = item.vm.kind(prop)
        assert kind in DRIVER, f"{item.vm.name}.{prop} is {kind}: set it when placing, not on the timeline"
        name = f"drv.{item.key}.{prop}"
        if name not in self.driver_of:
            tag, pkey = DRIVER[kind]
            v0 = item.value(prop)
            el = El(tag, {"propertyValue": v0}, [El("DataBindContext", {
                "sourcePathIds": item.path + (item.vm.ref(prop),), "propertyKey": pkey, "direction": True})], name=name)
            self.p.drivers.children.append(el)
            self.c.by[name] = el
            self.driver_of[name] = (item, prop)
            tr = self.c.track(name, "propertyValue")
            tr.keys[0]["v"] = float(v0) if kind == "number" else v0
        return name

    def _key(self, t, item, prop, value):
        name = self._driver(item, prop)
        kind = item.vm.kind(prop)
        if kind == "artboard":
            value = kit.icon_ref(value)
        self.c.set(t, name, "propertyValue", float(value) if kind == "number" else value)

    def state_at(self, item, prop, t):
        name = f"drv.{item.key}.{prop}"
        if name in self.driver_of:
            return self.c.tracks[(name, "propertyValue")].value_at(frame(t))
        return item.value(prop)

    def set(self, item, t=None, **props):
        """Set component properties at t (a key on each one's driver): a.set(email, error=True)."""
        t = self._t(t)
        for k, v in props.items():
            self._key(t, item, k, v)
        self._note(t, f"set {item.key} {props}")
        return t

    def key(self, item, prop, value, t=None, dur=0, ease="duda"):
        """A key of your own on an element (a placed item, or the name of one of your elements): prop "opacity", "x",
        "y", "scaleX", "scaleY", "rotation", "width"... dur 0 sets it at t; dur > 0 moves to it (ease: a motion
        token curve: duda, settle, strong, linear...). A component's own states go through set(). Returns the end."""
        t, dur = self._t(t), secs(dur)
        n = item if isinstance(item, str) else _el(item).name
        if dur:
            self.c.move(t, n, prop, float(value), dur, ease)
        else:
            self.c.set(t, n, prop, float(value))
        self._note(t + dur, f"key {n}.{prop} {value:g}")
        return t + dur

    # ------------------------------------------------------------ collapsibles
    def open(self, coll, t=None, dur="medium"):
        """Unfolds a p.collapsible(): the body opens to its full height while the chevron turns over (duda). Returns
        when it is open."""
        return self._fold(coll, True, t, dur)

    def close(self, coll, t=None, dur="medium"):
        """Folds a p.collapsible() (the reverse of open)."""
        return self._fold(coll, False, t, dur)

    def _is_open(self, coll, t):
        past = [o for ft, o in coll.folds if ft <= t]
        return past[-1] if past else coll.is_open

    def _fold(self, coll, opening, t, dur):
        t, dur = self._t(t), secs(dur)
        coll.folds.append((t, opening))
        h = self.p.bounds(coll.body, t)[3] if opening else 0.0
        self.c.move(t, coll.clip, "height", float(h), dur, "duda")
        self.c.move(t, coll.turn, "rotation", math.pi if opening else 0.0, dur, "duda")
        self._note(t + dur, f"{'open' if opening else 'close'} {coll.key}")
        return t + dur

    # ------------------------------------------------------------ elements: entrances and exits
    def enter(self, item, t=None, dy=8, dur=0.6, dx=0, scale=None, ease="settle"):
        """Arrive and settle: fades in while rising `dy` px into place (settle curve, it starts invisible).
        dx: it also comes `dx` px from the right (negative: from the left), a panel sliding in (dy=0).
        scale=0.96: it also grows to its size from its centre (a scale it already has, from p.free, is kept).
        ease: a curve token ("settle"; "duda_strong" for a panel)."""
        t, dur = self._t(t), secs(dur)
        el = _el(item)
        n = el.name
        op = self.c.track(n, "opacity")
        if len(op.keys) == 1:     # its first appearance: hidden until it enters
            op.keys[0]["v"] = 0.0
        gx = gy = 0.0
        if scale:
            for ax in ("scaleX", "scaleY"):
                s1 = float(el.attrs.get(ax) or 1.0)
                self.c.set(t, n, ax, s1 * scale)
                self.c.move(t + 1 / FPS, n, ax, s1, dur, ease)
            if not any(isinstance(c, El) and c.tag == "ComponentOrigin" for c in el.children):
                _, _, w, h = self.p.bounds(item, t)   # it grows from its top-left: its place moves with it
                gx, gy = (1 - scale) / 2 * w, (1 - scale) / 2 * h
        self.c.enter(t, n, dx=dx + gx, dy=dy + gy, dur=dur, ease=ease)
        self._note(t + dur, f"enter {n}")
        return t

    def stagger(self, items, t=None, step="list", dy=8, dur=0.6, dx=0, scale=None):
        """Several items entering one after another (step: "tight" 17 ms, "list" 67 ms, "loose" 83 ms, or s)."""
        t, dur = self._t(t), secs(dur)
        s = STEP.get(step, step)
        for i, it in enumerate(items):
            self.enter(it, t + i * s, dy, dur, dx, scale)
        return t

    def exit(self, item, t=None, dy=-6, dur=None):
        """Leaves: fades out (the fade token) while moving `dy` px."""
        t = self._t(t)
        n = _el(item).name
        dur = secs(dur) or kit.SHORT
        self.c.exit(t, n, dy=dy, dur=dur, fade=kit.FADE)
        self._note(t + dur, f"exit {n}")
        return t + dur

    # ------------------------------------------------------------ the cursor
    def cursor_in(self, side="right", t=None):
        """A cursor enters from off-frame (side: right, left, bottom, top), already moving, toward the next target.
        t=s: it sets off at s (and `now` moves to s, so the next click aims at where its target is by then).
        Without it, the first click brings one in from the right."""
        if t is not None:
            self.now = t
        return self._open_visit(side, t)

    def _open_visit(self, side, t):
        assert self.visit is None, "a cursor is already on screen (cursor_out first)"
        self.visit = {"name": f"CURSOR{len(self.visits) + 1}", "side": side, "enter": None, "points": [],
                      "leave": None, "start": self._t(t) if t is not None else None, "last": None}
        return self.now

    def _off(self, side, toward):
        x, y = toward
        W, H = self.p.w, self.p.h
        return {"right": (W + 70, min(H + 40, y + 140)), "left": (-70, min(H + 40, y + 140)),
                "bottom": (min(W + 40, x + 160), H + 70), "top": (min(W + 40, x + 120), -70)}[side]

    def _nearest_side(self, pt):
        x, y = pt
        d = {"right": self.p.w - x, "left": x, "bottom": self.p.h - y, "top": y}
        return min(d, key=d.get)

    def cursor_out(self, side=None, t=None):
        """The cursor leaves the frame right after its last action, accelerating (side: default the nearest).
        t=s: it creeps where it is until s, then leaves (it never parks dead still)."""
        v = self.visit
        if v is None:
            return self.now
        if t is not None:     # drift a few px off the control, then creep there until t
            lp = v["points"][-1]
            t0 = lp["t"] + (LEAD + 2 / FPS if lp.get("click") else 0) + lp.get("pause", 0)
            if t > t0 + 0.3:
                x, y = lp["at"]
                v["points"].append({"at": (round(x + 14, 2), round(y + 10, 2)), "t": round(t0 + 0.3, 4),
                                    "pause": round(t - t0 - 0.3, 4)})
        last = v["points"][-1]["at"]
        side = side or self._nearest_side(last)
        v["leave"] = {"right": (self.p.w + 80, last[1] + 120), "left": (-80, last[1] + 120),
                      "bottom": (last[0] + 120, self.p.h + 80), "top": (last[0] + 120, -80)}[side]
        self.visits.append(v)
        self.visit = None
        return self.now

    @staticmethod
    def _travel(a, b):
        return Visit.move_ms(type("V", (), {"tok": TOK["cursor"], "dpx": choreo.DPX})(), math.dist(a, b) * 1.03) / 1000

    def _go(self, at, t, click):
        """Add a cursor point (a click: t = press time; a pass: t = pass time). Returns the time used."""
        if self.visit is None:
            self._open_visit("right", None)
        v = self.visit
        if not v["points"]:
            start = v["start"] if v["start"] is not None else self.now
            v["enter"] = self._off(v["side"], at)
            natural = start + self._travel(v["enter"], at) - (LEAD if click else 0)
            t = natural if t is None else max(t, natural - 0.1)
        else:
            prev = v["points"][-1]
            depart = prev["t"] + (LEAD + 2 / FPS if prev.get("click") else 0) + prev.get("pause", 0)
            travel = self._travel(prev["at"], at)
            natural = max(depart, self.now) + travel - (LEAD if click else 0)
            if t is None:
                t = natural
            gap = t - (depart + travel - (LEAD if click else 0))
            if gap > 0.6:
                if prev.get("click") and click and gap <= 1.4:
                    v["points"].append({"aside": True})     # waits aside: drifts off and swoops back
                else:   # a long wait: it leaves, and a cursor comes back for this
                    self.cursor_out()
                    side = self._nearest_side(at)
                    self._open_visit(side, t - self._travel(self._off(side, at), at) + (LEAD if click else 0))
                    return self._go(at, t, click)
            t = max(t, depart + 0.7 * travel - (LEAD if click else 0))
        pt = {"at": (round(at[0], 2), round(at[1], 2)), "t": round(t, 4)}
        if click:
            pt["click"] = True
        v["points"].append(pt)
        return t

    # ------------------------------------------------------------ interactions
    def _reacts(self, item, t, press=True):
        """The control's reaction to a press at t: hover before it, the press, and its own result."""
        if item.kind == "part" and item.parent.kind == "aipanel":
            return self._panel_reacts(item, t)
        vm = item.vm
        props = {n for n, _, _ in vm.props} if vm else set()
        if "hover" in props:
            self._key(t - HOVER_LEAD, item, "hover", True)
        if press and "pressed" in props:
            self._key(t, item, "pressed", True)
            self._key(t + kit.PRESS, item, "pressed", False)
        if self.focus is not None and self.focus is not item:     # a press anywhere else blurs the field
            self._key(t, self.focus, "focused", False)
            self.focus = None
        if item.kind in ("input", "search", "textarea"):
            self._key(t, item, "focused", True)
            self.focus = item
        elif item.kind == "toggle":          # a selection control changes on the press frame
            self._key(t, item, "on", not self.state_at(item, "on", t))
        elif item.kind == "checkbox":
            self._key(t, item, "state", 0 if self.state_at(item, "state", t) == 1 else 1)
        elif item.kind == "radio":
            self._key(t, item, "selected", True)
        elif item.kind == "tab":
            self._key(t, item.parent, "selected", item.index)
        elif item.kind == "dropdown":
            self._key(t, item, "open", not self.state_at(item, "open", t))
        elif getattr(item, "coll", None) is not None:     # a collapsible's header folds or unfolds it
            self._fold(item.coll, not self._is_open(item.coll, t), t, "medium")

    def _panel_reacts(self, part, t):
        """A press on an AiPanel control: its hover, then the field takes the focus or send sends (stage 1: the
        field keeps the focus, as in the product)."""
        pan = part.parent
        if part.hover:
            self._key(t - HOVER_LEAD, pan, part.hover, True)
        if self.focus is not None and self.focus is not pan:
            self._key(t, self.focus, "focused", False)
            self.focus = None
        if part.pname == "field":
            self._key(t, pan, "focused", True)
            self.focus = pan
        elif part.pname == "send":
            self._key(t, pan, "stage", 1)

    def _unhover(self, item, t):
        if item.kind == "part" and getattr(item, "hover", None):
            self._key(t, item.parent, item.hover, False)
        elif item.vm and "hover" in {n for n, _, _ in item.vm.props}:
            self._key(t, item, "hover", False)

    def _aim(self, item, where, tp, click, at=None):
        """Go to `item` (or the absolute point `at`): the point is read at the frame the cursor gets there, since
        its target may be moving then (a panel sliding in, a row pushed down). Without t, a dry run of the path
        finds that frame (up to 3 passes). Returns (point, time)."""
        if at is not None:
            return at, self._go(at, tp, click)
        at = self.p.point(item, where, self.now if tp is None else tp)
        if tp is None:
            for _ in range(3):
                vis, n = self.visit, len(self.visits)
                saved = (dict(vis), list(vis["points"])) if vis else None
                t = self._go(at, None, click)
                if vis is not None:     # undo the dry run
                    vis.update(saved[0])
                    vis["points"][:] = saved[1]
                del self.visits[n:]
                self.visit = vis
                at2 = self.p.point(item, where, t)
                if math.dist(at, at2) < 0.5:
                    break
                at = at2
        return at, self._go(at, tp, click)

    def click(self, item=None, t=None, where=None, loading=None, at=None):
        """The cursor goes to `item` and clicks it: hover ~150 ms before, the press on the press frame (scale 0.96 /
        0.9 from the component), the cursor's own press, the result on the press frame (an input takes the focus).
        It aims at where `item` is on that frame. at=(x, y): a click on that point of the board instead (no item,
        or an item whose reaction it triggers there). loading=s: the button shows its spinner from the press for
        s seconds. Returns the press time."""
        assert item is not None or at is not None, "click what? (an item, or at=(x, y))"
        tp = self._t(t) if t is not None else None
        _, t = self._aim(item, where, tp, True, at)
        if item is not None:
            self._reacts(item, t)
        depart = t + LEAD + 2 / FPS
        if item is not None:
            self._unhover(item, depart + 0.1)
        self.visit["last"] = (item, t, where)
        self._note(t, f"click {item.key if item is not None else at}")
        self.now = depart
        loading = secs(loading)
        if loading:
            self._key(t, item, "loading", True)
            self._key(t + loading, item, "loading", False)
            self._note(t + loading, f"loading {item.key} {loading:g}s")
            self.now = t + loading
        return t

    def move_to(self, item=None, t=None, where=None, hold=0.0, at=None):
        """The cursor passes over `item` (no click), where it is by then; hold=s: it lingers there softly (a
        "thought"), hovering it. at=(x, y): a point of the board instead."""
        assert item is not None or at is not None, "move to what? (an item, or at=(x, y))"
        tp = self._t(t) if t is not None else None
        hold = secs(hold)
        _, t = self._aim(item, where, tp, False, at)
        if hold:
            self.visit["points"][-1]["pause"] = hold
        if item is not None and item.kind == "part" and getattr(item, "hover", None):
            self._key(max(0.0, t - 0.1), item.parent, item.hover, True)
            self._key(t + hold + 0.15, item.parent, item.hover, False)
        elif item is not None and item.vm and "hover" in {n for n, _, _ in item.vm.props}:
            self._key(max(0.0, t - 0.1), item, "hover", True)
            self._key(t + hold + 0.15, item, "hover", False)
        self._note(t, f"move to {item.key if item is not None else at}")
        self.now = t + hold
        return t

    def hover(self, item, hold=0.6, t=None, where=None):
        """move_to with a soft linger: the control shows its hover while the cursor creeps over it."""
        return self.move_to(item, t, where, hold)

    def type_into(self, item, text, then=None, then_where=None, cps=None, replace=False):
        """Duda's typing pattern. The cursor has just clicked `item` (it clicks it first if not); typing starts
        150 ms after that click, and the cursor drifts aside on one arc and swoops to `then`, clicking it as the last
        character lands (then_where: where on it, as in click). Without `then` the cursor leaves while the text is
        typed. An input, a search or a text area (its lines wrap). replace=True: the field already holds a text
        (placed, or typed before); it is selected and the new text types over it. An AiPanel: its field (the text
        becomes the panel's prompt). Returns when the text is done."""
        assert item.kind in ("input", "search", "textarea", "aipanel")
        panel = item.kind == "aipanel"
        target = item.part("field") if panel else item
        v = self.visit
        if not (v and v["last"] and v["last"][0] is target and v["points"][-1].get("click")):
            self.click(target, where="field" if item.kind == "input" else None)
        t0 = self.visit["last"][1]
        start = t0 + 0.15
        n = len(text)
        if then is not None:
            natural = start + n / (cps or 16)
            t1 = min(max(natural, t0 + 1.45), t0 + 2.1)        # the pattern's window (reference x1 to x1.45)
            at = self.p.point(then, then_where, t1)
            self.visit["points"] += [{"aside": True}, {"at": (round(at[0], 2), round(at[1], 2)), "t": t1, "click": True}]
            tp = t1
            self._reacts(then, tp)
            self._unhover(then, tp + LEAD + 2 / FPS + 0.1)
            self.visit["last"] = (then, tp, then_where)
            until = tp
            self.now = tp + LEAD + 2 / FPS
            self._note(tp, f"click {then.key}")
        else:
            self.cursor_out()
            until = start + n / (cps or 14)
            self.now = until
        if panel:   # the panel's field: `prompt` up to `typed`, the caret after the last letter
            assert not replace, "the panel's field types once (a follow-up: a.set(panel, prompt=..., typed=0))"
            item.inst[2]["prompt"] = text
            item.inst[2]["typed"] = 0
        cur = None if panel else self.state_at(item, "value", start)
        if panel:
            pass
        elif replace and cur:     # the old text goes on the first keystroke (it was selected), the new one types in
            self._key(start, item, "value", text)
            self._key(start, item, "typed", 0)
        else:   # the value is the text from the start; `typed` shows it one character at a time (human jitter)
            assert cur in ("", text), f"{item.key} already holds {cur!r} (replace=True types over it)"
            assert f"drv.{item.key}.typed" not in self.driver_of, f"{item.key} is typed into twice (replace=True)"
            item.inst[2]["value"] = text
            item.inst[2]["typed"] = 0
        rnd = random.Random(sum(map(ord, text)))
        jit = [rnd.uniform(0.6, 1.4) + (0.6 if ch in ",.:;" else 0) for ch in text]
        k = (until - start) / sum(jit)
        tt = start
        for i in range(n):
            tt += jit[i] * k
            self._key(min(tt, until), item, "typed", i + 1)
        if not panel:
            self._key(until + 2 / FPS, item, "typed", TYPED_ALL + 1)
        self._note(until, f"typed {text!r} into {item.key}")
        return until

    def remove(self, tag, t=None):
        """The cursor clicks a tag's x: the tag fades and shrinks a little on the press, then the row closes the gap
        smoothly (one state at a time; no jump). Returns when the row has settled."""
        assert tag.kind == "tag"
        v = self.visit
        if v and v["last"] and v["last"][0] is tag and v["last"][2] == "remove" and t is None:
            tp = v["last"][1]       # the cursor has just pressed its x (type_into ... then_where="remove")
        else:
            tp = self.click(tag, t, where="remove")
        self._key(tp - HOVER_LEAD, tag, "removeHover", True)
        n = tag.wrap.name
        x, y, w, h = self.p.bounds(tag, tp)
        par = self.p._parent_of(tag.wrap)
        pst = next(c for c in par.children if c.tag == "LayoutComponentStyle")
        gap = pst.attrs.get("gapHorizontal", 0) or 0
        # the wrapper holds the tag's measured width from the start, so the width can close
        st = next(c for c in tag.wrap.children if c.tag == "LayoutComponentStyle")
        st.attrs["layoutWidthScaleType"] = "fixed"
        tag.wrap.attrs["width"] = w
        self.c.track(n, "width").keys[0]["v"] = float(w)
        self.c.fade(tp, n, 0.0, SWAP)
        for ax in ("scaleX", "scaleY"):
            self.c.move(tp, n, ax, 0.92, SWAP, "duda")
        t1 = tp + SWAP
        dur = kit.SHORT
        peak = Visit_peak(choreo.ease_curve("duda"))
        cap = TOK["speed_cap_px_per_frame_at_1920"]["text_content"]
        while (w + gap) * peak / (dur * FPS) * choreo.OUT_SCALE > cap:
            dur += 1 / FPS
        self.c.move(t1, n, "width", 0.0, dur, "duda")
        mr = self.c.track(f"{n}.style", "marginRight")
        mr.keys[0]["v"] = 0.0
        self.c.move(t1, f"{n}.style", "marginRight", -float(gap), dur, "duda")
        t2 = t1 + dur + 1 / FPS
        disp = self.c.track(f"{n}.style", "displayValue")
        disp.keys[0]["v"] = 0
        self.c.set(t2, f"{n}.style", "displayValue", 1)
        self.c.set(t2, f"{n}.style", "marginRight", 0.0)
        self._key(t1, tag, "hover", False)
        self._key(t1, tag, "removeHover", False)
        self._note(t2, f"removed {tag.key} (row closes {w + gap:.0f} px in {dur:.2f} s)")
        return t2

    def message(self, item, text, kind=None, t=None):
        """An input's message under the field (kind: None info, "error", "success", "warning"). A message already
        shown leaves first (0.1 s), the new one arrives after: one state at a time. Returns when it is shown."""
        t = self._t(t)
        if self.state_at(item, "showMessage", t):
            self._key(t, item, "showMessage", False)
            t += SWAP + 1 / FPS
        flags = {"error": kind == "error", "success": kind == "success", "warning": kind == "warning"}
        for k, v in flags.items():
            if self.state_at(item, k, t) != v or v:
                self._key(t, item, k, v)
        self._key(t, item, "message", text)
        self._key(t, item, "showMessage", True)
        self.messages.append((item, t))
        self._note(t, f"message {item.key} {kind or 'info'}: {text!r}")
        self.now = t
        return t

    # ------------------------------------------------------------ the loop
    def loop(self, exit=None, hold=None):
        """End the loop cleanly: `exit` (the card or panel that entered at the start) leaves, everything goes back to
        its first frame while it is hidden, and >= 8 still frames close the loop. Call it last. Whatever changed
        outside `exit` would jump back on screen: the build fails it."""
        hold = 8 / FPS if hold is None else secs(hold)
        if self.visit is not None:
            self.cursor_out()
        t = max(self.now, self._cursor_end())
        if exit is not None:
            n = _el(exit).name
            assert self.c.track(n, "opacity").keys[0]["v"] == 0.0, f"{n} must enter at the start (a.enter) to exit"
            t = self.exit(exit, t)
        self.loop_exit = _el(exit) if exit is not None else None
        self.reset_at = t + 1 / FPS
        self.now = self.reset_at + hold
        self.looped = True
        return self.now

    def _cursor_end(self):
        end = 0.0
        for v in self.visits:
            last = v["points"][-1]
            end = max(end, last["t"] + last.get("pause", 0) + 1.2)
        return end

    # ------------------------------------------------------------ build
    def _finish(self, tabs, duration=None):
        if self.visit is not None:
            self.cursor_out()
        c = self.c
        for v in self.visits:     # the cursors: a Follow Path each, riding it a nested library Cursor
            name = v["name"]
            geo = Visit(name, v["enter"], copy.deepcopy(v["points"]), v["leave"], choreo.PT)
            follow = El("FollowPathConstraint", {"targetId": f"@{name}.path", "orient": False}, name=f"{name}.follow")
            nest = El("NestedArtboard", {"artboardId": "@art.cursor", "dataBindPathIds": (
                f"vm.{self.p.key}", f"vm.{self.p.key}.cursor")}, [El("NestedStateMachine", {
                    "animationId": "@sm.cursor"}, name=f"{name}.machine")], name=f"{name}.art")
            node = El("Node", {"x": 0, "y": 0, "opacity": 0, "scaleX": self.p.cursor_scale,
                               "scaleY": self.p.cursor_scale}, [nest, follow], name=name)
            shape = geo.path_shape()
            self.p.overlay.children[:0] = [node]
            self.p.overlay.children.append(shape)
            for e in (node, shape):
                c.parent[id(e)] = self.p.overlay
                kit.walk(e, lambda x: c.by.__setitem__(x.name, x) if x.name else None)
            c.cursor_visit(name, v["enter"], copy.deepcopy(v["points"]), v["leave"])
            self.end = max(self.end, c.visits[name].t_out or 0)
        dur = max(self.now, self.end) if self.looped else max(self.now, self.end) + 0.5
        if self.looped and self.end > self.reset_at:
            raise ValueError(f"something still happens at {self.end:.2f}s, after the loop's exit ({self.reset_at:.2f}s)")
        if duration is not None:    # exactly that long (a hero tab: tabChange right at its end)
            last = max(self.now, self.end)
            if last > secs(duration) + 1e-6:
                raise ValueError(f"build(duration={secs(duration):g}): the actions run until {last:.2f}s")
            dur = secs(duration)
        self._close_statuses(dur)
        c.duration, c.F = dur, frame(dur)
        c._samples = None
        late = sorted({n for (n, _), tr in c.tracks.items() if any(k["f"] > c.F for k in tr.keys)})
        if late:
            self.issues.append(f"keys after the end ({dur:.2f}s): {', '.join(late[:6])}"
                               f"{' ...' if len(late) > 6 else ''} (they never play)")
        if self.looped:   # back to the first frame while hidden
            fr = frame(self.reset_at)
            hidden = set()
            if self.loop_exit is not None:
                kit.walk(self.loop_exit, lambda e: hidden.add(e.name) if e.name else None)
            jumps = []
            for (n, p), tr in c.tracks.items():
                if tr.value_at(fr) != tr.keys[0]["v"] and not any(k["f"] > fr for k in tr.keys):
                    tr.set(fr, tr.keys[0]["v"])
                    if n in self.driver_of:
                        it = self.driver_of[n][0]
                        n = (it.parent if it.kind == "part" else it).wrap.name
                    if n not in hidden and not n.startswith("CURSOR"):
                        jumps.append(f"{n}.{p}" if not n.startswith(self.p.art) else n)
            if jumps:
                self.issues.append(f"loop: {', '.join(sorted(set(jumps)))} jump back to the first frame on screen; "
                                   f"loop(exit=...) the card or panel that holds them (it must enter at the start)")

    def _report(self, tabs):
        c = self.c
        report, issues = c.lint()
        issues += self.issues
        if not tabs:
            issues += [f"loop: {b}" for b in c.check_loop()]
        for item, t in self.messages:     # a message the viewer must read stays >= 1 s
            tr = c.tracks[(f"drv.{item.key}.showMessage", "propertyValue")]
            off = next((k["f"] / FPS for k in tr.keys if k["f"] > frame(t) and not k["v"]), c.F / FPS)
            if off - t < 1.0 - 1e-6 and off < c.F / FPS:
                issues.append(f"message on {item.key} at {t:.2f}s is shown only {off - t:.2f}s (reading: >= 1 s)")
        print("timeline:")
        for t, what in sorted(self.log, key=lambda x: x[0]):
            print(f"  {t:6.2f}s  {what}")
        for line in c.log:
            print("  ", line)
        print("speed lint (px/frame, cap):")
        for n, kind, peak, cap, at in sorted(report, key=lambda r: -r[2] / r[3])[:8]:
            print(f"   {'OVER' if peak > cap + 0.5 else 'ok  '} {peak:6.1f}/{cap:<3} {kind:8s} {n} @ {at / FPS:.2f}s")
        for i in issues:
            print("LINT:", i)
        return issues


def Visit_peak(e):
    """Peak speed of a normalised ease, as a multiple of its mean."""
    best, prev = 0.0, 0.0
    for j in range(1, 401):
        v = progress(e, j / 400)
        best = max(best, (v - prev) * 400)
        prev = v
    return best
