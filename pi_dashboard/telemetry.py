"""
Telemetry engine.

- With config.USE_REAL_SENSORS = False it runs a realistic simulation so the
  dashboard is fully alive on the bench / in VS Code.
- With USE_REAL_SENSORS = True it pulls the core readings from sensors.py and
  still computes the derived values (trips, odo, peaks, 0-30/0-60/quarter...).
"""
import random
from config import REDLINE

# gear -> (min_mph, max_mph)
GEARS = [(1, 0, 9), (2, 9, 21), (3, 21, 39), (4, 39, 59), (5, 59, 92)]


def gear_for_speed(mph):
    if mph < 1.2:
        return 0
    for g, lo, hi in GEARS:
        if lo <= mph < hi:
            return g
    return 5


class Telemetry:
    def __init__(self, sensors=None, use_real=False):
        self.sensors = sensors
        self.use_real = use_real
        self.reset_all()

    def reset_all(self):
        self.speed = 0.0
        self.rpm = 1050.0
        self.gear = 0
        self.throttle = 0.0
        self.fuel = 64.0
        self.cht = 78.0
        self.afr = 13.2
        self.volt = 12.6
        self.sats = 9
        self.odo = 1245.0
        self.tripA = 0.0
        self.tripB = 0.0
        self.ride_time = 0.0
        self.runtime = 0.0
        self.avg = 0.0
        self.maxspeed = 0.0
        self.peakrpm = 1050.0
        self.peaktemp = 78.0
        self.bestspeed = 0.0
        self.fan = False
        self.a030 = None
        self.a060 = None
        self.quarter = None
        self._target = 0.0
        self._change = 0.0
        self._dist = 0.0
        self._launch = False
        self._lt = 0.0
        self._ld = 0.0

    def reset_trip(self, which):
        if which == "A":
            self.tripA = 0.0
        elif which == "B":
            self.tripB = 0.0
        elif which == "perf":
            self.a030 = self.a060 = self.quarter = None
            self.peakrpm = self.rpm
            self.peaktemp = self.cht
            self.maxspeed = 0.0
            self.bestspeed = 0.0

    def _simulate(self, dt):
        self._change -= dt
        if self._change <= 0:
            self._change = 2 + random.random() * 4
            r = random.random()
            if r < 0.15:
                self._target = 0
            elif r < 0.35:
                self._target = 20 + random.random() * 20
            else:
                self._target = 35 + random.random() * 48
        diff = self._target - self.speed
        rate = 9 if diff > 0 else 14
        self.throttle = max(0.0, min(1.0, diff / 30 + 0.15))
        self.speed += (1 if diff > 0 else -1) * min(abs(diff), rate * dt)
        if self.speed < 0.05:
            self.speed = 0.0

        g = gear_for_speed(self.speed)
        if g == 0:
            rpm = 1000 + random.random() * 120
        else:
            _, lo, hi = GEARS[g - 1]
            frac = (self.speed - lo) / (hi - lo)
            rpm = 2400 + frac * 5400 + (random.random() * 240 - 120) + self.throttle * 350
        self.rpm = max(900, min(REDLINE + 100, rpm))
        self.gear = g

        tgt = 70 + (self.rpm / REDLINE) * 135 + self.throttle * 15
        self.cht += (tgt - self.cht) * 0.02

        at = 13.2
        if self.throttle > 0.55:
            at = 12.4
        elif diff < -2:
            at = 14.2
        self.afr += (at - self.afr) * 0.12 + (random.random() * 0.1 - 0.05)

        vt = 14.1 if self.rpm > 1500 else 12.5
        self.volt += (vt - self.volt) * 0.05 + (random.random() * 0.04 - 0.02)

        if random.random() < 0.03:
            self.sats = max(4, min(12, self.sats + (-1 if random.random() < 0.5 else 1)))

    def _read_real(self, dt):
        s = self.sensors
        self.speed = s.read_speed_mph()
        self.rpm = s.read_rpm()
        self.cht = s.read_cht()
        self.afr = s.read_afr()
        self.fuel = s.read_fuel_pct()
        self.volt = s.read_voltage()
        self.sats = s.read_satellites()
        self.gear = gear_for_speed(self.speed)
        self.throttle = 0.0

    def update(self, dt):
        if self.use_real and self.sensors is not None:
            self._read_real(dt)
        else:
            self._simulate(dt)

        mi = self.speed * dt / 3600.0
        self._dist += mi
        self.odo += mi
        self.tripA += mi
        self.tripB += mi
        self.ride_time += dt
        if self.speed > 1 or self.gear > 0:
            self.runtime += dt
        if not self.use_real:
            self.fuel = max(0.0, self.fuel - mi * 0.9)

        self.fan = self.cht > 170
        self.maxspeed = max(self.maxspeed, self.speed)
        self.bestspeed = self.maxspeed
        self.peakrpm = max(self.peakrpm, self.rpm)
        self.peaktemp = max(self.peaktemp, self.cht)
        self.avg = self._dist / (self.ride_time / 3600.0) if self.ride_time > 0 else 0.0

        if self.speed < 0.6:
            self._launch = True
            self._lt = 0.0
            self._ld = 0.0
        elif self._launch:
            self._lt += dt
            self._ld += mi
            if self.speed >= 30 and self.a030 is None:
                self.a030 = self._lt
            if self.speed >= 60 and self.a060 is None:
                self.a060 = self._lt
            if self._ld >= 0.25 and self.quarter is None:
                self.quarter = self._lt

    def sample(self):
        return dict(
            speed=self.speed, rpm=self.rpm, gear=self.gear, throttle=self.throttle,
            fuel=self.fuel, cht=self.cht, afr=self.afr, volt=self.volt, sats=self.sats,
            odo=self.odo, tripA=self.tripA, tripB=self.tripB, ride_time=self.ride_time,
            runtime=self.runtime, avg=self.avg, maxspeed=self.maxspeed, peakrpm=self.peakrpm,
            peaktemp=self.peaktemp, bestspeed=self.bestspeed, fan=self.fan,
            a030=self.a030, a060=self.a060, quarter=self.quarter,
        )
