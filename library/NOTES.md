# Library notes (v02)

Decisions, property tables, open questions and what building this taught us about Rive. A piece needs only
`QUICKSTART.md`; the README is about the library itself.

## Changelog

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
