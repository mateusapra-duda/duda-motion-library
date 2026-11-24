"""What the motion designer changed by hand in the Rive editor, in beat terms: our build against his file, so a new
version never loses a hand edit. A text report, and JSON for a later step that re-applies the edits.

usage: python $L/scripts/handdiff.py <ours> <his> [--json out.json] [--anim NAME] [--only REGEX] [--all] [--tol 0.001]
  ours: the build his edit started from (best: the .rev we delivered, or versions/vNN), or our current build: a piece
        folder (its scene.rml), a version folder (its scene.rml.txt), a .rml / .rml.txt, or a .rev
  his:  his .rev (exported from the editor), or the folder of `rive create <dir> --from-remote-file=<id>` (read only)
  A .rev is converted with `rive create --from-rev` into a cache (--work, default <tmp>/handdiff), never next to it.
  A .riv can't be read back by the CLI: ask for the .rev, or read his file from the account (--from-remote-file).

What it lists, per timeline, in frames and seconds (the timeline's fps; the editor leaves out the default 60):
- the timeline: length, fps, loop, work area; timelines only in one file;
- shifts: keys that moved together ("from f149 on: -37 f"), the most common hand edit; a track that only follows a
  shift is folded into it, the others show their own move and the move relative to the shift;
- each cursor (a Follow Path): its path in px (points moved, length), size, where it shows and vanishes, the presses,
  and each leg between two stops (frames, px, curve) with the press lead (press -> stop) and the peak speed. Follow
  Path % become px on each file's own path;
- every other changed track, by element: keys moved, values, curves (normalised 0-1 and named when they match the
  library's curves or tokens: "= cursor glide", "~ 80 80"), keys added or removed, and the moves on both sides
  ("0->1 f13-33 (20 f, linear)");
- elements added, removed or renamed; changed attributes (paths, texts...); state machines; view models.
Matched by name path, never by id (his ids differ from ours). Left out as noise: ids, float formatting (--tol),
attributes the editor keeps for itself (from `rive schema --all`: playhead, viewStart/End, expandedComponents...),
values the editor leaves out (the schema's defaults fill them in), the interpolation of a last key or of a flat
segment (never plays), the assets' files. --all lists the attribute changes the report folds.

JSON (--json): timelines, shifts, tracks (each with all of ours and his keys: frame, value, interpolation, raw and
normalised curve, so a step can set his track as it is), cursors (his path vertices and tracks, the derived beats),
elements, state machines, view models, and what was filtered.
"""
import argparse
import hashlib
import json
import math
import os
import re
import subprocess
import sys
import tempfile
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)                                  # python -I leaves the script's folder out
sys.path.insert(1, os.path.join(HERE, ".."))              # the library (hand, cuts): the curves' names
import keydiff  # noqa: E402
from keydiff import Scene, num  # noqa: E402
import hand  # noqa: E402
import cuts  # noqa: E402
import choreo  # noqa: E402
import ease  # noqa: E402

IDLIKE = keydiff.IDLIKE
SKIP_ATTRS = {"id", "name", "order", "editorOnly", "file", "propertyKey", "property", "objectId", "complexDependency",
              "isClockwise"}                              # isClockwise: the editor tracks the drawing's direction
MASK = {"pathFlags": 1}       # the bits that are an edit (bit 1 of pathFlags: the vertices' direction, the editor's)
EDITOR_SETS = {"componentProps"}                         # the editor marks these when it opens a file the CLI wrote
SKIP_TAGS = ("FocusData",)                                # keyboard focus bookkeeping, nothing that moves
NO_DEFAULT = {"double": "0", "uint": "0", "bool": "0", "String": ""}   # what a property with no schema default is
KEEP_EDITOR = {"includeInExport"}                         # editor-only, but it changes what the export holds
ASSETS = ("FontAsset", "ImageAsset", "AudioAsset", "FileAsset", "FileAssetContents", "ScriptAsset")
VM_TAGS = ("ViewModel", "DataBind", "DataConverter", "DataEnum", "Enum", "BindableProperty")
EXACT, NEAR = 0.02, 0.06                                  # a curve "= name" / "~ name" within these (per handle)


# ------------------------------------------------------------------------------------------------ inputs
def rive_bin():
    try:
        import bins
        return bins.rive()
    except Exception:
        return os.path.expanduser("~/.rive/bin/rive")


def resolve(p, work):
    """The scene file of an input: a folder, an RML file, or a .rev converted into the cache."""
    p = os.path.expanduser(p)
    if p.endswith(".riv"):
        sys.exit(f"{p}: a .riv can't be read back. Use his .rev (the editor's File > Export > .rev), or read his file "
                 f"from the account: rive create <dir> --from-remote-file=<id> (then remove push: from its rive.yaml)")
    if p.endswith(".rev"):
        h = hashlib.sha1(open(p, "rb").read()).hexdigest()[:12]
        out = os.path.join(work, f"{os.path.splitext(os.path.basename(p))[0]}-{h}")
        if not os.path.exists(os.path.join(out, "scene.rml")):
            os.makedirs(work, exist_ok=True)
            r = subprocess.run([rive_bin(), "create", out, f"--from-rev={p}"], capture_output=True, text=True,
                               timeout=300)
            if not os.path.exists(os.path.join(out, "scene.rml")):
                sys.exit(f"rive create --from-rev failed on {p}:\n{(r.stdout + r.stderr)[-1500:]}")
        return os.path.join(out, "scene.rml")
    return keydiff.scene_path(p)


# ------------------------------------------------------------------------------------------------ the schema
class Schema:
    """Each type's properties from `rive schema --json [--all] <Type>`: default, kind, enum values, editor-only."""

    def __init__(self, work):
        self.rive = rive_bin()
        stamp = int(os.path.getmtime(self.rive)) if os.path.exists(self.rive) else 0
        self.cache = os.path.join(work, f"schema4-{stamp}.json")
        try:
            self.types = json.load(open(self.cache))
        except Exception:
            self.types = {}
        self.dirty = False

    def _query(self, tag, every):
        try:
            out = subprocess.run([self.rive, "schema", "--json"] + (["--all"] if every else []) + [tag],
                                 capture_output=True, text=True, timeout=30).stdout
            return json.loads(out[out.index("{"):]).get("properties", [])
        except Exception:
            return None

    def props(self, tag):
        if tag not in self.types:
            every, public = self._query(tag, True), self._query(tag, False)
            pub = {p["name"] for p in public or []}
            self.types[tag] = None if every is None else {
                p["name"]: {"default": p.get("default"), "kind": p.get("type"),
                            "values": {v["name"]: str(v["value"]) for v in p.get("values", [])},
                            "bits": p.get("bits") or [], "owner": p.get("owner"), "name": p["name"],
                            "editor": p["name"] not in pub, "derived": p.get("derived", False)} for p in every}
            self.dirty = True
        return self.types[tag]

    def save(self):
        if self.dirty:
            try:
                json.dump(self.types, open(self.cache, "w"))
            except OSError:
                pass


class Norm:
    """Attribute values made comparable across our RML and the editor's: defaults, enums, bools, references."""

    def __init__(self, schema, scene):
        self.schema, self.scene = schema, scene
        self.filtered = Counter()

    def ref(self, v):
        return "/".join(self.scene.key.get(x, x if not IDLIKE.match(x) else "?") for x in v.split("-")) \
            if IDLIKE.match(v) else self.scene.key.get(v, v)

    def attrs(self, el):
        """{attribute: comparable value} of an element: what the schema knows, the editor's own left out. The flags'
        bits (RML writes hidden="true", the editor may write flags="1") become one attribute each."""
        props = self.schema.props(el.tag) or {}
        bits = (props.get("flags") or {}).get("bits", [])
        out = {}
        for a, v in el.attrib.items():
            if a in SKIP_ATTRS:
                continue
            if a in EDITOR_SETS:
                self.filtered["attributes the editor sets on opening (componentProps)"] += 1
                continue
            if a == "flags" and bits:
                for i, b in enumerate(bits):
                    if (int(float(v)) >> i) & 1:
                        out.setdefault(b, "1")
                continue
            if a in bits:
                out[a] = {"true": "1", "false": "0"}.get(v, v)
                continue
            p = props.get(a)
            if p is not None and (p["editor"] and a not in KEEP_EDITOR or p["kind"] == "FractionalIndex"
                                  or p["derived"]):
                self.filtered["editor-only attributes"] += 1
                continue
            if p is None:
                out[a] = ("?", self.value(p, v))       # unknown to the schema: compared only when both have it
                continue
            out[a] = self.value(p, v)
        return out

    def default(self, tag, a):
        props = self.schema.props(tag) or {}
        if a in (props.get("flags") or {}).get("bits", []):
            return "0"
        p = props.get(a)
        if p is None:
            return None
        self.filtered["defaults filled in"] += 1
        if p["default"] is None:
            return NO_DEFAULT.get(p["kind"])
        return self.value(p, p["default"])

    def full(self, el, mine, other):
        """mine (attrs() of el) with the schema's default for every attribute the other side has and el leaves out."""
        a = dict(mine)
        for k in other:
            if k not in a:
                a[k] = self.default(el.tag, k)
        return a

    def value(self, p, v):
        if p is None:
            return self.ref(v) if IDLIKE.match(v) else v
        k = p["kind"]
        if p.get("owner") == "ListenerAction" and v.isdigit():   # bits 1-2: the parent's kind, from the nesting
            return str(int(v) & 1)
        if p.get("name", "") in MASK and v.isdigit():
            return str(int(v) & MASK[p["name"]])
        if k in ("Id", "List<Id>"):
            self.filtered["references by name"] += 1
            return self.ref(v)
        if k == "bool":
            return {"true": "1", "false": "0"}.get(v, v)
        if k == "Color":
            return v.upper().replace("0X", "").replace("#", "")
        if p["values"] and v in p["values"]:
            return p["values"][v]
        return v


def same(a, b, tol):
    x, y = num(a), num(b)
    if x is not None and y is not None:
        return abs(x - y) <= tol * max(1.0, abs(x))
    if a is None or b is None:
        return a == b
    return re.sub(r"\s+", " ", str(a)).strip().upper() == re.sub(r"\s+", " ", str(b)).strip().upper()


# ------------------------------------------------------------------------------------------------ curves
def known_curves():
    """Named curves: the library's (hand, cuts), the motion tokens and a few of his files'."""
    out = []

    def add(name, c):
        c = tuple(float(x) for x in c)
        if not any(max(abs(p - q) for p, q in zip(c, c2)) < 1e-3 for _, c2 in out):
            out.append((name, c))
    add("cursor entry", hand.ENTER)
    add("cursor glide", hand.GLIDE)
    add("cursor creep", hand.CREEP_CURVE)
    add("80 80 (duda_strong)", choreo.TOKENS["ease"]["duda_strong"]["bezier"])
    add("80 80, his handle (zoom out)", cuts.OPEN["ease"])
    add("settle", choreo.TOKENS["ease"]["settle"]["bezier"])
    add("cut exit", cuts.EXIT)
    add("jump cut slide", cuts.JUMP["out_ease"])
    add("scroll (his)", cuts.SCROLL["ease"])
    add("camera slow zoom", cuts.CAMERA["slow_ease"])
    for name, t in choreo.TOKENS["ease"].items():
        if isinstance(t.get("bezier"), list):
            add({"gradient": "0.6 0 0.4 1 (old cursor / scroll token)"}.get(name, name), t["bezier"])
    add("Rive's default ease", keydiff.DEF_CUBIC)
    # from his files, not constants of the library
    add("his two-key entry, 1st (marketing-automation v15.12)", (0.0, 0.0, 0.2215, 0.614))
    add("his two-key entry, 2nd", (0.641, 0.361, 0.1835, 1.0))
    add("generation pass", (0.588, 0.0, 0.377, 1.0))
    add("prompt typing", (0.1804, 0.0442, 0.2292, 0.676))
    add("photo settle", (0.16, 1.0, 0.3, 1.0))
    return out


KNOWN = known_curves()


def curve_name(c):
    if not isinstance(c, tuple) or len(c) != 4:
        return ""
    best = min(KNOWN, key=lambda kc: max(abs(p - q) for p, q in zip(c, kc[1])))
    d = max(abs(p - q) for p, q in zip(c, best[1]))
    return f"= {best[0]}" if d <= EXACT else f"~ {best[0]}" if d <= NEAR else ""


def curve_txt(cn):
    if cn is None:
        return "hold"
    if cn == "linear":
        return "linear"
    if isinstance(cn, tuple) and cn and cn[0] == "elastic":
        return "elastic " + " ".join(f"{a}={v}" for a, v in cn[1:])
    s = " ".join(f"{round(x, 3) + 0.0:g}" for x in cn)
    n = curve_name(cn)
    return f"{s} {n}".strip()


# ------------------------------------------------------------------------------------------------ tracks
class Key:
    __slots__ = ("f", "v", "n", "i", "c", "x", "cn", "last")

    def __init__(self, k):
        self.f, self.v, self.i, self.c, self.x = k["f"], k["v"], k["i"], k.get("c"), k.get("x")
        self.n = num(self.v)
        self.cn, self.last = None, False

    def json(self, fps):
        d = {"frame": self.f, "s": round(self.f / fps, 4), "value": self.n if self.n is not None else self.v,
             "interp": self.i}
        if self.c is not None:
            d["curve_raw"] = list(self.c)
        if isinstance(self.cn, tuple) and self.cn[0] != "elastic":
            d["curve"] = [round(x, 4) for x in self.cn]
            if curve_name(self.cn):
                d["curve_name"] = curve_name(self.cn)
        if self.x:
            d["extra"] = dict(self.x)
        return d


def prep(raw, tol):
    """Keys with their curve normalised to 0-1 (cn): None where nothing plays (hold, a flat segment, the last key)."""
    ks = [Key(k) for k in raw]
    for a, b in zip(ks, ks[1:]):
        if a.i == "hold" or same(a.v, b.v, tol):
            a.cn = None
        elif a.i == "linear":
            a.cn = "linear"
        elif a.i in ("cubic", "cubicValue") and a.c:
            x1, y1, x2, y2 = a.c
            if a.i == "cubicValue":
                if a.n is None or b.n is None or b.n == a.n:
                    a.cn = a.c
                    continue
                y1, y2 = (y1 - a.n) / (b.n - a.n), (y2 - a.n) / (b.n - a.n)
            c = (x1, y1, x2, y2)
            a.cn = "linear" if abs(y1 - x1) < 2e-3 and abs(y2 - x2) < 2e-3 else c
        elif a.i == "elastic":
            a.cn = ("elastic",) + tuple(a.x or ())
        else:
            a.cn = a.i
    if ks:
        ks[-1].last = True
    return ks


def same_curve(a, b):
    if a.cn is None or b.cn is None or a.cn == "linear" or b.cn == "linear" or isinstance(a.cn, str) \
            or isinstance(b.cn, str) or a.cn[0] == "elastic" or b.cn[0] == "elastic":
        return a.cn == b.cn
    return all(abs(p - q) <= 5e-3 for p, q in zip(a.cn, b.cn))


def same_key(a, b, tol):
    return a.f == b.f and same(a.v, b.v, tol) and (a.last and b.last or same_curve(a, b))


def align(ka, kb, tol):
    """Pairs (a, b), (a, None) removed, (None, b) added: an edit alignment that pairs equal values, then near frames."""
    n, m = len(ka), len(kb)
    if n == m and all(same(a.v, b.v, tol) for a, b in zip(ka, kb)):
        return list(zip(ka, kb))
    GAP = 1.0

    def cost(a, b):
        return (0.0 if same(a.v, b.v, tol) else 0.55) + 0.4 * min(abs(a.f - b.f) / 120.0, 1.0)
    D = [[0.0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        D[i][0] = i * GAP
    for j in range(1, m + 1):
        D[0][j] = j * GAP
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            D[i][j] = min(D[i - 1][j - 1] + cost(ka[i - 1], kb[j - 1]), D[i - 1][j] + GAP, D[i][j - 1] + GAP)
    out, i, j = [], n, m
    while i or j:
        if i and j and abs(D[i][j] - (D[i - 1][j - 1] + cost(ka[i - 1], kb[j - 1]))) < 1e-9:
            out.append((ka[i - 1], kb[j - 1]))
            i, j = i - 1, j - 1
        elif i and abs(D[i][j] - (D[i - 1][j] + GAP)) < 1e-9:
            out.append((ka[i - 1], None))
            i -= 1
        else:
            out.append((None, kb[j - 1]))
            j -= 1
    return out[::-1]


def fv(v):
    if v is None:
        return "(unset)"
    x = num(v)
    return f"{x:.4g}" if x is not None else str(v)


def moves(ks, fps, limit=8):
    """The moves of a track in words: '@f0 v' then 'a->b f1-f2 (n f, curve)' or 'a->b at f2' (a jump)."""
    if not ks:
        return "-"
    out = [f"@f{ks[0].f} {fv(ks[0].v)}"]
    for a, b in zip(ks, ks[1:]):
        if a.cn is None and same(a.v, b.v, 1e-6):
            continue
        if a.cn is None:
            out.append(f"{fv(a.v)}->{fv(b.v)} at f{b.f}")
        else:
            out.append(f"{fv(a.v)}->{fv(b.v)} f{a.f}-{b.f} ({b.f - a.f} f, {curve_txt(a.cn)})")
    more = len(out) - 1 - limit
    return " · ".join(out[:limit + 1]) + (f" · ... ({more} more moves)" if more > 0 else "")


def dfs(df, fps):
    return f"{df:+d} f ({df / fps:+.2f} s)"


def track_change(ka, kb, tol, fps):
    """None when the same; else {kind, shift, ops}: ops are (kind, a, b) for each pair that differs."""
    if len(ka) == len(kb) and all(same_key(a, b, tol) for a, b in zip(ka, kb)):
        return None
    pairs = align(ka, kb, tol)
    ops = []
    for a, b in pairs:
        if a is None:
            ops.append(("added", a, b))
        elif b is None:
            ops.append(("removed", a, b))
        else:
            what = []
            if a.f != b.f:
                what.append("moved")
            if not same(a.v, b.v, tol):
                what.append("value")
            if not (a.last or b.last) and not same_curve(a, b):
                what.append("curve")
            if what:
                ops.append(("+".join(what), a, b))
    if not ops:
        return None
    shifts = {b.f - a.f for k, a, b in ops if k == "moved"}
    pure = all(k == "moved" for k, _, _ in ops) and len(shifts) == 1 and \
        len([1 for a, b in pairs if a and b and a.f == b.f]) == 0
    return {"kind": "shift" if pure else "edit", "shift": shifts.pop() if pure else None, "ops": ops, "pairs": pairs}


def op_txt(kind, a, b, fps, rel=None):
    if kind == "added":
        return f"+ key f{b.f}: {fv(b.v)}" + ("" if b.last else f" ({curve_txt(b.cn)})")
    if kind == "removed":
        return f"- key f{a.f}: {fv(a.v)}"
    parts = []
    if "moved" in kind:
        parts.append(f"f{a.f} -> f{b.f} ({b.f - a.f:+d}" + (f", {b.f - a.f - rel:+d} past the shift"
                                                             if rel and b.f - a.f != rel else "") + ")")
    else:
        parts.append(f"f{a.f}")
    if "value" in kind:
        parts.append(f"value {fv(a.v)} -> {fv(b.v)}")
    if "curve" in kind:
        parts.append(f"curve {curve_txt(a.cn)} -> {curve_txt(b.cn)}")
    return " ".join(parts)


# ------------------------------------------------------------------------------------------------ cursors
def vertices(pp, dx, dy):
    """P, in-handles, out-handles of a PointsPath, in the artboard (offset by its shape and parents)."""
    P, hin, hout = [], [], []
    for v in pp:
        if not v.tag.endswith("Vertex"):
            continue
        f = lambda k: float(v.get(k, 0))  # noqa: E731
        x, y = f("x") + dx, f("y") + dy
        if v.tag == "CubicDetachedVertex":
            ri, di, ro, do = f("inRotation"), f("inDistance"), f("outRotation"), f("outDistance")
        elif v.tag in ("CubicAsymmetricVertex", "CubicMirroredVertex"):
            r = f("rotation")
            di = f("inDistance") if v.tag == "CubicAsymmetricVertex" else f("distance")
            do = f("outDistance") if v.tag == "CubicAsymmetricVertex" else f("distance")
            ri, ro = r + math.pi, r
        else:
            ri = di = ro = do = 0.0
        P.append((x, y))
        hin.append((x + math.cos(ri) * di, y + math.sin(ri) * di))
        hout.append((x + math.cos(ro) * do, y + math.sin(ro) * do))
    return P, hin, hout


def value_at(ks, f):
    if not ks:
        return None
    if f <= ks[0].f:
        return ks[0].n
    for a, b in zip(ks, ks[1:]):
        if f < b.f:
            if a.cn is None or a.n is None or b.n is None:
                return a.n
            u = (f - a.f) / (b.f - a.f)
            if a.cn == "linear":
                return a.n + (b.n - a.n) * u
            if isinstance(a.cn, tuple) and a.cn[0] != "elastic":
                return a.n + (b.n - a.n) * ease.cubic_bezier(*a.cn)(u)
            return a.n + (b.n - a.n) * u
    return ks[-1].n


class Cursor:
    """A Follow Path's ride in one timeline: path in px, shows, vanishes, presses, legs between stops."""

    def __init__(self, sc, fp, parent, timeline, tol):
        self.name = sc.key.get(parent[fp].get("id"), parent[fp].get("name")) if fp in parent else fp.get("name")
        node = parent.get(fp)
        self.warn = []
        shape = next((e for e in sc.root.iter() if e.get("id") == fp.get("targetId")), None)
        pp = next(shape.iter("PointsPath"), None) if shape is not None else None
        dx = dy = 0.0
        e = shape
        while e is not None and e.tag != "Artboard":
            dx, dy = dx + float(e.get("x", 0)), dy + float(e.get("y", 0))
            if any(abs(float(e.get(a, d)) - d) > 1e-6 for a, d in (("rotation", 0), ("scaleX", 1), ("scaleY", 1))):
                self.warn.append(f"{e.get('name') or e.tag} is rotated or scaled: px measured without it")
            e = parent.get(e)
        self.P, self.hin, self.hout = vertices(pp, dx, dy) if pp is not None else ([], [], [])
        self.raw_vertices = [(v.tag, dict((k, x) for k, x in v.attrib.items() if k != "id"))
                             for v in (pp if pp is not None else []) if v.tag.endswith("Vertex")]
        self.path = None
        if len(self.P) >= 2:
            self.path = hand.Path.__new__(hand.Path)
            self.path._build(self.P, self.hin, self.hout, 240)
        self.L = self.path.length if self.path else 0.0
        tracks = sc.anims[timeline][1]
        fk = sc.key.get(fp.get("id"))
        nk = sc.key.get(node.get("id")) if node is not None else None
        self.keys = {"distance": prep(tracks.get((fk, "distance"), []), tol)}
        for prop in ("opacity", "scaleX"):
            raw = tracks.get((nk, prop))
            if raw is None:                       # on a named child of the node (its art)
                raw = next((v for (o, p), v in tracks.items() if p == prop and o and nk and o.startswith(nk + ".")),
                           [])
            self.keys[prop] = prep(raw, tol)
        self.track_ids = {(fk, "distance"), (nk, "opacity"), (nk, "scaleX"), (nk, "scaleY")}
        rest = node.get("scaleX") if node is not None else None
        sk = self.keys["scaleX"]
        self.rest = Counter(round(k.n, 4) for k in sk if k.n is not None).most_common(1)[0][0] if sk else \
            float(rest if rest is not None else 1)
        self.active = bool(self.keys["distance"])

    def pos(self, d):
        return self.path.pos(d) if self.path else (0.0, 0.0)

    def fades(self, up):
        out, ks = [], self.keys["opacity"]
        for a, b in zip(ks, ks[1:]):
            if a.n is None or b.n is None:
                continue
            if (up and a.n <= 0.01 and b.n >= 0.99) or (not up and a.n >= 0.99 and b.n <= 0.01):
                out.append((b.f if a.cn is None else a.f, b.f))
        return out

    def presses(self):
        out, ks = [], self.keys["scaleX"]
        for i, (a, b) in enumerate(zip(ks, ks[1:])):
            if a.n is not None and b.n is not None and abs(a.n - self.rest) < 1e-3 and b.n < self.rest - 0.02:
                back = next((k.f for k in ks[i + 2:] if k.n is not None and abs(k.n - self.rest) < 1e-3), None)
                out.append({"start": a.f, "bottom": b.f, "back": back, "depth": round(b.n / self.rest, 3)})
        return out

    def legs(self):
        """Moves between two stops: frames, px, the curve of each segment, peak px/frame."""
        ks, out, cur = self.keys["distance"], [], None
        for a, b in zip(ks, ks[1:]):
            moving = a.cn is not None and a.n is not None and b.n is not None and abs(b.n - a.n) > 1e-6
            if moving:
                if cur is None:
                    cur = {"start": a.f, "from": a.n, "segs": []}
                cur["segs"].append((a, b))
                cur["end"], cur["to"] = b.f, b.n
            elif cur is not None:
                out.append(cur)
                cur = None
        if cur is not None:
            out.append(cur)
        for lg in out:
            lg["frames"] = lg["end"] - lg["start"]
            lg["px"] = round((lg["to"] - lg["from"]) * self.L, 1)
            lg["curves"] = [s[0].cn for s in lg["segs"]]
            prev, peak = self.pos(lg["from"]), 0.0
            for f in range(lg["start"] + 1, lg["end"] + 1):
                p = self.pos(value_at(ks, f))
                peak, prev = max(peak, math.dist(p, prev)), p
            lg["peak"] = round(peak, 1)
            lg["at"] = [round(x, 1) for x in self.pos(lg["to"])]
        return out

    def beats(self):
        shows, gone, presses, legs = self.fades(True), self.fades(False), self.presses(), self.legs()
        for p in presses:                       # press lead: frames from the press to the stop it lands on
            lg = min(legs, key=lambda g: abs(g["end"] - p["start"])) if legs else None
            p["lead"] = lg["end"] - p["start"] if lg else None
        after = []                              # each vanish: frames since the last press before it
        for g0, _ in gone:
            before = [p["start"] for p in presses if p["start"] <= g0]
            after.append(g0 - before[-1] if before else None)
        return {"length_px": round(self.L, 1), "points": [[round(x, 1), round(y, 1)] for x, y in self.P],
                "size": round(self.rest, 4), "shows": shows, "vanishes": gone, "presses": presses,
                "vanish_after_last_press": after,
                "legs": [{k: v for k, v in lg.items() if k != "segs"} | {
                    "from_px": round(lg["from"] * self.L, 1), "to_px": round(lg["to"] * self.L, 1),
                    "curves": [[round(x, 4) for x in c] if isinstance(c, tuple) else c for c in lg["curves"]],
                    "curve_names": [curve_name(c) for c in lg["curves"]]} for lg in legs],
                # Follow Path % -> px on this file's path: each distance key, where it puts the cursor
                "distance_keys": [{"frame": k.f, "value": k.n, "px": round((k.n or 0) * self.L, 1),
                                   "xy": [round(v, 1) for v in self.pos(k.n or 0)], "interp": k.i,
                                   "curve_raw": list(k.c) if k.c else None} for k in self.keys["distance"]]}


def find_cursors(sc, parent, timeline, tol):
    out = {}
    for fp in sc.root.iter("FollowPathConstraint"):
        c = Cursor(sc, fp, parent, timeline, tol)
        if c.active or c.keys["opacity"]:
            out[c.name] = c
    return out


def pair_by_frame(xa, xb, fa):
    """Pair two lists of events by order when they have as many, else each of ours with his nearest (in frames)."""
    if len(xa) == len(xb):
        return list(zip(xa, xb))
    used, out = set(), []
    for a in xa:
        cand = [(abs(fa(b) - fa(a)), j) for j, b in enumerate(xb) if j not in used]
        if cand and min(cand)[0] <= 90:
            j = min(cand)[1]
            used.add(j)
            out.append((a, xb[j]))
        else:
            out.append((a, None))
    out += [(None, b) for j, b in enumerate(xb) if j not in used]
    return out


def cursor_report(name, ca, cb, fps, lines):
    A, B = ca.beats() if ca else None, cb.beats() if cb else None
    lines.append(f"\n== cursor {name}")
    if not A or not B:
        lines.append(f"  only in {'ours' if A else 'his'}")
        return {"name": name, "ours": A, "his": B}
    for w in sorted(set(ca.warn + cb.warn)):
        lines.append(f"  ! {w}")
    moved = []
    if len(ca.P) == len(cb.P):
        for i, (p, q) in enumerate(zip(ca.P, cb.P)):
            hd = max(math.dist(ca.hin[i], cb.hin[i]), math.dist(ca.hout[i], cb.hout[i]))
            d = math.dist(p, q)
            if d > 0.5:
                moved.append(f"point {i + 1} moved {d:.0f} px ({p[0]:.1f}, {p[1]:.1f}) -> ({q[0]:.1f}, {q[1]:.1f})")
            elif hd > 0.5:
                moved.append(f"point {i + 1}: handles moved (up to {hd:.0f} px)")
    else:
        moved.append(f"{len(ca.P)} -> {len(cb.P)} points: " + " ".join(f"({x:.0f},{y:.0f})" for x, y in cb.P))
    lines.append(f"  path: {A['length_px']:.0f} -> {B['length_px']:.0f} px, {len(ca.P)} -> {len(cb.P)} points"
                 + ("" if moved else " (same)"))
    for m in moved:
        lines.append(f"     {m}")
    sz = "same" if abs(A["size"] - B["size"]) < 1e-3 else f"{B['size'] * 100:.0f} %"
    lines.append(f"  size: {A['size'] * 100:.0f} % -> {sz}")

    def spans(xs):
        return " ".join(f"f{a}-{b} ({b - a} f)" for a, b in xs) or "-"
    for lab, k in (("shows", "shows"), ("vanishes", "vanishes")):
        same_ = A[k] == B[k]
        lines.append(f"  {lab}: {spans(A[k])} -> " + ("same" if same_ else spans(B[k])))
    pa, pb = A["presses"], B["presses"]
    lines.append(f"  presses: {' '.join('f%d' % p['start'] for p in pa) or '-'} -> "
                 + ("same" if [p["start"] for p in pa] == [p["start"] for p in pb] else
                    " ".join("f%d" % p["start"] for p in pb) or "-"))
    pp = pair_by_frame(pa, pb, lambda p: p["start"])
    if any(a and b and a["start"] != b["start"] for a, b in pp):
        lines.append("     moved: " + " ".join(f"{b['start'] - a['start']:+d}" if a and b else ("new" if b else "gone")
                                               for a, b in pp))
    da = [(p["depth"], p["bottom"] - p["start"], (p["back"] or p["bottom"]) - p["bottom"]) for p in pa]
    db = [(p["depth"], p["bottom"] - p["start"], (p["back"] or p["bottom"]) - p["bottom"]) for p in pb]
    if da != db:
        lines.append("     shape (depth, in, out f): " + " ".join(f"{d}/{i}+{o}" for d, i, o in da) + " -> "
                     + " ".join(f"{d}/{i}+{o}" for d, i, o in db))
    la, lb = [p.get("lead") for p in pa], [p.get("lead") for p in pb]
    lines.append(f"  press -> stop (f): {' '.join(map(str, la)) or '-'} -> "
                 + ("same" if la == lb else " ".join(map(str, lb)) or "-"))
    va, vb = A["vanish_after_last_press"], B["vanish_after_last_press"]
    lines.append(f"  last press -> vanish (f): {' '.join(map(str, va)) or '-'} -> "
                 + ("same" if va == vb else " ".join(map(str, vb)) or "-"))
    lines.append("  legs (frames, px, curve per segment; peak px/f):")
    for i, (a, b) in enumerate(pair_by_frame(A["legs"], B["legs"], lambda g: g["start"])):
        def leg(g):
            if g is None:
                return "-"
            cv = " + ".join(curve_txt(tuple(c) if isinstance(c, list) else c) for c in g["curves"])
            return f"f{g['start']}-{g['end']} ({g['frames']} f) {abs(g['px']):.0f} px  {cv}  peak {g['peak']}"
        if a and b and a["start"] == b["start"] and a["end"] == b["end"] and abs(a["px"] - b["px"]) < 1 and \
                a["curves"] == b["curves"]:
            lines.append(f"     {i + 1}. same: {leg(a)}")
            continue
        lines.append(f"     {i + 1}. ours {leg(a)}")
        lines.append(f"        his  {leg(b)}")
    return {"name": name, "ours": A, "his": B, "his_vertices": cb.raw_vertices}


# ------------------------------------------------------------------------------------------------ structure
def static_items(sc, skip):
    """{key: element} outside timelines and state machines."""
    out = {}
    for k, e in sc.el.items():
        if id(e) in skip:
            continue
        out[k] = e
    return out


def inside(sc, tags):
    s = set()
    for t in tags:
        for a in sc.root.iter(t):
            s.update(id(e) for e in a.iter())
    return s


def sm_lines(sc, norm):
    """Every state machine as {path: (tag, {attr: value})}: states by their timeline, transitions by their target, a
    second sibling with the same label numbered (#2); references inside the machine by these paths."""
    out = {}
    anim_name = {x.get("id"): x.get("name") for x in sc.root.iter("LinearAnimation")}
    for ab in sc.root.iter("Artboard"):
        for sm in ab.iter("StateMachine"):
            base = f"{ab.get('name')} / {sm.get('name')}"
            path, order = {}, []

            def label(e):
                if e.tag == "AnimationState":
                    return f"AnimationState[{anim_name.get(e.get('animationId'), e.get('animationId'))}]"
                return f"{e.tag}[{e.get('name')}]" if e.get("name") else e.tag

            def walk(e, p):
                used = Counter()
                for c in e:
                    lb = label(c)
                    used[lb] += 1
                    cp = f"{p}/{lb}" + (f"#{used[lb]}" if used[lb] > 1 else "")
                    path[id(c)] = cp
                    order.append(c)
                    walk(c, cp)
            walk(sm, base)
            by_id = {c.get("id"): path[id(c)] for c in order if c.get("id")}
            for c in order:
                p = path[id(c)]
                if c.tag == "StateTransition":           # by its target (the source is its parent)
                    tgt = by_id.get(c.get("stateToId"), "?").rsplit("/", 1)[-1]
                    p = p.rsplit("/", 1)[0] + f"/StateTransition[-> {tgt}]"
                    n = 2
                    while p in out:
                        p, n = p.split("]#")[0].rstrip("]") + f"]#{n}", n + 1
                a = norm.attrs(c)
                for k in list(a):
                    if c.get(k) in by_id:
                        a[k] = by_id[c.get(k)][len(base) + 1:]
                out[p] = (c.tag, a)
    return out


def tidy(tag, a):
    """A vertex handle under 0.01 px has no direction to speak of: its rotation is left out (the editor zeroes it)."""
    if tag.endswith("Vertex"):
        for side in ("in", "out"):
            if abs(num(a.get(f"{side}Distance")) or 0.0) < 0.01:
                a.pop(f"{side}Rotation", None)
    return a


def diff_dicts(da, db, tol, filtered=None):
    """{attribute: (ours, his)} that differ; an attribute unknown to the schema counts only when both have it."""
    out = {}
    for k in sorted(set(da) | set(db)):
        x, y = da.get(k), db.get(k)
        if isinstance(x, tuple) or isinstance(y, tuple):
            if x is None or y is None:
                if filtered is not None:
                    filtered["attributes unknown to the schema, on one side"] += 1
                continue
            x, y = x[1] if isinstance(x, tuple) else x, y[1] if isinstance(y, tuple) else y
        if not same(x, y, tol):
            out[k] = (x, y)
    return out


# ------------------------------------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ours")
    ap.add_argument("his")
    ap.add_argument("--json")
    ap.add_argument("--anim", help="only timelines whose name holds this")
    ap.add_argument("--only", help="only elements matching this regex (keys, attributes)")
    ap.add_argument("--all", action="store_true", help="every attribute change, not folded")
    ap.add_argument("--tol", type=float, default=1e-3)
    ap.add_argument("--work", default=os.path.join(tempfile.gettempdir(), "handdiff"))
    o = ap.parse_args()
    os.makedirs(o.work, exist_ok=True)
    pa, pb = resolve(o.ours, o.work), resolve(o.his, o.work)
    A, B = Scene(pa), Scene(pb)
    schema = Schema(o.work)
    NA, NB = Norm(schema, A), Norm(schema, B)
    only = re.compile(o.only) if o.only else None
    tol = o.tol
    L = []
    out = {"ours": pa, "his": pb, "timelines": [], "shifts": [], "tracks": [], "cursors": [], "elements": {},
           "state_machines": {}, "view_models": [], "filtered": {}}
    L.append(f"ours: {pa}\nhis:  {pb}")

    # ---- renames: an element only in one file, with the same tag, parent and attributes as one only in the other
    def parent_map(sc):
        return {c: p for p in sc.root.iter() for c in p}
    parA, parB = parent_map(A), parent_map(B)
    skipA = inside(A, ("LinearAnimation", "StateMachine"))
    skipB = inside(B, ("LinearAnimation", "StateMachine"))
    keyof_a = {id(e): k for k, e in A.el.items()}
    keyof_b = {id(e): k for k, e in B.el.items()}
    sa, sb = static_items(A, skipA), static_items(B, skipB)
    onlyA = [k for k in sa if k not in sb and keyof_a.get(id(parA.get(sa[k]))) in sb]
    onlyB = [k for k in sb if k not in sa and keyof_b.get(id(parB.get(sb[k]))) in sa]
    renamed = {}
    for kb in onlyB:
        eb = sb[kb]
        cands = [ka for ka in onlyA if sa[ka].tag == eb.tag and (sa[ka].get("name") or eb.get("name"))
                 and keyof_a.get(id(parA.get(sa[ka]))) == keyof_b.get(id(parB.get(eb)))
                 and not diff_dicts(*(lambda xa, xb: (NA.full(sa[ka], xa, xb), NB.full(eb, xb, xa)))(
                     NA.attrs(sa[ka]), NB.attrs(eb)), tol)
                 and [c.tag for c in sa[ka]] == [c.tag for c in eb]]
        if len(cands) == 1 and cands[0] not in renamed.values():
            renamed[kb] = cands[0]
    alias = {}
    for kb, ka in renamed.items():
        alias[kb] = ka
        for k in sb:
            if k.startswith(kb + "/"):
                alias[k] = ka + k[len(kb):]

    def al(k):
        return alias.get(k, k)

    # ---- timelines
    tl_all = sorted(set(A.anims) | set(B.anims))
    tls = [t for t in tl_all if not o.anim or o.anim in t]
    L.append("\n== timelines")
    shown_tl = 0
    for t in tls:
        ia, ib = A.info.get(t), B.info.get(t)
        if ia is None or ib is None:
            L.append(f"  {t}: only in {'ours' if ia else 'his'} ({(ia or ib)['duration']} f)")
            out["timelines"].append({"name": t, "only_in": "ours" if ia else "his"})
            continue
        fps = ib["fps"] or 60
        loop = (schema.props("LinearAnimation") or {}).get("loopValue")
        for i in (ia, ib):
            i["loop"] = NA.value(loop, str(i["loop"]))
        d = {k: (ia[k], ib[k]) for k in ("duration", "fps", "loop", "speed", "work") if ia[k] != ib[k]}
        out["timelines"].append({"name": t, "fps": fps, "ours": ia, "his": ib, "changed": list(d)})
        if d:
            shown_tl += 1
            parts = []
            for k, (x, y) in d.items():
                if k == "duration":
                    parts.append(f"length {x} -> {y} f ({x / (ia['fps'] or 60):.2f} -> {y / fps:.2f} s, {y - x:+d} f)")
                else:
                    parts.append(f"{k} {x} -> {y}")
            L.append(f"  {t}: " + "; ".join(parts))
    if not shown_tl:
        L.append(f"  same lengths and settings ({len(tls)} timelines)")

    # ---- tracks
    cursor_tracks = set()
    curs_by_tl = {}
    for t in tls:
        if t not in A.anims or t not in B.anims:
            continue
        ca, cb = find_cursors(A, parA, t, tol), find_cursors(B, parB, t, tol)
        if ca or cb:
            curs_by_tl[t] = (ca, cb)
            for c in list(ca.values()) + list(cb.values()):
                cursor_tracks |= {(t, al(x[0]) if x[0] else x[0], x[1]) for x in c.track_ids}

    changes = []          # (timeline, element, prop, change, ka, kb)
    for t in tls:
        if t not in A.anims or t not in B.anims:
            continue
        ta, tb = A.anims[t][1], {(al(k[0]), k[1]): v for k, v in B.anims[t][1].items()}
        for key in sorted(set(ta) | set(tb), key=lambda k: (str(k[0]), str(k[1]))):
            ka, kb = prep(ta.get(key, []), tol), prep(tb.get(key, []), tol)
            if key not in ta or key not in tb:
                ch = {"kind": "added" if key not in ta else "removed", "shift": None, "ops": [], "pairs": []}
            else:
                ch = track_change(ka, kb, tol, A.info[t]["fps"])
            if ch:
                changes.append((t, key[0], key[1], ch, ka, kb))

    # ---- shifts: frames that moved together
    L.append("\n== shifts (keys that moved together)")
    dominant, group_spans = {}, {}
    for t in tls:
        if t not in A.info or t not in B.info:
            continue
        fps = B.info[t]["fps"]
        moved = Counter()
        span = {}
        tracks_of = {}
        for (tt, el, prop, ch, ka, kb) in changes:
            if tt != t or (tt, el, prop) in cursor_tracks:
                continue
            for a, b in ch["pairs"]:
                if a and b and a.f != b.f:
                    df = b.f - a.f
                    moved[df] += 1
                    lo, hi = span.get(df, (a.f, a.f))
                    span[df] = (min(lo, a.f), max(hi, a.f))
                    tracks_of.setdefault(df, set()).add((el, prop))
        total = sum(moved.values())
        groups = [(df, n) for df, n in moved.most_common()
                  if n >= 4 and len({e for e, _ in tracks_of[df]}) >= (2 if n >= 0.08 * total else 3)]
        for df, n in groups[:6]:
            lo, hi = span[df]
            els = sorted({e for e, _ in tracks_of[df]})
            L.append(f"  {t}: {dfs(df, fps)} on {n} keys, {len(tracks_of[df])} tracks of {len(els)} elements, "
                     f"our f{lo}-f{hi}")
            out["shifts"].append({"timeline": t, "frames": df, "seconds": round(df / fps, 3), "keys": n,
                                  "tracks": len(tracks_of[df]), "from_frame": lo, "to_frame": hi, "elements": els})
        for side, word in (("removed", "removed"), ("added", "added")):
            at = {}
            for (tt, el, prop, ch, ka, kb) in changes:
                if tt != t or (tt, el, prop) in cursor_tracks:
                    continue
                for k, a, b in ch["ops"]:
                    if k == side:
                        at.setdefault((a or b).f, set()).add(el)
            for f, els in sorted(at.items()):
                if len(els) >= 3:
                    els = sorted(els, key=str)
                    L.append(f"  {t}: keys {word} at f{f} ({f / fps:.2f} s) on {len(els)} elements: "
                             + ", ".join(map(str, els[:8])) + (" ..." if len(els) > 8 else ""))
                    out["shifts"].append({"timeline": t, word: f, "elements": els})
        if groups:
            dominant[t] = (groups[0][0], span[groups[0][0]])
            group_spans[t] = [(df, span[df]) for df, _ in groups[:6]]
    if not out["shifts"]:
        L.append("  none")

    # ---- cursors
    for t, (ca, cb) in curs_by_tl.items():
        for name in sorted(set(ca) | set(cb)):
            a, b = ca.get(name), cb.get(name)
            mine = {(t, al(x[0]) if x[0] else x[0], x[1]) for c in (a, b) if c for x in c.track_ids}
            if a and b and not any((tt, el, p) in mine for (tt, el, p, *_r) in changes) and a.P == b.P and \
                    a.hin == b.hin and a.hout == b.hout:
                continue
            rep = cursor_report(f"{name}  ({t})", a, b, A.info[t]["fps"], L)
            rep["timeline"] = t
            out["cursors"].append(rep)

    # ---- the other tracks, by element
    folded, by_el = {}, {}
    for (t, el, prop, ch, ka, kb) in changes:
        fps = (B.info.get(t) or A.info[t])["fps"]
        entry = {"timeline": t, "element": el, "property": prop, "kind": ch["kind"], "shift": ch["shift"],
                 "ops": [{"op": k, "ours": a.json(fps) if a else None, "his": b.json(fps) if b else None}
                         for k, a, b in ch["ops"]],
                 "ours_keys": [k.json(fps) for k in ka], "his_keys": [k.json(fps) for k in kb]}
        out["tracks"].append(entry)
        if (t, el, prop) in cursor_tracks or (only and not only.search(str(el))):
            continue
        gs = group_spans.get(t, [])
        if ch["ops"] and all(k == "moved" and any(df == b.f - a.f and lo - 1 <= a.f <= hi + 1 for df, (lo, hi) in gs)
                             for k, a, b in ch["ops"]):
            folded.setdefault(t, set()).add(el)
            continue
        by_el.setdefault(t, {}).setdefault(el, []).append((prop, ch, ka, kb, fps))
    for t in tls:
        els = by_el.get(t, {})
        fold = sorted(folded.get(t, set()) - set(els), key=str)
        if not els and not fold:
            continue
        L.append(f"\n== keys, by element ({t})")
        if fold:
            L.append(f"  ({len(fold)} elements only follow the shifts above: " + ", ".join(map(str, fold[:12]))
                     + (" ..." if len(fold) > 12 else "") + ")")
        dom = dominant.get(t)
        for el in sorted(els, key=str):
            L.append(f"  [{el}]")
            for (prop, ch, ka, kb, fps) in els[el]:
                if ch["kind"] in ("added", "removed"):
                    ks = kb if ch["kind"] == "added" else ka
                    L.append(f"    {prop}: track only in {'his' if ch['kind'] == 'added' else 'ours'}: " + moves(ks, fps))
                    continue
                if ch["kind"] == "shift":
                    L.append(f"    {prop}: {dfs(ch['shift'], fps)}")
                    continue
                L.append(f"    {prop}:")
                ops = ch["ops"]
                for k, a, b in ops[:8]:
                    r = dom[0] if (dom and a and dom[1][0] - 2 <= a.f <= dom[1][1] + 2) else None
                    L.append(f"       {op_txt(k, a, b, fps, r)}")
                if len(ops) > 8:
                    L.append(f"       ... {len(ops) - 8} more")
                L.append(f"       ours: {moves(ka, fps)}")
                L.append(f"       his:  {moves(kb, fps)}")
    if not by_el and not folded:
        L.append("\n== keys, by element\n  none")

    # ---- elements and attributes
    L.append("\n== elements")
    cursor_paths = set()                              # the PointsPath of each cursor's path: in the cursor's section
    for sc, f in ((A, lambda k: k), (B, al)):
        ids = {fp.get("targetId") for fp in sc.root.iter("FollowPathConstraint")}
        for e in sc.root.iter():
            if e.get("id") in ids:
                cursor_paths.update(f(sc.key.get(pp.get("id"))) + "/" for pp in e.iter("PointsPath") if pp.get("id"))
    gone = [k for k in onlyA if k not in renamed.values()]
    new = [k for k in onlyB if k not in renamed]
    for k in gone:
        n = sum(1 for _ in sa[k].iter()) - 1
        L.append(f"  only in ours: {k} ({sa[k].tag}{f', +{n} inside' if n else ''})")
    for k in new:
        n = sum(1 for _ in sb[k].iter()) - 1
        L.append(f"  only in his:  {k} ({sb[k].tag}{f', +{n} inside' if n else ''})")
    for kb, ka in renamed.items():
        if not sb[kb].get("name"):                    # the editor keeps no name on some (a ClippingShape's)
            NB.filtered["names the editor drops (same element)"] += 1
            continue
        L.append(f"  renamed: {ka} -> {kb} ({sb[kb].tag})")
    out["elements"] = {"only_in_ours": gone, "only_in_his": new,
                       "renamed": [[a, b] for b, a in renamed.items() if sb[b].get("name")],
                       "changed": []}
    attr_lines, vm_lines, n_assets = [], [], 0
    sbal = {al(k): e for k, e in sb.items()}
    for k, ea in sa.items():
        eb = sbal.get(k)
        if eb is None:
            continue
        if ea.tag != eb.tag:
            attr_lines.append((k, f"type {ea.tag} -> {eb.tag}"))
            continue
        if ea.tag in ASSETS:
            n_assets += 1
            continue
        if ea.tag in SKIP_TAGS:
            continue
        xa, xb = NA.attrs(ea), NB.attrs(eb)
        xa, xb = tidy(ea.tag, NA.full(ea, xa, xb)), tidy(eb.tag, NB.full(eb, xb, xa))
        d = diff_dicts(xa, xb, tol, NA.filtered)
        if not d:
            continue
        out["elements"]["changed"].append({"element": k, "tag": ea.tag, "attrs": d})
        if any(k.startswith(p) for p in cursor_paths):
            continue                                  # in the cursor's section
        txt = "; ".join(f"{a} {fv(x)} -> {fv(y)}" for a, (x, y) in d.items())
        if only and not only.search(k):
            continue
        (vm_lines if ea.tag.startswith(VM_TAGS) else attr_lines).append((k, f"{ea.tag}: {txt}"[:400]))
    if attr_lines:
        L.append("  attributes:")
        shown = attr_lines if o.all else attr_lines[:60]
        for k, txt in shown:
            L.append(f"    {k}: {txt}")
        if len(attr_lines) > len(shown):
            L.append(f"    ... {len(attr_lines) - len(shown)} more (--all)")
    if not (gone or new or [k for k in renamed if sb[k].get("name")] or attr_lines):
        L.append("  same elements and attributes")

    # ---- state machines and view models
    L.append("\n== state machines and view models")
    sma, smb = sm_lines(A, NA), sm_lines(B, NB)

    def smdiff(p):
        (ta, xa), (tb, xb) = sma[p], smb[p]
        xa, xb = dict(xa), dict(xb)
        for k in set(xa) | set(xb):
            xa.setdefault(k, NA.default(ta, k))
            xb.setdefault(k, NB.default(tb, k))
        return diff_dicts(xa, xb, tol, NA.filtered)
    smd = {"only_in_ours": [p for p in sma if p not in smb], "only_in_his": [p for p in smb if p not in sma],
           "changed": {p: d for p in sma if p in smb for d in [smdiff(p)] if d}}
    out["state_machines"] = smd
    for p in smd["only_in_ours"][:20]:
        L.append(f"  state machine, only in ours: {p}")
    for p in smd["only_in_his"][:20]:
        L.append(f"  state machine, only in his: {p}")
    for p, d in list(smd["changed"].items())[:20]:
        L.append(f"  state machine: {p}: " + "; ".join(f"{a} {x} -> {y}" for a, (x, y) in d.items()))
    for k, txt in vm_lines:
        L.append(f"  view model: {k}: {txt}")
    out["view_models"] = [{"element": k, "change": txt} for k, txt in vm_lines]
    if not (smd["only_in_ours"] or smd["only_in_his"] or smd["changed"] or vm_lines):
        L.append("  same")

    # ---- summary
    n_tr = len([c for c in changes if (c[0], c[1], c[2]) not in cursor_tracks])
    n_fold = sum(len(v) for v in folded.values())
    filt = NA.filtered + NB.filtered
    out["filtered"] = dict(filt) | {"asset elements (files) not compared": n_assets}
    n_sm = len(smd["only_in_ours"]) + len(smd["only_in_his"]) + len(smd["changed"])
    L.append(f"\n== summary: {len(out['shifts'])} shift(s), {len(out['cursors'])} cursor(s) changed, {n_tr} other "
             f"track(s) changed ({n_fold} element(s) only follow a shift), {len(gone) + len(new)} element(s) only in "
             f"one file, {len(out['elements']['renamed'])} renamed, {len(attr_lines)} attribute change(s), "
             f"{len(vm_lines)} view model change(s), {n_sm} state machine change(s)")
    L.append("   left out as noise: " + ", ".join(f"{v} {k}" for k, v in out["filtered"].items()))
    schema.save()
    print("\n".join(L))
    if o.json:
        json.dump(out, open(o.json, "w"), indent=1, default=str)
        print(f"\nJSON: {o.json}")


if __name__ == "__main__":
    main()
