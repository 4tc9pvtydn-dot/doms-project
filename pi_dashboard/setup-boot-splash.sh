#!/usr/bin/env bash
# Branded boot for the DOMS RB252 dashboard on Raspberry Pi OS (Bookworm).
# - Disables the firmware rainbow splash
# - Hides the raspberry logos + kernel boot text
# - Installs a Plymouth splash showing the DOMS logo from the first second,
#   which then hands over to the dashboard.
set -e

DIR="$(cd "$(dirname "$0")" && pwd)"

# Bookworm keeps the firmware config in /boot/firmware; older images use /boot.
BOOT=/boot/firmware
[ -d "$BOOT" ] || BOOT=/boot
CONFIG="$BOOT/config.txt"
CMDLINE="$BOOT/cmdline.txt"
echo ">> Using boot dir: $BOOT"

echo ">> Installing Plymouth..."
sudo apt-get update
sudo apt-get install -y plymouth plymouth-themes

echo ">> Installing the DOMS Plymouth theme..."
THEME=/usr/share/plymouth/themes/doms
sudo mkdir -p "$THEME"
sudo cp "$DIR/assets/plymouth/doms.plymouth" "$THEME/doms.plymouth"
sudo cp "$DIR/assets/plymouth/doms.script"   "$THEME/doms.script"
sudo cp "$DIR/assets/boot_splash.png"        "$THEME/splash.png"

echo ">> Making DOMS the default boot theme (rebuilds initramfs)..."
sudo plymouth-set-default-theme -R doms

echo ">> Disabling the rainbow splash in $CONFIG..."
grep -q "^disable_splash=1" "$CONFIG" 2>/dev/null || \
  echo "disable_splash=1" | sudo tee -a "$CONFIG" >/dev/null

echo ">> Adding quiet/splash kernel params in $CMDLINE..."
# cmdline.txt MUST stay a single line; append params only if missing.
add_param() {
  grep -qF -- "$1" "$CMDLINE" || sudo sed -i "s/\$/ $1/" "$CMDLINE"
}
for p in quiet splash plymouth.ignore-serial-consoles logo.nologo \
         vt.global_cursor_default=0 loglevel=0 consoleblank=0; do
  add_param "$p"
done

echo ">> Redirecting boot text off the screen (console=tty3)..."
# All the kernel + systemd [FAILED]/[DEPEND] lines print to the console.
# Move the console to tty3 so the visible display (tty1) stays clean; the
# DOMS Plymouth splash shows, then the dashboard takes over - no error wall.
if grep -qE "console=tty[0-9]" "$CMDLINE"; then
  sudo sed -i -E 's/console=tty[0-9]+/console=tty3/g' "$CMDLINE"
elif ! grep -qF "console=tty3" "$CMDLINE"; then
  sudo sed -i 's/$/ console=tty3/' "$CMDLINE"
fi
sudo sed -i 's/  */ /g; s/^ //' "$CMDLINE"

echo ">> Disabling the login prompt on the visible console (getty@tty1)..."
sudo systemctl disable getty@tty1.service 2>/dev/null || true

echo ">> Disabling the desktop login manager (not used in console kiosk)..."
# lightdm was FAILING at boot and dragging plymouth-quit down with it.
sudo systemctl disable lightdm.service 2>/dev/null || true

echo ">> Silencing the failing swap/zram services (harmless on this kiosk)..."
# The 'resize swapfile' + zram cascade is pre-existing Pi OS noise and is not
# needed for the dashboard. Masking stops the [FAILED]/[DEPEND] lines.
for u in dphys-swapfile.service rpi-resize-swap-file.service \
         "systemd-zram-setup@zram0.service" dev-zram0.swap; do
  sudo systemctl mask "$u" 2>/dev/null || true
done

echo ""
echo "=================================================================="
echo " Branded boot installed. Reboot to see it:  sudo reboot"
echo " You should now see: DOMS logo (Plymouth) -> dashboard, no errors."
echo " Revert theme:   sudo plymouth-set-default-theme -R pix"
echo " Restore console: set console=tty1 in $CMDLINE + re-enable getty@tty1"
echo "=================================================================="

