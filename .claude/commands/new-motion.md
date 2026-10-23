---
description: Make a new Duda motion piece from a Figma storyboard or from a product use case, built with the Duda DS component library
argument-hint: <figma link | a use case in your own words> [notes]
---

We are making a new Duda motion piece. A Figma link, or a use case described in plain words, and optionally notes,
from the user:

$ARGUMENTS

- **A Figma link** (a storyboard): go to §2a.
- **A use case and no link** ("a store owner adds a product and publishes"): go to §2b. Claude looks at the real
  product and builds the screens itself; no storyboard is needed.
- **Nothing:** ask, in one message, for either the link to the storyboard (in Figma: right-click the section →
  Copy/Paste as → Copy link to selection) or the use case: what the person does in the product, step by step, and
  who the piece is for. Also ask whether it's for the site, a video, or both.

Talk to the user in their language, in plain words, and say what you're doing while you work. `CLAUDE.md` has the
working rules.

## 0. Ready check
1. `git pull --ff-only` for the latest library and rules. If it fails (offline, local changes), say so in one line.
2. `tools/doctor.sh`. If any line is ✗, follow `SETUP.md` first and come back.

## 1. Read before anything else
- `library/QUICKSTART.md`, all of it. Agents that read the whole page built faster and with fewer tokens than agents
  that skimmed it.
- `CLAUDE.md` again if this session didn't start in this folder.

## 2a. From a Figma storyboard
1. Open the link with the Figma tools and list the frames in order. Each frame is a pose of the piece.
2. Pick a short kebab-case name and create `pieces/<name>/`. If it exists, ask whether to continue it or start anew.
3. Export into `pieces/<name>/figma/`: `frames/` (a PNG per frame at 1x, named by pose), `assets/` (photos and
   avatars at 2–3x), `ctx/` (the design context of the parts you'll build).
4. Save the `get_metadata` dump and run `tools/figma_frames_diff.py` on it: what changes between frames.
5. Write `pieces/<name>/brief.md` (see "The brief" below), then go to §3.
If access fails, the Figma file must be shared with the account connected to Claude, or Figma needs reconnecting
(Settings → Connectors → Figma).

## 2b. From a use case (no storyboard)
1. **Inputs.** Ask only what's missing, in one message:
   - the flow, as the person's steps in order;
   - where it goes: a video (1920×1080 by default) or the site (the section's size), and about how long (a use-case
     video is usually 15–20 s);
   - the demo brand and people. Default: one fictional brand, fictional people with example.com emails. Never a real
     customer.
2. **Look at the product.** Load the `anthropic-skills:chrome-browser` skill and use Claude in Chrome (the user's
   Chrome, signed in to Duda), or the built-in browser. The user signs in themselves; never type a password.
   - Walk the flow in a test site or project, never a live or customer site.
   - Note the real labels, the states between steps and their order. Save a screenshot of each step to
     `pieces/<name>/product/` (`01_<step>.png`...).
   - Test data only: never publish, send an email, invite someone, activate anything live, connect a domain or buy.
     Undo your test edits at the end and say what remains.
   - If the product does something the library can't show yet (see `CLAUDE.md`), note it.
3. **The brief** (see below), with the product screenshots as the reference instead of Figma frames.
4. **Storyboard from stills.** Build each step's screen with the library, still (layout only, no actions yet), and
   render one still per step (`build.py --stills`). Show the user a sheet with each still next to its product
   screenshot. This is the storyboard: wait for their OK, and fix what they point out before animating.
5. Go to §3.

## The brief (`pieces/<name>/brief.md`)
- the request, in the user's words;
- the steps or frames in order (node ids for Figma; screenshot names for the product), and what changes between them;
- size, frame rate (60), where it goes (site: the `MAIN` contract in `CLAUDE.md`; video: MP4), loop or play once;
- which library components each part uses, and what the library lacks and how you'll handle it;
- the open questions.

## 3. Plan in words, then wait
Present, in plain words: the timing (about how long, what happens when), what the cursor does, the AI moments, the
loop seam (or the end, for a hero tab), what isn't in the library and how you'll build it, and the one-line reason
for each motion choice. Ask only what isn't obvious. **Wait for the user's OK before animating.**

## 4. Build (`library/QUICKSTART.md`)
1. `mkdir -p pieces/<name>/lib && cp -R library pieces/<name>/lib/biblioteca-v05` (already done in §2b).
2. Write `pieces/<name>/build.py` from the closest example in `examples/`. Components for everything that animates
   or reacts; photos and avatars as images.
3. Layout first: stills next to the reference (Figma frames or product screenshots, `tools/overlay.py` when the size
   matches); with Figma, fix until the mean diff is ≤ ~12/255, and look at the overlay.
4. The choreography with the actions, in the beat order. Build until there is no `LINT:` line, then
   `rive . --verify` (0 errors).
5. Stills of every key moment (`build.py --stills ...`). Look at them yourself, like a motion designer would. Fix
   anything that pops, jumps, shows an edge or loses the cursor.

## 5. Deliver (version 1 goes in `pieces/<name>/renders/v01/`)
- **Video:** `tools/render_mp4.sh pieces/<name> pieces/<name>/renders/v01/<name>_v01.mp4 '' '' 2` in the background
  (a few minutes), then `.venv/bin/python -I tools/lint_video.py` on the MP4. Open it for the user.
- **Site:** `(cd pieces/<name> && rive . --once)`, then the web check from QUICKSTART §1 (`play` restarts it, the
  loop or `tabChange` works, the states show).
- **Rive editor**, if they want to adjust by hand: `/to-rive <name> v01`.
Then tell the user where the files are, a short summary, what to judge by eye, and that they can ask for changes in
their own words.

## 6. Changes
- Map each note ("the cursor is too fast", "it jumps here") to the actions, the tokens or `motion-spec/MOTION.md`.
- Before changing a version the user has seen: `/new-version <name>`. The next version goes in `renders/v02/`.
- A note that should apply to every piece: write it in the piece's `NOTES.md` and tell the user to send it to Mateus.
