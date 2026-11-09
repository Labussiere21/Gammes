# GrilleMaker

Générateur de grilles d'accords (basse, guitare…) avec structure du morceau et export PDF portrait/paysage.

## Lancer directement (sans installer)
```
pip install -r requirements.txt
python app.py
```

## Installer
- **Windows** : installe Python 3.10+ et Inno Setup 6, puis double-clic sur `build_windows.bat`
  → `Output\GrilleMaker-Setup.exe` (raccourci Bureau + association des fichiers `.grille`).
- **Linux** : `./install_linux.sh` (désinstaller : `./uninstall_linux.sh`)
- **macOS** : `./build_macos.sh` → `dist/GrilleMaker.app`

## Utilisation
**Onglet Grilles**
- Ajoute une section (Intro, Couplet, Refrain, Pont, Solo, Outro…), règle le nombre de cellules par ligne et de lignes.
- Tape les accords. Deux accords dans une mesure : `C Bb` ou `C, Bb` → diagonale dans le PDF. `C/E` reste un renversement.
- Boutons : `‖:` début de reprise, `:‖` fin de reprise, **Répéter x** (x8…), cases **1.** / **2.**, `%` même mesure.
- Petite ligne sous l'accord : indication (rythme, « syncopé »…).
- Le nombre de mesures est calculé automatiquement (reprises et cases 1./2. comprises) ; décoche « Calcul auto » pour le forcer.
- Les cases vides en fin de ligne ne sont pas imprimées.

**Onglet Structure**
- Générateur : indique combien d'intros, couplets, refrains, solos… → numérotation automatique et chaque partie est reliée à sa grille (Couplet 3 → grille Couplet 1).
- Ajuste ensuite : ordre, grille jouée (ex. Solo = grille du Couplet 2), nom perso (« Refrain de fin »), note.

**PDF** : choisis Portrait ou Paysage puis « Générer le PDF ». La mise en page essaie de tout faire tenir sur une page (2 colonnes en paysage), sinon passe sur plusieurs pages.

Fichiers enregistrés en `.grille` (JSON). Bouton **Exemple** : Sultans of Swing.
