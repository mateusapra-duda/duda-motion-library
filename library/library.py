"""The library's components in build order, and library(): what a piece adds to its scene. Ships in every release
(dist/vNN/biblioteca/), so build.py here and a piece's build call the same thing.

    icons, comps = library.library()      # the "Icon/<name>" artboards and the component artboards
"""
import kit
from components import icon_button, core_button, divider, cursor, smart_tag, core_input, floating_bar

VERSION = "v02"
# a component only uses the ones before it
COMPONENTS = [("Icon button", icon_button), ("CoreButton", core_button), ("Divider", divider), ("Cursor", cursor),
              ("Smart_Tag", smart_tag), ("CoreInput", core_input), ("VibeFloatingBar", floating_bar)]


def library():
    """(icon artboards, component artboards). Call it once per build."""
    icons = kit.icon_artboards()
    comps = [mod.build() for _, mod in COMPONENTS]
    return icons, comps
