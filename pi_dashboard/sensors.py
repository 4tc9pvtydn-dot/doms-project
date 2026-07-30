"""
============================================================================
 HARDWARE HOOK  --  wire your real sensors here.
============================================================================
Each read_* method returns ONE number, or None if that sensor isn't wired
yet. Any method returning None makes the dashboard fall back to the simulator
for that value, so you can bring hardware online one piece at a time.

Currently implemented:  GPS speed + satellites (UART, NMEA).
Still to wire:          RPM, CHT, AFR, fuel, battery voltage.
============================================================================
"""
import config as cfg

try:
    import serial  # pyserial
except Exception:
    serial = None


class Sensors:
    def __init__(self):
        self.gps = None
        self._buf = b""
        self._speed_knots = None   # None until first valid fix
        self._sats = None
        self._open_gps()

    # ------------------------------------------------------------------ GPS
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
        """Read whatever bytes are waiting and parse complete NMEA lines."""
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
        talker = p[0][3:]  # e.g. RMC, GGA (handles GP/GN prefixes)
        try:
            if talker == "RMC" and len(p) > 7:
                status = p[2]
                if status == "A" and p[7] != "":
                    self._speed_knots = float(p[7])
                else:
                    self._speed_knots = 0.0
            elif talker == "GGA" and len(p) > 7:
                self._sats = int(p[7]) if p[7] != "" else 0
        except (ValueError, IndexError):
            pass

    def read_speed_mph(self):
        if self.gps is None:
            return None                      # not wired -> simulate
        self._pump_gps()
        if self._speed_knots is None:
            return 0.0                       # module present, no fix yet
        return self._speed_knots * 1.15078

    def read_satellites(self):
        if self.gps is None:
            return None
        self._pump_gps()
        return self._sats if self._sats is not None else 0

    # ---------------------------------------------------- not wired yet
    def read_rpm(self):
        return None

    def read_cht(self):
        return None

    def read_afr(self):
        return None

    def read_fuel_pct(self):
        return None

    def read_voltage(self):
        return None
