#!/bin/bash
# Live readout of every sensor exactly as the dashboard sees it. Ctrl+C to stop.
DIR="$(cd "$(dirname "$0")" && pwd)"
sudo systemctl stop rb250-dashboard 2>/dev/null
echo ">> I2C devices (ADS1115 must show 48):"
i2cdetect -y 1
cd "$DIR" && venv/bin/python - <<'EOF'
import time, config as cfg
from sensors import Sensors
s = Sensors()
f = lambda v, p: "--" if v is None else format(v, p)
while True:
    st, used, heard = s.gps_state()
    print(f"GPS {st:6s} {used}/{heard} sats  speed {f(s.read_speed_mph(), '.1f')} mph | "
          f"RPM {f(s.read_rpm(), '.0f')} ({s.rpm_hz:.1f} pulses/s, noise {s.rpm_rejects}) | "
          f"CHT {f(s.read_cht(), '.0f')} C | FUEL {f(s.read_fuel_pct(), '.0f')} % | "
          f"BATT {f(s.read_voltage(), '.1f')} V")
    for k, v in s.errors.items():
        print(f"   !! {k}: {v}")
    time.sleep(1)
EOF
echo ">> Restart the dashboard with:  sudo systemctl start rb250-dashboard"
