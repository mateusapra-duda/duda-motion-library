"""v04: the hero pieces' patterns, built from the library and native text (no exports): the Quick Edits panel, the Code
tab (a code editor that writes itself, a file tree), the AI's "Generating... / Done" status, and the Generation
effect (hero_1's square, with hero-view's details). Piece and Actions take them in (piece.py): a piece still imports
only piece.py.

Measures: the Vibe page hero storyboards (Figma 305:12538) at product size (the storyboards draw the product at
0.81); the code editor's colours and stream, hero3-code v04; the Generation effect, hero_1 as hero-view / hero3-code
make it."""
import os
import random
import re

import kit
from kit import El
from common import FPS, SWAP, secs, Item, _el, _color
import choreo
from choreo import frame

# ---------------------------------------------------------------- the code editor
SYNTAX = {"k": "#0033BF", "f": "#785E26", "t": "#268099", "s": "#A31414", "p": "#1F1F24", "c": "#6A737D",
          "ln": "#3D4A73", "caret": "#0033BF"}   # hero3-code (the storyboard's editor); c: comments
KEYWORDS = set("import from export default function return const let var if else for while do switch case break "
               "continue new class extends async await try catch finally throw typeof instanceof in of true false "
               "null undefined this as type interface".split())
TOKEN = re.compile(r"(//.*$)|(\"(?:\\.|[^\"])*\"|'(?:\\.|[^'])*'|`(?:\\.|[^`])*`)|([A-Za-z_$][\w$]*)|(\s+)|(.)")
CARET = "▏"


def highlight(line):
    """A line of JS / JSX -> [(text, kind)]: k keyword, f function call, t a component's tag, s string, c comment,
    p the rest. Spaces join the run before them."""
    runs = []
    for m in TOKEN.finditer(line):
        com, s, word, sp, _ = m.groups()
        tok = m.group(0)
        if com:
            kind = "c"
        elif s:
            kind = "s"
        elif word:
            before = line[:m.start()].rstrip()
            if word in KEYWORDS:
                kind = "k"
            elif before.endswith(("<", "</")) and word[0].isupper():
                kind = "t"
            elif line[m.end():].lstrip().startswith("("):
                kind = "f"
            else:
                kind = "p"
        else:
            kind = runs[-1][1] if sp and runs else "p"
        if runs and runs[-1][1] == kind:
            runs[-1] = (runs[-1][0] + tok, kind)
        else:
            runs.append((tok, kind))
    return runs


def tokens(s):
    """AI-sized chunks: a word, or a run of up to 3 punctuation marks, each carrying the spaces before it."""
    toks = re.findall(r"\s*(?:\w+|[^\w\s]{1,3})", s)
    rest = s[len("".join(toks)):]
    return toks + ([rest] if rest else [])


# ---------------------------------------------------------------- the Generation effect (hero_1)
FX_STOPS = [("00DDF1F9", 0), ("FFDDF1F9", .162), ("FFE6D7F1", .336), ("FFF4BBD2", .503), ("FFF9A84A", .681),
            ("FFF0CE72", .848), ("00F0CE72", 1)]   # stop 2 turns from lavender to light blue during the sweep
SWEEP0 = {"startX": -535.6, "startY": -1582.6, "endX": -105.1, "endY": -234.8}
SWEEP1 = {"startX": 107.4, "startY": 213.6, "endX": 1831.9, "endY": 4515.4}
SWEEP_EASE = [0.42, 0.0, 0.58, 1.0]   # Rive's default cubic, as in hero_1
GEN = {   # frames from the start (hero_1: MINI CARDS / TOP FLAVORS); feathers in px
    "small": dict(sweep=84, s0=1.11, scale=(13, 44), feather=(18, 3, 13, 42), stop=(37, 84), show=(36, 8)),
    "big": dict(sweep=131, s0=1.03, scale=(23, 68), feather=(16, 0, 23, 68), stop=(58, 131), show=(56, 8)),
}
DETAILS = dict(rows=dict(step=0.083, rise=4, dur=0.5, fade=0.15),      # hero3-code v04 beats.yaml `details`
               pop=dict(lead=0.03, across=0.35, pink_at=0.12, pink_in=0.06, own_at=0.26, own_dur=0.12),
               blur=dict(px=3.0, dur=0.5), count=dict(dur=0.7, blur=3.0))
ORANGE, PINK = "FFF59A52", "FFD69BD6"   # Base44's text colours on the way in
SHIMMER_S = 1.6                         # the product's AiProcessIndication shimmer period


def _feather_scale(h):
    """hero_1's feather was made for boxes 33+ px tall; a thin one keeps the same look with less."""
    return min(1.0, h * 0.6 / 18)


def _argb(c):
    return c if len(c) == 8 and not c.startswith("#") else _color(c)


class Patterns:
    """Piece placers (p.quick_edits, p.code_editor, p.file_tree, p.code_panel, p.gen_status, p.asset)."""

    # ------------------------------------------------------------ own files
    def asset(self, key, file):
        """An image file of the piece (in its folder) for your own drawing: returns its asset id ("@img.<key>") for
        an Image element (p.image places one in a box for you)."""
        k = f"{self.key}_{key}"
        kit.image_asset(k, os.path.join(self.here, file))
        return f"@img.{k}"

    # ------------------------------------------------------------ the code editor
    def code_editor(self, name, code, size=10, lh=17, numbers=True, empty=True, w="fill", h="fill", num_w=24,
                    pad=(8, 12, 16, 12), colors=None):
        """A code editor in JetBrains Mono (size / lh: the hero's 10 / 17), line numbers in a column at its left.
        code: the text (lines; JS / JSX is coloured on its own: keywords, calls, components, strings, comments), or
        a list of lines, each a string or [(text, kind)] (kind k, f, t, s, c, p). empty=True: the file starts empty
        and a.write_code() writes it, line by line (the caret rides the text, each number shows with its line).
        colors: {kind: '#rrggbb'} over the hero's (SYNTAX)."""
        kit.FONTS.setdefault("mono", ("JetBrainsMono-Regular.ttf", "JetBrains Mono"))
        pal = dict(SYNTAX, **(colors or {}))
        lines = code.split("\n") if isinstance(code, str) else list(code)
        lines = [highlight(ln) if isinstance(ln, str) else list(ln) for ln in lines]
        n0 = f"{self.art}.{name}"
        st = {}

        def style(kind):
            if kind not in st:
                st[kind] = kit.text_style(f"{self.key}_{name}_{kind}", None, _color(pal[kind]), size=size, lh=lh,
                                          font="mono")
            return st[kind]
        rows, runs, carets, nums = [], {}, {}, {}
        for i, line in enumerate(lines, 1):
            t = kit.text(f"{n0}.L{i}", [(style(k), "") for _, k in line] + [(style("caret"), "")], lp=kit.hug(),
                         wrap=False)
            names = [f"{n0}.L{i}.run{j}" for j in range(len(line) + 1)]
            if not empty:     # the literal goes in after (a run of code may start with "=", a binding to kit.text)
                for el, (txt, _) in zip((c for c in t.children if c.tag == "TextValueRun"), line):
                    el.attrs["text"] = txt
            runs[i], carets[i] = names[:-1], names[-1]
            self.no_layout.update(names)      # one line, a fixed row: its text never moves anything else
            kids = [t]
            if numbers:
                num = kit.text(f"{n0}.N{i}", [(style("ln"), str(i))], lp=kit.fill_w(), wrap=False, align="right",
                               opacity=0 if empty else None)
                nums[i] = num.name
                kids = [kit.box(f"{n0}.Nb{i}", [num], w=num_w, h=lh, flexDirectionValue="column",
                                layoutAlignmentType="topRight", layoutWidthScaleType="fixed",
                                layoutHeightScaleType="fixed"), t]
            rows.append(kit.box(f"{n0}.row{i}", kids, h=lh, flexDirectionValue="row", layoutAlignmentType="topLeft",
                                gapHorizontal=14, layoutWidthScaleType="fill", layoutHeightScaleType="fixed"))
        ed = self._box(name, rows, "column", 0, pad, "topLeft", w, h, clip=True)
        ed.kind = "code"
        ed.lines, ed.runs, ed.carets, ed.nums, ed.line_done = lines, runs, carets, nums, {}
        return ed

    def file_tree(self, name, entries, w=146, selected=None, row_h=24, style="Content/Body"):
        """The Code tab's file tree: entries top to bottom, two spaces of indent a level; "name/" a folder (a
        chevron), else a file (its icon); "+name": a file not there yet, a.add_file(tree, "name") brings it in (the
        rows below make room). selected: the file shown in the editor (a grey row).
        Targets: tree.rows["App.tsx"] (each row)."""
        ink = kit.color("Typography/primary-text-color")
        ink2 = kit.color("Typography/secondary-text-color")
        k = f"{self.key}_{name}"
        kit.text_style(k, style, ink)
        rows, slots, items, hidden = [], {}, {}, set()
        for i, line in enumerate(entries):
            depth = (len(line) - len(line.lstrip())) // 2
            label = line.strip()
            new = label.startswith("+")
            label = label.lstrip("+ ")
            folder = label.endswith("/")
            label = label.rstrip("/")
            n = f"{self.art}.{name}.r{i}"
            mark = kit.icon_slot(f"{n}.mark", "arrows/chevron_bottom" if folder else "general/i_file", ink2,
                                 size=12 if folder else 14, slot=14)
            txt = kit.text(f"{n}.t", [(k, "")], lp=kit.hug(), wrap=False)
            next(c for c in txt.children if c.tag == "TextValueRun").attrs["text"] = label
            row = self._box(f"{name}Row{i}", [mark, txt], "row", 6, (8 + 12 * depth, 0, 8, 0), "centerLeft", "fill",
                            row_h, cornerRadiusTL=4,
                            paints=[kit.solid(f"{n}.fill", _color("#efeff1") if label == selected else kit.CLEAR)])
            slot = kit.box(f"{n}.slot", [row.wrap], h=0 if new else row_h, clip=True, flexDirectionValue="column",
                           layoutWidthScaleType="fill", layoutHeightScaleType="fixed")
            if new:
                row.wrap.attrs["opacity"] = 0
                hidden.add(label)
            rows.append(slot)
            slots[label], items[label] = slot.name, row
        tree = self._box(name, rows, "column", 0, (4, 4, 4, 4), "topLeft", w, "hug")
        tree.kind = "tree"
        tree.rows, tree.slots, tree.hidden, tree.row_h = items, slots, hidden, row_h
        return tree

    def code_panel(self, name, code, files, file="App.tsx", tree_w=146, w="fill", h="fill", search="Search",
                   selected=None, **editor):
        """The Vibe Code tab: the file tree at the left (a search over it, a line at its right), the open file's tab
        over the editor (p.code_editor(code, **editor); `file` its name). files: p.file_tree entries.
        Targets: panel.tree (tree.rows[...]), panel.editor, panel.search, panel.tab."""
        n = f"{self.art}.{name}"
        find = self.search(f"{name}Search", w=tree_w - 16, placeholder=search)
        tree = self.file_tree(f"{name}Tree", files, w=tree_w, selected=selected or file)
        left = self._box(f"{name}Left", [self._box(f"{name}Find", [find], "column", 0, (8, 8, 8, 4), "topLeft", "fill",
                                                   "hug"), tree], "column", 0, 0, "topLeft", tree_w, "fill",
                         paints=[kit.solid(f"{n}.leftFill", kit.WHITE)])
        self._edge(left, "right", "#e4e4e6")
        tab = self.text(f"{name}File", file, style="Content/Body", color="Typography/primary-text-color")
        head = self._box(f"{name}Head", [kit.icon_slot(f"{n}.fileIcon", "general/i_file",
                                                       kit.color("Typography/secondary-text-color"), size=14), tab],
                         "row", 6, (16, 0, 16, 0), "centerLeft", "fill", 40)
        self._edge(head, "bottom", "#e4e4e6")
        ed = self.code_editor(f"{name}Editor", code, **editor)
        right = self._box(f"{name}Right", [head, ed], "column", 0, 0, "topLeft", "fill", "fill")
        panel = self._box(name, [left, right], "row", 0, 0, "topLeft", w, h,
                          paints=[kit.solid(f"{n}.fill", kit.WHITE)])
        panel.tree, panel.editor, panel.search, panel.tab = tree, ed, find, tab
        return panel

    # ------------------------------------------------------------ Quick Edits (the visual edit's text panel)
    def quick_edits(self, name, content="", heading="H1", font="Inter", weight="Bold", color="#1E1E1E", opacity="100%",
                    size="48", size_unit="px", letter="0", letter_unit="%", line="120", line_unit="%", w=406, h="fill",
                    pending=False):
        """The Quick Edits panel (hero View tab, the storyboard's 04): a 48 px header (QUICK EDITS, pop out, close),
        the Text section (Content: a p.text_area holding `content`), a line, Typography (Headline type, Font, Weight:
        dropdowns; Color: a swatch, its hex and opacity; Font size, Letter, Line: a value and its unit), and the
        footer ("Pending changes", Discard, Apply). pending=False: "Pending changes" shows only when a.show(qe.pending).
        Targets: qe.close, qe.popout, qe.content (the text area: a.type_into(qe.content, "...", replace=True)),
        qe.heading, qe.font, qe.weight, qe.color, qe.size, qe.size_unit, qe.letter, qe.letter_unit, qe.line,
        qe.line_unit, qe.discard, qe.apply, qe.pending."""
        n = f"{self.art}.{name}"
        ink2 = "Typography/secondary-text-color"
        title = self.text(f"{name}Title", "QUICK EDITS", style="Headlines/He 4", color=ink2)
        pop = self.icon_button(f"{name}Pop", icon="i_pop_out", variant=0, size=0, color=4)
        close = self.icon_button(f"{name}Close", icon="i_x", variant=0, size=0, color=4)
        head = self._box(f"{name}Head", [title, kit.box(f"{n}.headGap", h=1, layoutWidthScaleType="fill",
                                                        layoutHeightScaleType="fixed"), pop, close],
                         "row", 8, (24, 12, 16, 12), "centerLeft", "fill", 48)
        self._edge(head, "bottom", "#e4e4e6")

        def section(key, label):
            return self._box(f"{name}{key}", [
                self.text(f"{name}{key}T", label, style="Headlines/He 3"),
                kit.box(f"{n}.{key}Gap", h=1, layoutWidthScaleType="fill", layoutHeightScaleType="fixed"),
                kit.icon_slot(f"{n}.{key}Chev", "arrows/chevron_bottom", kit.color(ink2))],
                "row", 8, 0, "centerLeft", "fill", "hug")
        area = self.text_area(f"{name}Content", w=358, h=126, label="Content", value=content, placeholder="")
        rule = kit.box(f"{n}.rule", paints=[kit.solid(f"{n}.rule.fill", _color("#e4e4e6"))], h=1,
                       layoutWidthScaleType="fill", layoutHeightScaleType="fixed")

        def prop_row(key, label, controls):
            lab = self.text(f"{name}{key}L", label, style="Content/Body")
            cell = self._box(f"{name}{key}Lb", [lab], "row", 0, 0, "centerLeft", 134, 35)
            return self._box(f"{name}{key}Row", [cell] + controls, "row", 8, 0, "centerLeft", "fill", "hug")

        def dd(key, value, wd=200):
            return self.dropdown(f"{name}{key}", w=wd, showLabel=False, value=value)

        def pair(key, value, unit):
            return [self.input(f"{name}{key}", w=108, showLabel=False, value=value), dd(f"{key}Unit", unit, 84)]
        heading_d, font_d, weight_d = dd("Heading", heading), dd("Font", font), dd("Weight", weight)
        swatch = kit.box(f"{n}.swatch", paints=[kit.solid(f"{n}.swatch.fill", _color(color))], w=18, h=18,
                         cornerRadiusTL=3, layoutWidthScaleType="fixed", layoutHeightScaleType="fixed")
        hexv = self.text(f"{name}Hex", color.lstrip("#").upper(), style="Content/Body 14")
        op = self.text(f"{name}Opacity", opacity, style="Content/Body 14", color=ink2)
        col = self._box(f"{name}Color", [swatch, hexv, kit.box(f"{n}.colGap", h=1, layoutWidthScaleType="fill",
                                                               layoutHeightScaleType="fixed"), op],
                        "row", 8, (9, 0, 12, 0), "centerLeft", 200, 35, cornerRadiusTL=6,
                        paints=[kit.solid(f"{n}.colFill", kit.WHITE)])
        col.wrap.children.insert(0, kit.absolute(f"{n}.colEdge", paints=[kit.line(
            f"{n}.colEdge.stroke", kit.color("Borders/border-color"), 1)], inset=(0.5,) * 4, cornerRadiusTL=5.5))
        size_p, letter_p, line_p = pair("Size", size, size_unit), pair("Letter", letter, letter_unit), \
            pair("Line", line, line_unit)
        rows = [prop_row("HeadingP", "Headline type", [heading_d]), prop_row("FontP", "Font", [font_d]),
                prop_row("WeightP", "Weight", [weight_d]), prop_row("ColorP", "Color", [col]),
                prop_row("SizeP", "Font size", size_p), prop_row("LetterP", "Letter", letter_p),
                prop_row("LineP", "Line", line_p)]
        body = self._box(f"{name}Body", [section("Text", "Text"), area, rule, section("Typo", "Typography"),
                                         self._box(f"{name}Props", rows, "column", 16, 0, "topLeft", "fill", "hug")],
                         "column", 16, (24, 20, 24, 20), "topLeft", "fill", "fill", clip=True)
        dot = kit.box(f"{n}.dot", paints=[kit.solid(f"{n}.dot.fill", kit.color("Indications/pending-color"))], w=6,
                      h=6, cornerRadiusTL=3, layoutWidthScaleType="fixed", layoutHeightScaleType="fixed")
        pend = self._box(f"{name}Pending", [dot, self.text(f"{name}PendingT", "Pending changes",
                                                           style="Content/Body", color=ink2)],
                         "row", 6, 0, "centerLeft", "hug", "hug", opacity=None if pending else 0)
        discard = self.button(f"{name}Discard", label="Discard", variant=1, color=0)
        apply = self.button(f"{name}Apply", label="Apply", variant=0, color=0)
        foot = self._box(f"{name}Foot", [pend, kit.box(f"{n}.footGap", h=1, layoutWidthScaleType="fill",
                                                       layoutHeightScaleType="fixed"), discard, apply],
                         "row", 8, (24, 0, 24, 0), "centerLeft", "fill", 65)
        self._edge(foot, "top", "#e4e4e6")
        qe = self._box(name, [head, body, foot], "column", 0, 0, "topLeft", w, h,
                       paints=[kit.solid(f"{n}.fill", kit.WHITE)])
        self._edge(qe, "left", "#ededee")
        qe.close, qe.popout, qe.content, qe.pending = close, pop, area, pend
        qe.heading, qe.font, qe.weight, qe.color = heading_d, font_d, weight_d, col
        (qe.size, qe.size_unit), (qe.letter, qe.letter_unit), (qe.line, qe.line_unit) = size_p, letter_p, line_p
        qe.discard, qe.apply = discard, apply
        return qe

    # ------------------------------------------------------------ the AI's generation status
    def gen_status(self, name, label="Generating...", done="Done", style="Content/Body 14",
                   color="Typography/secondary-text-color"):
        """The AI star and "Generating..." (the hero Code tab's status): a.generating(st) runs the product's shimmer
        over the text (every 1.6 s), a.done(st) turns it to "Done" (the text crossfades, the box closes to the new
        width: placed against a right edge, the star slides toward it)."""
        n = f"{self.art}.{name}"
        k = f"{self.key}_{name}"
        kit.text_style(k, style, _color(color))
        band = El("TextModifierRange", {"modifyFrom": -0.36, "modifyTo": 0.36, "falloffFrom": 0, "falloffTo": 0,
                                        "offset": -2, "clamp": False}, name=f"{n}.band")
        shimmer = El("TextModifierGroup", {"modifyOpacity": True, "invertOpacity": True, "opacity": 0.37}, [band],
                     name=f"{n}.shimmer")
        gen = self._box(f"{name}Gen", [kit.text(f"{n}.genT", [(k, label)], lp=kit.hug(), wrap=False,
                                                modifiers=[shimmer])], "row", 0, 0, "centerLeft", "hug", "hug")
        fin = self._box(f"{name}Done", [kit.text(f"{n}.doneT", [(k, done)], lp=kit.hug(), wrap=False)], "row", 0, 0,
                        "centerLeft", "hug", "hug", opacity=0)
        texts = kit.box(f"{n}.texts", [fin.wrap, gen.wrap], layoutTypeValue="stack", layoutAlignmentType="centerRight",
                        flexDirectionValue="row", **kit.hug())
        st = self._box(name, [self._art(f"{name}.star", "ai_star.svg", 16), texts], "row", 6, 0, "centerLeft",
                       "hug", "hug")
        st.kind = "genstatus"
        st.gen, st.done_t, st.texts, st.band = gen, fin, texts, band.name
        return st

    # ------------------------------------------------------------ the AI's answer in the chat
    def chat_reply(self, name, paragraphs, actions=("i_duplicate", "i_options"), status="Thinking...", gap=24,
                   style="Content/Body 14", color="Typography/primary-text-color"):
        """The AI's answer as the product brings it (in p.ai_panel(chat=[ask, reply])): "Thinking..." waits right under
        the message (a.think(reply)); the paragraphs come in above it one by one, each opening its own room and
        pushing it down (a.reply(reply)); a second later it gives way to the answer's action icons, and no "Thought
        for Xs" is left. A paragraph takes no room until it comes. gap: between paragraphs (the panel's `gap`).
        Targets: reply.status (an AiProcessIndication), reply.actions (Icon buttons), reply.paragraphs."""
        n = f"{self.art}.{name}"
        paras, slots = [], []
        for i, string in enumerate(paragraphs):
            para = self.chat_ai(f"{name}P{i}", string, style=style, color=color)
            inner = kit.box(f"{n}.roomIn{i}", [para.wrap], paddingBottom=gap, flexDirectionValue="column",
                            layoutAlignmentType="topLeft", layoutWidthScaleType="fill", layoutHeightScaleType="hug")
            slots.append(kit.box(f"{n}.room{i}", [inner], h=0, clip=True, flexDirectionValue="column",   # no padding:
                                 layoutAlignmentType="topLeft", layoutWidthScaleType="fill",   # it would hold room
                                 layoutHeightScaleType="fixed"))
            paras.append(para)
        st = self.ai_status(f"{name}Status", label=status)
        acts = [self.icon_button(f"{name}Act{i}", icon=ic, variant=0, size=0, color=1) for i, ic in enumerate(actions)]
        bar = self._box(f"{name}Acts", acts, "row", 6, 0, "centerLeft", "hug", "hug", opacity=0)
        tail = self._box(f"{name}Tail", [bar, st], "column", 0, 0, "topLeft", "fill", "hug", layoutTypeValue="stack")
        reply = self._box(name, slots + [tail], "column", 0, 0, "topLeft", "fill", "hug")
        reply.kind = "reply"
        reply.status, reply.actions, reply.paragraphs, reply.bar = st, acts, paras, bar
        reply.rooms, reply.gap = [s.name for s in slots], gap
        return reply


class ActionPatterns:
    """Actions for the patterns, and plain keys made easy (hide, show, text, stream, count, beats)."""

    @staticmethod
    def _list(items):
        return items if isinstance(items, (list, tuple)) else [items]

    def _hidden_at_start(self, n):
        op = self.c.track(n, "opacity")
        if len(op.keys) == 1:     # its first appearance: hidden until then
            op.keys[0]["v"] = 0.0

    # ------------------------------------------------------------ showing and hiding
    def hide(self, items, t=None, dur=SWAP):
        """Items fade out together (dur: the swap's 0.1 s; one state at a time: what replaces them comes after).
        Returns when they are gone (it doesn't move `now`)."""
        t, dur = self._t(t), secs(dur)
        for it in self._list(items):
            self.c.fade(t, _el(it).name, 0.0, dur)
        self._note(t + dur, f"hide {', '.join(_el(i).name for i in self._list(items))}")
        return t + dur

    def show(self, items, t=None, dur="fade"):
        """Items fade in where they are (hidden until then, when it is their first appearance). Returns the end."""
        t, dur = self._t(t), secs(dur)
        for it in self._list(items):
            n = _el(it).name
            self._hidden_at_start(n)
            self.c.fade(t, n, 1.0, dur)
        self._note(t + dur, f"show {', '.join(_el(i).name for i in self._list(items))}")
        return t + dur

    # ------------------------------------------------------------ text
    def _runs(self, item):
        out = []
        kit.walk(_el(item), lambda e: out.append(e.name) if e.tag == "TextValueRun" and e.name else None)
        return out

    def _run(self, item):
        runs = self._runs(item)
        assert len(runs) == 1, f"{_el(item).name}: a.text / stream / count work on a p.text (one run of text)"
        return runs[0]

    def text(self, item, value, t=None, fade=False):
        """A p.text changes to `value` at t (a chat renamed, a label edited). fade=True: it fades out (0.1 s), changes,
        and fades back in. Returns when the new text shows."""
        t = self._t(t)
        run = self._run(item)
        if fade:
            n = _el(item).name
            self.c.fade(t, n, 0.0, SWAP)
            self.c.set(t + SWAP, run, "text", value)
            self.c.fade(t + SWAP + 1 / FPS, n, 1.0, kit.FADE)
            end = t + SWAP + 1 / FPS + kit.FADE
        else:
            self.c.set(t, run, "text", value)
            end = t
        self._note(end, f"text {_el(item).name} {value!r}")
        return end

    def stream(self, item, text=None, t=None, cps=80, seed=7):
        """The AI's reply arrives word by word (a p.text / p.chat_ai, empty until t): chunks of a word or a few
        marks, `cps` characters a second with a little jitter. text: what it writes (default: its own text).
        Returns when the last word is in."""
        t = self._t(t)
        run = self._run(item)
        el = self.c.by[run]
        if text is None:
            text = el.attrs.get("text", "")
        if (run, "text") not in self.c.tracks:
            el.attrs["text"] = ""     # empty from the first frame
        self.c.set(t, run, "text", "")
        rnd = random.Random(seed)
        cur, shown, last = t, "", None
        for tok in tokens(text):
            cur += max(1, len(tok.strip())) / cps * rnd.uniform(0.7, 1.3)
            shown += tok
            f = frame(cur)
            if f == last:     # several chunks in one frame: the last one wins
                self.c.track(run, "text").keys[-1]["v"] = shown
            else:
                self.c.set(f / FPS, run, "text", shown)
            last = f
        self._note(last / FPS, f"stream {_el(item).name} ({len(text)} chars)")
        return last / FPS

    def count(self, item, to, t=None, dur=0.7, ease="duda", fmt="{:,}", blur=3.0):
        """A number counts up from 0 to `to` (a p.text): the eased value frame by frame, sharpening from a light blur
        (Feather `blur`). fmt: how it is written ("{:,}" 1,234; "{}%")."""
        t, dur = self._t(t), secs(dur)
        run = self._run(item)
        curve = choreo.ease_curve(ease)
        n, prev = max(1, round(dur * FPS)), None
        for f in range(n + 1):
            v = fmt.format(round(to * choreo.progress(curve, f / n)))
            if v != prev:
                self.c.set(t + f / FPS, run, "text", v)
                prev = v
        if blur:
            for fe in self._feathers(item):
                self.c.set(t, fe, "strength", blur)
                self.c.move(t + 1 / FPS, fe, "strength", 0.0, DETAILS["blur"]["dur"], "duda")
        self._note(t + dur, f"count {_el(item).name} to {to}")
        return t + dur

    def _feathers(self, item):
        """A Feather in each text fill of `item` (added once, at 0: sharp), for the light blur of a pop or a count."""
        out = []

        def add(e):
            if e.tag == "Fill" and e.name and e.name.endswith(".fill") and any(
                    c.tag == "SolidColor" for c in e.children if isinstance(c, El)) and \
                    self.c.parent.get(id(e)) is not None and self.c.parent[id(e)].tag == "TextStylePaint":
                fe = next((c for c in e.children if isinstance(c, El) and c.tag == "Feather"), None)
                if fe is None:
                    fe = El("Feather", {"strength": 0.0}, name=f"{e.name[:-5]}.blur")
                    e.children.append(fe)
                    self.c.by[fe.name] = fe
                    self.c.parent[id(fe)] = e
                out.append(fe.name)
        kit.walk(_el(item), add)
        return out

    def _colors(self, item):
        out = []
        kit.walk(_el(item), lambda e: out.append(e.name) if e.tag == "SolidColor" and e.name and
                 self.c.parent.get(id(e)) is not None and self.c.parent[id(e)].tag == "Fill" and
                 self.c.parent.get(id(self.c.parent[id(e)])) is not None and
                 self.c.parent[id(self.c.parent[id(e)])].tag == "TextStylePaint" else None)
        return out

    # ------------------------------------------------------------ the AI's answer in the chat
    def _room_heights(self, reply, t):
        """Each paragraph's own height (its room is closed: the measure lays the rooms out open, once)."""
        styles = [next(c for c in self.c.by[r].children if c.tag == "LayoutComponentStyle") for r in reply.rooms]
        saved = [st.attrs.get("layoutHeightScaleType") for st in styles]
        for st in styles:
            st.attrs["layoutHeightScaleType"] = "hug"
        self.p._measured.clear()
        try:
            return [self.p.bounds(para, t)[3] for para in reply.paragraphs]
        finally:
            for st, v in zip(styles, saved):
                st.attrs["layoutHeightScaleType"] = v
            self.p._measured.clear()

    def think(self, reply, t=None):
        """The message is sent: "Thinking..." comes in right under it (it shimmers on its own). Returns t."""
        t = self._t(t)
        self.enter(reply.status, t, dy=4, dur=0.5)
        return t

    def reply(self, reply, t=None, step=0.27, then=1.0, stream=False, cps=80):
        """The answer of a p.chat_reply comes in above "Thinking...": each paragraph's room opens (0.25 s, duda),
        pushing the status down, and the paragraph enters into it (rising 4 px), `step` s after the one before;
        stream=True: its words come in instead (cps), and the next one waits for it. `then` s after the last, the
        status fades out (its shimmer stops while hidden) and the action icons fade in in its place. Returns when
        they show."""
        t = self._t(t)
        tt, last = t, t
        heights = self._room_heights(reply, t)
        for i, (para, room) in enumerate(zip(reply.paragraphs, reply.rooms)):
            h = heights[i] + reply.gap
            self.c.move(tt, room, "height", float(h), 0.25, "duda")
            if stream:
                last = self.stream(para, t=tt + 0.25, cps=cps)
                tt = last + 0.1
            else:
                self.enter(para, tt + 0.25, dy=4, dur=0.5)
                last = tt + 0.25 + 0.5
                tt += step
        t1 = last + secs(then)
        st = reply.status.wrap.name
        self.c.fade(t1, st, 0.0, SWAP)
        self._key(t1 + SWAP + 1 / FPS, reply.status, "done", True)
        self.show(reply.bar, t1 + 0.083, 0.15)
        self._note(t1 + 0.233, f"reply {reply.key}: {len(reply.paragraphs)} paragraph(s)")
        return t1 + 0.233

    # ------------------------------------------------------------ the code editor and the tree
    def write_code(self, editor, t=None, speeds=((1, 240), (12, 100)), pauses=None, newline=2, caret_hold=0.3,
                   seed=7):
        """The AI writes the file into a p.code_editor (empty=True): chunk by chunk (a word or a few marks), each
        line's number showing as it starts, the caret riding the end of the line being written. speeds: (from line,
        characters a second), the hero's: 240, then 100 from line 12; newline: a new line costs that many characters;
        pauses: {line: s} holds after a line. Returns when the last line is done (editor.line_done[n]: when line n
        is, to place other beats on the code)."""
        t = self._t(t)
        rnd = random.Random(seed)
        sp = sorted(speeds)
        pauses = pauses or {}
        cur, caret, last = t, None, {}
        for n, line in enumerate(editor.lines, 1):
            cps = [c for f, c in sp if f <= n][-1]
            if n > 1:
                cur += newline / cps
            f = frame(cur)
            if n in editor.nums:
                self.c.set(f / FPS, editor.nums[n], "opacity", 1.0)
            if caret is not None:
                self.c.set(f / FPS, caret, "text", "")
            caret = editor.carets[n]
            self.c.set(f / FPS, caret, "text", CARET)
            full = "".join(x for x, _ in line)
            shown = 0
            for tok in tokens(full):
                cur += len(tok.strip()) / cps * rnd.uniform(0.7, 1.3)
                shown += len(tok)
                f = frame(cur)
                start = 0
                for run, (x, _) in zip(editor.runs[n], line):
                    v = x[:max(0, min(len(x), shown - start))]
                    start += len(x)
                    if last.get(run, "") != v:
                        self.c.set(f / FPS, run, "text", v)
                        last[run] = v
            editor.line_done[n] = frame(cur) / FPS
            cur += pauses.get(n, 0.0)
        end = frame(cur) / FPS
        self.c.set(end + caret_hold, caret, "text", "")
        self._note(end, f"write_code {editor.key}: {len(editor.lines)} lines")
        return end

    def add_file(self, tree, label, t=None):
        """A new file arrives in a p.file_tree ("+name" there): the rows below make room (0.33 s), the file slides in
        from the left (0.5 s, settle). Returns when it has landed."""
        t = self._t(t)
        assert label in tree.hidden, f"{label!r} is not a new file of {tree.key} (mark it \"+{label}\")"
        self.c.move(t, tree.slots[label], "height", float(tree.row_h), 0.333, "duda")
        row = tree.rows[label].wrap.name
        self.c.enter(t + 0.1, row, dx=-6.0, dy=0.0, dur=0.5, ease="settle")
        self._note(t + 0.6, f"add_file {label}")
        return t + 0.6

    # ------------------------------------------------------------ the AI's status
    def generating(self, status, t=None):
        """A p.gen_status (or AiProcessIndication-like text of your own) starts shimmering at t, until a.done(status)
        (or the end). Returns t."""
        t = self._t(t)
        self.statuses.append([status, t, None])
        self._note(t, f"generating {status.key}")
        return t

    def done(self, status, t=None):
        """The status turns to "Done": "Generating..." fades out (0.1 s), "Done" fades in, the box closes to its
        width (0.33 s, duda). Returns when it has settled."""
        t = self._t(t)
        run = next((s for s in self.statuses if s[0] is status and s[2] is None), None)
        if run:
            run[2] = t
        w_gen = self.p.bounds(status.gen, t)[2]
        w_done = self.p.bounds(status.done_t, t)[2]
        st = next(c for c in status.texts.children if c.tag == "LayoutComponentStyle")
        st.attrs["layoutWidthScaleType"] = "fixed"
        status.texts.attrs["width"] = w_gen
        self.c.track(status.texts.name, "width").keys[0]["v"] = float(w_gen)
        self.c.fade(t, status.gen.wrap.name, 0.0, 0.1)
        self.c.fade(t + 0.083, status.done_t.wrap.name, 1.0, 0.15)
        self.c.move(t + 0.1, status.texts.name, "width", float(w_done), 0.333, "duda")
        self._note(t + 0.433, f"done {status.key}")
        return t + 0.433

    def _close_statuses(self, end):
        """The shimmer passes of every a.generating(), up to its a.done() (or `end`)."""
        for status, t0, t1 in self.statuses:
            band = status.band
            t1 = end if t1 is None else t1
            t = t0
            while t < t1 - 2 / FPS:
                seg = min(SHIMMER_S, t1 - t)
                # it lands a frame before the next pass's set (a key on the same frame would replace it)
                self.c.set(t, band, "offset", -0.25)
                self.c.move(t + 1 / FPS, band, "offset", round(-0.25 + 1.5 * (seg - 1 / FPS) / SHIMMER_S, 4),
                            seg - 2 / FPS, "linear")
                t += seg

    # ------------------------------------------------------------ the Generation effect
    def generate(self, item, t=None, kind=None, squares=None, rows=None, pops=None, clip=None, radius=8):
        """The AI builds `item` (hero_1's Generation effect, as the hero pieces make it): a square over it, filled
        with the 7-stop gradient and feathered, grows to 100 % while the gradient sweeps through; when the square
        shows it (frame 36 small, 56 big) the item fades in under it, then the details:
          rows   items inside it come in one after the other (83 ms apart), rising 4 px
          pops   texts (p.text) inside it pop along the row from the left: orange, pink, their own colour,
                 sharpening from a light blur
        kind: "small" / "big" (default by height: big from 100 px); squares: [(dx, dy, w, h[, radius])] from the
        item's top-left, or items, instead of one square on the whole item; clip: an item (or (x, y, w, h[, r]))
        the squares are cut to (a window with round corners). The item starts hidden. Returns when all has landed."""
        t0 = self._t(t)
        fx_n = len(self.p.effects)
        x, y, w, h = self.p.bounds(item, t0 + 0.6)     # where it is when the square shows it
        kind = kind or ("big" if h >= 100 else "small")
        g = GEN[kind]
        boxes = []
        for sq in (squares or [(0, 0, w, h, radius)]):
            if isinstance(sq, Item):
                bx, by_, bw, bh = self.p.bounds(sq, t0 + 0.6)
                boxes.append((bx, by_, bw, bh, radius))
            else:
                boxes.append((x + sq[0], y + sq[1], sq[2], sq[3], sq[4] if len(sq) > 4 else radius))
        kids = []
        for i, (bx, by_, bw, bh, r) in enumerate(boxes):
            nm = f"{self.p.art}.fx{fx_n}.{i}"
            fs = _feather_scale(bh)
            grad = El("LinearGradient", dict(SWEEP0), [El("GradientStop", {"colorValue": c, "position": p},
                                                          name=f"{nm}.stop{j}") for j, (c, p) in enumerate(FX_STOPS)],
                      name=f"{nm}.grad")
            paint = El("Fill", {"fillRule": "clockwise"},   # a feathered fill draws only under the clockwise rule
                       [grad, El("Feather", {"strength": round(g["feather"][0] * fs, 3)}, name=f"{nm}.feather")],
                       name=f"{nm}.fill")
            rect = El("Rectangle", {"width": bw, "height": bh, "cornerRadiusTL": r or None}, name=f"{nm}.rect")
            kids.append(El("Shape", {"x": bx + bw / 2, "y": by_ + bh / 2, "scaleX": g["s0"], "scaleY": g["s0"]},
                           [rect, paint], name=nm))
        if clip is not None:
            cx, cy, cw, ch = self.p.bounds(clip, t0 + 0.6) if isinstance(clip, Item) else clip[:4]
            cr = clip[4] if isinstance(clip, tuple) and len(clip) > 4 else 0
            src = f"{self.p.art}.fx{fx_n}.clip"
            kids.append(El("Shape", {"x": cx, "y": cy}, [El("Rectangle", {
                "width": cw, "height": ch, "originX": 0, "originY": 0, "cornerRadiusTL": cr or None},
                name=f"{src}.rect")], name=src))
            kids.append(El("ClippingShape", {"sourceId": f"@{src}", "fillRule": "nonZero"}, name=f"{src}.cut"))
        group = El("Node", {"x": 0, "y": 0}, kids, name=f"{self.p.art}.fx{fx_n}")
        self.p.fx.children.append(group)
        self.p.effects.append(group)
        self.c.parent[id(group)] = self.p.fx

        def reg(e, par):
            if e.name:
                self.c.by[e.name] = e
            for c in e.children:
                if isinstance(c, El):
                    self.c.parent[id(c)] = e
                    reg(c, e)
        reg(group, self.p.fx)
        span = lambda a, z: (z - a) / FPS   # noqa: E731
        for i, (_, _, _, bh, _) in enumerate(boxes):
            nm = f"{self.p.art}.fx{fx_n}.{i}"
            for k, v in SWEEP1.items():
                self.c.move(t0, f"{nm}.grad", k, v, span(0, g["sweep"]), SWEEP_EASE)
            a, z = g["scale"]
            for ax in ("scaleX", "scaleY"):
                self.c.move(t0 + a / FPS, nm, ax, 1.0, span(a, z), "linear")
            _, f1, a, z = g["feather"]
            self.c.move(t0 + a / FPS, f"{nm}.feather", "strength", round(f1 * _feather_scale(bh), 3), span(a, z),
                        "linear")
            a, z = g["stop"]
            self.c.move(t0 + a / FPS, f"{nm}.stop2", "colorValue", "FFDDF1F9", span(a, z), "linear")
        show = t0 + g["show"][0] / FPS
        n = _el(item).name
        self._hidden_at_start(n)
        self.c.fade(show, n, 1.0, g["show"][1] / FPS)
        ends = [t0 + g["sweep"] / FPS]
        d = DETAILS
        row_t = {}
        for i, r in enumerate(self._list(rows or [])):
            rt = show + i * d["rows"]["step"]
            rn = _el(r).name
            row_t[rn] = rt
            self._hidden_at_start(rn)
            self.c.enter(rt, rn, dy=d["rows"]["rise"], dur=d["rows"]["dur"], ease="settle", fade=d["rows"]["fade"])
            ends.append(rt + d["rows"]["dur"])
        pop = d["pop"]
        for p_ in self._list(pops or []):
            px = self.p.bounds(p_, show)[0]
            owner = next((rn for rn in row_t if self._inside(p_, rn)), None)
            tp = frame(row_t.get(owner, show) + pop["lead"] + pop["across"] * max(0.0, px - x) / max(w, 1)) / FPS
            for col in self._colors(p_):
                own = self.c.track(col, "colorValue").keys[0]["v"]
                self.c.set(t0, col, "colorValue", "00" + own[2:])
                self.c.set(tp, col, "colorValue", ORANGE)
                self.c.move(tp + pop["pink_at"], col, "colorValue", PINK, pop["pink_in"], "linear")
                self.c.move(tp + pop["own_at"], col, "colorValue", own, pop["own_dur"], "linear")
            for fe in self._feathers(p_):
                self.c.set(t0, fe, "strength", d["blur"]["px"])
                self.c.move(tp, fe, "strength", 0.0, d["blur"]["dur"], "duda")
            ends.append(tp + max(pop["own_at"] + pop["own_dur"], d["blur"]["dur"]))
        end = max(ends)
        self._note(end, f"generate {n} ({kind}, {len(boxes)} square(s))")
        return end

    def _inside(self, item, name):
        found = []
        target = _el(item)
        root = self.c.by.get(name)
        if root is not None:
            kit.walk(root, lambda e: found.append(1) if e is target else None)
        return bool(found)

    # ------------------------------------------------------------ your own beats
    def beats(self, beats):
        """Your own beats on the same timeline (the kit's beat sheet: {"t", "do": move / set / fade / enter / exit /
        pop..., "target": an element's name, ...}). They don't move `now`."""
        choreo.run_beats(self.c, beats)
        for b in beats:
            self._note((b.get("t") or 0) + (b.get("dur") or 0), f"beat {b.get('do')} {b.get('target', '')}")
