# DOMS RB252 Dashboard — Clean Install Guide

Fresh start from a corrupted SD card. Follow top to bottom; it takes ~20 min.

> TIP: Use a good-quality **A2-rated** microSD (SanDisk Extreme, Samsung Pro) or,
> better, boot from a **USB SSD**. Cheap cards are what caused the corruption,
> especially with power being cut without a clean shutdown.

---

## 1. Flash a fresh Raspberry Pi OS

1. Install **Raspberry Pi Imager** on your computer.
2. Choose OS: **Raspberry Pi OS (64-bit)** (the normal desktop version).
3. Choose your SD card.
4. Click the **gear / ⚙ (Edit Settings)** BEFORE writing, and set:
   - Hostname: `rb252`
   - **Enable SSH** (password auth)
   - Username: `doms`  + a password you'll remember
   - **Configure Wi-Fi** (your network name + password) — so the Pi is online
     the moment it boots and you can SSH in without a screen.
   - Locale / timezone to yours.
5. Write, then put the card in the Pi and power up on the bench.

---

## 2. Get the code onto the Pi (no USB stick needed)

The cleanest way is straight from GitHub over Wi-Fi.

**If the project is on GitHub** (ask the agent to "Save to GitHub" first):
```bash
sudo apt-get update && sudo apt-get install -y git
git clone https://github.com/<your-user>/<your-repo>.git
cd <your-repo>/pi_dashboard
```
(If the repo is **private**, use a GitHub Personal Access Token as the password,
or make the repo public for the clone then private again.)

**No GitHub?** On the Pi's desktop, open the browser, download the project ZIP,
then:
```bash
cd ~ && unzip -o ~/Downloads/RB252-Pi-Python.zip
cd pi_dashboard
```

---

## 3. Install

```bash
bash install.sh
```
This installs everything (pygame-with-kmsdrm, serial, sensor libs), enables
UART/I2C/SPI, sets passwordless poweroff, installs the auto-start service, and
runs a self-test. It keeps a **login prompt** so you can never get locked out
(press **Ctrl+Alt+F2** any time for a console).

Start it without rebooting:
```bash
sudo systemctl start rb252-dashboard
```
Reboot to confirm it auto-launches:
```bash
sudo reboot
```

---

## 4. Test the GPS (do this OUTSIDE)

**GPS will NEVER lock indoors / in a computer room — it needs a clear view of
the sky.** This is almost certainly why it isn't "picking up satellites".

First confirm the module is talking to the Pi:
```bash
sudo systemctl stop rb252-dashboard      # free the port for the test
stty -F /dev/serial0 38400 && timeout 6 cat /dev/serial0
# if that prints nothing readable, try the other common baud:
stty -F /dev/serial0 9600  && timeout 6 cat /dev/serial0
```
- You should see lines like `$GPGGA,...`, `$GPRMC,...`, `$GNRMC,...`.
  - **If you see them** → the module works. Now take the Pi + antenna **outside**,
    lay the antenna flat with a clear sky view, and wait **5–15 minutes** for a
    first (cold) fix. The module's LED starts **blinking** once it locks.
  - If the readable baud was **9600**, set `GPS_BAUD = 9600` in `config.py`.
- **If you see nothing/garbage at both bauds** → check wiring: GPS **TX → Pi RX
  (pin 10)**, GPS **RX → Pi TX (pin 8)** (TX/RX must cross), GPS **VCC → 3.3V or
  5V** per your module, **GND → GND**.

The dashboard shows `GPS SEARCHING` until it locks, then `GPS FIX n`.

---

## 5. Turn on your hardware (when wired)

Edit `config.py`:

```python
USE_REAL_SENSORS = True        # already on — reads hardware, simulates whatever's missing

# Battery/voltage sensor on ADS1115 A2 — already mapped.

# Power-loss graceful shutdown using the voltage sensor on the SWITCHED 12V feed:
POWER_LOSS_SHUTDOWN = True      # enable once backup power + switched feed are wired
POWER_LOSS_VOLTS    = 6.0       # below this = main power lost
IGNITION_OFF_DELAY  = 3.0       # seconds before it powers down

GPS_BAUD = 38400                # set to 9600 if that's what your module streams
```

Restart after any config change:
```bash
sudo systemctl restart rb252-dashboard
```

---

## 6. OPTIONAL — branded DOMS boot logo

Do this **only after** the dashboard is confirmed working on a reboot:
```bash
bash setup-boot-splash.sh
sudo reboot
```
If you ever want the normal desktop / to undo everything:
```bash
bash recover-desktop.sh
sudo reboot
```

---

## Golden rule to avoid another corrupted card
**Always shut down cleanly** before cutting power on the bench:
```bash
sudo poweroff
```
On the bike, the voltage-sensor power-loss shutdown (section 5) + a 5 V backup
does this for you automatically.
