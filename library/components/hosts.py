"""The library's own artboards (hosts, not components). Each has its own host view model (outside the editor every
artboard plays its view model's default instance), with one property per placed component holding that placement's
data.

  "Catalog"     every component in its states, as the DS pages show them (read-only: nothing reacts to the mouse)
  "Prototype"   the components to use by hand (interactive): hover, click, type. The floating bar's x closes it and
                "Show bar" opens it again
  "tests/Bar"   the pilot alone for the comparison with the visual edit v02 bar (left out of the .rev)
"""
from kit import (VM, El, Layer, use, box, text, text_style, hug, nested, solid, machine, host_artboard, set_to,
                 if_trigger, tick, icon_ref, ICON_FILES, color, argb, WHITE)
from components.icon_button import IB, COLORS as IB_COLORS
from components.core_button import CB, COLOR_NAMES, TYPES
from components.divider import DIV
from components.smart_tag import TAG, COLORS as TAG_COLORS
from components.core_input import CI
from components.cursor import CURSOR
from components import floating_bar as fb

DARK_BG = color("Backgrounds/bg-dark-color")
PAGE_BG = color("Backgrounds/bg-grey-color")


class Host:
    """Collects the placements of one host artboard: each one a property of the host view model, holding a new
    instance of the component's view model."""

    def __init__(self, key, name):
        self.key, self.name, self.props, self.n = key, name, [], 0

    def path(self, slot):
        return (f"vm.{self.key}", f"vm.{self.key}.{slot}")

    def place(self, slot, comp, vm, values, w="hug", h="hug"):
        ref = vm.inst(f"vmi.{vm.key}.{self.key}.{slot}", values, name=f"{self.name} {slot}")
        self.props.append((slot, f"vm:{vm.key}", ref))
        return nested(f"{self.name}.{slot}", comp, self.path(slot), w, h)

    def place_at(self, slot, comp, vm, values, x, y, w, h):
        """A component placed by its origin at (x, y) of a fixed box (the Cursor: its origin is the arrow's tip)."""
        ref = vm.inst(f"vmi.{vm.key}.{self.key}.{slot}", values, name=f"{self.name} {slot}")
        self.props.append((slot, f"vm:{vm.key}", ref))
        nest = El("NestedArtboard", {"artboardId": f"@art.{comp}", "dataBindPathIds": self.path(slot), "x": x, "y": y},
                  [El("NestedStateMachine", {"animationId": f"@sm.{comp}"}, name=f"{self.name}.{slot} machine")],
                  name=f"{self.name}.{slot}")
        return box(f"{self.name}.{slot}.box", [nest], w=w, h=h, layoutWidthScaleType="fixed",
                   layoutHeightScaleType="fixed")

    def bar(self, slot, interactive=False, over=None, **values):
        ref = fb.instance(f"vmi.bar.{self.key}.{slot}", f"{self.name} {slot}", interactive, over, **values)
        self.props.append((slot, "vm:bar", ref))
        return nested(f"{self.name}.{slot}", "bar", self.path(slot), "hug", "hug")

    def vm(self):
        return VM(self.key, f"{self.name} host", self.props)


def styles():
    text_style("catTitle", "Headlines/He 0", color("Typography/primary-text-color"))
    text_style("catSub", "Headlines/He 3", color("Typography/primary-text-color"))
    text_style("catCap", "Content/Tiny", color("Typography/secondary-text-color"))
    text_style("catCapLight", "Content/Tiny", argb("#FFFFFF", 0.7))


def cell(name, child, caption, dark=False):
    return box(name, [child, text(f"{name}.cap", [("catCapLight" if dark else "catCap", caption)], lp=hug(),
                                  wrap=False)],
               flexDirectionValue="column", layoutAlignmentType="topLeft", gapVertical=6, **hug())


def row(name, cells, dark=False, gap=20, label=None):
    kids = list(cells)
    if label:
        kids.insert(0, box(f"{name}.lab", [text(f"{name}.labT", [("catCapLight" if dark else "catCap", label)],
                                                lp=hug(), wrap=False)], w=176, layoutWidthScaleType="fixed",
                           layoutHeightScaleType="hug"))
    return box(name, kids, paints=[solid(f"{name}.bg", DARK_BG)] if dark else (), flexDirectionValue="row",
               layoutAlignmentType="topLeft", gapHorizontal=gap, paddingLeft=12, paddingRight=12, paddingTop=10,
               paddingBottom=10, cornerRadiusTL=8, **hug())


def section(name, title, rows):
    return box(name, [text(f"{name}.title", [("catTitle", title)], lp=hug(), wrap=False)] + rows,
               paints=[solid(f"{name}.bg", WHITE)], flexDirectionValue="column", layoutAlignmentType="topLeft",
               gapVertical=8, paddingLeft=24, paddingRight=24, paddingTop=20, paddingBottom=20, cornerRadiusTL=12,
               layoutWidthScaleType="fill", layoutHeightScaleType="hug")


# ================================================================ Catalog
def catalog():
    h = Host("cat", "Catalog")
    secs = []

    # icons: every DS icon in the library, as its own component (no data: the default dark)
    icons = []
    for nm in ICON_FILES:
        icons.append(cell(f"Cat.icon.{nm}", El("NestedArtboardLayout", {
            "artboardId": f"@{icon_ref(nm)}", "instanceWidth": 16, "instanceHeight": 16,
            "instanceWidthScaleType": "fixed", "instanceHeightScaleType": "fixed"}, name=f"Cat.icon.{nm}.c"), nm))
    secs.append(section("Cat.icons", "Icons · Icon/<DS name> (16, stroke 1.5)",
                        [row("Cat.iconsA", icons[:12], gap=24), row("Cat.iconsB", icons[12:], gap=24)]))

    # Icon button: a row per color, the states across
    ib_rows = []
    states = [("Default", {}), ("Hover", dict(hover=True)), ("Selected", dict(selected=True)),
              ("Focus", dict(focused=True)), ("Disabled", dict(disabled=True)), ("Loading", dict(loading=True)),
              ("Box", dict(variant=1)), ("Box hover", dict(variant=1, hover=True)), ("Border", dict(border=True)),
              ("Large", dict(size=1))]
    for c, cname in enumerate(IB_COLORS):
        cells = [cell(f"Cat.ib{c}.{i}", h.place(f"ib{c}_{i}", "ib", IB, dict(dict(size=0, color=c, icon=icon_ref(
            "i_duplicate" if c % 2 else "i_options")), **v)), s, dark=cname == "Light")
                 for i, (s, v) in enumerate(states)]
        ib_rows.append(row(f"Cat.ibRow{c}", cells, dark=cname == "Light", label=cname))
    secs.append(section("Cat.ib", "Icon button · color x state (Small 24; Large 32)", ib_rows))

    # CoreButton
    cb_rows = []
    cb_states = {0: [("Default", {}), ("Hover", dict(hover=True)), ("Selected", dict(selected=True)),
                     ("Focus", dict(focused=True)), ("Disabled", dict(disabled=True)), ("Loading", dict(loading=True))],
                 1: [("Default", {}), ("Hover", dict(hover=True)), ("Selected", dict(selected=True)),
                     ("Focus", dict(focused=True)), ("Disabled", dict(disabled=True))],
                 2: [("Default", {}), ("Hover", dict(hover=True)), ("Focus", dict(focused=True)),
                     ("Disabled", dict(disabled=True))]}
    for v in (0, 1, 2):
        for c, cname in enumerate(COLOR_NAMES[v]):
            dark = cname in ("Light transparent", "Light")
            cells = [cell(f"Cat.cb{v}{c}.{i}", h.place(f"cb{v}{c}_{i}", "cb", CB, dict(dict(
                label=cname if v < 2 else f"{cname} link", variant=v, color=c), **vals)), s, dark=dark)
                     for i, (s, vals) in enumerate(cb_states[v])]
            cb_rows.append(row(f"Cat.cbRow{v}{c}", cells, dark=dark, label=f"{TYPES[v]} · {cname}"))
    sizes = []
    for v in (0, 1, 2):
        for s, sname in enumerate(("Small", "Regular", "Large")):
            if v == 2 and s == 2:
                continue
            sizes.append(cell(f"Cat.cbS{v}{s}", h.place(f"cbS{v}{s}", "cb", CB, dict(
                label=sname, variant=v, size=s, showLeftIcon=True, leftIcon=icon_ref("i_plus"))),
                f"{TYPES[v]} {sname}"))
    cb_rows.append(row("Cat.cbSizes", sizes, label="Sizes + left icon"))
    extras = [cell("Cat.cbE0", h.place("cbE0", "cb", CB, dict(label="Next", showRightIcon=True)), "Right icon"),
              cell("Cat.cbE1", h.place("cbE1", "cb", CB, dict(label="Edit", variant=1, size=0, minWidth=72)),
                   "Secondary Small, minWidth 72"),
              cell("Cat.cbE2", h.place("cbE2", "cb", CB, dict(label="Delete", color=3, showLeftIcon=True,
                                                               leftIcon=icon_ref("i_trash"))), "Destructive + icon"),
              cell("Cat.cbE3", h.place("cbE3", "cb", CB, dict(label="Add", variant=2, color=1, showLeftIcon=True,
                                                               hover=True)), "Text hover + icon")]
    cb_rows.append(row("Cat.cbExtras", extras, label="More"))
    secs.append(section("Cat.cb", "CoreButton · type x color x state", cb_rows))

    # Smart_Tag, Divider, Cursor, CoreInput
    tags = []
    for c, cname in enumerate(TAG_COLORS):
        for i, (s, vals) in enumerate([("Default", {}), ("Hover", dict(hover=True)), ("Border", dict(border=True)),
                                       ("Prefix", dict(prefix=True)), ("x hover", dict(removeHover=True)),
                                       ("20 Full", dict(size=0, radius=1)),
                                       ("20 Full prefix", dict(size=0, radius=1, prefix=True))]):
            tags.append(cell(f"Cat.tag{c}.{i}", h.place(f"tag{c}_{i}", "tag", TAG, dict(dict(label=cname, color=c),
                                                                                         **vals)), s))
    tag_rows = [row(f"Cat.tagRow{c}", tags[c * 7:(c + 1) * 7], label=TAG_COLORS[c]) for c in range(3)]
    secs.append(section("Cat.tag", "Smart_Tag · color x state (26; 20 Full)", tag_rows))

    inputs = []
    for i, (s, vals) in enumerate([
            ("Empty", {}), ("Active", dict(value="lila.hart@mail.com")), ("Focus", dict(value="lila.hart@mail.com",
                                                                                      focused=True)),
            ("Error", dict(value="lila.hart@", error=True, showMessage=True, message="Enter a valid email")),
            ("Success", dict(value="lila.hart@mail.com", success=True, showMessage=True, message="Looks good")),
            ("Warning", dict(value="lila", warning=True, showMessage=True, message="Check this")),
            ("Read-only", dict(value="lila.hart@mail.com", readOnly=True)),
            ("Disabled", dict(value="lila.hart@mail.com", disabled=True)),
            ("Grey theme", dict(theme=1, value="lila.hart@mail.com")), ("Compact", dict(size=1, value="Compact")),
            ("Message", dict(showMessage=True, message="We never share it")), ("No label", dict(showLabel=False))]):
        inputs.append(cell(f"Cat.ci{i}", h.place(f"ci{i}", "ci", CI, dict(dict(label="Email address",
                                                                             placeholder="Enter email address"),
                                                                        **vals), 220, "hug"), s))
    ci_rows = [row("Cat.ciRowA", inputs[:6]), row("Cat.ciRowB", inputs[6:])]
    secs.append(section("Cat.ci", "CoreInput · state (Default; Grey; Compact)", ci_rows))

    misc = [cell("Cat.div0", h.place("div0", "div", DIV, dict(variant=0), 240, 18), "Divider · With text"),
            cell("Cat.div1", h.place("div1", "div", DIV, dict(variant=1), 240, 18), "No text"),
            cell("Cat.div2", h.place("div2", "div", DIV, dict(variant=2), 1, 24), "Vertical"),
            cell("Cat.cur0", h.place_at("cur0", "cursor", CURSOR, {}, 6, 4, 40, 34), "Cursor"),
            cell("Cat.cur1", h.place_at("cur1", "cursor", CURSOR, dict(shadow=True), 6, 4, 40, 34),
                 "Cursor · shadow")]
    bars = [cell("Cat.bar0", h.bar("bar0"), "VibeFloatingBar"),
            cell("Cat.bar1", h.bar("bar1", over={"edit": dict(hover=True), "trash": dict(hover=True)}),
                 "edit + trash hover")]
    secs.append(section("Cat.misc", "Divider · Cursor · VibeFloatingBar (pilot)",
                        [row("Cat.miscRow", misc, gap=32), row("Cat.barRow", bars, gap=32)]))

    vm = h.vm()
    use(vm)
    page = box("Cat.page", secs, flexDirectionValue="column", layoutAlignmentType="topLeft", gapVertical=24,
               paddingLeft=32, paddingRight=32, paddingTop=32, paddingBottom=32, layoutWidthScaleType="fill",
               layoutHeightScaleType="hug")
    lay = Layer("Idle")
    lay.state("idle", None, entry=True)
    return host_artboard(vm, "Catalog", 1700, 3000, [page], machine([lay]), 0, 0, bg=PAGE_BG)


# ================================================================ Prototype
def prototype():
    h = Host("proto", "Prototype")
    bar = h.bar("bar", interactive=True)
    show = h.place("showBar", "cb", CB, dict(label="Show bar", interactive=True, showLeftIcon=True,
                                              leftIcon=icon_ref("i_edit")))
    btns = [show, h.place("cancel", "cb", CB, dict(label="Cancel", variant=1, interactive=True)),
            h.place("learn", "cb", CB, dict(label="Learn more", variant=2, interactive=True, showRightIcon=True))]
    ibs = [h.place(f"ib{i}", "ib", IB, dict(dict(icon=icon_ref(ic), size=0, color=4, interactive=True), **x))
           for i, (ic, x) in enumerate([("i_plus", {}), ("i_options", {}), ("i_search", dict(hoverAnimated=True)),
                                        ("i_trash", dict(variant=1)), ("i_send", dict(color=0, size=1))])]
    tags = [h.place(f"tag{i}", "tag", TAG, dict(label=lab, color=c, interactive=True, prefix=c == 0))
            for i, (lab, c) in enumerate([("Home page", 0), ("Header", 1), ("Hero", 2)])]
    field = h.place("input", "ci", CI, dict(label="Page title", placeholder="Type a title", interactive=True,
                                            showMessage=True, message="Shown in the browser tab"), 320, "hug")
    div = h.place("divider", "div", DIV, dict(variant=1), 560, 18)
    rowf = lambda nm, kids, gap=12: box(nm, kids, flexDirectionValue="row", layoutAlignmentType="center",  # noqa
                                        gapHorizontal=gap, **hug())
    page = box("Proto.page", [box("Proto.barSlot", [bar], h=80, layoutWidthScaleType="hug", layoutHeightScaleType="fixed",
                                  flexDirectionValue="column", layoutAlignmentType="bottomCenter"),
                              rowf("Proto.btns", btns), rowf("Proto.ibs", ibs, 8), div, rowf("Proto.tags", tags, 8),
                              field],
               flexDirectionValue="column", layoutAlignmentType="topCenter", gapVertical=28, paddingTop=40,
               layoutWidthScaleType="fill", layoutHeightScaleType="fill")
    vm = h.vm()
    use(vm)
    # the bar's x closes the bar; "Show bar" opens it again
    lay = Layer("Bar")
    t = tick()
    dismiss = (vm.ref(), vm.ref("bar"), fb.BAR.ref("dismiss"), IB.ref("clicked"))
    lay.state("ready", None, lay.go("close", if_trigger("clicked", path=dismiss)),
              lay.go("open", if_trigger("clicked", path=(vm.ref(), vm.ref("showBar"), CB.ref("clicked")))),
              entry=True)
    lay.state("close", t, lay.go("ready", at_end=True),
              actions=[set_to("Boolean", "open", False, path=(vm.ref(), vm.ref("bar"), fb.BAR.ref("open")))])
    lay.state("open", t, lay.go("ready", at_end=True),
              actions=[set_to("Boolean", "open", True, path=(vm.ref(), vm.ref("bar"), fb.BAR.ref("open")))])
    return host_artboard(vm, "Prototype", 1340, 638, [page], machine([lay]), 1800, 0, bg=WHITE)


# ================================================================ tests/Bar
def bar_test():
    """The bar alone on white, opening at frame 0 (as the visual edit's selection), interactive for the hover test."""
    h = Host("tBar", "tests/Bar")
    bar = h.bar("bar", interactive=True, open=False)
    vm = h.vm()
    use(vm)
    lay = Layer("Script")
    lay.state("start", None, entry=True,
              actions=[set_to("Boolean", "open", True, path=(vm.ref(), vm.ref("bar"), fb.BAR.ref("open")))])
    stage = box("tBar.stage", [bar], flexDirectionValue="column", layoutAlignmentType="center",
                layoutWidthScaleType="fill", layoutHeightScaleType="fill")
    # the visual edit's canvas colour behind the bar, so the comparison only shows the bar
    return host_artboard(vm, "tests/Bar", 420, 120, [stage], machine([lay]), 1800, 800, bg=argb("#F6F3EE"))


def build():
    styles()
    return [catalog(), prototype(), bar_test()]
