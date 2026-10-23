#!/bin/zsh
# Upload pieces/<piece>/renders/<vNN>/<piece>_<vNN>.rev to the Rive editor as a NEW file in the project of the file
# that is open, through the editor's local MCP (the Rive desktop app must be open). The open file is not touched.
# The editor is sandboxed and can't read this folder, so the file goes as a data URI.
# usage: tools/upload_rev.sh <piece> <vNN> [--check]      --check: only tests that the MCP answers and the .rev exists
set -euo pipefail
ROOT="${0:A:h:h}"
URL="http://127.0.0.1:9791/mcp"
piece="${1:-}"; ver="${2:-}"; mode="${3:-}"
[[ "$piece" =~ '^[a-z0-9-]+$' ]] || { echo "usage: tools/upload_rev.sh <piece> <vNN> [--check]" >&2; exit 2; }
[[ "$ver" =~ '^v[0-9]+$' ]] || { echo "bad version: '$ver' (e.g. v01)" >&2; exit 2; }
[[ -z "$mode" || "$mode" == "--check" ]] || { echo "unknown option: $mode" >&2; exit 2; }
FILE="$ROOT/pieces/$piece/renders/$ver/${piece}_${ver}.rev"
[[ -f "$FILE" ]] || { echo "not found: $FILE" >&2; exit 1; }

HDR=(-H 'Content-Type: application/json' -H 'Accept: application/json, text/event-stream')
SID=$(curl -s -i --max-time 10 "$URL" "${HDR[@]}" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-11-25","capabilities":{},"clientInfo":{"name":"upload-rev","version":"1"}}}' \
  | tr -d '\r' | sed -n 's/^[Mm]cp-[Ss]ession-[Ii]d: //p') || true
[[ -n "$SID" ]] || { echo "the Rive editor's MCP didn't answer at $URL (is the Rive app open?)" >&2; exit 1; }

info() {  # session_info (read only): the file open in the editor, to check before and after
  curl -s --max-time 15 "$URL" "${HDR[@]}" -H "mcp-session-id: $SID" \
    -d '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"session_info","arguments":{}}}' | head -c 2000
  echo
}

if [[ "$mode" == "--check" ]]; then
  echo "ok: the Rive MCP answered and the .rev exists ($FILE, $(stat -f%z "$FILE") bytes). Nothing was sent."
  echo "session_info:"; info
  exit 0
fi

echo "session_info before:"; info
CALL=$(mktemp -t upload-rev)
trap 'rm -f "$CALL"' EXIT
printf '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"upload_rev","arguments":{"file":"data:application/octet-stream;name=%s;base64,%s","target":"current_project"}}}' \
  "$(basename "$FILE")" "$(base64 -i "$FILE" | tr -d '\n')" > "$CALL"
curl -s --max-time 180 "$URL" "${HDR[@]}" -H "mcp-session-id: $SID" --data-binary @"$CALL" | head -c 4000
echo
echo "session_info after:"; info
