---
description: Make a new Duda motion piece like /new-motion, delivered as a .rev to fine-tune in the Rive editor (for motion designers; needs a Rive account)
argument-hint: <figma link | a use case in your own words> [notes]
---

We are making a new Duda motion piece for a motion designer, who will fine-tune it by hand in the Rive editor. A Figma
link, or a use case described in plain words, and optionally notes, from the user:

$ARGUMENTS

It is the same piece as `/new-motion`: read `.claude/commands/new-motion.md` and follow it with these arguments, from
§0 to §4, then §6 for changes. Only two things are different: the Rive account check below, and the delivery, which
replaces §5.

## Rive account (right after the ready check in §0, before any other work)
The `.rev` needs a signed-in Rive account. Check it with `rive whoami`.
- Signed in: say which account in one line and go on.
- Not signed in: run `rive login` in the background. It opens a page in the browser with a short code, and the user
  approves it there with their own Rive account. Never ask for a password. Go on once `rive whoami` shows the account.
- No Rive account: say that `/new-motion` makes the same piece as an MP4, with no account, and ask which they want.

## Deliver (instead of §5; version 1 goes in `pieces/<name>/renders/v01/`)
1. `(cd pieces/<name> && rive . --rev=renders/v01/<name>_v01.rev)`. Never `rive push` or `--publish`.
2. Tell the user where the `.rev` is and how to open it: import it into their Rive project, or type
   `/to-rive <name> v01` to send it to the open Rive desktop app as a new file. Hand edits go in that file, and the
   final `.riv` for the site comes out of the editor (Export for Runtime).
3. A short summary and what to judge by eye. An MP4 of this version only if they ask: `tools/render_mp4.sh`, as in
   §5 of `new-motion.md`.

For a later version: keep the current one first (§6 of `new-motion.md`). If the user adjusted it in the Rive editor,
read those edits (Rive MCP, read only, after checking which file is active) and carry them into the build before
changing anything. Then the same delivery in `renders/vNN/`.
