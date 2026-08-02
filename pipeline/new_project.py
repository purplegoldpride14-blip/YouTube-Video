#!/usr/bin/env python3
"""
Scaffold a project folder, or update an existing project's metadata.

Usage:
    python3 new_project.py <slug> [--niche "..."] [--topic "..."] [--title "..."] [--hashtags]

Creates ../projects/<slug>/ with audio/ srt/ frames/ out/ and a project.json that
carries the niche, topic, title and style decisions forward through every later
stage. Safe to re-run on an existing slug: any flag you pass overwrites that
field in project.json, everything else is left as-is (this is how the title
gets set once the topic stage settles on one, without re-scaffolding).
"""
import os
import json
import argparse
from datetime import date


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("slug")
    ap.add_argument("--niche", default=None)
    ap.add_argument("--topic", default=None)
    ap.add_argument("--title", default=None)
    ap.add_argument("--hashtags", action="store_true", default=None,
                    help="allow hashtags in the description for this project")
    ap.add_argument("--root", default=os.path.join(os.path.dirname(__file__), "..", "projects"))
    a = ap.parse_args()

    root = os.path.abspath(os.path.join(a.root, a.slug))
    for sub in ("audio", "srt", "frames", "out"):
        os.makedirs(os.path.join(root, sub), exist_ok=True)

    p = os.path.join(root, "project.json")
    if os.path.exists(p):
        meta = json.load(open(p))
    else:
        meta = {
            "slug": a.slug,
            "created": str(date.today()),
            "niche": "",
            "topic": "",
            "title": "",
            "no_hashtags": True,
            "style_locked": False,
            "notes": "",
        }
    if a.niche is not None:
        meta["niche"] = a.niche
    if a.topic is not None:
        meta["topic"] = a.topic
    if a.title is not None:
        meta["title"] = a.title
    if a.hashtags is not None:
        meta["no_hashtags"] = not a.hashtags
    meta.setdefault("title", "")
    json.dump(meta, open(p, "w"), indent=2)

    style = os.path.join(root, "style.json")
    if not os.path.exists(style):
        json.dump({"style_block": "", "characters": {}, "reference_notes": ""},
                  open(style, "w"), indent=2)

    print(f"OK  {root}")
    for f in ("project.json", "style.json", "audio/", "srt/", "frames/", "out/"):
        print(f"    {f}")
    print("\nNext: write the script, then")
    print(f"    python3 script_check.py <script.txt> {root} --fix")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
