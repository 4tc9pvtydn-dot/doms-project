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
- Ignition back on within the 3s cancels it.
