# Stage 1-2 — niche, then topic

## 1. Ask for the niche

Present this menu. One question, one answer, and always leave the door open.

> Which niche is this video for?
>
> 1. History
> 2. News and current events
> 3. Politics
> 4. Sports
> 5. People and biography
> 6. Science and space
> 7. True crime and mystery
> 8. Money, business and finance
> 9. Health, fitness and psychology
> 10. Technology and AI
> 11. Culture, film and music
> 12. Something else — type it
>
> You can also drop in screenshots or links of channels or videos in the space
> you want to target, and I will read the style off those instead.

If images or links come in, read them for: subject matter, thumbnail conventions,
title grammar, video length, visual treatment, and narration register. Record what
you see in `project.json` under `notes` — it feeds the style stage later.

Write the answer to `project.json`:

```bash
python3 new_project.py <slug> --niche "History" 
```

## 2. Research the niche, then propose ten ideas

Research before proposing. Ten ideas invented from general knowledge are ten
ideas about what was popular a year ago.

**What to look for**

- What is currently over-performing in the niche: view counts far above the
  channel's subscriber count, recent uploads still climbing.
- The angle that is saturated. If six channels covered it this month, the
  eleventh video does not win on quality.
- The adjacent question nobody answered. Most outlier videos are a familiar
  subject entered through an unfamiliar door.
- Title grammar that is working right now in that niche: question titles,
  number titles, "the day X happened", second-person framing.

**Tools, in order of usefulness**

- NextLev MCP if it is connected: `search_niche_finder_channels`,
  `youtube_channel_outliers`, `search_viral_videos_small_channels`,
  `get_similar_videos`, `youtube_search`. Outliers from small channels are the
  strongest signal available — they mean the topic carried the video, not the
  subscriber base.
- Web search for anything in the last few weeks the tools do not cover.
- If neither is available, say so plainly rather than proposing from memory.

**Then present exactly ten ideas.** For each: a working title, one line on the
hook, and one line on why it is not saturated. Number them, and end with:

> Pick a number, or write your own idea and I will research that instead.

This is the first of two approval gates. Wait for the answer.

## 3. Research the chosen topic

Real, verifiable facts with sources. Concrete numbers are what make narration
land — a specific figure with a specific denominator beats an adjective every
time. Collect more than the script will use; the surplus is what lets the script
choose its best five facts instead of using all nine.

Keep the research notes separate from the script. They are not the transcript,
and the description stage later depends on that distinction being real.
