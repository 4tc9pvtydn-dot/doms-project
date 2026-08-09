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
sudo sed -i 's/  */ /g; s/^ //' "$CMDLINE"

echo ""
echo "=================================================================="
echo " Branded boot installed. Reboot to see it:  sudo reboot"
echo " You should now see: DOMS logo (Plymouth) -> dashboard."
echo " Revert theme:  sudo plymouth-set-default-theme -R pix"
echo "=================================================================="
