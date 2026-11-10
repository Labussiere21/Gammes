#!/usr/bin/env python3
"""
ScalaBass — contrôle de la théorie
==================================
À lancer depuis la racine du dépôt après toute modification des gammes, des
accords ou de chords-db.js :

    python _generator/audit_theory.py

Vérifie, sans rien modifier :
  1. gammes : intervalles croissants, orthographe (une lettre par degré, pas
     de triple altération), « mode N de … » annoncé = rotation réelle ;
  2. accords et arpèges : chaque note a un rôle et une orthographe cohérents ;
  3. positions de guitare affichées sur les pages : uniquement des notes de
     l'accord, tierce et septième présentes, fondamentale à la basse ;
  4. chords-db.js : positions qui contiennent une note étrangère à l'accord.
Code de sortie 1 s'il reste une erreur bloquante (points 1 à 3).
"""
import re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import generate as g, sb_common as c
import generate_chords_guitar as gc, generate_arpeges as ga

errors, warnings = [], []
RNG = {0: (0, 1), 1: (1, 3), 2: (2, 5), 3: (4, 6), 4: (6, 8), 5: (7, 10), 6: (9, 11)}
by = {s["id"]: s for s in g.SCALE_DEFS}

# 1. Gammes
for s in g.SCALE_DEFS:
    iv, ls = s["iv"], s["ls"]
    if len(iv) != len(ls) or iv != sorted(set(iv)) or iv[0] != 0 or ls != sorted(ls):
        errors.append(f"gamme {s['id']} : intervalles ou lettres incohérents")
        continue
    for l, i in zip(ls, iv):
        if not RNG[l][0] <= i <= RNG[l][1]:
            errors.append(f"gamme {s['id']} : degré {l + 1} à {i} demi-tons")
    for r in g.ROOTS:
        if any(len(n) > 3 for n in g.build_scale(r["name"], ls, iv)):
            errors.append(f"gamme {s['id']} en {r['name']} : triple altération")
    third = 'maj' if 4 in iv else 'min' if 3 in iv else None
    if third and s["fam"] != third and not (3 in iv and 4 in iv):
        errors.append(f"gamme {s['id']} : famille « {s['fam']} » mais tierce {third}")
    m = re.match(r'[Mm]ode (\w+) (.+)$', s.get("sub") or "")
    parents = {'harm.': 'harmonic', 'mél.': 'melodic', 'maj. harm.': 'harmonic_maj', 'dbl harm.': 'double_harm'}
    if m and m.group(2) in parents:
        p = by[parents[m.group(2)]]["iv"]
        k = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII'].index(m.group(1))
        if sorted((x - p[k]) % 12 for x in p) != iv:
            errors.append(f"gamme {s['id']} : n'est pas le {s['sub']}")

# 2. Accords et arpèges
for kind, items in (("accord", gc.ALL_CHORDS), ("arpège", ga.ALL_ARPS)):
    for ch in items:
        roles = [r for r, _ in c.chord_roles(ch["iv"])]
        if len(set(roles)) != len(roles):
            errors.append(f"{kind} {ch['id']} : rôle en double {roles}")
        for r in g.ROOTS:
            notes = c.chord_spelling(r["name"], ch["iv"])
            if [c.pc_of(n) for n in notes] != [(r["pc"] + i) % 12 for i in ch["iv"]]:
                errors.append(f"{kind} {ch['id']} en {r['name']} : orthographe fausse {notes}")

# 3. Positions affichées sur les pages d'accords
n_pos = 0
for ch in gc.ALL_CHORDS:
    for pc in range(12):
        vs = c.chord_voicings(pc, ch)
        if not vs:
            errors.append(f"accord {ch['id']} (tonique {pc}) : aucune position")
        for v in vs:
            n_pos += 1
            if not c.voicing_ok(v["frets"], pc, ch["iv"]):
                errors.append(f"accord {ch['id']} (tonique {pc}) : position invalide {v['frets']}")

# 4. Base brute
db = c.load_chords_db()
suffix_iv = {c.ID_TO_SUFFIX[ch["id"]]: ch["iv"] for ch in gc.ALL_CHORDS if ch["id"] in c.ID_TO_SUFFIX}
n_db = bad_db = 0
for k, key in enumerate(c.DB_KEYS):
    for entry in db["chords"][key]:
        iv = suffix_iv.get(entry["suffix"])
        if iv is None:
            continue
        allowed = {i % 12 for i in iv}
        for p in entry["positions"]:
            n_db += 1
            bf = p.get("baseFret", 1)
            pcs = {(c.GUITAR_OPEN[s] + (f if f == 0 else f + bf - 1) - k) % 12
                   for s, f in enumerate(p["frets"]) if f >= 0}
            if not pcs <= allowed:
                bad_db += 1
                warnings.append(f"chords-db {entry['key']}{entry['suffix']} {p['frets']} (case {bf}) : note étrangère")

print(f"{len(g.SCALE_DEFS)} gammes, {len(gc.ALL_CHORDS)} accords, {len(ga.ALL_ARPS)} arpèges contrôlés")
print(f"{n_pos} positions d'accords affichées sur les pages : toutes vérifiées" if not errors else "")
print(f"chords-db.js : {bad_db} positions sur {n_db} contiennent une note étrangère "
      f"(elles sont écartées des pages et de l'appli par la validation)")
for w in warnings[:10]:
    print("  ·", w)
if len(warnings) > 10:
    print(f"  · … et {len(warnings) - 10} autres")
if errors:
    print(f"\n{len(errors)} ERREUR(S) :")
    for e in errors[:60]:
        print("  ✗", e)
    sys.exit(1)
print("\nAucune erreur.")
