"""Render a piece to MP4: every frame of its timeline captured headless by the Rive CLI (frame N is --advance=N+1),
then encoded by ffmpeg (H.264, 60 fps). Works in any folder: it needs only the piece (build.py run once) and this
bundle.

usage: python lib/biblioteca-<v>/scripts/render_mp4.py <piece_dir> <out.mp4> [--size WxH] [--jobs 8]
  --size: the video's size (default: the main artboard's; 2x: --size 2680x1276 for a 1340 x 638 artboard)
  ffmpeg: on PATH, else the one of the imageio-ffmpeg package in the venv.
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # python -I leaves the script's folder out
import scene  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("proj")
    ap.add_argument("out")
    ap.add_argument("--size")
    ap.add_argument("--jobs", type=int, default=8)
    a = ap.parse_args()
    proj, out = os.path.abspath(a.proj), os.path.abspath(a.out)
    _, _, w, h, frames, fps = scene.info(proj)
    if a.size:
        w, h = map(int, a.size.lower().split("x"))
    rive = scene.rive()
    tmp = tempfile.mkdtemp(prefix="rivefr")

    def shot(f):
        subprocess.run([rive, ".", f"--screenshot={tmp}/f{f:05d}.png", f"--advance={f + 1}", f"--viewport={w}x{h}"],
                       cwd=proj, capture_output=True, timeout=120)
        return os.path.exists(f"{tmp}/f{f:05d}.png")

    print(f"capturing {frames} frames at {w}x{h} ({a.jobs} at a time)...")
    with ThreadPoolExecutor(a.jobs) as ex:
        ok = list(ex.map(shot, range(frames)))
    missing = [f for f, k in enumerate(ok) if not k]
    if missing:
        shutil.rmtree(tmp, ignore_errors=True)
        sys.exit(f"{len(missing)} frames failed (first: {missing[0]}); run `rive . --verify` in the piece")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    r = subprocess.run([scene.ffmpeg(), "-y", "-loglevel", "error", "-framerate", str(fps), "-i", f"{tmp}/f%05d.png",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "16", "-movflags", "+faststart", out],
                       capture_output=True, text=True)
    shutil.rmtree(tmp, ignore_errors=True)
    if r.returncode:
        sys.exit("ffmpeg failed:\n" + r.stderr[-1500:])
    print(f"wrote {out} ({frames} frames, {frames / fps:.2f} s, {w}x{h})")


if __name__ == "__main__":
    main()
