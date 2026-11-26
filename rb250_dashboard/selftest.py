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
    def gps_time(self): return None

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
    cfg.RIDES_FILE = os.path.join(tmp, "rides_app.json")
    pygame.init()
    for size in ((640, 480), (480, 320), (800, 480)):
        screen = pygame.display.set_mode(size)
        sc = Scaler(*size)
        now = time.time()

        # all live
        app = _app(FakeSensors())
        _settle(app)
        for page in (0, 1, 2):
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

    # ride log: saved, survives restart, csv written, short rides ignored
    import rides as rides_mod
    rp = os.path.join(tmp, "rides.json")
    log = rides_mod.RideLog(rp)

    class T:
        speed, rpm, cht = 48.0, 7200.0, 191.0
    for _ in range(600):           # 60 s at 48 mph = 0.8 mi
        log.update(T, 0.1)
    T.speed, T.rpm, T.cht = 30.0, 9100.0, 205.0
    log.update(T, 0.1)
    log.save()
    again = rides_mod.RideLog(rp).rides
    assert len(again) == 1 and abs(again[0]["miles"] - 0.8) < 0.02, again
    assert again[0]["top_mph"] == 48.0 and again[0]["peak_rpm"] == 9100 and again[0]["max_cht"] == 205
    assert os.path.exists(os.path.join(tmp, "rides.csv"))
    log.save()
    assert len(rides_mod.RideLog(rp).rides) == 1, "same ride saved twice"
    short = rides_mod.RideLog(os.path.join(tmp, "short.json"))
    T.speed = 0.0
    short.update(T, 5)
    short.save()
    assert not os.path.exists(os.path.join(tmp, "short.json")), "tiny ride should not be saved"

    # handlebar buttons: NEXT cycles pages, SELECT scrolls/moves, HOLD presses
    app3 = _app(FakeSensors())
    app3.telemetry.rides.rides = [{"start": i, "miles": 1.0, "secs": 60, "top_mph": 30,
                                   "peak_rpm": 5000, "max_cht": 150} for i in range(14)]
    seq = []
    for _ in range(3):
        app3.button("next")
        seq.append(app3.page)
    assert seq == [1, 2, 0], seq
    app3.button("next")                      # rides page
    app3.button("select"); assert app3.scroll == 6
    app3.button("select"); assert app3.scroll == 12
    app3.button("select"); assert app3.scroll == 0, "should wrap to top"
    app3.draw(screen, sc, time.time())
    app3.button("next")                      # settings
    app3.draw(screen, sc, time.time())
    n = len(app3.buttons)
    for _ in range(n - 1):
        app3.button("select")
    assert app3.buttons[app3.sel][1] == app3.request_shutdown, "last item should be POWER OFF"
    app3.button("hold")
    assert app3.confirm and app3.confirm_sel == 1, "confirm must default to CANCEL"
    app3.draw(screen, sc, time.time())
    app3.button("hold")
    assert not app3.confirm and not app3.powering_down, "CANCEL failed"
    app3.button("hold"); app3.button("select"); app3.button("hold")
    assert app3.powering_down, "POWER OFF via buttons failed"
    app3.sel = 1                              # brightness -
    app4 = _app(FakeSensors()); app4.page = 2
    app4.draw(screen, sc, time.time()); app4.button("select"); app4.button("hold")
    assert app4.brightness == 80, app4.brightness

    # settings buttons + confirm
    app2.page = 2
    app2.draw(screen, sc, time.time())
    for rect, cb in app2.buttons:
        cb()
    assert app2.confirm
    app2.confirm = False
    # graphics
    assert theme.cover_image("boot_bg.jpg", 480, 320) is not None
    assert theme.cover_image("shutdown_screen.jpg", 480, 320) is not None
    pygame.quit()
    print("SELFTEST OK - 640x480/480x320/800x480 render, buttons, live/missing sensors, "
          "traffic lights, ignition-off shutdown, miles saved")
    return 0


def preview(out="/tmp/rb250_previews"):
    os.makedirs(out, exist_ok=True)
    telemetry.ODO_PATH = os.path.join(out, "odo.json")
    cfg.RIDES_FILE = os.path.join(out, "rides.json")
    now = time.time()
    demo = [(now - 86400 * d - 3600 * h, m, s_, top, rpm, c) for d, h, m, s_, top, rpm, c in
            [(1, 2, 23.4, 3100, 58, 8240, 196), (2, 5, 8.2, 1260, 47, 7650, 184),
             (4, 1, 41.7, 5400, 62, 8610, 214), (6, 3, 3.1, 610, 39, 6900, 168)]]
    import json
    with open(cfg.RIDES_FILE, "w") as fh:
        json.dump([{"start": a, "miles": b, "secs": c, "top_mph": d, "peak_rpm": e,
                    "max_cht": f} for a, b, c, d, e, f in demo], fh)
    pygame.init()
    shots = [
        ("ride_ok", FakeSensors(), 0),
        ("ride_warn", FakeSensors(speed=55, rpm=8100, cht=196, fuel=31, volt=14.2), 0),
        ("ride_hot", FakeSensors(speed=61, rpm=8700, cht=222, fuel=9, volt=14.1), 0),
        ("ride_nosensors", FakeSensors(None, None, None, None, None, ("search", 0, 3)), 0),
        ("rides", FakeSensors(), 1),
        ("settings", FakeSensors(), 2),
    ]
    for size in ((640, 480), (480, 320), (800, 480)):
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
