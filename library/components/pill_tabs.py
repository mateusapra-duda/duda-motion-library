"""Pill_Tabs (DS: page "Tabs", Pill_Tabs + .Tabs).

DS props -> view model "Pill_Tabs":
  how many tabs: 2..6     count        tabs past `count` are hidden
  the selected tab        selected     0 = the first tab
  the labels              label1..label6
  Width: Hug | Fill       fill         Hug: each tab hugs its label (pad 8); Fill: the tabs share the width the host
                                       gives (pad 4)
  Icon                    icons        a 16 px icon before every label; icon1..icon6 (artboards, default Icon/i_site)
  (polish, not in the DS) the white tab crossfades to the new one (200 ms, duda); the icons switch colour at once
  (prototype)             interactive: a click selects the tab; changed fires
"""
from kit import (VM, use, box, absolute, solid, text, text_style, hug, nested_icon, shadow_layers, match_layer,
                 choice_layer, bool_layer, gate_layer, listener, fire, set_to, machine, component, color, icon_ref,
                 if_num, DS, WHITE)

N_TABS = 6
ON = color("Typography/primary-text-color")        # #272B35
OFF = color("Typography/secondary-text-color")     # #5D6068
TRACK = color("grey-200")    # #EDEDEE, as the DS component (the newer bg-med-grey token is #E4E4E6)
MS = 200

PILL = VM("pill", "Pill_Tabs", [
    ("count", "number", 3), ("selected", "number", 0)]
    + [(f"label{i}", "string", f"Tab {i}") for i in range(1, N_TABS + 1)]
    + [("fill", "boolean", False), ("icons", "boolean", False)]
    + [(f"icon{i}", "artboard", icon_ref("i_site")) for i in range(1, N_TABS + 1)]
    + [("interactive", "boolean", False), ("changed", "trigger", None)]
    + [(f"_fg{i}", "color", ON if i == 1 else OFF) for i in range(1, N_TABS + 1)])


def build():
    use(PILL)
    n = "PillTabs"
    text_style("pillLabel", "Headlines/He 2", OFF)
    shadow = DS["shadow"]["shadow-3"]["layers"]
    tabs = []
    for i in range(1, N_TABS + 1):
        t = f"{n}.tab{i}"
        sel = absolute(f"{t}.sel", [absolute(f"{t}.selFill", paints=[solid(f"{t}.selFill.fill", WHITE)],
                                             cornerRadiusTL=6)] + shadow_layers(f"{t}.sh", shadow, 6),
                       opacity=1 if i == 1 else 0)
        icon = box(f"{t}.iconWrap", [nested_icon(f"{t}.icon", f"icon{i}", f"_fg{i}", "i_site")], displayValue="none",
                   **hug())
        label = text(f"{t}.label", [("pillLabel", f"=label{i}")], lp=hug(), wrap=False)
        hit = absolute(f"{t}.hit", displayValue="none")
        # flow: icon, label (the hit draws on top, the white tab under everything)
        tabs.append(box(t, [hit, icon, label, sel], flexDirectionValue="row", layoutAlignmentType="center",
                        gapHorizontal=4, paddingLeft=8, paddingRight=8, cornerRadiusTL=6, h=28, layoutWidthScaleType="hug",
                        layoutHeightScaleType="fixed", flexBasis=0, flexBasisUnitsValue="auto",
                        displayValue="flex" if i <= 3 else "none"))
    row = box(n, tabs, paints=[solid(f"{n}.track", TRACK)], flexDirectionValue="row", layoutAlignmentType="centerLeft",
              paddingTop=2, paddingRight=2, paddingBottom=2, paddingLeft=2, cornerRadiusTL=8, h=32,
              layoutWidthScaleType="hug", layoutHeightScaleType="fixed")

    tab_names = [f"{n}.tab{i}" for i in range(1, N_TABS + 1)]
    sel_l = choice_layer("Selected", "selected", [f"Tab {i}" for i in range(1, N_TABS + 1)], [
        (f"{t}.sel", "opacity", *[1 if j == k else 0 for k in range(N_TABS)]) for j, t in enumerate(tab_names)] + [
        (f"{t}.label.pillLabel.color", "colorValue", *[ON if j == k else OFF for k in range(N_TABS)])
        for j, t in enumerate(tab_names)],
        actions={f"Tab {k + 1}": [set_to("Color", f"_fg{j + 1}", ON if j == k else OFF) for j in range(N_TABS)]
                 for k in range(N_TABS)}, ms=MS)
    counts = list(range(2, N_TABS + 1))
    count_l = match_layer("Count", [(f"{c} tabs", [if_num("count", "equal", c)]) for c in counts], [
        (f"{t}.style", "displayValue", *["flex" if j < c else "none" for c in counts])
        for j, t in enumerate(tab_names) if j >= 2])
    # Fill: the row takes the host's width and the tabs share it equally (flex basis 0 points); Hug: everything hugs
    # (layoutWidthScaleType 1 fill, 2 hug; flexBasisUnitsValue 1 points, 3 auto)
    fill_l = bool_layer("Fill", "fill", [(f"{n}.style", "layoutWidthScaleType", 2, 1)] + [
        look for t in tab_names for look in ((f"{t}.style", "layoutWidthScaleType", 2, 1),
                                             (f"{t}.style", "flexBasisUnitsValue", 3, 1),
                                             (f"{t}.style", "paddingLeft", 8, 4),
                                             (f"{t}.style", "paddingRight", 8, 4))],
        ms=0)
    icons_l = bool_layer("Icon", "icons", [(f"{t}.iconWrap.style", "displayValue", "none", "flex")
                                           for t in tab_names], ms=0)
    layers = [gate_layer([f"{t}.hit" for t in tab_names]), count_l, fill_l, icons_l, sel_l]
    listeners = [listener(f"{t}.hit", "click", set_to("Number", "selected", j), fire("changed"), name=f"select {j + 1}")
                 for j, t in enumerate(tab_names)]
    return component("Pill_Tabs", 240, 32, [row], machine(layers, listeners),
                     layout={"layoutWidthScaleType": "hug", "layoutHeightScaleType": "hug"})
