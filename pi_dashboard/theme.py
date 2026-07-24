"""
Theme: colours, fonts, carbon-fibre background, status logic, unit helpers
and a flexible text-drawing helper. Everything visual/shared lives here.
"""
import os
import glob
import pygame

# ---- Palette (RGB) ----
WHITE = (245, 247, 255)
AMBER = (251, 191, 36)
RED = (255, 77, 77)
GREEN = (74, 222, 128)
DIM = (138, 141, 150)
BG = (11, 11, 13)
PANEL = (18, 19, 23)
PANEL_BORDER = (44, 46, 52)
SEG_OFF = (28, 29, 33)

STATUS_COLOR = {"green": GREEN, "amber": AMBER, "red": RED, "white": WHITE}

_ASSETS = os.path.join(os.path.dirname(__file__), "assets", "fonts")
_DIGITAL = os.path.join(_ASSETS, "Orbitron-Bold.ttf")     # big numbers
_LABEL = os.path.join(_ASSETS, "ChakraPetch-Bold.ttf")    # labels / text

_font_cache = {}


def get_font(size, digital=False):
    key = (size, digital)
    if key in _font_cache:
        return _font_cache[key]
    path = _DIGITAL if digital else _LABEL
    try:
        if os.path.exists(path):
            f = pygame.font.Font(path, size)
        else:
            f = pygame.font.SysFont("dejavusans", size, bold=True)
    except Exception:
        f = pygame.font.Font(None, size)
    _font_cache[key] = f
    return f


# ---- Carbon-fibre background (procedural twill weave) ----
_carbon = None


def carbon_bg(w, h):
    global _carbon
    if _carbon is not None and _carbon.get_size() == (w, h):
        return _carbon
    surf = pygame.Surface((w, h))
    surf.fill(BG)
    t = 8
    a = (24, 25, 29)
    b = (14, 15, 18)
    for gy in range(0, h, t):
        for gx in range(0, w, t):
            light = ((gx // t) + (gy // t)) % 2 == 0
            pygame.draw.rect(surf, a if light else b, (gx, gy, t, t))
            if light:
                pygame.draw.line(surf, (40, 42, 48), (gx, gy + t), (gx + t, gy), 1)
            else:
                pygame.draw.line(surf, (8, 9, 11), (gx, gy), (gx + t, gy + t), 1)
    _carbon = surf
    return surf


def draw_text(surf, text, font, color, **anchors):
    """Render text and position via any pygame.Rect anchor kwargs
    (center=, topleft=, topright=, midtop=, midleft=, bottomleft= ...)."""
    s = font.render(str(text), True, color)
    r = s.get_rect()
    for k, v in anchors.items():
        setattr(r, k, v)
    surf.blit(s, r)
    return r


def panel(surf, rect, radius=10):
    pygame.draw.rect(surf, PANEL, rect, border_radius=radius)
    pygame.draw.rect(surf, PANEL_BORDER, rect, width=1, border_radius=radius)


# ---- Status thresholds (colour + danger/flash flag) ----
def fuel_status(pct):
    if pct <= 12:
        return "red", True
    if pct <= 25:
        return "amber", False
    return "green", False


def cht_status(t, amber=195, red=215):
    if t >= red + 8:
        return "red", True
    if t >= red:
        return "red", False
    if t >= amber:
        return "amber", False
    return "green", False


def afr_status(a):
    if a < 11.4 or a > 14.8:
        return "red", True
    if a < 12.5 or a > 13.8:
        return "amber", False
    return "green", False


def volt_status(v, running=True):
    if v > 15.2 or (running and v < 11.5):
        return "red", True
    if v < 12.2:
        return "amber", False
    if running and v >= 13.2:
        return "green", False
    return "amber", False


# ---- Units ----
def disp_speed(mph, units):
    return mph * 1.60934 if units == "kph" else mph


def disp_dist(mi, units):
    return mi * 1.60934 if units == "kph" else mi


def speed_unit(units):
    return "KM/H" if units == "kph" else "MPH"


def dist_unit(units):
    return "KM" if units == "kph" else "MI"


def fmt_time(sec):
    s = int(max(0, sec))
    h, m, ss = s // 3600, (s % 3600) // 60, s % 60
    return f"{h}:{m:02d}:{ss:02d}" if h > 0 else f"{m}:{ss:02d}"


def set_hw_brightness(pct):
    """Best-effort hardware backlight control on the Pi. Silently ignored
    on machines without a backlight sysfs interface (e.g. a laptop)."""
    for base in glob.glob("/sys/class/backlight/*"):
        try:
            with open(os.path.join(base, "max_brightness")) as fh:
                maxb = int(fh.read().strip())
            val = max(1, int(maxb * pct / 100))
            with open(os.path.join(base, "brightness"), "w") as fh:
                fh.write(str(val))
        except Exception:
            pass
