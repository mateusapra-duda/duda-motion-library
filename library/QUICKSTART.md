# Duda DS library v16b · QUICKSTART

The Duda Design System as Rive components, plus ready-made choreography. A piece is one Python file: place components,
lay them out, script the cursor and the states with actions, build. **This page is all you need**: don't open the
bundle's code, `manifest.json` or `motion-spec/` (the rules a piece needs are in section 6), except
`motion-spec/LEARNINGS.md`.

**v16b (2026-11-26): the motion designer's verdict on the ready-made animations (Prototypes).** He approved the grid but four cells,
and decided the three that were in doubt. All approved cells are curated examples now (section 4, "Curated
examples"). What changed in the defaults:
- **No creep after a press:** from a click the cursor takes ONE curve (0.6, 0, 0.25, 1) to its next stop, however long
  the wait ("no need to make the mouse walk slowly after the click").
- **The typing arc is his:** 16 % of the way at its middle, below (his Create Client); `type_into(gap=)` sets the
  time from press to press (1.45 s). A short step is a light bow, never a loop.
- **A collapsible opens on the press,** duda_strong over 0.5 s, the content fading in 0.2 s later (his "Stats report"
  row). Hang a list of them from a fixed top, so the header never moves under the cursor.
- **`a.stream` is letter by letter** (his call: the pattern stays one); word by word only with `words=True`.
- **Blocks generate as his Marketing Automation hero:** an edge line round each block as it shows, icons and their
  tiles turning orange -> pink -> their own, labels of interface blocks (`letters=False`) whole on his timings, and
  `a.generate(p.flow_link)` draws a map's line.
- **Code is written as his Code-reference:** a purple tip over magenta, the syntax colours coming in behind, no caret.

**v16 (2026-11-26): the motion designer's blind review (the bench).**
- **A file thrown into an input**, `a.drop_file(file, into=, zone=, result=)`: his own animation copied as it is, the
  library's first curated example (section 4, "Curated examples"). A file from outside the frame comes in already
  held, rides 141 px in 54 frames and the hand opens on the drop. Picking up what is on screen stays `a.drag`.
- **One cursor per scene** (the default): once the cursor has shown in a scene (between two `a.cut`s), the scene's
  next clicks press on their own (the Send presses itself); a cursor never vanishes and comes back in the same scene.
  `a.drag` takes over the arrow on screen (it turns into the hand where it is; no second cursor). The way out, when
  the motion designer asks for it: `a.click(..., cursor=True)`, `a.cursor_in(again=True)`, or
  `p.actions(cursor="any")` (the old behaviour). `cursor=False`: this click presses on its own.
- **`[cursorstart]`**: a cursor (or a hand) that shows and sits still (under 1.5 px a frame for more than 0.15 s) is an
  ISSUE: it shows already on its way.
- **`[hairline]` looks inside nested artboards** (the piece's components; and in `social.py`, the nested hero and its
  overlays under the video's camera: the flickering line of a social video was there).
- **Generation, box x loose** (`a.generate_screen`, on by default): only what has a box of its own is born from a
  gradient square (a photo, a library component, a fill that differs from what is behind it, a border, a shadow, a
  gradient). A block with no box of its own (a nav whose brand and menu are texts on the page, a column of texts and
  cards) is split on its own: its boxes keep their squares, its texts, icons and drawings come in loose, one by one, as
  in Base44. Every split is in the build's timeline; `(item, {"square": True})` keeps one whole, `split=False` all
  (the old way). A build where nothing splits is byte-identical to v15e.
- **`p.photo`: detail in a generated photo** (opt-in; `p.image` is unchanged): parts cut out of one photo (the big word
  on the wall, each product) come in on their own after the photo's background, and the photo comes in saturated,
  the saturation going away (Base44's hero). **v16a:** the parts are in the photo out of focus from its first frame
  and each comes into focus in its turn, in place (v16 cut them out: the filled holes showed as smudges on the wall
  and through the parts as they faded in).

**v15e (2026-11-25): what the social video taught.** A social video cut from a hero (`social.py`: the designers'
opening and end cards, a camera over the nested hero, 1:1 and 4:5 from one build; section 4); the centred zoom cut
between scenes, `a.cut(src, dst, "zoom", at="center")` (the click zoom still goes to the click); music on the beat
(`Music`, mixed into the MP4 by `render_mp4` and checked from its own audio); the `[hairline]` check and
`scripts/hairline.py` (a line under 1 px that flickers in a zoom); `render_mp4 --artboard`; and `a.drag` followed by
`a.cut` works again.

**v15d (2026-11-24): the hand-edit structure, checked.** `remap=` works on a piece with no cursor (it stopped there),
and the web check finds Playwright again. The Solo structure matches the plain build frame by frame in the site's
runtime (2.45.0), across zoom, white and tabs cuts and photos. With a runtime older than 2.45, `tabChange` doesn't
reach the page from a Solo piece: build that page without `remap=`.

**v15c (2026-11-24): built for hand edits.** `p.build(remap={...})` gives the same frames in a structure the motion
designer retimes by hand in the Rive editor:
- MAIN plays the scenes in a Solo, each with its own two-key "time".
- The elements you name (a card that generates) get an artboard of their own, with their own time.
- The cursor lives in its scene, or on MAIN when it crosses a cut.
- Section 8, "Built for hand edits". Without `remap=`, nothing changes.

**v15b (2026-11-24): a Figma screen in vector, the hand-edit diff, the email editor's parts.**
- `p.figma_screen`: a Figma screen from its SVG export, in vector, with native text and still parts as 2x plates
  (section 8).
- `scripts/handdiff.py`: what the motion designer changed by hand in the Rive editor (their `.rev` against our
  build), in beat terms: shifts, cursor legs and presses, curves, keys, elements. It is for a new version that keeps
  every hand edit.
- The email editor's parts: `p.template_card` (its hover with Use This / Preview), `p.block_panel`,
  `p.panel_field`, `p.segmented`, `p.color_field`, `p.color_picker` with `a.pick_color`.
- The interactive card: `live=True`, where the visitor's own mouse lights the hover, with no fake cursor.
- `p.hoverable(rise=)`; a hover also lights while the cursor goes to something inside the item.

**v15a (2026-11-24): fixes and small asks.** A disabled PrimaryButton as the DS draws it (its fill at 40 %, the
label at full white); `p.code_editor` draws the product's indent guides; `p.code_panel(save="Save Changes")` puts
"Discard" and "Save Changes" by the file's tab; `p.copilot_panel(field_top=)` keeps Figma's top for the field in any
frame; `a.cut` cascades a grid built as columns row by row across them; `render_mp4` (and every script) reads a
`.rev` saved by the editor (no `fps` on its timeline) and a `rive.yaml` with no `main:`; `webtest.py --port`.

**v14b (2026-11-23): what the two blind tests of v14 found.** An email carousel's story ends by ~5.5 s and the
rest stays still (`p.build(carousel=12)` notes a later last action; "~3 s still" is a hero's or a loop's); a
carousel with a Copilot opens on the send (`a.sent(msg, t=0)`). `a.cut` cascades what the click opened (the frame
around it comes in whole) and keys its screens' display itself. The cursor never shows inside the item it lights.
In `a.generate_screen` a block inside another comes with it. New: `p.hoverable` (a hover for your own drawing),
`p.copilot_field` (the docked Copilot's field, its send button keyed for you), `a.click(result=)`, the icons
`i_mobile_portrait`, `i_show`, `i_configuration`, `i_panel_right`, `p.icon("art/...")`, gradient `fill=` on
`p.card` / `p.free`, `opacity=` on the placers.

**The motion designer's cursor is the default (v14, 2026-11-23)**, from the precision research (302 review rounds of 36 pieces).
The cursor shows IN PLACE, ~220 px below its first target, on the side towards the frame's centre (a 3-frame fade,
already moving), and fades out where it rests, 8 frames after its last press: it never crosses the frame's edge. From
showing to the first target ONE curve (0, 0, 0.2514, 1), >= 38 frames; from stop to stop ONE curve (0.6, 0, 0.25, 1)
over 0.85 s + 1 ms per px, the typing arc passing its turn with no key there; after a press it goes straight on in
that one curve, however long the wait (v16b: no creep after a click); a wait after a stop creeps (~12 px/s) and a much
longer one (> 3 s) lets it vanish and another cursor show for the next target. Its tip never goes faster than 2.4 %
of the frame's width per frame (~31 px/f at 1300), and the build checks that for ANY cursor, the old one too. The old
cursor stays as an option: `a.cursor_in("right")` (or left, bottom, top). With it, the defaults that fought approved
rules changed: the hover lights when the tip ENTERS the item (not 150 ms before the press) and every control the tip
crosses lights too; a menu or popup the click opens starts on the release (8 frames after the press: `a.release()`,
`a.click(..., opens=modal)`); a menu's hover is dry (no fade); typing goes by the kind of text (a name ~14 letters/s,
not spread over the window; a sentence ~38; a prompt on one curve, the cursor gone); fields show no blinking caret;
`a.loop()` rests ~3 s in all (both sides of the seam); `p.build(carousel=12)` for a carousel tab (v14b: its story
ends by ~5.5 s, the rest still). Pieces made with an
older version keep theirs.

**A lighter generation, with no patches in the piece (v14, 2026-11-23: the motion designer's decisions on the precision research).**
(1) Every square is lighter: a card's from 108 % with Feather 11 -> 2, a panel's from 102 % with Feather 10 -> 1.5,
fading in over 16 frames; each square's first feather a little different (+-10 %). All the generation's feathers
(squares, wash, texts, icons) follow the size the piece is shown at: a 1340 px hero's as they are, a 432 px card's
at ~0.65 (squares) and half (wash, texts); in between by the width (`p.shown_at(w)` when a bigger artboard is shown
smaller). (2) `a.generate` / `a.generate_screen` / `a.loose` bring the content on their own, as an approved
hand-finished card did: texts letter by letter (the whole text orange #F9A84A -> pink #F4BBD2 -> its own,
Feather 4 -> 0), a two-line heading line by line, icons over 20 frames in the same colours, photos settling 112 % ->
100 % in their frame, numbers in v11's #AE68FA pop; the blocks and the loose elements in reading order, top to
bottom, with uneven gaps. No `details` pass, no purple on texts, no `_details` / `FX_STOPS` patches any more.
(3) `a.typewrite(text)`: any p.text types in with ONE key. (4) The answer (`a.reply`) is a plain typewriter, 120
letters a second and never more than 1 s in all. (5) The Copilot's send (LEARNINGS 5): the typed prompt rises 10.3 px
and fades out, the message comes 23 frames after the press with "Thinking..."; `a.send(panel)` presses send with no
cursor. (6) The AiPanel's field takes a fractional `typed` (one cubic key, ~53 letters a second: 84 frames for a ~74-letter prompt): the letter at the edge
fades in, never a half-drawn caret; there is no caret at all, and the placeholder goes on the click and never comes
back after sending.

**The approved rules of 2026-11-13 (v11).** (1) The Copilot's steps load with the classic spinner, never the
AI star, even where Figma draws the star: a 270° arc in one colour with a trail (#272B35 from 100 % to 12 %), turning
clockwise, one turn per 0.8 s; the step's text is dark from the start; at its end the spinner fades out in 3 frames,
still turning, and the check fades in over the next 3, the next line coming in as it lands. The "✦ Thinking..." above
keeps its star. (2) The Generation effect, as the approved example (the hero's dashboard): `a.wash` sweeps the whole
area first; each block comes from its gradient square (`a.generate`, as before); inside a block, titles and numbers
come in #AE68FA and turn to their own colour with a Feather 4 -> 0 (no more orange / pink); loose elements (no block)
come in with `a.loose` (#8D5DF5, Feather 4 -> 0); numbers count for 2 s on (0, 0, 0, 1), ending slowly, from close to their value (10-35 below it); every pass of
the gradient on (0.588, 0, 0.377, 1); `colors=` takes the designer's own gradient colours from Figma. Pieces made
with an older version keep it. Both are in `motion-spec/LEARNINGS.md`.

**Pick and drop (v12, 2026-11-13): the approved recipe, the rule for any drag.** The arrow turns into the closed hand on
the frame it takes the thing (a hard swap, no press scale), and the hand vanishes where it lets go (2 frames). The
thing follows the cursor (its own place stays empty), lifts up-left with a soft shadow, and on the drop it shrinks to
90 % and fades. A widget dragged from the side panel into a site (`a.drop_widget`): a blue "+" badge when it gets over
the site, the panel closes and the site scrolls to make room, the section below goes down, a blue line shows where it
goes, and on the drop the new section opens from inside the line, its items rising 40 px one after another. Path and
curves of the second reference up to the grab, the first from there on (the key frames in motion-spec/refs/drag-widget-ref*-key-frames.png; motion-spec/LEARNINGS.md 19.1). The cut to the close-up is a rare
option, off by default.

**A screen the AI generates (v13, 2026-11-13): the approved recipe** (`motion-spec/LEARNINGS.md` 6, 7 and 19.2). The generation
happens during the Copilot's loading, not after it: `a.generate_screen` starts the wash 6 frames after the message is
sent, with "✦ Thinking...", then the medium blocks big to small (~1 s apart) and the small details last (letters,
icons, lines); `a.steps(reply, t, until=end)` paces the steps so the last check lands as the generation ends (no
spinner turning alone), and the answer comes ~25 frames later. While the steps load, the top is "✦ Thinking..." even
where Figma shows "Show steps" (`p.chat_steps` has no "Show steps" any more). When the design has a gradient of its
own (a background, a card, a button), `gradient=(warm, cool)` gives the wash, the blocks and the texts its tones. And
`p.build` keeps only what the piece uses (the components it places, the fonts cut to its characters, the photos as
WebP): the welcome email went from 2.7 MB to 0.3 MB.

**Three defaults (v13c, 2026-11-18): the approved rules.** (1) A generation block always covers its component
with room to spare: 5 px more on every side and the component's corner radius + 5 (a square corner gets 5), read
from the item; at the exact size, the block's soft edge let the component's edge show through (dark dashes around
the block). (2) `a.loose` sharpens a loose icon or logo too, not only texts (and `a.generate_screen`'s details). (3)
An icon that only sits there is `p.icon`, drawn on its own: `p.icon_button` brings the whole component (~0.17 MB);
the answer's icons under `p.chat_reply` are `p.icon` now (`buttons=True` for a cursor that uses them).

**Two fixes on the v13 (v13b, 2026-11-13): the approved rules.** (1) The docked Copilot's field is always whole in the frame:
`p.copilot_panel` pins it to the panel's foot with Figma's margin (16 at 1x, ~13 px in a frame at 0.81); when the
frame is shorter than the panel, the conversation gets shorter, never the field. (2) The sent message, always: it
appears over 5 frames (linear) and rises 20 px in 30 frames (0, 0, 0, 1), both from the frame it is sent (`a.sent`;
the AiPanel's bubble does the same).

**The copilot's status (v08, 2026-10-26): the approved motion is the official one.** "Thinking..." stays right under
the user's message (the star turns in, the text wipes in and shimmers); as the answer starts below it, it wipes out
for "Thought for Xs" in the same place, without the star, then a chevron. In `p.ai_status`, `p.chat_reply` +
`a.think` / `a.reply` and the AiPanel. (The product pushes "Thinking..." down under the answer: poetic licence.)

**The Push Feedback Message (v09, 2026-10-26): `p.feedback` + `a.feedback`.** The DS alert after an action
("Permissions saved"...): top right, 24 px under the top bar and 24 px from the right (in a large popup: top centre of
it); it comes in, stays a few seconds and leaves on its own. v09 only adds it to v08.

**Marketing Automation (v10, 2026-10-27): the automation map and the Copilot's steps.** `p.flow_node` (the map's
steps: Start trigger, Add/Remove label, Update field, Send email, If/Else, End, and the Wait pill; hover, selected),
`p.flow_link` / `p.flow_split` (the map's lines, "+" and NO / YES), and `p.chat_steps` + `a.steps` (the Copilot's
steps, each turning into its check, then "Done - ..." in the summary's place). v10 only adds these to v09.

**The Highlights page (AEO report): v07d's is the official version** (approved on 2026-10-24; later versions keep it as is): a
piece with the Highlights page or its parts (KPI cards, donut, line chart) uses v07d or later; v07, v07b and v07c
were review rounds, not published here. The lavender layer over the line chart's area stays while the timeline plays, with
no fade (approved as is).

## 1. Set up a piece and build it (from the repo root)
```bash
mkdir -p pieces/<piece>/lib && cp -R library pieces/<piece>/lib/biblioteca-v16b
# write pieces/<piece>/build.py (start from the example in section 5), then:
.venv/bin/python -I pieces/<piece>/build.py                    # scene.rml (+ rive.yaml), timeline, lints
(cd pieces/<piece> && ~/.rive/bin/rive . --verify)             # must say 0 errors
.venv/bin/python -I pieces/<piece>/build.py --stills 1.2 3.4   # PNGs + sheet.png in build/stills/ (one CLI session, each frame 1 ms past its time)
mkdir -p pieces/<piece>/renders/v01 && (cd pieces/<piece> && ~/.rive/bin/rive . --rev=renders/v01/<piece>_v01.rev)
```
The build exits 1 and prints `LINT:` lines when a motion rule fails. Never run `rive push`, `--publish` or
`rive library publish`, and don't open a live preview unless asked. Python always via `.venv/bin/python -I`.
**Moving a piece made with an older version to v14** (only on purpose): drop its own `format="webp"` patch after
`p.build` (`slim` writes the format now; a second one makes the CLI fail with "malformed attribute"), and write
`a.cursor_in("right")` where it should keep the old cursor from the edge. Then compare with `scripts/keydiff.py`.

**Checks on every build** (`checks.py`, after the lints; fast, nothing rendered). An issue prints as `LINT: [check]`
and fails the build; a note prints as `NOTE: [check]`, for you to read:
- `[rml]` ISSUE: a loose `.rml` in the piece folder besides `scene.rml` (the CLI builds every `.rml` it finds). Keep
  copies as `.rml.txt`, or add the folder to `rive.yaml`'s `exclude`.
- `[weight]` objects per artboard (library components apart): note over 10k or 8k vertices of the piece's own drawing,
  ISSUE over 40k in one artboard (the editor freezes). `[outlines]`: text drawn as outlines (Figma SVG), note from 100
  letters: use native text.
- `[hidden]` never visible the whole timeline; `[offframe]` always outside the artboard (or its clipped box);
  `[offscene]` a screen (150+ objects) hidden by opacity 1 s or more while still on: key its display none
  (`a.c.set(t, "<box>.style", "displayValue", 1)`). The screens of an `a.cut` get it on their own (v14b).
- `[layoutfade]` what the lints can't see because they don't multiply layout boxes' opacity: a "false OVER" while the
  box is faded out, a `settle` on something visible through its box, a box held half-faded (each layer fades on its
  own: what it covers shows through). `a.cut`'s own moves are left out (v14b).
- `[hairline]` (v15e) a line under 1 px on screen (a stroke, or a painted box or rectangle that thin, times the scale
  of everything above it) shown 0.5 s or more while its scene zooms or slides slowly (0.02-2 px a frame): each frame it
  falls whole on a pixel row or across two, a flicker no still shows. Note; fix: 1.5 px or more on screen with the
  opacity down in proportion (thickness x opacity the same). Check it with `scripts/hairline.py`. `a.cut`'s own frames
  are left out. v16: it looks inside the components the piece nests (their static scale and opacity; their own state
  machines are not seen), and `social.py` runs it on the video: the nested hero, its overlays and what they nest,
  under the video's camera (a note names the artboard: `Site and phone XL > MAIN.x.bnLine`).
- `[cursorstart]` (v16) a cursor, or a hand (`a.drag`'s, `a.drop_file`'s), that shows and then sits still: under
  1.5 px a frame (at a 1340 px piece) for more than 0.15 s from its first frame. ISSUE: a cursor is on its way when
  it shows (LEARNINGS 3). A file that comes in held is `a.drop_file`, not `a.drag`.
- `[slim]` what each image became (lossy WebP 90 for photos, lossless for sharp ones, kept as it was) and its size.
`checks.allow("weight")` in build.py turns that check's issues into notes (an exception the motion designer approved).
On any built piece, the scene-only checks: `.venv/bin/python -I $L/checks.py pieces/<piece>`.

**Images** (`slim`, on by default): a photo becomes lossy WebP 90 and its asset says `format="webp" quality="0.9"`; a
sharp image (avatar or small image, UI capture, transparency, few colours) becomes lossless WebP and its asset says
`format="png"` (the editor's export re-encodes by that format, so it stays lossless there too); a `.webp` source is kept
as it is and gets its format. One image otherwise: `p.image(..., quality="lossless" | "lossy" | 85 | "keep")`, or
`slim.QUALITY["img.main_photo"] = ...` (the asset's name, or the file's) before `p.build`. Don't patch `format=` into
scene.rml after the build any more.

**Compare, edges, render, key diff, web check**: scripts in the bundle (they work in any folder;
`L=pieces/<piece>/lib/biblioteca-v16b`):
```bash
.venv/bin/python -I $L/scripts/compare.py pieces/<piece> pieces/<piece>/figma/frames/01.png@0 pieces/<piece>/figma/frames/02.png@719
.venv/bin/python -I $L/scripts/edges.py pieces/<piece>                    # edges and seams at ~5x, key frames
.venv/bin/python -I $L/scripts/render_mp4.py pieces/<piece> pieces/<piece>/renders/v01/<piece>_v01.mp4   # 2x
.venv/bin/python -I $L/scripts/keydiff.py pieces/<piece>/versions/v03 pieces/<piece> --expect 'cursor|reply'
.venv/bin/python -I $L/scripts/handdiff.py pieces/<piece>/versions/v03 ~/Desktop/<piece>_v03_edited.rev   # hand edits
.venv/bin/python -I $L/scripts/webtest.py pieces/<piece> 0.5 2 4      # the site's runtime 2.45.0, shots at those seconds
.venv/bin/python -I $L/scripts/hairline.py pieces/<piece> --at 2.0 --col 600 --rows 280:300   # does a thin line flicker?
.venv/bin/python -I $L/scripts/music_mux.py --check <video.mp4> pieces/<piece>/music.json      # the music of an MP4
```
- `compare`: each pose is a Figma PNG and its frame after `@` (or `--frame N` for all; a folder takes every PNG). Both
  are scaled to the artboard x 2 (`--scale`), never cropped (1x, 2x, the desktop app's 1024 px preview, a 1 px border
  is trimmed); one CLI session, each frame 1 ms past its time, `--fit=contain`. Per pose: the mean difference (target
  <= ~12/255), the % of pixels off by more than 40 (a local error the mean hides) and a 3 x 3 grid of both (a cell over
  4 % off gets `*`), then every text of 20 px or more (`--min-text`): its ink width in the render against the Figma
  frame at the same place, `TEXT` over 3 % (`--tol`); "unsure" when it is clipped, covered or has ink beside it in
  Figma. Pick rest poses (a text being typed reads small). Look at `build/compare/<pose>_overlay.jpg` (flagged texts
  boxed in red) before saying it matches; exit 1 when something is off.
- `edges`: renders the first and last frame, each hard cut and the two longest rests (`--frames 0,240` to choose) at
  ~5x (5.3: at a whole zoom, edges on 0.2 px steps hide their seam) and looks across every image edge, clipped box,
  nested component, filled block (two meeting = a seam) and the artboard's border. A line lighter or darker than both
  sides, all along the edge, at most ~1.6 px wide is `SUSPECT`; lines drawn on purpose (strokes, thin boxes, soft
  shadows) and hidden elements are left out. `build/edges/sheet_f<N>.jpg`: crops of the suspects and of every image
  edge, to look at; `--region x,y,w,h` adds a place you want to see. Fix a line with a band (LEARNINGS 13), run again.
- `render_mp4`: 2x by default (`--scale`, `--size WxH`) with `--fit=contain`, every frame 1 ms past its time (frame 0
  is the animation's, not the setup pose; a hard cut lands on its frame), 60 fps, x264 slow CRF 12, BT.709, faststart,
  in parallel CLI sessions (`--jobs`); it stops if scene.rml changes meanwhile. Look at `<out>_sheet.jpg`: frames read
  back from the MP4 itself. For the site's video, render from the project whose `.riv` is the delivered one. v15e:
  when the piece has a `music.json` (`Music.save`, section 4) the track goes in (AAC 256k, 48 kHz) through
  `music_mux.py` and is checked from the MP4's own audio; `--music <json>` another, `--no-music` none; a `--frames`
  test has none. `--artboard NAME`: another artboard with its own "Timeline" (a social video's format).
- `music_mux` (v15e): the mix, in this order: delay (before the speed change, or it is lost), `atempo` (same pitch),
  the video's length, fades. `atempo` plays the track early when it slows it (11-13 ms at 1.5-2 %; AAC adds nothing):
  compensated, then measured and corrected once. The check matches the track's loudness envelope against the MP4's
  (0.5 ms steps): the audio's offset (within 2 ms) and each `Music.hit` against its cut frame (within half a frame).
  `--check` on any MP4 with its `music.json` (a delivered social video: -0.7 ms, its hit +0.1 ms).
- `hairline` (v15e): renders ~30 frames from `--at` and reads one column across a horizontal line (`--col X --rows
  Y0:Y1`; `--row Y --cols X0:X1` for a vertical one), artboard px, the span holding that one line and plain background.
  Per frame the line's peak (its brightest difference from the background) and its sum; FLICKERS when the peak swings
  over 30/255 (exit 1). A 0.5 px line in a 2 %/s zoom swings ~46; the same line at 1.6 px and 31 % opacity, ~14.
- `keydiff`: two versions (piece folders or scene files, `versions/vNN/scene.rml.txt` too): the keys that moved or
  changed, by element (`shift +6 f`, `frames 120 -> 126`, `values f240: 0.5 -> 1`, `curves`), and objects only in one.
  `--expect REGEX`: what you meant to change; anything else is `UNEXPECTED` and exit 1. Run it after every change, before
  delivering (a change that moved what wasn't asked).
- `handdiff` (v15b): what the motion designer changed by hand in the Rive editor, so a new version never loses it.
  - Give it ours (the build the edit started from: the delivered `.rev`, `versions/vNN`, or the piece) and theirs
    (the `.rev` exported from the editor, or a folder made by `rive create <dir> --from-remote-file=<id>`).
  - It lists, per timeline, in frames and seconds:
    - the shifts ("from f149 on: -37 f"), the most common hand edit;
    - each cursor's path in px, its presses and its legs (frames, px, curve, the press lead);
    - every other changed track: keys, values, curves, named when they match a library curve ("= cursor glide");
    - elements added, removed or renamed, and changed texts and paths.
  - Matched by name, never by id; the editor's own bookkeeping is left out.
  - `--json out.json` writes every key on both sides, for a step that re-applies the edits.
  - A `.riv` can't be read back: ask for the `.rev`.
- `webtest` takes `build/<piece>.riv` (or `--riv <file>`), serves it, plays it headless with `autoBind` and saves
  `build/webtest/MAIN_<t>s.png` and the log (needs Node and Playwright: SETUP.md's optional
  step). `--plan plan.json` for clicks, typing and view model values: `[{"name": "x", "ab":
  "MAIN", "w": 1340, "h": 638, "s": 0.5, "watch": "play,email/value", "steps": [{"at": 2, "shot": "a"}, {"at": 3, "js":
  "window.T.fire('play')"}, {"at": 4, "click": [600, 300]}]}]`. Headless Chrome runs the clock unevenly: shots prove
  states, not timing (exact frames: the CLI stills). v15a: `--port N` serves on that port.
- Every script reads the piece through `rive.yaml` and `scene.rml`; v15a: a `rive.yaml` with no `main:` line uses the
  artboard "MAIN" (a note says so), and a timeline with no `fps` (a `.rev` saved by the editor, converted with
  `rive create --from-rev`) is 60 fps.

## 2. The scene
```python
p = Piece("MAIN", 1340, 638, bg="Backgrounds/bg-grey-color")   # artboard name, size, '#rrggbb' or DS colour token
```
`bg=None`: a see-through artboard (the page shows behind it). `cursor_shadow=True`: the cursor's soft shadow (the
storyboards draw it); `cursor_scale=`: its size.
**Components** (each returns an item the actions can target; `**props` are the props of section 3)

| call | what it makes |
|---|---|
| `p.button(slot, **props)` | CoreButton. v15a: `disabled=True` as the DS draws it: a PrimaryButton's fill at 40 % (Brand: the token "primary-40% (disabled)") with its label at full white; a SecondaryButton or TextButton fades to 40 % as a whole. `a.set(btn, disabled=False)` brings it back over the hover fade |
| `p.icon_button(slot, icon="i_send", **props)` | Icon button (for an icon the cursor hovers or clicks) |
| `p.icon(name, icon, color="Icons/icon-color", size=16, slot=24)` | v13c: a DS icon drawn on its own, for an icon that only sits there (no component: `p.icon_button` weighs ~0.17 MB): `size` px in a `slot` px square, as a small Icon button shows it (16 in 24, the DS grey); `color` a DS token or '#rrggbb'. `a.loose` sharpens it from a Feather. v14b: `icon="art/ai_star_purple"` draws one of the library's own drawings (art/) in its own colours; new DS icons `i_mobile_portrait`, `i_show`, `i_configuration`, `i_panel_right` |
| `p.input(slot, w=320, **props)` | CoreInput, `w` points wide |
| `p.search(slot, w=248, **props)` | SearchInput |
| `p.dropdown(slot, w=240, **props)` | CoreDropdown (a click opens / closes it; its menu is a `p.menu`) |
| `p.tag(slot, **props)` | Smart_Tag |
| `p.status(slot, **props)` · `p.promo(slot, **props)` | Status · Promotional Tag |
| `p.toggle(slot, **props)` · `p.checkbox(slot, **props)` · `p.radio(slot, **props)` | Core Toggle · Core Checkbox · Core Radio Button |
| `p.pill_tabs(slot, w="hug", **props)` · `p.core_tabs(slot, **props)` | Pill_Tabs · Core Tabs; each tab is a target: `tabs.tab(1)` |
| `p.list_item(slot, w=419, **props)` | ListItem |
| `p.thumb(slot, **props)` | Icon Thumbnail |
| `p.tooltip(slot, **props)` | Tooltip |
| `p.loader(slot, **props)` | Loader (always turns) |
| `p.ai_status(slot, **props)` | AiProcessIndication: the AI status line ("Thinking...", shimmering on its own; `shown=False` hides it until `a.set(st, shown=True)` plays its entrance; `done=True` swaps it for `thought`, "Thought for 3s"; `thought="Done", chevron=False`: "Done" with no chevron) |
| `p.feedback(slot, **props)` | FeedbackMessage (v09, the DS Push Feedback Message): the alert after an action, placed hidden; `a.feedback` brings it in and takes it away. Put it top right, 24 px under the top bar and 24 px from the right (a large popup: top centre) |
| `p.flow_node(slot, type=3, **props)` | FlowNode (v10, Marketing Automation): a step on the automation map. `type` 0 Start trigger, 1 Add/Remove label, 2 Update field, 3 Send email, 4 If/Else, 5 End (the card, 325 x 93), 6 Wait (the pill, 221 x 42); the title and subtitle default to the storyboard's. Nothing in it moves: bring it in with `a.generate`. `a.click(node)` selects it (the blue edge) |
| `p.ai_step(slot, **props)` | AiStep (v11): one line of the Copilot's steps (the classic spinner turning, then `done`: the check; the text dark all along). A list: `p.ai_steps` / `p.chat_steps` |
| `p.text_area(slot, w=358, h=126, **props)` | Text Area: a field of several lines under its label (the label takes 26 of `h`); `a.type_into` types into it, the lines wrap |
| `p.divider(slot, w=240, **props)` | Divider (`variant=2` vertical: give `h=`; `h=1`: just the line) |
| `p.bar(slot, style="ds", open=True, over={"trash": {"selected": True}})` | VibeFloatingBar; its parts are targets: `bar.part("trash")`. `style="storyboard"`: the hero storyboards' bar ("Edit Design", left, right, a menu in place of close) |

**Text, images, layout**

| call | what it makes |
|---|---|
| `p.text(name, "Hello", style="Headlines/He 1", color="Typography/primary-text-color", w=None)` | DS text: one line; `w=` points or `"fill"`: a paragraph that wraps (`align=` left, center, right) |
| `p.font(key, "fonts/Brand.ttf", "Brand")` then `p.text(..., style=None, font=key, size=, lh=, weight=)` | a client's typeface (a file in the piece folder, one per weight). The keys `duda`, `caret`, `mono` and `cal` (Cal Sans SemiBold: the dashboard's titles and numbers) are the library's |
| `p.image(name, "img/photo.jpg", w, h, fit="cover", radius=0, quality=None)` | a photo or screenshot in a w x h box: `cover` crops (Figma Fill), `contain` (Fit), `fill` stretches (v14: it drew small before). `quality` (v14): `"lossless"`, `"lossy"`, 1-100 or `"keep"` for this image; by default `slim` decides by kind (see Images) |
| `p.photo(name, "img/hero.png", w, h, parts=None, fit="cover", radius=0, align=(0.5, 0.5), saturate=True, quality=None)` | v16: a photo like `p.image` (same `fit`, `radius`, `align`, `quality`) whose generation has more detail. `parts={name: shape}`, back to front, in the photo's own pixels (as the file is): `(x, y, w, h)` a rectangle, `[(x, y), ...]` a polygon, or a dict: `box=(x0, y0, x1, y1)` / `poly=[...]`, `key="light"` (only the shape's white pixels: big white letters on a wall, not the wall between them; `"dark"` or `'#rrggbb'`), `anchor="bottom"` (an object; the default) or `"center"` (the default with a key): the part's origin, for your own keys. A part loses what the parts after it cover. The library makes a plate (v16a: the photo with every part out of focus in it, each blurred on its own over what is behind it) and one layer per part (the next state: that part sharp), in `build/photo/` (cached); at rest the photo is its own pixels. In a generation: the plate settles as any photo (112 % -> 100 %), then each part comes into focus over 10 frames, in place (no grow: a part scaled is out of register with what is under it), 8 frames apart, from ~0.4 s after the photo shows; a white or black part (the word) takes the texts' colour pass (orange -> pink -> its own). `saturate=True`: it comes in saturated (a "saturation" blend layer at 50 %, ~1.5x the colour) and loses it over 0.6 s, 0.1 s after the last part is in. `photo.parts["word"]`: a part's handle, for your own keys. Polygons: trace them on a zoomed grid of the photo, a few px outside the object's edge (behind a part, the photo is filled 16 px past its shape, seen only through its blur), and the object whole, or cut only where it is off-screen (the blur stops at a cut). Look at the frames of the entrance at 5x |
| `p.row(name, kids, gap=8, pad=0, align="centerLeft", w="hug", h="hug")` | horizontal stack |
| `p.column(name, kids, gap=16, pad=0, align="topLeft", w="hug", h="hug")` | vertical stack |
| `p.free(name, [(item, x, y), (item, x, y, scale)], w, h, clip=True, radius=0, fill=None)` | each child where Figma has it, back to front; `scale` from its top-left (a product UI at 0.73 in a storyboard); `radius`: round corners, the clip included. v14b: `fill` a background, a token / '#rrggbb' or a gradient `("#FFFBD6", "#FFFFFC")` top to bottom (an email's; `(c1, c2, "right")` left to right; more stops, or `(colour, position)`) |
| `p.stack(name, screens, w=None, h=None, clip=True)` | v14: the screens that `a.cut` swaps, in one place (a `p.free` with each at 0,0, `w` x `h`, default the frame, clipped). The first is on screen at the start, the others hidden until a cut brings them in. Give them in the tabs' order: a `"tabs"` cut moves against the pill. Example: `p.layout(p.stack("screens", [home, settings]))` |
| `p.wrap(name, elements, w="hug", h="hug")` | your own drawing (kit or tools/rml.py shapes) as a target (section 8); loose shapes go in a Node inside it, back to front, so the box doesn't stretch them |
| `p.figma_screen(name, "figma/vec/screen.svg", layer=None, frame=None, drop=(), parts=(), plates=(), texts=None, fonts=("duda",))` | v15: a Figma screen from its SVG export (Export > SVG of the frame, into the piece's `figma/vec/`) as one item, in vector: native text (one Text per line, in the DS weights), photos as images, masks and off-screen shapes left out. `layer`: the layer to draw (its Figma name); `frame=(w, h)`: the frame the export carries, its top-left is the box's (0, 0). `drop`: layers the library draws instead (a button, a field: place them over it). `parts`: layers that become their own items, `scr.parts["Table"]`, for `a.generate` / `a.enter` / `p.hoverable` (their texts are typed in). `plates`: still layers as 2x images (`True`: the whole screen). `texts`: `{"<layer or sheet key>": "its text"}` for texts not named by their text. Place it like any item (`p.free`, `p.stack` + `a.cut`) |
| `p.figma_sheet()` | v15: after the `figma_screen` calls, `build/figma/kept_<n>.png`: the texts that stayed outlined, big, each with its key. Read them and give them as `texts=`; run once per new export |
| `p.asset(key, "img/photo.png", quality=None)` | an image of the piece for your own `Image` elements: returns its asset id (`"@img.<key>"`). v14: `quality` this image's encoding in the light build, as `p.image(quality=)`: `"lossless"`, `"lossy"`, 1-100 or `"keep"` |
| `p.shown_at(w)` | v14 (LEARNINGS 7, "Feathers follow the size the piece is shown at"): the width (css px) the piece is shown at on the page, when it isn't its artboard's (a 1340 artboard shown in a 432 card). The generation's feathers scale by it: as drawn from 1340 up, ~0.65 on the squares and half on the wash and the texts at 432, in between by the width. Default: the artboard's width (a 432 x 264 card needs nothing). Call it before the actions |
| `p.card(name, kids, w=380, pad=24, gap=16, title=None, action=None)` | DS card: white, radius 8, 1 px edge, shadow-1; `title` (Bold 16/22) with an optional text button `action` ("See all", a target: `card.action`); `w="hug"`, `shadow=`, `border=`, `fill=` (v14b: a gradient too, as `p.free`'s; top to bottom needs `h` in points), `radius=` |
| `p.hoverable(item, veil=None, border=None, fill=None, show=(), fade=0.1, radius=None, rise=(), live=False)` | v14b: a hover for an item the piece drew (a `p.card`, `p.free`, row, column, `p.wrap`, an image): it lights as a library component's, on the frame the cursor's tip enters it, off when it leaves (`a.click`, `a.move_to`, `a.hover`), and also when the cursor only passes over it. `veil` a colour over it ('#rrggbbaa': a card darkening), `border` an edge inside it (colour or (colour, width)), `fill` a colour under its content (a row's #F6F6F8; for a box with no background of its own), `show` items inside it seen only while it is lit (a template card's "Use This" / "Preview"); each fades over `fade` s (0: dry). Example: `p.hoverable(card, show=[actions], fade=0.15)`. v15b: `rise` items also rise 6 px in 0.5 s as they show; the hover also lights while the cursor goes to something inside it (`a.click(card.use)` lights the card); `live=True`: the visitor's mouse lights it (the interactive card, below) |
| `p.template_card(name, label, image=None, w=308, live=False)` | v15b: a template of the email gallery (308 wide, the thumbnail `image` on #F4F4F4, its name under it). Its hover lights when the cursor's tip enters it, also on the way to its buttons: a dark veil and "..." fade in (0.15 s), Use This / Preview rise 6 px in 0.5 s. Targets `.use`, `.preview` (`a.click(card.use)`) |
| `p.block_panel(name, title, kids, w=266, h=None)` | v15b: the email editor's side panel for a block: the header (back arrow, `title` in caps) over a hairline, the body. `kids`: items, or strings: `"# Button style"` a section title, `"Link"` a field's label, `"---"` a divider. Two fields side by side: `p.row([...], gap=12, w="fill")` |
| `p.panel_field(name, value, unit=None, icon=None, chevron=False, w="fill", label=None)` | v15b: a field of the side panel (#F4F4F5): `value`, a `unit` at its right ("px"), an `icon` before the value ("common_actions/i_expand"), a `chevron` (a select); `label="Padding top"` puts a label above it. Target `.value` (`a.text(fld.value, "24")`) |
| `p.segmented(name, options, selected=0, w="fill")` | v15b: the panel's switch (Fit to text, Full width). `a.click(seg.options[1])` selects it on the press |
| `p.color_field(name, value, picker=None, w=113.5)` | v15b: the colour field (a swatch and the HEX). A press focuses it (blue edge) and opens `picker` on the release |
| `p.color_picker(name, colors, value=None, label="IN THIS EMAIL")` | v15b: the picker (saturation and hue with their handles, HEX, the swatches of `colors`), hidden until its field opens it (or `a.enter`). `value`: the colour it shows (its swatch has the blue ring). Place it where Figma has it (`p.free`, over the panel). Targets `.swatches[i]` |
| `opacity=` | v14b, on every placer (`p.button`, `p.icon_button`, `p.input`..., `p.icon`, `p.text`, `p.image`, `p.card`, `p.free`, `p.row`, `p.column`): a fixed opacity (undo / redo at 40 %). `a.enter` / `a.show` bring it to 1 |
| `p.drop_slot(name, new, line_w=None, color="#2A84EE")` | v12: where a widget dropped into a site opens (`a.drop_widget`): put it in the site's column between the two sections it goes between. It starts 0 high (the site looks untouched) and holds `new` (the section the widget becomes, shown only from the drop) and the blue line, `line_w` wide (default: the section's width - 108, so the opening ends on its edges) |
| `p.layout(root, align="center", pad=0)` | what the artboard shows (call once, before `p.actions()`) |

**DS patterns** (built from the piece's own content)

| call | what it makes |
|---|---|
| `p.menu(name, ["Rename", {"label": "Delete", "icon": "i_trash", "destructive": True}, "-", "# Section"], w=268)` | CoreFloatingMenu / a dropdown's menu (radius 12, shadow-5); `menu.entries` are its items |
| `p.collapsible(name, title, kids, w=400, open=False, icon=None, card=True)` | Collapsible: a click on `c.header` folds / unfolds it on the press; `a.open(c)` / `a.close(c)` without the cursor. v16b (his "Stats report" row): duda_strong over 0.5 s, what is under it going down, the content fading in 0.2 s after. Hang the list from a fixed top (`p.free`), not centred: centred, the header moves under the cursor as it opens |
| `p.table(name, header, rows, widths, w="hug")` | DS table: cells are strings (`"**Bold"`) or placed items; `table.rows` are the row boxes |
| `p.item_card(name, "1,204", "Visitors", icon="i_site", theme=1, trend="+12%")` | Item Card (the KPI card) |
| `p.modal(name, title, kids, w=480, primary="Save", secondary="Cancel", icon=None, primary_icon=None)` · `p.overlay(name, radius=0)` | Core modal (w 480 / 740 / 1000 / 1356; the title He 2 Bold 14/20 as the product; `icon="i_site"` before it; `primary_icon="chevron_right"` after the primary's label); targets `modal.primary`, `modal.secondary`, `modal.close`. The overlay goes under it in a `p.free` (`radius`: over a round window). A required field: `p.input(..., required=True)` |

**Dashboard: the AEO report** (v06: the site dashboard's Performance pages, Figma "AI-Visibility-highlights"; built at
the product's size: place it with `p.free(..., scale)` for a storyboard)

| call | what it makes |
|---|---|
| `p.aeo_highlights(name, kpis=None, donut=None, line=None, layout="figma", loading=False, tabs=("7 days", "14 days", "30 days"), tab=0, w=1101)` | the whole Highlights page: the title (Cal Sans) and its line, the date tabs (`tabs=None`: none), 4 KPI cards, the donut card and the line chart card (`layout="product"`: the line at the left, as the site has it). `kpis`: `[dict(value="82%", label="AI visibility score", trend="8.2%", down=False, icon="i_ai_assistant", tile="peach", info=False)]` (default: the Figma's four); `donut`: `[(label, value)]`; `line`: `dict(values=, ticks=, labels=)`. `loading=True`: skeletons until `a.load(page)`. Targets `.title`, `.tabs`, `.kpis[i]`, `.donut`, `.line`, `.donut_card`, `.line_card` |
| `p.dashboard(name, page=[...], site="Site Dashboard", rail=("i_stats", "-", "i_coupon", "i_settings", "-"), selected="i_stats", menu=None, menu_selected=0, w=1440, h=900, pad=32)` | the site dashboard's window: the top bar, the rail (the selected icon on a peach tile; "-" a divider), `menu=["Overview", "Highlights", "Visibility >"]`: the PERFORMANCE menu (">" adds a chevron), and the grey page holding `page`. Targets `.rail_items[i]` (tile: `.rail_tiles[i]`), `.menu_items[i]` (`.menu_tiles[i]`): `a.hide` one tile and `a.show` another to move the selection |
| `p.kpi_card(name, "82%", "AI visibility score", trend="8.2%", down=False, icon="i_ai_assistant", tile="peach", info=False, w=263, loading=False)` | the KPI card: the number (Cal Sans 26/28), the trend chip (green, up; `down=True`: red), the label (`info`: an (i) after it), the icon on a 36 px tile (peach, slate, mint, grey or '#rrggbb'). Targets `.value`, `.chip`, `.label` |
| `p.donut(name, [("ChatGPT", 32), ("Gemini", 54), ("Claude", 14)], total="23,000", total_label="Total", legend=True, size=184, w=304, loading=False)` | a donut as the Figma draws it (v07: 60 % hole, slices 1.2° apart with corners rounded 2.9 and a white edge; the Figma's coral, sage, slate...; `(label, value, '#rrggbb')` picks a colour), the total in its middle, the legend chips under it. Put it on a white card: a.draw uncovers it from under a white ring |
| `p.line_chart(name, values=None, ticks=(0, 1000, 2000, 3000, 4000), labels=None, w=662, h=305, fmt="{:,}", loading=False)` | a line over an area that fades down, the dashed grid, the y and x labels (default: the Figma's 64 points over 12 days) |
| `p.chart_card(name, "User visits", body, w="fill", h=418, pad=24, align="topLeft")` | a dashboard card: the header (Bold 16/22, a line under it) over `body` (a chart) |
| `p.skeleton(slot, w, h, circle=False, shimmer=True)` | Skeleton: a grey block that the product's shimmer crosses every 1.4 s (section 3) |

**The Vibe editor** (the product's shells, from its own components)

| call | what it makes |
|---|---|
| `p.vibe_workspace(name, canvas=[...], panel=None, w=1440, h=900, page="Home", radius=0, fill="#f6f6f8", compact=False)` | the whole window: top bar, canvas header, your `canvas` items on the white stage, the docked `panel` (or a list of panels in one place, the later ones on top: a chat and a Quick Edits that takes its place), the rail. `fill=None`: see-through around the stage; `compact`: the storyboards' denser canvas header. Targets `ws.topbar`, `ws.canvas_head`, `ws.rail`, `ws.panel` (`ws.panels`), `ws.stage` |
| `p.vibe_topbar(name, project="Project Name", tabs=("Canvas", "Code", "Manage"), tab=0, comments=True)` | the top bar (`tabs=None`: none); targets `.menu`, `.tabs`, `.comments`, `.share`, `.preview`, `.publish`, `.ai`, `.home` |
| `p.canvas_header(name, page="Home", compact=False)` · `p.vibe_rail(name, icons=(...), selected=None, learn=True)` | the bar over the canvas (`.refresh`, `.page`, `.device`; `compact`: 36 tall) · the right rail (`.buttons`; `"-"` is a divider; `learn`: the learning-centre cap at the end, as the product) |
| `p.ai_panel(name, title="New chat", prompt="...", reply=["paragraph", ...], floating=False, w=None, h="fill", placeholder=..., mode="Build", **props)` | v05: the **AiPanel component** (the copilot moved into the library): docked, the Vibe chat (406, a line at its left, +, the cursor tool, Build, mic); `floating=True`, the Copilot (368, rounded, a shadow, +, @). Empty it shows the greeting and four suggestions; `prompt` is what `a.type_into(panel, ...)` types and then the bubble; `reply` up to 3 paragraphs. Any AiPanel prop (section 3) goes in `props`. Targets: `panel.part("send")`, `"field"`, `"plus"`, `"tool"`, `"mic"`, `"build"`, `"options"`, `"collapse"`, `"chip1"`..`"chip4"`, `"showMore"` (floating: `"float"`, `"at"`) |
| `p.ai_panel(name, title, chat=[...], w=406, placeholder="Ask anything", mode="Plan", title_menu=True)` | the v04 panel, a free conversation of your own items (`chat=` given): header, the conversation, the ChatInput; targets `.options`, `.collapse`, `.input`, `.plus`, `.send`, `.title` (`a.text(panel.title, "...")`), `.chat`, `.content` (`a.hide(panel.content)` leaves the white panel for another) |
| `p.quick_edits(name, content="", heading="H1", font="Inter", weight="Bold", color="#1E1E1E", size="48", ...)` | the visual edit's Quick Edits panel (406 wide): header (pop out, close), Text (Content: a Text Area), Typography (dropdowns, the colour field, value + unit pairs), footer ("Pending changes", Discard, Apply). Targets `.content`, `.heading`, `.font`, `.weight`, `.color`, `.size` / `.size_unit`, `.letter`, `.line`, `.discard`, `.apply`, `.close`, `.popout`, `.pending` (hidden until `a.show(qe.pending)`) |
| `p.code_panel(name, code, files, file="App.tsx", tree_w=146, save=None)` | the Code tab: the file tree (a search over it) at the left, the open file's tab over a code editor. v15a: `save="Save Changes"`: the product's buttons at the right of the file's tab, "Discard" (a TextButton) 19 px before it, both disabled as the product shows them until there is a change (`a.set(panel.save, disabled=False)`). Targets `.tree`, `.editor`, `.search`, `.tab`, `.discard`, `.save` |
| `p.code_editor(name, code, size=10, lh=17, numbers=True, empty=True, guides=True, indent=2)` | the editor alone, JetBrains Mono, line numbers. `code`: text (JS / JSX coloured on its own) or lines of `[(text, kind)]` (k f t s c p); `empty`: it starts empty for `a.write_code`. v15a, `guides`: the product's indent guides, a 1 px #D3D3D3 line per level of `indent` spaces (a blank line takes the smaller indentation around it, so they run through it); they show with their line's number |
| `p.file_tree(name, ["src/", "  App.tsx", "  +TopBar.tsx"], w=146, selected=None)` | a tree: 2 spaces a level, `name/` a folder, `+name` a file that arrives later (`a.add_file`); `tree.rows["App.tsx"]` are targets |
| `p.gen_status(name, label="Generating...", done="Done")` | the AI star and "Generating..." (the hero Code tab): `a.generating` shimmers it, `a.done` turns it to "Done" |
| `p.chat_user(name, "text")` · `p.chat_ai(name, "text")` | the user's bubble (`fill=`, `pad=`) · the AI's answer; with `p.ai_status` they go in `chat=` (the free panel) |
| `p.chat_steps(name, summary, [step, ...], done, status="Thinking...", thought=None, gap=20, steps_top=14)` | the Copilot's answer while it builds (v10; in a chat column, `chat=[ask, reply]` or a `p.column`): v13: the status on top ("✦ Thinking..." while the steps load, even where Figma shows "Show steps"; `thought`: the done text, default "Thought for Xs"), the summary, then the steps (`a.steps`), and `a.reply` swaps the status for "Thought for Xs" and puts `done` in the summary's place as the summary and the steps leave. Text 13/1.35 as the storyboard. Targets `.status`, `.summary`, `.done`, `.steps` |
| `p.ai_steps(name, [step, ...], gap=8, top=0)` | the steps alone (v10): one AiStep a line, each taking no room until `a.steps` brings it in |
| `p.flow_link(name, h=36, add=True)` · `p.flow_split(name, span, stub=18, drop=76, labels=("NO", "YES"), add=True)` | the automation map's lines (v10, at the nodes' size; the storyboard draws the map at 0.5): a 2 px #D4D4D8 line with the "+" on its middle; an If/Else's branches, `span` between the two branches' centres, the box `span + 60` wide and centred on the node |
| `p.copilot_panel(name, header, chat, field=None, note=None, w=367, h=842, pad=(20, 16, 16, 12), chat_gap=21.2, chat_pad=0, fill="#FFFFFF", edge="#E4E4E7", margin=16, field_top=None)` | v13b: the docked Copilot of a storyboard (the email editor's, Figma's 367 x 842): `header` on top, `chat` (your items, or a list: a clipped column `chat_gap` apart), `field` at the foot, `note` (the line under it, if any). v14b: `field` defaults to the product's (`p.copilot_field`), and the `p.chat_steps` / `p.chat_reply` in `chat` drive it on their own. When the frame cuts the panel, the panel ends at the frame's bottom and the field stays whole, `margin` above it (Figma's 16 at 1x): the conversation gets shorter, never the field; the note goes below, out of the frame. v15a, `field_top`: the field's top as Figma draws it (panel points at 1x, from the panel's top): in a cut panel the field keeps that top at the product's height, shorter only when it wouldn't be whole `margin` above the frame's bottom ("same top, shorter"); without it the field is pinned `margin` above the bottom, which is Figma's top only in frames cut like the welcome email's. The build log says which. Build it before `p.layout`. Targets `.chat`, `.field` |
| `p.copilot_field(name, placeholder="Reply to Copilot", prompt=None, w="fill", h=124.5)` | v14b: the docked Copilot's field as the product draws it (ask-your-agent v05-v06): 124.5 high (100.8 at 0.81; in the welcome email's frame its top is Figma's 558), radius 8, a 1 px #EDEDEE edge, the grey placeholder, and at its foot only "+" (no outline) and send. Its button keys itself: grey #C9CACD while empty, orange from the first letter (no fade), the orange stop while the Copilot works (from `a.think` / `a.steps`; from frame 0 when sent at 0), and grey again with `a.reply`'s status swap (the stop fades out in 0.1 s, then the send fades in over 0.1 s; the edge rests). A cursor's `a.click(field)` makes the edge active and takes the placeholder away. `prompt`: a text to type: `a.typewrite(field.prompt, ...)` (the placeholder goes, the edge turns active, orange on the first letter), then `a.send(field, t, message=bubble)` (the press, the text flies out, the stop with the message). `p.copilot_panel` makes one by default. Targets `.prompt`, `.placeholder`, `.button` |
| `p.chat_reply(name, ["paragraph", ...], actions=("i_duplicate", "i_options"), gap=24, thought=None)` | the AI's answer as the copilot brings it (v08, in `chat=[ask, reply]`): the status right under the message (hidden until `a.think`), then each paragraph below it, taking no room until it comes, the action icons last. `thought`: the done text (default "Thought for Xs", X from `a.think` to `a.reply`). `gap`: above each paragraph and the icons. The icons are `p.icon` (v13c); `buttons=True` makes them Icon buttons, for a cursor that uses them. Targets `.status`, `.actions`, `.paragraphs`, `.bar` |

- `slot` / `name`: unique, letters and digits (it is the view model path on the web: `email/value`). Every call
  returns an item you pass to actions. `pad`: one number or (left, top, right, bottom). `w`/`h`: `"hug"`, `"fill"`
  or points. `align`: topLeft, topCenter, topRight, centerLeft, center, centerRight, bottomLeft, bottomCenter...
- Text styles: Display/Display 00, 0, 1, 2, 3 · Headlines/He 0 (18/24), He 1 (16/22 bold), He1 Half, He 2 (14/20),
  He 2 Bold, He 3 (13/18), He 4 (12/18) · Content/Description, Plain text (16), Body 14, Body (13), Body Bold,
  Paragraph, Tiny (12), Tiny Bold, Mini (11).
- Colour tokens: Backgrounds/bg-white-color, bg-grey-color, bg-med-grey-color, bg-dark-color · Typography/
  primary-text-color, secondary-text-color, hint-color, text-white-color · Borders/border-light-color,
  border-color, divider-color · Custom Branding/Primary-color · Indications/positive-color, negative-color,
  warning-color, info-color, ai-color, vibe-color. Anywhere a colour goes, '#rrggbb' works too.
- Icons (`icon=`, `leftIcon=`, `rightIcon=`, `prefixIcon=`, `suffixIcon=`, `icon1=`...): i_plus i_plus_2 i_send i_x
  i_search i_edit i_edit_disable i_duplicate i_trash i_info_circle i_spinner i_arrow_left/right/top/bottom
  chevron_right chevron_bottom i_at i_checkmark i_drag i_options i_padding i_site i_error i_hamburger i_share_file
  i_color_palette i_add_widget i_version i_mic i_cursor i_home i_refresh i_common_expand i_desktop i_ai_assistant
  i_site_comments i_learn i_appstore i_undo i_redo i_file i_pop_out i_like i_dislike i_floating_panel i_binoculars
  i_new_site i_user i_template · v06: i_stats i_coupon i_settings i_expand i_onboard_client i_engagement
  i_arrow_corner_up i_arrow_corner_down.
- Not in v06: lists that scroll, the Manage view, the editor's left panel, the
  agent's step list with drawn checks, the AEO report's other cards (Issues to optimize, Competitor AI Insights,
  Recent Responses). If a piece needs one, say so in its brief and ask before building it by hand.
- **The .riv needs its view model bound.** Every component reads its values and states from the piece's view model.
  On the site (`autoBind: true`), in the CLI and in the editor it shows right; where nothing binds the view model (the
  Mac's QuickLook, the space bar in the Finder; a runtime with `autoBind` off) icons show as "+", tabs and menus come
  out empty and the bar disappears. Not a broken file: always check it with the web check or the CLI.

### The interactive card (v15b)
A card on a page that the visitor hovers and clicks with their own mouse (a feature grid): it plays once, then
waits for the mouse. There is no fake cursor.
- `p.template_card(..., live=True)`, or `p.hoverable(item, ..., live=True)` for your own card. Call it before
  `p.actions()`.
- Its hover is a layer of MAIN's state machine, switched by listeners on the card. The timeline never keys it, and the
  build stops if an action would.
- MAIN's view model gets `<name>Hover` (a boolean) and `<name>Click` (a trigger fired on a click, for the page to
  listen to).
- A live template card's buttons are interactive: their own hover and press, and their own `clicked`.
- v15c: the piece plays once and holds its last frame (no loop, no `a.loop()`). The mouse lights the hover only once
  the entrance is done: MAIN's view model gets `introDone`, on at the timeline's end. `play` replays the entrance.
- Check it with the CLI's pointer: `rive . --advance=90 --pointer=move@x,y --advance=30 --screenshot=in.png`.

## 3. Components: props (set when placing, or on the timeline with `a.set`)
Choices are numbers. Every state below can also be keyed on the timeline; the actions key most of them for you.

| component | props: values (default first) | states |
|---|---|---|
| CoreButton | `label` "Button" · `variant` 0 Primary, 1 Secondary, 2 Text · `size` 1 Regular, 0 Small, 2 Large · `color` Primary: 0 Brand, 1 Dark, 2 Upgrade, 3 Destructive; Secondary: 0 Grey, 1 Light transparent, 2 Upgrade, 3 Dark transparent; Text: 0 Brand, 1 Secondary, 2 Dark, 3 Light · `showLeftIcon`/`leftIcon`, `showRightIcon`/`rightIcon` · `minWidth` 0 (points) | hover, pressed (0.96), selected, focused, disabled, loading (label leaves, then the spinner; width kept) |
| Icon button | `icon` i_plus · `variant` 0 Icon, 1 Box · `size` 1 Large 32, 0 Small 24 · `color` 0 Primary, 1 Grey, 2 Dark grey, 3 Light, 4 Dark · `border` false | hover, pressed (0.9), selected, focused, disabled, loading, hoverAnimated (pulse) |
| CoreInput | `label` / `showLabel` true · `required` false (a red asterisk) · `labelIcon` false (an info icon) · `placeholder` · `value` "" · `message` / `showMessage` false · `theme` 0 White, 1 Grey · `size` 0 Default 35, 1 Compact 25 | focused, error, success, warning (priority error > success > warning > focus), readOnly, disabled. A message opens its room under the field, then fades in |
| Smart_Tag | `label` "Tag" · `size` 1 Regular 26, 0 Small 20 · `radius` 0 6 px, 1 Full · `color` 0 Grey, 1 White, 2 Primary · `prefix`/`prefixIcon` i_site · `removeButton` true · `border` false | hover, removeHover |
| Divider | `variant` 0 With text, 1 No text, 2 Vertical · `label` "EARLIER" | - |
| VibeFloatingBar | `open` true · parts: `edit` (CoreButton), `divider`, `up`, `down`, `duplicate`, `padding`, `trash`, `dismiss` (Icon buttons); `p.bar(style="storyboard")` sets them as the storyboards do | `open` false: fades 0.15 s to 0.98; true: the product's entrance |
| Text Area | `label` / `showLabel` true · `required` · `labelIcon` · `placeholder` · `value` "" · `resize` true (the corner handle) | focused, readOnly, disabled |
| SearchInput | `placeholder` "Search by" · `value` "" | focused (caret, dark edge, the x), disabled |
| CoreDropdown | `label` / `showLabel` true · `value` "" · `placeholder` "Select" · `prefix` / `prefixIcon` i_site | open (dark edge, the chevron turns, 200 ms), error, disabled |
| Status | `label` "Status" · `color` 0 Neutral, 1 Positive, 2 Pending, 3 Dark Grey, 4 Yellow, 5 Negative, 6 Blue, 7 Purple · `border` false · `dropdown` true · `unread` false | hover |
| Promotional Tag | `type` 0 Default ("new" in an orange outline), 1 Premium, 2 AI, 3 New dot · `label` "new" | - |
| Core Toggle | `variant` 0 Toggle 28x18, 1 Switch 48x30 · `on` false | pressed, disabled (a click flips it) |
| Core Checkbox | `state` 0 Empty, 1 On, 2 Partial | pressed, disabled (a click checks / clears it; the check draws on) |
| Core Radio Button | `selected` false | pressed, disabled (a click selects it; `a.set(other, selected=False)` for the one it replaces) |
| Pill_Tabs | `count` 3 (2..6) · `selected` 0 · `label1`..`label6` · `fill` false (the tabs share `w`) · `icons` false / `icon1`..`icon6` | a click on `tabs.tab(i)` selects it (200 ms crossfade) |
| Core Tabs | `count` 3 (2..6) · `selected` 0 · `label1`..`label6` | a click on `tabs.tab(i)` selects it (the line grows from the tab's centre) |
| ListItem | `title` · `secondary` / `showSecondary` true · `prefix` true / `prefixIcon` / `prefixTheme` (as Icon Thumbnail's theme) · `suffix` true / `suffixIcon` i_options · `tag` / `tagLabel` "new" · `border` true · `state` 0 Default, 1 Default_Grey, 2 Selected border, 3 Selected grey, 4 Selected primary, 5 Error, 6 Disabled | hover (rows don't squeeze: the highlight is the reaction) |
| MenuListItem (`p.menu` entries) | `label` · `showIcon` / `icon` · `destructive` false | hover, selected (grey and a check) |
| Icon Thumbnail | `icon` i_site · `theme` 0 Primary, 1 Secondary, 2 Grey, 3 Highlight, 4 Display, 5 Error, 6 Warning · `size` 0 40, 1 36, 2 24, 3 16 · `circle` false | disabled |
| Tooltip | `text` · `hug` false (wraps at 200; true: one line) | shown (fades in, grows from 96 %; out it only fades) |
| Loader | `size` 0 16, 1 24, 2 48, 3 96 | always turns (one turn per 0.8 s) |
| AiPanel (`p.ai_panel`) | `title` "New chat" / `titleAfter` (the name once answered: docked with the action bar, floating 1.1 s after sending) · `copilot` false (true: floating) · `greeting`, `subtitle`, `chip1`..`chip4`, `showMore` · `placeholder` / `placeholderAfter` · `prompt` · `status` "Thinking..." · `reply`, `reply2`, `reply3` (an empty one is left out) · `build` "Build" · `disclaimer`, `link` · `thought` "Thought for 3s" (v08; `showThought` is gone: the swap is always there) · `figmaActions` false (like, dislike, undo too) | `stage` 0 empty, 0.5 the press on send (v14: the button presses, the typed prompt rises 10.3 px in 45 frames on (0.8, 0, 0.2, 1) and fades out between +16 and +26), 1 sent (the bubble appears over 5 frames and rises 20 px in 30; the star turns in, "Thinking..." wipes in; stop), 2..4 each paragraph comes in below the status (2 also swaps it for `thought` in place), 5 done (the action bar under the reply) · `typed` (v14: takes fractions: the letter at the edge fades in over one letter; no caret; the placeholder goes on `focused`, on the first half letter, and stays gone from the press on) · `typewriter` false (v14, `a.reply` turns it on: each paragraph types in by its `reveal1`..`reveal3`, 0 -> 1, instead of rising whole) · `focused` · `hidden` (closes: docked slides right, floating shrinks into its corner; false opens it, the suggestions cascading) · `hover<Control>` (hoverSend, hoverChip1...) · `interactive` (the prototype: a real field) |
| AiProcessIndication | `label` "Thinking..." · `thought` "Thought for 3s" · `spinner` false (a turning arc instead of the AI star) · `chevron` true | `shown` true (false: hidden; true plays the entrance: the star turns in from 60° and 8 px lower 5 frames later, the label wipes in 15 frames later) · `done` (the swap: the star fades, the label wipes out, `thought` wipes in where it was 10 frames later, the chevron 24 frames later; `chevron` false: none) |
| FeedbackMessage (`p.feedback`) | `text` · `variant` 1 Success, 0 Info, 2 Warning, 3 Error (a 16 px icon, 46 high), 4 Neutral (white, no icon, 42 high) | `shown` (`p.feedback` places it false; true: it drops 8 px into place as it fades in, 0.5 s, settle; false: it rises as it fades out, 0.25 s, duda) |
| FlowNode (`p.flow_node`) | `type` 3 Send email (0 Start trigger, 1 Add/Remove label, 2 Update field, 4 If/Else, 5 End, 6 Wait) · `title` · `subtitle` (Start trigger and End: no "..." menu) | `hover` (the edge to #D4D4D8, a slightly larger shadow; not in the storyboard), `selected` (a 1.5 px #3B82F6 edge, frame 07; `a.click` sets it) |
| AiStep (`p.ai_step`) | `label` (the step) | `done` (the swap, v11: the spinner fades out in 3 frames, still turning, then the check fades in over 3) |
| Skeleton (`p.skeleton`) | `circle` false (round: a dot, an avatar) · `shimmer` true | the band crosses every 1.4 s on its own (`shimmer` false: a still block) |

The cursor is the library's Cursor (blue #508AF6, white outline), placed by the actions; `Piece(..., cursor_scale=1.0)`
(a hero: 1.05, the "Get Found" size; inside a camera it grows with the zoom).

## 4. Actions: the choreography
`a = p.actions()` gives one timeline. Times are seconds; `t=None` means "now" (`a.now`). The cursor's actions (click,
type_into, move_to, remove...) and the waits move `now` to when they are done, so a sequence reads top to bottom;
what only keys content (enter, exit, show, hide, text, stream, generate, write_code...) returns its end and leaves
`now` alone (`a.at(a.hide(...))` waits for it). Every action also takes `t=` (an absolute time). Durations also take
token names (`"medium"`, `"read_hold"`).

| action | what happens (the rules hold by construction) |
|---|---|
| `a.at(t)` · `a.wait(s)` · `a.hold(s)` | move `now`; `hold` is a reading hold (a message stays >= 1 s) |
| `a.enter(item, dy=8, dur=0.6, dx=0, scale=None, ease="settle")` | arrives and settles: hidden until then, fades in while rising `dy` px (settle curve); `dx`: from the right (negative: left), `dy=0` for a panel; `scale=0.96`: it also grows from its centre |
| `a.show(items)` · `a.hide(items, dur=0.1)` | fade in where they are (hidden until then) · fade out together; one state at a time: what replaces them comes after the returned end |
| `a.stagger(items, step="list")` | entrances one after another: "tight" 17 ms, "list" 67 ms, "loose" 83 ms |
| `a.exit(item, dy=-6)` | fades (150 ms) while moving 6 px, 333 ms |
| `a.sent(item, t=None, dy=20)` | v13b, the rule for a sent message (always): the user's message (its bubble, or the row holding it) appears over 5 frames (linear) and rises `dy` px in 30 frames (0, 0, 0, 1), both from the frame t (the send). Hidden until then. `p.ai_panel` does the same on its own |
| `a.send(panel, t=None)` · `a.send(typed_text, t, message=bubble)` | v14 (LEARNINGS 5, "Sending"), the press on send with no cursor (the cursor clicked the field and left): the button presses (0.9), the typed prompt rises 10.3 px in 45 frames (0.8, 0, 0.2, 1) and fades out between +16 and +26, and 23 frames after the press the message comes in (`a.sent`: 5 frames, 20 px in 30) with "Thinking...". On an AiPanel the cursor's own press on `panel.part("send")` does the same. A field of your own (`p.copilot_panel`): pass the typed `p.text` and the `message`. v14b: `a.send(field, t, message=bubble)` on a `p.copilot_field(prompt=...)`: the button presses (0.9), the text flies out, the stop comes with the message. Press it `PROMPT_TYPE["send"]` (45) frames after the last letter. Returns when the message comes (a.steps / a.generate_screen / a.think start there) |
| `a.typewrite(item, t=None, cps=120, dur=None, ease="linear", soft=0)` | v14: any `p.text` (a `p.chat_ai`, a prompt in a field of your own, a caption) types in from t with ONE key (a text modifier's reveal goes from nothing to all): each letter whole, never half-drawn, no caret; `cps` letters a second or over `dur` s; `soft=6`: the generated copy's soft front instead. A prompt in a field of your own: `dur=PROMPT_TYPE["dur"] / 60, ease=PROMPT_TYPE["ease"]`, `PROMPT_TYPE["lead"]` frames after the click (`patterns.PROMPT_TYPE`). v14b: on a `p.copilot_field`'s prompt, the placeholder goes and the edge turns active as it starts, the send turns orange on the first letter. Hidden until t. Returns when the last letter is in |
| `a.cursor_in(side=None, t=None, again=False)` | v16: in a scene whose cursor has already shown, it does nothing (one cursor per scene; the build notes it); `again=True` brings another. v14: the cursor shows IN PLACE, ~220 px below its first target, towards the frame's centre (3-frame fade, already moving), and reaches it on one curve (>= 38 frames). `t=s`: it shows at s (`now` moves there). Optional: the first click brings one. v14b: never inside the item it goes to when that item has a hover: it shows where its tip enters it >= ~15 frames later (over another card, beside it), so the hover lights on the way, not on the cursor's first frame. `side="right"` (left, bottom, top): the old cursor, from off-frame, leaving through an edge |
| `a.move_to(item, where=None, hold=0, at=None)` · `a.hover(item, hold=0.6)` | goes to the item and stops on it; `hold=s`: it lingers, creeping on softly (a "thought", never still). The hover lights while the tip is inside. `at=(x, y)`: a point of the board instead |
| `a.pick_color(picker, color, t=None, targets=())` | v15b: the cursor clicks the swatch of `color` (its index or '#rrggbb'). On arrival its edge darkens. On the press it dips (0.9, back in 0.333 s), the ring moves to it, and HEX, the handles, the field that opened the picker and each of `targets` (an item drawn with a fill of its own: the email's button) turn to it in 0.333 s. Returns the press time |
| `a.click(item, where=None, loading=None, at=None, opens=None, result=None, cursor=None)` | v16, one cursor per scene: the scene's first click brings the cursor; once it has left (a long wait, a typing that sends it away), the next clicks of the scene press on their own (the component's squeeze, no cursor: "click X (on its own)" in the log). `cursor=True`: this click brings a cursor again (the motion designer asked for it); `cursor=False`: on its own even with a cursor on screen. The hover lights when the tip enters the item; the press starts 5 frames before the cursor stops (7 on a field): the component's squeeze + the cursor's 0.85 press; an input takes the focus, a toggle / checkbox / radio / tab changes on the press; a dropdown opens on the release (+8 frames), a collapsible folds +5. `opens=item`: a popup, modal or menu the click opens enters on the release (rising 8 px, 0.96 -> 1, 767 ms). `loading=s`: spinner for s seconds from the press. It aims where the item is on the press frame. `at=(x, y)`: a click on that point. v14b, `result=`: what the click changes, on the release too: `{component: {prop: value}}`, `{(item or element name, property): value}` (your own drawing: a swatch's colour, a HEX text) or a function called with the release time (for moves). A `p.hoverable` item lights its hover. Returns the press time |
| `a.release()` | v14: the latest click's release (press + 8 frames): where what the click opens starts (`a.enter(menu, t=a.release())`) |
| `a.type_into(input, search, text area or AiPanel, text, then=None, then_where=None, replace=False, kind=None, arc=None, gap=1.45)` | v14, by the kind of text: `kind="field"` (default; a name, an email): ~14 letters/s from 0.15 s after the click, with a human jitter; with `then` the cursor arcs aside (one glide, no key at the turn; v16b: his arc, 16 % of the way at its middle) and clicks `then` as the last letter lands, never sooner than `gap` s after the click (1.45; his First -> Last name: 1.07) (a short name is not spread over that window); no `then`: the cursor vanishes while it types. `kind="sentence"`: ~38 letters/s. `kind="prompt"` (the AiPanel's default; a text area as a prompt): the cursor clicks the field and vanishes, the text types from 9 frames later on one curve (0.1804, 0.0442, 0.2292, 0.676), ~53 letters/s; on the AiPanel `then=panel.part("send")` presses send on its own 12 frames after the last letter. `cps=`: letters/s instead. `arc=`: the typing arc's side ("up" when chips or controls sit under the text; default: the side that passes over fewer controls). `replace=True`: the field's text is selected and the new one types over it |
| `a.remove(tag)` | clicks the tag's x (or uses the click `type_into(..., then=tag, then_where="remove")` just made): the tag fades and shrinks 0.1 s, then the row closes the gap smoothly |
| `a.drop_file(file, into=None, at=None, t=None, zone=None, result=(), side="right", dist=None)` | v16, curated example 1 (his recipe, below): a file from outside the frame thrown into an input or drop area. `file`: what is carried (a card, a thumbnail; a copy is carried and the item itself stays hidden); `into`: where it lands (its centre; `at=(x, y)`: a point); `zone`: the input's drop highlight (drawn by the piece, hidden at rest), in over 9 frames from the start, out as the hand opens; `result`: what the drop leaves in the input (a chip, a thumbnail), fading in from +56 and scaling 125 % -> 100 %. The hand shows already moving and holding the file, rides 141 px (at 1340 px wide; `dist=` other px) from below-`side` of the drop in 54 frames, opens 5 frames before it stops, and goes with the file. A cursor on screen leaves first (the hand is the scene's cursor). Returns the open frame |
| `a.drag(item, to=None, at=None, t=None, plus=None, panel=None, over=None, badge=None)` | v12, any pick and drop (the approved rule) of something ON SCREEN (a file from outside the frame: `a.drop_file`): v16, the cursor on screen goes to the item and turns into the hand there (no second cursor); without one, a cursor of its own comes in already moving; with `plus` (and `panel`) it clicks "+" and the panel slides in from behind the left bar (42 frames); it slows into `item` and takes it: the arrow turns into the closed hand (a hard swap), 3 frames still, and a copy that follows the cursor lifts up-left (6.5, 7 px) with a soft shadow, its place staying empty; it drags out horizontally, arcs and lands vertically (88 frames); over `over` a blue "+" badge pops on it; on the drop it shrinks to 90 % and fades, the hand vanishing there. `to`: an item (lands on its centre); `at`: a point. Returns the drop |
| `a.drop_widget(card, slot, site=None, panel=None, plus=None, intro=[...], close_up=False, slide=None, scroll=None, fit=True)` | v12, the approved recipe: `card` (a widget in the panel) dragged as `a.drag` into a `p.drop_slot`. When the card gets over the site, the panel closes and `site` (the site's content, inside a clipped view) scrolls ~124 px in 58 frames (`slide`: it also moves left the panel's width, when it sits beside the panel; default when there's no `plus`); the section below goes down 33 px; 24 frames before the drop the blue line shows where it goes. On the drop the section opens from inside the line (to its height and 54 px each side, 1 s on (0.8, 0, 0.2, 1)), the site scrolling so it ends in view (`fit=False`: no extra scroll). `intro`: the section's items in reading order (a tuple: parts 4 frames apart; 12 frames between items), each rising 40 px with a 5-frame fade from 27 frames after the drop; an image fades in and settles slowly. `close_up=True`: the rare cut to the close-up (2.1x) at the drag's peak speed and back (107 % -> 100 %). `now` moves to the end of the intro |
| `a.steps(item, t=None, each=0.8, finish=True, until=None)` | a `p.chat_steps` (or `p.ai_steps`). v13: `t` is when the message is sent: "✦ Thinking..." comes in then (unless `a.think` brought it), the summary's room opens 18 frames later and the summary enters at 33 (rising 4 px), the first step at 54; `each`: one length or a list (one per step); `until=s`: the steps follow the generation, uneven lengths (the last the longest) so the last check lands at s (`a.generate_screen`'s end). Each step's room opens below and the line comes in with its spinner turning (rising 4 px); `each` s later the spinner fades out (3 frames) and the check fades in (3 frames), and the next line comes in as it lands (v11). `finish=False`: the last keeps loading (frame 05). Returns when the last is done. Then `a.reply(reply, t)` (~25 frames after the last check): the status swaps to "Thought for Xs", the summary and the steps fade out (0.1 s), their rooms close as `done`'s opens in the summary's place, and it enters |
| `a.feedback(item, t=None, hold=3.0)` | a `p.feedback` (v09): at t it drops 8 px into place as it fades in (0.5 s, settle), stays `hold` s and leaves on its own, rising as it fades (0.25 s, duda). Returns when it is gone. After a save with a spinner: `t` = the click's press + its `loading` |
| `a.message(input, text, kind=None)` | the message under the field; kind None (info), "error", "success", "warning". A shown message leaves first, then the new one arrives. Returns when it shows |
| `a.set(item, **props)` | any prop on the timeline: `a.set(bar, open=False)`, `a.set(btn, t=t_press, selected=True)`, `a.set(thinking, done=True)` (it swaps to its `thought`) |
| `a.key(item, prop, value, dur=0, ease="duda")` | a key of your own on a placed item or one of your elements: `"opacity"`, `"x"`, `"y"`, `"scaleX"`, `"rotation"`, `"width"`...; `dur` > 0 moves to it. A component's own states go through `set` |
| `a.click(panel.part("send"))` · `a.send(panel)` · `a.think(panel)` · `a.reply(panel, then=0.083, thought=None, cps=120, max_s=1.0, typewriter=True)` | an AiPanel: the click (or `a.send`) sends as above; `think` sends without the press (the prompt goes at once) · the answer starts at t: 9 frames before, the status swaps in place for "Thought for Xs"; v14: each paragraph's room opens 0.25 s before its first letter and the paragraph types (120 letters a second; the whole answer at most `max_s`, 1 s: a long one types faster); `then` s after the last letter, the action bar. `typewriter=False`: v13's whole paragraphs, `step` s apart. Typical: `a.type_into(panel, PROMPT, then=panel.part("send"))` (one cubic key 9 frames after the click; the send presses on its own 45 frames after the last letter, and `now` moves to the message), `a.wait(2.0)`, `a.reply(panel)` |
| `a.think(reply, t)` · `a.reply(reply, t, then=0.083, cps=120, max_s=1.0, typewriter=True, stream=False, thought=None)` | a `p.chat_reply`: `think` as before · `reply` (v14, LEARNINGS 6): a plain typewriter, each letter whole, no front, no feather, no colour pass, 120 letters a second and never more than 1 s in all; each paragraph's room opens 0.25 s before it; the icons `then` s after the last letter. On a `p.chat_steps` (after `a.steps`): the swap and the steps' fold at t, the done paragraph typed 21 frames later (ask-your-agent's approved timing); a `p.copilot_field` under the chat swaps its stop for the grey send with the status (v14b) |
| `a.text(item, "New title", fade=False)` | a `p.text` changes (a chat renamed); `fade=True`: out 0.1 s, change, back in |
| `a.stream(item, text=None, cps=None, words=False)` | the AI's reply (a `p.chat_ai` / `p.text`, empty until then), v16b letter by letter: each letter whole at the answer's pace (120 letters/s, the whole never over 1 s). `words=True`: v13's word by word (80 characters/s), only when the review asks for it |
| `a.count(item, 128, dur=2.0, fmt="{:,}", color="#AE68FA", start=None)` | a number counts up from close to its value (v11, the approved rule: `to` minus 10-35, random but the same in every build, never below 0; a long count, 0 to 3,023, looks linear; `start=0` counts from zero) (v11: 2 s on (0, 0, 0, 1), fast then ending slowly; 1.5-3 s fit), coming in #AE68FA and turning to its own colour as it sharpens from a Feather of 4 (40 frames); `color=None` keeps its colour; `a.count(item, 2.6, fmt="{:.1f}%")` counts in tenths |
| `a.load(items, t=None, step=None, dur=0.6, draw=True, count=True, glow=True)` | v06: skeletons give way to the content (a page, a card, a chart or a list), one item after another, `step` s apart (the product's 0.27; a Highlights page keeps its own timing unless `step` is given, v07d, Mateus's: the charts first, the KPI cards 21 frames later all at once, each next card's tint 4-5 frames later): the skeleton fades out (0.1 s), the content fades in; KPI numbers count up, from close to their value as `a.count` (v07: Mateus's curve, fast then a long soft landing, 1 s and each next card 10 frames longer) and their chip comes 0.55 s in; charts draw. `glow` (v07, on by default since v07b; `glow=False`: plain): the numbers count in blurred 3 px and tinted orange, pink, purple, then sharp in their colour. Returns when the last is in |
| `a.draw(chart, t=None, dur=None)` | a chart draws itself: a donut clockwise from the top (1.1 s, "duda": fastest half-way), then its total; a line chart (v07; in `a.load` its fastest moment, the start, falls on the donut's, v07c, or it starts once its labels are in): the line is traced from the left as it sharpens (0.67 s, linear) while the area's colour comes down from the top under a lavender layer (Mateus's) |
| `a.generate(item, kind=None, rows=None, pops=None, squares=None, clip=None, colors=None, feather=None, content=True, letters=True, ink=None, saturate=False)` | the Generation effect (hero_1): a square with the 7-stop gradient over `item` (5 px of room, the item's radius + 5), the gradient sweeps through on (0.588, 0, 0.377, 1), the item shows under it (frame 36 small, 56 big; `kind` by height). v14, lighter: a card's square from 108 % with Feather 11 -> 2, a panel's from 102 % with Feather 10 -> 1.5, fading in over 16 frames; each first feather +-10 % apart; all by the size shown (`p.shown_at`); `feather=(start, end)`: your own, as drawn. v14, its content on its own (`content=False`: none; a list: those only), in reading order from ~0.4 s after it shows (at once on a 432 card), ~6 frames apart: texts letter by letter (a soft front 6 letters wide, ~45 letters a second, 0.4-0.9 s a text; a heading's next line when the one above ends), the whole text orange #F9A84A -> pink #F4BBD2 -> its own, Feather 4 -> 0 in 40 (`letters=False`: whole, over 8 frames, Feather 6 -> 0 in 54); icons over 20 frames in the same colours; photos settle 112 % -> 100 % over 1.5 s (0.16, 1, 0.3, 1) from 6 frames before they show; numbers keep the #AE68FA pop (then `a.count`). `ink=(c1, c2)`: the texts' two colours (the design's, from `gradient=`). `rows` / `pops`: v11's, as before. Returns when all has landed v16: `saturate=True`: its photos (a `p.image` too) come in saturated and lose it (see `p.photo`); a `p.photo`'s parts come in after it on their own. v16b (his Marketing Automation hero, ma-novo v18.20B): a 0.75 px #EDBE96 line round the block over the squares, in 4 frames before it shows (to 90 % in 6), out from 8 after (over 10); an icon on a tile (a filled box <= 56 px holding only it): icon and tile orange -> pink (10 f) -> their own (30 f; the tile through the hues between), sharpening from a Feather 4 over 30 f; `letters=False` (a block of interface, a node on a map): labels whole, see-through orange -> orange (8 f) -> pink (10) -> own (20, on (0.25, 0.1, 0.25, 1)), Feather 6 -> 0 over 38, 6 frames after it shows and 8 apart; an icon off a tile (a "...") 30 frames after it shows. `a.generate(link)` on a `p.flow_link`: the line draws down in 18 f on (0.2, 0.6, 0.35, 1), a pink and orange tip turning grey, the "+" lighting up as the tip passes it (his map: each line 21 frames into the square of the card under it). A `p.flow_node` is a component: the generation can't reach inside it; build the cards of their parts for this detail (Prototypes cell 22) |
| `a.wash(area=None, t=None, colors=None, opacity=0.5, feather=None)` | the 7-stop gradient sweeps the whole `area` at 50 %, drawn 110 % and cut to the area, Feather 20 -> 3 (v14: by the size shown, 10 -> 1.5 on a 432 card; `feather=(start, end)` your own), in 217 frames; its tail fades out over the last 18 (it could stay in a corner). On a cream background `opacity=0.75` |
| `a.loose(items, t=None, stagger=None, letters=True, ink=None, color=None, saturate=False)` | v14: elements with no block under them (a logo, a name, a heading under a photo) come in as a block's content: texts letter by letter, icons over 20 frames, photos settling, all orange -> pink -> own with the feather, in reading order 3 frames apart (`stagger`), a heading's next line when the one above ends; a box or drawing of your own fades in over 20 frames with its paints in the same passes. `color=`: v11's single tint instead (the old #8D5DF5 look) v16: `saturate=True` as in `a.generate`. |
| `a.generate_screen(blocks, area=None, t=None, loose=(), details=(), gradient=None, colors=None, gap=None, clip=None, letters=True, order=True, split=True, saturate=False)` | v13's recipe (LEARNINGS 19.2), v14 with no patches: `t` = when the message is sent. The wash from 6 frames (to 223, its tail fading); `blocks` in reading order (top to bottom, left to right in a row; `order=False`: as listed), the first at 108 frames (96 on a 432 card), the next ones ~1 s apart (~0.5 s on a small card; +-15 %, uneven), the biggest as a panel (102 %, a 131-frame pass), the others as cards (108 %, 84); each block's texts, icons and photos come in as it shows (see `a.generate`); v14b: a block given plain whose centre falls inside a bigger block (a badge on the hero photo) starts with it, as one of its `rows` (rising 4 px as it shows), not with a ~1 s slot of its own: `[hero, badge, crystal]` times as `[(hero, {"rows": [badge]}), crystal]`; given with keywords, `(badge, {...})`, it keeps its own slot; `loose` at their place in the same order (under a block 4 frames after it shows it, never later than 3 frames before the next block starts; above every block 3 frames after the first starts); `details` (old) now go with the block they sit over, else with the loose ones. `gradient=(warm, cool)`: the design's own gradient: the wash (75 %), the blocks and the texts' two colours take its tones (`p.palette`); none: the classic gradient (no purple). `letters=False`: every text whole (an interface's short labels). Returns the generation's end: `a.steps(reply, t, until=end)`, then `a.reply(reply, t=end + 25 / 60)` v16, `split=True` (default), by structure: only what has a box of its own is born from a square: a photo, a library component, a box whose fill differs from what is behind it (its nearest filled box, a photo under it, or the page: more than 6/255 in any channel), a border, a shadow, a gradient, or a photo under 90 % of it. A block given with no box of its own (a nav whose brand and menu are texts on the page; a column with a heading, a paragraph and cards) is split: its boxed children keep their squares, in the order with the other blocks; its texts, icons and drawings come in loose (letter by letter, one after another in reading order, as `loose`); its own lines (a hairline under a nav, a divider) fade in with the first of them. A Figma part (`p.figma_screen(parts=)`) is classified by its shapes as big as it (its background): a part with no box of its own comes in loose, its native texts letter by letter and its other shapes fading in with them (a filled button inside it too: no square of its own). Each split is in the build's timeline (`generate_screen: MAIN.head split (...): 1 square(s) [announce], 6 loose [...]`). `(item, {"square": True})` keeps that block whole; so does any block given with `squares`, `rows`, `pops` or `content`; `split=False`: every block whole (v15e). `saturate=True`: the photos come in saturated (a `p.photo` does it on its own). |
| `p.palette(warm, cool)` | v13: the generation's colours from the design's gradient (its two ends), slightly stronger than in the design, with a middle tone: `{"wash": 5, "blocks": [5, 5], "text": c, "details": [c, c]}`; the welcome email's #FFFBD6 -> #DCEBFF gives the reference's tones (LEARNINGS 7, "The design's colours") |
| `a.generating(status)` · `a.done(status)` | a `p.gen_status` shimmers (every 1.6 s) until `done`: "Generating..." fades, "Done" fades in, the box closes to its width (the star slides toward the side it is placed against) |
| `a.write_code(editor, speeds=((1, 240), (12, 100)), pauses={18: 0.1})` | the AI writes a `p.code_editor` (or `panel.editor`), each line's number as it starts. v16b (his Code-reference): each line revealed letter by letter at the stream's pace, a purple #B36DFF tip over magenta #F100FF, the syntax colours coming in 0.2 s behind with a ramp that waits 0.6 s, then the purple and magenta go; no caret. (`p.code_editor(reveal=False)`: v15's chunks and caret.) Returns when the colours are all in; `editor.line_done[n]` is when line n is written |
| `a.add_file(tree, "TopBar.tsx")` | a `+file` of a `p.file_tree` arrives: the rows below make room, it slides in from the left |
| `a.beats([...])` · `a.c` | your own keys on the same timeline (section 8) |
| `a.open(coll)` · `a.close(coll)` | unfolds / folds a `p.collapsible` without the cursor (medium, duda) |
| `a.cursor_out(side=None, t=None, vanish=None)` | v14: the cursor fades out where it rests (3 frames), 8 frames after its last press; `t=s`: it creeps on until s, then fades; `vanish=s`: its fade starts at s exactly (a cut: gone before the exit, even while it lands). A wait of more than ~3 s between two targets makes it vanish and a new cursor show for the next one on its own. The old cursor (`cursor_in(side)`) leaves the frame accelerating (`side`: default the nearest) |
| `a.cut(src, dst, kind="slide", t=None, cursor="auto", cascade=None, at=None, dir=None, out_px=None, in_px=None, wait=None, edges=None, color=None)` | v14, LEARNINGS 8: screen `src` gives way to `dst` (both in one `p.stack` or `p.free`), answering the latest click (`t`: the press; default the latest click since the last cut). `kind`: `"slide"` a page that changes sideways (7 f after the press, out 215 px in 23 f accelerating, in 60 px settling in 54 f; px scale with the piece's width), `"zoom"` a click that goes into the thing clicked (14 f after, src to 120 % around the click in 23 f, white full from the cut -1 to +3 f, dst from 95 % settling in 54 f; `at=(x, y)`: another pivot; v15e, `at="center"`: a camera passage between scenes, as in a social video: no white and no click to answer, from `t` src zooms 7 % around the board's centre in 20 f (1, 0, 1, 1), reaching it on the frame before the cut, a dry cut at that peak, dst lands from 105 % in 35 f (0, 0, 0, 1); `dir="out"` (default) or `"in"` (src to 107 %, dst from 95 %); the axis is asserted at the centre, and a zoom-out asserts room around src at 93 % (none: no transition, or `dir="in"`, or a wider backdrop: `scripts/backdrop_xl.py`). The two zooms live together: into the thing clicked, to the click with the white; between scenes, on the centre), `"white"` in place, a panel that stays (0.15 s out, 0.1 s white, 0.25 s in), `"tabs"` a hero's tabs (out 26 px / 20 f, in 34 px / 26 f, a veil in each screen's body colour, against the pill). `edges` (on but for white): what shows past the frame continues the screen (vector bands copied from a render, 5 px inside). `cascade` (on but for tabs): what the click opened comes in row by row (8 px over 0.6 s, 67 ms apart). v14b: it is the content box under the click (the zoom's pivot) with the most rows; items side by side are one row, and what sits over it (a selection, its label, its toolbar) comes with its row. The frame around it (bars, panels, the box's own background and hairlines) comes in whole. When nothing under the click has 2+ rows, it is the box with the most items. v15a: a grid built as columns (columns side by side, widths within 25 %, each with 2+ rows) cascades as one, its rows running across the columns (both first cards together), never one column row by row and the other whole. The build notes say which. A list: those items, in that order; `False`: none. v14b: each screen's display is on only around its time (dst from 2 f before the press, src off 2 f after the cut, edge strips only while they show); a display the piece keyed itself is kept and only switched on where the cut needs it; dst may be display none at the click, and may hold size-0 boxes. `cursor`: `"auto"` walks across when its next move comes within ~2 s of the cut, else vanishes in place (3 f, 8 f after the press) and the next cursor shows after the cut; `"walk"` / `"vanish"` force it; the build log says which and why. Returns the cut's time (`now` moves there). Example: `a.click(open_btn)`, `a.cut(home, settings, "slide")`, `a.click(save)` |
| `a.camera_close(item=None, t=None, scale=None, ui=None, where=None, lead=None, jump=False)` | v14, LEARNINGS 9 (only when the motion designer or the design lead asks): a hard cut to a 2.5x close shot 31 f before the latest click, while the cursor is on its way (it shows inside the close shot); the camera follows the cursor's own path (fitted in at most 12 cubic keys) until it arrives, held inside `ui` (an item or (x0, y0, x1, y1): it never shows past it); after the arrival, a slow zoom 2.5 -> 2.4 (0.65, 0, 0.8, 0.7). The cursor grows with the camera. Editable in Rive: `CAMERA` > Transform constraint `CUT` (its strength keys are the cut and the zoom out) aimed at the rig `CAM_CLOSE` > `.zoom` > `.track`. `jump=True`: a jump cut into it. Call it right after the click it frames. Example: `a.click(field)`, `a.camera_close(ui=panel)` |
| `a.camera_open(t=None, lead=None, frames=None, ease=None)` | v14: back to the whole frame: the strong 80/80 zoom out (0.8, 0.0451, 0.2, 1) over 102 f from 25 f before the press at `t` (default the latest click: the send); the slow zoom runs 40 f into it, so the two read as one. Returns its end (`now` stays). Example: `t = a.type_into(field, "...", then=send)`, `a.camera_open(t=t)` |
| `a.jump_cut(t=None, out_px=None, out_frames=None, in_px=None, in_frames=None, dir="left", entry="continue", ease=None, edges=True)` | v14, LEARNINGS 8: a cut that isn't "totally hard": the whole picture slides 23.4 px in 27 f (1, 0, 1, 0.9554), and the next comes in 30 px on with it, settling in 34 f (`entry="opposite"`: from the other side). No `t`: the loop's seam; call it last, instead of `a.loop()` (the cursor leaves first; the end slides, frame 0 comes in). `t=s`: a cut inside the piece. `ease="80-80"`: the slide is the first half of an 84 f 80/80, cut on its peak. Px are on screen (divided by the camera's scale in a close shot). `edges`: what the slide uncovers continues the picture. Example: `a.wait(2.4)`, `a.jump_cut(ease="80-80")`, `p.build()` |
| `a.scroll(box, dy, t=None, dur=None, ease=None, cursor=False, read=None)` | v14, LEARNINGS 10: `box` (the content inside a clipping box) scrolls `dy` px (positive: the page goes up) in one move on (0.857, 0, 0.242, 1), never coming back, ~0.9 s + 1.5 ms per px (784 px in ~2.1 s), longer if it would pass the text's speed cap. It waits until its screen has been readable ~1 s (`read`). `cursor=True`: a cursor shows 6 f before it ends. Returns the end (`now` moves there). Example: `a.scroll(p.items["detailRows"], 300, cursor=True)`, `a.click(edit)` |
| `a.loop(exit=card, rest=3.0, hold=None)` | clean seam: `exit` (an item that `enter`ed at the start) leaves, everything resets while hidden, and the loop rests `rest` s still in all, both sides of the seam together (v14; the end part >= 8 frames); `hold=s`: exactly s at the end instead. Call last |
| `p.build(tabs=False, duration=None, slim=True, carousel=None, remap=None)` | writes `scene.rml`: "State Machine 1" (autoplay) with view model trigger `play` that restarts the timeline; the timeline loops. `tabs=True` (hero tab): plays once, fires `tabChange` at its end, `play` restarts. `duration=s`: exactly s seconds (a hero tab: `tabChange` right at s); without it, 0.5 s after the last action. Anything still moving after s fails the build. `carousel=12` (v14): a tab of a carousel that switches every 12 s: exactly 12 s, played once, no `a.loop()`; f0 must show the first screen whole (no entrance at the start, no white); v14b: a NOTE when the last action ends after ~5.5 s (an email carousel's story ends by then and the rest stays still; "~3 s still" is a hero's or a loop's) or when a docked Copilot's message sits still at f0. v13, `slim` (on by default): only what the piece uses goes in (the components it places, the fonts cut to its characters in `slim/`, the images as WebP: photos lossy 90, sharp ones lossless; see Images); `slim=False`: the whole library. v14: then `checks.py` (see Checks on every build) v15c, `remap={...}`: the same frames, built for hand edits in the Rive editor: MAIN plays the scenes in a Solo, each scene and each element you name on a two-key time remap (section 8, "Built for hand edits") |

- `where`: `"center"` (default; an input's default is `"field"`), `"remove"` (a tag's x), or `(dx, dy)` from the centre.
- **A click's result** is keyed for you: on the press, inputs and searches take the focus, a toggle flips, a
  checkbox checks or clears, a radio selects, `tabs.tab(i)` selects its tab; a dropdown opens or closes on the
  release (+8 frames), a collapsible's header folds or unfolds it 5 frames after the press. What the click opens
  (a popup, a modal, a menu) starts on the release: `opens=` or `a.release()`. Anything else (a menu item that
  changes a value, a status that turns "done") is `a.click(..., result=)` (v14b) or an `a.set` at `a.release()` (or `now`, 2 frames after the cursor
  stops: between +7 and +9 frames, the research's +3 to +8 for a result).
- **Positions are measured**: the build lays the scene out with the CLI at the moment of each action (after a removed
  tag, a grown card...) and aims there. Never compute coordinates. `p.point(item, where, t)` / `p.bounds(item, t)`
  give them if you need them (artboard points).
- **Drivers**: each state an action keys is a custom property `drv.<slot>.<prop>` (group "Drivers", under the
  artboard) bound into the component's view model and keyed on the one "Timeline". In the Rive editor they are ordinary keys to adjust.
- On the web (`@rive-app/webgl2@2.45.0`, `autoBind: true`, `stateMachines: "State Machine 1"`): the artboard's view
  model has `play`, `tabChange`, `cursor` and one property per slot (`email/value`, `go/loading`, `bar/trash/hover`).

### Curated examples (v16)
An action copied from an animation the motion designer made or approved, its numbers his (not deduced from a rule).
Use it as it is: the numbers are not to be tuned per piece. A pick for a moment that has one wins over a rule.

| # | action | source (read only) | his numbers |
|---|---|---|---|
| 1 | `a.drop_file` (LEARNINGS 19.3) | his `header_(example).rev`, "DROPPING THE IMAGE", as the Migration Page v05 copied it (v05.2 drop zone, v05.4 hand size: his requests) | the hand shows holding the file by its bottom edge (centre 0.203 x the hand's height above it; the open hand 1.25 x the arrow), fades in over 4 f; rides 141 px (130.2, 54.8 from the drop; the start's handle 48.3 px across) in 54 f on (0.42, 0, 0.1235, 1): peak 8.4 px/f at ~1/4 of the time, 98 % at f44; grows 90 -> 100 % (x (0.4587, 0, 0.0608, 1) in 53 f, y (0.42, 0, 0.2339, 1) in 54 f); opens at +48/49; the file shrinks to 82 % over +47..+58 on (1, 0, 0.97, 0.964); hand and file fade +54..+58; zone in 0..+9, out +49..+61; result in +56..+82 and 125 -> 100 % over +57..+127 on (0, 0.74, 0.199, 1) |
| 2 | `a.type_into(then=, gap=)` (Prototypes 05) | his Create Client, manage-hero2 v14 (the Manage tab of duda.co/vibe's hero), his own cursor | First name and Last name side by side, Email address under them, Save & Continue; presses 177, 241, 328, 415 (1.07 s, 1.45, 1.45 press to press), the text ~14 letters/s from 0.15 s after each click; each leg ONE curve on an arc 16 % of the way at its middle, below (53.6 / 335, 55 / 343, 78.7 / 492 px) |
| 3 | `a.click(c.header)` on a `p.collapsible` (Prototypes 09) | his "Stats report" row, manage-hero2 v14 (the same hero) | on the press, the room opens on duda_strong over 0.5 s and what is under it goes down with it; the content fades in 0.2 s later; the cursor goes straight on |
| 4 | `a.generate(card, letters=False)` and `a.generate(link)` (Prototypes 22) | ma-novo v18.20B, the live hero of duda.co/marketing-automation | the blocks 38 frames apart; each block's square as the library's; the edge line, the tile and icon colours, the labels and the "..." as in `a.generate` above; each line 21 frames into the square of the card under it |
| 5 | `a.write_code` (Prototypes 31) | his Code-reference.rev, as hero3-code v11 copied it | the purple tip, the magenta 0.1 s behind, the syntax colours 0.2 s behind with a ramp that waits 0.6 s, the purple and magenta gone when the colours are in; no caret |

**The ready-made animations he approved (2026-11-26).** The motion designer reviewed cells 01-42 of the Prototypes
grid (`prototypes.py`) on the ready-animations .rev and approved 30 of them, the deduced ones too: 01-04, 06, 08,
12-18, 20, 21, 25-30, 32-36, 38, 39, 41 and 42. Each is a curated example of its action, to copy as it is (origin:
"approved by the motion designer in the ready-animations .rev"). Waiting for his look at v16b: 05 and 09 (rejected,
now his Create Client and his Stats report row, rows 2 and 3 above), 19, 22 and 31 (adjusted on his answers), 07,
10, 11, 37 and 40 (adjusted: no creep after a press) and 23 and 24 (adjusted: the blocks' edge line). Cell 43 is
row 1, his own animation.

When to use which: a file, an image or a screenshot that comes from outside the frame already held, into an input or
a drop area: `a.drop_file`. Something that is on screen (a widget in the panel, a card, a row) picked up and carried:
`a.drag` / `a.drop_widget` (LEARNINGS 19.1: the cursor goes to it, takes it, lifts it).

### The music: beats and cuts (v15e)
A piece with a soundtrack (a social video) puts its cuts on the beat. `Music` (in the bundle: `from music import
Music`) knows where the track's beats fall in the video; `save` writes `music.json`, which `render_mp4` mixes in.
```python
from music import Music
m = Music("music/track.wav", bpm=120, first=0.125, delay=0.2)   # beats at 0.125 + 0.5 k s in the track; the track
                                                                  # starts 0.2 s into the video (negative: into it)
t = a.cut(s1, s2, "zoom", at="center", t=m.snap(5.0) - 21 / 60)   # the centred zoom cuts 21 f after its start
m.on_beat(t)               # AssertionError with the nearest beats' frames when it is off (half a frame of slack)
m.hit(16.625, t)           # the track's 16.625 s plays on the cut: asserted, and checked in the MP4's audio
m.save(HERE)               # music.json: delay, stretch, fades (fade_out=1.5 by default), hits
```
- `m.snap(t, every=1)`: the beat nearest t as its frame's time (`every=4` bars, from a downbeat `first`);
  `m.frames(lo, hi)`: the beats' frames between two frames (where a cut can go).
- `m.fit(track_t, t)`: the last small gap, the track slower or faster so that hit lands on t, at most 2 % (asserted);
  split a bigger one: the scene shorter, the music the rest (LEARNINGS 21).

### A social video from a hero (v15e)
`social.py` cuts a social video (1:1 1080 x 1080, 4:5 1080 x 1350, one artboard each, the cuts on the same frames)
from a hero you built: the hero's MAIN plays nested by time remap, under a camera, between the designers' opening and
end cards. The video reads the hero's scene and never edits it; `out` is another folder.
```python
from social import Social, Zoom
v = Social("pieces/<hero>", "pieces/<hero>-social", nest={"4x5": "MAIN 4x5"})   # the hero's folder, the video's
hero_in = v.opening("Grow your clients with\nnative Marketing\nAutomation", hero_in=170)   # logo, then word by word
v.play((950, 984), (0, 828))                       # MAIN stretches (m0, m1), in order, from hero_in
m = lambda M: v.frame_of(M, 1)                     # a MAIN frame of the 2nd stretch -> a video frame
v.shot(0, (500, 400, 320))                         # framing = (cx, cy, width) in MAIN px, or {format: framing}
v.move(m(110), m(212), (347.5, 319, 604))          # scale and offset blended: a zoom about one fixed point
cut = v.slide(m(429), (1006, 319, 604))            # cuts.KINDS["slide"]; returns the cut frame
v.end_card("duda.co/marketing-automation", at=m(800), room=(673, -168, 1356, 776))   # centred zoom cut + end card
v.build()                                          # scene.rml, social/ (backgrounds, cut fonts), build/social.json
```
| call | what it does |
|---|---|
| `Social(hero, out, formats=("1x1", "4x5"), nest="MAIN", patch=None)` | `hero`: a built hero's folder (or its .rml) whose artboard has a "Timeline"; `formats` from `social.FORMATS` or your own dict (its cards are the 1:1's scaled: check them); `nest` per format; `patch(text)` edits the hero's scene for this video only |
| `v.opening(headline, hero_in, rate=1.01, dy=None)` | the opening card: the logo (its letters a white second shape), the Cal Sans headline word by word in a 974 px box (`\n` between lines; a line too wide raises), a 1 %/s zoom-out to its last frame; the hero comes in at `hero_in` (1.04 -> 1, 50 f). `dy`: Rive draws Cal Sans lower than Figma, default `text_dy(size, line height)`, which says whether it was measured, interpolated or EXTRAPOLATED: measure it against the Figma PNG |
| `v.play(*stretches)`, `v.frame_of(M, stretch)`, `v.main_at(f)`, `v.duration()` | the hero's MAIN frames to show, `(m0, m1)` with m1 left out, in order |
| `v.shot(f, framing, zoom=None, world=None)` | the camera on a framing from frame f. A product scene holds still: a constant zoom only with an explicit `Zoom(f0, f1, factor, ease, rate, pivot)` |
| `v.move(f0, f1, framing, ease=HERO_MOVE)` | a camera move: scale and offset blended (`k` and `-k c`), never by width; default curve the hero's zoom-out (0.8, 0.0451, 0.2, 1) |
| `v.slide(f, framing, direction="left", out_px=None, in_px=None)` | the match cut by position (23 f out, cut, 54 f in); keyed as one cubic pair, as a hand-made one is |
| `v.zoom_cut(f, framing, direction="out", room=None)`, `v.end_card(url, at, frames=162, room=None)` | the zoom cut about the frame's centre, with `a.cut(..., "zoom", at="center")`'s numbers (`cuts.ZOOM_CENTER`: 7 % in 20 f, a dry cut at the peak, 105 -> 100 % in 35 f); a pivot off the centre raises, and so does a frame with no room around it ("no room for a centred zoom": give `room=` from a wider backdrop, or drop the transition). `end_card` ends on the logo and the URL (Duda Sans 350), zooming out 1 %/s |
| `v.overlay(artboard, at, show, hide=None, offset=0)`, `v.clip(f, rects)`, `v.hide_main(f)` | another hero artboard over MAIN inside the camera (an XL copy, so the camera can pull back past an edge); MAIN's clip rects (the same count in every call); MAIN off |
| `v.build(slim=True)` | `scene.rml` (the hero plus "SOCIAL 1x1" / "SOCIAL 4x5", each with "Timeline" and "State Machine 1"), `social/` (the backgrounds, the fonts cut), `build/social.json` (every cut's frame and second, for the music), `rive.yaml` if missing; notes the cuts, the entry/exit speed ratio and the cards' speeds |
Render each format with `render_mp4.py <out> <mp4> --artboard "SOCIAL 1x1" --scale 1 --crf 16` (social: 1080 wide, CRF
16), the music through `music.json` (section 4, "The music"). The scripts behind it:
- `scripts/social_bg.py W H out.webp [--seed 7]`: the posts' background at any size (the CSS gradient's angle from the
  aspect: 1:1 167.48 deg, 4:5 164.48 deg; a rotated blurred rectangle; 2.4/255 grain; lossless WebP). Never crop one
  format from another (the angle changes).
- `scripts/backdrop_xl.py src dst.webp L T R B [--blur 14] [--ramp 24]`: a photo extended by its own mirror, blurred
  only where it is new, joined by a 24 px ramp, lossless; exit 1 unless the original region is untouched (max diff 0).
  The room a centred zoom-out needs.

## 5. Example piece
A sign-up card (`examples/signup/build.py`; it builds, verifies and passes the lints as is):
```python
"""Sign-up: a visitor fills a short form, drops an interest, accepts the terms and creates the account (library v14
example)."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "lib", "biblioteca-v16b"))
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
a.cursor_in()                                    # the cursor shows in place, below the first field
a.type_into(name, "Jane Cooper", then=email)     # click (focus), type, arc aside, glide to the next field
a.type_into(email, "jane@acme.com", then=tags[2], then_where="remove")   # ...then to the x of "Apps"
a.remove(tags[2])                                # "Apps" leaves, then the row closes up
a.click(agree)                                   # the box checks on the press frame
a.click(go, loading=1.2)                         # hover (the tip entering), press, spinner for 1.2 s
a.cursor_out()                                   # its job is done: it fades out where it rests
a.message(email, "Account created. Check your inbox", kind="success")
a.hold(1.6)                                      # reading time
a.loop(exit=card)                                # the card leaves, everything resets while hidden, ~3 s rest

p.build()                                        # p.build(tabs=True) for a hero tab
```

**Pick and drop** (v12): a widget dragged from the side panel into a site. The parts `a.drop_widget` needs:
```python
new = p.card("newsec", [p.row("newrow", [texts, photo], gap=40, w="fill")], w=693, radius=0, shadow=None,
             border=False, fill="#F3EEE6")                    # the section the widget becomes
slot = p.drop_slot("slot", new)                               # where it opens: between two sections of the site
site = p.column("site", [hero, stats, slot, footer], w=693)   # the site's content...
view = p.free("view", [(site, 0, 0)], w=693, h=590)           # ...in a clipped view (it scrolls inside it)
plus = p.icon_button("plus", icon="i_plus", variant=1)        # the "+" on the left bar
w1 = p.list_item("w1", w=246, title="Stream carousel", tag=True, tagLabel="New", suffix=False)
panel = p.card("panel", [w1, w2], w=285, h=590, radius=0, shadow=None, border=False)
rail = p.card("rail", [plus, *rail_icons], w=45, h=590, pad=(10, 12, 10, 12), gap=14, radius=0, shadow=None, border=False)
win = p.free("win", [(view, 45, 0), (panel, 45, 0), (rail, 0, 0)], w=738, h=590)   # back to front: the bar in front
p.layout(win)
a = p.actions()
a.drop_widget(w1, slot, site=site, panel=panel, plus=plus, intro=[(title1, body1), title2, photo])
```
Without `plus` the panel starts open and the site sits beside it (`(site, 285, 0)` in the view); `close_up=True` adds
the rare cut to the close-up. Any other drag (a file onto a folder, a card into a column): `a.drag(item, to=target)`.

**Two screens and a cut** (v14, LEARNINGS 8):
```python
home = p.free("home", [...], 1340, 638)
settings = p.free("settings", [...], 1340, 638)
p.layout(p.stack("screens", [home, settings]))         # the first on screen, the other hidden until the cut
a = p.actions()
a.at(0.6)
a.cursor_in()
a.click(open_btn)
a.cut(home, settings, "slide")          # the next click comes within 2 s: the cursor walks across the cut
a.click(save)
a.click(back)
a.cut(settings, home, "white")          # nothing after it: the cursor vanishes in place before the exit
a.wait(2.0)
a.jump_cut()                            # the seam as a jump cut (or a.loop())
p.build()
```

**A screen the AI generates** (v13, LEARNINGS 19.2; the welcome email in the email editor):
```python
ask = p.row("ask", [bubble], align="topRight", w="fill")                # the message, just sent
reply = p.chat_steps("reply", "Reading your website and designing a welcome email in the same style.",
                     ["Reading your website", "Pulling brand colors, fonts and photos",
                      "Writing the subject line and copy", "Designing the layout"],
                     "Here's your welcome email, designed from your website: ...")
copilot = p.copilot_panel("copilot", header, [ask, reply])  # v14b: the product's field, whole in the frame; its stop -> send on its own
# ... the email: `email` (its background has a #FFFBD6 -> #DCEBFF gradient), `hero` (the photo block, with `badge`,
# `welcome` and `tagline` over it), `crystal` (the lower photo), `logo` and `quote` (texts on the page)
a = p.actions()
a.sent(ask, t=0.0)                                                      # the message: in over 5 f, up 20 px in 30 f
end = a.generate_screen([hero, badge, crystal], area=email, t=0.0, loose=[logo, quote],   # v14b: badge comes with hero
                        details=[welcome, tagline], gradient=("#FFFBD6", "#DCEBFF"))
a.steps(reply, t=0.0, until=end)                                        # "✦ Thinking...", the summary, the steps
a.reply(reply, t=end + 25 / 60)                                         # "Thought for 4s" and the answer
p.build(tabs=True, duration=12)
```

**A site generated with its loose parts and a photo in detail** (v16):
```python
hero = p.photo("hero", "img/site_hero.png", 760, 400, radius=12, align=(0.5, 0.0), parts={
    "word": dict(box=(180, 80, 2250, 560), key="light"),          # the white letters on the wall
    "green": [(525, 392), (714, 389), ..., (870, 1300), (384, 1300)],  # the bottle, traced on a zoomed grid
    "jar": [(1566, 1059), (2219, 1059), (2240, 1300), (1546, 1300)]})
head = p.column("head", [announce, nav], gap=0, w=W)    # nav: texts on the page, no fill
side = p.column("side", [heading, para, card1, card2, shop], gap=16, w=330)
end = a.generate_screen([head, hero, side, news], area=(0, 0, W, H), t=0.3)
# timeline: MAIN.head split (...): 1 square(s) [announce], 6 loose [...], 1 line(s) of its own
#           MAIN.side split (...): 3 square(s) [card1, card2, shop], 2 loose [heading, para]
```

## 6. Motion rules for library pieces
From the team's motion spec (MOTION.md, PROCESS.md, tokens.json), for site pieces. The actions above already enforce
cursor paths and timing, press lead, the typing pattern, hover/press reactions, speed caps, swaps inside the
components, measured positions, the loop reset and the state machine. You still own:
- **Character**: smooth, rhythmic, nothing jumps. What appears arrives and settles (6–10 px, or scale 0.92–0.96 → 1,
  while fading in, decelerating): never pops in already placed, never overshoots or bounces. Use `enter`/`stagger`.
- **Movement does the work, opacity doesn't**: opacity only as a cut or a fade <= 167 ms. Never crossfade two
  screens; never morph one element into another.
- **One state at a time**: the new state starts on the old one's last visible frame (the old fades 100 ms). Never
  both on screen; never two dense layers (UI, text) above 15 % opacity on the same frame.
- **No layout reflow while animating**: what appears or leaves animates the space it takes (`remove`, messages do).
  Don't `set` a prop that resizes a box mid-scene unless the space animates.
- **Rest to rest**: anything visible starts and ends at zero speed, with no reversal or speed jump between two moves
  of the same element. The fast-start `settle` curve only where the start is invisible (an entrance); visible moves
  use `duda` (short) or `duda_strong` (~500 ms, panels, sizes).
- **Timing** (ms): press/release 50 · fade <= 167 · short 333 · medium 500 · panel 767 · long 850 · transition
  ~1000 · AI gradient sweep 1600. Stagger 17 for clustered micro elements, 67–83 for list rows and cards.
- **Reading**: every message the viewer must read stays >= ~1 s once fully visible (`a.hold`). Don't rush the end.
- **Beat order** (write them in this order): camera → cursor → hover and click → content reveals → AI gradients and
  loaders. Content first, then its label or chip.
- **Cursor** (v14, the motion designer's): appears and vanishes in place (3 frames), never crossing the frame's edge, never
  parked. One cursor per task (the same cursor goes on to the next step); a wait after a hover creeps (~12 px/s), never
  after a press: from a click, one curve to the next stop (v16b). v16, **one cursor
  per scene** (the blind review, 2026-11-26; it replaces "a wait of more than ~3 s lets it vanish and another one
  show"): once the cursor has shown in a scene, the scene's next actions happen without it (the Send presses on its
  own), never vanishing and coming back in the same action; the library does it for you, and `cursor=True` /
  `again=True` / `p.actions(cursor="any")` bring one back only when the motion designer asks. It clicks a field
  before typing. On its way it doesn't pass over other
  controls (the build bows the path away from them; one it still crosses lights up, as in the product). Its tip stays
  >= ~65 px above the bottom edge; it never shows inside the item it goes to (v14b). A soft "thought" (`hover(hold=)`) only on things that open more options. A long
  prompt: the cursor clicks the field and vanishes (`type_into(panel, ...)`). At a cut, `a.cut` decides: it walks across when its next move
  comes within ~2 s, else it vanishes in place before the exit and the next cursor shows after the cut (the build log
  says which).
- **Screen changes** (v14): always `a.cut` with the kind the moment needs: `slide` for a page that changes sideways,
  `zoom` for a click that goes into the thing clicked, `white` when a panel stays, `tabs` for a hero's tabs. Screens
  in a `p.stack`; never a crossfade, never a screen popping in. The cascade goes on what the click opened, and the
  frame around it comes in whole (v14b). Don't key the screens' display by hand (v14b).
- **Scrolling** (v14): always `a.scroll`: one move, never coming back.
- **A file thrown into an input** (v16): always `a.drop_file` (curated example 1, his numbers as they are).
- **Pick and drop** (v12): always `a.drag` / `a.drop_widget` for what is on screen: the closed hand on the grab frame (a hard swap, no
  press scale), the thing follows the cursor with its place empty, lifts with a soft shadow, shrinks and fades on the
  drop where the hand vanishes. Never drag with the arrow, never move the original.
- **Every click reacts**: the hover when the tip enters (a menu's: dry, no fade), the press (0.9 icon buttons, 0.96
  wide buttons); a selection control changes on the press; what the click opens comes on the release (+8 frames), a
  result (a modal, a notification) a few frames after the press, never on it (`a.click(result=)`). List rows don't
  squeeze: their highlight is the reaction. Something the piece drew lights too: `p.hoverable` (v14b).
- **Speed caps** (px per frame at 1920 wide, 60 fps): readable text 30, chips and icons 40. The cursor: 2.4 % of the
  frame's width per frame (~31 px/f at 1300; his approved peaks 18-26), any cursor, checked by the build. Panels and
  chat content don't slide their full width; they are revealed or enter with a short settle.
- **AI elements breathe**: AI buttons, the AI star, "thinking"/"updating" get the slow animated gradient (curve
  `gradient`, 1.5–2.7 s), and nothing else does. Agent progress is a list that keeps moving: the active step has a
  loader and the AI shimmer, resolves into a drawn check on the loader's last visible frame, the next step enters
  below. `p.ai_status` is the status line with the product's shimmer ("Thinking..." → `done` "Thought for 3s"; or
  `spinner`); `a.generate` is the gradient wash that builds a component, `p.gen_status` the "Generating... / Done"
  status. The step list with drawn checks is not in the library yet: flag it in the brief.
- **A screen the AI generates** (v13, v14): always `a.generate_screen`, started with the message (the generation is
  the loading): top to bottom, each block's texts, icons and photos as it shows, the loose elements at their place,
  in the design's own gradient when it has one, else the classic one; the steps on `until=` its end. Nothing to add
  by hand: no text passes, no photo scale, no feathers of your own. A piece shown smaller than its artboard:
  `p.shown_at(w)` first.
- **What gets a square** (v16; the blind review: what sits in a box comes from the gradient square, what sits loose on
  the background comes in on its own, as in Base44): only what has a box of its own. Give `a.generate_screen` the
  page's sections as they are (a head, a hero, a side column, a footer): the library splits a section with no box of
  its own, so a nav on the page's colour comes in text by text, never as one gradient rectangle. Read the timeline's
  "split" lines; force a square only when the review asks for it (`(item, {"square": True})`).
- **A hero photo with objects** (v16, v16a): `p.photo` with `parts` for the big word and each product, so the
  background comes in sharp first and the objects come into focus after it, saturated, the saturation going away.
  Check the plate in `build/photo/` (each object soft, no sharp line of its edge left) and the entrance's frames at 5x.
- **A generation block** (v13c, v14): `a.generate` sizes it (5 px of room, radius + 5) and lightens it (108 % / 102 %,
  Feather 11 -> 2 / 10 -> 1.5, the big one fading in); `feather=` only when a reviewer asks for a specific one.
  **A still icon**: `p.icon`, not `p.icon_button`.
- **A prompt in the Copilot** (v14): the cursor clicks the field and leaves; `typed` takes one cubic key on
  (0.1804, 0.0442, 0.2292, 0.676) from 9 frames after the click, ~53 letters a second (84 frames for a ~74-letter
  prompt; `a.type_into` on an AiPanel does it); with `then=panel.part("send")` the send presses on its own 45 frames
  after the last letter (`a.send` for a field of your own). Never a caret, never the placeholder back.
- **The answer** (v14): `a.reply` types it, 120 letters a second, at most 1 s; never `stream=True` or whole
  paragraphs for a Copilot that answered a generation.
- **A sent message** (v13b): always `a.sent` (5 frames in, 20 px up in 30, both from the send; the AiPanel does it on
  its own), never `a.enter`. **A docked Copilot** in a frame shorter than Figma's panel: `p.copilot_panel`, so the
  field stays whole at the foot (Figma's margin) and the conversation gets shorter.
- **A docked Copilot's field** (v14b): always `p.copilot_panel`'s own (`p.copilot_field`): the product's height, only
  "+" and send; never drawn by hand, never an `a.key` on it. Its button is grey #C9CACD while the field is empty,
  orange from the first letter (no fade), the orange stop while the Copilot works, and grey again with the status
  swap at the answer (stop out 0.1 s, then send in 0.1 s; the edge back to rest).
- **A block inside a block** (v14b): pass it plain in `a.generate_screen`'s list; it comes with the block it sits on,
  as one of its rows, never with a ~1 s slot of its own (it would push every later block, the steps and "Thought for
  Xs").
- **Loop seam**: ~3 s still in all, both sides of the seam together (`loop()` makes it), so the page stays calm; or
  a match cut, or a jump cut (`a.jump_cut()`, called last instead of `a.loop()`). Spinners and shimmers stop before the seam. A hero tab plays once (`tabs=True`) and opens already
  moving (its first movement <= ~0.9 s); a carousel tab (`carousel=12`) shows its first screen whole at f0, never
  goes back to the start, and (v14b) its story ends by ~5.5 s, the rest still (the approved email carousels: 5.2-5.5
  s; "~3 s still" is a hero's or a loop's). **A carousel with a Copilot** (v14b): it opens on the send, the message
  coming in at frame 0 with `a.sent(msg, t=0)` (the approved ask-your-agent): the first screen is the editor, the
  message arriving is the action; never a bubble sitting still at f0.
- **Figma is the reference, not the limit**: motion may add the states the design implies (hover, press, focus,
  progress) with its own components and colours, never new content. The product decides content and behaviour.
- **Site, not video**: on the site the product window stays still (no camera drift on the UI; a hero's slow drift
  goes only on its background photo, confirmed with the motion designer). No zoom into part of the scene unless the motion designer or the design lead asks: then `a.camera_close` /
  `a.camera_open` (or `a.drop_widget(close_up=True)`, a rare cut the approved recipe allows). The artboard is
  square-cornered (the page rounds it); no cut-off edge may show.
- **Review** like Mateus does, frame by frame, on the stills of every beat: edges and corners appearing, the
  cursor vanishing, jumps (a pop, a reflow in one frame, a state flashing), a zoom into part of the scene.

Token names (motion-spec/tokens.json, already wired into the actions): curves `duda`, `duda_strong`, `settle`,
`gradient`, `scroll` (the old scroll ease (0.6, 0, 0.4, 1); `a.scroll` uses LEARNINGS 10's (0.857, 0, 0.242, 1)), `linear` (opacity, spinners, press);
durations `press`, `release`, `fade`, `short`, `medium`, `panel`, `long`, `transition`, `gradient_sweep`,
`read_hold`; stagger `tight`, `list`, `loose`; `state_swap.fade_out_ms` (100); `speed_cap_px_per_frame_at_1920`. The
cursor's numbers are the motion designer's, in the library (v14): 0.85 s + 1 ms per px from stop to stop, press 0.85 in 3+3 frames,
5 frames before it stops (7 on a field); the tokens' `cursor.move_ms` and `hover_lead_ms` are the old cursor's.

## 7. When the build says LINT
- `... peaks at X px/f > cap`: give the move more time or less distance (actions size their own moves).
- `cursor CURSOR1: ... px/f ... over the ceiling`: the cursor is too fast for 2.4 % of the frame per frame: give
  the click more time (`t=` later) or let the action time itself.
- `cursor CURSOR1: slows down and surges again`: a hitch between two stops (keys of your own on its path?): one curve
  from stop to stop.
- `cursor CURSOR1: parked still on screen`: it waits dead still; let it creep (`hover(hold=)`) or vanish
  (`cursor_out()`).
- `carousel: <box> isn't on screen at f0`: a carousel tab shows its first screen whole at f0: no `a.enter` at the
  start. `NOTE: carousel: the last action ends at ...` (bring the story earlier: it ends by ~5.5 s) / `NOTE:
  carousel: ... sits still at f0` (`a.sent(msg, t=0)`) / `NOTE: hero tab: the first movement starts at ...`: soft rules,
  printed, not failing.
- `clicks ... but nothing reacts`: click components, not text or boxes.
- `message on <slot> ... shown only`: `a.hold(...)` longer after the message.
- `loop: ... jump back`: `a.loop(exit=card)` with the card (that `enter`ed at the start) holding what changed.
- `something still happens after the loop's exit`: end every action before `a.loop()`.

## 8. Mixing the library with a scene of your own
A hero often needs what the library doesn't draw (a photo behind the window, an export of a site, a shape of the
storyboard). The library pieces and your own elements live in one artboard and one timeline:
- **Your own drawing** goes in with `p.wrap(name, [elements])`: `kit.El` / tools' `rml.py` elements (shapes, paths,
  gradients, `Image` with `"assetId": p.asset("bg", "img/bg.jpg")`). Give each element a unique name: it is how you
  key it. Build everything before `p.actions()` (the timeline only knows what is placed by then).
- **Storyboard placement**: `p.free("win", [(bg, 0, 0), (ws, 87, 41, 0.81)], 1340, 638, radius=12)`: the product UI
  at the storyboard's scale, the window's corners round (the clip too). The cursor aims at scaled children.
- **Your own keys**: `a.c.set(t, "MAIN.bg", "scaleX", 1.03)`, `a.c.move(t, name, prop, to, dur, "duda")`,
  `a.c.fade(...)`, `a.c.enter(...)`, or a beat sheet `a.beats([{"t": 0, "do": "move", "target": name, "prop":
  "scaleX", "to": 1.035, "dur": 6, "ease": [0.37, 0, 0.63, 1]}])`. They don't move `now`. A placed item's element is
  `"<ARTBOARD>.<name>"` (`"MAIN.card"`); your own keep their names.
- **A background drift** (the hero's photo; the window stays still): `a.beats` on the photo's wrap, scale 1 → 1.035
  → 1 over the whole tab.
- **A panel that takes another's place** (the chat → Quick Edits): place both in `p.vibe_workspace(panel=[chat, qe])`,
  then `t = a.hide(chat.content)` and `a.enter(qe, t, dx=16, dy=0, dur="panel", ease="duda_strong")`.
- **A hero tab of a set length**: `p.build(tabs=True, duration=12)`; `tabChange` fires right at 12 s.
- **See-through**: `Piece(..., bg=None)` and `p.vibe_workspace(..., fill=None)` let the page show around the window.
- A kept version's scene is saved as `scene.rml.txt` (so Rive doesn't build it); see §6 of `new-motion.md`.

### A screen from Figma (v15)
When the storyboard shows a product screen the library has no component for, draw it from Figma's SVG export instead
of a picture (no raster UI) or hand-placed shapes:
1. Export the frame as SVG into `figma/vec/` (text stays outlined in the export: the build redraws it as native text)
   and the frame as PNG 1x into `figma/frames/` for the check.
2. `scr = p.figma_screen("home", "figma/vec/home.svg", layer="Screen – Home", frame=(1166, 729), drop=["New
   Automation"], parts=["Table"])`, then `p.figma_sheet()` once: name the outlined texts it lists with `texts=`
   (a layer named "Text_3", a text with a link in it, a badge named "Status" that shows "Active").
3. Place the library's components over the screen where `drop` left a hole (`p.free("win", [(scr, 0, 0), (button, x,
   y, scale)])`), and animate it with the usual actions: `a.generate(scr.parts["Table"])`, `a.cut(scr, scr2,
   "slide")`, `a.enter(scr, ...)`.
4. The build prints one line per screen (shapes, native texts, outlined, plates, clips left out). Compare a still with
   the Figma PNG; `[outlines]` in the notes says how many letters are still outlines.
- A still part that only moves or fades whole: `plates=["Left rail"]` (a 2x lossless WebP made by the Rive CLI from
  the same vectors). A screen that never animates inside: `plates=True`.
- A client's font: `p.font("brand", "fonts/Brand.ttf", "Brand")`, then `fonts=("duda", "brand")`.
- Don't name an item `page`: the layout's root already has that name.

### Built for hand edits: `p.build(remap=...)` (v15c)

The same frames as a plain build, in a structure you can retime by hand in the Rive editor: two keys move a whole
scene or element instead of hundreds. Without `remap=`, the build is exactly as before.

**What it builds**

- **MAIN**: the background, "State Machine 1" (`play` / `tabChange`), the view model, and one "Timeline" that plays
  only these:
  - **"Scenes"**, a Solo with one nested artboard per scene. Only the active one draws. The Solo's active scene has
    a hold key on the frame each scene takes over (the cut frame).
  - **"<Scene> time"**, per scene: a time remap with two keys, 0 to 1, linear, from the frame before the scene
    shows to the frame the next one takes over. Drag both keys to move the scene. Bring them closer to speed it up.
  - The cursor visits that cross a cut (see the cursor rule), drawn over the Solo.
- **One artboard per scene**: only what shows in its stretch (its screens, its cursor visits, its Generation
  effects), its own "Timeline" from 0, and the drivers of the components it shows.
- **One artboard per element you name**, nested in its place inside its scene, so it moves with its screen. It
  carries its keys, its drivers and its Generation effects. Its own "<Element> time" sits in the scene's Timeline,
  from the frame before it first changes to its last change.

**Options**

| `remap=` | what it does |
|---|---|
| `{"scenes": ["Home", "Settings"]}` | one scene per stretch between two `a.cut` (one more name than cuts) |
| `{"scenes": [("Intro", 0), ("Editor", 3.2)]}` | the second each scene starts, for a piece without `a.cut` |
| `{"scenes": [("Intro", 0), ("Editor", 3.2, 0.5)]}` | the two scenes overlap for 0.5 s (a crossfade of your own) |
| `{"scenes": None}` | the whole piece as one scene that MAIN nests (it plays smoother in the editor) |
| `"elements": {"Home": [card]}` | items that get an artboard of their own, by scene |
| `"cursor": "main"` or `"scene"` | overrides the cursor rule: every visit on MAIN, or each visit copied into every scene it shows in |

**The cursor rule.** It applies per visit (one `a.cursor_in` ... `cursor_out`):
- A visit that shows inside one scene lives in that scene, so it moves and retimes with it.
- A visit that walks across a cut, or shows during an overlap, lives on MAIN over the Solo, keyed on MAIN's
  Timeline.

The build log says where each visit went and why. For example, `a.cut(..., cursor="vanish")` and a new
`a.cursor_in()` after the cut give one visit per scene.

**Overlaps.** Two scenes draw in the same frames, for example a crossfade of your own with `a.key(..., "opacity")`.
- The Solo keeps the earlier scene through the overlap and switches when it ends.
- A second nest of the later scene, "<Scene> (overlap)", sits outside the Solo. It shows by opacity during the
  overlap only (hold keys), with the same time keys. Move "<Scene> time" and "<Scene> (overlap) time" together.
- Each part is drawn once during the overlap: by the earlier scene if it showed before the overlap, else by the
  later one.
- The overlap nest goes above or below the Solo, following the later scene's draw order in the plain build.
- The library's own cuts (slide, zoom, white, tabs) never overlap. Name them with `"scenes": [...]`.

**The log.** After the usual timeline and lints, the build prints:
- one line per scene: the frame it becomes active, its Time, its size;
- one line per element and per cursor visit;
- one line per overlap: its frames, and where its nest went;
- NOTEs for what needs a look.

**Checking it.** Build the piece twice, plain and with `remap=`, render every frame of both, and compare. Then, in
the editor, drag a scene's two "time" keys and the Solo's key and play MAIN.

**Limits**

- An element must sit alone in a `p.free` slot `(x, y)` or be a screen of a `p.stack`, because a flex layout would
  move around it.
- Not with live hovers (`p.hoverable(live=True)`): the build stops. Their layers and listeners live on MAIN's state
  machine.
- A part that shows on both sides of an overlap is drawn by both scenes there, so a see-through one gets stronger.
  The log names it.
- A driver whose component shows in more than one scene stays on MAIN's Timeline.
- A driver's change after its component's scene has ended is dropped, since nothing shows it. The log lists the
  frames.
- Only `scene.rml` changes. The lints and checks run on the same choreography, and `--stills` and the web check
  render the remapped file.
- v15d: with a runtime older than 2.45 (2.39.2), `tabChange` doesn't reach the page from a Solo piece. A page that
  depends on `tabChange` there: build it without `remap=`. `play` and the scene switches work in both. In 2.39.2 the zoom and
  tabs cuts scale a few px off their point, with or without the Solo (the old runtime's; 2.45.0 matches the CLI).
- A rebuild overwrites hand edits, so keep the edited `.rev`.

## 9. Before the plan: the questions only the motion designer can answer
v14, from the precision research (package 7): these answers changed whole versions when they
came late. Ask them with the plan (`/nova-peca`, `/new-motion`), in plain words, before v01; everything technical the
library decides.
1. **Where does it live?** A hero tab of the site (plays once, `tabs=True`, opens already moving, `tabChange` at
   its end), a carousel tab (`carousel=12`: 12 s, the first screen whole at f0, no white at the start or end, no
   return to the start, the story over by ~5.5 s and the rest still), a card (loops on its own; or plays once / on hover / on click), or a
   section that loops (`a.loop()`, ~3 s rest). The container's size, if the page crops it.
2. **Its length and rhythm**: how long (the carousel's 12 s, a tab's duration) and where the story's beats fall
   inside it. When he gives times, they are seconds:frames ("00:03:40" = 3 s + 40 frames = frame 220); repeat the
   moment back in words ("the generation done at 3.67 s") before building.
3. **Which fields does the visitor type?** Only the message, every field (`type_into` each, ~1.45 s per field), or
   the start of the first one and the browser's autofill for the rest.
4. **Which generation?** The hero_1 squares (`a.generate_screen`, the default), the map's blocks, or the bars of a
   recording. And "Thought for Xs": a fixed text or counted from the send.
5. **Is there an approved piece this one should copy?** Its cursor, timings, generation or close-ups (read its
   build and its `brief.md` first).
6. **What on the storyboard is not the product?** Placeholder icons, notes, things only the storyboard shows (a
   time, a toast the product doesn't have): list them frame by frame and ask which stay. Content and behaviour are the
   product's; spacing and sizes are Figma's when it is the same UI.
7. **The cursor at a screen change** only when the plan has one the library can't decide (`a.cut(..., cursor=)`
   decides from the next action; ask when he has a preference).
