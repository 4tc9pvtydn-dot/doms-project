#!/usr/bin/env python3
"""
DOMS RB252 - Lambretta Digital Dashboard (Pygame)

Run on a laptop for testing:      python main.py
Run full-screen (on the Pi):      python main.py --fullscreen
Headless smoke test:              python main.py --selftest
"""
import os
import sys
import time
import argparse
import subprocess

# Allow headless import for --selftest before creating a window.
if "--selftest" in sys.argv:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402

import config as cfg  # noqa: E402
from theme import (  # noqa: E402
    carbon_bg, get_font, WHITE, AMBER, DIM, set_hw_brightness,
    cht_status, afr_status,
)
from widgets import page_dots, warning_banner  # noqa: E402
from telemetry import Telemetry  # noqa: E402
from sensors import Sensors  # noqa: E402
from pages import RidePage, EnginePage, GpsPage, PerformancePage, SettingsPage  # noqa: E402

W, H = cfg.WIDTH, cfg.HEIGHT
BOOT_SECONDS = 2.6
FADE_SECONDS = 0.4
SWIPE_THRESHOLD = 50
TAP_MOVE_MAX = 14


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
        self.data = self.telemetry.sample()
        self.fonts = build_fonts()
        self.page_index = 0
        self.pages = [
            RidePage(self), EnginePage(self), GpsPage(self),
            PerformancePage(self), SettingsPage(self),
        ]
        self.shutdown_overlay = False
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

    def request_shutdown(self):
        if cfg.ALLOW_SHUTDOWN:
            try:
                subprocess.Popen(["sudo", "shutdown", "-h", "now"])
            except Exception:
                self.shutdown_overlay = True
        else:
            self.shutdown_overlay = True

    def reboot_ui(self):
        self.shutdown_overlay = False
        self.telemetry.reset_all()
        self.page_index = 0

    def warning_message(self):
        cn, cd = cht_status(self.data["cht"], self.settings["cht_amber"], self.settings["cht_red"])
        if cd:
            return "CYLINDER TEMP CRITICAL"
        an, ad = afr_status(self.data["afr"])
        if ad:
            return "AFR DANGER - CHECK MIXTURE"
        return None


def draw_boot(surf, fonts, elapsed):
    surf.blit(carbon_bg(W, H), (0, 0))
    from theme import draw_text, RED
    draw_text(surf, "DOMS", fonts["boot_big"], WHITE, center=(320, 190))
    draw_text(surf, "RB252", fonts["boot_sub"], AMBER, center=(320, 240))
    draw_text(surf, "INITIALISING...", fonts["label_sm"], DIM, center=(320, 300))
    bar = pygame.Rect(190, 320, 260, 8)
    pygame.draw.rect(surf, (28, 29, 33), bar, border_radius=4)
    prog = max(0.0, min(1.0, elapsed / BOOT_SECONDS))
    if prog > 0:
        pygame.draw.rect(surf, AMBER, (bar.x, bar.y, int(bar.w * prog), bar.h), border_radius=4)


def draw_shutdown(surf, fonts):
    surf.fill((0, 0, 0))
    from theme import draw_text
    pygame.draw.circle(surf, DIM, (320, 190), 24, 3)
    pygame.draw.line(surf, DIM, (320, 172), (320, 196), 3)
    draw_text(surf, "SYSTEM HALTED", fonts["label"], DIM, center=(320, 250))
    r = pygame.Rect(250, 285, 140, 40)
    from widgets import button
    button(surf, r, "RESTART", fonts["btn"])
    return r


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

    # transition state
    trans = {"active": False, "dir": 0, "t": 0.0, "from": 0}
    press = {"pos": None, "moved": 0.0}

    def goto(idx):
        idx = max(0, min(len(app.pages) - 1, idx))
        if idx != app.page_index:
            trans["active"] = True
            trans["dir"] = 1 if idx > app.page_index else -1
            trans["t"] = 0.0
            trans["from"] = app.page_index
            app.page_index = idx

    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        dt = min(dt, 0.05)
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
                press["pos"] = to_canvas(e.pos, display)
                press["moved"] = 0.0
            elif e.type == pygame.MOUSEMOTION and press["pos"] is not None:
                cp = to_canvas(e.pos, display)
                press["moved"] = max(press["moved"], abs(cp[0] - press["pos"][0]))
            elif e.type == pygame.MOUSEBUTTONUP and press["pos"] is not None:
                cp = to_canvas(e.pos, display)
                dx = cp[0] - press["pos"][0]
                if app.shutdown_overlay:
                    if getattr(app, "_restart_rect", None) and app._restart_rect.collidepoint(cp):
                        app.reboot_ui()
                elif abs(dx) > SWIPE_THRESHOLD and not trans["active"]:
                    goto(app.page_index + (1 if dx < 0 else -1))
                elif press["moved"] < TAP_MOVE_MAX and not trans["active"]:
                    app.pages[app.page_index].handle_tap(cp)
                press["pos"] = None

        # update sim
        if booted and not app.shutdown_overlay:
            app.telemetry.update(dt)
            app.data = app.telemetry.sample()

        elapsed = time.time() - start
        if not booted and elapsed >= BOOT_SECONDS:
            booted = True
            fade_start = time.time()

        # ---- draw ----
        if not booted:
            draw_boot(canvas, app.fonts, elapsed)
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
            page_dots(canvas, len(app.pages), app.page_index, 468)

            # boot fade-in
            if fade_start is not None:
                fe = time.time() - fade_start
                if fe < FADE_SECONDS:
                    ov = pygame.Surface((W, H))
                    ov.set_alpha(int(255 * (1 - fe / FADE_SECONDS)))
                    ov.fill((0, 0, 0))
                    canvas.blit(ov, (0, 0))
                else:
                    fade_start = None

        # brightness dim overlay (visual night-dim; also drives hw backlight)
        b = app.settings["brightness"]
        if b < 100:
            dim = pygame.Surface((W, H))
            dim.set_alpha(int((100 - b) / 100 * 175))
            dim.fill((0, 0, 0))
            canvas.blit(dim, (0, 0))

        # scale canvas to the real display
        if display.get_size() != (W, H):
            pygame.transform.scale(canvas, display.get_size(), display)
        else:
            display.blit(canvas, (0, 0))
        pygame.display.flip()

    pygame.quit()


def run_selftest(app, canvas):
    """Render every page + exercise taps headlessly to catch crashes."""
    for i, page in enumerate(app.pages):
        app.page_index = i
        for _ in range(5):
            app.telemetry.update(0.1)
            app.data = app.telemetry.sample()
            app.blink2 = True
            page.draw(canvas)
    # exercise interactive taps
    for page in (app.pages[2], app.pages[3], app.pages[4]):
        page.draw(canvas)
        for rect, cb in page.buttons:
            cb()
    app.set_brightness(-30)
    app.set_brightness(20)
    app.request_shutdown()
    draw_shutdown(canvas, app.fonts)
    print("SELFTEST OK - rendered %d pages" % len(app.pages))
    pygame.quit()
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
