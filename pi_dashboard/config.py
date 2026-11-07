"""
DOMS RB252 Dashboard - configuration & sensor calibration.
"""

# --- Engine / display tuning ---
REDLINE = 8500
SHIFT_RPM = 7800

# --- Data source ---
# True = read live sensors where wired; anything returning None stays simulated,
# so you can bring hardware online one sensor at a time.
USE_REAL_SENSORS = True

# --- GPS (UART) ---
GPS_PORT = "/dev/serial0"   # Pi UART (GPIO14/15, pins 8/10)
GPS_BAUD = 9600

# ======================================================================
#  ADS1115 analog inputs  (AFR, fuel, battery)  - I2C: SDA pin3, SCL pin5
# ======================================================================
AFR_ADC_CH = 0     # ADS1115 A0
FUEL_ADC_CH = 1    # ADS1115 A1
BATT_ADC_CH = 2    # ADS1115 A2

# Arduino 0-25V voltage sensor module (30k/7.5k) -> ratio 5.0
BATT_DIVIDER = 5.0

# AFR: 0-5V controller output -> divider into the ADS (max 3.3V).
# Example R1=10k, R2=20k -> measured = Vafr*20/30 = Vafr*0.667 -> AFR_DIVIDER = 1.5
AFR_DIVIDER = 1.5
AFR_V0 = 10.0      # AFR that 0V represents  (check your controller!)
AFR_V5 = 20.0      # AFR that 5V represents

# Fuel: resistive sender. Wiring: 3.3V -- Rref -- [node -> ADS A1] -- sender -- GND
FUEL_REF_OHMS = 100.0     # the fixed reference resistor you fit
FUEL_OHMS_EMPTY = 240.0   # sender ohms when EMPTY
FUEL_OHMS_FULL = 33.0     # sender ohms when FULL

# ======================================================================
#  MAX31855 K-type thermocouple (CHT) - SPI: MOSI/MISO/SCLK + a CS pin
# ======================================================================
CHT_CS_PIN = "D5"          # chip-select (BCM5 = physical pin 29)

# ======================================================================
#  RPM pickup  (KEEP OFF until a safe conditioning circuit is built!)
# ======================================================================
RPM_ENABLED = True         # opto module on pin 11 (OUT) + Pi GND
RPM_GPIO = 17              # BCM17 = physical pin 11
RPM_MAX_VALID = 12000      # pulses faster than this rpm are ignored as noise
RPM_WINDOW = 0.3           # seconds of pulses averaged per reading
RPM_GLITCH = 0.6           # ignore a pulse arriving sooner than 60% of the last gap (stator noise)
RPM_MAX_RISE = 15000       # max displayed rev rise per second (stops instant spikes)
RPM_SMOOTH = 0.25          # display smoothing time (s); higher = steadier
FUEL_SMOOTH = 8.0          # fuel smoothing time (s) - stops slosh flicker
RPM_PULL_UP = True         # Pi's built-in 3.3V pull-up on pin 11 (no external resistor/VCC needed)
RPM_PULSES_PER_REV = 1     # HT-lead wrap pickup: 1 spark per rev (single-cyl 2-stroke)

# ======================================================================
#  IGNITION SENSE -> graceful auto power-off when the bike is switched off
# ======================================================================
IGNITION_SENSE_ENABLED = False   # set True once the sense circuit is wired
IGNITION_GPIO = 27               # BCM27 = physical pin 13
IGNITION_ACTIVE_HIGH = True      # True: pin HIGH when ignition ON
                                 # False: for an opto that pulls the pin LOW when ON
IGNITION_OFF_DELAY = 3.0         # seconds OFF before shutdown (ignores stalls/dips)

# ======================================================================
#  POWER-LOSS SHUTDOWN via the voltage sensor (no extra parts!)
#  Wire the 0-25V sensor (ADS1115 A2) to the SWITCHED 12V feed. When you
#  switch off, that line drops to ~0V; the dashboard sees the voltage
#  collapse and shuts down cleanly while the 5V backup holds it up.
# ======================================================================
POWER_LOSS_SHUTDOWN = False      # set True once the backup + switched feed are wired
POWER_LOSS_VOLTS = 6.0           # below this = main power lost (12V system)

# --- Power ---
ALLOW_SHUTDOWN = True

# --- Native panel resolution (Waveshare 3.5" DSI (E)) ---
WIDTH = 640
HEIGHT = 480
