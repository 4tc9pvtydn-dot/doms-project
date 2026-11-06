"""
============================================================================
 HARDWARE HOOK  --  live sensor reads.
============================================================================
Each read_* returns a number, or None if that sensor isn't wired / its board
isn't found. None makes the dashboard fall back to the simulator for that
value, so you can bring hardware online one piece at a time. All hardware
libraries are imported lazily and guarded, so a missing board never crashes
the dashboard.

Wired via:
  GPS  -> UART (pins 8/10)              [implemented]
  AFR  -> ADS1115 A0 (0-5V + divider)   [implemented]
  Fuel -> ADS1115 A1 (resistive)        [implemented]
  Batt -> ADS1115 A2 (divider)          [implemented]
  CHT  -> MAX31855 K-type (SPI)         [implemented]
  RPM  -> GPIO pulse count              [implemented, gated by RPM_ENABLED]
============================================================================
"""
import time
from collections import deque
import config as cfg

try:
    import serial  # pyserial
except Exception:
    serial = None


class Sensors:
    def __init__(self):
        # GPS
        self.gps = None
        self._buf = b""
        self._speed_knots = None
        self._sats = None
        self._in_view = {}
        self._open_gps()
        # lazy hardware handles + "disabled after failure" flags
        self._ads = None
        self._ads_chans = {}
        self._ads_off = False
        self._cht = None
        self._cht_off = False
        self._rpm = None
        self._rpm_off = False
        self._rpm_times = deque(maxlen=2000)
        self.rpm_hz = 0.0
        self._ign = None
        self._ign_off = False

    def status(self):
        """Per-sensor LIVE / SIM / OFF for the Settings page."""
        def st(handle, failed):
            return "SIM" if failed else ("LIVE" if handle is not None else "...")
        return [
            ("GPS", f"{self._sats or 0}/{sum(self._in_view.values())}" if self.gps is not None else "SIM"),
            ("ADC", st(self._ads, self._ads_off)),
            ("CHT", st(self._cht, self._cht_off)),
            ("RPM", "OFF" if not cfg.RPM_ENABLED else st(self._rpm, self._rpm_off)),
        ]
    # ------------------------------------------------------------- GPS
    def _open_gps(self):
        if serial is None:
            print("[sensors] pyserial not installed - GPS disabled")
            return
        try:
            self.gps = serial.Serial(cfg.GPS_PORT, cfg.GPS_BAUD, timeout=0)
            print(f"[sensors] GPS open on {cfg.GPS_PORT} @ {cfg.GPS_BAUD}")
        except Exception as e:
            self.gps = None
            print(f"[sensors] GPS not available ({e}) - using simulation")

    def _pump_gps(self):
        if self.gps is None:
            return
        try:
            data = self.gps.read(512)
        except Exception:
            return
        if not data:
            return
        self._buf += data
        while b"\n" in self._buf:
            line, self._buf = self._buf.split(b"\n", 1)
            self._parse(line.decode("ascii", "ignore").strip())

    def _parse(self, line):
        if not line.startswith("$"):
            return
        p = line.split(",")
        talker = p[0][3:]  # RMC / GGA (handles GP, GN, GL... prefixes)
        try:
            if talker == "RMC" and len(p) > 7:
                if p[2] == "A" and p[7] != "":
                    self._speed_knots = float(p[7])
                else:
                    self._speed_knots = 0.0
            elif talker == "GGA" and len(p) > 7:
                self._sats = int(p[7]) if p[7] != "" else 0
            elif talker == "GSV" and len(p) > 3 and p[3] != "":
                self._in_view[p[0][1:3]] = int(p[3])  # satellites heard, per system
        except (ValueError, IndexError):
            pass

    def read_speed_mph(self):
        if self.gps is None:
            return None
        self._pump_gps()
        if self._speed_knots is None:
            return 0.0
        return self._speed_knots * 1.15078

    def read_satellites(self):
        if self.gps is None:
            return None
        self._pump_gps()
        return self._sats if self._sats is not None else 0

    # --------------------------------------------------- ADS1115 (analog)
    def _ads_chan(self, chn):
        if self._ads_off:
            return None
        try:
            if self._ads is None:
                import board
                import busio
                import adafruit_ads1x15.ads1115 as ADS
                self._ADS = ADS
                i2c = busio.I2C(board.SCL, board.SDA)
                self._ads = ADS.ADS1115(i2c)
            if chn not in self._ads_chans:
                try:
                    from adafruit_ads1x15.analog_in import AnalogIn
                except ImportError:
                    from adafruit_ads1x15 import AnalogIn
                # library v2 uses ADS.P0..P3, v3+ uses plain channel numbers / Pin.A0..A3
                pin = getattr(self._ADS, f"P{chn}", chn)
                self._ads_chans[chn] = AnalogIn(self._ads, pin)
            return self._ads_chans[chn]
        except Exception as e:
            self._ads_off = True
            print(f"[sensors] ADS1115 not available ({e}) - AFR/fuel/battery simulated")
            return None

    def read_afr(self):
        ch = self._ads_chan(cfg.AFR_ADC_CH)
        if ch is None:
            return None
        try:
            v = ch.voltage * cfg.AFR_DIVIDER   # reconstruct the 0-5V signal
            return cfg.AFR_V0 + (v / 5.0) * (cfg.AFR_V5 - cfg.AFR_V0)
        except Exception:
            return None

    def read_fuel_pct(self):
        ch = self._ads_chan(cfg.FUEL_ADC_CH)
        if ch is None:
            return None
        try:
            v = ch.voltage
            denom = 3.3 - v
            if denom <= 0.05:
                return 0.0  # open circuit (sender unplugged / no ground) -> show empty
            rs = cfg.FUEL_REF_OHMS * v / denom
            span = (cfg.FUEL_OHMS_FULL - cfg.FUEL_OHMS_EMPTY)
            if span == 0:
                return None
            pct = (rs - cfg.FUEL_OHMS_EMPTY) / span * 100.0
            return max(0.0, min(100.0, pct))
        except Exception:
            return None

    def read_voltage(self):
        ch = self._ads_chan(cfg.BATT_ADC_CH)
        if ch is None:
            return None
        try:
            return ch.voltage * cfg.BATT_DIVIDER
        except Exception:
            return None

    # --------------------------------------------------- MAX31855 (CHT)
    def read_cht(self):
        if self._cht_off:
            return None
        try:
            if self._cht is None:
                import board
                import digitalio
                import adafruit_max31855
                cs = digitalio.DigitalInOut(getattr(board, cfg.CHT_CS_PIN))
                self._cht = adafruit_max31855.MAX31855(board.SPI(), cs)
            return self._cht.temperature
        except Exception as e:
            self._cht_off = True
            print(f"[sensors] MAX31855 not available ({e}) - CHT simulated")
            return None

    # --------------------------------------------------- RPM (gated)
    def read_rpm(self):
        if not cfg.RPM_ENABLED or self._rpm_off:
            return None
        try:
            if self._rpm is None:
                from gpiozero import DigitalInputDevice
                dev = DigitalInputDevice(cfg.RPM_GPIO, pull_up=getattr(cfg, "RPM_PULL_UP", False))

                ppr = max(0.1, cfg.RPM_PULSES_PER_REV)
                min_gap = 60.0 / (cfg.RPM_MAX_VALID * ppr)  # faster than this = electrical noise

                def _tick():
                    t = time.monotonic()
                    if self._rpm_times and t - self._rpm_times[-1] < min_gap:
                        return
                    self._rpm_times.append(t)

                dev.when_activated = _tick
                self._rpm = dev
            # average over a rolling window instead of per-frame counts
            now = time.monotonic()
            win = cfg.RPM_WINDOW
            while self._rpm_times and now - self._rpm_times[0] > win:
                self._rpm_times.popleft()
            ts = list(self._rpm_times)
            if len(ts) < 2 or now - ts[-1] > 0.5:
                self.rpm_hz = 0.0
                return 0.0
            self.rpm_hz = (len(ts) - 1) / (ts[-1] - ts[0])
            return self.rpm_hz * 60.0 / max(0.1, cfg.RPM_PULSES_PER_REV)
        except Exception as e:
            self._rpm_off = True
            print(f"[sensors] RPM input not available ({e}) - simulated")
            return None

    # --------------------------------------------------- IGNITION SENSE
    def ignition_on(self):
        """True = ignition on, False = off, None = sensing disabled/unavailable.
        A disconnected sense wire fails SAFE (reads ON) so it won't shut down."""
        if not cfg.IGNITION_SENSE_ENABLED or self._ign_off:
            return None
        try:
            if self._ign is None:
                from gpiozero import DigitalInputDevice
                self._ign = DigitalInputDevice(
                    cfg.IGNITION_GPIO, pull_up=cfg.IGNITION_ACTIVE_HIGH
                )
            val = bool(self._ign.value)
            return val if cfg.IGNITION_ACTIVE_HIGH else (not val)
        except Exception as e:
            self._ign_off = True
            print(f"[sensors] ignition sense not available ({e})")
            return None
