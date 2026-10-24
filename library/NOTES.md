# Library notes (v07d)

Decisions, property tables, open questions and what building this taught us about Rive. A piece needs only
`QUICKSTART.md`; the README is about the library itself.

## Changelog

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

## What we learned about Rive (CLI 1.7.0, runtime 2.45.0)
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
