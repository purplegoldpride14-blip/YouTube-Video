# Stage 7-9 — visual style, then the image batch

## 1. Research what is working, then offer options

Before presenting anything, look at what the top-performing recent videos in this
niche actually look like. Style is niche-dependent and it moves: the treatment
that carried a history channel two years ago reads as dated now.

Present four to six options, each described concretely enough that the difference
is obvious, and say which ones you saw performing and where. A starting menu by
niche — adjust it to what the research shows:

| Niche | Styles that tend to carry |
|---|---|
| History | painted storybook illustration; aged documentary photo-real; woodcut or engraving; flat vector infographic |
| News, politics | photo-real editorial composites; clean graphic-card style with strong colour blocking; muted documentary realism |
| Sports | high-contrast stylised action illustration; poster-graphic with heavy typography; photo-real stadium lighting |
| People, biography | cinematic portrait realism; retro film-grain era-accurate; hand-drawn character illustration |
| Science, space | photo-real 3D render; NASA-plate realism; clean diagrammatic vector |
| True crime | desaturated noir realism; grainy evidence-photo look; silhouette and shadow illustration |
| Money, business | bold flat vector; isometric 3D; newspaper-collage |
| Health, psychology | soft medical illustration; warm minimal vector; anatomical diagram realism |
| Tech, AI | neon-dark futurism; clean product-render minimalism; glitch-collage |
| Culture, film, music | poster-art illustration; era-accurate photo-real; bold graphic collage |

Always close with:

> Or describe the look you want in your own words, or send reference images and I
> will write the style block from those.

If reference images arrive, describe them back in the style block's own
vocabulary — medium, line quality, colour treatment, lighting, background
handling, composition, and what to exclude.

## 2. Write style.json

```json
{
  "style_block": "one paragraph, appended verbatim to every scene prompt",
  "characters": {
    "KEY": "the exact descriptor phrase, reused word for word in every prompt"
  },
  "reference_notes": "what the reference images or research showed"
}
```

The style block must cover: medium, character or subject treatment, background
treatment, lighting, palette, composition, and an explicit exclusion list. End it
with `no text anywhere in the image` — the thumbnail is the only exception, and
it overrides this deliberately.

**Character descriptors are copied, never paraphrased.** Every prompt that
features a recurring subject repeats the identical phrase. Paraphrasing is how
faces drift over a hundred images.

## 3. Lock the style on scene 1

Generate **scene 1 only**, using its real prompt from `prompts.json`, at the
locked settings:

```
model nano-banana-2 | text2image | 2K | 16:9 | count 1 | autoEnhancePrompt false
```

`autoEnhancePrompt` must be false. It rewrites the style block, and the subjects
drift between scenes.

Show it. Wait. This is the second and last approval gate. If it is rejected, ask
what specifically to change, edit the style block, regenerate scene 1, and show
it again. Do not proceed on a maybe — every later image inherits this decision.

## 4. Then run the whole batch without stopping

Once scene 1 is approved, generate every remaining scene automatically. No
check-ins, no "shall I continue", no progress approvals. Stop only for a blocking
failure: a blocked domain, a hard cap, a validator failing.

```bash
python3 manifest.py init   ../projects/<slug>
python3 manifest.py next   ../projects/<slug> 4     # then submit each via OpenArt
python3 manifest.py submit ../projects/<slug> <n> <historyId>
python3 manifest.py record ../projects/<slug> <n> <url>
python3 manifest.py fetch  ../projects/<slug>
python3 manifest.py verify ../projects/<slug>
python3 manifest.py status ../projects/<slug>
```

Never hold batch state in context. `status` is the only source of truth about
what is left, and `retry` puts a failed scene back in the queue.

## A worked style.json

From a history channel that runs illustrated rather than photo-real. Note that
the character entry is a phrase, not a description — it is pasted into prompts
verbatim, every time, unchanged.

```json
{
  "style_block": "Hand-drawn 2D cartoon webcomic illustration. Characters are stick figures with perfectly round white heads, thin black outlines, large oval eyes with big black pupils, no nose, simple line mouths, and thin black noodle limbs with angular kinks at the elbows and knees. Painted storybook background with soft gradient shading, warm glowing firelight, saturated skies, textured rock and earth, high contrast against the flat white characters. Cinematic 16:9 composition, bold and readable at small size. No photorealism, no 3D render, no anime, no realistic human faces, no watermark, no signature, no extra fingers, no distorted limbs, no garbled or misspelled lettering, no text anywhere in the image.",
  "characters": {
    "EXILE": "the exile, a stick figure ancient human with a round white head, wide worried eyes, messy shoulder-length dark brown hair and a shaggy brown fur wrap over one shoulder",
    "BAND": "band members, stick figure ancient humans with round white heads and shaggy brown fur wraps"
  },
  "reference_notes": "matched to the three top-performing channels in the niche; all three run flat character art over painted backgrounds"
}
```

A scene prompt is then: the shot description, with every character reference
replaced by its exact phrase, followed by the style block appended whole.
