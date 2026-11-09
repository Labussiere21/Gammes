#!/usr/bin/env bash
# Installe GrilleMaker pour l'utilisateur courant (Linux)
set -e
SRC="$(cd "$(dirname "$0")" && pwd)"
DEST="$HOME/.local/share/grillemaker"
BIN="$HOME/.local/bin"
echo "→ Vérification de python3-tk…"
python3 -c "import tkinter" 2>/dev/null || {
  echo "tkinter manquant : sudo apt install python3-tk python3-venv (ou équivalent)"; exit 1; }
mkdir -p "$DEST" "$BIN" "$HOME/.local/share/applications"
cp -r "$SRC"/app.py "$SRC"/model.py "$SRC"/pdf_render.py "$SRC"/icon.png "$SRC"/exemples "$SRC"/requirements.txt "$DEST"/
echo "→ Environnement Python…"
python3 -m venv "$DEST/venv"
"$DEST/venv/bin/pip" install -q --upgrade pip
"$DEST/venv/bin/pip" install -q -r "$DEST/requirements.txt"
cat > "$BIN/grillemaker" << EOS
#!/usr/bin/env bash
exec "$DEST/venv/bin/python" "$DEST/app.py" "\$@"
EOS
chmod +x "$BIN/grillemaker"
cat > "$HOME/.local/share/applications/grillemaker.desktop" << EOS
[Desktop Entry]
Name=GrilleMaker
Comment=Générateur de grilles d'accords
Exec=$BIN/grillemaker %f
Icon=$DEST/icon.png
Terminal=false
Type=Application
Categories=Audio;Music;
EOS
echo "✓ Installé. Lance « grillemaker » ou via le menu des applications."
