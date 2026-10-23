---
description: Keep the current version's sources before changing a version the user has seen
argument-hint: <piece> [what will change]
---

Piece and, if given, what will change:

$ARGUMENTS

1. **Find the current version:** the highest `pieces/<piece>/renders/vNN/`. None: say no version was delivered yet,
   and stop.
2. **Keep its sources:** copy `build.py`, `scene.rml`, `brief.md` and `NOTES.md` (those that exist) to
   `pieces/<piece>/versions/vNN/`. If that folder already exists, don't overwrite it: say so and stop.
3. **Hand edits:** if the user adjusted vNN in the Rive editor, read those edits through the Rive MCP (read only,
   after checking which file is active) before changing anything, and list what will be carried into the build.
4. **Note it in `brief.md`**, under "Versions": the next version is v(NN+1), with what changes in one line.
5. **Answer** in one line: the next version and what changes.
