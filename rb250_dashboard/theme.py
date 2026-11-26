"""Colours, fonts, traffic-light logic and the screen scaler."""
import os
import time
import pygame
import config as cfg

WHITE = (245, 247, 255)
AMBER = (251, 176, 36)
RED = (255, 64, 64)
GREEN = (60, 220, 120)
DIM = (130, 134, 144)
FAINT = (70, 73, 82)
BG = (10, 10, 12)
PANEL = (20, 21, 25)
EDGE = (44, 46, 52)
SEG_OFF = (30, 31, 36)

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "assets", "fonts")
_DIGITAL = os.path.join(FONTS, "Orbitron-Bold.ttf")
_LABEL = os.path.join(FONTS, "ChakraPetch-Bold.ttf")


def blink(hz=2.0):
    return int(time.time() * hz) % 2 == 0


class Scaler:
    """Layout is designed on an 800x480 grid and stretched to the real screen
    (640x480, 480x320, 800x480 ...)."""

    def __init__(self, w, h):
        self.w, self.h = w, h
        # stretch to fill any screen shape; text + strokes use the smaller scale
        self.sx = w / cfg.DESIGN_W
        self.sy = h / cfg.DESIGN_H
        self.s = min(self.sx, self.sy)
        self._fonts = {}

    def p(self, x, y):
        return (int(x * self.sx), int(y * self.sy))

    def r(self, x, y, w, h):
        return pygame.Rect(int(x * self.sx), int(y * self.sy),
                           max(1, int(w * self.sx)), max(1, int(h * self.sy)))

    def n(self, v):
        return max(1, int(v * self.s))

    def to_design(self, pos):
        return (pos[0] / self.sx, pos[1] / self.sy)

    def font(self, size, digital=False):
        px = max(10, int(size * self.s))
        key = (px, digital)
        if key not in self._fonts:
            path = _DIGITAL if digital else _LABEL
            try:
                self._fonts[key] = pygame.font.Font(path, px)
            except Exception:
                self._fonts[key] = pygame.font.Font(None, px)
        return self._fonts[key]


def text(surf, sc, msg, size, color, digital=False, **anchor):
    """Draw text; anchor values are design-grid points, e.g. center=(400, 240)."""
    img = sc.font(size, digital).render(str(msg), True, color)
    rect = img.get_rect()
    for k, v in anchor.items():
        setattr(rect, k, sc.p(*v))
    surf.blit(img, rect)
    return rect


# ---- traffic lights ----
def fuel_color(pct):
    if pct is None:
        return DIM
    if pct < cfg.FUEL_RED:
        return RED
    if pct < cfg.FUEL_AMBER:
        return AMBER
    return GREEN


def cht_color(t):
    if t is None:
        return DIM
    if t > cfg.CHT_RED:
        return RED
    if t >= cfg.CHT_AMBER:
        return AMBER
    return GREEN


def volt_color(v):
    if v is None:
        return DIM
    if v > cfg.VOLT_HIGH:
        return RED
    if v < cfg.VOLT_LOW:
        return AMBER
    return GREEN


def rpm_zone_color(rpm):
    if rpm >= cfg.REDLINE:
        return RED
    if rpm >= cfg.SHIFT_RPM:
        return AMBER
    if rpm >= 0.6 * cfg.RPM_SCALE_MAX:
        return (214, 222, 92)
    return GREEN


_img_cache = {}


def cover_image(name, w, h):
    """Load assets/<name> scaled to cover w x h (centre-cropped). None if missing."""
    key = (name, w, h)
    if key not in _img_cache:
        try:
            img = pygame.image.load(os.path.join(HERE, "assets", name)).convert()
            iw, ih = img.get_size()
            k = max(w / iw, h / ih)
            img = pygame.transform.smoothscale(img, (int(iw * k) + 1, int(ih * k) + 1))
            out = pygame.Surface((w, h))
            out.blit(img, ((w - img.get_width()) // 2, (h - img.get_height()) // 2))
            _img_cache[key] = out
        except Exception:
            _img_cache[key] = None
    return _img_cache[key]
