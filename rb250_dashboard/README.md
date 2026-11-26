# RB250 Dashboard — Pi Zero 2 W

Live Lambretta dashboard: GPS speed, revs, head temp (CHT), fuel, battery
voltage, trip + odometer miles, and auto shutdown when the ignition goes off
(UPS HAT keeps the Pi powered while it shuts down), and a wake wire on pin 5
that starts it again at the next ignition-on (see WIRING.md). UPS battery %
is on the Settings page.

Every reading is live. If a sensor isn't connected it shows `--` and
`NO SIGNAL` – never a made-up number.

## Install (fresh Raspberry Pi OS Lite or Desktop, 32/64-bit)
1. Copy this `rb250_dashboard` folder to the Pi (e.g. `~/rb250_dashboard`).
2. `cd ~/rb250_dashboard && bash install.sh`
3. `sudo reboot` – the dashboard starts on its own.

Set your current mileage once (before first ride):
```
nano ~/rb250_dashboard/config.py      # ODO_START = 12345
rm -f ~/.rb250/odometer.json && sudo systemctl restart rb250-dashboard
```

## Screens
- **Ride**: RPM bar 1–10k + digital RPM + peak marker, big MPH, head temp,
  fuel, battery, trip + odometer. GPS status top centre.
- **Rides** (NEXT button): every ride (ignition on → off) with date, miles,
  time, average + top speed, peak revs and hottest head temp. Rides under
  0.1 mile aren't kept. The clock and dates are set from GPS, so no Wi-Fi needed.
- **Settings** (NEXT again): reset trip, brightness, sensor status,
  auto-shutdown status, POWER OFF.

## Buttons
NEXT (pin 37) changes page. SELECT (pin 36) scrolls rides / moves the
highlight on Settings; hold SELECT 1s to press. See WIRING.md.

## Colours
| | Green | Amber | Red |
|---|---|---|---|
| Head temp | under 180°C | 180–210°C | over 210°C (flashes + ENGINE HOT) |
| Fuel | 50–100% | 15–50% | under 15% (flashes + FUEL LOW) |
| Battery | 11.8–15V | under 11.8V | over 15V |

Change limits in `config.py`, then `sudo systemctl restart rb250-dashboard`.

## Handy commands
| | |
|---|---|
| Live sensor readout | `bash sensor-test.sh` |
| Raw GPS data | `bash gps-test.sh` |
| Ride log on a computer | copy `~/.rb250/rides.csv` (opens in Excel) |
| Logs / errors | `journalctl -u rb250-dashboard -b` |
| Restart | `sudo systemctl restart rb250-dashboard` |
| Wrong screen picture | `bash set-screen.sh 480x320` (or `800x480`, `auto`) |
| RB250 boot logo (optional) | `bash setup-boot-splash.sh` |

## Laptop test
`python main.py` (N = NEXT, Space = SELECT, Enter = hold) · `python main.py --selftest` · `python main.py --preview`
