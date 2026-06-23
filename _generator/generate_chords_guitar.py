#!/usr/bin/env python3
"""
ScalaBass — Générateur de pages statiques SEO — Accords Guitare
===============================================================
Génère fr/accords-guitare/{note}/{accord}/index.html  (49 accords × 17 toniques = ~833 pages FR)
Génère en/chords-guitar/{note}/{accord}/index.html   (49 accords × 17 toniques = ~833 pages EN)
Génère fr/accords-guitare/index.html (hub FR)
Génère en/chords-guitar/index.html  (hub EN)
Met à jour sitemap.xml (sans toucher aux autres pages)

Lancer depuis la racine du repo :
    pip install -r _generator/requirements.txt
    python _generator/generate_chords_guitar.py
"""

import re, sys
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

sys.path.insert(0, str(Path(__file__).parent))
from generate import ROOTS, ENHARMONIC_ROOTS

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
REPO_ROOT   = Path(__file__).parent.parent
OUT_FR      = REPO_ROOT / "fr" / "accords-guitare"
OUT_EN      = REPO_ROOT / "en" / "chords-guitar"
TMPL_DIR    = Path(__file__).parent / "templates"
BASE_URL    = "https://labussiere21.github.io/Gammes"
APP_URL     = f"{BASE_URL}/accords-guitare.html"

# ---------------------------------------------------------------------------
# DONNÉES ACCORDS (tirées de accords-guitare.html, sans les renversements)
# ---------------------------------------------------------------------------
CHORD_GROUPS = [
    {"id": "triades", "label_fr": "Triades", "label_en": "Triads", "chords": [
        {"id":"maj",     "sym":"",      "label_fr":"Majeur",            "label_en":"Major",             "iv":[0,4,7]},
        {"id":"min",     "sym":"m",     "label_fr":"Mineur",            "label_en":"Minor",             "iv":[0,3,7]},
        {"id":"aug",     "sym":"+",     "label_fr":"Augmenté",          "label_en":"Augmented",         "iv":[0,4,8]},
        {"id":"dim",     "sym":"°",     "label_fr":"Diminué",           "label_en":"Diminished",        "iv":[0,3,6]},
        {"id":"sus2",    "sym":"sus2",  "label_fr":"Sus2",              "label_en":"Sus2",              "iv":[0,2,7]},
        {"id":"sus4",    "sym":"sus4",  "label_fr":"Sus4",              "label_en":"Sus4",              "iv":[0,5,7]},
        {"id":"p5",      "sym":"5",     "label_fr":"Power 5",           "label_en":"Power 5",           "iv":[0,7]},
    ]},
    {"id": "sixtes", "label_fr": "Sixtes & add", "label_en": "Sixths & add", "chords": [
        {"id":"add9",    "sym":"add9",  "label_fr":"Add9",              "label_en":"Add9",              "iv":[0,2,4,7]},
        {"id":"madd9",   "sym":"madd9", "label_fr":"Mineur add9",       "label_en":"Minor add9",        "iv":[0,2,3,7]},
        {"id":"6",       "sym":"6",     "label_fr":"Majeur 6",          "label_en":"Major 6th",         "iv":[0,4,7,9]},
        {"id":"m6",      "sym":"m6",    "label_fr":"Mineur 6",          "label_en":"Minor 6th",         "iv":[0,3,7,9]},
        {"id":"69",      "sym":"6/9",   "label_fr":"Six-neuf",          "label_en":"Six-nine",          "iv":[0,2,4,7,9]},
        {"id":"m69",     "sym":"m6/9",  "label_fr":"Mineur 6/9",        "label_en":"Minor 6/9",         "iv":[0,2,3,7,9]},
    ]},
    {"id": "sept", "label_fr": "7èmes", "label_en": "7ths", "chords": [
        {"id":"maj7",    "sym":"Δ7",    "label_fr":"Majeur 7",          "label_en":"Major 7th",         "iv":[0,4,7,11]},
        {"id":"m7",      "sym":"m7",    "label_fr":"Mineur 7",          "label_en":"Minor 7th",         "iv":[0,3,7,10]},
        {"id":"7",       "sym":"7",     "label_fr":"Dominante 7",       "label_en":"Dominant 7th",      "iv":[0,4,7,10]},
        {"id":"m7b5",    "sym":"ø7",    "label_fr":"Demi-diminué ø7",   "label_en":"Half-diminished",   "iv":[0,3,6,10]},
        {"id":"dim7",    "sym":"°7",    "label_fr":"Diminué 7",         "label_en":"Diminished 7th",    "iv":[0,3,6,9]},
        {"id":"mmaj7",   "sym":"mΔ7",   "label_fr":"Mineur Maj7",       "label_en":"Minor Major 7th",   "iv":[0,3,7,11]},
        {"id":"augmaj7", "sym":"+Δ7",   "label_fr":"Augmenté Maj7",     "label_en":"Augmented Maj7",    "iv":[0,4,8,11]},
        {"id":"aug7",    "sym":"7+",    "label_fr":"Augmenté 7",        "label_en":"Augmented 7th",     "iv":[0,4,8,10]},
        {"id":"7sus4",   "sym":"7sus4", "label_fr":"7 Sus4",            "label_en":"7 Sus4",            "iv":[0,5,7,10]},
        {"id":"7sus2",   "sym":"7sus2", "label_fr":"7 Sus2",            "label_en":"7 Sus2",            "iv":[0,2,7,10]},
        {"id":"7b5",     "sym":"7♭5",   "label_fr":"7 bémol 5",         "label_en":"7 flat 5",          "iv":[0,4,6,10]},
        {"id":"m7s5",    "sym":"m7♯5",  "label_fr":"Mineur 7 dièse 5",  "label_en":"Minor 7 sharp 5",   "iv":[0,3,8,10]},
    ]},
    {"id": "neuf", "label_fr": "9èmes", "label_en": "9ths", "chords": [
        {"id":"maj9",    "sym":"Δ9",    "label_fr":"Majeur 9",          "label_en":"Major 9th",         "iv":[0,4,7,11,2]},
        {"id":"m9",      "sym":"m9",    "label_fr":"Mineur 9",          "label_en":"Minor 9th",         "iv":[0,3,7,10,2]},
        {"id":"9",       "sym":"9",     "label_fr":"Dominante 9",       "label_en":"Dominant 9th",      "iv":[0,4,7,10,2]},
        {"id":"7b9",     "sym":"7♭9",   "label_fr":"7 bémol 9",         "label_en":"7 flat 9",          "iv":[0,4,7,10,1]},
        {"id":"7s9",     "sym":"7♯9",   "label_fr":"7 dièse 9",         "label_en":"7 sharp 9",         "iv":[0,4,7,10,3]},
        {"id":"m9maj7",  "sym":"m9Δ7",  "label_fr":"Mineur 9 Maj7",     "label_en":"Minor 9 Maj7",      "iv":[0,3,7,11,2]},
        {"id":"9s11",    "sym":"9♯11",  "label_fr":"9 dièse 11",        "label_en":"9 sharp 11",        "iv":[0,4,7,10,2,6]},
        {"id":"maj9s11", "sym":"Δ9♯11", "label_fr":"Majeur 9 dièse 11", "label_en":"Major 9 sharp 11",  "iv":[0,4,7,11,2,6]},
    ]},
    {"id": "onze", "label_fr": "11èmes", "label_en": "11ths", "chords": [
        {"id":"11",      "sym":"11",    "label_fr":"Dominante 11",      "label_en":"Dominant 11th",     "iv":[0,7,10,2,5]},
        {"id":"m11",     "sym":"m11",   "label_fr":"Mineur 11",         "label_en":"Minor 11th",        "iv":[0,3,7,10,2,5]},
        {"id":"maj11",   "sym":"Δ11",   "label_fr":"Majeur 11",         "label_en":"Major 11th",        "iv":[0,4,7,11,2,5]},
        {"id":"7s11",    "sym":"7♯11",  "label_fr":"7 dièse 11 Lydien", "label_en":"7 sharp 11",        "iv":[0,4,7,10,6]},
        {"id":"maj7s11", "sym":"Δ7♯11", "label_fr":"Maj7 dièse 11",     "label_en":"Maj7 sharp 11",     "iv":[0,4,7,11,6]},
    ]},
    {"id": "treize", "label_fr": "13èmes", "label_en": "13ths", "chords": [
        {"id":"13",      "sym":"13",    "label_fr":"Dominante 13",      "label_en":"Dominant 13th",     "iv":[0,4,7,10,2,9]},
        {"id":"m13",     "sym":"m13",   "label_fr":"Mineur 13",         "label_en":"Minor 13th",        "iv":[0,3,7,10,2,9]},
        {"id":"maj13",   "sym":"Δ13",   "label_fr":"Majeur 13",         "label_en":"Major 13th",        "iv":[0,4,7,11,2,9]},
        {"id":"13s11",   "sym":"13♯11", "label_fr":"13 dièse 11",       "label_en":"13 sharp 11",       "iv":[0,4,7,10,6,9]},
        {"id":"13b9",    "sym":"13♭9",  "label_fr":"13 bémol 9",        "label_en":"13 flat 9",         "iv":[0,4,7,10,1,9]},
    ]},
    {"id": "alt", "label_fr": "Altérés", "label_en": "Altered", "chords": [
        {"id":"7alt",    "sym":"7alt",  "label_fr":"7 altéré",          "label_en":"Altered 7th",       "iv":[0,4,8,10,1]},
        {"id":"7b9b5",   "sym":"7♭9♭5", "label_fr":"7 bémol 9 bémol 5", "label_en":"7 flat 9 flat 5",  "iv":[0,4,6,10,1]},
        {"id":"7s9b5",   "sym":"7♯9♭5", "label_fr":"7 dièse 9 bémol 5", "label_en":"7 sharp 9 flat 5", "iv":[0,4,6,10,3]},
        {"id":"7b9s5",   "sym":"7♭9♯5", "label_fr":"7 bémol 9 dièse 5", "label_en":"7 flat 9 sharp 5", "iv":[0,4,8,10,1]},
        {"id":"7s9s5",   "sym":"7♯9♯5", "label_fr":"7 dièse 9 dièse 5", "label_en":"7 sharp 9 sharp 5","iv":[0,4,8,10,3]},
        {"id":"13b5",    "sym":"13♭5",  "label_fr":"13 bémol 5",        "label_en":"13 flat 5",         "iv":[0,4,6,10,9]},
    ]},
]

# Liste plate de tous les accords (pour liens annexes)
ALL_CHORDS = [c for g in CHORD_GROUPS for c in g["chords"]]
GROUP_BY_CHORD = {c["id"]: g for g in CHORD_GROUPS for c in g["chords"]}

# ---------------------------------------------------------------------------
# NOMS DE NOTES
# ---------------------------------------------------------------------------
NOTE_NAMES_FR = ['Do','Réb','Ré','Mib','Mi','Fa','Solb','Sol','Lab','La','Sib','Si']
NOTE_NAMES_EN = ['C','Db','D','Eb','E','F','Gb','G','Ab','A','Bb','B']
IV_LABEL = {0:'R',1:'♭9',2:'9',3:'♭3',4:'3',5:'11',6:'♯11',7:'5',8:'♯5',9:'13',10:'♭7',11:'7'}

def chord_notes(root_pc, iv, lang='fr'):
    names = NOTE_NAMES_FR if lang == 'fr' else NOTE_NAMES_EN
    return [names[(root_pc + i) % 12] for i in iv]

def chord_notes_with_roles(root_pc, iv, lang='fr'):
    names = NOTE_NAMES_FR if lang == 'fr' else NOTE_NAMES_EN
    return [{"name": names[(root_pc + i) % 12], "role": IV_LABEL.get(i, str(i))} for i in iv]

def chord_slug(chord_id):
    return chord_id.replace('_', '-')

# ---------------------------------------------------------------------------
# DESCRIPTIONS FR
# ---------------------------------------------------------------------------
CHORD_DESC_FR = {
    # Triades
    "maj": "L'accord majeur est le pilier de la guitare. Ses formes ouvertes E, A, G, C et D sont les premiers accords appris par tout guitariste, et le système CAGED permet de les transposer sur tout le manche. Lumineux et stable, il est présent dans tous les styles de la pop au jazz en passant par le rock et la folk.",
    "min": "L'accord mineur apporte une couleur mélancolique indispensable à la guitare. Les formes Em et Am en position ouverte sonnent remarquablement bien avec les cordes à vide, et la forme barre (E ou A) permet de jouer n'importe quel accord mineur sur tout le manche. C'est un des accords fondamentaux du rock, de la soul et du blues.",
    "aug": "L'accord augmenté remplace la quinte juste par une quinte augmentée, créant une tension symétrique et mystérieuse. À la guitare, seulement 3 formes distinctes couvrent les 12 toniques grâce à sa symétrie. Il sonne parfaitement dans les progressions chromatiques et dans les transitions vers l'accord majeur ou mineur correspondant.",
    "dim": "L'accord diminué empile deux tierces mineures, créant une instabilité très expressive. À la guitare, sa forme compacte se déplace facilement sur le manche par intervalles de 3 demi-tons (symétrie). On le trouve en musique classique, jazz et métal pour créer de la tension avant une résolution.",
    "sus2": "L'accord sus2 suspend la tierce et la remplace par la seconde majeure, créant une sonorité ouverte sans ambiguïté majeure/mineure. Très prisé dans le rock acoustique et la pop, il donne des textures aériennes. Les formes Dsus2 et Asus2 en position ouverte sont des classiques absolus de la guitare acoustique.",
    "sus4": "L'accord sus4 remplace la tierce par la quarte juste, créant une tension qui cherche naturellement à se résoudre. La progression sus4 → majeur est l'une des ornementations les plus simples et expressives de la guitare. Les formes Dsus4, Asus4 et Esus4 en position ouverte sont incontournables.",
    "p5": "L'accord de quinte (power chord) réduit l'harmonie à la fondamentale et la quinte, sans tierce. Cette neutralité combinée à la saturation de l'ampli électrique est l'arme secrète du rock et du métal. Il se joue souvent sur 2 ou 3 cordes avec un seul doigt, ce qui permet des changements d'accords fulgurants.",
    # Sixtes & add
    "add9": "L'accord add9 ajoute la neuvième (seconde à l'octave) à la triade majeure sans septième, créant une couleur lumineuse et étendue. Très populaire en pop et rock acoustique, les formes Gadd9 et Dadd9 en position ouverte avec cordes à vide résonantes sont immédiatement reconnaissables. Il enrichit sans alourdir.",
    "madd9": "L'accord mineur add9 enrichit la triade mineure d'une neuvième sans passer par la septième. Il conserve la mélancolie du mineur tout en ajoutant une dimension aérée. Très utilisé dans la musique de film et le rock alternatif, il est particulièrement beau sur guitare acoustique avec des cordes à vide résonantes.",
    "6": "L'accord majeur de sixte ajoute la sixte majeure à la triade, sans la tension d'une septième. Sa sonorité douce et légèrement rétro est indispensable au jazz, au swing et à la bossa nova. Sur la guitare, il se joue souvent en position ouverte ou en barre avec la sixte accessible sur la corde aiguë.",
    "m6": "L'accord mineur de sixte associe la tierce mineure à la sixte majeure, créant une couleur douce-amère très expressive. Très présent en jazz et en bossa nova, sa sixte majeure dans un contexte mineur lui confère une richesse harmonique particulière. Souvent utilisé dans des lignes de basse descendantes.",
    "69": "L'accord 6/9 ajoute simultanément la sixte et la neuvième à la triade majeure sans septième. Son ambiance ouverte et légèrement suspendue est une signature de la funk et du jazz. Prince, Stevie Wonder en ont fait un élément central de leur langage harmonique. Sur la guitare, ses voicings en drop-2 sont très efficaces.",
    "m69": "L'accord mineur 6/9 combine la couleur sombre du mineur avec les extensions lumineuses de la sixte et de la neuvième. Il offre une richesse harmonique nuancée entre ombre et lumière. Très utilisé dans le jazz modal et la musique de film pour une couleur expressive sans la tension de la septième.",
    # 7èmes
    "maj7": "L'accord majeur septième associe la triade majeure à la septième majeure, créant une couleur enveloppante de sérénité. C'est l'accord des degrés I et IV dans la gamme majeure, très utilisé en jazz, bossa nova et pop sophistiquée. Sur la guitare, ses formes ouvertes (Cmaj7, Emaj7, Amaj7) sonnent avec beaucoup de profondeur.",
    "m7": "L'accord mineur septième est l'un des plus polyvalents de la guitare. Sa couleur douce et légèrement voilée est indispensable au jazz, à la soul et à la funk. La forme Am7 en position ouverte est un grand classique acoustique. Présent aux degrés II, III et VI de la gamme majeure, il est au cœur de toutes les progressions jazz.",
    "7": "L'accord de dominante septième crée une tension forte qui appelle la résolution. Son triton interne (entre la tierce majeure et la septième mineure) lui donne son énergie directionnelle caractéristique. Indispensable au blues et au jazz, il se joue aussi sur les trois degrés I7, IV7, V7 du blues pour cette tension permanente.",
    "m7b5": "L'accord demi-diminué (ø7) combine la quinte diminuée et la septième mineure. C'est l'accord du degré II dans la gamme mineure harmonique, central dans la cadence ii°7–V7–Im en jazz. Sur la guitare, ses voicings compacts se superposent souvent aux formes de l'accord m6, facilitant la mémorisation.",
    "dim7": "L'accord diminué de septième empile trois tierces mineures, divisant l'octave en quatre parties égales. Sa symétrie parfaite lui permet de se résoudre vers quatre toniques différentes. Seulement 3 formes distinctes suffisent pour les 12 toniques, ce qui en fait un accord étonnamment compact sur le manche malgré sa complexité harmonique.",
    "mmaj7": "L'accord mineur majeur 7 combine la tierce mineure et la septième majeure, créant une tension interne très particulière. On le trouve au degré I de la gamme mineure harmonique et dans la célèbre descente chromatique (mM7–m7–m6). Popularisé par les films d'Alfred Hitchcock, il est synonyme de mystère et de suspense.",
    "augmaj7": "L'accord augmenté majeur 7 cumule la quinte augmentée et la septième majeure, créant une double altération très colorée. Il appartient au mode lydien augmenté (3e mode de la mineure mélodique). Sa couleur insolite et tendue est très prisée en jazz modal et dans la composition contemporaine.",
    "aug7": "L'accord augmenté de septième (7#5) est une dominante avec quinte augmentée, créant une double tension. Il appartient à la gamme par tons et peut se résoudre chromatiquement dans plusieurs directions. Très présent dans le blues et le jazz avancé, il annonce souvent une résolution vers un accord mineur.",
    "7sus4": "L'accord 7sus4 combine la suspension de quarte avec la septième mineure de dominante, reportant la résolution tout en maintenant la tension fonctionnelle. Très utilisé dans le jazz-fusion, la soul et la funk, il peut précéder un accord de dominante ou se résoudre directement. Herbie Hancock en a fait un pilier de son langage.",
    "7sus2": "L'accord 7sus2 combine la seconde majeure et la septième mineure, créant une sonorité ouverte et modale. Il évite la définition majeur/mineur tout en maintenant la couleur de septième de dominante. Très utilisé dans le jazz modal et la fusion pour des atmosphères flottantes et ambiguës.",
    "7b5": "L'accord 7b5 remplace la quinte juste par une quinte diminuée, ajoutant un second triton à la tension du V7. Il est interchangeable avec le V7 d'une tonique à distance de triton (substitution), ce qui en fait un accord central dans la réharmonisation jazz. Ses voicings compacts sur les 4 cordes médianes sont très efficaces.",
    "m7s5": "L'accord mineur 7 quinte augmentée (m7#5) crée une tension insolite en combinant une couleur mineure et une quinte altérée vers le haut. On le trouve dans les contextes jazz avancés sur certains degrés de la mineure mélodique. Sa sonorité ambiguë est exploitée dans la musique expérimentale et la fusion.",
    # 9èmes
    "maj9": "L'accord majeur neuvième enrichit le maj7 d'une neuvième, ajoutant une dimension impressionniste. C'est l'accord du degré I ou IV dans les harmonisations jazz sophistiquées. Sa sonorité enveloppante est indispensable en jazz, soul et R&B. Sur la guitare, on sélectionne souvent 4-5 notes parmi ses composants pour un voicing jouable.",
    "m9": "L'accord mineur neuvième ajoute la neuvième au m7, créant une texture riche et douce très présente en jazz moderne et R&B. Sa neuvième majeure (toujours naturelle) apporte une fraîcheur dans la couleur sombre du mineur. Les voicings jazz sans quinte concentrent la fondamentale, la tierce, la septième et la neuvième.",
    "9": "L'accord de neuvième de dominante enrichit le V7 d'une neuvième majeure. Cette extension adoucit légèrement la tension tout en enrichissant la couleur. Très utilisé en jazz, blues avancé et funk, il peut remplacer le V7 dans presque tous les contextes. Jimi Hendrix en a fait un usage emblématique dans son style funk-rock.",
    "7b9": "L'accord 7♭9 ajoute une neuvième bémol au V7, intensifiant considérablement la tension de dominante. Sa neuvième bémol forme une dissonance de demi-ton avec la fondamentale, créant une attraction puissante vers la résolution. Il est au cœur du vocabulaire bebop, surtout dans les cadences en tonalité mineure.",
    "7s9": "L'accord 7♯9 — aussi appelé 'accord Hendrix' — place une neuvième augmentée sur un accord de dominante majeur. Cette coexistence de la tierce majeure et de la neuvième augmentée (= tierce mineure) est explosive et caractéristique du blues-rock. Purple Haze (E7♯9) l'a rendu célèbre. Sa forme barre est compacte et transportable.",
    "m9maj7": "L'accord mineur 9 majeur 7 combine la couleur mineure avec la septième majeure et la neuvième. Il est présent au degré I de la gamme mineure mélodique et crée une tension interne expressive. Utilisé en jazz avancé pour des progressions mineurs très colorées, il est le point de départ de nombreux voicings modaux.",
    "9s11": "L'accord 9♯11 est la neuvième de dominante enrichie d'une quarte augmentée (triton), issu du mode lydien-mixolydien. Cette double tension crée une couleur flottante très jazz. Scott Henderson et Herbie Hancock l'utilisent sur les dominantes pour éviter les clichés et maintenir un langage harmonique sophistiqué.",
    "maj9s11": "L'accord Maj9♯11 est l'accord du mode lydien par excellence. Sa quarte augmentée donne cette couleur rêveuse et éthérée très utilisée en jazz modal et musique de film. Sur la guitare, ses voicings drop-2 ou quartal permettent de capturer cette couleur lumineuse avec des positions jouables.",
    # 11èmes
    "11": "L'accord de onzième de dominante s'utilise surtout sans tierce pour éviter le frottement avec la quarte juste. Dans le jazz, il crée des textures ouvertes et flottantes. Miles Davis a exploré ce type de voicing dans ses périodes modale et fusion, créant des atmosphères harmoniques moins définies et plus contemporaines.",
    "m11": "L'accord mineur onzième empile la quarte juste sur le m9, créant une harmonie dense sans friction grâce à la tierce mineure. C'est l'accord phare du jazz modal et du néo-soul. D'Miles Davis à Kendrick Lamar, il traverse les styles. Ses voicings quartal — en empilant les quartes — lui donnent une couleur très contemporaine.",
    "maj11": "L'accord majeur onzième ajoute la quarte juste au maj9. La tierce majeure et la onzième forment un demi-ton de tension qui demande un voicing soigné. On omet souvent la tierce pour laisser résonner les autres intervalles. Sa richesse harmonique s'épanouit parfaitement dans les ballades jazz à tempo lent.",
    "7s11": "L'accord 7♯11 (lydien-mixolydien) est l'accord du mode lydien dominant. Sa quarte augmentée et sa septième mineure coexistent dans une double dissonance sophistiquée. Thelonious Monk et Bill Evans l'ont popularisé. Sur la guitare, les voicings quartal sont particulièrement adaptés pour maximiser l'ambiguïté tonale.",
    "maj7s11": "L'accord Maj7♯11 est la version majeure du mode lydien avec septième majeure. Sa quarte augmentée crée cette couleur éthérée et lumineuse très utilisée en jazz modal et cinéma. Les voicings ouverts avec cordes à vide résonantes sont particulièrement évocateurs sur guitare acoustique.",
    # 13èmes
    "13": "L'accord de treizième de dominante accumule la sixte sur les extensions du V9, créant la dominante la plus complète possible. En pratique, on sélectionne les intervalles les plus expressifs — généralement tierce, septième et treizième — pour un voicing jouable sur la guitare. Sa résolution est particulièrement riche harmoniquement.",
    "m13": "L'accord mineur treizième ajoute la sixte majeure au m11, créant l'accord mineur le plus étendu possible. Sa sixte dans un contexte mineur lui donne sa couleur douce-amère caractéristique. Très présent en jazz contemporain et R&B haut de gamme, ses voicings pratiques sélectionnent 4-5 notes parmi ses 7 composants.",
    "maj13": "L'accord majeur treizième est l'extension maximale du maj7, combinant neuvième, onzième et treizième. Dans la pratique jazz, on sélectionne les intervalles significatifs pour des voicings idiomatiques. Sa couleur lyrique et complexe en fait l'accord de résolution ultime dans les ballades jazz, souvent placé sur le I final.",
    "13s11": "L'accord 13♯11 est la forme la plus complète du mode lydien-mixolydien. Sa richesse spectrale exceptionnelle et sa couleur flottante en font un favori du jazz moderne. Herbie Hancock et les guitaristes post-bop l'utilisent comme accord de couleur statique autant que comme dominante fonctionnelle. Les voicings drop-2 ou quartal en capturent l'essence.",
    "13b9": "L'accord 13♭9 combine la sixte majeure (treizième) et la neuvième bémol sur une dominante, créant une tension maximale dans deux directions simultanément. C'est l'accord de dominante le plus chargé du vocabulaire bebop. Sa résolution vers l'accord mineur ou majeur crée des mouvements chromatiques très expressifs.",
    # Altérés
    "7alt": "L'accord altéré (7alt) accumule plusieurs altérations sur la dominante : ♭9, ♯9, ♭5 et/ou ♯5. Il représente la tension de dominante la plus extrême, issue de la gamme altérée (7e mode de la mineure mélodique). Sur la guitare, les voicings alt utilisent les 4 cordes aiguës en omettant fondamentale et quinte.",
    "7b9b5": "L'accord 7♭9♭5 double la tension du V7 avec une quinte diminuée et une neuvième bémol. Sa double altération crée une dissonance extrême très appréciée dans le bebop et le jazz avancé. Il peut être utilisé comme substitut du V7alt sur les résolutions ii-V-I en mineur.",
    "7s9b5": "L'accord 7♯9♭5 combine la quinte diminuée (triton) et la neuvième augmentée (= tierce mineure), créant une tension ambiguë entre majeur et mineur. C'est une variante de l'accord Hendrix avec quinte altérée. Sa sonorité explosive est très prisée dans le blues-rock avancé et le jazz-fusion.",
    "7b9s5": "L'accord 7♭9♯5 combine la quinte augmentée et la neuvième bémol, deux altérations caractéristiques de la gamme mineure harmonique vue de son 5e degré (phrygien dominant). Sa tension dramatique et son caractère sombre conviennent parfaitement aux résolutions vers les accords mineurs.",
    "7s9s5": "L'accord 7♯9♯5 accumule deux altérations vers le haut (neuvième et quinte augmentées), créant une couleur très tendue issue de la gamme par tons. Sa symétrie particulière est exploitée dans les contextes jazz avancés pour des tensions avant résolution vers des accords majeurs ou mineurs.",
    "13b5": "L'accord 13♭5 est une dominante enrichie de la treizième avec quinte diminuée, créant une tension combinée entre le registre grave (♭5) et aigu (13e). Très présent dans le jazz avancé et la fusion pour des dominantes altérées complexes, il ouvre des possibilités de réharmonisation sophistiquées.",
}

# ---------------------------------------------------------------------------
# DESCRIPTIONS EN
# ---------------------------------------------------------------------------
CHORD_DESC_EN = {
    # Triads
    "maj": "The major chord is the cornerstone of guitar playing. Its open shapes — E, A, G, C and D — are the first chords every guitarist learns, and the CAGED system lets you move them across the entire neck. Bright and stable, it appears in every style from rock and pop to jazz and folk.",
    "min": "The minor chord brings an essential melancholic color to guitar. The open Em and Am shapes ring beautifully with resonant open strings, and the barre forms (E or A shape) let you play any minor chord anywhere on the neck. It is fundamental to rock, soul, blues, and countless other styles.",
    "aug": "The augmented chord replaces the perfect fifth with an augmented fifth, creating a symmetric, mysterious tension. On guitar, only 3 distinct shapes cover all 12 keys thanks to its symmetry. It works beautifully in chromatic progressions and as a stepping stone toward the corresponding major or minor chord.",
    "dim": "The diminished chord stacks two minor thirds, creating expressive harmonic instability. On guitar, its compact shape moves easily across the neck in 3-semitone intervals (symmetry). Found in classical music, jazz, and metal, it generates tension that begs for resolution.",
    "sus2": "The sus2 chord suspends the third and replaces it with a major second, creating an open sound with no major/minor ambiguity. Very popular in acoustic rock and pop, it creates airy textures. The open Dsus2 and Asus2 shapes are absolute classics of the acoustic guitar.",
    "sus4": "The sus4 chord replaces the third with a perfect fourth, creating tension that naturally seeks resolution. The sus4 → major progression is one of the simplest and most expressive ornaments on guitar. The open Dsus4, Asus4, and Esus4 shapes are essential.",
    "p5": "The power chord (5th chord) reduces harmony to root and fifth, with no third. This neutrality combined with electric amplifier saturation is the secret weapon of rock and metal. Usually played on 2 or 3 strings with one finger, it allows lightning-fast chord changes across the fretboard.",
    # Sixths & add
    "add9": "The add9 chord adds the ninth (second at the octave) to the major triad without a seventh, creating a bright, extended color. Very popular in pop and acoustic rock, the open Gadd9 and Dadd9 shapes with resonant open strings are instantly recognizable. It enriches without adding harmonic weight.",
    "madd9": "The minor add9 chord enriches the minor triad with a ninth without a seventh. It keeps the melancholy of minor while adding an airy quality. Widely used in film music and alternative rock, it sounds particularly beautiful on acoustic guitar with resonant open strings.",
    "6": "The major 6th chord adds the major sixth to the triad without the tension of a seventh. Its soft, slightly retro sound is essential in jazz, swing, and bossa nova. On guitar, it is often played open or barred with the sixth accessible on the high string.",
    "m6": "The minor 6th chord pairs the minor third with the major sixth, creating a bittersweet, expressive color. Very present in jazz and bossa nova, its major sixth in a minor context gives it a special harmonic richness. Often used in descending bass line progressions.",
    "69": "The 6/9 chord adds both the sixth and ninth to the major triad without a seventh. Its open, slightly suspended quality is a signature of funk and jazz. Prince and Stevie Wonder made it central to their harmonic language. On guitar, drop-2 voicings are particularly effective.",
    "m69": "The minor 6/9 chord combines the dark color of minor with the bright extensions of the sixth and ninth. It offers nuanced harmonic richness between shadow and light. Widely used in modal jazz and film music for an expressive color without the tension of a seventh.",
    # 7ths
    "maj7": "The major seventh chord pairs the major triad with the major seventh, creating an enveloping, serene color. It represents degrees I and IV in major key harmonizations, widely used in jazz, bossa nova, and sophisticated pop. On guitar, the open Cmaj7, Emaj7, and Amaj7 shapes sound with great depth.",
    "m7": "The minor seventh chord is one of the most versatile on guitar. Its soft, slightly veiled color is indispensable in jazz, soul, and funk. The open Am7 shape is an acoustic classic. Appearing on degrees II, III, and VI of the major scale, it is at the heart of all jazz progressions.",
    "7": "The dominant seventh chord creates strong tension that calls for resolution. Its internal tritone (between the major third and minor seventh) gives it its characteristic directional energy. Essential in blues and jazz, it is also used on all three main blues degrees (I7, IV7, V7) for permanent tension.",
    "m7b5": "The half-diminished chord (ø7) combines a diminished fifth and a minor seventh. It is the chord on degree II of the harmonic minor scale, central to the ii°7–V7–Im jazz cadence. On guitar, its compact voicings often overlap with m6 shapes, making them easier to memorize and use together.",
    "dim7": "The diminished seventh chord stacks three minor thirds, dividing the octave into four equal parts. Its perfect symmetry lets it resolve to four different tonics. Only 3 distinct shapes cover all 12 keys, making it a surprisingly compact chord to master despite its harmonic complexity.",
    "mmaj7": "The minor major 7th chord combines a minor third with a major seventh, creating a very particular internal tension. Found on degree I of the harmonic minor scale, it is known for the famous chromatic descent (mM7–m7–m6). Popularized by Alfred Hitchcock film scores, it evokes mystery and suspense.",
    "augmaj7": "The augmented major 7th chord accumulates an augmented fifth and a major seventh, creating a doubly colorful alteration. It belongs to the Lydian augmented mode (3rd mode of melodic minor). Its unusual, tense color is prized in modal jazz and contemporary composition.",
    "aug7": "The augmented dominant 7th chord (7#5) is a dominant chord with an augmented fifth, creating double tension. It belongs to the whole-tone scale and can resolve chromatically in several directions. Common in blues and advanced jazz, it often precedes resolution to minor chords.",
    "7sus4": "The 7sus4 chord combines the fourth suspension with the dominant minor seventh, delaying resolution while maintaining functional tension. Widely used in jazz-fusion, soul, and funk, it can precede a standard dominant chord or resolve directly. Herbie Hancock made it a pillar of his harmonic language.",
    "7sus2": "The 7sus2 chord combines the major second with the minor seventh, creating an open, modal sound. It avoids the major/minor definition while maintaining the dominant seventh color. Very used in modal jazz and fusion for floating, ambiguous atmospheres.",
    "7b5": "The 7♭5 chord replaces the perfect fifth with a diminished fifth, adding a second tritone to the V7 tension. It is interchangeable with the V7 a tritone away (tritone substitution), making it central to jazz reharmonization. Its compact voicings on the middle 4 strings are very effective.",
    "m7s5": "The minor 7 sharp 5 chord (m7#5) creates an unusual tension by combining a minor color with an upward-altered fifth. Found in advanced jazz contexts on certain degrees of the melodic minor, its ambiguous sound is exploited in experimental music and fusion.",
    # 9ths
    "maj9": "The major ninth chord enriches the maj7 with a ninth, adding an Impressionist dimension. It represents degree I or IV in sophisticated jazz harmonizations. Its enveloping sound is essential in jazz, soul, and R&B. On guitar, you typically select 4–5 notes from its components for a playable voicing.",
    "m9": "The minor ninth chord adds the ninth to the m7, creating a rich, soft texture very present in modern jazz and R&B. Its natural (major) ninth brings freshness to the dark minor color. Jazz voicings often omit the fifth to concentrate the root, third, seventh, and ninth.",
    "9": "The dominant ninth chord enriches the V7 with a major ninth. This extension slightly softens the tension while enriching the color. Widely used in jazz, advanced blues, and funk, it can replace the V7 in almost any context. Jimi Hendrix made iconic use of it in his funk-rock style.",
    "7b9": "The 7♭9 chord adds a flat ninth to the V7, considerably intensifying the dominant tension. Its flat ninth forms a semitone dissonance with the root, creating a powerful pull toward resolution. It is central to bebop vocabulary, especially in minor key cadences.",
    "7s9": "The 7♯9 chord — also called the 'Hendrix chord' — places an augmented ninth over a major dominant chord. The coexistence of the major third and augmented ninth (= minor third) is explosive and characteristic of blues-rock. Purple Haze (E7♯9) made it famous. Its barre shape is compact and transportable across the neck.",
    "m9maj7": "The minor 9 major 7 chord combines the minor color with a major seventh and ninth. It appears on degree I of the melodic minor scale and creates expressive internal tension. Used in advanced jazz for richly colored minor progressions, it is the starting point for many modal voicings.",
    "9s11": "The 9♯11 chord is the dominant ninth enriched with an augmented fourth (tritone), derived from the Lydian Mixolydian mode. This double tension creates a floating, very jazz-sounding color. Scott Henderson and Herbie Hancock use it on dominants to avoid clichés and maintain sophisticated harmonic language.",
    "maj9s11": "The Maj9♯11 chord is the quintessential Lydian mode chord. Its augmented fourth gives it that dreamy, ethereal color widely used in modal jazz and film music. On guitar, drop-2 or quartal voicings capture this bright color in playable positions.",
    # 11ths
    "11": "The dominant 11th chord is most often used without the third to avoid the clash with the perfect fourth. In jazz, it creates open, floating textures. Miles Davis explored this type of voicing during his modal and fusion periods, creating less defined and more contemporary harmonic atmospheres.",
    "m11": "The minor 11th chord stacks the perfect fourth onto the m9, creating a dense harmonic texture without friction thanks to the minor third. It is the signature chord of modal jazz and neo-soul. From Miles Davis to Kendrick Lamar, it crosses all styles. Quartal voicings — stacking fourths — give it a very contemporary sound.",
    "maj11": "The major 11th chord adds the perfect fourth to the maj9. The major third and the eleventh form a semitone of tension requiring careful voicing. Omitting the third often lets the other intervals resonate freely. Its harmonic richness flourishes best in slow-tempo jazz ballads.",
    "7s11": "The 7♯11 chord (Lydian dominant) is the Lydian Mixolydian mode chord. Its augmented fourth and minor seventh coexist in a sophisticated double dissonance. Thelonious Monk and Bill Evans popularized it. On guitar, quartal voicings are particularly suited to maximize its tonal ambiguity.",
    "maj7s11": "The Maj7♯11 chord is the Lydian mode with a major seventh. Its augmented fourth creates that ethereal, luminous color widely used in modal jazz and cinema. Open voicings with resonant open strings are particularly evocative on acoustic guitar.",
    # 13ths
    "13": "The dominant 13th chord accumulates the sixth over the 9th extensions, creating the most complete dominant possible. In practice, you select the most expressive intervals — typically third, seventh, and thirteenth — for a playable guitar voicing. Its resolution is particularly harmonically rich.",
    "m13": "The minor 13th chord adds the major sixth to the m11, creating the most extended minor chord possible. Its sixth in a minor context gives it its bittersweet characteristic color. Very present in contemporary jazz and high-end R&B, practical voicings select 4–5 notes from its 7 components.",
    "maj13": "The major 13th chord is the maximum extension of the maj7, combining ninth, eleventh, and thirteenth. In jazz practice, you select the significant intervals for idiomatic voicings. Its lyrical, complex color makes it the ultimate resolution chord in jazz ballads, often placed on the final I chord.",
    "13s11": "The 13♯11 chord is the most complete form of the Lydian Mixolydian mode. Its exceptional spectral richness and floating color make it a favorite in modern jazz. Herbie Hancock and post-bop guitarists use it as both a color chord and a functional dominant. Drop-2 or quartal voicings capture its essence.",
    "13b9": "The 13♭9 chord combines the major sixth (thirteenth) and the flat ninth on a dominant, creating maximum tension in two simultaneous directions. It is the most loaded dominant chord in the bebop vocabulary. Its resolution to major or minor creates very expressive chromatic voice movements.",
    # Altered
    "7alt": "The altered chord (7alt) accumulates several alterations on the dominant: ♭9, ♯9, ♭5 and/or ♯5. It represents the most extreme dominant tension, derived from the altered scale (7th mode of melodic minor). On guitar, alt voicings use the top 4 strings, omitting root and fifth to keep only the most expressive tensions.",
    "7b9b5": "The 7♭9♭5 chord doubles the V7 tension with a diminished fifth and a flat ninth. Its double alteration creates extreme dissonance appreciated in bebop and advanced jazz. It can be used as a substitute for V7alt in ii-V-I minor resolutions.",
    "7s9b5": "The 7♯9♭5 chord combines the diminished fifth (tritone) and the augmented ninth (= minor third), creating an ambiguous tension between major and minor. It is a variant of the Hendrix chord with an altered fifth. Its explosive sound is prized in advanced blues-rock and jazz-fusion.",
    "7b9s5": "The 7♭9♯5 chord combines the augmented fifth and the flat ninth, two alterations characteristic of the harmonic minor scale seen from its 5th degree (Phrygian dominant). Its dramatic tension and dark character are perfect for resolving to minor chords.",
    "7s9s5": "The 7♯9♯5 chord accumulates two upward alterations (augmented ninth and fifth), creating a tense color derived from the whole-tone scale. Its particular symmetry is exploited in advanced jazz contexts for tension before resolving to major or minor chords.",
    "13b5": "The 13♭5 chord is a dominant enriched with the thirteenth and a diminished fifth, combining tension in the low register (♭5) and high register (13th). Very present in advanced jazz and fusion for complex altered dominants, it opens sophisticated reharmonization possibilities.",
}

# ---------------------------------------------------------------------------
# INDICES DE DOIGTÉS / POSITIONS (courts, pour le hint HTML)
# ---------------------------------------------------------------------------
POSITIONS_HINT_FR = {
    "maj":  "Formes ouvertes (E, A, G, C, D) + barré mobile sur tout le manche via le système CAGED.",
    "min":  "Formes ouvertes Em et Am + barré mobile (forme E ou A).",
    "7":    "Formes ouvertes E7, A7, D7, G7 disponibles + barré mobile E7 et A7.",
    "maj7": "Formes ouvertes Emaj7, Amaj7, Dmaj7 disponibles + variantes en barre.",
    "m7":   "Formes ouvertes Em7, Am7, Dm7 disponibles + barre mobile Am7 et Em7.",
}
POSITIONS_HINT_EN = {
    "maj":  "Open shapes (E, A, G, C, D) + movable barre chord across the neck via the CAGED system.",
    "min":  "Open Em and Am shapes + movable barre chord (E or A shape).",
    "7":    "Open E7, A7, D7, G7 shapes available + movable barre E7 and A7.",
    "maj7": "Open Emaj7, Amaj7, Dmaj7 shapes available + barre variations.",
    "m7":   "Open Em7, Am7, Dm7 shapes available + movable Am7 and Em7 barre.",
}

# ---------------------------------------------------------------------------
# ACCORDS CONNEXES par groupe
# ---------------------------------------------------------------------------
def related_in_group(chord_id, group_id, limit=5):
    for g in CHORD_GROUPS:
        if g["id"] == group_id:
            return [c for c in g["chords"] if c["id"] != chord_id][:limit]
    return []

# ---------------------------------------------------------------------------
# GÉNÉRATION
# ---------------------------------------------------------------------------
def main():
    env = Environment(loader=FileSystemLoader(str(TMPL_DIR)), autoescape=True)
    chord_tpl = env.get_template("chord_guitar.html.jinja2")

    pages_fr = []
    pages_en = []

    print(f"Génération accords guitare FR → {OUT_FR}")
    print(f"Génération accords guitare EN → {OUT_EN}")

    for group in CHORD_GROUPS:
        for chord in group["chords"]:
            cslug = chord_slug(chord["id"])

            # Pages canoniques (12 toniques)
            for root in ROOTS:
                _gen_page(chord_tpl, chord, group, root, cslug, 'fr',
                          OUT_FR, pages_fr, canonical_root=root)
                _gen_page(chord_tpl, chord, group, root, cslug, 'en',
                          OUT_EN, pages_en, canonical_root=root)

            # Pages enharmoniques (5 toniques supplémentaires)
            for eroot in ENHARMONIC_ROOTS:
                _gen_page(chord_tpl, chord, group, eroot, cslug, 'fr',
                          OUT_FR, pages_fr, canonical_root=None, is_enharmonic=True)
                _gen_page(chord_tpl, chord, group, eroot, cslug, 'en',
                          OUT_EN, pages_en, canonical_root=None, is_enharmonic=True)

    # ---- Hubs ----
    gen_hub(OUT_FR, 'fr', pages_fr)
    gen_hub(OUT_EN, 'en', pages_en)

    update_sitemap(pages_fr, pages_en)

    print(f"  FR : {len(pages_fr)} pages (dont {len(pages_fr)-1} accords + 1 hub)")
    print(f"  EN : {len(pages_en)} pages (dont {len(pages_en)-1} accords + 1 hub)")
    print(f"  Total : {len(pages_fr)+len(pages_en)} pages")
    print("  sitemap.xml mis à jour")
    print("Done.")


def _gen_page(tpl, chord, group, root, cslug, lang, out_root, pages_list,
              canonical_root=None, is_enharmonic=False):
    root_slug_fr = root.get("slug", root["slug"])
    root_slug_en = root.get("slug_en", root["slug_en"])
    root_fr_name = root.get("fr", root.get("name",""))
    root_en_name = root.get("name","")

    page_url_fr = f"{BASE_URL}/fr/accords-guitare/{root_slug_fr}/{cslug}/"
    page_url_en = f"{BASE_URL}/en/chords-guitar/{root_slug_en}/{cslug}/"

    if is_enharmonic:
        can_slug_fr = root.get("canonical_slug", root_slug_fr)
        can_slug_en = root.get("canonical_slug_en", root_slug_en)
        canonical_url_fr = f"{BASE_URL}/fr/accords-guitare/{can_slug_fr}/{cslug}/"
        canonical_url_en = f"{BASE_URL}/en/chords-guitar/{can_slug_en}/{cslug}/"
    else:
        canonical_url_fr = page_url_fr
        canonical_url_en = page_url_en

    if lang == 'fr':
        page_url = page_url_fr
        canonical_url = canonical_url_fr
    else:
        page_url = page_url_en
        canonical_url = canonical_url_en

    n_notes = len(chord["iv"])
    chord_label = chord["label_fr"] if lang == 'fr' else chord["label_en"]
    group_label = group["label_fr"] if lang == 'fr' else group["label_en"]
    desc = CHORD_DESC_FR.get(chord["id"], "") if lang == 'fr' else CHORD_DESC_EN.get(chord["id"], "")
    positions_hint = POSITIONS_HINT_FR.get(chord["id"]) if lang == 'fr' else POSITIONS_HINT_EN.get(chord["id"])

    notes_primary   = chord_notes(root["pc"], chord["iv"], lang)
    notes_secondary = chord_notes(root["pc"], chord["iv"], 'en' if lang == 'fr' else 'fr')
    notes_wr        = chord_notes_with_roles(root["pc"], chord["iv"], lang)
    notes_str       = " – ".join(notes_primary)

    root_display_fr = root_fr_name
    root_display_en = root_en_name

    nav_roots_fr = [{"name": r["fr"],   "slug": r["slug"]}    for r in ROOTS]
    nav_roots_en = [{"name": r["name"], "slug": r["slug_en"]} for r in ROOTS]

    related = related_in_group(chord["id"], group["id"])

    if lang == 'fr':
        chord_name_full = f"{root_display_fr} {chord_label}"
        ctx = {
            "lang": "fr",
            "root": root,
            "chord": chord,
            "chord_slug": cslug,
            "chord_label": chord_label,
            "group_label": group_label,
            "n_notes": n_notes,
            "notes_primary": notes_primary,
            "notes_secondary": notes_secondary,
            "notes_secondary_label": "Notation anglaise",
            "notes_with_roles": notes_wr,
            "notes_str": notes_str,
            "desc": desc,
            "positions_hint": positions_hint,
            "related_chords": related,
            "app_link": APP_URL,
            "page_url": page_url,
            "canonical_url": canonical_url,
            "alt_url_fr": canonical_url_fr,
            "alt_url_en": canonical_url_en,
            "BASE_URL": BASE_URL,
            "nav_roots": nav_roots_fr,
            "nav_base": f"{BASE_URL}/fr/accords-guitare",
            "ui_title": f"Accord {chord_name_full} guitare — {notes_str} | ScalaBass",
            "ui_meta_desc": f"Accord {chord_name_full} à la guitare : {notes_str}. {n_notes} note{'s' if n_notes>1 else ''}. Diagrammes, positions sur le manche, système CAGED. Appli interactive.",
            "ui_h1": f"Accord de {chord_name_full} à la guitare",
            "ui_symbol": "Symbole",
            "ui_notes": "Notes de l'accord",
            "ui_intervals": "Structure de l'accord",
            "ui_about": "À propos de cet accord",
            "ui_cta_text": f"Voir tous les diagrammes et positions sur le manche pour <strong>{chord_name_full}</strong> dans l'appli interactive ScalaBass.",
            "ui_cta_btn": "Explorer dans ScalaBass →",
            "ui_other_keys": "Même accord dans d'autres toniques",
            "ui_all_chords": "Tous les accords guitare",
            "ui_related": f"Autres accords {group_label}",
            "ui_og_title": f"Accord {chord_name_full} — Guitare",
            "ui_og_desc": f"{chord_name_full} guitare : {notes_str}",
            "ui_schema_head": f"Accord {chord_name_full} guitare",
            "ui_schema_desc": f"{chord_name_full} pour guitare 6 cordes : {notes_str}.",
        }
        out_dir = out_root / root_slug_fr / cslug
    else:
        chord_name_full = f"{root_display_en} {chord_label}"
        ctx = {
            "lang": "en",
            "root": root,
            "chord": chord,
            "chord_slug": cslug,
            "chord_label": chord_label,
            "group_label": group_label,
            "n_notes": n_notes,
            "notes_primary": notes_primary,
            "notes_secondary": notes_secondary,
            "notes_secondary_label": "Solfège",
            "notes_with_roles": notes_wr,
            "notes_str": notes_str,
            "desc": desc,
            "positions_hint": positions_hint,
            "related_chords": related,
            "app_link": APP_URL,
            "page_url": page_url,
            "canonical_url": canonical_url,
            "alt_url_fr": canonical_url_fr,
            "alt_url_en": canonical_url_en,
            "BASE_URL": BASE_URL,
            "nav_roots": nav_roots_en,
            "nav_base": f"{BASE_URL}/en/chords-guitar",
            "ui_title": f"{chord_name_full} Guitar Chord — {notes_str} | ScalaBass",
            "ui_meta_desc": f"{chord_name_full} guitar chord: {notes_str}. {n_notes} note{'s' if n_notes>1 else ''}. Chord diagrams, CAGED positions, interactive fretboard.",
            "ui_h1": f"{chord_name_full} Guitar Chord",
            "ui_symbol": "Symbol",
            "ui_notes": "Chord Notes",
            "ui_intervals": "Chord Structure",
            "ui_about": "About this chord",
            "ui_cta_text": f"See all diagrams and fretboard positions for <strong>{chord_name_full}</strong> in the interactive ScalaBass app.",
            "ui_cta_btn": "Explore in ScalaBass →",
            "ui_other_keys": "Same chord in other keys",
            "ui_all_chords": "All guitar chords",
            "ui_related": f"Other {group_label} chords",
            "ui_og_title": f"{chord_name_full} Guitar Chord",
            "ui_og_desc": f"{chord_name_full} guitar: {notes_str}",
            "ui_schema_head": f"{chord_name_full} guitar chord",
            "ui_schema_desc": f"{chord_name_full} for 6-string guitar: {notes_str}.",
        }
        out_dir = out_root / root_slug_en / cslug

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "index.html").write_text(tpl.render(**ctx), encoding="utf-8")
    pages_list.append(page_url)


def gen_hub(out_root, lang, pages_list):
    """Génère la page hub listant tous les accords × toutes les toniques."""
    out_root.mkdir(parents=True, exist_ok=True)
    if lang == 'fr':
        hub_url = f"{BASE_URL}/fr/accords-guitare/"
        hub_base = f"{BASE_URL}/fr/accords-guitare"
        title = "Tous les accords de guitare — Diagrammes et positions | ScalaBass"
        desc_meta = "Tous les accords de guitare 6 cordes : triades, septièmes, neuvièmes, extensions, altérations. Diagrammes, positions CAGED, appli interactive."
        h1 = "Tous les accords de guitare"
        sub = "49 types d'accords × 12 toniques — diagrammes, positions, appli interactive"
    else:
        hub_url = f"{BASE_URL}/en/chords-guitar/"
        hub_base = f"{BASE_URL}/en/chords-guitar"
        title = "All Guitar Chords — Diagrams and Positions | ScalaBass"
        desc_meta = "All 6-string guitar chords: triads, sevenths, ninths, extensions, altered chords. Chord diagrams, CAGED positions, interactive app."
        h1 = "All Guitar Chords"
        sub = "49 chord types × 12 keys — diagrams, positions, interactive app"

    rows = []
    for group in CHORD_GROUPS:
        gl = group["label_fr"] if lang == 'fr' else group["label_en"]
        chord_links = []
        for chord in group["chords"]:
            cslug = chord_slug(chord["id"])
            sym_html = f' <small style="opacity:.6">{chord["sym"]}</small>' if chord["sym"] else ""
            chord_links.append(f'<a href="{hub_base}/{"do" if lang=="fr" else "c"}/{cslug}/">{chord["label_fr"] if lang=="fr" else chord["label_en"]}{sym_html}</a>')
        rows.append(f'<div class="hub-group"><h2>{gl}</h2><div class="chord-links">{"".join(chord_links)}</div></div>')

    note_links = []
    for r in ROOTS:
        n_slug = r["slug"] if lang == 'fr' else r["slug_en"]
        n_name = r["fr"] if lang == 'fr' else r["name"]
        first_c = chord_slug(CHORD_GROUPS[0]["chords"][0]["id"])
        note_links.append(f'<a href="{hub_base}/{n_slug}/{first_c}/">{n_name}</a>')

    html = f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>{title}</title>
  <meta name="description" content="{desc_meta}">
  <link rel="canonical" href="{hub_url}">
  <link rel="alternate" hreflang="fr" href="{BASE_URL}/fr/accords-guitare/">
  <link rel="alternate" hreflang="en" href="{BASE_URL}/en/chords-guitar/">
  <link rel="alternate" hreflang="x-default" href="{BASE_URL}/fr/accords-guitare/">
  <style>
    :root{{--bg:#1a1a20;--panel:#23232b;--line:#333340;--text:#e8e8f0;--muted:#8888a0;--brass:#c4102c}}
    *{{box-sizing:border-box;margin:0;padding:0}}
    body{{background:var(--bg);color:var(--text);font-family:"Segoe UI",system-ui,sans-serif;font-size:15px;line-height:1.6}}
    a{{color:var(--brass);text-decoration:none}} a:hover{{text-decoration:underline}}
    .topnav{{background:var(--panel);border-bottom:1px solid var(--line);padding:10px 20px;display:flex;align-items:center;gap:16px;flex-wrap:wrap}}
    .topnav .logo{{font-weight:700;letter-spacing:.15em;font-size:13px;text-transform:uppercase;color:var(--brass)}}
    .topnav a{{color:var(--muted);font-size:13px}}
    main{{max-width:900px;margin:0 auto;padding:28px 24px 64px}}
    h1{{font-size:clamp(22px,4vw,34px);font-weight:700;margin-bottom:6px}}
    .sub{{color:var(--muted);margin-bottom:28px;font-size:14px}}
    h2{{font-size:14px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);margin:24px 0 10px;border-bottom:1px solid var(--line);padding-bottom:6px}}
    .hub-group{{margin-bottom:28px}}
    .chord-links{{display:flex;flex-wrap:wrap;gap:6px}}
    .chord-links a{{background:var(--panel);border:1px solid var(--line);border-radius:6px;padding:5px 12px;font-size:13px;color:var(--muted)}}
    .chord-links a:hover{{color:var(--text);text-decoration:none}}
    .note-links{{display:flex;flex-wrap:wrap;gap:6px;margin:16px 0 28px}}
    .note-links a{{background:var(--panel);border:1px solid rgba(196,16,44,.3);border-radius:6px;padding:5px 14px;font-size:13px;color:var(--brass);font-weight:700}}
    .note-links a:hover{{text-decoration:none;opacity:.8}}
    .cta{{margin-top:40px;padding:20px 24px;background:var(--panel);border:1px solid rgba(196,16,44,.3);border-radius:10px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px}}
    .cta-btn{{background:var(--brass);color:#fff;font-weight:700;padding:10px 20px;border-radius:8px;font-size:14px}}
    .cta-btn:hover{{text-decoration:none;opacity:.9}}
  </style>
</head>
<body>
<nav class="topnav">
  <span class="logo">ScalaBass</span>
  <a href="{BASE_URL}/manche-guitare.html">{"Manche" if lang=="fr" else "Fretboard"}</a>
  <a href="{BASE_URL}/gammes-guitare.html">{"Gammes" if lang=="fr" else "Scales"}</a>
  <a href="{BASE_URL}/arpeges-guitare.html">{"Arpèges" if lang=="fr" else "Arpeggios"}</a>
  <a href="{BASE_URL}/accords-guitare.html">{"Accords" if lang=="fr" else "Chords"}</a>
  <a href="{BASE_URL}/intervalles-guitare.html">{"Intervalles" if lang=="fr" else "Intervals"}</a>
</nav>
<main>
  <h1>{h1}</h1>
  <p class="sub">{sub}</p>

  <h2>{"Choisir une tonique" if lang=="fr" else "Choose a key"}</h2>
  <div class="note-links">{"".join(note_links)}</div>

  {"".join(rows)}

  <div class="cta">
    <p style="color:var(--muted);font-size:14px">{"Appli interactive : diagrammes, audio, manche, CAGED pour tous les accords en temps réel." if lang=="fr" else "Interactive app: diagrams, audio, fretboard, CAGED for all chords in real time."}</p>
    <a class="cta-btn" href="{APP_URL}">{"Lancer ScalaBass →" if lang=="fr" else "Launch ScalaBass →"}</a>
  </div>
</main>
</body>
</html>"""

    (out_root / "index.html").write_text(html, encoding="utf-8")
    pages_list.append(hub_url)


def update_sitemap(pages_fr, pages_en):
    """Ajoute/remplace les pages accords guitare dans le sitemap."""
    sitemap_path = REPO_ROOT / "sitemap.xml"
    existing = []
    if sitemap_path.exists():
        content = sitemap_path.read_text(encoding="utf-8")
        existing = re.findall(r'<loc>(.*?)</loc>', content)
    kept = [u for u in existing
            if "/fr/accords-guitare/" not in u and "/en/chords-guitar/" not in u]
    all_urls = kept + pages_fr + pages_en
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for url in all_urls:
        lines.append(f'  <url><loc>{url}</loc></url>')
    lines.append('</urlset>')
    sitemap_path.write_text('\n'.join(lines) + '\n', encoding="utf-8")


if __name__ == "__main__":
    main()
