"""
clicker_quartz.py — Quartz-based click and drag posting.

Posts mouse events directly via CGEventPost without moving the visible cursor.
All coordinates are in Quartz screen points (origin at top-left of main display).
"""

import time
import Quartz


def click_at(screen_x: float, screen_y: float, delay: float = 0.05) -> None:
    """
    Post a left-click (mousedown + mouseup) at the given screen coordinates.
    Does NOT move the visible mouse cursor.
    """
    point = Quartz.CGPointMake(screen_x, screen_y)

    # Mouse down
    event_down = Quartz.CGEventCreateMouseEvent(
        None, Quartz.kCGEventLeftMouseDown, point, Quartz.kCGMouseButtonLeft
    )
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, event_down)

    time.sleep(delay)

    # Mouse up
    event_up = Quartz.CGEventCreateMouseEvent(
        None, Quartz.kCGEventLeftMouseUp, point, Quartz.kCGMouseButtonLeft
    )
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, event_up)


def drag(
    start_x: float,
    start_y: float,
    end_x: float,
    end_y: float,
    duration: float = 0.3,
    steps: int = 20,
) -> None:
    """
    Post a click-and-drag from (start_x, start_y) to (end_x, end_y).
    Interpolates intermediate points over `duration` seconds.
    """
    start_point = Quartz.CGPointMake(start_x, start_y)

    # Mouse down at start
    event_down = Quartz.CGEventCreateMouseEvent(
        None, Quartz.kCGEventLeftMouseDown, start_point, Quartz.kCGMouseButtonLeft
    )
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, event_down)

    step_delay = duration / steps

    # Interpolate drag points
    for i in range(1, steps + 1):
        t = i / steps
        ix = start_x + (end_x - start_x) * t
        iy = start_y + (end_y - start_y) * t
        point = Quartz.CGPointMake(ix, iy)

        event_drag = Quartz.CGEventCreateMouseEvent(
            None, Quartz.kCGEventLeftMouseDragged, point, Quartz.kCGMouseButtonLeft
        )
        Quartz.CGEventPost(Quartz.kCGHIDEventTap, event_drag)
        time.sleep(step_delay)

    # Mouse up at end
    end_point = Quartz.CGPointMake(end_x, end_y)
    event_up = Quartz.CGEventCreateMouseEvent(
        None, Quartz.kCGEventLeftMouseUp, end_point, Quartz.kCGMouseButtonLeft
    )
    Quartz.CGEventPost(Quartz.kCGHIDEventTap, event_up)


def window_to_screen(
    wx: float,
    wy: float,
    window_bounds: tuple[float, float, float, float],
    scale: float,
) -> tuple[float, float]:
    """
    Convert window-pixel coordinates (from a screenshot) to screen points.

    The screenshot from CGWindowListCreateImage is in native pixels (2x on Retina),
    but CGEventPost expects screen points. So we divide by the scale factor.

    Args:
        wx, wy: Pixel coordinates within the window screenshot
        window_bounds: (x, y, width, height) in screen points
        scale: Retina scale factor (e.g. 2.0)

    Returns:
        (screen_x, screen_y) in Quartz screen points
    """
    bx, by, _, _ = window_bounds
    screen_x = bx + wx / scale
    screen_y = by + wy / scale
    return screen_x, screen_y
