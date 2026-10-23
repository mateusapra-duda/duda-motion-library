#!/usr/bin/env bash
# Render a piece to MP4 by capturing every frame headless with the Rive CLI (frame N = --advance N+1).
# usage: tools/render_mp4.sh <piece_dir> <out.mp4> [width] [height] [scale=1] [jobs=8]
#   width/height default to the main artboard's size (rive.yaml `main:`); scale 2 renders at 2x for crisp text.
#   The length is the main artboard's "Timeline" (a library piece), else its first timeline.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PY="$ROOT/.venv/bin/python"
RIVE="$("$PY" "$ROOT/tools/bins.py" rive)"
FFMPEG="$("$PY" "$ROOT/tools/bins.py" ffmpeg)"
PROJ="$(cd "$1" && pwd)"; OUT="$2"
read -r AW AH FRAMES < <("$PY" -I - "$PROJ" <<'PY'
import re, sys
proj = sys.argv[1]
main = re.search(r'^main:\s*"?([^"\n]+)"?', open(f"{proj}/rive.yaml").read(), re.M).group(1).strip()
s = open(f"{proj}/scene.rml").read()
art = s[re.search(r'<Artboard[^>]*name="%s"' % re.escape(main), s).start():]
w = re.search(r'width="([\d.]+)"', art).group(1); h = re.search(r'height="([\d.]+)"', art).group(1)
end = art.find("</Artboard>")
anims = re.findall(r'<LinearAnimation[^>]*', art[:end])
pick = next((a for a in anims if 'name="Timeline"' in a), anims[0] if anims else "")
m = re.search(r'duration="(\d+)"', pick)
print(round(float(w)), round(float(h)), m.group(1) if m else 0)
PY
)
[ "$FRAMES" -gt 0 ] || { echo "no timeline on the main artboard: nothing to render" >&2; exit 1; }
SCALE="${5:-1}"; JOBS="${6:-8}"
W="${3:-$((AW * SCALE))}"; H="${4:-$((AH * SCALE))}"
mkdir -p "$(dirname "$OUT")"
TMP=$(mktemp -d "${TMPDIR:-/tmp}/rivefr.XXXX")
shot() {  # render the frames listed on stdin, in parallel; a frame that fails is simply missing afterwards
  xargs -P "$JOBS" -I{} sh -c 'cd "$0" && "$2" . --screenshot="$1/f$(printf %05d {}).png" --advance=$(({}+1)) --viewport='"${W}x${H}"' --fit=contain >/dev/null 2>&1' "$PROJ" "$TMP" "$RIVE" || true
}
seq 0 $((FRAMES-1)) | shot
for try in 1 2 3; do  # the CLI occasionally crashes on a frame: render the missing ones again
  MISSING=$(seq 0 $((FRAMES-1)) | while read f; do [ -f "$TMP/f$(printf %05d "$f").png" ] || echo "$f"; done)
  [ -z "$MISSING" ] && break
  echo "re-rendering $(echo "$MISSING" | wc -l | tr -d ' ') missing frame(s), try $try"
  echo "$MISSING" | shot
done
"$FFMPEG" -y -loglevel error -framerate 60 -pattern_type glob -i "$TMP/f*.png" -c:v libx264 -preset slow -crf 16 -pix_fmt yuv420p -movflags +faststart "$OUT"
echo "frames: $(ls "$TMP" | wc -l | tr -d ' ')/$FRAMES -> $OUT (60 fps, ${W}x${H})"
rm -rf "$TMP"
