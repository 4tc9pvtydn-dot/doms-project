#!/usr/bin/env bash
# One-shot installer for the DOMS RB252 dashboard on Raspberry Pi OS.
# Sets up a Python venv, installs pygame, and enables boot-on-power-up.
set -e

DIR="$(cd "$(dirname "$0")" && pwd)"
USER_NAME="$(whoami)"

echo ">> Installing system packages (pygame SDL runtime)..."
sudo apt-get update
sudo apt-get install -y python3-venv python3-pip \
  libsdl2-2.0-0 libsdl2-image-2.0-0 libsdl2-mixer-2.0-0 libsdl2-ttf-2.0-0 \
  libfreetype6 libportmidi0

echo ">> Creating virtual environment..."
python3 -m venv "$DIR/venv"
"$DIR/venv/bin/pip" install --upgrade pip
"$DIR/venv/bin/pip" install -r "$DIR/requirements.txt"

echo ">> Quick self-test..."
"$DIR/venv/bin/python" "$DIR/main.py" --selftest

echo ">> Installing systemd service (boot straight to dashboard)..."
sed "s|__DIR__|$DIR|g; s|__USER__|$USER_NAME|g" \
  "$DIR/rb252-dashboard.service" | sudo tee /etc/systemd/system/rb252-dashboard.service > /dev/null
sudo systemctl daemon-reload
sudo systemctl enable rb252-dashboard.service

echo ""
echo "=================================================================="
echo " Done. The dashboard will launch automatically on next boot."
echo " Start now:   sudo systemctl start rb252-dashboard"
echo " View logs:   journalctl -u rb252-dashboard -f"
echo " Stop:        sudo systemctl stop rb252-dashboard"
echo "=================================================================="
