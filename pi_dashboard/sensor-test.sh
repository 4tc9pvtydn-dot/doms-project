#!/bin/bash
# Live readout of the ADS1115 channels as the dashboard sees them (Ctrl+C to stop).
DIR="$(cd "$(dirname "$0")" && pwd)"
echo ">> I2C devices (ADS1115 should show 48):"
i2cdetect -y 1 2>/dev/null || echo "   i2cdetect missing: sudo apt install -y i2c-tools"
PY="$DIR/venv/bin/python"; [ -x "$PY" ] || PY=python3
cd "$DIR" && "$PY" - <<'EOF'
import time, config as cfg
from sensors import Sensors
s = Sensors()
while True:
    r = s.read_rpm()
    if r is not None:
        print(f"RPM {r:6.0f} | raw pulses {s.rpm_hz:6.1f}/s (PULSES_PER_REV={cfg.RPM_PULSES_PER_REV})")
    v = s.read_voltage(); f = s.read_fuel_pct(); a = s.read_afr()
    if v is None:
        print("ADS1115 NOT READ - see error above"); time.sleep(1); continue
    raw = s._ads_chan(cfg.FUEL_ADC_CH).voltage
    print(f"Battery {v:5.2f} V | Fuel {f:5.1f} % (A1 {raw:.2f} V) | AFR {a:5.2f}")
    time.sleep(1)
EOF
