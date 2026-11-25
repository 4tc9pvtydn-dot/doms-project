#!/bin/bash
# Force the HDMI output resolution, e.g.:  bash set-screen.sh 480x320
# Only needed if the 3.5" HDMI screen shows a cropped/blank/wrong picture.
# Undo:  bash set-screen.sh auto
set -e
MODE="$1"
BOOT=/boot/firmware; [ -d "$BOOT" ] || BOOT=/boot
CMDLINE="$BOOT/cmdline.txt"
[ -n "$MODE" ] || { echo "usage: bash set-screen.sh 480x320 | 800x480 | auto"; exit 1; }
sudo cp "$CMDLINE" "$CMDLINE.bak"
sudo sed -i -E 's/ ?video=HDMI-A-1:[^ ]*//g' "$CMDLINE"
if [ "$MODE" != "auto" ]; then
  sudo sed -i "1 s/\$/ video=HDMI-A-1:${MODE}M@60D/" "$CMDLINE"
fi
echo ">> cmdline.txt is now:"; cat "$CMDLINE"
echo ">> Reboot to apply:  sudo reboot   (backup saved as cmdline.txt.bak)"
