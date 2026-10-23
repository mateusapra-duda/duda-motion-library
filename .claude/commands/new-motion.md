---
description: Make a new Duda motion piece from a Figma storyboard, built with the Duda DS component library
argument-hint: <figma link> [notes]
---

We are making a new Duda motion piece. Figma link, and optionally notes, from the user:

$ARGUMENTS

If there is no Figma link above, ask for the link to the section or frame that holds the storyboard (in Figma:
right-click it → Copy/Paste as → Copy link to selection), and what the piece is for (the site, a video, both).

Talk to the user in their language, in plain words, and say what you're doing while you work. `CLAUDE.md` has the
working rules.

## 0. Ready check
1. `git pull --ff-only` for the latest library and rules. If it fails (offline, local changes), say so in one line.
2. `tools/doctor.sh`. If any line is ✗, follow `SETUP.md` first and come back.

## 1. Read before anything else
- `library/QUICKSTART.md`, all of it. Agents that read the whole page built faster and with fewer tokens than agents
  that skimmed it.
- `CLAUDE.md` again if this session didn't start in this folder.

## 2. Storyboard → brief
1. Open the link with the Figma tools and list the frames in order. Each frame is a pose of the piece.
2. Pick a short kebab-case name and create `pieces/<name>/`. If it exists, ask whether to continue it or start anew.
3. Export into `pieces/<name>/figma/`: `frames/` (a PNG per frame at 1x, named by pose), `assets/` (photos and
   avatars at 2–3x), `ctx/` (the design context of the parts you'll build).
4. Save the `get_metadata` dump and run `tools/figma_frames_diff.py` on it: what changes between frames.
5. Write `pieces/<name>/brief.md`:
   - the request, in the user's words;
   - the frames in order, with node ids, and what changes between them;
   - size, frame rate (60), where it goes (site: the `MAIN` contract in `CLAUDE.md`; video: MP4), loop or play once;
   - which library components each part uses, and anything the library lacks (ask before hand-building it);
   - the open questions.
If access fails, the Figma file must be shared with the account connected to Claude, or Figma needs reconnecting
(Settings → Connectors → Figma).

## 3. Plan in words, then wait
Present, in plain words: the timing (about how long, what happens when), what the cursor does, the AI moments, the
loop seam (or the end, for a hero tab), and the one-line reason for each motion choice. Ask only what isn't obvious.
**Wait for the user's OK before building.**

## 4. Build (`library/QUICKSTART.md`)
1. `mkdir -p pieces/<name>/lib && cp -R library pieces/<name>/lib/biblioteca-v02`.
2. Write `pieces/<name>/build.py` from the closest example in `examples/`. Components for everything that animates
   or reacts; photos and avatars as images.
3. Layout first: stills of the first frame next to the Figma frames (`tools/overlay.py`); fix until the mean diff is
   ≤ ~12/255, and look at the overlay.
4. The choreography with the actions, in the beat order. Build until there is no `LINT:` line, then
   `rive . --verify` (0 errors).
5. Stills of every key moment (`build.py --stills ...`). Look at them yourself, like a motion designer would. Fix
   anything that pops, jumps, shows an edge or loses the cursor.

## 5. Deliver (version 1 goes in `pieces/<name>/renders/v01/`)
- **Site:** `(cd pieces/<name> && rive . --once)`, then the web check from QUICKSTART §1 (`play` restarts it, the
  loop or `tabChange` works, the states show).
- **Video:** `tools/render_mp4.sh pieces/<name> pieces/<name>/renders/v01/<name>_v01.mp4 '' '' 2` in the background
  (a few minutes), then `.venv/bin/python -I tools/lint_video.py` on the MP4. Open it for the user.
- **Rive editor**, if they want to adjust by hand: `/to-rive <name> v01`.
Then tell the user where the files are, a short summary, what to judge by eye, and that they can ask for changes in
their own words.

## 6. Changes
- Map each note ("the cursor is too fast", "it jumps here") to the actions, the tokens or `motion-spec/MOTION.md`.
- Before changing a version the user has seen: `/new-version <name>`. The next version goes in `renders/v02/`.
- A note that should apply to every piece: write it in the piece's `NOTES.md` and tell the user to send it to Mateus.
