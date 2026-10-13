#!/usr/bin/env python3
"""
DOMS RB252 - Lambretta Digital Dashboard (Pygame)

Laptop test:      python main.py
Full-screen (Pi): python main.py --fullscreen
Headless test:    python main.py --selftest
"""
import os
import sys
import time
import argparse
import subprocess

if "--selftest" in sys.argv:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402

import config as cfg  # noqa: E402
from theme import (  # noqa: E402
    carbon_bg, get_font, WHITE, AMBER, DIM, set_hw_brightness,
    cht_status, afr_status, draw_text, load_cover_image,
)
from widgets import page_dots, warning_banner, button  # noqa: E402
from telemetry import Telemetry  # noqa: E402
from sensors import Sensors  # noqa: E402
from pages import RidePage, EnginePage, GpsPage, PerformancePage, SettingsPage  # noqa: E402

W, H = cfg.WIDTH, cfg.HEIGHT
BOOT_SECONDS = 2.6
FADE_SECONDS = 0.4
SWIPE_THRESHOLD = 45
TAP_MOVE_MAX = 16
DOTS_CY = 468
SHUTDOWN_GRAPHIC_SECONDS = 3.0


def build_fonts():
    return {
        "brand": get_font(20, digital=True),
        "clock": get_font(22, digital=True),
        "speed": get_font(150, digital=True),
        "gear": get_font(60, digital=True),
        "afr": get_font(30, digital=True),
        "num_lg": get_font(38, digital=True),
        "num_md": get_font(28, digital=True),
        "label_sm": get_font(13),
        "label": get_font(16),
        "title": get_font(16),
        "btn": get_font(15),
        "boot_big": get_font(46, digital=True),
        "boot_sub": get_font(30, digital=True),
        "modal": get_font(20),
    }


class App:
    def __init__(self, fullscreen=False):
        self.settings = {
            "brightness": 100, "units": "mph", "clock24": True,
            "cht_amber": 195, "cht_red": 215,
        }
        self.telemetry = Telemetry(
            Sensors() if cfg.USE_REAL_SENSORS else None, cfg.USE_REAL_SENSORS
        )
        self.sensors = self.telemetry.sensors
        self.data = self.telemetry.sample()
        self.fonts = build_fonts()
        self.page_index = 0
        self.pages = [
            RidePage(self), EnginePage(self), GpsPage(self),
            PerformancePage(self), SettingsPage(self),
        ]
        self.shutdown_overlay = False
        self.confirm_shutdown = False
        self.powering_down = False
        self._pd_since = None
        self._ign_off_since = None
        self.ign_countdown = None
        self.blink2 = False
        self.fullscreen = fullscreen

    def clock_str(self):
        t = time.localtime()
        h, m = t.tm_hour, t.tm_min
        if not self.settings["clock24"]:
            h = h % 12 or 12
            return f"{h}:{m:02d}"
        return f"{h:02d}:{m:02d}"

    def set_brightness(self, delta):
        b = max(20, min(100, self.settings["brightness"] + delta))
        self.settings["brightness"] = b
        set_hw_brightness(b)

    # ---- shutdown flow (with confirm) ----
    def request_shutdown(self):
        self.confirm_shutdown = True

    def cancel_shutdown(self):
        self.confirm_shutdown = False

    def begin_poweroff(self):
        """Show the goodbye graphic first; the main loop issues the actual
        poweroff after SHUTDOWN_GRAPHIC_SECONDS."""
        self.confirm_shutdown = False
        self.powering_down = True
        self._pd_since = None

    def do_shutdown(self):
        self.confirm_shutdown = False
        self.powering_down = False
        if cfg.ALLOW_SHUTDOWN:
            # -n = non-interactive: fail fast if no passwordless rule,
            # rather than hanging or half-acting (which looked like a reboot).
            for cmd in (["sudo", "-n", "systemctl", "poweroff"],
                        ["sudo", "-n", "poweroff"],
                        ["sudo", "-n", "shutdown", "-h", "now"]):
                try:
                    r = subprocess.run(cmd, capture_output=True, timeout=8)
                    if r.returncode == 0:
                        return
                except Exception:
                    continue
        # Couldn't power off (or not allowed) -> show halted screen, don't loop.
        self.shutdown_overlay = True

    def reboot_ui(self):
        self.shutdown_overlay = False
        self.telemetry.reset_all()
        self.page_index = 0

    def check_ignition(self, now, volts=None):
        """Trigger a graceful power-down when main power is lost, detected by
        either the ignition-sense pin OR the voltage sensor collapsing."""
        ign = cfg.IGNITION_SENSE_ENABLED
        vloss = getattr(cfg, "POWER_LOSS_SHUTDOWN", False)
        if not (ign or vloss):
            return
        power_lost = False
        if ign and self.sensors is not None and self.sensors.ignition_on() is False:
            power_lost = True
        if vloss and volts is not None and volts < cfg.POWER_LOSS_VOLTS:
            power_lost = True
        if power_lost:
            if self._ign_off_since is None:
                self._ign_off_since = now
            remaining = cfg.IGNITION_OFF_DELAY - (now - self._ign_off_since)
            self.ign_countdown = max(0.0, remaining)
            if remaining <= 0:
                self.begin_poweroff()
        else:
            self._ign_off_since = None
            self.ign_countdown = None

    def dot_index_at(self, cx, cy):
        if cy < DOTS_CY - 16:
            return None
        gap = 16
        startx = 320 - (len(self.pages) - 1) * gap / 2
        for i in range(len(self.pages)):
            if abs(cx - (startx + i * gap)) < 12:
                return i
        return None

    def warning_message(self):
        cn, cd = cht_status(self.data["cht"], self.settings["cht_amber"], self.settings["cht_red"])
        if cd:
            return "CYLINDER TEMP CRITICAL"
        an, ad = afr_status(self.data["afr"])
        if ad:
            return "AFR DANGER - CHECK MIXTURE"
        return None


def draw_boot(surf, fonts, elapsed):
    img = load_cover_image("boot_logo.jpg", W, H)
    if img is not None:
        surf.blit(img, (0, 0))
    else:
        surf.blit(carbon_bg(W, H), (0, 0))
        draw_text(surf, "DOMS", fonts["boot_big"], WHITE, center=(320, 190))
        draw_text(surf, "RB252", fonts["boot_sub"], AMBER, center=(320, 240))
    bar = pygame.Rect(190, 452, 260, 6)
    pygame.draw.rect(surf, (28, 29, 33), bar, border_radius=3)
    prog = max(0.0, min(1.0, elapsed / BOOT_SECONDS))
    if prog > 0:
        pygame.draw.rect(surf, AMBER, (bar.x, bar.y, int(bar.w * prog), bar.h), border_radius=3)


def draw_powering_down(surf, fonts):
    img = load_cover_image("shutdown_screen.jpg", W, H)
    if img is not None:
        surf.blit(img, (0, 0))
    else:
        surf.fill((0, 0, 0))
        draw_text(surf, "UNTIL NEXT TIME DUDE", fonts["modal"], AMBER, center=(320, 240))


def draw_shutdown(surf, fonts):
    surf.fill((0, 0, 0))
    pygame.draw.circle(surf, DIM, (320, 190), 24, 3)
    pygame.draw.line(surf, DIM, (320, 172), (320, 196), 3)
    draw_text(surf, "SYSTEM HALTED", fonts["label"], DIM, center=(320, 250))
    r = pygame.Rect(250, 285, 140, 40)
    button(surf, r, "RESTART", fonts["btn"])
    return r


def draw_confirm(surf, fonts):
    ov = pygame.Surface((W, H))
    ov.set_alpha(190)
    ov.fill((0, 0, 0))
    surf.blit(ov, (0, 0))
    box = pygame.Rect(140, 150, 360, 180)
    pygame.draw.rect(surf, (20, 21, 25), box, border_radius=14)
    pygame.draw.rect(surf, (90, 20, 20), box, 2, border_radius=14)
    draw_text(surf, "POWER OFF?", fonts["modal"], WHITE, center=(320, 195))
    draw_text(surf, "The Pi will shut down.", fonts["label_sm"], DIM, center=(320, 225))
    yes = pygame.Rect(165, 262, 150, 46)
    no = pygame.Rect(325, 262, 150, 46)
    button(surf, yes, "POWER OFF", fonts["btn"], color=(200, 30, 30))
    button(surf, no, "CANCEL", fonts["btn"])
    return yes, no


def draw_ign(surf, fonts, secs):
    col = (200, 30, 30) if int(time.time() * 2) % 2 == 0 else (120, 10, 10)
    pygame.draw.rect(surf, col, (0, 200, 640, 80))
    draw_text(surf, "BIKE OFF - POWERING DOWN", fonts["modal"], WHITE, center=(320, 228))
    draw_text(surf, f"{secs:.0f}s   (switch on to cancel)", fonts["label"], WHITE, center=(320, 258))


def to_canvas(pos, disp):
    dw, dh = disp.get_size()
    return (pos[0] * W / dw, pos[1] * H / dh)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fullscreen", action="store_true")
    ap.add_argument("--windowed", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    pygame.init()
    pygame.display.set_caption("DOMS RB252")

    fullscreen = args.fullscreen and not args.windowed
    if args.selftest:
        display = pygame.display.set_mode((W, H))
    elif fullscreen:
        display = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        pygame.mouse.set_visible(False)
    else:
        display = pygame.display.set_mode((W, H))

    canvas = pygame.Surface((W, H))
    app = App(fullscreen=fullscreen)
    clock = pygame.time.Clock()

    if args.selftest:
        return run_selftest(app, canvas)

    start = time.time()
    booted = False
    fade_start = None
    trans = {"active": False, "dir": 0, "t": 0.0, "from": 0}
    press = {"pos": None, "moved": 0.0}

    def goto(idx):
        idx = max(0, min(len(app.pages) - 1, idx))
        if idx != app.page_index and not trans["active"]:
            trans["active"] = True
            trans["dir"] = 1 if idx > app.page_index else -1
            trans["t"] = 0.0
            trans["from"] = app.page_index
            app.page_index = idx

    def pointer_down(cx, cy):
        press["pos"] = (cx, cy)
        press["moved"] = 0.0

    def pointer_move(cx, cy):
        if press["pos"] is not None:
            press["moved"] = max(press["moved"], abs(cx - press["pos"][0]))

    def pointer_up(cx, cy):
        if press["pos"] is None:
            return
        dx = cx - press["pos"][0]
        press["pos"] = None
        # modal / overlays first
        if app.confirm_shutdown:
            if app._confirm_yes.collidepoint((cx, cy)):
                app.begin_poweroff()
            elif app._confirm_no.collidepoint((cx, cy)):
                app.cancel_shutdown()
            return
        if app.shutdown_overlay:
            if getattr(app, "_restart_rect", None) and app._restart_rect.collidepoint((cx, cy)):
                app.reboot_ui()
            return
        if trans["active"]:
            return
        if abs(dx) > SWIPE_THRESHOLD:
            goto(app.page_index + (1 if dx < 0 else -1))
        elif press["moved"] < TAP_MOVE_MAX:
            dot = app.dot_index_at(cx, cy)
            if dot is not None:
                goto(dot)
            else:
                app.pages[app.page_index].handle_tap((cx, cy))

    running = True
    while running:
        dt = min(clock.tick(60) / 1000.0, 0.05)
        app.blink2 = int(time.time() * 2) % 2 == 0

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            elif e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_ESCAPE, pygame.K_q):
                    running = False
                elif e.key == pygame.K_RIGHT:
                    goto(app.page_index + 1)
                elif e.key == pygame.K_LEFT:
                    goto(app.page_index - 1)
                elif e.key == pygame.K_f:
                    pygame.display.toggle_fullscreen()
            elif e.type == pygame.MOUSEBUTTONDOWN:
                cx, cy = to_canvas(e.pos, display)
                pointer_down(cx, cy)
            elif e.type == pygame.MOUSEMOTION:
                cx, cy = to_canvas(e.pos, display)
                pointer_move(cx, cy)
            elif e.type == pygame.MOUSEBUTTONUP:
                cx, cy = to_canvas(e.pos, display)
                pointer_up(cx, cy)
            elif e.type == pygame.FINGERDOWN:
                pointer_down(e.x * W, e.y * H)
            elif e.type == pygame.FINGERMOTION:
                pointer_move(e.x * W, e.y * H)
            elif e.type == pygame.FINGERUP:
                pointer_up(e.x * W, e.y * H)

        if booted and not app.shutdown_overlay and not app.powering_down:
            app.telemetry.update(dt)
            app.data = app.telemetry.sample()
            app.check_ignition(time.time(), app.data.get("volt"))

        elapsed = time.time() - start
        if not booted and elapsed >= BOOT_SECONDS:
            booted = True
            fade_start = time.time()

        # ---- draw ----
        if not booted:
            draw_boot(canvas, app.fonts, elapsed)
        elif app.powering_down:
            draw_powering_down(canvas, app.fonts)
            now = time.time()
            if app._pd_since is None:
                app._pd_since = now
            elif now - app._pd_since >= SHUTDOWN_GRAPHIC_SECONDS:
                app.do_shutdown()
        elif app.shutdown_overlay:
            app._restart_rect = draw_shutdown(canvas, app.fonts)
        else:
            if trans["active"]:
                trans["t"] += dt / 0.28
                if trans["t"] >= 1.0:
                    trans["active"] = False
                p = min(1.0, trans["t"])
                ease = 1 - (1 - p) * (1 - p)
                s_from = pygame.Surface((W, H))
                s_to = pygame.Surface((W, H))
                app.pages[trans["from"]].draw(s_from)
                app.pages[app.page_index].draw(s_to)
                off = int(ease * W)
                d = trans["dir"]
                canvas.blit(s_from, (-d * off, 0))
                canvas.blit(s_to, (d * (W - off), 0))
            else:
                app.pages[app.page_index].draw(canvas)

            msg = app.warning_message()
            if msg:
                warning_banner(canvas, msg)
            page_dots(canvas, len(app.pages), app.page_index, DOTS_CY)

            if app.ign_countdown is not None:
                draw_ign(canvas, app.fonts, app.ign_countdown)
            if app.confirm_shutdown:
                app._confirm_yes, app._confirm_no = draw_confirm(canvas, app.fonts)

            if fade_start is not None:
                fe = time.time() - fade_start
                if fe < FADE_SECONDS:
                    ov = pygame.Surface((W, H))
                    ov.set_alpha(int(255 * (1 - fe / FADE_SECONDS)))
                    ov.fill((0, 0, 0))
                    canvas.blit(ov, (0, 0))
                else:
                    fade_start = None

        b = app.settings["brightness"]
        if b < 100:
            dim = pygame.Surface((W, H))
            dim.set_alpha(int((100 - b) / 100 * 175))
            dim.fill((0, 0, 0))
            canvas.blit(dim, (0, 0))

        if display.get_size() != (W, H):
            pygame.transform.scale(canvas, display.get_size(), display)
        else:
            display.blit(canvas, (0, 0))
        pygame.display.flip()

    pygame.quit()


def run_selftest(app, canvas):
    # render every page
    for i, page in enumerate(app.pages):
        app.page_index = i
        for _ in range(5):
            app.telemetry.update(0.1)
            app.data = app.telemetry.sample()
            app.blink2 = True
            page.draw(canvas)
    # navigation logic
    assert app.dot_index_at(320, DOTS_CY) is not None, "centre dot not hittable"
    d0 = app.dot_index_at(320 - 2 * 16, DOTS_CY)
    assert d0 == 0, f"left dot should be page 0, got {d0}"
    # interactive taps on gps/perf/settings
    for page in (app.pages[2], app.pages[3], app.pages[4]):
        page.draw(canvas)
        for rect, cb in page.buttons:
            cb()
    # shutdown confirm flow + poweroff command path
    app.request_shutdown()
    assert app.confirm_shutdown
    app.cancel_shutdown()
    assert not app.confirm_shutdown
    # verify do_shutdown issues a real poweroff command when allowed
    import main as _m
    calls = []

    class _R:
        returncode = 0

    def _fake_run(cmd, *a, **k):
        calls.append(cmd)
        return _R()

    _orig_run, _m.subprocess.run = _m.subprocess.run, _fake_run
    _orig_allow, cfg.ALLOW_SHUTDOWN = cfg.ALLOW_SHUTDOWN, True
    app.confirm_shutdown = True
    app.shutdown_overlay = False
    app.do_shutdown()
    _m.subprocess.run = _orig_run
    cfg.ALLOW_SHUTDOWN = _orig_allow
    assert calls and "poweroff" in " ".join(calls[0]), f"no poweroff command issued: {calls}"
    assert not app.shutdown_overlay, "should power off, not fall back to halted overlay"
    # ignition-sensed auto power-off -> shows goodbye graphic, then powers off
    _orig_ign, cfg.IGNITION_SENSE_ENABLED = cfg.IGNITION_SENSE_ENABLED, True

    class _IgnOff:
        def ignition_on(self):
            return False

    app.sensors = _IgnOff()
    app.powering_down = False
    app._ign_off_since = None
    app.check_ignition(1000.0)
    assert app.ign_countdown is not None and app.ign_countdown > 0, "no countdown started"
    app.check_ignition(1000.0 + cfg.IGNITION_OFF_DELAY + 0.1)
    assert app.powering_down, "ignition-off did not start power-down (goodbye graphic)"
    cfg.IGNITION_SENSE_ENABLED = _orig_ign
    # voltage-collapse auto power-off (backup power-loss via the voltage sensor)
    _orig_vl, cfg.POWER_LOSS_SHUTDOWN = getattr(cfg, "POWER_LOSS_SHUTDOWN", False), True
    app.sensors = None
    app.powering_down = False
    app._ign_off_since = None
    app.check_ignition(2000.0, 12.6)                      # power present -> no countdown
    assert app.ign_countdown is None, "voltage OK should not start a countdown"
    app.check_ignition(2000.0, 0.3)                       # power collapsed
    assert app.ign_countdown is not None, "voltage collapse did not start countdown"
    app.check_ignition(2000.0 + cfg.IGNITION_OFF_DELAY + 0.1, 0.3)
    assert app.powering_down, "voltage collapse did not start power-down"
    cfg.POWER_LOSS_SHUTDOWN = _orig_vl
    app.powering_down = False
    app._ign_off_since = None
    app.ign_countdown = None
    # goodbye + boot graphics load (cover-scaled to screen)
    assert _m.load_cover_image("shutdown_screen.jpg", W, H) is not None, "shutdown graphic missing"
    assert _m.load_cover_image("boot_logo.jpg", W, H) is not None, "boot graphic missing"
    # hybrid telemetry: fake GPS speed overrides sim, others simulated
    class FakeSensors:
        def read_speed_mph(self): return 42.0
        def read_satellites(self): return 7
        def read_rpm(self): return None
        def read_cht(self): return None
        def read_afr(self): return None
        def read_fuel_pct(self): return None
        def read_voltage(self): return None
    from telemetry import Telemetry
    t = Telemetry(FakeSensors(), True)
    t.update(0.1)
    s = t.sample()
    assert abs(s["speed"] - 42.0) < 0.001, "real GPS speed not applied"
    assert s["sats"] == 7, "real sats not applied"
    assert s["rpm"] > 0, "simulated rpm should still run"
    print("SELFTEST OK - pages render, nav works, GPS hybrid applied")
    pygame.quit()
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
