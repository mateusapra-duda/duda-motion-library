"""Library reel: the same components with different parameters, then a cursor walks them through their states."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "lib", "biblioteca-v05"))
from piece import Piece  # noqa: E402

p = Piece("MAIN", 880, 500, bg="Backgrounds/bg-grey-color")


def group(name, label, kids, gap=12):
    cap = p.text(f"{name}Cap", label, style="Content/Tiny", color="Typography/secondary-text-color")
    return p.column(name, [cap, p.row(f"{name}Row", kids, gap=gap)], gap=10)


# one component each, placed with different parameters
publish = p.button("publish", label="Publish")
preview = p.button("preview", label="Preview", color=1)
cancel = p.button("cancel", label="Cancel", variant=1)
upgrade = p.button("upgrade", label="Upgrade", color=2)
delete = p.button("delete", label="Delete", color=3, showLeftIcon=True, leftIcon="i_trash")
learn = p.button("learn", label="Learn more", variant=2, showRightIcon=True, rightIcon="i_arrow_right")
buttons = group("buttons", "CoreButton", [publish, preview, cancel, upgrade, delete, learn])

edit = p.icon_button("edit", icon="i_edit", color=1)
dup = p.icon_button("dup", icon="i_duplicate", color=1)
trash = p.icon_button("trash", icon="i_trash", color=1)
add = p.icon_button("add", icon="i_plus", variant=1)
search = p.icon_button("search", icon="i_search", color=2, border=True)
icons = group("icons", "Icon button", [edit, dup, trash, add, search], gap=8)

tags = [p.tag("home", label="Home page", prefix=True), p.tag("header", label="Header"),
        p.tag("hero", label="Hero", color=2), p.tag("blog", label="Blog", radius=1),
        p.tag("store", label="Store", color=1, border=True)]
tagrow = group("tags", "Smart_Tag", tags, gap=8)

site = p.input("site", w=300, label="Site name", placeholder="My site")
email = p.input("email", w=300, label="Work email", placeholder="you@company.com")
fields = group("fields", "CoreInput", [site, email], gap=24)

card = p.card("card", [buttons, icons, tagrow, fields], w=720, pad=32, gap=28)
p.layout(card)

# the states, walked by one cursor
a = p.actions()
a.enter(card, t=0.2)
a.at(1.1)
a.cursor_in("right")
a.click(publish, loading=1.0)                              # hover, press, spinner
t = a.click(edit)
a.set(edit, t=t, selected=True)                            # selected on the press frame
a.type_into(site, "Studio HQ", then=email)                 # focus, Duda typing, swoop to the next field
a.type_into(email, "hello@studio.com", then=tags[2], then_where="remove")
a.remove(tags[2])                                          # "Hero" leaves, the row closes up
a.cursor_out()
a.message(email, "Looks good", kind="success")
a.hold(1.4)
a.loop(exit=card)

p.build()
