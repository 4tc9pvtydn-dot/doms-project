"""
RB250 Dashboard - configuration & sensor calibration (Pi Zero 2 W).
Edit values here, then:  sudo systemctl restart rb250-dashboard
"""

# --- Rev counter ---
REDLINE = 8500
SHIFT_RPM = 7800
RPM_SCALE_MAX = 10000

# --- Colour limits (traffic lights) ---
CHT_AMBER = 180        # degC: green below, amber from here
CHT_RED = 210          # degC: red (danger) above
FUEL_RED = 15          # %: red below
FUEL_AMBER = 50        # %: amber below, green from here to full
VOLT_LOW = 11.8        # V: amber below
VOLT_HIGH = 15.0       # V: red above (charging fault)

# --- GPS (UART pins 8/10) ---
GPS_PORT = "/dev/serial0"
GPS_BAUD = 9600
GPS_STALE_SECS = 3.0   # no GPS sentence for this long = GPS lost

# ======================================================================
#  ADS1115 analog inputs - I2C: SDA pin 3, SCL pin 5
# ======================================================================
FUEL_ADC_CH = 1    # A1: fuel sender (3.3V -[100R]- node -> A1, sender to GND)
BATT_ADC_CH = 2    # A2: 0-25V voltage sensor on the SWITCHED 12V
BATT_DIVIDER = 5.0

FUEL_REF_OHMS = 100.0
FUEL_OHMS_EMPTY = 240.0
FUEL_OHMS_FULL = 33.0
FUEL_SMOOTH = 8.0          # seconds - stops slosh flicker

# ======================================================================
#  MAX31855 K-type thermocouple (CHT) - SPI, CS on pin 29 (BCM5)
# ======================================================================
CHT_CS_PIN = "D5"

# ======================================================================
#  RPM - opto module OUT -> pin 11 (BCM17), GND -> Pi GND, HT-lead wrap
# ======================================================================
RPM_ENABLED = True
RPM_GPIO = 17
RPM_PULL_UP = True         # Pi's built-in 3.3V pull-up (no external resistor)
RPM_PULSES_PER_REV = 1     # HT-lead pickup: 1 spark per rev
RPM_MAX_VALID = 12000      # faster pulses = noise
RPM_WINDOW = 0.3           # seconds of pulses averaged
RPM_GLITCH = 0.6           # ignore a pulse sooner than 60% of the last gap
RPM_MAX_RISE = 15000       # max displayed rise per second
RPM_SMOOTH = 0.25

# ======================================================================
#  AUTO SHUTDOWN (UPS HAT keeps the Pi alive; the voltage sensor on the
#  switched 12V drops when the engine/ignition is switched off)
# ======================================================================
POWER_LOSS_SHUTDOWN = True
POWER_LOSS_VOLTS = 6.0     # below this = ignition off
POWER_OFF_DELAY = 3.0      # seconds below before shutting down (ignores dips)
ALLOW_SHUTDOWN = True

# ======================================================================
#  UPS HAT (C) for Pi Zero - INA219 battery monitor on I2C 0x43
#  Wake: after shutdown the UPS keeps the Pi powered (halted). A short
#  low pulse on pin 5 at ignition-on starts it again (see WIRING.md).
# ======================================================================
UPS_ENABLED = True
UPS_I2C_ADDR = 0x43
UPS_EMPTY_V = 3.40        # battery volts = 0%
UPS_FULL_V = 4.15         # battery volts = 100%
UPS_LOW_PCT = 10          # on battery power and below this -> shut down safely

# --- Miles ---
ODO_FILE = "~/.rb250/odometer.json"   # kept outside the app folder: survives updates
ODO_START = 0.0                # set your bike's current mileage before first run
MIN_MOVING_MPH = 2.0           # ignore GPS drift when stopped

# --- Screen: uses whatever the screen reports (480x320, 800x480 ...) ---
DESIGN_W = 800
DESIGN_H = 480
FPS = 30
