# DOMS RB252 — Wiring Reference

Pin numbers are **physical** (the 1–40 header positions). Values match `config.py`.

## Pi pins used
| Pi pin | Function | Goes to |
|---|---|---|
| 1  | 3.3 V        | ADS1115 VDD, MAX31855 VIN, fuel & AFR divider top |
| 2 / 4 | 5 V       | GPS VCC, 5 V backup |
| 3  | SDA (GPIO2)  | ADS1115 SDA |
| 5  | SCL (GPIO3)  | ADS1115 SCL |
| 6 / 9 / 14 | GND  | common ground for EVERYTHING |
| 8  | TXD (GPIO14) | GPS RX |
| 10 | RXD (GPIO15) | GPS TX |
| 11 | GPIO17       | RPM pulse input (via opto) |
| 19 | MOSI (GPIO10)| MAX31855 (optional) |
| 21 | MISO (GPIO9) | MAX31855 DO |
| 23 | SCLK (GPIO11)| MAX31855 CLK |
| 29 | GPIO5        | MAX31855 CS |

## Golden rules
- Power the **ADS1115 from 3.3 V (pin 1)** so analog inputs never exceed 3.3 V.
- Every module's **GND must return to a common Pi GND**. Floating ground = flaky/no readings.

---

## GPS (UART) — set GPS_BAUD = 9600
- VCC → 5 V (pin 2/4) · GND → pin 6
- GPS TX → Pi pin 10 · GPS RX → Pi pin 8
- No resistors.

## ADS1115 (I2C) — AFR / Fuel / Battery
- VDD → 3.3 V (pin 1) · GND → pin 6 · SDA → pin 3 · SCL → pin 5 · ADDR → GND (0x48)
- A0 = AFR · A1 = Fuel · A2 = Battery

## Battery / 0–25 V voltage sensor → ADS A2
- Screw IN **+** → switched 12 V · screw IN **−** → ground
- Out **S** → ADS A2 · Out **−** → ADS GND · Out **+** = unused
- No extra resistor (divider is built in, ratio 5).

## Fuel sender (240 Ω empty → 33 Ω full) → ADS A1   [needs 1 resistor]
```
3.3V ──[100 Ω]──●── sender ── GND
                └──► ADS A1
```
- Resistor: **1 × 100 Ω, ¼ W** (FUEL_REF_OHMS = 100).

## AFR controller (0–5 V out) → ADS A0   [needs 2 resistors]
```
AFR 0-5V ──[10 kΩ]──●──[20 kΩ]── GND
                    └──► ADS A0
```
- Resistors: **10 kΩ + 20 kΩ, ¼ W** (AFR_DIVIDER = 1.5). Share ground with the Pi.

## CHT — MAX31855 K-type (SPI)
- VIN → 3.3 V · GND → GND · DO → pin 21 · CLK → pin 23 · CS → pin 29
- Thermocouple: yellow (+) / red (−) into the screw terminals. No resistors.

## RPM pickup → GPIO17 (pin 11)   [needs an opto-isolator, see RPM section]
NEVER wire an ignition pulse straight to a GPIO. Use a PC817/4N35 opto.
```
tacho/coil pulse ──[R1 10 kΩ]── PC817 pin1 (LED+)
            PC817 pin2 (LED−) ── ignition GND
3.3V ──[R2 10 kΩ]──● ── Pi pin 11 (GPIO17)
PC817 pin4 (collector) ──┘
PC817 pin3 (emitter) ── Pi GND
```
Then in config.py: `RPM_ENABLED = True` and set `RPM_PULSES_PER_REV`.

## Ignition sense (GPIO27) — NOT USED
Power-loss shutdown uses the voltage sensor instead, so GPIO27 stays unused.
