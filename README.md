# Duda motion library

Duda motion pieces built natively in Rive, by Claude, from a Figma storyboard or just a product use case described
in your own words. The Duda Design System is rebuilt here
as Rive components with every state built in (hover, press, focus, typing, loading, success…), so a new screen is
assembled from the same parts instead of being drawn again. The motion follows Duda's house rules.

**Why:** the same product-UI piece took a fresh AI agent 12 min and 1.4M tokens with the library, against 26 min and
2.5M from scratch, at the same quality. See the demo page:
[Half the time. Half the tokens.](https://claude.ai/artifact/Jjg1uVh2HzaFVAxs88GWtm)

## First time on this Mac
In the Claude desktop app, open **Code**, choose an empty folder, and paste:

```
Set up this computer so I can make Duda motion pieces:
1. Download github.com/mateusapra-duda/duda-motion-library into this folder.
2. Then follow the SETUP.md file inside it.
Explain each step in simple terms before running it, and tell me if I need to restart the session.
```

Already have the folder? Type `/setup-motion` to check or repair it.

## Every new piece
```
/new-motion <figma link> [what it's for]
/new-motion <a use case, e.g. "a store owner adds a product and publishes the store">
```
With a Figma link, Claude follows the storyboard. With a use case, it walks the flow in the real product (in a test
site, in your Chrome, signed in with your Duda account), builds the screens with the library and shows you a still of
each step to approve. Either way it proposes the timing in words and waits for your OK, then builds the piece, checks
it frame by frame and delivers it in `pieces/<name>/renders/v01/`: an MP4, a `.riv` for the site, or both. To change
something, describe it in your own words.

- `/new-version <piece>`: keeps the current version before changing one you've already seen.
- `/to-rive <piece>`: opens the piece in the Rive editor as a new file, to adjust by hand (needs a Rive seat).

## What's inside
| folder | what |
|---|---|
| `library/` | the Duda DS as Rive components (24: buttons, inputs, tabs, lists, menus, the AI status, the AI chat panel, the floating bar, the cursor; 50 icons), the Vibe editor's shells and hero parts (chat, Quick Edits, Code tab, Generation effect) and the choreography actions. `QUICKSTART.md` is the page Claude reads |
| `motion-spec/` | Duda's house motion rules (`MOTION.md`) and their tokens (`tokens.json`) |
| `examples/` | finished pieces to start from |
| `tools/` | setup check, MP4 render and lint, still-vs-Figma overlay, upload to the Rive editor |
| `pieces/` | the pieces you make (they stay on your Mac) |

Questions, or a rule that should change for everyone: Mateus Aprá, motion design.
