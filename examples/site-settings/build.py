"""Site settings: a live, responsive screen made only of library components (library v06), for a demo page.

No timeline and no cursor: every component is interactive (hover, press, focus, typing) and the page drives the
rest through the view model. `inspect` (boolean) shows Figma's instance look on every component: a 1 px #9747FF
outline that follows the layout, and a chip with the component glyph and the component's name.

usage: .venv/bin/python -I pieces/<piece>/build.py [--heights]   (copy library/ to <piece>/lib/biblioteca-v06 first)
       --heights: the height the content needs at 360, 420, 600, 900 and 1280 wide (Fit.Layout)
"""
import copy
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "lib", "biblioteca-v06"))
import kit  # noqa: E402
from kit import El  # noqa: E402
from piece import Piece  # noqa: E402

RIVE = os.path.expanduser("~/.rive/bin/rive")
ART, W, H = "SiteSettings", 1280, 720
PURPLE = kit.hex_argb("#9747FF")
PAD = 24                       # page padding
CHIP_H, CHIP_GAP = 14, 1       # the inspect chip: height, room between it and the outline

p = Piece(ART, W, H, bg="Backgrounds/bg-white-color", here=HERE)


def comp(item, name):
    """Remember which library component an item is (the inspect chip's label)."""
    item.comp_name = name
    return item


# ------------------------------------------------------------ the screen (library components + text + boxes)
title = p.text("title", "Site settings", style="Headlines/He 0")
cancel = comp(p.button("cancel", label="Cancel", variant=1, color=0, interactive=True), "CoreButton")
publish = comp(p.button("publish", label="Publish", variant=0, color=0, interactive=True), "CoreButton")
actions = p.row("actions", [cancel, publish], gap=8)
header = p._box("header", [title, actions], "row", 16, 0, "spaceBetweenCenter", "fill", "hug")
divider = comp(p.divider("divider", w="fill", variant=1), "Divider")

site = comp(p.input("siteName", w="fill", label="Site name", value="Studio HQ", interactive=True), "CoreInput")
domain = comp(p.input("domain", w="fill", label="Custom domain", value="studiohq.com", success=True,
                      message="Domain connected", showMessage=True, interactive=True), "CoreInput")
email = comp(p.input("email", w="fill", label="Contact email", placeholder="name@studiohq.com", interactive=True),
             "CoreInput")
left = p._box("left", [site, domain, email], "column", 20, 0, "topLeft", "fill", "hug", minWidth=300)

pages_l = p.text("pagesLabel", "Pages", style="Headlines/He 2")
tags = [comp(p.tag("tagHome", label="Home page", color=2, prefix=True, interactive=True), "Smart_Tag")]
for slot, lab in (("tagAbout", "About"), ("tagBlog", "Blog"), ("tagContact", "Contact")):
    tags.append(comp(p.tag(slot, label=lab, color=0, interactive=True), "Smart_Tag"))
tag_row = p._box("tags", tags, "row", 8, 0, "centerLeft", "fill", "hug", flexWrapValue="wrap", gapVertical=22)
sections_l = p.text("sectionsLabel", "Sections", style="Headlines/He 2")
ibs = []
for slot, icon in (("secEdit", "i_edit"), ("secDuplicate", "i_duplicate"), ("secTrash", "i_trash"),
                   ("secAdd", "i_plus")):
    ibs.append(comp(p.icon_button(slot, icon=icon, variant=1 if slot == "secAdd" else 0,
                                  color=0 if slot == "secAdd" else 2, interactive=True), "Icon button"))
ib_row = p._box("sectionButtons", ibs, "row", 36, 0, "centerLeft", "fill", "hug", flexWrapValue="wrap",
                gapVertical=22)
pages = p._box("pages", [pages_l, tag_row], "column", 16, 0, "topLeft", "fill", "hug")
sections = p._box("sections", [sections_l, ib_row], "column", 16, 0, "topLeft", "fill", "hug")
right = p._box("right", [pages, sections], "column", 24, 0, "topLeft", "fill", "hug", minWidth=300)
# the two columns side by side when there is room for both (300 + 32 + 300), stacked when there is not
body = p._box("body", [left, right], "row", 32, 0, "topLeft", "fill", "hug", flexWrapValue="wrap", gapVertical=28)
content = p._box("content", [header, divider, body], "column", 20, 0, "topLeft", "fill", "hug")
p.layout(content, align="topLeft", pad=PAD)

placed = [cancel, publish, divider, site, domain, email] + tags + ibs     # reading order: the inspect stagger


# ------------------------------------------------------------ inspect: Figma's instance look on every component
kit.text_style("inspChip", "Content/Mini", kit.WHITE)
kit.STYLES["inspChip"].update(size=9, lh=12, weight=550)   # (kit.text_style can't override size: v03)


def inspect_overlay(item):
    """An outline box pinned 0.5 outside the placement (its 1 px stroke sits just outside the component and follows
    every reflow) with the chip above its top-left corner. Drawn over the component, hidden until `inspect`."""
    n = item.wrap.name
    glyph = kit.icon(os.path.join(HERE, "glyph.svg"), f"{n}.insp.glyph", kit.WHITE, size=8)
    gbox = kit.box(f"{n}.insp.gbox", [glyph], w=8, h=8, layoutWidthScaleType="fixed", layoutHeightScaleType="fixed")
    label = kit.text(f"{n}.insp.name", [("inspChip", item.comp_name)], lp=kit.hug(), wrap=False)
    chip = kit.absolute(f"{n}.insp.chip", [gbox, label], paints=[kit.solid(f"{n}.insp.chip.fill", PURPLE)],
                        inset=(-0.5, -(CHIP_H + CHIP_GAP + 0.5), None, None), flexDirectionValue="row",
                        layoutAlignmentType="centerLeft", gapHorizontal=3, paddingLeft=4, paddingRight=5,
                        paddingTop=1, paddingBottom=1, cornerRadiusTL=2, **kit.hug())
    box = kit.absolute(f"{n}.insp", [chip], paints=[kit.line(f"{n}.insp.edge", PURPLE, 1.0)],
                       inset=(-0.5, -0.5, -0.5, -0.5), opacity=0.0)
    item.wrap.children.insert(1, box)      # right after its style: the first child draws on top
    return f"{n}.insp"


overlays = [inspect_overlay(it) for it in placed]


# ------------------------------------------------------------ the artboard, its view model and state machine
p.props.append(("inspect", "boolean", False))
p.vm = kit.VM(p.key, f"{ART} view model", p.props)
kit.use(p.vm)
STEP, FADE = kit.MOTION["stagger"]["list"] / 1000, kit.FADE       # 67 ms list stagger, 150 ms fades
TIGHT = kit.MOTION["stagger"]["tight"] / 1000
lay = kit.Layer("Inspect")
a_in = kit.Anim("Inspect in", STEP * (len(overlays) - 1) + FADE)
a_out = kit.Anim("Inspect out", TIGHT * (len(overlays) - 1) + FADE)
for i, o in enumerate(overlays):
    a_in.key(o, "opacity", 0, 0.0).move(o, "opacity", i * STEP, i * STEP + FADE, 0.0, 1.0)
    a_out.key(o, "opacity", 0, 1.0).move(o, "opacity", i * TIGHT, i * TIGHT + FADE, 1.0, 0.0)
looks = [(o, "opacity", 0.0, 1.0) for o in overlays]
lay.state("off", kit.pose("Inspect off", looks, 0), lay.go("in", kit.if_bool("inspect", True)), entry=True)
lay.state("in", a_in, lay.go("on", at_end=True), lay.go("out", kit.if_bool("inspect", False)))
lay.state("on", kit.pose("Inspect on", looks, 1), lay.go("out", kit.if_bool("inspect", False)))
lay.state("out", a_out, lay.go("off", at_end=True), lay.go("in", kit.if_bool("inspect", True)))
lay.enter_if("on", kit.if_bool("inspect", True))

board = El("Artboard", {"defaultStateMachineId": f"@sm.{p.key}", "viewModelId": f"@{p.vm.ref()}",
                        "viewModelInstanceId": f"@vmi.{p.key}", "styleId": f"@{ART}Art.style",
                        "width": W, "height": H, "clip": True, "x": 0, "y": 0},
           [kit.style(f"{ART}Art"), kit.solid(f"{ART}Art.fill", p.bg), El("FocusData", {"canFocus": False}),
            p.root, kit.machine([lay])], name=ART, ref=f"art.{p.key}")


def write(board, here, measure=False):
    xml, _ = kit.assemble([board] + p.comps + p.icons, list(kit.VM.all))
    open(os.path.join(here, "scene.rml"), "w").write(xml + "\n")
    lib = os.path.relpath(os.path.join(HERE, "lib", "biblioteca-v06"), here)
    if not os.path.exists(os.path.join(here, "rive.yaml")):
        open(os.path.join(here, "rive.yaml"), "w").write(
            f'name: {"site-settings" if not measure else "measure"}\nmain: "{ART}"\nexclude:\n  - build\n  - web\n'
            f'  - renders\n  - {lib}/icons\n  - {lib}/ds\n')


def heights(widths=(360, 420, 600, 900, 1280)):
    """The height the content needs at each width: lay the screen out with the CLI (Fit.Layout, as on the web) and
    read the content box's bounds (a semantics marker)."""
    out = os.path.join(HERE, "build", "measure")
    os.makedirs(out, exist_ok=True)
    if not os.path.exists(os.path.join(out, "fonts")):
        os.symlink(os.path.join(HERE, "lib", "biblioteca-v06", "fonts"), os.path.join(out, "fonts"))
    b = copy.deepcopy(board)
    by = {}
    kit.walk(b, lambda e: by.__setitem__(e.name, e) if e.name else None)
    by[content.wrap.name].children.insert(1, El("SemanticData", {"role": "group", "label": "content"},
                                                name="content.measure"))
    font = kit.FONT_DIR[0]
    kit.FONT_DIR[0] = "fonts"
    write(b, out, measure=True)
    kit.FONT_DIR[0] = font
    res = {}
    for w in widths:
        r = subprocess.run([RIVE, out, "--semantics=-", f"--viewport={w}x2000", "--advance=2", "--quiet"],
                           capture_output=True, text=True, timeout=120)
        found = {}

        def walk(node):
            if node.get("label") == "content" and node.get("bounds"):
                found["b"] = node["bounds"]
            for c in node.get("children", []):
                walk(c)
        for root in json.loads(r.stdout)["roots"]:
            walk(root)
        bb = found["b"]
        res[w] = round(bb["y"] + bb["height"] + PAD)
    return res


write(board, HERE)
print(f"wrote scene.rml: {ART} {W}x{H} (Fit.Layout follows the canvas), {len(placed)} components, "
      f"view model '{p.vm.name}', 'State Machine 1'")
if "--heights" in sys.argv:
    print("content height by width:", heights())
