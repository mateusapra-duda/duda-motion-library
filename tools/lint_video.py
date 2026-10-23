"""Motion lint on a rendered MP4 (works for any engine: Rive, HTML, After Effects renders).

Checks: pops (one-frame jumps much larger than their neighbours), frozen stretches, loop seam, and, for every
planned match cut, that the motion keeps its direction across the cut (phase correlation on both sides).
usage: python lint_video.py video.mp4 [--cuts project/build/cuts.json] [--holds "0-0.5"] [--freeze 0.5]
"""
import argparse
import json
import re
import subprocess

import numpy as np

import bins

ap = argparse.ArgumentParser()
ap.add_argument("video")
ap.add_argument("--cuts", default="", help="cuts.json written by the build (planned match cuts)")
ap.add_argument("--freeze", type=float, default=0.5, help="seconds without change that count as frozen")
ap.add_argument("--holds", default="", help="planned still ranges in seconds, e.g. 0-0.5,19.6-20.8")
a = ap.parse_args()

FFMPEG = bins.ffmpeg()
info = subprocess.run([FFMPEG, "-hide_banner", "-i", a.video], capture_output=True, text=True).stderr  # no ffprobe needed
m = re.search(r"Video: .*?, (\d+)x(\d+).*?, ([\d.]+) fps", info)
w, h, fps = int(m.group(1)), int(m.group(2)), float(m.group(3))
sw, sh = 480, int(480 * h / w) // 2 * 2
raw = subprocess.run([FFMPEG, "-loglevel", "error", "-i", a.video, "-vf", f"scale={sw}:{sh},format=gray", "-f", "rawvideo", "-"],
                     capture_output=True).stdout
fr = np.frombuffer(raw, np.uint8).reshape(-1, sh, sw).astype(np.float32)
n = len(fr)
d = np.array([np.abs(fr[i + 1] - fr[i]).mean() for i in range(n - 1)])
holds = [tuple(map(float, r.split("-"))) for r in a.holds.split(",") if r]
cuts = json.load(open(a.cuts))["cuts"] if a.cuts else []
src_fps = json.load(open(a.cuts))["fps"] if a.cuts else fps
cut_frames = [round(c["frame"] * fps / src_fps) for c in cuts]


def near_cut(i, tol=3):
    return any(abs(i - cf) <= tol or abs(i - (cf - 1)) <= tol for cf in cut_frames if cf > 0)


print(f"{a.video}: {n} frames @ {fps:g} fps, mean motion {d.mean():.2f}")
# pops: a frame-to-frame change >4x the local median and above an absolute floor (planned cuts excluded)
pops = []
for i in range(len(d)):
    win = np.concatenate([d[max(0, i - 6):i], d[i + 1:i + 7]])
    med = np.median(win) if len(win) else 0
    if d[i] > 2.0 and d[i] > 4 * max(med, 0.3) and not near_cut(i):
        pops.append((i + 1) / fps)
print(f"pops (outside planned cuts): {len(pops)}" + ("" if not pops else "  at " + ", ".join(f"{t:.2f}s" for t in pops[:20])))

# frozen stretches outside planned holds
frozen, start = [], None
for i, v in enumerate(np.append(d, 1e9)):
    if v < 0.01:
        start = i if start is None else start
    else:
        if start is not None and (i - start) / fps >= a.freeze:
            t0, t1 = start / fps, i / fps
            if not any(h0 <= t0 and t1 <= h1 + 0.1 for h0, h1 in holds):
                frozen.append((t0, t1))
        start = None
print(f"frozen > {a.freeze}s (unplanned): {len(frozen)}" + ("" if not frozen else "  " + ", ".join(f"{x:.2f}-{y:.2f}s" for x, y in frozen)))


def shift(p, q):
    """Translation of q relative to p (phase correlation), in pixels of the 480-wide proxy."""
    win = np.outer(np.hanning(p.shape[0]), np.hanning(p.shape[1]))
    A, B = np.fft.fft2((p - p.mean()) * win), np.fft.fft2((q - q.mean()) * win)
    R = np.conj(A) * B
    r = np.abs(np.fft.ifft2(R / (np.abs(R) + 1e-9)))
    y, x = np.unravel_index(np.argmax(r), r.shape)
    return int(x if x < p.shape[1] / 2 else x - p.shape[1]), int(y if y < p.shape[0] / 2 else y - p.shape[0])


# planned match cuts: the motion keeps its direction across the cut
for c, cf in zip(cuts, cut_frames):
    if c["seam"]:
        before, after = shift(fr[-3], fr[-2]), shift(fr[0], fr[1])
    else:
        i = int(np.argmax(d[cf - 3:cf + 3])) + cf - 3  # the actual cut: biggest change near the planned frame
        before, after = shift(fr[i - 2], fr[i - 1]), shift(fr[i + 1], fr[i + 2])
    if c["kind"] in ("up", "down", "left", "right"):
        axis = 1 if c["kind"] in ("up", "down") else 0
        ok = before[axis] * after[axis] > 0
        print(f"match cut {c['from']}->{c['to']} {c['kind']} at {c['time']:.2f}s: shift before {before}, after {after} "
              f"-> {'same direction' if ok else 'DIRECTION CHANGES'}")
    else:
        print(f"match cut {c['from']}->{c['to']} {c['kind']} at {c['time']:.2f}s: zoom (checked by the static lint)")

# loop seam: an ordinary step, or a planned cut
seam = np.abs(fr[0] - fr[-1]).mean()
local = np.median(d[-10:]) if n > 10 else 0
if any(c["seam"] for c in cuts):
    print(f"loop seam: planned match cut (last->first change {seam:.2f})")
else:
    verdict = "OK" if seam <= max(1.0, 3 * local) else "VISIBLE JUMP"
    print(f"loop seam: last->first change {seam:.2f} (neighbouring steps {local:.2f}) -> {verdict}")
