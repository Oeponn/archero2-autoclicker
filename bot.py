"""
bot.py — Archero 2 Background Autoclicker

Main entry point. Finds the iPhone Mirroring window, loads templates,
and runs the game state machine in a loop.

Usage:
    python bot.py           # normal run
    python bot.py --test    # click/swipe test then click start button

Stop:
    Ctrl+C in the terminal

Requirements:
    1. pip install -r requirements.txt
    2. Grant Terminal (or iTerm2) permissions in System Settings → Privacy & Security:
       - Accessibility
       - Screen Recording
    3. Have Archero 2 open in iPhone Mirroring (non-fullscreen, visible on your desktop)
"""

import os
import sys
import signal
import time

import config
import window as win_mod
import vision
import clicker_quartz as clicker
from state_machine import GameStateMachine


# ── Graceful shutdown ────────────────────────────────────────────────────────

_stopped = False


def _signal_handler(signum, frame):
    global _stopped
    _stopped = True
    print("\n\n  Ctrl+C received — shutting down...")


signal.signal(signal.SIGINT, _signal_handler)


# ── Validation ───────────────────────────────────────────────────────────────

def check_images() -> list[str]:
    """Return list of missing required image files."""
    missing = []
    for name, path in config.IMAGE_PATHS.items():
        if not os.path.exists(path):
            missing.append(f"  {name}: {path}")
    return missing


def check_permissions() -> None:
    """
    Quick sanity check: try to list windows.
    If Screen Recording permission is missing, CGWindowListCopyWindowInfo
    returns an empty/minimal list.
    """
    window_list = None
    try:
        import Quartz
        window_list = Quartz.CGWindowListCopyWindowInfo(
            Quartz.kCGWindowListOptionOnScreenOnly, Quartz.kCGNullWindowID
        )
    except Exception:
        pass

    if window_list is None or len(window_list) < 3:
        print("⚠️  Screen Recording permission may not be granted.")
        print("   Go to: System Settings → Privacy & Security → Screen Recording")
        print("   Add your Terminal app, then restart it.\n")


# ── Test mode ────────────────────────────────────────────────────────────────

def run_test(bounds: tuple, scale: float, templates: dict) -> None:
    """
    Diagnostic test: taps, swipes, then tries to click the start button.
    Run with: python bot.py --test
    """
    bx, by, bw, bh = bounds
    cx = bx + bw / 2          # screen-absolute center X
    cy = by + bh / 2          # screen-absolute center Y

    print("\n── Test: 3 taps at window center ───────────────────")
    for i in range(1, 4):
        print(f"  Tap {i}/3 at ({cx:.0f}, {cy:.0f})")
        clicker.click_at(cx, cy)
        time.sleep(0.6)

    print("\n── Test: 3 swipes UP from center ───────────────────")
    for i in range(1, 4):
        start_y = by + bh * 0.75
        end_y   = by + bh * 0.35
        print(f"  Swipe up {i}/3  ({cx:.0f}, {start_y:.0f}) → ({cx:.0f}, {end_y:.0f})")
        clicker.drag(cx, start_y, cx, end_y, duration=0.35)
        time.sleep(0.8)

    print("\n── Test: 3 swipes DOWN from center ─────────────────")
    for i in range(1, 4):
        start_y = by + bh * 0.35
        end_y   = by + bh * 0.75
        print(f"  Swipe down {i}/3  ({cx:.0f}, {start_y:.0f}) → ({cx:.0f}, {end_y:.0f})")
        clicker.drag(cx, start_y, cx, end_y, duration=0.35)
        time.sleep(0.8)

    print("\n── Test: click start button ────────────────────────")
    import vision as vis
    img = win_mod.screenshot(win_mod.find_window(config.IPHONE_MIRRORING_WINDOW_NAME))
    match = vis.find_template(img, templates.get("start"))
    if match:
        mx, my, tw, th = match
        sx, sy = clicker.window_to_screen(mx, my, bounds, scale)
        print(f"  Found start button at window pixel ({mx}, {my}) → screen ({sx:.0f}, {sy:.0f})")
        clicker.click_at(sx, sy)
        print("  Clicked!")
    else:
        print("  Start button not found in current screenshot.")
        print("  Make sure the game is on the main menu with the Start button visible.")

    print("\n── Test complete ────────────────────────────────────\n")


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    print("=" * 55)
    print("  Archero 2 Background Autoclicker")
    print("=" * 55)
    print()

    # Check permissions
    check_permissions()

    # Validate images
    missing = check_images()
    if missing:
        print("❌ Missing reference images:")
        for m in missing:
            print(m)
        print("\nPlace the required images in the images/ directory.")
        sys.exit(1)
    print("✅ All reference images found.")

    # Find iPhone Mirroring window
    print(f"\nLooking for '{config.IPHONE_MIRRORING_WINDOW_NAME}' window...")
    window_info = None
    for _ in range(10):
        window_info = win_mod.find_window(config.IPHONE_MIRRORING_WINDOW_NAME)
        if window_info:
            break
        time.sleep(1)

    if window_info is None:
        print(f"❌ Could not find '{config.IPHONE_MIRRORING_WINDOW_NAME}' window.")
        print("   Make sure iPhone Mirroring is open and visible on your desktop.")
        sys.exit(1)

    bounds = win_mod.get_bounds(window_info)
    scale = win_mod.get_scale_factor()
    print(f"✅ Found window at ({bounds[0]:.0f}, {bounds[1]:.0f}), "
          f"size {bounds[2]:.0f}×{bounds[3]:.0f}, scale={scale:.1f}x")

    # Test screenshot
    test_img = win_mod.screenshot(window_info)
    if test_img is None:
        print("❌ Failed to capture window screenshot.")
        print("   Check Screen Recording permission.")
        sys.exit(1)
    print(f"✅ Screenshot captured: {test_img.shape[1]}×{test_img.shape[0]} pixels")

    # Load templates
    print("\nLoading reference images...")
    templates = vision.load_templates()
    print(f"✅ Loaded {len(templates)} templates.")

    # ── Test mode ────────────────────────────────────────────────────────────
    if "--test" in sys.argv:
        print("\n⚡ TEST MODE — tapping, swiping, then clicking start button.")
        print("   Switch to iPhone Mirroring now — starting in 3s...")
        time.sleep(3)
        run_test(bounds, scale, templates)
        return

    # Instructions
    print()
    print("─" * 55)
    print("  RUNNING — you can use your computer normally.")
    print("  Keep iPhone Mirroring visible (not full-screen).")
    print("  Press Ctrl+C in this terminal to stop.")
    print("─" * 55)
    print()

    # Create state machine
    sm = GameStateMachine(templates=templates, scale=scale)

    # Main loop
    try:
        while not _stopped:
            should_continue = sm.tick()
            if not should_continue:
                break
            time.sleep(config.POLL_INTERVAL)
    except KeyboardInterrupt:
        pass

    # Summary
    print()
    print("=" * 55)
    print(f"  Autoclicker stopped.")
    print(f"  Completed {sm.run_count} run(s).")
    print("=" * 55)


if __name__ == "__main__":
    main()
