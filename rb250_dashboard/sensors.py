"""
Live sensor reads. Every read_* returns a number, or None when that sensor
isn't connected / stops answering (the screen then shows "--").
Failed hardware is retried every few seconds, so plugging a sensor back in
recovers without a restart. Hardware libraries are imported lazily.

  GPS  -> UART pins 8/10           Fuel -> ADS1115 A1
  CHT  -> MAX31855 (SPI, CS pin 29) Batt -> ADS1115 A2 (switched 12V)
  RPM  -> opto OUT on pin 11
"""
import time
from collections import deque
import config as cfg

try:
    import serial  # pyserial
except Exception:
    serial = None

RETRY_SECS = 5.0


class Sensors:
    def __init__(self):
        self.gps = None
        self._buf = b""
        self._speed_knots = None
        self._fix = False
        self._sats = 0
        self._in_view = {}
        self._gps_last = 0.0
        self._gps_retry = 0.0
        self._ads = None
        self._ads_chans = {}
        self._ads_retry = 0.0
        self._cht = None
        self._cht_retry = 0.0
        self._rpm = None
        self._rpm_off = False
        self._rpm_times = deque(maxlen=2000)
        self._rpm_ref = None
        self.rpm_hz = 0.0
        self.rpm_rejects = 0
        self._ups_bus = None
        self._ups_retry = 0.0
        self.errors = {}
        self._open_gps()

    def _fail(self, name, e):
        msg = " ".join(str(e).split())[:140]
        if self.errors.get(name) != msg:
            print(f"[sensors] {name} not available ({msg})")
        self.errors[name] = msg

    def _ok(self, name):
        if name in self.errors:
            print(f"[sensors] {name} OK")
            del self.errors[name]

    # ------------------------------------------------------------- GPS
    def _open_gps(self):
        if serial is None:
            self._fail("GPS", "pyserial not installed")
            return
        try:
            self.gps = serial.Serial(cfg.GPS_PORT, cfg.GPS_BAUD, timeout=0)
            self._gps_last = time.monotonic()
            print(f"[sensors] GPS port open {cfg.GPS_PORT} @ {cfg.GPS_BAUD}")
        except Exception as e:
            self.gps = None
            self._gps_retry = time.monotonic() + RETRY_SECS
            self._fail("GPS", e)

    def _pump_gps(self):
        if self.gps is None:
            if time.monotonic() > self._gps_retry:
                self._open_gps()
            return
        try:
            data = self.gps.read(1024)
        except Exception as e:
            self._fail("GPS", e)
            self.gps = None
            self._gps_retry = time.monotonic() + RETRY_SECS
            return
        if not data:
            return
        self._buf = (self._buf + data)[-4096:]
        while b"\n" in self._buf:
            line, self._buf = self._buf.split(b"\n", 1)
            self._parse(line.decode("ascii", "ignore").strip())

    def _parse(self, line):
        if not line.startswith("$") or len(line) < 7:
            return
        p = line.split(",")
        kind = p[0][3:6]
        try:
            if kind == "RMC" and len(p) > 7:
                self._gps_last = time.monotonic()
                self._fix = p[2] == "A"
                self._speed_knots = float(p[7]) if (self._fix and p[7]) else 0.0
            elif kind == "GGA" and len(p) > 7:
                self._gps_last = time.monotonic()
                self._sats = int(p[7]) if p[7] else 0
            elif kind == "GSV" and len(p) > 3 and p[3]:
                self._in_view[p[0][1:3]] = int(p[3])
        except (ValueError, IndexError):
            pass

    def gps_state(self):
        """('none'|'search'|'fix', sats_used, sats_heard)."""
        self._pump_gps()
        heard = sum(self._in_view.values())
        if self.gps is None or time.monotonic() - self._gps_last > cfg.GPS_STALE_SECS:
            return "none", 0, 0
        if self._fix:
            self._ok("GPS")
            return "fix", self._sats, heard
        return "search", self._sats, heard

    def read_speed_mph(self):
        state, _, _ = self.gps_state()
        if state != "fix" or self._speed_knots is None:
            return None
        return self._speed_knots * 1.15078

    # --------------------------------------------------- ADS1115 (analog)
    def _ads_volts(self, chn):
        if self._ads is None:
            if time.monotonic() < self._ads_retry:
                return None
            try:
                import board
                import busio
                import adafruit_ads1x15.ads1115 as ADS
                self._ADS = ADS
                self._ads = ADS.ADS1115(busio.I2C(board.SCL, board.SDA))
                self._ads_chans = {}
            except Exception as e:
                self._ads = None
                self._ads_retry = time.monotonic() + RETRY_SECS
                self._fail("ADS1115", e)
                return None
        try:
            if chn not in self._ads_chans:
                try:
                    from adafruit_ads1x15.analog_in import AnalogIn
                except ImportError:
                    from adafruit_ads1x15 import AnalogIn
                pin = getattr(self._ADS, f"P{chn}", chn)  # lib v2 = P0.., v3 = 0..
                self._ads_chans[chn] = AnalogIn(self._ads, pin)
            v = self._ads_chans[chn].voltage
            self._ok("ADS1115")
            return v
        except Exception as e:
            self._ads = None
            self._ads_retry = time.monotonic() + RETRY_SECS
            self._fail("ADS1115", e)
            return None

    def read_fuel_pct(self):
        v = self._ads_volts(cfg.FUEL_ADC_CH)
        if v is None:
            return None
        if v > 3.2 or v < 0.05:
            self._fail("FUEL", f"sender open/short ({v:.2f}V on A1)")
            return None
        self._ok("FUEL")
        rs = cfg.FUEL_REF_OHMS * v / (3.3 - v)
        pct = (rs - cfg.FUEL_OHMS_EMPTY) / (cfg.FUEL_OHMS_FULL - cfg.FUEL_OHMS_EMPTY) * 100.0
        return max(0.0, min(100.0, pct))

    def read_voltage(self):
        v = self._ads_volts(cfg.BATT_ADC_CH)
        return None if v is None else v * cfg.BATT_DIVIDER

    # --------------------------------------------------- MAX31855 (CHT)
    def read_cht(self):
        if self._cht is None:
            if time.monotonic() < self._cht_retry:
                return None
            try:
                import board
                import digitalio
                import adafruit_max31855
                cs = digitalio.DigitalInOut(getattr(board, cfg.CHT_CS_PIN))
                self._cht = adafruit_max31855.MAX31855(board.SPI(), cs)
            except Exception as e:
                self._cht_retry = time.monotonic() + RETRY_SECS
                self._fail("CHT", e)
                return None
        try:
            t = self._cht.temperature  # raises if the thermocouple is unplugged
            self._ok("CHT")
            return t
        except Exception as e:
            self._fail("CHT", e)
            return None

    # --------------------------------------------------- RPM
    def read_rpm(self):
        if not cfg.RPM_ENABLED or self._rpm_off:
            return None
        try:
            if self._rpm is None:
                from gpiozero import DigitalInputDevice
                dev = DigitalInputDevice(cfg.RPM_GPIO, pull_up=cfg.RPM_PULL_UP)
                ppr = max(0.1, cfg.RPM_PULSES_PER_REV)
                min_gap = 60.0 / (cfg.RPM_MAX_VALID * ppr)

                def _tick():
                    t = time.monotonic()
                    if self._rpm_times:
                        gap = t - self._rpm_times[-1]
                        if gap < min_gap:
                            return
                        if self._rpm_ref and gap < cfg.RPM_GLITCH * self._rpm_ref:
                            self._rpm_ref *= 0.85
                            self.rpm_rejects += 1
                            return
                        self._rpm_ref = gap if gap < 0.5 else None
                    self._rpm_times.append(t)

                dev.when_activated = _tick
                self._rpm = dev
                self._ok("RPM")
        except Exception as e:
            self._rpm_off = True
            self._fail("RPM", e)
            return None
        now = time.monotonic()
        while self._rpm_times and now - self._rpm_times[0] > cfg.RPM_WINDOW:
            self._rpm_times.popleft()
        ts = list(self._rpm_times)
        if len(ts) < 2 or now - ts[-1] > 0.5:
            self.rpm_hz = 0.0
            return 0.0  # engine stopped
        self.rpm_hz = (len(ts) - 1) / (ts[-1] - ts[0])
        return self.rpm_hz * 60.0 / max(0.1, cfg.RPM_PULSES_PER_REV)

    # --------------------------------------------------- UPS HAT (INA219)
    def read_ups(self):
        """(battery_volts, percent) from the UPS HAT, or None."""
        if not cfg.UPS_ENABLED:
            return None
        if self._ups_bus is None:
            if time.monotonic() < self._ups_retry:
                return None
            try:
                from smbus2 import SMBus
                self._ups_bus = SMBus(1)
            except Exception as e:
                self._ups_retry = time.monotonic() + RETRY_SECS
                self._fail("UPS", e)
                return None
        try:
            raw = self._ups_bus.read_word_data(cfg.UPS_I2C_ADDR, 0x02)  # bus voltage
            raw = ((raw & 0xFF) << 8) | (raw >> 8)
            volts = (raw >> 3) * 0.004
            pct = (volts - cfg.UPS_EMPTY_V) / (cfg.UPS_FULL_V - cfg.UPS_EMPTY_V) * 100
            self._ok("UPS")
            return volts, max(0.0, min(100.0, pct))
        except Exception as e:
            self._ups_retry = time.monotonic() + RETRY_SECS
            self._fail("UPS", e)
            return None

    # --------------------------------------------------- status
    def status(self):
        st, used, heard = self.gps_state()
        gps = {"none": "NONE", "search": f"{used}/{heard}", "fix": f"{used}/{heard}"}[st]
        return [
            ("GPS", gps, st == "fix"),
            ("ADC", "LIVE" if self._ads is not None else "NONE", self._ads is not None),
            ("CHT", "NONE" if "CHT" in self.errors or self._cht is None else "LIVE",
             "CHT" not in self.errors and self._cht is not None),
            ("RPM", "OFF" if not cfg.RPM_ENABLED else ("NONE" if self._rpm_off else "LIVE"),
             cfg.RPM_ENABLED and not self._rpm_off),
            ("UPS", "NONE" if "UPS" in self.errors else "LIVE", "UPS" not in self.errors),
        ]
