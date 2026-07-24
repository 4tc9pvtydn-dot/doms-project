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
