"""
capture.py — Reference image capture tool

Run this script to take screenshots of buttons you want the autoclicker to recognize.
Each saved image in images/ will be used by clicker.py to find and click that button.

Usage:
    python capture.py

Then follow the prompts. Have Archero 2 open in iPhone Mirroring.
"""

import os
import time
import pyautogui
from PIL import Image

IMAGES_DIR = "images"


def capture_button(name: str) -> None:
    """
    Countdown then take a full screenshot, letting the user manually crop it
    with the built-in macOS screenshot tool instead — or just saves the full
    screen for reference.

    Preferred workflow: use macOS screenshot (Cmd+Shift+4) to drag-select the
    button region, save to images/<name>.png directly.
    """
    print(f"\nCapturing '{name}'")
    print("  Switch to the game window NOW. Screenshotting in 3 seconds...")
    for i in range(3, 0, -1):
        print(f"  {i}...")
        time.sleep(1)

    screenshot = pyautogui.screenshot()
    path = os.path.join(IMAGES_DIR, f"{name}_full.png")
    screenshot.save(path)
    print(f"  Full screenshot saved to {path}")
    print(f"  Open it and crop the button region, then save as images/{name}.png")


def guided_capture() -> None:
    os.makedirs(IMAGES_DIR, exist_ok=True)

    buttons = [
        ("start_btn",    "The button to START a stage (e.g. 'Play' or 'Enter')"),
        ("continue_btn", "The button shown AFTER a stage ends (e.g. 'Continue', 'Next', or the X to close results)"),
        ("no_energy",    "Any popup/dialog that appears when you run OUT OF ENERGY (optional — for auto-stop)"),
    ]

    print("=" * 60)
    print("Archero 2 — Button Capture Tool")
    print("=" * 60)
    print("This will take full screenshots so you can crop button regions.")
    print("Alternatively, use Cmd+Shift+4 to drag-select and save directly")
    print("to images/<button_name>.png — that's the fastest approach.\n")

    for name, description in buttons:
        existing = os.path.join(IMAGES_DIR, f"{name}.png")
        if os.path.exists(existing):
            print(f"[SKIP] {name}.png already exists.")
            continue

        answer = input(f"Capture '{name}' — {description}? (y/n): ").strip().lower()
        if answer == "y":
            capture_button(name)
        else:
            print(f"  Skipped. Remember to add images/{name}.png manually.")

    print("\nDone! Edit/crop the full screenshots and save button crops as:")
    for name, _ in buttons:
        print(f"  images/{name}.png")
    print("\nThen run: python clicker.py")


if __name__ == "__main__":
    guided_capture()
