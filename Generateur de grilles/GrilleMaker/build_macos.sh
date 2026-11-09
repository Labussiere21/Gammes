#!/usr/bin/env bash
# Build macOS (.app) — nécessite Python 3 (python.org, avec Tk)
set -e; cd "$(dirname "$0")"
python3 -m pip install -r requirements.txt pyinstaller
python3 -m PyInstaller --noconfirm --clean --windowed --name GrilleMaker \
  --add-data "exemples:exemples" --add-data "icon.png:." app.py
echo "✓ dist/GrilleMaker.app"
