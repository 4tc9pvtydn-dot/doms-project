"""The five dashboard pages."""
import pygame

import config as cfg
from theme import (
    WHITE, AMBER, RED, GREEN, DIM, STATUS_COLOR, carbon_bg, draw_text,
    fuel_status, cht_status, afr_status, volt_status,
    disp_speed, disp_dist, speed_unit, dist_unit, fmt_time,
)
from widgets import (
    rpm_bar, vertical_bar, stat_tile, button, fan_icon, page_dots,
)


def grid_cells(x0, y0, w, h, cols, rows, gap=12):
    cw = (w - (cols - 1) * gap) / cols
    ch = (h - (rows - 1) * gap) / rows
    cells = []
    for ry in range(rows):
        for cx in range(cols):
            cells.append(pygame.Rect(int(x0 + cx * (cw + gap)),
                                     int(y0 + ry * (ch + gap)),
                                     int(cw), int(ch)))
    return cells


class Page:
    def __init__(self, app):
        self.app = app
        self.buttons = []

    def draw(self, surf):
        raise NotImplementedError

    def handle_tap(self, pos):
        for rect, cb in self.buttons:
            if rect.collidepoint(pos):
                cb()
                return True
        return False


class RidePage(Page):
    def draw(self, surf):
        d = self.app.data
        st = self.app.settings
        f = self.app.fonts
        surf.blit(carbon_bg(640, 480), (0, 0))

        # Top: brand + clock
        r = draw_text(surf, "DOMS ", f["brand"], WHITE, topleft=(16, 10))
        draw_text(surf, "RB252", f["brand"], AMBER, topleft=(r.right, 10))
        draw_text(surf, self.app.clock_str(), f["clock"], WHITE, topright=(624, 9))

        # Side bars
        fn, fd = fuel_status(d["fuel"])
        vertical_bar(surf, (18, 98, 26, 316), d["fuel"] / 100.0, fn, fd, "FUEL", f)
        cn, cd = cht_status(d["cht"], st["cht_amber"], st["cht_red"])
        vertical_bar(surf, (596, 98, 26, 316), (d["cht"] - 40) / 200.0, cn, cd, "TEMP", f)

        # RPM bar just above the speed
        rpm_bar(surf, (170, 48, 300, 34), d["rpm"], cfg.REDLINE, cfg.SHIFT_RPM)

        # Speed + gear
        spd = round(disp_speed(d["speed"], st["units"]))
        draw_text(surf, spd, f["speed"], WHITE, center=(320, 168))
        draw_text(surf, speed_unit(st["units"]), f["label_sm"], DIM, center=(320, 248))
        gear = "N" if d["gear"] == 0 else d["gear"]
        draw_text(surf, gear, f["gear"], AMBER, center=(320, 314))
        draw_text(surf, "GEAR", f["label_sm"], DIM, center=(320, 356))

        # Bottom row: AFR | Voltage(+fan) | Odometer
        an, ad = afr_status(d["afr"])
        acol = STATUS_COLOR[an] if not (ad and self.app.blink2) else tuple(int(c * 0.3) for c in STATUS_COLOR[an])
        lr = draw_text(surf, "AFR ", f["label_sm"], DIM, midleft=(16, 442))
        draw_text(surf, f"{d['afr']:.1f}", f["afr"], acol, midleft=(lr.right, 440))

        vn, vd = volt_status(d["volt"], True)
        vr = draw_text(surf, f"{d['volt']:.1f}V", f["num_md"], STATUS_COLOR[vn], center=(300, 440))
        if d["fan"]:
            fan_icon(surf, (vr.right + 16, 440), 8, GREEN)

        odo = int(disp_dist(d["odo"], st["units"]))
        draw_text(surf, f"{odo:,} {dist_unit(st['units']).lower()}",
                  f["num_md"], DIM, center=(478, 440))


class EnginePage(Page):
    def draw(self, surf):
        d = self.app.data
        st = self.app.settings
        f = self.app.fonts
        surf.blit(carbon_bg(640, 480), (0, 0))
        draw_text(surf, "ENGINE", f["title"], DIM, topleft=(20, 16))

        c = grid_cells(20, 66, 600, 300, 3, 2)
        an, ad = afr_status(d["afr"])
        cn, cd = cht_status(d["cht"], st["cht_amber"], st["cht_red"])
        vn, vd = volt_status(d["volt"], True)
        stat_tile(surf, c[0], "RPM", f"{int(d['rpm']):,}", None, WHITE, f, big=True)
        stat_tile(surf, c[1], "AFR", f"{d['afr']:.1f}", None, STATUS_COLOR[an], f, big=True, danger=ad)
        stat_tile(surf, c[2], "CHT", f"{int(d['cht'])}", "C", STATUS_COLOR[cn], f, big=True, danger=cd)
        stat_tile(surf, c[3], "EGT (FUTURE)", "--", None, DIM, f)
        stat_tile(surf, c[4], "BATTERY", f"{d['volt']:.1f}", "V", STATUS_COLOR[vn], f, big=True)

        # Fan status cell
        from theme import panel
        panel(surf, c[5])
        draw_text(surf, "FAN STATUS", f["label_sm"], DIM, topleft=(c[5].x + 14, c[5].y + 10))
        if d["fan"]:
            fan_icon(surf, (c[5].x + 30, c[5].y + 48), 12, GREEN)
            draw_text(surf, "ON", f["num_md"], GREEN, midleft=(c[5].x + 52, c[5].y + 48))
        else:
            fan_icon(surf, (c[5].x + 30, c[5].y + 48), 12, DIM)
            draw_text(surf, "OFF", f["num_md"], DIM, midleft=(c[5].x + 52, c[5].y + 48))

        # Runtime bar
        from theme import panel as _p
        rt = pygame.Rect(20, 378, 600, 46)
        _p(surf, rt)
        draw_text(surf, "ENGINE RUNTIME", f["label_sm"], DIM, midleft=(rt.x + 16, rt.centery))
        draw_text(surf, fmt_time(d["runtime"]), f["num_md"], WHITE, midleft=(rt.x + 190, rt.centery))


class GpsPage(Page):
    def draw(self, surf):
        d = self.app.data
        st = self.app.settings
        f = self.app.fonts
        surf.blit(carbon_bg(640, 480), (0, 0))
        draw_text(surf, "GPS", f["title"], DIM, topleft=(20, 16))
        draw_text(surf, f"{int(d['sats'])} SAT", f["num_md"], GREEN, topright=(620, 12))

        su = speed_unit(st["units"])
        du = dist_unit(st["units"])
        c = grid_cells(20, 66, 600, 296, 3, 2)
        stat_tile(surf, c[0], "CURRENT", round(disp_speed(d["speed"], st["units"])), su, WHITE, f, big=True)
        stat_tile(surf, c[1], "AVERAGE", round(disp_speed(d["avg"], st["units"])), su, WHITE, f)
        stat_tile(surf, c[2], "MAXIMUM", round(disp_speed(d["maxspeed"], st["units"])), su, AMBER, f)
        stat_tile(surf, c[3], "TRIP A", f"{disp_dist(d['tripA'], st['units']):.1f}", du, WHITE, f)
        stat_tile(surf, c[4], "TRIP B", f"{disp_dist(d['tripB'], st['units']):.1f}", du, WHITE, f)
        stat_tile(surf, c[5], "RIDE TIME", fmt_time(d["ride_time"]), None, WHITE, f)

        self.buttons = []
        ba = pygame.Rect(20, 376, 290, 42)
        bb = pygame.Rect(330, 376, 290, 42)
        button(surf, ba, "RESET TRIP A", f["btn"])
        button(surf, bb, "RESET TRIP B", f["btn"])
        self.buttons.append((ba, lambda: self.app.telemetry.reset_trip("A")))
        self.buttons.append((bb, lambda: self.app.telemetry.reset_trip("B")))


class PerformancePage(Page):
    def draw(self, surf):
        d = self.app.data
        st = self.app.settings
        f = self.app.fonts
        surf.blit(carbon_bg(640, 480), (0, 0))
        draw_text(surf, "PERFORMANCE", f["title"], DIM, topleft=(20, 16))

        def t(v):
            return "--" if v is None else f"{v:.2f}"

        c = grid_cells(20, 66, 600, 296, 3, 2)
        stat_tile(surf, c[0], "0-30", t(d["a030"]), "s", GREEN, f, big=True)
        stat_tile(surf, c[1], "0-60", t(d["a060"]), "s", GREEN, f, big=True)
        stat_tile(surf, c[2], "1/4 MILE", t(d["quarter"]), "s", AMBER, f, big=True)
        stat_tile(surf, c[3], "PEAK RPM", f"{int(d['peakrpm']):,}", None, RED, f)
        stat_tile(surf, c[4], "PEAK TEMP", f"{int(d['peaktemp'])} C", None, RED, f)
        stat_tile(surf, c[5], "BEST SPEED", round(disp_speed(d["bestspeed"], st["units"])),
                  speed_unit(st["units"]), AMBER, f)

        self.buttons = []
        b = pygame.Rect(20, 376, 600, 42)
        button(surf, b, "RESET PERFORMANCE STATS", f["btn"])
        self.buttons.append((b, lambda: self.app.telemetry.reset_trip("perf")))


class SettingsPage(Page):
    def draw(self, surf):
        st = self.app.settings
        f = self.app.fonts
        surf.blit(carbon_bg(640, 480), (0, 0))
        draw_text(surf, "SETTINGS", f["title"], DIM, topleft=(20, 14))
        self.buttons = []
        from theme import panel

        def row(y, label):
            rect = pygame.Rect(20, y, 600, 48)
            panel(surf, rect)
            draw_text(surf, label, f["label_sm"], DIM, midleft=(rect.x + 14, rect.centery))
            return rect

        def add(rect, cb):
            self.buttons.append((rect, cb))

        # Brightness
        r = row(48, "BRIGHTNESS")
        minus = pygame.Rect(r.right - 200, r.y + 7, 40, 34)
        plus = pygame.Rect(r.right - 54, r.y + 7, 40, 34)
        button(surf, minus, "-", f["btn"])
        button(surf, plus, "+", f["btn"])
        draw_text(surf, f"{st['brightness']}%", f["num_md"], WHITE, center=(r.right - 107, r.centery))
        add(minus, lambda: self.app.set_brightness(-10))
        add(plus, lambda: self.app.set_brightness(10))

        # Units
        r = row(104, "UNITS")
        mph = pygame.Rect(r.right - 200, r.y + 7, 90, 34)
        kph = pygame.Rect(r.right - 100, r.y + 7, 90, 34)
        button(surf, mph, "MPH", f["btn"], active=st["units"] == "mph")
        button(surf, kph, "KM/H", f["btn"], active=st["units"] == "kph")
        add(mph, lambda: st.__setitem__("units", "mph"))
        add(kph, lambda: st.__setitem__("units", "kph"))

        # Clock
        r = row(160, "CLOCK")
        h24 = pygame.Rect(r.right - 200, r.y + 7, 90, 34)
        h12 = pygame.Rect(r.right - 100, r.y + 7, 90, 34)
        button(surf, h24, "24H", f["btn"], active=st["clock24"])
        button(surf, h12, "12H", f["btn"], active=not st["clock24"])
        add(h24, lambda: st.__setitem__("clock24", True))
        add(h12, lambda: st.__setitem__("clock24", False))

        # CHT warning limits
        r = row(216, "CHT WARN LIMITS (C)")
        am = pygame.Rect(r.right - 300, r.y + 7, 34, 34)
        ap = pygame.Rect(r.right - 210, r.y + 7, 34, 34)
        rm = pygame.Rect(r.right - 130, r.y + 7, 34, 34)
        rp = pygame.Rect(r.right - 40, r.y + 7, 34, 34)
        button(surf, am, "-", f["btn"])
        button(surf, ap, "+", f["btn"])
        button(surf, rm, "-", f["btn"])
        button(surf, rp, "+", f["btn"])
        draw_text(surf, f"A {st['cht_amber']}", f["label"], AMBER, center=(r.right - 240, r.centery - 12))
        draw_text(surf, f"R {st['cht_red']}", f["label"], RED, center=(r.right - 70, r.centery - 12))
        add(am, lambda: st.__setitem__("cht_amber", max(100, st["cht_amber"] - 5)))
        add(ap, lambda: st.__setitem__("cht_amber", min(220, st["cht_amber"] + 5)))
        add(rm, lambda: st.__setitem__("cht_red", max(120, st["cht_red"] - 5)))
        add(rp, lambda: st.__setitem__("cht_red", min(250, st["cht_red"] + 5)))

        # Calibration (info)
        r = row(272, "SENSOR CALIBRATION")
        draw_text(surf, "Edit sensors.py on the Pi", f["label"], DIM, midright=(r.right - 16, r.centery))

        # Shutdown
        sd = pygame.Rect(20, 332, 600, 44)
        button(surf, sd, "SHUTDOWN", f["btn"], color=(200, 30, 30))
        add(sd, lambda: self.app.request_shutdown())
