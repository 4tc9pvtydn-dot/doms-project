"""
============================================================================
 HARDWARE HOOK  --  wire your real sensors here.
============================================================================
Set  USE_REAL_SENSORS = True  in config.py, then fill in each read_* method
below with the code that talks to your hardware. Each method must return a
single number in the units shown. Until you implement one, it returns a safe
placeholder so the dashboard keeps running.

Suggested libraries (install into the venv as needed):
  GPS speed / sats : pyserial + pynmea2   (USB or UART GPS -> /dev/serial0)
  RPM pickup       : gpiozero / pigpio     (count pulses on a GPIO pin)
  CHT thermocouple : adafruit-circuitpython-max31855  (SPI, K-type)
  AFR controller   : analog 0-5V -> ADS1115 (adafruit-circuitpython-ads1x15)
  Fuel sender      : resistive -> voltage divider -> ADS1115
  Battery voltage  : voltage divider -> ADS1115
============================================================================
"""


class Sensors:
    def __init__(self):
        # TODO: open serial ports / SPI / I2C buses here, e.g.
        # import serial; self.gps = serial.Serial("/dev/serial0", 9600, timeout=0)
        pass

    # --- GPS -----------------------------------------------------------
    def read_speed_mph(self):
        # TODO: parse NMEA $GPRMC/$GPVTG speed, convert knots->mph (*1.15078)
        return 0.0

    def read_satellites(self):
        # TODO: parse $GPGGA satellite count
        return 0

    # --- RPM pickup ----------------------------------------------------
    def read_rpm(self):
        # TODO: pulses_per_sec * 60 / pulses_per_rev
        return 0.0

    # --- Cylinder head temperature (deg C) -----------------------------
    def read_cht(self):
        # TODO: return max31855.temperature
        return 0.0

    # --- Air/Fuel ratio ------------------------------------------------
    def read_afr(self):
        # TODO: map controller analog voltage to AFR (e.g. 0-5V -> 10-20 AFR)
        return 13.0

    # --- Fuel level (percent 0-100) ------------------------------------
    def read_fuel_pct(self):
        # TODO: map sender resistance/voltage to 0-100 (calibrate empty/full)
        return 50.0

    # --- Battery voltage (volts) ---------------------------------------
    def read_voltage(self):
        # TODO: adc_voltage * divider_ratio
        return 12.6
