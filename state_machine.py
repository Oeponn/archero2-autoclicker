"""
state_machine.py — Game flow state machine for Archero 2 autoclicker.

States:
  IDLE → STARTING → TALENT_GLORY → ROULETTE → BATTLING
  BATTLING can transition to: LEVEL_UP, VALKYRIE, ANGEL, DEVIL, ENDING
  Each of those transitions back to BATTLING (or IDLE for ENDING).
"""

import time
from enum import Enum, auto

import config
import window as win_mod
import clicker_quartz as clicker
import vision


class State(Enum):
    IDLE = auto()
    STARTING = auto()
    TALENT_GLORY = auto()
    ROULETTE = auto()
    BATTLING = auto()
    LEVEL_UP = auto()
    VALKYRIE = auto()
    ANGEL = auto()
    DEVIL = auto()
    ENDING = auto()


class GameStateMachine:
    def __init__(self, templates: dict, scale: float, window_pid: int):
        self.templates = templates
        self.scale = scale
        self.pid = window_pid
        self.state = State.IDLE
        self.run_count = 0
        self._state_enter_time = time.time()
        self._last_heartbeat = 0.0

    def _log(self, msg: str) -> None:
        print(f"  [{self.state.name}] {msg}", flush=True)

    def _set_state(self, new_state: State) -> None:
        print(f"  → {new_state.name}", flush=True)
        self.state = new_state
        self._state_enter_time = time.time()
        self._last_heartbeat = time.time()

    def _state_elapsed(self) -> float:
        return time.time() - self._state_enter_time

    def _heartbeat(self, interval: float = 5.0) -> None:
        if time.time() - self._last_heartbeat >= interval:
            self._log("scanning...")
            self._last_heartbeat = time.time()

    # ── Window helpers ────────────────────────────────────────────────────────

    def _get_window_and_screenshot(self):
        window_info = win_mod.find_window(config.IPHONE_MIRRORING_WINDOW_NAME)
        if window_info is None:
            return None
        bounds = win_mod.get_bounds(window_info)
        img = win_mod.screenshot(window_info)
        if img is None:
            return None
        return window_info, bounds, img

    # ── Click helpers ─────────────────────────────────────────────────────────

    def _click_at_pixel(self, px: float, py: float, bounds: tuple) -> None:
        """Convert window-pixel coords to screen coords and click via CGEventPostToPid."""
        sx, sy = clicker.window_to_screen(px, py, bounds, self.scale)
        self._log(f"  click → window px ({px:.0f}, {py:.0f})  screen pt ({sx:.0f}, {sy:.0f})")
        clicker.click_at(sx, sy, pid=self.pid, delay=config.CLICK_DELAY)

    def _click_skill_3_middle(self, banner_cx, banner_cy, banner_tw, banner_th, bounds):
        px = banner_cx + config.THREE_SKILL_MIDDLE_X_MULT * banner_tw
        py = banner_cy + config.THREE_SKILL_MIDDLE_Y_MULT * banner_th
        self._log(f"Clicking MIDDLE skill (banner {banner_cx:.0f},{banner_cy:.0f} size {banner_tw}×{banner_th})")
        self._click_at_pixel(px, py, bounds)

    def _click_skill_2_left(self, banner_cx, banner_cy, banner_tw, banner_th, bounds):
        px = banner_cx + config.TWO_SKILL_LEFT_X_MULT * banner_tw
        py = banner_cy + config.TWO_SKILL_LEFT_Y_MULT * banner_th
        self._log(f"Clicking LEFT skill (banner {banner_cx:.0f},{banner_cy:.0f} size {banner_tw}×{banner_th})")
        self._click_at_pixel(px, py, bounds)

    def _swipe_up(self, bounds: tuple) -> None:
        bx, by, bw, bh = bounds
        start_sx = bx + bw / 2
        start_sy = by + bh * 0.75
        end_sy   = by + bh * (0.75 - config.SWIPE_UP_FRACTION)
        self._log(f"Swipe UP  ({start_sx:.0f}, {start_sy:.0f}) → ({start_sx:.0f}, {end_sy:.0f})")
        clicker.drag(start_sx, start_sy, start_sx, end_sy,
                     pid=self.pid, duration=config.DRAG_DURATION)

    def _tap_screen(self, sx: float, sy: float, label: str = "") -> None:
        self._log(f"Tap {label} ({sx:.0f}, {sy:.0f})")
        clicker.click_at(sx, sy, pid=self.pid, delay=config.CLICK_DELAY)

    def _tap_window_center(self, bounds: tuple) -> None:
        bx, by, bw, bh = bounds
        self._tap_screen(bx + bw / 2, by + bh / 2, "center")

    def _tap_window_lower(self, bounds: tuple) -> None:
        bx, by, bw, bh = bounds
        self._tap_screen(bx + bw / 2, by + bh * 0.85, "lower-center")

    # ── Main tick ─────────────────────────────────────────────────────────────

    def tick(self) -> bool:
        result = self._get_window_and_screenshot()
        if result is None:
            self._log("iPhone Mirroring window not found, waiting...")
            time.sleep(2)
            return True

        _, bounds, img = result

        if self.state == State.IDLE:
            return self._handle_idle(img, bounds)
        elif self.state == State.STARTING:
            return self._handle_starting(img, bounds)
        elif self.state == State.TALENT_GLORY:
            return self._handle_talent_glory(img, bounds)
        elif self.state == State.ROULETTE:
            return self._handle_roulette(img, bounds)
        elif self.state == State.BATTLING:
            return self._handle_battling(img, bounds)
        elif self.state == State.LEVEL_UP:
            return self._handle_level_up(img, bounds)
        elif self.state == State.VALKYRIE:
            return self._handle_valkyrie(img, bounds)
        elif self.state == State.ANGEL:
            return self._handle_angel(img, bounds)
        elif self.state == State.DEVIL:
            return self._handle_devil(img, bounds)
        elif self.state == State.ENDING:
            return self._handle_ending(img, bounds)
        return True

    # ── State handlers ────────────────────────────────────────────────────────

    def _handle_idle(self, img, bounds) -> bool:
        match = vision.find_template(img, self.templates.get("start"))
        if match:
            cx, cy, tw, th = match
            self._log(f"Found start button at window px ({cx}, {cy})  size {tw}×{th}")
            self._click_at_pixel(cx, cy, bounds)
            time.sleep(config.POST_ACTION_DELAY)
            self.run_count += 1
            print(f"\n{'='*50}")
            print(f"  Run #{self.run_count} / {config.MAX_RUNS}")
            print(f"{'='*50}")
            self._set_state(State.STARTING)
            return True

        if self._state_elapsed() > config.IDLE_TIMEOUT:
            self._log(f"No start button found for {config.IDLE_TIMEOUT}s — stopping.")
            return False

        self._heartbeat()
        return True

    def _handle_starting(self, img, bounds) -> bool:
        match = vision.find_template(img, self.templates.get("talent_glory"))
        if match:
            self._log("Talent Glory screen detected")
            self._set_state(State.TALENT_GLORY)
            return True

        if self._state_elapsed() > config.STATE_TIMEOUT:
            if vision.find_template(img, self.templates.get("roulette_banner")):
                self._log("Skipped to Roulette")
                self._set_state(State.ROULETTE)
                return True
            self._log("No talent glory / roulette — click may not have registered, retrying")
            self.run_count -= 1
            self._set_state(State.IDLE)

        self._heartbeat()
        return True

    def _handle_talent_glory(self, img, bounds) -> bool:
        match = vision.find_template(img, self.templates.get("talent_glory"))
        if match:
            cx, cy, tw, th = match
            self._click_skill_3_middle(cx, cy, tw, th, bounds)
            time.sleep(config.POST_ACTION_DELAY)
            self._swipe_up(bounds)
            time.sleep(config.POST_ACTION_DELAY)
            self._set_state(State.ROULETTE)
        elif self._state_elapsed() > config.STATE_TIMEOUT:
            self._log("Talent Glory banner gone, moving to Roulette")
            self._set_state(State.ROULETTE)
        else:
            self._heartbeat()
        return True

    def _handle_roulette(self, img, bounds) -> bool:
        match = vision.find_template(img, self.templates.get("roulette_start"))
        if match:
            cx, cy, tw, th = match
            self._log(f"Found Roulette Start at window px ({cx}, {cy})")
            self._click_at_pixel(cx, cy, bounds)
            time.sleep(config.ROULETTE_SPIN_WAIT)
            self._tap_window_center(bounds)
            time.sleep(1.0)
            self._tap_window_center(bounds)
            time.sleep(config.POST_ACTION_DELAY)
            self._set_state(State.BATTLING)
            return True

        if vision.find_template(img, self.templates.get("roulette_banner")):
            self._log("Roulette banner visible, no Start button — tapping center")
            self._tap_window_center(bounds)
            time.sleep(config.ROULETTE_SPIN_WAIT)
            self._tap_window_center(bounds)
            time.sleep(1.0)
            self._tap_window_center(bounds)
            time.sleep(config.POST_ACTION_DELAY)
            self._set_state(State.BATTLING)
            return True

        if self._state_elapsed() > config.STATE_TIMEOUT:
            self._log("Roulette not found, assuming battle started")
            self._set_state(State.BATTLING)
        else:
            self._heartbeat()
        return True

    def _handle_battling(self, img, bounds) -> bool:
        ending = vision.find_any(img, self.templates, ["tap_empty", "reward"])
        if ending:
            self._log(f"Ending screen: '{ending[0]}'")
            self._set_state(State.ENDING)
            return True
        if vision.find_template(img, self.templates.get("level_up")):
            self._log("Level Up!")
            self._set_state(State.LEVEL_UP)
            return True
        if vision.find_template(img, self.templates.get("valkyrie")):
            self._log("Valkyrie encountered")
            self._set_state(State.VALKYRIE)
            return True
        if vision.find_template(img, self.templates.get("angel")):
            self._log("Angel encountered")
            self._set_state(State.ANGEL)
            return True
        if vision.find_template(img, self.templates.get("devil")):
            self._log("Devil encountered")
            self._set_state(State.DEVIL)
            return True
        self._heartbeat()
        return True

    def _handle_level_up(self, img, bounds) -> bool:
        match = vision.find_template(img, self.templates.get("level_up"))
        if match:
            cx, cy, tw, th = match
            self._click_skill_3_middle(cx, cy, tw, th, bounds)
            time.sleep(config.POST_ACTION_DELAY)
        self._set_state(State.BATTLING)
        return True

    def _handle_valkyrie(self, img, bounds) -> bool:
        match = vision.find_template(img, self.templates.get("valkyrie"))
        if match:
            cx, cy, tw, th = match
            self._click_skill_2_left(cx, cy, tw, th, bounds)
            time.sleep(config.POST_ACTION_DELAY)
        self._set_state(State.BATTLING)
        return True

    def _handle_angel(self, img, bounds) -> bool:
        match = vision.find_template(img, self.templates.get("angel"))
        if match:
            cx, cy, tw, th = match
            self._click_skill_2_left(cx, cy, tw, th, bounds)
            time.sleep(config.POST_ACTION_DELAY)
        self._set_state(State.BATTLING)
        return True

    def _handle_devil(self, img, bounds) -> bool:
        match = vision.find_template(img, self.templates.get("reject"))
        if match:
            cx, cy, tw, th = match
            self._log(f"Found Reject at window px ({cx}, {cy})")
            self._click_at_pixel(cx, cy, bounds)
            time.sleep(config.POST_ACTION_DELAY)
            self._set_state(State.BATTLING)
        elif self._state_elapsed() > config.STATE_TIMEOUT:
            self._log("Reject not found after timeout, returning to BATTLING")
            self._set_state(State.BATTLING)
        else:
            self._heartbeat()
        return True

    def _handle_ending(self, img, bounds) -> bool:
        self._log("Tapping to dismiss ending screens (3×)")
        for i in range(1, 4):
            self._tap_window_lower(bounds)
            self._log(f"Tap {i}/3")
            time.sleep(config.ENDING_TAP_DELAY)

        print(f"  Run #{self.run_count} complete.")
        if self.run_count >= config.MAX_RUNS:
            print(f"\n  Reached max runs ({config.MAX_RUNS}). Stopping.")
            return False

        self._set_state(State.IDLE)
        return True
