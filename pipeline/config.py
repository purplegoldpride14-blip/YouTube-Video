"""
Single source of truth for every pipeline constant.

RULE: if a number appears in PROCESS.md or SKILL.md, it is a comment describing
this file, not an independent statement of fact. If they disagree, this file wins.
"""

# ---------- script ----------
WORDS_MIN = 1800          # target band; outside this you get a WARNING
WORDS_MAX = 1900
WORDS_HARD_MIN = 1750     # outside the hard band the run STOPS
WORDS_HARD_MAX = 1950

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
IMAGE_MODEL = "nano-banana-2"
IMAGE_MODE = "text2image"
IMAGE_RESOLUTION = "2K"
IMAGE_ASPECT = "16:9"
IMAGE_COUNT = 1
AUTO_ENHANCE_PROMPT = False  # ALWAYS false - it rewrites the locked style block
MIN_IMAGE_BYTES = 10000      # anything smaller is a failed download, not an image

# ---------- video ----------
OUT_WIDTH = 1920
OUT_HEIGHT = 1080
OUT_FPS = 30
VIDEO_CRF = 18
VIDEO_PRESET = "medium"
MOTION_DEFAULT = "none"   # "none" | "kenburns"
KENBURNS_ZOOM = 1.08      # 8% travel over the life of a scene

# ---------- required network domains ----------
# Must be allowlisted BEFORE the run starts. Cannot be changed mid-session.
REQUIRED_DOMAINS = ["storage.googleapis.com", "cdn.openart.ai"]
