---
name: youtube-video-pipeline
description: >
  Produce a full narrated YouTube video end to end for any niche - niche and
  topic selection, research, script, narration audio, aligned SRT, scene plan,
  visual style, image batch, assembly, description and thumbnail. Use when the
  user wants to make a new video, resume an interrupted one, or run any single
  stage (script check, audio merge, SRT build, scene plan, image batch,
  assembly, description, thumbnail). Trigger on "new video", "make a video",
  "resume <slug>", or a request to write a script, build an SRT, plan scenes or
  assemble a video for a channel.
---

# YouTube video pipeline

Every path below is relative to the repository root, not to this file.

Read `PROCESS.md` before starting. Every number lives in `pipeline/config.py`;
the docs describe it and never override it.

## Always run first

```bash
cd pipeline && python3 preflight.py
```

It installs ffmpeg if it is missing and checks the domain allowlist. If a domain
is blocked, STOP and tell the user. The allowlist is fixed at session start and
cannot be changed mid-run; discovering it at scene 40 wastes the whole batch.

## Two approval gates, and one thumbnail check

**Gate 1 — topic.** Ask for the niche, research what is over-performing in it,
propose exactly ten ideas, wait for the pick.

**Gate 2 — style.** Offer visual styles that are working in this niche, write the
style block, generate scene 1 only at locked settings, show it, wait for approval.

**Thumbnail check.** Show the thumbnail before finalising. Regenerate until approved.

Between and after these, run without check-ins. In particular, once scene 1 is
approved, generate all remaining scenes automatically with no continuation prompts.

## Stage sequence

1. **Niche.** `playbooks/01_niche_and_topic.md`. Menu plus a write-in option;
   accept reference images or links.
2. **Topic and title.** Research the niche for what is currently
   over-performing, propose ten ideas, wait. Then research the chosen topic
   properly, with sources. Once the topic is settled (picked from the ten or
   written in), immediately propose three to five title options built from
   that research and ask the user to pick one or write their own. Save it to
   `project.json` under `title` via `new_project.py ... --title "..."` before
   moving on to the script. Do not defer this to the description/thumbnail
   stage - the title is chosen here, not guessed at the end.
3. **Script.** `playbooks/02_script.md`. 1,800-1,900 words. Then:
   `python3 script_check.py <script.txt> ../projects/<slug> --fix`
4. **Narration.** The user generates the audio with OpenArt's own
   "Create Voice Over" feature (ElevenLabs voices, in the OpenArt app - this is
   not reachable through the OpenArt MCP tools available here, only
   `openart_generate_image`/`openart_generate_video` are), same voice settings
   for every part, and drops the files in `projects/<slug>/audio/`. Then:
   `python3 audio_merge.py ../projects/<slug>/audio ../projects/<slug>`
   This verifies part order by measured speech rate, merges losslessly, and
   raises the volume to -14 LUFS.
5. **SRT.** Import each part to Descript as its own composition via the Descript
   MCP, export one SRT per composition into `projects/<slug>/srt/` as
   `part1_raw.srt`..`partN_raw.srt`. Then:
   `python3 srt_build.py ../projects/<slug>/srt ../projects/<slug>`
   This aligns the transcript to the script, keeps the script's words with the
   transcript's timings, and drops anything the transcript has that the script
   does not. Five words per cue.
6. **Scene plan.** `python3 scene_plan.py propose ../projects/<slug>`, read
   `scenes_draft.txt`, adjust `boundaries.json` where the proposal missed a
   subject change, then `python3 scene_plan.py build ../projects/<slug>`.
   Fix any FAIL by moving boundaries, never by editing config.
7. **Style.** `playbooks/03_visual_style.md`. Offer options, accept a write-in or
   reference images, write `style.json`.
8. **Scene 1.** Generate it alone at locked settings. Approve. Lock.
9. **Batch.** Write `prompts.json` mapping scene number to prompt, reusing
   character descriptors verbatim and appending the style block to every one.
   Then `manifest.py init / next / submit / record / fetch / verify / status`,
   in a loop, autonomously, until `status` says all done.
10. **Assemble.** `python3 assemble.py ../projects/<slug>`.
11. **Description.** `playbooks/04_description_and_thumbnail.md`. Use
    `prompts/description_prompt.txt` verbatim, base it on the narration files and
    never on the research notes, then run `description_check.py`.
12. **Thumbnail.** Use `prompts/thumbnail_prompt.txt` verbatim. It asks you to
    write an image prompt; that prompt is what goes to OpenArt. Show it, and
    regenerate until approved. Save the approved image itself to
    `projects/<slug>/out/thumbnail.png` (not just the prompt).
13. **Deliver.** Once the thumbnail is approved, run:
    `python3 deliver.py ../projects/<slug>`
    It verifies `description.md`, `out/captions.srt`, `out/thumbnail.png` and
    `out/final.mp4` all exist, then checks the video against
    `GIT_PUSH_MAX_BYTES`. `out/` is gitignored by default (generated media
    never belongs in git), so this step always needs `-f`:
    - **Under the limit:** `git add -f description.md out/captions.srt
      out/thumbnail.png out/final.mp4`, commit, push. The video ships in the
      repo alongside everything else.
    - **Over the limit:** `deliver.py` splits it into
      `out/chunks/final.mp4.part_NNN` files and writes a `.sha256` next to
      them. `git add -f description.md out/captions.srt out/thumbnail.png`
      (never the oversized video), commit, push, then send the chunk files to
      the user via chat (batch several per message) along with the sha256 and
      the reassembly command (`cat final.mp4.part_* > final.mp4`, or on
      Windows `copy /b`). Never attempt to push a blob over the limit -
      GitHub hard-rejects it and wastes the whole push.
    This is bookkeeping, not judgement - do it without asking, the same way
    the earlier deterministic stages run without check-ins.

## Resuming

`python3 manifest.py status ../projects/<slug>` reports exactly what remains.
Downloaded frames persist. Never regenerate a scene already marked done.
