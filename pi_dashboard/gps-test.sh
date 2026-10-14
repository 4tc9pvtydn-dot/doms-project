#!/usr/bin/env bash
# GPS diagnostic for the DOMS RB252 dashboard.
# Finds whether the module is streaming NMEA and at what baud rate.
# Run on the Pi:  bash gps-test.sh
set +e

PORT="${1:-/dev/serial0}"

echo ">> Stopping the dashboard to free the GPS port..."
sudo systemctl stop rb252-dashboard 2>/dev/null

BOOT=/boot/firmware; [ -d "$BOOT" ] || BOOT=/boot

echo ""
echo ">> Port: $PORT ->"; ls -l "$PORT" 2>/dev/null || echo "   (!! $PORT not found)"
echo ">> UART config in $BOOT/config.txt:"
grep -E "enable_uart|disable-bt|miniuart" "$BOOT/config.txt" 2>/dev/null || echo "   (none set - see fix below)"
echo ">> Serial console in use? (should say none):"
tr ' ' '\n' < /proc/cmdline | grep -iE "console=serial|console=ttyAMA|console=ttyS" || echo "   none (good)"
echo ""

FOUND=""
for b in 9600 38400 4800 57600 115200; do
  echo "================ trying ${b} baud ================"
  stty -F "$PORT" "$b" 2>/dev/null
  data=$(timeout 4 cat "$PORT" 2>/dev/null | tr -cd '\11\12\15\40-\176')
  echo "$data" | grep -a '\$G' | head -4
  if echo "$data" | grep -qa '\$G[PNL]'; then
    echo ">> *** NMEA DETECTED at ${b} baud ***"
    FOUND="$b"
  elif [ -n "$data" ]; then
    echo "   (got bytes but no NMEA - likely wrong baud or mini-UART noise)"
  else
    echo "   (no data)"
  fi
done

echo ""
echo "=================================================================="
if [ -n "$FOUND" ]; then
  echo " MODULE WORKS.  Set this in config.py:   GPS_BAUD = $FOUND"
  echo " Then look for a fix (needs clear sky): the RMC/GGA fields fill in"
  echo " and the module LED starts blinking once locked."
else
  echo " NO NMEA at any baud. Most likely causes:"
  echo "  1) UART not freed - run these then reboot and test again:"
  echo "       echo 'enable_uart=1'        | sudo tee -a $BOOT/config.txt"
  echo "       echo 'dtoverlay=disable-bt' | sudo tee -a $BOOT/config.txt"
  echo "       sudo systemctl disable hciuart"
  echo "  2) Wiring - GPS TX -> Pi pin 10 (RXD), GPS RX -> Pi pin 8 (TXD)"
  echo "     (TX/RX must CROSS), plus VCC and GND. Is the module LED lit?"
fi
echo " Restart dashboard:  sudo systemctl start rb252-dashboard"
echo "=================================================================="