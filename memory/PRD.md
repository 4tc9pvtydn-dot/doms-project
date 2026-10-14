# Lambretta RB252 — Digital Dashboard V2

## Problem Statement
Digital dashboard for a Lambretta scooter running on a Raspberry Pi 4B with a Waveshare 3.5" DSI touchscreen (640×480). 5 swipeable pages driven by GPS speed, RPM pickup, CHT, AFR, fuel sender and battery voltage sensors. V2 in this environment uses SIMULATED live telemetry (no real sensors, no backend, in-session only).

## User Choices
- Simulated live data (realistic changing values)
- Carbon fibre dark theme, full-screen, all data readable while riding
- Include future visual touches: carbon fibre texture, shift light, smooth bar animations, warning banner
- No persistence (in-session only)

## Architecture
- Frontend-only React app (no backend/DB used). Fixed 640×480 frame scaled to fit viewport.
- `src/hooks/useTelemetry.js` — simulation engine (100ms tick): speed wander, gear/RPM derivation, CHT/AFR/voltage models, trips, odometer, peaks, 0-30/0-60/¼-mile launch detection.
- `src/lib/dashUtils.js` — colour threshold logic (fuel/CHT/AFR/voltage), unit conversion, time formatting.
- `src/components/dash/` — StartupScreen, RidePage, EnginePage, GpsPage, PerformancePage, SettingsPage, RpmBar (center-out LED), VerticalBar, WarningBanner, PageIndicator, StatTile.
- `src/App.js` — boot sequence (~2.6s), page navigation (swipe + ArrowLeft/Right keys), brightness filter, warning derivation, shutdown/restart.

## Implemented (2026-07-24)
- Startup screen (DOMS RB252 + loading bar) fading into Ride page.
- Page 1 Ride: huge speed digits, large gear, center-out RPM bar with shift flash, fuel + temp vertical bars, AFR, battery voltage (+ animated fan icon), clock, odometer — all colour-coded.
- Page 2 Engine: RPM, AFR, CHT, EGT (future placeholder), Battery, Fan status, Engine runtime.
- Page 3 GPS: current/avg/max speed, Trip A/B, ride time, satellites, trip reset buttons.
- Page 4 Performance: 0-30, 0-60, ¼ mile, peak RPM/temp, best speed, reset button.
- Page 5 Settings: brightness, units (MPH/KPH), 12/24h clock, CHT warn limits, calibration info, shutdown.
- Global page indicator dots, flashing red warning banner (CHT critical / AFR danger), smooth framer-motion animations, MPH↔KPH conversion, night-dimming via brightness.
- Tested via testing agent: 95% pass, all core flows working.

## Backlog / Future
- P1: Bluetooth phone connection; ride logging to CSV.
- P2: Night-mode auto-dim schedule; real sensor GPIO/serial integration on the Pi (GPS, RPM pickup, CHT, AFR, fuel, voltage); fan control + indicators + warning lights outputs.
- P2: EGT sensor once hardware added.

---

## UPDATE — Native Python/Pygame rewrite (current source of truth)
Tech pivoted from React to **Python (Pygame)** kiosk app under `/app/pi_dashboard/` (React in `/app/frontend` is dead code). Runs on the Pi framebuffer via `SDL_VIDEODRIVER=kmsdrm`. Hybrid telemetry: live sensor reads when hardware present, else simulated fallback. Test with `SDL_VIDEODRIVER=dummy python main.py --selftest`. Do NOT use the automated web testing agent. Distributable: `/app/RB252-Pi-Python.zip` (rebuilt on code changes, excludes venv).

### Implemented (2026-08-09)
- Custom AI boot logo (`assets/boot_logo.jpg`, DOMS RB252 Lambretta on carbon) shown during 2.6s boot with amber progress bar.
- Custom shutdown graphic (`assets/shutdown_screen.jpg`, "UNTIL NEXT TIME DUDE" sunset) shown for 3s before the actual poweroff, on both the ignition-off auto-shutdown and the manual Settings→POWER OFF confirm.
- New `powering_down` app state + `begin_poweroff()`; `theme.load_cover_image()` (aspect-cover, cached) and `theme.gps_status()` helper.
- GPS lock status text: Ride page shows centred "GPS SEARCHING" (amber, blinking) vs "GPS FIX n"; GPS page top-right shows "SEARCHING n SAT" vs "FIX n SAT" (SEARCHING when <4 sats). Helps distinguish no-lock from broken module.
- Verified via headless `--selftest` (pages render, nav, GPS hybrid, ignition→power-down graphic, both graphics load) + rendered PNG previews.

### Update 2 (fresh-start + tach + power-loss shutdown)
- New **wedge RPM tach** (`widgets.rpm_tach`): left-to-right segments grow small->large, 1-10k scale on top, digital RPM readout, white peak-hold marker, green/lime/amber/red zones + shift flash. Wired into RidePage (replaced old centre-out `rpm_bar`).
- **Voltage-sensor power-loss shutdown** (no extra parts): `config.POWER_LOSS_SHUTDOWN` + `POWER_LOSS_VOLTS=6.0`. `main.check_ignition(now, volts)` now triggers graceful poweroff when the battery sensor (ADS1115 A2, wired to the SWITCHED 12V feed) collapses, OR via the GPIO27 ignition pin. Hybrid-safe (never triggers on simulated volts). Reuses existing `begin_poweroff` + goodbye-graphic flow.
- **Safer installer**: `install.sh` no longer auto-runs `setup-boot-splash.sh`; keeps getty@tty1 (login prompt) so no lockout. Boot splash is opt-in. `setup-boot-splash.sh` reverted the aggressive console=tty3/getty-disable (the cause of the earlier lockout). Added `recover-desktop.sh` and `FINAL_SETUP.md` (clean-install guide).
- Hardware wiring guidance delivered: 0-25V voltage sensor -> ADS1115 A2; 5.1V adjustable backup via one Schottky into Pi 5V pin; backup must be 5V (NOT 3.3V - Pi won't run).
- Backup voltage default `IGNITION_OFF_DELAY` lowered 4.0 -> 3.0s.

### Known field issues (user hardware, not code)
- SD card corruption -> read-only root, repeatedly, from cutting power without clean shutdown on the bench. Resolution: fresh flash (A2 card / USB SSD) + always `sudo poweroff`. The voltage power-loss shutdown prevents this on the bike.
- GPS "no satellites": being tested indoors/computer room -> can never lock. Needs clear sky + 5-15 min cold start. Module likely fine. Verify NMEA via `cat /dev/serial0` at 38400 then 9600.

### Backlog (Python app)
- P1: RPM reading logic in `sensors.py` (stubbed for Pi safety until user builds opto-isolator circuit).
- P2: AFR reading (pending user's AFR controller + 0-5V mapping).
- P3: Ride logging to CSV, Bluetooth phone link, EGT/fan status integration.
