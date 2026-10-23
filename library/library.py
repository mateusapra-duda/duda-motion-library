"""The library's components in build order, and library(): what a piece adds to its scene. Ships in every release
(dist/vNN/biblioteca/), so build.py here and a piece's build call the same thing.

    icons, comps = library.library()      # the "Icon/<name>" artboards and the component artboards
"""
import kit
from components import (icon_button, core_button, divider, cursor, smart_tag, core_input, floating_bar, toggle,
                        checkbox, radio, pill_tabs, search_input,
                        status, promo_tag, tooltip, loader, icon_thumbnail, core_tabs, list_item,
                        menu_item, dropdown, ai_process, text_area)

VERSION = "v04"
# a component only uses the ones before it
COMPONENTS = [("Icon button", icon_button), ("CoreButton", core_button), ("Divider", divider), ("Cursor", cursor),
              ("Smart_Tag", smart_tag), ("CoreInput", core_input), ("VibeFloatingBar", floating_bar),
              ("Core Toggle", toggle), ("Core Checkbox", checkbox), ("Core Radio Button", radio),
              ("Pill_Tabs", pill_tabs), ("SearchInput", search_input), ("Status", status),
              ("Promotional Tag", promo_tag), ("Tooltip", tooltip), ("Loader", loader),
              ("Icon Thumbnail", icon_thumbnail), ("Core Tabs", core_tabs), ("ListItem", list_item),
              ("MenuListItem", menu_item), ("CoreDropdown", dropdown), ("AiProcessIndication", ai_process),
              ("Text Area", text_area)]


def library():
    """(icon artboards, component artboards). Call it once per build."""
    icons = kit.icon_artboards()
    comps = [mod.build() for _, mod in COMPONENTS]
    return icons, comps
