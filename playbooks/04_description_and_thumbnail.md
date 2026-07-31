# Stage 11-12 — description, then thumbnail

## Description

Use `prompts/description_prompt.txt` **verbatim**. It is the creator's standing
prompt, not something to improve on.

The one thing that goes wrong: "based on my transcript" means the actual
narration. Not the research notes. A past episode named researchers in the
description who were never spoken in the video, because the research file was
sitting next to the script and had more names in it.

Before naming anybody, grep the real narration for capitalised names and use only
what survives:

```bash
grep -ohE '\b[A-Z][a-z]+ [A-Z][a-z]+\b' ../projects/<slug>/narration_part*.txt | sort -u
```

Rules that hold for every project unless `project.json` says otherwise:

- No hashtags.
- No "Sources" section unless a source is named aloud in the video.
- Section headers come from this video's own beat structure, not from a template.
- Timestamps are optional and not part of the default flow.

Save as `description.md`, then:

```bash
python3 description_check.py ../projects/<slug>/description.md ../projects/<slug>/project.json
```

It hard-fails over YouTube's 5,000-character cap or on any hashtag. Do not skip
it. A description can clear the 500-word floor and still be nowhere near the
character limit, or comfortably over it; only the script tells you which.

## Thumbnail

Use `prompts/thumbnail_prompt.txt` **verbatim**. Read what it is actually asking
for: it is a request for *you to write an image prompt*, not a prompt to hand to
the image model. Two steps.

**Step 1 — design the prompt for this specific video.** Constraints, all of them:

- on-image text under six words, and fewer is better — the channels that win in
  most niches run one or two
- not a copy of the video title
- a composition built to stop a scroll: tight, high-contrast, a single face or
  object at its most dramatic moment, strong rim lighting to separate subject
  from background, readable at 210 pixels wide
- the two-word question convention works across niches: `SICK?`, `NO JOBS?`,
  `WHY VANISH?`

**Step 2 — generate it** with OpenArt: nano-banana-2, 2K, 16:9,
`autoEnhancePrompt: false`.

This is the one image in the whole video that deliberately overrides the style
block's "no text anywhere" rule.

**Then ask for approval.** It is the single most-seen asset of the video and the
only one that decides whether anything else gets watched. If it is rejected, ask
what to change, regenerate, and ask again. Loop until it is approved — this
approval is not one of the two hard gates, but it is not optional either.

Save the winning prompt to `thumbnail_prompt_used.txt` in the project folder.
