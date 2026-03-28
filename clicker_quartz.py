"""
clicker_quartz.py — Quartz-based click and drag posting.

iPhone Mirroring requires events through the real HID system (kCGHIDEventTap).
To avoid the cursor visibly jumping, we:
  1. Save the current cursor position
  2. Post the click via HID (cursor moves briefly)
  3. Immediately warp the cursor back

The cursor is away from its original position for ~50ms — imperceptible.
All coordinates are in Quartz screen points (origin at top-left of main display).
"""

import time
import Quartz


def _get_cursor_pos() -> Quartz.CGPoint:
    """Return the current cursor position as a CGPoint."""
    return Quartz.CGEventGetLocation(Quartz.CGEventCreate(None))


def _post_hid(event) -> None:
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, event)


def click_at(screen_x: float, screen_y: float, pid: int = None, delay: float = 0.01) -> None:
    """
    Click at the given screen coordinates via HID event tap.
    Cursor warps back to its original position immediately after.
    `pid` is accepted for API compatibility but not used (HID tap is required).
    """
    original = _get_cursor_pos()
    point = Quartz.CGPointMake(screen_x, screen_y)

    event_down = Quartz.CGEventCreateMouseEvent(
        None, Quartz.kCGEventLeftMouseDown, point, Quartz.kCGMouseButtonLeft
    )
    _post_hid(event_down)
    time.sleep(delay)
    event_up = Quartz.CGEventCreateMouseEvent(
        None, Quartz.kCGEventLeftMouseUp, point, Quartz.kCGMouseButtonLeft
    )
    _post_hid(event_up)

    # Snap cursor back — happens so fast it's invisible
    Quartz.CGWarpMouseCursorPosition(original)


def drag(
    start_x: float,
    start_y: float,
    end_x: float,
    end_y: float,
    pid: int = None,
    duration: float = 0.3,
    steps: int = 20,
) -> None:
    """
    Click-and-drag via HID event tap.
    Cursor warps back to its original position after the drag completes.
    `pid` is accepted for API compatibility but not used.
    """
    original = _get_cursor_pos()

    event_down = Quartz.CGEventCreateMouseEvent(
        None, Quartz.kCGEventLeftMouseDown,
        Quartz.CGPointMake(start_x, start_y), Quartz.kCGMouseButtonLeft
    )
    _post_hid(event_down)

    step_delay = duration / steps
    for i in range(1, steps + 1):
        t  = i / steps
        ix = start_x + (end_x - start_x) * t
        iy = start_y + (end_y - start_y) * t
        event_drag = Quartz.CGEventCreateMouseEvent(
            None, Quartz.kCGEventLeftMouseDragged,
            Quartz.CGPointMake(ix, iy), Quartz.kCGMouseButtonLeft
        )
        _post_hid(event_drag)
        time.sleep(step_delay)

    event_up = Quartz.CGEventCreateMouseEvent(
        None, Quartz.kCGEventLeftMouseUp,
        Quartz.CGPointMake(end_x, end_y), Quartz.kCGMouseButtonLeft
    )
    _post_hid(event_up)

    Quartz.CGWarpMouseCursorPosition(original)


def window_to_screen(
    wx: float,
    wy: float,
    window_bounds: tuple[float, float, float, float],
    scale: float,
) -> tuple[float, float]:
    """Convert window-pixel coords to screen points. Screenshots are 2x on Retina."""
    bx, by, _, _ = window_bounds
    return bx + wx / scale, by + wy / scale
