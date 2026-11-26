# RB250 Lambretta Dashboard — PRD

## Problem statement (current)
Native Pygame dashboard for a Lambretta, now on a **Raspberry Pi Zero 2 W** (Pi 4 failed) with a
**3.5" HDMI screen (not yet bought; 480×320 or 800×480 — layout auto-scales)**. Same GPIO pins as before.
Everything live (no simulation): GPS speed, revs, CHT, fuel, voltage, trip + odometer miles.
AFR and gear indicator removed. Branding "RB250" everywhere (no DOMS / RB252).
UPS HAT keeps the Pi up; auto-shutdown when the switched-12V voltage sensor drops (ignition off).

## User choices
- CHT colours: green <180°C, amber 180–210°C, red >210°C
- Fuel colours: red <15%, amber 15–50%, green 50–100%
- Missing sensor: show `--` + small "NO SIGNAL" warning
- Layout: one ride screen + settings page (default)

## Architecture — `/app/rb250_dashboard/` (old `/app/pi_dashboard` deleted; `/app/frontend` is dead code)
- `config.py` pins, limits, calibration · `sensors.py` live reads w/ auto-retry (GPS UART 9600, ADS1115 A1 fuel / A2 volts, MAX31855 CS pin 29, RPM opto pin 11 w/ noise filter, 1 pulse/rev HT-lead pickup)
- `telemetry.py` polling rates, smoothing, miles persisted to `~/.rb250/odometer.json`
- `theme.py` colours, traffic-light logic, `Scaler` (800×480 design grid → any screen)
- `ui.py` ride/settings/boot/goodbye/countdown/confirm screens · `main.py` loop + power-loss logic
- `selftest.py` headless test (`python main.py --selftest`) + `--preview` PNGs
- `install.sh`, `rb250-dashboard.service`, `sensor-test.sh`, `gps-test.sh`, `set-screen.sh`, `setup-boot-splash.sh` (optional Plymouth), README.md, WIRING.md
- Distributable: `/app/RB250-PiZero2W.zip`. Test only with selftest (native app, no web testing agent).

## Implemented
- 2026-06: Full RB250 rewrite for Pi Zero 2 W (above). Selftest passes at 480×320 and 800×480.
- Earlier (Pi 4 era): GPS baud 9600 fix, ADS1115 lib v3 fix, RPM rolling-window + glitch filter, fuel open-circuit handling, sensor status page.

- 2026-06: Waveshare UPS HAT (C) support: INA219 @0x43 battery %/volts on Settings (smbus2), low-UPS shutdown only when off bike power, ignition-on during goodbye cancels auto power-off (manual POWER OFF not cancelled). Wake-from-halt via opto + 100uF cap pulse on pin 5 (GPIO3) documented in WIRING.md; installer comments out gpio-shutdown overlay. User chose: always shut down + wake wire.
- 2026-06: Ride logging (`rides.py`): ride = ignition-on→shutdown; miles, duration, avg/top mph, peak rpm, max CHT; saved every 30s + at shutdown to ~/.rb250/rides.json + rides.csv; rides <0.1 mi dropped. New RIDES page (page 2 of 3, last 6 rides, CHT colour-coded). Pi clock set from GPS RMC time via `sudo -n date` (sudoers updated) so dates are right without Wi-Fi.
- 2026-06: Screen confirmed = Newhaven NHD-3.5-HDMI-HR-RSXP 640x480 HDMI, no touch. Scaler now stretches (sx/sy) to fill any aspect. Two GPIO buttons (`buttons.py`, gpiozero, pull-ups): NEXT BCM26/pin37 cycles pages; SELECT BCM16/pin36 = scroll rides / move highlight, hold 1s = press; confirm defaults to CANCEL. Keyboard N/Space/Enter mirrors for laptop.
- 2026-06: Ride detail view: Rides page SELECT moves a highlight row by row (auto pages, wraps), HOLD opens the ride full-screen (6 big tiles: distance, time, avg, top, peak revs red≥redline, hottest head CHT-coloured); in detail SELECT = older ride, HOLD/NEXT = back. Previews in rb250_dashboard/previews/.
- 2026-06: CRUISE page (page 2 of 4: Ride → Cruise → Rides → Settings): large analog speed dial 0–80 (DIAL_MAX_MPH) with needle, lit arc + small digital readout; wide vertical 12-segment fuel bar left and head-temp bar right (0–250°C, amber/red limit ticks, traffic colours, flash at red); larger clock centre-bottom; trip + odo. Page constants RIDE/CRUISE/RIDES/SETTINGS in main.py.
- 2026-06: Speed dial max 100 mph. Units switch (`units.py`): Settings → SWITCH TO KM/H/MPH, saved in ~/.rb250/settings.json; converts speed, dial (0–160 km/h, labels every 20), trip/odo, rides list + detail; data stays stored in miles (rides.csv stays in miles).
- 2026-06: 3D-printable dash panel `rb250_dashboard/cad/make_panel.py` → rb250_dash_panel.stl (+ preview PNG + 1:1 A4 PDF template; copy at /app/RB250-dash-panel.stl). 2mm plate, 130 high, widths 80/119/130/135/142 at 5/18/37/62/100mm from top, 150 at leg bottoms; rounded-U gap 90 wide from 111mm, legs 30 wide; screen window 73x56 (NHD viewing area 72.48x55.38 + clearance), top edge on the 119 line (18mm), centred.
- 2026-06: Panel button holes: two 12mm holes 92mm down, ±25mm from centre (SELECT left, NEXT right); BTN_D/BTN_Y/BTN_X params in make_panel.py.
- 2026-06: Panel thickness changed 2mm → 4mm (too flexible).
- 2026-06: Panel raised lettering (+0.8mm): SELECT / NEXT (4.5mm, ChakraPetch) under each hole, RB250 badge (6.5mm) between the buttons; buttons moved to ±30mm to fit the badge. Lettering via matplotlib TextPath→shapely, asserted inside the plate.

## Backlog
- P0: user builds wake circuit + verifies wake from halt on bench
- P0: user installs on Zero 2 W; verify all sensors live on bike (HT-lead RPM pickup, GPS lock with battery fitted)
- P2: optional backlight PWM wiring for real brightness control
