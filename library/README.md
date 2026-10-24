# Duda Design System · Rive component library (v06)

The Duda Design System (Figma `W1HVKzyIBQ8sOyFHv6Jzgm`) rebuilt as Rive components. As in Figma, bigger components
are made of smaller ones, and every value comes from the DS tokens (`ds/tokens.json`). Where the DS has two
generations of a token, the newer one wins.

**Building a piece? Read `QUICKSTART.md`.** It has the import, the component tables, the choreography actions
(`piece.py`), a complete example and the motion rules a piece needs. This page is about the library itself.

## Components

| artboard | made of | what it is |
|---|---|---|
| `Icon/<name>` (58) | - | the DS icons, 16x16, stroke 1.5. Placed by an artboard property (Figma's instance swap) |
| `Icon button` | Icon | Icon / Box, Small 24 / Large 32, 5 colors, hover, press, selected, focus, loading, disabled |
| `CoreButton` | Icon | Primary / Secondary / Text, 3 sizes, 12 colors, left and right icons, the same states |
| `Divider` | - | With text / No text / Vertical |
| `Cursor` | - | the product cursor, origin at the tip, `click` trigger |
| `Smart_Tag` | Icon | 2 sizes, 2 radii, Grey / White / Primary, prefix icon, remove button |
| `CoreInput` | Icon | label, placeholder, live typing (two-way `value`), focus, error / success / warning, read-only, disabled |
| `VibeFloatingBar` | CoreButton, Divider, 6 Icon buttons | the visual edit's floating bar (the pilot) |
| `Core Toggle` | - | Toggle 28x18 (check on the knob) / Switch 48x30, on, pressed, disabled |
| `Core Checkbox` | - | Empty / On / Partial (the check draws on), pressed, disabled |
| `Core Radio Button` | - | selected (the dot grows in), pressed, disabled |
| `Pill_Tabs` | Icon | 2–6 tabs, Hug / Fill, icons; the white tab crossfades to the selected one |
| `SearchInput` | Icon | placeholder, scripted typing (`typed`), focus (caret, the x), disabled |
| `Status` | Icon | 8 colours, border, hover, the chevron, the unread dot |
| `Promotional Tag` | - | Default ("new"), Premium, AI, New dot |
| `Tooltip` | - | max 200 or hug; `shown` fades and grows in |
| `Loader` | - | 16 / 24 / 48 / 96, the DS arc, always turning |
| `Icon Thumbnail` | Icon | 7 themes, 4 sizes, circle, disabled |
| `Core Tabs` | - | 2–6 tabs; the 2 px line grows from the selected tab's centre |
| `ListItem` | Icon Thumbnail, Icon | prefix thumbnail, title / secondary, "new" tag, suffix icon, 7 states + hover |
| `MenuListItem` | Icon | a 32 px menu row: icon, hover, selected (a check), destructive |
| `CoreDropdown` | Icon | Type Text: label, value / placeholder, prefix icon, open (the chevron turns), error, disabled |
| `AiProcessIndication` | Icon | the AI status line: "Thinking..." shimmering, done ("Thought for 3s" + chevron; v04: no chevron), spinner |
| `Text Area` | Icon | v04: several lines under the CoreInput label (required, info icon), typing that wraps, focus, read-only, disabled, the resize corner |
| `AiPanel` | - (draws its own DS icons) | v05: the AI chat, docked (Vibe) or floating (Copilot): open / close, suggestions, typing, send, "Thinking...", the reply paragraph by paragraph, the action bar, hovers, a prototype with a real text field |
| `Skeleton` | - | v06: the dashboard's loading block, a grey bar the product's shimmer crosses every 1.4 s on its own; `circle`, `shimmer` |

Built from the components in `dashboard.py` (v06; piece helpers, native and editable in Rive): the site dashboard of the
AEO report (window, rail, PERFORMANCE menu, KPI card, donut, line chart, chart card, the whole Highlights page) and
the actions that load it (`a.load`: skeletons give way to the content) and draw the charts (`a.draw`). `scripts/`
renders an MP4, compares a frame with a Figma PNG and runs the web check from any folder.

Every component has its own `State Machine 1` and is driven only by its view model. `NOTES.md` has the full property
tables and the DS × polish decisions; `manifest.json` lists every property with its kind and default.

Rules every component follows:
- Properties carry the DS names. Choices are numbers, never enums (`variant`, `size`, `color`: 0, 1, 2...), because an
  enum starts at its first value and fires the layers bound to it at frame 0.
- `hover`, `pressed`, `focused`... can be set from outside (a scripted animation) or, when `interactive` is on, by the
  component's own listeners (the mouse). `click` plays a press from outside; `clicked` fires when the visitor clicks.
- Motion uses the team's tokens (`motion-spec/tokens.json`): hover 150 ms, press 50 ms and a soft 333 ms release,
  entrances with the settle curve.

## Files

| path | what it is |
|---|---|
| `piece.py` | pieces in a few lines: `Piece` (placing, layout, measured positions) and `Actions` (choreography) |
| `patterns.py`, `common.py` | the hero parts (Quick Edits, the Code tab, the AI's answer and status, the Generation effect) and what they share with `piece.py` |
| `kit.py` | the lower level: tokens, view models, layout, state machines, icons, output. For what the actions don't cover |
| `library.py`, `components/` | the components in build order, one module per component (`hosts.py`: the `Host` helper) |
| `icons/`, `art/`, `ds/tokens.json` | the DS icons (svg), the library's own drawings (AI star, logo, loader arc) and the DS tokens, read from Figma |
| `vendor/`, `motion-spec/` | frozen copies of the build tools and of the motion tokens this release was made with |
| `fonts/` | Duda Sans (`LabelSansVF.ttf`), the caret font for typing (`DudaSansCaret.ttf`), the underlined cut for the AI panel's link (`DudaSansUnderline.ttf`) and JetBrains Mono (the code editor) |
| `webtest/` | plays a `.riv` in the site's runtime (`@rive-app/webgl2@2.45.0`), headless, with scripted steps |

## The lower level (scenes the actions don't cover)

```python
sys.path.insert(0, os.path.join(HERE, "lib", "biblioteca-v06"))
import kit, library
from components.hosts import Host
from components.icon_button import IB

icons, comps = library.library()
h = Host("main", "MAIN")                       # the piece's view model: one property per placement
bar = h.bar("bar", interactive=True)           # the floating bar, with its own parts
send = h.place("send", "ib", IB, dict(icon=kit.icon_ref("i_send"), color=0, interactive=True))
...
xml, doc = kit.assemble([main] + comps + icons, list(kit.VM.all))
```

Drive the components from the piece's state machine through their properties, with paths (piece VM → placement →
component property), or react to `clicked`. `examples/page-settings` and `examples/site-settings` mix both levels.

## Versions
A released version never changes; a change means a new version (v07…), and pieces move to it on purpose. Pieces copy
the release into `lib/biblioteca-v06`, so an update never changes a piece already made. The library is built and
released by the repo owner.

Tested with the Rive CLI 1.7.0 (`--verify` 0 errors, stills of every artboard, pointer tests) and with
`@rive-app/webgl2@2.45.0` with autoBind (hover, click, typing, view model edits from the page, icon swap).
