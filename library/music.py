"""A piece's soundtrack (v15e): where the track's beats fall in the video, cuts put on them (with an assert), and the
mix that scripts/render_mp4.py puts in the MP4 (music.json, written by `save`).

    from music import Music
    m = Music("music/track.wav", bpm=120, first=0.125, delay=0.2)   # the track's beats at 0.125 + 0.5 k s; it starts
                                                                      # 0.2 s into the video
    t = a.cut(s1, s2, "zoom", at="center", t=m.snap(5.0) - 21 / 60)   # the centred zoom cuts 21 f after its start
    m.on_beat(t)                         # AssertionError (with the nearest beats) when the cut is off the beat
    m.save(HERE)                         # music.json: render_mp4 mixes it in and checks it in the MP4's own audio

Times are the video's, in seconds; `frame`s are the video's at `fps`. A beat is on a cut when it falls within half a
frame of the cut frame's time (frame / fps). `stretch` > 1 plays the track slower, same pitch (ffmpeg atempo): at most
~2 % (LEARNINGS 21), set by `fit` to land one hit on one moment.
"""
import json
import os


class Music:
    def __init__(self, file, bpm=None, first=0.0, delay=0.0, stretch=1.0, fade_out=1.5, fade_in=0.0, fps=60):
        """file: the track (a path from the piece's folder, or absolute); bpm and first (a beat in the track, in its
        own seconds: a downbeat, so every=4 counts bars) make the beat grid; delay: where the track's 0 plays in the
        video (negative: the video starts that far into the track); fade_out / fade_in: seconds at the video's end /
        the track's start."""
        self.file, self.bpm, self.first, self.delay = file, bpm, float(first), float(delay)
        self.stretch, self.fade_out, self.fade_in, self.fps = float(stretch), float(fade_out), float(fade_in), fps
        self.hits = []
        assert 0.98 <= self.stretch <= 1.02, f"stretch {self.stretch}: at most 2 % (a track any slower or faster shows)"

    def at(self, track_t):
        """The video time at which the track's moment `track_t` (its own seconds) plays."""
        return self.delay + track_t * self.stretch

    def beat(self, k):
        """The video time of beat k (beat 0 = `first`; negative ones come before it)."""
        assert self.bpm, "Music(bpm=...) for a beat grid"
        return self.at(self.first + k * 60.0 / self.bpm)

    def _k(self, t, every):
        kf = ((t - self.delay) / self.stretch - self.first) * self.bpm / 60.0
        return int(round(kf / every)) * every

    def snap(self, t, every=1):
        """The beat (every `every` beats: 2 halves, 4 bars from a downbeat `first`) nearest t, as the time of the
        frame it falls on: give it to an action's t (a cut lands its frame on it)."""
        return round(self.beat(self._k(t, every)) * self.fps) / self.fps

    def on_beat(self, t, every=1, what="the cut"):
        """Assert t (a cut's time, as a.cut returns it) is on a beat, within half a frame; returns the beat number."""
        k = self._k(t, every)
        b = self.beat(k)
        f = round(t * self.fps)
        near = sorted({round(self.beat(k + d * every) * self.fps) for d in (-1, 0, 1)})
        assert abs(b - f / self.fps) <= 0.5 / self.fps + 1e-9, (
            f"{what} at frame {f} ({t:.3f} s) is {abs(b - f / self.fps) * 1000:.0f} ms off the beat: the nearest beats "
            f"fall on frames {near} (Music.snap)")
        return k

    def fit(self, track_t, t, max_stretch=0.02):
        """Set `stretch` so the track's moment track_t (a hit) plays at t (the delay stays): the last ~2 % that moving
        the cut can't take. Returns the stretch."""
        s = (t - self.delay) / track_t
        assert abs(s - 1) <= max_stretch + 1e-9, (
            f"the track would play {abs(s - 1) * 100:.1f} % {'slower' if s > 1 else 'faster'} (at most "
            f"{max_stretch * 100:.0f} %): move the cut, or the delay")
        self.stretch = s
        return s

    def hit(self, track_t, t):
        """The track's moment track_t must play at t (a cut): asserted here, and render_mp4 checks it in the MP4's own
        audio (by correlation with the track)."""
        f = round(t * self.fps)
        err = self.at(track_t) - f / self.fps
        assert abs(err) <= 0.5 / self.fps + 1e-9, (
            f"the track's {track_t} s plays {err * 1000:+.0f} ms from frame {f}: move the cut, or Music.fit")
        self.hits.append((float(track_t), f))
        return self

    def frames(self, lo, hi, every=1):
        """The frames of the beats between frames lo and hi (where a cut can go), every `every` beats."""
        k = self._k(lo / self.fps, every) - every
        out = []
        while round(self.beat(k) * self.fps) <= hi:
            if round(self.beat(k) * self.fps) >= lo:
                out.append(round(self.beat(k) * self.fps))
            k += every
        return out

    def spec(self):
        return dict(file=self.file, delay=self.delay, stretch=self.stretch, fade_out=self.fade_out,
                    fade_in=self.fade_in, fps=self.fps, bpm=self.bpm, first=self.first,
                    hits=[list(h) for h in self.hits])

    def save(self, proj):
        """Write <proj>/music.json, which scripts/render_mp4.py mixes into the MP4 (--no-music leaves it out)."""
        path = os.path.join(proj, "music.json")
        src = self.file if os.path.isabs(self.file) else os.path.join(proj, self.file)
        assert os.path.exists(src), f"music: {src} not found"
        with open(path, "w") as fh:
            json.dump(self.spec(), fh, indent=1)
        return path

    def __repr__(self):
        bpm = f", {self.bpm / self.stretch:.2f} bpm" if self.bpm else ""
        return (f"Music({os.path.basename(self.file)} from {self.delay:.4f} s, x{self.stretch:.5f}{bpm}, "
                f"fade out {self.fade_out} s, {len(self.hits)} hit(s))")

