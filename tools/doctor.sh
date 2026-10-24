#!/usr/bin/env bash
# Check that this Mac can build Duda motion pieces with the library. One line per check; exit 1 if anything is missing.
# The last check builds the library's example piece (examples/signup) in pieces/_doctor and renders one still.
# usage: tools/doctor.sh
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PY="$ROOT/.venv/bin/python"
FAIL=0
ok()  { echo "✓ $1"; }
bad() { echo "✗ $1"; FAIL=1; }

if git --version >/dev/null 2>&1; then ok "git $(git --version | awk '{print $3}')"
else bad "git: missing (SETUP.md step 2)"; fi

RIVE="$(command -v rive || echo "$HOME/.rive/bin/rive")"
if [ -x "$RIVE" ]; then ok "Rive CLI $("$RIVE" --version 2>/dev/null | awk '{print $NF}')"
else bad "Rive CLI: missing (SETUP.md step 3)"; fi

if [ -x "$PY" ] && "$PY" -I -c "import PIL, numpy, yaml, fontTools, imageio_ffmpeg" 2>/dev/null; then
  ok "Python $("$PY" -c 'import platform; print(platform.python_version())') + packages (.venv)"
else bad "Python venv or packages: missing (SETUP.md step 5)"; fi

FFMPEG="$("$PY" -I "$ROOT/tools/bins.py" ffmpeg 2>/dev/null)"
if [ -n "$FFMPEG" ] && "$FFMPEG" -hide_banner -encoders 2>/dev/null | grep -q libx264; then ok "ffmpeg $("$FFMPEG" -version | awk 'NR==1{print $3}')"
else bad "ffmpeg: missing (SETUP.md step 5)"; fi

if [ -f "$ROOT/library/fonts/LabelSansVF.ttf" ] && [ -f "$ROOT/library/fonts/DudaSansCaret.ttf" ]; then ok "Duda Sans fonts (library/fonts)"
else bad "Duda Sans fonts: missing in library/fonts (SETUP.md step 6)"; fi

if [ "$FAIL" = 0 ]; then
  D="$ROOT/pieces/_doctor"
  rm -rf "$D"; mkdir -p "$D/lib"
  cp -R "$ROOT/library" "$D/lib/biblioteca-v06"
  cp "$ROOT/examples/signup/build.py" "$D/build.py"
  if ! "$PY" -I "$D/build.py" >"$D/build.log" 2>&1; then bad "example build failed: see pieces/_doctor/build.log"
  elif ! ( cd "$D" && "$RIVE" . --verify >"$D/verify.log" 2>&1 ); then bad "rive --verify failed: see pieces/_doctor/verify.log"
  else
    ( cd "$D" && "$RIVE" . --screenshot="$D/doctor.png" --advance=301 --viewport=1340x638 --fit=contain >/dev/null 2>&1 )
    if [ -f "$D/doctor.png" ]; then ok "example piece builds, verifies and renders: pieces/_doctor/doctor.png"
    else bad "test render failed: run \`rive . --screenshot\` in pieces/_doctor to see why"; fi
  fi
fi
exit "$FAIL"
