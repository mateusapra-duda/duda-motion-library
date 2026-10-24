# Duda motion library

This repo builds Duda motion pieces natively in Rive, with the Duda Design System rebuilt as Rive components
(`library/`). A piece starts from a Figma storyboard, or from a product use case described in plain words: then
Claude looks at the real product and builds the screens itself, so a product teammate can make a use-case video on
their own. A piece is one short Python file: place components, lay them out, script the cursor
and the states with ready-made actions, build. The output is a `.riv` for the site (state machine + view model), an
MP4, and a `.rev` for hand edits in the Rive editor.

Building with the library is the fastest way we found: in a side-by-side test, the same product-UI piece took a fresh
agent 12 min and 1.4M tokens with the library against 26 min and 2.5M from scratch, at the same quality.

## Who you're working with
Duda teammates: designers, marketers, motion designers. Most aren't programmers.
- Reply in the language they write in, in plain words. Don't show code unless they ask; say what you're doing and
  what they'll see.
- Make the motion decisions yourself from `motion-spec/` and `library/QUICKSTART.md`, and explain each in one line
  when you present a plan.
- They judge by eye. Turn their notes ("too fast", "it jumps") into the rules and tokens.
- If something isn't clear, ask. Do what was asked and offer extras in one line.

## Commands
- `/setup-motion`: installs or repairs what this Mac needs (follows `SETUP.md`).
- `/new-motion <figma link | use case> [notes]`: storyboard (or the real product, for a use case) → brief → stills
  and a plan in words → **waits for an OK** → builds the piece.
- `/new-version <piece>`: keeps the current version's sources before changing a version the user has seen.
- `/to-rive <piece> [vNN]`: exports the `.rev` and opens it in the Rive editor for hand edits.

## Where things are
| path | what |
|---|---|
| `library/QUICKSTART.md` | **the one page a piece needs**: components, props, actions, the example, the motion rules. Read all of it before building |
| `library/README.md`, `library/NOTES.md`, `library/manifest.json` | what the library holds, full property tables and decisions, every property with its kind and default |
| `library/webtest/` | plays a `.riv` in the site's runtime, headless, with scripted steps |
| `motion-spec/MOTION.md`, `motion-spec/tokens.json` | Duda's house motion rules and their tokens. The library's actions already apply them; read MOTION.md when a piece needs something the actions don't cover |
| `examples/` | `signup` (the QUICKSTART example), `page-settings`, `library-reel` (one component, many settings), `site-settings` (a responsive screen driven from the page, no timeline) |
| `tools/` | `doctor.sh` (setup check), `render_mp4.sh`, `lint_video.py`, `overlay.py` (still vs Figma), `figma_frames_diff.py`, `upload_rev.sh` |
| `pieces/<name>/` | one folder per piece made on this Mac (not in git) |

## How a piece is made
1. **Storyboard or use case → `pieces/<name>/brief.md`**: the frames (or, for a use case, the product's steps, with a
   screenshot of each in `product/`) in order, what changes between them (`tools/figma_frames_diff.py` on a
   `get_metadata` dump), the size and where it goes (site or video), the questions. For a use case, the screens are
   built still with the library first and approved as the storyboard.
2. **Plan in words**: timing, what the cursor does, the AI moments, the loop seam. **Wait for the OK.**
3. **Build with the library** (`library/QUICKSTART.md` §1): copy `library/` into the piece as
   `lib/biblioteca-v06`, start `build.py` from the closest example. Everything that animates or reacts is a native
   component; only static images (photos, avatars) are raster.
4. **Layout first**: stills next to the Figma frames (`tools/overlay.py`, mean diff ≤ ~12/255). Look at the overlays
   before saying it matches.
5. **Choreography** with the actions, in this order: camera → cursor → hover and click → content reveals → AI
   gradients and loaders.
6. **Check**: the build's lints clean, `rive . --verify` with 0 errors, stills of every key moment (frame N at 60 fps
   is `--advance=N+1`). Review them like a motion designer: edges and corners appearing, the cursor vanishing, jumps,
   a zoom into part of the scene.
7. **Deliver** what was asked, in `pieces/<name>/renders/vNN/`:
   - site: `rive . --once` → `build/<name>.riv`, then the web check;
   - video: `tools/render_mp4.sh pieces/<name> pieces/<name>/renders/vNN/<name>_vNN.mp4 '' '' 2`, then
     `tools/lint_video.py` on it;
   - Rive editor: `/to-rive`.

## Rules
- Python only through `.venv/bin/python -I`. No sudo, never ask for a password, token or key.
- Never run `rive push`, `--publish` or `rive library publish`: they upload to the user's Rive account.
- Never change Figma. Read it only.
- **Product vs Figma**: content, parts, states, their order and behaviour come from the product. Spacing, font sizes
  and other details come from Figma when the same UI exists in both. If separating them gets complicated, follow the
  product.
- **Polish is allowed, invention isn't**: Duda curves and durations instead of raw CSS transitions, arrive and settle,
  staggers, softer hover and press. Never a feature or state the product doesn't have. Note in the piece's `NOTES.md`
  what is product and what is polish.
- The library doesn't have yet: images and photos, toggles, checkboxes, dropdowns, menus, scrolling lists, the AI
  gradient. If a piece needs one, say so in the plan, build it by hand as simply as the design allows (with `kit`, see
  `library/README.md`, following `motion-spec/MOTION.md`), and list it in the piece's `NOTES.md` as a library
  suggestion.
- **In the product** (use cases): the user signs in themselves; never type a password or create an account. Work in
  a test site or project only, with test data: never publish, send an email, invite someone, activate anything live,
  connect a domain or buy. Undo test edits and say what remains. Demo content uses one fictional brand and fictional
  people (example.com), never a real customer.
- Each piece lives in `pieces/<name>/` (brief, build, renders, versions, NOTES). Never touch another piece.
- `library/`, `motion-spec/`, `tools/` and `examples/` are shared by the team and change only through the repo owner
  (Mateus Aprá). A note that should apply to every piece goes in the piece's `NOTES.md` as a suggestion; tell the user
  to send it to him.
- Long commands (renders, batches) run in the background with a time limit. No open-ended waits: if something takes
  more than ~1 min without an answer, stop and say so.

## Pieces for the Duda site
- Artboard `MAIN` at the storyboard frame's size, 60 fps. `State Machine 1` with autoplay and a view model with
  autoBind: trigger `play` (the page fires it, the piece restarts) and, for a hero tab, `tabChange` (the piece fires
  it at the end; `p.build(tabs=True)`). Each component slot is a view model path the page can set (`email/value`).
- Runtime: `@rive-app/webgl2@2.45.0`. Nested components driven by keys need 2.44.1 or newer with autoBind.
- No enums: an enum starts at its first value and fires what's bound to it at frame 0. The library uses numbers.
- The artboard is square-cornered (the page rounds it). The product UI stays still on the site: no camera drift on
  the UI (a hero's slow drift goes only on a background photo), never a zoom into part of the scene.
- The local build is unsigned. That only matters for Luau scripts (the web runtime refuses unsigned scripts); library
  pieces have none.
- **Web check** (`library/QUICKSTART.md` §1): serve over http (`file://` fails), wait ~2 s for images to decode after
  load. Headless Chrome runs the clock unevenly: its shots prove states, not timing.

## Rive editor
- `.rev` needs `rive login` (a Rive seat). `tools/upload_rev.sh <piece> <vNN>` sends it as a new file to the project
  of the file open in the Rive app (through the editor's local MCP, port 9791). The open file isn't touched.
- With the Rive MCP: only one session writes at a time; check `session_info.activeFileId` before every write; writes
  are live, so read back after each; `focusArtboard` first (`find_objects` only sees the active artboard); look up
  property keys with `query_property_keys`, never guess; `createArtboard` without x/y; one asset per `upload_asset`.
- Hand edits made in the editor: read them through the MCP (read only), turn them into actions or tokens, compare
  frame by frame. Never rebuild a version over someone's edits without comparing first.
- To see how a reference `.rev` was made: `rive create <scratch folder> --from-rev=<file.rev>` gives a readable
  `scene.rml`.
- Before inventing an RML type or property: `rive docs <topic>` and `rive schema <Type>`.
