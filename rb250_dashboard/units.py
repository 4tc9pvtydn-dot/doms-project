"""Display units (MPH / KM/H). Everything is stored in miles; this only
converts what's shown. The choice is saved in ~/.rb250/settings.json."""
import json
import os

KM = 1.609344
PATH = os.path.expanduser("~/.rb250/settings.json")
kmh = False


def load(path=None):
    global kmh, PATH
    PATH = path or PATH
    try:
        with open(PATH) as fh:
            kmh = json.load(fh).get("units") == "kmh"
    except Exception:
        kmh = False


def toggle():
    global kmh
    kmh = not kmh
    try:
        os.makedirs(os.path.dirname(PATH), exist_ok=True)
        with open(PATH, "w") as fh:
            json.dump({"units": "kmh" if kmh else "mph"}, fh)
    except Exception as e:
        print(f"[units] could not save ({e})")


def spd(mph):
    return None if mph is None else (mph * KM if kmh else mph)


def dist(mi):
    return mi * KM if kmh else mi


def spd_label():
    return "KM/H" if kmh else "MPH"


def dist_label():
    return "KM" if kmh else "MI"


def dial_max():
    """Top of the speedo: 100 mph or 160 km/h."""
    return 160 if kmh else 100
