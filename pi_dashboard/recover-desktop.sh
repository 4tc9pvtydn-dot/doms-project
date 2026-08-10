#!/usr/bin/env bash
# Recovery: undo the DOMS kiosk boot changes and return to normal Raspberry Pi OS.
# Use this if you're stuck in the dashboard/console and want the desktop (or a
# normal console) back. Run on the Pi:  bash recover-desktop.sh
set -e

echo ">> Stopping + disabling the dashboard service..."
sudo systemctl stop rb252-dashboard 2>/dev/null || true
sudo systemctl disable rb252-dashboard 2>/dev/null || true

echo ">> Re-enabling the login prompt (getty@tty1)..."
sudo systemctl enable getty@tty1.service 2>/dev/null || true

echo ">> Unmasking swap/zram services..."
sudo systemctl unmask dphys-swapfile.service rpi-resize-swap-file.service \
  "systemd-zram-setup@zram0.service" dev-zram0.swap 2>/dev/null || true

echo ">> Restoring the visible console (console=tty3 -> console=tty1)..."
BOOT=/boot/firmware
[ -d "$BOOT" ] || BOOT=/boot
sudo sed -i 's/console=tty3/console=tty1/g' "$BOOT/cmdline.txt"

echo ">> Restoring boot behaviour..."
# B4 = desktop autologin (Full image). Falls back to console autologin (B2)
# automatically if the desktop isn't installed / B4 fails (Lite image).
if ! sudo raspi-config nonint do_boot_behaviour B4 2>/dev/null; then
  echo "   (desktop not available - using console autologin instead)"
  sudo raspi-config nonint do_boot_behaviour B2 || true
fi

echo ""
echo "=================================================================="
echo " Recovery done. Reboot to return to normal Pi OS:  sudo reboot"
echo " To re-install the dashboard kiosk later:  bash install.sh"
echo "=================================================================="
