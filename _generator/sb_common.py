#!/usr/bin/env python3
"""
ScalaBass — briques communes des générateurs de pages SEO
=========================================================
Module autonome (aucun import depuis generate.py) partagé par les quatre
générateurs. Il fournit :

  * l'orthographe correcte des notes d'accords et d'arpèges
    (Ré majeur = Ré – Fa♯ – La, et non Ré – Sol♭ – La) ;
  * la formule en degrés d'une gamme (1 2 ♭3 4 5 ♭6 ♭7) ;
  * les accords de septième d'une gamme, sa gamme mère, ses notes
    caractéristiques, son accord de tonique ;
  * un diagramme de manche en SVG et une tablature (une position jouable) ;
  * les diagrammes d'accords de guitare en SVG, à partir de chords-db.js
    (positions vérifiées note par note) avec un chercheur de secours ;
  * les textes pédagogiques « comment travailler ».

Tout est calculé : aucune donnée n'est recopiée à la main.
"""
import json, re
from functools import lru_cache
from pathlib import Path
from markupsafe import Markup, escape

REPO_ROOT = Path(__file__).parent.parent
BASE_URL = "https://scalabass.com"

LETTERS = ['C', 'D', 'E', 'F', 'G', 'A', 'B']
LETTER_PC = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}
FR_LETTER = {'C': 'Do', 'D': 'Ré', 'E': 'Mi', 'F': 'Fa', 'G': 'Sol', 'A': 'La', 'B': 'Si'}
MAJOR_IV = [0, 2, 4, 5, 7, 9, 11]
MINOR_IV = [0, 2, 3, 5, 7, 8, 10]
# Nom le plus simple pour chaque hauteur (secours quand l'orthographe
# théorique demanderait un double dièse ou un double bémol).
SIMPLE = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B']

BASS_OPEN = [28, 33, 38, 43]               # E1 A1 D2 G2
GUITAR_OPEN = [40, 45, 50, 55, 59, 64]     # E2 A2 D3 G3 B3 E4
STRING_NAMES = {4: ['E', 'A', 'D', 'G'], 6: ['E', 'A', 'D', 'G', 'B', 'e']}

# Slugs des 12 toniques canoniques, par hauteur
ROOT_SLUGS = [
    ("C", "Do", "do", "c"), ("Db", "Réb", "re-bemol", "db"), ("D", "Ré", "re", "d"),
    ("Eb", "Mib", "mi-bemol", "eb"), ("E", "Mi", "mi", "e"), ("F", "Fa", "fa", "f"),
    ("F#", "Fa#", "fa-diese", "f-sharp"), ("G", "Sol", "sol", "g"),
    ("Ab", "Lab", "la-bemol", "ab"), ("A", "La", "la", "a"),
    ("Bb", "Sib", "si-bemol", "bb"), ("B", "Si", "si", "b"),
]


# ---------------------------------------------------------------------------
# NOTES
# ---------------------------------------------------------------------------
def pc_of(note):
    pc = LETTER_PC[note[0]]
    for c in note[1:]:
        pc += 1 if c == '#' else -1 if c == 'b' else 0
    return pc % 12


def show(note, lang='en'):
    """Nom affiché : 'F#' → 'F♯' (en) ou 'Fa♯' (fr)."""
    acc = note[1:].replace('#', '♯').replace('b', '♭')
    return (FR_LETTER[note[0]] if lang == 'fr' else note[0]) + acc


def spell(root, letter_step, semitones):
    """Note située `letter_step` lettres et `semitones` demi-tons au-dessus
    de `root`. Les doubles altérations sont ramenées au nom le plus simple."""
    letter = LETTERS[(LETTERS.index(root[0]) + letter_step) % 7]
    target = (pc_of(root) + semitones) % 12
    diff = (target - LETTER_PC[letter] + 12) % 12
    if diff > 6:
        diff -= 12
    if abs(diff) >= 2:
        return SIMPLE[target]
    return letter + ('#' * diff if diff > 0 else 'b' * (-diff))


def root_ascii(root):
    """Nom ASCII de la tonique d'un dict ROOTS/ENHARMONIC_ROOTS ('Db', 'C#')."""
    return root["name"].replace('♯', '#').replace('♭', 'b')


# ---------------------------------------------------------------------------
# ACCORDS / ARPÈGES : rôle et orthographe de chaque note
# ---------------------------------------------------------------------------
def chord_roles(iv):
    """[(rôle, pas de lettre)] pour chaque intervalle d'un accord.
    Le rôle dépend du contexte : 6 demi-tons = ♭5 dans un accord diminué mais
    ♯11 quand la quinte juste est présente ; 9 demi-tons = 6, 13 ou 7 diminuée."""
    s = {i % 12 for i in iv}
    has_third = 3 in s or 4 in s
    has_seventh = 10 in s or 11 in s
    dim7 = 3 in s and 6 in s and 9 in s and not has_seventh and 7 not in s
    out = []
    for i in iv:
        m = i % 12
        if m == 0:   r = ('R', 0)
        elif m == 1: r = ('♭9', 1)
        elif m == 2: r = ('9', 1) if (has_third or i >= 12) else ('2', 1)
        elif m == 3: r = ('♯9', 1) if 4 in s else ('♭3', 2)
        elif m == 4: r = ('3', 2)
        elif m == 5: r = ('11', 3) if has_third else ('4', 3)
        elif m == 6: r = ('♯11', 3) if (7 in s or i >= 12) else ('♭5', 4)
        elif m == 7: r = ('5', 4)
        elif m == 8: r = ('♭13', 5) if 7 in s else ('♯5', 4)
        elif m == 9:
            if dim7:            r = ('°7', 6)
            elif has_seventh:   r = ('13', 5)
            else:               r = ('6', 5)
        elif m == 10: r = ('♭7', 6)
        else:         r = ('7', 6)
        out.append(r)
    return out


def chord_spelling(root, iv):
    """Notes ASCII d'un accord, correctement orthographiées."""
    return [spell(root, step, i) for (_, step), i in zip(chord_roles(iv), iv)]


def chord_notes(root, iv, lang='fr'):
    return [show(n, lang) for n in chord_spelling(root, iv)]


def chord_notes_with_roles(root, iv, lang='fr'):
    return [{"name": show(n, lang), "role": r}
            for n, (r, _) in zip(chord_spelling(root, iv), chord_roles(iv))]


# ---------------------------------------------------------------------------
# GAMMES : formule, accords, parenté
# ---------------------------------------------------------------------------
def degree_formula(ls, iv):
    """['1','2','♭3',…] : chaque degré comparé à la gamme majeure."""
    out = []
    for l, i in zip(ls, iv):
        d = i - MAJOR_IV[l]
        acc = {0: '', 1: '♯', 2: '♯♯', -1: '♭', -2: '♭♭'}.get(d, '')
        out.append(f"{acc}{l + 1}")
    return out


SEVENTH_Q = {
    (4, 7, 11): ('maj7', 'Majeur 7', 'Major 7'),
    (4, 7, 10): ('7', 'Dominante 7', 'Dominant 7'),
    (3, 7, 10): ('m7', 'mineur 7', 'minor 7'),
    (3, 7, 11): ('mMaj7', 'mineur majeur 7', 'minor major 7'),
    (3, 6, 10): ('m7♭5', 'demi-diminué', 'half-diminished'),
    (3, 6, 9):  ('°7', 'diminué 7', 'diminished 7'),
    (4, 8, 11): ('maj7♯5', 'majeur 7 ♯5', 'major 7 ♯5'),
    (4, 8, 10): ('7♯5', '7 ♯5', '7 ♯5'),
    (4, 6, 10): ('7♭5', '7 ♭5', '7 ♭5'),
    (4, 6, 11): ('maj7♭5', 'majeur 7 ♭5', 'major 7 ♭5'),
    (3, 6, 11): ('°Maj7', 'diminué majeur 7', 'diminished major 7'),
    (4, 8, 9):  ('6♯5', 'sixte ♯5', 'sixth ♯5'),
    (4, 7, 9):  ('6', 'sixte', 'sixth'),
    (3, 7, 9):  ('m6', 'mineur 6', 'minor 6'),
}
ROMAN = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII']


def build_sevenths(notes, lang='fr'):
    """Accords de 4 sons (empilement de tierces) d'une gamme de 7 notes."""
    if len(notes) != 7:
        return []
    out = []
    for i in range(7):
        r, t, f, s = (notes[(i + k) % 7] for k in (0, 2, 4, 6))
        rp = pc_of(r)
        key = tuple((pc_of(x) - rp) % 12 for x in (t, f, s))
        q = SEVENTH_Q.get(key)
        if not q:
            continue
        minor = key[0] == 3
        out.append({"roman": ROMAN[i].lower() if minor else ROMAN[i],
                    "name": show(r, lang) + q[0],
                    "quality": q[1] if lang == 'fr' else q[2]})
    return out if len(out) >= 5 else []


def tonic_chord(iv):
    """Accord de tonique d'une gamme → (symbole, id accord guitare, id arpège)."""
    s = set(iv)
    third = 'M' if 4 in s else 'm' if 3 in s else 's4' if 5 in s else 's2' if 2 in s else None
    fifth = 'P' if 7 in s else 'd' if 6 in s else 'a' if 8 in s else 'P'
    seventh = 'M' if 11 in s and 10 not in s else 'm' if 10 in s else 'M' if 11 in s else None
    table = {
        ('M', 'P', 'M'): ('maj7', 'maj7', 'maj7'),
        ('M', 'P', 'm'): ('7', '7', 'dom7'),
        ('M', 'P', None): ('', 'maj', 'maj'),
        ('m', 'P', 'm'): ('m7', 'm7', 'min7'),
        ('m', 'P', 'M'): ('mMaj7', 'mmaj7', 'minmaj7'),
        ('m', 'P', None): ('m', 'min', 'min'),
        ('m', 'd', 'm'): ('m7♭5', 'm7b5', 'halfdim'),
        ('m', 'd', None): ('°', 'dim', 'dim'),
        ('M', 'a', 'M'): ('maj7♯5', 'augmaj7', 'aug'),
        ('M', 'a', 'm'): ('7♯5', 'aug7', 'aug7'),
        ('M', 'a', None): ('+', 'aug', 'aug'),
        ('M', 'd', 'm'): ('7♭5', '7b5', 'dom7b5'),
        ('s4', 'P', 'm'): ('7sus4', '7sus4', 'dom7sus4'),
        ('s4', 'P', None): ('sus4', 'sus4', 'sus4'),
        ('s2', 'P', None): ('sus2', 'sus2', 'sus2'),
    }
    if third == 'm' and fifth == 'd' and 9 in s and 10 not in s and 11 not in s:
        return ('°7', 'dim7', 'dim7')
    return table.get((third, fifth, seventh)) or table.get((third, 'P', seventh)) \
        or table.get((third, fifth, None)) or ('', None, None)


def characteristic_degrees(ls, iv):
    """Degrés qui distinguent la gamme de sa référence (majeure si tierce
    majeure, mineure naturelle sinon). Vide si la gamme n'a pas 7 degrés."""
    if sorted(ls) != list(range(7)):
        return [], None
    ref = MAJOR_IV if 4 in iv else MINOR_IV
    ref_name = 'maj' if 4 in iv else 'min'
    form = degree_formula(ls, iv)
    return [(l, form[k]) for k, (l, i) in enumerate(zip(ls, iv)) if i != ref[l]], ref_name


PARENTS = [  # (id de gamme, intervalles, nom fr, nom en)
    ("major",        [0, 2, 4, 5, 7, 9, 11], "majeur",            "major"),
    ("melodic",      [0, 2, 3, 5, 7, 9, 11], "mineure mélodique",  "melodic minor"),
    ("harmonic",     [0, 2, 3, 5, 7, 8, 11], "mineure harmonique", "harmonic minor"),
    ("harmonic_maj", [0, 2, 4, 5, 7, 8, 11], "majeure harmonique", "harmonic major"),
    ("double_harm",  [0, 1, 4, 5, 7, 8, 11], "double harmonique",  "double harmonic"),
]


def parent_scale(root, scale):
    """Si la gamme est un mode d'une gamme mère, renvoie
    {id, degree, tonic (ASCII), pc, name_fr, name_en}. Sinon None."""
    iv = scale["iv"]
    if len(iv) != 7 or sorted(scale["ls"]) != list(range(7)):
        return None
    for pid, piv, nfr, nen in PARENTS:
        for k in range(1, 7):
            rot = sorted((x - piv[k]) % 12 for x in piv)
            if rot == iv:
                tonic = spell(root, (7 - k) % 7, (12 - piv[k]) % 12)
                return {"id": pid, "degree": k + 1, "tonic": tonic, "pc": pc_of(tonic),
                        "name_fr": nfr, "name_en": nen}
    return None


# ---------------------------------------------------------------------------
# MANCHE : position jouable + tablature
# ---------------------------------------------------------------------------
def tab_positions(open_midis, root_pc, offsets):
    """Une position jouable pour la suite de hauteurs root+offsets.
    Renvoie [(corde, case, midi)] (corde 0 = la plus grave)."""
    f0 = (root_pc - open_midis[0]) % 12
    s0 = 0
    if f0 > 7 and len(open_midis) > 1:           # trop haut sur la corde grave
        s0, f0 = 1, (root_pc - open_midis[1]) % 12
    start = open_midis[s0] + f0
    lo = max(0, f0 - 1)
    out, cur = [], s0
    for off in offsets:
        p = start + off
        pick = None
        for s in range(cur, len(open_midis)):     # dans la position
            f = p - open_midis[s]
            if lo <= f <= lo + 3:
                pick = (s, f); break
        if pick is None:                          # extension d'une case
            for s in range(cur, len(open_midis)):
                f = p - open_midis[s]
                if f == lo + 4 or (f == lo - 1 and f >= 0):
                    pick = (s, f); break
        if pick is None:                          # démanché sur la dernière corde utile
            for s in range(len(open_midis) - 1, cur - 1, -1):
                f = p - open_midis[s]
                if 0 <= f <= 22:
                    pick = (s, f); break
        if pick is None:
            break
        cur = pick[0]
        out.append((pick[0], pick[1], p))
    return out


def scale_offsets(iv, octaves=1):
    offs = []
    for o in range(octaves):
        offs += [i + 12 * o for i in iv]
    return offs + [12 * octaves]


def ascii_tab(positions, n_strings):
    names = STRING_NAMES[n_strings]
    lines = [names[s] + '|-' for s in range(n_strings)]
    for (s, f, _) in positions:
        w = len(str(f)) + 1
        for k in range(n_strings):
            lines[k] += (str(f) + '-') if k == s else '-' * w
    return '\n'.join(l + '|' for l in reversed(lines))


def fits_one_position(positions):
    fr = [f for (_, f, _) in positions if f > 0]
    return (max(fr) - min(fr) <= 4) if fr else True


def fretboard_svg(open_midis, labels, root_pc, title, n_frets=12):
    """Manche complet (cases 0 à n_frets) en SVG.
    labels : {hauteur (0-11): texte affiché dans la pastille}."""
    n = len(open_midis)
    L, T, FW, SH = 40, 22, 58, 28
    W = L + n_frets * FW + 16
    H = T + (n - 1) * SH + 34
    y = lambda s: T + (n - 1 - s) * SH          # corde aiguë en haut, comme une tablature
    xf = lambda f: L + f * FW
    p = [f'<svg class="fb" viewBox="0 0 {W} {H}" role="img" aria-label="{escape(title)}" '
         f'xmlns="http://www.w3.org/2000/svg"><title>{escape(title)}</title>']
    for f in (3, 5, 7, 9):
        if f <= n_frets:
            p.append(f'<circle cx="{xf(f) - FW / 2}" cy="{T + (n - 1) * SH / 2}" r="5" class="fb-in"/>')
    if n_frets >= 12:
        for dy in (-SH, SH):
            p.append(f'<circle cx="{xf(12) - FW / 2}" cy="{T + (n - 1) * SH / 2 + dy / (1 if n > 4 else 2)}" r="5" class="fb-in"/>')
    for f in range(n_frets + 1):
        p.append(f'<line x1="{xf(f)}" y1="{T}" x2="{xf(f)}" y2="{T + (n - 1) * SH}" class="{"fb-nut" if f == 0 else "fb-fret"}"/>')
        if f:
            p.append(f'<text x="{xf(f) - FW / 2}" y="{H - 6}" class="fb-num">{f}</text>')
    names = STRING_NAMES[n]
    for s in range(n):
        p.append(f'<line x1="{L}" y1="{y(s)}" x2="{xf(n_frets)}" y2="{y(s)}" class="fb-str" stroke-width="{1 + (n - 1 - s) * 0.35:.2f}"/>')
        p.append(f'<text x="6" y="{y(s) + 4}" class="fb-sn">{names[s]}</text>')
    for s in range(n):
        for f in range(n_frets + 1):
            pc = (open_midis[s] + f) % 12
            if pc not in labels:
                continue
            cx = L - 13 if f == 0 else xf(f) - FW / 2
            cls = 'fb-root' if pc == root_pc else 'fb-note'
            txt = labels[pc]
            p.append(f'<g class="{cls}"><circle cx="{cx}" cy="{y(s)}" r="11"/>'
                     f'<text x="{cx}" y="{y(s) + 3.5}" class="{"fb-t3" if len(txt) > 2 else "fb-t"}">{escape(txt)}</text></g>')
    p.append('</svg>')
    return Markup(''.join(p))


# ---------------------------------------------------------------------------
# GAMMES : contexte supplémentaire des pages
# ---------------------------------------------------------------------------
SECTION = {
    ('bass', 'fr'): ("fr/gammes", "fr/arpeges-basse", "à la basse", "gammes.html"),
    ('bass', 'en'): ("en/scales", "en/arpeggios-bass", "on bass", "gammes.html"),
    ('guitar', 'fr'): ("fr/gammes-guitare", "fr/arpeges-guitare", "à la guitare", "gammes-guitare.html"),
    ('guitar', 'en'): ("en/scales-guitar", "en/arpeggios-guitar", "on guitar", "gammes-guitare.html"),
}


def _root_slug(pc, lang):
    return ROOT_SLUGS[pc % 12][2 if lang == 'fr' else 3]


def ordinal(n, lang):
    if lang == 'fr':
        return f"{n}ᵉ" if n > 1 else "1ᵉʳ"
    return f"{n}{ {1: 'st', 2: 'nd', 3: 'rd'}.get(n, 'th') }"


def scale_extras(root, scale, lang, instrument, notes_raw, label):
    """Tout le contenu pédagogique ajouté aux pages de gammes."""
    fr = lang == 'fr'
    rname = root_ascii(root)
    rpc = root["pc"]
    rshow = show(rname, lang)
    iv, ls = scale["iv"], scale["ls"]
    slug_s = scale["id"].replace('_', '-')
    sec_scale, sec_arp, inst_txt, app = SECTION[(instrument, lang)]
    open_midis = BASS_OPEN if instrument == 'bass' else GUITAR_OPEN
    n_str = len(open_midis)
    formula = degree_formula(ls, iv)

    # Manche + tablature
    labels = {pc_of(n): show(n, lang) for n in notes_raw}
    name_full = (f"Gamme de {rshow} {label}" if fr else f"{rshow} {label} scale")
    fb = fretboard_svg(open_midis, labels, rpc,
                       f"{name_full} {inst_txt} : " + (
                           "toutes les notes sur le manche, cases 0 à 12" if fr
                           else "every note on the fretboard, frets 0 to 12"))
    octaves = 2 if instrument == 'guitar' else 1
    pos = tab_positions(open_midis, rpc, scale_offsets(iv, octaves))
    if octaves == 2 and (len(pos) < len(iv) * 2 + 1 or not fits_one_position(pos)):
        octaves = 1
        pos = tab_positions(open_midis, rpc, scale_offsets(iv, 1))
    tab = ascii_tab(pos, n_str)
    frets = [f for (_, f, _) in pos]
    lo_f, hi_f = min(frets), max(frets)
    if fr:
        tab_cap = (f"Une position pour monter la gamme sur {'une octave' if octaves == 1 else 'deux octaves'}"
                   f", cases {lo_f} à {hi_f}. Chaque chiffre est une case ; lis de gauche à droite.")
    else:
        tab_cap = (f"One position to play the scale over {'one octave' if octaves == 1 else 'two octaves'}"
                   f", frets {lo_f} to {hi_f}. Each number is a fret; read left to right.")

    # Accords de septième
    sevenths = build_sevenths(notes_raw, lang) if sorted(ls) == list(range(7)) else []

    # Accord de tonique + liens croisés
    sym, chord_id, arp_id = tonic_chord(iv)
    tonic_name = show(rname, lang) + sym
    links = []
    if arp_id:
        links.append({
            "href": f"{BASE_URL}/{sec_arp}/{_root_slug(rpc, lang)}/{arp_id}/",
            "text": (f"Arpège {tonic_name} {inst_txt}" if fr else f"{tonic_name} arpeggio {inst_txt}")})
    if chord_id:
        links.append({
            "href": f"{BASE_URL}/{'fr/accords-guitare' if fr else 'en/chords-guitar'}/{_root_slug(rpc, lang)}/{chord_id.replace('_', '-')}/",
            "text": (f"Accord {tonic_name} à la guitare" if fr else f"{tonic_name} guitar chord")})
    other = 'guitar' if instrument == 'bass' else 'bass'
    links.append({
        "href": f"{BASE_URL}/{SECTION[(other, lang)][0]}/{_root_slug(rpc, lang)}/{slug_s}/",
        "text": (f"Gamme de {rshow} {label} {SECTION[(other, lang)][2]}" if fr
                 else f"{rshow} {label} scale {SECTION[(other, lang)][2]}")})

    # Gamme mère
    par = parent_scale(rname, scale)
    parent = None
    if par:
        ptonic = show(par["tonic"], lang)
        href = f"{BASE_URL}/{sec_scale}/{_root_slug(par['pc'], lang)}/{par['id'].replace('_', '-')}/"
        if fr:
            txt = (f"{rshow} {label} est le {ordinal(par['degree'], 'fr')} mode de la gamme de "
                   f"{ptonic} {par['name_fr']} : ce sont exactement les mêmes notes, "
                   f"mais le centre de gravité est {rshow}.")
            link = f"Gamme de {ptonic} {par['name_fr']}"
        else:
            txt = (f"{rshow} {label} is the {ordinal(par['degree'], 'en')} mode of the "
                   f"{ptonic} {par['name_en']} scale: exactly the same notes, "
                   f"but {rshow} is the tonal centre.")
            link = f"{ptonic} {par['name_en']} scale"
        parent = {"text": txt, "href": href, "link": link}

    # Notes caractéristiques
    chars, ref = characteristic_degrees(ls, iv)
    char_txt = None
    if chars and len(chars) <= 3:
        items = ", ".join(f"{deg} ({show(notes_raw[k], lang)})"
                          for k, (l, deg) in enumerate(zip(ls, formula))
                          if (l, deg) in chars)
        if fr:
            char_txt = (f"Par rapport à la gamme {'majeure' if ref == 'maj' else 'mineure naturelle'} de {rshow}, "
                        f"ce qui change : {items}. Ce sont les notes à faire entendre pour que la couleur de la gamme ressorte.")
        else:
            char_txt = (f"Compared with {rshow} {'major' if ref == 'maj' else 'natural minor'}, "
                        f"what changes: {items}. These are the notes to bring out so the colour of the scale comes through.")

    # Comment travailler
    metro = f"{BASE_URL}/metronome.html" if fr else f"{BASE_URL}/en/metronome/"
    n = len(iv)
    if fr:
        steps = [
            Markup(f"Joue la gamme en montant puis en descendant, lentement, au <a href=\"{metro}\">métronome</a> "
                   f"(60 à la noire, une note par temps). Dis le nom de chaque note à voix haute."),
            ("Enchaîne par tierces (1-3, 2-4, 3-5…) puis par groupes de trois notes : c'est ce qui transforme une gamme en phrases."
             if n >= 7 else
             "Joue-la par groupes de trois notes (1-2-3, 2-3-4…) puis en sautant une note sur deux : tu sors du simple aller-retour."),
            (f"Joue l'arpège de {tonic_name} ({'fondamentale, tierce, quinte' + (', septième' if sym not in ('', 'm', '°', '+', 'sus2', 'sus4') else '')}), "
             f"puis reviens à la gamme en visant ces notes sur les temps forts."),
            (f"Improvise sur un accord de {tonic_name} tenu ou sur une note de {rshow} en boucle, "
             f"en insistant sur les notes caractéristiques." if char_txt else
             f"Improvise sur un accord de {tonic_name} tenu ou sur une note de {rshow} en boucle : "
             f"commence et termine tes phrases sur une note de l'accord."),
            "Change de tonique en suivant le cycle des quartes : la même forme se déplace telle quelle sur le manche.",
        ]
    else:
        steps = [
            Markup(f"Play the scale up and down slowly with a <a href=\"{metro}\">metronome</a> "
                   f"(60 bpm, one note per beat). Say each note name out loud."),
            ("Play it in thirds (1-3, 2-4, 3-5…) and then in three-note groups: this is what turns a scale into phrases."
             if n >= 7 else
             "Play it in three-note groups (1-2-3, 2-3-4…) and then skipping every other note, to break out of the up-and-down run."),
            (f"Play the {tonic_name} arpeggio ({'root, third, fifth' + (', seventh' if sym not in ('', 'm', '°', '+', 'sus2', 'sus4') else '')}), "
             f"then go back to the scale and land on those notes on the strong beats."),
            (f"Improvise over a sustained {tonic_name} chord or a looped {rshow} drone, "
             f"leaning on the characteristic notes." if char_txt else
             f"Improvise over a sustained {tonic_name} chord or a looped {rshow} drone: "
             f"start and end your phrases on a chord tone."),
            "Move to other keys around the cycle of fourths: the same shape slides along the neck unchanged.",
        ]

    ui = {
        "ui_formula": "Formule" if fr else "Formula",
        "ui_formula_hint": ("Chaque degré est comparé à la gamme majeure." if fr
                            else "Each degree is compared with the major scale."),
        "ui_fb_title": (f"{name_full} sur le manche de {'basse' if instrument == 'bass' else 'guitare'}" if fr
                        else f"{name_full} on the {'bass' if instrument == 'bass' else 'guitar'} fretboard"),
        "ui_fb_hint": ("La tonique est en couleur. Accordage standard, cases 0 à 12 ; au-delà de la 12ᵉ case le motif se répète."
                       if fr else
                       "The root is highlighted. Standard tuning, frets 0 to 12; past the 12th fret the pattern repeats."),
        "ui_tab_title": "Tablature" if fr else "Tab",
        "ui_listen": "Écouter la gamme" if fr else "Play the scale",
        "ui_sev_title": "Accords de septième de la gamme" if fr else "Seventh chords of the scale",
        "ui_tonic_title": "Sur quel accord la jouer" if fr else "Which chord to play it over",
        "ui_tonic_text": (
            f"L'accord construit sur la tonique est {tonic_name} : c'est sur lui que la gamme sonne le plus naturellement."
            if fr else
            f"The chord built on the root is {tonic_name}: this is where the scale sounds most at home."),
        "ui_practice_title": "Comment travailler cette gamme" if fr else "How to practise this scale",
        "ui_see_also": "À voir aussi" if fr else "See also",
        "ui_parent_title": "Gamme mère" if fr else "Parent scale",
    }
    ui.update({
        "formula": formula, "fretboard": fb, "tab": tab, "tab_caption": tab_cap,
        "play_midi": ",".join(str(m) for (_, _, m) in pos),
        "sevenths": sevenths, "tonic_name": tonic_name, "cross_links": links,
        "parent": parent, "char_text": char_txt, "practice": steps,
        "instrument": instrument,
    })
    return ui


# ---------------------------------------------------------------------------
# ARPÈGES : contexte supplémentaire
# ---------------------------------------------------------------------------
def arp_extras(root, arp, lang, instrument, name_full):
    fr = lang == 'fr'
    rname = root_ascii(root)
    rpc = root["pc"]
    iv = arp["iv"]
    notes = chord_spelling(rname, iv)
    roles = [r for r, _ in chord_roles(iv)]
    open_midis = BASS_OPEN if instrument == 'bass' else GUITAR_OPEN
    labels = {pc_of(n): show(n, lang) for n in notes}
    inst_fr = 'basse' if instrument == 'bass' else 'guitare'
    title = (f"Arpège {name_full} sur le manche de {inst_fr}, cases 0 à 12" if fr
             else f"{name_full} arpeggio on the {instrument} fretboard, frets 0 to 12")
    fb = fretboard_svg(open_midis, labels, rpc, title)
    offs = list(iv)
    top = 12 if max(iv) < 12 else 24
    if top not in offs:
        offs.append(top)
    if instrument == 'guitar' and max(iv) < 12:
        two = [i for i in iv] + [i + 12 for i in iv] + [24]
        p2 = tab_positions(open_midis, rpc, two)
        pos = p2 if len(p2) == len(two) and fits_one_position(p2) else tab_positions(open_midis, rpc, offs)
    else:
        pos = tab_positions(open_midis, rpc, offs)
    frets = [f for (_, f, _) in pos]
    if fr:
        cap = f"Une position jouable, cases {min(frets)} à {max(frets)}. Monte puis redescends, une note par temps."
        steps = [
            f"Repère d'abord la fondamentale ({show(rname, 'fr')}) partout sur le manche : c'est ton point d'ancrage.",
            "Joue l'arpège en montant et en descendant, lentement, en nommant le rôle de chaque note ("
            + ", ".join(roles) + ").",
            ("Sur une grille, change d'arpège à chaque accord en gardant la main dans la même zone : c'est la base d'une ligne de basse qui « suit » l'harmonie."
             if instrument == 'bass' else
             "Sur une grille, change d'arpège à chaque accord en gardant la main dans la même zone : tes solos suivront l'harmonie au lieu de rester dans une seule gamme."),
            "Ajoute des notes d'approche : un demi-ton sous chaque note de l'arpège, juste avant le temps.",
        ]
    else:
        cap = f"One playable position, frets {min(frets)} to {max(frets)}. Go up then back down, one note per beat."
        steps = [
            f"First find the root ({show(rname, 'en')}) all over the neck: it is your anchor.",
            "Play the arpeggio up and down slowly, naming the role of each note (" + ", ".join(roles) + ").",
            ("Over a chord chart, switch arpeggio on every chord while keeping your hand in the same area: this is the core of a bass line that follows the harmony."
             if instrument == 'bass' else
             "Over a chord chart, switch arpeggio on every chord while keeping your hand in the same area: your solos will follow the harmony instead of sitting in one scale."),
            "Add approach notes: a semitone below each arpeggio note, just before the beat.",
        ]
    return {
        "fretboard": fb, "tab": ascii_tab(pos, len(open_midis)), "tab_caption": cap,
        "play_midi": ",".join(str(m) for (_, _, m) in pos),
        "practice": steps,
        "ui_fb_title": (f"Arpège {name_full} sur le manche de {inst_fr}" if fr
                        else f"{name_full} arpeggio on the {instrument} fretboard"),
        "ui_fb_hint": ("La fondamentale est en couleur. Accordage standard, cases 0 à 12." if fr
                       else "The root is highlighted. Standard tuning, frets 0 to 12."),
        "ui_tab_title": "Tablature" if fr else "Tab",
        "ui_listen": "Écouter l'arpège" if fr else "Play the arpeggio",
        "ui_practice_title": "Comment travailler cet arpège" if fr else "How to practise this arpeggio",
    }


# ---------------------------------------------------------------------------
# ACCORDS DE GUITARE : positions vérifiées + diagrammes
# ---------------------------------------------------------------------------
DB_KEYS = ['C', 'Csharp', 'D', 'Eb', 'E', 'F', 'Fsharp', 'G', 'Ab', 'A', 'Bb', 'B']
ID_TO_SUFFIX = {
    'maj': 'major', 'min': 'minor', 'dim': 'dim', 'dim7': 'dim7', 'aug': 'aug', 'p5': '5',
    'sus2': 'sus2', 'sus4': 'sus4', '7sus4': '7sus4',
    '7': '7', 'maj7': 'maj7', 'm7': 'm7', 'mmaj7': 'mmaj7', 'm7b5': 'm7b5',
    'aug7': 'aug7', '7b5': '7b5', 'augmaj7': 'maj7#5',
    'add9': 'add9', 'madd9': 'madd9', '6': '6', 'm6': 'm6', '69': '69', 'm69': 'm69',
    '9': '9', 'maj9': 'maj9', 'm9': 'm9', 'm9maj7': 'mmaj9', '7b9': '7b9', '7s9': '7#9',
    '9s11': '9#11', '11': '11', 'maj11': 'maj11', 'm11': 'm11',
    '13': '13', 'maj13': 'maj13', '7alt': 'alt',
}


@lru_cache(maxsize=1)
def load_chords_db():
    src = (REPO_ROOT / "chords-db.js").read_text(encoding="utf-8")
    i = src.index('{', src.index('GUITAR_CHORDS_DB'))
    db, _ = json.JSONDecoder().raw_decode(src[i:])
    return db


def required_tones(iv):
    """Notes indispensables d'un accord. La quinte juste est facultative dès
    4 sons ; dans les accords de 11e et 13e, les extensions inférieures aussi."""
    s = [i % 12 for i in iv]
    req = set(s)
    if len(req) >= 4:
        req.discard(7)
    roles = dict(zip(s, [r for r, _ in chord_roles(iv)]))
    names = set(roles.values())
    if '13' in names:
        for m, r in roles.items():
            if r in ('9', '11'):
                req.discard(m)
    elif '11' in names and ('♭7' in names or '7' in names):
        for m, r in roles.items():
            if r == '9':
                req.discard(m)
        if 4 in req:            # la tierce majeure frotte avec la 11e : souvent omise
            req.discard(4)
    return req


def voicing_ok(frets_abs, root_pc, iv):
    """Position valide : uniquement des notes de l'accord, toutes les notes
    indispensables, fondamentale à la basse, jouable à quatre doigts."""
    notes = [(GUITAR_OPEN[s] + f) for s, f in enumerate(frets_abs) if f is not None]
    if len(notes) < min(3, len(set(i % 12 for i in iv)) + 1):
        return False
    pcs = {(n - root_pc) % 12 for n in notes}
    allowed = {i % 12 for i in iv}
    if not pcs <= allowed or not required_tones(iv) <= pcs:
        return False
    if min(notes) % 12 != root_pc % 12:
        return False
    fretted = [f for f in frets_abs if f]
    if fretted and max(fretted) - min(fretted) > 3:
        return False
    return fingers_needed(frets_abs) <= 4


def fingers_needed(frets_abs):
    fretted = [f for f in frets_abs if f]
    if not fretted:
        return 0
    lo = min(fretted)
    has_open = any(f == 0 for f in frets_abs)
    at_lo = [s for s, f in enumerate(frets_abs) if f == lo]
    others = sum(1 for f in fretted if f != lo)
    if not has_open and len(at_lo) >= 2:
        # barré possible si aucune corde plus aiguë que la première du barré n'est étouffée ou à vide
        if all(frets_abs[s] is not None for s in range(at_lo[0], 6)):
            return 1 + others
    return len(at_lo) + others


def find_voicings(root_pc, iv, limit=4):
    """Chercheur de secours : parcourt toutes les positions de 4 cases."""
    allowed = {i % 12 for i in iv}
    found = []
    for lo in range(0, 11):
        opts = []
        for s in range(6):
            o = [None]
            for f in ([0] if lo == 0 else []) + list(range(max(1, lo), max(1, lo) + 4)):
                if (GUITAR_OPEN[s] + f - root_pc) % 12 in allowed:
                    o.append(f)
            opts.append(o)
        def rec(s, cur):
            if s == 6:
                fa = tuple(cur)
                sounding = [k for k, f in enumerate(fa) if f is not None]
                if len(sounding) < 4 and len(allowed) > 2:
                    return
                if not sounding or sounding != list(range(sounding[0], sounding[-1] + 1)):
                    return
                if sounding[-1] < 4:
                    return
                if voicing_ok(list(fa), root_pc, iv):
                    found.append(fa)
                return
            for f in opts[s]:
                rec(s + 1, cur + [f])
        rec(0, [])
    def score(fa):
        notes = [GUITAR_OPEN[s] + f for s, f in enumerate(fa) if f is not None]
        pcs = {(n - root_pc) % 12 for n in notes}
        return (-(len(pcs)), fingers_needed(list(fa)), -len(notes), min(f for f in fa if f is not None))
    uniq = sorted(set(found), key=score)
    out, used = [], []
    for fa in uniq:
        lo = min([f for f in fa if f] or [0])
        if any(abs(lo - u) < 3 for u in used):
            continue
        used.append(lo); out.append(fa)
        if len(out) >= limit:
            break
    return sorted(out, key=lambda fa: min([f for f in fa if f] or [0]))


def chord_voicings(root_pc, chord, limit=5):
    """Positions affichées sur la page : base vérifiée, puis chercheur."""
    iv = chord["iv"]
    out, seen = [], set()
    suffix = ID_TO_SUFFIX.get(chord["id"])
    if suffix:
        entry = next((c for c in load_chords_db()["chords"][DB_KEYS[root_pc % 12]]
                      if c["suffix"] == suffix), None)
        for p in (entry or {}).get("positions", []):
            bf = p.get("baseFret", 1)
            fa = [None if f < 0 else (0 if f == 0 else f + bf - 1) for f in p["frets"]]
            if tuple(fa) in seen or not voicing_ok(fa, root_pc, iv):
                continue
            seen.add(tuple(fa))
            out.append({"frets": fa, "fingers": p.get("fingers")})
    if len(out) < 3:
        for fa in find_voicings(root_pc, iv):
            if fa not in seen:
                seen.add(fa)
                out.append({"frets": list(fa), "fingers": None})
    out.sort(key=lambda v: (min([f for f in v["frets"] if f] or [0]), sum(f is None for f in v["frets"])))
    return out[:limit]


def chord_svg(v, root_pc, names_by_pc, title):
    fa, fingers = v["frets"], v["fingers"]
    fretted = [f for f in fa if f]
    lo = min(fretted) if fretted else 1
    hi = max(fretted) if fretted else 1
    base = 1 if hi <= 4 else lo
    rows = 4 if hi - base < 4 else 5
    L, T, SW, FH = 30, 34, 24, 30
    W, H = L + 5 * SW + 40, T + rows * FH + 30
    x = lambda s: L + s * SW
    p = [f'<svg class="cd" viewBox="0 0 {W} {H}" role="img" aria-label="{escape(title)}" '
         f'xmlns="http://www.w3.org/2000/svg"><title>{escape(title)}</title>']
    for r in range(rows + 1):
        cls = 'cd-nut' if (r == 0 and base == 1) else 'cd-fret'
        p.append(f'<line x1="{L}" y1="{T + r * FH}" x2="{x(5)}" y2="{T + r * FH}" class="{cls}"/>')
    for s in range(6):
        p.append(f'<line x1="{x(s)}" y1="{T}" x2="{x(s)}" y2="{T + rows * FH}" class="cd-str"/>')
    if base > 1:
        p.append(f'<text x="{x(5) + 20}" y="{T + FH / 2 + 4}" class="cd-base">{base}</text>')
    # barré
    if fretted and not any(f == 0 for f in fa):
        at = [s for s, f in enumerate(fa) if f == lo]
        if len(at) >= 2 and all(fa[s] is not None for s in range(at[0], 6)):
            yb = T + (lo - base) * FH + FH / 2
            p.append(f'<rect x="{x(at[0]) - 8}" y="{yb - 8}" width="{x(5) - x(at[0]) + 16}" height="16" rx="8" class="cd-barre"/>')
    for s, f in enumerate(fa):
        if f is None:
            p.append(f'<text x="{x(s)}" y="{T - 10}" class="cd-mk">×</text>')
            continue
        pc = (GUITAR_OPEN[s] + f) % 12
        root = pc == root_pc % 12
        if f == 0:
            p.append(f'<circle cx="{x(s)}" cy="{T - 14}" r="5" class="{"cd-open cd-r" if root else "cd-open"}"/>')
        else:
            cy = T + (f - base) * FH + FH / 2
            p.append(f'<circle cx="{x(s)}" cy="{cy}" r="9" class="{"cd-dot cd-r" if root else "cd-dot"}"/>')
            if fingers and fingers[s]:
                p.append(f'<text x="{x(s)}" y="{cy + 3.5}" class="cd-fg">{fingers[s]}</text>')
        p.append(f'<text x="{x(s)}" y="{H - 8}" class="cd-nn">{escape(names_by_pc.get(pc, ""))}</text>')
    p.append('</svg>')
    return Markup(''.join(p))


def chord_extras(root, chord, lang, name_full):
    fr = lang == 'fr'
    rname = root_ascii(root)
    rpc = root["pc"]
    notes = chord_spelling(rname, chord["iv"])
    names = {pc_of(n): show(n, lang) for n in notes}
    diagrams = []
    for k, v in enumerate(chord_voicings(rpc, chord), 1):
        fa = v["frets"]
        fretted = [f for f in fa if f]
        lo = min(fretted) if fretted else 0
        _sep = "-" if any(f is not None and f >= 10 for f in fa) else ""
        code = _sep.join('x' if f is None else str(f) for f in fa)
        has_open = any(f == 0 for f in fa)
        barre = (not has_open and fretted and sum(1 for f in fa if f == lo) >= 2
                 and fingers_needed(fa) < len(fretted))
        if fr:
            kind = "position ouverte" if has_open else (f"barré case {lo}" if barre else f"case {lo}")
            title = f"Accord {name_full} à la guitare, {kind} ({code})"
        else:
            kind = "open position" if has_open else (f"barre at fret {lo}" if barre else f"fret {lo}")
            title = f"{name_full} guitar chord, {kind} ({code})"
        diagrams.append({"svg": chord_svg(v, rpc, names, title), "kind": kind, "code": code,
                         "midi": ",".join(str(GUITAR_OPEN[s] + f) for s, f in enumerate(fa) if f is not None)})
    if fr:
        steps = [
            "Pose les doigts un par un, de la corde grave vers l'aiguë, puis gratte corde par corde : chaque note doit sonner sans frise.",
            "Les cordes marquées × ne se jouent pas : étouffe-les avec le bord d'un doigt voisin ou évite-les à la main droite.",
            "Enchaîne avec l'accord précédent et le suivant de ton morceau, au métronome, en changeant sur le premier temps.",
            "Apprends au moins deux positions : une en bas du manche, une plus haut. Tu choisiras selon l'accord qui suit.",
        ]
    else:
        steps = [
            "Place your fingers one at a time from the low string to the high one, then pick string by string: every note should ring cleanly.",
            "Strings marked × are not played: mute them with the edge of a neighbouring finger or skip them with your picking hand.",
            "Practise the change from the previous chord and to the next chord of your song, with a metronome, landing on beat one.",
            "Learn at least two positions: one low on the neck, one higher up. You will pick whichever is closest to the next chord.",
        ]
    return {
        "diagrams": diagrams, "practice": steps,
        "ui_diag_title": (f"Positions de l'accord {name_full} à la guitare" if fr else f"{name_full} guitar chord positions"),
        "ui_diag_hint": ("× = corde non jouée, ○ = corde à vide, pastille colorée = fondamentale. "
                         "Le chiffre à droite indique la case de départ ; les chiffres dans les pastilles, les doigts."
                         if fr else
                         "× = string not played, ○ = open string, coloured dot = root. "
                         "The number on the right is the starting fret; numbers in the dots are fingers."),
        "ui_listen": "Écouter" if fr else "Play",
        "ui_practice_title": "Comment travailler cet accord" if fr else "How to practise this chord",
    }


# ---------------------------------------------------------------------------
# NAVIGATION COMMUNE DES PAGES GÉNÉRÉES
# ---------------------------------------------------------------------------
def site_nav(lang, instrument):
    fr = lang == 'fr'
    g = instrument == 'guitar'
    B = BASE_URL
    main = [
        ("Manche" if fr else "Fretboard", f"{B}/manche-guitare.html" if g else f"{B}/"),
        ("Gammes" if fr else "Scales", f"{B}/gammes-guitare.html" if g else f"{B}/gammes.html"),
        ("Arpèges" if fr else "Arpeggios", f"{B}/arpeges-guitare.html" if g else f"{B}/arpeges-basse.html"),
        ("Accords" if fr else "Chords", f"{B}/accords-guitare.html" if g else f"{B}/accords-basse.html"),
        ("Intervalles" if fr else "Intervals", f"{B}/intervalles-guitare.html" if g else f"{B}/intervalles.html"),
        ("Cadences" if fr else "Progressions", f"{B}/cadences-guitare.html" if g else f"{B}/cadences.html"),
    ]
    tools = [
        ("Métronome" if fr else "Metronome", f"{B}/metronome.html" if fr else f"{B}/en/metronome/"),
        ("Accordeur" if fr else "Tuner", f"{B}/accordeur.html" if fr else f"{B}/en/tuner/"),
        ("Grilles d'accords" if fr else "Chord charts", f"{B}/grilles.html" if fr else f"{B}/en/chord-charts/"),
        ("Notes du manche" if fr else "Fretboard trainer", f"{B}/notes-manche.html" if fr else f"{B}/en/fretboard-trainer/"),
        ("Oreille" if fr else "Ear training", f"{B}/oreille.html" if fr else f"{B}/en/ear-training/"),
    ]
    sections = [
        ("Gammes de basse" if fr else "Bass scales", f"{B}/fr/gammes/" if fr else f"{B}/en/scales/"),
        ("Gammes de guitare" if fr else "Guitar scales", f"{B}/fr/gammes-guitare/" if fr else f"{B}/en/scales-guitar/"),
        ("Arpèges de basse" if fr else "Bass arpeggios", f"{B}/fr/arpeges-basse/" if fr else f"{B}/en/arpeggios-bass/"),
        ("Arpèges de guitare" if fr else "Guitar arpeggios", f"{B}/fr/arpeges-guitare/" if fr else f"{B}/en/arpeggios-guitar/"),
        ("Accords de guitare" if fr else "Guitar chords", f"{B}/fr/accords-guitare/" if fr else f"{B}/en/chords-guitar/"),
    ]
    return {"nav_main": main, "nav_tools": tools, "nav_sections": sections,
            "ui_tools": "Outils" if fr else "Tools",
            "ui_brand": "ScalaSix" if g else "ScalaBass",
            "ui_footer": ("Gratuit, sans inscription. Théorie musicale pour bassistes et guitaristes."
                          if fr else "Free, no sign-up. Music theory for bass players and guitarists."),
            "og_image": f"{B}/og-image.png"}


def breadcrumb_ld(items):
    """items : [(nom, url)] → JSON-LD BreadcrumbList."""
    return Markup(json.dumps({
        "@context": "https://schema.org", "@type": "BreadcrumbList",
        "itemListElement": [{"@type": "ListItem", "position": k, "name": n, "item": u}
                            for k, (n, u) in enumerate(items, 1)]}, ensure_ascii=False))


def sitemap_lines(urls, lastmod):
    return [f'  <url><loc>{u}</loc><lastmod>{lastmod}</lastmod></url>' for u in urls]
