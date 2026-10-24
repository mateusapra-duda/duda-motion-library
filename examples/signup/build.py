"""Sign-up: a visitor fills a short form, drops an interest, accepts the terms and creates the account (library v07d
example)."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "lib", "biblioteca-v07d"))
from piece import Piece  # noqa: E402

p = Piece("MAIN", 1340, 638, bg="Backgrounds/bg-grey-color")

# the screen: components in DS layout boxes
title = p.text("title", "Create your account", style="Headlines/He 1")
name = p.input("name", label="Full name", placeholder="Your name")
email = p.input("email", label="Work email", placeholder="you@company.com")
tags = [p.tag(f"tag{i}", label=t, color=2 if i == 0 else 0) for i, t in enumerate(["Websites", "Stores", "Apps"])]
interests = p.row("interests", tags, gap=8)
agree = p.checkbox("agree")
terms = p.row("terms", [agree, p.text("termsT", "I agree to the terms", style="Content/Body")], gap=8)
go = p.button("go", label="Create account", minWidth=320)
card = p.card("card", [title, name, email, interests, terms, go], w=368, gap=20)
p.layout(card)

# the choreography: one timeline, read top to bottom
a = p.actions()
a.enter(card, t=0.2)                             # the card arrives and settles
a.at(1.0)
a.cursor_in("right")                             # the cursor comes in from the right, already moving
a.type_into(name, "Jane Cooper", then=email)     # click (focus), type, drift aside, swoop to the next field
a.type_into(email, "jane@acme.com", then=tags[2], then_where="remove")   # ...then to the x of "Apps"
a.remove(tags[2])                                # "Apps" leaves, then the row closes up
a.click(agree)                                   # the box checks on the press frame
a.click(go, loading=1.2)                         # hover, press, spinner for 1.2 s
a.cursor_out()                                   # its job is done: it leaves the frame
a.message(email, "Account created. Check your inbox", kind="success")
a.hold(1.6)                                      # reading time
a.loop(exit=card)                                # the card leaves, everything resets while hidden

p.build()                                        # p.build(tabs=True) for a hero tab
