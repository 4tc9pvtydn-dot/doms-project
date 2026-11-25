# RB250 wiring — Pi Zero 2 W (same pin numbers as before)

Pin numbers are the **physical** header pins (pin 1 = 3.3V, corner nearest the SD card).

| Module | Wire | Pi pin |
|---|---|---|
| **GPS** | VCC | 2 or 4 (5V) — or 1 (3.3V) if the module is 3.3V-only |
| | GND | any GND (6, 9, 14, 20, 25, 30, 34, 39) |
| | TX | **10** (RXD) |
| | RX | **8** (TXD) |
| **ADS1115** | VDD | 1 (3.3V) |
| | GND | GND |
| | SDA | 3 |
| | SCL | 5 |
| | ADDR | GND |
| | A1 | fuel node (below) |
| | A2 | voltage sensor `S` |
| **MAX31855 (CHT)** | VIN | 1 or 17 (3.3V) |
| | GND | GND |
| | DO | 21 |
| | CLK | 23 |
| | CS | 29 |
| | Thermocouple | yellow = +, red = − |
| **RPM opto module** | OUT | **11** only |
| | GND | GND |
| | VCC | not connected (Pi's built-in pull-up is used) |
| | Input | HT-lead wrap: 5–10 turns of insulated wire round the plug lead |
| **Voltage sensor (0–25V)** | screw + | **switched** 12V (dead when ignition off) |
| | screw − | bike ground |
| | S | ADS1115 A2 |
| | − (pin side) | GND |

## Fuel sender (2-wire)
```
3.3V ──[100 Ω]──┬── sender signal wire
                └── ADS1115 A1
sender ground wire ── GND
```

## Never
- Nothing from the bike's 12V, coil or stator goes straight to any Pi pin.
- Never put 5V on pin 11.

## UPS HAT + auto shutdown
- The UPS HAT powers the Pi; its input comes from your 12V→5V converter on the switched supply.
- Ignition off → voltage sensor (A2) drops below 6V → 3s countdown on screen
  → goodbye screen → Pi shuts down safely on UPS power.
- Ignition back on during the countdown or goodbye screen cancels it.
- UPS battery % shows on the Settings page. If the Pi is ever running on UPS
  battery and it drops below 10%, it shuts down safely by itself.

## Wake wire — starts the Pi again at ignition-on
After shutdown the UPS keeps the Pi powered but halted. A Pi wakes from halt
when **pin 5 is briefly pulled to ground**. A capacitor turns "ignition on" into
that short pulse, and an opto module keeps the bike's 12V away from the Pi.

Parts: 1 × PC817 opto module rated for 12V input (same type as the RPM module),
1 × 100 µF 25V electrolytic capacitor, 1 × 10 kΩ resistor.

```
switched 12V ──(+)[100µF](−)──┬── opto IN+
                              [10kΩ]
bike ground ──────────────────┴── opto IN−

opto OUT ── Pi pin 5        (shares pin 5 with the ADS1115 + UPS SCL — that's fine)
opto GND ── Pi GND
opto VCC ── not connected
```
- Capacitor stripe (−) faces the opto, (+) faces the 12V.
- Ignition on → the capacitor passes a ~0.2s pulse → opto pulls pin 5 low → Pi boots (~30–40s).
- The 10 kΩ lets the capacitor empty when the ignition is off, ready for next time.
- While riding, the capacitor blocks steady 12V, so pin 5 is left alone for I2C.
- If you switch the ignition back on in the last few seconds while the Pi is
  already powering off, it may miss the pulse: switch off, wait 5s, switch on.

Test on the bench: shut down (Settings → POWER OFF), wait for the green LED
to stop, then switch the 12V on — the RB250 boot screen should appear.
