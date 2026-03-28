"""
testClick.py — Diagnose click delivery to iPhone Mirroring.

Usage:
    python testClick.py info        # show window info + what's at the target coords
    python testClick.py pyautogui   # hijacks mouse, double-click (focus then press)
    python testClick.py quartz      # CGEventPost at target coords (cursor moves)
    python testClick.py activate    # briefly bring iPhone Mirroring to front, click, restore focus
"""

import sys
import time

import window as win_mod
import vision
import config


def find_start(templates):
    """Screenshot the window and find the start button. Returns (info, bounds, scale, img, match)."""
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
    return info, bounds, scale, img, match


def print_target(bounds, scale, match):
    import clicker_quartz as clicker
    cx, cy, tw, th = match
    sx, sy = clicker.window_to_screen(cx, cy, bounds, scale)
    print(f"   window pixel : ({cx}, {cy})  size {tw}×{th}")
    print(f"   screen point : ({sx:.0f}, {sy:.0f})")
    print(f"   window bounds: x={bounds[0]:.0f} y={bounds[1]:.0f} "
          f"w={bounds[2]:.0f} h={bounds[3]:.0f}")
    print(f"   retina scale : {scale}x")
    return sx, sy


# ── info mode ─────────────────────────────────────────────────────────────────

def mode_info(info, bounds, scale, match):
    import Quartz
    from AppKit import NSWorkspace

    print("\n── Window info ──────────────────────────────────────")
    import clicker_quartz as clicker
    sx, sy = print_target(bounds, scale, match)

    pid = win_mod.get_pid(info)
    print(f"   iPhone Mirroring PID: {pid}")

    # Check Accessibility permission
    print(f"\n── Accessibility ────────────────────────────────────")
    try:
        from ApplicationServices import AXIsProcessTrusted
        trusted = AXIsProcessTrusted()
    except Exception:
        # Fall back to a Quartz-level check
        try:
            trusted = Quartz.CGPreflightScreenCaptureAccess()
            print("   (using CGPreflightScreenCaptureAccess as proxy)")
        except Exception:
            trusted = None
    print(f"   Trusted: {trusted}")
    if trusted is False:
        print("   ⚠️  Not trusted — clicks may be silently dropped.")
        print("   Fix: System Settings → Privacy & Security → Accessibility → add Terminal")

    # List all on-screen windows and find what's at the target coordinates
    print(f"\n── Windows at/near target ({sx:.0f}, {sy:.0f}) ─────────────")
    window_list = Quartz.CGWindowListCopyWindowInfo(
        Quartz.kCGWindowListOptionOnScreenOnly | Quartz.kCGWindowListExcludeDesktopElements,
        Quartz.kCGNullWindowID,
    )
    hits = []
    for w in (window_list or []):
        b = w.get(Quartz.kCGWindowBounds, {})
        wx, wy = b.get("X", 0), b.get("Y", 0)
        ww, wh = b.get("Width", 0), b.get("Height", 0)
        if wx <= sx <= wx + ww and wy <= sy <= wy + wh:
            hits.append(w)

    if hits:
        for w in hits:
            owner = w.get(Quartz.kCGWindowOwnerName, "?")
            name  = w.get(Quartz.kCGWindowName, "")
            layer = w.get(Quartz.kCGWindowLayer, "?")
            b     = w.get(Quartz.kCGWindowBounds, {})
            print(f"   ✓ '{owner}' / '{name}'  layer={layer}  "
                  f"bounds=({b.get('X',0):.0f},{b.get('Y',0):.0f} "
                  f"{b.get('Width',0):.0f}×{b.get('Height',0):.0f})")
    else:
        print("   (no windows found at target coords)")

    # Frontmost app
    front = NSWorkspace.sharedWorkspace().frontmostApplication()
    print(f"\n── Frontmost app ────────────────────────────────────")
    print(f"   {front.localizedName()}  (PID {front.processIdentifier()})")


# ── pyautogui method ──────────────────────────────────────────────────────────

def mode_pyautogui(bounds, scale, match):
    import pyautogui
    import clicker_quartz as clicker
    cx, cy, tw, th = match
    sx, sy = clicker.window_to_screen(cx, cy, bounds, scale)
    print(f"  Click 1/2 at ({sx:.0f}, {sy:.0f}) — focusing window")
    pyautogui.click(sx, sy)
    time.sleep(0.3)
    print(f"  Click 2/2 at ({sx:.0f}, {sy:.0f}) — pressing button")
    pyautogui.click(sx, sy)
    print("  Done.")


# ── Quartz CGEventPostToPid ───────────────────────────────────────────────────

def mode_quartz(info, bounds, scale, match):
    import clicker_quartz as clicker
    cx, cy, tw, th = match
    sx, sy = clicker.window_to_screen(cx, cy, bounds, scale)
    pid = win_mod.get_pid(info)
    print(f"  CGEventPostToPid({pid}) click at ({sx:.0f}, {sy:.0f})")
    clicker.click_at(sx, sy, pid=pid, delay=0.1)
    print("  Done — cursor should NOT have moved.")


# ── Activate + click + restore ────────────────────────────────────────────────

def mode_activate(info, bounds, scale, match):
    """
    Briefly bring iPhone Mirroring to front, click, restore previous app.
    The flash is ~300ms — fast enough to barely notice.
    """
    import clicker_quartz as clicker
    from AppKit import NSWorkspace, NSApplicationActivateIgnoringOtherApps
    import AppKit

    cx, cy, tw, th = match
    sx, sy = clicker.window_to_screen(cx, cy, bounds, scale)

    # Remember the currently active app so we can restore it
    ws = NSWorkspace.sharedWorkspace()
    prev_app = ws.frontmostApplication()
    print(f"  Current frontmost app: {prev_app.localizedName()}")

    # Find the iPhone Mirroring NSRunningApplication
    pid = win_mod.get_pid(info)
    im_app = None
    for app in ws.runningApplications():
        if app.processIdentifier() == pid:
            im_app = app
            break

    if im_app is None:
        print("❌ Could not find iPhone Mirroring in running applications.")
        return

    print(f"  Activating '{im_app.localizedName()}' (PID {pid})...")
    im_app.activateWithOptions_(NSApplicationActivateIgnoringOtherApps)
    time.sleep(0.2)   # let it come to front

    print(f"  Clicking at ({sx:.0f}, {sy:.0f}) — cursor will warp back instantly")
    clicker.click_at(sx, sy, delay=0.1)

    time.sleep(0.1)

    print(f"  Restoring '{prev_app.localizedName()}'...")
    prev_app.activateWithOptions_(NSApplicationActivateIgnoringOtherApps)

    print("  Done — did the game respond? (cursor should be back where it was)")


# ── Warp test ─────────────────────────────────────────────────────────────────

def mode_warptest(info, bounds, scale):
    """Click randomly near window center every second for 10s, logging each click."""
    import random
    from AppKit import NSWorkspace, NSApplicationActivateIgnoringOtherApps

    bx, by, bw, bh = bounds
    pid = win_mod.get_pid(info)
    ws  = NSWorkspace.sharedWorkspace()

    # Resolve apps once
    im_app   = next((a for a in ws.runningApplications() if a.processIdentifier() == pid), None)
    prev_app = ws.frontmostApplication()

    print(f"  Window center: screen ({bx + bw/2:.0f}, {by + bh/2:.0f})")
    print(f"  Clicks will land within ±15% of center")
    print()

    for i in range(1, 11):
        # Random offset within ±15% of window size around center
        jx = random.uniform(-bw * 0.15, bw * 0.15)
        jy = random.uniform(-bh * 0.15, bh * 0.15)
        sx = bx + bw / 2 + jx
        sy = by + bh / 2 + jy

        # Activate, click, restore
        if im_app:
            im_app.activateWithOptions_(NSApplicationActivateIgnoringOtherApps)
            time.sleep(0.15)

        print(f"  [{i:02d}/10] click at screen ({sx:.0f}, {sy:.0f})", flush=True)
        clicker.click_at(sx, sy, delay=0.05)

        if prev_app:
            prev_app.activateWithOptions_(NSApplicationActivateIgnoringOtherApps)

        time.sleep(1.0)

    print("\n  Done — how did the cursor feel?")


# ── Main ──────────────────────────────────────────────────────────────────────

MODES = ("info", "pyautogui", "quartz", "activate", "warptest")

def main():
    if len(sys.argv) < 2 or sys.argv[1] not in MODES:
        print("Usage:")
        for m in MODES:
            print(f"  python testClick.py {m}")
        sys.exit(1)

    method = sys.argv[1]

    print(f"\nLoading templates...")
    templates = vision.load_templates()

    print(f"Finding start button in iPhone Mirroring window...")
    result = find_start(templates)
    if result is None:
        sys.exit(1)

    info, bounds, scale, img, match = result
    print(f"✅ Found start button:")
    print_target(bounds, scale, match)

    if method == "info":
        mode_info(info, bounds, scale, match)
        return

    if method == "warptest":
        print(f"\nStarting warp test in 3 seconds — 10 clicks, 1 per second...")
        time.sleep(3)
        print("── Warp test ──")
        mode_warptest(info, bounds, scale)
        return

    print(f"\nStarting in 3 seconds...")
    time.sleep(3)

    if method == "pyautogui":
        print("── pyautogui (mouse hijack) ──")
        mode_pyautogui(bounds, scale, match)
    elif method == "quartz":
        print("── Quartz CGEventPostToPid (no cursor movement) ──")
        mode_quartz(info, bounds, scale, match)
    elif method == "activate":
        print("── Activate + click + restore ──")
        mode_activate(info, bounds, scale, match)


if __name__ == "__main__":
    main()
