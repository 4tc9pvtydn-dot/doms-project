#!/usr/bin/env bash
# OPTIONAL: show the RB250 logo from the first second of boot (Plymouth).
# Run only after the dashboard is confirmed working. Undo:
#   sudo plymouth-set-default-theme -R pix
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
BOOT=/boot/firmware; [ -d "$BOOT" ] || BOOT=/boot

sudo apt-get install -y plymouth plymouth-themes
THEME=/usr/share/plymouth/themes/rb250
sudo mkdir -p "$THEME"
sudo cp "$DIR/assets/plymouth/rb250.plymouth" "$THEME/"
sudo cp "$DIR/assets/plymouth/rb250.script" "$THEME/"
sudo cp "$DIR/assets/boot_splash.png" "$THEME/splash.png"
sudo plymouth-set-default-theme -R rb250

grep -q "^disable_splash=1" "$BOOT/config.txt" || echo "disable_splash=1" | sudo tee -a "$BOOT/config.txt" >/dev/null
for p in quiet splash logo.nologo; do
  grep -qw -- "$p" "$BOOT/cmdline.txt" || sudo sed -i "1 s/\$/ $p/" "$BOOT/cmdline.txt"
done
echo ">> RB250 boot logo installed. Reboot to see it. (Login console is kept.)"
