"""
vision.py — OpenCV template matching on window screenshots.
"""

import os
import cv2
import numpy as np

import config


def _scale_native(img: np.ndarray) -> np.ndarray:
    """
    Scale a native iOS screenshot crop down to TEMPLATE resolution.

    Native iPhone 16 Pro screenshots (and WDA screenshots) are 1206×2622 px.
    Templates are matched against screenshots resized to TEMPLATE_W×TEMPLATE_H,
    so any crop taken at native resolution must be scaled by the same ratio.
    """
    sx = config.TEMPLATE_W / config.NATIVE_W
    sy = config.TEMPLATE_H / config.NATIVE_H
    new_w = max(1, round(img.shape[1] * sx))
    new_h = max(1, round(img.shape[0] * sy))
    return cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)


def load_templates() -> dict[str, np.ndarray]:
    """
    Load all reference images from config.IMAGE_PATHS.

    Images in images_native/ are full-resolution iOS screenshots and are
    automatically scaled down to TEMPLATE resolution at load time — no
    manual resizing needed. Images in images/ are left as-is.

    Returns a dict mapping logical name → BGR numpy array.
    Skips missing files with a warning.
    """
    native_dir = os.path.normpath(config.NATIVE_IMAGES_DIR)
    templates = {}
    for name, path in config.IMAGE_PATHS.items():
        if not os.path.exists(path):
            print(f"  [WARN] Missing image: {path}")
            continue
        img = cv2.imread(path, cv2.IMREAD_COLOR)
        if img is None:
            print(f"  [WARN] Failed to load: {path}")
            continue
        # Auto-scale native screenshots to match template resolution
        if os.path.normpath(path).startswith(native_dir):
            img = _scale_native(img)
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

    # Match in grayscale — removes colour differences between Mac-captured
    # templates and WDA screenshots while preserving shape/texture detail.
    ss_gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
    tm_gray = cv2.cvtColor(template,   cv2.COLOR_BGR2GRAY)
    result = cv2.matchTemplate(ss_gray, tm_gray, cv2.TM_CCOEFF_NORMED)
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
