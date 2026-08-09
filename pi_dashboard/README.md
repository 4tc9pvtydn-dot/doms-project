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

---

## Live data & controls (v2 update)

**Navigation on the touchscreen**
- **Swipe** left/right to change pages, **or tap a page dot** at the bottom to jump straight to a page (works even if swipe feels fiddly).
- Arrow keys still work if a keyboard is attached.

**Power off from the screen**
- Settings page → **POWER OFF** → confirm. With `ALLOW_SHUTDOWN = True` (default)
  and the sudo rule that `install.sh` adds, this cleanly shuts the Pi down.

**GPS (wired first)** — `USE_REAL_SENSORS = True` runs a **hybrid**: any sensor
that returns real data is used live; anything not wired yet stays simulated, so
the whole dash keeps working while you bring hardware online one piece at a time.

GPS wiring used (UART):
| GPS pin | Pi physical pin | Note |
|---|---|---|
| VCC | Pin 1 (3.3V) or Pin 2 (5V if module supports it) | |
| GND | Pin 6 | |
| TX  | Pin 10 (GPIO15 / RXD) | GPS TX → Pi RX |
| RX  | Pin 8  (GPIO14 / TXD) | GPS RX → Pi TX |

Enable the UART (also done by `install.sh`):
```bash
sudo raspi-config nonint do_serial_hw 0     # enable serial hardware
sudo raspi-config nonint do_serial_cons 1   # disable serial login console
sudo reboot
```
The GPS port/baud are set in `config.py` (`/dev/serial0`, 9600). Real GPS drives
**speed, gear and satellites**; RPM/CHT/AFR/fuel/voltage remain simulated until
you fill in their `read_*` methods in `sensors.py`.

**Note on pygame:** on the Pi we use the **system** pygame (`apt install python3-pygame`)
because the `pip` build lacks `kmsdrm` (needed to draw with no desktop). The venv
is created with `--system-site-packages` so it can see it. `install.sh` handles this.

---

## Sensor wiring (ADS1115 + MAX31855)

Enable the buses (done automatically by `install.sh`): I2C + SPI + UART.

### ADS1115 — AFR, Fuel, Battery (I²C)
| ADS1115 | Pi pin |
|---|---|
| VDD | Pin 1 (3.3V) |
| GND | Pin 9 |
| SCL | Pin 5 (GPIO3) |
| SDA | Pin 3 (GPIO2) |
| A0  | AFR signal (via divider) |
| A1  | Fuel sender node |
| A2  | Battery (via divider) |

⚠️ **The ADS1115 inputs must stay under 3.3V.** Use dividers:
- **Battery:** R1=39k to +batt, R2=10k to GND → set `BATT_DIVIDER=4.9`.
- **AFR (0–5V):** R1=10k, R2=20k → set `AFR_DIVIDER=1.5`. Confirm your controller's
  0V/5V → AFR mapping and set `AFR_V0` / `AFR_V5`.
- **Fuel:** `3.3V — Rref(100Ω) — [node→A1] — sender — GND`. Put your sender's
  empty/full ohms in `FUEL_OHMS_EMPTY` / `FUEL_OHMS_FULL`.

### MAX31855 — CHT (SPI)
| MAX31855 | Pi pin |
|---|---|
| VIN | Pin 17 (3.3V) |
| GND | Pin 25 |
| SCK | Pin 23 (GPIO11) |
| DO (MISO) | Pin 21 (GPIO9) |
| CS | Pin 29 (GPIO5) → `CHT_CS_PIN="D5"` |

K-type thermocouple to the MAX31855 screw terminals (mind polarity).

### RPM — ⚠️ DO NOT connect raw ignition to a GPIO
Ignition/CDI pulses are hundreds of volts and will destroy the Pi. You need a
**conditioning circuit** (opto-isolator, or a clamp + divider) that outputs a
clean **0–3.3V** pulse into `RPM_GPIO` (BCM17 / pin 11). Only then set
`RPM_ENABLED = True` and `RPM_PULSES_PER_REV` to your engine's sparks-per-rev.
Until then it stays simulated.

Every sensor is fail-safe: if its board/signal isn't present, that reading
falls back to the simulator, so you can wire them up one at a time.


