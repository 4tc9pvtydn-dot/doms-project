# RB250 Dashboard — Pi Zero 2 W

Live Lambretta dashboard: GPS speed, revs, head temp (CHT), fuel, battery
voltage, trip + odometer miles, and auto shutdown when the ignition goes off
(UPS HAT keeps the Pi powered while it shuts down).

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
- **Settings** (swipe left, or → key): reset trip, brightness, sensor status,
  auto-shutdown status, POWER OFF.

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
| Logs / errors | `journalctl -u rb250-dashboard -b` |
| Restart | `sudo systemctl restart rb250-dashboard` |
| Wrong screen picture | `bash set-screen.sh 480x320` (or `800x480`, `auto`) |
| RB250 boot logo (optional) | `bash setup-boot-splash.sh` |

## Laptop test
`python main.py --size 480x320` · `python main.py --selftest` · `python main.py --preview`
