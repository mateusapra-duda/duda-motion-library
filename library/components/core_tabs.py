"""Core Tabs (DS: page "Tabs & Breadcrumbs", 148647:14974, tab .Tab 97:2598).

DS props -> view model "Core Tabs":
  how many tabs: 2..6     count        tabs past `count` are hidden
  the selected tab        selected     0 = the first tab (a 2 px dark line under it)
  the labels              label1..label6
  (not here yet)          the counter, the unread dot and Disabled tabs; Full bleed
  (polish, not in the DS) the line grows from the tab's centre and the old one shrinks (200 ms, duda)
  (prototype)             interactive: a click selects the tab; changed fires
"""
from kit import (VM, use, box, absolute, solid, text, text_style, hug, match_layer, choice_layer, gate_layer,
                 listener, fire, set_to, machine, component, color, if_num)

N_TABS = 6
INK = color("Typography/primary-text-color")    # #272B35, every tab's label and the line
RULE = color("grey-200")                        # the divider under the row (#EDEDEE)
MS = 200

CTABS = VM("ctabs", "Core Tabs", [("count", "number", 3), ("selected", "number", 0)]
           + [(f"label{i}", "string", f"Tab {i}") for i in range(1, N_TABS + 1)]
           + [("interactive", "boolean", False), ("changed", "trigger", None)])


def build():
    use(CTABS)
    n = "CoreTabs"
    text_style("ctabLabel", "Headlines/He 3", INK)     # Medium 13/18
    tabs = []
    for i in range(1, N_TABS + 1):
        t = f"{n}.tab{i}"
        line = absolute(f"{t}.line", paints=[solid(f"{t}.line.fill", INK)], inset=(0, None, 0, 0), origin=(0.5, 0.5),
                        opacity=1 if i == 1 else 0, h=2, layoutHeightScaleType="fixed")
        line.attrs["scaleX"] = 1 if i == 1 else 0
        hit = absolute(f"{t}.hit", displayValue="none")
        label = text(f"{t}.label", [("ctabLabel", f"=label{i}")], lp=hug(), wrap=False)
        tabs.append(box(t, [hit, line, label], flexDirectionValue="column", layoutAlignmentType="bottomCenter",
                        paddingBottom=10, h=36, layoutWidthScaleType="hug", layoutHeightScaleType="fixed",
                        displayValue="flex" if i <= 3 else "none"))
    row = box(f"{n}.row", tabs, flexDirectionValue="row", layoutAlignmentType="topLeft", gapHorizontal=24, **hug())
    rule = absolute(f"{n}.rule", paints=[solid(f"{n}.rule.fill", RULE)], inset=(0, None, 0, 0), h=1,
                    layoutHeightScaleType="fixed")
    body = box(n, [row, rule], flexDirectionValue="column", layoutAlignmentType="topLeft", **hug())

    names = [f"{n}.tab{i}" for i in range(1, N_TABS + 1)]
    sel_l = choice_layer("Selected", "selected", [f"Tab {i}" for i in range(1, N_TABS + 1)], [
        look for j, t in enumerate(names)
        for look in ((f"{t}.line", "opacity", *[1 if j == k else 0 for k in range(N_TABS)]),
                     (f"{t}.line", "scaleX", *[1 if j == k else 0 for k in range(N_TABS)]))], ms=MS)
    counts = list(range(2, N_TABS + 1))
    count_l = match_layer("Count", [(f"{c} tabs", [if_num("count", "equal", c)]) for c in counts], [
        (f"{t}.style", "displayValue", *["flex" if j < c else "none" for c in counts])
        for j, t in enumerate(names) if j >= 2])
    layers = [gate_layer([f"{t}.hit" for t in names]), count_l, sel_l]
    listeners = [listener(f"{t}.hit", "click", set_to("Number", "selected", j), fire("changed"), name=f"select {j + 1}")
                 for j, t in enumerate(names)]
    return component("Core Tabs", 240, 36, [body], machine(layers, listeners),
                     layout={"layoutWidthScaleType": "hug", "layoutHeightScaleType": "hug"})
