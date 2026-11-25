"""Render a piece to a production MP4: every frame of one round of its timeline captured headless by the Rive CLI, at
2x by default, then H.264 at 60 fps, CRF 12, BT.709 (LEARNINGS 14). Works in any folder: it needs only the piece
(build.py run once) and this bundle.

usage: python lib/biblioteca-<v>/scripts/render_mp4.py <piece_dir> <out.mp4> [--scale 2 | --size WxH] [--jobs 6]
                                                       [--frames A-B] [--crf 12] [--no-sheet]
                                                       [--music music.json | --no-music] [--artboard NAME]
  --scale: the video's size as a multiple of the main artboard's (default 2: 2680x1276 for 1340 x 638); --size WxH
  instead. Any size other than the artboard's renders with --fit=contain (with the CLI's default fit, "layout", the
  artboard is laid out again at the bigger size: the UI goes to the middle and what isn't in the layout stays in a
  corner; lumi-dental-winback v03).
  --artboard NAME (v15e): another artboard of the scene, with its own "Timeline" (a social video's "SOCIAL 1x1" or
  "SOCIAL 4x5", 1080 wide: --scale 1); default rive.yaml's main.
  --frames A-B: only those frames (a test); --jobs: CLI processes at a time, each one build and one GPU context
  (`--commands`) for its share of the frames.
Production rules it follows (2026-11-19, ma-novo v18.6B-v18.19):
  - every frame is taken 1 ms after its time: frame 0 drawn with `advance 0` (or none) is the setup pose, not the
    animation's frame 0, and a hard cut (a hold key) mid-timeline showed one frame late when the time landed a hair
    before it;
  - x264 preset slow, CRF 12, High, yuv420p, tagged BT.709, faststart; exactly one round (-frames:v);
  - a contact sheet of frames read back from the MP4 itself (<out>_sheet.jpg): look at it before delivering;
  - the scene must not change while it renders (a build mid-render mixes versions): it stops if scene.rml changes.
  For the site's file: render from the project whose scene made the delivered .riv.
Music (v15e): when the piece has a music.json (the library's Music.save, in build.py), or with --music <json>, the
track goes in (AAC 256k, 48 kHz) by scripts/music_mux.py: delay before atempo, the AAC lead compensated, and checked
from the MP4's own audio (the offset within 2 ms, each Music.hit within half a frame of its cut); --no-music leaves it
out. A --frames test gets no music.
ffmpeg: on PATH, else the one of the imageio-ffmpeg package in the venv.
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # python -I leaves the script's folder out
import music_mux  # noqa: E402
import scene  # noqa: E402


def digest(proj):
    return hashlib.sha256(open(os.path.join(proj, "scene.rml"), "rb").read()).hexdigest()


def capture(rive, proj, tmp, frames, w, h, fit, artboard=None):
    """One CLI process: build once, then each frame 1 ms past its time (advance 1ms, then whole frames)."""
    cmds = ["advance 1ms"]
    now = 0
    for f in frames:
        if f > now:
            cmds.append(f"advance {f - now}")
            now = f
        cmds.append(f"screenshot {tmp}/f{f:05d}.png")
    cmds.append("quit")
    path = os.path.join(tmp, f"cmds_{frames[0]:05d}.txt")
    open(path, "w").write("\n".join(cmds) + "\n")
    args = [rive, ".", f"--commands={path}", f"--viewport={w}x{h}", "--quiet"]
    if fit:
        args.append(f"--fit={fit}")
    if artboard:
        args.append(f"--artboard={artboard}")
    r = subprocess.run(args, cwd=proj, capture_output=True, text=True, timeout=60 + 4 * len(frames))
    errs = [ln for ln in r.stdout.splitlines() if ln.startswith("err")]
    return [f for f in frames if not os.path.exists(f"{tmp}/f{f:05d}.png")], errs + ([r.stderr[-600:]] if r.returncode
                                                                                     else [])


def sheet(ff, mp4, out, frames, fps, cols=4, n=12):
    """Frames read back from the MP4 (what the viewer gets), with their numbers."""
    from PIL import Image, ImageDraw
    tmp = tempfile.mkdtemp(prefix="mp4sheet")
    picks = sorted({round(i * (frames - 1) / (n - 1)) for i in range(n)})
    ims = []
    for f in picks:
        p = os.path.join(tmp, f"s{f:05d}.png")
        subprocess.run([ff, "-loglevel", "error", "-y", "-i", mp4, "-vf", f"select=eq(n\\,{f})", "-vsync", "0",
                        "-sws_flags", "accurate_rnd+full_chroma_int",   # the default rounding reads white as 253
                        "-frames:v", "1", p], capture_output=True)
        if os.path.exists(p):
            ims.append((f, Image.open(p).convert("RGB")))
    shutil.rmtree(tmp, ignore_errors=True)
    if not ims:
        return None
    w = 480
    h = round(w * ims[0][1].height / ims[0][1].width)
    rows = (len(ims) + cols - 1) // cols
    s = Image.new("RGB", (cols * (w + 8) + 8, rows * (h + 26) + 8), (236, 236, 238))
    d = ImageDraw.Draw(s)
    for i, (f, im) in enumerate(ims):
        x, y = 8 + (i % cols) * (w + 8), 8 + (i // cols) * (h + 26)
        s.paste(im.resize((w, h)), (x, y + 18))
        d.text((x, y + 2), f"frame {f} ({f / fps:.2f} s)", fill=(40, 40, 40))
    s.save(out, quality=88)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("proj")
    ap.add_argument("out")
    ap.add_argument("--scale", type=float, default=2.0)
    ap.add_argument("--size")
    ap.add_argument("--jobs", type=int, default=6)
    ap.add_argument("--frames")
    ap.add_argument("--crf", type=int, default=12)
    ap.add_argument("--no-sheet", action="store_true")
    ap.add_argument("--music")
    ap.add_argument("--no-music", action="store_true")
    ap.add_argument("--artboard")
    a = ap.parse_args()
    proj, out = os.path.abspath(a.proj), os.path.abspath(a.out)
    _, _, aw, ah, frames, fps = scene.info(proj, a.artboard)
    w, h = map(int, a.size.lower().split("x")) if a.size else (round(aw * a.scale), round(ah * a.scale))
    w, h = w + w % 2, h + h % 2               # yuv420p wants even sizes
    fit = None if (w, h) == (aw, ah) else "contain"
    todo = list(range(frames))
    if a.frames:
        lo, hi = (int(x) for x in a.frames.split("-"))
        todo = [f for f in todo if lo <= f <= hi]
    rive, before = scene.rive(), digest(proj)
    tmp = tempfile.mkdtemp(prefix="rivefr")
    jobs = max(1, min(a.jobs, len(todo) // 30 or 1))
    chunks = [todo[i * len(todo) // jobs:(i + 1) * len(todo) // jobs] for i in range(jobs)]
    print(f"capturing {len(todo)} frames at {w}x{h}{' (fit contain)' if fit else ''}, {jobs} CLI process(es)...")
    with ThreadPoolExecutor(jobs) as ex:
        res = list(ex.map(lambda c: capture(rive, proj, tmp, c, w, h, fit, a.artboard), [c for c in chunks if c]))
    missing = sorted(f for m, _ in res for f in m)
    if missing:
        errs = [e for _, es in res for e in es][:5]
        shutil.rmtree(tmp, ignore_errors=True)
        sys.exit(f"{len(missing)} frames failed (first: {missing[0]}): {errs}\nrun `rive . --verify` in the piece")
    if digest(proj) != before:
        shutil.rmtree(tmp, ignore_errors=True)
        sys.exit("scene.rml changed during the render (a build?): the frames mix versions; render again")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    first = todo[0]
    mj = a.music or os.path.join(proj, "music.json")
    music = None if a.no_music or a.frames or not os.path.exists(mj) else json.load(open(mj))
    video = os.path.join(tmp, "video.mp4") if music else out
    ff = scene.ffmpeg()
    r = subprocess.run([ff, "-y", "-loglevel", "error", "-framerate", str(fps), "-start_number", str(first),
                        "-i", f"{tmp}/f%05d.png", "-frames:v", str(len(todo)),
                        "-vf", "scale=out_color_matrix=bt709:out_range=tv,"
                        "setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709:range=tv",
                        "-c:v", "libx264", "-preset", "slow", "-crf", str(a.crf), "-profile:v", "high",
                        "-pix_fmt", "yuv420p", "-color_primaries", "bt709", "-color_trc", "bt709",
                        "-colorspace", "bt709", "-color_range", "tv", "-movflags", "+faststart", video],
                       capture_output=True, text=True)
    if r.returncode:
        shutil.rmtree(tmp, ignore_errors=True)
        sys.exit("ffmpeg failed:\n" + r.stderr[-1500:])
    if music:
        music_mux.put(ff, video, music, os.path.dirname(os.path.abspath(mj)), out)
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"wrote {out} ({len(todo)} frames, {len(todo) / fps:.2f} s, {w}x{h}, CRF {a.crf}, BT.709"
          f"{', music ' + os.path.basename(music['file']) if music else ''})")
    if not a.no_sheet:
        s = sheet(ff, out, os.path.splitext(out)[0] + "_sheet.jpg", len(todo), fps)
        if s:
            print(f"      {s} (frames read back from the MP4: look at it before delivering)")


if __name__ == "__main__":
    main()
