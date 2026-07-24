"""
DOMS RB252 Dashboard - configuration.

Edit these values to change behaviour on the Pi.
"""

# --- Engine / display tuning ---
REDLINE = 8500          # RPM at which the bar is full / redline
SHIFT_RPM = 7800        # RPM at which the shift-light starts flashing

# --- Data source ---
# False = built-in realistic simulator (great for the bench / VS Code).
# True  = read live values from sensors.py (wire your hardware there).
USE_REAL_SENSORS = False

# --- Power ---
# True  = the SHUTDOWN button actually powers the Pi off (`sudo shutdown -h now`).
#         Requires a passwordless sudo rule (see README).
# False = SHUTDOWN just shows a "SYSTEM HALTED" screen (safe for laptop testing).
ALLOW_SHUTDOWN = False

# --- Native panel resolution (Waveshare 3.5" DSI) ---
WIDTH = 640
HEIGHT = 480
