# PROCESS — narrated YouTube video pipeline

The work splits in two, and the split is the whole design:

- **Judgement** — niche, topic, script, scene boundaries, visual style, thumbnail.
  Stays with the agent, because these are genuinely editorial.
- **Arithmetic** — offsets, alignment, merges, splits, durations, loudness,
  encoding, validation. Lives in `pipeline/`, runs identically every time, and
  fails loudly.

> Every number in this document describes `pipeline/config.py`. If they ever
> disagree, config.py wins. A previous version of this spec stated the script
> length in two places, they contradicted each other, and it cost a full
> regeneration.

---

## Run order

```bash
cd pipeline
python3 preflight.py                                    # FIRST. Always.
python3 new_project.py <slug> --niche "History"

# after writing script.txt
python3 script_check.py <script.txt> ../projects/<slug> --fix

# after the user drops the voice-over files into projects/<slug>/audio/
python3 audio_merge.py ../projects/<slug>/audio ../projects/<slug>

# after exporting one raw SRT per part from Descript into projects/<slug>/srt/
python3 srt_build.py ../projects/<slug>/srt ../projects/<slug>

# scene plan: propose, read the draft, adjust, build
python3 scene_plan.py propose ../projects/<slug>
python3 scene_plan.py build   ../projects/<slug>

# image batch (agent-driven, resumable, no approval gates between scenes)
python3 manifest.py init   ../projects/<slug>
python3 manifest.py next   ../projects/<slug> 4
python3 manifest.py submit ../projects/<slug> <n> <historyId>
python3 manifest.py record ../projects/<slug> <n> <url>
python3 manifest.py fetch  ../projects/<slug>
python3 manifest.py status ../projects/<slug>

python3 assemble.py ../projects/<slug> [--motion kenburns]
python3 description_check.py ../projects/<slug>/description.md ../projects/<slug>/project.json

# after picking highlight moments into shorts.json
python3 make_shorts.py ../projects/<slug>

# after the thumbnail is approved and saved to out/thumbnail.png
python3 deliver.py ../projects/<slug>
```

---

## Approval gates

1. **Topic.** Ten researched ideas, or the user's own. Human picks.
2. **Style.** Scene 1 generated alone at locked settings. Human approves.
3. *(soft)* **Thumbnail.** Shown before finalising, regenerated until approved.

Everything else runs without check-ins. Stop mid-run only for a blocking failure:
a domain not allowlisted, a hard cap exceeded, a validator failing. Flag those
immediately rather than working around them silently.

---

## The numbers, and why

**Script: 1,800-1,900 words, hard band 1,750-1,950.** About eleven to twelve
minutes narrated. Warn on small drift, fail on real drift.

**TTS split: under 10,000 characters per part, balanced.** 10,000 is the engine's
hard limit, not a style choice. Balanced rather than greedy: a greedy split leaves
a stub final part, the halves pick up different room tone, and the join is
audible.

**Volume: -14 LUFS, true peak -1.5 dB, applied once to the merged track.**
Two-pass linear loudnorm, so the gain is constant across the whole video and the
sample count survives. Per-part normalisation would give each part its own gain
and a level step at the seam.

**Offsets: decoded sample counts, never nominal mp3 duration.** A container that
reports 333.662s can decode to 333.624s — a 38ms difference from encoder delay and
padding, which drifts every caption in every later part. `audio_merge.py` asserts
that the merged sample count equals the sum of the parts.

**Part order: measured, never trusted from the filename.** Each candidate ordering
is scored by how consistent its characters-per-second is. One real case landed at
16.3 and 15.0 under the correct assignment versus 18.1 and 13.5 swapped. The
filename is not evidence.

**Captions: the script's words, the transcript's timings.** The raw SRT is a
transcript of the audio, so it carries ASR errors, filler, and anything Descript
picked up that was never written. `srt_build.py` aligns the two word streams and
keeps the script's spelling with the transcript's timing. Anything the transcript
has that the script does not is dropped. Five words per cue, split at sentence
ends and balanced so no cue is orphaned.

**Scenes: 6.5s target, 2.5s floor, 9s soft max, 12s hard max.** Plus two things
the earlier version did not do:

- *The opening cuts faster.* The first 30 seconds targets 4.5s per visual. The
  hook earns the click; the body settles into a rhythm.
- *The target breathes ±15% on a three-scene cycle.* Cutting on an exact
  metronome is what makes these videos feel machine-made, and it is visible even
  when nothing else is.

Boundaries are proposed automatically by `scene_plan.py propose` from four
rules in priority order — cut only at a sentence end; cut when a new person,
place or thing appears; cut anyway past the target; then merge anything under the
floor and split anything over the hard max. The agent reads `scenes_draft.txt` and
adjusts. Proposing a draft and editing it is far more reliable than authoring a
hundred cue indices by hand, which is what the earlier version asked for.

**Images: nano-banana-2-lite, text2image, 16:9, count 1.** Fast and, as of this
writing, unlimited-use on OpenArt. Its params are prompt, imageCount, and
aspectRatio only - no resolution (fixed at 1K internally) and no
autoEnhancePrompt, so there is nothing that can silently rewrite the locked
style block the way `autoEnhancePrompt` could on nano-banana-2. Character
descriptor phrases are still reused verbatim in every prompt that features
them; paraphrasing them is how faces drift over a hundred images regardless of
model.

**Description: 5,000 character hard cap.** YouTube's actual platform limit
(support.google.com/youtube/answer/12948449). Independent of, and stricter than,
the ~500 word floor. Always run `description_check.py`.

**Shorts: 15s soft floor, 90s soft max, 180s hard max.** The hard max is
YouTube's own technical cap on a Short; the soft bounds are retention, not a
platform rule, so they warn rather than fail. Which moments qualify is
judgement (`shorts.json`), not something `make_shorts.py` decides - it only
turns a chosen scene range into a vertical, captioned clip. A clip that only
makes sense with earlier context does not belong in `shorts.json` at all.

---

## Hard-won details

**The image batch does not belong in a chat interface.** Chat returns one tool
result per exchange, so each scene costs two round trips. A 110-scene video is
220+ exchanges. That is the reason this repo exists.

**Never hold batch state in context.** `manifest.py status` is the only source of
truth about what has been generated. A run that dies at scene 60 resumes at 60.

**The description comes from the narration, not the research notes.** This has
gone wrong once already: the research file had five more researcher names in it
than the video ever spoke, and all five ended up in the description. Grep the
narration before naming anyone.

**No dashes, and no anything else the narrator trips on.** `narration_lint.py`
auto-fixes the deterministic cases and flags the ones that need a rewrite
(numerals, ALL-CAPS, currency, roman numerals, URLs). A substitution is not a fix
for those; the sentence is.

---

## Repo layout

```
.claude/skills/youtube-video-pipeline/SKILL.md   the agent's entry point
pipeline/              deterministic stages, all resumable, stdlib only
  config.py              every constant, single source of truth
  preflight.py           tools + ffmpeg install + domain allowlist
  new_project.py         scaffold projects/<slug>/
  narration_lint.py      everything a voice-over stumbles on
  script_check.py        word band, lint, balanced TTS-safe split
  audio_merge.py         part order, lossless merge, exact offsets, volume boost
  srt_build.py           transcript aligned to script -> captions.srt + words.json
  scene_plan.py          propose boundaries, then validate -> scenes.json
  manifest.py            resumable image batch bookkeeping
  assemble.py            frames + audio -> mp4, optional ken burns
  description_check.py   character cap and hashtag policy
  make_shorts.py         shorts.json scene ranges -> vertical captioned clips
  deliver.py              mirror deliverables into out/, split anything over the git push limit
playbooks/             the editorial half, one file per decision
prompts/               the two standing prompts, used verbatim
projects/<slug>/
  project.json  style.json  script.txt  narration_partN.txt
  boundaries.json  prompts.json  description.md  shorts.json
  audio/  srt/  frames/
  out/                  the single handoff folder - everything the user takes
                        elsewhere ends up here, mirrored by deliver.py
    final.mp4  thumbnail.png  captions.srt  words.json  description.md
    narration_partN.txt  shorts/<name>.mp4  chunks/  shorts/chunks/
```
