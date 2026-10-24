"""The library's own artboards (hosts, not components). Each has its own host view model (outside the editor every
artboard plays its view model's default instance), with one property per placed component holding that placement's
data.

  "Catalog"     every component in its states, as the DS pages show them (read-only: nothing reacts to the mouse)
  "Prototype"   the components to use by hand (interactive): hover, click, type. The floating bar's x closes it and
                "Show bar" opens it again
  "Catalog motion"  the components going through their states on their own, in a loop (each one's own transitions:
                hover, press, typing, selection, loading, the AI status...), to review frame by frame
  "Prototype v03"   the v03 components to use by hand: toggles, checkboxes, a radio group, tabs, a list that selects,
                a dropdown whose menu sets its value, a tooltip on hover, "Generate" with the AI status
  "tests/Bar"   the pilot alone for the comparison with the visual edit v02 bar (left out of the .rev)
"""
import kit
from kit import (VM, El, Anim, Layer, use, box, absolute, text, text_style, hug, nested, solid, line, machine,
                 host_artboard, set_to, fire, listener, if_trigger, if_bool, tick, pose, icon_ref, ICON_FILES, color,
                 argb, hex_argb, WHITE)
from components.icon_button import IB, COLORS as IB_COLORS
from components.core_button import CB, COLOR_NAMES, TYPES
from components.divider import DIV
from components.smart_tag import TAG, COLORS as TAG_COLORS
from components.core_input import CI
from components.cursor import CURSOR
from components import floating_bar as fb
from components.toggle import TOGGLE
from components.checkbox import CHECKBOX
from components.radio import RADIO
from components.pill_tabs import PILL
from components.search_input import SEARCH
from components.status import STATUS, COLORS as STATUS_COLORS
from components.promo_tag import PROMO, TYPES as PROMO_TYPES
from components.tooltip import TIP
from components.loader import LOADER, SIZES as LOADER_SIZES
from components.icon_thumbnail import THUMB, THEMES as THUMB_THEMES, SIZES as THUMB_SIZES
from components.core_tabs import CTABS
from components.list_item import LI, STATES as LI_STATES
from components.menu_item import MI
from components.dropdown import DD
from components.ai_process import AIP
from components.text_area import TA
from components import ai_panel as aipanel
from components.skeleton import SKEL

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
                        [row(f"Cat.icons{i // 12}", icons[i:i + 12], gap=24)
                         for i in range(0, len(icons), 12)]))

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
            ("Message", dict(showMessage=True, message="We never share it")), ("No label", dict(showLabel=False)),
            ("Required + info (v04)", dict(required=True, labelIcon=True))]):
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
                 "edit + trash hover"),
            cell("Cat.bar2", h.bar("bar2", over=fb.STORYBOARD), "storyboard (v04)")]
    skels = [cell(f"Cat.sk{i}", h.place(f"sk{i}", "skel", SKEL, v, w, ht), s)
             for i, (s, v, w, ht) in enumerate([("Bar (shimmer)", {}, 160, 16), ("Line", {}, 104, 10),
                                                ("Circle", dict(circle=True), 36, 36),
                                                ("Still", dict(shimmer=False), 160, 16)])]
    secs.append(section("Cat.misc", "Divider · Cursor · VibeFloatingBar (pilot) · Skeleton (v06)",
                        [row("Cat.miscRow", misc, gap=32), row("Cat.barRow", bars, gap=32),
                         row("Cat.skRow", skels, gap=32, label="Skeleton")]))

    # v03 · selection controls
    sel = [cell(f"Cat.tog{i}", h.place(f"tog{i}", "toggle", TOGGLE, v), s)
           for i, (s, v) in enumerate([("Toggle off", {}), ("Toggle on", dict(on=True)),
                                       ("Disabled", dict(disabled=True)), ("Disabled on", dict(on=True, disabled=True)),
                                       ("Switch off", dict(variant=1)), ("Switch on", dict(variant=1, on=True)),
                                       ("Switch disabled", dict(variant=1, on=True, disabled=True))])]
    boxes = [cell(f"Cat.chk{i}", h.place(f"chk{i}", "checkbox", CHECKBOX, v), s)
             for i, (s, v) in enumerate([("Empty", {}), ("On", dict(state=1)), ("Partial", dict(state=2)),
                                         ("Disabled", dict(disabled=True)), ("Disabled on", dict(state=1, disabled=True))])]
    radios = [cell(f"Cat.rad{i}", h.place(f"rad{i}", "radio", RADIO, v), s)
              for i, (s, v) in enumerate([("Off", {}), ("On", dict(selected=True)), ("Disabled", dict(disabled=True)),
                                          ("Disabled on", dict(selected=True, disabled=True))])]
    secs.append(section("Cat.sel", "Core Toggle · Core Checkbox · Core Radio Button",
                        [row("Cat.togRow", sel, gap=32, label="Core Toggle"),
                         row("Cat.chkRow", boxes, gap=32, label="Core Checkbox"),
                         row("Cat.radRow", radios, gap=32, label="Core Radio Button")]))

    # tabs
    labels = dict(label1="Canvas", label2="Code", label3="Manage", label4="Settings")
    pills = [cell(f"Cat.pill{i}", h.place(f"pill{i}", "pill", PILL, dict(labels, **v), *wh), s)
             for i, (s, v, wh) in enumerate([
                 ("3 tabs", {}, ()), ("Selected 2nd", dict(selected=1), ()), ("2 tabs", dict(count=2), ()),
                 ("Icons", dict(icons=True), ()), ("Fill 320", dict(fill=True), (320, "hug"))])]
    ctabs = [cell(f"Cat.ctab{i}", h.place(f"ctab{i}", "ctabs", CTABS, dict(labels, **v)), s)
             for i, (s, v) in enumerate([("3 tabs", {}), ("4 tabs, 3rd selected", dict(count=4, selected=2))])]
    secs.append(section("Cat.tabs", "Pill_Tabs · Core Tabs",
                        [row("Cat.pillRow", pills, gap=32, label="Pill_Tabs"),
                         row("Cat.ctabRow", ctabs, gap=48, label="Core Tabs")]))

    # inputs, tags, tooltips
    search = [cell(f"Cat.srch{i}", h.place(f"srch{i}", "search", SEARCH, v, 248, "hug"), s)
              for i, (s, v) in enumerate([("Empty", {}), ("Focus", dict(focused=True)),
                                          ("Value", dict(value="Hero section")),
                                          ("Disabled", dict(disabled=True))])]
    statuses = [cell(f"Cat.st{c}", h.place(f"st{c}", "status", STATUS, dict(label=cname, color=c)), cname)
                for c, cname in enumerate(STATUS_COLORS)]
    st_more = [cell(f"Cat.stM{i}", h.place(f"stM{i}", "status", STATUS, dict(dict(label="Published", color=1), **v)),
                    s) for i, (s, v) in enumerate([("Border", dict(border=True)), ("Hover", dict(hover=True)),
                                                   ("Unread", dict(unread=True)), ("No dropdown", dict(dropdown=False))])]
    promos = [cell(f"Cat.promo{t}", h.place(f"promo{t}", "promo", PROMO, dict(type=t)), tname)
              for t, tname in enumerate(PROMO_TYPES)]
    tips = [cell("Cat.tip0", h.place("tip0", "tip", TIP, dict(
                text="Changes are saved as a draft until you publish.")), "Max 200"),
            cell("Cat.tip1", h.place("tip1", "tip", TIP, dict(text="Copy link", hug=True)), "Hug")]
    secs.append(section("Cat.more", "SearchInput · Status · Promotional Tag · Tooltip",
                        [row("Cat.srchRow", search, label="SearchInput"),
                         row("Cat.stRow", statuses, label="Status · color"),
                         row("Cat.stMore", st_more, label="Status · more"),
                         row("Cat.promoRow", promos, gap=32, label="Promotional Tag"),
                         row("Cat.tipRow", tips, gap=32, label="Tooltip")]))

    # loader, thumbnails
    loaders = [cell(f"Cat.load{i}", h.place(f"load{i}", "loader", LOADER, dict(size=i)), f"{px}px")
               for i, px in enumerate(LOADER_SIZES)]
    themes = [cell(f"Cat.th{t}", h.place(f"th{t}", "thumb", THUMB, dict(theme=t)), tname)
              for t, tname in enumerate(THUMB_THEMES)]
    th_more = ([cell(f"Cat.thS{i}", h.place(f"thS{i}", "thumb", THUMB, dict(size=i)), f"{px}px")
                for i, px in enumerate(THUMB_SIZES)]
               + [cell("Cat.thC", h.place("thC", "thumb", THUMB, dict(circle=True, theme=3)), "Circle"),
                  cell("Cat.thD", h.place("thD", "thumb", THUMB, dict(disabled=True)), "Disabled")])
    secs.append(section("Cat.thumbs", "Loader · Icon Thumbnail",
                        [row("Cat.loadRow", loaders, gap=32, label="Loader (always turns)"),
                         row("Cat.thRow", themes, gap=28, label="Icon Thumbnail · theme"),
                         row("Cat.thMore", th_more, gap=28, label="Icon Thumbnail · more")]))

    # lists, menus, dropdowns, AI status
    items = [cell(f"Cat.li{i}", h.place(f"li{i}", "li", LI, dict(title="Home page", secondary=st,
                                                                       state=i), 360, "hug"), st)
             for i, st in enumerate(LI_STATES)]
    items += [cell("Cat.liH", h.place("liH", "li", LI, dict(title="Home page", secondary="Hover", hover=True),
                                      360, "hug"), "Hover"),
              cell("Cat.liT", h.place("liT", "li", LI, dict(title="Blog", secondary="Tag, no suffix", tag=True,
                                                                   suffix=False, prefixTheme=3), 360, "hug"), "Tag")]
    li_rows = [row(f"Cat.liRow{i // 3}", items[i:i + 3], gap=24, label="ListItem" if i == 0 else " ")
               for i in range(0, len(items), 3)]
    menus = [cell(f"Cat.mi{i}", h.place(f"mi{i}", "mi", MI, dict(dict(label=lab), **v), 192, "hug"), s)
             for i, (s, lab, v) in enumerate([
                 ("Default", "Rename", {}), ("Icon", "Duplicate", dict(showIcon=True, icon=icon_ref("i_duplicate"))),
                 ("Hover", "Settings", dict(hover=True)), ("Selected", "Desktop", dict(selected=True)),
                 ("Destructive", "Delete", dict(destructive=True, showIcon=True, icon=icon_ref("i_trash")))])]
    drops = [cell(f"Cat.dd{i}", h.place(f"dd{i}", "dd", DD, dict(dict(label="Page"), **v), 240, "hug"), s)
             for i, (s, v) in enumerate([
                 ("Empty", {}), ("Value", dict(value="Home")), ("Open", dict(value="Home", open=True)),
                 ("Prefix", dict(value="Home", prefix=True)), ("Error", dict(error=True)),
                 ("Disabled", dict(value="Home", disabled=True))])]
    aips = [cell(f"Cat.aip{i}", h.place(f"aip{i}", "aip", AIP, v), s)
            for i, (s, v) in enumerate([("Thinking (shimmer)", {}), ("Done", dict(label="Thought for 3s", done=True)),
                                        ("Spinner", dict(label="Updating the project...", spinner=True)),
                                        ("Done, no chevron (v04)", dict(label="Done", done=True, chevron=False))])]
    areas = [cell(f"Cat.ta{i}", h.place(f"ta{i}", "ta", TA, dict(dict(label="Content"), **v), 358, 126), s)
             for i, (s, v) in enumerate([
                 ("Value", dict(value="Grow your business with a site that works as hard as you do")),
                 ("Placeholder", dict(placeholder="Write the headline")),
                 ("Focused, required", dict(value="Weekly report", focused=True, required=True))])]
    secs.append(section("Cat.lists", "ListItem · MenuListItem · CoreDropdown · AiProcessIndication",
                        li_rows + [row("Cat.miRow", menus, label="MenuListItem"),
                                   row("Cat.ddRowA", drops[:3], label="CoreDropdown"),
                                   row("Cat.ddRowB", drops[3:], label=" "),
                                   row("Cat.aipRow", aips, gap=32, label="AiProcessIndication"),
                                   row("Cat.taRow", areas, gap=32, label="Text Area (v04)")]))

    vm = h.vm()
    use(vm)
    page = box("Cat.page", secs, flexDirectionValue="column", layoutAlignmentType="topLeft", gapVertical=24,
               paddingLeft=32, paddingRight=32, paddingTop=32, paddingBottom=32, layoutWidthScaleType="fill",
               layoutHeightScaleType="hug")
    lay = Layer("Idle")
    lay.state("idle", None, entry=True)
    return host_artboard(vm, "Catalog", 1700, 5420, [page], machine([lay]), 0, 0, bg=PAGE_BG)


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


# ================================================================ timed states (Catalog motion, Prototype v03)
FIRE = object()   # put(..., click=FIRE) fires a trigger


def put(vm, slot, cvm, **props):
    """Actions on the placement at `slot` (its view model `cvm`): prop = value, or FIRE for a trigger."""
    out = []
    for k, v in props.items():
        path = (vm.ref(), vm.ref(slot), cvm.ref(k))
        if v is FIRE:
            out.append(fire(k, path=path))
        else:
            kind = "Boolean" if isinstance(v, bool) else "Number" if isinstance(v, (int, float)) else "String"
            out.append(set_to(kind, k, v, path=path))
    return out


def cycle(name, steps):
    """A layer that loops through steps = [(seconds, actions)]: each step's actions run as it starts, then it holds."""
    lay = Layer(name)
    for i, (secs, acts) in enumerate(steps):
        lay.state(f"s{i}", Anim(f"{name} {i}", secs), lay.go(f"s{(i + 1) % len(steps)}", at_end=True),
                  entry=i == 0, actions=acts)
    return lay


def typed_steps(vm, slot, cvm, string, cps=16):
    """Typing, one character per step (`typed` counts what shows)."""
    return [(1 / cps, put(vm, slot, cvm, typed=i)) for i in range(1, len(string) + 1)]


def menu_box(name, items, w=220):
    """A dropdown's menu (DS .CoreDropdwonMenu): white, radius 12, an edge, shadow-5, the items 2 apart."""
    edge = absolute(f"{name}.edge", paints=[line(f"{name}.edge.s", hex_argb("#e2e2e4"), 1)], inset=(0.5,) * 4,
                    cornerRadiusTL=11.5)
    inner = box(f"{name}.body", [edge] + items, w=w, paints=[solid(f"{name}.fill", WHITE)], flexDirectionValue="column",
                layoutAlignmentType="topLeft", gapVertical=2, paddingLeft=8, paddingRight=8, paddingTop=8,
                paddingBottom=8, cornerRadiusTL=12, layoutWidthScaleType="fixed", layoutHeightScaleType="hug")
    sh = kit.shadow_layers(f"{name}.sh", kit.DS["shadow"]["shadow-5"]["layers"], 12)
    return box(name, [inner] + sh, **hug())


def menu_layer(name, menu, open_path, display=False):
    """The menu shows while the dropdown is open: it fades in 150 ms, out 100 ms (display: also out of the way of
    the mouse while hidden)."""
    lay = Layer(name)
    hidden = [(menu, "opacity", 0)] + ([(f"{menu}.style", "displayValue", "none")] if display else [])
    show = Anim(f"{name} show", 0.15).move(menu, "opacity", 0, 0.15, 0, 1)
    hide = Anim(f"{name} hide", 0.1).move(menu, "opacity", 0, 0.1, 1, 0)
    if display:
        show.key(f"{menu}.style", "displayValue", 0, "flex")
        hide.key(f"{menu}.style", "displayValue", 0, "flex").key(f"{menu}.style", "displayValue", 0.1, "none")
    lay.state("hidden", pose(f"{name} hidden", [(t, p, v) for t, p, v in hidden], 0),
              lay.go("show", if_bool("open", True, path=open_path)), entry=True)
    lay.state("show", show, lay.go("hide", if_bool("open", False, path=open_path)))
    lay.state("hide", hide, lay.go("show", if_bool("open", True, path=open_path)), lay.go("hidden", at_end=True))
    return lay


# ================================================================ Catalog motion
def catalog_motion():
    h = Host("motion", "Motion")
    pl = h.place
    secs, lays = [], []

    # buttons, tags, the input, the bar, the cursor
    cb = cell("Mot.cb", pl("cb", "cb", CB, dict(label="Publish")), "CoreButton: hover, press, loading")
    ib = cell("Mot.ib", pl("ib", "ib", IB, dict(icon=icon_ref("i_edit"), color=4, size=1)),
              "Icon button: hover, press, selected")
    tag = cell("Mot.tag", pl("tag", "tag", TAG, dict(label="Websites", color=2)), "Smart_Tag: hover, x hover")
    inp = cell("Mot.ci", pl("ci", "ci", CI, dict(label="Email address", placeholder="Enter email address",
                                                 value="lila.hart@mail.com", typed=0), 260, "hug"),
               "CoreInput: focus, typing, error, success")
    bar = cell("Mot.bar", h.bar("bar"), "VibeFloatingBar: out and in")
    cur = cell("Mot.cur", h.place_at("cur", "cursor", CURSOR, {}, 6, 4, 40, 34), "Cursor: click")
    secs.append(section("Mot.a", "Catalog motion · each component goes through its states on its own",
                        [row("Mot.aRow", [cb, ib, tag, inp], gap=40), row("Mot.aRow2", [bar, cur], gap=40)]))

    # selection controls and tabs
    tog = cell("Mot.tog", pl("tog", "toggle", TOGGLE, {}), "Toggle: press, on / off")
    sw = cell("Mot.sw", pl("sw", "toggle", TOGGLE, dict(variant=1)), "Switch")
    chk = cell("Mot.chk", pl("chk", "checkbox", CHECKBOX, {}), "Checkbox: on, partial")
    radios = [pl(f"r{i}", "radio", RADIO, dict(selected=i == 0)) for i in range(3)]
    rad = cell("Mot.rad", box("Mot.radRow", radios, flexDirectionValue="row", gapHorizontal=16, **hug()),
               "Radio: the choice moves")
    pills = cell("Mot.pill", pl("pill", "pill", PILL, dict(label1="Canvas", label2="Code", label3="Manage")),
                 "Pill_Tabs")
    ctab = cell("Mot.ctab", pl("ctab", "ctabs", CTABS, dict(count=4, label1="Overview", label2="Pages", label3="SEO",
                                                            label4="Settings")), "Core Tabs")
    secs.append(section("Mot.b", "Selection controls · tabs",
                        [row("Mot.bRow", [tog, sw, chk, rad], gap=48), row("Mot.bRow2", [pills, ctab], gap=48)]))

    # search, status, tooltip, loader, AI status
    srch = cell("Mot.srch", pl("srch", "search", SEARCH, dict(value="Hero section", typed=0), 248, "hug"),
                "SearchInput: focus, typing")
    st = cell("Mot.st", pl("st", "status", STATUS, dict(label="Pending", color=2)), "Status: hover, Pending -> Published")
    stu = cell("Mot.stu", pl("stu", "status", STATUS, dict(label="New comment", color=6, dropdown=False)),
               "Status: unread dot")
    tip = cell("Mot.tip", box("Mot.tipBox", [pl("tip", "tip", TIP, dict(text="Copy link", hug=True, shown=False))],
                              w=120, h=34, layoutWidthScaleType="fixed", layoutHeightScaleType="fixed"),
               "Tooltip: in, out")
    load = cell("Mot.load", box("Mot.loadRow", [pl("load0", "loader", LOADER, dict(size=1)),
                                               pl("load1", "loader", LOADER, dict(size=2))],
                                flexDirectionValue="row", layoutAlignmentType="center", gapHorizontal=16, **hug()),
                "Loader: always turns")
    aip = cell("Mot.aip", pl("aip", "aip", AIP, {}), "AiProcessIndication: thinking -> done")
    aip2 = cell("Mot.aip2", pl("aip2", "aip", AIP, dict(label="Updating the project...", spinner=True)),
                "AiProcessIndication: spinner -> done")
    secs.append(section("Mot.c", "Search · status · tooltip · loader · AI status",
                        [row("Mot.cRow", [srch, st, stu, tip], gap=48), row("Mot.cRow2", [load, aip, aip2], gap=48)]))

    # lists, the dropdown and its menu
    items = [pl(f"li{i}", "li", LI, dict(title=t, secondary=s2, prefixTheme=th), 320, "hug")
             for i, (t, s2, th) in enumerate([("Home page", "Published", 0), ("About", "Draft", 3),
                                              ("Blog", "Published", 1)])]
    lst = cell("Mot.li", box("Mot.liCol", items, flexDirectionValue="column", gapVertical=8, **hug()),
               "ListItem: hover, select")
    labels = ["Home", "About", "Blog", "Contact"]
    mitems = [pl(f"m{i}", "mi", MI, dict(label=l, selected=i == 0), "fill", "hug") for i, l in enumerate(labels)]
    menu = menu_box("Mot.menu", mitems)
    dd = pl("dd", "dd", DD, dict(label="Page", value="Home"), 240, "hug")
    drop = cell("Mot.dd", box("Mot.ddCol", [dd, menu], w=260, h=250, flexDirectionValue="column", gapVertical=8,
                              layoutWidthScaleType="fixed", layoutHeightScaleType="fixed"),
                "CoreDropdown + menu: open, hover, choose")
    secs.append(section("Mot.d", "ListItem · CoreDropdown · MenuListItem", [row("Mot.dRow", [lst, drop], gap=64)]))

    vm = h.vm()
    use(vm)
    P = lambda slot, cvm, **kw: put(vm, slot, cvm, **kw)  # noqa: E731
    lays += [
        cycle("CoreButton", [(1.0, P("cb", CB, hover=False, loading=False)), (0.4, P("cb", CB, hover=True)),
                             (0.1, P("cb", CB, click=FIRE)), (1.6, P("cb", CB, loading=True, hover=False)),
                             (0.9, P("cb", CB, loading=False))]),
        cycle("Icon button", [(1.0, P("ib", IB, hover=False, selected=False)), (0.4, P("ib", IB, hover=True)),
                              (0.1, P("ib", IB, click=FIRE)), (1.5, P("ib", IB, selected=True, hover=False))]),
        cycle("Smart_Tag", [(1.0, P("tag", TAG, hover=False, removeHover=False)), (0.9, P("tag", TAG, hover=True)),
                            (1.1, P("tag", TAG, removeHover=True))]),
        cycle("CoreInput", [(0.9, P("ci", CI, focused=False, typed=0, error=False, success=False, showMessage=False)),
                            (0.3, P("ci", CI, focused=True))]
              + typed_steps(vm, "ci", CI, "lila.hart@")
              + [(1.6, P("ci", CI, error=True, message="Enter a valid email", showMessage=True))]
              + [(1 / 16, P("ci", CI, typed=i)) for i in range(11, 19)]
              + [(0.2, P("ci", CI, error=False)), (2.0, P("ci", CI, success=True, message="Looks good"))]),
        cycle("Bar", [(2.0, P("bar", fb.BAR, open=True)), (1.2, P("bar", fb.BAR, open=False))]),
        cycle("Cursor", [(1.2, []), (0.4, P("cur", CURSOR, click=FIRE))]),
        cycle("Toggle", [(1.0, P("tog", TOGGLE, on=False)), (0.1, P("tog", TOGGLE, pressed=True)),
                         (1.2, P("tog", TOGGLE, pressed=False, on=True)), (0.1, P("tog", TOGGLE, pressed=True)),
                         (0.2, P("tog", TOGGLE, pressed=False, on=False))]),
        cycle("Switch", [(1.2, P("sw", TOGGLE, on=False)), (1.2, P("sw", TOGGLE, on=True))]),
        cycle("Checkbox", [(1.0, P("chk", CHECKBOX, state=0)), (0.1, P("chk", CHECKBOX, pressed=True)),
                           (1.2, P("chk", CHECKBOX, pressed=False, state=1)), (1.2, P("chk", CHECKBOX, state=2))]),
        cycle("Radio", [(1.0, sum((P(f"r{j}", RADIO, selected=j == i) for j in range(3)), [])) for i in range(3)]),
        cycle("Pill_Tabs", [(1.2, P("pill", PILL, selected=i)) for i in range(3)]),
        cycle("Core Tabs", [(1.0, P("ctab", CTABS, selected=i)) for i in range(4)]),
        cycle("SearchInput", [(0.9, P("srch", SEARCH, focused=False, typed=0)), (0.3, P("srch", SEARCH, focused=True))]
              + typed_steps(vm, "srch", SEARCH, "Hero section") + [(1.8, [])]),
        cycle("Status", [(1.2, P("st", STATUS, label="Pending", color=2, hover=False)), (0.6, P("st", STATUS, hover=True)),
                         (1.6, P("st", STATUS, label="Published", color=1, hover=False))]),
        cycle("Status unread", [(1.2, P("stu", STATUS, unread=False)), (1.6, P("stu", STATUS, unread=True))]),
        cycle("Tooltip", [(1.0, P("tip", TIP, shown=False)), (1.6, P("tip", TIP, shown=True))]),
        cycle("AI status", [(2.6, P("aip", AIP, label="Thinking...", done=False)),
                            (1.8, P("aip", AIP, label="Thought for 3s", done=True))]),
        cycle("AI spinner", [(2.4, P("aip2", AIP, label="Updating the project...", spinner=True, done=False)),
                             (1.8, P("aip2", AIP, label="Project updated", spinner=False, done=True))]),
        cycle("ListItem", [(0.9, sum((P(f"li{j}", LI, hover=False, state=0) for j in range(3)), [])),
                           (0.5, P("li0", LI, hover=True)), (0.5, P("li0", LI, hover=False) + P("li1", LI, hover=True)),
                           (0.3, P("li1", LI, state=3)), (1.6, P("li1", LI, hover=False))]),
        cycle("Dropdown", [(1.0, P("dd", DD, open=False, value="Home") + sum((P(f"m{j}", MI, selected=j == 0, hover=False)
                                                                             for j in range(4)), [])),
                           (0.6, P("dd", DD, open=True)), (0.3, P("m1", MI, hover=True)),
                           (0.4, P("m1", MI, hover=False) + P("m2", MI, hover=True)),
                           (0.2, P("m2", MI, selected=True) + P("m0", MI, selected=False)),
                           (1.8, P("dd", DD, value="Blog", open=False) + P("m2", MI, hover=False))]),
        menu_layer("Menu", "Mot.menu", (vm.ref(), vm.ref("dd"), DD.ref("open")))]

    page = box("Mot.page", secs, flexDirectionValue="column", layoutAlignmentType="topLeft", gapVertical=24,
               paddingLeft=32, paddingRight=32, paddingTop=32, paddingBottom=32, layoutWidthScaleType="fill",
               layoutHeightScaleType="hug")
    return host_artboard(vm, "Catalog motion", 1700, 1224, [page], machine(lays), 3600, 0, bg=PAGE_BG)


# ================================================================ Prototype v03
def prototype_v03():
    h = Host("proto3", "Proto3")
    pl = h.place
    text_style("p3Label", "Content/Body", color("Typography/primary-text-color"))
    text_style("p3Head", "Headlines/He 3", color("Typography/secondary-text-color"))

    def lab(name, ctrl, caption):
        return box(name, [ctrl, text(f"{name}.t", [("p3Label", caption)], lp=hug(), wrap=False)],
                   flexDirectionValue="row", layoutAlignmentType="centerLeft", gapHorizontal=8, **hug())

    def group(name, title, kids, gap=16, direction="row"):
        head = text(f"{name}.h", [("p3Head", title)], lp=hug(), wrap=False)
        body = box(f"{name}.b", kids, flexDirectionValue=direction, layoutAlignmentType="centerLeft",
                   gapHorizontal=gap, gapVertical=gap, **hug())
        return box(name, [head, body], flexDirectionValue="column", layoutAlignmentType="topLeft", gapVertical=10,
                   **hug())

    on = dict(interactive=True)
    sel = group("P3.sel", "Toggle · Checkbox · Radio (a group: one choice)", [
        lab("P3.tog", pl("tog", "toggle", TOGGLE, dict(on, on=True)), "Auto-save"),
        lab("P3.sw", pl("sw", "toggle", TOGGLE, dict(on, variant=1)), "Dark mode"),
        lab("P3.c0", pl("c0", "checkbox", CHECKBOX, dict(on, state=1)), "Header"),
        lab("P3.c1", pl("c1", "checkbox", CHECKBOX, on), "Footer"),
        lab("P3.c2", pl("c2", "checkbox", CHECKBOX, on), "Blog"),
        lab("P3.r0", pl("r0", "radio", RADIO, dict(on, selected=True)), "Desktop"),
        lab("P3.r1", pl("r1", "radio", RADIO, on), "Tablet"),
        lab("P3.r2", pl("r2", "radio", RADIO, on), "Mobile")], gap=24)
    tabs = group("P3.tabs", "Pill_Tabs · Core Tabs", [
        pl("pill", "pill", PILL, dict(on, label1="Canvas", label2="Code", label3="Manage")),
        pl("ctab", "ctabs", CTABS, dict(on, count=4, label1="Overview", label2="Pages", label3="SEO",
                                        label4="Settings"))], gap=48)
    tipbox = box("P3.tipBox", [pl("tip", "tip", TIP, dict(text="Shown on the page's tab", hug=True, shown=False))],
                 w=200, h=34, flexDirectionValue="row", layoutAlignmentType="centerLeft",
                 layoutWidthScaleType="fixed", layoutHeightScaleType="fixed")
    info = box("P3.info", [pl("info", "ib", IB, dict(on, icon=icon_ref("i_info_circle"), color=1, size=0)), tipbox],
               flexDirectionValue="row", layoutAlignmentType="centerLeft", gapHorizontal=6, **hug())
    gen = box("P3.gen", [pl("go", "cb", CB, dict(on, label="Generate", showLeftIcon=True, leftIcon=icon_ref("i_plus"))),
                         box("P3.aipBox", [pl("aip", "aip", AIP, dict(label="Ready", done=True))], w=200, h=24,
                             layoutWidthScaleType="fixed", layoutHeightScaleType="fixed")],
              flexDirectionValue="row", layoutAlignmentType="centerLeft", gapHorizontal=16, **hug())
    more = group("P3.more", "Status (hover) · Tooltip (hover the i) · Generate -> the AI status", [
        pl("st0", "status", STATUS, dict(on, label="Published", color=1)),
        pl("st1", "status", STATUS, dict(on, label="Draft", color=0, unread=True)), info, gen], gap=32)
    items = [pl(f"li{i}", "li", LI, dict(on, title=t, secondary=s2, prefixTheme=th, state=3 if i == 0 else 0), 300,
                "hug") for i, (t, s2, th) in enumerate([("Home page", "Published", 0), ("About", "Draft", 3),
                                                        ("Blog", "Published", 1)])]
    labels = ["Home", "About", "Blog", "Contact"]
    mitems = [pl(f"m{i}", "mi", MI, dict(on, label=l, selected=i == 0), "fill", "hug") for i, l in enumerate(labels)]
    menu = menu_box("P3.menu", mitems)
    dd = pl("dd", "dd", DD, dict(label="Page", value="Home"), 240, "hug")
    ddhit = absolute("P3.ddHit", inset=(0, 26, 0, 0))
    ddwrap = box("P3.ddWrap", [ddhit, dd], flexDirectionValue="column", **hug())
    drop = box("P3.drop", [ddwrap, menu], w=260, h=230, flexDirectionValue="column", gapVertical=8,
               layoutWidthScaleType="fixed", layoutHeightScaleType="fixed")
    lists = group("P3.lists", "ListItem (click to select) · CoreDropdown (click it, then choose)",
                  [box("P3.liCol", items, flexDirectionValue="column", gapVertical=8, **hug()), drop], gap=48)

    h.props.append(("ddClick", "trigger", None))
    vm = h.vm()
    use(vm)
    P = lambda slot, cvm, **kw: put(vm, slot, cvm, **kw)  # noqa: E731
    path = lambda slot, cvm, prop: (vm.ref(), vm.ref(slot), cvm.ref(prop))  # noqa: E731
    t = tick()

    def group_layer(name, slots, cvm, pick):
        """Clicking one of `slots` runs pick(i): the actions that make it the chosen one."""
        lay = Layer(name)
        lay.state("ready", None, *[lay.go(f"pick{i}", if_trigger("clicked", path=path(s, cvm, "clicked")))
                                   for i, s in enumerate(slots)], entry=True)
        for i in range(len(slots)):
            lay.state(f"pick{i}", t, lay.go("ready", at_end=True), actions=pick(i))
        return lay

    radios = group_layer("Radio group", ["r0", "r1", "r2"], RADIO,
                         lambda i: sum((P(f"r{j}", RADIO, selected=False) for j in range(3) if j != i), []))
    lists_l = group_layer("List", ["li0", "li1", "li2"], LI,
                          lambda i: sum((P(f"li{j}", LI, state=3 if j == i else 0) for j in range(3)), []))
    menu_l = group_layer("Menu choice", [f"m{i}" for i in range(4)], MI,
                         lambda i: sum((P(f"m{j}", MI, selected=j == i) for j in range(4)), [])
                         + P("dd", DD, value=labels[i], open=False))
    ddp = path("dd", DD, "open")
    drop_l = Layer("Dropdown")
    drop_l.state("ready", None, drop_l.go("open", if_trigger("ddClick"), if_bool("open", False, path=ddp)),
                 drop_l.go("close", if_trigger("ddClick"), if_bool("open", True, path=ddp)), entry=True)
    drop_l.state("open", t, drop_l.go("ready", at_end=True), actions=P("dd", DD, open=True))
    drop_l.state("close", t, drop_l.go("ready", at_end=True), actions=P("dd", DD, open=False))
    hp = path("info", IB, "hover")
    tip_l = Layer("Tooltip")
    tip_l.state("off", None, tip_l.go("on", if_bool("hover", True, path=hp)), entry=True,
                actions=P("tip", TIP, shown=False))
    tip_l.state("on", None, tip_l.go("off", if_bool("hover", False, path=hp)), actions=P("tip", TIP, shown=True))
    gen_l = Layer("Generate")
    go_click = lambda: if_trigger("clicked", path=path("go", CB, "clicked"))  # noqa: E731
    gen_l.state("idle", pose("Generate idle", [("P3.aipBox", "opacity", 0)], 0), gen_l.go("think", go_click()),
                entry=True)
    gen_l.state("ready", None, gen_l.go("think", go_click()))
    gen_l.state("think", Anim("Generate think", 2.4).move("P3.aipBox", "opacity", 0, 0.15, 0, 1),
                gen_l.go("done", at_end=True),
                actions=P("go", CB, loading=True) + P("aip", AIP, label="Thinking...", done=False))
    gen_l.state("done", t, gen_l.go("ready", at_end=True),
                actions=P("go", CB, loading=False) + P("aip", AIP, label="Thought for 3s", done=True))
    layers = [radios, lists_l, menu_l, drop_l, menu_layer("Menu", "P3.menu", ddp, display=True), tip_l, gen_l]
    listeners = [listener("P3.ddHit", "click", fire("ddClick"), name="dropdown click")]
    page = box("Proto3.page", [sel, tabs, more, lists], flexDirectionValue="column", layoutAlignmentType="topLeft",
               gapVertical=36, paddingLeft=48, paddingTop=40, layoutWidthScaleType="fill",
               layoutHeightScaleType="fill")
    return host_artboard(vm, "Prototype v03", 1340, 680, [page], machine(layers, listeners), 1800, 1500, bg=WHITE)


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


# ================================================================ AiPanel (v05)
PANEL = aipanel.AIP
FLOATING = dict(copilot=True, placeholder="Ask anything", placeholderAfter="Reply to Copilot",   # the product's
                prompt="What can I ask Copilot to do?", titleAfter="Copilot Capabilities Inquiry",
                reply="Here's what you can ask me to do: add, rearrange or restyle sections, change colors, fonts and "
                      "spacing, update the header, footer and navigation, and write copy or generate images.",
                reply2="")
PANEL_LOOKS = [("Docked (Vibe)", {}, aipanel.DOCKED_W), ("Docked, answered (stage 5)", dict(stage=5), aipanel.DOCKED_W),
               ("Floating (Copilot)", FLOATING, aipanel.FLOATED_W),
               ("Floating, answered", dict(FLOATING, stage=5), aipanel.FLOATED_W)]


def panel_host(name, looks, x, y, title, layers=None):
    """A host artboard with one AiPanel per look (caption, values, width), side by side at the panel's height.
    layers(vm): the host's own state machine layers (else it only shows them)."""
    h = Host(name.replace(" ", ""), name)
    cells = [cell(f"{name}.c{i}", h.place(f"panel{i}", "aipanel", PANEL, v, w, aipanel.DEFAULT_H), s)
             for i, (s, v, w) in enumerate(looks)]
    vm = h.vm()
    use(vm)
    page = box(f"{name}.page", [section(f"{name}.sec", title, [row(f"{name}.row", cells, gap=32)])],
               flexDirectionValue="column", layoutAlignmentType="topLeft", paddingLeft=32, paddingRight=32,
               paddingTop=32, paddingBottom=32, layoutWidthScaleType="fill", layoutHeightScaleType="hug")
    lays = list(layers(vm)) if layers else [Layer("Idle").state("idle", None, entry=True)]
    w = 2 * 32 + 2 * 24 + 24 + sum(lk[2] for lk in looks) + 32 * (len(looks) - 1)
    return host_artboard(vm, name, w, 900, [page], machine(lays), x, y, bg=PAGE_BG)


def catalog_panel():
    """The AiPanel's looks: docked and floating, before and after a message."""
    return panel_host("Catalog AiPanel", PANEL_LOOKS, 0, 5500,
                      "AiPanel (v05) · docked (the Vibe chat) and floating (the Copilot)")


def motion_panel():
    """The AiPanel going through its states on a loop, as a piece drives it: it opens, the prompt is typed and sent,
    "Thinking...", the reply paragraph by paragraph, the action bar, it closes."""
    looks = [("Docked: the whole conversation", dict(hidden=True), aipanel.DOCKED_W),
             ("Floating: the whole conversation", dict(FLOATING, hidden=True), aipanel.FLOATED_W)]

    def layers(vm):
        lays = []
        for i, (_, v, _w) in enumerate(looks):
            slot = f"panel{i}"
            P = lambda **k: put(vm, slot, PANEL, **k)   # noqa: E731
            n = len(dict(aipanel.TEXTS, **v)["prompt"])
            typing = [(3 / 68, P(typed=min(c, n))) for c in range(3, n + 3, 3)]   # ~68 characters a second
            lays.append(cycle(f"AiPanel {i}", [
                (0.6, P(hidden=True, stage=0, typed=0, focused=False)), (1.4, P(hidden=False)),
                (0.5, P(hoverChip1=True)), (0.4, P(hoverChip1=False)), (0.4, P(focused=True))] + typing + [
                (0.3, P(hoverSend=True)), (0.4, P(stage=1)), (1.8, P(hoverSend=False)),
                (3.4, P(respond=FIRE)), (0.6, P(hoverCopy=True)), (0.8, P(hoverCopy=False)), (1.0, P(hidden=True))]))
        return lays
    return panel_host("Motion AiPanel", looks, 1900, 5500,
                      "AiPanel motion · each panel runs a whole conversation on a loop", layers)


def prototype_panel():
    """Both panels with `interactive` on: type in the field, Enter or the send button, a suggestion, » closes and the
    corner button opens it again; in the editor's data panel every trigger (send, respond, reset, open, close)."""
    looks = [("Docked: use it with the mouse and the keyboard", dict(interactive=True), aipanel.DOCKED_W),
             ("Floating", dict(FLOATING, interactive=True), aipanel.FLOATED_W)]
    return panel_host("Prototype AiPanel", looks, 3000, 5500, "AiPanel prototype")


def build():
    styles()
    return [catalog(), prototype(), catalog_motion(), prototype_v03(), bar_test(), catalog_panel(), motion_panel(),
            prototype_panel()]
