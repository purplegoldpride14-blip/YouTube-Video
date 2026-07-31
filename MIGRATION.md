# MIGRATION — from `Ancient-Humans` to this

Your existing repo is untouched. This is a separate tree. Nothing here writes to
`purplegoldpride14-blip/Ancient-Humans`.

## What carried over unchanged

- The two standing prompts, word for word, now in `prompts/`.
- 5 words per caption cue.
- nano-banana-2, 2K, 16:9, `autoEnhancePrompt: false`.
- −14 LUFS, true peak −1.5 dB.
- Sample-accurate offsets from decoded sample counts, never container duration.
- Balanced (not greedy) TTS split under the 10,000-character cap.
- The 5,000-character description cap and the no-hashtag rule.
- Resumable image-batch bookkeeping, and the rule that batch state never lives
  in context.

## What changed

| | Before | Now |
|---|---|---|
| Scope | one channel, one style | any niche; niche menu plus write-in plus reference images |
| Script length | 1,900–2,000 words | 1,800–1,900 words, hard band 1,750–1,950 |
| Narration safety | em and en dashes only | full linter: dashes, symbols, abbreviations, brackets, semicolons, ellipses, smart quotes auto-fixed; numerals, ALL-CAPS, currency, roman numerals, URLs flagged for rewrite |
| Volume | `loudnorm` at assembly | explicit boost step right after the voice-over arrives, two-pass linear so offsets survive; assembly verifies rather than re-normalising |
| Part order | prose instruction to eyeball chars/sec | measured automatically across every candidate ordering |
| Captions | raw ASR text, hand-corrected | transcript aligned to the script; script's words, transcript's timings; anything not in the script is dropped |
| Scene boundaries | hand-authored, 100+ cue indices | proposed automatically, reviewed as readable text, then validated |
| Pacing | flat 6.5s target | 4.5s through the first 30 seconds, 6.5s after, ±15% breathing on a three-scene cycle |
| Scene ceiling | 15s hard max | 9s soft, 12s hard, with clause-level splitting |
| Motion | still frames | still frames by default, `--motion kenburns` available |
| ffmpeg | assumed present | installed by preflight if missing |
| Repo size | 1.5 GB of committed frames | media gitignored |
| Dead weight | `setup_pipeline.py` (60 KB base64 blob), a `timestamps.py` reference to a file that does not exist | gone |

## Verified against your Ep.3 assets

Everything below was run against the real files in your repo before shipping:

- `audio_merge.py` reproduces your exact offsets: part 2 at 333.6243084s, total
  736.026s, and scores the part order at 16.30 and 15.01 chars/sec — the same
  numbers your `PROCESS_v8.md` recorded by hand.
- `srt_build.py` aligns your two Descript exports at 99.1% and 98.9% exact match,
  corrects 21 ASR words to the script's spelling, and drops 11 words the
  transcript had that the script never contained.
- `scene_plan.py` proposes 123 scenes at a 5.98s mean with a 5.02s hook, against
  your hand-built 108 scenes at a 6.82s mean.
- `assemble.py` produced a real 1920x1080 h264 render on both motion paths, with
  the timeline drift at 0.0ms.

## Using it alongside the old repo

Put this in a new folder and open that folder in Claude Code. Your old repo keeps
working exactly as it does now; nothing in this tree reads or writes it.

```bash
unzip video-pipeline.zip
cd video-pipeline/pipeline
python3 preflight.py
python3 new_project.py my-first-video --niche "History"
```

Then, in Claude Code, from the `video-pipeline` folder, type:

> /youtube-video-pipeline

Or just say what you want — "make me a new video about X" — and it loads itself.
The skill sits at `.claude/skills/youtube-video-pipeline/SKILL.md`, which is the
only place Claude Code scans. A bare `SKILL.md` at the repo root, the way your old
repo had it, is never auto-discovered; it only works if you tell Claude to read it
by name every session.

## If you later want it on GitHub as its own repo

This creates a brand new repo. It does not touch `Ancient-Humans`.

```bash
cd video-pipeline
git init
git add .
git commit -m "Generalised video pipeline: any niche, aligned captions, proposed scene plans"
gh repo create youtube-video-pipeline --private --source=. --push
```

Without the `gh` CLI, create the empty repo on github.com first, then:

```bash
git remote add origin https://github.com/<you>/youtube-video-pipeline.git
git branch -M main
git push -u origin main
```

## If you would rather bring it into the old repo on a branch

Still safe: a branch changes nothing on `main` until you merge it, and you can
delete the branch afterwards.

```bash
git clone https://github.com/purplegoldpride14-blip/Ancient-Humans.git
cd Ancient-Humans
git checkout -b pipeline-v2
cp -r /path/to/video-pipeline/* .
git add .
git commit -m "Add generalised pipeline v2"
git push -u origin pipeline-v2
```

`main` is untouched. Open a pull request when and if you want it.

One thing worth doing separately if you ever do merge: those 108 committed PNGs
are why the clone is 1.5 GB, and deleting them in a new commit does not shrink
it — the objects stay in history. Removing them for real needs
`git filter-repo`, which rewrites history, so it is a decision to make on
purpose rather than by accident.
