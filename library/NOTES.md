# Library notes (v15d)

Decisions, property tables, open questions and what building this taught us about Rive. A piece needs only
`QUICKSTART.md`; the README is about the library itself.

## Changelog

### v15d (2026-11-24)
**The Solo structure, checked where v15c had not been** (a rule fix, no new feature).
- **Fix: `remap=` on a piece with no cursor visit** (or with no Generation effect left in a scene) stopped with
  "Element.remove(x): element not found". Each scene's copy read its parents before dropping what it doesn't show, so
  the empty cursor or effects layer was removed twice. `_detach` removes it only if it is still there. Found on an
  email card built as one scene (`{"scenes": None}`). The pieces with a cursor build byte-identical to v15c.
- **Fix: the web check found no Playwright** once npm cleaned its npx cache (one fixed cache folder). `webtest/run.cjs`
  now looks in every npx cache for `playwright` or `playwright-core`, takes `PLAYWRIGHT=`, and says what to do.
- **Proved** (a test piece: home with a photo, a card that generates, a zoom cut, a white cut, a toggle, a tabs cut,
  a photo on two more screens; a hero tab, 518 frames):
  - Solo vs plain, in the CLI: 506 frames identical at +1 ms, the rest ≤1/255. The Solo switches on the cut frames
    (202, 295, 462). Exact sampling: 510 identical, the rest ≤1/255.
  - The site's runtime, 2.45.0, frame by frame (the clock by hand): every frame matches the CLI's (median 0.16/255,
    the renderers' anti-aliasing; 0.002 on the cut frames); `tabChange` on frame 518 and 518 frames after each `play`;
    `play` after the end and in the middle of a scene restarts it exactly (518/518 frames identical to the first
    pass).
  - An email card as one scene (`{"scenes": None}`, a photo, a loop, no cursor): 779 of 781 frames identical (one past the loop
    seam included), the other two 1 px at 1/255.
- **Older runtimes** (2.39.2, the email carousel's widget):
  - `play` restarts the Solo piece exactly, and the scenes switch on the right frames.
  - The zoom and tabs cuts scale a few px off their point (up to 7/255 mean, f183-218 and f472-480), in the plain
    build too: 2.39.2 draws the Solo piece and the plain one pixel-identical (519/519 frames). It is the old runtime's;
    2.45.0 matches the CLI.
  - `tabChange` doesn't reach the page with the Solo structure (it does with a plain piece). A page that depends on
    `tabChange` with a runtime older than 2.45: build it without `remap=`. The carousel and the home switch by time,
    so they don't depend on it.
- Still not proven: several overlaps; the editor's export of a keyed Solo (the .riv here came from the CLI).

### v15c (2026-11-24)
**Built for hand edits** (item 2 of the v15 scope, after the motion designer's answers on the test .rev):
`p.build(remap={...})`, `remap.py`.
- What the motion designer said:
  - The two-key "time" per scene and per component helps them control timing. Moving "Card time" worked, closer keys
    speed it up, and MAIN played smoothly.
  - One artboard per scene, and components such as the card as artboards too.
  - The cursor goes on MAIN if it crosses more than one scene, else inside its scene.
  - The scenes go in a Solo.
  - Opacity only where two scenes must draw together, and the build says where.
- **MAIN**: background, State Machine 1, view model, one Timeline.
  - The Solo "Scenes" has one nest per scene. Its active scene is keyed with KeyFrameId `activeComponentId` (hold) on
    each switch frame; there are no opacity keys. An inactive child doesn't draw, and is left out of the tree.
  - "<Scene> time": 0 -> 1 linear, from the frame before the scene shows to the frame the next takes over. The scene
    applies its time on the frame it becomes active, so the switch frames are identical under both samplings.
- **Scenes**: a copy of the piece with what paints in its stretch, its own Timeline (keys trimmed at the edges,
  curves split), the drivers of its components.
- **Elements**: `elements={"Home": [card]}`, an artboard the item's size nested in its own slot (a `p.free` slot or a
  `p.stack` screen), with its keys, drivers and Generation effect. Its time sits in its scene's Timeline. An effect
  goes only to an element of the scene where it plays: a probe caught the Settings panel taking the card's effect.
- **Cursor rule, per visit**: all its frames inside one scene -> that scene; across a cut or during an overlap -> MAIN
  above the Solo. The log says which and why. `"cursor": "main"` / `"scene"` override it.
- **Overlaps**: `("Settings", s, overlap_s)`.
  - The Solo keeps the earlier scene and switches when the overlap ends.
  - "<Scene> (overlap)" sits outside the Solo, with the same time keys and hold opacity 0/1/0, above or below the
    Solo as the plain build draws it.
  - Each part is drawn once there; parts drawn by both scenes are noted.
  - The library's cuts never overlap.
- **Proof** (the test piece: home, a card that generates, a click, a slide cut, a toggle; 361 frames):
  - Solo vs plain: 270 frames identical at +1 ms, the rest ≤1/255 (≤55 px).
  - One visit per scene: 265 identical, the rest ≤1/255.
  - Crossfade overlap: 282 identical, the overlap frames 177-206 all identical.
  - The .rev read back by `rive create --from-rev`: 361/361.
  - A plain build is byte-identical with and without the hook. 6 builds verify 0/0.
- **Not proven**:
  - the editor's and the site runtime's handling of a keyed Solo (the CLI renderer only);
  - zoom, white and tabs cuts;
  - `scenes=None`;
  - photos;
  - several overlaps.
- **Limits**:
  - Not with live hovers.
  - Moving only the Solo key doesn't move the time keys.
  - The overlap nest's time can't be linked to the scene's in the editor (move both).
  - A rebuild overwrites hand edits: read them with `scripts/handdiff.py` first.

**The interactive card follows LEARNINGS 15** (a rule fix to v15b's live mode).
- v15b's live piece looped, or replayed at its end in a hero tab, and took the mouse during the entrance.
- Now a piece with a live card plays once and holds its last frame, and the hover waits for `introDone`. MAIN's view
  model gets that boolean; it turns on at the timeline's end, and `play` replays the entrance with it off.
- Checked with the CLI's pointer: a hover during the entrance stays off, then lights once the entrance ends; the
  cards hold after the end.

### v15b (2026-11-24)
**A Figma screen in vector, the hand-edit diff, the email editor's parts.** The structure for hand edits in the
editor (MAIN nested, scenes and elements on time remap) waits for the motion designer's answer on a test file; it is
not in this release.
- **A Figma screen in vector** (`p.figma_screen`, `fromfigma.py` + `textfit.py`). It replaces the pieces' four copies
  (vec.py, vecsvg.py, nativetext.py, plates.py).
  - Texts become native, one Text per line, in the DS weights. The fit is nonzero, sampled at pixel centres.
  - Photos become images; masks and off-screen shapes are left out.
  - `parts` become their own items; `plates` turn still layers into 2x lossless WebP.
  - `p.figma_sheet()` shows the texts that stayed outlined, with keys to name them by.
  - A layer name is used as the text only when the font draws as many pieces of ink as the outline has. This caught
    a green badge showing "Status" where Figma says "Active", in a piece's own build. It rejected those 5
    badges and none of the 31 real texts in the two proofs.
  - Proofs on two piece families, each against the piece's own build:
    - vecsvg family: mean diff 0.71/255 against the piece's own build, and closer to the Figma PNG than the piece.
    - vec.py family: 1.18/255. Native text took objects from 14.9k to 4.1k and the scene from 2.0 to 0.6 MB.
  - Left out:
    - the JSON route;
    - mixed-style text, which stays outlined;
    - only the 3 DS weights are tried;
    - parts are drawn over the rest of the screen.
- **The hand-edit diff** (`scripts/handdiff.py`): ours (the build the edit started from) against theirs (the `.rev`
  from the editor), in beat terms: shifts, cursors (path in px, presses, legs, press lead), curves named by the
  library's tokens, keys, elements, attributes, state machines, view models.
  - It is matched by name path, not by id. The editor's bookkeeping, its omitted defaults and float noise are
    filtered out.
  - `--json` writes every key on both sides.
  - It generalises the pieces' cursor_edit.py / mateus_cursor.py.
  - `keydiff.py` keeps the scene's tree and each timeline's settings (fps, length, loop, work area) for it. A name
    shared by an artboard and its view model now gets its tag in the key, and a KeyFrameId's value is the name it
    points at.
- **The email editor's parts** (`editor.py`), measured on the email storyboard's frames 01-02 at product size:
  - `p.template_card`: its hover is a veil #3A3D45C7 with "..." fading in over 0.15 s, while Use This / Preview rise
    6 px in 0.5 s.
  - `p.block_panel`, `p.panel_field`, `p.segmented` and `p.color_field`.
  - `p.color_picker`: saturation and hue drawn natively (gradients), with their handles.
  - `a.pick_color`: the swatch's edge on arrival; on the press, the dip (0.9, back in 0.333 s "duda") and the ring;
    over 0.333 s, HEX, the handles, the field and any `targets` turn.
  - Rings never picked aren't built.
  - Checked against Figma frame 02 (the picker, the panel) and the approved piece's timing.
- **The interactive card** (`live=True` on `p.template_card` / `p.hoverable`): the visitor's own mouse lights the
  hover. There is no fake cursor.
  - A layer on MAIN's state machine is switched by `<name>Hover`; listeners on a hit box under the card's content set
    it. A click fires `<name>Click`.
  - A live card's buttons are interactive.
  - Checked with the CLI's pointer (`--pointer=move@` / `click@` + `--data-dump`):
    - the hover turns on and off;
    - it stays on over the buttons;
    - the button's own hover is true;
    - the click triggers fire.
  - The build stops if the timeline would key a live hover. The [hidden] check leaves its layers out.
- **`p.hoverable(rise=)`**, and a hover that also lights while the cursor goes to something inside the item.
  `a.click(card.use)` lights the card from the tip's entry until it leaves, as in the approved email piece.

### v15a (2026-11-24)
**Fixes and small asks.**
- **CoreButton disabled**: the state faded the whole box to 40 %, the white label too (on the salmon fill it nearly
  vanished). Now as the DS's disabled row: a PrimaryButton keeps its label white and only its fill changes, to the
  token "primary-40% (disabled)" (Brand) or its own colour at 40 % (Dark, Upgrade, Destructive); Secondary and Text
  fade as a whole, as before. A "Disabled" layer with one state per Primary colour (+ "Enabled", "Other types"),
  blended over the hover fade; "Enabled" keys only the box's opacity, so the look layer's fill shows.
- **`p.code_editor` indent guides** (`guides=True, indent=2`): a 1 px #D3D3D3 line per level, at the level's column
  (JetBrains Mono: 0.6 em a letter); a blank line takes the smaller indentation of the nearest lines around it.
  Hidden with the line (empty=True) and shown with its number by a.write_code.
- **`p.code_panel(save="Save Changes")`**: "Discard" (TextButton Secondary, small, disabled) 19 px before "Save
  Changes" (Primary Brand, small, disabled) at the right of the file's tab, as the product. Targets `.discard`,
  `.save`.
- **Scripts:** `scene.info` (every script) reads a timeline with no `fps` as 60 (a `.rev` saved by the editor and
  converted with `rive create --from-rev`: render_mp4 crashed on it) and a `rive.yaml` with no `main:` as "MAIN",
  with a note. `webtest.py --port N`.
- **`a.cut` cascade on a grid in columns:** columns side by side, widths within 25 % (`GRID_W`), each with 2+ visual
  rows, count as one grid: its items cascade by visual rows across the columns. Before, the box under the click was
  the clicked column alone (it cascaded, the other column came in whole).
- **`p.copilot_panel(field_top=)`:** Figma's top of the field, panel points at 1x. In a cut panel the field keeps it
  at the product's height (124.5), shorter only when it wouldn't be whole `margin` above the frame's bottom ("same
  top, shorter": 558.21 kept, 142.56 -> 100.83 at 0.81). Under 60 % of the field's height left: pinned as before,
  with a note. Without it, as v14b.
- **Text pops** (an earlier proposal to make the generation's text colour pass more visible): closed. The rules
  approved after it (LEARNINGS 7, 19.2) and v14 cover it: texts inside a block start 0.40 s after the square shows
  it, orange -> pink -> own with a Feather; colours by `ink=` / `colors=` / `gradient=`; a loose text with a single
  tint is `a.loose(color=)`.
- Checked: release check clean; the 31 prototypes build; an approved hand-finished card rebuilt on v15a gives the
  same keys as on v14b; the two blind pieces rebuilt: unchanged but the CoreButton's Disabled timelines.

### v14b (2026-11-23)
**What the two blind tests of v14 found** (a welcome email the Copilot generates, "the generation test", and a
template opened and recoloured, "the template test"). The motion designer's three taste answers of the same day keep
v14 as it is (LEARNINGS 4, 7, 8:
feathers by size for every piece of that size, popups and selectors on the release, slide cuts 215 / 60 px).

**1. The email carousel's rhythm** (LEARNINGS 11): its story ends by ~5-5.5 s and the rest stays still (the approved
ones: still from 5.53 s, the last action at 5.2 s); "~3 s still" is a hero's or a loop's. `p.build(carousel=12)` notes a last action
after 5.6 s (5.5 x the carousel's length / 12, + 0.1); the old "~3 s still at the end" note is gone.
**2. The cut's cascade on what the click opened** (cuts.py; LEARNINGS 10): `_cut_rows(dst, t, P)`: the content box
under the click (the zoom's pivot or the press) with the most visual rows; a box >= 95 % of the screen's width or
height is frame and comes in whole; items overlapping vertically are one row; the box's own background and hairlines
(<= 2 px) out of the rows; overlays drawn in front of it (a selection, its label, its toolbar; within 8 px of each
other one cluster) join the row of their biggest member's middle. Fallback: v14's "most items" box, counted in visual
rows. The build note names the box. `cascade=` (list or False) as before.
**3. a.cut robust** (cuts.py): size-0 boxes in dst (an empty spacer) are skipped (`_cut_box`; a screen with no box
raises a clear error); dst in display none at the click is switched on 2 f before the press; the cut keys its
screens' display itself (dst on from 2 f before it is needed, src none from 2 f after it hides, edge strips only while
they show), keeping and only switching on the display keys a piece wrote. checks.py: [offscene] no longer fires on
a cut's screens; `series()` read "flex" / "none" the wrong way round.
**4. The cursor shows outside the item it lights** (piece.py `_show_at`): when its first target has a hover, the show
point keeps 12 px clear of it and its tip must still be outside 15 frames after the fade (the entry curve starts
fast); 8 directions, 220-480 px, the nearest. Note: "cursor: shows N px from X, outside it". the template test: the card's
hover lit at f63 (the cursor's 3rd frame) -> f87.
**5. A block inside a block** (patterns.py `_nest`): in `a.generate_screen` a block given plain whose centre falls
inside a bigger block joins that block's `rows` (the smallest holder, up to one that is no one's row; reading order,
after the rows given); `(item, {...})` keeps its own slot. The generation test: `[hero, badge, crystal]` -> the last check at 260
(was 313), keydiff 0 against the hand-written `(hero, {"rows": [badge]})`.
**6. `p.hoverable(item, veil=, border=, fill=, show=, fade=0.1, radius=)`** (piece.py): a hover for an item the
piece drew, lit by the tip as a component's (`_want_hover`, `_resolve_hovers`, passovers too), off when it leaves
(`_hover_set`, `_unhover`); layers `<item>.hov.veil / .edge / .fill` (absolute, opacity 0), `show` items hidden until
lit; a layer that never lights isn't built (`_prune_hovers`).
**7. `p.copilot_field`** (patterns.py `FIELD`, `copilot_field`, `_field`): the docked Copilot's field as the product
draws it (124.5 high: 100.83 at 0.81, top at Figma's 558.2; radius 8; 1 px #EDEDEE edge, #CFCFD3 active; placeholder
#9B9BA2 at 12, 14; only "+" and send). `p.copilot_panel(field=None)` makes it by default and links it to its
`p.chat_steps` / `p.chat_reply`. Its button keys itself: grey #C9CACD empty, orange from the first letter (hold),
the orange stop while working (`a.think` / `a.steps` / `a.send`, from f0 when sent at 0), back to grey with
`a.reply`'s status swap (stop out 0.1 s, then send in 0.1 s; the approved 280-286 / 286-292; `FIELD["swap"]`).
`a.typewrite(field.prompt)`: placeholder gone and edge active as it starts, orange on the first letter;
`a.send(field, t, message=)`: the press (0.9), the stop with the message. `a.click(field)` (a cursor) focuses it
(`_reacts`; a field's 7-frame press lead). The generation test: the hand-drawn field (25 lines) and its `a.key`s gone; the swap at
285-297.
**8. QUICKSTART 6**: a carousel with a Copilot opens on the send (`a.sent(msg, t=0)`); `p.build(carousel=)` notes a
docked Copilot's message sitting still at f0 (the chat's first row with no opacity / y keys).
**9. Lints**: scripts/compare.py measures a text's Figma ink on the band matching Rive's line (`ink(match=)`: "20%
Off" -23 % -> +4.4 %, the font's own glyphs); [layoutfade] leaves out the frames a.cut moves its own boxes in
(`_cut_windows`); the README's "Tested with Rive CLI 1.7.0" -> 1.9.2.
**10. Small ones**: `a.click(result=)` on the release (a dict of component props, `(name, prop): value`, or a
function of the release time); icons `i_mobile_portrait`, `i_show`, `i_configuration` (filled), `i_panel_right`;
`p.icon("art/...")` (the library's own drawings); gradient `fill=` on `p.card` / `p.free` (top to bottom, or
`(c1, c2, "right")`; `_paint`); `opacity=` on every placer (`_op`).

**Checked**: copies of the two blind pieces rebuilt on the final library without their workarounds: lints clean,
verify 0/0; stills of (the generation test: the field at f0, the last
check at 261, the swap 285-297; the template test: the show point, the card's hover at the tip, the white, the panel whole and the
email's rows, the colour on the release).

### v14 (2026-11-23)
**The precision research** (482 requests in 302 rounds of 36 pieces, two blind tests) and
**The motion designer's decisions of 2026-11-23**: his cursor becomes the default; the cursor at a screen
change walks or vanishes, chosen from the history; the zoom cut at 120 % + white; a lighter generation in every piece.

**1. The motion designer's cursor, the default** (`hand.py`, new; piece.py's cursor section rewritten):
- One Follow Path per cursor through the show point, each stop and the typing arc's turn; distance keys only at the
  stops (and a creep's hand-over); `hand.Path` bows each leg 8 % upwards ("already rising towards the target"), the
  side flipped when the upward bow would pass over more controls than the downward one (`Actions._bow_sides`).
- It shows in place, ~220 px below its first target, towards the frame's centre (`hand.show_point`; beside it when
  the target is near the bottom; tip >= 65 px from the bottom, >= 40 from the other edges), with a 3-frame fade,
  already moving; it fades out 8 frames after its last press (`cursor_out(vanish=)`: at a set time, for a cut).
- Show -> first stop: one curve (0, 0, 0.2514, 1), >= 38 frames; stop -> stop: one curve (0.6, 0, 0.25, 1) over
  0.85 s + 1 ms per px, squeezed to 0.8x or stretched to 1.35x to meet a set time; a longer wait creeps (~12 px/s,
  easing in) and hands over to the glide at the creep's speed (a "value" ease with its first handle solved); more than
  3 s beyond the glide: it vanishes and a new cursor shows for the next target. A stop then a press on the same spot
  (move_to + click) lands short and creeps onto it (never still). A leg under 24 px is a creep.
- The press 5 frames before the stop (7 on a field: input, search, text area, dropdown); the next move 2 frames after
  the stop; press 1 -> 0.85 in 3 + 3 frames, linear. The ride from 0.1 % to 99.9 %; every last key holds.
- The typing arc (`type_into(..., then=)`): ONE glide through a smooth turn vertex, no key there (`hand.arc_turn`,
  22 % of the chord, >= 60 px), on the side that passes over fewer controls (`Actions._arc_side`; `arc=` forces it).
- The speed ceiling: 2.4 % of the frame's width per frame (31 px/f at 1300; his approved peaks 18-26), a glide or an
  entry too fast for it gets longer (`hand.glide_frames`, `hand.entry_frames`).
- The old cursor stays: `a.cursor_in("right")` (left, bottom, top) keeps cursorpath's visit (off-frame in and out),
  now under the same ceiling (its entry legs stretch to it); a piece that chose it gets it again after a long wait.
- **The build checks every cursor** (`Actions._cursor_lints`, in screen space; the library's, the old one, and any
  Follow Path cursor a piece or drag.py builds itself, read back from its RML vertices with `hand.RmlPath`): the tip
  under the ceiling (inside a camera, relative to the zoom: the cursor grows with the interface), one peak between two
  stops, never parked >= 30 frames, the ride inside 0.001-0.999 where it shows. `a.cursor_tip(f)` gives the tip for
  anything that follows the cursor (`a._after_cursors`).

**2. Defaults that fought approved rules** (LEARNINGS 4, 5, 11):
- **Hover when the tip enters** (`Actions._resolve_hovers`): read off the built path, on the frame the fully shown tip
  enters the item, off when it leaves or the cursor vanishes; none during the 3-frame fade; and every hoverable control
  the tip crosses between two stops lights up as in the product (`passes over ...` in the log). Was: 150 ms before the
  press (`hover_lead_ms`), "it reads as a bug". The tag's x (`removeHover`) the same way.
- **A click's result after the press**: a dropdown opens on the release (+8 frames), a collapsible folds +5;
  `a.release()` (the latest press + 8 frames) and `a.click(..., opens=item)` (a popup, modal or menu entering on the
  release, 0.96 -> 1, rising 8 px, 767 ms). Selection controls (toggle, checkbox, radio, tabs) stay on the press.
- **A menu's hover is dry** (MenuListItem's Hover layer in 0 ms, as the product's dropdown).
- **Typing by the kind of text** (`type_into(kind=)`): "field" ~14 letters/s from 0.15 s after the click, NOT spread
  over the 1.45 s window (the cursor still clicks `then` no sooner than 1.45 s after: "Lila lenta" came from the
  spreading); "sentence" ~38; "prompt" (the AiPanel's default): the cursor vanishes, the text types from 9 frames
  after the click on (0.1804, 0.0442, 0.2292, 0.676), ~53 letters/s (84 frames for his ~74-letter prompt), ONE key on
  the panel's `typed`; `then=panel.part("send")` presses send on its own 45 frames after the last letter (ma-novo
  v18.20B, approved), and `now` moves to the message (+23 f): a.think / a.steps / a screen start there; `a.click` on
  the panel's send does the same (`a.think(panel)` after it doesn't send again).
- **No blinking caret**: CoreInput / SearchInput / Text Area show the caret only while the text types.
- **The loop rests ~3 s** (`a.loop(rest=3.0)`): still frames on both sides of the seam together (the end part >= 8
  frames; `hold=` keeps an exact end). Was 8 frames.
- **A carousel tab** (`p.build(carousel=12)`): exactly 12 s, played once (`play` restarts it), no `a.loop()`; the
  build fails it when the layout's first box isn't on screen at f0 and notes less than ~2.5 s still at the end. A hero
  tab (`tabs=True`) gets a note when its first movement starts after ~0.9 s. Notes (`a.notes`) print, never fail.

**3. A lighter generation, with no patches in the piece** (approved 2026-11-23; LEARNINGS 5, 6, 7, 19.2;
patterns.py, components/ai_panel.py):
- **Lighter squares** (`GEN`): cards from 108 % (was 111 %) with Feather 11 -> 2 (was 18 -> 3), panels from 102 %
  (was 103 %) with Feather 10 -> 1.5 (was 16 -> 0), the panel's square fading in over 16 frames from the sweep's
  start (his 12-20 in hero-view v15.1). On a card-sized square the band's own transparent end already brings it in
  over ~16 frames (measured: the card's photo square 17 -> 33 frames into its pass); the fade matters where the
  band's front is on the square from the start (a 400 x 600 panel: frame 0). Each first feather is seeded +-10 %
  (`GEN_VARY`, "vary between them", MA v14). `feather=(start, end)` per call, as drawn.
- **Feathers by the size shown** (`SIZE_REF`, `FEATHER_AT`, `p.shown_at`): 1 from 1340 px, at 432 px 0.65 on the
  squares (11 -> 2 becomes 7.2 -> 1.3, lumi's approved 7.2 -> 1.2), half on the wash (10 -> 1.5) and on the texts and
  icons (4 -> 2); linear in between. Default width: the artboard's. Timings by size too (`SCREEN`): a 432 card's
  first block at 96 frames and ~28 frames apart, the welcome email's (772) at 108 and 63.
- **The content comes in on its own** (`a.generate(content=)`, `_cascade`, `_letters`, `_whole`, `_settle`):
  every p.text, p.icon and p.image inside a block (the innermost block when they nest), in reading order
  (`_reading_order`: rows by vertical overlap, left to right), ~6 frames apart and a little uneven, from 0.4 s after
  the block shows on a 772 px screen (at once on a 432 card, as lumi's banner letters). Texts: a TextModifierGroup
  (`<text>.reveal`, opacity) + one range (`<text>.front`, percentage: modifyFrom = falloffFrom = -10, falloffTo 0,
  modifyTo = w = min(0.5, 6 / letters), offset -w -> 1, linear, ~45 letters a second, 0.4-0.9 s); the whole fill
  orange #F9A84A from the start, pink #F4BBD2 over 10 frames after max(0.35 s, 60 %), held 8, its own over 20; a
  Feather on the fill 4 -> 0 over 40 (by size). A heading's second line (`_next_line`: right under it, same height
  +-20 %, overlapping across; a measured box may overlap the next line by a quarter) starts when the first ends.
  `letters=False`: whole (8 frames, Feather 6 -> 0 over 54). Icons: 20 frames, the same colours and feather
  (`_shape_feathers`). Photos: the inner Image 112 % -> 100 % over 1.5 s (0.16, 1, 0.3, 1) from 6 frames before the
  square shows them, counted as landed half way (97 % there). Numbers (`NUMBER`): v11's pop, #AE68FA.
- **`a.generate_screen` with no patches**: reading order (`order=False` keeps the list's), the biggest block a panel
  and the others cards (v13c: the first one listed was the panel), uneven gaps (+-15 %), `details` folded
  into the block they sit over, `loose` slotted under the block above them (+4 frames, capped 3 frames before the
  next block) or 3 frames after the first block when above all. The design's gradient gives the texts' two colours
  (`p.palette`'s details). The wash fades its tail over 18 frames (lumi faded it by hand).
- **`a.loose`** (v14): the same cascade as a block's content; `color=` keeps v11's single tint.
- **`a.typewrite(text, t, cps=, dur=, ease=, soft=)`**: one key on a text modifier's offset (typeValue percentage,
  w = 0: whole letters). The prompt's numbers in `PROMPT_TYPE` (lead 9, 84 frames, (0.1804, 0.0442, 0.2292, 0.676),
  the press 45 frames after the last letter: ma-novo v18.20B).
- **`a.reply` types** (`REPLY_CPS` 120, `REPLY_MAX_S` 1.0; `_type_lengths`): each paragraph's room opens 0.25 s before
  its first letter; on a p.chat_steps the swap and fold at t and the paragraph 21 frames later (ask-your-agent
  v12-v13: 280 / 301); on an AiPanel by its new `typewriter` and `reveal1..3`. `typewriter=False` is v13's.
- **The send** (`a.send`, `_panel_send`; AiPanel `SEND_STAGE` 0.5, `FLY`, the Send layer): the press (0.9, LEARNINGS
  4's press), the typed prompt up 10.3 px in 45 frames (0.8, 0, 0.2, 1), out between +16 and +26, the message (stage
  1) at +23. piece.py's cursor press on `panel.part("send")` calls `_panel_send`. A field of your own:
  `a.send(text, t, message=)`. `a.think` (stage straight to 1) still sends without the press.
- **The AiPanel's field**: `typed` takes fractions (the Typed range: unit index, modifyFrom -0.5, falloffFrom +0.5,
  offset = typed: letter i fades in as `typed` goes i -> i + 1); no caret (the caret, its blink and the
  CaretA/CaretB states are gone); the placeholder has its own layer (gone on `focused`, on typed >= 0.5, from stage
  0.5 on): it never comes back after sending.
- **Checked** (agentA's test pieces, `rive --verify` clean, lints clean): the QUICKSTART example; a 432 x 264
  lumi-like card on the defaults (banner block 96, its letters 132 = lumi's; logo 117, photo block 120, photo settling
  170, heading 180 / 204, the line under it 207, the end 277 frames; lumi's hand version 112 / 124 / 174 / 184 / 222 /
  287); the welcome email (ask-your-agent's blind-test layout, library only: generation ends 4.33 s, the answer
  typed by 6.10 s); a floating AiPanel (prompt typed in one key, the send, the message at +23, the answer typed in
  1 s). Stills at 5x: small block mid-pass, big square fading in, a heading letter by letter, the photo settling, the
  prompt's soft edge, the send in three frames, the answer's last letters.

**4. Cuts, camera, jump cut, scroll** (`cuts.py`, new; LEARNINGS 8-10):
next to its constant in cuts.py):
- **`a.cut(src, dst, kind)`** with `p.stack`: `slide` (7 f after the press; 215 px out in 23 f (1, 0, 1, 1), 60 px in
  settling in 54 f; px scaled by the piece's width / 1340), `zoom` (14 f after; 120 % around the click, the motion
  designer 2026-11-23, 135 % before; white in over 9 f, full from the cut -1 to +3, out over 15 f; 95 % -> 100 % in 54 f),
  `white` (in place: 9 f out, 6 f of white, 15 f in), `tabs` (hero-tabs v03: 26 px / 20 f out, 34 px / 26 f in,
  a veil in src's body colour closing over the exit's last 10 f, one in dst's opening over the entry's first 10 f; the
  page moves against the pill, by the screens' order in the stack). The screens' x/y/scale/opacity and the cascade
  (LEARNINGS 10: 8 px, 0.6 s, 67 ms apart, rows found as the box with most items in dst) go on the timeline when the
  action is called; src goes back in place hidden the frame after the cut.
- **The edges** (LEARNINGS 8: what shows past the frame continues the screen): at the build's end each screen that
  reaches its clipping box is rendered at rest (the board without the cursors, the camera and the screen's own move;
  cached in `build/cuts/<hash>/`), the line 5 px inside the edge is cut into runs of one colour (tolerance 4/255, at
  most 48 bands), and each run becomes a vector band from 2 px inside the edge out past the farthest the edge travels
  (+8 px). The strip rides the screen's own moves (same pivot) and shows only while the edge is off. Vector, never a
  bitmap: no raster UI. Checked at 5x on the slide, zoom, tabs and jump stills: no seam, no step.
- **The white / veil** is one box over both screens and their edges in their common box; the cursor stays above it.
- **The cursor at a cut** (LEARNINGS 8, new criterion): "auto" waits for the cursor's next move: within 2 s of the cut
  (his 1.37, 1.38, 1.55 s) it walks; later or never (his 3.6 s, none), it vanishes in place (3 f, from 8 f after the
  press, never before 5 f, always before the exit) and the next cursor starts its way in 6 f after the cut. It
  watches the piece's `_go`, `cursor_out` and `cursor_in` (a dry run, undone if it would vanish); the build log prints
  the verdict per cut. When the piece itself sends the cursor away (its long-wait rule), auto vanishes instead of
  walking and then leaving.
- **The camera** (LEARNINGS 9; with the default cursor, a cursor that shows during the close shot's lead shows
  inside the close shot, `_cam_show_inside`): `a.camera_close` / `a.camera_open` build the editable rig at the build's end (it needs
  the cursor's keys): `CAMERA` gets a Transform constraint `CUT` aimed at `CAM_CLOSE` (where the cursor sits in the
  close shot) > `.zoom` (2.5 -> 2.4) > `.track` (minus the cursor's tip, held inside `ui`). `CUT`'s strength: hold
  0 -> 1 at the cut, the 80/80 (0.8, 0.0451, 0.2, 1) back to 0 over 102 f from send -25 f, and frame 0's value on the
  last frame. The track is a Hermite fit of the cursor's path in at most 12 cubic keys (error < 0.25 px on the board,
  < 1 px on screen); the slow zoom ends 40 f into the zoom out.
- **`a.jump_cut`**: a `JUMP` node inside the camera holds the whole picture (cursors too); at the seam it replaces
  `a.loop` (the end slides 23.4 px in 27 f, frame 0 starts 30 px on and settles in 34 f). `ease="80-80"`: the first
  half of an 84 f 80/80, cut on the peak (ma-novo v18.9). Px on screen (divided by the camera's scale inside a close
  shot). Edges: vector strips in `JUMP` on the side the slide or the entry uncovers (in a close shot, only where the
  view meets the interface's edge). Two jumps close together: the first's settle is cut short where the next slide
  starts.
- **`a.scroll`**: one move on (0.857, 0, 0.242, 1), 0.9 s + 1.5 ms/px, slowed if it would pass the text cap; waits
  until its screen has been readable 1 s; `cursor=True` brings a cursor 6 f before the end.
- **The lint**: choreo's speed lint skips each cut's frames for what the cut moves (as it does for its own match
  cuts), skips the camera's rig, and skips every mover in a jump cut's frames (the whole picture moves); each cut gets
  a row with its last step into the cut against the match cut's cap (150).
- **Checked**: six test pieces (slide + white with the cursor walking then vanishing; zoom with the cursor vanishing,
  a scroll with a cursor and a jump at the seam; tabs walking, forced walk and vanishing; camera close-up + zoom out +
  an 80/80 jump at the seam; the same with a jump into the close shot; a forced vanish): `lints: clean`,
  `rive --verify` 0 errors, stills before/during/after each cut and 5x crops of every edge.
- **Not yet** (LEARNINGS 18): the close shot's rounded corners keyed with `CUT`, hiding what already left before a
  zoom out, a fixed header or one frame on top across a cut, edges for a screen inside a scaled box. The slide's
  distances stay 215 / 60 px (marketing-automation v15.6, approved); the research's median over his other cuts is
  ~57 / 35 px (the motion designer, 2026-11-23: 215 / 60 stays the default).

**5. The checks (package 5) and the images** (`checks.py`, `slim.py`, `scripts/`):
- **Checks on every build** (`checks.py`, called after the lints): `[rml]` loose .rml (ISSUE), `[weight]` objects and
  vertices per artboard (note over 10k / 8k, ISSUE over 40k), `[outlines]` text as outlines (note from 100 letters),
  `[hidden]`, `[offframe]`, `[offscene]` (screen hidden by opacity but still on), `[layoutfade]` (the lints' blind spot:
  layout boxes' opacity; false OVER, settle on a visible thing, a box held half-faded) and `[slim]` (what each image
  became). `checks.allow(name)` for an approved exception. 0.04-2.3 s on the test pieces (the first `[offframe]` run
  measures the layout once; cached after). The example and lumi-dental-winback build clean; ma-novo gets 7 notes
  (+4 `[slim]`): a mail window hidden 7.2 s but still on, a false OVER at its jump cut, half-fades (its screens.py
  re-times the scenes after the build, which the checks don't see: read those as hints).
- **slim, images by kind**: photos lossy WebP 90 (`format="webp" quality="0.9"`), sharp images lossless WebP
  (`format="png"`: the editor's export stays lossless), `.webp` sources kept with their format, decisions cached in
  `slim/.images.json`; `slim.QUALITY` per image. **Moving a piece to v14: drop its own `format="webp"` patch after
  `p.build`** (it now writes the attribute twice): lumi-dental-winback's `assert ... "the photo's ImageAsset moved"`
  fires (the scene p.build wrote is already right, byte-identical to the delivered one); ma-novo's regex silently
  writes `format` twice and the CLI fails ("<ImageAsset> has a malformed attribute"). Also patching it: accept-payments,
  hero-tabs (build.py) and the optimize.py of build-your-audience and design-with-context.
- **scripts/compare.py**: many poses per call (`pose.png@frame`, folders), scaled not cropped, `--fit=contain`, % of
  pixels off > 40 per area, big texts' size vs Figma (`TEXT` over 3 %). On the blind ask-your-agent test it flags
  "Welcome." -6.2 % (Rive 213.5 px, Figma 227.5); on the approved piece +1.3 %, passes.
- **scripts/edges.py** (new): edges and seams at ~5x on the key frames, suspects + contact sheets.
- **scripts/render_mp4.py**: 2x with `--fit=contain` by default, frames 1 ms past their time (frame 0 and hard cuts
  right: ma-novo's cut at frame 950 showed one frame late before), CRF 12, BT.709 tagged, `--commands` sessions in
  parallel (lumi 720 frames 2x in 10 s), sheet read back from the MP4, stops if the scene changes during the render.
- **scripts/keydiff.py** (new): version-to-version key diff by element, `--expect` for "only what was asked changed".
- **`p.image(fit="fill")` stretches** (`common.FIT`: Rive's fill is 7; 0 is "resize", which drew it small) and
  `p.image(..., quality=)` sets one image's encoding. **`p.stills` takes each frame 1 ms past its time** in one CLI
  session (frame 0 was the setup pose; a hard cut showed one frame late).

**6. (v15)** Package 6 of the research (bigger pieces: a Figma screen in vector with native text, the main artboard
nested with each element on a time remap, a diff of the designer's file against our build, ready components) is
planned for v15.

**7. The questions for the plan** (QUICKSTART section 9): where it lives, its length and rhythm, which fields, which
generation, an approved piece to copy, what on the storyboard isn't the product, the cursor at a cut.

<!-- v14 agents -->

### v13c (2026-11-18)
**The approved rules** (motion-spec/LEARNINGS.md 7; checked against an approved hand-finished piece):
- **The generation block** (`a.generate`, so `a.generate_screen` too): each square covers its item with `room` px
  more on every side (5) and the item's corner radius + 5 (`ROOM`, patterns.py). The radius is read from the item
  (`_radius`): its box's corner, an image's clip, a drawing's bottom rectangle, a component's own card (through its
  artboard; shadows, edges and hidden variants aside); 0 (so 5) for a square corner. Before: the item's exact size,
  radius 8 whatever its own, and the block's soft edge let the component's edge show (dark dashes on a photo's edge,
  a yellow bar's corners leaking). `radius=` overrides the reading; squares given as numbers are drawn as given.
- **`a.loose` sharpens icons and drawings** (and `a.generate_screen`'s details): `_shape_feathers` puts a Feather in
  every fill and stroke of the item's shapes. A feathered fill draws only under the clockwise rule, so each shape's
  contours are turned to wind as that rule needs (`_wind_clockwise`: nonZero, an outer contour drawn anticlockwise
  turns with everything inside it; evenOdd, by nesting depth); a path left anticlockwise vanished (a logo's tooth).
  The strength is scaled back under a scaled drawing (a 400 px SVG drawn at 24), so the blur reads 4 on screen.
- **`p.icon`** (piece.py): a DS icon drawn on its own (`kit.icon_slot`, 16 in 24, the DS grey), for an icon that only
  sits there: `p.icon_button` brings the whole component (~0.17 MB in a light piece). `p.chat_reply`'s action icons
  are `p.icon` now (`buttons=True` keeps Icon buttons).
- **Checked**: an approved piece rebuilt on the defaults gives the same scene as its hand-made version; the frames where the photo and the bar light up under their blocks (164-176, 207-220) at 5x: the old exact squares
  show the dashes and the bar's corners, the new ones none. 66 DS icons and 62 Figma SVGs drawn with the clockwise
  rule and a sharp Feather match their plain drawing (0.05/255 at most), none vanishes, all blur at 4.

### v13b (2026-11-13)
**The approved rules** (checked against the reviewer's hand-finished welcome email):
- **`p.copilot_panel`** (patterns.py + `Piece._fit_panels`): the docked Copilot (header, conversation, field, note).
  At `p.actions()`, if the frame cuts the panel, the panel's height becomes the frame's (in its own units, through its
  scale), its bottom padding Figma's 16, and the note goes out absolute below it: the field ends 16 above the frame's
  bottom (12.96 px in the welcome email at 0.81, the reference's 13), the conversation (fill, clipped) takes what is
  left. Before, a piece's own panel at Figma's 842 let the frame cut the field.
- **`a.sent`** (patterns.py): the sent message's opacity 0 -> 1 over 5 frames (linear) and its y +20 -> 0 over 30
  frames (0, 0, 0, 1), both keyed from the send frame (`a.enter` faded over the token's 9 frames and moved from the
  next frame).
- **AiPanel**: the bubble has its own layer (`bubble_layer`): stage 1 brings it in the same way (it faded over 0.12 s
  with no rise); a follow-up after the answer (stage back under 5) brings the new one in again.
- **Checked**: the welcome email rebuilt: the field's bottom at 658.6 (the reference's 658.6), the message's keys
  0 -> 5 / 0 -> 30 frames, matching the reference frame by frame (0, 1, 2, 3, 5, 10, 20, 30); the email itself
  unchanged (0.00 of difference against v13). The field keeps Figma's height (142.6 px in the frame; the reference
  drew a shorter one, 100 px, with only + and send).

### v13 (2026-11-13)
**The approved rules of 2026-11-13**: motion-spec/LEARNINGS.md 6, 7 and 19.2 (the reviewer's hand-finished welcome email; key frames in motion-spec/refs/generate-screen-ref1-key-frames.png):
- **`a.generate_screen`** (patterns.py): a screen the AI generates, during the Copilot's loading, big to small. From the
  send: the wash 6 -> 223 frames over the area; the blocks from 108, `gap` apart (63 frames), the first as a panel
  (1.03 -> 1, Feather 16 -> 0, the pass 131 frames), the others as cards (1.11 -> 1, Feather 18 -> 3, 84), every block's
  pass on (0.42, 0, 0.58, 1) (the wash keeps (0.588, 0, 0.377, 1)); loose texts from 111, 57 apart (in 20 frames, the
  text colour from frame 8 to 53, Feather 6 -> 0 in 53); the details 18 frames after the last block starts (the warm
  tone in 8, held 10, the text colour in 9, held 9, their own in 18; Feather 6 -> 0 in 48 on duda). Returns the end.
- **`a.steps(until=)`**: the steps' lengths spread unevenly (weights 1 / 0.82 / 1.45 ..., the last 2.1: the reference's
  33 / 27 / 48 / 69 frames) so the last check lands at the generation's end; `each` takes a list. On a p.chat_steps,
  `t` is the send: the status at t, the summary's room at +18 frames, the summary at +33, the first step at +54.
- **`p.chat_steps`**: the status ("✦ Thinking...", an AiProcessIndication) on top in place of "Show steps"; `a.reply`
  swaps it for "Thought for Xs" (X: whole seconds since the send) as the summary and the steps leave.
- **`p.palette(warm, cool)`** / `gradient=`: the generation's colours from the design's gradient (HSL from its two ends:
  the warm end 7 and 10 % darker, the cool end less saturated, a middle tone 35° past the cool hue; texts the middle
  tone at 72 % lightness, details the warm tone at 64 %), within 1-3 levels of the reference's measured tones; the wash
  at 75 % with it.
- **`p.build(slim=True)`** (slim.py, from the pieces' own): only what MAIN reaches stays (components, view models,
  fonts), the fonts are cut to the characters used plus ASCII (in slim/), the photos become WebP 90 (and say WebP for
  the editor's export). The welcome email: scene 3.0 -> 0.70 MB, .rev 2.7 MB -> 291 KB (the reference: 211 KB; the
  rest are the DS button, divider, status and step components it places).
- `a.generate` / `a.wash`: the squares stay hidden until their start (a corner could show from frame 0); `ease=`.
- `a.loose`: fade, lead, dur, feather, feather_dur.
- **Checked**: the welcome email rebuilt with v13 against the hand-finished one at the recipe's key frames (0.5, 1.5,
  2.3, 3.2, 4.0, 5.0, 8.0 s) and at 120 / 175 / 200 / 220 / 250 frames: under 1/255 of mean difference on the email.

### v12 (2026-11-13)
**Pick and drop, the approved recipe of 2026-11-13** (motion-spec/LEARNINGS.md 19.1; key frames in
motion-spec/refs/drag-widget-ref1-key-frames.png, with the hand, and drag-widget-ref2-key-frames.png, panel closed,
the close-up). The standard: the second reference's path and curves up to the grab, the first's from there on. In
`drag.py`:
- **The hand** (`art/hand_grab.svg`, vector, ~1.15x the arrow): on the grab frame the arrow goes to 0 and the hand
  to 1 (no press scale: the closed hand is the press); it vanishes where it lets go, 2 frames.
- **The cursor**: one path for the whole gesture (cubic legs, a Follow Path on the cursor's node, its distance keyed
  leg by leg): to "+" 37 frames (0.379, 0, 0.246, 1), the press 0.85; to the card 93 frames in two legs at one speed
  (52 frames / 67 % of the length on (0.478, 0, 0.346, 0.817), then (0.777, 0.347, 0.299, 1)); with the panel already
  open, 28 frames on (0, 0, 0.175, 1); the drag 88 frames on (0.596, 0, 0.152, 1), out horizontally, an arc, landing
  vertically. The cursor comes in already moving (fades in over 2 frames).
- **The card**: a copy of the card's layout (absolute, so it stays out of the root's flow) in the effects layer, held
  by the cursor with a Translation constraint (offset); the original hides, so its place is empty. 3 frames still,
  then it lifts (-6.5, -7) in 8 frames on (0, 0, 0, 1); shadow 10 % black, blur 20, offset 4/4 (in 10 frames, out 7);
  the blue badge (21 px #2A84EE) pops when the card's right edge passes the panel's; the drop: 100 -> 90 % in 10
  frames on (0.736, 0, 1, 1), fading in the last 5.
- **The site making room** (`a.drop_widget`): the panel closes and the site scrolls 124 px (and slides left the panel's
  width when it sits beside it) in 58 frames on (0.551, 0, 0.151, 1), starting as the card crosses into the site; the
  section below goes down 33 px in 50 frames (0.637, 0, 0.338, 1); the blue line (3.7 px) 24 frames before the drop
  (4-frame fade); the opening from inside the line (60 frames on (0.8, 0, 0.2, 1), +54 px each side, clipping the
  section), the outline out at +27 over 4; the intro from +27 frames: rise 40 px in 50 frames (0, 0, 0.205, 1),
  5-frame fade, parts 4 frames apart, items 12.
- **The close-up** (`close_up=True`, off by default; the motion rules' "no zoom" has this one exception): a camera node
  over the whole board (`Piece.camera_node`), the cut at the drag's peak speed to 2.1x around the drop; the rest of the
  drag in that shot on (0, 0, 0, 0.92) (the line rising 30 px in 7 frames); ~70 frames later a hard cut back at 107 %
  settling to 100 % in 58 frames (0, 0, 0, 1).
- **Approximations**: the badge's elastic grow is keyed (0.7 -> 1.12 -> 0.97 -> 1 in 10 frames); the image's slow drift
  (the reference: x -104.5 px over 150 frames) is a settle of the image inside its frame, 1.06 -> 1 over 150 frames; the
  cursor is the library's arrow.
- **Rive / build lessons**: a layout copied under a plain Node renders and follows the Node's transforms, but it joins
  the artboard's root flow and pushes the scene aside unless its style is absolute; a box's measured bounds take in
  the children that overflow it, so the slot carries a 1 px mark (a 0 px box isn't measured) to read where it is.

### v11 (2026-11-13)
**The approved rules of 2026-11-13** (also in motion-spec/LEARNINGS.md):
- **AiStep**: the classic spinner, never the AI star (even where Figma draws it): the DS Loader's 270° arc in #272B35
  with a trail to 12 % (art/step_spinner.svg, stroke 1.5 at 16), 13 px, turning clockwise once per 0.8 s
  (kit.spin_layer: it always turns, so its fade has no jump). The label is the step, dark from the start; the view
  model is `label` + `done` (`working` is gone). `done`: the spinner fades out over 3 frames, still turning, then
  the check fades in over 3. `a.steps`: the next line comes in as the check lands, its room opening 0.25 s ahead
  (the approved example: line in at 54, spinner out 87-90, check 90-93, next line 93). The status above
  ("✦ Thinking...") keeps its star.
- **Generation effect** (the approved example, the hero's dashboard): every gradient pass on
  (0.588, 0, 0.377, 1) (was Rive's default cubic); `pops` come in #AE68FA and turn to their own colour with a
  Feather 4 -> 0 (0.4 s after the block shows: the earlier ones lit under the square; an 8-frame fade, then 36
  frames, linear), no more orange / pink; `a.count` 2 s on (0, 0, 0, 1), from close to the value (the approved rule: `to` minus a random 10-35, seeded
  by the item and `to` so every build is the same, never below 0; tenths for a decimal; `start=0` from zero; the
  Highlights KPIs too), #AE68FA -> own and Feather 4 -> 0 over 40
  frames (`color=None` keeps the colour: the Highlights count keeps its v07d glow); new `a.wash` (the whole area
  before the blocks: 50 %, drawn 110 % and cut to the area, Feather 20 -> 3 from frame 35 to 108, 217 frames; the
  example's sweep scaled from its 682.5 x 620.5 area) and `a.loose` (no block: 20-frame fade, #8D5DF5 -> own and
  Feather 4 -> 0 over 40, linear; texts' and shapes' colours, texts' Feather); `colors=` (5 colours) on
  `a.generate` and `a.wash` for the designer's own gradient.
- **Rive CLI 1.9.2**: stills, compare and render_mp4 at `--advance=N`; webtest plays an existing `.riv` (`--riv`).

### v10 (2026-10-27)
**Marketing Automation** (for the Marketing Automation piece; Figma FwDTS5Q6g5BKw3WOrEHImL,
"MA - Create automation with one email" 1:8997):
- **FlowNode** (the file's "Automation / Flow node" 1:2659 and "Automation / Wait step" 1:2667): `type` 0..5 the card
  (325 x 93: padding 12 / 12 / 14, the 36 px tile with an 18 px icon, Medium 16/1.35 title, the "..." menu, Regular
  16/1.35 subtitle with an ellipsis; edge #E4E4E7, radius 8, shadow 0 1 2 #00000014), 6 the Wait pill (221 x 42, a 26
  px #F4F4F5 tile, a 14 px clock and "..."). Tiles: Start trigger and End #D4F25A, Add/Remove label and Update field
  #F1ECFB, Send email #A7E8F6, If/Else and Wait #F4F4F5. `selected`: frame 07's 1.5 px #3B82F6 edge (a.click sets it
  on the press frame). `hover` isn't in the storyboard: the edge to #D4D4D8 and a larger shadow (a licence). Nothing
  in it moves: the nodes come in with the Generation effect (`a.generate`).
- The storyboard draws the map at 0.5 (the canvas at 62 % of the UI at 0.81): the components are at their own size,
  a piece places them at 0.5. Figma kept the strokes of the "+" at 1.5 in the frame, so `p.flow_link`'s plus is 3 at
  the nodes' size.
- **p.flow_link / p.flow_split**: the map's lines (#D4D4D8, 2 px), the "+" (22 px, #F7F7F8, a 1.6 px edge) and the
  NO / YES tags (Medium 16, #5D6068 on #F7F7F8, radius 6), measured from frame 06.
- **AiStep + p.ai_steps / p.chat_steps + a.steps** ("Copilot progress" 1:9309, frame 05; "Done - ..." in frame 06):
  13/1.35 text, a 13 px check (1.5 stroke) or the purple AI star (special/i_ai_star, simplified: its four quadrants and
  two centre washes, no blurs), "Working..." in #A0A3AA with the AiProcessIndication's shimmer. The swap is timed as
  v08's status swap. Each line's room opens (0.25 s, duda) and the line enters rising 4 px, as p.chat_reply's
  paragraphs. a.reply on a chat_steps: one state at a time, the summary and the steps out (0.1 s), `done` in.
- Icons added in icons/automation/ (from the file, on the 16 grid): i_lightning, i_label, i_content, i_email,
  i_split, i_clock, i_more, i_menu_dots; art/ai_star_purple.svg.
- Not in it: the "..." under the Done text in frame 06 (an Icon button, if a piece wants it); the Copilot panel's
  header and its input (the piece's own, or p.ai_panel).
- Nothing else changed from v09.

### v09 (2026-10-26)
**FeedbackMessage, new** (for manage-hero2's "Permissions saved" after Save): the
DS "Push Feedback Message" (154396:213304; Success 160:3621, 332 x 48). `p.feedback` places it hidden; `a.feedback(item,
t, hold=3.0)` drops it 8 px into place as it fades in (0.5 s, settle), holds and lifts it away as it fades (0.25 s,
duda). The DS rules: top right, 24 px under the top bar and 24 px from the right (a large popup: top centre); it goes
on its own in a few seconds; an x, no button, maybe a link.
- Variants: 0 Info, 1 Success, 2 Warning, 3 Error, 4 Neutral (the set ".Push Feedback" 160:3624). Error has a 16 px
  icon (46 high) and Neutral is white with no icon (42 high). Measured on the stills: 48 / 48 / 48 / 46 / 42 high,
  the widths within 2 px of Figma's (325 / 332 / 329 / 309 / 293).
- The text is Content/Body with the 0.2 letter spacing of the Figma style: `ds/tokens.json` has no letterSpacing for
  Content/Body, which made the boxes ~7 px narrow. Applied only here (`ls=0.2`); the other components keep theirs.
- A Rive text line is ~2 px shorter than its line height, so the line keeps 2 px above and below as a min height
  (22; Neutral 18) instead of padding.
- The icons are the DS validations drawings with their own colours (art/feedback_*.svg); the x is the "Functional"
  16 px i_X. The link the DS allows isn't drawn.
- Nothing else changed from v08.

### v08 (2026-10-26)
**The copilot's status, official** (approved by Mateus): the "Thinking..." motion of hero-view v10
(his hp_section_3, artboard "Copilot v1", "COPILOT ANIMATION 1", without "Working...") is the library's copilot.
Poetic licence: the product pushes "Thinking..." down under the answer without interpolation; here it stays put.
Frames at 60 fps:
- **Entrance**: the star 5 frames after the message, turning from 60° to 0° and rising 8 px in 35 frames
  (0, 0, 0, 1), appearing in 7; "Thinking..." wipes in 15 frames after the message; the shimmer as before (a 37 %
  band every 1.6 s), from that moment.
- **Swap**, 9 frames before the answer: the star fades in 6 frames and "Thinking..." wipes out, left first;
  10 frames in, "Thought for Xs" wipes in where it was, without the star; 24 frames in, the chevron (up) in 5.
- **Wipe**: an opacity group, not inverted, one range, linear: hidden offset -1 / falloffFrom 0 / falloffTo 0; in:
  offset to 0 in 15 frames, falloffTo to 1 in 15 from 5 frames later; out: falloffFrom to 1 in 15, offset to 1 in
  15 from 5 frames later. The label has two (in, out), so the entrance and the swap are separate layers; the
  groups multiply.
- **The answer** below the status: each paragraph opens its room (0.25 s, duda) and enters rising 4 px, 0.27 s
  apart; the action icons at the end, below (0.083 s after the last, 0.15 s).

Where:
- `AiProcessIndication`: new `thought` ("Thought for 3s") and `shown` (true by default: a status placed as before
  shows from the start, shimmering); `done` now is the swap (in v07d it only stopped the shimmer and showed the
  chevron after the label). The star turns on its centre (a Node), the chevron as before.
- `p.chat_reply` + `a.think` / `a.reply`: the status on top (hidden until `a.think`), the rooms below with the gap
  above each paragraph, the icons last. `a.reply(t)`: t is when the answer starts; `done` 9 frames before; X in
  "Thought for Xs" = round(t - think); `then` now 0.083 (was 1.0, the status's stay before the icons).
- AiPanel: a head (the status and "Thought" stacked) on top of the output, the paragraphs and then the action bar;
  stage 1 plays the entrance, stage 2 the swap, the paragraphs wait the swap's 9 frames (SWAP_LEAD); THEN_S 0.083;
  `a.reply(panel)` keys "Thought for Xs" from when it was sent (unless the placement gives `thought`).
- **Breaking** (pieces stay on their version until they move): AiPanel's `showThought` is gone (the swap is always
  there); `a.reply(..., then=)` means the gap before the icons; a `p.ai_status` placed with `done=True` and a
  `label` shows its `thought` now (give `thought=`; the Catalog's "Done, no chevron" is `thought="Done"`).
- **Fixed**: `a.reply` opened short rooms. The measure gives artboard points (a p.vibe_workspace at 0.81 shrinks
  them) and the glyphs (~2 px short a line): a 4-line paragraph of 18 px lines measured 57 px in the hero, 70 at
  1:1. A room now is lines x the style's line height (lines from the measure, in the paragraph's own scale):
  36 / 90 / 36 for hero-view's answer, as its v10 by hand.
- Checked: hero-view v10's chat rebuilt with the library (stills 0.30 / 3.40 / 3.50 / 3.60 / 3.75 / 4.30 / 5.00 s,
  same look); the CLI stills can show a view model switch one frame late on some frames (60, 201: the
  renderer's clock rounding on a key exactly on the frame; frames 3, 10, 20, 40 react on time); on the site it
  plays in real time.

### v07d (2026-10-24)
**Official** (2026-10-24): Mateus approved v07d. It is the Highlights version pieces use from now on. The
lavender layer over the area stays as v07c made it (no fade, unlike header_2, where it fades out over frames
336-364): his call.
Mateus's review of v07c (v07, v07b and v07c stay as released): when each block of the Highlights starts, as his
header_2 times it (measured in its loop: the page scrolls up and the blocks start as they come in). Inside the
blocks nothing changed.
- His: the donut starts (frame 298), the four KPI counts start together 21 frames later (319), the line chart 26
  frames after the donut (324); each next KPI's glow tint 4, 5 and 5 frames after the one before (327, 331, 336,
  341), their blur going together.
- `a.load(page)` now keeps the page's timing (`page.starts`, `page.glow_lag`; `step=` brings back one item after
  another): both chart cards' skeletons go first, the donut draws, the KPI cards 21 frames later, all at once, the
  line on the donut's peak, 33 frames after the donut (his 26: our donut, "duda" in 1.1 s, peaks later than his
  slices; in his file the line peaks 3 frames before the donut's fastest stretch, so together, as asked).
- In the prototype: the donut draws from 0.70 s, the KPIs count from 1.05 s, the line from 1.25 s (both peaks).
  v07c: the KPIs from 0.70 s, 0.27 s apart, the donut 2.05 s, the line 2.60 s.

### v07c (2026-10-24)
Mateus's review of v07b (v07 and v07b stay as released):
- The donut draws with "duda" again (his pick over v07b's (0, 0, 0, 1)).
- The line chart's inside as his hand animation (header_2, read again): the line traced (TrimPath end) as its
  Feather 5 goes, 40 frames, linear; the area's gradient sliding in with (0, 0, 0, 1), 40 frames; the colour is a
  second area over it with the same gradient and a lavender top stop (#E6D7F1 at 50 %), his "GRADIENT GRAPH 2",
  which stays while the timeline plays (clear at rest, so the catalog and the Figma check keep the Figma colour).
  No fade on the line or the area.
- In `a.load` the line chart starts on the donut's peak: the donut is fastest half-way ("duda"), the line's entry at
  its start (the gradient's curve), so the line starts 0.55 s after the donut starts drawing (`_peak`). Without a
  donut in the load, it starts once its labels are in. In the prototype: the donut draws from 2.05 s, both peak at
  2.60 s.

### v07b (2026-10-24)
Mateus's review of v07 (v07 stays as released):
- `a.load` glows by default (`glow=False`: the plain count). The library file has one "Prototype Highlights", with it.
- The line chart draws once its labels are in (`dur`, 0.6 s, after its skeletons go), and its line and area are no
  longer in the fade (they show at once under their own reveal: the fade hid its start).
- "LLMs Visits" was the one rough loading: the opacities were the same in every card (skeletons out in 0.1 s,
  content in over 0.6 s; measured on the built timeline), but its ring drew with "duda" (0.75, 0, ...: slow start,
  the peak in the middle) while the rest start fast. Now the donut draws with (0, 0, 0, 1), as the counts.

### v07 (2026-10-24)
Why: Mateus's hand animation of the same Highlights page (header_2, read with rive create
--from-rev) beside the v06 one; the best of both. Kept from v06: the skeletons and their shimmer, the number's fade
in, the entrances of the details (the y labels, the legend chips).
- **The count**: his curve, cubic (0, 0, 0, 1), fast then a long soft landing (v06: "duda" over 0.7 s, stopping
  dry), 1 s for the first card and 10 frames more for each next one (his: 60, 70, 80, 100 frames). The chip comes
  0.55 s after its number starts.
- **`a.load(glow=True)`**, a choice to show Mateus: his blur and tint on the counting numbers. A Feather of 3 for
  24 frames, to 0 over 40 (linear); the colour orange #F9A84A, then pink #F4BBD2, purple #8D5DF5 and its own, 7
  frames apart from 8 frames in. The text's fill gets the clockwise rule, or its feather doesn't draw (the v06 count
  blur never showed for that reason; a.count keeps it, a.load now counts without it).
- **The donut as the Figma's "Pie"** (read on 26:10090 with use_figma: arcs with inner radius 0.6, corner radius
  2.125 and a white 1.417 stroke, at 0.733): filled slices (straight-vertex paths, the arcs every 2 degrees, the
  four corners rounded 2.9), 1.2 degrees apart, a white edge of 1.93. a.draw shrinks a white ring over it (a trimmed
  stroke, from the top, clockwise), so the donut sits on a white card; the slices appear at once under it (fading
  them would show them through the ring).
- **The line chart**, his way: the line is traced (TrimPath end) as its blur (Feather 5) goes, 40 frames, linear;
  the area's gradient slides down into place (his offsets: the transparent stop from 0.68 of the height up, the
  coloured one from 1.19 above the top) with cubic (0, 0, 0, 1), its colour lavender #E6D7F1 (his, 50 %) turning to
  its own. The plot no longer widens.
- Library file: "Prototype Highlights glow" beside "Prototype Highlights" (the same with glow=True).
- Figma check (the pose of v06, rebuilt): 5.3/255, the donut in place.

### v06 (2026-10-23)
Why: the AEO report pieces (Duda dashboard, Performance > Highlights; Figma i4AzmiPVfqgBsoEMUHrOlK "AI-Visibility-
highlights" 26:9582) and what the use case test (pecas/teste-uc-a-so-figma vs teste-uc-b-biblioteca) found missing:
a shimmer skeleton, charts, the dashboard shell, the KPI card of the Figma, its icons, shapes in p.wrap, and scripts
that run outside the repo.
- **Skeleton** (components/skeleton.py), a component: a grey block (bg-med-grey) that a soft white band (65 %,
  feather 18) crosses every 1.4 s, on its own (its state machine loops); `circle`, `shimmer`. The band is 60 % of the
  block's width and moves in percent (-60 % to 100 %), so any bar shimmers alike.
- **dashboard.py**, piece patterns (native, editable in Rive, data at build time): `p.kpi_card` (Figma's card: Cal
  Sans number, trend chip, tile icon), `p.donut` (trimmed ellipse strokes, 60 % hole, 2 px gaps), `p.line_chart`
  (grid, labels, line over a fading area, in a clip a.draw widens), `p.chart_card`, `p.skeleton`, `p.dashboard` (top
  bar, rail, optional PERFORMANCE menu, grey page), `p.aeo_highlights` (the whole page, `layout` "figma" or
  "product", `loading`). Actions `a.load` (skeleton -> content one item after another, 0.27 s apart, numbers count,
  charts draw) and `a.draw`.
- **Hosts** (dashboard_hosts.py, library file only: piece parts are built as pieces there): "Catalog Dashboard" (the
  KPI card, both chart cards, the Highlights page in both arrangements and loading, the shell with and without the
  menu) and "Prototype Highlights" (1440 x 900, the product's arrangement in the shell: it loads from 0.6 s and plays
  again and again in the editor; `play` restarts it). Added on 2026-10-24: the first v06 .rev had neither.
- Figma's charts sit at 80 % (measured on the frame: every colour of the donut and the line); the Figma page is drawn
  at 0.733 and its shell at 0.68, the library builds both at product size (in the Figma frame, at 0.733, the rail
  and top bar come out 3 px bigger).
- 8 icons (from the Figma, normalised to a 16 viewBox): i_stats, i_coupon, i_settings, i_expand, i_onboard_client,
  i_engagement, i_arrow_corner_up / down. The font Cal Sans SemiBold (`font="cal"`). 58 icons.
- `p.wrap`: loose shapes (not layouts, nodes or texts) go in a Node inside the box, back to front, so the layout
  doesn't stretch them. `a.count` counts a decimal value in tenths ("2.6%"). The measure fonts link is replaced when
  it points at another version (the FileExistsError below).
- The bundle has `scripts/` (render_mp4, compare with a Figma PNG, webtest: they read rive.yaml and scene.rml, use
  vendor/bins.py, and work in any folder) and `webtest/`. The piece's rive.yaml leaves both out.
- Product × Figma: texts from the product where they differ (the (i) on Total leads and Conversion rate; "Visits" /
  "LLMs Visits" in the product layout); spacing and sizes from the Figma.
- Test: the Figma frame rebuilt from the library (dashboard + aeo_highlights at 0.733 over the photo): mean
  difference 5.3/255 (header 9, KPI 8.5, charts 5); the product layout at 1440 x 900 with the menu.

### v05 (2026-10-23)
Why: Mateus asked for one library for everything ("não é mais eficiente fazermos toda biblioteca num arquivo?"): the
copilot component (pecas/copilot v04, Rive 2675574) was the last chat built outside it.
- **AiPanel** (components/ai_panel.py), the copilot moved into the library: the same layout, states and timings
  (the product's, details from the hero storyboards), docked (the Vibe chat, 406) or floating (`copilot`: the
  Copilot, 368, rounded, the shadow, its own toolbar). Open / close, the greeting and four suggestions cascading in,
  typing with the caret, focus, sending (the bubble, "Thinking..." shimmering, the stop button), the reply, the action
  bar, the chat renamed, `showThought` / `figmaActions` (the Figma's options), every hover, and the prototype
  (`interactive`: a real text field, Enter, clicks, a corner button that reopens it).
- **The reply as the product** (HERO1's v04 request, now inside the component): "Thinking..." right under the
  message; up to three paragraphs (`reply`, `reply2`, `reply3`), each opening its own room above the status and
  pushing it down (Rive's layout animation: 0.25 s, the duda curve), then rising 4 px into it; 1 s after the last is
  in, the action bar takes the status's place. The copilot v04 brought one block word by word, the status under its
  final height.
- **Driven by values** (so a piece's drivers reach it): `stage` (0 empty, 1 sent, 2..4 the paragraphs, 5 done) and
  `hidden`; the triggers (`open`, `close`, `send`, `respond`, `reset`) only set them. Gone from the copilot v04:
  `replyProgress` (the word-by-word reveal) and `width` / `height` (the placement gives the size).
- **In pieces**: `p.ai_panel(...)` places the component (`chat=[...]` keeps the v04 panel, a free conversation of
  your own items); `a.type_into(panel, text)`, `a.click(panel.part("send"))`, `a.think(panel)`, `a.reply(panel)`,
  `a.set(panel, hidden=True)`; the parts are measured for the cursor (send, field, chips, toolbar, header).
- **DS values** (the library's rule), where the copilot v04 had the product's or the Figma's: the orange #F56D41
  (was #EC6641), the field's edge Borders/border-light-color #EDEDEE (was the Figma's #E4E4E6), the disclaimer in
  Typography/hint-color #9B9BA2 (was #93959A), the DS icons at stroke 1.5 (was 1.25). Added to `icons/` from the
  product's sprite: i_like, i_dislike, i_floating_panel, i_binoculars, i_new_site, i_user, i_template (50 in all).
  Font: DudaSansUnderline.ttf (the disclaimer's link).
- **Hosts**: "Catalog AiPanel" (both looks, empty and answered), "Motion AiPanel" (both run a whole conversation on a
  loop, as a piece drives them), "Prototype AiPanel" (both interactive: play it in the editor; the data panel lists
  every trigger).
- **Checked against the copilot v04**, frame for frame on the same data: empty 0.38/255, typing 0.45/255, answered
  0.22/255 (the differences are the DS values above; every box is in the same place).

### v04 (2026-10-23)
Why: what the three hero pieces rebuilt with v03 needed (hero-view v05/v06, manage-hero2, hero3-code v04: their
NOTES), and what they had to build by hand around the library.
- **Mixing** (QUICKSTART section 8): `p.asset` (an image for own elements), `p.font` refuses the library's keys
  (duda, caret, mono), `a.beats` and `a.c` documented as the way to key own elements, `p.free(radius=)` and
  `p.overlay(radius=)` (a round window, its clip included), `Piece(bg=None)` and `p.vibe_workspace(fill=None)`
  (see-through), `p.build(duration=s)` (exact length; `tabChange` right at s; anything later fails the build; keys
  after the end are a lint).
- **The cursor**: `a.click` / `a.move_to` aim where the target is on the press frame (a dry run of the path finds
  that frame: a panel still sliding in), `at=(x, y)` for a point of the board; `a.cursor_in(t=)` now moves `now` (a
  long wait's re-entry inside the actions doesn't); `a.enter(dx=, scale=, ease=)`; the cursor's shadow
  (`Piece(cursor_shadow=True)`). The floating bar's parts are measured (a longer label: "Edit Design").
- **Fidelity**: the comments icon in the top bar, the learning-centre cap in the rail, the modal's title icon, the
  red asterisk and the info icon on a label (`required`, `labelIcon`), an arrow after the modal's primary
  (`primary_icon`), the modal title at the product's size (He 2 Bold 14/20), `p.ai_status(chevron=False)`, a compact
  canvas header, the chat title's menu chevron (`ai_panel(title_menu=)`), the storyboard bar (`p.bar(style=
  "storyboard")`; the DS bar stays the default: both, decided by me with Mateus's "segue como for ficar melhor").
- **The AI's answer as the product** (HERO1, checked live in Vibe; Mateus: follow the product): `p.chat_reply` +
  `a.think` / `a.reply`: "Thinking..." right under the message, each paragraph opens its own room above it and pushes
  it down, ~1 s after the last it gives way to the action icons; no "Thought for Xs". In v03 the chat's items took
  their room from the start, invisible.
- **New actions**: `a.show` / `a.hide`, `a.text` (swap a text, optionally with a fade), `a.stream` (word by word),
  `a.count` (a number counts up, sharpening), `a.type_into(replace=True)` and into a Text Area.
- **New parts** (patterns.py): Text Area (a component, DS 80799:13404), `p.quick_edits` (the visual edit's panel),
  `p.code_panel` / `p.code_editor` / `p.file_tree` with `a.write_code` / `a.add_file` (hero3-code's stream and
  colours, JetBrains Mono, registered only when an editor is used), `p.gen_status` with `a.generating` / `a.done`,
  and the Generation effect `a.generate` (hero_1's square, gradient and feather timings; hero-view's details: rows,
  pops in orange and pink with a light blur). The effects draw over the scene and under the cursors.
- **Icons**: i_site_comments, i_learn, i_appstore, i_undo, i_redo (the product's sprite), i_file, i_pop_out (drawn on
  the DS grid); `art/resize.svg` (the Text Area's corner). 43 in all.
- **Measure**: keys that never change a layout (opacity, scale, colours, gradients, the code's lines) are left out
  of the measure's state: fewer CLI passes.
- **QuickLook** (HERO1): a .riv made with the library looks broken where nothing binds its view model (the Finder's
  space bar; `autoBind` off): every component reads its values from the piece's view model. It can't be fixed from
  the file; the QUICKSTART says so and how to check instead.
- `piece.py` split: `common.py` (what piece and patterns share) and `patterns.py` (the parts above).

### v03 (2026-10-23)
Why: the release notes (Figma `Tk3ABHfpGTaO6IBFC5oCpJ`, 7 notes) and pieces that mix the library with their own
images, fonts and drawings. v02 had only the 7 atoms of the pilot.
- **Mixing** (`piece.py`): `p.image` (a photo in a box: cover / contain / fill, radius), `p.font` and
  `p.text(font=, size=, lh=, weight=, ls=, w=, align=)` (a client's typeface; paragraphs that wrap, `w="fill"`),
  `p.free` (each child where Figma has it, with a scale; the cursor aims right under the scale), `p.wrap` (own
  drawings as targets), `a.key` (any property of an own element), `card(shadow=, border=, fill=, radius=, h=,
  w="hug", title=, action=)`, `divider(h=)`, `cursor_out(t=)` (the cursor creeps aside, then leaves).
- **15 components**: Core Toggle, Core Checkbox, Core Radio Button, Pill_Tabs, SearchInput, Status, Promotional Tag,
  Tooltip, Loader, Icon Thumbnail, Core Tabs, ListItem, MenuListItem, CoreDropdown, AiProcessIndication. Each has a
  placer in `piece.py`; a click keys its result on the press frame (toggle flips, checkbox checks, radio selects,
  `tabs.tab(i)` selects, dropdown opens, search takes the focus); `type_into` types into a SearchInput.
- **DS patterns as piece helpers** (a piece's own content can't go inside a Rive component): `p.menu` (titles,
  dividers, MenuListItems; `menu.entries`), `p.collapsible` (a header click folds / unfolds body and chevron;
  `a.open` / `a.close`), `p.table`, `p.modal` + `p.overlay`, `p.item_card` (the KPI card).
- **The Vibe editor** from library components, each button a cursor target: `p.vibe_topbar`, `p.canvas_header`,
  `p.vibe_rail`, `p.ai_panel` (header, conversation, ChatInput, disclaimer), `p.chat_user` / `p.chat_ai`,
  `p.vibe_workspace` (the window).
- **Icons and art**: 13 icons from the product's sprite (36 in all, stroke 1.5); `art/` (AI star, Premium badge, the
  Loader arc, the Duda logo, the "Vibe" wordmark as outlines), shipped in the bundle. `kit.icon` keeps an SVG's own
  colours: linear and radial gradients, gradient strokes, colour names and #rgb.
- SearchInput and CoreInput share one `typing()` helper (CoreInput's output is byte-identical to v02).
- The Catalog shows every new component in its states (1700x5104).
- Proof: release note "Vibe MCP oct 2026", frame 3, built from the library at 10.6/255 mean difference from Figma.

### v02 (2026-10-23)
Why: the A/B test (2026-10-22) showed the library saved time (−27 %) and steps (−26 %) but only 5 % of the
weighted tokens. The cost was reading (README, manifest and bundle code to learn the library; MOTION.md, PROCESS.md
and tokens.json before any code) and hand-writing the choreography. And CoreButton's loading cross-faded label and
spinner for a few frames.
- **`QUICKSTART.md`**: the one page a piece needs (198 lines): import, component tables, actions, a complete example
  (the release's example is that block), and "Motion rules for library pieces", a digest of the motion spec for
  site pieces with the token names.
- **`piece.py`**: `Piece` (place components, DS text, rows / columns / cards, layout) and `Actions` (one timeline:
  enter / stagger / exit, cursor_in / cursor_out, move_to / hover / click with loading, type_into with the Duda
  typing pattern, remove (tag), message (input), set, hold, loop) on the kit's `choreo` and `cursorpath`, so the
  kit's lints run on every build and pass by construction. `build()` makes "State Machine 1" with `play` (restart);
  `tabs=True` plays once and fires `tabChange`.
  - **Drivers**: a component state on the timeline is a custom property `drv.<slot>.<prop>` (group "Drivers")
    bound into the component's view model; one timeline holds the cursor, the entrances and every state.
  - **Measured positions**: the cursor aims at what the CLI lays out (`--semantics`, a marker per placement) at the
    moment of each action, cached in `build/measure/`. No coordinates by hand, no re-render to find them.
  - The loop seam fails the build when something changed outside the `exit` card (it would jump back on screen).
  - Durations take the motion token names (`"medium"`, `"read_hold"`).
- **One state at a time** (MOTION.md, State swaps), new `kit.swap_layer` / `kit.spin_layer`:
  - CoreButton and Icon button loading: the label (icon) leaves in 0.1 s, then the spinner arrives on its last visible
    frame; the spinner turns on its own layer, so it never jumps. The width is kept.
  - CoreInput: the status and message icons swap one at a time; the message's room opens and closes smoothly
    (it used to appear and push what is under the field in one frame).
  - Smart_Tag: the component had no overlap (`removed` only fires); the removal is the piece action `remove`.
  - Checked: Icon button selected / hover, Divider, Cursor and the bar have no state swap that overlaps.
- **kit.assemble(namespace=, external=)** (pecas/showcase suggestion): a name prefix for artboards, component assets
  and view models, and references to ids another `.rml` of the same project defines.
- Release: the bundle carries `piece.py`, `QUICKSTART.md`, the motion tokens in `motion-spec/` (where the vendored
  `choreo.py` reads them) and `choreo.py`, `cursorpath.py`, `ease.py` in `vendor/`.
- `webtest/run.cjs` takes `WEBTEST_URL`, so a piece's `.riv` can be tested from a server at the repo root.

## View models

Choices are numbers (no enums). `interactive` turns on the component's own listeners (mouse hover / press / click);
with it off, the same states are set from outside. `click` (in) plays a press; `clicked` (out) fires on a real click.
Internal props start with `_` and are not exposed.

### Icon button (artboard `Icon button`, 32x32, hugs)
| prop | kind | default | values |
|---|---|---|---|
| icon | artboard | Icon/i_plus | any `Icon/<name>` |
| variant | number | 0 | 0 Icon, 1 Box (the DS "type") |
| size | number | 1 | 0 Small 24, 1 Large 32 |
| color | number | 0 | 0 Primary, 1 Grey, 2 Dark grey, 3 Light, 4 Dark |
| border | boolean | false | 1 px #e2e2e4 |
| hover, pressed, selected, focused, disabled, loading | boolean | false | the DS states |
| hoverAnimated | boolean | false | the hover pulse (0.4 s) |
| interactive | boolean | false | own listeners |
| click / clicked | trigger | | in / out |

### CoreButton (artboard `CoreButton`, hugs)
| prop | kind | default | values |
|---|---|---|---|
| label | string | "Button" | |
| variant | number | 0 | 0 Primary, 1 Secondary, 2 Text |
| size | number | 1 | 0 Small, 1 Regular, 2 Large (Text has Small / Regular; Large reads as Regular) |
| color | number | 0 | Primary: 0 Brand, 1 Dark, 2 Upgrade, 3 Destructive · Secondary: 0 Grey, 1 Light transparent, 2 Upgrade, 3 Dark transparent · Text: 0 Brand, 1 Secondary, 2 Dark, 3 Light |
| showLeftIcon / leftIcon | boolean / artboard | false / Icon/i_plus | |
| showRightIcon / rightIcon | boolean / artboard | false / Icon/i_arrow_right | |
| minWidth | number | 0 | points |
| hover, pressed, selected, focused, disabled, loading, interactive | boolean | false | |
| click / clicked | trigger | | |

### Divider (artboard `Divider`, 240x18)
`variant` 0 With text, 1 No text, 2 Vertical · `label` "EARLIER".

### Cursor (artboard `Cursor`, origin at the tip)
`color` #508AF6 · `outline` white · `shadow` false · `shadowColor` black 20% · `click` trigger (0.85 over 3+3 frames).

### Smart_Tag (artboard `Smart_Tag`, hugs)
| prop | kind | default | values |
|---|---|---|---|
| label | string | "Tag" | |
| size | number | 1 | 0 Small 20, 1 Regular 26 |
| radius | number | 0 | 0 6 px, 1 Full |
| color | number | 0 | 0 Grey, 1 White, 2 Primary |
| prefix / prefixIcon | boolean / artboard | false / Icon/i_site | |
| removeButton, border | boolean | true, false | |
| hover, removeHover, interactive | boolean | false | |
| clicked / removed | trigger | | out |

### CoreInput (artboard `CoreInput`, 240 wide, hugs height)
| prop | kind | default | values |
|---|---|---|---|
| label / showLabel | string / boolean | "Label" / true | |
| placeholder | string | "Placeholder" | |
| value | string | "" | two-way: the visitor's typing writes it (interactive) |
| typed | number | 999 | characters shown, for scripted typing (the ui-controls typing, caret font) |
| message / showMessage | string / boolean | "Message" / false | |
| theme | number | 0 | 0 White, 1 Grey |
| size | number | 0 | 0 Default (35), 1 Compact (25) |
| focused, disabled, readOnly | boolean | false | |
| error, success, warning | boolean | false | priority error > success > warning > focus |
| interactive | boolean | false | click to focus and type |

### VibeFloatingBar (artboard `VibeFloatingBar`, 311x37, hugs) — the pilot
`open` (true) · `interactive` (false, passed down to every part) · and one property per part, each an instance of
the part's view model: `edit` (CoreButton), `divider` (Divider), `up`, `down`, `duplicate`, `padding`, `trash`,
`dismiss` (Icon button). Nested props are reachable 3 levels down, e.g. `bar/up/icon`, `bar/edit/label`,
`bar/dismiss/clicked`.

### v03 components (choices are numbers; `interactive` / `clicked` as above where listed)
| artboard | props (default) |
|---|---|
| Core Toggle (28x18, hugs) | `variant` 0 Toggle, 1 Switch 48x30 · `on` · `disabled` · `pressed` · `interactive`, `click` / `clicked` |
| Core Checkbox (16x16) | `state` 0 Empty, 1 On, 2 Partial · `disabled` · `pressed` · `interactive`, `click` / `clicked` |
| Core Radio Button (18x18) | `selected` · `disabled` · `pressed` · `interactive`, `click` / `clicked` |
| Pill_Tabs (hugs) | `count` 3 · `selected` 0 · `label1`..`label6` · `fill` · `icons`, `icon1`..`icon6` (Icon/i_site) · `interactive`, `changed` |
| SearchInput (248, hugs height) | `placeholder` "Search by" · `value` · `typed` 999 · `focused` · `disabled` |
| Status (hugs) | `label` "Status" · `color` 0 Neutral .. 7 Purple · `border` · `hover` · `dropdown` true · `unread` · `interactive`, `clicked` |
| Promotional Tag (hugs) | `type` 0 Default, 1 Premium, 2 AI, 3 New dot · `label` "new" |
| Tooltip (hugs) | `text` · `hug` · `shown` true |
| Loader (hugs) | `size` 0 16, 1 24, 2 48, 3 96 |
| Icon Thumbnail (hugs) | `icon` Icon/i_site · `theme` 0 Primary .. 6 Warning · `size` 0 40, 1 36, 2 24, 3 16 · `circle` · `disabled` |
| Core Tabs (hugs) | `count` 3 · `selected` 0 · `label1`..`label6` · `interactive`, `changed` |
| ListItem (419, hugs height) | `title` · `secondary` / `showSecondary` true · `prefix` true / `prefixIcon` / `prefixTheme` 0 · `suffix` true / `suffixIcon` Icon/i_options · `tag` / `tagLabel` "new" · `border` true · `state` 0 Default .. 6 Disabled · `hover` · `interactive`, `clicked` |
| MenuListItem (192, hugs height) | `label` · `showIcon` / `icon` · `hover` · `selected` · `destructive` · `interactive`, `clicked` |
| CoreDropdown (240, hugs height) | `label` / `showLabel` true · `value` · `placeholder` "Select" · `prefix` / `prefixIcon` · `open` · `disabled` · `error` |
| AiProcessIndication (hugs) | `label` "Thinking..." · `done` · `spinner` |

## Product / DS × polish

| what | product or DS | library | why |
|---|---|---|---|
| hover in / out | instant or 100 ms | 150 ms, fade token | motion spec |
| press | none | scale 0.9 (Icon button), 0.96 (CoreButton), 50 ms in, 333 ms release | arrive and settle |
| loading | label swapped for a spinner | keeps the width; the label leaves (0.1 s), then the spinner arrives on its last visible frame and turns 0.8 s per turn (v02) | no jump in the layout; one state at a time |
| message in (CoreInput) | appears | its room opens (0.25 s, duda), then it fades in and rises 4 px, settle; out: fades 0.1 s, then the room closes (v02) | no reflow in one frame |
| status / message icon (CoreInput) | swapped | the old icon fades 0.1 s, the new one starts on its last visible frame (v02) | one state at a time |
| tag removed (piece action) | disappears | fades and shrinks to 0.92 in 0.1 s, then the row closes the gap (duda, sized under the text cap) | one state at a time, no reflow in one frame |
| bar entrance | visual-edit v02 timings | same keyframes (opacity 0.05→0.20 s, scale 0.96→1 0.05→0.383 s, settle) | product |
| bar exit | - | fade 0.15 s, scale to 0.98 | polish |
| icon stroke | product 1.25 | DS 1.5 | Mateus, 2026-10-22 |

## Differences from the visual-edit v02 bar (all DS values)

Mean difference 6.4–8.0/255 through the entrance, ~8.3/255 on hover (`build/check/cmp/`). Same layout, sizes and
timing. The differences:
- icon stroke 1.5 (DS) vs 1.25;
- the padding icon is DS `general/i_padding` (the DS page "Mapping Icons - Flex Floating Bar" maps
  `i_flex_btn_clear_padding` to it) vs the product's clear_padding;
- Edit fill #e4e4e6 (newer bg-med-grey) vs #EDEDEE; divider #e2e2e4 vs #EDEDEE;
- icon hover tile black 4% (DS Dark color) vs 8%;
- hover fades in 150 ms vs 100 ms;
- the Edit label sits about 1 px higher.
The bar's edge (#E0E4E6, legacy Platform/Divider), drag handle and shadow are the product's.

## Open questions and assumptions

Fixed in v06: a piece whose `build/measure/fonts` link pointed at a deleted `lib/biblioteca-vNN` stopped with
"FileExistsError ... build/measure/fonts"; piece.py now checks `os.path.lexists` and replaces the link.

v03, known gaps (each says what a piece can't do yet):
- Pill_Tabs' white tab crossfades instead of sliding (hug widths are only known at runtime).
- SearchInput and the AI panel's ChatInput have no live text field (a piece types into SearchInput; the ChatInput is
  still). The top bar's AI button and the send button are drawings, without hover.
- MenuListItem has no hierarchy levels nor the checkbox prefix; CoreDropdown is Type Text only; Core Tabs has no
  counter, unread dot or disabled tab; Item Card is the horizontal KPI layout only.
- Icon Thumbnail's 24 / 16 px radii (4) are a guess. The Loader arc is the DS grey (the release notes draw it in
  colour).
- No Code / Manage views, no editor left panel, no scrolling lists, no AI gradient wash (generation effect).
- Only the DS / product icons a piece has needed so far (36): more are exported as pieces ask.

Decided 2026-10-22 (Mateus delegated the calls; v01 stays as built):
- CoreInput focus border: the newer token Borders/active-border-color is #aeafb3, the CoreInput component in Figma
  draws #cfcfd3. **Decided: #aeafb3** (DS values win, and the newer token wins).
- **Kept as assumed** until a DS page measures them: Icon button `border` (1 px #e2e2e4) and the Box hovers (the DS
  page has no Box hover variant); Text button focus ring (#e2e2e4); Compact text 13/18.
- CoreInput Mobile size: **left out for now** (the Vibe pieces are desktop UI). Added when a piece needs it.
- **Polish approved:** loading keeps the button's width, press scale (0.9 Icon button, 0.96 CoreButton), the
  CoreInput message fades in.
- Primary Disabled uses opacity 0.4 (the same as the DS on white, not on a dark background).
- The DS prop `type` is `variant` here (`type` is a Luau keyword).
- Order of sizes: CoreButton 0 Small / 1 Regular / 2 Large; Icon button 0 Small / 1 Large.

## What we learned about Rive (CLI 1.7.0 to 1.9.2, runtime 2.45.0)
- (v06) A feathered fill draws only with `fillRule="clockwise"` (on a layout box too): with the default rule the
  CLI draws nothing at all. An empty `hug` box has no height even with top and bottom insets: give it a size
  (percent units work, `heightUnitsValue="percent"`). `positionLeft` in percent can be keyed.
- (v06) In a layout box the first child draws on top: a selection tile listed before its icon hides it.
- (v05) The CLI applies every `--data` at the start, whatever its place among the `--advance`s: a sequence (send,
  then respond) needs a timeline (a host's, a piece's) to be tested. Only `--pointer` / `--semantic-action` follow the
  advances.
- (v05) Layout animation (`animationStyleType` custom, `interpolationType` cubic with a `CubicEaseInterpolator` in the
  style, `interpolationTime` in seconds) eases a box to its new place when the layout changes: a paragraph shown
  (display none -> flex) pushes what follows down smoothly, with no measuring. Works in the CLI and on 2.45.0.
- (v05) With the real text field shown (`interactive`), runtime 2.45.0 logs "Artboard::markLayoutDirty - trying to
  mark a layout dirty during clean pass!" (7 to 14 times as it loads); the field, the clicks and Enter all work.
- (v05) Element names are global in an RML document (listeners too): a component's own names get a prefix
  (`AiPanel.`), and listener names that repeat across components get refs.

- Icons as components work as Figma's instance swap: an artboard view model property bound to
  `NestedArtboard.artboardId`, with a child view model instance whose color is bound to the parent's color. It works
  two levels deep (Catalog → Icon button → Icon). On the web, swap with `vmi.artboard(path).value =
  r.getBindableArtboard(name)`.
- Lists work on the web (`addInstance`, `removeInstanceAt`). `viewModel.defaultInstance()` gives an instance with
  the defaults; `viewModel.instance()` gives a blank one (a color comes out black).
- Nested props: set_to actions with paths of 3 levels (`vm.bar → vm.bar.up → vm.ib.interactive`) and triggers 4
  levels deep (`proto → bar → dismiss → clicked`) work, in the CLI and on the web.
- A nested component hugs only when its own artboard's style hugs.
- A stateful nested artboard's own view model instance (the icon's tint) needs `exports="true"`, or it is dropped
  at export and the placement falls back to the view model's default (`rive inspect . --summary` reports it).
- Binding a layout value (minWidth) needs the style to carry it in points first (`minWidth=0`), or the bound value
  is read in the wrong units.
- CLI pointer tests: coordinates are viewport pixels (the artboard is fitted), so pass `--viewport=<artboard size>`
  for artboard points; a gesture at frame 0 sets the data but nested state machines miss it (advance ~5 frames
  first); frames after the last gesture don't reach nested state machines (end with a still `--pointer=move` on the
  same spot); `--key` doesn't type into a TextInput. Typing was tested on the web only.
- `--screenshot` captures only `main`: `stills.py` renders any artboard through a temporary project.
- Headless Chromium runs the clock unevenly: web shots prove states, not timing.
- Custom properties (`CustomPropertyBoolean` / `Number` / `String`) with a `DataBindContext` toward a nested
  component's view model, keyed on the host's timeline, drive the component's state machine: in the CLI and on the
  web (2.45.0, autoBind). It is how one timeline holds the cursor and every component state ("drivers").
- `rive <dir> --semantics=- --advance=2` prints the laid-out bounds of every `SemanticData` (role group): a cheap,
  exact layout measure (the piece's cursor targets), even of hug and flex layouts.
- Several `.rml` files in one project compile as one document; a file can point at another's ids directly
  (`kit.assemble(external=)`), and names can carry a prefix (`namespace=`).

## Tests (v03)

- Library: `rive . --verify` 0 errors, 0 warnings; the Catalog (1700x5104) shows the 15 new components in their states.
- The QUICKSTART example (now with a checkbox), built from the frozen bundle (`python release.py --check v03`): lints
  clean, verify clean, 9.17 s loop, 14 drivers, cursor peak 30.6/45 px/f.
- Web, `@rive-app/webgl2@2.45.0`, autoBind: the Catalog renders every new component (the Loader turns, the AI status
  shimmers); the example plays and its view model reads back `agree/state` 0 → 1 at 5.30 s, `go/loading` on at 5.90 s
  and off at 7.10 s; the release-note proof (Vibe workspace, AI panel, chat, `ai_status` spinner) renders as in the CLI.
- Proof against Figma: release note "Vibe MCP oct 2026", frame 3, mean difference 10.6/255.
- Open: "Chèvre" loses its accent in the CLI and on the web (the font has "è").
- `.rev`: `renders/v03/biblioteca_v03.rev`, uploaded to the Rive project as a new file (id 2678126).

## Tests (v02)

- Library: `rive . --verify` 0 errors, 0 warnings; `rive inspect . --summary` no problems.
- Regression against `dist/v01` (the same Catalog, Prototype and tests/Bar built from each bundle, 10 stills at fixed
  frames: `renders/v02/regress_catalog_pilot_v01_vs_v02.png`): mean difference 0.000/255 on every still. At rest
  nothing changed; the changes are only in the transitions.
- The same state changes on both versions (loading on / off, error → success, a message in), frame by frame
  (`renders/v02/swaps_v01_vs_v02.png`): v01 shows label and spinner together (f35, f95) and the error and success icons
  together (f97); v02 shows one state at a time and keeps the button's width.
- The QUICKSTART example, built from the frozen bundle (`python release.py --check v02`): lints clean, verify clean,
  8.55 s loop, 12 drivers, cursor peak 30.6/45 px/f (`renders/v02/example_stills.png`).
- Cold read: the example rebuilt by following only QUICKSTART.md (copy the bundle, paste the example, the four
  commands), and a second piece written from it alone (the floating bar: hover, duplicate, delete, undo; lints and
  verify clean, `renders/v02/coldread_bar_piece.png`). What it needed was added to the page: the web check, `mkdir`
  before `--rev`, `card(align=)`, what v02 doesn't have.
- Web, `@rive-app/webgl2@2.45.0`, autoBind (`renders/v02/web_example_play.png`): the example plays (typing, focus,
  remove hover, loading, success message read back from the view model), and `play` mid-run restarts it from the
  first frame (typed back to 0, the card hidden, then entering, the typing again). Also from a server at the repo
  root with `WEBTEST_URL`.
- `.rev`: `renders/v02/biblioteca_v02.rev` (not uploaded).

## Tests (v01)

- `rive . --verify`: 0 errors, 0 warnings. `rive inspect . --summary`: no problems.
- The `.rev` (`renders/v01/biblioteca_v01.rev`, made with `python build.py --rev`) leaves out the tests; read back
  with `rive create --from-rev`, it verifies clean and its Catalog renders identical to the library's.
- CLI pointer cases on Prototype (`build/check/cli/sheet.png`): hover, press, click to close and reopen (also mid
  entrance), hover pulse, tag x hover, input focus.
- Web, `@rive-app/webgl2@2.45.0` with autoBind (`build/check/web_proto.png`, `build/check/web_bar_list.png`,
  `build/check/web_features.png`): hover on a nested icon button and on Edit, the x closes the bar, Show bar reopens
  it, edits from the page (label, icon swap, color, loading, selected), typing "Hello Vibe" writes `input/value`,
  error state, the bar's open / close, list with `defaultInstance()`.
- Release check (`python release.py --check v01`, `build/check/dist_v01_example.png`): the example piece builds
  from the frozen bundle only, verifies clean, and its own state machine closes and reopens the bar.

## Suggestions for the team kit (not applied: tools/ is read-only from here)

- `rive_schema.py` could take the cache path from an argument, so a frozen copy can share one cache.
- A `stills.py`-like helper in `tools/` (stills of any artboard) would help every piece with more than one artboard.
