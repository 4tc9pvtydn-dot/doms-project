"""
Ride log: one ride = ignition on -> shutdown. Saved every 30s and at
shutdown to ~/.rb250/rides.json, plus rides.csv to open on a computer.
"""
import csv
import json
import os
import time

import config as cfg

MIN_RIDE_MILES = 0.1
KEEP = 500


class RideLog:
    def __init__(self, path=None):
        self.path = os.path.expanduser(path or cfg.RIDES_FILE)
        self.rides = self._load()
        self.cur = None
        self._started = time.time()

    def _load(self):
        try:
            with open(self.path) as fh:
                return json.load(fh)
        except Exception:
            return []

    def update(self, t, dt):
        """Fold the latest telemetry into the current ride."""
        if self.cur is None:
            self.cur = {"start": self._started, "miles": 0.0, "secs": 0.0, "top_mph": 0.0,
                        "peak_rpm": 0.0, "max_cht": None}
        c = self.cur
        c["secs"] += dt
        if t.speed is not None and t.speed >= cfg.MIN_MOVING_MPH:
            c["miles"] += t.speed * dt / 3600.0
            c["top_mph"] = max(c["top_mph"], t.speed)
        if t.rpm is not None:
            c["peak_rpm"] = max(c["peak_rpm"], t.rpm)
        if t.cht is not None:
            c["max_cht"] = t.cht if c["max_cht"] is None else max(c["max_cht"], t.cht)

    def clock_fixed(self, offset):
        """System clock was corrected (from GPS) - shift the ride start too."""
        self._started += offset
        if self.cur:
            self.cur["start"] += offset

    def history(self):
        """Saved rides plus the one in progress, newest first."""
        out = [r for r in self.rides if not self.cur or r["start"] != self.cur["start"]]
        if self.cur and self.cur["miles"] >= MIN_RIDE_MILES:
            out.append(dict(self.cur))
        return sorted(out, key=lambda r: r["start"], reverse=True)

    def save(self):
        if not self.cur or self.cur["miles"] < MIN_RIDE_MILES:
            return
        row = {k: (round(v, 2) if isinstance(v, float) else v) for k, v in self.cur.items()}
        self.rides = [r for r in self.rides if r["start"] != row["start"]] + [row]
        self.rides = self.rides[-KEEP:]
        try:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            tmp = self.path + ".tmp"
            with open(tmp, "w") as fh:
                json.dump(self.rides, fh)
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp, self.path)
            self._write_csv()
        except Exception as e:
            print(f"[rides] could not save ({e})")

    def _write_csv(self):
        path = os.path.splitext(self.path)[0] + ".csv"
        with open(path, "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["date", "start", "duration_min", "miles", "avg_mph", "top_mph",
                        "peak_rpm", "max_cht_c"])
            for r in self.rides:
                w.writerow([time.strftime("%Y-%m-%d", time.localtime(r["start"])),
                            time.strftime("%H:%M", time.localtime(r["start"])),
                            round(r["secs"] / 60, 1), round(r["miles"], 1), avg_mph(r),
                            round(r["top_mph"]), round(r["peak_rpm"]),
                            "" if r["max_cht"] is None else round(r["max_cht"])])


def avg_mph(r):
    return round(r["miles"] / (r["secs"] / 3600), 1) if r["secs"] > 0 else 0.0
