"""Cursor visits: a curved Follow Path from off-frame, through the targets, and out again.

Geometry: one open cubic path per visit. Each leg bows gently to one side (token cursor.path_bow);
points the cursor passes through without clicking are smooth (mirrored handles) so the velocity
vector stays continuous there. Timing: keys on FollowPathConstraint.distance (normalised by arc
length, verified in Rive) with CubicValue handles that match the speed on both sides of every
waypoint: 0 at clicks, a fraction of the leg's mean speed at pass points, fast at the off-frame ends.
"""
import bisect
import math

from rml import El

FPS = 60


def _rot(v, a):
    c, s = math.cos(a), math.sin(a)
    return (v[0] * c - v[1] * s, v[0] * s + v[1] * c)


def _peak_rel(e):
    """Peak speed of a normalised cubic-bezier ease, as a multiple of its mean speed."""
    x1, y1, x2, y2 = e
    best, prev = 0.0, (0.0, 0.0)
    for j in range(1, 2001):
        t = j / 2000
        u = 1 - t
        x = 3 * u * u * t * x1 + 3 * u * t * t * x2 + t ** 3
        y = 3 * u * u * t * y1 + 3 * u * t * t * y2 + t ** 3
        if x - prev[0] > 1e-9:
            best = max(best, (y - prev[1]) / (x - prev[0]))
        prev = (x, y)
    return best


def _unit(v):
    n = math.hypot(*v) or 1.0
    return (v[0] / n, v[1] / n)


class Visit:
    """points: list of dicts {at: (x, y), t: seconds, click: bool, pause: s, bow: f, tangent: (dx, dy), ease: name|[4]}
      or {aside: true} between two clicks (Duda's typing pattern: position and time are computed). The default shape
      is a simple arc from the first click to the next one, bulging away from the text (`side: down|up`, `sagitta`);
      {aside: hook} is video 1's hook (to the side, then curving back), for a next control behind the field;
      t = press time for clicks, pass time otherwise; pause = creep this long there (a short "thought", or waiting
      aside); bow = curvature of the leg arriving at this point (sign = side); tangent = heading at a pass/slow point;
      ease = normalised cubic for the leg arriving at this point ("away"/"back" from tokens cursor.aside.ease,
      "go"/"land" from cursor.breath.ease).
    enter/leave: off-frame points. leave=None keeps the cursor riding its scene's exit, and it vanishes at the cut:
      MOTION.md forbids that and choreo's lint reports it."""

    def __init__(self, name, enter, points, leave, tokens):
        self.name, self.tok, self.T = name, tokens["cursor"], tokens
        # tokens measured in px of the 680-wide reference frame -> this project's design px (1.0 for video 1)
        self.dpx = tokens.get("dpx", 1.0)
        self.fps = tokens.get("fps", FPS)
        self.enter, self.points, self.leave = tuple(enter), points, (tuple(leave) if leave else None)
        # waypoint specs: {p, kind, t, bow (leg arriving here), tangent}; a point with `pause` becomes two slow
        # waypoints a few px apart (the cursor creeps between them: a "thought", or waiting aside)
        self.specs = [{"p": self.enter, "kind": "end"}]
        aside_tok = self.tok["aside"]
        for k, p in enumerate(points):
            if p.get("aside"):  # Duda's typing pattern: drift aside after a click, swoop back to the next click
                nxt = points[k + 1]
                if not (points[k - 1].get("click") and nxt.get("click")):
                    raise ValueError(f"{name}: an aside point must sit between two clicks")
                nxt.setdefault("ease", "back")
                shape = "hook" if p["aside"] == "hook" else "arc"
                self.specs.append({"p": None, "kind": "pass", "t": None, "aside": True, "shape": shape,
                                   "bow": aside_tok["bow"], "tangent": aside_tok["turn_tangent"], "pause": 0.0,
                                   "ease": aside_tok["ease"]["away"],
                                   "offset": tuple(p.get("offset", [v * self.dpx for v in aside_tok["turn_offset"]])),
                                   "sagitta": p.get("sagitta", aside_tok.get("arc_sagitta", 0.16)),
                                   "side": p.get("side", aside_tok.get("arc_side", "down")),
                                   "prev_t": points[k - 1]["t"], "next_t": nxt["t"]})
                continue
            kind = "click" if p.get("click") else ("slow" if p.get("pause") else "pass")
            ease = p.get("ease")
            if isinstance(ease, str):  # a named ease from tokens (cursor.aside.ease, cursor.breath.ease)
                named = {**self.tok["aside"]["ease"], **self.tok.get("breath", {}).get("ease", {})}
                ease = named[ease]
            self.specs.append({"p": tuple(p["at"]), "kind": kind, "t": p["t"], "bow": p.get("bow"),
                               "tangent": p.get("tangent"), "pause": p.get("pause", 0.0), "ease": ease})
            if kind == "slow":
                self.specs.append({"p": None, "kind": "slow", "t": p["t"] + p["pause"], "creep_of": len(self.specs) - 1})
        if self.leave:
            self.specs.append({"p": self.leave, "kind": "end"})
        self._place_asides()
        self._build_geometry()

    def _place_asides(self):
        """Turn point and time of every aside move: start from the token offset, split the window so the speed is the
        same on both sides of the turn, and pull the turn closer until the swoop back stays under the cursor cap."""
        lead = self.tok["press_lead_frames"] / self.fps
        cap = self.T["speed_cap_px_per_frame_at_1920"]["cursor"] * 0.97
        out_scale = self.T["canvas"]["output_scale"]
        for i, sp in enumerate(self.specs):  # provisional positions, so the geometry can be built
            if sp.get("aside"):
                prev = self.specs[i - 1]["p"]
                if sp["shape"] == "arc":
                    self._arc_turn(sp, prev, self.specs[i + 1])
                else:
                    sp["p"] = (prev[0] + sp["offset"][0], prev[1] + sp["offset"][1])
                sp["t"] = sp["prev_t"]
        for i, sp in enumerate(self.specs):
            if not sp.get("aside"):
                continue
            prev, nxt = self.specs[i - 1], self.specs[i + 1]
            away, back = sp["ease"], nxt["ease"]
            t0 = sp["prev_t"] + lead + 2 / self.fps  # leaves the first click
            t3 = sp["next_t"] + lead            # lands on the next click
            k = 1.0
            for _ in range(30):
                if sp["shape"] == "hook":
                    sp["p"] = (prev["p"][0] + sp["offset"][0] * k, prev["p"][1] + sp["offset"][1] * k)
                self._build_geometry()
                L1, L2 = self.leg_len[i - 1], self.leg_len[i]
                a = (1 - away[3]) / (1 - away[2]) * L1      # end speed of 'away' ~ a / T1
                b = (back[1] / back[0]) * L2                 # start speed of 'back' ~ b / T2
                T1 = (t3 - t0) * a / (a + b)
                sp["t"] = t0 + T1
                peak = _peak_rel(back) * L2 / ((t3 - t0 - T1) * self.fps) * out_scale
                if peak <= cap or sp["shape"] == "arc":
                    break
                k *= 0.95
            sp["peak"], sp["scale"] = peak, k

    @staticmethod
    def _arc_turn(sp, prev, nxt_spec):
        """The aside as one simple arc from the click to the next control: the turn is the arc's midpoint, offset from
        the chord by sagitta x chord on the chosen side (default: below, away from the text being typed), heading
        along the chord; both halves bow to that side like a circle through the three points."""
        nxt = nxt_spec["p"]
        cx, cy = nxt[0] - prev[0], nxt[1] - prev[1]
        L = math.hypot(cx, cy) or 1.0
        n = (-cy / L, cx / L)
        want = {"down": (0, 1), "up": (0, -1), "left": (-1, 0), "right": (1, 0)}[sp["side"]]
        if n[0] * want[0] + n[1] * want[1] < 0:
            n = (-n[0], -n[1])
        s = sp["sagitta"] * L
        sp["p"] = (prev[0] + cx / 2 + n[0] * s, prev[1] + cy / 2 + n[1] * s)
        sp["tangent"] = (cx, cy)
        R = (L * L / 4 + s * s) / (2 * s)                    # circle through the click, the turn and the next control
        h = math.hypot(L / 2, s)                              # each half's chord
        bow = (R - math.sqrt(max(R * R - h * h / 4, 0.0))) / h

        def signed(a, b):                                     # positive bow bulges toward (-dy, dx) of the leg
            dx, dy = b[0] - a[0], b[1] - a[1]
            return bow if (-dy * n[0] + dx * n[1]) >= 0 else -bow
        sp["bow"] = signed(prev, sp["p"])
        if nxt_spec.get("bow") is None or nxt_spec.get("arc_bow"):
            nxt_spec["bow"], nxt_spec["arc_bow"] = signed(sp["p"], nxt), True


    # ------------------------------------------------------------ geometry
    def _build_geometry(self):
        S = self.specs
        creep_v = self.tok["creep_px_per_s"] * self.dpx
        hcap = 140 * self.dpx

        def theta_for(bow):
            return math.copysign(math.asin(min(0.9, 4 * abs(bow))), bow)  # handles rotated by theta bow ~ chord*sin/4

        # creep partners sit just ahead of their point, along its tangent
        def tangent_at(i):
            sp = S[i]
            if sp.get("tangent"):
                return _unit(sp["tangent"])
            prev = S[i - 1]["p"]
            j = i + 1
            while S[j]["p"] is None:
                j += 1
            nxt = S[j]["p"]
            return _unit((nxt[0] - prev[0], nxt[1] - prev[1]))
        for i, sp in enumerate(S):
            if sp.get("creep_of") is not None:
                base = S[sp["creep_of"]]
                tan = tangent_at(sp["creep_of"])
                base["tan"] = sp["tan"] = tan
                L = creep_v * base["pause"]
                sp["p"] = (base["p"][0] + tan[0] * L, base["p"][1] + tan[1] * L)
        P = [sp["p"] for sp in S]
        n = len(P)
        self.waypoints, self.kinds = P, [sp["kind"] for sp in S]
        verts = []
        for i, sp in enumerate(S):
            p = sp["p"]
            v = {"p": p, "in": None, "out": None, "kind": sp["kind"]}
            if sp["kind"] in ("pass", "slow"):
                tan = sp.get("tan") or tangent_at(i)
                lin = min(math.dist(P[i - 1], p) / 3, hcap)
                lout = min(math.dist(p, P[i + 1]) / 3, hcap)
                v["in"] = (p[0] - tan[0] * lin, p[1] - tan[1] * lin)
                v["out"] = (p[0] + tan[0] * lout, p[1] + tan[1] * lout)
            verts.append(v)
        # handles at click/end points: along the chord, rotated so the leg bows (default: every leg to the same side)
        for i in range(n - 1):
            a, b = verts[i], verts[i + 1]
            bow = S[i + 1].get("bow")
            theta = theta_for(bow if bow is not None else self.tok["path_bow"])
            c = (b["p"][0] - a["p"][0], b["p"][1] - a["p"][1])
            L = math.hypot(*c) / 3
            if a["out"] is None:
                d = _rot(_unit(c), theta)
                a["out"] = (a["p"][0] + d[0] * L, a["p"][1] + d[1] * L)
            if b["in"] is None:
                d = _rot(_unit((-c[0], -c[1])), -theta)
                b["in"] = (b["p"][0] + d[0] * L, b["p"][1] + d[1] * L)
        self.verts = verts
        # arc-length table
        self.samples, self.lengths = [], [0.0]
        for i in range(n - 1):
            p0, c1, c2, p1 = verts[i]["p"], verts[i]["out"], verts[i + 1]["in"], verts[i + 1]["p"]
            for j in range(400):
                t = j / 400
                u = 1 - t
                pt = tuple(u ** 3 * p0[k] + 3 * u * u * t * c1[k] + 3 * u * t * t * c2[k] + t ** 3 * p1[k] for k in range(2))
                if self.samples:
                    self.lengths.append(self.lengths[-1] + math.dist(self.samples[-1], pt))
                self.samples.append(pt)
        last = verts[-1]["p"]
        self.lengths.append(self.lengths[-1] + math.dist(self.samples[-1], last))
        self.samples.append(last)
        self.total = self.lengths[-1]
        # cumulative distance at each waypoint (exact sample indices at leg boundaries)
        self.s = [self.lengths[i * 400] / self.total for i in range(n - 1)] + [1.0]
        self.leg_len = [(self.s[i + 1] - self.s[i]) * self.total for i in range(n - 1)]

    def pos_at(self, d):
        """Design-px position (in the path's coordinate space) at normalised distance d."""
        target = min(max(d, 0.0), 1.0) * self.total
        k = bisect.bisect_left(self.lengths, target)
        k = min(max(k, 1), len(self.lengths) - 1)
        a, b = self.samples[k - 1], self.samples[k]
        span = self.lengths[k] - self.lengths[k - 1] or 1e-9
        r = (target - self.lengths[k - 1]) / span
        return (a[0] + (b[0] - a[0]) * r, a[1] + (b[1] - a[1]) * r)

    # ------------------------------------------------------------ timing
    def move_ms(self, length):
        m = self.tok["move_ms"]
        return min(max(450 + 1.4 * length / self.dpx, m["min"]), m["max"])

    def schedule(self):
        """-> list of legs {t0, t1, s0, s1, i, formula_ms}; the caller snaps them to frames and sets v0/v1
        (normalised distance per second) before asking for handles().
        Clicks land before the cursor fully stops: the press starts press_lead_frames before the arrival."""
        tok = self.tok
        lead = tok["press_lead_frames"] / self.fps
        S = self.specs
        arrive, depart = {}, {}
        for i, sp in enumerate(S[1:], 1):
            if sp["kind"] == "end":
                continue
            if sp["kind"] == "click":
                arrive[i] = sp["t"] + lead
                depart[i] = arrive[i] + 2 / self.fps
            else:
                arrive[i] = depart[i] = sp["t"]
        last_point = len(S) - 2 if self.leave else len(S) - 1
        legs = [{"t1": arrive[1], "t0": arrive[1] - self.move_ms(self.leg_len[0]) / 1000, "i": 0}]
        for i in range(1, last_point):
            legs.append({"t0": depart[i], "t1": arrive[i + 1], "i": i})
        if self.leave:
            k = len(S) - 2
            legs.append({"t0": depart[k], "t1": depart[k] + self.move_ms(self.leg_len[-1]) / 1000, "i": k})
        for leg in legs:
            i = leg["i"]
            leg["s0"], leg["s1"] = self.s[i], self.s[i + 1]
            leg["formula_ms"] = self.move_ms(self.leg_len[i])
            leg["ease"] = S[i + 1].get("ease")
        self.legs = legs
        self.t_in = legs[0]["t0"]
        self.t_out = legs[-1]["t1"] if self.leave else None
        return legs

    def creep_speed(self):
        """Normalised distance per second while creeping."""
        return self.tok["creep_px_per_s"] * self.dpx / self.total

    @staticmethod
    def ease_slope(leg, at_end):
        """Speed (normalised distance / s) at the start or end of a leg that uses a given ease."""
        x1, y1, x2, y2 = leg["ease"]
        rel = (1 - y2) / (1 - x2) if at_end else (y1 / x1 if x1 else 0.0)
        return rel * leg["mean"]

    @staticmethod
    def handles(leg, rest_x=0.6, move_x=1 / 3):
        """CubicValue (x1, y1, x2, y2) for one leg: slope v0 at the start and v1 at the end (or the leg's own ease)."""
        T = leg["t1"] - leg["t0"]
        s0, s1 = leg["s0"], leg["s1"]
        if leg.get("ease"):
            x1, y1, x2, y2 = leg["ease"]
            return (x1, s0 + y1 * (s1 - s0), x2, s0 + y2 * (s1 - s0))
        a = rest_x if leg["v0"] == 0 else move_x
        b = rest_x if leg["v1"] == 0 else move_x
        y1 = s0 + leg["v0"] * a * T
        y2 = s1 - leg["v1"] * b * T
        y1 = min(y1, s1)
        y2 = max(y2, s0)
        return (a, y1, 1 - b, y2)

    # ------------------------------------------------------------ RML
    def path_shape(self):
        kids = []
        for v in self.verts:
            x, y = v["p"]
            attrs = {"x": x, "y": y}
            if v["kind"] in ("pass", "slow"):
                dx, dy = v["out"][0] - x, v["out"][1] - y
                din = math.dist(v["in"], v["p"])
                dout = math.hypot(dx, dy)
                kids.append(El("CubicAsymmetricVertex", {"x": x, "y": y, "rotation": math.atan2(dy, dx),
                                                          "inDistance": din, "outDistance": dout}))
                continue
            for k in ("in", "out"):
                h = v[k]
                if h is None:
                    attrs[f"{k}Rotation"], attrs[f"{k}Distance"] = 0.0, 0.0
                else:
                    attrs[f"{k}Rotation"] = math.atan2(h[1] - y, h[0] - x)
                    attrs[f"{k}Distance"] = math.dist(h, v["p"])
            kids.append(El("CubicDetachedVertex", attrs))
        return El("Shape", {"x": 0, "y": 0}, [El("PointsPath", {"isClosed": False}, kids, name=f"{self.name}.pathpts")],
                  name=f"{self.name}.path")
