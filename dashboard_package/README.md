# DOMS RB252 — Lambretta Digital Dashboard V2

A 5-page performance dashboard for a Lambretta scooter, designed for a
**Raspberry Pi 4B** with a **Waveshare 3.5" DSI touchscreen (640×480)**.

This build uses a **simulated telemetry engine** (realistic changing values) so
the whole dash runs standalone with no hardware wired in. Real sensors
(GPS / RPM pickup / CHT / AFR / fuel sender / battery voltage) can be wired in
later by replacing the simulator in `src/hooks/useTelemetry.js`.

## Pages
1. **Ride** – huge speed + gear, center-out RPM LED bar (shift flash), fuel/temp bars, AFR, battery voltage, fan icon, clock, odometer.
2. **Engine** – RPM, AFR, CHT, EGT (future), battery, fan status, engine runtime.
3. **GPS** – current / average / max speed, Trip A/B, ride time, satellites.
4. **Performance** – 0-30, 0-60, ¼ mile, peak RPM/temp, best speed.
5. **Settings** – brightness, units (MPH/KPH), clock, CHT warning limits, shutdown.

Swipe left/right (or arrow keys) to change pages. Page dots show position.

---

## Requirements
- Node.js 18+ and Yarn
- (On the Pi) Chromium browser for kiosk mode

## Install & Run (development)
```bash
cd frontend
yarn install
yarn start
```
Opens on http://localhost:3000

## Build for production
```bash
cd frontend
yarn build
```
Static files land in `frontend/build/`. Serve them with any static server:
```bash
npx serve -s build -l 3000
```

## Environment
`frontend/.env` contains `REACT_APP_BACKEND_URL`. This build makes **no backend
calls** (data is simulated), so the value is unused — you can leave it as-is.

---

## Raspberry Pi kiosk setup (640×480 touchscreen)
1. Build the app (`yarn build`) and serve it (e.g. `npx serve -s build -l 3000`)
   or run `yarn start` on boot.
2. Launch Chromium full-screen pointing at the app:
```bash
chromium-browser --kiosk --incognito \
  --window-size=640,480 --window-position=0,0 \
  --disable-pinch --overscroll-history-navigation=0 \
  http://localhost:3000
```
3. Auto-start on boot: add the serve + chromium commands to
   `~/.config/lxsession/LXDE-pi/autostart` or a systemd user service.

The dashboard is a fixed 640×480 canvas that auto-scales to fit the display.

---

## Wiring real sensors (next step)
Replace the body of `useTelemetry.js` so it reads live values instead of the
simulator, keeping the same output shape:
`{ speed, rpm, gear, fuel, cht, afr, volt, satellites, odometer, tripA, tripB,
   rideTime, engineRuntime, avgSpeed, maxSpeed, peakRpm, peakTemp, bestSpeed,
   fanOn, accel0_30, accel0_60, quarter, running }`

Typical Pi approach: a small Python service reads GPIO/serial/I²C sensors and
exposes them over a local WebSocket or HTTP endpoint; the hook subscribes to it.
