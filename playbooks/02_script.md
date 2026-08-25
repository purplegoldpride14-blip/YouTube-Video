# Stage 3 — the script

1,600 to 1,700 words. Roughly ten to eleven minutes of narration. Enforced by
`script_check.py`, which also splits the script into TTS-safe parts and strips
anything the voice-over would stumble on.

## Structure

**0:00-0:15 — the cold open.** No channel name, no "in today's video", no
throat-clearing. Open inside the situation, mid-moment, in the second person or
in close third. The first sentence should be short enough to read in one breath.

**0:15-0:45 — the promise, framed as a question.** State the thing the viewer
does not know and will know by the end. Then reframe it: most videos in every
niche ask the obvious question, and the retention comes from asking the better
one. "The question is not how they survived. The question is why your body
treats this as a wound."

**0:45-8:00 — three or four movements.** Each movement is a small arc: setup,
the specific fact that pays it off, then the implication. Between movements,
plant an open loop — a name, a number or a consequence you promise to return to
— and close it later. Never open more than two loops at once.

**8:00-10:30 — the turn.** The part the viewer did not see coming. Usually the
moment the historical or factual material becomes about them.

**Last 45 seconds — land it, then hand off.** Answer the opening question in one
sentence. No summary of what was covered. End on a line that is quotable rather
than conclusive. No "like and subscribe" in the narration.

## Retention tactics that actually move the number

- **Sentence length varies.** Long, long, short. The short one is where the
  attention resets. A script of uniformly medium sentences is a script people
  leave at four minutes.
- **Second person early.** "You" in the first thirty seconds converts a topic
  into a situation.
- **Specific over general.** "Seventy-one large animals across 2,076
  hunter-days" holds; "hunting was difficult" does not.
- **Re-hook every ninety seconds.** A question, a reversal, a number that
  contradicts the last one, or a direct address.
- **Never explain something the viewer already accepted.** The most common
  retention leak is the paragraph that restates the previous paragraph.
- **Cut the fourth example.** Three is a pattern; four is a list, and lists are
  where people leave.
- **Read the first sixty seconds aloud.** If it takes a breath you would not
  naturally take, rewrite it.

## Narration safety

The voice-over reads the text literally, so anything that is punctuation to a
reader is a stumble to a narrator. `script_check.py --fix` handles these
automatically:

- em dashes, en dashes and spaced hyphens become comma pauses
- numeric ranges become "1990 to 1995"
- `&` `%` `+` `=` `#` `@` `~` `/` `°` become the words
- `e.g.` `i.e.` `etc.` `vs.` `Dr.` `St.` `U.S.` `a.m.` become the words
- brackets, semicolons, ellipses, markdown and smart quotes are removed

These it flags for you to rewrite by hand, because substituting a token is not
the fix — the sentence is:

- **bare numerals** — spell them out; engines disagree about "1,204" and "2.5"
- **ALL-CAPS tokens** — decide whether it is a word or letters, and write it that way
- **currency** — "$5M" is read three different ways; write "five million dollars"
- **roman numerals** — "Henry VIII" is read as letters
- **URLs and emails** — say the name instead

## Then run

```bash
python3 script_check.py <script.txt> ../projects/<slug> --fix
```

It hard-fails outside 1,550-1,750 words, warns outside 1,600-1,700, and writes
`narration_part1.txt`..`partN.txt` split evenly under the 10,000-character TTS cap.
Balanced, not greedy: a 1,610/290 split gives the two halves different room tone
and makes the join audible.
