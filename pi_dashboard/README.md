# DOMS RB252 — Lambretta Digital Dashboard (Python / Pygame)

A full-screen performance dashboard for a **Raspberry Pi 4B** with a
**Waveshare 3.5" DSI touchscreen (640×480)**. It runs as a native Python app,
boots straight to the Ride screen on power-up, and is ready for you to wire in
real sensors.

Runs the same on your laptop (in VS Code) and on the Pi.

![pages](five swipeable pages: Ride · Engine · GPS · Performance · Settings)

---

## 1. Try it on your computer first (VS Code)

Requires **Python 3.9+**.

```bash
cd pi_dashboard
python -m venv venv
# Windows:  venv\Scripts\activate
# macOS/Linux:  source venv/bin/activate
pip install -r requirements.txt
python main.py
```

A 640×480 window opens with **simulated live data**.

Controls:
- **Swipe** left/right (touch) or **← / → arrow keys** to change pages.
- **F** = toggle full-screen, **Esc / Q** = quit.
- On the touchscreen, all buttons (trip resets, settings) are tap-friendly.

Headless check (no window): `python main.py --selftest`

---

## 2. Install on the Raspberry Pi (boot straight to the dashboard)

1. Copy this `pi_dashboard` folder onto the Pi (e.g. to `/home/pi/rb252-dashboard`).
2. Run the installer:
   ```bash
   cd ~/rb252-dashboard
   chmod +x install.sh
   ./install.sh
   ```
   This creates a venv, installs pygame, runs a self-test, and installs a
   **systemd service** so the dashboard launches automatically on every boot.
3. Start it now (or just reboot):
   ```bash
   sudo systemctl start rb252-dashboard
   # logs:  journalctl -u rb252-dashboard -f
   ```

The service runs full-screen directly on the framebuffer (`SDL_VIDEODRIVER=kmsdrm`),
so you do **not** need the desktop environment — ideal for a clean kiosk boot.

> Prefer the desktop autostart instead? Add this to
> `~/.config/lxsession/LXDE-pi/autostart`:
> `@/home/pi/rb252-dashboard/venv/bin/python /home/pi/rb252-dashboard/main.py --fullscreen`

### Power off from the Settings page
Set `ALLOW_SHUTDOWN = True` in `config.py`, then allow passwordless shutdown:
```bash
echo "$USER ALL=(ALL) NOPASSWD:/sbin/shutdown" | sudo tee /etc/sudoers.d/rb252
```

---

## 3. Wiring in your real sensors

1. Open **`config.py`** and set `USE_REAL_SENSORS = True`.
2. Open **`sensors.py`** and fill in each `read_*` method with your hardware code.
   Every method returns a single number; placeholders keep the app running until
   you implement them.

| Reading            | Method              | Typical hardware / library |
|--------------------|---------------------|----------------------------|
| GPS speed & sats   | `read_speed_mph`, `read_satellites` | UART/USB GPS + `pyserial` + `pynmea2` |
| RPM pickup         | `read_rpm`          | pulse counting via `gpiozero` / `pigpio` |
| Cylinder head temp | `read_cht`          | K-type + MAX31855 (`adafruit-circuitpython-max31855`) |
| AFR controller     | `read_afr`          | 0–5 V analog → ADS1115 (`adafruit-circuitpython-ads1x15`) |
| Fuel sender        | `read_fuel_pct`     | resistive → divider → ADS1115 |
| Battery voltage    | `read_voltage`      | voltage divider → ADS1115 |

Install extra libraries into the venv, e.g.:
```bash
venv/bin/pip install pyserial pynmea2 adafruit-circuitpython-max31855 adafruit-circuitpython-ads1x15
```

The gear, trips, odometer, averages, peaks and 0-30/0-60/¼-mile timers are all
computed automatically from your speed/RPM readings.

---

## 4. Tuning (`config.py`)
- `REDLINE` / `SHIFT_RPM` — RPM bar full-scale and shift-light point.
- `WIDTH` / `HEIGHT` — panel resolution (640×480 for the Waveshare 3.5").

## Project layout
```
pi_dashboard/
├── main.py            # app loop, boot screen, swipe/keys, page transitions
├── config.py          # tuning + hardware/power flags
├── telemetry.py       # simulator + derived metrics
├── sensors.py         # << wire real hardware here
├── theme.py           # colours, fonts, carbon texture, status logic
├── widgets.py         # RPM bar, vertical bars, tiles, buttons, banner
├── pages.py           # the 5 pages
├── assets/fonts/      # Orbitron + Chakra Petch
├── requirements.txt
├── install.sh         # Pi installer + boot-on-power-up
└── rb252-dashboard.service
```

Fonts: Orbitron & Chakra Petch (SIL Open Font License).
