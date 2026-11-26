"""
Two handlebar push-buttons (screen has no touch). Each button: one leg to
the GPIO pin, other leg to GND (Pi's built-in pull-up is used).

  NEXT   (pin 37 / BCM26): next page
  SELECT (pin 36 / BCM16): press = scroll / move highlight, hold = press it
"""
from collections import deque
import config as cfg


class Buttons:
    def __init__(self):
        self.events = deque()
        self._held = False
        self.ok = False
        if not cfg.BUTTONS_ENABLED:
            return
        try:
            from gpiozero import Button
            self._next = Button(cfg.BTN_NEXT_GPIO, pull_up=True, bounce_time=0.05)
            self._sel = Button(cfg.BTN_SELECT_GPIO, pull_up=True, bounce_time=0.05,
                               hold_time=cfg.BTN_HOLD_SECS)
            self._next.when_pressed = lambda: self.events.append("next")
            self._sel.when_held = self._on_hold
            self._sel.when_released = self._on_release
            self.ok = True
            print("[buttons] ready")
        except Exception as e:
            print(f"[buttons] not available ({e})")

    def _on_hold(self):
        self._held = True
        self.events.append("hold")

    def _on_release(self):
        if not self._held:
            self.events.append("select")
        self._held = False

    def poll(self):
        while self.events:
            yield self.events.popleft()
