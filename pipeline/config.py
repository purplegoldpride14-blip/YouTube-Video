"""
Single source of truth for every pipeline constant.

RULE: if a number appears in PROCESS.md or SKILL.md, it is a comment describing
this file, not an independent statement of fact. If they disagree, this file wins.
"""

# ---------- script ----------
WORDS_MIN = 1600          # target band; outside this you get a WARNING
WORDS_MAX = 1700
WORDS_HARD_MIN = 1550     # outside the hard band the run STOPS
WORDS_HARD_MAX = 1750

TTS_CHAR_CAP = 10000      # engine hard limit per submission
TTS_CHAR_TARGET = 9500    # headroom so a late edit cannot push a part over

# ---------- narration safety (see narration_lint.py) ----------
# Characters the narrator stumbles on. Auto-fixed by the linter.
DASH_CHARS = ["\u2014", "\u2013", "\u2012", "\u2015", "\u2212"]  # em, en, figure, bar, minus
# Advisory issues (numerals, ALL CAPS, currency) WARN by default and FAIL with --strict.
LINT_STRICT_DEFAULT = False

# ---------- description ----------
DESCRIPTION_CHAR_CAP = 5000   # YouTube's real limit, not a style preference
DESCRIPTION_WORD_MIN = 500    # creator's own floor
DESCRIPTION_NO_HASHTAGS = True  # per-project override in project.json

# ---------- audio ----------
WAV_RATE = 44100
WAV_CHANNELS = 1
TARGET_LUFS = -14.0       # the volume boost target, applied in audio_merge.py
TARGET_TP = -1.5
TARGET_LRA = 11.0
LOUDNESS_TOLERANCE = 1.0  # assemble.py warns if the merged track drifts past this

# ---------- scenes ----------
SCENE_TARGET_SEC = 6.5    # average visual on screen
SCENE_MIN_SEC = 2.5       # below this, merge into a neighbour
SCENE_SOFT_MAX_SEC = 9.0  # above this, prefer a split at a sentence end
SCENE_HARD_MAX_SEC = 12.0 # above this, must split
SCENE_CAP = 220           # more than this and the image batch is not worth the credits

# Retention pacing: the opening runs faster than the body, then settles.
HOOK_SEC = 30.0           # length of the fast-cut opening window
HOOK_TARGET_SEC = 4.5     # average visual length inside the hook
# Anti-metronome: no more than this many consecutive scenes within 0.5s of each other.
MAX_UNIFORM_RUN = 6

# ---------- captions ----------
SRT_MAX_WORDS_PER_CUE = 5  # carried over unchanged

# ---------- images ----------
IMAGE_PROVIDER = "huggingface"
IMAGE_MODEL = "z-image-turbo"          # Tongyi-MAI/Z-Image-Turbo, Apache 2.0
IMAGE_SPACE = "mrfakename/Z-Image-Turbo"  # public Gradio Space (ZeroGPU), via
                                           # the Hugging Face MCP connector's
                                           # gr1_z_image_turbo_generate_image tool
IMAGE_WIDTH = 1280            # 16:9. Space allows 512-2048, no aspect param -
IMAGE_HEIGHT = 720             # width/height are set directly instead.
IMAGE_STEPS = 9                # "9 steps = 8 DiT forwards", the Space's own
                                # recommended default - do not raise for quality,
                                # this model is distilled for exactly this range.
IMAGE_RANDOMIZE_SEED = True    # each scene is an independent image; no reason
                                # to fix a seed across the batch.
# Params are prompt, width, height, num_inference_steps, seed, randomize_seed -
# nothing else. No negative-prompt field and no prompt-rewriting toggle to
# disable; the raw prompt is always what gets used.
# This is a shared public Space, not a paid API: expect ZeroGPU queueing under
# load, and the returned image URL is an ephemeral file on that Space's
# replica, not stable CDN storage. Download every scene's image immediately
# after generating it - do not defer fetching across a batch of recorded URLs
# the way the old OpenArt provider allowed.
MIN_IMAGE_BYTES = 10000      # anything smaller is a failed download, not an image

# ---------- video ----------
OUT_WIDTH = 1920
OUT_HEIGHT = 1080
OUT_FPS = 30
VIDEO_CRF = 18
VIDEO_PRESET = "medium"
MOTION_DEFAULT = "none"   # "none" | "kenburns"
KENBURNS_ZOOM = 1.08      # 8% travel over the life of a scene

# ---------- shorts ----------
SHORTS_WIDTH = 1080
SHORTS_HEIGHT = 1920
SHORTS_FONT = "DejaVu Sans"
SHORTS_FONT_SIZE = 58
SHORTS_BLUR_SIGMA = 22        # background blur strength behind the letterboxed clip
SHORTS_BG_DARKEN = -0.08      # eq brightness applied to the blurred background
SHORTS_MIN_SEC = 15           # below this, a clip is too thin to stand alone - WARN
SHORTS_SOFT_MAX_SEC = 30      # creator's target ceiling - WARN above this
SHORTS_HARD_MAX_SEC = 180     # YouTube Shorts' technical cap - FAIL

# ---------- delivery ----------
# GitHub hard-blocks a pushed blob over 100 MB. Stay well under that so a push
# never fails partway through.
GIT_PUSH_MAX_BYTES = 95_000_000
# SendUserFile hard-caps at 30 MiB per file. Stay under that with margin.
CHAT_CHUNK_BYTES = 25 * 1024 * 1024

# ---------- required network domains ----------
# Must be allowlisted BEFORE the run starts. Cannot be changed mid-session.
REQUIRED_DOMAINS = ["storage.googleapis.com", "cdn.openart.ai"]
