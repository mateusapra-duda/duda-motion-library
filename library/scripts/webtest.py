"""Play a piece's .riv as the site will: headless Chromium with the site's runtime (@rive-app/webgl2 2.45.0, autoBind)
and captures at given times. Works in any folder: it needs the piece (build.py run once), this bundle, Node and
Playwright (from the npx cache: `npx playwright install chromium-headless-shell` once; PLAYWRIGHT=<path to
node_modules/playwright> to use another).

usage: python lib/biblioteca-<v>/scripts/webtest.py <piece_dir> [seconds ...]        (default: 0.5 1 2 3)
       python lib/biblioteca-<v>/scripts/webtest.py <piece_dir> --plan PLAN.json     (clicks, typing, view model
                                                                                      values: see webtest/run.cjs)
  Builds build/<name>.riv (rive . --once), serves the piece on a local port, runs webtest/run.cjs and writes
  build/webtest/MAIN_<t>s.png plus the page's log (the view model, errors). Times are real time from the moment the
  file is ready, so they are approximate: for exact frames use the CLI (rive . --screenshot --advance=N+1).
"""
import json
import os
import shutil
import socket
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # python -I leaves the script's folder out
import scene  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
WEB = os.path.join(HERE, "..", "webtest")


def main():
    args = sys.argv[1:]
    if not args:
        sys.exit(__doc__)
    proj = os.path.abspath(args[0])
    name, main_ab, w, h, _, _ = scene.info(proj)
    r = subprocess.run([scene.rive(), ".", "--once"], cwd=proj, capture_output=True, text=True, timeout=300)
    riv = os.path.join(proj, "build", f"{name}.riv")
    if r.returncode or not os.path.exists(riv):
        sys.exit("the .riv did not build:\n" + (r.stdout + r.stderr)[-1500:])
    page_dir = os.path.join(proj, "build", "webtest")
    os.makedirs(page_dir, exist_ok=True)
    shutil.copy2(os.path.join(WEB, "index.html"), os.path.join(page_dir, "index.html"))
    if "--plan" in args:
        plan = json.load(open(args[args.index("--plan") + 1]))
    else:
        times = [float(t) for t in args[1:]] or [0.5, 1, 2, 3]
        plan = [{"name": main_ab, "ab": main_ab, "w": w, "h": h, "steps": [{"at": t, "shot": f"{t:g}s"} for t in times]}]
    for t in plan:
        t.setdefault("src", f"../{name}.riv")
    plan_path = os.path.join(page_dir, "plan.json")
    json.dump(plan, open(plan_path, "w"), indent=1)
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    server = subprocess.Popen([sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1"], cwd=proj,
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        env = dict(os.environ, WEBTEST_URL=f"http://127.0.0.1:{port}/build/webtest/index.html")
        r = subprocess.run(["node", os.path.join(WEB, "run.cjs"), plan_path, page_dir], env=env, capture_output=True,
                           text=True, timeout=300)
        print((r.stdout + r.stderr).strip())
        if r.returncode:
            sys.exit(1)
    finally:
        server.terminate()


if __name__ == "__main__":
    main()
