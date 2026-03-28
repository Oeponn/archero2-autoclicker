"""
clicker_wda.py — WebDriverAgent-based touch injection for iPhone.

Sends touch events directly to the iPhone via WDA REST API over USB.
Zero cursor movement, zero focus stealing.

Requirements:
  - Tab 1: xcodebuild test -scheme WebDriverAgentRunner ... (keep running)
  - Tab 2: iproxy 8100 8100                                (keep running)
"""

import base64
import cv2
import numpy as np
import requests

WDA_URL = "http://localhost:8100"

_session_id: str | None = None
_iphone_w: int = 402
_iphone_h: int = 874


def _get_session() -> str:
    global _session_id
    if _session_id:
        try:
            r = requests.get(f"{WDA_URL}/session/{_session_id}", timeout=2)
            if r.status_code == 200:
                return _session_id
        except Exception:
            pass
    r = requests.post(f"{WDA_URL}/session", json={"capabilities": {}}, timeout=5)
    data = r.json()
    _session_id = data["sessionId"]
    return _session_id


def init() -> bool:
    """Connect to WDA and cache the phone screen dimensions. Returns True on success."""
    global _iphone_w, _iphone_h
    try:
        r = requests.get(f"{WDA_URL}/status", timeout=3)
        if not r.json().get("value", {}).get("ready"):
            return False
        session = _get_session()
        r = requests.get(f"{WDA_URL}/session/{session}/window/size", timeout=3)
        size = r.json()["value"]
        _iphone_w = size["width"]
        _iphone_h = size["height"]
        print(f"  WDA connected — phone screen: {_iphone_w}×{_iphone_h} pts")
        return True
    except Exception as e:
        print(f"  WDA init failed: {e}")
        return False


def screenshot() -> np.ndarray | None:
    """
    Capture the iPhone screen via WDA.
    Resizes to TEMPLATE_W × TEMPLATE_H so reference images match.
    Returns BGR numpy array or None.
    """
    import config
    try:
        session = _get_session()
        r = requests.get(f"{WDA_URL}/session/{session}/screenshot", timeout=5)
        png_data = base64.b64decode(r.json()["value"])
        arr = np.frombuffer(png_data, dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if img is not None:
            img = cv2.resize(img, (config.TEMPLATE_W, config.TEMPLATE_H),
                             interpolation=cv2.INTER_AREA)
        return img
    except Exception:
        return None


def _to_wda(px: float, py: float, win_pixel_w: float, win_pixel_h: float) -> tuple[int, int]:
    """Convert window-pixel coords to iPhone WDA logical point coordinates."""
    x = round(px * _iphone_w / win_pixel_w)
    y = round(py * _iphone_h / win_pixel_h)
    return x, y


def click_at(px: float, py: float, win_pixel_w: float, win_pixel_h: float,
             delay: float = 0.05) -> None:
    """Tap at window-pixel (px, py). No cursor movement."""
    session = _get_session()
    x, y = _to_wda(px, py, win_pixel_w, win_pixel_h)
    pause_ms = max(50, int(delay * 1000))
    payload = {
        "actions": [{
            "type": "pointer",
            "id": "finger1",
            "parameters": {"pointerType": "touch"},
            "actions": [
                {"type": "pointerMove", "duration": 0, "x": x, "y": y},
                {"type": "pointerDown", "button": 0},
                {"type": "pause", "duration": pause_ms},
                {"type": "pointerUp", "button": 0},
            ],
        }]
    }
    requests.post(f"{WDA_URL}/session/{session}/actions", json=payload, timeout=5)


def drag(
    start_px: float, start_py: float,
    end_px: float, end_py: float,
    win_pixel_w: float, win_pixel_h: float,
    duration: float = 0.4,
) -> None:
    """Swipe from (start_px, start_py) to (end_px, end_py) in window-pixel coords."""
    session = _get_session()
    sx, sy = _to_wda(start_px, start_py, win_pixel_w, win_pixel_h)
    ex, ey = _to_wda(end_px, end_py, win_pixel_w, win_pixel_h)
    duration_ms = max(200, int(duration * 1000))
    payload = {
        "actions": [{
            "type": "pointer",
            "id": "finger1",
            "parameters": {"pointerType": "touch"},
            "actions": [
                {"type": "pointerMove", "duration": 0, "x": sx, "y": sy},
                {"type": "pointerDown", "button": 0},
                {"type": "pointerMove", "duration": duration_ms, "x": ex, "y": ey},
                {"type": "pointerUp", "button": 0},
            ],
        }]
    }
    requests.post(f"{WDA_URL}/session/{session}/actions", json=payload, timeout=10)
