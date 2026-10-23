# Setup (for Claude)

Instructions for Claude to set up a Mac for this repo. The person you're helping is probably not technical.

- Before each step, say in one simple sentence what it does and why. Skip steps that are already done.
- Everything installs into the user's home folder. Never use sudo, never install Homebrew, never ask for a password.
  If something seems to need one, stop and explain.
- The user logs in to Figma and Rive themselves, in the browser. Never ask for a password, token or key in the chat.
- Run long installs in the background and tell the user what's happening while they wait.

## 1. Check what's there
```bash
tools/doctor.sh
```
It prints ✓ or ✗ for git, the Rive CLI, the Python environment, ffmpeg and the fonts, then builds the library's
example piece and renders one still. Do only the steps for the ✗ lines, plus steps 7 and 8 (Figma and the browser),
always.

If this folder isn't the project yet (no `tools/doctor.sh`), do step 2 first.

## 2. git and the project
1. Check `xcode-select -p`. If it fails, run `xcode-select --install` and tell the user: "A macOS window will ask to
   install the command line developer tools. Click Install and wait until it finishes (a few minutes)." Wait until
   `xcode-select -p` works. If it asks for an administrator password the user doesn't have, IT has to approve it.
2. Clone the project (it's public, no login needed):
   ```bash
   git clone https://github.com/mateusapra-duda/duda-motion-library.git .
   ```
   If the folder isn't empty, clone into a subfolder `duda-motion-library` instead, and at the end tell the user to
   open that subfolder in Claude.

## 3. Rive CLI
```bash
curl -fsSL https://releases.rive.app/cli/install.sh | sh
```
- It installs to `~/.rive/bin/rive`. Make sure `~/.zshrc` has `export PATH="$HOME/.rive/bin:$PATH"` (add it if it's
  missing).
- Building, checking and rendering need no Rive account. Only `/to-rive` (the `.rev` for the editor) needs
  `rive login`, with a Rive seat; the user does it themselves when they first need it.

## 4. uv (Python manager)
If `uv` isn't on PATH or in `~/.local/bin`:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```
It installs to `~/.local/bin/uv`. In this session, call it by that full path.

## 5. Python environment
```bash
~/.local/bin/uv venv --python 3.14 .venv
```
```bash
~/.local/bin/uv pip install --python .venv/bin/python -r requirements.txt
```
- uv downloads its own Python, so the Mac's Python doesn't matter.
- `imageio-ffmpeg` bundles ffmpeg, so Homebrew isn't needed.
- If `.venv` exists but is broken (for example, copied from another Mac), delete it and create it again.

## 6. Fonts
Nothing to install: Duda Sans and the caret font come with the project (`library/fonts/`). If doctor says they're
missing, the clone is incomplete: run `git pull` (or `git checkout -- library/fonts`).

## 7. Figma
Check whether you have Figma tools in this session (`get_metadata`, `get_design_context`, `get_screenshot`).
- If you don't, tell the user to connect Figma: open the Claude app's settings → **Connectors** → **Figma** →
  **Connect**, approve it in the browser with their **Duda** Figma account (Duda's files don't open from a personal
  account), then start a new session in this folder.
- If you do, run `whoami`. It should show a Duda email. If it shows a personal account, ask them to reconnect with the
  Duda one.
- Figma is only read, never changed.

## 8. Browser and a Duda test site (for use cases)
To build a piece from a use case, Claude walks the flow in the real product.
- Claude uses the user's own Chrome through the **Claude in Chrome** extension, signed in with their Duda account.
  Check it with the Claude in Chrome tools (load the `anthropic-skills:chrome-browser` skill, then list the tabs).
  - If it isn't connected, tell the user to install the extension
    (https://chromewebstore.google.com/detail/fcoeoabgfenejglbffodgkkbkcdhcgfn), open the Claude side panel in
    Chrome, and sign in with the same Claude account as this app.
- Alternative: the Claude app's built-in browser, where the user signs in to Duda themselves. Never ask for or type
  a password.
- The flow is walked in a test site or project, never a live or customer site.

## 9. Web check (optional, for pieces that go on the site)
Plays a `.riv` in the site's runtime, headless (`library/webtest/`). Needs Node.js: if `node --version` fails, skip
this step and say the web check isn't available yet. Otherwise:
```bash
npm install --prefix tools/web playwright@1.62.0
```
```bash
tools/web/node_modules/.bin/playwright install chromium-headless-shell
```

## 10. Rive editor (optional, for hand edits)
`/to-rive` sends the `.rev` to the Rive desktop app through its local connection. If the user wants to adjust pieces
by hand, they install the Rive desktop app (from rive.app) and log in themselves.

## 11. Final check
Run `tools/doctor.sh` again. Every line must be ✓.
- Show the user the test still (`pieces/_doctor/doctor.png`).
- If you cloned the project in this session, tell them to start a new session in the project folder, so the commands
  load.
- End with: "All set. To make a piece, type `/new-motion` followed by the Figma link of a storyboard, or just
  describe the use case in your own words: I'll look at the product and build it."
