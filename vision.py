"""
vision.py — OpenCV template matching on window screenshots.
"""

import os
import cv2
import numpy as np

import config


def load_templates() -> dict[str, np.ndarray]:
    """
    Load all reference images from config.IMAGE_PATHS.
    Returns a dict mapping logical name → BGR numpy array.
    Skips missing files with a warning.
    """
    templates = {}
    for name, path in config.IMAGE_PATHS.items():
        if not os.path.exists(path):
            print(f"  [WARN] Missing image: {path}")
            continue
        img = cv2.imread(path, cv2.IMREAD_COLOR)
        if img is None:
            print(f"  [WARN] Failed to load: {path}")
            continue
        templates[name] = img
    return templates


def find_template(
    screenshot: np.ndarray,
    template: np.ndarray,
    threshold: float = config.CONFIDENCE,
) -> tuple[int, int, int, int] | None:
    """
    Find a template in a screenshot using normalized cross-correlation.

    Returns (cx, cy, tw, th) — the center coordinates and size of the match
    in pixel coordinates within the screenshot. Returns None if no match
    above threshold.
    """
    if screenshot is None or template is None:
        return None

    # Ensure both are the same color depth
    if len(screenshot.shape) != len(template.shape):
        return None

    th, tw = template.shape[:2]
    sh, sw = screenshot.shape[:2]

    # Template must be smaller than screenshot
    if th > sh or tw > sw:
        return None

    result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)

    if max_val >= threshold:
        # max_loc is (x, y) of top-left corner of match
        cx = max_loc[0] + tw // 2
        cy = max_loc[1] + th // 2
        return (cx, cy, tw, th)

    return None


def find_any(
    screenshot: np.ndarray,
    templates: dict[str, np.ndarray],
    names: list[str],
    threshold: float = config.CONFIDENCE,
) -> tuple[str, int, int, int, int] | None:
    """
    Try matching each named template against the screenshot in order.
    Returns (name, cx, cy, tw, th) for the first match above threshold,
    or None if nothing matched.
    """
    for name in names:
        tmpl = templates.get(name)
        if tmpl is None:
            continue
        result = find_template(screenshot, tmpl, threshold)
        if result is not None:
            cx, cy, tw, th = result
            return (name, cx, cy, tw, th)
    return None
