#!/usr/bin/env python3
"""
Prepare the finished project for handoff.

Does three things, in order:
1. Verifies the deliverables exist: description.md, out/captions.srt,
   out/thumbnail.png, out/final.mp4.
2. Checks out/final.mp4 against GIT_PUSH_MAX_BYTES. Under the limit, it is
   left alone - the agent git-adds it (with -f, since out/ is gitignored)
   alongside the other three and pushes.
3. Over the limit, splits it into CHAT_CHUNK_BYTES pieces under
   out/chunks/, plus a sha256 of the original so the recipient can verify a
   reassembly. This script never touches git and never sends anything to
   chat - both are agent actions, not scripted ones.

Usage:
    python3 deliver.py <project_dir>
"""
import sys
import os
import hashlib

from config import GIT_PUSH_MAX_BYTES, CHAT_CHUNK_BYTES


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def split_file(src, dest_dir, chunk_bytes):
    os.makedirs(dest_dir, exist_ok=True)
    base = os.path.basename(src)
    for old in os.listdir(dest_dir):
        if old.startswith(base + ".part_"):
            os.remove(os.path.join(dest_dir, old))
    parts = []
    with open(src, "rb") as f:
        n = 0
        while True:
            data = f.read(chunk_bytes)
            if not data:
                break
            part_path = os.path.join(dest_dir, f"{base}.part_{n:03d}")
            with open(part_path, "wb") as out:
                out.write(data)
            parts.append(part_path)
            n += 1
    return parts


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    pd = sys.argv[1]

    required = {
        "description": os.path.join(pd, "description.md"),
        "captions": os.path.join(pd, "out", "captions.srt"),
        "thumbnail": os.path.join(pd, "out", "thumbnail.png"),
        "video": os.path.join(pd, "out", "final.mp4"),
    }
    missing = [name for name, p in required.items() if not os.path.exists(p)]
    if missing:
        print(f"FAIL: missing deliverable(s) before running deliver.py: {', '.join(missing)}")
        for name in missing:
            print(f"      expected {required[name]}")
        return 1

    video_path = required["video"]
    video_bytes = os.path.getsize(video_path)

    print(f"OK  description.md, out/captions.srt, out/thumbnail.png all present")
    print(f"    out/final.mp4: {video_bytes:,} bytes")

    if video_bytes <= GIT_PUSH_MAX_BYTES:
        print(f"OK  under the {GIT_PUSH_MAX_BYTES:,}-byte git push limit")
        print("NEXT: git add -f description.md out/captions.srt out/thumbnail.png out/final.mp4, commit, push")
        return 0

    print(f"OK  over the {GIT_PUSH_MAX_BYTES:,}-byte git push limit - splitting for chat delivery instead")
    checksum = sha256_of(video_path)
    chunks_dir = os.path.join(pd, "out", "chunks")
    parts = split_file(video_path, chunks_dir, CHAT_CHUNK_BYTES)
    sha_path = os.path.join(chunks_dir, os.path.basename(video_path) + ".sha256")
    with open(sha_path, "w") as f:
        f.write(f"{checksum}  {os.path.basename(video_path)}\n")

    print(f"OK  split into {len(parts)} part(s) in {chunks_dir}")
    print(f"    sha256 {checksum}")
    print("NEXT: git add -f description.md out/captions.srt out/thumbnail.png (NOT out/final.mp4), commit, push")
    print(f"      then send the {len(parts)} chunk file(s) to the user via chat, and give them the sha256")
    print("      above plus the reassembly command (cat final.mp4.part_* > final.mp4, or Windows copy /b)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
