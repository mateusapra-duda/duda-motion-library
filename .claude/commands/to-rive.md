---
description: Export a piece's .rev and open it as a new file in the Rive editor, for hand edits
argument-hint: <piece> [vNN]
---

Piece and, if given, the version:

$ARGUMENTS

1. **Version:** the one given, or the highest `pieces/<piece>/renders/vNN/`. Create the folder if it doesn't exist.
2. **Clean build:** `.venv/bin/python -I pieces/<piece>/build.py && (cd pieces/<piece> && rive . --verify)`. With a
   `LINT:` line or an error: stop and say why.
3. **The `.rev`** (needs `rive login`; `rive whoami` checks it, and the user logs in themselves):
   `(cd pieces/<piece> && rive . --once --rev=renders/vNN/<piece>_vNN.rev)`. Never `rive push` or `--publish`.
4. **Into the editor:** the Rive desktop app must be open, with any file of the project where the piece should go.
   - `tools/upload_rev.sh <piece> <vNN> --check` first: the MCP answers and shows the open file.
   - Say you're about to write to Rive (only one session writes at a time), then `tools/upload_rev.sh <piece> <vNN>`.
     It arrives as a **new** file; the open one isn't touched.
   - If the script can't reach the app, tell the user to open the Rive app and try again, or to import the `.rev`
     into their Rive project by hand.
5. **Answer:** the new file's name in Rive, where the `.rev` is, that hand edits go in that file, and that the final
   `.riv` comes from the editor (Export for Runtime) into `renders/vNN/`.
