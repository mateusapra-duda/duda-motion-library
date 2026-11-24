"""v15b: the email editor's parts, and the interactive card.

Measured on the "Pick a template" and "Recolor the button" storyboard frames, which draw the product at 0.81. The
values here are at product size.

  p.template_card(name, label, image=None, w=308, live=False)
        A template in the gallery: its thumbnail on #F4F4F4 and its name.
        - Its hover lights when the cursor's tip enters the card, also on the way to the card's own buttons: a dark
          veil and "..." fade in (0.15 s), and Use This / Preview rise 6 px in 0.5 s.
        - card.use and card.preview are the two CoreButtons, e.g. a.click(card.use).
  p.block_panel(name, title, kids, w=266, h=None)
        The editor's side panel for one block: the header (back arrow and title, e.g. "BUTTON BLOCK") over a
        hairline, then the body.
        - kids are items or strings: "# Button style" is a section title, "Link" a field's label, "---" a divider.
        - Two fields side by side: p.row([...], gap=12, w="fill").
  p.panel_field(name, value, unit=None, icon=None, chevron=False, w="fill", label=None)
        A field of the panel (#F4F4F5): its value, a unit at the right ("px"), an icon before it, a chevron for a
        select. label= puts a label above it, both in a column (the panel's "Padding top" pair).
  p.segmented(name, options, selected=0, w="fill")
        The panel's switch (Fit to text | Full width). a.click(seg.options[i]) selects option i on the press.
  p.color_field(name, value, picker=None, w=113.5)
        The colour field: a swatch and the HEX.
        - A press focuses it (blue edge) and opens `picker` on the release (8 f after the press).
  p.color_picker(name, colors, value=None, label="IN THIS EMAIL")
        The picker: saturation and hue with their handles, HEX, a divider and the swatches of `colors`.
        - It stays hidden until its field opens it, or until a.enter(picker).
        - value: the colour it shows (default the field's). The swatch of that colour has the blue ring.
  a.pick_color(picker, color, t=None, targets=())
        The cursor clicks the swatch of `color` (its index in `colors`, or '#rrggbb').
        - On arrival: the swatch's edge darkens.
        - On the press: the swatch dips (0.9, back in 0.333 s) and the ring moves to it.
        - Also on the press, over 0.333 s: HEX and the handles go to the new colour, and so do the field that opened
          the picker and each of `targets` (an item drawn with a fill of its own, e.g. the email's button).
        - a.click(swatch) does the same: picker.swatches[i].

The interactive card (v15b): p.template_card(..., live=True), or p.hoverable(item, ..., live=True).
  - The visitor's own mouse lights the hover, through listeners on MAIN's state machine. There is no fake cursor,
    and the timeline doesn't key the hover.
  - MAIN's view model gets `<name>Hover` (a boolean) and `<name>Click` (a trigger fired on a click, for the page to
    listen to).
  - A live card's buttons are interactive: they have their own hover and press, and fire their own `clicked`.
  - Call it before p.actions().
"""
import colorsys

import kit
from kit import El
from common import FPS, Item, _el, _color
import hand

INK, GREY, HINT, LINE, BLUE = "#272B35", "#5D6068", "#A0A3AA", "#E4E4E7", "#3B82F6"
FIELD, FIELD_EDGE, SWATCH_EDGE = "#F4F4F5", "#DADADF", "#E4E4E7"
VEIL = "#3A3D45C7"
SAT_W, SAT_H, HUE_W = 176, 124, 10
HUES = ("#FF0000", "#FFFF00", "#00FF00", "#00FFFF", "#0000FF", "#FF00FF", "#FF0000")
PICK_MS = 0.333          # the swatch's way back, the handles, the fields turning: the storyboard piece's 20 frames


def _hsv(hexc):
    r, g, b = (int(hexc.lstrip("#")[i:i + 2], 16) / 255 for i in (0, 2, 4))
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    return h * 360, s, v


def _pure(h):
    r, g, b = colorsys.hsv_to_rgb(h / 360, 1, 1)
    return "#%02X%02X%02X" % (round(r * 255), round(g * 255), round(b * 255))


def _sat_xy(hexc):
    _, s, v = _hsv(hexc)
    return round(s * SAT_W, 3), round((1 - v) * SAT_H, 3)


def _hue_y(hexc):
    h, s, _ = _hsv(hexc)
    return round(min(SAT_H - 6, max(6, h / 360 * SAT_H)), 3)


class EditorPatterns:
    # ------------------------------------------------------------ small parts
    def _ebox(self, name, kids=(), w="hug", h="hug", fill=None, stroke=None, sw=1.0, r=0, pad=0, gap=0, d="row",
              align="centerLeft", clip=False, ring=None, origin=None):
        """A box as Figma's auto layout draws it: a fill, a border inside it (it takes room: the padding grows by its
        width), a radius. ring=(colour, width): a second inside edge, hidden (a swatch's selection)."""
        n = f"{self.art}.{name}"
        pads = list(pad) if isinstance(pad, (tuple, list)) else [pad] * 4
        if len(pads) == 2:                    # (horizontal, vertical)
            pads = pads * 2
        edges = []
        for tag, col, wd, hide in ([("edge", stroke, sw, False)] if stroke else []) + \
                                  ([("ring", ring[0], ring[1], True)] if ring else []):
            edges.append(kit.absolute(f"{n}.{tag}", paints=[kit.line(f"{n}.{tag}.s", _color(col), wd)],
                                      inset=(wd / 2,) * 4, opacity=0.0 if hide else None,
                                      cornerRadiusTL=max(0.0, r - wd / 2) or None))
        if stroke:
            pads = [v + sw for v in pads]
        st = {}
        if r:
            st["cornerRadiusTL"] = r
        if origin:
            st["origin"] = origin
        paints = [kit.solid(f"{n}.fill", _color(fill))] if fill else []
        return self._box(name, edges[::-1] + list(kids), d, gap, tuple(pads), align, w, h, paints=paints, clip=clip,
                         **st)

    def _etext(self, name, s, size, weight=350, color=INK, ls=None):
        return self.text(name, s, style=None, font="duda", size=size, lh=round(size * 1.35, 3), weight=weight,
                         color=color, ls=ls)

    def _eicon(self, name, icon, size, color=INK):
        el = kit.icon_slot(f"{self.art}.{name}", icon, _color(color), size=size)
        item = Item(self, name, "icon", el)
        self.items[name] = item
        return item

    # ------------------------------------------------------------ the gallery
    def template_card(self, name, label, image=None, w=308, thumb=(259.17, 436), live=False):
        """A template of the email gallery (module doc). image: the thumbnail (a file in the piece folder), drawn
        `thumb` big, 20 px from the top, centred, aligned to its top. Returns the card (card.use, card.preview)."""
        aw, ah = w - 2, 456
        kids = [(self._ebox(f"{name}Bg", w=aw, h=ah, fill="#F4F4F4"), 0, 0)]
        if image:
            kids.append((self.image(f"{name}Img", image, thumb[0], thumb[1], align=(0.5, 0.0)),
                         round((aw - thumb[0]) / 2, 2), 20))
        btn = {"interactive": True} if live else {}
        use = self.button(f"{name}Use", label="Use This", variant=0, color=0, size=1, minWidth=140, **btn)
        prev = self.button(f"{name}Preview", label="Preview", variant=1, color=0, size=1, minWidth=140, **btn)
        veil = self.free(f"{name}Veil", [(self._ebox(f"{name}VeilBg", w=aw, h=ah, fill=VEIL), 0, 0),
                                         (self._eicon(f"{name}More", "automation/i_more", 16, "#FFFFFF"),
                                          aw - 16 - 16, 16)], aw, ah, clip=False)
        btns = self.free(f"{name}Btns", [(use, 0, 0), (prev, 0, 40)], 140, 72, clip=False)
        kids += [(veil, 0, 0), (btns, round((aw - 140) / 2, 2), round((ah - 72) / 2, 2))]
        area = self.free(f"{name}Area", kids, aw, ah, clip=True)
        foot = self._ebox(f"{name}Foot", [self._etext(f"{name}Label", label, 15, 550)], w="fill",
                          pad=(16, 16, 16, 18))
        card = self._ebox(name, [area, foot], w=w, d="column", align="topLeft", fill="#FFFFFF", stroke="#E8E8EB",
                          r=8, clip=True)
        card.kind = "templatecard"
        card.use, card.preview = use, prev
        self.hoverable(card, show=[veil], rise=[btns], fade=0.15, live=live)
        return card

    # ------------------------------------------------------------ the side panel
    def panel_field(self, name, value, unit=None, icon=None, chevron=False, w="fill", label=None):
        """A field of the block panel (module doc). icon: a DS icon ("common_actions/i_expand") before the value."""
        kids = []
        if icon:
            kids.append(self._eicon(f"{name}Icon", icon, 14))
        kids.append(self._etext(f"{name}Value", value, 13))
        if unit or chevron:
            kids.append(self._box(f"{name}Sp", [], "row", 0, 0, "centerLeft", "fill", 1))
        if unit:
            kids.append(self._etext(f"{name}Unit", unit, 11, color=HINT))
        if chevron:
            kids.append(self._eicon(f"{name}Chevron", "arrows/chevron_bottom", 12))
        fld = self._ebox(name if label is None else f"{name}Box", kids, w=w if label is None else "fill", fill=FIELD,
                         r=4, pad=8, gap=8)
        fld.value = self.items[f"{name}Value"]
        if label is None:
            return fld
        col = self._ebox(name, [self._etext(f"{name}Label", label, 13), fld], w=w, d="column", gap=6,
                         align="topLeft")
        col.value, col.field = fld.value, fld
        return col

    def segmented(self, name, options, selected=0, w="fill"):
        """The panel's switch (module doc): a #EDEDF0 track, the selected option white."""
        opts = []
        for i, s in enumerate(options):
            on = i == selected
            o = self._ebox(f"{name}Opt{i}", [self._etext(f"{name}Opt{i}T", s, 13, color=INK if on else GREY)],
                           w="fill", r=6, pad=(0, 7), align="center")
            n = _el(o).name
            _el(o).children.append(kit.absolute(f"{n}.on", paints=[kit.solid(f"{n}.on.f", _color("#FFFFFF"))],
                                                opacity=1.0 if on else 0.0, cornerRadiusTL=6))   # last: under the text
            o.kind, o.index = "segment", i
            o.react = (lambda k: lambda a, t: a._segment(k, t))(o)
            opts.append(o)
        seg = self._ebox(name, opts, w=w, fill="#EDEDF0", r=8, pad=3, align="topLeft")
        for o in opts:
            o.seg = seg
        seg.options, seg.selected = opts, selected
        return seg

    def block_panel(self, name, title, kids, w=266, h=None):
        """The side panel of a block (module doc): white, a hairline on its right."""
        head = self._ebox(f"{name}Head", [
            self._ebox(f"{name}HeadRow", [self._eicon(f"{name}Back", "arrows/i_arrow_left", 14, GREY),
                                          self._etext(f"{name}Title", title.upper(), 11, 700, GREY, ls=0.44)],
                       w="fill", pad=(14, 16), gap=8),
            self._ebox(f"{name}HeadLine", w="fill", h=1, fill=LINE)], w="fill", d="column", align="topLeft")
        body = []
        for i, k in enumerate(kids):
            if isinstance(k, str) and k == "---":
                body.append(self._ebox(f"{name}Div{i}", w="fill", h=1, fill=LINE))
            elif isinstance(k, str) and k.startswith("# "):
                body.append(self._etext(f"{name}H{i}", k[2:], 15, 700))
            elif isinstance(k, str):
                body.append(self._etext(f"{name}L{i}", k, 13))
            else:
                body.append(k)
        body = self._ebox(f"{name}Body", body, w="fill", d="column", pad=(14, 13.5, 14, 16), gap=10, align="topLeft")
        n = f"{self.art}.{name}"
        line = kit.absolute(f"{n}.rule", paints=[kit.solid(f"{n}.rule.f", _color(LINE))], inset=(None, 0, 0, 0), w=1,
                            layoutWidthScaleType="fixed")
        return self._ebox(name, [line, head, body], w=w, h="hug" if h is None else h, d="column", fill="#FFFFFF",
                          pad=(0, 0, 1, 0), align="topLeft")

    # ------------------------------------------------------------ the colour field and picker
    def color_field(self, name, value, picker=None, w=113.5):
        """The panel's colour field (module doc)."""
        sw = self._ebox(f"{name}Swatch", w=18, h=18, fill=value, stroke=FIELD_EDGE, r=3)
        fld = self._ebox(name, [sw, self._etext(f"{name}Hex", value.upper(), 13)], w=w, fill=FIELD, stroke=FIELD_EDGE,
                         r=4, pad=8, gap=8)
        fld.kind, fld.swatch, fld.hex, fld.picker = "colorfield", sw, self.items[f"{name}Hex"], None
        fld.react = lambda a, t: a._color_field(fld, t)
        if picker is not None:
            self.link_picker(fld, picker)
        return fld

    def link_picker(self, field, picker):
        """The field opens the picker, and a pick turns the field (p.color_field(picker=) does it)."""
        field.picker, picker.field = picker, field

    def color_picker(self, name, colors, value=None, label="IN THIS EMAIL"):
        """The colour picker (module doc). colors: '#rrggbb' each; value: the colour shown (default the first)."""
        colors = [c.upper() for c in colors]
        value = (value or colors[0]).upper()
        n = f"{self.art}.{name}"
        sx, sy = _sat_xy(value)
        hdl = kit.shape_ellipse(f"{n}.satH", 8, stroke=_color("#FFFFFF"), stroke_w=2, x=sx, y=sy)
        hw = self.wrap(f"{name}SatHandle", [hdl], w=SAT_W, h=SAT_H)
        grad = kit.box(f"{n}.satBg", [
            kit.absolute(f"{n}.satDark", paints=self._paint(f"{n}.satDark.f", ("#00000000", "#000000"), SAT_W, SAT_H)),
            kit.absolute(f"{n}.satLight", paints=self._paint(f"{n}.satLight.f", ("#FFFFFF", "#FFFFFF00", "right"),
                                                             SAT_W, SAT_H))],
            w=SAT_W, h=SAT_H, paints=[kit.solid(f"{n}.satHue", _color(_pure(_hsv(value)[0])))], clip=True,
            cornerRadiusTL=3, layoutWidthScaleType="fixed", layoutHeightScaleType="fixed")
        sat = kit.box(f"{n}.sat", [kit.absolute(f"{n}.satAt", [_el(hw)], inset=(0, 0, None, None), layoutWidthScaleType="hug",
                                                layoutHeightScaleType="hug"), grad], w=SAT_W,
                      h=SAT_H, layoutWidthScaleType="fixed", layoutHeightScaleType="fixed")
        hh = kit.shape_ellipse(f"{n}.hueH", 9.5, stroke=_color("#FFFFFF"), stroke_w=2.5, x=6, y=_hue_y(value))
        hhw = self.wrap(f"{name}HueHandle", [hh], w=HUE_W + 1, h=SAT_H)
        bar = kit.absolute(f"{n}.hueBar", paints=self._paint(f"{n}.hueBar.f", HUES, HUE_W, SAT_H),
                           inset=(1, 0, None, 0), w=HUE_W, layoutWidthScaleType="fixed", cornerRadiusTL=HUE_W / 2)
        hue = kit.box(f"{n}.hue", [kit.absolute(f"{n}.hueAt", [_el(hhw)], inset=(0, 0, None, None), layoutWidthScaleType="hug",
                                                layoutHeightScaleType="hug"), bar],
                      w=HUE_W + 1, h=SAT_H, layoutWidthScaleType="fixed", layoutHeightScaleType="fixed")
        top = self._box(f"{name}Top", [sat, hue], "row", 11, 0, "topLeft", "hug", "hug")
        hex_row = self._ebox(f"{name}HexRow", [
            self._ebox(f"{name}HexSel", [self._etext(f"{name}HexSelT", "HEX", 12),
                                         self._eicon(f"{name}HexC", "arrows/chevron_bottom", 12)],
                       stroke=FIELD_EDGE, r=4, pad=(8, 6, 6, 6), gap=12),
            self._ebox(f"{name}HexVal", [self._etext(f"{name}Hex", value.lower(), 12)], stroke=FIELD_EDGE, r=4,
                       pad=(8, 6))], gap=8, align="topLeft")
        swatches = []
        for i, c in enumerate(colors):
            s = self._ebox(f"{name}Sw{i}", w=22, h=22, fill=c, stroke=SWATCH_EDGE, r=4, ring=(BLUE, 2),
                           origin=(0.5, 0.5))
            if c == value:
                kit.walk(_el(s), lambda e: e.attrs.__setitem__("opacity", 1.0) if e.name == f"{n}Sw{i}.ring" else None)
            s.kind, s.index = "swatch", i
            self.hoverable(s, border=(HINT, 1), fade=0)
            s.hover_off = 0.25            # the edge goes back a moment after the press (the ring shows)
            swatches.append(s)
        pk = self.card(name, [top, hex_row, self._ebox(f"{name}Div", w=SAT_W + 11 + HUE_W + 1, h=1, fill=LINE),
                              self._etext(f"{name}Label", label.upper(), 10, 550, HINT, ls=0.4),
                              self._ebox(f"{name}Swatches", swatches, gap=6)],
                       w="hug", pad=17, gap=14, radius=8, shadow="shadow-3")
        _el(pk).attrs["opacity"] = 0.0
        pk.kind = "colorpicker"
        pk.colors, pk.swatches, pk.hex, pk.field = colors, swatches, self.items[f"{name}Hex"], None
        pk.sel = colors.index(value) if value in colors else None
        pk.color, pk.is_open = value, False
        pk.handles = (f"{n}.satH", f"{n}.hueH", f"{n}.satHue.color")
        for s in swatches:
            s.picker = pk
            s.react = (lambda k: lambda a, t: a._pick(k.picker, k.index, t))(s)
        return pk


class EditorActions:
    def _prune_rings(self):
        """A picker's swatch rings that never show aren't built (only the picked ones and the first one are)."""
        for pk in [it for it in self.p.items.values() if it.kind == "colorpicker"]:
            for sw in pk.swatches:
                el, ring = _el(sw), f"{_el(sw).name}.ring"
                kids = [k for k in el.children if isinstance(k, El) and k.name == ring]
                if kids and (ring, "opacity") not in self.c.tracks and not kids[0].attrs.get("opacity"):
                    el.children.remove(kids[0])

    def _color_field(self, fld, t):
        """A press on a colour field: its edge turns blue (the focus); its picker opens on the release."""
        self.c.set(t, f"{_el(fld).name}.edge.s.color", "colorValue", _color(BLUE))
        pk = fld.picker
        if pk is not None and not pk.is_open:
            pk.is_open = True
            tr = t + hand.RELEASE / FPS
            self.c.set(0, f"{_el(pk).name}.style", "displayValue", 1)      # off while hidden (it costs nothing)
            self.c.set(tr, f"{_el(pk).name}.style", "displayValue", 0)
            self.enter(pk, tr, dy=6, dur=0.5)

    def _segment(self, opt, t):
        """A press on a switch option: it turns white on the press, the one before goes back to the track."""
        seg = opt.seg
        old = seg.options[seg.selected]
        if old is opt:
            return
        for o, on in ((old, False), (opt, True)):
            self.c.set(t, f"{_el(o).name}.on", "opacity", 1.0 if on else 0.0)
            for col in self._paint_colors(self.p.items[f"{o.key}T"]):
                self.c.set(t, col, "colorValue", _color(INK if on else GREY))
        seg.selected = opt.index

    def pick_color(self, picker, color, t=None, targets=()):
        """The cursor picks a swatch of the picker (module doc). Returns the press time."""
        i = color if isinstance(color, int) else picker.colors.index(color.upper())
        picker.targets = list(targets)
        return self.click(picker.swatches[i], t=t)

    def _pick(self, pk, i, t):
        """A swatch pressed at t: the dip, the ring, HEX, the handles, the field and the targets."""
        sw, new = pk.swatches[i], pk.colors[i]
        n = _el(sw).name
        for ax in ("scaleX", "scaleY"):
            self.c.move(t, n, ax, 0.9, 0.05)
            self.c.move(t + 0.05, n, ax, 1.0, PICK_MS, "duda")
        if pk.sel is not None and pk.sel != i:
            self.c.set(t, f"{_el(pk.swatches[pk.sel]).name}.ring", "opacity", 0.0)
        self.c.set(t, f"{n}.ring", "opacity", 1.0)
        pk.sel = i
        self.text(pk.hex, new.lower(), t=t)
        sat_h, hue_h, sat_hue = pk.handles
        x, y = _sat_xy(new)
        self.c.move(t, sat_h, "x", x, PICK_MS, "duda")
        self.c.move(t, sat_h, "y", y, PICK_MS, "duda")
        if abs(_hsv(new)[0] - _hsv(pk.color)[0]) > 0.5 and _hsv(new)[1] > 0:
            self.c.move(t, hue_h, "y", _hue_y(new), PICK_MS, "duda")
            self.c.move(t, sat_hue, "colorValue", _color(_pure(_hsv(new)[0])), PICK_MS, "duda")
        fills = []
        if pk.field is not None:
            fills.append(f"{_el(pk.field.swatch).name}.fill.color")
            self.text(pk.field.hex, new.upper(), t=t)
        for it in getattr(pk, "targets", ()):
            el = _el(it)
            own = [c for c in el.children if isinstance(c, El) and c.tag == "Fill"]
            assert own, f"a.pick_color: {el.name} has no fill of its own to turn (targets: items drawn with a fill)"
            fills += [k.name for k in own[0].children if isinstance(k, El) and k.tag == "SolidColor"]
        for f in fills:
            self.c.move(t, f, "colorValue", _color(new), PICK_MS, "duda")
        pk.color = new
        self._note(t, f"pick {new}")
