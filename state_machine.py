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
import clicker_wda as clicker
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
    def __init__(self, templates: dict):
        self.templates = templates
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

    # ── Screenshot ────────────────────────────────────────────────────────────

    def _get_screenshot(self):
        img = clicker.screenshot()
        if img is None:
            return None
        return img

    # ── Click helpers ─────────────────────────────────────────────────────────
    # WDA coordinates are in iPhone logical points (402×874).
    # Screenshots from WDA are at the same logical resolution so
    # px/py from image matching map 1:1 to WDA coordinates.

    def _click_at_pixel(self, px: float, py: float, img) -> None:
        h, w = img.shape[:2]
        self._log(f"  click → px ({px:.0f}, {py:.0f})")
        clicker.click_at(px, py, w, h, delay=config.CLICK_DELAY)

    def _click_skill_3_middle(self, banner_cx, banner_cy, banner_tw, banner_th, img):
        px = banner_cx + config.THREE_SKILL_MIDDLE_X_MULT * banner_tw
        py = banner_cy + config.THREE_SKILL_MIDDLE_Y_MULT * banner_th
        self._log(f"Clicking MIDDLE skill (banner {banner_cx:.0f},{banner_cy:.0f} size {banner_tw}×{banner_th})")
        self._click_at_pixel(px, py, img)

    def _click_skill_2_left(self, banner_cx, banner_cy, banner_tw, banner_th, img):
        px = banner_cx + config.TWO_SKILL_LEFT_X_MULT * banner_tw
        py = banner_cy + config.TWO_SKILL_LEFT_Y_MULT * banner_th
        self._log(f"Clicking LEFT skill (banner {banner_cx:.0f},{banner_cy:.0f} size {banner_tw}×{banner_th})")
        self._click_at_pixel(px, py, img)

    def _swipe_up(self, img) -> None:
        h, w = img.shape[:2]
        start_px = w / 2
        start_py = h * 0.75
        end_py   = h * (0.75 - config.SWIPE_UP_FRACTION)
        self._log(f"Swipe UP  ({start_px:.0f}, {start_py:.0f}) → ({start_px:.0f}, {end_py:.0f})")
        clicker.drag(start_px, start_py, start_px, end_py, w, h,
                     duration=config.DRAG_DURATION)

    def _tap_center(self, img) -> None:
        h, w = img.shape[:2]
        self._log(f"Tap center ({w//2}, {h//2})")
        clicker.click_at(w / 2, h / 2, w, h, delay=config.CLICK_DELAY)

    def _tap_lower(self, img) -> None:
        h, w = img.shape[:2]
        self._log(f"Tap lower-center ({w//2}, {h*0.85:.0f})")
        clicker.click_at(w / 2, h * 0.85, w, h, delay=config.CLICK_DELAY)

    # ── Main tick ─────────────────────────────────────────────────────────────

    def tick(self) -> bool:
        img = self._get_screenshot()
        if img is None:
            self._log("WDA screenshot failed, waiting...")
            time.sleep(2)
            return True

        if self.state == State.IDLE:
            return self._handle_idle(img)
        elif self.state == State.STARTING:
            return self._handle_starting(img)
        elif self.state == State.TALENT_GLORY:
            return self._handle_talent_glory(img)
        elif self.state == State.ROULETTE:
            return self._handle_roulette(img)
        elif self.state == State.BATTLING:
            return self._handle_battling(img)
        elif self.state == State.LEVEL_UP:
            return self._handle_level_up(img)
        elif self.state == State.VALKYRIE:
            return self._handle_valkyrie(img)
        elif self.state == State.ANGEL:
            return self._handle_angel(img)
        elif self.state == State.DEVIL:
            return self._handle_devil(img)
        elif self.state == State.ENDING:
            return self._handle_ending(img)
        return True

    # ── State handlers ────────────────────────────────────────────────────────

    def _handle_idle(self, img) -> bool:
        match, btn = None, None
        for name in ("start", "ready"):
            result = vision.find_template(img, self.templates.get(name))
            if result:
                match, btn = result, name
                break

        if match:
            cx, cy, tw, th = match
            self._log(f"Found '{btn}' button at ({cx}, {cy})  size {tw}×{th} — clicking")
            self._click_at_pixel(cx, cy, img)
            time.sleep(config.POST_ACTION_DELAY)

            # Ready flow: after clicking Ready the game shows a Start button next
            if btn == "ready":
                self._log("Waiting for Start button after Ready...")
                for _ in range(10):
                    time.sleep(1)
                    img2 = clicker.screenshot()
                    start_match = vision.find_template(img2, self.templates.get("start"))
                    if start_match:
                        sx, sy, stw, sth = start_match
                        self._log(f"Found 'start' after ready at ({sx}, {sy}) — clicking")
                        self._click_at_pixel(sx, sy, img2)
                        time.sleep(config.POST_ACTION_DELAY)
                        break
                else:
                    self._log("Start button not found after Ready — continuing anyway")

            self.run_count += 1
            print(f"\n{'='*50}")
            print(f"  Run #{self.run_count} / {config.MAX_RUNS}")
            print(f"{'='*50}")
            self._set_state(State.STARTING)
            return True

        # Mid-game resume: bot started while a run is already in progress
        if vision.find_template(img, self.templates.get("talent_glory")):
            self._log("Detected mid-game: Talent Glory — resuming")
            self.run_count += 1
            self._set_state(State.TALENT_GLORY)
            return True
        if vision.find_template(img, self.templates.get("roulette_banner")):
            self._log("Detected mid-game: Roulette — resuming")
            self.run_count += 1
            self._set_state(State.ROULETTE)
            return True
        if vision.find_template(img, self.templates.get("level_up")):
            self._log("Detected mid-game: Level Up — resuming")
            self.run_count += 1
            self._set_state(State.LEVEL_UP)
            return True
        if vision.find_template(img, self.templates.get("devil")):
            self._log("Detected mid-game: Devil — resuming")
            self.run_count += 1
            self._set_state(State.DEVIL)
            return True
        if vision.find_any(img, self.templates, ["tap_empty", "reward"]):
            self._log("Detected mid-game: Ending screen — resuming")
            self.run_count += 1
            self._set_state(State.ENDING)
            return True

        if self._state_elapsed() > config.IDLE_TIMEOUT:
            self._log(f"No start button found for {config.IDLE_TIMEOUT}s — stopping.")
            return False

        self._heartbeat()
        return True

    def _handle_starting(self, img) -> bool:
        if vision.find_template(img, self.templates.get("talent_glory")):
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

    def _handle_talent_glory(self, img) -> bool:
        match = vision.find_template(img, self.templates.get("talent_glory"))
        if match:
            cx, cy, tw, th = match
            self._click_skill_3_middle(cx, cy, tw, th, img)
            time.sleep(config.POST_ACTION_DELAY)
            self._swipe_up(img)
            time.sleep(config.POST_ACTION_DELAY)
            self._set_state(State.ROULETTE)
        elif self._state_elapsed() > config.STATE_TIMEOUT:
            self._log("Talent Glory banner gone, moving to Roulette")
            self._set_state(State.ROULETTE)
        else:
            self._heartbeat()
        return True

    def _handle_roulette(self, img) -> bool:
        match = vision.find_template(img, self.templates.get("roulette_start"))
        if match:
            cx, cy, tw, th = match
            self._log(f"Found Roulette Start at ({cx}, {cy})")
            self._click_at_pixel(cx, cy, img)
            time.sleep(config.ROULETTE_SPIN_WAIT)
            self._tap_center(img)
            time.sleep(1.0)
            self._tap_center(img)
            time.sleep(config.POST_ACTION_DELAY)
            self._set_state(State.BATTLING)
            return True
        if vision.find_template(img, self.templates.get("roulette_banner")):
            self._log("Roulette banner visible, no Start button — tapping center")
            self._tap_center(img)
            time.sleep(config.ROULETTE_SPIN_WAIT)
            self._tap_center(img)
            time.sleep(1.0)
            self._tap_center(img)
            time.sleep(config.POST_ACTION_DELAY)
            self._set_state(State.BATTLING)
            return True
        if self._state_elapsed() > config.STATE_TIMEOUT:
            self._log("Roulette not found, assuming battle started")
            self._set_state(State.BATTLING)
        else:
            self._heartbeat()
        return True

    def _handle_battling(self, img) -> bool:
        if vision.find_any(img, self.templates, ["tap_empty", "reward"]):
            self._log("Ending screen detected")
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

    def _handle_level_up(self, img) -> bool:
        match = vision.find_template(img, self.templates.get("level_up"))
        if match:
            cx, cy, tw, th = match
            self._click_skill_3_middle(cx, cy, tw, th, img)
            time.sleep(config.POST_ACTION_DELAY)
        self._set_state(State.BATTLING)
        return True

    def _handle_valkyrie(self, img) -> bool:
        match = vision.find_template(img, self.templates.get("valkyrie"))
        if match:
            cx, cy, tw, th = match
            self._click_skill_2_left(cx, cy, tw, th, img)
            time.sleep(config.POST_ACTION_DELAY)
        self._set_state(State.BATTLING)
        return True

    def _handle_angel(self, img) -> bool:
        match = vision.find_template(img, self.templates.get("angel"))
        if match:
            cx, cy, tw, th = match
            self._click_skill_2_left(cx, cy, tw, th, img)
            time.sleep(config.POST_ACTION_DELAY)
        self._set_state(State.BATTLING)
        return True

    def _handle_devil(self, img) -> bool:
        match = vision.find_template(img, self.templates.get("reject"))
        if match:
            cx, cy, tw, th = match
            self._log(f"Found Reject at ({cx}, {cy})")
            self._click_at_pixel(cx, cy, img)
            time.sleep(config.POST_ACTION_DELAY)
            self._set_state(State.BATTLING)
        elif self._state_elapsed() > config.STATE_TIMEOUT:
            self._log("Reject not found after timeout, returning to BATTLING")
            self._set_state(State.BATTLING)
        else:
            self._heartbeat()
        return True

    def _handle_ending(self, img) -> bool:
        self._log("Tapping to dismiss ending screen")
        self._tap_lower(img)
        time.sleep(config.ENDING_TAP_DELAY)
        print(f"  Run #{self.run_count} complete.")
        if self.run_count >= config.MAX_RUNS:
            print(f"\n  Reached max runs ({config.MAX_RUNS}). Stopping.")
            return False
        self._set_state(State.IDLE)
        return True
