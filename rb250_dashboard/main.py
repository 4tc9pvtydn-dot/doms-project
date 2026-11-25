#!/usr/bin/env python3
"""
RB250 - Lambretta digital dashboard (Pygame, Pi Zero 2 W, HDMI screen)

Pi (service):   python main.py --fullscreen
Laptop window:  python main.py --size 480x320
Headless test:  python main.py --selftest
Screenshots:    python main.py --preview
"""
import os
import sys
import time
import glob
import argparse
import subprocess

if "--selftest" in sys.argv or "--preview" in sys.argv:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402
import config as cfg  # noqa: E402
import ui  # noqa: E402
from theme import Scaler  # noqa: E402
from telemetry import Telemetry  # noqa: E402

BOOT_SECONDS = 2.6
GOODBYE_SECONDS = 3.0
SWIPE_PX = 0.08  # fraction of screen width


class App:
    def __init__(self, sensors):
        self.sensors = sensors
        self.telemetry = Telemetry(sensors)
        self.page = 0  # 0 = ride, 1 = rides log, 2 = settings
        self.pages = 3
        self.brightness = 100
        self.confirm = False
        self.powering_down = False
        self.halted = False
        self._pd_since = None
        self._low_since = None
        self._auto_pd = False
        self.shutdown_reason = None
        self.countdown = None
        self.buttons = []
        self.boot_start = time.time()

    # ---- brightness: real backlight if the screen has one, else dim overlay
    def set_brightness(self, delta):
        self.brightness = max(20, min(100, self.brightness + delta))
        for base in glob.glob("/sys/class/backlight/*"):
            try:
                with open(os.path.join(base, "max_brightness")) as fh:
                    mx = int(fh.read())
                with open(os.path.join(base, "brightness"), "w") as fh:
                    fh.write(str(max(1, mx * self.brightness // 100)))
            except Exception:
                pass

    # ---- shutdown
    def request_shutdown(self):
        self.confirm = True

    def begin_poweroff(self, auto=False):
        self._auto_pd = auto
        self.confirm = False
        self.countdown = None
        self.powering_down = True
        self._pd_since = None
        self.telemetry.save()

    def do_poweroff(self):
        self.powering_down = False
        self.halted = True
        if not cfg.ALLOW_SHUTDOWN:
            return False
        for cmd in (["sudo", "-n", "systemctl", "poweroff"], ["sudo", "-n", "poweroff"]):
            try:
                if subprocess.run(cmd, capture_output=True, timeout=8).returncode == 0:
                    return True
            except Exception:
                continue
        return False

    def check_power(self, now):
        """Ignition off = switched-12V sensor drops below POWER_LOSS_VOLTS."""
        v = self.telemetry.volt
        if not cfg.POWER_LOSS_SHUTDOWN or self.halted:
            return
        lost = v is not None and v < cfg.POWER_LOSS_VOLTS
        if self.powering_down:
            # ignition back on before the Pi actually powers off -> carry on riding
            if self._auto_pd and v is not None and not lost:
                self.powering_down = False
                self._low_since = None
            return
        ups = self.telemetry.ups
        if ups is not None and ups[1] < cfg.UPS_LOW_PCT and (v is None or lost):
            self.shutdown_reason = "UPS BATTERY LOW"
            self.begin_poweroff(auto=True)
            return
        if lost:
            if self._low_since is None:
                self._low_since = now
            left = cfg.POWER_OFF_DELAY - (now - self._low_since)
            self.countdown = max(0.0, left)
            if left <= 0:
                self.shutdown_reason = "IGNITION OFF"
                self.begin_poweroff(auto=True)
        else:
            self._low_since = None
            self.countdown = None

    # ---- input
    def tap(self, pos):
        if self.confirm:
            if self._yes.collidepoint(pos):
                self.begin_poweroff()
            elif self._no.collidepoint(pos):
                self.confirm = False
            return
        if self.page == 2:
            for rect, cb in self.buttons:
                if rect.collidepoint(pos):
                    cb()
                    return

    def swipe(self, direction):
        if not self.confirm:
            self.page = max(0, min(self.pages - 1, self.page + direction))

    # ---- frame
    def draw(self, surf, sc, now):
        if now - self.boot_start < BOOT_SECONDS:
            ui.boot_screen(surf, sc, (now - self.boot_start) / BOOT_SECONDS)
            return
        if self.halted:
            ui.halted_screen(surf, sc)
            return
        if self.powering_down:
            ui.goodbye_screen(surf, sc)
            if self._pd_since is None:
                self._pd_since = now
            elif now - self._pd_since >= GOODBYE_SECONDS:
                self.do_poweroff()
            return
        clock = time.strftime("%H:%M")
        if self.page == 0:
            ui.ride_screen(surf, sc, self.telemetry, clock)
            self.buttons = []
        elif self.page == 1:
            ui.rides_screen(surf, sc, self.telemetry)
            self.buttons = []
        else:
            self.buttons = ui.settings_screen(surf, sc, self)
        ui.page_dots(surf, sc, self.pages, self.page)
        if self.countdown is not None:
            ui.countdown_overlay(surf, sc, self.countdown)
        if self.confirm:
            self._yes, self._no = ui.confirm_overlay(surf, sc)
        if self.brightness < 100:
            dim = pygame.Surface((sc.w, sc.h))
            dim.set_alpha(int((100 - self.brightness) / 100 * 190))
            surf.blit(dim, (0, 0))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fullscreen", action="store_true")
    ap.add_argument("--size", default="480x320")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--preview", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        import selftest
        return selftest.run()
    if args.preview:
        import selftest
        return selftest.preview()

    pygame.init()
    pygame.display.set_caption("RB250")
    if args.fullscreen:
        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        pygame.mouse.set_visible(False)
    else:
        w, h = (int(v) for v in args.size.lower().split("x"))
        screen = pygame.display.set_mode((w, h))
    sc = Scaler(*screen.get_size())
    print(f"[main] screen {sc.w}x{sc.h}")

    from sensors import Sensors
    app = App(Sensors())
    clock = pygame.time.Clock()
    press = None

    running = True
    while running:
        dt = min(clock.tick(cfg.FPS) / 1000.0, 0.1)
        now = time.time()
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            elif e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_ESCAPE, pygame.K_q):
                    running = False
                elif e.key == pygame.K_RIGHT:
                    app.swipe(1)
                elif e.key == pygame.K_LEFT:
                    app.swipe(-1)
            elif e.type in (pygame.MOUSEBUTTONDOWN, pygame.FINGERDOWN):
                press = _pos(e, sc)
            elif e.type in (pygame.MOUSEBUTTONUP, pygame.FINGERUP) and press:
                pos = _pos(e, sc)
                dx = pos[0] - press[0]
                if abs(dx) > sc.w * SWIPE_PX:
                    app.swipe(1 if dx < 0 else -1)
                else:
                    app.tap(pos)
                press = None

        if not app.halted:
            app.telemetry.update(dt)
            app.check_power(time.monotonic())
        app.draw(screen, sc, now)
        pygame.display.flip()

    app.telemetry.save()
    pygame.quit()


def _pos(e, sc):
    if e.type in (pygame.FINGERDOWN, pygame.FINGERUP):
        return (int(e.x * sc.w), int(e.y * sc.h))
    return e.pos


if __name__ == "__main__":
    sys.exit(main() or 0)
