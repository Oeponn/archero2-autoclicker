"""
config.py — All constants, image paths, timing, and offset configuration.
"""

import os

# ── Window Discovery ─────────────────────────────────────────────────────────
IPHONE_MIRRORING_WINDOW_NAME = "iPhone Mirroring"

# ── Image Matching ───────────────────────────────────────────────────────────
CONFIDENCE = 0.75  # OpenCV TM_CCOEFF_NORMED threshold (0–1)

# Resolution WDA screenshots are resized to before template matching.
TEMPLATE_W = 652
TEMPLATE_H = 1440

# ── Timing ───────────────────────────────────────────────────────────────────
POLL_INTERVAL = 0.5        # Seconds between detection cycles in battle
CLICK_DELAY = 0.01         # Seconds between mousedown and mouseup (keep short to minimize cursor jump)
POST_ACTION_DELAY = 1.5    # Seconds to wait after a major action (skill pick, etc.)
ROULETTE_SPIN_WAIT = 3.0   # Seconds to wait for roulette spin animation
DRAG_DURATION = 0.4        # Seconds for the swipe-up drag gesture
START_WAIT = 3.0           # Seconds to wait after clicking start for talent glory
ENDING_TAP_DELAY = 2.0     # Seconds between taps on ending screens

# ── Safety ───────────────────────────────────────────────────────────────────
MAX_RUNS = 50              # Maximum stage runs before auto-stop
IDLE_TIMEOUT = 30          # Seconds to wait for start button before giving up
STATE_TIMEOUT = 15         # Seconds to wait for expected screen transitions

# ── Images ───────────────────────────────────────────────────────────────────
IMAGES_DIR = "images"

# Native iOS screenshot folder (iPhone 16 Pro: 1206×2622 px, same as WDA).
# Crop a screenshot on your phone, AirDrop it here, reference it in IMAGE_PATHS
# below — vision.py auto-scales it to TEMPLATE resolution at load time.
NATIVE_IMAGES_DIR = "images_native"
NATIVE_W = 1206   # Native / WDA screenshot width  (iPhone 16 Pro portrait)
NATIVE_H = 2622   # Native / WDA screenshot height

def _n(name: str) -> str:
    """Return path for a native iOS screenshot in images_native/."""
    return os.path.join(NATIVE_IMAGES_DIR, name)

IMAGE_PATHS = {
    # Phase 1: Start / Ready
    "start":              _n("0_start_btn.jpg"),
    "ready":              _n("0_ready_btn.jpg"),

    # Phase 2: Talent Glory (3-skill pick middle)
    "talent_glory":       _n("3_talent_glory.jpg"),

    # Phase 3: Roulette
    "roulette_banner":    _n("a_roulette_banner.jpg"),
    "roulette_start":     _n("a_roulette_start.jpg"),

    # Battle events
    "level_up":           _n("3_level_up.jpg"),
    "valkyrie":           _n("2_encountered_valkyrie.jpg"),
    "angel":              _n("2_met_an_angel.jpg"),
    "devil":              _n("1_met_a_devil.jpg"),
    "reject":             _n("1_reject.jpg"),

    # Ending
    "challenge_ended":    _n("ending_challenge_ended.jpg"),
    "tap_empty":          _n("ending_tap_empty.jpg"),
    "reward":             _n("ending_reward.jpg"),
}

# ── Skill Click Offsets ──────────────────────────────────────────────────────
# Expressed as multiples of the detected banner dimensions for resolution
# independence. After detecting a banner at (cx, cy) with size (bw, bh):
#   click_x = cx + x_mult * bw
#   click_y = cy + y_mult * bh

# 3-skill layout (talent glory, level up): pick the MIDDLE skill
THREE_SKILL_MIDDLE_X_MULT = 0.0     # Centered horizontally with banner
THREE_SKILL_MIDDLE_Y_MULT = 6.5     # ~6.5 banner heights below

# 2-skill layout (valkyrie, angel): pick the LEFT skill
TWO_SKILL_LEFT_X_MULT = -0.33       # Left of center by 1/3 banner width
TWO_SKILL_LEFT_Y_MULT = 6.8         # ~6.8 banner heights below

# Swipe-up gesture: fraction of window height to drag
SWIPE_UP_FRACTION = 0.3             # Drag upward 30% of window height
