"""
clicker_quartz.py — Quartz-based click and drag posting.

Uses CGEventPostToPid to deliver events directly to a specific process.
This does NOT move the visible mouse cursor and does NOT require the
target window to be frontmost.

All coordinates are in Quartz screen points (origin at top-left of main display).
"""

import time
import Quartz


def click_at(screen_x: float, screen_y: float, pid: int, delay: float = 0.05) -> None:
    """
    Post a left-click at the given screen coordinates directly to `pid`.
    The visible mouse cursor does NOT move.
    The target window does NOT need to be frontmost.
    """
    source = Quartz.CGEventSourceCreate(Quartz.kCGEventSourceStatePrivate)
    point  = Quartz.CGPointMake(screen_x, screen_y)

    event_down = Quartz.CGEventCreateMouseEvent(
        source, Quartz.kCGEventLeftMouseDown, point, Quartz.kCGMouseButtonLeft
    )
    Quartz.CGEventPostToPid(pid, event_down)

    time.sleep(delay)

    event_up = Quartz.CGEventCreateMouseEvent(
        source, Quartz.kCGEventLeftMouseUp, point, Quartz.kCGMouseButtonLeft
    )
    Quartz.CGEventPostToPid(pid, event_up)


def drag(
    start_x: float,
    start_y: float,
    end_x: float,
    end_y: float,
    pid: int,
    duration: float = 0.3,
    steps: int = 20,
) -> None:
    """
    Post a click-and-drag from (start_x, start_y) to (end_x, end_y) directly to `pid`.
    The visible mouse cursor does NOT move.
    """
    source      = Quartz.CGEventSourceCreate(Quartz.kCGEventSourceStatePrivate)
    start_point = Quartz.CGPointMake(start_x, start_y)

    event_down = Quartz.CGEventCreateMouseEvent(
        source, Quartz.kCGEventLeftMouseDown, start_point, Quartz.kCGMouseButtonLeft
    )
    Quartz.CGEventPostToPid(pid, event_down)

    step_delay = duration / steps
    for i in range(1, steps + 1):
        t  = i / steps
        ix = start_x + (end_x - start_x) * t
        iy = start_y + (end_y - start_y) * t
        event_drag = Quartz.CGEventCreateMouseEvent(
            source, Quartz.kCGEventLeftMouseDragged,
            Quartz.CGPointMake(ix, iy), Quartz.kCGMouseButtonLeft
        )
        Quartz.CGEventPostToPid(pid, event_drag)
        time.sleep(step_delay)

    event_up = Quartz.CGEventCreateMouseEvent(
        source, Quartz.kCGEventLeftMouseUp,
        Quartz.CGPointMake(end_x, end_y), Quartz.kCGMouseButtonLeft
    )
    Quartz.CGEventPostToPid(pid, event_up)


def window_to_screen(
    wx: float,
    wy: float,
    window_bounds: tuple[float, float, float, float],
    scale: float,
) -> tuple[float, float]:
    """
    Convert window-pixel coordinates (from a screenshot) to screen points.
    Screenshot pixels are 2x on Retina; divide by scale to get screen points.
    """
    bx, by, _, _ = window_bounds
    return bx + wx / scale, by + wy / scale
