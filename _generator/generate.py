#!/usr/bin/env python3
"""
ScalaBass — Générateur de pages statiques SEO
==============================================
Génère fr/gammes/{note}/{gamme}/index.html  (72 gammes × 12 toniques = 864 pages)
Génère aussi fr/gammes/index.html (hub de toutes les gammes)
Génère aussi sitemap.xml (mis à jour)

Lancer depuis la racine du repo :
    pip install -r _generator/requirements.txt
    python _generator/generate.py
"""

import os, re
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
REPO_ROOT  = Path(__file__).parent.parent
OUT_ROOT   = REPO_ROOT / "fr" / "gammes"
TMPL_DIR   = Path(__file__).parent / "templates"
BASE_URL   = "https://labussiere21.github.io/Gammes"
APP_URL    = f"{BASE_URL}/index.html"

# ---------------------------------------------------------------------------
# DONNÉES : NOTES (12 toniques canoniques)
# ---------------------------------------------------------------------------
ROOTS = [
    {"pc": 0,  "name": "C",  "fr": "Do",   "slug": "do"},
    {"pc": 1,  "name": "Db", "fr": "Réb",  "slug": "re-bemol"},
    {"pc": 2,  "name": "D",  "fr": "Ré",   "slug": "re"},
    {"pc": 3,  "name": "Eb", "fr": "Mib",  "slug": "mi-bemol"},
    {"pc": 4,  "name": "E",  "fr": "Mi",   "slug": "mi"},
    {"pc": 5,  "name": "F",  "fr": "Fa",   "slug": "fa"},
    {"pc": 6,  "name": "F#", "fr": "Fa#",  "slug": "fa-diese"},
    {"pc": 7,  "name": "G",  "fr": "Sol",  "slug": "sol"},
    {"pc": 8,  "name": "Ab", "fr": "Lab",  "slug": "la-bemol"},
    {"pc": 9,  "name": "A",  "fr": "La",   "slug": "la"},
    {"pc": 10, "name": "Bb", "fr": "Sib",  "slug": "si-bemol"},
    {"pc": 11, "name": "B",  "fr": "Si",   "slug": "si"},
]

# ---------------------------------------------------------------------------
# DONNÉES : GAMMES (extraites de SCALE_DEFS dans index.html)
# ---------------------------------------------------------------------------
SCALE_DEFS = [
    # GROUPE 0 — MODES DIATONIQUES
    {"id":"major",           "label":"Majeure",                "sub":"Ionien",              "group":0,"diat":True, "fam":"maj","ls":[0,1,2,3,4,5,6],"iv":[0,2,4,5,7,9,11]},
    {"id":"minor",           "label":"Mineure naturelle",      "sub":"Éolien",              "group":0,"diat":True, "fam":"min","ls":[0,1,2,3,4,5,6],"iv":[0,2,3,5,7,8,10]},
    {"id":"harmonic",        "label":"Mineure harmonique",     "sub":"",                    "group":0,"diat":True, "fam":"min","ls":[0,1,2,3,4,5,6],"iv":[0,2,3,5,7,8,11]},
    {"id":"melodic",         "label":"Mineure mélodique",      "sub":"",                    "group":0,"diat":True, "fam":"min","ls":[0,1,2,3,4,5,6],"iv":[0,2,3,5,7,9,11]},
    {"id":"dorian",          "label":"Dorien",                 "sub":"mode II",             "group":0,"diat":True, "fam":"min","ls":[0,1,2,3,4,5,6],"iv":[0,2,3,5,7,9,10]},
    {"id":"phrygian",        "label":"Phrygien",               "sub":"mode III",            "group":0,"diat":True, "fam":"min","ls":[0,1,2,3,4,5,6],"iv":[0,1,3,5,7,8,10]},
    {"id":"lydian",          "label":"Lydien",                 "sub":"mode IV",             "group":0,"diat":True, "fam":"maj","ls":[0,1,2,3,4,5,6],"iv":[0,2,4,6,7,9,11]},
    {"id":"mixolydian",      "label":"Mixolydien",             "sub":"mode V",              "group":0,"diat":True, "fam":"maj","ls":[0,1,2,3,4,5,6],"iv":[0,2,4,5,7,9,10]},
    {"id":"locrian",         "label":"Locrien",                "sub":"mode VII",            "group":0,"diat":True, "fam":"min","ls":[0,1,2,3,4,5,6],"iv":[0,1,3,5,6,8,10]},
    # GROUPE 1 — PENTATONIQUES, BLUES, SYMÉTRIQUES
    {"id":"penta_min",       "label":"Pentatonique mineure",   "sub":"5 notes",             "group":1,"diat":False,"fam":"min","ls":[0,2,3,4,6],       "iv":[0,3,5,7,10]},
    {"id":"penta_maj",       "label":"Pentatonique majeure",   "sub":"5 notes",             "group":1,"diat":False,"fam":"maj","ls":[0,1,2,4,5],       "iv":[0,2,4,7,9]},
    {"id":"blues_min",       "label":"Blues mineure",          "sub":"6 notes",             "group":1,"diat":False,"fam":"min","ls":[0,2,3,4,4,6],     "iv":[0,3,5,6,7,10]},
    {"id":"blues_maj",       "label":"Blues majeure",          "sub":"6 notes",             "group":1,"diat":False,"fam":"maj","ls":[0,1,2,2,4,5],     "iv":[0,2,3,4,7,9]},
    {"id":"penta_dom",       "label":"Pentatonique dominante", "sub":"5 notes",             "group":1,"diat":False,"fam":"maj","ls":[0,1,2,4,5],       "iv":[0,2,4,7,10]},
    {"id":"penta_min6",      "label":"Pentatonique mineure 6", "sub":"5 notes",             "group":1,"diat":False,"fam":"min","ls":[0,2,3,5,6],       "iv":[0,3,5,9,10]},
    {"id":"penta_sus",       "label":"Pentatonique sus",       "sub":"5 notes",             "group":1,"diat":False,"fam":"maj","ls":[0,1,3,4,6],       "iv":[0,2,5,7,10]},
    {"id":"blues_dom",       "label":"Blues dominante",        "sub":"6 notes",             "group":1,"diat":False,"fam":"maj","ls":[0,1,2,3,4,5],     "iv":[0,2,4,6,7,10]},
    {"id":"blues_hex",       "label":"Blues hexatonique",      "sub":"6 notes",             "group":1,"diat":False,"fam":"min","ls":[0,1,2,3,4,6],     "iv":[0,2,3,5,7,10]},
    {"id":"penta_maj7",      "label":"Pentatonique majeure 7", "sub":"5 notes",             "group":1,"diat":False,"fam":"maj","ls":[0,1,2,4,5],       "iv":[0,2,4,7,11]},
    {"id":"penta_min_lead",  "label":"Pentatonique min. guidage","sub":"6 notes",           "group":1,"diat":False,"fam":"min","ls":[0,2,3,4,6,6],     "iv":[0,3,5,7,10,11]},
    {"id":"boogie",          "label":"Rock'n'Roll / Boogie",   "sub":"7 notes",             "group":1,"diat":False,"fam":"maj","ls":[0,1,2,2,4,5,6],   "iv":[0,2,3,4,7,9,10]},
    {"id":"penta_majb2",     "label":"Pentatonique maj. b2",   "sub":"5 notes",             "group":1,"diat":False,"fam":"maj","ls":[0,1,2,4,5],       "iv":[0,1,4,7,9]},
    {"id":"dim",             "label":"Diminuée T-½T",          "sub":"8 notes, symétrique", "group":1,"diat":False,"fam":"min","ls":[0,1,2,3,4,5,5,6], "iv":[0,2,3,5,6,8,9,11]},
    {"id":"dim_ht",          "label":"Diminuée ½T-T",          "sub":"8 notes, symétrique", "group":1,"diat":False,"fam":"min","ls":[0,0,1,2,3,4,5,6], "iv":[0,1,3,4,6,7,9,10]},
    {"id":"half_dim",        "label":"Demi-diminuée",          "sub":"= Locrien",           "group":1,"diat":False,"fam":"min","ls":[0,1,2,3,4,5,6],   "iv":[0,1,3,5,6,8,10]},
    {"id":"whole_tone",      "label":"Par ton",                "sub":"6 notes, symétrique", "group":1,"diat":False,"fam":"maj","ls":[0,1,2,3,4,5],     "iv":[0,2,4,6,8,10]},
    {"id":"aug_hex",         "label":"Hexatonique augmentée",  "sub":"6 notes, symétrique", "group":1,"diat":False,"fam":"maj","ls":[0,1,2,3,4,5],     "iv":[0,3,4,7,8,11]},
    {"id":"chromatic",       "label":"Chromatique",            "sub":"12 notes",            "group":1,"diat":False,"fam":"maj","ls":list(range(12)),   "iv":list(range(12))},
    # GROUPE 2 — MODES JAZZ
    {"id":"phryg_dom",       "label":"Phrygien dominant",      "sub":"Mode V harm.",        "group":2,"diat":False,"fam":"maj","ls":[0,1,2,3,4,5,6],"iv":[0,1,4,5,7,8,10]},
    {"id":"lydian_dom",      "label":"Lydien dominant",        "sub":"Mode IV mél.",        "group":2,"diat":False,"fam":"maj","ls":[0,1,2,3,4,5,6],"iv":[0,2,4,6,7,9,10]},
    {"id":"altered",         "label":"Altérée",                "sub":"Mode VII mél.",       "group":2,"diat":False,"fam":"min","ls":[0,1,2,2,4,5,6],"iv":[0,1,3,4,6,8,10]},
    {"id":"locrian_s2",      "label":"Locrien #2",             "sub":"Mode VI mél.",        "group":2,"diat":False,"fam":"min","ls":[0,1,2,3,4,5,6],"iv":[0,2,3,5,6,8,10]},
    {"id":"lydian_aug",      "label":"Lydien augmenté",        "sub":"Mode III mél.",       "group":2,"diat":False,"fam":"maj","ls":[0,1,2,3,4,5,6],"iv":[0,2,4,6,8,9,11]},
    {"id":"mixo_b6",         "label":"Mixolydien b6",          "sub":"Mode V mél.",         "group":2,"diat":False,"fam":"maj","ls":[0,1,2,3,4,5,6],"iv":[0,2,4,5,7,8,10]},
    {"id":"dorian_b2",       "label":"Dorien b2",              "sub":"Mode II mél.",        "group":2,"diat":False,"fam":"min","ls":[0,1,2,3,4,5,6],"iv":[0,1,3,5,7,9,10]},
    {"id":"locrian6",        "label":"Locrien nat.6",          "sub":"Mode II harm.",       "group":2,"diat":False,"fam":"min","ls":[0,1,2,3,4,5,6],"iv":[0,1,3,5,6,9,10]},
    {"id":"ionian_s5",       "label":"Ionien #5",              "sub":"Mode III harm.",      "group":2,"diat":False,"fam":"maj","ls":[0,1,2,3,4,5,6],"iv":[0,2,4,5,8,9,11]},
    {"id":"dorian_s4",       "label":"Dorien #4",              "sub":"Mode IV harm.",       "group":2,"diat":False,"fam":"min","ls":[0,1,2,3,4,5,6],"iv":[0,2,3,6,7,9,10]},
    {"id":"lydian_s2",       "label":"Lydien #2",              "sub":"Mode VI harm.",       "group":2,"diat":False,"fam":"maj","ls":[0,1,2,3,4,5,6],"iv":[0,3,4,6,7,9,11]},
    {"id":"superlocrian_bb7","label":"Super Locrien bb7",      "sub":"Mode VII harm.",      "group":2,"diat":False,"fam":"min","ls":[0,1,2,3,4,5,6],"iv":[0,1,3,4,6,8,9]},
    {"id":"bebop_maj",       "label":"Bebop majeure",          "sub":"8 notes (#5)",        "group":2,"diat":False,"fam":"maj","ls":[0,1,2,3,4,4,5,6],"iv":[0,2,4,5,7,8,9,11]},
    {"id":"bebop_dom",       "label":"Bebop dominante",        "sub":"8 notes",             "group":2,"diat":False,"fam":"maj","ls":[0,1,2,3,4,5,6,6],"iv":[0,2,4,5,7,9,10,11]},
    {"id":"bebop_min",       "label":"Bebop mineure",          "sub":"8 notes",             "group":2,"diat":False,"fam":"min","ls":[0,1,2,3,3,4,5,6],"iv":[0,2,3,4,5,7,9,10]},
    # GROUPE 3 — EXOTIQUES
    {"id":"double_harm",     "label":"Double harmonique",      "sub":"Byzantine / Tsigane", "group":3,"diat":False,"fam":"maj","ls":[0,1,2,3,4,5,6],"iv":[0,1,4,5,7,8,11]},
    {"id":"hung_min",        "label":"Mineure hongroise",      "sub":"Gypsy minor",         "group":3,"diat":False,"fam":"min","ls":[0,1,2,3,4,5,6],"iv":[0,2,3,6,7,8,11]},
    {"id":"hung_maj",        "label":"Majeure hongroise",      "sub":"Hungarian major",     "group":3,"diat":False,"fam":"maj","ls":[0,1,2,3,4,5,6],"iv":[0,3,4,6,7,9,10]},
    {"id":"gypsy_maj",       "label":"Tzigane majeure",        "sub":"Gypsy major",         "group":3,"diat":False,"fam":"maj","ls":[0,1,2,3,4,5,6],"iv":[0,1,4,5,7,8,10]},
    {"id":"romanian_min",    "label":"Mineure roumaine",       "sub":"Dorien #4",           "group":3,"diat":False,"fam":"min","ls":[0,1,2,3,4,5,6],"iv":[0,2,3,6,7,9,10]},
    {"id":"persian",         "label":"Persane",                "sub":"Exotique",            "group":3,"diat":False,"fam":"min","ls":[0,1,2,3,4,5,6],"iv":[0,1,4,5,6,8,11]},
    {"id":"arabic",          "label":"Arabe",                  "sub":"Exotique",            "group":3,"diat":False,"fam":"maj","ls":[0,1,2,3,4,5,6],"iv":[0,2,4,5,6,8,10]},
    {"id":"enigmatic",       "label":"Enigmatique",            "sub":"Verdi",               "group":3,"diat":False,"fam":"maj","ls":[0,1,2,3,4,5,6],"iv":[0,1,4,6,8,10,11]},
    {"id":"napolitaine_maj", "label":"Napolitaine majeure",    "sub":"Exotique",            "group":3,"diat":False,"fam":"maj","ls":[0,1,2,3,4,5,6],"iv":[0,1,3,5,7,9,11]},
    {"id":"napolitaine_min", "label":"Napolitaine mineure",    "sub":"Exotique",            "group":3,"diat":False,"fam":"min","ls":[0,1,2,3,4,5,6],"iv":[0,1,3,5,7,8,11]},
    {"id":"prometheus",      "label":"Prometheus",             "sub":"Scriabine",           "group":3,"diat":False,"fam":"maj","ls":[0,1,2,3,5,6],   "iv":[0,2,4,6,9,10]},
    {"id":"overtone",        "label":"Acoustique (Overtone)",  "sub":"= Lydien dominant",   "group":3,"diat":False,"fam":"maj","ls":[0,1,2,3,4,5,6],"iv":[0,2,4,6,7,9,10]},
    {"id":"hijaz",           "label":"Hijaz",                  "sub":"Maqam",               "group":3,"diat":False,"fam":"min","ls":[0,1,2,3,4,5,6],"iv":[0,1,4,5,7,8,10]},
    {"id":"hijaz_kar",       "label":"Hijaz Kar",              "sub":"Maqam",               "group":3,"diat":False,"fam":"min","ls":[0,1,2,3,4,5,6],"iv":[0,1,4,5,7,8,11]},
    {"id":"bayati",          "label":"Bayati",                 "sub":"Maqam",               "group":3,"diat":False,"fam":"min","ls":[0,1,2,3,4,5,6],"iv":[0,1,3,5,7,8,10]},
    {"id":"nahawand",        "label":"Nahawand",               "sub":"Maqam",               "group":3,"diat":False,"fam":"min","ls":[0,1,2,3,4,5,6],"iv":[0,2,3,5,7,8,11]},
    {"id":"rast",            "label":"Rast",                   "sub":"Maqam",               "group":3,"diat":False,"fam":"maj","ls":[0,1,2,3,4,5,6],"iv":[0,2,4,5,7,9,10]},
    {"id":"nikriz",          "label":"Nikriz",                 "sub":"Maqam",               "group":3,"diat":False,"fam":"min","ls":[0,1,2,3,4,5,6],"iv":[0,2,3,6,7,8,10]},
    {"id":"saba",            "label":"Saba",                   "sub":"Maqam",               "group":3,"diat":False,"fam":"min","ls":[0,1,2,3,4,5,6],"iv":[0,1,3,4,6,8,10]},
    {"id":"kurd",            "label":"Kurd",                   "sub":"Maqam",               "group":3,"diat":False,"fam":"min","ls":[0,1,2,3,4,5,6],"iv":[0,1,3,5,7,8,10]},
    {"id":"hirajoshi",       "label":"Hirajoshi",              "sub":"Japonaise, 5 notes",  "group":3,"diat":False,"fam":"min","ls":[0,1,2,4,5],     "iv":[0,2,3,7,8]},
    {"id":"insen",           "label":"Insen",                  "sub":"Japonaise, 5 notes",  "group":3,"diat":False,"fam":"min","ls":[0,1,3,4,6],     "iv":[0,1,5,7,10]},
    {"id":"kumoi",           "label":"Kumoi",                  "sub":"Japonaise, 5 notes",  "group":3,"diat":False,"fam":"min","ls":[0,1,2,4,5],     "iv":[0,2,3,7,9]},
    {"id":"iwato",           "label":"Iwato",                  "sub":"Japonaise, 5 notes",  "group":3,"diat":False,"fam":"min","ls":[0,1,3,4,6],     "iv":[0,1,5,6,10]},
    {"id":"yo",              "label":"Yo",                     "sub":"Japonaise, 5 notes",  "group":3,"diat":False,"fam":"maj","ls":[0,1,3,4,5],     "iv":[0,2,5,7,9]},
    {"id":"bhairav",         "label":"Bhairav",                "sub":"Raga indien",         "group":3,"diat":False,"fam":"maj","ls":[0,1,2,3,4,5,6],"iv":[0,1,4,5,7,8,11]},
    {"id":"todi",            "label":"Todi",                   "sub":"Raga indien",         "group":3,"diat":False,"fam":"min","ls":[0,1,2,3,4,5,6],"iv":[0,1,3,6,7,8,11]},
    {"id":"kafi",            "label":"Kafi",                   "sub":"Raga indien",         "group":3,"diat":False,"fam":"min","ls":[0,1,2,3,4,5,6],"iv":[0,2,3,5,7,9,10]},
    {"id":"kalyan",          "label":"Kalyan",                 "sub":"Raga indien",         "group":3,"diat":False,"fam":"maj","ls":[0,1,2,3,4,5,6],"iv":[0,2,4,6,7,9,11]},
]

# ---------------------------------------------------------------------------
# DESCRIPTIONS PAR GAMME (unique, pour le SEO on-page)
# ---------------------------------------------------------------------------
SCALE_DESCS = {
    "major":        "La gamme majeure est le fondement de toute la théorie musicale occidentale. Lumineuse et stable, elle structure la majorité des morceaux de rock, pop, jazz et musique classique. Pour la basse, elle fournit la feuille de route naturelle pour construire des lignes dans n'importe quelle tonalité majeure.",
    "minor":        "La gamme mineure naturelle (mode éolien) est la gamme mineure de référence. Plus sombre et expressive que la majeure, elle est omniprésente dans le rock, la pop mélancolique, le métal et le jazz. Les lignes de basse en mineur naturel soulignent parfaitement l'émotion de la tonalité.",
    "harmonic":     "La gamme mineure harmonique se distingue par sa seconde augmentée (3 demi-tons) entre le 6e et le 7e degré. Ce saut caractéristique lui donne un caractère dramatique et orientalisant très présent dans la musique classique, le flamenco et les films d'action. La 7e sensible crée une forte tension vers la tonique.",
    "melodic":      "La gamme mineure mélodique (ascendante) monte avec un 6e et 7e degrés naturels, ce qui fluidifie le mouvement mélodique. Elle est au cœur du langage jazz moderne : indispensable sur les accords mineurs avec majeure 7, les ii demi-diminués et les dominantes altérées.",
    "dorian":       "Le mode dorien est la gamme mineure avec une 6te majeure — c'est la couleur du jazz et du funk par excellence. On la retrouve dans 'So What' de Miles Davis, 'Oye Como Va' de Santana, ou encore sous les doigts de Jaco Pastorius. Pour la basse, c'est le mode le plus polyvalent en mineur.",
    "phrygian":     "Le mode phrygien est caractérisé par sa 2nde mineure (demi-ton entre 1er et 2e degré), qui lui confère un caractère espagnol et métal. Incontournable pour les riffs heavy, la musique ibérique et le flamenco. À la basse, il crée une tension immédiate dès les premières notes.",
    "lydian":       "Le mode lydien, avec sa 4te augmentée (#4), sonne rêveur et flottant. Très utilisé dans la musique de film (John Williams, Ennio Morricone) et le jazz modal. À la basse, les lignes lydiennes apportent une légèreté et une luminosité inhabituelles.",
    "mixolydian":   "Le mode mixolydien est la gamme majeure avec une 7ème mineure (b7) — c'est le son du blues, du rock et de la funk. Il sonne naturellement sur tous les accords dominants (7e). Pour la basse, il est incontournable dans le blues, le rock classique (Rolling Stones, Hendrix) et toute musique groovy.",
    "locrian":      "Le mode locrien, avec sa 5te diminuée (b5), est le plus instable des modes diatoniques. Rare à l'état pur, il s'utilise principalement sur les accords demi-diminués (iiø7) dans les cadences jazz. La basse l'emploie comme couleur passagère pour renforcer cette instabilité harmonique.",
    "penta_min":    "La pentatonique mineure est la gamme la plus jouée à la basse. Ses 5 notes sans demi-tons sonnent naturellement sur le blues, le rock et le funk. Sa simplicité apparente cache une richesse infinie : c'est la base de la quasi-totalité des solos et des lignes de basse improvisées en mineur.",
    "penta_maj":    "La pentatonique majeure est la version lumineuse de la pentatonique. Ses 5 notes coulent avec fluidité sur la majorité des progressions majeures. Très présente dans le country, la pop et le rock, elle est l'outil privilégié pour construire des lignes de basse chantantes sans risque de fausse note.",
    "blues_min":    "La gamme blues mineure ajoute la 'blue note' (b5, le triton) à la pentatonique mineure. C'est cette note dissonante qui crée le caractère 'sale' et expressif du blues. Pour la basse, ce b5 de passage entre la 4te et la 5te parfaite est une signature stylistique incontournable.",
    "blues_maj":    "La gamme blues majeure enrichit la pentatonique majeure avec la b3 (tierce mineure), apportant l'ambiguïté majeur/mineur propre au blues et au rock'n'roll. Ce mélange de lumière et de tension est au cœur du son de Chuck Berry, Elvis Presley et de tout le rock originel.",
    "penta_dom":    "La pentatonique dominante (ou pentatonique mixolydienne) contient la b7, ce qui la rend parfaitement adaptée aux accords dominants (7e). Très utilisée dans le blues, le funk et le jazz fusion, elle sonne sur les accords V7 avec un caractère tendu et groovy.",
    "penta_min6":   "La pentatonique mineure 6 contient la 6te majeure en plus des notes mineures habituelles. Cette couleur est très utilisée dans le jazz et la bossa nova pour donner un caractère plus ouvert et lumineux à des contextes mineurs. Elle sonne particulièrement bien sur les accords mineurs 6.",
    "penta_sus":    "La pentatonique sus (ou pentatonique de quarte suspendue) ne contient ni 3ce majeure ni 3ce mineure, ce qui lui donne un caractère ambigu et flottant. Elle est très prisée dans le jazz modal, l'ambient et la musique contemporaine pour créer des atmosphères sans résolution claire.",
    "blues_dom":    "La gamme blues dominante enrichit la pentatonique dominante avec le triton (#4/b5). Très proche de la gamme acoustique/lydien dominant, elle sonne avec une tension maximale sur les accords dominants altérés. Indispensable pour les lignes de basse jazz-blues expressives.",
    "blues_hex":    "La gamme blues hexatonique (6 notes) est une variante de la pentatonique mineure enrichie. Elle offre plus de couleurs que la pentatonique classique tout en gardant son caractère blues. Très utilisée dans le rock alternatif et le blues-rock moderne.",
    "penta_maj7":   "La pentatonique majeure 7 remplace la 7ème mineure habituelle par la 7ème majeure, lui donnant une couleur très jazz et douce. Elle sonne parfaitement sur les accords majeurs avec septième majeure (maj7) et permet des lignes de basse très élégantes.",
    "penta_min_lead": "La pentatonique mineure avec note de guidage (leading tone) ajoute la 7ème majeure à la pentatonique mineure. Cette 7ème naturelle crée une forte attraction vers la tonique, très utile pour ponctuer les fins de phrases musicales avec expressivité.",
    "boogie":       "La gamme Rock'n'Roll / Boogie est une gamme hybride majeure-blues avec la 3ce mineure et la 7ème mineure. Elle capture l'essence du boogie-woogie, du rock'n'roll originel et du shuffle. Les lignes de basse en boogie (alternant fondamentale et 5te avec passages chromatiques) en dérivent directement.",
    "penta_majb2":  "La pentatonique majeure b2 (avec 2nde mineure) est une gamme pentatonique exotique qui mélange caractère oriental et langage pentatonique familier. Sa 2nde mineure caractéristique lui donne un son unique, à mi-chemin entre le phrygien et la pentatonique standard.",
    "dim":          "La gamme diminuée T-½T (alternance ton/demi-ton) est une gamme symétrique de 8 notes. Sa périodicité de 3 demi-tons lui confère une ambiguïté tonale totale — elle sonne identiquement depuis 4 fondamentales différentes. Très utilisée en jazz sur les accords diminués et les dominantes b9.",
    "dim_ht":       "La gamme diminuée ½T-T (alternance demi-ton/ton) est la version inversée de la gamme diminuée. Elle sonne également sur les accords diminués et dominants b9, avec un caractère encore plus tendu du fait du demi-ton initial.",
    "half_dim":     "La gamme demi-diminuée est équivalente au mode locrien. Elle définit les accords demi-diminués (iiø7) et sert à improviser sur ces accords dans les cadences jazz. Sa b5 crée une tension immédiate qui demande résolution.",
    "whole_tone":   "La gamme par ton (6 notes, alternance de tons entiers) est entièrement symétrique — elle n'a que 2 versions enharmoniques pour les 12 toniques. Son ambiguïté harmonique totale (pas de demi-tons, pas de dominante claire) crée un effet onirique et flottant très utilisé par Debussy et dans le jazz fusion.",
    "aug_hex":      "La gamme hexatonique augmentée est une gamme symétrique de 6 notes basée sur deux triades augmentées. Elle définit parfaitement les accords augmentés et crée des couleurs très colorées et instables. Utilisée dans le jazz moderne et la musique contemporaine.",
    "chromatic":    "La gamme chromatique contient les 12 demi-tons de l'octave. Bien qu'elle ne soit pas une 'gamme' au sens harmonique, elle est fondamentale pour les passages chromatiques, les chromatic runs et les notes de passage. À la basse, les approches chromatiques (encadrements) sont un outil expressif essentiel.",
    "phryg_dom":    "Le phrygien dominant (mode V de la gamme mineure harmonique) combine la 2nde mineure du phrygien avec une 3ce majeure. C'est la gamme du flamenco, du metal extrême et de la musique orientale. Sa tension dramatique en fait une couleur immédiatement reconnaissable.",
    "lydian_dom":   "Le lydien dominant (mode IV de la mineure mélodique) combine la #4 du lydien avec la b7 du mixolydien. C'est la gamme jazz par excellence pour improviser sur les accords dominants avec substitution tritonique (tritone substitution). Elle est au cœur du son bebop et post-bop.",
    "altered":      "La gamme altérée (mode VII de la mineure mélodique, ou superlocrien) contient toutes les tensions altérées : b9, #9, b5, #5. C'est la gamme ultime pour les résolutions V7alt→I en jazz. Les bassistes l'utilisent pour créer une tension maximale avant la résolution.",
    "locrian_s2":   "Le locrien #2 (mode VI de la mineure mélodique, aussi appelé locrien naturel 2) est plus stable que le locrien standard grâce à sa 2nde majeure. Il s'utilise sur les accords iiø7 dans les cadences ii-V-i en mineur, avec un caractère moins tendu que le locrien pur.",
    "lydian_aug":   "Le lydien augmenté (mode III de la mineure mélodique) combine une 4te augmentée (#4) ET une 5te augmentée (#5). Très dissonant et coloré, il s'utilise sur les accords augmentés majeurs 7 dans les progressions chromatiques jazz.",
    "mixo_b6":      "Le mixolydien b6 (mode V de la mineure mélodique) est le mixolydien avec une 6te mineure. Il crée un mélange unique de chaleur mixolydienne et d'ombre mineure. Utilisé sur les accords dominants avec une couleur mystérieuse dans le jazz et la musique de film.",
    "dorian_b2":    "Le dorien b2 (mode II de la mineure mélodique, ou phrygien #6) combine la 2nde mineure du phrygien avec la 6te majeure du dorien. Très utilisé dans le jazz pour les accords ii7 avec couleur phrygienne, il offre un caractère à la fois sombre et ouvert.",
    "locrian6":     "Le locrien nat.6 (mode II de la mineure harmonique) est un locrien avec une 6te majeure naturelle à la place de la b6. Cette 6te naturelle adoucit légèrement l'instabilité du locrien et est préféré par certains jazzmen pour improviser sur les accords demi-diminués.",
    "ionian_s5":    "L'ionien #5 (mode III de la mineure harmonique) est un mode majeur avec une 5te augmentée. Très coloré, il s'utilise sur les accords augmentés dans les contextes harmoniques riches. Sa #5 crée une tension inhabituelle dans un contexte autrement ionien.",
    "dorian_s4":    "Le dorien #4 (mode IV de la mineure harmonique, aussi appelé mineure roumaine ou lydien mineur) combine le caractère sombre du dorien avec une 4te augmentée. Il est utilisé dans les musiques d'Europe de l'Est et dans le jazz pour créer des couleurs exotiques sur les accords mineurs.",
    "lydian_s2":    "Le lydien #2 (mode VI de la mineure harmonique) est un mode majeur avec une 2nde augmentée ET une 4te augmentée. Ces deux altérations lui donnent un caractère très exotique et expressif, utilisé dans les musiques d'Europe orientale et dans le jazz moderne.",
    "superlocrian_bb7": "Le super locrien bb7 (mode VII de la mineure harmonique) est extrêmement rare et très dissonant. Sa double bémol 7 (6te majeure enharmonique) en fait un mode théorique utilisé dans les contextes jazz les plus avancés pour créer des tensions maximales.",
    "bebop_maj":    "La gamme bebop majeure ajoute une 5te chromatique augmentée (#5) entre la 5te et la 6te de la gamme majeure. Cette 8e note de passage permet des lignes bebop fluides sur les temps forts. C'est une gamme fondamentale du langage bebop inventé par Charlie Parker et Dizzy Gillespie.",
    "bebop_dom":    "La gamme bebop dominante est la gamme mixolydienne avec une 7ème majeure chromtique ajoutée entre la b7 et l'octave. Cette note de passage permet des phrases bebop fluides sur les accords dominants. C'est l'une des gammes les plus utilisées dans le bebop et le jazz classique.",
    "bebop_min":    "La gamme bebop mineure ajoute une 3ce majeure entre la 3ce mineure et la 4te, créant une gamme de 8 notes. Cette note chromatique de passage permet des lignes bebop fluides sur les accords mineurs. Elle est au cœur du langage d'improvisation jazz en mineur.",
    "double_harm":  "La gamme double harmonique (byzantine ou tsigane) contient deux secondes augmentées, ce qui lui donne un caractère extrêmement expressif et dramatique. On la retrouve dans la musique des Balkans, la musique arabe classique et le metal progressif. Ses intervalles larges la rendent difficile mais très expressive à la basse.",
    "hung_min":     "La gamme mineure hongroise (Gypsy minor) est caractérisée par une #4 entre sa b3 et sa #4, créant une seconde augmentée très caractéristique. C'est la gamme traditionnelle des Roms d'Europe centrale, présente dans la musique tsigane, le flamenco tardif et certains styles de metal.",
    "hung_maj":     "La gamme majeure hongroise possède une 3ce mineure entre le 2e et 3e degrés, créant un son exotique dans un contexte majoritaire. Utilisée dans la musique folklorique d'Europe centrale et dans le jazz expérimental.",
    "gypsy_maj":    "La gamme tzigane majeure (Gypsy major) est une gamme exotique avec une b2 et une #4, donnant un caractère oriental intense. Très présente dans la musique Romani et dans les improvisations de Django Reinhardt.",
    "romanian_min": "La gamme mineure roumaine est une variante du dorien avec une 4te augmentée (#4). Ce mélange de couleur dorienne et d'intervalle augmenté lui donne un caractère folk d'Europe de l'Est très distinctif. Utilisée dans la musique traditionnelle roumaine, grecque et turque.",
    "persian":      "La gamme persane est l'une des gammes les plus dissonantes, avec une b2, une #3, une b5 et une b6. Malgré son nom, elle est plus proche d'une construction théorique que d'une gamme réellement utilisée en Iran. Son caractère exotique extrême la rend intéressante pour les couleurs musicales insolites.",
    "arabic":       "La gamme arabe est une variante de la gamme par ton avec une 4te juste et une b6. Elle capture certaines couleurs de la musique du Moyen-Orient et est utilisée dans le jazz et la musique fusion à des fins d'exotisme sonore.",
    "enigmatic":    "La gamme énigmatique (de Verdi) est une gamme de 7 notes construite artificiellement pour sa complexité harmonique. Avec sa b2, sa #3, ses #5 et #6, elle génère des harmonies très insolites et difficiles à intégrer dans un contexte tonal classique.",
    "napolitaine_maj": "La gamme napolitaine majeure est une gamme majeure avec une 2nde mineure. Son b2 lui donne un caractère sombre et expressif inhabituel pour une gamme majeure. Elle est utilisée dans la musique classique napolitaine du 18e siècle et dans le jazz expérimental.",
    "napolitaine_min": "La gamme napolitaine mineure (ou mineure avec b2 et b6) est une gamme très expressive avec deux altérations bémols. Son caractère dramatique et mélancolique la rend présente dans la musique classique, le flamenco et le jazz modal.",
    "prometheus":   "La gamme de Prométhée (ou gamme acoustique mystique) a été théorisée par Alexandre Scriabine. Avec son accord mystique (4tes superposées) comme base, elle crée une atmosphère suspendue et contemplative. Présente dans la musique impressionniste et le jazz modal expérimental.",
    "overtone":     "La gamme acoustique (overtone scale, identique au lydien dominant) reflète la série des harmoniques naturelles. Son #4 et b7 lui donnent à la fois la luminosité lydienne et la tension mixolydienne. Béla Bartók l'a beaucoup utilisée, et elle est précieuse en jazz pour les accords dominants avec couleur lydienne.",
    "hijaz":        "Le maqam Hijaz est l'un des modes les plus importants de la musique arabe classique. Sa 2nde augmentée entre le b2 et la 3ce majeure lui donne un caractère profondément expressif et mélancolique. Très proche du phrygien dominant, il est omniprésent dans la musique du monde arabe, de la Turquie et des Balkans.",
    "hijaz_kar":    "Le maqam Hijaz Kar est une variante enrichie du Hijaz avec une 7ème majeure supplémentaire. Ce maqam aux deux secondes augmentées est très utilisé dans la musique arabe et turque classique pour exprimer des émotions intenses.",
    "bayati":       "Le maqam Bayati est l'un des maqams arabes les plus utilisés et les plus expressifs. Son b2 et sa structure particulière lui donnent une mélancolie douce et profonde que les musiciens arabes considèrent comme l'expression de la tristesse raffinée.",
    "nahawand":     "Le maqam Nahawand est l'équivalent arabe de la gamme mineure harmonique. Très utilisé dans la musique arabe et turque, il crée un pont naturel entre la théorie musicale occidentale et les modes orientaux.",
    "rast":         "Le maqam Rast est souvent considéré comme le 'do majeur' de la musique arabe — un mode équilibré et fondamental. Sa légère ambiguïté (proche du mixolydien) le rend très versatile dans la musique du Moyen-Orient et d'Asie centrale.",
    "nikriz":       "Le maqam Nikriz est une gamme aux deux 2ndes augmentées qui lui donnent un caractère dramatique et passionné. Présent dans la musique arabe, turque et balkanique, il est utilisé pour exprimer des émotions intenses et profondes.",
    "saba":         "Le maqam Saba (ou Sabâ) est l'un des maqams les plus expressifs et les plus difficiles de la musique arabe. Sa b4 distinctive lui donne un caractère de profonde mélancolie que les musiciens arabes associent à la tristesse et au deuil.",
    "kurd":         "Le maqam Kurd est très proche du mode phrygien occidental, avec sa 2nde mineure caractéristique. Il est très utilisé dans la musique kurde, arabe et turque, donnant un caractère sombre et grave très expressif.",
    "hirajoshi":    "La gamme Hirajoshi est l'une des gammes pentatoniques japonaises les plus connues. Avec ses deux demi-tons caractéristiques, elle crée une atmosphère contemplative et mélancolique typique de la musique traditionnelle japonaise (koto, shakuhachi). Très utilisée dans la musique contemporaine et le metal alternatif.",
    "insen":        "La gamme Insen est une pentatonique japonaise dérivée du maqam Phrygien. Avec son b2 et sa structure asymétrique, elle crée des atmosphères très particulières utilisées dans la musique de koto et dans les musiques de films de tradition japonaise.",
    "kumoi":        "La gamme Kumoi est une pentatonique japonaise douce avec une 3ce mineure et une 6te majeure. Son caractère mélancolique mais moins sombre que Hirajoshi en fait un outil expressif pour les compositeurs cherchant une couleur japonaise accessible.",
    "iwato":        "La gamme Iwato est une pentatonique japonaise très dissonante, avec deux demi-tons consécutifs (b2-b5). Son instabilité inhérente est utilisée pour créer des moments de grande tension dans la musique traditionnelle japonaise et la musique contemporaine.",
    "yo":           "La gamme Yo est la pentatonique majeure japonaise standard, utilisée dans la musique traditionnelle japonaise profane (chansons populaires, musique festive). Plus lumineuse que les autres gammes japonaises, elle se rapproche de la pentatonique majeure occidentale.",
    "bhairav":      "Le raga Bhairav est l'un des ragas les plus importants de la musique classique indienne. Joué traditionnellement au lever du soleil, il exprime la sérénité matinale grâce à ses deux bémols (b2 et b6) dans un contexte majoritaire. Sa couleur unique influence de nombreux musiciens de world music et de jazz.",
    "todi":         "Le raga Todi est l'un des ragas les plus complexes et expressifs de la musique hindoustanie. Avec ses b2, b3, #4 et b6, il crée une atmosphère profondément mélancolique et introspective. Joué en fin de matinée, il est considéré comme l'un des ragas les plus difficiles à maîtriser.",
    "kafi":         "Le raga Kafi est approximativement équivalent au mode dorien occidental. Très versatile dans la musique indienne, il peut être joué à toute heure et dans des contextes festifs comme sérieux. Sa proximité avec le dorien en fait un pont accessible entre la théorie musicale indienne et occidentale.",
    "kalyan":       "Le raga Kalyan est l'équivalent indien du mode lydien. Joué traditionnellement au coucher du soleil, il exprime un sentiment d'aspiration et de beauté sereine. Sa #4 caractéristique est au centre de nombreuses compositions de la musique classique indienne du nord.",
}

# ---------------------------------------------------------------------------
# DESCRIPTIONS GÉNÉRIQUES (fallback)
# ---------------------------------------------------------------------------
GROUP_DESCS = {
    0: "Ce mode diatonique à 7 notes est issu de la gamme majeure et de ses rotations. Il structure la théorie harmonique occidentale et fournit la base pour comprendre les accords et les progressions.",
    1: "Cette gamme non-diatonique offre des couleurs sonores spécifiques souvent utilisées dans des genres musicaux précis. Elle est un outil d'improvisation précieux pour les bassistes cherchant à sortir des sentiers battus.",
    2: "Ce mode dérivé de la gamme mineure mélodique ou harmonique est au cœur du langage jazz moderne. Il permet d'improviser avec précision sur des accords complexes aux tensions spécifiques.",
    3: "Cette gamme exotique est issue d'une tradition musicale non-occidentale. Elle apporte des couleurs sonores inhabituelles pour l'oreille occidentale et ouvre des perspectives harmoniques uniques.",
}

# ---------------------------------------------------------------------------
# CALCUL DES NOTES
# ---------------------------------------------------------------------------
LETTERS    = ['C','D','E','F','G','A','B']
LETTER_PC  = {'C':0,'D':2,'E':4,'F':5,'G':7,'A':9,'B':11}
FR_NAMES   = {'C':'Do','D':'Ré','E':'Mi','F':'Fa','G':'Sol','A':'La','B':'Si'}
INTERVAL_NAMES = {
    0:'Fondamentale',1:'2nde mineure',2:'2nde majeure',3:'3ce mineure',
    4:'3ce majeure',5:'4te juste',6:'Triton',7:'5te juste',
    8:'6te mineure',9:'6te majeure',10:'7ème mineure',11:'7ème majeure',
}
DEG_ROMAN  = ['I','II','III','IV','V','VI','VII']
TRIAD_Q    = {(4,7):'Majeur',(3,7):'mineur',(3,6):'diminué',(4,8):'augmenté'}
TRIAD_SUFS = {'Majeur':'','mineur':'m','diminué':'°','augmenté':'+'}
TRIAD_LOWS = {'Majeur':False,'mineur':True,'diminué':True,'augmenté':False}

def pc_of(note_str):
    pc = LETTER_PC[note_str[0]]
    for c in note_str[1:]:
        if c == '#': pc += 1
        elif c == 'b': pc -= 1
    return pc % 12

def build_scale(root, ls, iv):
    root_li = LETTERS.index(root[0])
    root_pc = pc_of(root)
    notes = []
    for i in range(len(iv)):
        letter = LETTERS[(root_li + ls[i]) % 7]
        tpc = (root_pc + iv[i]) % 12
        npc = LETTER_PC[letter]
        diff = (tpc - npc + 12) % 12
        if diff > 6: diff -= 12
        acc = '#' * diff if diff > 0 else 'b' * (-diff) if diff < 0 else ''
        notes.append(letter + acc)
    return notes

def pretty(note_str):
    return note_str.replace('#','♯').replace('b','♭')

def fr_note(note_str):
    letter = note_str[0]
    acc    = note_str[1:].replace('#','♯').replace('b','♭')
    return FR_NAMES[letter] + acc

def interval_str(iv):
    parts = []
    for i in range(len(iv)):
        nxt = iv[(i+1) % len(iv)]
        cur = iv[i]
        diff = (nxt - cur + 12) % 12
        if diff == 1:   parts.append('½T')
        elif diff == 2: parts.append('T')
        elif diff == 3: parts.append('T+½T')
        elif diff == 4: parts.append('2T')
        else:           parts.append(f'{diff}½T')
    return ' – '.join(parts)

def build_triads(root, ls, iv):
    if len(iv) != 7:
        return []
    notes = build_scale(root, ls, iv)
    triads = []
    for i in range(7):
        r = notes[i]
        t = notes[(i+2)%7]
        f = notes[(i+4)%7]
        rpc = pc_of(r); tpc = pc_of(t); fpc = pc_of(f)
        i3 = (tpc-rpc+12)%12; i5 = (fpc-rpc+12)%12
        quality = TRIAD_Q.get((i3,i5), None)
        if not quality:
            triads.append({'roman':DEG_ROMAN[i],'name':pretty(r)+'?','quality':'—'})
            continue
        suf = TRIAD_SUFS[quality]
        low = TRIAD_LOWS[quality]
        roman = DEG_ROMAN[i].lower() if low else DEG_ROMAN[i]
        if quality == 'diminué': roman += '°'
        if quality == 'augmenté': roman += '+'
        triads.append({'roman':roman,'name':fr_note(r)+suf,'quality':quality})
    return triads

# ---------------------------------------------------------------------------
# SLUGS
# ---------------------------------------------------------------------------
def scale_slug(scale_id):
    return scale_id.replace('_','-')

# ---------------------------------------------------------------------------
# GÉNÉRATION
# ---------------------------------------------------------------------------
def main():
    env = Environment(loader=FileSystemLoader(str(TMPL_DIR)), autoescape=True)
    scale_tpl = env.get_template("scale.html.jinja2")
    hub_tpl   = env.get_template("hub.html.jinja2")

    pages = []  # Pour le sitemap

    print(f"Génération dans {OUT_ROOT} …")
    for scale in SCALE_DEFS:
        slug_s = scale_slug(scale["id"])
        for root in ROOTS:
            notes_raw = build_scale(root["name"], scale["ls"], scale["iv"])
            notes_fr  = [fr_note(n)  for n in notes_raw]
            notes_en  = [pretty(n)   for n in notes_raw]
            notes_str = " – ".join(notes_fr)
            ivstr     = interval_str(scale["iv"])
            triads    = build_triads(root["name"], scale["ls"], scale["iv"]) if scale["diat"] else []
            desc      = SCALE_DESCS.get(scale["id"]) or GROUP_DESCS.get(scale["group"], "")
            n_notes   = len(scale["iv"])
            app_link  = f"{APP_URL}?root={root['name']}&scale={scale['id']}"
            page_url  = f"{BASE_URL}/fr/gammes/{root['slug']}/{slug_s}/"

            ctx = {
                "root":       root,
                "scale":      scale,
                "scale_slug": slug_s,
                "notes_fr":   notes_fr,
                "notes_en":   notes_en,
                "notes_str":  notes_str,
                "ivstr":      ivstr,
                "triads":     triads,
                "desc":       desc,
                "n_notes":    n_notes,
                "app_link":   app_link,
                "page_url":   page_url,
                "BASE_URL":   BASE_URL,
            }

            out_dir = OUT_ROOT / root["slug"] / slug_s
            out_dir.mkdir(parents=True, exist_ok=True)
            (out_dir / "index.html").write_text(
                scale_tpl.render(**ctx), encoding="utf-8"
            )
            pages.append(page_url)

    # ---- Hub /fr/gammes/index.html ----
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    hub_ctx = {
        "scales": SCALE_DEFS,
        "roots":  ROOTS,
        "BASE_URL": BASE_URL,
        "scale_slug": scale_slug,
    }
    (OUT_ROOT / "index.html").write_text(
        hub_tpl.render(**hub_ctx), encoding="utf-8"
    )
    pages.append(f"{BASE_URL}/fr/gammes/")

    # ---- Sitemap (append aux URLs existantes) ----
    write_sitemap(pages)

    print(f"  {len(pages)-1} pages gammes + 1 hub = {len(pages)} pages au total")
    print("  sitemap.xml mis à jour")
    print("Done.")

def write_sitemap(new_pages):
    sitemap_path = REPO_ROOT / "sitemap.xml"

    # Lire l'existant pour garder les URLs non-gammes
    existing = []
    if sitemap_path.exists():
        content = sitemap_path.read_text(encoding="utf-8")
        existing = re.findall(r'<loc>(.*?)</loc>', content)
    # Fusionner sans doublons (les nouvelles /fr/gammes/ remplacent les anciennes)
    kept = [u for u in existing if "/fr/gammes/" not in u]
    all_urls = kept + new_pages

    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for url in all_urls:
        lines.append(f'  <url><loc>{url}</loc></url>')
    lines.append('</urlset>')
    sitemap_path.write_text('\n'.join(lines) + '\n', encoding="utf-8")

if __name__ == "__main__":
    main()
