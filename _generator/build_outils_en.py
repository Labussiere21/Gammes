#!/usr/bin/env python3
"""build_outils_en.py — SEO des 3 outils (métronome, accordeur, grilles).

À lancer depuis la racine du site après chaque modification d'une page outil :
    python _generator/build_outils_en.py

1. Met à jour le <head> des pages FR (title, description, canonical, hreflang,
   Open Graph, Twitter, JSON-LD).
2. Génère les versions anglaises : en/metronome/, en/tuner/, en/chord-charts/
   (copie de la page FR, <head> anglais, textes [data-en] déjà en anglais dans
   le HTML, langue forcée sur EN).
Le script est idempotent : on peut le relancer autant de fois que nécessaire.
"""
import html, os, re, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = 'https://scalabass.com'
OG_IMG = SITE + '/og-image.png'

TOOLS = [
  dict(fr='metronome.html', en='en/metronome/',
    t_fr="Métronome en ligne gratuit avec groove basse et batterie | ScalaBass",
    d_fr="Métronome gratuit pour bassistes et guitaristes : tap tempo, mesures, accents, subdivisions, figures rythmiques (syncope, croche pointée…), swing, entraîneur de tempo et groove avec batterie et basse calées sur le tempo.",
    k_fr="métronome en ligne, métronome gratuit, métronome basse, métronome guitare, tap tempo, figures rythmiques, syncope, croche pointée, groove basse, batterie virtuelle",
    n_fr="Métronome et groove ScalaBass", b_fr="Métronome",
    t_en="Free online metronome with bass & drum groove | ScalaBass",
    d_en="Free online metronome for bass and guitar players: tap tempo, time signatures, accents, subdivisions, rhythmic figures (syncopation, dotted eighths…), swing, speed trainer and a groove with drums and bass locked to the tempo.",
    k_en="online metronome, free metronome, bass metronome, guitar metronome, tap tempo, rhythmic figures, syncopation, dotted eighth, bass groove, drum machine",
    n_en="ScalaBass metronome and groove", b_en="Metronome",
    req="Requires JavaScript and Web Audio"),
  dict(fr='accordeur.html', en='en/tuner/',
    t_fr="Accordeur basse et guitare en ligne gratuit (micro) | ScalaBass",
    d_fr="Accordeur chromatique gratuit pour basse (4, 5, 6 cordes) et guitare : détection automatique par le micro, accordages prédéfinis (drop D, DADGAD, open G…), note de référence réglable.",
    k_fr="accordeur basse, accordeur guitare, accordeur en ligne, accordeur chromatique, accordage basse 5 cordes, drop D, DADGAD",
    n_fr="Accordeur basse et guitare ScalaBass", b_fr="Accordeur",
    t_en="Free online bass and guitar tuner (microphone) | ScalaBass",
    d_en="Free chromatic tuner for bass (4, 5 and 6 strings) and guitar using your microphone: automatic mode, preset tunings (Drop D, DADGAD, Open G…) and adjustable A4 reference.",
    k_en="bass tuner, guitar tuner, online tuner, chromatic tuner, 5 string bass tuning, drop D, DADGAD, microphone tuner",
    n_en="ScalaBass bass and guitar tuner", b_en="Tuner",
    req="Requires JavaScript and a microphone"),
  dict(fr='grilles.html', en='en/chord-charts/',
    t_fr="Générateur de grilles d'accords gratuit (export PDF) | ScalaBass",
    d_fr="Crée tes grilles d'accords : reprises, cases 1 et 2, structure du morceau (couplets, refrains, solo…) et export PDF paysage ou portrait. Gratuit, sans compte, tes morceaux restent sur ton appareil.",
    k_fr="grille d'accords, générateur de grille, grille accords PDF, structure morceau, reprises, grille basse, grille guitare",
    n_fr="Générateur de grilles d'accords ScalaBass", b_fr="Grilles d'accords",
    t_en="Free chord chart maker (PDF export) | ScalaBass",
    d_en="Create chord charts online: repeats, 1st and 2nd endings, song structure (verse, chorus, solo…) and landscape or portrait PDF export. Free, no account, your songs stay on your device.",
    k_en="chord chart maker, chord chart generator, chord chart PDF, song structure, lead sheet, bass chord chart, guitar chord chart",
    n_en="ScalaBass chord chart maker", b_en="Chord charts",
    req="Requires JavaScript"),
]

A = lambda s: html.escape(s, quote=True)

def head_block(t, lang):
    fr_url, en_url = SITE + '/' + t['fr'], SITE + '/' + t['en']
    url = fr_url if lang == 'fr' else en_url
    T, D, K, N, B = (t[x + '_' + lang] for x in 'tdknb')
    ld = [{
        "@context": "https://schema.org", "@type": "WebApplication", "name": N, "url": url,
        "description": D, "applicationCategory": "MusicApplication", "operatingSystem": "Any",
        "browserRequirements": t['req'], "isAccessibleForFree": True, "inLanguage": lang,
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "EUR"},
        "publisher": {"@type": "Organization", "name": "ScalaBass", "url": SITE + '/'},
    }, {
        "@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "ScalaBass", "item": SITE + '/'},
            {"@type": "ListItem", "position": 2, "name": B, "item": url}],
    }]
    return '\n'.join([
        f'<title data-fr="{A(t["t_fr"])}">{html.escape(T)}</title>',
        f'<meta name="description" content="{A(D)}">',
        f'<meta name="keywords" content="{A(K)}">',
        f'<link rel="canonical" href="{url}">',
        f'<link rel="alternate" hreflang="fr" href="{fr_url}">',
        f'<link rel="alternate" hreflang="en" href="{en_url}">',
        f'<link rel="alternate" hreflang="x-default" href="{fr_url}">',
        '<meta property="og:type" content="website">',
        f'<meta property="og:site_name" content="ScalaBass">',
        f'<meta property="og:title" content="{A(T)}">',
        f'<meta property="og:description" content="{A(D)}">',
        f'<meta property="og:url" content="{url}">',
        f'<meta property="og:image" content="{OG_IMG}">',
        f'<meta property="og:locale" content="{"fr_FR" if lang == "fr" else "en_US"}">',
        f'<meta property="og:locale:alternate" content="{"en_US" if lang == "fr" else "fr_FR"}">',
        '<meta name="twitter:card" content="summary_large_image">',
        f'<meta name="twitter:title" content="{A(T)}">',
        f'<meta name="twitter:description" content="{A(D)}">',
        f'<meta name="twitter:image" content="{OG_IMG}">',
        '<script type="application/ld+json">',
        json.dumps(ld, ensure_ascii=False),
        '</script>',
    ])

SEO_RE = re.compile(r'<title[^>]*>.*?</title>.*?<script type="application/ld\+json">.*?</script>', re.S)
# lignes SEO entre <title> et le JSON-LD : on garde tout le reste (polices, CSS…)
KEEP_RE = re.compile(r'<link\b(?![^>]*rel="(?:canonical|alternate)")[^>]*>')
FORCE_RE = re.compile(r'<script data-sb-lang>.*?</script>\n?', re.S)

def rewrite_head(src, t, lang):
    m = SEO_RE.search(src)
    if not m:
        raise SystemExit('bloc SEO introuvable dans ' + t['fr'])
    kept = '\n'.join(KEEP_RE.findall(m.group(0)))
    src = src[:m.start()] + head_block(t, lang) + '\n' + kept + src[m.end():]
    # l'URL fixe la langue de la page
    src = FORCE_RE.sub('', src)
    src = src.replace('<meta charset="UTF-8">',
        '<meta charset="UTF-8">\n<script data-sb-lang>try{localStorage.setItem(\'sblang\',\'%s\')}catch(e){}</script>' % lang, 1)
    return src

DATA_EN_RE = re.compile(r'<(p|h1|h2|h3|span|small|summary|li)\b([^>]*?)\sdata-en="([^"]*)"([^>]*)>(.*?)</\1>', re.S)

def to_en(src, t):
    src = rewrite_head(src, t, 'en')
    src = src.replace('<html lang="fr">', '<html lang="en">', 1)
    # les ressources sont en chemins relatifs à la racine
    src = src.replace('<meta charset="UTF-8">', '<meta charset="UTF-8">\n<base href="/">', 1)
    def sw(m):
        tag, a1, en, a2, fr = m.groups()
        if 'data-fr=' in a1 + a2:
            return m.group(0)
        return f'<{tag}{a1} data-en="{en}" data-fr="{A(fr)}"{a2}>{html.unescape(en)}</{tag}>'
    return DATA_EN_RE.sub(sw, src)

def main():
    for t in TOOLS:
        p = os.path.join(ROOT, t['fr'])
        src = open(p, encoding='utf-8').read()
        fr = rewrite_head(src, t, 'fr')
        open(p, 'w', encoding='utf-8', newline='\n').write(fr)
        out = os.path.join(ROOT, t['en'], 'index.html')
        os.makedirs(os.path.dirname(out), exist_ok=True)
        open(out, 'w', encoding='utf-8', newline='\n').write(to_en(fr, t))
        print('ok', t['fr'], '->', t['en'])

if __name__ == '__main__':
    main()
