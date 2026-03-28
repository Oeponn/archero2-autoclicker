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
    def __init__(
        self,
        templates: dict,
        scale: float,
    ):
        self.templates = templates
        self.scale = scale
        self.state = State.IDLE
        self.run_count = 0
        self._state_enter_time = time.time()
        self._last_state_log = None

    def _log(self, msg: str) -> None:
        print(f"  [{self.state.name}] {msg}")

    def _log_transition(self, new_state: State) -> None:
        if self._last_state_log != new_state:
            print(f"  → {new_state.name}")
            self._last_state_log = new_state

    def _set_state(self, new_state: State) -> None:
        self._log_transition(new_state)
        self.state = new_state
        self._state_enter_time = time.time()

    def _state_elapsed(self) -> float:
        return time.time() - self._state_enter_time

    def _get_window_and_screenshot(self) -> tuple[dict, tuple, any] | None:
        """Find window, get bounds, take screenshot. Returns None on failure."""
        window_info = win_mod.find_window(config.IPHONE_MIRRORING_WINDOW_NAME)
        if window_info is None:
            return None
        bounds = win_mod.get_bounds(window_info)
        img = win_mod.screenshot(window_info)
        if img is None:
            return None
        return window_info, bounds, img

    def _click_at_pixel(self, px: float, py: float, bounds: tuple) -> None:
        """Convert window-pixel coords to screen coords and click."""
        sx, sy = clicker.window_to_screen(px, py, bounds, self.scale)
        clicker.click_at(sx, sy, delay=config.CLICK_DELAY)

    def _click_skill_3_middle(self, banner_cx, banner_cy, banner_tw, banner_th, bounds):
        """Click the middle skill in a 3-skill layout, offset from banner."""
        px = banner_cx + config.THREE_SKILL_MIDDLE_X_MULT * banner_tw
        py = banner_cy + config.THREE_SKILL_MIDDLE_Y_MULT * banner_th
        self._log(f"Clicking middle skill at pixel ({px:.0f}, {py:.0f})")
        self._click_at_pixel(px, py, bounds)

    def _click_skill_2_left(self, banner_cx, banner_cy, banner_tw, banner_th, bounds):
        """Click the left skill in a 2-skill layout, offset from banner."""
        px = banner_cx + config.TWO_SKILL_LEFT_X_MULT * banner_tw
        py = banner_cy + config.TWO_SKILL_LEFT_Y_MULT * banner_th
        self._log(f"Clicking left skill at pixel ({px:.0f}, {py:.0f})")
        self._click_at_pixel(px, py, bounds)

    def _swipe_up(self, bounds: tuple) -> None:
        """Swipe up from center-bottom of the window."""
        _, _, bw, bh = bounds
        # Start from center-bottom (in screen points)
        start_sx = bounds[0] + bw / 2
        start_sy = bounds[1] + bh * 0.75
        end_sx = start_sx
        end_sy = start_sy - bh * config.SWIPE_UP_FRACTION
        self._log("Swiping up")
        clicker.drag(start_sx, start_sy, end_sx, end_sy, duration=config.DRAG_DURATION)

    def _tap_window_center(self, bounds: tuple) -> None:
        """Tap the center of the window."""
        bx, by, bw, bh = bounds
        sx = bx + bw / 2
        sy = by + bh / 2
        clicker.click_at(sx, sy, delay=config.CLICK_DELAY)

    def _tap_window_lower(self, bounds: tuple) -> None:
        """Tap the lower-center area of the window (for dismissing)."""
        bx, by, bw, bh = bounds
        sx = bx + bw / 2
        sy = by + bh * 0.85
        clicker.click_at(sx, sy, delay=config.CLICK_DELAY)

    # ── State handlers ───────────────────────────────────────────────────────

    def tick(self) -> bool:
        """
        Run one detection + action cycle.
        Returns False when the bot should stop (max runs, no energy, etc.).
        """
        result = self._get_window_and_screenshot()
        if result is None:
            self._log("iPhone Mirroring window not found, waiting...")
            time.sleep(2)
            return True

        window_info, bounds, img = result

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

    def _handle_idle(self, img, bounds) -> bool:
        """Look for start button. Click it to begin a run."""
        match = vision.find_template(img, self.templates.get("start"))
        if match:
            cx, cy, tw, th = match
            self._log("Found start button — clicking")
            self._click_at_pixel(cx, cy, bounds)
            time.sleep(config.POST_ACTION_DELAY)
            self.run_count += 1
            print(f"\n{'='*50}")
            print(f"  Run #{self.run_count} / {config.MAX_RUNS}")
            print(f"{'='*50}")
            self._set_state(State.STARTING)
            return True

        # Timeout: no start button found
        if self._state_elapsed() > config.IDLE_TIMEOUT:
            self._log(f"No start button found for {config.IDLE_TIMEOUT}s — stopping.")
            return False

        return True

    def _handle_starting(self, img, bounds) -> bool:
        """Wait for talent glory screen after clicking start."""
        match = vision.find_template(img, self.templates.get("talent_glory"))
        if match:
            self._log("Talent Glory screen detected")
            self._set_state(State.TALENT_GLORY)
            return True

        # Maybe went straight to roulette or battle
        if self._state_elapsed() > config.STATE_TIMEOUT:
            self._log("Talent Glory not found, checking for roulette or battle...")
            # Check roulette
            rmatch = vision.find_template(img, self.templates.get("roulette_banner"))
            if rmatch:
                self._set_state(State.ROULETTE)
                return True
            # Fall through to battling
            self._set_state(State.BATTLING)

        return True

    def _handle_talent_glory(self, img, bounds) -> bool:
        """Pick the middle skill, then swipe up to advance."""
        match = vision.find_template(img, self.templates.get("talent_glory"))
        if match:
            cx, cy, tw, th = match
            self._click_skill_3_middle(cx, cy, tw, th, bounds)
            time.sleep(config.POST_ACTION_DELAY)

            # Swipe up to trigger roulette
            self._swipe_up(bounds)
            time.sleep(config.POST_ACTION_DELAY)

            self._set_state(State.ROULETTE)
        elif self._state_elapsed() > config.STATE_TIMEOUT:
            self._log("Talent Glory banner disappeared, moving on")
            self._set_state(State.ROULETTE)

        return True

    def _handle_roulette(self, img, bounds) -> bool:
        """Click start on roulette, wait for spin, tap to skip and dismiss."""
        # Look for the roulette start button
        match = vision.find_template(img, self.templates.get("roulette_start"))
        if match:
            cx, cy, tw, th = match
            self._log("Found roulette Start — clicking")
            self._click_at_pixel(cx, cy, bounds)

            # Wait for spin animation
            time.sleep(config.ROULETTE_SPIN_WAIT)

            # Tap to skip
            self._log("Tapping to skip roulette animation")
            self._tap_window_center(bounds)
            time.sleep(1.0)

            # Tap to dismiss result
            self._log("Tapping to dismiss roulette result")
            self._tap_window_center(bounds)
            time.sleep(config.POST_ACTION_DELAY)

            self._set_state(State.BATTLING)
            return True

        # Also check for roulette banner (maybe start button not cropped right)
        banner = vision.find_template(img, self.templates.get("roulette_banner"))
        if banner:
            # Roulette is showing but we can't find the start button specifically
            # Try tapping center of window
            self._log("Roulette banner visible, tapping center")
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

        return True

    def _handle_battling(self, img, bounds) -> bool:
        """
        During battle, poll for events in priority order:
        1. Ending screens (highest priority)
        2. Level up
        3. Valkyrie
        4. Angel
        5. Devil
        """
        # Check ending screens first
        ending_match = vision.find_any(
            img, self.templates, ["tap_empty", "reward"]
        )
        if ending_match:
            self._log(f"Detected ending: {ending_match[0]}")
            self._set_state(State.ENDING)
            return True

        # Check level up
        match = vision.find_template(img, self.templates.get("level_up"))
        if match:
            self._log("Level Up detected")
            self._set_state(State.LEVEL_UP)
            return True

        # Check valkyrie
        match = vision.find_template(img, self.templates.get("valkyrie"))
        if match:
            self._log("Valkyrie encountered")
            self._set_state(State.VALKYRIE)
            return True

        # Check angel
        match = vision.find_template(img, self.templates.get("angel"))
        if match:
            self._log("Angel encountered")
            self._set_state(State.ANGEL)
            return True

        # Check devil
        match = vision.find_template(img, self.templates.get("devil"))
        if match:
            self._log("Devil encountered")
            self._set_state(State.DEVIL)
            return True

        # Nothing detected — still battling
        return True

    def _handle_level_up(self, img, bounds) -> bool:
        """Pick the middle skill (3-skill layout)."""
        match = vision.find_template(img, self.templates.get("level_up"))
        if match:
            cx, cy, tw, th = match
            self._click_skill_3_middle(cx, cy, tw, th, bounds)
            time.sleep(config.POST_ACTION_DELAY)
        self._set_state(State.BATTLING)
        return True

    def _handle_valkyrie(self, img, bounds) -> bool:
        """Pick the left skill (2-skill layout)."""
        match = vision.find_template(img, self.templates.get("valkyrie"))
        if match:
            cx, cy, tw, th = match
            self._click_skill_2_left(cx, cy, tw, th, bounds)
            time.sleep(config.POST_ACTION_DELAY)
        self._set_state(State.BATTLING)
        return True

    def _handle_angel(self, img, bounds) -> bool:
        """Pick the left skill (2-skill layout)."""
        match = vision.find_template(img, self.templates.get("angel"))
        if match:
            cx, cy, tw, th = match
            self._click_skill_2_left(cx, cy, tw, th, bounds)
            time.sleep(config.POST_ACTION_DELAY)
        self._set_state(State.BATTLING)
        return True

    def _handle_devil(self, img, bounds) -> bool:
        """Click the reject button."""
        match = vision.find_template(img, self.templates.get("reject"))
        if match:
            cx, cy, tw, th = match
            self._log("Clicking Reject")
            self._click_at_pixel(cx, cy, bounds)
            time.sleep(config.POST_ACTION_DELAY)
        elif self._state_elapsed() > config.STATE_TIMEOUT:
            self._log("Reject button not found, returning to battle")
        else:
            return True  # Keep looking for reject button
        self._set_state(State.BATTLING)
        return True

    def _handle_ending(self, img, bounds) -> bool:
        """Tap to dismiss the ending screens and return to idle."""
        self._log("Tapping to dismiss ending screen")
        self._tap_window_lower(bounds)
        time.sleep(config.ENDING_TAP_DELAY)

        # Tap again to dismiss rewards/second screen
        self._tap_window_lower(bounds)
        time.sleep(config.ENDING_TAP_DELAY)

        # One more tap for good measure
        self._tap_window_lower(bounds)
        time.sleep(config.ENDING_TAP_DELAY)

        print(f"  Run #{self.run_count} complete.")

        if self.run_count >= config.MAX_RUNS:
            print(f"\n  Reached max runs ({config.MAX_RUNS}). Stopping.")
            return False

        self._set_state(State.IDLE)
        return True
