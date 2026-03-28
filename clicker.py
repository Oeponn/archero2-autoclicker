"""
clicker.py — Archero 2 autoclicker

Automates daily energy usage: finds and clicks the start/continue buttons
in a loop until energy runs out or a timeout is reached.

Usage:
    python clicker.py

ABORT anytime by moving your mouse to the TOP-LEFT corner of the screen.

Prerequisites:
    1. pip install -r requirements.txt
    2. Grant Terminal Accessibility + Screen Recording in:
       System Settings → Privacy & Security
    3. Run capture.py first to create reference images in images/
"""

import os
import sys
import time
import pyautogui

# ── Safety ──────────────────────────────────────────────────────────────────
pyautogui.FAILSAFE = True   # Move mouse to top-left corner to abort immediately
pyautogui.PAUSE = 0.3       # Small pause between every pyautogui call

# ── Config ───────────────────────────────────────────────────────────────────
CONFIDENCE = 0.85           # Match confidence (0–1). Lower if buttons aren't found.
CLICK_DELAY = 1.5           # Seconds to wait after clicking before looking again
STAGE_TIMEOUT = 300         # Max seconds to wait for a stage to finish (5 min)
MAX_RUNS = 50               # Safety cap on total stage runs

IMAGES = {
    "start":     "images/start_btn.png",
    "continue":  "images/continue_btn.png",
    "no_energy": "images/no_energy.png",   # optional — triggers loop exit
}

# ── Helpers ──────────────────────────────────────────────────────────────────

def find(image_path: str) -> tuple | None:
    """Return center (x, y) of image_path on screen, or None if not found."""
    if not os.path.exists(image_path):
        return None
    try:
        location = pyautogui.locateCenterOnScreen(image_path, confidence=CONFIDENCE)
        return location  # Box(left, top, width, height) center point or None
    except pyautogui.ImageNotFoundException:
        return None


def click_image(image_path: str, label: str) -> bool:
    """Find and click an image. Returns True on success."""
    pos = find(image_path)
    if pos:
        print(f"  Found '{label}' at {pos} — clicking")
        pyautogui.click(pos)
        time.sleep(CLICK_DELAY)
        return True
    return False


def wait_for_image(image_path: str, label: str, timeout: int) -> bool:
    """Poll for an image to appear within timeout seconds. Returns True if found."""
    print(f"  Waiting for '{label}'...", end="", flush=True)
    deadline = time.time() + timeout
    while time.time() < deadline:
        if find(image_path):
            print(" found.")
            return True
        time.sleep(1)
        print(".", end="", flush=True)
    print(" timed out.")
    return False


def check_missing_images() -> list[str]:
    missing = []
    for key, path in IMAGES.items():
        if key == "no_energy":
            continue  # optional
        if not os.path.exists(path):
            missing.append(path)
    return missing

# ── Main loop ────────────────────────────────────────────────────────────────

def run() -> None:
    print("=" * 55)
    print("Archero 2 Autoclicker")
    print("Move mouse to TOP-LEFT corner at any time to abort.")
    print("=" * 55)

    missing = check_missing_images()
    if missing:
        print("\nMissing reference images:")
        for m in missing:
            print(f"  {m}")
        print("\nRun  python capture.py  first to create them.")
        sys.exit(1)

    print("\nStarting in 3 seconds — switch to iPhone Mirroring now...\n")
    time.sleep(3)

    for run_num in range(1, MAX_RUNS + 1):
        print(f"[Run {run_num}/{MAX_RUNS}]")

        # ── Check for no-energy popup (optional early exit) ──────────────────
        if os.path.exists(IMAGES["no_energy"]) and find(IMAGES["no_energy"]):
            print("  'No energy' detected — stopping.")
            break

        # ── Click start button ────────────────────────────────────────────────
        if not click_image(IMAGES["start"], "start"):
            print("  Start button not found. Retrying in 2s...")
            time.sleep(2)
            if not click_image(IMAGES["start"], "start"):
                print("  Still not found — stopping. Check your reference image or window position.")
                break

        # ── Wait for stage to finish ──────────────────────────────────────────
        found = wait_for_image(IMAGES["continue"], "continue", STAGE_TIMEOUT)
        if not found:
            print("  Stage didn't finish within timeout — stopping.")
            break

        # ── Click continue ────────────────────────────────────────────────────
        if not click_image(IMAGES["continue"], "continue"):
            print("  Continue button disappeared — will retry next loop.")
            time.sleep(1)

        print()  # blank line between runs

    print("\nAutoclicker finished.")


if __name__ == "__main__":
    run()
