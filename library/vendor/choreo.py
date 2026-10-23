"""beats.yaml + motion-spec/tokens.json  ->  one RML LinearAnimation ("ANIM_MAIN").

The beat sheet says *what* moves *when*, using token names; this file decides the keyframes, so the
house rules hold by construction:
  - every segment's ease sits on its first keyframe, every cubic has its interpolator
  - moves start from the value the property actually has at that moment (no jumps)
  - cursors enter and leave off-frame on a curved Follow Path; they slow down at pass points but only stop to click
  - transitions are match cuts: exit accelerating (1,0,1,1) | hard cut | entry decelerating in the same direction,
    with the entry's first-frame speed sized from the exit's last frames
  - every scene camera drifts, so the frame is never fully still
  - every track ends where it started (seamless loop): tracks of a scene are reset while that scene is hidden
Then it lints the result in screen space (speed caps, parked cursors, match-cut direction and speed ratio,
never-static, loop) and writes build/cuts.json for the video lint.
"""
import copy
import json
import math
import os
import random

import yaml

from cursorpath import Visit
from ease import cubic_bezier, cubic_value
from rml import El
from rive_schema import load

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMA = load()
TOKENS = json.load(open(os.path.join(HERE, "..", "motion-spec", "tokens.json")))
FPS = TOKENS["fps"]
OUT_SCALE = TOKENS["canvas"]["output_scale"]
W, H = TOKENS["canvas"]["design"]
REF_SCALE = TOKENS["canvas"]["output_scale"]  # px values in tokens are measured on the 680-wide reference frame
DPX = 1.0   # reference-frame px -> this project's design px (so tokens keep their size on the output)
PT = dict(TOKENS, dpx=1.0)  # tokens as this project sees them (canvas + dpx)


def configure(canvas=None):
    """Per-project canvas (beats.yaml `canvas: {design: [w, h], output: [w, h]}`); without it, tokens.json's
    reference canvas (video 1: 680x480 design shown at 1920x1356)."""
    global OUT_SCALE, W, H, DPX, PT
    PT = copy.deepcopy(TOKENS)
    if canvas:
        dw, dh = canvas["design"]
        ow, oh = canvas.get("output", canvas["design"])
        PT["canvas"] = {"design": [dw, dh], "output": [ow, oh], "output_scale": ow / dw}
    OUT_SCALE = PT["canvas"]["output_scale"]
    W, H = PT["canvas"]["design"]
    DPX = REF_SCALE / OUT_SCALE
    PT["dpx"] = DPX
    return PT

KF_TYPE = {"double": "KeyFrameDouble", "Color": "KeyFrameColor", "String": "KeyFrameString", "bool": "KeyFrameBool",
           "uint": "KeyFrameUint", "uint8": "KeyFrameUint", "Id": "KeyFrameId"}
DEFAULTS = {"opacity": 1.0, "scaleX": 1.0, "scaleY": 1.0, "rotation": 0.0, "x": 0.0, "y": 0.0, "text": "",
            "start": 0.0, "end": 0.0, "offset": 0.0, "distance": 0.0}


def ease_curve(name):
    if isinstance(name, (list, tuple)):
        return tuple(name)
    if name in ("linear", "hold"):
        return name
    return tuple(TOKENS["ease"][name]["bezier"])


def frame(t):
    return int(round(t * FPS))


def progress(e, p, v0=0.0, v1=1.0):
    if e == "linear":
        return p
    if isinstance(e, tuple) and e and e[0] == "value":
        return cubic_value(e[1], e[2], e[3], e[4], v0, v1)(p)
    return cubic_bezier(*e)(p)


class Track:
    def __init__(self, el, prop, key, ptype, v0):
        self.el, self.prop, self.key, self.ptype = el, prop, key, ptype
        self.keys = [{"f": 0, "v": v0, "ease": "hold"}]

    def value_at(self, f):
        prev = self.keys[0]
        for k in self.keys:
            if k["f"] > f:
                if prev["ease"] == "hold" or prev["f"] == f or self.ptype != "double":
                    return prev["v"]
                p = (f - prev["f"]) / (k["f"] - prev["f"])
                return prev["v"] + (k["v"] - prev["v"]) * progress(prev["ease"], p, prev["v"], k["v"])
            prev = k
        return prev["v"]

    def sample(self, n):
        return [self.value_at(f) for f in range(n + 1)]

    def _check_free(self, f0, f1, what):
        for i, k in enumerate(self.keys):
            if f0 < k["f"] < f1:
                raise ValueError(f"{self.el.name}.{self.prop}: {what} at f{f0}-f{f1} overlaps key at f{k['f']}")
            if k["f"] <= f0 and k["ease"] != "hold" and i + 1 < len(self.keys) and self.keys[i + 1]["f"] > f0:
                raise ValueError(f"{self.el.name}.{self.prop}: {what} at f{f0} starts inside a running move (f{k['f']})")

    def _upsert(self, f, v, ease):
        for k in self.keys:
            if k["f"] == f:
                k.update({"v": v, "ease": ease})
                return
        self.keys.append({"f": f, "v": v, "ease": ease})
        self.keys.sort(key=lambda k: k["f"])

    def set(self, f, v):
        self._check_free(f, f + 1, "set")
        self._upsert(f, v, "hold")

    def move(self, f0, f1, v1, ease):
        if f1 <= f0:
            return self.set(f0, v1)
        self._check_free(f0, f1, "move")
        v0 = self.value_at(f0)
        self._upsert(f0, v0, ease)
        self._upsert(f1, v1, "hold")


class Choreo:
    def __init__(self, artboard, by, duration):
        self.by, self.tracks = by, {}
        self.duration = duration
        self.F = frame(duration)
        self.log, self.cuts, self.visits, self.cut_entries = [], [], {}, set()
        self.resolves = []
        self.parent = {}

        def walk(el):
            for c in el.children:
                if isinstance(c, El):
                    self.parent[id(c)] = el
                    walk(c)
        walk(artboard)
        self.artboard = artboard
        self._samples = None

    # ------------------------------------------------------------ tracks
    def track(self, name, prop):
        k = (name, prop)
        if k in self.tracks:
            return self.tracks[k]
        el = self.by[name]
        typedef = SCHEMA["types"].get(el.tag, {})
        if prop not in typedef:
            raise KeyError(f"{el.tag} {name!r} has no property {prop!r}")
        key = typedef[prop]
        ptype = SCHEMA["keys"][str(key)]["type"]
        v = el.attrs.get(prop)
        if v is None:
            v = DEFAULTS.get(prop, 0.0)
        if ptype == "double":
            v = float(v)
        self.tracks[k] = Track(el, prop, key, ptype, v)
        return self.tracks[k]

    def base(self, name, prop):
        v = self.by[name].attrs.get(prop)
        return float(v) if isinstance(v, (int, float)) else (v if v is not None else DEFAULTS.get(prop, 0.0))

    def now(self, name, prop, t):
        return self.track(name, prop).value_at(frame(t))

    # ------------------------------------------------------------ primitives
    def set(self, t, target, prop, value):
        self.track(target, prop).set(frame(t), value)

    def move(self, t, target, prop, to, dur, ease="duda"):
        self.track(target, prop).move(frame(t), frame(t + dur), to, ease_curve(ease))

    # ------------------------------------------------------------ composites
    def fade(self, t, target, to, dur=None):
        self.move(t, target, "opacity", to, dur if dur is not None else TOKENS["duration"]["fade"] / 1000, "linear")

    def enter(self, t, target, dx=0.0, dy=None, dur=0.6, ease="settle", fade=None):
        """Appear while arriving: the start is invisible, so the 'settle' curve is allowed here."""
        dy = 6.0 * DPX if dy is None else dy
        if dy:
            y0 = self.base(target, "y")
            self.set(t, target, "y", y0 + dy)
            self.move(t + 1 / FPS, target, "y", y0, dur, ease)
        if dx:
            x0 = self.base(target, "x")
            self.set(t, target, "x", x0 + dx)
            self.move(t + 1 / FPS, target, "x", x0, dur, ease)
        self.fade(t, target, 1.0, fade)

    def words(self, t, prefix, kind="title", step=None, blur=None, dy=None, dur=None):
        """The closing line, word by word (tokens closing_words): each word `<prefix>W<i>` (rvbuild Video.words) fades
        in, rises and sharpens from a light blur, `step` s after the one before. Hidden and blurred from frame 0."""
        tok = TOKENS["closing_words"]
        step = tok["stagger_ms"][kind] / 1000 if step is None else step
        blur = round(tok["blur_px"][kind] * DPX, 3) if blur is None else blur
        dy = round(tok["rise_px"] * DPX, 3) if dy is None else dy
        dur = tok["sharpen_ms"] / 1000 if dur is None else dur
        n = 0
        while f"{prefix}W{n}" in self.by:
            w, tw = f"{prefix}W{n}", t + n * step
            self.track(w, "opacity").keys[0]["v"] = 0.0
            self.track(f"{w}.blur", "strength").keys[0]["v"] = blur
            self.enter(tw, w, dy=dy)
            self.move(tw, f"{w}.blur", "strength", 0.0, dur, tok["ease"])
            n += 1
        if n == 0:
            raise ValueError(f"words: no {prefix}W0 in the scene (build the line with Video.words)")
        self.log.append(f"words {prefix}: {n} words from {t:.2f}s, every {step * 1000:.0f} ms, all sharp by "
                        f"{t + (n - 1) * step + dur:.2f}s")

    def exit(self, t, target, dx=0.0, dy=None, dur=0.333, fade=None):
        dy = -6.0 * DPX if dy is None else dy
        if dy:
            self.move(t, target, "y", self.now(target, "y", t) + dy, dur, "duda")
        if dx:
            self.move(t, target, "x", self.now(target, "x", t) + dx, dur, "duda")
        self.fade(t, target, 0.0, fade)

    def pop(self, t, target, s0=0.94, dur=0.5):
        s1 = self.base(target, "scaleX")
        for p in ("scaleX", "scaleY"):
            self.set(t, target, p, s1 * s0)
            self.move(t + 1 / FPS, target, p, s1, dur, "settle")
        self.fade(t, target, 1.0, 0.1)

    def click(self, t, name):
        c = TOKENS["cursor"]
        s = self.base(name, "scaleX")
        down, up = c["press_frames"] / FPS, c["release_frames"] / FPS
        for p in ("scaleX", "scaleY"):
            self.move(t, name, p, s * c["press_scale"], down, "linear")
            self.move(t + down, name, p, s, up, "linear")
        return t + down + up

    def press(self, t, target, scale=0.9):
        """A button reacting to the cursor's press: squeezes on the press frames, springs back on release."""
        c = TOKENS["cursor"]
        s = self.base(target, "scaleX")
        down, up = c["press_frames"] / FPS, (c["release_frames"] + 3) / FPS
        for p in ("scaleX", "scaleY"):
            self.move(t, target, p, s * scale, down, "linear")
            self.move(t + down, target, p, s, up, "duda")

    def type(self, t, target, text, cps=38, seed=7, until=None):
        """Human-ish typing: per-character jitter, small pauses after punctuation.
        With `until`, the speed is chosen so the last character lands at that time (e.g. as the cursor comes back)."""
        rnd = random.Random(seed)
        jit = [rnd.uniform(0.6, 1.4) for _ in text]
        pauses = 0.10 * sum(ch in ",.:;" for ch in text)
        if until is not None:
            cps = sum(jit) / max(until - t - pauses, 0.1)
            self.log.append(f"typing at {cps:.0f} chars/s to finish at {until:.2f}s")
        tr = self.track(target, "text")
        cur = t
        for i in range(1, len(text) + 1):
            ch = text[i - 1]
            cur += (1 / cps) * jit[i - 1]
            if ch in ",.:;":
                cur += 0.10
            tr.set(frame(cur), text[:i])
        return cur

    def resolve(self, t, spin, check, live=None, done=None):
        """A loader turns into a check (tokens state_swap): the loader fades out, and the check starts drawing on the
        loader's last visible frame (never both on screen); the label swaps from shimmering to solid at that moment."""
        sw = TOKENS["state_swap"]
        fade = sw["fade_out_ms"] / 1000
        self.fade(t, spin, 0.0, fade)
        start = (frame(t + fade) - 2) / FPS  # the check's first drawn frame = the loader's last visible frame
        self.move(start, check, "end", 1.0, sw["check_draw"]["ms"] / 1000, sw["check_draw"]["ease"])
        if live:
            self.fade(start, live, 0.0, 0.15)
        if done:
            self.fade(start, done, 1.0, 0.15)
        self.resolves.append((spin, check))

    def spin(self, t0, t1, target, period=0.8):
        turns = (t1 - t0) / period
        r0 = self.now(target, "rotation", t0)
        self.move(t0, target, "rotation", r0 + turns * 2 * math.pi, t1 - t0, "linear")

    def sweep(self, t0, t1, grad, width, period, ease="gradient"):
        """Gradient sweep: start/end X travel one width per period (AI shimmer)."""
        t = t0
        while t + period <= t1 + 1e-6:
            self.set(t, grad, "startX", -width)
            self.set(t, grad, "endX", 0.0)
            self.move(t + 1 / FPS, grad, "startX", width, period - 1 / FPS, ease)
            self.move(t + 1 / FPS, grad, "endX", 2 * width, period - 1 / FPS, ease)
            t += period
        return t

    def push(self, t, scene, to, dur, ease="duda", carry=None):
        """Camera push inside one scene (the same screen at two scales, e.g. 1x -> 2.5x): PUSH_X scales about its own
        pivot. Not a match cut: one continuous move, rest to rest. The ease runs in log-scale space (an even zoom),
        baked as one cubic fitted to that curve."""
        node = f"PUSH_{scene}"
        s0 = self.now(node, "scaleX", t)
        fit, err = fit_log_ease(ease_curve(ease), s0, to)
        for p in ("scaleX", "scaleY"):
            self.track(node, p).move(frame(t), frame(t + dur), to, fit)
            for tgt, s1 in (carry or {}).items():   # e.g. a cursor riding the push, kept at its designed size
                self.track(tgt, p).move(frame(t), frame(t + dur), s1, fit)
        self.log.append(f"push {scene}: {s0:g} -> {to:g} in {dur:.2f}s, log-space ease fit {tuple(round(v, 3) for v in fit)} "
                        f"(max error {err * 100:.2f}%)")

    def rewrite(self, t, line, width=None, dur=0.8, ease="gradient", glow=True):
        """AI rewrite of one line of text: a highlight sweeps left to right and its edge is the swap boundary
        (left of it the new text, right of it still the old one, never both on the same pixel), with a soft glow riding
        the edge. Needs line.newmask (clip source, scaleX 0 -> 1 from its left edge), line.oldmask (clip source whose
        left edge moves from 0 to width) and, optionally, line.glow. The width defaults to the newmask's rectangle."""
        width = width if width is not None else float(self.by[f"{line}.newmask.rect"].attrs["width"])
        self.move(t, f"{line}.newmask", "scaleX", 1.0, dur, ease)
        self.move(t, f"{line}.oldmask", "x", self.base(f"{line}.oldmask", "x") + width, dur, ease)
        if glow:
            g = f"{line}.glow"
            self.move(t, g, "x", self.base(g, "x") + width, dur, ease)
            self.fade(t, g, 1.0, 0.1)
            self.fade(t + dur - 0.12, g, 0.0, 0.12)

    # ------------------------------------------------------------ cursor visits
    def cursor_visit(self, name, enter, points, leave):
        v = Visit(name, enter, points, leave, PT)
        legs = v.schedule()
        cur = TOKENS["cursor"]
        cap = TOKENS["speed_cap_px_per_frame_at_1920"]["cursor"] * 0.95

        def speeds():
            for leg in legs:
                leg["t0"], leg["t1"] = frame(leg["t0"]) / FPS, frame(leg["t1"]) / FPS
                leg["mean"] = (leg["s1"] - leg["s0"]) / max(leg["t1"] - leg["t0"], 1e-6)
            def speed(kind, j, other):
                if kind == "end":
                    return cur["enter_speed_ratio"] * legs[j]["mean"]
                if kind == "click":
                    return 0.0
                if kind == "slow":  # creeping: a short "thought" or waiting aside
                    return v.creep_speed()
                if legs[other].get("ease"):  # the neighbouring leg has its own ease: match its speed here
                    return Visit.ease_slope(legs[other], at_end=other < j)
                return cur["pass_speed_ratio"] * min(legs[j]["mean"], legs[other]["mean"])
            for j, leg in enumerate(legs):
                leg["v0"] = speed(v.kinds[leg["i"]], j, j - 1)
                leg["v1"] = speed(v.kinds[leg["i"] + 1], j, j + 1)
                k0, k1 = v.kinds[leg["i"]], v.kinds[leg["i"] + 1]
                if (k1 == "slow") != (k0 == "slow") and (leg.get("auto_ease") or not leg.get("ease")):
                    # into / out of a "thought": long, soft curves whose end slopes are solved to meet the creep
                    x1, _, x2, _ = cur["think"]["approach_ease" if k1 == "slow" else "depart_ease"]
                    m = leg["mean"]
                    leg["ease"] = [x1, leg["v0"] * x1 / m, x2, 1 - leg["v1"] * (1 - x2) / m]
                    leg["auto_ease"] = True
                leg["handles"] = ("value",) + Visit.handles(leg)

        def visible_peak(leg):
            f0, f1 = frame(leg["t0"]), frame(leg["t1"])
            prev, peak = None, 0.0
            for f in range(f0, f1 + 1):
                d = leg["s0"] + (leg["s1"] - leg["s0"]) * progress(leg["handles"], (f - f0) / (f1 - f0), leg["s0"], leg["s1"])
                p = v.pos_at(d)
                ins = -2 < p[0] < W + 2 and -2 < p[1] < H + 2
                if prev is not None and ins and prev[1]:
                    peak = max(peak, math.dist(p, prev[0]) * OUT_SCALE)
                prev = (p, ins)
            return peak

        speeds()
        # off-frame ends are free: stretch the entry/exit legs until the visible part respects the cursor cap
        for leg, side in ((legs[0], "t0"), (legs[-1], "t1") if leave else (None, None)):
            for _ in range(40):
                if leg is None or visible_peak(leg) <= cap:
                    break
                leg[side] += (-3 if side == "t0" else 3) / FPS
                speeds()
        for a, b in zip(legs, legs[1:]):
            if a.get("ease") and b.get("ease") and not (a.get("auto_ease") or b.get("auto_ease")):
                va, vb = Visit.ease_slope(a, True), Visit.ease_slope(b, False)
                self.log.append(f"{name}: eased legs meet at {a['t1']:.2f}s, speed in/out {va * v.total / FPS * OUT_SCALE:.1f}/"
                                f"{vb * v.total / FPS * OUT_SCALE:.1f} px/f")
        d = self.track(f"{name}.follow", "distance")
        for leg in legs:
            d.move(frame(leg["t0"]), frame(leg["t1"]), leg["s1"], leg["handles"])
            ratio = (leg["t1"] - leg["t0"]) * 1000 / leg["formula_ms"]
            creeping = v.kinds[leg["i"]] == v.kinds[leg["i"] + 1] == "slow"
            if not creeping and not 0.7 <= ratio <= 2.0:
                self.log.append(f"note: {name} leg {leg['i']} lasts {ratio:.2f}x the distance formula")
        self.set(legs[0]["t0"], name, "opacity", 1.0)
        for p in points:
            if p.get("click"):
                self.click(p["t"], name)
        if leave:
            self.set(legs[-1]["t1"] + 1 / FPS, name, "opacity", 0.0)
        v.t_in, v.t_out = legs[0]["t0"], (legs[-1]["t1"] if leave else None)
        self.visits[name] = v
        self.log.append(f"cursor {name}: in {v.t_in:.2f}s, clicks {[round(p['t'], 2) for p in points if p.get('click')]}"
                        + (f", out {v.t_out:.2f}s" if leave else ", no leave (it would vanish with the cut)"))

    # ------------------------------------------------------------ camera
    def drift(self, scene, kind, t0, t1, rate=None, parallax=None):
        """Slow constant camera motion over [t0, t1], centred on the laid-out pose. A drift that takes over from
        another drift of the same scene (it follows the scene's last move, MOTION.md) starts where the camera
        is, so the hand-over never jumps."""
        node = f"DRIFT_{scene}"
        T = t1 - t0
        follows = any(d[0] == scene and d[1] < t0 for d in getattr(self, "_drifts", []))
        self._drifts = getattr(self, "_drifts", []) + [(scene, t0)]
        if follows and kind != "zoom":
            r = rate if rate is not None else TOKENS["camera_drift"]["pan_px_per_frame_at_1920"]
            prop = "x" if kind == "x" else "y"
            for tgt, k in [(node, 1.0)] + list((parallax or {}).items()):
                a = self.track(tgt, prop).value_at(frame(t0))
                self.set(t0, tgt, prop, a)
                self.move(t0, tgt, prop, a + r / OUT_SCALE * FPS * T * k, T, "linear")
            return
        if kind == "zoom":
            r = rate if rate is not None else TOKENS["camera_drift"]["zoom_per_s"]
            moves = [("scaleX", 1 - r * T / 2, 1 + r * T / 2), ("scaleY", 1 - r * T / 2, 1 + r * T / 2)]
        else:
            r = rate if rate is not None else TOKENS["camera_drift"]["pan_px_per_frame_at_1920"]
            total = r / OUT_SCALE * FPS * T  # design px, signed
            moves = [("x" if kind == "x" else "y", -total / 2, total / 2)]
        for tgt, k in [(node, 1.0)] + list((parallax or {}).items()):
            for prop, a, b in moves:
                base = self.base(tgt, prop)
                if prop.startswith("scale"):
                    a, b = base * (1 + (a - 1) * k), base * (1 + (b - 1) * k)
                else:
                    a, b = base + a * k, base + b * k
                self.set(t0, tgt, prop, a)
                self.move(t0, tgt, prop, b, T, "linear")

    def match_cut(self, t, src, dst, kind, amount=None, exit_dur=None, entry_dur=None, parallax=None):
        """Exit `src` accelerating, hard cut at t, `dst` continues the same motion decelerating.
        Zoom cuts take match_cut.zoom: amount, frames and a fixed entry offset (not the speed ratio)."""
        mc = TOKENS["match_cut"]
        zt = mc["zoom"] if kind.startswith("zoom") else None
        amount = amount if amount is not None else zt["amount"]
        exit_dur = exit_dur or (zt["exit_frames"] / FPS if zt else mc["exit_ms"]["typical"] / 1000)
        entry_dur = entry_dur or (zt["entry_frames"] / FPS if zt else mc["entry_ms"]["typical"] / 1000)
        seam = abs(t - self.duration) < 1e-6
        fc = self.F if seam else frame(t)
        n_exit, n_entry = frame(exit_dur), frame(entry_dur)
        ex, en = tuple(mc["exit_ease"]), ease_curve(mc["entry_ease"])
        S, D = f"SCENE_{src}", f"SCENE_{dst}"
        zoom = kind.startswith("zoom")
        props = ["scaleX", "scaleY"] if zoom else (["x"] if kind in ("left", "right") else ["y"])
        sign = {"up": -1, "left": -1, "down": 1, "right": 1, "zoom_in": 1, "zoom_out": -1}[kind]

        # exit: from the current value, accelerating
        for p in props:
            v0 = self.track(S, p).value_at(fc - n_exit)
            v1 = v0 * (1 + sign * amount) if zoom else v0 + sign * amount
            self.track(S, p).move(fc - n_exit, fc, v1, ex)
            for tgt, k in (parallax or {}).items():
                b0 = self.track(tgt, p).value_at(fc - n_exit)
                b1 = b0 * (1 + sign * amount * k) if zoom else b0 + sign * amount * k
                self.track(tgt, p).move(fc - n_exit, fc, b1, ex)
            prof = [v0 + (v1 - v0) * progress(ex, i / n_exit) for i in range(n_exit + 1)]
            steps = [(math.log(prof[i + 1] / prof[i]) if zoom else prof[i + 1] - prof[i]) for i in range(n_exit)]
        exit_speed = sum(abs(s) for s in steps[-4:]) / 4

        # entry: same direction, decelerating; a pan's first step = ratio x the exit's last steps
        target = mc["entry_speed_ratio"]["target"] * exit_speed
        q1 = progress(en, 1 / n_entry)
        f_entry = 0 if seam else fc
        for p in props:
            base = self.base(D, p)
            if zoom:   # match_cut.zoom: a fixed offset from rest
                start = base * (1 - sign * zt["entry_offset"])
            else:
                start = base - sign * target / q1
            self.set(f_entry / FPS, D, p, start)
            self.track(D, p).move(f_entry, f_entry + n_entry, base, en)
        self.cut_entries.add((D, f_entry))

        # the cut itself
        self.set(fc / FPS, S, "opacity", 0.0)
        self.set(fc / FPS, D, "opacity", 1.0)
        offset = abs(start - self.base(D, props[0]))
        self.cuts.append({"frame": fc % self.F, "time": round((fc % self.F) / FPS, 3), "from": src, "to": dst, "kind": kind,
                          "seam": seam, "exit_frames": n_exit, "entry_frames": n_entry})
        self.log.append(f"match cut {src}->{dst} {kind} at {t:.2f}s: exit {amount} in {exit_dur:.2f}s, "
                        f"entry offset {offset:.3f} in {entry_dur:.2f}s")

    # ------------------------------------------------------------ loop closure
    def scene_of(self, name):
        el = self.by.get(name)
        while el is not None:
            if el.name and el.name.startswith("SCENE_"):
                return el.name
            el = self.parent.get(id(el))
        return None

    def auto_reset(self):
        """Put every scene-owned track back to its frame-0 value while its scene is hidden."""
        vis, unresolved = {}, []
        for (n, p), tr in list(self.tracks.items()):
            if self._loop_ok(tr):
                continue
            sc = self.scene_of(n)
            if sc is None and n.split(".")[0] in self.visits:   # a `screen: true` cursor: reset while it is hidden
                sc = n.split(".")[0]
            if sc is None:
                unresolved.append(f"{n}.{p}")
                continue
            if sc not in vis:
                vis[sc] = self.track(sc, "opacity").sample(self.F)
            v = vis[sc]
            last = tr.keys[-1]["f"]
            first_val = tr.keys[0]["v"]
            # the first hidden stretch after the scene has been on screen again (a cursor may start its off-frame
            # entry before its scene's cut: that is not the end of its scene)
            f, seen = None, v[last] > 1e-3
            for g in range(last + 1, self.F):
                seen = seen or v[g] > 1e-3
                if seen and v[g] < 1e-3 and v[g - 1] < 1e-3:
                    f = g
                    break
            if f is None and not seen:
                f = next((g for g in range(last + 1, self.F) if v[g] < 1e-3 and v[g - 1] < 1e-3), None)
            if f is not None:
                tr.set(f, first_val)
                continue
            if v[0] < 1e-3 and v[1] < 1e-3 and len(tr.keys) > 1 and tr.keys[1]["f"] > 1:
                tr.keys[0]["v"] = tr.value_at(self.F)
                tr._upsert(1, first_val, "hold")
                continue
            unresolved.append(f"{n}.{p}")
        return unresolved

    def _loop_ok(self, tr):
        first, last = tr.keys[0]["v"], tr.value_at(self.F)
        if tr.ptype != "double":
            return first == last
        if abs(first - last) < 1e-3:
            return True
        return tr.prop == "rotation" and abs(((last - first) / (2 * math.pi)) - round((last - first) / (2 * math.pi))) < 1e-3

    def check_loop(self):
        return [f"{n}.{p}: starts {tr.keys[0]['v']!r} ends {tr.value_at(self.F)!r}"
                for (n, p), tr in self.tracks.items() if not self._loop_ok(tr)]

    # ------------------------------------------------------------ screen-space evaluation
    def _sample_all(self):
        if self._samples is None:
            self._samples = {k: tr.sample(self.F) for k, tr in self.tracks.items() if tr.ptype == "double"}
        return self._samples

    def prop(self, el, p, f):
        s = self._sample_all().get((el.name, p)) if el.name else None
        if s is not None:
            return s[min(f, self.F)]
        v = el.attrs.get(p)
        return float(v) if isinstance(v, (int, float)) else DEFAULTS.get(p, 0.0)

    def to_screen(self, el, pt, f, include_self=False):
        """Point in el's parent space (or el's own space if include_self) -> artboard coordinates at frame f."""
        x, y = pt
        cur = el if include_self else self.parent.get(id(el))
        while cur is not None and cur is not self.artboard:
            if cur.tag in ("Node", "Shape", "Text", "Image"):
                sx, sy = self.prop(cur, "scaleX", f), self.prop(cur, "scaleY", f)
                r = self.prop(cur, "rotation", f)
                x, y = x * sx, y * sy
                if r:
                    x, y = x * math.cos(r) - y * math.sin(r), x * math.sin(r) + y * math.cos(r)
                x, y = x + self.prop(cur, "x", f), y + self.prop(cur, "y", f)
            cur = self.parent.get(id(cur))
        return x, y

    def opacity_chain(self, el, f):
        o, cur = 1.0, el
        while cur is not None and cur is not self.artboard:
            if cur.tag in ("Node", "Shape", "Text", "Image"):
                o *= self.prop(cur, "opacity", f)
            cur = self.parent.get(id(cur))
        return o

    def cursor_pos(self, name, f):
        d = self.prop(self.by[f"{name}.follow"], "distance", f)
        return self.to_screen(self.by[f"{name}.path"], self.visits[name].pos_at(d), f, include_self=True)

    def scene_frame(self, sc, f):
        """Screen positions of the content frame's corners and centre for scene sc."""
        content = self.by[f"CONTENT_{sc[6:]}"]
        return [self.to_screen(content, p, f, include_self=True) for p in [(0, 0), (W, 0), (0, H), (W, H), (W / 2, H / 2)]]

    # ------------------------------------------------------------ lint (static, exact, screen space)
    def lint(self):
        caps = TOKENS["speed_cap_px_per_frame_at_1920"]
        issues, report = [], []
        scenes = sorted({s for s in (self.scene_of(n) for (n, _) in self.tracks) if s})
        vis = {sc: self.track(sc, "opacity").sample(self.F) for sc in scenes}
        cut_window = set()
        for c in self.cuts:
            fc = self.F if c["seam"] else c["frame"]
            cut_window.update(g % self.F for g in range(fc - c["exit_frames"], fc + 1))
            f0 = 0 if c["seam"] else fc
            cut_window.update(range(f0, f0 + c["entry_frames"] + 1))

        # 1. element speeds (own moves seen through the camera), outside match-cut windows
        # (clip sources '...mask' are invisible; '.glow' lights ride an AI sweep like a gradient: not content)
        movers = {n for (n, p) in self.tracks if p in ("x", "y") and not n.startswith(("SCENE_", "DRIFT_", "BG"))
                  and not n.endswith("mask") and ".glow" not in n}
        for n in sorted(movers):
            el = self.by[n]
            cap = caps["chips_icons"] if n.startswith("CHIP") or ".knob" in n else caps["text_content"]
            peak, at = 0.0, 0
            prev = self.to_screen(el, (self.prop(el, "x", 0), self.prop(el, "y", 0)), 0)
            for f in range(1, self.F + 1):
                cur = self.to_screen(el, (self.prop(el, "x", f), self.prop(el, "y", f)), f)
                on_screen = -2 < cur[0] < W + 2 and -2 < cur[1] < H + 2
                if f - 1 not in cut_window and f not in cut_window and on_screen and self.opacity_chain(el, f) > 0.05:
                    sp = math.dist(prev, cur) * OUT_SCALE
                    if sp > peak:
                        peak, at = sp, f
                prev = cur
            report.append((n, "content" if cap == caps["text_content"] else "icon", peak, cap, at))
            if peak > cap + 0.5:
                issues.append(f"{n} peaks at {peak:.1f} px/f > cap {cap} at {at / FPS:.2f}s")

        # 1b. readable text carried by the camera (drift, push, scrolling parents), on screen, outside match cuts
        for n in sorted(k for k, el in self.by.items() if el.tag == "Text" and k not in movers):
            el, sc = self.by[n], self.scene_of(n)
            if sc not in vis:
                continue
            peak, at, prev = 0.0, 0, None
            for f in range(self.F + 1):
                if vis[sc][min(f, self.F - 1)] < 1e-3 or f in cut_window:
                    prev = None
                    continue
                cur = self.to_screen(el, (self.prop(el, "x", f), self.prop(el, "y", f)), f)
                if prev is not None and 0 <= cur[0] <= W and 0 <= cur[1] <= H and self.opacity_chain(el, f) > 0.05:
                    sp = math.dist(prev, cur) * OUT_SCALE
                    if sp > peak:
                        peak, at = sp, f
                prev = cur
            if peak > 1.0:
                report.append((n, "text/cam", peak, caps["text_content"], at))
            if peak > caps["text_content"] + 0.5:
                issues.append(f"text {n} moves {peak:.1f} px/f on screen > cap {caps['text_content']} at {at / FPS:.2f}s")

        # 2. cursors: speed while inside the frame, parking, appearing/vanishing on screen
        def inside(p):
            return -2 < p[0] < W + 2 and -2 < p[1] < H + 2
        for name, v in self.visits.items():
            el = self.by[name]
            peak, at, still = 0.0, 0, 0
            prev = self.cursor_pos(name, 0)
            for f in range(1, self.F + 1):
                cur = self.cursor_pos(name, f)
                visible = self.opacity_chain(el, f) > 0.05 and inside(cur)
                sp = math.dist(prev, cur) * OUT_SCALE
                if visible and f not in cut_window and sp > peak:
                    peak, at = sp, f
                if visible and sp < 0.3:
                    still += 1
                    if still == int(0.5 * FPS):
                        issues.append(f"{name} is parked (visible and still > 0.5s) at {(f - still) / FPS:.2f}s")
                else:
                    still = 0
                prev = cur
            report.append((name, "cursor", peak, caps["cursor"], at))
            if peak > caps["cursor"] + 0.5:
                issues.append(f"{name} peaks at {peak:.1f} px/f > cap {caps['cursor']} at {at / FPS:.2f}s")
            for tt, what in ((v.t_in, "appears"), (v.t_out, "vanishes")):
                if tt is not None and inside(self.cursor_pos(name, frame(tt))):
                    p = self.cursor_pos(name, frame(tt))
                    issues.append(f"{name} {what} inside the frame at {tt:.2f}s ({p[0]:.0f}, {p[1]:.0f})")
            # it never leaves with a cut: a cursor riding its scene's exit vanishes on screen at the cut (eComm review)
            for f in range(self.F):
                if self.opacity_chain(el, f) > 0.05 >= self.opacity_chain(el, f + 1) and inside(self.cursor_pos(name, f)):
                    p = self.cursor_pos(name, f)
                    issues.append(f"{name} vanishes with its scene's cut at {(f + 1) / FPS:.2f}s ({p[0]:.0f}, {p[1]:.0f}): "
                                  "give it a leave that ends off-frame before the cut, or, when its click opens the next screen, "
                                  "`screen: true` so it crosses the cut (MOTION.md, Cursor)")
                    break
            # its first visible frame (a cursor may start its entry before its scene's cut) must be off-frame too
            f_vis = next((f for f in range(self.F) if self.opacity_chain(el, f) > 0.05), None)
            if f_vis is not None and f_vis > frame(v.t_in) and inside(self.cursor_pos(name, f_vis)):
                p = self.cursor_pos(name, f_vis)
                issues.append(f"{name} shows up inside the frame when its scene cuts in at {f_vis / FPS:.2f}s "
                              f"({p[0]:.0f}, {p[1]:.0f}): start its entry later")

        # 2a. cursor value graphs are smooth: at every key the slope coming in equals the slope going out
        def slope(k0, k1, at_end):
            e, T, dv = k0["ease"], max(k1["f"] - k0["f"], 1), k1["v"] - k0["v"]
            if e == "hold":
                return 0.0
            if e == "linear":
                return dv / T
            if e[0] == "value":
                _, x1, y1, x2, y2 = e
                return ((k1["v"] - y2) / ((1 - x2) * T)) if at_end else ((y1 - k0["v"]) / (x1 * T) if x1 else 0.0)
            x1, y1, x2, y2 = e
            return (((1 - y2) / (1 - x2)) if at_end else (y1 / x1 if x1 else 0.0)) * dv / T
        for name in self.visits:
            keys = self.tracks[(f"{name}.follow", "distance")].keys
            for i in range(1, len(keys) - 1):
                f = keys[i]["f"]
                p = self.cursor_pos(name, f)
                if self.opacity_chain(self.by[name], f) < 0.05 or not (0 <= p[0] <= W and 0 <= p[1] <= H):
                    continue  # off-frame ends are free
                vin, vout = slope(keys[i - 1], keys[i], True), slope(keys[i], keys[i + 1], False)
                big = max(abs(vin), abs(vout)) * self.visits[name].total * OUT_SCALE
                if big > 0.3 and not 0.75 <= (vout + 1e-12) / (vin + 1e-12) <= 1.33:
                    issues.append(f"{name}: kink in the value graph at {f / FPS:.2f}s "
                                  f"({vin * self.visits[name].total * OUT_SCALE:.2f} -> {vout * self.visits[name].total * OUT_SCALE:.2f} px/f)")

        # 2b. every click gets a visible reaction (hover before, or something on the press frame)
        lead = int(TOKENS["cursor"]["hover_lead_ms"] / 1000 * FPS) + 3
        for name, v in self.visits.items():
            for p in v.points:
                if not p.get("click"):
                    continue
                f = frame(p["t"])
                hit = any(f - lead <= k["f"] <= f + 3 for (n, _), tr in self.tracks.items()
                          if not n.startswith("CURSOR") for k in tr.keys)
                if not hit:
                    issues.append(f"{name} clicks at {p['t']:.2f}s but nothing reacts (add a hover/press)")

        # 2c. state swaps never overlap: a check may start only on its loader's last visible frame
        pairs = set(self.resolves) | {(n, n[:-5] + ".check.stroke.trim") for (n, p) in self.tracks
                                      if n.endswith(".spin") and (n[:-5] + ".check.stroke.trim", "end") in self.tracks}
        for spin, check in sorted(pairs):
            op = self._sample_all().get((spin, "opacity"))
            tr = self._sample_all().get((check, "end"))
            if not op or not tr:
                continue
            both = sum(1 for f in range(self.F) if op[f] > 0.02 and tr[f] > 0.005)
            if both > 1:
                issues.append(f"{check.split('.')[0]}: check and loader on screen together for {both} frames")

        # 3. match cuts: same direction, entry speed ratio, exit speed, never two scenes at once
        mcr = TOKENS["match_cut"]["entry_speed_ratio"]
        for c in self.cuts:
            S, D = f"SCENE_{c['from']}", f"SCENE_{c['to']}"
            fc = self.F if c["seam"] else c["frame"]
            f_entry = 0 if c["seam"] else fc

            def motion(sc, fa, fb):
                a, b = self.scene_frame(sc, fa), self.scene_frame(sc, fb)
                return (b[4][0] - a[4][0], b[4][1] - a[4][1]), math.log((b[3][0] - b[0][0]) / (a[3][0] - a[0][0]))
            ex = [motion(S, g - 1, g) for g in range(fc - 3, fc + 1)]
            en = motion(D, f_entry, f_entry + 1)
            if c["kind"].startswith("zoom"):
                e_sp, n_sp = sum(abs(z) for _, z in ex) / 4, abs(en[1])
                same = all(z * en[1] > 0 for _, z in ex)
            else:
                vx, vy = sum(v[0] for v, _ in ex) / 4, sum(v[1] for v, _ in ex) / 4
                e_sp, n_sp = math.hypot(vx, vy), math.hypot(*en[0])
                same = (vx * en[0][0] + vy * en[0][1]) > 0
            ratio = n_sp / e_sp if e_sp else 0
            exit_px = max(math.dist(p, q) for p, q in zip(self.scene_frame(S, fc - 1), self.scene_frame(S, fc))) * OUT_SCALE
            c["ratio"], c["exit_last_px"] = round(ratio, 2), round(exit_px, 1)
            line = f"{c['from']}->{c['to']} {c['kind']}: same direction {same}, entry/exit speed {ratio:.2f}, exit last step {exit_px:.0f} px/f"
            report.append((f"cut {c['from']}->{c['to']}", "match cut", exit_px, caps["match_cut"], fc))
            if not same:
                issues.append(f"match cut {line}: direction changes across the cut")
            top = TOKENS["match_cut"]["zoom"]["entry_speed_ratio_max"] if c["kind"].startswith("zoom") else mcr["max"]
            if not mcr["min"] <= ratio <= top:
                issues.append(f"match cut {line}: speed ratio outside {mcr['min']}-{top}")
            self.log.append("match cut check: " + line)
        for f in range(self.F):
            on = [sc for sc in vis if vis[sc][f] > 1e-3]
            if len(on) > 1:
                issues.append(f"two scenes visible at {f / FPS:.2f}s: {on}")
                break

        # 4. never static: the visible scene's camera always moves a little
        still_from = None
        for f in range(self.F):
            mv = 0.0
            for sc in (s for s in vis if vis[s][f] > 1e-3):
                a, b = self.scene_frame(sc, f), self.scene_frame(sc, f + 1)
                mv = max(mv, max(math.dist(p, q) for p, q in zip(a, b)) * OUT_SCALE)
            if mv < 0.05:
                still_from = f if still_from is None else still_from
            else:
                if still_from is not None and f - still_from >= 3:
                    issues.append(f"camera still {still_from / FPS:.2f}-{f / FPS:.2f}s")
                still_from = None

        # 5. 'settle' (fast start) only where the start is invisible
        for (n, p), tr in self.tracks.items():
            for k in tr.keys:
                if k["ease"] == ease_curve("settle") and (n, k["f"]) not in self.cut_entries:
                    op = self.tracks.get((n, "opacity"))
                    if op and op.value_at(max(0, k["f"] - 1)) > 0.1:
                        issues.append(f"{n}.{p}: 'settle' (fast start) at {k['f'] / FPS:.2f}s on a visible element")
        return report, issues

    # ------------------------------------------------------------ output
    def to_rml(self):
        kos = {}
        for (n, p), tr in sorted(self.tracks.items(), key=lambda kv: (kv[0][0], kv[0][1])):
            kf_tag = KF_TYPE.get(tr.ptype, "KeyFrameDouble")
            kps = []
            for k in tr.keys:
                attrs = {"frame": k["f"], "value": k["v"] if tr.ptype != "bool" else bool(k["v"])}
                kids = []
                if kf_tag in ("KeyFrameDouble", "KeyFrameColor"):
                    e = k["ease"]
                    if e == "hold":
                        attrs["interpolationType"] = "hold"
                    elif e == "linear":
                        attrs["interpolationType"] = "linear"
                    elif e[0] == "value":
                        attrs["interpolationType"] = 3
                        kids.append(El("CubicValueInterpolator", {"x1": e[1], "y1": e[2], "x2": e[3], "y2": e[4]}))
                    else:
                        attrs["interpolationType"] = "cubic"
                        kids.append(El("CubicEaseInterpolator", {"x1": e[0], "y1": e[1], "x2": e[2], "y2": e[3]}))
                kps.append(El(kf_tag, attrs, kids))
            kos.setdefault(n, []).append(El("KeyedProperty", {"propertyKey": tr.key}, kps))
        return [El("KeyedObject", {"objectId": "@" + n}, props) for n, props in kos.items()]


def fit_log_ease(e, s0, s1, n=48):
    """Cubic (x1, 0, x2, 1) whose progress on a linear scale property follows ease e applied in log-scale space,
    so a big zoom looks even instead of rushing at the start. Returns (curve, max error as a fraction of the move)."""
    a, b = math.log(s0), math.log(s1)
    ps = [i / n for i in range(1, n)]
    ev = cubic_bezier(*e) if isinstance(e, tuple) else (lambda p: p)
    target = [(math.exp(a + (b - a) * ev(p)) - s0) / (s1 - s0) for p in ps]

    def err(x):
        x1, x2 = min(max(x[0], 0.01), 0.99), min(max(x[1], 0.01), 0.99)
        f = cubic_bezier(x1, 0.0, x2, 1.0)
        return max(abs(f(p) - q) for p, q in zip(ps, target))
    best, step = [e[0] if isinstance(e, tuple) else 0.5, e[2] if isinstance(e, tuple) else 0.5], 0.1
    cur = err(best)
    while step > 1e-4:
        moved = False
        for i in (0, 1):
            for d in (-step, step):
                cand = list(best)
                cand[i] = min(max(cand[i] + d, 0.01), 0.99)
                v = err(cand)
                if v < cur:
                    best, cur, moved = cand, v, True
        if not moved:
            step /= 2
    return (round(best[0], 4), 0.0, round(best[1], 4), 1.0), cur


def run_beats(c, beats):
    for b in beats:
        b = dict(b)
        op = b.pop("do")
        t = b.pop("t", None)
        if op == "move":
            c.move(t, b["target"], b["prop"], b["to"], b["dur"], b.get("ease", "duda"))
        elif op == "set":
            c.set(t, b["target"], b["prop"], b["value"])
        elif op == "fade":
            c.fade(t, b["target"], b["to"], b.get("dur"))
        elif op == "enter":
            c.enter(t, b["target"], b.get("dx", 0.0), b.get("dy"), b.get("dur", 0.6), b.get("ease", "settle"), b.get("fade"))
        elif op == "exit":
            c.exit(t, b["target"], b.get("dx", 0.0), b.get("dy"), b.get("dur", 0.333), b.get("fade"))
        elif op == "words":
            c.words(t, b["target"], b.get("kind", "title"), b.get("step"), b.get("blur"), b.get("dy"), b.get("dur"))
        elif op == "pop":
            c.pop(t, b["target"], b.get("from", 0.94), b.get("dur", 0.5))
        elif op == "cursor_visit":
            c.cursor_visit(b["id"], b["enter"], b["points"], b.get("leave"))
        elif op == "press":
            c.press(t, b["target"], b.get("scale", 0.9))
        elif op == "type":
            end = c.type(t, b["target"], b["text"], b.get("cps", 38), until=b.get("until"))
            c.log.append(f"typing ends at {end:.2f}s")
        elif op == "resolve":
            c.resolve(t, b["spin"], b["check"], b.get("live"), b.get("done"))
        elif op == "spin":
            c.spin(t, b["until"], b["target"], b.get("period", 0.8))
        elif op == "sweep":
            c.sweep(t, b["until"], b["grad"], b["width"], b.get("period", 1.6), b.get("ease", "gradient"))
        elif op == "drift":
            c.drift(b["scene"], b["kind"], b["from"], b["to"], b.get("rate"), b.get("parallax"))
        elif op == "reset":  # every animated property of target back to its frame-0 value (use while it is covered)
            for (n, prop), tr in list(c.tracks.items()):
                if n == b["target"]:
                    tr.set(frame(t), tr.keys[0]["v"])
        elif op == "match_cut":
            c.match_cut(t, b["from"], b["to"], b["kind"], b.get("amount"), b.get("exit_dur"), b.get("entry_dur"), b.get("parallax"))
        elif op == "push":
            c.push(t, b["scene"], b["to"], b["dur"], b.get("ease", "duda"), b.get("carry"))
        elif op == "rewrite":
            c.rewrite(t, b["line"], b.get("width"), b.get("dur", 0.8), b.get("ease", "gradient"), b.get("glow", True))
        else:
            raise ValueError(f"unknown beat {op}")


def visits_in(beats_path):
    """Cursor visits declared in a beat sheet (build.py lays out their paths). Each Visit keeps its beat in .opts
    (e.g. `size`, the cursor's scale)."""
    spec = yaml.safe_load(open(beats_path))
    configure(spec.get("canvas"))
    out = []
    for b in spec["beats"]:
        if b["do"] == "cursor_visit":
            v = Visit(b["id"], b["enter"], b["points"], b.get("leave"), PT)
            v.opts = b
            out.append((b["id"], b.get("scene"), v))
    return out


def apply_pose(by, beats_path, pose, visits=()):
    """A storyboard frame shown statically: beats.yaml `poses: {name: {scene: X, set: {"NODE:prop": v}, cursor: {ID: [x, y]}}}`.
    Returns the scene to show. `cursor` puts a visit's cursor on the waypoint at [x, y] (as in the Figma frame)."""
    spec = (yaml.safe_load(open(beats_path)).get("poses") or {})[pose]
    for k, v in (spec.get("set") or {}).items():
        name, prop = k.rsplit(":", 1)
        by[name].attrs[prop] = v
    vis = {name: v for name, _, v in visits}
    for name, at in (spec.get("cursor") or {}).items():
        v = vis[name]
        i = min(range(len(v.waypoints)), key=lambda j: math.dist(v.waypoints[j], at))
        by[f"{name}.follow"].attrs["distance"] = v.s[i]
        by[name].attrs["opacity"] = 1
    return spec["scene"]


def attach(doc, artboard, sm, by, static=False, beats_path=None, build_dir=None):
    if beats_path and os.path.exists(beats_path):
        configure(yaml.safe_load(open(beats_path)).get("canvas"))
    if static or not beats_path or not os.path.exists(beats_path):
        anim = El("LinearAnimation", {"fps": FPS, "duration": 1, "loopValue": "loop"}, name="ANIM_MAIN")
        artboard.children = [anim, sm] + artboard.children
        return None
    spec = yaml.safe_load(open(beats_path))
    c = Choreo(artboard, by, spec["duration"])
    for k, v in (spec.get("initial") or {}).items():
        name, prop = k.rsplit(":", 1)
        c.track(name, prop).keys[0]["v"] = float(v) if isinstance(v, (int, float)) else v
    # camera ops first (they own frame 0 of the scene nodes), then everything else in sheet order
    beats = spec["beats"]
    run_beats(c, [b for b in beats if b["do"] in ("match_cut", "drift")])
    run_beats(c, [b for b in beats if b["do"] not in ("match_cut", "drift")])
    unresolved = c.auto_reset()
    bad = c.check_loop()
    anim = El("LinearAnimation", {"fps": FPS, "duration": c.F, "loopValue": "loop"}, c.to_rml(), name="ANIM_MAIN")
    artboard.children = [anim, sm] + artboard.children
    report, issues = c.lint()
    for line in c.log:
        print("  ", line)
    print("speed lint (px/frame @1920):")
    for n, kind, peak, cap, at in sorted(report, key=lambda r: -r[2] / r[3])[:14]:
        print(f"   {'OVER' if peak > cap + 0.5 else 'ok  '} {peak:6.1f}/{cap:<3} {kind:9s} {n} @ {at / FPS:.2f}s")
    for i in issues:
        print("LINT:", i)
    if bad:
        print("LOOP CHECK: tracks that don't return to their first value:")
        for b in bad:
            print("   ", b, "(not owned by a scene)" if any(b.startswith(u + ":") for u in unresolved) else "")
    else:
        print("loop check: every track ends where it starts")
    if build_dir:
        os.makedirs(build_dir, exist_ok=True)
        with open(os.path.join(build_dir, "cuts.json"), "w") as fh:
            json.dump({"fps": FPS, "frames": c.F, "cuts": c.cuts}, fh, indent=1)
    return c
