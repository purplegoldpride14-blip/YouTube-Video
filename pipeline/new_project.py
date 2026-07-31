#!/usr/bin/env python3
"""
Scaffold a project folder.

Usage:
    python3 new_project.py <slug> [--niche "..."] [--topic "..."] [--hashtags]

Creates ../projects/<slug>/ with audio/ srt/ frames/ out/ and a project.json that
carries the niche, topic and style decisions forward through every later stage.
"""
import os
import json
import argparse
from datetime import date


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("slug")
    ap.add_argument("--niche", default="")
    ap.add_argument("--topic", default="")
    ap.add_argument("--hashtags", action="store_true",
                    help="allow hashtags in the description for this project")
    ap.add_argument("--root", default=os.path.join(os.path.dirname(__file__), "..", "projects"))
    a = ap.parse_args()

    root = os.path.abspath(os.path.join(a.root, a.slug))
    for sub in ("audio", "srt", "frames", "out"):
        os.makedirs(os.path.join(root, sub), exist_ok=True)

    meta = {
        "slug": a.slug,
        "created": str(date.today()),
        "niche": a.niche,
        "topic": a.topic,
        "no_hashtags": not a.hashtags,
        "style_locked": False,
        "notes": "",
    }
    p = os.path.join(root, "project.json")
    if not os.path.exists(p):
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
