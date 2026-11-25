#!/usr/bin/env bash
# RB250 dashboard installer - Raspberry Pi Zero 2 W, Raspberry Pi OS (Bookworm/Trixie)
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
USER_NAME="$(whoami)"
BOOT=/boot/firmware; [ -d "$BOOT" ] || BOOT=/boot
CFG="$BOOT/config.txt"

echo ">> Removing the old RB252 dashboard service (if present)..."
sudo systemctl disable --now rb252-dashboard 2>/dev/null || true
sudo rm -f /etc/systemd/system/rb252-dashboard.service /etc/sudoers.d/rb252-shutdown

echo ">> Installing system packages..."
sudo apt-get update
sudo apt-get install -y python3-pygame python3-serial python3-venv python3-gpiozero \
  python3-lgpio i2c-tools libsdl2-2.0-0 libsdl2-ttf-2.0-0 libsdl2-image-2.0-0

echo ">> Screen + touch permissions for $USER_NAME..."
sudo usermod -aG video,render,input,tty,gpio,i2c,spi,dialout "$USER_NAME" 2>/dev/null || \
  sudo usermod -aG video,render,input,tty "$USER_NAME"

echo ">> Python environment (uses the system pygame/gpiozero)..."
python3 -m venv --system-site-packages "$DIR/venv"
"$DIR/venv/bin/pip" install -q -r "$DIR/requirements.txt" || \
  echo "!! sensor libraries failed to install - re-run install.sh with internet"

echo ">> Enabling GPS serial, I2C (ADS1115) and SPI (MAX31855)..."
sudo raspi-config nonint do_serial_hw 0 || true
sudo raspi-config nonint do_serial_cons 1 || true
sudo raspi-config nonint do_i2c 0 || true
sudo raspi-config nonint do_spi 0 || true
grep -q "^enable_uart=1" "$CFG" || echo "enable_uart=1" | sudo tee -a "$CFG" >/dev/null
grep -q "^dtoverlay=disable-bt" "$CFG" || echo "dtoverlay=disable-bt" | sudo tee -a "$CFG" >/dev/null
sudo systemctl disable hciuart 2>/dev/null || true
# pin 5 is the wake-from-halt pin; a gpio-shutdown overlay would turn it into a power button
sudo sed -i 's/^dtoverlay=gpio-shutdown/#dtoverlay=gpio-shutdown/' "$CFG"

echo ">> Passwordless power off (for auto-shutdown + POWER OFF button)..."
echo "$USER_NAME ALL=(ALL) NOPASSWD:/usr/bin/systemctl poweroff,/usr/sbin/poweroff,/sbin/poweroff" | \
  sudo tee /etc/sudoers.d/rb250-shutdown >/dev/null
sudo chmod 440 /etc/sudoers.d/rb250-shutdown

echo ">> Self-test..."
"$DIR/venv/bin/python" "$DIR/main.py" --selftest

echo ">> Boot straight into the dashboard..."
sed "s|__DIR__|$DIR|g; s|__USER__|$USER_NAME|g" "$DIR/rb250-dashboard.service" | \
  sudo tee /etc/systemd/system/rb250-dashboard.service >/dev/null
sudo systemctl daemon-reload
sudo systemctl enable rb250-dashboard.service
sudo systemctl set-default multi-user.target

echo ""
echo "=============================================================="
echo " RB250 installed.  Reboot to start:   sudo reboot"
echo " Logs:      journalctl -u rb250-dashboard -f"
echo " Stop:      sudo systemctl stop rb250-dashboard"
echo " Sensors:   bash sensor-test.sh      GPS: bash gps-test.sh"
echo " Screen size (only if the picture is wrong):  bash set-screen.sh 480x320"
echo " Optional RB250 boot logo:  bash setup-boot-splash.sh"
echo "=============================================================="
