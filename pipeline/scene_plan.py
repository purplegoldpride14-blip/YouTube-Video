#!/usr/bin/env python3
"""
Plan the visual cuts.

Two commands:

  propose   Reads words.json and writes a first-draft boundaries.json plus a
            readable scenes_draft.txt. The draft is built from four rules, in
            priority order:

              1. Cut only at a sentence end. A visual that changes mid-sentence
                 reads as a mistake.
              2. Cut when the script introduces a new person, place or thing.
                 Novelty is measured lexically: content words this script has
                 not used before.
              3. Cut anyway once the scene passes its target length. The target
                 is HOOK_TARGET_SEC for the first HOOK_SEC of the video and
                 SCENE_TARGET_SEC after that - the opening earns the click, so
                 it cuts faster, then the body settles into a rhythm.
              4. Merge anything under SCENE_MIN_SEC into its shorter neighbour,
                 and split anything over SCENE_HARD_MAX_SEC at its best interior
                 sentence end.

            The target also breathes by +/-15% on a three-scene cycle. Cutting
            on an exact metronome is the thing that makes these videos feel
            machine-made.

  build     Reads boundaries.json (yours or the draft, edited), validates the
            arithmetic, and writes scenes.json.

Usage:
    python3 scene_plan.py propose <project_dir>
    python3 scene_plan.py build   <project_dir>
"""
import sys
import os
import re
import json
import argparse

from config import (SCENE_TARGET_SEC, SCENE_MIN_SEC, SCENE_SOFT_MAX_SEC,
                    SCENE_HARD_MAX_SEC, SCENE_CAP, HOOK_SEC, HOOK_TARGET_SEC)

SENT_END = re.compile(r"[.!?]$")
BREATHE = [0.85, 1.0, 1.15]

STOP = set("""
a about above after again against all am an and any are as at be because been before being below
between both but by can cannot could did do does doing down during each few for from further had
has have having he her here hers him his how i if in into is it its itself just me more most my no
nor not now of off on once only or other our out over own same she should so some such than that
the their them then there these they this those through to too under until up very was we were what
when where which while who whom why will with you your yours than been about like get got one two
three four five six seven eight nine ten first second next last thing things really actually just
even still also because something someone anything nothing every never always
""".split())


def load_words(project_dir):
    p = os.path.join(project_dir, "out", "words.json")
    return json.load(open(p))


def sentences(words):
    """Group the word stream into sentences, 0-based word index ranges."""
    out, start = [], 0
    for i, w in enumerate(words):
        if SENT_END.search(w["w"]):
            out.append({"i0": start, "i1": i, "start": words[start]["start"],
                        "end": words[i]["end"],
                        "text": " ".join(x["w"] for x in words[start:i + 1])})
            start = i + 1
    if start < len(words):
        out.append({"i0": start, "i1": len(words) - 1, "start": words[start]["start"],
                    "end": words[-1]["end"],
                    "text": " ".join(x["w"] for x in words[start:])})
    return out


def novelty(sent, seen):
    """Content words this script has not used before. Proper nouns count double,
    because a new named person or place is the strongest reason to cut."""
    score, new = 0, []
    toks = sent["text"].split()
    for k, raw in enumerate(toks):
        t = re.sub(r"[^A-Za-z0-9']", "", raw)
        if len(t) < 4:
            continue
        low = t.lower()
        if low in STOP or low in seen:
            continue
        new.append(low)
        score += 2 if (t[0].isupper() and k > 0) else 1
    return score, new


def target_for(t, k):
    base = HOOK_TARGET_SEC if t < HOOK_SEC else SCENE_TARGET_SEC
    return base * BREATHE[k % len(BREATHE)]


def _durs(starts, words, audio_dur):
    """Contiguous durations: every scene runs until the next one begins, which is
    how build() lays them out and therefore the only measurement worth making."""
    out = []
    for i, s in enumerate(starts):
        t0 = words[s]["start"]
        t1 = words[starts[i + 1]]["start"] if i + 1 < len(starts) else audio_dur
        out.append(t1 - t0)
    return out


def _cut_candidates(words, w0, w1, sent_starts):
    """Where a long scene may be cut, best first: sentence starts, then clause
    starts, then any word."""
    interior = range(w0 + 1, w1 + 1)
    sents = [i for i in interior if i in sent_starts]
    if sents:
        return sents
    clause = [i for i in interior if re.search(r"[,;:]$", words[i - 1]["w"])]
    return clause or list(interior)


def propose(project_dir):
    words = load_words(project_dir)
    meta = json.load(open(os.path.join(project_dir, "out", "audio_meta.json")))
    audio_dur = meta["duration_sec"]
    sents = sentences(words)
    sent_starts = {s["i0"] for s in sents}
    seen = set()

    # pass 1: group sentences, cutting on subject change or on the running target
    starts = [0]
    k = 0
    for si, s in enumerate(sents):
        score, new = novelty(s, seen)
        seen.update(new)
        if si == 0:
            continue
        t0 = words[starts[-1]]["start"]
        dur = s["start"] - t0          # length if this scene ends here
        with_this = s["end"] - t0      # length if this sentence joins it
        tgt = target_for(t0, k)
        # cut before a long sentence rather than after it - overshooting by a
        # whole sentence is what pushes scenes past the soft max
        overshoot = with_this > SCENE_SOFT_MAX_SEC and dur >= SCENE_MIN_SEC
        # a subject change only earns a cut once the scene has had time to read
        subject = score >= 2 and dur >= max(SCENE_MIN_SEC, 0.65 * tgt)
        if subject or dur >= tgt or overshoot:
            starts.append(s["i0"])
            k += 1

    # pass 2: split anything over the hard max, sentence ends first, then clauses
    changed = True
    while changed:
        changed = False
        durs = _durs(starts, words, audio_dur)
        for i, d in enumerate(durs):
            if d <= SCENE_HARD_MAX_SEC:
                continue
            w0 = starts[i]
            w1 = (starts[i + 1] - 1) if i + 1 < len(starts) else len(words) - 1
            cands = _cut_candidates(words, w0, w1, sent_starts)
            if not cands:
                continue
            t0 = words[w0]["start"]
            best = min(cands, key=lambda c: abs((words[c]["start"] - t0) - SCENE_TARGET_SEC))
            starts.insert(i + 1, best)
            changed = True
            break

    # pass 2b: a scene over the soft max gets split at a clause boundary if both
    # halves still clear the floor. A ten-second hold on one still is the single
    # most visible way these videos stall.
    stuck = set()
    changed = True
    while changed:
        changed = False
        durs = _durs(starts, words, audio_dur)
        for i, d in enumerate(durs):
            if d <= SCENE_SOFT_MAX_SEC or starts[i] in stuck:
                continue
            w0 = starts[i]
            w1 = (starts[i + 1] - 1) if i + 1 < len(starts) else len(words) - 1
            end_t = words[w0]["start"] + d
            cands = [c for c in range(w0 + 1, w1 + 1)
                     if c in sent_starts or re.search(r"[,;:]$", words[c - 1]["w"])]
            ok = [c for c in cands
                  if words[c]["start"] - words[w0]["start"] >= SCENE_MIN_SEC
                  and end_t - words[c]["start"] >= SCENE_MIN_SEC]
            if not ok:
                stuck.add(w0)
                continue
            mid = words[w0]["start"] + d / 2
            starts.insert(i + 1, min(ok, key=lambda c: abs(words[c]["start"] - mid)))
            changed = True
            break

    # pass 3: merge anything under the floor into its shorter neighbour
    changed = True
    while changed and len(starts) > 1:
        changed = False
        durs = _durs(starts, words, audio_dur)
        for i, d in enumerate(durs):
            if d >= SCENE_MIN_SEC:
                continue
            prev_d = durs[i - 1] if i > 0 else 1e9
            next_d = durs[i + 1] if i + 1 < len(durs) else 1e9
            starts.pop(i if prev_d <= next_d else i + 1)
            changed = True
            break

    bounds = [s + 1 for s in starts]  # 1-based word indices
    bp = os.path.join(project_dir, "boundaries.json")
    json.dump({"boundaries": bounds}, open(bp, "w"), indent=1)

    durs = _durs(starts, words, audio_dur)
    draft = os.path.join(project_dir, "scenes_draft.txt")
    with open(draft, "w", encoding="utf-8") as f:
        for n, s in enumerate(starts, 1):
            end = (starts[n] - 1) if n < len(starts) else len(words) - 1
            txt = " ".join(w["w"] for w in words[s:end + 1])
            f.write(f"[{n:03d}] {words[s]['start']:7.2f}s  {durs[n-1]:5.2f}s  word {s+1}\n")
            f.write(f"      {txt}\n\n")

    scenes = starts
    print(f"OK  proposed {len(scenes)} scenes from {len(sents)} sentences")
    print(f"    dur min {min(durs):.2f}s | mean {sum(durs)/len(durs):.2f}s | max {max(durs):.2f}s")
    print(f"    wrote {bp}")
    print(f"    wrote {draft}   <- read this, adjust boundaries.json, then run build")
    return 0


def build(project_dir):
    words = load_words(project_dir)
    meta = json.load(open(os.path.join(project_dir, "out", "audio_meta.json")))
    B = json.load(open(os.path.join(project_dir, "boundaries.json")))["boundaries"]

    if B != sorted(B) or len(set(B)) != len(B):
        print("FAIL: boundaries must be sorted and unique")
        return 1
    if B[0] != 1:
        print("FAIL: the first boundary must be word 1")
        return 1
    if B[-1] > len(words):
        print(f"FAIL: boundary {B[-1]} exceeds the word count {len(words)}")
        return 1

    scenes = []
    for i, b in enumerate(B):
        end_w = (B[i + 1] - 2) if i + 1 < len(B) else len(words) - 1
        scenes.append({
            "n": i + 1,
            "start": words[b - 1]["start"],
            "end": words[end_w]["end"],
            "word_from": b,
            "word_to": end_w + 1,
            "text": " ".join(w["w"] for w in words[b - 1:end_w + 1]),
        })

    for i in range(len(scenes) - 1):
        scenes[i]["end"] = scenes[i + 1]["start"]
    scenes[0]["start"] = 0.0
    scenes[-1]["end"] = meta["duration_sec"]
    for s in scenes:
        s["dur"] = round(s["end"] - s["start"], 4)

    errs, warns = [], []
    if len(scenes) > SCENE_CAP:
        errs.append(f"{len(scenes)} scenes exceeds the cap of {SCENE_CAP}")
    for s in scenes:
        if s["dur"] < SCENE_MIN_SEC:
            errs.append(f"scene {s['n']} is {s['dur']:.2f}s, under the {SCENE_MIN_SEC}s floor")
        elif s["dur"] > SCENE_HARD_MAX_SEC:
            errs.append(f"scene {s['n']} is {s['dur']:.2f}s, over the {SCENE_HARD_MAX_SEC}s hard max")
        elif s["dur"] > SCENE_SOFT_MAX_SEC:
            warns.append(f"scene {s['n']} is {s['dur']:.2f}s, over the {SCENE_SOFT_MAX_SEC}s soft max")

    hook = [s for s in scenes if s["start"] < HOOK_SEC]
    if hook:
        hm = sum(s["dur"] for s in hook) / len(hook)
        if hm > HOOK_TARGET_SEC * 1.4:
            warns.append(f"the first {HOOK_SEC:.0f}s averages {hm:.2f}s per visual, "
                         f"slower than the {HOOK_TARGET_SEC}s hook target")

    for w in warns:
        print(f"WARN: {w}")
    if errs:
        for e in errs:
            print(f"FAIL: {e}")
        return 1

    out_dir = os.path.join(project_dir, "out")
    os.makedirs(out_dir, exist_ok=True)
    json.dump(scenes, open(os.path.join(out_dir, "scenes.json"), "w"), indent=2)

    durs = [s["dur"] for s in scenes]
    print(f"OK  {len(scenes)} scenes (cap {SCENE_CAP}, "
          f"ideal {round(meta['duration_sec']/SCENE_TARGET_SEC)})")
    print(f"    dur min {min(durs):.2f}s | mean {sum(durs)/len(durs):.2f}s | max {max(durs):.2f}s")
    if hook:
        print(f"    hook  first {HOOK_SEC:.0f}s: {len(hook)} visuals, "
              f"{sum(s['dur'] for s in hook)/len(hook):.2f}s each")
    print(f"    coverage {scenes[0]['start']:.3f} -> {scenes[-1]['end']:.3f} "
          f"(audio {meta['duration_sec']:.3f})")
    print(f"    wrote {out_dir}/scenes.json")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["propose", "build"])
    ap.add_argument("project_dir")
    a = ap.parse_args()
    sys.exit(propose(a.project_dir) if a.command == "propose" else build(a.project_dir))
