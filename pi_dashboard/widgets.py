"""Reusable dashboard widgets drawn with pygame."""
import math
import time
import pygame

from theme import (
    WHITE, AMBER, RED, DIM, SEG_OFF, PANEL_BORDER, STATUS_COLOR,
    draw_text, panel, get_font,
)


def _blink(hz):
    return int(time.time() * hz) % 2 == 0


def rpm_tach(surf, rect, rpm, peak, fonts, max_rpm=10000, shift_rpm=7800, redline=8500):
    """Left-to-right wedge RPM bar: segments grow small->large, 1-10k scale
    across the top, with a peak-hold marker. Colour zones green/amber/red."""
    from theme import GREEN
    x, y, w, h = rect
    scale_h = 15
    bar_y = y + scale_h + 2
    bar_h = h - scale_h - 2
    base = bar_y + bar_h

    # 1-10k scale labels + ticks across the top
    for k in range(1, 11):
        lx = x + (k / 10.0) * w
        draw_text(surf, str(k), fonts["label_sm"], DIM, midbottom=(int(lx), y + scale_h))
        pygame.draw.line(surf, (60, 62, 70), (int(lx), bar_y), (int(lx), bar_y + 3), 1)

    # wedge segments
    n = 50
    gap = 2
    seg_w = (w - (n - 1) * gap) / n
    frac = max(0.0, min(1.0, rpm / max_rpm))
    lit = round(frac * n)
    shift = rpm >= shift_rpm
    hide = shift and not _blink(9)
    min_h = 5
    for i in range(n):
        lvl = (i + 1) / n
        seg_h = min_h + (bar_h - min_h) * lvl
        sx = x + i * (seg_w + gap)
        rpm_at = lvl * max_rpm
        if rpm_at >= redline:
            c = RED
        elif rpm_at >= shift_rpm:
            c = AMBER
        elif rpm_at >= 0.6 * max_rpm:
            c = (214, 222, 92)
        else:
            c = GREEN
        on = i < lit
        col = c if (on and not hide) else SEG_OFF
        pygame.draw.rect(surf, col, (int(sx), int(base - seg_h), int(seg_w) + 1, int(seg_h)),
                         border_radius=1)

    # peak-hold marker
    if peak and peak > 0:
        pf = max(0.0, min(1.0, peak / max_rpm))
        px = int(x + pf * w)
        pygame.draw.line(surf, WHITE, (px, bar_y - 3), (px, base), 2)
        pygame.draw.polygon(surf, WHITE, [(px - 4, bar_y - 7), (px + 4, bar_y - 7), (px, bar_y - 2)])

    pygame.draw.line(surf, PANEL_BORDER, (x, base + 1), (x + w, base + 1), 1)


def rpm_bar(surf, rect, rpm, redline, shift_rpm):
    """Centre-out LED style RPM bar."""
    x, y, w, h = rect
    per = 22
    gap = 2
    center_gap = 4
    seg_w = (w - center_gap - (2 * per - 1) * gap) / (2 * per)
    frac = max(0.0, min(1.0, rpm / redline))
    lit = round(frac * per)
    shift = rpm >= shift_rpm
    hide = shift and not _blink(9)  # fast flash when near redline
    cx = x + w / 2

    def seg_color(idx):
        lvl = idx / per
        if lvl >= 0.82:
            return RED
        if lvl >= 0.6:
            return AMBER
        return WHITE

    for i in range(per):  # right side
        sx = cx + center_gap / 2 + i * (seg_w + gap)
        on = i < lit
        col = seg_color(i) if on and not hide else SEG_OFF
        pygame.draw.rect(surf, col, (sx, y, seg_w, h), border_radius=2)
    for i in range(per):  # left side (mirror)
        sx = cx - center_gap / 2 - (i + 1) * seg_w - i * gap
        on = i < lit
        col = seg_color(i) if on and not hide else SEG_OFF
        pygame.draw.rect(surf, col, (sx, y, seg_w, h), border_radius=2)


def vertical_bar(surf, rect, frac, status_name, danger, label, fonts):
    """Vertical fill bar (fuel / temp)."""
    x, y, w, h = rect
    draw_text(surf, label, fonts["label_sm"], DIM, midbottom=(x + w / 2, y - 6))
    pygame.draw.rect(surf, (19, 20, 24), (x, y, w, h), border_radius=6)
    pygame.draw.rect(surf, PANEL_BORDER, (x, y, w, h), 1, border_radius=6)
    frac = max(0.0, min(1.0, frac))
    fh = int((h - 4) * frac)
    col = STATUS_COLOR[status_name]
    if danger and not _blink(2):
        col = tuple(int(c * 0.28) for c in col)
    if fh > 0:
        pygame.draw.rect(surf, col, (x + 2, y + h - 2 - fh, w - 4, fh), border_radius=4)


def stat_tile(surf, rect, label, value, unit, color, fonts, big=False, danger=False):
    panel(surf, rect)
    x, y, w, h = rect
    draw_text(surf, label.upper(), fonts["label_sm"], DIM, topleft=(x + 14, y + 10))
    vc = color
    if danger and not _blink(2):
        vc = tuple(int(c * 0.28) for c in color)
    vf = fonts["num_lg"] if big else fonts["num_md"]
    vr = draw_text(surf, value, vf, vc, topleft=(x + 13, y + 30))
    if unit:
        draw_text(surf, unit, fonts["label_sm"], DIM, bottomleft=(vr.right + 6, vr.bottom - 4))
    return vr


def button(surf, rect, text, font, active=False, color=None):
    if active:
        pygame.draw.rect(surf, AMBER, rect, border_radius=8)
        draw_text(surf, text, font, (0, 0, 0), center=rect.center)
    elif color:
        pygame.draw.rect(surf, color, rect, border_radius=8)
        draw_text(surf, text, font, WHITE, center=rect.center)
    else:
        pygame.draw.rect(surf, (24, 25, 30), rect, border_radius=8)
        pygame.draw.rect(surf, PANEL_BORDER, rect, 1, border_radius=8)
        draw_text(surf, text, font, WHITE, center=rect.center)


def fan_icon(surf, center, radius, color):
    cx, cy = center
    ang = time.time() * 6.0
    for i in range(3):
        a = ang + i * (2 * math.pi / 3)
        ex = cx + math.cos(a) * radius
        ey = cy + math.sin(a) * radius
        pygame.draw.line(surf, color, (cx, cy), (ex, ey), 3)
    pygame.draw.circle(surf, color, (int(cx), int(cy)), 3)


def page_dots(surf, count, index, cy):
    gap = 16
    startx = 320 - (count - 1) * gap / 2
    for i in range(count):
        cx = int(startx + i * gap)
        if i == index:
            pygame.draw.circle(surf, WHITE, (cx, cy), 5)
        else:
            pygame.draw.circle(surf, (95, 97, 105), (cx, cy), 4)


def warning_banner(surf, msg):
    col = (220, 0, 0) if _blink(1.4) else (110, 0, 0)
    pygame.draw.rect(surf, col, (0, 0, 640, 34))
    draw_text(surf, msg, get_font(19), WHITE, center=(320, 17))
