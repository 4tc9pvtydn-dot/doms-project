"""
Live telemetry: polls sensors at sensible rates, smooths noisy readings and
keeps trip / odometer miles (saved to disk so they survive power-off).
Every value is None when its sensor isn't giving a reading.
"""
import json
import os
import subprocess
import time
import config as cfg
from rides import RideLog

ODO_PATH = os.path.expanduser(cfg.ODO_FILE)
SAVE_EVERY = 30.0


class Telemetry:
    def __init__(self, sensors):
        self.sensors = sensors
        self.speed = self.rpm = self.cht = self.fuel = self.volt = None
        self.gps = ("none", 0, 0)
        self.ups = None  # (volts, pct)
        self.peak_rpm = 0.0
        self._prev = {}
        self._next = {"ads": 0.0, "cht": 0.0, "ups": 0.0}
        self._last_save = time.monotonic()
        self._dirty = False
        self.odo, self.trip = self._load()
        self.rides = RideLog()
        self._next_clock = 0.0

    # ---------------- miles persistence
    def _load(self):
        try:
            with open(ODO_PATH) as fh:
                d = json.load(fh)
            return float(d.get("odo", cfg.ODO_START)), float(d.get("trip", 0.0))
        except Exception:
            return float(cfg.ODO_START), 0.0

    def save(self):
        tmp = ODO_PATH + ".tmp"
        try:
            os.makedirs(os.path.dirname(ODO_PATH), exist_ok=True)
            with open(tmp, "w") as fh:
                json.dump({"odo": round(self.odo, 3), "trip": round(self.trip, 3)}, fh)
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp, ODO_PATH)
            self._dirty = False
        except Exception as e:
            print(f"[telemetry] could not save miles ({e})")
        self.rides.save()

    def _sync_clock(self, now):
        """No Wi-Fi on the bike: set the Pi's clock from GPS time."""
        if now < self._next_clock:
            return
        self._next_clock = now + 60
        g = self.sensors.gps_time() if hasattr(self.sensors, "gps_time") else None
        if g is None or abs(g - time.time()) < 30:
            return
        before = time.time()
        try:
            r = subprocess.run(["sudo", "-n", "date", "-u", "-s", f"@{int(g)}"],
                               capture_output=True, timeout=5)
            if r.returncode == 0:
                self.rides.clock_fixed(time.time() - before)
                print("[telemetry] clock set from GPS")
        except Exception as e:
            print(f"[telemetry] could not set clock ({e})")

    def reset_trip(self):
        self.trip = 0.0
        self.peak_rpm = 0.0
        self.save()

    # ---------------- helpers
    def _smooth(self, key, v, dt, tau):
        if v is None:
            self._prev.pop(key, None)
            return None
        prev = self._prev.get(key)
        out = v if prev is None or tau <= 0 else prev + (v - prev) * min(1.0, dt / tau)
        self._prev[key] = out
        return out

    def _due(self, key, period, now):
        if now >= self._next[key]:
            self._next[key] = now + period
            return True
        return False

    # ---------------- main update
    def update(self, dt):
        s = self.sensors
        now = time.monotonic()
        self.gps = s.gps_state()
        self.speed = s.read_speed_mph()

        r = s.read_rpm()
        if r is not None and self._prev.get("rpm") is not None:
            r = min(r, self._prev["rpm"] + cfg.RPM_MAX_RISE * dt)
        self.rpm = self._smooth("rpm", r, dt, cfg.RPM_SMOOTH)
        if self.rpm is not None:
            self.peak_rpm = max(self.peak_rpm, self.rpm)

        if self._due("ads", 0.2, now):
            self.fuel = self._smooth("fuel", s.read_fuel_pct(), 0.2, cfg.FUEL_SMOOTH)
            self.volt = self._smooth("volt", s.read_voltage(), 0.2, 0.4)
        if self._due("cht", 0.25, now):
            self.cht = s.read_cht()
        if self._due("ups", 2.0, now):
            self.ups = s.read_ups()

        if self.speed is not None and self.speed >= cfg.MIN_MOVING_MPH:
            mi = self.speed * dt / 3600.0
            self.odo += mi
            self.trip += mi
            self._dirty = True
        self.rides.update(self, dt)
        self._sync_clock(now)
        if self._dirty and now - self._last_save > SAVE_EVERY:
            self._last_save = now
            self.save()
