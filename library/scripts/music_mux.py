"""Put a piece's music (music.json, written by the library's Music.save) into an MP4, and check it from the MP4's own
audio (v15e, LEARNINGS 21). render_mp4.py calls it after the video; it also works on its own:

usage: python lib/biblioteca-<v>/scripts/music_mux.py <video.mp4> <music.json> <out.mp4>
       python lib/biblioteca-<v>/scripts/music_mux.py --check <video_with_music.mp4> <music.json>

The mix, in this order (ffmpeg):
  aresample=48000, adelay=<(delay + AAC) / stretch, in samples>, atempo=<1 / stretch>, asetpts=N/SR/TB, apad,
  atrim=<the video's length>, afade (in at the track's start, out at the video's end).
  - the delay goes BEFORE atempo: after it, the delay is lost (and the audio ends 0.17 s short); before it, atempo
    stretches it too, hence / stretch;
  - atempo plays the track early when it slows it (11-13 ms at 1.5-2 % slower, 1-3 ms faster; AAC adds nothing:
    measured with PCM, 2026-11-25): a lead added to the delay, then measured (below) and corrected once when the
    audio sits over 1 ms off (the closer of the two kept);
  - AAC 256k, 48 kHz; the video stream is copied as it is.
The check, from the MP4's audio: the loudness envelope (0.5 ms steps) of the track around a moment, stretched like the
mix, matched (normalised correlation, +-50 ms) against the MP4's around where that moment should play.
  - the offset, at points across the track: how far the audio as a whole sits from where it should (want <= 2 ms);
  - each hit (Music.hit): where the track's moment played against its cut frame (want within half a frame).
ffmpeg: on PATH, else the one of the imageio-ffmpeg package in the venv.
"""
import json
import os
import re
import subprocess
import sys
import tempfile

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # python -I leaves the script's folder out
import scene  # noqa: E402

SR = 48000
RATE = 2000            # envelope samples per second (0.5 ms)


def lead(stretch):
    """atempo's lead, seconds (ffmpeg 8.1, 2026-11-25: -12.9 ms at x1.015, -11.0 at x1.02, -0.9 at x0.99 in PCM;
    AAC the same as PCM). The first guess; put() measures and corrects."""
    return 0.0 if abs(stretch - 1) < 1e-9 else 0.011 if stretch > 1 else 0.001


def track_path(spec, base):
    f = spec["file"]
    return f if os.path.isabs(f) else os.path.join(base, f)


def video_frames(ff, mp4):
    """(frames, fps) of the MP4's video stream, counted (no ffprobe in the imageio build)."""
    r = subprocess.run([ff, "-hide_banner", "-i", mp4, "-map", "0:v:0", "-c", "copy", "-f", "null", "-"],
                       capture_output=True, text=True)
    n = re.findall(r"frame=\s*(\d+)", r.stderr)
    fps = re.search(r"(\d+(?:\.\d+)?) fps", r.stderr)
    assert n and fps, f"no video stream in {mp4}"
    return int(n[-1]), float(fps.group(1))


def chain(spec, dur, comp):
    st, d = spec["stretch"], spec["delay"] + comp
    f = [f"aresample={SR}"]
    if d >= 0:
        f.append(f"adelay=delays={round(d / st * SR)}S:all=1")
    else:                                      # the video starts into the track
        f += [f"atrim=start={-d / st:.6f}", "asetpts=PTS-STARTPTS"]
    if abs(st - 1) > 1e-9:
        f.append(f"atempo={1 / st:.8f}")
    f += [f"asetpts=N/{SR}/TB", "apad", f"atrim=duration={dur:.6f}"]
    if spec.get("fade_in"):
        f.append(f"afade=t=in:st={max(0.0, spec['delay']):.4f}:d={spec['fade_in']}")
    if spec.get("fade_out"):
        f.append(f"afade=t=out:st={dur - spec['fade_out']:.4f}:d={spec['fade_out']}")
    return ",".join(f)


def mux(ff, video, spec, base, out, comp=None):
    comp = lead(spec["stretch"]) if comp is None else comp
    frames, fps = video_frames(ff, video)
    dur = frames / fps
    r = subprocess.run([ff, "-y", "-loglevel", "error", "-i", video, "-i", track_path(spec, base),
                        "-filter_complex", f"[1:a]{chain(spec, dur, comp)}[a]", "-map", "0:v:0", "-map", "[a]",
                        "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-ar", str(SR), "-movflags", "+faststart",
                        out], capture_output=True, text=True)
    if r.returncode:
        sys.exit("ffmpeg (music) failed:\n" + r.stderr[-1500:])
    return dur


def pcm(ff, path, audio_only=True):
    r = subprocess.run([ff, "-v", "error", "-i", path] + (["-map", "0:a:0"] if audio_only else []) +
                       ["-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True)
    assert r.returncode == 0 and r.stdout, f"no audio in {path}"
    return np.frombuffer(r.stdout, dtype=np.float32)


def envelope(x):
    hop = SR // RATE
    n = len(x) // hop
    e = np.abs(x[:n * hop]).reshape(n, hop).mean(1)
    return np.convolve(e, np.ones(4) / 4, "same")          # 2 ms


def locate(env_track, env_mp4, track_t, expect, stretch, half=0.3, search=0.05):
    """Where (video seconds) the track's moment track_t plays in the MP4 (expected at `expect`), and the match's
    correlation; None when the track is near silent there."""
    u = np.arange(-half * stretch, half * stretch, 1.0 / RATE)             # output offsets around the moment
    src = (track_t + u / stretch) * RATE
    if src[0] < 0 or src[-1] >= len(env_track) - 1:
        return None
    w = np.interp(src, np.arange(len(env_track)), env_track)
    if w.std() < 1e-4:
        return None
    w = (w - w.mean()) / w.std()
    best = None
    lags = np.arange(-search, search, 1.0 / RATE)
    cs = []
    for lag in lags:
        i = (expect + lag + u) * RATE
        if i[0] < 0 or i[-1] >= len(env_mp4) - 1:
            cs.append(-1.0)
            continue
        m = np.interp(i, np.arange(len(env_mp4)), env_mp4)
        cs.append(float(np.dot(w, (m - m.mean()) / (m.std() + 1e-12)) / len(w)))
    cs = np.array(cs)
    j = int(np.argmax(cs))
    off = lags[j]
    if 0 < j < len(cs) - 1:                                                  # parabolic refinement
        a, b, c = cs[j - 1], cs[j], cs[j + 1]
        den = a - 2 * b + c
        if den < 0:
            off += 0.5 * (a - c) / den / RATE
    best = (expect + off, float(cs[j]))
    return best


def check(ff, mp4, spec, base, quiet=False):
    """(offset in s, [(track_t, frame, error in s, corr)], fails): the audio's offset and each hit, from the MP4."""
    env_t = envelope(pcm(ff, track_path(spec, base), audio_only=False))
    env_m = envelope(pcm(ff, mp4))
    st, fps = spec["stretch"], spec.get("fps", 60)
    dur = len(env_m) / RATE
    t0 = max(0.0, -spec["delay"] / st) + 0.5
    t1 = min(len(env_t) / RATE, (dur - spec["delay"] - (spec.get("fade_out") or 0)) / st) - 0.5
    offs = []
    for track_t in np.linspace(t0, t1, 9) if t1 > t0 else []:
        r = locate(env_t, env_m, track_t, spec["delay"] + track_t * st, st)
        if r and r[1] > 0.5:
            offs.append(r[0] - (spec["delay"] + track_t * st))
    off = float(np.median(offs)) if offs else float("nan")
    hits, fails = [], []
    for track_t, f in spec.get("hits", []):
        r = locate(env_t, env_m, track_t, spec["delay"] + track_t * st, st)
        if r is None:
            fails.append(f"hit {track_t} s: the track is silent there")
            continue
        err = r[0] - f / fps
        hits.append((track_t, f, err, r[1]))
        if abs(err) > 0.5 / fps:
            fails.append(f"hit {track_t} s plays {err * 1000:+.1f} ms from frame {f} (over half a frame)")
    if not offs:
        fails.append("the track could not be found in the MP4's audio")
    elif abs(off) > 0.002:
        fails.append(f"the audio sits {off * 1000:+.1f} ms from where it should (over 2 ms)")
    if not quiet:
        print(f"music in {os.path.basename(mp4)}: offset {off * 1000:+.1f} ms (median of {len(offs)} points)")
        for track_t, f, err, c in hits:
            print(f"  hit {track_t} s -> frame {f}: {err * 1000:+.1f} ms (corr {c:.2f})")
    return off, hits, fails


def put(ff, video, spec, base, out):
    """Mux and check; when the audio sits over 1 ms off, mux again with atempo's lead corrected by what was measured
    and keep the closer of the two (atempo's shift moves in steps, so a correction can overshoot). Exits on a failed
    check."""
    comp = lead(spec["stretch"])
    mux(ff, video, spec, base, out, comp)
    off = check(ff, out, spec, base, quiet=True)[0]
    if off == off and abs(off) > 0.001:
        alt = out + ".alt.mp4"
        mux(ff, video, spec, base, alt, comp - off)
        off2 = check(ff, alt, spec, base, quiet=True)[0]
        if off2 == off2 and abs(off2) < abs(off):
            os.replace(alt, out)
            print(f"music: the audio sat {off * 1000:+.1f} ms off; muxed again with {(comp - off) * 1000:+.1f} ms of "
                  "lead")
        elif os.path.exists(alt):
            os.remove(alt)
    off, hits, fails = check(ff, out, spec, base)
    if fails:
        sys.exit("music check failed: " + "; ".join(fails))
    return off, hits


def main():
    a = sys.argv[1:]
    ff = scene.ffmpeg()
    if a and a[0] == "--check" and len(a) == 3:
        spec = json.load(open(a[2]))
        _, _, fails = check(ff, a[1], spec, os.path.dirname(os.path.abspath(a[2])))
        sys.exit("FAIL: " + "; ".join(fails) if fails else 0)
    if len(a) != 3:
        sys.exit(__doc__)
    spec = json.load(open(a[1]))
    tmp = None
    if os.path.abspath(a[0]) == os.path.abspath(a[2]):
        tmp = tempfile.mktemp(suffix=".mp4")
        os.replace(a[0], tmp)
    put(ff, tmp or a[0], spec, os.path.dirname(os.path.abspath(a[1])), a[2])
    if tmp:
        os.remove(tmp)
    print(f"wrote {a[2]}")


if __name__ == "__main__":
    main()
