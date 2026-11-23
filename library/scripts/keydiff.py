"""What changed between two versions of a piece, grouped by element: the keys of every timeline (frames moved, values,
curves) and the static properties. To check "only what was asked changed" before delivering, or what the motion
designer changed by hand in the editor. Works in any folder: it reads only the two scenes.

usage: python lib/biblioteca-<v>/scripts/keydiff.py <A> <B> [--expect REGEX] [--only REGEX] [--anim NAME]
                                                    [--no-static] [--byid] [--tol 0.001] [--full]
  A, B: a scene (scene.rml, a kept scene.rml.txt) or a piece folder (its scene.rml), or a version folder
        (versions/vNN: its scene.rml.txt). An editor .rev: convert it first, `rive create <dir> --from-rev=<file>`
        (read only), and pass <dir>.
  Elements are matched by name (the library names everything; ids shift when a version adds an element); --byid
  matches by id (two builds of the same scene). The editor's RML (`property="opacity"`) and the library's
  (`propertyKey="18"`) compare alike; the editor's omitted defaults are filled in (frame 0, value 0, hold, cubic
  0.42 0 0.58 1).
  Per track: "shift +3 f" when only the frames moved by the same amount, else each key A -> B.
  --expect REGEX: the elements that may change (the request: "CURSOR|cursor"); anything else that changed is listed
        as UNEXPECTED and the exit code is 1. --only: show only these elements. --full: every key, not the summary.
  Ids, references and the editor's bookkeeping (order, positions in its panels) are left out of the static diff.

From pesquisa-precisao/ferramentas-ajuste-mao (keydiff.py + shiftsum.py), into the library in v14.
"""
import argparse
import os
import re
import sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "vendor"))

DEF_CUBIC = (0.42, 0.0, 0.58, 1.0)
IDLIKE = re.compile(r"^-?\d+:\d+(-\d+:\d+)*$")


def key_names():
    try:
        import rive_schema
        return {int(k): v["name"] for k, v in rive_schema.load()["keys"].items()}
    except Exception:
        return {13: "x", 14: "y", 15: "rotation", 16: "scaleX", 17: "scaleY", 18: "opacity"}


KEYS = key_names()


def scene_path(p):
    if os.path.isdir(p):
        for f in ("scene.rml", "scene.rml.txt"):
            if os.path.exists(os.path.join(p, f)):
                return os.path.join(p, f)
        sys.exit(f"no scene.rml (or scene.rml.txt) in {p}")
    return p


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


class Scene:
    def __init__(self, path, byid=False):
        self.path = path
        root = ET.fromstring(open(path, encoding="utf-8").read())
        self.key, self.tag, self.static = {}, {}, {}     # id -> stable key (see _keys), tag, static attributes
        self._keys(root, byid)
        anim_ids = set()
        for tag in ("LinearAnimation", "StateMachine"):
            for a in root.iter(tag):
                anim_ids.update(id(e) for e in a.iter())
        top_art = {id(a) for a in root.findall("Artboard")}
        for el in root.iter():
            i = el.get("id")
            if i is None or id(el) in anim_ids:
                continue
            attrs = {}
            for k, v in el.attrib.items():
                if k in ("id", "name", "order", "editorOnly") or IDLIKE.match(v):
                    continue
                if k in ("x", "y") and id(el) in top_art:     # an artboard's place on the stage
                    continue
                attrs[k] = v
            self.static[self.key[i]] = (el.tag, attrs)
        self.anims = {}
        for ab in root.iter("Artboard"):
            for la in ab.iter("LinearAnimation"):
                tracks = {}
                for ko in la.iter("KeyedObject"):
                    oid = self.key.get(ko.get("objectId"), ko.get("objectId"))
                    for kp in ko.findall("KeyedProperty"):
                        prop = kp.get("property") or KEYS.get(int(kp.get("propertyKey", -1)), kp.get("propertyKey"))
                        keys = []
                        for kf in kp:
                            if not kf.tag.startswith("KeyFrame"):
                                continue
                            k = {"f": int(float(kf.get("frame", 0))),
                                 "v": kf.get("value", "00000000" if kf.tag == "KeyFrameColor" else "0"),
                                 "i": str(kf.get("interpolationType", "hold"))}
                            k["i"] = {"0": "hold", "1": "linear", "2": "cubic", "3": "cubicValue"}.get(k["i"], k["i"])
                            for ip in kf:
                                c = [num(ip.get(a)) for a in ("x1", "y1", "x2", "y2")]
                                c = tuple(round(d if v is None else v, 4) for v, d in zip(c, DEF_CUBIC))
                                k["c"] = c
                                extra = tuple((a, ip.get(a)) for a in ("amplitude", "period", "easingValue")
                                              if ip.get(a) is not None)
                                if extra:
                                    k["x"] = extra
                            if k["i"] in ("cubic", "cubicValue") and "c" not in k:
                                k["c"] = DEF_CUBIC
                            keys.append(k)
                        tracks[(oid, prop)] = keys
                self.anims[f"{ab.get('name')} / {la.get('name') or la.get('id')}"] = (la.get("duration"), tracks)

    def _keys(self, root, byid):
        """A key per element that survives ids shifting between versions: its name when the name (with the tag) is
        unique, else its nearest such ancestor's key + "/Tag[n]" (the n-th child of that tag). byid: the id."""
        count = {}
        for el in root.iter():
            if el.get("name"):
                count[(el.get("name"), el.tag)] = count.get((el.get("name"), el.tag), 0) + 1
        dup = {n for (n, _), c in count.items() if c > 1}

        def walk(el, base):
            seen = {}
            for c in el:
                seen[c.tag] = seen.get(c.tag, 0) + 1
                n = c.get("name")
                if byid and c.get("id"):
                    k = c.get("id")
                elif n and count[(n, c.tag)] == 1:
                    k = n if n not in dup else f"{n} ({c.tag})"
                else:
                    k = f"{base}/{c.tag}[{seen[c.tag]}]"
                if c.get("id"):
                    self.key[c.get("id")] = k
                    self.tag[k] = c.tag
                walk(c, k)
        walk(root, "")

def fmtv(v):
    x = num(v)
    return f"{x:.4g}" if x is not None else v


def fmt_key(k):
    s = f"{k['f']}:{fmtv(k['v'])}"
    if k["i"] != "hold":
        s += f"/{k['i'][:3]}"
    if "c" in k and k["i"] in ("cubic", "cubicValue"):
        s += "(" + " ".join(f"{x:.3g}" for x in k["c"]) + ")"
    if "x" in k:
        s += str(dict(k["x"]))
    return s


def same_v(a, b, tol):
    x, y = num(a), num(b)
    if x is not None and y is not None:
        return abs(x - y) <= tol * max(1.0, abs(x))
    return a == b


def same_curve(a, b):
    ca, cb = a.get("c"), b.get("c")
    if a["i"] != b["i"] or (ca is None) != (cb is None) or a.get("x") != b.get("x"):
        return False
    return ca is None or all(abs(p - q) <= 2e-3 for p, q in zip(ca, cb))


def compare(ka, kb, tol):
    """None when equal, else a one-line summary (shift / values / curves) and whether the summary says it all."""
    if ka is None or kb is None:
        return ("new track" if ka is None else "track removed"), False
    if len(ka) == len(kb) and all(x["f"] == y["f"] and same_v(x["v"], y["v"], tol) and same_curve(x, y)
                                  for x, y in zip(ka, kb)):
        return None
    if len(ka) != len(kb):
        return f"{len(ka)} -> {len(kb)} keys", False
    shifts = sorted({y["f"] - x["f"] for x, y in zip(ka, kb)})
    vals = [(x, y) for x, y in zip(ka, kb) if not same_v(x["v"], y["v"], tol)]
    curves = [(x, y) for x, y in zip(ka, kb) if not same_curve(x, y)]
    parts = []
    if shifts != [0]:
        parts.append(f"shift {shifts[0]:+d} f" if len(shifts) == 1 else
                     "frames " + " ".join(f"{y['f'] - x['f']:+d}" for x, y in zip(ka, kb)))
    if vals:
        parts.append("values " + ", ".join(f"f{x['f']} {fmtv(x['v'])} -> {fmtv(y['v'])}" for x, y in vals[:4])
                     + (" ..." if len(vals) > 4 else ""))
    if curves:
        parts.append("curves " + ", ".join(f"f{x['f']} {fmt_key(x).split('/', 1)[-1]} -> "
                                           f"{fmt_key(y).split('/', 1)[-1]}" for x, y in curves[:3])
                     + (" ..." if len(curves) > 3 else ""))
    return "; ".join(parts), len(shifts) == 1 and not vals and not curves


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("a")
    ap.add_argument("b")
    ap.add_argument("--expect")
    ap.add_argument("--only")
    ap.add_argument("--anim")
    ap.add_argument("--no-static", action="store_true")
    ap.add_argument("--byid", action="store_true")
    ap.add_argument("--tol", type=float, default=1e-3)
    ap.add_argument("--full", action="store_true")
    o = ap.parse_args()
    A, B = Scene(scene_path(o.a), o.byid), Scene(scene_path(o.b), o.byid)
    only = re.compile(o.only) if o.only else None
    expect = re.compile(o.expect) if o.expect else None

    def owner(k):
        """The element a key belongs to: the named element (a vertex of a path belongs to the path's owner)."""
        return k.split("/")[0] or k
    changed = {}          # element -> [lines]
    print(f"A: {A.path}\nB: {B.path}")
    for an in sorted(set(A.anims) | set(B.anims)):
        if o.anim and o.anim not in an:
            continue
        if an not in A.anims or an not in B.anims:
            changed.setdefault(f"(timeline {an})", []).append(f"only in {'A' if an in A.anims else 'B'}")
            continue
        (da, ta), (db, tb) = A.anims[an], B.anims[an]
        if da != db:
            changed.setdefault(f"(timeline {an})", []).append(f"duration {da} -> {db} frames")
        for key in sorted(set(ta) | set(tb), key=lambda k: (k[0], str(k[1]))):
            ka, kb = ta.get(key), tb.get(key)
            r = compare(ka, kb, o.tol)
            if r is None:
                continue
            summary, says_all = r
            sub = key[0][len(owner(key[0])):]
            lines = changed.setdefault(owner(key[0]), [])
            lines.append(f"{sub + ' ' if sub else ''}{key[1]}: {summary}" + (f"   [{an}]" if len(A.anims) > 1 else ""))
            if o.full or not says_all:
                for side, ks in (("A", ka), ("B", kb)):
                    txt = " ".join(fmt_key(k) for k in (ks if o.full else (ks or [])[:10])) if ks else "-"
                    more = f" ... ({len(ks)} keys)" if ks and not o.full and len(ks) > 10 else ""
                    lines.append(f"    {side}: {txt}{more}")
    if not o.no_static:
        sa, sb = A.static, B.static
        gone = {}
        for k in sorted(set(sa) | set(sb)):
            sub = k[len(owner(k)):]
            if k not in sa or k not in sb:
                tag = (sa.get(k) or sb.get(k))[0]
                gone.setdefault((owner(k), "A" if k in sa else "B"), []).append(tag + (sub and f" {sub}"))
                continue
            (tag, xa), (_, xb) = sa[k], sb[k]
            d = [f"{p} {xa.get(p)} -> {xb.get(p)}" for p in sorted(set(xa) | set(xb))
                 if not same_v(xa.get(p), xb.get(p), o.tol)]
            if d:
                changed.setdefault(owner(k), []).append(f"{tag}{sub and ' ' + sub}: " + "; ".join(d)[:300])
        for (el, side), what in sorted(gone.items()):
            changed.setdefault(el, []).append(f"only in {side}: {len(what)} object(s) ({', '.join(what[:4])}"
                                              + (" ..." if len(what) > 4 else "") + ")")
    shown = {e: ls for e, ls in changed.items() if not only or only.search(e)}
    for e in sorted(shown):
        print(f"\n[{e}]")
        for ln in shown[e]:
            print("  " + ln)
    unexpected = sorted(e for e in changed if expect and not expect.search(e))
    print(f"\n{len(changed)} element(s) changed" + (f" ({len(shown)} shown)" if only else ""))
    if expect:
        if unexpected:
            print(f"UNEXPECTED ({len(unexpected)}), outside --expect {o.expect!r}: " + ", ".join(unexpected[:20])
                  + (" ..." if len(unexpected) > 20 else ""))
            sys.exit(1)
        print(f"only what --expect {o.expect!r} names changed")


if __name__ == "__main__":
    main()
