"""v06: the Duda dashboard's Performance pages (the AEO report, Highlights) as piece parts, built from the library and
native shapes: the KPI card (Figma "Glance Data card"), the chart card, the donut and the line chart, the dashboard
shell (top bar, rail, the PERFORMANCE menu), the whole Highlights page, and their loading state (the Skeleton
component, the product's shimmer). Piece and Actions take them in (piece.py): a piece still imports only piece.py.

Measures: Figma i4AzmiPVfqgBsoEMUHrOlK, "AI-Visibility-highlights" (26:9582), which draws the page at 0.733 and the
shell at 0.68 (read with use_figma, 2026-10-23); here at product size. Content, order and loading: the product
(my.duda.co, site > Performance > Highlights, 2026-10-23: the titles show at once, the rest is skeletons with a
1.4 s shimmer, then the KPI cards fade in one after another)."""
import math
import re

import kit
from kit import El
from common import FPS, SWAP, secs, Item, _el, _color
import choreo
from choreo import frame

kit.FONTS.setdefault("cal", ("CalSans-SemiBold.ttf", "Cal Sans"))   # DS Display 1 / 2 (the variables say Cal Sans)

INK, NUM, SECOND, HINT = "#272b35", "#1e1e1e", "#5d6068", "#9b9ba2"
PAGE_BG, LINE, GRID = "#f5f5f7", "#e4e4e6", "#ededee"   # bg-grey, border-light (newer tokens), grey-200
TREND = {False: ("Indications/positive-med-color", "Indications/positive-light-color", "i_arrow_corner_up"),
         True: ("Indications/negative-med-color", "Indications/negative-light-color", "i_arrow_corner_down")}
# the KPI cards' tiles (Figma: #FFBCA7 45 %, #B7C2D2 39 % over the white card; #E1ECE5; #F5F5F7, the product's)
TILES = {"peach": "#ffe1d7", "slate": "#e3e7ed", "mint": "#e1ece5", "grey": "#f5f5f7"}
PALETTE = ("#ff8f77", "#bbcec3", "#8d97b2", "#f07c5a", "#b4ca82")   # the donut's pieces, in order (Figma)
CHART_A = 0.8           # Figma draws the donut, the line and its area at 80 %
SKEL_RING = "#efeff0"                                                # the product's ring while loading

KPIS = [dict(value="82%", trend="8.2%", label="AI visibility score", icon="i_ai_assistant", tile="peach"),
        dict(value="56,234", trend="12.5%", label="User visits", icon="i_user", tile="slate"),
        dict(value="1,462", trend="15.8%", label="Total leads", icon="i_onboard_client", tile="mint", info=True),
        dict(value="2.6%", trend="0.4%", label="Conversion rate", icon="i_engagement", tile="grey", info=True)]
DONUT = [("ChatGPT", 32), ("Gemini", 54), ("Claude", 14)]           # Figma's arcs: 115.2, 194.4, 46.8 degrees
# Figma's "User visits" line (26:10512), the part its plot shows (64 points), as visits
VISITS = [2434, 2434, 2434, 2457, 2457, 2457, 2365, 2434, 2457, 2457, 2503, 2503, 2434, 2457, 2480, 2641, 2641, 2664,
          2664, 2641, 2641, 2664, 2618, 2618, 2595, 2526, 2526, 2730, 2799, 2730, 2961, 3191, 3053, 3099, 3053, 2845,
          2845, 2822, 2822, 2822, 2845, 2730, 2776, 2776, 2776, 2730, 2776, 2707, 2684, 2707, 2707, 2776, 2707, 2684,
          2592, 2592, 2615, 2615, 2592, 2500, 2546, 2293, 2316, 2293]
DAYS = ["01 Jan", "07 Jan", "13 Jan", "19 Jan", "25 Jan", "31 Jan", "06 Feb", "12 Feb", "18 Feb", "24 Feb", "02 Mar",
        "08 Mar"]
DRAW = {"donut": 1.1, "line": 1.6}   # a.draw's default seconds (the donut clockwise, the line from the left)


def _number(s):
    """'56,234' -> (56234, '{:,}'); '82%' -> (82, '{}%'); '2.6%' -> (2.6, '{:.1f}%'); None if there is no number."""
    m = re.match(r"^(\D*?)(\d[\d,]*(?:\.\d+)?)(.*)$", s)
    if not m:
        return None
    pre, num, post = m.groups()
    dec = len(num.split(".")[1]) if "." in num else 0
    spec = ("," if "," in num else "") + (f".{dec}f" if dec else "")
    val = float(num.replace(",", "")) if dec else int(num.replace(",", ""))
    return val, pre + "{" + (":" + spec if spec else "") + "}" + post


class DashboardPatterns:
    """Piece placers: p.skeleton, p.kpi_card, p.chart_card, p.donut, p.line_chart, p.dashboard, p.aeo_highlights."""

    def skeleton(self, slot, w, h, **props):
        """Skeleton (a loading block, the product's shimmer): w x h points. props: circle, shimmer."""
        from components.skeleton import SKEL
        return self._place(slot, "skeleton", SKEL, "skel", props, w=w, h=h)

    # ------------------------------------------------------------ shared
    def _white(self, name, kids, w, h, pad, gap, align="topLeft", clip=False):
        n = f"{self.art}.{name}"
        return self._box(name, kids, "column", gap, pad, align, w, h,
                         paints=[kit.solid(f"{n}.fill", kit.WHITE)], cornerRadiusTL=8, clip=clip)

    def _label(self, name, string, k, x, y, w, h, align="left"):
        """A text of style k in a w x h box pinned at (x, y) of its parent."""
        n = f"{self.art}.{name}"
        t = kit.text(f"{n}.t", [(k, string)], lp=kit.fill_w(), wrap=False, align=align)
        return kit.absolute(n, [t], inset=(x, y, None, None), w=w, h=h, layoutWidthScaleType="fixed",
                            layoutHeightScaleType="fixed", flexDirectionValue="column",
                            layoutAlignmentType="centerLeft")

    def _stack(self, name, kids, w="hug", h="hug", align="topLeft"):
        """Children on top of each other (a skeleton over what replaces it); the first one draws on top."""
        return self._box(name, kids, "column", 0, 0, align, w, h, layoutTypeValue="stack")

    @staticmethod
    def _hidden(*items):
        for it in items:
            _el(it).attrs["opacity"] = 0

    # ------------------------------------------------------------ the KPI card
    def kpi_card(self, name, value, label, trend=None, down=False, icon="i_ai_assistant", tile="peach", info=False,
                 w=263, loading=False):
        """The KPI card of the dashboard (Figma "Glance Data card": a DS Item Card with the "% Trend" chip): the
        number (Cal Sans 26/28), the trend chip (a 16 px dot with an arrow and the % in Bold 12/14: green, or red
        with down=True), the label (Medium 13/18) with an info icon (info=True), and a 36 px tile with a 20 px icon
        at the right (tile: peach, slate, mint, grey or '#rrggbb'). White, radius 8, 88 tall; w: points or "fill".
        loading=True: skeletons stand in for it until a.load(card). Targets: card.value (a.count), card.chip."""
        n = f"{self.art}.{name}"
        val = self.text(f"{name}Value", value, style=None, font="cal", size=26, lh=28, color=NUM)
        top, chip = [val], None
        if trend:
            fg, bg, ic = TREND[bool(down)]
            dot = kit.box(f"{n}.dot", [kit.icon_slot(f"{n}.arrow", kit.ICON_FILES[ic], _color(fg), size=10, stroke_w=1.6)],
                          paints=[kit.solid(f"{n}.dot.fill", _color(bg))], w=16, h=16, cornerRadiusTL=8,
                          flexDirectionValue="column", layoutAlignmentType="center", layoutWidthScaleType="fixed",
                          layoutHeightScaleType="fixed")
            chip = self._box(f"{name}Chip", [dot, self.text(f"{name}Trend", trend, style=None, size=12, lh=14,
                                                            weight=700, color=fg)],
                             "row", 4, (0, 0, 0, 5), "centerLeft", "hug", "hug")
            top.append(chip)
        bottom = [self.text(f"{name}Label", label, style="Headlines/He 3", color=SECOND)]
        if info:
            bottom.append(kit.icon_slot(f"{n}.info", "common_actions/i_info_circle", _color(SECOND), size=14))
        texts = self.column(f"{name}Texts", [self.row(f"{name}Top", top, gap=8, align="bottomLeft"),
                                             self.row(f"{name}Bottom", bottom, gap=4)], gap=8)
        tile_el = kit.box(f"{n}.tile", [kit.icon_slot(f"{n}.icon", kit.ICON_FILES[icon], _color(INK), size=20, stroke_w=1.2)],
                          paints=[kit.solid(f"{n}.tile.fill", _color(TILES.get(tile, tile)))], w=36, h=36,
                          cornerRadiusTL=4, flexDirectionValue="column", layoutAlignmentType="center",
                          layoutWidthScaleType="fixed", layoutHeightScaleType="fixed")
        space = kit.box(f"{n}.space", h=1, layoutWidthScaleType="fill", layoutHeightScaleType="fixed")
        content = self.row(f"{name}Row", [texts, space, tile_el], gap=16, align="topLeft", w="fill")
        kids, skel = [content], None
        if loading:
            sp2 = kit.box(f"{n}.skSpace", h=1, layoutWidthScaleType="fill", layoutHeightScaleType="fixed")
            bars = self.column(f"{name}SkBars", [self.skeleton(f"{name}Sk1", 64, 20),
                                                 self.skeleton(f"{name}Sk2", 104, 12)], gap=16, pad=(0, 4, 0, 0))
            skel = self.row(f"{name}Skel", [bars, sp2, self.skeleton(f"{name}Sk3", 36, 36)], gap=16, align="topLeft",
                            w="fill")
            self._hidden(content)
            kids = [self._stack(f"{name}Stack", [skel, content], w="fill")]
        card = self._white(name, kids, w, 88, 16, 0)
        card.kind = "kpi"
        card.value, card.chip, card.label = val, chip, bottom[0]
        card.loading = (skel, content) if loading else None
        return card

    # ------------------------------------------------------------ the chart card
    def chart_card(self, name, title, body, w="fill", h=418, pad=24, align="topLeft"):
        """A dashboard card with a header (Figma ".Card header": 60 tall, the title in Bold 16/22, a line under it)
        over `body` (an item, or a list stacked in a column, padded `pad`). White, radius 8; h: points or "hug"."""
        head = self._box(f"{name}Head", [self.text(f"{name}Title", title, style="Headlines/He 1")], "row", 8,
                         (24, 0, 24, 0), "centerLeft", "fill", 60)
        self._edge(head, "bottom", LINE)
        kids = body if isinstance(body, (list, tuple)) else [body]
        inner = self._box(f"{name}Body", kids, "column", 0, pad, align, "fill", "fill" if h != "hug" else "hug")
        card = self._white(name, [head, inner], w, h, 0, 0, clip=True)
        card.title = card.head = head
        return card

    # ------------------------------------------------------------ the donut
    def donut(self, name, segments=None, total="23,000", total_label="Total", legend=True, size=184, w=304,
              loading=False):
        """A donut chart (Figma "Pie": inner radius 60 %, 2 px white gaps), drawn clockwise from the top by
        a.draw(donut). segments: [(label, value)] or (label, value, '#rrggbb') (default colours: Figma's coral, sage,
        slate...). total / total_label in its centre (Cal Sans 21/24 over Regular 13/18); legend: chips two by two
        under it (dot, label, its %), `w` wide. loading=True: a grey ring and skeletons until a.load(donut)."""
        segs = [s if len(s) > 2 else (s[0], s[1], PALETTE[i % len(PALETTE)]) for i, s in enumerate(segments or DONUT)]
        n = f"{self.art}.{name}"
        r = size / 2
        rm, gap = r * 0.8, 1.0
        whole = sum(s[1] for s in segs)
        shapes, trims, a0 = [], [], 0.0
        g = gap / (2 * math.pi * rm)
        for i, (_, v, col) in enumerate(segs):
            t0, t1 = a0 / whole + g, (a0 + v) / whole - g     # the ellipse's path starts at the top, clockwise
            a0 += v
            shapes.append(El("Shape", {"x": r, "y": r}, [
                El("Ellipse", {"width": 2 * rm, "height": 2 * rm}, name=f"{n}.seg{i}.ellipse"),
                El("Stroke", {"thickness": r * 0.4 - 2 * gap}, [
                    El("SolidColor", {"colorValue": kit.argb(col, CHART_A)}, name=f"{n}.seg{i}.color"),
                    El("TrimPath", {"start": round(t0, 6), "end": round(t1, 6), "offset": 0, "modeValue": 1},
                       name=f"{n}.seg{i}.trim")], name=f"{n}.seg{i}.stroke")], name=f"{n}.seg{i}"))
            trims.append((f"{n}.seg{i}.trim", round(t0, 6), round(t1, 6)))
        art = El("Node", {}, shapes, name=f"{n}.segs")
        k_tot, k_lab = f"{self.key}_{name}_tot", f"{self.key}_{name}_lab"
        kit.text_style(k_tot, None, _color(INK), font="cal", size=21, lh=24)
        kit.text_style(k_lab, "Content/Body", _color(SECOND))
        center = self.column(f"{name}Center", [
            kit.box(f"{n}.totW", [kit.text(f"{n}.tot.t", [(k_tot, total)], lp=kit.hug(), wrap=False)], h=24,
                    **kit.hug()),
            kit.box(f"{n}.labW", [kit.text(f"{n}.lab.t", [(k_lab, total_label)], lp=kit.hug(), wrap=False)], h=18,
                    **kit.hug())], gap=2, align="topCenter")
        ring_kids, skel, content = [art], [], [art, center]
        if loading:
            grey = El("Node", {}, [El("Shape", {"x": r, "y": r}, [
                El("Ellipse", {"width": 2 * rm, "height": 2 * rm}, name=f"{n}.sk.e"),
                kit.line(f"{n}.sk.s", _color(SKEL_RING), r * 0.4)], name=f"{n}.skRingShape")], name=f"{n}.skRing")
            bars = self.column(f"{name}SkCenter", [self.skeleton(f"{name}Sk1", 46, 14),
                                                   self.skeleton(f"{name}Sk2", 30, 8)], gap=6, align="topCenter")
            ring_kids.append(grey)
            skel += [grey, bars]
            mid = self._stack(f"{name}Mid", [bars, center], align="center")
        else:
            mid = center
        ring = self._box(f"{name}Ring", ring_kids + [mid], "column", 0, 0, "center", size, size)
        parts = [ring]
        if legend:
            chips = []
            for i, (lab, v, col) in enumerate(segs):
                dot = kit.box(f"{n}.lg{i}.dot", paints=[kit.solid(f"{n}.lg{i}.dot.fill", kit.argb(col, CHART_A))],
                              w=10, h=10, cornerRadiusTL=5, layoutWidthScaleType="fixed", layoutHeightScaleType="fixed")
                left = self.row(f"{name}Lg{i}L", [dot, self.text(f"{name}Lg{i}Name", lab, style="Content/Body",
                                                                color="#19213d")], gap=6)
                sp = kit.box(f"{n}.lg{i}.sp", h=1, layoutWidthScaleType="fill", layoutHeightScaleType="fixed")
                pct = self.text(f"{name}Lg{i}Pct", f"{round(100 * v / whole)}%", style="Content/Body", color="#353e5c")
                chip = self._box(f"{name}Lg{i}", [left, sp, pct], "row", 6, (8, 4, 8, 4), "centerLeft", "fill", 29,
                                 paints=[kit.solid(f"{n}.lg{i}.fill", kit.WHITE)], cornerRadiusTL=6)
                chip.wrap.children.insert(0, kit.absolute(f"{n}.lg{i}.edge", paints=[kit.line(
                    f"{n}.lg{i}.edge.s", _color(GRID))], inset=(0.5,) * 4, cornerRadiusTL=5.5))
                chips.append(chip)
            rows = [self.row(f"{name}LgRow{j}", chips[j:j + 2] + ([] if len(chips[j:j + 2]) == 2 else [
                kit.box(f"{n}.lgPad{j}", h=1, layoutWidthScaleType="fill", layoutHeightScaleType="fixed")]),
                gap=8, w="fill") for j in range(0, len(chips), 2)]
            lg = self.column(f"{name}Legend", rows, gap=8, w="fill")
            content.append(lg)
            if loading:
                lsk = self.row(f"{name}SkLegend", [self.skeleton(f"{name}Sk3", (w - 8) / 2, 20),
                                                   self.skeleton(f"{name}Sk4", (w - 8) / 2, 20)], gap=8, w="fill")
                skel.append(lsk)
                parts.append(self._stack(f"{name}LgStack", [lsk, lg], w="fill"))
            else:
                parts.append(lg)
        if loading:
            self._hidden(*content)
        item = self._box(name, parts, "column", 40, 0, "topCenter", w, "hug")
        item.kind, item.chart = "donut", "donut"
        item.trims, item.center, item.segments = trims, center, segs
        item.loading = (skel, [c for c in content if c is not center]) if loading else None   # a.draw brings the total
        return item

    # ------------------------------------------------------------ the line chart
    def line_chart(self, name, values=None, ticks=(0, 1000, 2000, 3000, 4000), labels=None, w=662, h=305,
                   fmt="{:,}", loading=False):
        """A line chart over a grid (Figma "Single Wave Graph"): the y labels (Regular 10.5, hint colour) right-aligned
        at the left, dashed lines (grey-200, 4 / 7) and a solid base line, the x labels (Regular 12) along the
        bottom, the line (#AAB6D5, 2 px) over an area that fades down (#AEB5C8), both at 80 %. a.draw(chart) reveals
        it from the left. values: the points, spread evenly (default: Figma's 64); ticks: the y scale, bottom to top;
        labels: the x labels (default 12 days). loading=True: skeletons at the y labels, no line, until a.load."""
        vals = list(values or VISITS)
        labels = DAYS if labels is None else labels
        n = f"{self.art}.{name}"
        top_c, bot_c, x0, lab_w = 9.6, h - 34.3, 46.0, 30.0
        ymin_v, ymax_v = ticks[0], ticks[-1]
        ys = [bot_c - (bot_c - top_c) * k / (len(ticks) - 1) for k in range(len(ticks))]
        k_y, k_x = f"{self.key}_{name}_y", f"{self.key}_{name}_x"
        kit.text_style(k_y, None, _color(HINT), size=10.5, lh=14, weight=350)
        kit.text_style(k_x, None, _color(HINT), size=12, lh=16, weight=350)
        grid = []
        for k, y in enumerate(ys):
            xs = x0 if k == 0 else 42.0
            kids = [El("PointsPath", {"isClosed": False}, [El("StraightVertex", {"x": xs, "y": y}),
                                                         El("StraightVertex", {"x": w, "y": y})], name=f"{n}.g{k}.p")]
            dash = [] if k == 0 else [El("DashPath", {"offset": 0}, [El("Dash", {"length": 4}),
                                                                     El("Dash", {"length": 7})])]
            kids.append(El("Stroke", {"thickness": 1, "cap": "round" if dash else "square"}, [
                El("SolidColor", {"colorValue": _color(GRID)}, name=f"{n}.g{k}.c")] + dash, name=f"{n}.g{k}.s"))
            grid.append(El("Shape", {}, kids, name=f"{n}.g{k}"))
        ylabels = [self._label(f"{name}Y{k}", fmt.format(v), k_y, 0, ys[k] - 7, lab_w, 14, "right")
                   for k, v in enumerate(ticks)]
        nx = len(labels)
        xlabels = [self._label(f"{name}X{i}", s, k_x, x0 - 4 + i * (w - x0 - 40) / max(1, nx - 1), h - 19, 48, 16,
                               "center") for i, s in enumerate(labels)]
        pw = w - x0
        pts = [(i * pw / max(1, len(vals) - 1), bot_c - (v - ymin_v) / (ymax_v - ymin_v) * (bot_c - top_c))
               for i, v in enumerate(vals)]
        top_y = min(p[1] for p in pts)
        area = El("Shape", {}, [El("PointsPath", {"isClosed": True}, [El("StraightVertex", {"x": x, "y": y})
                                                                      for x, y in pts + [(pw, bot_c), (0, bot_c)]],
                                   name=f"{n}.area.p"),
                                El("Fill", {}, [El("LinearGradient", {"startX": 0, "startY": top_y, "endX": 0,
                                                                      "endY": bot_c}, [
                                    El("GradientStop", {"colorValue": kit.argb("#aeb5c8", CHART_A), "position": 0},
                                       name=f"{n}.area.s0"),
                                    El("GradientStop", {"colorValue": kit.argb("#aeb5c8", 0), "position": 1},
                                       name=f"{n}.area.s1")], name=f"{n}.area.grad")], name=f"{n}.area.fill")],
                   name=f"{n}.area")
        stroke = El("Shape", {}, [El("PointsPath", {"isClosed": False}, [El("StraightVertex", {"x": x, "y": y})
                                                                         for x, y in pts], name=f"{n}.line.p"),
                                  El("Stroke", {"thickness": 2, "cap": "round", "join": "round"}, [
                                      El("SolidColor", {"colorValue": kit.argb("#aab6d5", CHART_A)}, name=f"{n}.line.c")],
                                     name=f"{n}.line.s")], name=f"{n}.line")
        # the line and its area in a clip that a.draw widens from the left (the drawing stays where it is)
        plot = kit.absolute(f"{n}.plot", [El("Node", {}, [stroke, area], name=f"{n}.plotArt")],
                            inset=(x0, 0, None, None), w=pw, h=bot_c + 1, clip=True, layoutWidthScaleType="fixed",
                            layoutHeightScaleType="fixed")
        kids = [plot] + ylabels + xlabels + [El("Node", {}, grid, name=f"{n}.grid")]
        skel, content = [], [plot] + ylabels + xlabels
        if loading:
            for k, y in enumerate(ys):
                sk = self.skeleton(f"{name}Sk{k}", 22, 8)
                kids.append(kit.absolute(f"{n}.sk{k}", [_el(sk)], inset=(lab_w - 22, y - 4, None, None),
                                         **kit.hug()))
                skel.append(f"{n}.sk{k}")
            self._hidden(*content)
        item = self._box(name, kids, "column", 0, 0, "topLeft", w, h)
        item.kind, item.chart = "line", "line"
        item.plot, item.plot_w = plot, pw
        item.loading = (skel, content) if loading else None
        return item

    # ------------------------------------------------------------ the dashboard shell
    def dashboard(self, name, page=(), site="Site Dashboard", rail=("i_stats", "-", "i_coupon", "i_settings", "-"),
                  selected="i_stats", menu=None, menu_title="Performance", menu_selected=0, w=1440, h=900, pad=32):
        """The site dashboard's window (Figma "ideal_customer_experience"): a top bar (58, white, a line under it,
        the site's name in Bold 10/14 capitals), the rail (58 wide: », then 46 px cells with 16 px icons; the
        selected one on a peach tile; "-" a divider), an optional PERFORMANCE menu (the product's: menu=["Highlights",
        "Visibility >", ...], ">" adds a chevron; menu_selected), and the page (grey #F5F5F7, padded `pad`) holding
        `page` (items stacked in a column, 24 apart).
        Targets: shell.rail_items[i] (shell.rail_tiles[i]: its tile, a.show / a.hide), shell.menu_items[i]
        (shell.menu_tiles[i])."""
        n = f"{self.art}.{name}"
        k_site = f"{self.key}_{name}_site"
        kit.text_style(k_site, None, _color(SECOND), size=10, lh=14, weight=700, ls=0.4)
        top = self._box(f"{name}Top", [kit.box(f"{n}.siteW", [kit.text(f"{n}.site.t", [(k_site, site.upper())],
                                                                        lp=kit.hug(), wrap=False)], h=14, **kit.hug())],
                        "row", 8, (17, 0, 17, 0), "centerLeft", "fill", 58, paints=[kit.solid(f"{n}.top.fill",
                                                                                               kit.WHITE)])
        self._edge(top, "bottom", LINE)
        expand = kit.box(f"{n}.expand", [kit.icon_slot(f"{n}.expandI", kit.ICON_FILES["i_expand"], _color(SECOND))],
                         w=32, h=32, flexDirectionValue="column", layoutAlignmentType="center",
                         layoutWidthScaleType="fixed", layoutHeightScaleType="fixed")
        head = self._box(f"{name}RailHead", [expand], "row", 0, (13, 9, 13, 9), "centerLeft", "fill", 50)
        self._edge(head, "bottom", LINE)
        cells, items, tiles = [], [], []
        for i, ic in enumerate(rail):
            if ic == "-":
                rule = kit.box(f"{n}.rule{i}", paints=[kit.solid(f"{n}.rule{i}.fill", _color(LINE))], h=1,
                               layoutWidthScaleType="fill", layoutHeightScaleType="fixed")
                cells.append(kit.box(f"{n}.ruleRow{i}", [rule], flexDirectionValue="column", paddingTop=4,
                                     paddingBottom=4, **kit.fill_w()))
                continue
            tile = kit.absolute(f"{n}.tile{i}", paints=[kit.solid(f"{n}.tile{i}.fill", _color("#fcd2c4"))],
                                inset=(7, 7, 7, 7), cornerRadiusTL=6, opacity=1 if ic == selected else 0)
            cell = self.wrap(f"{name}Rail{i}", [kit.box(f"{n}.cell{i}", [kit.icon_slot(
                f"{n}.railI{i}", kit.ICON_FILES[ic], _color(INK)), tile], w=46, h=46, flexDirectionValue="column",
                layoutAlignmentType="center", layoutWidthScaleType="fixed", layoutHeightScaleType="fixed")])
            cells.append(cell)
            items.append(cell)
            tiles.append(tile)
        group = self._box(f"{name}RailItems", cells, "column", 2, (6, 6, 6, 0), "topLeft", "fill", "hug")
        rail_box = self._box(f"{name}Rail", [head, group], "column", 0, 0, "topLeft", 58, "fill",
                             paints=[kit.solid(f"{n}.rail.fill", kit.WHITE)])
        self._edge(rail_box, "right", LINE)
        row = [rail_box]
        m_items, m_tiles = [], []
        if menu:
            k_t, k_i = f"{self.key}_{name}_mt", f"{self.key}_{name}_mi"
            kit.text_style(k_t, "Display/Display 4", _color(SECOND))
            kit.text_style(k_i, "Content/Body 14", _color(INK))
            mhead = self._box(f"{name}MenuHead", [kit.box(f"{n}.mtW", [kit.text(f"{n}.mt.t", [(k_t, menu_title.upper())],
                                                                                lp=kit.hug(), wrap=False)], h=16,
                                                          **kit.hug())], "row", 0, (16, 0, 16, 0), "centerLeft", "fill",
                              50)
            self._edge(mhead, "bottom", LINE)
            rows = []
            for i, e in enumerate(menu):
                lab, sub = (e[:-1].rstrip(), True) if e.endswith(">") else (e, False)
                sel = kit.absolute(f"{n}.mSel{i}", paints=[kit.solid(f"{n}.mSel{i}.fill", _color(PAGE_BG))],
                                   cornerRadiusTL=6, opacity=1 if i == menu_selected else 0)
                kids = [kit.box(f"{n}.mLab{i}", [kit.text(f"{n}.mLab{i}.t", [(k_i, lab)], lp=kit.hug(),
                                                          wrap=False)], h=20, **kit.hug()),
                        kit.box(f"{n}.mSp{i}", h=1, layoutWidthScaleType="fill", layoutHeightScaleType="fixed")]
                if sub:
                    kids.append(kit.icon_slot(f"{n}.mChev{i}", kit.ICON_FILES["chevron_right"], _color(INK)))
                kids.append(sel)    # last: a layout box draws its first child on top
                it = self._box(f"{name}Menu{i}", kids, "row", 8, (8, 0, 8, 0), "centerLeft", "fill", 40,
                               origin=(0.5, 0.5))
                rows.append(it)
                m_items.append(it)
                m_tiles.append(sel)
            mlist = self._box(f"{name}MenuItems", rows, "column", 2, (8, 8, 8, 8), "topLeft", "fill", "hug")
            mbox = self._box(f"{name}Menu", [mhead, mlist], "column", 0, 0, "topLeft", 200, "fill",
                             paints=[kit.solid(f"{n}.menu.fill", kit.WHITE)])
            self._edge(mbox, "right", LINE)
            row.append(mbox)
        body = self._box(f"{name}Page", list(page), "column", 24, pad, "topLeft", "fill", "fill",
                         paints=[kit.solid(f"{n}.page.fill", _color(PAGE_BG))], clip=True)
        row.append(body)
        main = self._box(f"{name}Main", row, "row", 0, 0, "topLeft", "fill", "fill")
        shell = self._box(name, [top, main], "column", 0, 0, "topLeft", w, h, clip=True,
                          paints=[kit.solid(f"{n}.fill", kit.WHITE)])
        shell.top, shell.page = top, body
        shell.rail_items, shell.rail_tiles = items, tiles
        shell.menu_items, shell.menu_tiles = m_items, m_tiles
        return shell

    # ------------------------------------------------------------ the whole Highlights page
    def aeo_highlights(self, name, kpis=None, donut=None, line=None, layout="figma", loading=False,
                       tabs=("7 days", "14 days", "30 days"), tab=0, title="Highlights",
                       subtitle="Get a snapshot of your site’s overall performance.", w=1101,
                       donut_title="LLMs visits", line_title="User visits"):
        """The AEO report's Highlights page: the title (Cal Sans 32/40) and its line (Regular 16/22), the date tabs
        (Pill_Tabs; tabs=None: none), the KPI cards in a row (kpis: [dict(value, label, trend, down, icon, tile,
        info)], default Figma's four), and two chart cards, 418 tall: the donut (donut: its segments) and the line
        chart (line: dict(values=, ticks=, labels=)). layout "figma": the donut at the left; "product": the line at
        the left, titled "Visits" / "LLMs Visits" unless given. loading=True: everything but the titles starts as
        skeletons; a.load(page) brings it in (the KPI cards one after another, then the charts draw).
        Targets: page.title, page.tabs, page.kpis[i] (.value, .chip), page.donut, page.line (their cards:
        page.donut_card, page.line_card)."""
        title_t = self.text(f"{name}Title", title, style="Display/Display 1", font="cal")
        sub_t = self.text(f"{name}Sub", subtitle, style="Content/Plain text")
        head = [self.column(f"{name}Heading", [title_t, sub_t], gap=4)]
        tabs_it = None
        if tabs:
            head.append(kit.box(f"{self.art}.{name}.headSp", h=1, layoutWidthScaleType="fill",
                                layoutHeightScaleType="fixed"))
            tabs_it = self.pill_tabs(f"{name}Tabs", count=len(tabs), selected=tab,
                                     **{f"label{i + 1}": t for i, t in enumerate(tabs)})
            head.append(tabs_it)
        header = self.row(f"{name}Header", head, gap=16, pad=(0, 0, 0, 8), align="bottomLeft", w="fill")   # 32 to the cards
        specs = KPIS if kpis is None else kpis
        cw = (w - 16 * (len(specs) - 1)) / len(specs)
        cards = [self.kpi_card(f"{name}Kpi{i}", **dict(dict(w=cw, loading=loading), **k)) for i, k in enumerate(specs)]
        krow = self.row(f"{name}Kpis", cards, gap=16, w="fill")
        product = layout == "product"
        if product:
            donut_title = "LLMs Visits" if donut_title == "LLMs visits" else donut_title
            line_title = "Visits" if line_title == "User visits" else line_title
        dw = 352
        lw = w - dw - 24
        d = self.donut(f"{name}Donut", segments=donut, w=dw - 48, loading=loading)
        ln = self.line_chart(f"{name}Line", w=lw - 48, loading=loading, **(line or {}))
        dcard = self.chart_card(f"{name}DonutCard", donut_title, d, w=dw, pad=(24, 48, 24, 24), align="topCenter")
        lcard = self.chart_card(f"{name}LineCard", line_title, ln, w=lw)
        crow = self.row(f"{name}Charts", [lcard, dcard] if product else [dcard, lcard], gap=24, align="topLeft",
                        w="fill")
        page = self.column(name, [header, krow, crow], gap=24, w=w)
        page.kind = "page"
        page.title, page.subtitle, page.tabs, page.kpis = title_t, sub_t, tabs_it, cards
        page.donut, page.line, page.donut_card, page.line_card = d, ln, dcard, lcard
        page.loadables = cards + ([ln, d] if product else [d, ln])
        return page


class DashboardActions:
    """a.load (skeletons -> content) and a.draw (the donut clockwise, the line from the left)."""

    def load(self, items, t=None, step=0.27, dur=0.6, draw=True, count=True):
        """Skeletons give way to the content (one state at a time: the skeleton fades out in 0.1 s, the content fades
        in over `dur`), item after item `step` s apart (the product: ~0.27 s). items: a KPI card, a chart, a page
        (all of its parts), or a list. draw: charts draw as they come in (a.draw); count: KPI numbers count up from
        0 and their trend chip comes after the number. Returns when the last one is in."""
        t = self._t(t)
        flat = []
        for it in self._list(items):
            flat += getattr(it, "loadables", None) or [it]
        end = t
        for i, it in enumerate(flat):
            ti = t + i * step
            if getattr(it, "loading", None):
                skel, content = it.loading
                for s in self._list(skel):
                    self.c.fade(ti, s if isinstance(s, str) else _el(s).name, 0.0, SWAP)
                for c in self._list(content):
                    n = _el(c).name
                    self.c.fade(ti + SWAP, n, 1.0, secs(dur))
                ti += SWAP
            end = max(end, ti + secs(dur))
            if getattr(it, "kind", None) == "kpi" and count:
                num = _number(self.c.by[self._run(it.value)].attrs.get("text", ""))
                if num:
                    c_end = self.count(it.value, num[0], ti, fmt=num[1])
                    if it.chip is not None:
                        n = _el(it.chip).name
                        self.c.set(0, n, "opacity", 0.0)
                        self.c.fade(c_end - 0.15, n, 1.0, kit.FADE)
                    end = max(end, c_end)
            if getattr(it, "chart", None) and draw:
                end = max(end, self.draw(it, ti))
            elif getattr(it, "kind", None) == "donut" and it.loading:
                self.c.fade(ti, _el(it.center).name, 1.0, secs(dur))
        self._note(end, f"load {', '.join(_el(i).name for i in flat)}")
        return end

    def draw(self, chart, t=None, dur=None, ease=None):
        """A chart draws itself: a donut clockwise from the top, one piece after another, and its total comes in;
        a line chart is revealed from the left (its line and area). Hidden until t. Returns the end."""
        t = self._t(t)
        dur = secs(dur) if dur is not None else DRAW[chart.chart]
        if chart.chart == "donut":
            curve = choreo.ease_curve(ease or "duda")
            t0, t1 = chart.trims[0][1], chart.trims[-1][2]
            nf = max(1, round(dur * FPS))
            for name, a, b in chart.trims:
                tr = self.c.track(name, "end")
                tr.keys[0]["v"] = a
                self.c.set(t, name, "end", a)
                prev = None
                for f in range(nf + 1):
                    head = t0 + (t1 - t0) * choreo.progress(curve, f / nf)
                    v = round(min(b, max(a, head)), 5)
                    if v != prev:
                        self.c.set(t + f / FPS, name, "end", v)
                        prev = v
            cn = _el(chart.center).name
            self.c.set(0, cn, "opacity", 0.0)
            self.c.fade(t + dur * 0.6, cn, 1.0, kit.SHORT)
        else:
            n = _el(chart.plot).name
            tr = self.c.track(n, "width")
            tr.keys[0]["v"] = 0.0
            self.c.set(t, n, "width", 0.0)
            self.c.move(t + 1 / FPS, n, "width", chart.plot_w, dur, ease or "scroll")
        self._note(t + dur, f"draw {_el(chart).name}")
        return t + dur
