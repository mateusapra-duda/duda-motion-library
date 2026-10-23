"""Page settings: a visitor names the page, drops a tag and saves (library v05 piece, 720x440).

Everything visible is a library v05 component or a DS text / layout box from piece.py. Built here with the kit, only
what the library lacks: the card's shadow-2 (the library card has shadow-1, the DS "Cards" shadow).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "lib", "biblioteca-v05"))
import kit  # noqa: E402
from kit import El  # noqa: E402
from piece import Piece  # noqa: E402

INNER = 420 - 2 * 24          # the card's content width: 420 wide, padding 24 (DS spacing-3)
TOP = 73                      # the card's top edge: the resting card (294.8 high, measured) sits centred, and it grows
                              # downward when "Saved" opens under the field (layout "center" would slide it up)


def shadow(item, level):
    """Swap a library card's DS shadow layers for another DS shadow (same names, same place under the body)."""
    n = item.wrap.name
    new = kit.shadow_layers(f"{n}.sh", kit.DS["shadow"][level]["layers"], kit.radius("border-radius-m"))
    kids = item.wrap.children
    idx = [i for i, c in enumerate(kids) if isinstance(c, El) and (c.name or "").startswith(f"{n}.sh.")]
    assert len(idx) == len(new), (idx, len(new))
    for i, el in zip(idx, new):
        kids[i] = el


p = Piece("MAIN", 720, 440, bg="#F6F6F8")

# ------------------------------------------------------------------ the screen
title = p.text("heading", "Page settings", style="Headlines/He 0")                   # 18/24, 550, #272B35
close = p.icon_button("close", icon="i_x", size=0, color=1)                          # Small 24, Grey
header = p.row("header", [title, close], gap=8, align="spaceBetweenCenter", w=INNER)
rule = p.divider("rule", w=INNER, variant=1)                                         # No text, full width
name = p.input("pageTitle", w=INNER, label="Page title", placeholder="Type a title")  # Default 35, White
tags_label = p.text("tagsLabel", "Tags", style="Content/Body")                      # the input label's style
tags = [p.tag("home", label="Home page", color=0, prefix=True, prefixIcon="i_site"),
        p.tag("header2", label="Header", color=0),
        p.tag("hero", label="Hero", color=2)]
tag_row = p.row("tagRow", tags, gap=8)
tags_block = p.column("tagsBlock", [tags_label, tag_row], gap=8)                     # label to content: 8, as the input
cancel = p.button("cancel", label="Cancel", variant=1, color=0, size=1)              # Secondary Grey, Regular 32
save = p.button("save", label="Save", variant=0, color=0, size=1)                    # Primary Brand, Regular 32
footer = p.row("footer", [cancel, save], gap=8, align="centerRight", w=INNER)
card = p.card("card", [header, rule, name, tags_block, footer], w=420, pad=24, gap=16)
shadow(card, "shadow-2")
p.layout(card, align="topCenter", pad=(0, TOP, 0, 0))

# ------------------------------------------------------------------ the choreography
a = p.actions()
a.enter(card, t=0.0)                                   # the card arrives and settles
a.at(0.7)                                              # the card has settled
a.cursor_in("right")                                   # from off-frame, already moving
# it clicks the field ~60% across (clear of the text it will type), so the aside arc to Hero's x turns in the gap
# under the field instead of crawling over the "Header" tag; dy: from the input's centre to its 35 px field's centre
_, _, w, h = p.bounds(name, a.now)
a.click(name, where=(0.1 * w, h / 2 - 35 / 2))         # focus: caret + active border on the press
t_hero = a.type_into(name, "About us", then=tags[2], then_where="remove")   # type, aside, swoop to Hero's x
a.set(tags[2], t=t_hero - 0.40, hover=True)            # the tag hovers as the tip enters it (measured: 0.40 s
                                                       # before the press), not only 150 ms before; then x hover
a.remove(tags[2])                                      # Hero leaves, then the row closes up
a.wait(0.25)                                           # a beat to see the row close (the leg to Save stretches)
a.click(save, loading=1.0)                             # hover, press, spinner ~1 s (width kept)
a.cursor_out()                                         # its job is done: it leaves the frame
a.message(name, "Saved", kind="success")               # success state + "Saved" under the field
a.hold(1.8)                                            # reading: >= 1 s once "Saved" is fully in (~0.5 s to arrive)
a.loop(exit=card)                                      # the card leaves, everything resets while hidden

p.build()
