# Duda DS library v07d · QUICKSTART

The Duda Design System as Rive components, plus ready-made choreography. A piece is one Python file: place components,
lay them out, script the cursor and the states with actions, build. **This page is all you need**: don't open the
bundle's code, `manifest.json` or `motion-spec/` (the rules a piece needs are in section 6).

**The Highlights page (AEO report): v07d is the official version** (approved on 2026-10-24): a piece with the
Highlights page or its parts (KPI cards, donut, line chart) uses this library from now on (v07, v07b and v07c
were review rounds, not published here). The lavender layer over the line chart's area stays while the timeline
plays, with no fade (approved as is).

## 1. Set up a piece and build it (from the repo root)
```bash
mkdir -p pieces/<piece>/lib && cp -R library pieces/<piece>/lib/biblioteca-v07d
# write pieces/<piece>/build.py (start from the example in section 5), then:
.venv/bin/python -I pieces/<piece>/build.py                    # scene.rml (+ rive.yaml), timeline, lints
(cd pieces/<piece> && ~/.rive/bin/rive . --verify)             # must say 0 errors
.venv/bin/python -I pieces/<piece>/build.py --stills 1.2 3.4   # PNGs + sheet.png in build/stills/ (frame N = --advance=N+1)
(cd pieces/<piece> && ~/.rive/bin/rive . --once)               # unsigned build/<piece>.riv, for the web check
mkdir -p pieces/<piece>/renders/v01 && (cd pieces/<piece> && ~/.rive/bin/rive . --once --rev=renders/v01/<piece>_v01.rev)
```
The build exits 1 and prints `LINT:` lines when a motion rule fails. Never run `rive push`, `--publish` or
`rive library publish`, and don't open a live preview unless asked. Python always via `.venv/bin/python -I`.
**Compare, render, web check**: scripts in the bundle (they work in any folder; `L=pieces/<piece>/lib/biblioteca-v07d`):
```bash
.venv/bin/python -I $L/scripts/compare.py pieces/<piece> pieces/<piece>/figma/frames/<pose>.png --frame 0   # vs Figma
.venv/bin/python -I $L/scripts/render_mp4.py pieces/<piece> pieces/<piece>/renders/v01/<piece>_v01.mp4    # every frame
.venv/bin/python -I $L/scripts/webtest.py pieces/<piece> 0.5 2 4      # the site's runtime 2.45.0, shots at those seconds
```
`compare` captures the frame at the Figma PNG's size and prints the mean difference (target <= ~12/255) and a 3 x 3
grid of it (where it is off); look at `build/compare/<pose>_overlay.jpg` before saying it matches. `render_mp4`: the
main artboard's size (`--size 2680x1276` for 2x). `webtest` builds `build/<piece>.riv`, serves it, plays it headless
with `autoBind` and saves `build/webtest/MAIN_<t>s.png` and the log (needs Node and Playwright: SETUP.md's optional
step). `--plan plan.json` for clicks, typing and view model values: `[{"name": "x", "ab":
"MAIN", "w": 1340, "h": 638, "s": 0.5, "watch": "play,email/value", "steps": [{"at": 2, "shot": "a"}, {"at": 3, "js":
"window.T.fire('play')"}, {"at": 4, "click": [600, 300]}]}]`. Headless Chrome runs the clock unevenly: shots prove
states, not timing (exact frames: the CLI stills).

## 2. The scene
```python
p = Piece("MAIN", 1340, 638, bg="Backgrounds/bg-grey-color")   # artboard name, size, '#rrggbb' or DS colour token
```
`bg=None`: a see-through artboard (the page shows behind it). `cursor_shadow=True`: the cursor's soft shadow (the
storyboards draw it); `cursor_scale=`: its size.
**Components** (each returns an item the actions can target; `**props` are the props of section 3)

| call | what it makes |
|---|---|
| `p.button(slot, **props)` | CoreButton |
| `p.icon_button(slot, icon="i_send", **props)` | Icon button |
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
| `p.ai_status(slot, **props)` | AiProcessIndication: the AI status line ("Thinking...", shimmering on its own; `done=True, chevron=False`: "Done" with no chevron) |
| `p.text_area(slot, w=358, h=126, **props)` | Text Area: a field of several lines under its label (the label takes 26 of `h`); `a.type_into` types into it, the lines wrap |
| `p.divider(slot, w=240, **props)` | Divider (`variant=2` vertical: give `h=`; `h=1`: just the line) |
| `p.bar(slot, style="ds", open=True, over={"trash": {"selected": True}})` | VibeFloatingBar; its parts are targets: `bar.part("trash")`. `style="storyboard"`: the hero storyboards' bar ("Edit Design", left, right, a menu in place of close) |

**Text, images, layout**

| call | what it makes |
|---|---|
| `p.text(name, "Hello", style="Headlines/He 1", color="Typography/primary-text-color", w=None)` | DS text: one line; `w=` points or `"fill"`: a paragraph that wraps (`align=` left, center, right) |
| `p.font(key, "fonts/Brand.ttf", "Brand")` then `p.text(..., style=None, font=key, size=, lh=, weight=)` | a client's typeface (a file in the piece folder, one per weight). The keys `duda`, `caret`, `mono` and `cal` (Cal Sans SemiBold: the dashboard's titles and numbers) are the library's |
| `p.image(name, "img/photo.jpg", w, h, fit="cover", radius=0)` | a photo or screenshot in a w x h box: `cover` crops (Figma Fill), `contain` (Fit), `fill` stretches |
| `p.row(name, kids, gap=8, pad=0, align="centerLeft", w="hug", h="hug")` | horizontal stack |
| `p.column(name, kids, gap=16, pad=0, align="topLeft", w="hug", h="hug")` | vertical stack |
| `p.free(name, [(item, x, y), (item, x, y, scale)], w, h, clip=True, radius=0)` | each child where Figma has it, back to front; `scale` from its top-left (a product UI at 0.73 in a storyboard); `radius`: round corners, the clip included |
| `p.wrap(name, elements, w="hug", h="hug")` | your own drawing (kit or tools/rml.py shapes) as a target (section 8); loose shapes go in a Node inside it, back to front, so the box doesn't stretch them |
| `p.asset(key, "img/photo.png")` | an image of the piece for your own `Image` elements: returns its asset id (`"@img.<key>"`) |
| `p.card(name, kids, w=380, pad=24, gap=16, title=None, action=None)` | DS card: white, radius 8, 1 px edge, shadow-1; `title` (Bold 16/22) with an optional text button `action` ("See all", a target: `card.action`); `w="hug"`, `shadow=`, `border=`, `fill=`, `radius=` |
| `p.layout(root, align="center", pad=0)` | what the artboard shows (call once, before `p.actions()`) |

**DS patterns** (built from the piece's own content)

| call | what it makes |
|---|---|
| `p.menu(name, ["Rename", {"label": "Delete", "icon": "i_trash", "destructive": True}, "-", "# Section"], w=268)` | CoreFloatingMenu / a dropdown's menu (radius 12, shadow-5); `menu.entries` are its items |
| `p.collapsible(name, title, kids, w=400, open=False, icon=None, card=True)` | Collapsible: a click on `c.header` folds / unfolds it; `a.open(c)` / `a.close(c)` without the cursor |
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
| `p.code_panel(name, code, files, file="App.tsx", tree_w=146)` | the Code tab: the file tree (a search over it) at the left, the open file's tab over a code editor. Targets `.tree`, `.editor`, `.search`, `.tab` |
| `p.code_editor(name, code, size=10, lh=17, numbers=True, empty=True)` | the editor alone, JetBrains Mono, line numbers. `code`: text (JS / JSX coloured on its own) or lines of `[(text, kind)]` (k f t s c p); `empty`: it starts empty for `a.write_code` |
| `p.file_tree(name, ["src/", "  App.tsx", "  +TopBar.tsx"], w=146, selected=None)` | a tree: 2 spaces a level, `name/` a folder, `+name` a file that arrives later (`a.add_file`); `tree.rows["App.tsx"]` are targets |
| `p.gen_status(name, label="Generating...", done="Done")` | the AI star and "Generating..." (the hero Code tab): `a.generating` shimmers it, `a.done` turns it to "Done" |
| `p.chat_user(name, "text")` · `p.chat_ai(name, "text")` | the user's bubble (`fill=`, `pad=`) · the AI's answer; with `p.ai_status` they go in `chat=` (the free panel) |
| `p.chat_reply(name, ["paragraph", ...], actions=("i_duplicate", "i_options"), gap=24)` | the AI's answer as the product brings it (in `chat=[ask, reply]`): "Thinking..." right under the message, each paragraph taking no room until it comes, the action icons after. Targets `.status`, `.actions`, `.paragraphs` |

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
| AiPanel (`p.ai_panel`) | `title` "New chat" / `titleAfter` (the name once answered: docked with the action bar, floating 1.1 s after sending) · `copilot` false (true: floating) · `greeting`, `subtitle`, `chip1`..`chip4`, `showMore` · `placeholder` / `placeholderAfter` · `prompt` · `status` "Thinking..." · `reply`, `reply2`, `reply3` (an empty one is left out) · `build` "Build" · `disclaimer`, `link` · `showThought` false (Figma: "Thought for 3s" instead of the status) · `figmaActions` false (like, dislike, undo too) | `stage` 0 empty, 1 sent (bubble, "Thinking...", stop), 2..4 each paragraph opens its room and comes in, 5 done (action bar) · `typed` · `focused` · `hidden` (closes: docked slides right, floating shrinks into its corner; false opens it, the suggestions cascading) · `hover<Control>` (hoverSend, hoverChip1...) · `interactive` (the prototype: a real field) |
| AiProcessIndication | `label` "Thinking..." · `spinner` false (a turning arc instead of the AI star) · `chevron` true | done (the shimmer stops, a chevron shows: "Thought for 3s"; `chevron` false: none) |
| Skeleton (`p.skeleton`) | `circle` false (round: a dot, an avatar) · `shimmer` true | the band crosses every 1.4 s on its own (`shimmer` false: a still block) |

The cursor is the library's Cursor (blue #508AF6, white outline), placed by the actions; `Piece(..., cursor_scale=1.0)`.

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
| `a.cursor_in(side="right", t=None)` | a cursor comes in from off-frame, already moving (right, left, bottom, top); `t=s`: it sets off at s (`now` moves there). Optional: the first click brings one from the right |
| `a.move_to(item, where=None, hold=0, at=None)` · `a.hover(item, hold=0.6)` | passes over / lingers softly (a "thought"), the item shows its hover; `at=(x, y)`: a point of the board instead |
| `a.click(item, where=None, loading=None, at=None)` | hover 150 ms before, press on the press frame (the component's squeeze + the cursor's 0.85 press), focus if it is an input; `loading=s`: spinner for s seconds from the press. It aims where the item is on the press frame (a panel still sliding in). `at=(x, y)`: a click on that point. Returns the press time |
| `a.type_into(input, search, text area or AiPanel, text, then=None, then_where=None, replace=False)` | Duda typing pattern: clicks the field if needed (focus), types from 150 ms later, the cursor drifts aside on one arc and swoops to `then`, clicking it as the last character lands; no `then`: the cursor leaves while it types. `replace=True`: the field's text is selected and the new one types over it |
| `a.remove(tag)` | clicks the tag's x (or uses the click `type_into(..., then=tag, then_where="remove")` just made): the tag fades and shrinks 0.1 s, then the row closes the gap smoothly |
| `a.message(input, text, kind=None)` | the message under the field; kind None (info), "error", "success", "warning". A shown message leaves first, then the new one arrives. Returns when it shows |
| `a.set(item, **props)` | any prop on the timeline: `a.set(bar, open=False)`, `a.set(btn, t=t_press, selected=True)`, `a.set(thinking, label="Thought for 3s", done=True)` |
| `a.key(item, prop, value, dur=0, ease="duda")` | a key of your own on a placed item or one of your elements: `"opacity"`, `"x"`, `"y"`, `"scaleX"`, `"rotation"`, `"width"`...; `dur` > 0 moves to it. A component's own states go through `set` |
| `a.click(panel.part("send"))` · `a.think(panel)` · `a.reply(panel, step=0.27, then=1.0)` | an AiPanel: the click sends (stage 1: the bubble, "Thinking..." under it, the stop button; the field keeps the focus) · `think` sends without the click · each paragraph of its `reply` opens its room (0.25 s), pushing the status down, and comes in (rising 4 px); `then` s after the last is in, the action bar takes the status's place. `a.set(panel, hidden=True)` closes it. Typical: `a.type_into(panel, PROMPT, then=panel.part("send"))`, `a.wait(1.6)`, `a.reply(panel)` |
| `a.think(reply)` · `a.reply(reply, step=0.27, then=1.0, stream=False)` | a `p.chat_reply`: "Thinking..." comes in under the message · each paragraph opens its room (0.25 s), pushing the status down, and enters into it; `then` s after the last, the status gives way to the action icons (no "Thought for Xs", as the product). `stream=True`: word by word |
| `a.text(item, "New title", fade=False)` | a `p.text` changes (a chat renamed); `fade=True`: out 0.1 s, change, back in |
| `a.stream(item, text=None, cps=80)` | the AI's reply word by word (a `p.chat_ai` / `p.text`, empty until then) |
| `a.count(item, 128, dur=0.7, fmt="{:,}")` | a number counts up from 0, sharpening from a light blur; `a.count(item, 2.6, fmt="{:.1f}%")` counts in tenths |
| `a.load(items, t=None, step=None, dur=0.6, draw=True, count=True, glow=True)` | v06: skeletons give way to the content (a page, a card, a chart or a list), one item after another, `step` s apart (the product's 0.27; a Highlights page keeps its own timing unless `step` is given, v07d, Mateus's: the charts first, the KPI cards 21 frames later all at once, each next card's tint 4-5 frames later): the skeleton fades out (0.1 s), the content fades in; KPI numbers count up (v07: Mateus's curve, fast then a long soft landing, 1 s and each next card 10 frames longer) and their chip comes 0.55 s in; charts draw. `glow` (v07, on by default since v07b; `glow=False`: plain): the numbers count in blurred 3 px and tinted orange, pink, purple, then sharp in their colour. Returns when the last is in |
| `a.draw(chart, t=None, dur=None)` | a chart draws itself: a donut clockwise from the top (1.1 s, "duda": fastest half-way), then its total; a line chart (v07; in `a.load` its fastest moment, the start, falls on the donut's, v07c, or it starts once its labels are in): the line is traced from the left as it sharpens (0.67 s, linear) while the area's colour comes down from the top under a lavender layer (Mateus's) |
| `a.generate(item, kind=None, rows=None, pops=None, squares=None, clip=None)` | the Generation effect (hero_1): a square with the 7-stop gradient over `item`, the wash sweeps through, the item shows under it (frame 36 small, 56 big; `kind` by height); `rows`: items inside that come in one after another, rising 4 px; `pops`: texts that pop orange, pink, their colour, sharpening; `squares`: `[(dx, dy, w, h, r)]` or items instead of one square; `clip`: an item the squares are cut to. Returns when all has landed |
| `a.generating(status)` · `a.done(status)` | a `p.gen_status` shimmers (every 1.6 s) until `done`: "Generating..." fades, "Done" fades in, the box closes to its width (the star slides toward the side it is placed against) |
| `a.write_code(editor, speeds=((1, 240), (12, 100)), pauses={18: 0.1})` | the AI writes a `p.code_editor` (or `panel.editor`): chunk by chunk, each line's number as it starts, the caret riding the line. Returns the end; `editor.line_done[n]` is when line n is done |
| `a.add_file(tree, "TopBar.tsx")` | a `+file` of a `p.file_tree` arrives: the rows below make room, it slides in from the left |
| `a.beats([...])` · `a.c` | your own keys on the same timeline (section 8) |
| `a.open(coll)` · `a.close(coll)` | unfolds / folds a `p.collapsible` without the cursor (medium, duda) |
| `a.cursor_out(side=None, t=None)` | leaves the frame after its last action, accelerating (nearest side); `t=s`: it creeps where it is until s, then leaves. Long gaps between clicks make it leave and a new cursor come in on its own |
| `a.loop(exit=card)` | clean seam: `exit` (an item that `enter`ed at the start) leaves, everything resets while hidden, 8 still frames. Call last |
| `p.build(tabs=False, duration=None)` | writes `scene.rml`: "State Machine 1" (autoplay) with view model trigger `play` that restarts the timeline; the timeline loops. `tabs=True` (hero tab): plays once, fires `tabChange` at its end, `play` restarts. `duration=s`: exactly s seconds (a hero tab: `tabChange` right at s); without it, 0.5 s after the last action. Anything still moving after s fails the build |

- `where`: `"center"` (default; an input's default is `"field"`), `"remove"` (a tag's x), or `(dx, dy)` from the centre.
- **A click's result** is keyed for you on the press frame: inputs and searches take the focus, a toggle flips, a
  checkbox checks or clears, a radio selects, `tabs.tab(i)` selects its tab, a dropdown opens or closes, a
  collapsible's header folds or unfolds it. Anything else (a menu item that changes a value, a status that turns
  "done") is an `a.set` at the press time `a.click` returns.
- **Positions are measured**: the build lays the scene out with the CLI at the moment of each action (after a removed
  tag, a grown card...) and aims there. Never compute coordinates. `p.point(item, where, t)` / `p.bounds(item, t)`
  give them if you need them (artboard points).
- **Drivers**: each state an action keys is a custom property `drv.<slot>.<prop>` (group "Drivers", under the
  artboard) bound into the component's view model and keyed on the one "Timeline". In the Rive editor they are ordinary keys to adjust.
- On the web (`@rive-app/webgl2@2.45.0`, `autoBind: true`, `stateMachines: "State Machine 1"`): the artboard's view
  model has `play`, `tabChange`, `cursor` and one property per slot (`email/value`, `go/loading`, `bar/trash/hover`).

## 5. Example piece
A sign-up card (`examples/signup/build.py`; it builds, verifies and passes the lints as is):
```python
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
- **Cursor**: enters and leaves off-frame; never appears, vanishes or parks inside the frame. One cursor per task
  (the same cursor goes on to the next step). Waits of ~1.5–2 s go aside (typing pattern); longer, it leaves. It clicks
  a field before typing. A soft "thought" (`hover(hold=)`) only on things that open more options.
- **Every click reacts**: hover ~150 ms before, press on the press frame (0.9 icon buttons, 0.96 wide buttons), and
  the result on the press frame, not after. List rows don't squeeze: their highlight is the reaction.
- **Speed caps** (px per frame at 1920 wide, 60 fps): readable text 30, chips and icons 40, cursor 45. Panels and
  chat content don't slide their full width; they are revealed or enter with a short settle.
- **AI elements breathe**: AI buttons, the AI star, "thinking"/"updating" get the slow animated gradient (curve
  `gradient`, 1.5–2.7 s), and nothing else does. Agent progress is a list that keeps moving: the active step has a
  loader and the AI shimmer, resolves into a drawn check on the loader's last visible frame, the next step enters
  below. `p.ai_status` is the status line with the product's shimmer ("Thinking..." → `done` "Thought for 3s"; or
  `spinner`); `a.generate` is the gradient wash that builds a component, `p.gen_status` the "Generating... / Done"
  status. The step list with drawn checks is not in the library yet: flag it in the brief.
- **Loop seam**: the last frame flows into the first: a hold of >= 8 still frames (`loop()` makes it) or a match
  cut. Spinners and shimmers stop before the seam. A hero tab plays once (`tabs=True`).
- **Figma is the reference, not the limit**: motion may add the states the design implies (hover, press, focus,
  progress) with its own components and colours, never new content. The product decides content and behaviour.
- **Site, not video**: on the site the product window stays still (no camera drift on the UI; a hero's slow drift
  goes only on its background photo, confirmed with Mateus). No zoom into part of the scene, ever. The artboard is
  square-cornered (the page rounds it); no cut-off edge may show.
- **Review** like Mateus does, frame by frame, on the stills of every beat: edges and corners appearing, the
  cursor vanishing, jumps (a pop, a reflow in one frame, a state flashing), a zoom into part of the scene.

Token names (motion-spec/tokens.json, already wired into the actions): curves `duda`, `duda_strong`, `settle`,
`gradient`, `scroll` (long scrolls of readable text, ~1.4 s for ~830 px), `linear` (opacity, spinners, press);
durations `press`, `release`, `fade`, `short`, `medium`, `panel`, `long`, `transition`, `gradient_sweep`,
`read_hold`; stagger `tight`, `list`, `loose`; `state_swap.fade_out_ms` (100); `cursor.*` (move 550–900 ms by
distance, press 0.85 in 3+3 frames, press 5 frames before it stops, hover 150 ms before); `speed_cap_px_per_frame_at_1920`.

## 7. When the build says LINT
- `... peaks at X px/f > cap`: give the move more time or less distance (actions size their own moves).
- `CURSOR1 is parked` / `appears inside the frame`: fewer idle gaps in a visit; let it `cursor_out()` and come back.
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
- After `/new-version`, the old version's scene is kept as `scene.rml.txt` (so Rive doesn't build it).
