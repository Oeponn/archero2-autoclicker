"""
window.py — iPhone Mirroring window discovery and screenshot capture.

Uses macOS Quartz APIs to find the window and capture its contents
without requiring it to be the frontmost window.
"""

import numpy as np
import Quartz
from AppKit import NSScreen


def find_window(owner_name: str = "iPhone Mirroring") -> dict | None:
    """
    Find the iPhone Mirroring window by owner name.
    Returns the window info dict, or None if not found.
    """
    window_list = Quartz.CGWindowListCopyWindowInfo(
        Quartz.kCGWindowListOptionOnScreenOnly
        | Quartz.kCGWindowListExcludeDesktopElements,
        Quartz.kCGNullWindowID,
    )
    if window_list is None:
        return None

    for win in window_list:
        name = win.get(Quartz.kCGWindowOwnerName, "")
        # Skip windows with no bounds or zero size
        bounds = win.get(Quartz.kCGWindowBounds)
        if not bounds:
            continue
        if bounds.get("Width", 0) < 50 or bounds.get("Height", 0) < 50:
            continue
        if owner_name.lower() in name.lower():
            return win

    return None


def get_bounds(window_info: dict) -> tuple[float, float, float, float]:
    """
    Extract (x, y, width, height) from window info.
    Coordinates are in Quartz screen points (origin at top-left of main display).
    """
    b = window_info[Quartz.kCGWindowBounds]
    return (b["X"], b["Y"], b["Width"], b["Height"])


def get_window_id(window_info: dict) -> int:
    """Return the CGWindowID for the window."""
    return window_info[Quartz.kCGWindowNumber]


def get_pid(window_info: dict) -> int:
    """Return the PID of the window's owning process."""
    return window_info[Quartz.kCGWindowOwnerPID]


def get_scale_factor() -> float:
    """
    Return the Retina scale factor for the main display.
    Typically 2.0 on Retina, 1.0 on non-Retina.
    """
    main_screen = NSScreen.mainScreen()
    return main_screen.backingScaleFactor()


def screenshot(window_info: dict) -> np.ndarray | None:
    """
    Capture the iPhone Mirroring window content as a BGR numpy array.
    Works even when the window is partially behind other windows.
    Returns None if the capture fails.
    """
    x, y, w, h = get_bounds(window_info)
    rect = Quartz.CGRectMake(x, y, w, h)
    window_id = get_window_id(window_info)

    # Capture just this window (by its ID) in its bounds
    cg_image = Quartz.CGWindowListCreateImage(
        rect,
        Quartz.kCGWindowListOptionIncludingWindow,
        window_id,
        Quartz.kCGWindowImageBoundsIgnoreFraming,
    )
    if cg_image is None:
        return None

    # Convert CGImage to numpy array
    img_width = Quartz.CGImageGetWidth(cg_image)
    img_height = Quartz.CGImageGetHeight(cg_image)
    bytes_per_row = Quartz.CGImageGetBytesPerRow(cg_image)
    data_provider = Quartz.CGImageGetDataProvider(cg_image)
    raw_data = Quartz.CGDataProviderCopyData(data_provider)

    if raw_data is None:
        return None

    # Raw data is BGRA (on most macOS systems)
    np_array = np.frombuffer(raw_data, dtype=np.uint8)
    np_array = np_array.reshape((img_height, bytes_per_row // 4, 4))
    # Crop to actual width (bytes_per_row may include padding)
    np_array = np_array[:, :img_width, :]
    # Convert BGRA to BGR (drop alpha channel)
    bgr = np_array[:, :, :3].copy()

    return bgr
