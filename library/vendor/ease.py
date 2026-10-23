"""Evaluate Rive interpolators exactly as frames see them (shared by the extractor, choreo and lint)."""
import math


def cubic_bezier(x1, y1, x2, y2):
    """CSS/Rive cubic-bezier ease: returns f(progress) -> eased progress."""
    def coord(a, b, t):
        u = 1 - t
        return 3 * u * u * t * a + 3 * u * t * t * b + t ** 3

    def f(p):
        if p <= 0:
            return 0.0
        if p >= 1:
            return 1.0
        lo, hi = 0.0, 1.0
        for _ in range(60):
            mid = (lo + hi) / 2
            if coord(x1, x2, mid) < p:
                lo = mid
            else:
                hi = mid
        return coord(y1, y2, (lo + hi) / 2)
    return f


def cubic_value(x1, y1, x2, y2, v0, v1):
    """Rive CubicValueInterpolator: x1/x2 shape time, y1/y2 are values in property units."""
    def coord(a, b, t, p0=0.0, p3=1.0):
        u = 1 - t
        return u ** 3 * p0 + 3 * u * u * t * a + 3 * u * t * t * b + t ** 3 * p3

    span = (v1 - v0) or 1.0

    def f(p):
        if p <= 0:
            return 0.0
        if p >= 1:
            return 1.0
        lo, hi = 0.0, 1.0
        for _ in range(60):
            mid = (lo + hi) / 2
            if coord(x1, x2, mid) < p:
                lo = mid
            else:
                hi = mid
        return (coord(y1, y2, (lo + hi) / 2, v0, v1) - v0) / span
    return f


def elastic(easing=1, amplitude=1.0, period=1.0):
    """Rive ElasticInterpolator (easingValue 0=in, 1=out, 2=inOut)."""
    a = max(amplitude, 1.0)
    p = max(period, 1e-4)
    s = p / 4 if amplitude < 1 else p / (2 * math.pi) * math.asin(1 / a)

    def out(t):
        return a * 2 ** (-10 * t) * math.sin((t - s) * 2 * math.pi / p) + 1

    def f(t):
        if t <= 0:
            return 0.0
        if t >= 1:
            return 1.0
        if easing == 0:
            return 1 - out(1 - t)
        if easing == 2:
            return (1 - out(1 - 2 * t)) / 2 if t < .5 else (out(2 * t - 1) + 1) / 2
        return out(t)
    return f


def from_segment(seg):
    it = seg.get("interp")
    e = seg.get("ease")
    if it == "linear":
        return lambda t: t
    if it == "hold":
        return lambda t: 0.0 if t < 1 else 1.0
    if isinstance(e, list) and e and e[0] == "elastic":
        return elastic(int(e[1]), e[2], e[3])
    if isinstance(e, list) and e and e[0] == "value":
        v0 = seg.get("v0", 0.0)
        return cubic_value(*e[1:], v0, v0 + seg.get("delta", 1.0))
    if isinstance(e, list) and len(e) == 4:
        return cubic_bezier(*e)
    return cubic_bezier(0.42, 0, 0.58, 1)


def frame_profile(f, n_frames):
    """Fractions of the total change covered by each output frame (len n_frames)."""
    n = max(1, int(round(n_frames)))
    pts = [f(k / n) for k in range(n + 1)]
    return [abs(b - a) for a, b in zip(pts, pts[1:])]
