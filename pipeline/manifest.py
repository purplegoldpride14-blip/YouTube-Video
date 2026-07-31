#!/usr/bin/env python3
"""
Resumable image-batch bookkeeping.

The agent drives OpenArt through MCP tool calls, because a shell script cannot
call MCP. What it must NOT do is hold the batch state in context. Every
submission and every download is recorded here, so a run that dies at scene 60
resumes at scene 60 instead of spending credits regenerating sixty images.

Agent loop, no approval gates between scenes:
    manifest.py init   <project_dir>
    manifest.py next   <project_dir> [count]     -> scenes still needing a submit
    manifest.py submit <project_dir> <n> <historyId>
    manifest.py record <project_dir> <n> <url>
    manifest.py fetch  <project_dir>             -> downloads everything recorded
    manifest.py verify <project_dir>             -> checks the files are real images
    manifest.py retry  <project_dir> <n> [...]   -> puts scenes back to todo
    manifest.py status <project_dir>

Reads out/scenes.json and prompts.json; writes out/manifest.json.
"""
import sys
import os
import json
import subprocess
from collections import Counter

from config import MIN_IMAGE_BYTES


def paths(project_dir):
    out = os.path.join(project_dir, "out")
    return {
        "scenes": os.path.join(out, "scenes.json"),
        "prompts": os.path.join(project_dir, "prompts.json"),
        "manifest": os.path.join(out, "manifest.json"),
        "frames": os.path.join(project_dir, "frames"),
    }


def load(p):
    return json.load(open(p))


def save(p, d):
    json.dump(d, open(p, "w"), indent=2)


def cmd_init(pd):
    P = paths(pd)
    scenes, prompts = load(P["scenes"]), load(P["prompts"])
    missing = [str(s["n"]) for s in scenes if str(s["n"]) not in prompts]
    if missing:
        print(f"FAIL: no prompt for scene(s) {', '.join(missing[:20])}")
        return 1
    m = {"scenes": {}}
    for s in scenes:
        n = str(s["n"])
        m["scenes"][n] = {"n": s["n"], "prompt": prompts[n], "state": "todo",
                          "historyId": None, "url": None, "file": None}
    save(P["manifest"], m)
    print(f"OK  initialised {len(m['scenes'])} scenes -> {P['manifest']}")
    return 0


def cmd_next(pd, count=1):
    m = load(paths(pd)["manifest"])
    todo = sorted((v for v in m["scenes"].values() if v["state"] == "todo"),
                  key=lambda v: v["n"])
    for v in todo[:int(count)]:
        print(json.dumps({"n": v["n"], "prompt": v["prompt"]}))
    return 0


def _set(pd, n, **kw):
    P = paths(pd)
    m = load(P["manifest"])
    if str(n) not in m["scenes"]:
        print(f"FAIL: no scene {n}")
        return None, None
    m["scenes"][str(n)].update(**kw)
    save(P["manifest"], m)
    return m, P


def cmd_submit(pd, n, hid):
    m, _ = _set(pd, n, state="submitted", historyId=hid)
    if m:
        print(f"OK  scene {n} submitted ({hid})")
    return 0 if m else 1


def cmd_record(pd, n, url):
    m, _ = _set(pd, n, state="ready", url=url)
    if m:
        print(f"OK  scene {n} url recorded")
    return 0 if m else 1


def cmd_retry(pd, *ns):
    for n in ns:
        _set(pd, n, state="todo", historyId=None, url=None, file=None)
    print(f"OK  reset {len(ns)} scene(s) to todo")
    return 0


def cmd_fetch(pd):
    P = paths(pd)
    m = load(P["manifest"])
    os.makedirs(P["frames"], exist_ok=True)
    got = failed = 0
    for k in sorted(m["scenes"], key=int):
        v = m["scenes"][k]
        if v["state"] != "ready" or not v["url"]:
            continue
        dest = os.path.join(P["frames"], f"scene_{v['n']:03d}.png")
        r = subprocess.run(["curl", "-s", "-L", "-o", dest, v["url"]])
        ok = (r.returncode == 0 and os.path.exists(dest)
              and os.path.getsize(dest) > MIN_IMAGE_BYTES)
        if ok:
            v.update(state="done", file=os.path.abspath(dest))
            got += 1
        else:
            failed += 1
            print(f"WARN: scene {v['n']} download failed")
    save(P["manifest"], m)
    print(f"OK  downloaded {got}, failed {failed}")
    return 0


def cmd_verify(pd):
    """Every scene must have a real file on disk. A manifest that says done and a
    frames folder that disagrees is the failure this catches."""
    P = paths(pd)
    m = load(P["manifest"])
    bad = []
    for k in sorted(m["scenes"], key=int):
        v = m["scenes"][k]
        f = v.get("file") or os.path.join(P["frames"], f"scene_{v['n']:03d}.png")
        if os.path.exists(f) and os.path.getsize(f) > MIN_IMAGE_BYTES:
            if v["state"] != "done":
                v.update(state="done", file=os.path.abspath(f))
            continue
        bad.append(v["n"])
        if v["state"] == "done":
            v.update(state="ready", file=None)
    save(P["manifest"], m)
    if bad:
        print(f"WARN: {len(bad)} frame(s) missing or truncated: {bad[:20]}")
        print("      fetch again, or retry those scenes")
        return 1
    print(f"OK  all {len(m['scenes'])} frames present and non-trivial")
    return 0


def cmd_status(pd):
    m = load(paths(pd)["manifest"])
    c = Counter(v["state"] for v in m["scenes"].values())
    total = len(m["scenes"])
    print(f"total {total} | " + " | ".join(f"{k} {v}" for k, v in sorted(c.items())))
    missing = [v["n"] for v in sorted(m["scenes"].values(), key=lambda x: x["n"])
               if v["state"] != "done"]
    if missing:
        head = ", ".join(map(str, missing[:20]))
        print(f"not done ({len(missing)}): {head}{' ...' if len(missing) > 20 else ''}")
        return 0
    print("ALL SCENES DONE - ready to assemble")
    return 0


COMMANDS = {
    "init": lambda a: cmd_init(a[0]),
    "next": lambda a: cmd_next(a[0], a[1] if len(a) > 1 else 1),
    "submit": lambda a: cmd_submit(a[0], a[1], a[2]),
    "record": lambda a: cmd_record(a[0], a[1], a[2]),
    "retry": lambda a: cmd_retry(a[0], *a[1:]),
    "fetch": lambda a: cmd_fetch(a[0]),
    "verify": lambda a: cmd_verify(a[0]),
    "status": lambda a: cmd_status(a[0]),
}

if __name__ == "__main__":
    if len(sys.argv) < 3 or sys.argv[1] not in COMMANDS:
        print(__doc__)
        sys.exit(2)
    sys.exit(COMMANDS[sys.argv[1]](sys.argv[2:]) or 0)
