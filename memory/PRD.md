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

## Backlog
- P0: user builds wake circuit + verifies wake from halt on bench
- P0: user installs on Zero 2 W; verify all sensors live on bike (HT-lead RPM pickup, GPS lock with battery fitted)
- P1: confirm HDMI screen choice (must not plug onto GPIO header — pins are in use); touch via USB or none
- P2: ride CSV log
