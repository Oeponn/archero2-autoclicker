"""
testClick.py — Diagnose click delivery to iPhone Mirroring.

Usage:
    python testClick.py pyautogui   # hijacks mouse, clicks start button once
    python testClick.py quartz      # Quartz CGEventPost, no cursor movement

Both methods find the start button via image matching first, then click it.
Watch the game to see which method (if either) actually registers.
"""

import sys
import time

import cv2
import window as win_mod
import vision
import config


def find_start(templates):
    """Screenshot the window and find the start button. Returns (bounds, img, match) or None."""
    info = win_mod.find_window(config.IPHONE_MIRRORING_WINDOW_NAME)
    if info is None:
        print("❌ iPhone Mirroring window not found.")
        return None
    bounds = win_mod.get_bounds(info)
    scale = win_mod.get_scale_factor()
    img = win_mod.screenshot(info)
    if img is None:
        print("❌ Screenshot failed — check Screen Recording permission.")
        return None
    match = vision.find_template(img, templates.get("start"))
    if match is None:
        print("❌ Start button not found in screenshot — is it visible on screen?")
        return None
    return bounds, scale, img, match


# ── pyautogui method ──────────────────────────────────────────────────────────

def click_pyautogui(bounds, scale, match):
    import pyautogui
    cx, cy, tw, th = match
    import clicker_quartz as clicker
    sx, sy = clicker.window_to_screen(cx, cy, bounds, scale)
    print(f"  pyautogui click 1/2 at screen ({sx:.0f}, {sy:.0f}) — focusing window")
    pyautogui.click(sx, sy)
    time.sleep(0.3)
    print(f"  pyautogui click 2/2 at screen ({sx:.0f}, {sy:.0f}) — pressing button")
    pyautogui.click(sx, sy)
    print("  Done — did the game respond?")


# ── Quartz method ─────────────────────────────────────────────────────────────

def click_quartz(bounds, scale, match):
    import clicker_quartz as clicker
    cx, cy, tw, th = match
    sx, sy = clicker.window_to_screen(cx, cy, bounds, scale)
    print(f"  Quartz CGEventPost click at screen ({sx:.0f}, {sy:.0f})")
    clicker.click_at(sx, sy, delay=0.1)
    print("  Done — did the game respond?")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ("pyautogui", "quartz"):
        print("Usage:  python testClick.py pyautogui")
        print("        python testClick.py quartz")
        sys.exit(1)

    method = sys.argv[1]

    print(f"\nLoading templates...")
    templates = vision.load_templates()

    print(f"Finding start button in iPhone Mirroring window...")
    result = find_start(templates)
    if result is None:
        sys.exit(1)

    bounds, scale, img, match = result
    cx, cy, tw, th = match
    print(f"✅ Found start button:")
    print(f"   window pixel : ({cx}, {cy})  size {tw}×{th}")

    import clicker_quartz as clicker
    sx, sy = clicker.window_to_screen(cx, cy, bounds, scale)
    print(f"   screen point : ({sx:.0f}, {sy:.0f})")
    print(f"   window bounds: x={bounds[0]:.0f} y={bounds[1]:.0f} w={bounds[2]:.0f} h={bounds[3]:.0f}")
    print(f"   retina scale : {scale}x")
    print()
    print("Clicking in 3 seconds — switch to iPhone Mirroring now...")
    time.sleep(3)

    if method == "pyautogui":
        print("── pyautogui (mouse hijack) ──")
        click_pyautogui(bounds, scale, match)
    else:
        print("── Quartz CGEventPost (background) ──")
        click_quartz(bounds, scale, match)


if __name__ == "__main__":
    main()
