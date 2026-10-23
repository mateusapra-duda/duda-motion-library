"""Icon Thumbnail (DS: page "Graphic assets", 94621:20477).

DS props -> view model "Icon Thumbnail":
  the icon                icon        (artboard, default Icon/i_site; the DS default is i_duda, not in icons/ yet)
  Theme                   theme       0 Primary, 1 Secondary, 2 Grey, 3 Highlight, 4 Display, 5 Error, 6 Warning
  Size                    size        0 40px, 1 36px, 2 24px, 3 16px (the icon is 16, 12 at 16px)
  Circle                  circle
  State: Disabled         disabled    (the icon at 40 %)
thumb() / theme_layer() draw the same tile inside other components (ListItem's prefix).
"""
from kit import (VM, use, box, solid, nested_icon, match_layer, choice_layer, bool_layer, machine, component,
                 icon_ref, if_num, if_bool, set_to, hex_argb)

THEMES = ("Primary", "Secondary", "Grey", "Highlight", "Display", "Error", "Warning")
# the tile (Primary: primary 12 % over white) and the icon, per theme
BG = [hex_argb(c) for c in ("#feeee8", "#f6f6f8", "#ededee", "#f4effe", "#ffffff", "#fee9e9", "#ffecc8")]
FG = [hex_argb(c) for c in ("#272b35", "#272b35", "#272b35", "#6442ae", "#272b35", "#ac1616", "#df633b")]
SIZES = (40, 36, 24, 16)

THUMB = VM("thumb", "Icon Thumbnail", [
    ("icon", "artboard", icon_ref("i_site")), ("theme", "number", 0), ("size", "number", 0),
    ("circle", "boolean", False), ("disabled", "boolean", False), ("_fg", "color", FG[0])])


def thumb(n, icon_prop, fg_prop, size=40):
    """The tile: `<n>.thumb` (fill `<n>.thumb.fill`) with the icon `<n>.iconWrap` in its centre."""
    icon = box(f"{n}.iconWrap", [nested_icon(f"{n}.icon", icon_prop, fg_prop, "i_site")], origin=(0.5, 0.5),
               layoutWidthScaleType="hug", layoutHeightScaleType="hug")
    return box(f"{n}.thumb", [icon], paints=[solid(f"{n}.thumb.fill", BG[0])], flexDirectionValue="column",
               layoutAlignmentType="center", cornerRadiusTL=6, w=size, h=size, layoutWidthScaleType="fixed",
               layoutHeightScaleType="fixed")


def theme_layer(n, prop, fg_prop):
    return choice_layer("Theme", prop, THEMES, [(f"{n}.thumb.fill.color", "colorValue", *BG)],
                        actions={t: [set_to("Color", fg_prop, FG[i])] for i, t in enumerate(THEMES)})


def build():
    use(THUMB)
    n = "IconThumb"
    tile = thumb(n, "icon", "_fg")
    cases, looks_w, looks_r, looks_s = [], [], [], []
    for i, s in enumerate(SIZES):
        for circle in (False, True):
            cases.append((f"{s}px{' circle' if circle else ''}",
                          [if_num("size", "equal", i), if_bool("circle", circle)]))
            looks_w.append(s)
            looks_r.append(s / 2 if circle else (6 if s >= 36 else 4))
            looks_s.append(0.75 if s == 16 else 1)
    size_l = match_layer("Size", cases, [(f"{n}.thumb", "width", *looks_w), (f"{n}.thumb", "height", *looks_w),
                                         (f"{n}.thumb.style", "cornerRadiusTL", *looks_r),
                                         (f"{n}.iconWrap", "scaleX", *looks_s), (f"{n}.iconWrap", "scaleY", *looks_s)])
    disabled = bool_layer("Disabled", "disabled", [(f"{n}.iconWrap", "opacity", 1, 0.4)])
    return component("Icon Thumbnail", 40, 40, [tile], machine([theme_layer(n, "theme", "_fg"), size_l, disabled]),
                     layout={"layoutWidthScaleType": "hug", "layoutHeightScaleType": "hug"})
