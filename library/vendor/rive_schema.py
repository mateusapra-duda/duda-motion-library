"""Property-key map for Rive core types, built once from `rive schema --json` and cached."""
import json
import os
import subprocess

import bins

CACHE = os.path.join(os.path.dirname(__file__), "schema_cache.json")


def _rive(*args):
    out = subprocess.run([bins.rive(), "schema", *args], capture_output=True, text=True).stdout
    # the CLI may print an update notice before the JSON
    start = min(i for i in (out.find("["), out.find("{")) if i >= 0)
    return json.loads(out[start:])


def load():
    if os.path.exists(CACHE):
        with open(CACHE) as f:
            return json.load(f)
    types = _rive("--list", "--json")
    names = [t if isinstance(t, str) else t.get("type") or t.get("name") for t in types]
    keys, typedefs = {}, {}
    for name in names:
        try:
            d = _rive("--json", "--all", name)
        except Exception:
            continue
        typedefs[name] = {p["name"]: p["key"] for p in d.get("properties", [])}
        for p in d.get("properties", []):
            keys[str(p["key"])] = {"name": p["name"], "owner": p["owner"], "type": p["type"]}
    data = {"keys": keys, "types": typedefs}
    with open(CACHE, "w") as f:
        json.dump(data, f)
    return data


if __name__ == "__main__":
    d = load()
    print(len(d["keys"]), "property keys,", len(d["types"]), "types")
