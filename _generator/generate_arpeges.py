#!/usr/bin/env python3
"""
ScalaBass — Générateur de pages statiques SEO — Arpèges Basse & Guitare
=======================================================================
Génère fr/arpeges-basse/{note}/{arpege}/index.html     (27 × 17 = 459 FR basse)
Génère en/arpeggios-bass/{note}/{arpege}/index.html    (459 EN basse)
Génère fr/arpeges-guitare/{note}/{arpege}/index.html   (459 FR guitare)
Génère en/arpeggios-guitar/{note}/{arpege}/index.html  (459 EN guitare)
+ 4 hubs + sitemap

Lancer depuis la racine du repo :
    pip install -r _generator/requirements.txt
    python _generator/generate_arpeges.py
"""

import re, sys
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

sys.path.insert(0, str(Path(__file__).parent))
from generate import ROOTS, ENHARMONIC_ROOTS

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).parent.parent
TMPL_DIR  = Path(__file__).parent / "templates"
BASE_URL  = "https://labussiere21.github.io/Gammes"

NOTE_NAMES_FR = ['Do', 'Réb', 'Ré', 'Mib', 'Mi', 'Fa', 'Solb', 'Sol', 'Lab', 'La', 'Sib', 'Si']
NOTE_NAMES_EN = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G', 'Ab', 'A', 'Bb', 'B']

ARP_IV_LABEL = {
    0: 'R', 1: '♭9', 2: '9', 3: '♭3', 4: '3', 5: '4/11',
    6: '♭5', 7: '5', 8: '♯5', 9: '6', 10: '♭7', 11: '7',
    14: '9', 17: '11', 18: '♯11', 21: '13',
}

# ---------------------------------------------------------------------------
# DONNÉES ARPÈGES (communes basse et guitare)
# ---------------------------------------------------------------------------
ARPEGE_GROUPS = [
    {"id": "maj3", "label_fr": "Tierce Majeure", "label_en": "Major third", "arps": [
        {"id": "maj",        "label_fr": "Majeur",       "label_en": "Major",          "iv": [0,4,7],           "sym": ""},
        {"id": "maj7",       "label_fr": "Majeur 7",     "label_en": "Major 7",        "iv": [0,4,7,11],        "sym": "maj7"},
        {"id": "maj9",       "label_fr": "Majeur 9",     "label_en": "Major 9",        "iv": [0,4,7,11,14],     "sym": "maj9"},
        {"id": "maj7sharp11","label_fr": "Maj7♯11",      "label_en": "Maj7♯11",        "iv": [0,4,7,11,18],     "sym": "maj7♯11"},
        {"id": "maj13",      "label_fr": "Majeur 13",    "label_en": "Major 13",       "iv": [0,4,7,11,14,21],  "sym": "maj13"},
        {"id": "dom7",       "label_fr": "Dominant 7",   "label_en": "Dominant 7",     "iv": [0,4,7,10],        "sym": "7"},
        {"id": "dom9",       "label_fr": "Dominant 9",   "label_en": "Dominant 9",     "iv": [0,4,7,10,14],     "sym": "9"},
        {"id": "dom11",      "label_fr": "Dominant 11",  "label_en": "Dominant 11",    "iv": [0,4,7,10,14,17],  "sym": "11"},
        {"id": "dom13",      "label_fr": "Dominant 13",  "label_en": "Dominant 13",    "iv": [0,4,7,10,14,21],  "sym": "13"},
        {"id": "maj6",       "label_fr": "Majeur 6",     "label_en": "Major 6",        "iv": [0,4,7,9],         "sym": "6"},
    ]},
    {"id": "min3", "label_fr": "Tierce mineure", "label_en": "Minor third", "arps": [
        {"id": "min",        "label_fr": "Mineur",       "label_en": "Minor",          "iv": [0,3,7],           "sym": "m"},
        {"id": "min7",       "label_fr": "Mineur 7",     "label_en": "Minor 7",        "iv": [0,3,7,10],        "sym": "m7"},
        {"id": "min9",       "label_fr": "Mineur 9",     "label_en": "Minor 9",        "iv": [0,3,7,10,14],     "sym": "m9"},
        {"id": "min11",      "label_fr": "Mineur 11",    "label_en": "Minor 11",       "iv": [0,3,7,10,14,17],  "sym": "m11"},
        {"id": "min13",      "label_fr": "Mineur 13",    "label_en": "Minor 13",       "iv": [0,3,7,10,14,17,21],"sym": "m13"},
        {"id": "min6",       "label_fr": "Mineur 6",     "label_en": "Minor 6",        "iv": [0,3,7,9],         "sym": "m6"},
        {"id": "minmaj7",    "label_fr": "Mineur Maj7",  "label_en": "Minor Maj7",     "iv": [0,3,7,11],        "sym": "mMaj7"},
    ]},
    {"id": "nosub", "label_fr": "Sans tierce", "label_en": "No third", "arps": [
        {"id": "p5",         "label_fr": "Power 5",      "label_en": "Power 5",        "iv": [0,7],             "sym": "5"},
        {"id": "sus2",       "label_fr": "Sus2",         "label_en": "Sus2",           "iv": [0,2,7],           "sym": "sus2"},
        {"id": "sus4",       "label_fr": "Sus4",         "label_en": "Sus4",           "iv": [0,5,7],           "sym": "sus4"},
        {"id": "dom7sus4",   "label_fr": "7sus4",        "label_en": "7sus4",          "iv": [0,5,7,10],        "sym": "7sus4"},
    ]},
    {"id": "aug5", "label_fr": "Quinte augmentée", "label_en": "Augmented fifth", "arps": [
        {"id": "aug",        "label_fr": "Augmenté",     "label_en": "Augmented",      "iv": [0,4,8],           "sym": "aug"},
        {"id": "aug7",       "label_fr": "7 Augmenté",   "label_en": "Augmented 7",    "iv": [0,4,8,10],        "sym": "7aug"},
    ]},
    {"id": "dim5", "label_fr": "Quinte diminuée", "label_en": "Diminished fifth", "arps": [
        {"id": "dim",        "label_fr": "Diminué",      "label_en": "Diminished",     "iv": [0,3,6],           "sym": "dim"},
        {"id": "halfdim",    "label_fr": "Demi-diminué", "label_en": "Half-diminished","iv": [0,3,6,10],        "sym": "m7♭5"},
        {"id": "dim7",       "label_fr": "7 Diminué",    "label_en": "Diminished 7",   "iv": [0,3,6,9],         "sym": "dim7"},
        {"id": "dom7b5",     "label_fr": "7 ♭5",         "label_en": "7 ♭5",           "iv": [0,4,6,10],        "sym": "7♭5"},
    ]},
]

ALL_ARPS    = [a for g in ARPEGE_GROUPS for a in g["arps"]]
GROUP_BY_ID = {a["id"]: g for g in ARPEGE_GROUPS for a in g["arps"]}

# ---------------------------------------------------------------------------
# DESCRIPTIONS — BASSE FR
# ---------------------------------------------------------------------------
DESC_BASS_FR = {
    "maj":        "L'arpège majeur parcourt les notes de la triade majeure (fondamentale, tierce majeure, quinte juste). Pilier du jeu de basse, il se retrouve sur les degrés I et IV de toute progression tonale, du blues au jazz en passant par le rock et la funk. Ses positions en boîtes CAGED couvrent tout le manche de façon systématique.",
    "maj7":       "L'arpège majeur 7 ajoute la septième majeure à la triade, créant une couleur lumineuse et sereine. Idéal sur les degrés I et IV en jazz et bossa nova, il doit être joué avec soin pour éviter la friction de la septième avec la tonique de l'accord suivant.",
    "maj9":       "L'arpège majeur 9 étend la triade majeure avec la septième majeure et la neuvième. Sa couleur lumineuse et ouverte est au cœur du jazz contemporain et de la pop sophistiquée. La neuvième ajoute de la fluidité mélodique aux lignes de walking bass sur les degrés I et IV.",
    "maj7sharp11":"L'arpège maj7♯11 est issu de la gamme lydienne. Sa quarte augmentée (♯11) remplace la quarte juste, apportant une couleur brillante et moderne sans dissonance agressive. Très utilisé en jazz fusion et bossa nova sur les degrés I ou IV lydiens.",
    "maj13":      "L'arpège majeur 13 empile neuvième, onzième et treizième sur la triade maj7, offrant une richesse harmonique maximale. Sur la basse, on sélectionne généralement 3 à 4 des notes disponibles pour construire une ligne cohérente. Très présent en jazz avancé et fusion.",
    "dom7":       "L'arpège de dominante 7 est l'arpège le plus important du blues. Son triton interne (tierce majeure ↔ septième mineure) crée une tension directionnelle vers la résolution. Présent sur le degré V de toute gamme majeure et sur les trois degrés I7, IV7, V7 du blues.",
    "dom9":       "L'arpège de dominante 9 cumule le triton de la dominante 7 et la neuvième, décuplant la tension harmonique. Sa résolution vers la tonique est encore plus forte qu'avec la simple 7. C'est l'arpège de référence pour les lignes de basse blues et funk sophistiquées sur le degré V.",
    "dom11":      "L'arpège de dominante 11 est l'accord de suspension par excellence en jazz. Sa quarte juste crée une tension caractéristique résolue en retirant la tierce. Les positions centrales du manche de basse permettent de faire sonner toute la richesse de cet accord.",
    "dom13":      "L'arpège de dominante 13 est l'accord de dominante le plus complet du jazz. Sa treizième (sixte) ajoutée sur la dominante 9 crée une tension maximale qui réclame sa résolution. Indispensable dans les cadences ii – V7(13) – I du bebop.",
    "maj6":       "L'arpège majeur 6 enrichit la triade d'une sixte majeure sans la tension de la septième. Sa couleur douce et légèrement rétro est très utilisée en jazz, swing et bossa nova. Il évite la dissonance de la septième tout en ajoutant de la profondeur harmonique.",
    "min":        "L'arpège mineur est le pilier des tonalités mineures à la basse. Sa tierce mineure lui donne sa couleur mélancolique caractéristique. Indispensable au rock, jazz, soul et blues, il se retrouve aux degrés II, III et VI des progressions majeures.",
    "min7":       "L'arpège mineur 7 est l'arpège de basse le plus polyvalent du jazz et de la funk. Il correspond aux degrés II, III et VI de la gamme majeure et constitue la base de toutes les lignes de basse sur les progressions ii-V-I. Marcus Miller et Jaco Pastorius en ont fait leur marque de fabrique.",
    "min9":       "L'arpège mineur 9 enrichit la triade mineure d'une septième mineure et d'une neuvième, créant une palette sonore douce et mélancolique. Incontournable en jazz, soul et R&B, il offre de nombreuses possibilités pour des lignes de basse expressives et des ornements mélodiques.",
    "min11":      "L'arpège mineur 11 ajoute l'onzième juste au min9, créant une couleur suspendue et enveloppante caractéristique du jazz modal et de la soul contemporaine. Sa quarte résonne parfaitement avec la septième mineure pour des progressions de basse profondes et évocatrices.",
    "min13":      "L'arpège mineur 13 est la forme mineure la plus riche, avec ses 7 notes encapsulant toute la gamme dorienne. À la basse, il ouvre un vaste vocabulaire de lignes mélodiques et est très présent en jazz fusion sur les modes mineur et dorien.",
    "min6":       "L'arpège mineur 6 ajoute la sixte majeure à la triade mineure, créant une couleur douce-amère très expressive. Très utilisé en jazz et bossa nova, notamment dans les progressions de basse descendantes chromatiques (mM7 – m7 – m6).",
    "minmaj7":    "L'arpège mineur Maj7 combine une tierce mineure et une septième majeure — une tension interne propre à la gamme mineure harmonique. Sa couleur mystérieuse est utilisée en jazz avancé, musique de film et dans la descente chromatique mM7 – m7 – m6.",
    "p5":         "L'arpège Power 5 ne contient que la fondamentale et la quinte juste, sans tierce. Neutre harmoniquement (ni majeur ni mineur), il est la fondation du rock et du métal à la basse. Deux notes suffisent à poser l'accord tout en laissant aux autres instruments toute liberté pour la couleur harmonique.",
    "sus2":       "L'arpège sus2 évite la tierce et utilise la seconde majeure, créant une couleur ouverte sans ambiguïté majeure/mineure. Expressif en rock et pop moderne, il laisse beaucoup de liberté harmonique et s'intègre facilement dans des textures aériennes et contemporaines.",
    "sus4":       "L'arpège sus4 remplace la tierce par la quarte juste, créant une tension suspendue qui cherche naturellement sa résolution. Son instabilité naturelle rend les lignes de basse dynamiques. Très présent en funk et rock pour créer des moments de tension expressifs.",
    "dom7sus4":   "L'arpège 7sus4 combine la suspension de quarte et la septième mineure, créant une texture ouverte tout en maintenant la tension fonctionnelle de dominante. Très apprécié en jazz-fusion et funk (Herbie Hancock, Marcus Miller), il peut précéder un accord de dominante ou se résoudre directement.",
    "aug":        "L'arpège augmenté remplace la quinte juste par une quinte augmentée, créant une couleur symétrique et mystérieuse. Sa géométrie particulière — une même forme couvre 3 toniques — simplifie son apprentissage. Utilisé en jazz et musique de film pour des transitions colorées.",
    "aug7":       "L'arpège augmenté 7 cumule quinte augmentée et septième mineure. Issu de la gamme par tons, il précède souvent une résolution vers un accord mineur avec une double tension très expressive. Très apprécié en jazz avancé et fusion.",
    "dim":        "L'arpège diminué empile des tierces mineures sur une quinte diminuée. Sa symétrie — une même forme couvre 3 toniques différentes — facilite son apprentissage sur tout le manche. Excellent pour des passages de tension dramatiques avant une résolution, en jazz comme en classique.",
    "halfdim":    "L'arpège demi-diminué (ø) est central dans les progressions jazz en mineur sur le degré ii. Sa quinte diminuée et sa septième mineure créent une tension qui appelle la résolution vers le V7 puis l'Im. Indispensable pour les cadences ii°–V7–Im.",
    "dim7":       "L'arpège diminué 7 divise l'octave en 4 parties égales. Sa symétrie parfaite lui permet de se résoudre vers 4 toniques différentes — 3 formes couvrent les 12 toniques. Très utilisé en jazz et musique classique pour des passages chromatiques et dramatiques.",
    "dom7b5":     "L'arpège 7♭5 combine tierce majeure, quinte diminuée et septième mineure. Sa quinte bémol crée un second triton, intensifiant la tension de dominante. Interchangeable avec le V7 d'une tonique à distance de triton (substitution tritonique), c'est un outil clé de la réharmonisation jazz.",
}

# ---------------------------------------------------------------------------
# DESCRIPTIONS — BASSE EN
# ---------------------------------------------------------------------------
DESC_BASS_EN = {
    "maj":        "The major arpeggio spans the three notes of the major triad (root, major third, perfect fifth). A cornerstone of bass playing, it appears on degrees I and IV of any tonal progression from blues to jazz. CAGED box positions provide systematic coverage of the entire neck.",
    "maj7":       "The major 7th arpeggio adds the major seventh to the triad, creating a luminous, serene color. Ideal on degrees I and IV in jazz and bossa nova. Play its seventh carefully to avoid friction with the root of the next chord.",
    "maj9":       "The major 9th arpeggio extends the major triad with the major seventh and ninth. Its luminous, open color is central to contemporary jazz and sophisticated pop. The ninth adds melodic flow to walking bass lines on degrees I and IV.",
    "maj7sharp11":"The maj7♯11 arpeggio derives from the Lydian mode. Its augmented fourth (♯11) replaces the perfect fourth, adding a brilliant, modern color without aggressive dissonance. Widely used in jazz fusion and bossa nova on Lydian degrees I and IV.",
    "maj13":      "The major 13th arpeggio stacks ninth, eleventh, and thirteenth over a maj7 triad, offering maximum harmonic richness. On bass, you typically select 3–4 of its available notes to build a coherent line. Very present in advanced jazz and fusion.",
    "dom7":       "The dominant 7th arpeggio is the most important arpeggio in blues. Its internal tritone (major third ↔ minor seventh) creates directional tension toward resolution. Found on degree V of any major key and on all three blues degrees I7, IV7, V7.",
    "dom9":       "The dominant 9th arpeggio combines the tritone of the dominant 7th with the ninth, multiplying harmonic tension. Its resolution toward the tonic is even stronger than a simple 7th. The reference arpeggio for sophisticated blues and funk bass lines on degree V.",
    "dom11":      "The dominant 11th arpeggio is the classic suspension chord in jazz. Its perfect fourth creates characteristic tension that resolves by removing the third. Central neck positions let you voice the full richness of this chord idiomatically on bass.",
    "dom13":      "The dominant 13th arpeggio is the most complete dominant chord in jazz. Its thirteenth (sixth) added over the dominant 9 creates maximum tension that demands resolution. Essential in the ii – V7(13) – I cadences of bebop.",
    "maj6":       "The major 6th arpeggio enriches the triad with a major sixth without the tension of a seventh. Its soft, slightly retro color is widely used in jazz, swing, and bossa nova. It avoids seventh dissonance while adding harmonic depth.",
    "min":        "The minor arpeggio is the foundation of minor tonalities on bass. Its minor third gives it a characteristic melancholic color. Indispensable in rock, jazz, soul, and blues, it appears on degrees II, III, and VI of major progressions.",
    "min7":       "The minor 7th arpeggio is the most versatile jazz and funk bass arpeggio. It corresponds to degrees II, III, and VI of the major scale and forms the foundation of all bass lines in ii-V-I progressions. A cornerstone of the Marcus Miller and Jaco Pastorius style.",
    "min9":       "The minor 9th arpeggio enriches the minor triad with a minor seventh and ninth, creating a soft, melancholic sound palette. Essential in jazz, soul, and R&B, it offers numerous possibilities for expressive bass lines and melodic ornaments.",
    "min11":      "The minor 11th arpeggio adds the perfect eleventh to the min9, creating a suspended, enveloping color characteristic of modal jazz and contemporary soul. Its fourth resonates perfectly with the minor seventh for deep, evocative bass progressions.",
    "min13":      "The minor 13th arpeggio is the richest minor form, with its 7 notes encapsulating the entire Dorian mode. On bass, it opens a vast vocabulary of melodic lines widely used in jazz fusion on minor and Dorian modes.",
    "min6":       "The minor 6th arpeggio adds the major sixth to the minor triad, creating a bittersweet, expressive color. Widely used in jazz and bossa nova, particularly in descending chromatic bass progressions (mM7 – m7 – m6).",
    "minmaj7":    "The minor maj7 arpeggio combines a minor third with a major seventh — an internal tension specific to the harmonic minor scale. Its mysterious color is used in advanced jazz, film music, and the chromatic descent mM7 – m7 – m6.",
    "p5":         "The Power 5 arpeggio contains only the root and perfect fifth, with no third. Harmonically neutral (neither major nor minor), it is the foundation of rock and metal on bass. Two notes suffice to define the chord while giving other instruments complete harmonic freedom.",
    "sus2":       "The sus2 arpeggio avoids the third and uses the major second, creating an open color with no major/minor ambiguity. Expressive in modern rock and pop, it allows great harmonic freedom and integrates easily into airy, contemporary textures.",
    "sus4":       "The sus4 arpeggio replaces the third with a perfect fourth, creating suspended tension that naturally seeks resolution. Its inherent instability makes bass lines dynamic. Very present in funk and rock for expressive moments of tension.",
    "dom7sus4":   "The 7sus4 arpeggio combines the fourth suspension with the minor seventh, creating an open texture while maintaining dominant functional tension. Prized in jazz-fusion and funk (Herbie Hancock, Marcus Miller), it can precede a dominant chord or resolve directly.",
    "aug":        "The augmented arpeggio replaces the perfect fifth with an augmented fifth, creating a symmetric, mysterious color. Its particular geometry — one shape covers 3 tonics — simplifies learning across the neck. Used in jazz and film music for colorful transitions.",
    "aug7":       "The augmented 7th arpeggio combines augmented fifth and minor seventh. Derived from the whole-tone scale, it often precedes resolution to a minor chord with expressive double tension. Very appreciated in advanced jazz and fusion.",
    "dim":        "The diminished arpeggio stacks minor thirds over a diminished fifth. Its symmetry — one shape covers 3 different tonics — facilitates learning across the entire neck. Excellent for dramatic tension passages before resolution, in jazz as in classical music.",
    "halfdim":    "The half-diminished arpeggio (ø) is central in minor jazz progressions on degree ii. Its diminished fifth and minor seventh create tension that calls for resolution toward V7 then Im. Essential for ii°–V7–Im cadences.",
    "dim7":       "The diminished 7th arpeggio divides the octave into 4 equal parts. Its perfect symmetry allows it to resolve to 4 different tonics — 3 shapes cover all 12 keys. Widely used in jazz and classical music for chromatic and dramatic passages.",
    "dom7b5":     "The 7♭5 arpeggio combines major third, diminished fifth, and minor seventh. Its flatted fifth creates a second tritone, intensifying dominant tension. Interchangeable with the V7 a tritone away (tritone substitution), it is a key tool in jazz reharmonization.",
}

# ---------------------------------------------------------------------------
# DESCRIPTIONS — GUITARE FR
# ---------------------------------------------------------------------------
DESC_GUIT_FR = {
    "maj":        "L'arpège majeur est fondamental à la guitare. Les 5 positions CAGED permettent de le travailler sur tout le manche. C'est la base du sweep picking et de l'economy picking pour des lignes mélodiques fluides sur les degrés I et IV de toute progression.",
    "maj7":       "L'arpège majeur 7 apporte la couleur jazz lumineuse par excellence sur les degrés I et IV. Ses formes compactes sur 3 à 4 cordes se transposent facilement via le système CAGED. Idéal pour improviser en jazz, bossa nova et pop sophistiquée.",
    "maj9":       "L'arpège majeur 9 enrichit le maj7 de la neuvième, ajoutant une dimension impressionniste. En position haute, ses extensions créent de superbes lignes mélodiques en jazz modal et fusion. On sélectionne généralement 4-5 notes pour des runs fluides.",
    "maj7sharp11":"L'arpège maj7♯11 est issu de la gamme lydienne et apporte une couleur brillante et flottante. Sa quarte augmentée (♯11) est caractéristique du jazz modal et de la fusion. Ses positions en quartes empilées sur la guitare donnent des sonorités très modernes.",
    "maj13":      "L'arpège majeur 13 offre une richesse harmonique maximale avec ses 6 notes. Sur la guitare, on sélectionne les intervalles clés — généralement tierce, septième et treizième — pour des voicings jouables. Sa couleur lyrique est idéale pour les ballades jazz.",
    "dom7":       "L'arpège de dominante 7 est la brique fondamentale du blues à la guitare. Son triton interne (tierce ↔ septième mineure) crée la tension caractéristique du blues. Présent sur les degrés I7, IV7, V7 du blues, il se pratique en positions CAGED et en scale boxes.",
    "dom9":       "L'arpège de dominante 9 enrichit la dominante 7 d'une neuvième. Sa résolution vers la tonique est encore plus forte. Sur la guitare, il s'intègre parfaitement dans les lignes blues-rock et funk, notamment pour les solos en position haute.",
    "dom11":      "L'arpège de dominante 11 crée une suspension caractéristique du jazz fusion. Sa quarte juste apporte une texture ouverte et flottante. Sur la guitare, les voicings quartal (quartes empilées) en capturent idéalement la couleur modale.",
    "dom13":      "L'arpège de dominante 13 est la dominante la plus riche du jazz. Sa treizième (sixte) sur le V9 crée une tension maximale. Sur la guitare, on sélectionne tierce, septième et treizième pour des voicings compacts et efficaces sur les 4 cordes médianes.",
    "maj6":       "L'arpège majeur 6 apporte une couleur jazz douce et légèrement rétro. Très utilisé en jazz, swing et bossa nova, il évite la dissonance de la septième. Sur la guitare, ses formes en position ouverte (G6, D6) sonnent avec beaucoup de chaleur.",
    "min":        "L'arpège mineur est incontournable à la guitare. Ses boîtes CAGED en position mineure couvrent tout le manche. Indispensable au rock, jazz, soul et blues sur les degrés II, III et VI des progressions majeures, il est aussi la base du solo pentatonique étendu.",
    "min7":       "L'arpège mineur 7 est le plus polyvalent du jazz et de la funk à la guitare. Il se retrouve aux degrés II, III et VI de la gamme majeure et constitue la base des progressions ii-V-I. Ses formes compactes permettent des runs fluides et des lignes mélodiques expressives.",
    "min9":       "L'arpège mineur 9 enrichit le min7 de la neuvième, ajoutant une touche de fraîcheur à la couleur sombre du mineur. Très utilisé en jazz contemporain, soul et R&B. Sur la guitare, les voicings sans quinte (fondamentale, tierce, septième, neuvième) sont très efficaces.",
    "min11":      "L'arpège mineur 11 est la signature du jazz modal et du néo-soul. Sa quarte juste sur le min9 crée une texture enveloppante. Ses voicings en quartes empilées — très populaires en jazz fusion — capturent idéalement cette couleur modale sur la guitare.",
    "min13":      "L'arpège mineur 13 encapsule toute la gamme dorienne en un seul arpège. Sur la guitare, il offre un vocabulaire mélodique immense pour les solos en contexte mineur modal. Très utilisé par les guitaristes jazz-fusion pour des lignes sophistiquées.",
    "min6":       "L'arpège mineur 6 associe la tierce mineure et la sixte majeure, créant une couleur douce-amère très expressive. Très utilisé en jazz et bossa nova. Sur la guitare, ses voicings proches du demi-diminué facilitent la mémorisation des positions.",
    "minmaj7":    "L'arpège mineur Maj7 combine tierce mineure et septième majeure, créant une tension interne très particulière. Popularisé par les musiques de film d'Hitchcock, il s'intègre dans la descente chromatique mM7–m7–m6. Sa sonorité mystérieuse est très efficace dans les solos dramatiques.",
    "p5":         "L'arpège Power 5 (fondamentale + quinte) est neutre harmoniquement, ni majeur ni mineur. Sur la guitare électrique avec distorsion, il est la base du rock et du métal. Facile à mémoriser (deux notes à distance de quinte), il permet des runs rapides sur tout le manche.",
    "sus2":       "L'arpège sus2 évite la tierce pour une couleur ouverte sans ambiguïté majeure/mineure. Très populaire en rock acoustique et pop, les formes Dsus2 et Asus2 en position ouverte sont des classiques. À l'électrique, il crée des textures aériennes très contemporaines.",
    "sus4":       "L'arpège sus4 remplace la tierce par la quarte, créant une tension qui cherche sa résolution. Sur la guitare, la progression sus4 → majeur est une ornementation classique. Les formes Dsus4 et Asus4 en position ouverte sont parmi les plus expressives du répertoire acoustique.",
    "dom7sus4":   "L'arpège 7sus4 combine la suspension de quarte et la septième mineure de dominante, créant une texture ouverte très jazz-fusion. Herbie Hancock en a fait un pilier de son langage. Sur la guitare, ses voicings sans quinte sont très efficaces en position haute.",
    "aug":        "L'arpège augmenté remplace la quinte par une quinte augmentée, créant une couleur symétrique et mystérieuse. Sa géométrie unique — une même forme couvre 3 toniques — simplifie l'apprentissage. Très expressif pour des transitions chromatiques et des effets de tension en jazz et musique de film.",
    "aug7":       "L'arpège augmenté 7 cumule quinte augmentée et septième mineure. Issu de la gamme par tons, il précède souvent une résolution vers un accord mineur. Sur la guitare, sa symétrie le rend facile à déplacer et il est très efficace dans les solos de jazz avancé.",
    "dim":        "L'arpège diminué empile trois tierces mineures. Sa symétrie parfaite — une forme couvre 3 toniques différentes — en fait un outil compact sur tout le manche. Sur la guitare, il est très utilisé en sweep picking pour des lignes chromatiques dramatiques.",
    "halfdim":    "L'arpège demi-diminué (ø) est central dans les progressions ii–V–I en mineur en jazz. Sa quinte diminuée et sa septième mineure créent une tension qui appelle la résolution. Sur la guitare, ses voicings compacts se superposent aux formes m6, facilitant la mémorisation.",
    "dim7":       "L'arpège diminué 7 divise l'octave en 4 parties égales. Sa symétrie parfaite le rend très pratique à la guitare — 3 formes couvrent les 12 toniques. Idéal pour le sweep picking chromatique et les passages dramatiques en jazz, rock et classique.",
    "dom7b5":     "L'arpège 7♭5 combine tierce majeure, quinte diminuée et septième mineure. Sa quinte bémol crée un second triton, intensifiant la tension de dominante. Interchangeable avec le V7 d'une tonique à distance de triton, c'est un outil clé de la réharmonisation jazz pour le guitariste.",
}

# ---------------------------------------------------------------------------
# DESCRIPTIONS — GUITARE EN
# ---------------------------------------------------------------------------
DESC_GUIT_EN = {
    "maj":        "The major arpeggio is fundamental to guitar playing. The 5 CAGED positions let you practice it across the entire neck. It is the foundation of sweep picking and economy picking for smooth melodic lines on degrees I and IV of any progression.",
    "maj7":       "The major 7th arpeggio delivers the quintessential jazz luminosity on degrees I and IV. Its compact 3–4 string shapes transpose easily via the CAGED system. Ideal for improvising in jazz, bossa nova, and sophisticated pop.",
    "maj9":       "The major 9th arpeggio enriches the maj7 with the ninth, adding an Impressionist dimension. In higher positions, its extensions create superb melodic lines in modal jazz and fusion. You typically select 4–5 notes for smooth runs.",
    "maj7sharp11":"The maj7♯11 arpeggio comes from the Lydian mode and brings a brilliant, floating color. Its augmented fourth (♯11) is characteristic of modal jazz and fusion. Quartal voicings on guitar give it a very contemporary sound.",
    "maj13":      "The major 13th arpeggio offers maximum harmonic richness with its 6 notes. On guitar, select the key intervals — typically third, seventh, and thirteenth — for playable voicings. Its lyrical color is ideal for jazz ballads.",
    "dom7":       "The dominant 7th arpeggio is the building block of blues guitar. Its internal tritone (third ↔ minor seventh) creates the characteristic blues tension. Used on I7, IV7, and V7 blues degrees, it is practiced via CAGED positions and scale boxes.",
    "dom9":       "The dominant 9th arpeggio enriches the dominant 7th with a ninth. Its resolution to the tonic is even more powerful. On guitar, it integrates perfectly into blues-rock and funk lines, especially for solos in higher positions.",
    "dom11":      "The dominant 11th arpeggio creates a characteristic suspension in jazz fusion. Its perfect fourth brings an open, floating texture. On guitar, quartal voicings (stacked fourths) ideally capture its modal color.",
    "dom13":      "The dominant 13th arpeggio is the richest dominant in jazz. Its thirteenth (sixth) over the V9 creates maximum tension. On guitar, select third, seventh, and thirteenth for compact voicings effective on the middle 4 strings.",
    "maj6":       "The major 6th arpeggio brings a soft, slightly retro jazz color. Widely used in jazz, swing, and bossa nova, it avoids seventh dissonance. On guitar, its open-position shapes (G6, D6) sound with great warmth.",
    "min":        "The minor arpeggio is essential on guitar. Its CAGED minor-position boxes cover the entire neck. Indispensable in rock, jazz, soul, and blues on degrees II, III, and VI, it also forms the basis of extended pentatonic soloing.",
    "min7":       "The minor 7th arpeggio is the most versatile in jazz and funk guitar. It appears on degrees II, III, and VI of the major scale and forms the basis of ii-V-I progressions. Its compact shapes allow smooth runs and expressive melodic lines.",
    "min9":       "The minor 9th arpeggio enriches the min7 with the ninth, adding freshness to the dark minor color. Widely used in contemporary jazz, soul, and R&B. On guitar, voicings without the fifth (root, third, seventh, ninth) are very effective.",
    "min11":      "The minor 11th arpeggio is the signature of modal jazz and neo-soul. Its perfect fourth over the min9 creates an enveloping texture. Quartal voicings — stacked fourths — popular in jazz fusion, ideally capture this modal color on guitar.",
    "min13":      "The minor 13th arpeggio encapsulates the entire Dorian mode in one arpeggio. On guitar, it provides an immense melodic vocabulary for solos in a minor modal context. Widely used by jazz-fusion guitarists for sophisticated lines.",
    "min6":       "The minor 6th arpeggio pairs the minor third with the major sixth, creating a bittersweet, expressive color. Widely used in jazz and bossa nova. On guitar, its voicings close to the half-diminished shape facilitate position memorization.",
    "minmaj7":    "The minor maj7 arpeggio combines minor third and major seventh, creating a very particular internal tension. Popularized by Hitchcock film scores, it fits into the chromatic descent mM7–m7–m6. Its mysterious sound is very effective in dramatic guitar solos.",
    "p5":         "The Power 5 arpeggio (root + fifth) is harmonically neutral, neither major nor minor. On electric guitar with distortion, it is the backbone of rock and metal. Easy to memorize (two notes a fifth apart), it allows fast runs across the entire neck.",
    "sus2":       "The sus2 arpeggio avoids the third for an open color with no major/minor ambiguity. Very popular in acoustic rock and pop, the Dsus2 and Asus2 open shapes are classics. On electric, it creates very contemporary airy textures.",
    "sus4":       "The sus4 arpeggio replaces the third with the fourth, creating tension that seeks resolution. On guitar, the sus4 → major progression is a classic ornament. The open Dsus4 and Asus4 shapes are among the most expressive in the acoustic repertoire.",
    "dom7sus4":   "The 7sus4 arpeggio combines the fourth suspension with the dominant minor seventh, creating an open jazz-fusion texture. Herbie Hancock made it a pillar of his language. On guitar, voicings without the fifth are very effective in higher positions.",
    "aug":        "The augmented arpeggio replaces the fifth with an augmented fifth, creating a symmetric, mysterious color. Its unique geometry — one shape covers 3 tonics — simplifies learning. Very expressive for chromatic transitions and tension effects in jazz and film music.",
    "aug7":       "The augmented 7th arpeggio combines augmented fifth and minor seventh. Derived from the whole-tone scale, it often precedes resolution to a minor chord. On guitar, its symmetry makes it easy to shift and very effective in advanced jazz solos.",
    "dim":        "The diminished arpeggio stacks three minor thirds. Its perfect symmetry — one shape covers 3 different tonics — makes it a compact tool across the entire neck. On guitar, it is widely used in sweep picking for dramatic chromatic lines.",
    "halfdim":    "The half-diminished arpeggio (ø) is central in ii–V–I progressions in minor jazz. Its diminished fifth and minor seventh create tension that calls for resolution. On guitar, its compact voicings overlap with m6 shapes, facilitating position memorization.",
    "dim7":       "The diminished 7th arpeggio divides the octave into 4 equal parts. Its perfect symmetry makes it very practical on guitar — 3 shapes cover all 12 keys. Ideal for chromatic sweep picking and dramatic passages in jazz, rock, and classical.",
    "dom7b5":     "The 7♭5 arpeggio combines major third, diminished fifth, and minor seventh. Its flatted fifth creates a second tritone, intensifying dominant tension. Interchangeable with the V7 a tritone away, it is a key jazz reharmonization tool for the guitarist.",
}

# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------
def arp_notes(root_pc, iv, lang='fr'):
    names = NOTE_NAMES_FR if lang == 'fr' else NOTE_NAMES_EN
    return [names[(root_pc + i) % 12] for i in iv]

def arp_notes_with_roles(root_pc, iv, lang='fr'):
    names = NOTE_NAMES_FR if lang == 'fr' else NOTE_NAMES_EN
    return [{"name": names[(root_pc + i) % 12], "role": ARP_IV_LABEL.get(i, str(i))} for i in iv]

def related_in_group(arp_id, group_id, limit=5):
    for g in ARPEGE_GROUPS:
        if g["id"] == group_id:
            others = [a for a in g["arps"] if a["id"] != arp_id]
            return [{"id": a["id"], "slug": a["id"], "sym": a["sym"], "label_fr": a["label_fr"], "label_en": a["label_en"]} for a in others[:limit]]
    return []

# ---------------------------------------------------------------------------
# GÉNÉRATION PAGES
# ---------------------------------------------------------------------------
def gen_pages(tpl, inst, lang_code, out_root, base_url_path, app_url,
              desc_dict, pages_list, accent, btn_color, brand,
              ui_strings, nav_lnks):
    for group in ARPEGE_GROUPS:
        for arp in group["arps"]:
            slug = arp["id"]

            # Pages canoniques (12 toniques)
            for root in ROOTS:
                _gen_one(tpl, inst, lang_code, out_root, base_url_path, app_url,
                         desc_dict, pages_list, accent, btn_color, brand,
                         ui_strings, nav_lnks, group, arp, slug, root,
                         is_enharmonic=False)

            # Pages enharmoniques (5 toniques supplémentaires)
            for eroot in ENHARMONIC_ROOTS:
                _gen_one(tpl, inst, lang_code, out_root, base_url_path, app_url,
                         desc_dict, pages_list, accent, btn_color, brand,
                         ui_strings, nav_lnks, group, arp, slug, eroot,
                         is_enharmonic=True)


def _gen_one(tpl, inst, lang_code, out_root, base_url_path, app_url,
             desc_dict, pages_list, accent, btn_color, brand,
             ui_strings, nav_lnks, group, arp, slug, root, is_enharmonic):
    if lang_code == 'fr':
        root_slug_key = "slug"
        root_name_key = "fr"
    else:
        root_slug_key = "slug_en"
        root_name_key = "name"

    root_slug = root.get(root_slug_key, root["slug"])
    page_url  = f"{BASE_URL}/{base_url_path}/{root_slug}/{slug}/"
    alt_fr    = f"{BASE_URL}/{base_url_path.replace('en/', 'fr/').replace('arpeggios', 'arpeges')}/{root.get('slug', root.get('slug', ''))}/" + slug + "/"

    if is_enharmonic:
        if lang_code == 'fr':
            can_slug = root.get("canonical_slug", root_slug)
        else:
            can_slug = root.get("canonical_slug_en", root_slug)
        canonical_url = f"{BASE_URL}/{base_url_path}/{can_slug}/{slug}/"
    else:
        canonical_url = page_url

    # Alt URLs (for hreflang)
    # We need both FR and EN alternate
    fr_base = base_url_path.replace("en/", "fr/").replace("arpeggios-bass", "arpeges-basse").replace("arpeggios-guitar", "arpeges-guitare")
    en_base = base_url_path.replace("fr/", "en/").replace("arpeges-basse", "arpeggios-bass").replace("arpeges-guitare", "arpeggios-guitar")
    root_slug_fr = root.get("slug", "")
    root_slug_en = root.get("slug_en", "")
    alt_url_fr = f"{BASE_URL}/{fr_base}/{root_slug_fr}/{slug}/"
    alt_url_en = f"{BASE_URL}/{en_base}/{root_slug_en}/{slug}/"

    n_notes       = len(arp["iv"])
    arp_label     = arp["label_fr"] if lang_code == 'fr' else arp["label_en"]
    group_label   = group["label_fr"] if lang_code == 'fr' else group["label_en"]
    root_name     = root.get(root_name_key, root.get("name", ""))
    root_fr_name  = root.get("fr", root.get("name", ""))
    root_en_name  = root.get("name", "")

    notes_primary   = arp_notes(root["pc"], arp["iv"], lang_code)
    notes_secondary = arp_notes(root["pc"], arp["iv"], 'en' if lang_code == 'fr' else 'fr')
    notes_wr        = arp_notes_with_roles(root["pc"], arp["iv"], lang_code)
    notes_str       = " – ".join(notes_primary)

    desc = desc_dict.get(arp["id"], "")

    if lang_code == 'fr':
        arp_name_full = f"{root_fr_name} {arp_label}"
    else:
        arp_name_full = f"{root_en_name} {arp_label}"

    nav_roots = [{"name": r["fr"] if lang_code == 'fr' else r["name"],
                  "slug": r["slug"] if lang_code == 'fr' else r["slug_en"]} for r in ROOTS]

    related = related_in_group(arp["id"], group["id"])

    ui = ui_strings
    ctx = {
        "lang": lang_code,
        "root": root,
        "arp": arp,
        "arp_slug": slug,
        "arp_label": arp_label,
        "group_label": group_label,
        "n_notes": n_notes,
        "notes_primary": notes_primary,
        "notes_secondary": notes_secondary,
        "notes_secondary_label": ui["notes_secondary_label"],
        "notes_with_roles": notes_wr,
        "notes_str": notes_str,
        "desc": desc,
        "related_arps": related,
        "app_link": app_url,
        "page_url": page_url,
        "canonical_url": canonical_url,
        "alt_url_fr": alt_url_fr,
        "alt_url_en": alt_url_en,
        "BASE_URL": BASE_URL,
        "nav_roots": nav_roots,
        "nav_base": f"{BASE_URL}/{base_url_path}",
        "nav_links": nav_lnks,
        "accent": accent,
        "btn_text_color": btn_color,
        "ui_brand": brand,
        "ui_title": f"{ui['title_tmpl'].format(name=arp_name_full, notes=notes_str)}",
        "ui_meta_desc": f"{ui['meta_tmpl'].format(name=arp_name_full, notes=notes_str, n=n_notes)}",
        "ui_h1": f"{ui['h1_tmpl'].format(name=arp_name_full)}",
        "ui_symbol": ui["symbol"],
        "ui_notes": ui["notes"],
        "ui_intervals": ui["intervals"],
        "ui_about": ui["about"],
        "ui_cta_text": f"{ui['cta_text'].format(name=f'<strong>{arp_name_full}</strong>')}",
        "ui_cta_btn": ui["cta_btn"],
        "ui_other_keys": ui["other_keys"],
        "ui_all_arps": ui["all_arps"],
        "ui_related": f"{ui['related'].format(group=group_label)}",
        "ui_og_title": f"{arp_name_full} — {brand}",
        "ui_og_desc": f"{arp_name_full} : {notes_str}",
        "ui_schema_head": f"{arp_name_full}",
        "ui_schema_desc": f"{arp_name_full} : {notes_str}.",
    }

    out_dir = out_root / root_slug / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "index.html").write_text(tpl.render(**ctx), encoding="utf-8")
    pages_list.append(page_url)


# ---------------------------------------------------------------------------
# HUB
# ---------------------------------------------------------------------------
def gen_hub(out_root, lang_code, pages_list, base_url_path, app_url, accent,
            brand, h1, sub, desc_meta, nav_lnks):
    out_root.mkdir(parents=True, exist_ok=True)
    hub_url  = f"{BASE_URL}/{base_url_path}/"
    hub_base = f"{BASE_URL}/{base_url_path}"

    rows = []
    for group in ARPEGE_GROUPS:
        gl = group["label_fr"] if lang_code == 'fr' else group["label_en"]
        links = []
        for arp in group["arps"]:
            first_r = ROOTS[0]["slug"] if lang_code == 'fr' else ROOTS[0]["slug_en"]
            lbl = arp["label_fr"] if lang_code == 'fr' else arp["label_en"]
            sym_html = f' <small style="opacity:.6">{arp["sym"]}</small>' if arp["sym"] else ""
            links.append(f'<a href="{hub_base}/{first_r}/{arp["id"]}/">{lbl}{sym_html}</a>')
        rows.append(f'<div class="hub-group"><h2>{gl}</h2><div class="arp-links">{"".join(links)}</div></div>')

    note_links = []
    for r in ROOTS:
        n_slug = r["slug"] if lang_code == 'fr' else r["slug_en"]
        n_name = r["fr"] if lang_code == 'fr' else r["name"]
        first_a = ARPEGE_GROUPS[0]["arps"][0]["id"]
        note_links.append(f'<a href="{hub_base}/{n_slug}/{first_a}/">{n_name}</a>')

    nav_html = "\n".join(f'  <a href="{lnk["url"]}">{lnk["label"]}</a>' for lnk in nav_lnks)
    title_attr = "Tous les arpèges" if lang_code == 'fr' else "All arpeggios"
    launch_btn = "Lancer ScalaBass →" if lang_code == 'fr' else "Launch ScalaBass →"
    keys_head  = "Choisir une tonique" if lang_code == 'fr' else "Choose a key"

    html = f"""<!DOCTYPE html>
<html lang="{lang_code}">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>{h1} — Diagrammes et positions | {brand}</title>
  <meta name="description" content="{desc_meta}">
  <link rel="canonical" href="{hub_url}">
  <style>
    :root{{--bg:#1a1a20;--panel:#23232b;--line:#333340;--text:#e8e8f0;--muted:#8888a0;--accent:{accent}}}
    *{{box-sizing:border-box;margin:0;padding:0}}
    body{{background:var(--bg);color:var(--text);font-family:"Segoe UI",system-ui,sans-serif;font-size:15px;line-height:1.6}}
    a{{color:var(--accent);text-decoration:none}} a:hover{{text-decoration:underline}}
    .topnav{{background:var(--panel);border-bottom:1px solid var(--line);padding:10px 20px;display:flex;align-items:center;gap:16px;flex-wrap:wrap}}
    .topnav .logo{{font-weight:700;letter-spacing:.15em;font-size:13px;text-transform:uppercase;color:var(--accent)}}
    .topnav a{{color:var(--muted);font-size:13px}}
    main{{max-width:900px;margin:0 auto;padding:28px 24px 64px}}
    h1{{font-size:clamp(22px,4vw,34px);font-weight:700;margin-bottom:6px}}
    .sub{{color:var(--muted);margin-bottom:28px;font-size:14px}}
    h2{{font-size:14px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);margin:24px 0 10px;border-bottom:1px solid var(--line);padding-bottom:6px}}
    .hub-group{{margin-bottom:28px}}
    .arp-links{{display:flex;flex-wrap:wrap;gap:6px}}
    .arp-links a{{background:var(--panel);border:1px solid var(--line);border-radius:6px;padding:5px 12px;font-size:13px;color:var(--muted)}}
    .arp-links a:hover{{color:var(--text);text-decoration:none}}
    .note-links{{display:flex;flex-wrap:wrap;gap:6px;margin:16px 0 28px}}
    .note-links a{{background:var(--panel);border:1px solid rgba(200,100,30,.3);border-radius:6px;padding:5px 14px;font-size:13px;color:var(--accent);font-weight:700}}
    .cta{{margin-top:40px;padding:20px 24px;background:var(--panel);border:1px solid var(--line);border-radius:10px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px}}
    .cta-btn{{background:var(--accent);color:#fff;font-weight:700;padding:10px 20px;border-radius:8px;font-size:14px}}
    .cta-btn:hover{{text-decoration:none;opacity:.9}}
  </style>
</head>
<body>
<nav class="topnav">
  <span class="logo">{brand}</span>
{nav_html}
</nav>
<main>
  <h1>{h1}</h1>
  <p class="sub">{sub}</p>
  <h2>{keys_head}</h2>
  <div class="note-links">{"".join(note_links)}</div>
  {"".join(rows)}
  <div class="cta">
    <p style="color:var(--muted);font-size:14px">{desc_meta}</p>
    <a class="cta-btn" href="{app_url}">{launch_btn}</a>
  </div>
</main>
</body>
</html>"""

    (out_root / "index.html").write_text(html, encoding="utf-8")
    pages_list.append(hub_url)


# ---------------------------------------------------------------------------
# SITEMAP
# ---------------------------------------------------------------------------
def update_sitemap(pages_bass_fr, pages_bass_en, pages_guit_fr, pages_guit_en):
    sitemap_path = REPO_ROOT / "sitemap.xml"
    existing = []
    if sitemap_path.exists():
        content = sitemap_path.read_text(encoding="utf-8")
        existing = re.findall(r'<loc>(.*?)</loc>', content)
    kept = [u for u in existing
            if "/fr/arpeges-basse/" not in u
            and "/en/arpeggios-bass/" not in u
            and "/fr/arpeges-guitare/" not in u
            and "/en/arpeggios-guitar/" not in u]
    all_urls = kept + pages_bass_fr + pages_bass_en + pages_guit_fr + pages_guit_en
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for url in all_urls:
        lines.append(f'  <url><loc>{url}</loc></url>')
    lines.append('</urlset>')
    sitemap_path.write_text('\n'.join(lines) + '\n', encoding="utf-8")


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
def main():
    env = Environment(loader=FileSystemLoader(str(TMPL_DIR)), autoescape=True)
    tpl = env.get_template("arpege.html.jinja2")

    # ---- BASSE ----
    out_bass_fr = REPO_ROOT / "fr" / "arpeges-basse"
    out_bass_en = REPO_ROOT / "en" / "arpeggios-bass"
    app_bass    = f"{BASE_URL}/arpeges-basse.html"
    accent_bass = "#d9a849"
    btn_bass    = "#160f08"
    brand_bass  = "ScalaBass"
    nav_bass_fr = [
        {"url": f"{BASE_URL}/index.html",        "label": "Manche"},
        {"url": f"{BASE_URL}/gammes.html",        "label": "Gammes"},
        {"url": f"{BASE_URL}/arpeges-basse.html", "label": "Arpèges"},
        {"url": f"{BASE_URL}/intervalles.html",   "label": "Intervalles"},
        {"url": f"{BASE_URL}/cadences.html",      "label": "Cadences"},
        {"url": f"{BASE_URL}/analyse.html",       "label": "Analyse"},
        {"url": f"{BASE_URL}/quintes.html",       "label": "Tonalités"},
    ]
    nav_bass_en = [
        {"url": f"{BASE_URL}/index.html",        "label": "Fretboard"},
        {"url": f"{BASE_URL}/gammes.html",        "label": "Scales"},
        {"url": f"{BASE_URL}/arpeges-basse.html", "label": "Arpeggios"},
        {"url": f"{BASE_URL}/intervalles.html",   "label": "Intervals"},
        {"url": f"{BASE_URL}/cadences.html",      "label": "Cadences"},
        {"url": f"{BASE_URL}/analyse.html",       "label": "Analyse"},
        {"url": f"{BASE_URL}/quintes.html",       "label": "Keys"},
    ]

    ui_bass_fr = {
        "notes_secondary_label": "Notation anglaise",
        "title_tmpl":  "Arpège {name} basse — {notes} | ScalaBass",
        "meta_tmpl":   "Arpège {name} à la basse électrique : {notes}. {n} notes. Positions, intervalles, appli interactive.",
        "h1_tmpl":     "Arpège {name} à la basse",
        "symbol":      "Symbole",
        "notes":       "Notes de l'arpège",
        "intervals":   "Structure de l'arpège",
        "about":       "À propos de cet arpège",
        "cta_text":    "Voir toutes les positions sur le manche pour {name} dans l'appli interactive ScalaBass.",
        "cta_btn":     "Explorer dans ScalaBass →",
        "other_keys":  "Même arpège dans d'autres toniques",
        "all_arps":    "Tous les arpèges basse",
        "related":     "Autres arpèges {group}",
    }
    ui_bass_en = {
        "notes_secondary_label": "Solfège",
        "title_tmpl":  "{name} Bass Arpeggio — {notes} | ScalaBass",
        "meta_tmpl":   "{name} bass arpeggio: {notes}. {n} notes. Positions, intervals, interactive app.",
        "h1_tmpl":     "{name} Bass Arpeggio",
        "symbol":      "Symbol",
        "notes":       "Arpeggio Notes",
        "intervals":   "Arpeggio Structure",
        "about":       "About this arpeggio",
        "cta_text":    "See all fretboard positions for {name} in the interactive ScalaBass app.",
        "cta_btn":     "Explore in ScalaBass →",
        "other_keys":  "Same arpeggio in other keys",
        "all_arps":    "All bass arpeggios",
        "related":     "Other {group} arpeggios",
    }

    pages_bass_fr = []
    pages_bass_en = []
    print("Basse FR -> " + str(out_bass_fr))
    gen_pages(tpl, 'bass', 'fr', out_bass_fr, "fr/arpeges-basse", app_bass,
              DESC_BASS_FR, pages_bass_fr, accent_bass, btn_bass, brand_bass,
              ui_bass_fr, nav_bass_fr)
    print("Basse EN -> " + str(out_bass_en))
    gen_pages(tpl, 'bass', 'en', out_bass_en, "en/arpeggios-bass", app_bass,
              DESC_BASS_EN, pages_bass_en, accent_bass, btn_bass, brand_bass,
              ui_bass_en, nav_bass_en)

    print("Hubs basse …")
    gen_hub(out_bass_fr, 'fr', pages_bass_fr, "fr/arpeges-basse", app_bass, accent_bass,
            brand_bass,
            "Arpèges de basse", "27 types d'arpèges × 12 toniques — positions, intervalles, appli interactive",
            "Arpèges de basse électrique : majeur, mineur, 7, maj7, dominante, diminué, augmenté et extensions. Positions sur le manche, intervalles, appli interactive.",
            nav_bass_fr)
    gen_hub(out_bass_en, 'en', pages_bass_en, "en/arpeggios-bass", app_bass, accent_bass,
            brand_bass,
            "Bass Arpeggios", "27 arpeggio types × 12 keys — positions, intervals, interactive app",
            "Electric bass arpeggios: major, minor, 7th, maj7, dominant, diminished, augmented and extensions. Fretboard positions, intervals, interactive app.",
            nav_bass_en)

    # ---- GUITARE ----
    out_guit_fr = REPO_ROOT / "fr" / "arpeges-guitare"
    out_guit_en = REPO_ROOT / "en" / "arpeggios-guitar"
    app_guit    = f"{BASE_URL}/arpeges-guitare.html"
    accent_guit = "#bf1828"
    btn_guit    = "#fff"
    brand_guit  = "ScalaSix"
    nav_guit_fr = [
        {"url": f"{BASE_URL}/manche-guitare.html",      "label": "Manche"},
        {"url": f"{BASE_URL}/gammes-guitare.html",       "label": "Gammes"},
        {"url": f"{BASE_URL}/arpeges-guitare.html",      "label": "Arpèges"},
        {"url": f"{BASE_URL}/accords-guitare.html",      "label": "Accords"},
        {"url": f"{BASE_URL}/intervalles-guitare.html",  "label": "Intervalles"},
    ]
    nav_guit_en = [
        {"url": f"{BASE_URL}/manche-guitare.html",      "label": "Fretboard"},
        {"url": f"{BASE_URL}/gammes-guitare.html",       "label": "Scales"},
        {"url": f"{BASE_URL}/arpeges-guitare.html",      "label": "Arpeggios"},
        {"url": f"{BASE_URL}/accords-guitare.html",      "label": "Chords"},
        {"url": f"{BASE_URL}/intervalles-guitare.html",  "label": "Intervals"},
    ]

    ui_guit_fr = {
        "notes_secondary_label": "Notation anglaise",
        "title_tmpl":  "Arpège {name} guitare — {notes} | ScalaSix",
        "meta_tmpl":   "Arpège {name} à la guitare 6 cordes : {notes}. {n} notes. Positions, sweep picking, appli interactive.",
        "h1_tmpl":     "Arpège {name} à la guitare",
        "symbol":      "Symbole",
        "notes":       "Notes de l'arpège",
        "intervals":   "Structure de l'arpège",
        "about":       "À propos de cet arpège",
        "cta_text":    "Voir toutes les positions sur le manche pour {name} dans l'appli interactive ScalaSix.",
        "cta_btn":     "Explorer dans ScalaSix →",
        "other_keys":  "Même arpège dans d'autres toniques",
        "all_arps":    "Tous les arpèges guitare",
        "related":     "Autres arpèges {group}",
    }
    ui_guit_en = {
        "notes_secondary_label": "Solfège",
        "title_tmpl":  "{name} Guitar Arpeggio — {notes} | ScalaSix",
        "meta_tmpl":   "{name} guitar arpeggio: {notes}. {n} notes. Positions, sweep picking, interactive app.",
        "h1_tmpl":     "{name} Guitar Arpeggio",
        "symbol":      "Symbol",
        "notes":       "Arpeggio Notes",
        "intervals":   "Arpeggio Structure",
        "about":       "About this arpeggio",
        "cta_text":    "See all fretboard positions for {name} in the interactive ScalaSix app.",
        "cta_btn":     "Explore in ScalaSix →",
        "other_keys":  "Same arpeggio in other keys",
        "all_arps":    "All guitar arpeggios",
        "related":     "Other {group} arpeggios",
    }

    pages_guit_fr = []
    pages_guit_en = []
    print("Guitare FR -> " + str(out_guit_fr))
    gen_pages(tpl, 'guitar', 'fr', out_guit_fr, "fr/arpeges-guitare", app_guit,
              DESC_GUIT_FR, pages_guit_fr, accent_guit, btn_guit, brand_guit,
              ui_guit_fr, nav_guit_fr)
    print("Guitare EN -> " + str(out_guit_en))
    gen_pages(tpl, 'guitar', 'en', out_guit_en, "en/arpeggios-guitar", app_guit,
              DESC_GUIT_EN, pages_guit_en, accent_guit, btn_guit, brand_guit,
              ui_guit_en, nav_guit_en)

    print("Hubs guitare …")
    gen_hub(out_guit_fr, 'fr', pages_guit_fr, "fr/arpeges-guitare", app_guit, accent_guit,
            brand_guit,
            "Arpèges de guitare", "27 types d'arpèges × 12 toniques — positions, sweep picking, appli interactive",
            "Arpèges guitare 6 cordes : majeur, mineur, 7, maj7, dominante, diminué, augmenté et extensions. Positions CAGED, sweep picking, appli interactive.",
            nav_guit_fr)
    gen_hub(out_guit_en, 'en', pages_guit_en, "en/arpeggios-guitar", app_guit, accent_guit,
            brand_guit,
            "Guitar Arpeggios", "27 arpeggio types × 12 keys — CAGED positions, sweep picking, interactive app",
            "Guitar arpeggios: major, minor, 7th, maj7, dominant, diminished, augmented and extensions. CAGED positions, sweep picking, interactive app.",
            nav_guit_en)

    # ---- SITEMAP ----
    update_sitemap(pages_bass_fr, pages_bass_en, pages_guit_fr, pages_guit_en)

    total = len(pages_bass_fr) + len(pages_bass_en) + len(pages_guit_fr) + len(pages_guit_en)
    print(f"\nBasse  FR: {len(pages_bass_fr)} | EN: {len(pages_bass_en)}")
    print(f"Guitare FR: {len(pages_guit_fr)} | EN: {len(pages_guit_en)}")
    print(f"Total : {total} pages")
    print("sitemap.xml mis à jour")
    print("Done.")


if __name__ == "__main__":
    main()
