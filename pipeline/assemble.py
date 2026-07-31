#!/usr/bin/env python3
"""
Assemble frames plus merged audio into the finished video.

Each scene image is held for exactly its scene duration, so the cuts land on the
caption timings by construction rather than by drift. The timeline is checked
against the audio before a single frame is encoded.

Motion:
  --motion none      still frames. Fast, and identical to the timings in scenes.json.
  --motion kenburns  a slow alternating push-in / pull-out on every scene. Static
                     AI stills for eleven minutes is the most common reason these
                     videos lose people; a small constant drift costs nothing to
                     watch and holds the eye. Each scene is rendered as its own
                     segment, so the durations stay exact.

Audio is expected to be already boosted by audio_merge.py. This verifies the
level rather than normalising a second time. Use --normalize if you merged with
--no-boost.

Usage:
    python3 assemble.py <project_dir> [--motion none|kenburns] [--normalize] [--jobs N]
"""
import sys
import os
import json
import subprocess
import tempfile
import argparse
import re
from concurrent.futures import ThreadPoolExecutor

from config import (OUT_WIDTH, OUT_HEIGHT, OUT_FPS, VIDEO_CRF, VIDEO_PRESET,
                    TARGET_LUFS, TARGET_TP, TARGET_LRA, MOTION_DEFAULT,
                    KENBURNS_ZOOM, LOUDNESS_TOLERANCE)


def run(cmd, check=True):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if check and r.returncode != 0:
        print("FAIL:", " ".join(cmd[:14]), "...")
        print(r.stderr[-3000:])
        sys.exit(1)
    return r


def frame_path(frames_dir, n):
    return os.path.abspath(os.path.join(frames_dir, f"scene_{n:03d}.png"))


def measure_lufs(path):
    r = run(["ffmpeg", "-v", "info", "-i", path, "-af",
             f"loudnorm=I={TARGET_LUFS}:TP={TARGET_TP}:LRA={TARGET_LRA}:print_format=json",
             "-f", "null", "-"], check=False)
    m = re.search(r"\{[^{}]*\"input_i\"[\s\S]*?\}", r.stderr)
    return float(json.loads(m.group(0))["input_i"]) if m else None


def build_still_list(scenes, frames_dir):
    f = tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False)
    for s in scenes:
        f.write(f"file '{frame_path(frames_dir, s['n'])}'\nduration {s['dur']:.6f}\n")
    # the final entry must be repeated for ffconcat to honour its duration
    f.write(f"file '{frame_path(frames_dir, scenes[-1]['n'])}'\n")
    f.close()
    return f.name


def render_segment(args):
    s, frames_dir, seg_dir = args
    dst = os.path.join(seg_dir, f"seg_{s['n']:04d}.mp4")
    frames = max(int(round(s["dur"] * OUT_FPS)), 1)
    step = (KENBURNS_ZOOM - 1.0) / frames
    if s["n"] % 2:
        z = f"min(zoom+{step:.6f},{KENBURNS_ZOOM})"          # push in
    else:
        z = f"if(eq(on,0),{KENBURNS_ZOOM},max(zoom-{step:.6f},1.0))"  # pull out
    vf = (f"scale={OUT_WIDTH*2}:{OUT_HEIGHT*2}:force_original_aspect_ratio=decrease,"
          f"pad={OUT_WIDTH*2}:{OUT_HEIGHT*2}:(ow-iw)/2:(oh-ih)/2:color=black,"
          f"zoompan=z='{z}':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
          f":s={OUT_WIDTH}x{OUT_HEIGHT}:fps={OUT_FPS},format=yuv420p")
    run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-i", frame_path(frames_dir, s["n"]),
         "-vf", vf, "-frames:v", str(frames), "-r", str(OUT_FPS),
         "-c:v", "libx264", "-crf", str(VIDEO_CRF), "-preset", VIDEO_PRESET, dst])
    return dst


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project_dir")
    ap.add_argument("--motion", choices=["none", "kenburns"], default=MOTION_DEFAULT)
    ap.add_argument("--normalize", action="store_true",
                    help="apply loudnorm here (only if you merged with --no-boost)")
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("-o", "--out", default=None)
    a = ap.parse_args()

    out_dir = os.path.join(a.project_dir, "out")
    frames_dir = os.path.join(a.project_dir, "frames")
    scenes = json.load(open(os.path.join(out_dir, "scenes.json")))
    meta = json.load(open(os.path.join(out_dir, "audio_meta.json")))
    out_path = a.out or os.path.join(out_dir, "final.mp4")

    wav = os.path.join(out_dir, meta["merged_wav"])
    if not os.path.exists(wav):
        print(f"FAIL: {wav} not found. Re-run audio_merge.py.")
        return 1

    missing = [s["n"] for s in scenes if not os.path.exists(frame_path(frames_dir, s["n"]))]
    if missing:
        print(f"FAIL: {len(missing)} frame(s) missing: {missing[:20]}")
        return 1

    total = sum(s["dur"] for s in scenes)
    drift = abs(total - meta["duration_sec"])
    if drift > 0.05:
        print(f"FAIL: scene durations total {total:.3f}s vs audio {meta['duration_sec']:.3f}s")
        return 1
    print(f"Frames present: {len(scenes)} | timeline drift {drift*1000:.1f}ms | motion {a.motion}")

    lufs = measure_lufs(wav)
    if lufs is not None:
        off = abs(lufs - TARGET_LUFS)
        print(f"Audio level: {lufs:.1f} LUFS (target {TARGET_LUFS})")
        if off > LOUDNESS_TOLERANCE and not a.normalize:
            print(f"WARN: {off:.1f} dB from target. Re-run audio_merge.py, "
                  f"or assemble with --normalize.")

    tmp = None
    if a.motion == "kenburns":
        seg_dir = tempfile.mkdtemp(prefix="segs_")
        print(f"Rendering {len(scenes)} motion segments with {a.jobs} workers...")
        with ThreadPoolExecutor(max_workers=a.jobs) as ex:
            segs = list(ex.map(render_segment,
                               [(s, frames_dir, seg_dir) for s in scenes]))
        tmp = tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False)
        for s in segs:
            tmp.write(f"file '{s}'\n")
        tmp.close()
        listfile, vargs = tmp.name, ["-c:v", "copy"]
    else:
        listfile = build_still_list(scenes, frames_dir)
        vargs = ["-vf", (f"scale={OUT_WIDTH}:{OUT_HEIGHT}:force_original_aspect_ratio=decrease,"
                         f"pad={OUT_WIDTH}:{OUT_HEIGHT}:(ow-iw)/2:(oh-ih)/2:color=black,"
                         f"format=yuv420p"),
                 "-r", str(OUT_FPS), "-c:v", "libx264",
                 "-crf", str(VIDEO_CRF), "-preset", VIDEO_PRESET]

    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0",
           "-i", listfile, "-i", wav] + vargs
    if a.normalize:
        cmd += ["-af", f"loudnorm=I={TARGET_LUFS}:TP={TARGET_TP}:LRA={TARGET_LRA}"]
    cmd += ["-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out_path]

    print("Encoding...")
    run(cmd)
    os.unlink(listfile)

    dur = float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                     "-of", "csv=p=0", out_path]).stdout.strip())
    size = os.path.getsize(out_path) / 1e6
    print(f"\nOK  {out_path}")
    print(f"    {dur:.2f}s ({dur/60:.1f} min) | {size:.1f} MB | "
          f"{OUT_WIDTH}x{OUT_HEIGHT} @ {OUT_FPS}fps")
    if abs(dur - meta["duration_sec"]) > 0.5:
        print(f"WARN: output {dur:.2f}s vs audio {meta['duration_sec']:.2f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
