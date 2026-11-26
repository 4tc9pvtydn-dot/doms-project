"""Screens: ride, cruise, rides, settings, boot, power-down overlays."""
import math
import time
import pygame
import config as cfg
from theme import (WHITE, AMBER, RED, GREEN, DIM, FAINT, BG, PANEL, EDGE, SEG_OFF,
                   blink, text, fuel_color, cht_color, volt_color, rpm_zone_color,
                   cover_image)

NO_SIGNAL = "--"
RIDES_PER_PAGE = 6


def fmt(v, spec):
    return NO_SIGNAL if v is None else format(v, spec)


def panel(surf, sc, x, y, w, h, border=EDGE):
    r = sc.r(x, y, w, h)
    pygame.draw.rect(surf, PANEL, r, border_radius=sc.n(10))
    pygame.draw.rect(surf, border, r, max(1, sc.n(2) // 2), border_radius=sc.n(10))
    return r


# ------------------------------------------------------------ widgets
def tach(surf, sc, rpm, peak):
    """Left-to-right wedge bar, 1-10k scale, peak marker, shift flash."""
    x, y, w, h = 24, 58, 752, 86
    scale_h = 20
    base = y + h
    for k in range(1, 11):
        lx = x + k / 10 * w
        text(surf, sc, str(k), 19, DIM, midbottom=(lx - 6 if k == 10 else lx, y + scale_h - 2))
    n, gap = 50, 3
    seg_w = (w - (n - 1) * gap) / n
    val = rpm or 0.0
    lit = round(max(0.0, min(1.0, val / cfg.RPM_SCALE_MAX)) * n)
    hide = val >= cfg.SHIFT_RPM and not blink(9)
    for i in range(n):
        lvl = (i + 1) / n
        sh = 6 + (h - scale_h - 6) * lvl
        col = rpm_zone_color(lvl * cfg.RPM_SCALE_MAX) if (i < lit and not hide) else SEG_OFF
        pygame.draw.rect(surf, col, sc.r(x + i * (seg_w + gap), base - sh, seg_w + 0.6, sh))
    if peak > 0:
        px = x + min(1.0, peak / cfg.RPM_SCALE_MAX) * w
        pygame.draw.line(surf, WHITE, sc.p(px, y + scale_h), sc.p(px, base), sc.n(3))


def gauge_row(surf, sc, y, label, value, unit, frac, color, flash=False, note=None):
    """Label + big value + horizontal traffic-light bar."""
    panel(surf, sc, 470, y, 306, 82, border=RED if flash and blink(2) else EDGE)
    text(surf, sc, label, 20, DIM, topleft=(486, y + 6))
    vcol = color if not (flash and not blink(2)) else FAINT
    vr = text(surf, sc, value, 36, vcol, digital=True, topright=(700, y + 6))
    text(surf, sc, unit, 19, DIM, topleft=(708, y + 20))
    if note:
        text(surf, sc, note, 17, AMBER, topleft=(486, y + 32))
    bar = sc.r(486, y + 58, 274, 12)
    pygame.draw.rect(surf, SEG_OFF, bar, border_radius=sc.n(6))
    if frac is not None and frac > 0:
        fill = bar.copy()
        fill.w = max(sc.n(6), int(bar.w * min(1.0, frac)))
        pygame.draw.rect(surf, color, fill, border_radius=sc.n(6))
    return vr


def top_bar(surf, sc, gps, clock_str):
    text(surf, sc, "RB250", 24, AMBER, digital=True, midleft=(24, 26))
    state, used, heard = gps
    if state == "fix":
        msg, col = f"GPS {used} SAT", GREEN
    elif state == "search":
        msg, col = f"GPS SEARCHING {heard}", AMBER if blink(1.5) else FAINT
    else:
        msg, col = "NO GPS", RED
    text(surf, sc, msg, 21, col, center=(400, 26))
    text(surf, sc, clock_str, 24, WHITE, digital=True, midright=(776, 26))


# ------------------------------------------------------------ screens
def ride_screen(surf, sc, t, clock_str):
    surf.fill(BG)
    top_bar(surf, sc, t.gps, clock_str)
    tach(surf, sc, t.rpm, t.peak_rpm)

    # digital rpm under the bar
    rcol = RED if (t.rpm or 0) >= cfg.REDLINE else WHITE
    r = text(surf, sc, fmt(t.rpm, ".0f"), 40, rcol, digital=True, topleft=(24, 154))
    text(surf, sc, "RPM", 19, DIM, bottomleft=(sc.to_design(r.bottomright)[0] + 8, 190))
    if t.rpm is None:
        text(surf, sc, "NO RPM SIGNAL", 17, AMBER, topleft=(24, 200))

    # speed
    spd = None if t.speed is None else round(t.speed)
    text(surf, sc, NO_SIGNAL if spd is None else spd, 170, WHITE, digital=True,
         midbottom=(235, 400))
    text(surf, sc, "MPH", 24, DIM, midtop=(235, 402))

    # right column gauges
    hot = t.cht is not None and t.cht > cfg.CHT_RED
    gauge_row(surf, sc, 154, "HEAD TEMP", fmt(t.cht, ".0f"), "°C",
              None if t.cht is None else t.cht / 250.0, cht_color(t.cht), flash=hot,
              note="NO SIGNAL" if t.cht is None else None)
    low = t.fuel is not None and t.fuel < cfg.FUEL_RED
    gauge_row(surf, sc, 244, "FUEL", fmt(t.fuel, ".0f"), "%",
              None if t.fuel is None else t.fuel / 100.0, fuel_color(t.fuel), flash=low,
              note="NO SIGNAL" if t.fuel is None else None)
    gauge_row(surf, sc, 334, "BATTERY", fmt(t.volt, ".1f"), "V",
              None if t.volt is None else (t.volt - 10) / 5.0, volt_color(t.volt),
              note="NO SIGNAL" if t.volt is None else None)

    # miles strip
    text(surf, sc, "TRIP", 18, DIM, bottomleft=(24, 462))
    text(surf, sc, f"{t.trip:.1f}", 24, WHITE, digital=True, bottomleft=(72, 466))
    text(surf, sc, "ODO", 18, DIM, bottomleft=(470, 462))
    text(surf, sc, f"{t.odo:,.0f}", 24, WHITE, digital=True, bottomleft=(512, 466))
    text(surf, sc, "MI", 18, DIM, bottomright=(776, 462))

    if hot:
        warn_banner(surf, sc, "ENGINE HOT - EASE OFF")
    elif low:
        warn_banner(surf, sc, "FUEL LOW")


def vbar(surf, sc, x, label, value, unit, frac, color, marks=(), flash=False):
    """Tall, wide vertical bar (fills from the bottom) with value underneath."""
    top, bottom, w = 64, 372, 104
    text(surf, sc, label, 20, DIM, midtop=(x + w / 2, 30))
    outer = sc.r(x, top, w, bottom - top)
    pygame.draw.rect(surf, PANEL, outer, border_radius=sc.n(12))
    pygame.draw.rect(surf, RED if flash and blink(2) else EDGE, outer, sc.n(2),
                     border_radius=sc.n(12))
    n, gap = 12, 6
    seg_h = (bottom - top - 16 - gap * (n - 1)) / n
    lit = 0 if frac is None else math.ceil(max(0.0, min(1.0, frac)) * n - 0.01)
    for i in range(n):
        y = bottom - 8 - (i + 1) * seg_h - i * gap
        col = color if i < lit and not (flash and not blink(2)) else SEG_OFF
        pygame.draw.rect(surf, col, sc.r(x + 12, y, w - 24, seg_h), border_radius=sc.n(4))
    for f, mcol in marks:  # limit ticks, e.g. amber / red temp lines
        y = bottom - 8 - f * (bottom - top - 16)
        pygame.draw.line(surf, mcol, sc.p(x - 6, y), sc.p(x + 4, y), sc.n(3))
    text(surf, sc, value, 38, color if value != NO_SIGNAL else DIM, digital=True,
         midtop=(x + w / 2, 382))
    text(surf, sc, unit if value != NO_SIGNAL else "NO SIGNAL", 17,
         DIM if value != NO_SIGNAL else AMBER, midtop=(x + w / 2, 424))


def speed_dial(surf, sc, mph):
    """Large analog speedo. 0..DIAL_MAX over a 240 degree sweep."""
    cx, cy = sc.p(400, 214)
    rad = sc.n(196)
    top = cfg.DIAL_MAX_MPH
    a0, sweep = math.radians(210), math.radians(240)

    def at(v, r):
        a = a0 - sweep * max(0.0, min(1.0, v / top))
        return (cx + r * math.cos(a), cy - r * math.sin(a))

    pygame.draw.circle(surf, PANEL, (cx, cy), rad)
    pygame.draw.circle(surf, EDGE, (cx, cy), rad, sc.n(3))
    # lit arc up to the current speed
    if mph:
        steps = max(2, int(60 * min(1.0, mph / top)))
        pts = [at(mph * i / steps, rad - sc.n(14)) for i in range(steps + 1)]
        pygame.draw.lines(surf, AMBER, False, pts, sc.n(8))
    for v in range(0, top + 1, 5):
        major = v % 10 == 0
        pygame.draw.line(surf, WHITE if major else FAINT, at(v, rad - sc.n(26 if major else 22)),
                         at(v, rad - sc.n(40 if major else 32)), sc.n(4 if major else 2))
        if major:
            lbl = sc.font(24, True).render(str(v), True, WHITE)
            surf.blit(lbl, lbl.get_rect(center=at(v, rad - sc.n(72))))
    # needle
    if mph is not None:
        a = a0 - sweep * max(0.0, min(1.0, mph / top))
        tip = (cx + (rad - sc.n(30)) * math.cos(a), cy - (rad - sc.n(30)) * math.sin(a))
        side = sc.n(7)
        base1 = (cx + side * math.cos(a + math.pi / 2), cy - side * math.sin(a + math.pi / 2))
        base2 = (cx + side * math.cos(a - math.pi / 2), cy - side * math.sin(a - math.pi / 2))
        pygame.draw.polygon(surf, RED, [tip, base1, base2])
    pygame.draw.circle(surf, (40, 41, 46), (cx, cy), sc.n(20))
    pygame.draw.circle(surf, AMBER, (cx, cy), sc.n(8))
    # small digital readout + unit inside the dial
    val = NO_SIGNAL if mph is None else f"{round(mph)}"
    img = sc.font(48, True).render(val, True, WHITE)
    surf.blit(img, img.get_rect(center=(cx, cy + sc.n(92))))
    unit = sc.font(18).render("MPH" if mph is not None else "NO GPS", True,
                              DIM if mph is not None else AMBER)
    surf.blit(unit, unit.get_rect(center=(cx, cy + sc.n(132))))


def cruise_screen(surf, sc, t, clock_str):
    """Long-ride page: big speedo, fuel left, head temp right, time + miles."""
    surf.fill(BG)
    low = t.fuel is not None and t.fuel < cfg.FUEL_RED
    vbar(surf, sc, 24, "FUEL", fmt(t.fuel, ".0f"), "%",
         None if t.fuel is None else t.fuel / 100.0, fuel_color(t.fuel), flash=low)
    hot = t.cht is not None and t.cht > cfg.CHT_RED
    m = cfg.CHT_BAR_MAX
    vbar(surf, sc, 672, "HEAD", fmt(t.cht, ".0f"), "°C",
         None if t.cht is None else t.cht / m, cht_color(t.cht),
         marks=((cfg.CHT_AMBER / m, AMBER), (cfg.CHT_RED / m, RED)), flash=hot)
    speed_dial(surf, sc, t.speed)
    text(surf, sc, clock_str, 44, WHITE, digital=True, midbottom=(400, 452))
    text(surf, sc, "TRIP", 18, DIM, bottomleft=(150, 448))
    text(surf, sc, f"{t.trip:.1f}", 24, WHITE, digital=True, bottomleft=(198, 452))
    text(surf, sc, "ODO", 18, DIM, bottomleft=(500, 448))
    text(surf, sc, f"{t.odo:,.0f}", 24, WHITE, digital=True, bottomleft=(542, 452))


def warn_banner(surf, sc, msg):
    col = (210, 0, 0) if blink(1.4) else (110, 0, 0)
    pygame.draw.rect(surf, col, sc.r(0, 0, 800, 52))
    text(surf, sc, msg, 24, WHITE, center=(400, 26))


def button(surf, sc, x, y, w, h, label, fill=(26, 27, 32), fg=WHITE):
    r = sc.r(x, y, w, h)
    pygame.draw.rect(surf, fill, r, border_radius=sc.n(10))
    pygame.draw.rect(surf, EDGE, r, 1, border_radius=sc.n(10))
    text(surf, sc, label, 20, fg, center=(x + w / 2, y + h / 2))
    return r


def settings_screen(surf, sc, app):
    """Returns list of (rect, callback) buttons."""
    surf.fill(BG)
    text(surf, sc, "SETTINGS", 24, AMBER, digital=True, midleft=(24, 30))
    btns = []
    t = app.telemetry

    text(surf, sc, "TRIP", 18, DIM, midleft=(24, 96))
    text(surf, sc, f"{t.trip:.1f} MI", 26, WHITE, digital=True, midleft=(150, 96))
    btns.append((button(surf, sc, 560, 72, 216, 50, "RESET TRIP"), t.reset_trip))

    text(surf, sc, "BRIGHTNESS", 18, DIM, midleft=(24, 166))
    text(surf, sc, f"{app.brightness}%", 26, WHITE, digital=True, midleft=(230, 166))
    btns.append((button(surf, sc, 560, 142, 100, 50, "-"), lambda: app.set_brightness(-20)))
    btns.append((button(surf, sc, 676, 142, 100, 50, "+"), lambda: app.set_brightness(20)))

    text(surf, sc, "SENSORS", 18, DIM, midleft=(24, 236))
    x = 160
    for name, state, ok in app.sensors.status():
        col = GREEN if ok else (DIM if state == "OFF" else AMBER)
        r = text(surf, sc, f"{name} {state}", 18, col, midleft=(x, 236))
        x = sc.to_design(r.midright)[0] + 26

    if t.ups is None:
        text(surf, sc, "UPS BATTERY", 18, DIM, midleft=(24, 290))
        text(surf, sc, "NO SIGNAL", 18, AMBER, midleft=(230, 290))
    else:
        uv, up = t.ups
        ucol = RED if up < cfg.UPS_LOW_PCT else (AMBER if up < 40 else GREEN)
        text(surf, sc, "UPS BATTERY", 18, DIM, midleft=(24, 290))
        text(surf, sc, f"{up:.0f}%  {uv:.2f}V", 24, ucol, digital=True, midleft=(230, 290))

    volt = t.volt
    auto = "ON" if cfg.POWER_LOSS_SHUTDOWN else "OFF"
    text(surf, sc, f"AUTO SHUTDOWN {auto}  (below {cfg.POWER_LOSS_VOLTS:.0f}V)", 16, DIM,
         midleft=(24, 330))
    if cfg.POWER_LOSS_SHUTDOWN and volt is None:
        text(surf, sc, "NO VOLTAGE READING - AUTO SHUTDOWN CAN'T WORK", 15, AMBER,
             midleft=(24, 352))

    btns.append((button(surf, sc, 250, 376, 300, 60, "POWER OFF", fill=(170, 24, 24)),
                 app.request_shutdown))
    text(surf, sc, "SELECT = move    HOLD SELECT = press", 15, FAINT, midright=(776, 452))
    return btns


def rides_screen(surf, sc, t, sel=0):
    """Ride history, newest first (the ride in progress is marked NOW)."""
    from rides import avg_mph
    surf.fill(BG)
    text(surf, sc, "RIDES", 24, AMBER, digital=True, midleft=(24, 30))
    hist = t.rides.history()
    total = sum(r["miles"] for r in hist)
    text(surf, sc, f"{len(hist)} rides  {total:,.0f} mi", 18, DIM, midright=(776, 30))
    cols = [(24, "DATE"), (190, "MILES"), (290, "TIME"), (390, "AVG"), (480, "TOP"),
            (570, "PEAK RPM"), (700, "MAX °C")]
    for x, h in cols:
        text(surf, sc, h, 16, DIM, midleft=(x, 78))
    pygame.draw.line(surf, EDGE, sc.p(24, 94), sc.p(776, 94), 1)
    if not hist:
        text(surf, sc, "No rides yet - rides over 0.1 mile are saved", 20, DIM,
             center=(400, 250))
    cur = t.rides.cur["start"] if t.rides.cur else None
    sel = min(sel, max(0, len(hist) - 1))
    offset = sel // RIDES_PER_PAGE * RIDES_PER_PAGE
    if hist:
        text(surf, sc, f"{sel + 1} of {len(hist)}   SELECT = next   HOLD = open", 16, DIM,
             midleft=(24, 446))
    for i, r in enumerate(hist[offset:offset + RIDES_PER_PAGE]):
        y = 124 + i * 52
        if offset + i == sel:
            pygame.draw.rect(surf, (40, 32, 14), sc.r(14, y - 24, 772, 48), border_radius=sc.n(8))
            pygame.draw.rect(surf, AMBER, sc.r(14, y - 24, 772, 48), sc.n(2), border_radius=sc.n(8))
        live = r["start"] == cur
        when = "NOW" if live else time.strftime("%d %b %H:%M", time.localtime(r["start"]))
        mins = int(r["secs"] // 60)
        cht = r.get("max_cht")
        vals = [when, f"{r['miles']:.1f}", f"{mins // 60}:{mins % 60:02d}", f"{avg_mph(r):.0f}",
                f"{r['top_mph']:.0f}", f"{r['peak_rpm']:.0f}", NO_SIGNAL if cht is None else f"{cht:.0f}"]
        for (x, _), v in zip(cols, vals):
            col = AMBER if live and x == 24 else WHITE
            if x == 700 and cht is not None:
                col = cht_color(cht)
            text(surf, sc, v, 22, col, midleft=(x, y))
        pygame.draw.line(surf, (28, 29, 34), sc.p(24, y + 26), sc.p(776, y + 26), 1)


def tile(surf, sc, x, y, w, h, label, value, unit, color=WHITE):
    panel(surf, sc, x, y, w, h)
    text(surf, sc, label, 19, DIM, topleft=(x + 16, y + 12))
    r = text(surf, sc, value, 58, color, digital=True, bottomleft=(x + 16, y + h - 12))
    if unit:
        text(surf, sc, unit, 20, DIM, bottomleft=(sc.to_design(r.bottomright)[0] + 8, y + h - 20))


def ride_detail_screen(surf, sc, t, sel):
    """One ride full-screen with big numbers."""
    from rides import avg_mph
    surf.fill(BG)
    hist = t.rides.history()
    if not hist:
        return
    sel = min(sel, len(hist) - 1)
    r = hist[sel]
    live = t.rides.cur is not None and r["start"] == t.rides.cur["start"]
    when = time.strftime("%a %d %b %Y  %H:%M", time.localtime(r["start"]))
    text(surf, sc, "RIDE IN PROGRESS" if live else "RIDE", 24, AMBER, digital=True,
         midleft=(24, 32))
    text(surf, sc, when, 20, WHITE, midright=(776, 32))
    mins = int(r["secs"] // 60)
    cht = r.get("max_cht")
    w, h, gx, gy = 240, 160, 16, 16
    tiles = [
        ("DISTANCE", f"{r['miles']:.1f}", "MI", WHITE),
        ("RIDE TIME", f"{mins // 60}:{mins % 60:02d}", "", WHITE),
        ("AVERAGE", f"{avg_mph(r):.0f}", "MPH", WHITE),
        ("TOP SPEED", f"{r['top_mph']:.0f}", "MPH", WHITE),
        ("PEAK REVS", f"{r['peak_rpm']:.0f}", "RPM",
         RED if r["peak_rpm"] >= cfg.REDLINE else WHITE),
        ("HOTTEST HEAD", NO_SIGNAL if cht is None else f"{cht:.0f}", "°C", cht_color(cht)),
    ]
    for i, (label, val, unit, col) in enumerate(tiles):
        x = 24 + (i % 3) * (w + gx)
        y = 70 + (i // 3) * (h + gy)
        tile(surf, sc, x, y, w, h, label, val, unit, col)
    text(surf, sc, f"{sel + 1} of {len(hist)}   SELECT = older ride   HOLD = back", 16, DIM,
         midleft=(24, 446))


def highlight(surf, sc, rect):
    pygame.draw.rect(surf, AMBER, rect.inflate(sc.n(8), sc.n(8)), sc.n(3),
                     border_radius=sc.n(12))


def page_dots(surf, sc, count, index):
    for i in range(count):
        cx = 400 + (i - (count - 1) / 2) * 22
        col = WHITE if i == index else FAINT
        pygame.draw.circle(surf, col, sc.p(cx, 470), sc.n(5 if i == index else 4))


def boot_screen(surf, sc, progress):
    img = cover_image("boot_bg.jpg", sc.w, sc.h)
    if img is not None:
        surf.blit(img, (0, 0))
    else:
        surf.fill(BG)
    text(surf, sc, "RB250", 84, AMBER, digital=True, center=(400, 380))
    bar = sc.r(260, 440, 280, 8)
    pygame.draw.rect(surf, SEG_OFF, bar, border_radius=sc.n(4))
    fill = bar.copy()
    fill.w = int(bar.w * max(0.0, min(1.0, progress)))
    if fill.w:
        pygame.draw.rect(surf, AMBER, fill, border_radius=sc.n(4))


def goodbye_screen(surf, sc):
    img = cover_image("shutdown_screen.jpg", sc.w, sc.h)
    if img is not None:
        surf.blit(img, (0, 0))
    else:
        surf.fill(BG)
        text(surf, sc, "UNTIL NEXT TIME DUDE", 36, AMBER, center=(400, 240))


def countdown_overlay(surf, sc, secs):
    col = (200, 30, 30) if blink(2) else (120, 10, 10)
    pygame.draw.rect(surf, col, sc.r(0, 180, 800, 120))
    text(surf, sc, "IGNITION OFF - SHUTTING DOWN", 28, WHITE, center=(400, 222))
    text(surf, sc, f"{secs:.0f}s  (switch on to cancel)", 20, WHITE, center=(400, 266))


def confirm_overlay(surf, sc):
    shade = pygame.Surface((sc.w, sc.h))
    shade.set_alpha(200)
    surf.blit(shade, (0, 0))
    panel(surf, sc, 160, 130, 480, 220, border=(120, 30, 30))
    text(surf, sc, "POWER OFF?", 30, WHITE, center=(400, 175))
    text(surf, sc, "SELECT = switch   HOLD = confirm", 15, DIM, center=(400, 215))
    yes = button(surf, sc, 190, 250, 200, 70, "POWER OFF", fill=(190, 28, 28))
    no = button(surf, sc, 410, 250, 200, 70, "CANCEL")
    return yes, no


def halted_screen(surf, sc):
    surf.fill((0, 0, 0))
    text(surf, sc, "SAFE TO SWITCH OFF", 28, DIM, center=(400, 240))
