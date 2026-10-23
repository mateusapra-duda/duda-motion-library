"""What changes between storyboard frames, from a Figma `get_metadata` dump.

The dump is what the Figma MCP's get_metadata returns for a page or section (the XML text, or the JSON array
[{type, text}] the harness saves when the result is large). Node ids differ between frames, so they are dropped;
numbers are rounded to 0.5 px so float noise doesn't show up as a change.

usage: python figma_frames_diff.py DUMP 01=305:44398 02=305:43518 03=305:45278 ...
       (prints, for each pair of consecutive frames, the layer lines that disappear (-) and appear (+))
"""
import difflib
import json
import re
import sys


def load_lines(path):
    raw = open(path, encoding="utf-8").read()
    try:
        data = json.loads(raw)
        raw = "".join(x.get("text", "") for x in data) if isinstance(data, list) else raw
    except json.JSONDecodeError:
        pass
    return raw.splitlines()


def subtree(lines, node_id):
    start = next(i for i, l in enumerate(lines) if f'id="{node_id}"' in l)
    base = len(lines[start]) - len(lines[start].lstrip())
    out = []
    for l in lines[start + 1:]:
        ind = len(l) - len(l.lstrip())
        if ind <= base:
            break
        if not l.strip().startswith("</"):
            out.append(" " * (ind - base) + normalize(l.strip()))
    return out


def normalize(s):
    s = re.sub(r'id="[^"]*" ', "", s)
    return re.sub(r'="(-?\d+\.\d+(?:e-?\d+)?)"', lambda m: f'="{round(float(m.group(1)) * 2) / 2:g}"', s)


def main():
    lines = load_lines(sys.argv[1])
    frames = [a.split("=", 1) for a in sys.argv[2:]]
    trees = {label: subtree(lines, nid) for label, nid in frames}
    labels = [label for label, _ in frames]
    for a, b in zip(labels, labels[1:]):
        diff = [l for l in difflib.unified_diff(trees[a], trees[b], lineterm="", n=0)
                if l[:1] in "+-" and not l.startswith(("+++", "---"))]
        print(f"===== {a} -> {b}: {len(diff)} linhas mudam")
        for l in diff:
            print(l[:220])


if __name__ == "__main__":
    main()
