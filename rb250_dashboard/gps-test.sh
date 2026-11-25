#!/bin/bash
# Show 10 seconds of raw GPS data at 9600 baud.
sudo systemctl stop rb250-dashboard 2>/dev/null
echo ">> /dev/serial0 -> $(readlink /dev/serial0)"
stty -F /dev/serial0 9600 raw -echo
echo ">> Raw GPS (look for \$GNRMC / \$GPGGA / \$GPGSV lines):"
timeout 10 cat /dev/serial0
echo ""
echo ">> Nothing above?  Check GPS TX -> pin 10, GPS RX -> pin 8, VCC + GND."
echo ">> In \$..GGA the 8th value = satellites used (00 = no lock yet)."
echo ">> Restart the dashboard with:  sudo systemctl start rb250-dashboard"
