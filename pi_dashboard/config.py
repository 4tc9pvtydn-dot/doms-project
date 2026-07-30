"""
DOMS RB252 Dashboard - configuration.
"""

# --- Engine / display tuning ---
REDLINE = 8500          # RPM at which the bar is full / redline
SHIFT_RPM = 7800        # RPM at which the shift-light starts flashing

# --- Data source ---
# True  = read live values from sensors.py where available.
#         Any sensor method that returns None falls back to the simulator,
#         so you can bring hardware online one sensor at a time.
# False = full simulation (great for the bench / VS Code).
USE_REAL_SENSORS = True

# --- GPS (UART) ---
GPS_PORT = "/dev/serial0"   # Pi UART (GPIO14/15, pins 8/10)
GPS_BAUD = 9600

# --- Power ---
# True  = the on-screen POWER OFF actually shuts the Pi down.
#         install.sh adds the passwordless sudo rule for this.
# False = POWER OFF just shows a "SYSTEM HALTED" screen (safe for laptop).
ALLOW_SHUTDOWN = True

# --- Native panel resolution (Waveshare 3.5" DSI (E)) ---
WIDTH = 640
HEIGHT = 480
