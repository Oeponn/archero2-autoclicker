"""
config.py — All constants, image paths, timing, and offset configuration.
"""

import os

# ── Window Discovery ─────────────────────────────────────────────────────────
IPHONE_MIRRORING_WINDOW_NAME = "iPhone Mirroring"

# ── Image Matching ───────────────────────────────────────────────────────────
CONFIDENCE = 0.85  # OpenCV TM_CCOEFF_NORMED threshold (0–1)

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

IMAGE_PATHS = {
    # Phase 1: Start
    "start":              os.path.join(IMAGES_DIR, "0_start_btn.png"),

    # Phase 2: Talent Glory (3-skill pick middle)
    "talent_glory":       os.path.join(IMAGES_DIR, "3_talent_glory.png"),

    # Phase 3: Roulette
    "roulette_banner":    os.path.join(IMAGES_DIR, "a_roulette_banner.png"),
    "roulette_start":     os.path.join(IMAGES_DIR, "a_roulette_start.png"),

    # Battle events
    "level_up":           os.path.join(IMAGES_DIR, "3_level_up.png"),
    "valkyrie":           os.path.join(IMAGES_DIR, "2_encountered_valkyrie.png"),
    "angel":              os.path.join(IMAGES_DIR, "2_met_an_angel.png"),
    "devil":              os.path.join(IMAGES_DIR, "1_met_a_devil.png"),
    "reject":             os.path.join(IMAGES_DIR, "1_reject.png"),

    # Ending
    "tap_empty":          os.path.join(IMAGES_DIR, "ending_tap_empty.png"),
    "reward":             os.path.join(IMAGES_DIR, "ending_reward.png"),
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
