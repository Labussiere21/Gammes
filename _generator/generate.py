#!/usr/bin/env python3
"""
ScalaBass — Générateur de pages statiques SEO
==============================================
Génère fr/gammes/{note}/{gamme}/index.html  (72 gammes × 12 toniques = 864 pages FR)
Génère en/scales/{note}/{gamme}/index.html  (72 gammes × 12 toniques = 864 pages EN)
Génère fr/gammes/index.html (hub FR)
Génère en/scales/index.html (hub EN)
Génère sitemap.xml

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
REPO_ROOT    = Path(__file__).parent.parent
OUT_ROOT_FR  = REPO_ROOT / "fr" / "gammes"
OUT_ROOT_EN  = REPO_ROOT / "en" / "scales"
TMPL_DIR     = Path(__file__).parent / "templates"
BASE_URL     = "https://labussiere21.github.io/Gammes"
APP_URL      = f"{BASE_URL}/gammes.html"

# ---------------------------------------------------------------------------
# DONNÉES : NOTES (12 toniques canoniques)
# ---------------------------------------------------------------------------
ROOTS = [
    {"pc": 0,  "name": "C",  "fr": "Do",   "slug": "do",        "slug_en": "c"},
    {"pc": 1,  "name": "Db", "fr": "Réb",  "slug": "re-bemol",  "slug_en": "db"},
    {"pc": 2,  "name": "D",  "fr": "Ré",   "slug": "re",        "slug_en": "d"},
    {"pc": 3,  "name": "Eb", "fr": "Mib",  "slug": "mi-bemol",  "slug_en": "eb"},
    {"pc": 4,  "name": "E",  "fr": "Mi",   "slug": "mi",        "slug_en": "e"},
    {"pc": 5,  "name": "F",  "fr": "Fa",   "slug": "fa",        "slug_en": "f"},
    {"pc": 6,  "name": "F#", "fr": "Fa#",  "slug": "fa-diese",  "slug_en": "f-sharp"},
    {"pc": 7,  "name": "G",  "fr": "Sol",  "slug": "sol",       "slug_en": "g"},
    {"pc": 8,  "name": "Ab", "fr": "Lab",  "slug": "la-bemol",  "slug_en": "ab"},
    {"pc": 9,  "name": "A",  "fr": "La",   "slug": "la",        "slug_en": "a"},
    {"pc": 10, "name": "Bb", "fr": "Sib",  "slug": "si-bemol",  "slug_en": "bb"},
    {"pc": 11, "name": "B",  "fr": "Si",   "slug": "si",        "slug_en": "b"},
]

# Enharmonies : 5 toniques supplémentaires (dièses/bémols manquants)
# canonical_slug / canonical_slug_en pointent vers la page principale
ENHARMONIC_ROOTS = [
    {"pc": 1,  "name": "C#", "fr": "Do♯",  "slug": "do-diese",  "slug_en": "c-sharp",
     "canonical_slug": "re-bemol",  "canonical_slug_en": "db"},
    {"pc": 3,  "name": "D#", "fr": "Ré♯",  "slug": "re-diese",  "slug_en": "d-sharp",
     "canonical_slug": "mi-bemol",  "canonical_slug_en": "eb"},
    {"pc": 6,  "name": "Gb", "fr": "Sol♭", "slug": "sol-bemol", "slug_en": "g-flat",
     "canonical_slug": "fa-diese",  "canonical_slug_en": "f-sharp"},
    {"pc": 8,  "name": "G#", "fr": "Sol♯", "slug": "sol-diese", "slug_en": "g-sharp",
     "canonical_slug": "la-bemol",  "canonical_slug_en": "ab"},
    {"pc": 10, "name": "A#", "fr": "La♯",  "slug": "la-diese",  "slug_en": "a-sharp",
     "canonical_slug": "si-bemol",  "canonical_slug_en": "bb"},
]

# ---------------------------------------------------------------------------
# DONNÉES : GAMMES
# ---------------------------------------------------------------------------
SCALE_DEFS = [
    # GROUPE 0 — MODES DIATONIQUES
    {"id":"major",           "label":"Majeure",                "label_en":"Major",                  "sub":"Ionien",              "sub_en":"Ionian",              "group":0,"diat":True, "fam":"maj","ls":[0,1,2,3,4,5,6],"iv":[0,2,4,5,7,9,11]},
    {"id":"minor",           "label":"Mineure naturelle",      "label_en":"Natural Minor",           "sub":"Éolien",              "sub_en":"Aeolian",             "group":0,"diat":True, "fam":"min","ls":[0,1,2,3,4,5,6],"iv":[0,2,3,5,7,8,10]},
    {"id":"harmonic",        "label":"Mineure harmonique",     "label_en":"Harmonic Minor",          "sub":"",                    "sub_en":"",                    "group":0,"diat":True, "fam":"min","ls":[0,1,2,3,4,5,6],"iv":[0,2,3,5,7,8,11]},
    {"id":"melodic",         "label":"Mineure mélodique",      "label_en":"Melodic Minor",           "sub":"",                    "sub_en":"",                    "group":0,"diat":True, "fam":"min","ls":[0,1,2,3,4,5,6],"iv":[0,2,3,5,7,9,11]},
    {"id":"dorian",          "label":"Dorien",                 "label_en":"Dorian",                 "sub":"mode II",             "sub_en":"mode II",             "group":0,"diat":True, "fam":"min","ls":[0,1,2,3,4,5,6],"iv":[0,2,3,5,7,9,10]},
    {"id":"phrygian",        "label":"Phrygien",               "label_en":"Phrygian",               "sub":"mode III",            "sub_en":"mode III",            "group":0,"diat":True, "fam":"min","ls":[0,1,2,3,4,5,6],"iv":[0,1,3,5,7,8,10]},
    {"id":"lydian",          "label":"Lydien",                 "label_en":"Lydian",                 "sub":"mode IV",             "sub_en":"mode IV",             "group":0,"diat":True, "fam":"maj","ls":[0,1,2,3,4,5,6],"iv":[0,2,4,6,7,9,11]},
    {"id":"mixolydian",      "label":"Mixolydien",             "label_en":"Mixolydian",             "sub":"mode V",              "sub_en":"mode V",              "group":0,"diat":True, "fam":"maj","ls":[0,1,2,3,4,5,6],"iv":[0,2,4,5,7,9,10]},
    {"id":"locrian",         "label":"Locrien",                "label_en":"Locrian",                "sub":"mode VII",            "sub_en":"mode VII",            "group":0,"diat":True, "fam":"min","ls":[0,1,2,3,4,5,6],"iv":[0,1,3,5,6,8,10]},
    # GROUPE 1 — PENTATONIQUES, BLUES, SYMÉTRIQUES
    {"id":"penta_min",       "label":"Pentatonique mineure",   "label_en":"Minor Pentatonic",       "sub":"5 notes",             "sub_en":"5 notes",             "group":1,"diat":False,"fam":"min","ls":[0,2,3,4,6],       "iv":[0,3,5,7,10]},
    {"id":"penta_maj",       "label":"Pentatonique majeure",   "label_en":"Major Pentatonic",       "sub":"5 notes",             "sub_en":"5 notes",             "group":1,"diat":False,"fam":"maj","ls":[0,1,2,4,5],       "iv":[0,2,4,7,9]},
    {"id":"blues_min",       "label":"Blues mineure",          "label_en":"Minor Blues",            "sub":"6 notes",             "sub_en":"6 notes",             "group":1,"diat":False,"fam":"min","ls":[0,2,3,4,4,6],     "iv":[0,3,5,6,7,10]},
    {"id":"blues_maj",       "label":"Blues majeure",          "label_en":"Major Blues",            "sub":"6 notes",             "sub_en":"6 notes",             "group":1,"diat":False,"fam":"maj","ls":[0,1,2,2,4,5],     "iv":[0,2,3,4,7,9]},
    {"id":"penta_dom",       "label":"Pentatonique dominante", "label_en":"Dominant Pentatonic",    "sub":"5 notes",             "sub_en":"5 notes",             "group":1,"diat":False,"fam":"maj","ls":[0,1,2,4,5],       "iv":[0,2,4,7,10]},
    {"id":"penta_min6",      "label":"Pentatonique mineure 6", "label_en":"Minor 6 Pentatonic",     "sub":"5 notes",             "sub_en":"5 notes",             "group":1,"diat":False,"fam":"min","ls":[0,2,3,5,6],       "iv":[0,3,5,9,10]},
    {"id":"penta_sus",       "label":"Pentatonique sus",       "label_en":"Sus Pentatonic",         "sub":"5 notes",             "sub_en":"5 notes",             "group":1,"diat":False,"fam":"maj","ls":[0,1,3,4,6],       "iv":[0,2,5,7,10]},
    {"id":"blues_dom",       "label":"Blues dominante",        "label_en":"Dominant Blues",         "sub":"6 notes",             "sub_en":"6 notes",             "group":1,"diat":False,"fam":"maj","ls":[0,1,2,3,4,5],     "iv":[0,2,4,6,7,10]},
    {"id":"blues_hex",       "label":"Blues hexatonique",      "label_en":"Hexatonic Blues",        "sub":"6 notes",             "sub_en":"6 notes",             "group":1,"diat":False,"fam":"min","ls":[0,1,2,3,4,6],     "iv":[0,2,3,5,7,10]},
    {"id":"penta_maj7",      "label":"Pentatonique majeure 7", "label_en":"Major 7 Pentatonic",     "sub":"5 notes",             "sub_en":"5 notes",             "group":1,"diat":False,"fam":"maj","ls":[0,1,2,4,5],       "iv":[0,2,4,7,11]},
    {"id":"penta_min_lead",  "label":"Pentatonique min. guidage","label_en":"Minor Lead Pentatonic","sub":"6 notes",             "sub_en":"6 notes",             "group":1,"diat":False,"fam":"min","ls":[0,2,3,4,6,6],     "iv":[0,3,5,7,10,11]},
    {"id":"boogie",          "label":"Rock'n'Roll / Boogie",   "label_en":"Rock'n'Roll / Boogie",   "sub":"7 notes",             "sub_en":"7 notes",             "group":1,"diat":False,"fam":"maj","ls":[0,1,2,2,4,5,6],   "iv":[0,2,3,4,7,9,10]},
    {"id":"penta_majb2",     "label":"Pentatonique maj. b2",   "label_en":"Major b2 Pentatonic",    "sub":"5 notes",             "sub_en":"5 notes",             "group":1,"diat":False,"fam":"maj","ls":[0,1,2,4,5],       "iv":[0,1,4,7,9]},
    {"id":"dim",             "label":"Diminuée T-½T",          "label_en":"Diminished (W-H)",       "sub":"8 notes, symétrique", "sub_en":"8 notes, symmetric",  "group":1,"diat":False,"fam":"min","ls":[0,1,2,3,4,5,5,6], "iv":[0,2,3,5,6,8,9,11]},
    {"id":"dim_ht",          "label":"Diminuée ½T-T",          "label_en":"Diminished (H-W)",       "sub":"8 notes, symétrique", "sub_en":"8 notes, symmetric",  "group":1,"diat":False,"fam":"min","ls":[0,0,1,2,3,4,5,6], "iv":[0,1,3,4,6,7,9,10]},
    {"id":"half_dim",        "label":"Demi-diminuée",          "label_en":"Half Diminished",        "sub":"= Locrien",           "sub_en":"= Locrian",           "group":1,"diat":False,"fam":"min","ls":[0,1,2,3,4,5,6],   "iv":[0,1,3,5,6,8,10]},
    {"id":"whole_tone",      "label":"Par ton",                "label_en":"Whole Tone",             "sub":"6 notes, symétrique", "sub_en":"6 notes, symmetric",  "group":1,"diat":False,"fam":"maj","ls":[0,1,2,3,4,5],     "iv":[0,2,4,6,8,10]},
    {"id":"aug_hex",         "label":"Hexatonique augmentée",  "label_en":"Augmented Hexatonic",    "sub":"6 notes, symétrique", "sub_en":"6 notes, symmetric",  "group":1,"diat":False,"fam":"maj","ls":[0,1,2,3,4,5],     "iv":[0,3,4,7,8,11]},
    {"id":"chromatic",       "label":"Chromatique",            "label_en":"Chromatic",              "sub":"12 notes",            "sub_en":"12 notes",            "group":1,"diat":False,"fam":"maj","ls":list(range(12)),   "iv":list(range(12))},
    # GROUPE 2 — MODES JAZZ
    {"id":"phryg_dom",       "label":"Phrygien dominant",      "label_en":"Phrygian Dominant",      "sub":"Mode V harm.",         "sub_en":"Mode V harm.",        "group":2,"diat":False,"fam":"maj","ls":[0,1,2,3,4,5,6],"iv":[0,1,4,5,7,8,10]},
    {"id":"lydian_dom",      "label":"Lydien dominant",        "label_en":"Lydian Dominant",        "sub":"Mode IV mél.",         "sub_en":"Mode IV mel.",        "group":2,"diat":False,"fam":"maj","ls":[0,1,2,3,4,5,6],"iv":[0,2,4,6,7,9,10]},
    {"id":"altered",         "label":"Altérée",                "label_en":"Altered",                "sub":"Mode VII mél.",        "sub_en":"Mode VII mel.",       "group":2,"diat":False,"fam":"min","ls":[0,1,2,2,4,5,6],"iv":[0,1,3,4,6,8,10]},
    {"id":"locrian_s2",      "label":"Locrien #2",             "label_en":"Locrian #2",             "sub":"Mode VI mél.",         "sub_en":"Mode VI mel.",        "group":2,"diat":False,"fam":"min","ls":[0,1,2,3,4,5,6],"iv":[0,2,3,5,6,8,10]},
    {"id":"lydian_aug",      "label":"Lydien augmenté",        "label_en":"Lydian Augmented",       "sub":"Mode III mél.",        "sub_en":"Mode III mel.",       "group":2,"diat":False,"fam":"maj","ls":[0,1,2,3,4,5,6],"iv":[0,2,4,6,8,9,11]},
    {"id":"mixo_b6",         "label":"Mixolydien b6",          "label_en":"Mixolydian b6",          "sub":"Mode V mél.",          "sub_en":"Mode V mel.",         "group":2,"diat":False,"fam":"maj","ls":[0,1,2,3,4,5,6],"iv":[0,2,4,5,7,8,10]},
    {"id":"dorian_b2",       "label":"Dorien b2",              "label_en":"Dorian b2",              "sub":"Mode II mél.",         "sub_en":"Mode II mel.",        "group":2,"diat":False,"fam":"min","ls":[0,1,2,3,4,5,6],"iv":[0,1,3,5,7,9,10]},
    {"id":"locrian6",        "label":"Locrien nat.6",          "label_en":"Locrian nat.6",          "sub":"Mode II harm.",        "sub_en":"Mode II harm.",       "group":2,"diat":False,"fam":"min","ls":[0,1,2,3,4,5,6],"iv":[0,1,3,5,6,9,10]},
    {"id":"ionian_s5",       "label":"Ionien #5",              "label_en":"Ionian #5",              "sub":"Mode III harm.",       "sub_en":"Mode III harm.",      "group":2,"diat":False,"fam":"maj","ls":[0,1,2,3,4,5,6],"iv":[0,2,4,5,8,9,11]},
    {"id":"dorian_s4",       "label":"Dorien #4",              "label_en":"Dorian #4",              "sub":"Mode IV harm.",        "sub_en":"Mode IV harm.",       "group":2,"diat":False,"fam":"min","ls":[0,1,2,3,4,5,6],"iv":[0,2,3,6,7,9,10]},
    {"id":"lydian_s2",       "label":"Lydien #2",              "label_en":"Lydian #2",              "sub":"Mode VI harm.",        "sub_en":"Mode VI harm.",       "group":2,"diat":False,"fam":"maj","ls":[0,1,2,3,4,5,6],"iv":[0,3,4,6,7,9,11]},
    {"id":"superlocrian_bb7","label":"Super Locrien bb7",      "label_en":"Super Locrian bb7",      "sub":"Mode VII harm.",       "sub_en":"Mode VII harm.",      "group":2,"diat":False,"fam":"min","ls":[0,1,2,3,4,5,6],"iv":[0,1,3,4,6,8,9]},
    {"id":"bebop_maj",       "label":"Bebop majeure",          "label_en":"Bebop Major",            "sub":"8 notes (#5)",         "sub_en":"8 notes (#5)",        "group":2,"diat":False,"fam":"maj","ls":[0,1,2,3,4,4,5,6],"iv":[0,2,4,5,7,8,9,11]},
    {"id":"bebop_dom",       "label":"Bebop dominante",        "label_en":"Bebop Dominant",         "sub":"8 notes",              "sub_en":"8 notes",             "group":2,"diat":False,"fam":"maj","ls":[0,1,2,3,4,5,6,6],"iv":[0,2,4,5,7,9,10,11]},
    {"id":"bebop_min",       "label":"Bebop mineure",          "label_en":"Bebop Minor",            "sub":"8 notes",              "sub_en":"8 notes",             "group":2,"diat":False,"fam":"min","ls":[0,1,2,3,3,4,5,6],"iv":[0,2,3,4,5,7,9,10]},
    # GROUPE 3 — EXOTIQUES
    {"id":"double_harm",     "label":"Double harmonique",      "label_en":"Double Harmonic",        "sub":"Byzantine / Tsigane",  "sub_en":"Byzantine / Gypsy",   "group":3,"diat":False,"fam":"maj","ls":[0,1,2,3,4,5,6],"iv":[0,1,4,5,7,8,11]},
    {"id":"hung_min",        "label":"Mineure hongroise",      "label_en":"Hungarian Minor",        "sub":"Gypsy minor",          "sub_en":"Gypsy minor",         "group":3,"diat":False,"fam":"min","ls":[0,1,2,3,4,5,6],"iv":[0,2,3,6,7,8,11]},
    {"id":"hung_maj",        "label":"Majeure hongroise",      "label_en":"Hungarian Major",        "sub":"Hungarian major",      "sub_en":"Hungarian major",     "group":3,"diat":False,"fam":"maj","ls":[0,1,2,3,4,5,6],"iv":[0,3,4,6,7,9,10]},
    {"id":"gypsy_maj",       "label":"Tzigane majeure",        "label_en":"Gypsy Major",            "sub":"Gypsy major",          "sub_en":"Gypsy major",         "group":3,"diat":False,"fam":"maj","ls":[0,1,2,3,4,5,6],"iv":[0,1,4,5,7,8,10]},
    {"id":"romanian_min",    "label":"Mineure roumaine",       "label_en":"Romanian Minor",         "sub":"Dorien #4",            "sub_en":"Dorian #4",           "group":3,"diat":False,"fam":"min","ls":[0,1,2,3,4,5,6],"iv":[0,2,3,6,7,9,10]},
    {"id":"persian",         "label":"Persane",                "label_en":"Persian",                "sub":"Exotique",             "sub_en":"Exotic",              "group":3,"diat":False,"fam":"min","ls":[0,1,2,3,4,5,6],"iv":[0,1,4,5,6,8,11]},
    {"id":"arabic",          "label":"Arabe",                  "label_en":"Arabic",                 "sub":"Exotique",             "sub_en":"Exotic",              "group":3,"diat":False,"fam":"maj","ls":[0,1,2,3,4,5,6],"iv":[0,2,4,5,6,8,10]},
    {"id":"enigmatic",       "label":"Enigmatique",            "label_en":"Enigmatic",              "sub":"Verdi",                "sub_en":"Verdi",               "group":3,"diat":False,"fam":"maj","ls":[0,1,2,3,4,5,6],"iv":[0,1,4,6,8,10,11]},
    {"id":"napolitaine_maj", "label":"Napolitaine majeure",    "label_en":"Neapolitan Major",       "sub":"Exotique",             "sub_en":"Exotic",              "group":3,"diat":False,"fam":"maj","ls":[0,1,2,3,4,5,6],"iv":[0,1,3,5,7,9,11]},
    {"id":"napolitaine_min", "label":"Napolitaine mineure",    "label_en":"Neapolitan Minor",       "sub":"Exotique",             "sub_en":"Exotic",              "group":3,"diat":False,"fam":"min","ls":[0,1,2,3,4,5,6],"iv":[0,1,3,5,7,8,11]},
    {"id":"prometheus",      "label":"Prometheus",             "label_en":"Prometheus",             "sub":"Scriabine",            "sub_en":"Scriabin",            "group":3,"diat":False,"fam":"maj","ls":[0,1,2,3,5,6],   "iv":[0,2,4,6,9,10]},
    {"id":"overtone",        "label":"Acoustique (Overtone)",  "label_en":"Overtone",               "sub":"= Lydien dominant",    "sub_en":"= Lydian dominant",   "group":3,"diat":False,"fam":"maj","ls":[0,1,2,3,4,5,6],"iv":[0,2,4,6,7,9,10]},
    {"id":"hijaz",           "label":"Hijaz",                  "label_en":"Hijaz",                  "sub":"Maqam",                "sub_en":"Maqam",               "group":3,"diat":False,"fam":"min","ls":[0,1,2,3,4,5,6],"iv":[0,1,4,5,7,8,10]},
    {"id":"hijaz_kar",       "label":"Hijaz Kar",              "label_en":"Hijaz Kar",              "sub":"Maqam",                "sub_en":"Maqam",               "group":3,"diat":False,"fam":"min","ls":[0,1,2,3,4,5,6],"iv":[0,1,4,5,7,8,11]},
    {"id":"bayati",          "label":"Bayati",                 "label_en":"Bayati",                 "sub":"Maqam",                "sub_en":"Maqam",               "group":3,"diat":False,"fam":"min","ls":[0,1,2,3,4,5,6],"iv":[0,1,3,5,7,8,10]},
    {"id":"nahawand",        "label":"Nahawand",               "label_en":"Nahawand",               "sub":"Maqam",                "sub_en":"Maqam",               "group":3,"diat":False,"fam":"min","ls":[0,1,2,3,4,5,6],"iv":[0,2,3,5,7,8,11]},
    {"id":"rast",            "label":"Rast",                   "label_en":"Rast",                   "sub":"Maqam",                "sub_en":"Maqam",               "group":3,"diat":False,"fam":"maj","ls":[0,1,2,3,4,5,6],"iv":[0,2,4,5,7,9,10]},
    {"id":"nikriz",          "label":"Nikriz",                 "label_en":"Nikriz",                 "sub":"Maqam",                "sub_en":"Maqam",               "group":3,"diat":False,"fam":"min","ls":[0,1,2,3,4,5,6],"iv":[0,2,3,6,7,8,10]},
    {"id":"saba",            "label":"Saba",                   "label_en":"Saba",                   "sub":"Maqam",                "sub_en":"Maqam",               "group":3,"diat":False,"fam":"min","ls":[0,1,2,3,4,5,6],"iv":[0,1,3,4,6,8,10]},
    {"id":"kurd",            "label":"Kurd",                   "label_en":"Kurd",                   "sub":"Maqam",                "sub_en":"Maqam",               "group":3,"diat":False,"fam":"min","ls":[0,1,2,3,4,5,6],"iv":[0,1,3,5,7,8,10]},
    {"id":"hirajoshi",       "label":"Hirajoshi",              "label_en":"Hirajoshi",              "sub":"Japonaise, 5 notes",   "sub_en":"Japanese, 5 notes",   "group":3,"diat":False,"fam":"min","ls":[0,1,2,4,5],     "iv":[0,2,3,7,8]},
    {"id":"insen",           "label":"Insen",                  "label_en":"Insen",                  "sub":"Japonaise, 5 notes",   "sub_en":"Japanese, 5 notes",   "group":3,"diat":False,"fam":"min","ls":[0,1,3,4,6],     "iv":[0,1,5,7,10]},
    {"id":"kumoi",           "label":"Kumoi",                  "label_en":"Kumoi",                  "sub":"Japonaise, 5 notes",   "sub_en":"Japanese, 5 notes",   "group":3,"diat":False,"fam":"min","ls":[0,1,2,4,5],     "iv":[0,2,3,7,9]},
    {"id":"iwato",           "label":"Iwato",                  "label_en":"Iwato",                  "sub":"Japonaise, 5 notes",   "sub_en":"Japanese, 5 notes",   "group":3,"diat":False,"fam":"min","ls":[0,1,3,4,6],     "iv":[0,1,5,6,10]},
    {"id":"yo",              "label":"Yo",                     "label_en":"Yo",                     "sub":"Japonaise, 5 notes",   "sub_en":"Japanese, 5 notes",   "group":3,"diat":False,"fam":"maj","ls":[0,1,3,4,5],     "iv":[0,2,5,7,9]},
    {"id":"bhairav",         "label":"Bhairav",                "label_en":"Bhairav",                "sub":"Raga indien",          "sub_en":"Indian raga",         "group":3,"diat":False,"fam":"maj","ls":[0,1,2,3,4,5,6],"iv":[0,1,4,5,7,8,11]},
    {"id":"todi",            "label":"Todi",                   "label_en":"Todi",                   "sub":"Raga indien",          "sub_en":"Indian raga",         "group":3,"diat":False,"fam":"min","ls":[0,1,2,3,4,5,6],"iv":[0,1,3,6,7,8,11]},
    {"id":"kafi",            "label":"Kafi",                   "label_en":"Kafi",                   "sub":"Raga indien",          "sub_en":"Indian raga",         "group":3,"diat":False,"fam":"min","ls":[0,1,2,3,4,5,6],"iv":[0,2,3,5,7,9,10]},
    {"id":"kalyan",          "label":"Kalyan",                 "label_en":"Kalyan",                 "sub":"Raga indien",          "sub_en":"Indian raga",         "group":3,"diat":False,"fam":"maj","ls":[0,1,2,3,4,5,6],"iv":[0,2,4,6,7,9,11]},
]

# ---------------------------------------------------------------------------
# DESCRIPTIONS FRANÇAIS
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
    "bebop_dom":    "La gamme bebop dominante est la gamme mixolydienne avec une 7ème majeure chromatique ajoutée entre la b7 et l'octave. Cette note de passage permet des phrases bebop fluides sur les accords dominants. C'est l'une des gammes les plus utilisées dans le bebop et le jazz classique.",
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

GROUP_DESCS = {
    0: "Ce mode diatonique à 7 notes est issu de la gamme majeure et de ses rotations. Il structure la théorie harmonique occidentale et fournit la base pour comprendre les accords et les progressions.",
    1: "Cette gamme non-diatonique offre des couleurs sonores spécifiques souvent utilisées dans des genres musicaux précis. Elle est un outil d'improvisation précieux pour les bassistes cherchant à sortir des sentiers battus.",
    2: "Ce mode dérivé de la gamme mineure mélodique ou harmonique est au cœur du langage jazz moderne. Il permet d'improviser avec précision sur des accords complexes aux tensions spécifiques.",
    3: "Cette gamme exotique est issue d'une tradition musicale non-occidentale. Elle apporte des couleurs sonores inhabituelles pour l'oreille occidentale et ouvre des perspectives harmoniques uniques.",
}

# ---------------------------------------------------------------------------
# DESCRIPTIONS ANGLAIS
# ---------------------------------------------------------------------------
SCALE_DESCS_EN = {
    "major":        "The major scale is the foundation of Western music theory. Bright and stable, it underlies the vast majority of rock, pop, jazz, and classical pieces. For bass players, it provides the natural roadmap for building lines in any major key.",
    "minor":        "The natural minor scale (Aeolian mode) is the reference minor scale. Darker and more expressive than the major, it appears constantly in rock, melancholic pop, metal, and jazz. Bass lines in natural minor perfectly underscore the emotional weight of the key.",
    "harmonic":     "The harmonic minor scale stands out for its augmented second (3 semitones) between the 6th and 7th degrees. This distinctive leap gives it a dramatic, Eastern-tinged character found in classical music, flamenco, and action film scores. The leading tone creates strong tension toward the tonic.",
    "melodic":      "The melodic minor scale (ascending form) raises both the 6th and 7th degrees, smoothing out melodic movement. It sits at the heart of modern jazz language: essential on minor-major-7 chords, half-diminished iis, and altered dominants.",
    "dorian":       "The Dorian mode is the minor scale with a major 6th — the signature sound of jazz and funk. Found in Miles Davis's 'So What', Santana's 'Oye Como Va', and under Jaco Pastorius's fingers. For bass, it is the most versatile minor mode.",
    "phrygian":     "The Phrygian mode is defined by its minor 2nd (half-step between the 1st and 2nd degrees), giving it a Spanish, metal character. Essential for heavy riffs, Iberian music, and flamenco. On bass, it creates immediate tension from the very first notes.",
    "lydian":       "The Lydian mode, with its augmented 4th (#4), sounds dreamy and floating. Widely used in film music (John Williams, Ennio Morricone) and modal jazz. Bass lines in Lydian bring an unusual lightness and brightness.",
    "mixolydian":   "The Mixolydian mode is the major scale with a minor 7th (b7) — the sound of blues, rock, and funk. It sits naturally over all dominant chords (7th). For bass, it is essential in blues, classic rock (Rolling Stones, Hendrix), and any groovy context.",
    "locrian":      "The Locrian mode, with its diminished 5th (b5), is the most unstable diatonic mode. Rarely used in its pure form, it appears mainly on half-diminished (iiø7) chords in jazz cadences. Bass players use it as a passing color to reinforce harmonic instability.",
    "penta_min":    "The minor pentatonic is the most-played bass scale. Its 5 half-step-free notes sound naturally over blues, rock, and funk. Its apparent simplicity hides infinite richness: it is the foundation of virtually all improvised bass solos and lines in minor keys.",
    "penta_maj":    "The major pentatonic is the bright version of the pentatonic. Its 5 notes flow effortlessly over most major progressions. Prevalent in country, pop, and rock, it is the go-to tool for crafting singable bass lines without hitting a wrong note.",
    "blues_min":    "The minor blues scale adds the 'blue note' (b5, the tritone) to the minor pentatonic. This dissonant note creates the 'dirty', expressive character of the blues. For bass, the b5 passing between the 4th and perfect 5th is a defining stylistic signature.",
    "blues_maj":    "The major blues scale enriches the major pentatonic with the b3 (minor third), bringing the major/minor ambiguity central to blues and rock'n'roll. This blend of light and tension is at the heart of Chuck Berry, Elvis Presley, and all original rock.",
    "penta_dom":    "The dominant pentatonic (Mixolydian pentatonic) contains the b7, making it perfectly suited for dominant (7th) chords. Widely used in blues, funk, and jazz fusion, it sounds over V7 chords with a tense, groovy character.",
    "penta_min6":   "The minor 6 pentatonic contains the major 6th alongside the usual minor notes. This color is widely used in jazz and bossa nova to give a more open, luminous character to minor contexts. It sounds particularly well over minor 6 chords.",
    "penta_sus":    "The suspended pentatonic (quartal pentatonic) contains neither a major nor a minor 3rd, giving it an ambiguous, floating character. Prized in modal jazz, ambient, and contemporary music for creating atmospheres without clear resolution.",
    "blues_dom":    "The dominant blues scale enriches the dominant pentatonic with the tritone (#4/b5). Very close to the overtone/Lydian dominant scale, it sounds with maximum tension over altered dominant chords. Indispensable for expressive jazz-blues bass lines.",
    "blues_hex":    "The hexatonic blues (6 notes) is a variant of the enriched minor pentatonic. It offers more colors than the classic pentatonic while retaining its blues character. Widely used in alternative rock and modern blues-rock.",
    "penta_maj7":   "The major 7 pentatonic replaces the usual minor 7th with a major 7th, giving it a very jazzy, soft color. It sounds perfectly over major 7 chords (maj7) and allows elegant bass lines.",
    "penta_min_lead": "The minor pentatonic with a leading tone adds the major 7th to the minor pentatonic. This natural 7th creates a strong pull toward the tonic, very useful for punctuating musical phrase endings expressively.",
    "boogie":       "The Rock'n'Roll / Boogie scale is a major-blues hybrid with the minor 3rd and minor 7th. It captures the essence of boogie-woogie, original rock'n'roll, and the shuffle. Classic bass boogie lines (alternating root and 5th with chromatic runs) derive directly from it.",
    "penta_majb2":  "The major b2 pentatonic (with a minor 2nd) is an exotic pentatonic blending an Oriental character with a familiar pentatonic language. Its characteristic minor 2nd gives it a unique sound halfway between Phrygian and the standard pentatonic.",
    "dim":          "The whole-half diminished scale (W-H alternation) is a symmetric 8-note scale. Its periodicity of 3 semitones creates total tonal ambiguity — it sounds identically from 4 different roots. Widely used in jazz over diminished chords and b9 dominants.",
    "dim_ht":       "The half-whole diminished scale (H-W alternation) is the inverted version of the diminished scale. It also works over diminished chords and b9 dominants, with an even tenser character due to the initial half-step.",
    "half_dim":     "The half-diminished scale is equivalent to the Locrian mode. It defines half-diminished chords (iiø7) and is used to improvise over them in jazz cadences. Its b5 creates immediate tension demanding resolution.",
    "whole_tone":   "The whole-tone scale (6 notes, all whole steps) is completely symmetric — only 2 enharmonic versions exist for all 12 roots. Its total harmonic ambiguity (no semitones, no clear dominant) creates a dreamlike, floating effect widely used by Debussy and in jazz fusion.",
    "aug_hex":      "The augmented hexatonic is a symmetric 6-note scale built from two augmented triads. It perfectly defines augmented chords and creates highly colorful, unstable sounds. Used in modern jazz and contemporary music.",
    "chromatic":    "The chromatic scale contains all 12 semitones of the octave. Though not a 'scale' in the harmonic sense, it is fundamental for chromatic passages, runs, and passing notes. For bass, chromatic approaches (encircling notes) are an essential expressive tool.",
    "phryg_dom":    "The Phrygian dominant (mode V of the harmonic minor scale) combines the minor 2nd of Phrygian with a major 3rd. It is the scale of flamenco, extreme metal, and Oriental music. Its dramatic tension makes it instantly recognizable.",
    "lydian_dom":   "The Lydian dominant (mode IV of the melodic minor) combines the #4 of Lydian with the b7 of Mixolydian. It is the quintessential jazz scale for improvising over dominant chords with tritone substitution. Central to bebop and post-bop language.",
    "altered":      "The altered scale (mode VII of the melodic minor, or superlocrian) contains all altered tensions: b9, #9, b5, #5. It is the ultimate scale for V7alt→I resolutions in jazz. Bassists use it to create maximum tension before the resolution.",
    "locrian_s2":   "Locrian #2 (mode VI of the melodic minor, also called natural 2 Locrian) is more stable than standard Locrian thanks to its major 2nd. Used on iiø7 chords in minor ii-V-i cadences, with a less tense character than pure Locrian.",
    "lydian_aug":   "Lydian Augmented (mode III of the melodic minor) combines an augmented 4th (#4) AND an augmented 5th (#5). Very dissonant and colorful, used on major 7 augmented chords in chromatic jazz progressions.",
    "mixo_b6":      "Mixolydian b6 (mode V of the melodic minor) is Mixolydian with a minor 6th. It creates a unique blend of Mixolydian warmth and minor shadow. Used on dominant chords with a mysterious color in jazz and film music.",
    "dorian_b2":    "Dorian b2 (mode II of the melodic minor, or Phrygian #6) combines the minor 2nd of Phrygian with the major 6th of Dorian. Widely used in jazz for ii7 chords with Phrygian color, offering a simultaneously dark and open character.",
    "locrian6":     "Locrian nat.6 (mode II of the harmonic minor) is a Locrian with a natural major 6th instead of the b6. This natural 6th slightly softens Locrian's instability and is preferred by some jazz musicians for improvising over half-diminished chords.",
    "ionian_s5":    "Ionian #5 (mode III of the harmonic minor) is a major mode with an augmented 5th. Highly colorful, used on augmented chords in harmonically rich contexts. Its #5 creates an unusual tension in an otherwise Ionian setting.",
    "dorian_s4":    "Dorian #4 (mode IV of the harmonic minor, also called Romanian minor or Lydian minor) combines Dorian's dark character with an augmented 4th. Used in Eastern European music and jazz to create exotic colors on minor chords.",
    "lydian_s2":    "Lydian #2 (mode VI of the harmonic minor) is a major mode with both an augmented 2nd AND an augmented 4th. These two alterations give it a very exotic, expressive character, used in Eastern European folk music and modern jazz.",
    "superlocrian_bb7": "Super Locrian bb7 (mode VII of the harmonic minor) is extremely rare and very dissonant. Its double-flat 7 (enharmonic major 6th) makes it a theoretical mode used in the most advanced jazz contexts for creating maximum tensions.",
    "bebop_maj":    "The bebop major scale adds a chromatic augmented 5th (#5) between the 5th and 6th of the major scale. This 8th passing note allows fluid bebop lines on strong beats. A fundamental scale in the bebop language invented by Charlie Parker and Dizzy Gillespie.",
    "bebop_dom":    "The bebop dominant scale is the Mixolydian with an added chromatic major 7th between the b7 and the octave. This passing note allows fluid bebop phrases over dominant chords. One of the most-used scales in bebop and classic jazz.",
    "bebop_min":    "The bebop minor scale adds a major 3rd between the minor 3rd and the 4th, creating an 8-note scale. This chromatic passing note allows fluid bebop lines over minor chords. It is at the core of jazz improvisation language in minor.",
    "double_harm":  "The double harmonic scale (Byzantine or Gypsy) contains two augmented seconds, giving it an extremely expressive and dramatic character. Found in Balkan music, classical Arabic music, and progressive metal. Its wide intervals make it challenging but highly expressive on bass.",
    "hung_min":     "The Hungarian minor (Gypsy minor) is characterized by a #4 between its b3 and #4, creating a very distinctive augmented second. It is the traditional scale of Central European Roma music, present in Gypsy music, later flamenco, and some metal styles.",
    "hung_maj":     "The Hungarian major has a minor 3rd between the 2nd and 3rd degrees, creating an exotic sound in a major context. Used in Central European folk music and experimental jazz.",
    "gypsy_maj":    "The Gypsy major is an exotic scale with a b2 and a #4, giving it an intense Oriental character. Very present in Romani music and in Django Reinhardt's improvisations.",
    "romanian_min": "The Romanian minor is a variant of Dorian with an augmented 4th (#4). This blend of Dorian color and augmented interval gives it a distinctive Eastern European folk character. Used in traditional Romanian, Greek, and Turkish music.",
    "persian":      "The Persian scale is one of the most dissonant scales, with a b2, #3, b5, and b6. Despite its name, it is closer to a theoretical construction than a scale actually used in Iran. Its extreme exotic character makes it interesting for unusual musical colors.",
    "arabic":       "The Arabic scale is a variant of the whole-tone scale with a perfect 4th and a b6. It captures certain colors of Middle Eastern music and is used in jazz and fusion music for sonic exoticism.",
    "enigmatic":    "The enigmatic scale (Verdi's scale) is a 7-note scale artificially constructed for its harmonic complexity. With its b2, #3, #5, and #6, it generates very unusual harmonies difficult to integrate into a classical tonal context.",
    "napolitaine_maj": "The Neapolitan major scale is a major scale with a minor 2nd. Its b2 gives it a dark, expressive character unusual for a major scale. Used in 18th-century Neapolitan classical music and experimental jazz.",
    "napolitaine_min": "The Neapolitan minor (or minor with b2 and b6) is a highly expressive scale with two flat alterations. Its dramatic, melancholic character makes it present in classical music, flamenco, and modal jazz.",
    "prometheus":   "The Prometheus scale (or mystic acoustic scale) was theorized by Alexander Scriabin. Based on his mystic chord (stacked 4ths), it creates a suspended, contemplative atmosphere. Present in impressionist music and experimental modal jazz.",
    "overtone":     "The overtone scale (identical to Lydian dominant) reflects the natural harmonic series. Its #4 and b7 give it both Lydian brightness and Mixolydian tension. Béla Bartók used it extensively, and it is valuable in jazz for dominant chords with a Lydian color.",
    "hijaz":        "The Hijaz maqam is one of the most important modes in classical Arabic music. Its augmented second between the b2 and the major 3rd gives it a deeply expressive, melancholic character. Closely related to Phrygian dominant, it is ubiquitous in Arab, Turkish, and Balkan music.",
    "hijaz_kar":    "The Hijaz Kar maqam is an enriched variant of Hijaz with an additional major 7th. This maqam with two augmented seconds is widely used in Arabic and Turkish classical music to express intense emotions.",
    "bayati":       "The Bayati maqam is one of the most used and expressive Arabic maqams. Its b2 and particular structure give it a sweet, deep melancholy that Arabic musicians consider the expression of refined sadness.",
    "nahawand":     "The Nahawand maqam is the Arabic equivalent of the harmonic minor scale. Widely used in Arabic and Turkish music, it creates a natural bridge between Western music theory and Eastern modes.",
    "rast":         "The Rast maqam is often considered the 'C major' of Arabic music — a balanced and fundamental mode. Its slight ambiguity (close to Mixolydian) makes it very versatile in Middle Eastern and Central Asian music.",
    "nikriz":       "The Nikriz maqam is a scale with two augmented seconds giving it a dramatic, passionate character. Present in Arabic, Turkish, and Balkan music, it is used to express intense and deep emotions.",
    "saba":         "The Saba maqam (or Sabâ) is one of the most expressive and difficult maqams in Arabic music. Its distinctive b4 gives it a character of deep melancholy that Arabic musicians associate with sorrow and mourning.",
    "kurd":         "The Kurd maqam is very close to the Western Phrygian mode, with its characteristic minor 2nd. Widely used in Kurdish, Arabic, and Turkish music, giving a dark and grave expressive character.",
    "hirajoshi":    "Hirajoshi is one of the best-known Japanese pentatonic scales. With its two characteristic semitones, it creates a contemplative, melancholic atmosphere typical of traditional Japanese music (koto, shakuhachi). Widely used in contemporary music and alternative metal.",
    "insen":        "The Insen scale is a Japanese pentatonic derived from the Phrygian mode. With its b2 and asymmetric structure, it creates very particular atmospheres used in koto music and Japanese film scores.",
    "kumoi":        "The Kumoi scale is a gentle Japanese pentatonic with a minor 3rd and major 6th. Its melancholic but less dark character than Hirajoshi makes it an expressive tool for composers seeking an accessible Japanese color.",
    "iwato":        "The Iwato scale is a very dissonant Japanese pentatonic with two consecutive semitones (b2-b5). Its inherent instability is used to create moments of great tension in traditional Japanese music and contemporary music.",
    "yo":           "The Yo scale is the standard Japanese major pentatonic, used in traditional Japanese secular music (folk songs, festive music). Brighter than other Japanese scales, it resembles the Western major pentatonic.",
    "bhairav":      "Raga Bhairav is one of the most important ragas in Indian classical music. Traditionally played at dawn, it expresses morning serenity through its two flats (b2 and b6) in a major context. Its unique color influences many world music and jazz musicians.",
    "todi":         "Raga Todi is one of the most complex and expressive ragas in Hindustani music. With its b2, b3, #4, and b6, it creates a deeply melancholic and introspective atmosphere. Played in late morning, it is considered one of the most difficult ragas to master.",
    "kafi":         "Raga Kafi is approximately equivalent to the Western Dorian mode. Very versatile in Indian music, it can be played at any time and in both festive and serious contexts. Its proximity to Dorian makes it an accessible bridge between Indian and Western music theory.",
    "kalyan":       "Raga Kalyan is the Indian equivalent of the Lydian mode. Traditionally played at sunset, it expresses a feeling of aspiration and serene beauty. Its characteristic #4 is central to many compositions in North Indian classical music.",
}

GROUP_DESCS_EN = {
    0: "This 7-note diatonic mode derives from the major scale and its rotations. It structures Western harmonic theory and provides the foundation for understanding chords and progressions.",
    1: "This non-diatonic scale offers specific sonic colors often used in particular musical genres. It is a valuable improvisation tool for bassists looking to go beyond the beaten path.",
    2: "This mode derived from the melodic or harmonic minor scale is at the core of modern jazz language. It allows precise improvisation over complex chords with specific tensions.",
    3: "This exotic scale comes from a non-Western musical tradition. It brings unusual sonic colors to the Western ear and opens unique harmonic perspectives.",
}

# ---------------------------------------------------------------------------
# CALCUL DES NOTES
# ---------------------------------------------------------------------------
LETTERS    = ['C','D','E','F','G','A','B']
LETTER_PC  = {'C':0,'D':2,'E':4,'F':5,'G':7,'A':9,'B':11}
FR_NAMES   = {'C':'Do','D':'Ré','E':'Mi','F':'Fa','G':'Sol','A':'La','B':'Si'}
DEG_ROMAN  = ['I','II','III','IV','V','VI','VII']
TRIAD_Q    = {(4,7):'Major',(3,7):'minor',(3,6):'diminished',(4,8):'augmented'}
TRIAD_SUFS_EN = {'Major':'','minor':'m','diminished':'°','augmented':'+'}
TRIAD_LOWS_EN = {'Major':False,'minor':True,'diminished':True,'augmented':False}
TRIAD_Q_FR    = {'Major':'Majeur','minor':'mineur','diminished':'diminué','augmented':'augmenté'}
TRIAD_SUFS_FR = {'Major':'','minor':'m','diminished':'°','augmented':'+'}

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

def build_triads(root, ls, iv, lang='fr'):
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
        quality_en = TRIAD_Q.get((i3,i5), None)
        if not quality_en:
            triads.append({'roman':DEG_ROMAN[i],'name':pretty(r)+'?','quality':'—'})
            continue
        if lang == 'en':
            suf  = TRIAD_SUFS_EN[quality_en]
            low  = TRIAD_LOWS_EN[quality_en]
            qual = quality_en
            note_name = pretty(r)
        else:
            suf  = TRIAD_SUFS_FR[quality_en]
            low  = TRIAD_LOWS_EN[quality_en]
            qual = TRIAD_Q_FR[quality_en]
            note_name = fr_note(r)
        roman = DEG_ROMAN[i].lower() if low else DEG_ROMAN[i]
        if quality_en == 'diminished': roman += '°'
        if quality_en == 'augmented':  roman += '+'
        triads.append({'roman':roman,'name':note_name+suf,'quality':qual})
    return triads

def scale_slug(scale_id):
    return scale_id.replace('_','-')

# ---------------------------------------------------------------------------
# GÉNÉRATION
# ---------------------------------------------------------------------------
def main():
    env = Environment(loader=FileSystemLoader(str(TMPL_DIR)), autoescape=True)
    scale_tpl = env.get_template("scale.html.jinja2")
    hub_fr_tpl = env.get_template("hub.html.jinja2")

    pages_fr = []
    pages_en = []

    print(f"Génération FR dans {OUT_ROOT_FR} …")
    print(f"Génération EN dans {OUT_ROOT_EN} …")

    for scale in SCALE_DEFS:
        slug_s = scale_slug(scale["id"])
        for root in ROOTS:
            notes_raw = build_scale(root["name"], scale["ls"], scale["iv"])
            notes_fr  = [fr_note(n) for n in notes_raw]
            notes_en  = [pretty(n)  for n in notes_raw]
            ivstr     = interval_str(scale["iv"])
            n_notes   = len(scale["iv"])
            app_link  = f"{APP_URL}?root={root['name']}&scale={scale['id']}"

            page_url_fr = f"{BASE_URL}/fr/gammes/{root['slug']}/{slug_s}/"
            page_url_en = f"{BASE_URL}/en/scales/{root['slug_en']}/{slug_s}/"

            # ---- Page FR ----
            triads_fr = build_triads(root["name"], scale["ls"], scale["iv"], lang='fr')
            desc_fr   = SCALE_DESCS.get(scale["id"]) or GROUP_DESCS.get(scale["group"], "")
            notes_str = " – ".join(notes_fr)
            ctx_fr = {
                "lang":        "fr",
                "root":        root,
                "scale":       scale,
                "scale_slug":  slug_s,
                "label":       scale["label"],
                "sub":         scale.get("sub", ""),
                "notes_primary":   notes_fr,
                "notes_secondary": notes_en,
                "notes_secondary_label": "Notation anglaise",
                "notes_str":   notes_str,
                "ivstr":       ivstr,
                "triads":      triads_fr,
                "desc":        desc_fr,
                "n_notes":     n_notes,
                "app_link":    app_link,
                "page_url":    page_url_fr,
                "canonical_url": page_url_fr,
                "alt_url_fr":  page_url_fr,
                "alt_url_en":  page_url_en,
                "BASE_URL":    BASE_URL,
                "nav_roots":   [{"name": r["fr"],   "slug": r["slug"]}    for r in ROOTS],
                "nav_base":    f"{BASE_URL}/fr/gammes",
                # UI FR
                "ui_title":         f"Gamme de {root['fr']} {scale['label']} pour basse — {notes_str}",
                "ui_meta_desc":     f"Gamme de {root['fr']} {scale['label']} pour basse 4 cordes : {notes_str}. {n_notes} note{'s' if n_notes>1 else ''}. Intervalles : {ivstr}. Positions sur le manche, tablature interactive.",
                "ui_h1":            f"Gamme de {root['fr']} {scale['label']}",
                "ui_bass":          "Basse 4 cordes",
                "ui_family":        f"famille {'majeure' if scale['fam']=='maj' else 'mineure'}",
                "ui_notes":         "Notes",
                "ui_ivstruct":      "Structure d'intervalles",
                "ui_triads_title":  "Accords de la gamme (triades)",
                "ui_degree":        "Degré",
                "ui_chord":         f"Accord (en {root['fr']})",
                "ui_quality":       "Qualité",
                "ui_about":         "À propos de cette gamme",
                "ui_cta_text":      f"Voir les positions sur le manche, le piano et les arpèges pour <strong>{root['fr']} {scale['label']}</strong> dans l'appli interactive.",
                "ui_cta_btn":       "Explorer dans ScalaBass →",
                "ui_other_keys":    "Même gamme dans d'autres toniques",
                "ui_all_scales":    "Toutes les gammes",
                "ui_og_title":      f"Gamme {root['fr']} {scale['label']} — Basse",
                "ui_og_desc":       f"{root['fr']} {scale['label']} : {notes_str}",
                "ui_schema_head":   f"Gamme de {root['fr']} {scale['label']} pour basse",
                "ui_schema_desc":   f"{root['fr']} {scale['label']} pour basse 4 cordes : {notes_str}. Intervalles : {ivstr}.",
            }
            out_dir_fr = OUT_ROOT_FR / root["slug"] / slug_s
            out_dir_fr.mkdir(parents=True, exist_ok=True)
            (out_dir_fr / "index.html").write_text(scale_tpl.render(**ctx_fr), encoding="utf-8")
            pages_fr.append(page_url_fr)

            # ---- Page EN ----
            triads_en = build_triads(root["name"], scale["ls"], scale["iv"], lang='en')
            desc_en   = SCALE_DESCS_EN.get(scale["id"]) or GROUP_DESCS_EN.get(scale["group"], "")
            notes_str_en = " – ".join(notes_en)
            ctx_en = {
                "lang":        "en",
                "root":        root,
                "scale":       scale,
                "scale_slug":  slug_s,
                "label":       scale.get("label_en", scale["label"]),
                "sub":         scale.get("sub_en", scale.get("sub", "")),
                "notes_primary":   notes_en,
                "notes_secondary": notes_fr,
                "notes_secondary_label": "Solfège",
                "notes_str":   notes_str_en,
                "ivstr":       ivstr,
                "triads":      triads_en,
                "desc":        desc_en,
                "n_notes":     n_notes,
                "app_link":    app_link,
                "page_url":    page_url_en,
                "canonical_url": page_url_en,
                "alt_url_fr":  page_url_fr,
                "alt_url_en":  page_url_en,
                "BASE_URL":    BASE_URL,
                "nav_roots":   [{"name": r["name"], "slug": r["slug_en"]} for r in ROOTS],
                "nav_base":    f"{BASE_URL}/en/scales",
                # UI EN
                "ui_title":        f"{root['name']} {scale.get('label_en', scale['label'])} Scale for Bass — {notes_str_en}",
                "ui_meta_desc":    f"{root['name']} {scale.get('label_en', scale['label'])} scale for 4-string bass: {notes_str_en}. {n_notes} note{'s' if n_notes>1 else ''}. Intervals: {ivstr}. Fretboard positions, interactive tablature.",
                "ui_h1":           f"{root['name']} {scale.get('label_en', scale['label'])} Scale",
                "ui_bass":         "4-string bass",
                "ui_family":       f"{'major' if scale['fam']=='maj' else 'minor'} family",
                "ui_notes":        "Notes",
                "ui_ivstruct":     "Interval Structure",
                "ui_triads_title": "Scale Chords (triads)",
                "ui_degree":       "Degree",
                "ui_chord":        f"Chord (in {root['name']})",
                "ui_quality":      "Quality",
                "ui_about":        "About this scale",
                "ui_cta_text":     f"See fretboard positions, piano and arpeggios for <strong>{root['name']} {scale.get('label_en', scale['label'])}</strong> in the interactive app.",
                "ui_cta_btn":      "Explore in ScalaBass →",
                "ui_other_keys":   "Same scale in other keys",
                "ui_all_scales":   "All scales",
                "ui_og_title":     f"{root['name']} {scale.get('label_en', scale['label'])} Scale — Bass",
                "ui_og_desc":      f"{root['name']} {scale.get('label_en', scale['label'])}: {notes_str_en}",
                "ui_schema_head":  f"{root['name']} {scale.get('label_en', scale['label'])} scale for bass",
                "ui_schema_desc":  f"{root['name']} {scale.get('label_en', scale['label'])} for 4-string bass: {notes_str_en}. Intervals: {ivstr}.",
            }
            out_dir_en = OUT_ROOT_EN / root["slug_en"] / slug_s
            out_dir_en.mkdir(parents=True, exist_ok=True)
            (out_dir_en / "index.html").write_text(scale_tpl.render(**ctx_en), encoding="utf-8")
            pages_en.append(page_url_en)

    # ---- Pages enharmoniques (canonical → page principale bémol/dièse) ----
    print("Génération des pages enharmoniques …")
    for scale in SCALE_DEFS:
        slug_s = scale_slug(scale["id"])
        for eroot in ENHARMONIC_ROOTS:
            notes_raw = build_scale(eroot["name"], scale["ls"], scale["iv"])
            notes_fr  = [fr_note(n) for n in notes_raw]
            notes_en  = [pretty(n)  for n in notes_raw]
            ivstr     = interval_str(scale["iv"])
            n_notes   = len(scale["iv"])
            app_link  = f"{APP_URL}?root={eroot['name']}&scale={scale['id']}"

            page_url_fr      = f"{BASE_URL}/fr/gammes/{eroot['slug']}/{slug_s}/"
            canonical_url_fr = f"{BASE_URL}/fr/gammes/{eroot['canonical_slug']}/{slug_s}/"
            page_url_en      = f"{BASE_URL}/en/scales/{eroot['slug_en']}/{slug_s}/"
            canonical_url_en = f"{BASE_URL}/en/scales/{eroot['canonical_slug_en']}/{slug_s}/"

            # FR
            triads_fr = build_triads(eroot["name"], scale["ls"], scale["iv"], lang='fr')
            desc_fr   = SCALE_DESCS.get(scale["id"]) or GROUP_DESCS.get(scale["group"], "")
            notes_str = " – ".join(notes_fr)
            ctx_fr = {
                "lang":        "fr",
                "root":        eroot,
                "scale":       scale,
                "scale_slug":  slug_s,
                "label":       scale["label"],
                "sub":         scale.get("sub", ""),
                "notes_primary":   notes_fr,
                "notes_secondary": notes_en,
                "notes_secondary_label": "Notation anglaise",
                "notes_str":   notes_str,
                "ivstr":       ivstr,
                "triads":      triads_fr,
                "desc":        desc_fr,
                "n_notes":     n_notes,
                "app_link":    app_link,
                "page_url":    page_url_fr,
                "canonical_url": canonical_url_fr,
                "alt_url_fr":  canonical_url_fr,
                "alt_url_en":  canonical_url_en,
                "BASE_URL":    BASE_URL,
                "nav_roots":   [{"name": r["fr"],   "slug": r["slug"]}    for r in ROOTS],
                "nav_base":    f"{BASE_URL}/fr/gammes",
                "ui_title":         f"Gamme de {eroot['fr']} {scale['label']} pour basse — {notes_str}",
                "ui_meta_desc":     f"Gamme de {eroot['fr']} {scale['label']} pour basse : {notes_str}. {n_notes} note{'s' if n_notes>1 else ''}. Intervalles : {ivstr}.",
                "ui_h1":            f"Gamme de {eroot['fr']} {scale['label']}",
                "ui_bass":          "Basse 4 cordes",
                "ui_family":        f"famille {'majeure' if scale['fam']=='maj' else 'mineure'}",
                "ui_notes":         "Notes",
                "ui_ivstruct":      "Structure d'intervalles",
                "ui_triads_title":  "Accords de la gamme (triades)",
                "ui_degree":        "Degré",
                "ui_chord":         f"Accord (en {eroot['fr']})",
                "ui_quality":       "Qualité",
                "ui_about":         "À propos de cette gamme",
                "ui_cta_text":      f"Voir les positions sur le manche pour <strong>{eroot['fr']} {scale['label']}</strong> dans l'appli interactive.",
                "ui_cta_btn":       "Explorer dans ScalaBass →",
                "ui_other_keys":    "Même gamme dans d'autres toniques",
                "ui_all_scales":    "Toutes les gammes",
                "ui_og_title":      f"Gamme {eroot['fr']} {scale['label']} — Basse",
                "ui_og_desc":       f"{eroot['fr']} {scale['label']} : {notes_str}",
                "ui_schema_head":   f"Gamme de {eroot['fr']} {scale['label']} pour basse",
                "ui_schema_desc":   f"{eroot['fr']} {scale['label']} pour basse : {notes_str}. Intervalles : {ivstr}.",
            }
            out_dir_fr = OUT_ROOT_FR / eroot["slug"] / slug_s
            out_dir_fr.mkdir(parents=True, exist_ok=True)
            (out_dir_fr / "index.html").write_text(scale_tpl.render(**ctx_fr), encoding="utf-8")
            pages_fr.append(page_url_fr)

            # EN
            triads_en = build_triads(eroot["name"], scale["ls"], scale["iv"], lang='en')
            desc_en   = SCALE_DESCS_EN.get(scale["id"]) or GROUP_DESCS_EN.get(scale["group"], "")
            notes_str_en = " – ".join(notes_en)
            ctx_en = {
                "lang":        "en",
                "root":        eroot,
                "scale":       scale,
                "scale_slug":  slug_s,
                "label":       scale.get("label_en", scale["label"]),
                "sub":         scale.get("sub_en", scale.get("sub", "")),
                "notes_primary":   notes_en,
                "notes_secondary": notes_fr,
                "notes_secondary_label": "Solfège",
                "notes_str":   notes_str_en,
                "ivstr":       ivstr,
                "triads":      triads_en,
                "desc":        desc_en,
                "n_notes":     n_notes,
                "app_link":    app_link,
                "page_url":    page_url_en,
                "canonical_url": canonical_url_en,
                "alt_url_fr":  canonical_url_fr,
                "alt_url_en":  canonical_url_en,
                "BASE_URL":    BASE_URL,
                "nav_roots":   [{"name": r["name"], "slug": r["slug_en"]} for r in ROOTS],
                "nav_base":    f"{BASE_URL}/en/scales",
                "ui_title":        f"{eroot['name']} {scale.get('label_en', scale['label'])} Scale for Bass — {notes_str_en}",
                "ui_meta_desc":    f"{eroot['name']} {scale.get('label_en', scale['label'])} scale for bass: {notes_str_en}. {n_notes} note{'s' if n_notes>1 else ''}. Intervals: {ivstr}.",
                "ui_h1":           f"{eroot['name']} {scale.get('label_en', scale['label'])} Scale",
                "ui_bass":         "4-string bass",
                "ui_family":       f"{'major' if scale['fam']=='maj' else 'minor'} family",
                "ui_notes":        "Notes",
                "ui_ivstruct":     "Interval Structure",
                "ui_triads_title": "Scale Chords (triads)",
                "ui_degree":       "Degree",
                "ui_chord":        f"Chord (in {eroot['name']})",
                "ui_quality":      "Quality",
                "ui_about":        "About this scale",
                "ui_cta_text":     f"See fretboard positions for <strong>{eroot['name']} {scale.get('label_en', scale['label'])}</strong> in the interactive app.",
                "ui_cta_btn":      "Explore in ScalaBass →",
                "ui_other_keys":   "Same scale in other keys",
                "ui_all_scales":   "All scales",
                "ui_og_title":     f"{eroot['name']} {scale.get('label_en', scale['label'])} Scale — Bass",
                "ui_og_desc":      f"{eroot['name']} {scale.get('label_en', scale['label'])}: {notes_str_en}",
                "ui_schema_head":  f"{eroot['name']} {scale.get('label_en', scale['label'])} scale for bass",
                "ui_schema_desc":  f"{eroot['name']} {scale.get('label_en', scale['label'])} for bass: {notes_str_en}. Intervals: {ivstr}.",
            }
            out_dir_en = OUT_ROOT_EN / eroot["slug_en"] / slug_s
            out_dir_en.mkdir(parents=True, exist_ok=True)
            (out_dir_en / "index.html").write_text(scale_tpl.render(**ctx_en), encoding="utf-8")
            pages_en.append(page_url_en)

    # ---- Hub FR ----
    OUT_ROOT_FR.mkdir(parents=True, exist_ok=True)
    hub_ctx_fr = {
        "scales": SCALE_DEFS,
        "roots":  ROOTS,
        "BASE_URL": BASE_URL,
        "scale_slug": scale_slug,
    }
    (OUT_ROOT_FR / "index.html").write_text(hub_fr_tpl.render(**hub_ctx_fr), encoding="utf-8")
    pages_fr.append(f"{BASE_URL}/fr/gammes/")

    # ---- Hub EN ----
    OUT_ROOT_EN.mkdir(parents=True, exist_ok=True)
    hub_ctx_en = {
        "scales": SCALE_DEFS,
        "roots":  ROOTS,
        "BASE_URL": BASE_URL,
        "scale_slug": scale_slug,
        "lang": "en",
    }
    (OUT_ROOT_EN / "index.html").write_text(hub_fr_tpl.render(**hub_ctx_en), encoding="utf-8")
    pages_en.append(f"{BASE_URL}/en/scales/")

    # ---- Sitemap ----
    write_sitemap(pages_fr, pages_en)

    print(f"  FR : {len(pages_fr)-1} pages gammes + 1 hub = {len(pages_fr)} pages")
    print(f"  EN : {len(pages_en)-1} pages scales + 1 hub = {len(pages_en)} pages")
    print("  sitemap.xml mis à jour")
    print("Done.")

def write_sitemap(pages_fr, pages_en):
    sitemap_path = REPO_ROOT / "sitemap.xml"
    existing = []
    if sitemap_path.exists():
        content = sitemap_path.read_text(encoding="utf-8")
        existing = re.findall(r'<loc>(.*?)</loc>', content)
    kept = [u for u in existing if "/fr/gammes/" not in u and "/en/scales/" not in u]
    all_urls = kept + pages_fr + pages_en
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for url in all_urls:
        lines.append(f'  <url><loc>{url}</loc></url>')
    lines.append('</urlset>')
    sitemap_path.write_text('\n'.join(lines) + '\n', encoding="utf-8")

if __name__ == "__main__":
    main()
