#!/usr/bin/env python3
"""
Cut highlight clips out of the finished video for use as YouTube Shorts.

Judgement and arithmetic split the same way everywhere else in this repo:
which moments are strong enough to stand alone is an editorial call, so the
agent writes it down in shorts.json. This script does the mechanical part -
find the exact timestamps, crop to vertical, blur-pad to fill the frame, burn
in the matching captions, and cut - identically every time.

shorts.json, in the project directory, is a list of:
    {"name": "01_the_setup", "first_scene": 1, "last_scene": 11}

first_scene/last_scene are scene numbers from out/scenes.json - the cut points
land on the same sentence-end boundaries the main edit already uses, so a clip
never opens or closes mid-sentence. Only include moments that would stop a
scroll on their own; a clip that only makes sense with the surrounding context
does not belong here.

Usage:
    python3 make_shorts.py <project_dir>

Reads out/scenes.json, out/captions.srt, out/final.mp4, and shorts.json.
Writes out/shorts/<name>.mp4 (vertical 9:16, captions burned in).
"""
import sys
import os
import re
import json
import subprocess

from config import (SHORTS_WIDTH, SHORTS_HEIGHT, SHORTS_FONT, SHORTS_FONT_SIZE,
                    SHORTS_BLUR_SIGMA, SHORTS_BG_DARKEN, SHORTS_MIN_SEC,
                    SHORTS_SOFT_MAX_SEC, SHORTS_HARD_MAX_SEC,
                    VIDEO_CRF, VIDEO_PRESET)

TS_RE = re.compile(r"(\d\d):(\d\d):(\d\d),(\d\d\d)")

ASS_HEADER = """[Script Info]
ScriptType: v4.00+
PlayResX: {w}
PlayResY: {h}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font},{size},&H00FFFFFF,&H000000FF,&H00000000,&H96000000,1,0,0,0,100,100,0,0,1,3.5,0,2,70,70,300,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def parse_srt_ts(ts):
    h, m, s, ms = map(int, TS_RE.match(ts).groups())
    return h * 3600 + m * 60 + s + ms / 1000.0


def fmt_ass_ts(t):
    t = max(0.0, t)
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = int(t % 60)
    cs = int(round((t - int(t)) * 100))
    if cs == 100:
        cs = 0
        s += 1
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def load_srt_cues(path):
    text = open(path, encoding="utf-8").read()
    cues = []
    for block in text.split("\n\n"):
        lines = block.strip().splitlines()
        if len(lines) < 2:
            continue
        m = re.search(r"(\d\d:\d\d:\d\d,\d\d\d)\s*-->\s*(\d\d:\d\d:\d\d,\d\d\d)", lines[1])
        if not m:
            continue
        cues.append((parse_srt_ts(m.group(1)), parse_srt_ts(m.group(2)),
                    " ".join(lines[2:])))
    return cues


def write_clip_ass(cues, clip_start, clip_end, dest):
    events = []
    for start, end, text in cues:
        if start >= clip_start - 0.08 and end <= clip_end + 0.08:
            rs, re_ = max(0.0, start - clip_start), max(0.0, end - clip_start)
            text = text.replace("{", "(").replace("}", ")")
            events.append(f"Dialogue: 0,{fmt_ass_ts(rs)},{fmt_ass_ts(re_)},"
                          f"Default,,0,0,0,,{text}")
    header = ASS_HEADER.format(w=SHORTS_WIDTH, h=SHORTS_HEIGHT,
                               font=SHORTS_FONT, size=SHORTS_FONT_SIZE)
    open(dest, "w", encoding="utf-8").write(header + "\n".join(events) + "\n")
    return len(events)


def cut_clip(source, start, dur, ass_path, dest):
    ass_escaped = ass_path.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")
    filt = (
        f"[0:v]split=2[bg0][fg0];"
        f"[bg0]scale={SHORTS_WIDTH}:{SHORTS_HEIGHT}:force_original_aspect_ratio=increase,"
        f"crop={SHORTS_WIDTH}:{SHORTS_HEIGHT},gblur=sigma={SHORTS_BLUR_SIGMA},"
        f"eq=brightness={SHORTS_BG_DARKEN}[bg];"
        f"[fg0]scale={SHORTS_WIDTH}:-2[fgv];"
        f"[bg][fgv]overlay=(W-w)/2:(H-h)/2,ass='{ass_escaped}'[vout]"
    )
    cmd = ["ffmpeg", "-y", "-v", "error", "-ss", str(start), "-i", source,
           "-t", str(dur), "-filter_complex", filt,
           "-map", "[vout]", "-map", "0:a",
           "-c:v", "libx264", "-crf", str(VIDEO_CRF), "-preset", VIDEO_PRESET,
           "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", dest]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.returncode == 0, r.stderr


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    pd = sys.argv[1]

    scenes_path = os.path.join(pd, "out", "scenes.json")
    captions_path = os.path.join(pd, "out", "captions.srt")
    video_path = os.path.join(pd, "out", "final.mp4")
    clips_path = os.path.join(pd, "shorts.json")
    out_dir = os.path.join(pd, "out", "shorts")
    subs_dir = os.path.join(out_dir, "subs")

    for label, p in [("out/scenes.json", scenes_path), ("out/captions.srt", captions_path),
                     ("out/final.mp4", video_path), ("shorts.json", clips_path)]:
        if not os.path.exists(p):
            print(f"FAIL: missing {label} at {p}")
            return 1

    scenes = {s["n"]: s for s in json.load(open(scenes_path))}
    cues = load_srt_cues(captions_path)
    clips = json.load(open(clips_path))

    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(subs_dir, exist_ok=True)

    ok_count = fail_count = 0
    seen_names = set()
    for c in clips:
        name = c["name"]
        if name in seen_names:
            print(f"FAIL: duplicate clip name {name!r}")
            fail_count += 1
            continue
        seen_names.add(name)

        first, last = c["first_scene"], c["last_scene"]
        if first not in scenes or last not in scenes:
            print(f"FAIL: {name}: scene {first} or {last} not in scenes.json")
            fail_count += 1
            continue
        if last < first:
            print(f"FAIL: {name}: last_scene {last} before first_scene {first}")
            fail_count += 1
            continue

        start, end = scenes[first]["start"], scenes[last]["end"]
        dur = end - start
        if dur > SHORTS_HARD_MAX_SEC:
            print(f"FAIL: {name}: {dur:.1f}s exceeds the {SHORTS_HARD_MAX_SEC:.0f}s "
                  f"Shorts cap - narrow the scene range")
            fail_count += 1
            continue
        if dur < SHORTS_MIN_SEC:
            print(f"WARN: {name}: {dur:.1f}s is thin for a standalone clip "
                  f"(floor {SHORTS_MIN_SEC:.0f}s)")
        if dur > SHORTS_SOFT_MAX_SEC:
            print(f"WARN: {name}: {dur:.1f}s is long for a Short "
                  f"(soft max {SHORTS_SOFT_MAX_SEC:.0f}s)")

        ass_path = os.path.join(subs_dir, f"{name}.ass")
        n_cues = write_clip_ass(cues, start, end, ass_path)
        dest = os.path.join(out_dir, f"{name}.mp4")
        ok, err = cut_clip(video_path, start, dur, ass_path, dest)
        if not ok:
            print(f"FAIL: {name}: {err[-1500:]}")
            fail_count += 1
            continue

        size = os.path.getsize(dest) / 1e6
        print(f"OK  {name}.mp4  {dur:5.1f}s  {size:5.1f} MB  {n_cues} caption cues")
        ok_count += 1

    print(f"\n{ok_count} clip(s) written to {out_dir}, {fail_count} failed")
    return 1 if fail_count else 0


if __name__ == "__main__":
    sys.exit(main())
