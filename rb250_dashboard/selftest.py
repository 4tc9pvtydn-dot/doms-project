"""Headless self-test and screenshot previews (no hardware needed)."""
import os
import time
import tempfile
import pygame
import config as cfg
import theme
import telemetry
import main as m
from theme import Scaler


class FakeSensors:
    def __init__(self, speed=42.0, rpm=5200.0, cht=172.0, fuel=64.0, volt=13.8,
                 gps=("fix", 8, 11), ups=(4.05, 87.0)):
        self.v = dict(speed=speed, rpm=rpm, cht=cht, fuel=fuel, volt=volt, ups=ups)
        self.gps = gps

    def gps_state(self): return self.gps
    def read_speed_mph(self): return self.v["speed"]
    def read_rpm(self): return self.v["rpm"]
    def read_cht(self): return self.v["cht"]
    def read_fuel_pct(self): return self.v["fuel"]
    def read_voltage(self): return self.v["volt"]
    def read_ups(self): return self.v["ups"]

    def status(self):
        return [("GPS", "8/11", True), ("ADC", "LIVE", True), ("CHT", "LIVE", True),
                ("RPM", "LIVE", True), ("UPS", "LIVE", True)]


def _settle(app, secs=1.0):
    for _ in range(int(secs / 0.05)):
        app.telemetry._next = {"ads": 0.0, "cht": 0.0, "ups": 0.0}
        app.telemetry.update(0.05)


def _app(sensors):
    app = m.App(sensors)
    app.boot_start = 0
    return app


def run():
    tmp = tempfile.mkdtemp()
    telemetry.ODO_PATH = os.path.join(tmp, "odo.json")
    pygame.init()
    for size in ((480, 320), (800, 480)):
        screen = pygame.display.set_mode(size)
        sc = Scaler(*size)
        now = time.time()

        # all live
        app = _app(FakeSensors())
        _settle(app)
        for page in (0, 1):
            app.page = page
            app.draw(screen, sc, now)
        assert abs(app.telemetry.speed - 42) < 0.01
        assert app.telemetry.trip > 0, "trip not counting"

        # every sensor missing -> dashes, no crash, no shutdown
        app = _app(FakeSensors(None, None, None, None, None, ("none", 0, 0)))
        _settle(app)
        app.page = 0
        app.draw(screen, sc, now)
        t = app.telemetry
        assert None in (t.speed,) and t.cht is None and t.fuel is None and t.volt is None
        app.check_power(100.0)
        assert app.countdown is None, "missing voltage must never shut down"

    # traffic lights
    assert theme.cht_color(170) == theme.GREEN
    assert theme.cht_color(195) == theme.AMBER
    assert theme.cht_color(215) == theme.RED
    assert theme.fuel_color(10) == theme.RED
    assert theme.fuel_color(30) == theme.AMBER
    assert theme.fuel_color(50) == theme.GREEN

    # ignition off -> countdown -> goodbye -> poweroff command
    fs = FakeSensors()
    app = _app(fs)
    _settle(app)
    app.check_power(10.0)
    assert app.countdown is None
    fs.v["volt"] = 0.4
    _settle(app, 1.0)
    app.check_power(20.0)
    assert app.countdown is not None, "voltage drop did not start countdown"
    fs.v["volt"] = 13.5
    _settle(app, 1.0)
    app.check_power(21.0)
    assert app.countdown is None, "voltage back should cancel"
    fs.v["volt"] = 0.4
    _settle(app, 1.0)
    app.check_power(30.0)
    app.check_power(30.0 + cfg.POWER_OFF_DELAY + 0.1)
    assert app.powering_down, "did not begin power-down"
    calls = []

    class R:
        returncode = 0
    orig = m.subprocess.run
    m.subprocess.run = lambda cmd, **k: calls.append(cmd) or R()
    app.draw(screen, sc, 100.0)
    app.draw(screen, sc, 100.0 + m.GOODBYE_SECONDS + 0.1)
    m.subprocess.run = orig
    assert calls and "poweroff" in " ".join(calls[0]), "no poweroff issued"

    # ignition back on during the goodbye screen -> cancel, keep riding
    fs = FakeSensors()
    app = _app(fs)
    _settle(app)
    fs.v["volt"] = 0.4
    _settle(app, 1.0)
    app.check_power(40.0)
    app.check_power(40.0 + cfg.POWER_OFF_DELAY + 0.1)
    assert app.powering_down
    fs.v["volt"] = 13.6
    _settle(app, 1.0)
    app.check_power(45.0)
    assert not app.powering_down, "ignition on during goodbye should cancel"

    # manual POWER OFF must NOT be cancelled by good voltage
    app.begin_poweroff()
    app.check_power(50.0)
    assert app.powering_down, "manual power off was cancelled"

    # UPS low: only shuts down when NOT on bike power
    fs = FakeSensors(ups=(3.45, 6.0))
    app = _app(fs)
    _settle(app, 2.5)
    app.check_power(60.0)
    assert not app.powering_down, "UPS low while ignition on must not shut down"
    fs.v["volt"] = None
    _settle(app, 1.0)
    app.check_power(61.0)
    assert app.powering_down and app.shutdown_reason == "UPS BATTERY LOW"

    # miles survive a restart
    app2 = _app(FakeSensors(speed=0.0))
    assert abs(app2.telemetry.odo - app.telemetry.odo) < 0.01, "odometer not saved"
    app2.telemetry.reset_trip()
    assert app2.telemetry.trip == 0

    # settings buttons + confirm
    app2.page = 1
    app2.draw(screen, sc, time.time())
    for rect, cb in app2.buttons:
        cb()
    assert app2.confirm
    app2.confirm = False
    # graphics
    assert theme.cover_image("boot_bg.jpg", 480, 320) is not None
    assert theme.cover_image("shutdown_screen.jpg", 480, 320) is not None
    pygame.quit()
    print("SELFTEST OK - 480x320 + 800x480 render, live/missing sensors, "
          "traffic lights, ignition-off shutdown, miles saved")
    return 0


def preview(out="/tmp/rb250_previews"):
    os.makedirs(out, exist_ok=True)
    telemetry.ODO_PATH = os.path.join(out, "odo.json")
    pygame.init()
    shots = [
        ("ride_ok", FakeSensors(), 0),
        ("ride_warn", FakeSensors(speed=55, rpm=8100, cht=196, fuel=31, volt=14.2), 0),
        ("ride_hot", FakeSensors(speed=61, rpm=8700, cht=222, fuel=9, volt=14.1), 0),
        ("ride_nosensors", FakeSensors(None, None, None, None, None, ("search", 0, 3)), 0),
        ("settings", FakeSensors(), 1),
    ]
    for size in ((480, 320), (800, 480)):
        screen = pygame.display.set_mode(size)
        sc = Scaler(*size)
        for name, fs, page in shots:
            app = _app(fs)
            app.telemetry.odo, app.telemetry.trip = 1245.3, 23.7
            _settle(app)
            app.telemetry.peak_rpm = max(app.telemetry.peak_rpm, 6900)
            app.page = page
            app.draw(screen, sc, time.time())
            pygame.image.save(screen, f"{out}/{name}_{size[0]}.png")
        app = _app(FakeSensors())
        app.boot_start = time.time() - 1.6
        app.draw(screen, sc, time.time())
        pygame.image.save(screen, f"{out}/boot_{size[0]}.png")
    print(f"previews in {out}")
    return 0
