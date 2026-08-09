#!/usr/bin/env bash
# Installer for the DOMS RB252 dashboard on Raspberry Pi OS (Bookworm).
# Uses the system pygame (built WITH kmsdrm) so it can draw with no desktop,
# sets up GPS UART + shutdown permission, and enables boot-on-power-up.
set -e

DIR="$(cd "$(dirname "$0")" && pwd)"
USER_NAME="$(whoami)"

echo ">> Installing system packages (pygame with kmsdrm, serial)..."
sudo apt-get update
sudo apt-get install -y python3-pygame python3-serial \
  libsdl2-2.0-0 libsdl2-ttf-2.0-0 libsdl2-image-2.0-0 python3-venv

echo ">> Adding $USER_NAME to video/render/input/tty groups (screen + touch)..."
sudo usermod -aG video,render,input,tty "$USER_NAME"

echo ">> Creating venv that can see the system pygame..."
python3 -m venv --system-site-packages "$DIR/venv"
"$DIR/venv/bin/pip" install --upgrade pip
"$DIR/venv/bin/pip" install -r "$DIR/requirements.txt"

echo ">> Enabling UART (GPS), I2C (ADS1115) and SPI (MAX31855)..."
sudo raspi-config nonint do_serial_hw 0 || true
sudo raspi-config nonint do_serial_cons 1 || true
sudo raspi-config nonint do_i2c 0 || true
sudo raspi-config nonint do_spi 0 || true

echo ">> Installing sensor libraries into the venv..."
"$DIR/venv/bin/pip" install \
  adafruit-blinka \
  adafruit-circuitpython-ads1x15 \
  adafruit-circuitpython-max31855 \
  gpiozero lgpio || echo "!! sensor libs failed - GPS still works; retry later"

echo ">> Allowing passwordless power off (for the on-screen POWER OFF button)..."
echo "$USER_NAME ALL=(ALL) NOPASSWD:/usr/bin/systemctl poweroff,/usr/bin/systemctl reboot,/usr/sbin/poweroff,/sbin/poweroff,/usr/sbin/shutdown,/sbin/shutdown" | \
  sudo tee /etc/sudoers.d/rb252-shutdown > /dev/null
sudo chmod 440 /etc/sudoers.d/rb252-shutdown

echo ">> Self-test..."
"$DIR/venv/bin/python" "$DIR/main.py" --selftest

echo ">> Installing systemd service (boot straight to dashboard)..."
sed "s|__DIR__|$DIR|g; s|__USER__|$USER_NAME|g" \
  "$DIR/rb252-dashboard.service" | sudo tee /etc/systemd/system/rb252-dashboard.service > /dev/null
sudo systemctl daemon-reload
sudo systemctl enable rb252-dashboard.service
sudo systemctl set-default multi-user.target   # boot to console (no desktop)

echo ">> Setting up branded boot splash (DOMS logo via Plymouth)..."
bash "$DIR/setup-boot-splash.sh" || echo "!! boot splash setup failed - dashboard still works"

echo ""
echo "=================================================================="
echo " Done.  REBOOT to launch:  sudo reboot"
echo " Start now:   sudo systemctl start rb252-dashboard"
echo " View logs:   journalctl -u rb252-dashboard -f"
echo " Stop:        sudo systemctl stop rb252-dashboard"
echo " Desktop back: sudo systemctl set-default graphical.target"
echo "=================================================================="
