# YouTube video pipeline

Automates a narrated YouTube video end to end, for any niche, from Claude Code.

Open the folder in Claude Code and type **`/youtube-video-pipeline`**, or just say
what you want — "make me a new video", "resume <slug>" — and the skill loads itself.

## Quickstart

```bash
cd pipeline
python3 preflight.py                       # always first; installs ffmpeg if needed
python3 new_project.py my-first-video --niche "History"
```

Then follow the skill. It runs twelve stages with two approval gates: you pick
the topic from ten researched ideas, and you approve the visual style off scene 1.
Everything between and after those runs without check-ins.

## What's here

| Path | What it is |
|---|---|
| `.claude/skills/youtube-video-pipeline/SKILL.md` | the skill definition — the agent's entry point |
| `PROCESS.md` | the spec, and why each rule exists |
| `playbooks/` | the editorial half: niche, script, style, description, thumbnail |
| `prompts/` | the two standing prompts, used verbatim |
| `pipeline/` | the deterministic half: eleven stdlib-only scripts |
| `projects/` | one folder per video; media is gitignored |

## Requirements

- Python 3.9+, ffmpeg (preflight installs it), curl
- Descript MCP for the transcript SRT
- OpenArt MCP for the images and thumbnail
- NextLev MCP is optional but makes the topic research much better

No pip installs. Everything in `pipeline/` is stdlib.

## Stage map

| # | Stage | Command |
|---|---|---|
| 1-2 | niche, ten ideas, topic research, title pick | `playbooks/01_niche_and_topic.md` |
| 3 | script, 1,800-1,900 words | `script_check.py <script> ../projects/<slug> --fix` |
| 4 | merge audio, verify order, boost to -14 LUFS | `audio_merge.py ../projects/<slug>/audio ../projects/<slug>` |
| 5 | align Descript SRT to the script | `srt_build.py ../projects/<slug>/srt ../projects/<slug>` |
| 6 | scene boundaries | `scene_plan.py propose\|build ../projects/<slug>` |
| 7-8 | style options, lock on scene 1 | `playbooks/03_visual_style.md` |
| 9 | full image batch, unattended | `manifest.py init\|next\|submit\|record\|fetch\|status` |
| 10 | assemble | `assemble.py ../projects/<slug> [--motion kenburns]` |
| 11 | description | `description_check.py ../projects/<slug>/description.md` |
| 12 | thumbnail, approved by you | `playbooks/04_description_and_thumbnail.md` |
