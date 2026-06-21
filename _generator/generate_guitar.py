#!/usr/bin/env python3
"""
ScalaBass — Générateur de pages statiques SEO — Guitare
========================================================
Génère fr/gammes-guitare/{note}/{gamme}/index.html  (72 gammes × 17 toniques = ~1224 pages FR)
Génère en/scales-guitar/{note}/{gamme}/index.html   (72 gammes × 17 toniques = ~1224 pages EN)
Génère fr/gammes-guitare/index.html (hub FR)
Génère en/scales-guitar/index.html  (hub EN)
Met à jour sitemap.xml (sans toucher aux pages basse)

Lancer depuis la racine du repo :
    pip install -r _generator/requirements.txt
    python _generator/generate_guitar.py
"""

import os, re, sys
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

# Importe les données et fonctions partagées depuis generate.py
sys.path.insert(0, str(Path(__file__).parent))
from generate import (
    ROOTS, ENHARMONIC_ROOTS, SCALE_DEFS,
    build_scale, build_triads, fr_note, pretty,
    interval_str, scale_slug, pc_of,
)

# ---------------------------------------------------------------------------
# CONFIG GUITARE
# ---------------------------------------------------------------------------
REPO_ROOT    = Path(__file__).parent.parent
OUT_ROOT_FR  = REPO_ROOT / "fr" / "gammes-guitare"
OUT_ROOT_EN  = REPO_ROOT / "en" / "scales-guitar"
TMPL_DIR     = Path(__file__).parent / "templates"
BASE_URL     = "https://labussiere21.github.io/Gammes"
APP_URL      = f"{BASE_URL}/gammes-guitare.html"

# ---------------------------------------------------------------------------
# DESCRIPTIONS GUITARE — FRANÇAIS
# ---------------------------------------------------------------------------
SCALE_DESCS_GUITAR_FR = {
    "major":
        "La gamme majeure est le fondement de la guitare tonale. Du rock à la pop en passant par la country et le jazz, elle est présente partout. Sur le manche, elle s'apprend via le système CAGED qui permet de la jouer dans cinq positions différentes sur les 6 cordes. Maîtriser la gamme majeure à la guitare, c'est comprendre l'harmonie dans toutes les tonalités.",
    "minor":
        "La gamme mineure naturelle est la gamme rock et métal par excellence à la guitare. Ses positions sur le manche forment des boîtes facilement utilisables pour l'improvisation. Eddie Van Halen, Slash, Angus Young — tous construisent leurs solos à partir de cette gamme. Sa couleur sombre et directe convient parfaitement aux riffs en palm mute et aux solos mélodiques.",
    "harmonic":
        "La gamme mineure harmonique donne à la guitare un son dramatique et orientalisant immédiatement reconnaissable. Sa seconde augmentée (T+½T) entre le 6e et le 7e degré crée un saut caractéristique que l'on retrouve dans le flamenco, le métal néoclassique (Yngwie Malmsteen) et la musique de film. Elle sonne magistralement sur les progressions i–V dans toutes les tonalités mineures.",
    "melodic":
        "La gamme mineure mélodique (ascendante) est incontournable dans le jazz guitare. Elle produit les gammes altérées, lydien dominant et locrien #2 par simple rotation. Joe Pass, Pat Metheny, Mike Stern — tous exploitent ses couleurs sur les ii-V-I mineurs. Son 6e et 7e degrés naturels permettent des lignes mélodiques très fluides sur les accords minMaj7.",
    "dorian":
        "Le mode dorien est LA gamme du blues-rock et du funk à la guitare. Sa 6te majeure lui donne une ouverture lumineuse dans un contexte mineur. Carlos Santana, David Gilmour et John Mayer l'utilisent constamment. Il sonne parfaitement sur les progressions i–IV typiques du blues modal, et ses positions se superposent naturellement à la pentatonique mineure.",
    "phrygian":
        "Le mode phrygien définit le son du métal progressif, du flamenco et de la guitare orientale. Sa 2nde mineure crée une tension immédiate dès la première note. Tom Morello, Kirk Hammett et les guitaristes de flamenco en font leur couleur principale. Dans le métal, il structure les riffs les plus sombres ; dans le flamenco, il définit l'âme des falsetas.",
    "lydian":
        "Le mode lydien avec sa 4te augmentée sonne rêveur et éthéré à la guitare. Steve Vai et Joe Satriani l'ont élevé au rang de signature sonore dans la fusion et le rock instrumental. Il sonne parfaitement sur les accords Maj7#11 et crée des atmosphères flottantes très utilisées dans la musique de film. Sur le manche, sa #4 est facile à repérer par rapport à la gamme majeure standard.",
    "mixolydian":
        "Le mode mixolydien est le son du rock, du blues et de la country à la guitare. Sa b7 sur fond majoreur lui donne la chaleur du blues sans l'obscurité du mineur. Les riffs de Brown Sugar (Rolling Stones), Sweet Home Alabama (Lynyrd Skynyrd) et Born to Run (Springsteen) en découlent directement. Sur les accords dominants, il est l'outil de référence des guitaristes de blues et de rock.",
    "locrian":
        "Le mode locrien, avec sa 5te diminuée, est rarement utilisé à l'état pur à la guitare. On le trouve principalement dans le métal extrême (pour les riffs sur accord iiø) et dans l'improvisation jazz sur les accords demi-diminués. Son instabilité inhérente peut être exploitée de façon créative dans les passages de transition vers une résolution tonale.",
    "penta_min":
        "La pentatonique mineure est la gamme de guitare la plus jouée au monde. Jimmy Page, Eric Clapton, Jimi Hendrix, BB King — tous ont bâti leur carrière sur ces 5 notes. Ses cinq positions (boîtes CAGED) couvrent tout le manche et permettent d'improviser immédiatement sur n'importe quel blues ou rock. C'est la première gamme à apprendre absolument à la guitare.",
    "penta_maj":
        "La pentatonique majeure est la version lumineuse et country de la pentatonique. Mark Knopfler, Keith Richards et les guitaristes de country l'utilisent constamment pour des lignes chantantes et mélodiques. Elle sonne naturellement sur les progressions majeures I–IV–V et permet des bends et hammer-ons très expressifs. Le passage entre pentatonique mineure et majeure est l'une des techniques clés du blues-rock.",
    "blues_min":
        "La gamme blues mineure est l'âme de la guitare électrique. Sa blue note (b5) entre la quarte et la quinte parfaite crée cette tension expressif propre au blues. SRV, BB King, Buddy Guy — tous l'exploitent à travers des bends, des vibratos et des slides. Sur le manche, la blue note est facilement accessible depuis la boîte 1 de la pentatonique mineure.",
    "blues_maj":
        "La gamme blues majeure mélange la chaleur de la pentatonique majeure avec l'ambiguïté de la tierce mineure. C'est le son du rock'n'roll originel — Chuck Berry, Elvis, Carl Perkins. Elle sonne parfaitement sur les progressions I7–IV7–V7 du blues. Les guitaristes de country l'utilisent aussi pour donner un petit côté 'sale' aux lignes en double cordes.",
    "penta_dom":
        "La pentatonique dominante (avec b7) est parfaitement adaptée aux accords de septième et au blues. Elle sonne sur les dominantes I7, IV7 et V7 du blues sans fausse note. Très utilisée dans le blues-rock, le funk et le rhythm'n'blues à la guitare, elle permet des phrases expressives sur toutes les positions du manche.",
    "penta_min6":
        "La pentatonique mineure 6 introduit la sixte majeure dans un contexte mineur, ce qui crée une couleur jazz très caractéristique. À la guitare, elle sonne parfaitement sur les accords mineurs 6 et permet des voicings ouverts très raffinés. Très utilisée dans le jazz manouche et le jazz guitare pour donner de la couleur aux phrases mineures.",
    "penta_sus":
        "La pentatonique sus (sans tierce définie) crée des atmosphères flottantes et ambiguës à la guitare. Elle est très prisée dans la musique de John Scofield, Pat Metheny et les guitaristes de jazz-fusion pour improviser sur les accords sus4 et add9. Sur le manche, ses positions se superposent facilement aux formes de la pentatonique majeure.",
    "blues_dom":
        "La gamme blues dominante enrichit la pentatonique dominante avec le triton. Elle sonne avec une tension maximale sur les accords V7 altérés et les dominantes substitution tritonique. Les guitaristes de jazz-blues (Robben Ford, Larry Carlton) l'utilisent pour créer des tensions expressives avant la résolution.",
    "blues_hex":
        "La gamme blues hexatonique enrichit la pentatonique mineure avec la 2nde majeure, ajoutant une couleur dorian. Elle est très populaire dans le blues-rock moderne et l'alternative rock pour des lignes plus sophistiquées que la pentatonique pure, tout en restant accessible sur le manche.",
    "penta_maj7":
        "La pentatonique majeure 7 remplace la 7ème mineure habituelle par la 7ème majeure, donnant une couleur jazz douce et élégante. À la guitare, elle sonne parfaitement sur les accords Maj7 et CMaj9. Les guitaristes de jazz (Pat Metheny, Lenny Breau) l'utilisent pour des phrases fluides et raffinées sur les accords majeurs avec septième.",
    "penta_min_lead":
        "La pentatonique mineure avec note de guidage (7ème majeure) est très utilisée en jazz et en fusion à la guitare. Cette 7ème naturelle crée une forte attraction vers la tonique, parfaite pour ponctuer les fins de phrases avec caractère. Elle enrichit la pentatonique mineure classique sans en changer la structure fondamentale.",
    "boogie":
        "La gamme Rock'n'Roll / Boogie capture l'essence du shuffle et du boogie-woogie à la guitare. Les patterns en double cordes caractéristiques du boogie (alternance fondamentale–5te avec passages chromatiques) dérivent directement de cette gamme. Présente dans tout le rock'n'roll originel, du rockabilly jusqu'au rock classique des années 70.",
    "penta_majb2":
        "La pentatonique majeure b2 mélange une couleur pentatonique familière avec l'exotisme de la 2nde mineure. À la guitare, elle crée des phrases à mi-chemin entre le monde oriental et le langage pentatonique occidental. Utilisée par certains guitaristes de world-fusion pour des couleurs inattendues.",
    "dim":
        "La gamme diminuée T-½T est une gamme symétrique de 8 notes très utilisée dans le jazz et le métal à la guitare. Sa périodicité de 3 demi-tons signifie que ses positions se répètent toutes les 3 cases. Les guitaristes de jazz l'utilisent sur les accords dim7 et les dominantes b9, tandis que les guitaristes de métal exploitent sa symétrie pour des runs rapides très caractéristiques.",
    "dim_ht":
        "La gamme diminuée ½T-T (half-whole) est très utilisée dans le jazz et le bebop sur les accords dominants b9. Son demi-ton initial lui donne un caractère encore plus tendu. Les guitaristes de jazz comme John Scofield et Pat Martino l'exploitent sur les V7b9 pour des phrases très expressives.",
    "half_dim":
        "La gamme demi-diminuée (= Locrien) s'utilise sur les accords iiø7 dans les cadences jazz ii-V-i en mineur. À la guitare, elle est présente dans les progressions de jazz standard (Autumn Leaves, All The Things You Are). Sa b5 crée une tension qui demande immédiatement résolution vers la dominante.",
    "whole_tone":
        "La gamme par ton est entièrement symétrique — seulement deux versions pour les 12 toniques. À la guitare, ses positions sont très régulières et faciles à visualiser. Trey Anastasio (Phish) et Frank Zappa l'exploitent pour des effets flottants et onirique. Elle sonne parfaitement sur les accords augmentés et les dominantes #5.",
    "aug_hex":
        "La gamme hexatonique augmentée est basée sur deux triades augmentées et crée des couleurs très colorées. À la guitare, ses positions symétriques permettent des passages techniques très impressionnants. Utilisée dans le jazz moderne et la composition contemporaine pour des effets de couleur inhabituels.",
    "chromatic":
        "La gamme chromatique (12 demi-tons) est indispensable pour les passages de transition à la guitare. Les approches chromatiques (encadrements) sont une technique fondamentale du jazz et du blues. Allan Holdsworth a construit tout un langage autour des runs chromatiques. Sur le manche, elle permet de relier n'importe quelle position en passant par toutes les cases.",
    "phryg_dom":
        "Le phrygien dominant est le son du flamenco et du métal néoclassique à la guitare. Paco de Lucía, Yngwie Malmsteen et les guitaristes de métal progressif en ont fait leur signature. Sa 2nde mineure et sa tierce majeure créent une tension dramatique immédiate. Dans le flamenco, il structure les falsetas les plus expressives ; dans le métal, il produit les riffs les plus sombres et dramatiques.",
    "lydian_dom":
        "Le lydien dominant (lydien avec b7) est une couleur jazz-fusion par excellence à la guitare. Scott Henderson, John McLaughlin et Frank Zappa l'exploitent sur les accords V7#11 et les substitutions tritoniques. Sa #4 et sa b7 lui donnent à la fois la luminosité du lydien et la tension du mixolydien.",
    "altered":
        "La gamme altérée (superlocrien) contient toutes les tensions altérées : b9, #9, b5, #5. À la guitare, c'est la gamme des résolutions V7alt→i les plus expressives du jazz. John Scofield, Pat Metheny et Mike Stern l'utilisent sur les dominantes altérées pour créer une tension maximale avant la résolution en mineur.",
    "locrian_s2":
        "Le locrien #2 est plus stable que le locrien standard grâce à sa 2nde majeure. À la guitare, il s'utilise sur les accords iiø7 dans les cadences ii-V-i en mineur. Sa 2nde naturelle permet des phrases plus fluides que le locrien pur tout en maintenant l'ambiguïté du b5 caractéristique.",
    "lydian_aug":
        "Le lydien augmenté combine #4 et #5, créant un son très coloré et dissonant. À la guitare, il sonne sur les accords Maj7#5 dans les progressions chromatiques jazz. Sa double altération le rend complexe mais très expressif pour les guitaristes de jazz contemporain cherchant des couleurs inhabituelles.",
    "mixo_b6":
        "Le mixolydien b6 mélange chaleur du mixolydien et obscurité mineure. À la guitare, il crée des atmosphères mystérieuses sur les accords dominants. Utilisé dans le jazz et les musiques de film, il offre une alternative colorée au mixolydien standard pour les V7 avec couleur modal.",
    "dorian_b2":
        "Le dorien b2 (= phrygien #6) mélange la 2nde mineure du phrygien avec l'ouverture de la 6te majeure dorienne. À la guitare, il crée des couleurs inattendues et sophistiquées sur les accords mineurs. Utilisé dans le jazz modal et la fusion pour des phrases qui surprennent l'oreille habitée aux modes standards.",
    "locrian6":
        "Le locrien nat.6 adoucit l'instabilité du locrien grâce à sa 6te majeure naturelle. À la guitare, certains jazzmen préfèrent ce mode pour improviser sur les accords iiø7, sa 6te naturelle permettant des mouvements mélodiques moins tendus que le locrien pur tout en maintenant l'atmosphère du mode.",
    "ionian_s5":
        "L'ionien #5 est un mode majeur avec une 5te augmentée qui crée une tension inhabituelle. À la guitare, il sonne sur les accords augmentés Maj7#5 et permet des phrases qui déjouent l'oreille habituée au son ionien standard. Sa #5 crée une couleur très reconnaissable dans les progressions chromatiques.",
    "dorian_s4":
        "Le dorien #4 (mineure roumaine) combine la couleur du dorien avec une 4te augmentée très expressive. À la guitare, il est présent dans les musiques de l'Europe de l'Est, le jazz modal et certains styles de métal progressif. Sa #4 lui donne un caractère à la fois familier (dorien) et exotique (seconde augmentée).",
    "lydian_s2":
        "Le lydien #2 est l'un des modes les plus exotiques de la mineure harmonique. Avec sa 2nde augmentée ET sa 4te augmentée, il crée des couleurs très caractéristiques à la guitare. Utilisé dans les musiques d'Europe orientale et dans le jazz expérimental pour des phrases musicalement insolites.",
    "superlocrian_bb7":
        "Le super locrien bb7 est extrêmement rare à la guitare — sa double bémol 7 en fait un mode théorique utilisé dans les contextes jazz les plus avancés. Il est enseigné dans les conservatoires de jazz comme cas limite de la théorie modale de la mineure harmonique.",
    "bebop_maj":
        "La gamme bebop majeure ajoute une 5te augmentée chromatique entre la 5te et la 6te. À la guitare, ce 8e degré de passage permet de créer des phrases bebop fluides avec les notes mélodiques sur les temps forts. Charlie Christian et Wes Montgomery ont jeté les bases de ce langage qui reste incontournable dans le jazz guitare.",
    "bebop_dom":
        "La gamme bebop dominante est la gamme mixolydienne avec une 7ème majeure de passage. À la guitare, elle permet des phrases de type bebop très fluides sur les accords dominants. Charlie Christian, Joe Pass et Pat Martino l'utilisent pour structurer leurs lignes avec une logique harmonique impeccable.",
    "bebop_min":
        "La gamme bebop mineure ajoute une tierce majeure de passage entre la tierce mineure et la quarte. À la guitare, elle permet des phrases bebop expressives sur les accords mineurs. Utilisée dans le jazz classique et le bebop pour des lignes mélodiques qui coulent naturellement sur les temps.",
    "double_harm":
        "La gamme double harmonique (byzantine, tsigane) est caractérisée par ses deux secondes augmentées très expressives. À la guitare, elle est présente dans le flamenco avancé, les musiques des Balkans et le métal progressif (Guthrie Govan). Ses intervalles larges la rendent techniquement exigeante mais l'effet sonore est immédiatement saisissant.",
    "hung_min":
        "La gamme mineure hongroise (Gypsy minor) est au cœur du jazz manouche à la guitare. Django Reinhardt et ses successeurs (Stochelo Rosenberg, Biréli Lagrène) l'exploitent constamment dans le style manouche parisien. Sa #4 et sa b6 lui donnent ce caractère dramatique et romanesque si caractéristique.",
    "hung_maj":
        "La gamme majeure hongroise avec sa 3ce mineure inhabituelle crée un son exotique dans un contexte majeur. À la guitare, elle est utilisée dans les musiques folk d'Europe centrale et dans le jazz expérimental pour créer des couleurs inattendues sur des progressions majeures.",
    "gypsy_maj":
        "La gamme tzigane majeure (Gypsy major) est présente dans le jazz manouche et les musiques romani. Django Reinhardt et les guitaristes de style manouche l'exploitent pour des phrases très expressives avec des bends et ornements caractéristiques. Sa b2 et sa #4 lui donnent un caractère immédiatement reconnaissable.",
    "romanian_min":
        "La gamme mineure roumaine est un dorien avec une 4te augmentée qui crée un son folk d'Europe de l'Est très distinctif à la guitare. Elle est utilisée dans les musiques traditionnelles roumaines, grecques et turques, ainsi que dans le jazz manouche et la world-fusion pour des couleurs insolites.",
    "persian":
        "La gamme persane est l'une des plus dissonantes pour la guitare. Avec sa b2, #3 et b5, elle crée des tensions inhabituelles très exploitées dans la musique expérimentale et le métal d'avant-garde. Sa structure théorique complexe la rend difficile à intégrer mais intéressante pour des effets de couleur extrêmes.",
    "arabic":
        "La gamme arabe est une variante de la gamme par ton qui capture certaines couleurs de la musique orientale. À la guitare, elle est utilisée dans la world-fusion et le jazz pour créer des ambiances du Moyen-Orient. Ses positions sur le manche sont relativement accessibles grâce à sa symétrie partielle.",
    "enigmatic":
        "La gamme énigmatique de Verdi est une construction théorique aux harmonies très complexes. À la guitare, elle crée des ambiances très insolites difficiles à ancrer dans un contexte tonal standard. Certains compositeurs de rock progressif et de metal avant-gardiste l'exploitent pour son caractère imprévisible et désorienta.",
    "napolitaine_maj":
        "La gamme napolitaine majeure (majeure avec b2) donne à la guitare un caractère sombre et expressif inhabituel pour un contexte majeur. Elle est utilisée dans la musique classique napolitaine et dans certains styles de jazz modal pour des progressions Iusual et Maj7 avec couleur phrygienne.",
    "napolitaine_min":
        "La gamme napolitaine mineure est très expressive à la guitare, avec ses b2 et b6 qui renforcent le caractère mélancolique et dramatique. Elle est présente dans le flamenco, certains styles de métal (à travers ses secondes augmentées) et le jazz modal pour des atmosphères très intenses.",
    "prometheus":
        "La gamme de Prométhée de Scriabine crée une atmosphère suspendue et contemplative à la guitare. Ses positions sur le manche offrent des possibilités harmoniques très originales. Utilisée dans la musique impressionniste et le jazz modal expérimental pour des moments de flottement harmonique.",
    "overtone":
        "La gamme acoustique (overtone, identique au lydien dominant) reflète la série des harmoniques naturelles. À la guitare, elle sonne magistralement sur les accords V7#11 et les substitutions tritoniques. Béla Bartók l'a théorisée et les guitaristes de jazz-fusion (John McLaughlin, Allan Holdsworth) l'exploitent pour ses couleurs uniques.",
    "hijaz":
        "Le maqam Hijaz donne à la guitare un son immédiatement reconnaissable du Moyen-Orient. Sa 2nde augmentée entre le b2 et la 3ce majeure est au cœur du flamenco, de la musique arabe et de certains styles de métal. Très proche du phrygien dominant, il est exploité par de nombreux guitaristes de fusion et de world-music.",
    "hijaz_kar":
        "Le maqam Hijaz Kar avec ses deux secondes augmentées est très expressif à la guitare. Il permet des phrases très ornementées caractéristiques de la musique arabe et turque classique. Les guitaristes de world-fusion l'utilisent pour des couleurs encore plus dramatiques que le Hijaz standard.",
    "bayati":
        "Le maqam Bayati possède une couleur mélancolique profonde qui s'exprime particulièrement bien à la guitare acoustique. Sa b2 et sa structure particulière permettent des phrases très expressives ornées de glissandos et de vibratos. Très présent dans la world-music et la fusion méditerranéenne.",
    "nahawand":
        "Le maqam Nahawand est l'équivalent arabe de la mineure harmonique, ce qui le rend accessible aux guitaristes occidentaux. À la guitare, il crée un pont entre le langage mineur harmonique classique et les modes orientaux. Ses positions sont proches de la mineure harmonique standard.",
    "rast":
        "Le maqam Rast est considéré comme le 'majeur' de la musique arabe. À la guitare, sa légère ambiguïté (proche du mixolydien) le rend versatile pour des colorations orientales dans des contextes harmoniques familiers. Très utilisé dans la world-fusion et la guitare méditerranéenne.",
    "nikriz":
        "Le maqam Nikriz et ses deux secondes augmentées créent une tension dramatique à la guitare. Il est utilisé dans la musique arabe, turque et balkanique pour des phrases très expressives. Sa structure enrichie rappelle le dorien #4 et permet des lignes mélodiques à la fois exotiques et musicalement cohérentes.",
    "saba":
        "Le maqam Saba avec sa b4 distinctive est l'un des maqams les plus expressifs de la guitare méditerranéenne. Sa mélancolie profonde s'exprime à travers des ornements caractéristiques (glissandos, trilles). Très difficile à intégrer dans un contexte tonal occidental, il est une couleur à part entière dans la world-fusion.",
    "kurd":
        "Le maqam Kurd est très proche du mode phrygien, ce qui le rend accessible aux guitaristes habitués aux contextes metal et rock. Il est présent dans la musique kurde, arabe et turque pour des phrases sombres et expressives. Sa 2nde mineure le rapproche du phrygien tout en lui donnant une couleur légèrement différente dans les ornements.",
    "hirajoshi":
        "La gamme Hirajoshi est la pentatonique japonaise par excellence à la guitare. Ses deux demi-tons caractéristiques créent une atmosphère contemplative immédiate. Très utilisée dans le metal alternatif et le metal progressif (Animals as Leaders, Tosin Abasi), elle permet des riffs et phrases melodiques à la couleur asiatique très reconnaissable.",
    "insen":
        "La gamme Insen est une pentatonique japonaise asymétrique qui crée des atmosphères très particulières à la guitare. Avec son b2 et sa 4te juste, elle permet des phrases méditatives et contemplatives. Joe Satriani et les guitaristes de fusion l'utilisent pour créer des moments de couleur exotique dans leurs compositions.",
    "kumoi":
        "La gamme Kumoi est une pentatonique japonaise douce, moins sombre que Hirajoshi. À la guitare, elle permet des phrases mélodiques mélancoliques avec une légèreté particulière. Ses positions sur le manche sont accessibles et permettent d'incorporer facilement la couleur japonaise dans des solos.",
    "iwato":
        "La gamme Iwato est la pentatonique japonaise la plus dissonante, avec deux demi-tons consécutifs. À la guitare, son instabilité inhérente est exploitée pour des moments de grande tension dans le metal progressif et la composition contemporaine. Ses positions sur le manche sont compactes et permettent des runs techniques intéressants.",
    "yo":
        "La gamme Yo est la pentatonique majeure japonaise, plus lumineuse que les autres gammes de la tradition japonaise. À la guitare, elle sonne de façon naturelle et accessible, se rapprochant de la pentatonique majeure occidentale. Idéale pour introduire une couleur japonaise subtile dans des solos ou compositions.",
    "bhairav":
        "Le raga Bhairav crée une atmosphère de sérénité matinale à la guitare. Sa b2 et sa b6 dans un contexte majoritaire lui donnent une couleur unique très expressive. John McLaughlin (Shakti) et les guitaristes de world-fusion l'exploitent pour des compositions qui marient les traditions musicales indiennes et occidentales.",
    "todi":
        "Le raga Todi est l'un des ragas les plus complexes et expressifs de la musique indienne classique. À la guitare, ses b2, b3, #4 et b6 créent des tensions inhabituelles qui demandent une grande maîtrise. John McLaughlin y revient régulièrement dans ses compositions fusion pour créer des atmosphères méditatives intenses.",
    "kafi":
        "Le raga Kafi est l'équivalent indien du mode dorien. À la guitare, sa proximité avec le dorien le rend accessible aux guitaristes de jazz. John McLaughlin et Shakti ont popularisé cette couleur en fusion, montrant comment le raga Kafi peut s'intégrer naturellement dans un langage de guitare jazz contemporain.",
    "kalyan":
        "Le raga Kalyan est l'équivalent indien du mode lydien. À la guitare, sa #4 caractéristique crée le même effet flottant et ascendant que le lydien occidental. Les guitaristes de world-fusion (Ravi Shankar × Philip Glass, John McLaughlin) l'exploitent pour des atmosphères crépusculaires très belles.",
}

GROUP_DESCS_GUITAR_FR = {
    0: "Ce mode diatonique à 7 notes est issu de la gamme majeure et de ses rotations. Il structure la théorie harmonique occidentale et fournit la base pour comprendre les accords et les voicings à la guitare.",
    1: "Cette gamme non-diatonique offre des couleurs sonores spécifiques très utilisées dans des genres précis. Elle est un outil d'improvisation essentiel pour les guitaristes qui veulent sortir des sentiers battus.",
    2: "Ce mode dérivé de la gamme mineure mélodique ou harmonique est au cœur du jazz guitare moderne. Il permet d'improviser avec précision sur des accords complexes aux tensions spécifiques.",
    3: "Cette gamme exotique est issue d'une tradition musicale non-occidentale. Elle apporte des couleurs sonores inhabituelles pour l'oreille occidentale et ouvre des perspectives harmoniques uniques à la guitare.",
}

# ---------------------------------------------------------------------------
# DESCRIPTIONS GUITARE — ANGLAIS
# ---------------------------------------------------------------------------
SCALE_DESCS_GUITAR_EN = {
    "major":
        "The major scale is the backbone of guitar playing across all styles. From rock to pop, country to jazz, it appears everywhere. On the fretboard, it is learned through the CAGED system which maps five different positions across all 6 strings. Mastering the major scale on guitar means understanding harmony in every key.",
    "minor":
        "The natural minor scale is the quintessential rock and metal scale on guitar. Its fretboard positions form box shapes ideal for improvisation. Eddie Van Halen, Slash, Angus Young — all built their solos from this scale. Its dark, direct character suits palm-muted riffs and melodic lead playing perfectly.",
    "harmonic":
        "The harmonic minor scale gives guitar a dramatic, Eastern-tinged sound that is instantly recognizable. Its augmented second (W+H) between the 6th and 7th degrees creates a distinctive leap found in flamenco, neoclassical metal (Yngwie Malmsteen) and film scores. It sounds magnificent over i–V progressions in all minor keys.",
    "melodic":
        "The melodic minor scale (ascending form) is essential in jazz guitar. It generates the altered, Lydian dominant, and Locrian #2 scales through simple rotation. Joe Pass, Pat Metheny, Mike Stern — all exploit its colors on minor ii-V-I progressions. Its natural 6th and 7th degrees allow very fluid melodic lines over minMaj7 chords.",
    "dorian":
        "The Dorian mode is THE scale of blues-rock and funk guitar. Its major 6th gives it a luminous opening in a minor context. Carlos Santana, David Gilmour, and John Mayer use it constantly. It fits perfectly over typical i–IV blues modal progressions and naturally overlaps with the minor pentatonic positions.",
    "phrygian":
        "The Phrygian mode defines the sound of progressive metal, flamenco, and Oriental guitar. Its minor 2nd creates immediate tension from the first note. Tom Morello, Kirk Hammett, and flamenco guitarists use it as their primary color. In metal, it structures the darkest riffs; in flamenco, it defines the soul of the falsetas.",
    "lydian":
        "The Lydian mode with its augmented 4th sounds dreamy and ethereal on guitar. Steve Vai and Joe Satriani elevated it to signature status in fusion and instrumental rock. It works beautifully over Maj7#11 chords and creates floating atmospheres widely used in film music. On the fretboard, the #4 is easy to spot compared to the standard major scale.",
    "mixolydian":
        "The Mixolydian mode is the sound of rock, blues, and country guitar. Its b7 over a major backdrop gives the warmth of blues without the darkness of minor. Brown Sugar (Rolling Stones), Sweet Home Alabama (Lynyrd Skynyrd), and Born to Run (Springsteen) riffs all derive from it. Over dominant chords, it is the go-to tool for blues and rock guitarists.",
    "locrian":
        "The Locrian mode, with its diminished 5th, is rarely used in its pure form on guitar. It appears mainly in extreme metal (for riffs over iiø chords) and jazz improvisation over half-diminished chords. Its inherent instability can be exploited creatively in transitional passages toward a tonal resolution.",
    "penta_min":
        "The minor pentatonic is the most-played guitar scale in the world. Jimmy Page, Eric Clapton, Jimi Hendrix, BB King — all built their careers on these 5 notes. Its five positions (CAGED boxes) cover the entire neck and allow immediate improvisation over any blues or rock. It is the absolute first scale to learn on guitar.",
    "penta_maj":
        "The major pentatonic is the bright, country version of the pentatonic. Mark Knopfler, Keith Richards, and country guitarists use it constantly for singable, melodic lines. It fits naturally over I–IV–V major progressions and allows very expressive bends and hammer-ons. The switch between minor and major pentatonic is one of the key techniques of blues-rock guitar.",
    "blues_min":
        "The minor blues scale is the soul of electric guitar. Its blue note (b5) between the 4th and perfect 5th creates the expressive tension specific to blues. SRV, BB King, Buddy Guy — all exploit it through bends, vibratos, and slides. On the neck, the blue note is easily accessible from box 1 of the minor pentatonic.",
    "blues_maj":
        "The major blues scale blends the warmth of the major pentatonic with the ambiguity of the minor 3rd. It is the sound of original rock'n'roll — Chuck Berry, Elvis, Carl Perkins. Works perfectly over I7–IV7–V7 blues progressions. Country guitarists also use it to add a 'gritty' feel to double-stop lines.",
    "penta_dom":
        "The dominant pentatonic (with b7) is perfectly suited for seventh chords and the blues on guitar. It works over the I7, IV7, and V7 dominants of the blues without a wrong note. Widely used in blues-rock, funk, and R&B guitar, it allows expressive phrases in all neck positions.",
    "penta_min6":
        "The minor 6 pentatonic introduces the major 6th into a minor context, creating a very characteristic jazz color on guitar. It sounds great over minor 6 chords and allows very refined open voicings. Widely used in gypsy jazz and jazz guitar to add color to minor phrases.",
    "penta_sus":
        "The suspended pentatonic (no defined 3rd) creates floating, ambiguous atmospheres on guitar. Prized by John Scofield, Pat Metheny, and jazz-fusion guitarists for improvising over sus4 and add9 chords. On the neck, its positions easily overlap with major pentatonic shapes.",
    "blues_dom":
        "The dominant blues scale enriches the dominant pentatonic with the tritone. It sounds with maximum tension over V7 altered chords and tritone substitution dominants. Jazz-blues guitarists (Robben Ford, Larry Carlton) use it to create expressive tensions before the resolution.",
    "blues_hex":
        "The hexatonic blues enriches the minor pentatonic with the major 2nd, adding a Dorian color. It is very popular in modern blues-rock and alternative rock for lines more sophisticated than the pure pentatonic, while remaining accessible on the neck.",
    "penta_maj7":
        "The major 7 pentatonic replaces the usual minor 7th with a major 7th, giving a soft, elegant jazz color on guitar. It sounds great over Maj7 and CMaj9 chords. Jazz guitarists (Pat Metheny, Lenny Breau) use it for fluid, refined phrases over major seventh chords.",
    "penta_min_lead":
        "The minor pentatonic with leading tone (major 7th) is widely used in jazz and fusion guitar. This natural 7th creates a strong pull toward the tonic, perfect for punctuating phrase endings with character. It enriches the classic minor pentatonic without changing its fundamental structure.",
    "boogie":
        "The Rock'n'Roll / Boogie scale captures the essence of shuffle and boogie-woogie on guitar. The characteristic double-stop boogie patterns (alternating root–5th with chromatic runs) derive directly from this scale. Present throughout original rock'n'roll, from rockabilly to classic 1970s rock.",
    "penta_majb2":
        "The major b2 pentatonic blends a familiar pentatonic structure with the exoticism of the minor 2nd. On guitar, it creates phrases halfway between an Oriental world and Western pentatonic language. Used by some world-fusion guitarists for unexpected colors.",
    "dim":
        "The whole-half diminished scale is an 8-note symmetric scale widely used in jazz and metal guitar. Its periodicity of 3 semitones means its positions repeat every 3 frets. Jazz guitarists use it over dim7 and b9 dominant chords, while metal guitarists exploit its symmetry for fast, very characteristic runs.",
    "dim_ht":
        "The half-whole diminished scale is widely used in jazz and bebop on b9 dominant chords. Its initial half-step gives it an even tenser character. Jazz guitarists like John Scofield and Pat Martino exploit it on V7b9 for very expressive phrases.",
    "half_dim":
        "The half-diminished scale (= Locrian) is used over iiø7 chords in jazz ii-V-i cadences in minor. On guitar, it appears in jazz standard progressions (Autumn Leaves, All The Things You Are). Its b5 creates tension that immediately calls for resolution toward the dominant.",
    "whole_tone":
        "The whole-tone scale is entirely symmetric — only two versions for all 12 keys. On guitar, its positions are very regular and easy to visualize. Trey Anastasio (Phish) and Frank Zappa exploit it for floating, dreamy effects. It works over augmented chords and #5 dominants.",
    "aug_hex":
        "The augmented hexatonic scale is built from two augmented triads and creates very colorful sounds on guitar. Its symmetric positions allow technically impressive passages. Used in modern jazz and contemporary composition for unusual color effects.",
    "chromatic":
        "The chromatic scale (12 semitones) is essential for transitional passages on guitar. Chromatic approaches (encircling notes) are a fundamental technique in jazz and blues. Allan Holdsworth built an entire language around chromatic runs. On the neck, it connects any position by passing through every fret.",
    "phryg_dom":
        "The Phrygian dominant is the sound of flamenco and neoclassical metal on guitar. Paco de Lucía, Yngwie Malmsteen, and progressive metal guitarists have made it their signature. Its minor 2nd and major 3rd create immediate dramatic tension. In flamenco it structures the most expressive falsetas; in metal it produces the darkest, most dramatic riffs.",
    "lydian_dom":
        "The Lydian dominant (Lydian with b7) is a quintessential jazz-fusion color on guitar. Scott Henderson, John McLaughlin, and Frank Zappa exploit it over V7#11 chords and tritone substitutions. Its #4 and b7 give it both Lydian brightness and Mixolydian tension.",
    "altered":
        "The altered scale (superlocrian) contains all altered tensions: b9, #9, b5, #5. On guitar, it is the scale for the most expressive V7alt→i resolutions in jazz. John Scofield, Pat Metheny, and Mike Stern use it over altered dominants to create maximum tension before resolution in minor.",
    "locrian_s2":
        "Locrian #2 is more stable than standard Locrian thanks to its major 2nd. On guitar, it is used over iiø7 chords in ii-V-i minor cadences. Its natural 2nd allows more fluid phrases than pure Locrian while maintaining the characteristic b5 ambiguity.",
    "lydian_aug":
        "Lydian Augmented combines #4 and #5, creating a very colorful and dissonant sound on guitar. It works over Maj7#5 chords in chromatic jazz progressions. Its double alteration makes it complex but very expressive for contemporary jazz guitarists seeking unusual colors.",
    "mixo_b6":
        "Mixolydian b6 blends Mixolydian warmth with minor darkness. On guitar, it creates mysterious atmospheres over dominant chords. Used in jazz and film music, it offers a colorful alternative to standard Mixolydian for modal V7 colors.",
    "dorian_b2":
        "Dorian b2 (= Phrygian #6) blends the minor 2nd of Phrygian with the openness of Dorian's major 6th. On guitar, it creates unexpected, sophisticated colors on minor chords. Used in modal jazz and fusion for phrases that surprise ears accustomed to standard modes.",
    "locrian6":
        "Locrian nat.6 softens Locrian's instability with its natural major 6th. On guitar, some jazz players prefer this mode for improvising over iiø7 chords, its natural 6th allowing less tense melodic movements than pure Locrian while maintaining the modal atmosphere.",
    "ionian_s5":
        "Ionian #5 is a major mode with an augmented 5th that creates an unusual tension. On guitar, it works over augmented Maj7#5 chords and allows phrases that wrong-foot ears accustomed to the standard Ionian sound. Its #5 creates a very recognizable color in chromatic progressions.",
    "dorian_s4":
        "Dorian #4 (Romanian minor) combines Dorian color with a very expressive augmented 4th. On guitar, it appears in Eastern European folk music, modal jazz, and some progressive metal styles. Its #4 gives it a character that is both familiar (Dorian) and exotic (augmented second).",
    "lydian_s2":
        "Lydian #2 is one of the most exotic modes of the harmonic minor. With its augmented 2nd AND augmented 4th, it creates very distinctive colors on guitar. Used in Eastern European folk music and experimental jazz for musically unusual phrases.",
    "superlocrian_bb7":
        "Super Locrian bb7 is extremely rare on guitar — its double-flat 7 makes it a theoretical mode used in the most advanced jazz contexts. It is taught in jazz conservatories as an edge case of harmonic minor modal theory.",
    "bebop_maj":
        "The bebop major scale adds a chromatic augmented 5th between the 5th and 6th. On guitar, this 8th passing note allows fluid bebop lines with melodic notes on the strong beats. Charlie Christian and Wes Montgomery laid the foundations of this language that remains essential in jazz guitar.",
    "bebop_dom":
        "The bebop dominant scale is Mixolydian with an added major 7th passing note. On guitar, it allows very fluid bebop-style phrases over dominant chords. Charlie Christian, Joe Pass, and Pat Martino use it to structure their lines with impeccable harmonic logic.",
    "bebop_min":
        "The bebop minor scale adds a major 3rd passing note between the minor 3rd and the 4th. On guitar, it allows expressive bebop phrases over minor chords. Used in classic jazz and bebop for melodic lines that flow naturally on the beats.",
    "double_harm":
        "The double harmonic scale (Byzantine, Gypsy) is characterized by its two very expressive augmented seconds. On guitar, it appears in advanced flamenco, Balkan music, and progressive metal (Guthrie Govan). Its wide intervals make it technically demanding but the sonic effect is immediately striking.",
    "hung_min":
        "The Hungarian minor (Gypsy minor) is at the heart of gypsy jazz guitar. Django Reinhardt and his successors (Stochelo Rosenberg, Biréli Lagrène) use it constantly in the Parisian manouche style. Its #4 and b6 give it that dramatic, romantic character so characteristic of the style.",
    "hung_maj":
        "The Hungarian major with its unusual minor 3rd creates an exotic sound in a major context on guitar. Used in Central European folk music and experimental jazz to create unexpected colors on major progressions.",
    "gypsy_maj":
        "The Gypsy major appears in gypsy jazz and Romani music on guitar. Django Reinhardt and manouche-style guitarists exploit it for very expressive phrases with characteristic bends and ornaments. Its b2 and #4 give it an immediately recognizable character.",
    "romanian_min":
        "The Romanian minor is a Dorian with an augmented 4th that creates a distinctive Eastern European folk sound on guitar. Used in traditional Romanian, Greek, and Turkish music as well as gypsy jazz and world-fusion for unusual colors.",
    "persian":
        "The Persian scale is one of the most dissonant for guitar. With its b2, #3, and b5, it creates unusual tensions exploited in experimental music and avant-garde metal. Its complex theoretical structure makes it difficult to integrate but interesting for extreme color effects.",
    "arabic":
        "The Arabic scale is a variant of the whole-tone scale that captures certain Middle Eastern colors. On guitar, it is used in world-fusion and jazz to create Middle Eastern ambiences. Its positions on the neck are relatively accessible thanks to its partial symmetry.",
    "enigmatic":
        "Verdi's enigmatic scale is a theoretical construction with very complex harmonies. On guitar, it creates very unusual atmospheres difficult to anchor in a standard tonal context. Some progressive rock and avant-garde metal composers exploit it for its unpredictable, disorienting character.",
    "napolitaine_maj":
        "The Neapolitan major scale (major with b2) gives guitar a dark, expressive character unusual for a major context. Used in Neapolitan classical music and some modal jazz styles for Iusual and Maj7 progressions with Phrygian coloring.",
    "napolitaine_min":
        "The Neapolitan minor is very expressive on guitar, its b2 and b6 reinforcing the melancholic and dramatic character. Present in flamenco, some metal styles (through its augmented seconds), and modal jazz for very intense atmospheres.",
    "prometheus":
        "Scriabin's Prometheus scale creates a suspended, contemplative atmosphere on guitar. Its positions on the neck offer very original harmonic possibilities. Used in Impressionist music and experimental modal jazz for moments of harmonic suspension.",
    "overtone":
        "The overtone scale (identical to Lydian dominant) reflects the natural harmonic series. On guitar, it sounds magnificent over V7#11 chords and tritone substitutions. Béla Bartók theorized it and jazz-fusion guitarists (John McLaughlin, Allan Holdsworth) exploit it for its unique colors.",
    "hijaz":
        "The Hijaz maqam gives guitar an immediately recognizable Middle Eastern sound. Its augmented second between the b2 and the major 3rd is central to flamenco, Arabic music, and some metal styles. Very close to Phrygian dominant, it is exploited by many fusion and world-music guitarists.",
    "hijaz_kar":
        "The Hijaz Kar maqam with its two augmented seconds is very expressive on guitar. It allows highly ornamented phrases characteristic of Arabic and Turkish classical music. World-fusion guitarists use it for even more dramatic colors than standard Hijaz.",
    "bayati":
        "The Bayati maqam has a deeply melancholic color that expresses itself particularly well on acoustic guitar. Its b2 and particular structure allow very expressive phrases ornamented with glissandos and vibratos. Very present in world music and Mediterranean fusion.",
    "nahawand":
        "The Nahawand maqam is the Arabic equivalent of the harmonic minor, making it accessible to Western guitarists. On guitar, it creates a bridge between classical Western harmonic minor language and Oriental modes. Its positions are close to the standard harmonic minor.",
    "rast":
        "The Rast maqam is considered the 'major' of Arabic music. On guitar, its slight ambiguity (close to Mixolydian) makes it versatile for Oriental colorings in familiar harmonic contexts. Widely used in world-fusion and Mediterranean guitar.",
    "nikriz":
        "The Nikriz maqam and its two augmented seconds create dramatic tension on guitar. Used in Arabic, Turkish, and Balkan music for very expressive phrases. Its enriched structure recalls Dorian #4 and allows melodic lines that are both exotic and musically coherent.",
    "saba":
        "The Saba maqam with its distinctive b4 is one of the most expressive maqams in Mediterranean guitar. Its deep melancholy is expressed through characteristic ornaments (glissandos, trills). Very difficult to integrate into a Western tonal context, it is a color in its own right in world-fusion.",
    "kurd":
        "The Kurd maqam is very close to the Phrygian mode, making it accessible to guitarists accustomed to metal and rock contexts. Present in Kurdish, Arabic, and Turkish music for dark and expressive phrases. Its minor 2nd brings it close to Phrygian while giving it a slightly different color in its ornaments.",
    "hirajoshi":
        "Hirajoshi is the quintessential Japanese pentatonic scale on guitar. Its two characteristic semitones create an immediately contemplative atmosphere. Widely used in alternative and progressive metal (Animals as Leaders, Tosin Abasi), it enables riffs and melodic phrases with a very recognizable Asian color.",
    "insen":
        "The Insen scale is an asymmetric Japanese pentatonic that creates very particular atmospheres on guitar. With its b2 and perfect 4th, it enables meditative, contemplative phrases. Joe Satriani and fusion guitarists use it to add exotic color moments to their compositions.",
    "kumoi":
        "The Kumoi scale is a gentle Japanese pentatonic, less dark than Hirajoshi. On guitar, it enables melancholic melodic phrases with a special lightness. Its neck positions are accessible and allow easily incorporating Japanese color into solos.",
    "iwato":
        "The Iwato scale is the most dissonant Japanese pentatonic, with two consecutive semitones. On guitar, its inherent instability is exploited for moments of great tension in progressive metal and contemporary composition. Its neck positions are compact and allow interesting technical runs.",
    "yo":
        "The Yo scale is the Japanese major pentatonic, brighter than other Japanese tradition scales. On guitar, it sounds natural and accessible, resembling the Western major pentatonic. Ideal for introducing a subtle Japanese color into solos or compositions.",
    "bhairav":
        "Raga Bhairav creates an atmosphere of morning serenity on guitar. Its b2 and b6 in a major context give it a unique expressive color. John McLaughlin (Shakti) and world-fusion guitarists exploit it for compositions that blend Indian and Western musical traditions.",
    "todi":
        "Raga Todi is one of the most complex and expressive ragas in Indian classical music. On guitar, its b2, b3, #4, and b6 create unusual tensions requiring great mastery. John McLaughlin returns to it regularly in his fusion compositions to create intense meditative atmospheres.",
    "kafi":
        "Raga Kafi is the Indian equivalent of the Dorian mode. On guitar, its proximity to Dorian makes it accessible to jazz guitarists. John McLaughlin and Shakti popularized this color in fusion, showing how Raga Kafi can naturally integrate into a contemporary jazz guitar language.",
    "kalyan":
        "Raga Kalyan is the Indian equivalent of the Lydian mode. On guitar, its characteristic #4 creates the same floating, ascending effect as Western Lydian. World-fusion guitarists (Ravi Shankar × Philip Glass, John McLaughlin) exploit it for very beautiful twilight atmospheres.",
}

GROUP_DESCS_GUITAR_EN = {
    0: "This 7-note diatonic mode derives from the major scale and its rotations. It structures Western harmonic theory and provides the foundation for understanding chords and voicings on guitar.",
    1: "This non-diatonic scale offers specific sonic colors widely used in particular genres. It is an essential improvisation tool for guitarists looking to go beyond the beaten path.",
    2: "This mode derived from the melodic or harmonic minor scale is at the core of modern jazz guitar language. It allows precise improvisation over complex chords with specific tensions.",
    3: "This exotic scale comes from a non-Western musical tradition. It brings unusual sonic colors to the Western ear and opens unique harmonic perspectives on guitar.",
}

# ---------------------------------------------------------------------------
# GÉNÉRATION
# ---------------------------------------------------------------------------
def main():
    env = Environment(loader=FileSystemLoader(str(TMPL_DIR)), autoescape=True)
    scale_tpl = env.get_template("scale_guitar.html.jinja2")
    hub_tpl   = env.get_template("hub.html.jinja2")

    pages_fr = []
    pages_en = []

    print(f"Génération guitare FR dans {OUT_ROOT_FR} …")
    print(f"Génération guitare EN dans {OUT_ROOT_EN} …")

    for scale in SCALE_DEFS:
        slug_s = scale_slug(scale["id"])
        for root in ROOTS:
            notes_raw = build_scale(root["name"], scale["ls"], scale["iv"])
            notes_fr  = [fr_note(n) for n in notes_raw]
            notes_en  = [pretty(n)  for n in notes_raw]
            ivstr     = interval_str(scale["iv"])
            n_notes   = len(scale["iv"])
            app_link  = f"{APP_URL}?root={root['name']}&scale={scale['id']}"

            page_url_fr = f"{BASE_URL}/fr/gammes-guitare/{root['slug']}/{slug_s}/"
            page_url_en = f"{BASE_URL}/en/scales-guitar/{root['slug_en']}/{slug_s}/"

            # ---- Page FR ----
            triads_fr = build_triads(root["name"], scale["ls"], scale["iv"], lang='fr')
            desc_fr   = SCALE_DESCS_GUITAR_FR.get(scale["id"]) or GROUP_DESCS_GUITAR_FR.get(scale["group"], "")
            notes_str = " – ".join(notes_fr)
            ctx_fr = {
                "lang":        "fr",
                "root":        root,
                "scale":       scale,
                "scale_slug":  slug_s,
                "label":       scale["label"],
                "sub":         scale.get("sub", ""),
                "notes_primary":         notes_fr,
                "notes_secondary":       notes_en,
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
                "nav_base":    f"{BASE_URL}/fr/gammes-guitare",
                "ui_title":         f"Gamme de {root['fr']} {scale['label']} guitare — {notes_str}",
                "ui_meta_desc":     f"Gamme de {root['fr']} {scale['label']} pour guitare 6 cordes : {notes_str}. {n_notes} note{'s' if n_notes>1 else ''}. Intervalles : {ivstr}. Positions sur le manche, manche interactif.",
                "ui_h1":            f"Gamme de {root['fr']} {scale['label']} à la guitare",
                "ui_instrument":    "Guitare 6 cordes",
                "ui_family":        f"famille {'majeure' if scale['fam']=='maj' else 'mineure'}",
                "ui_notes":         "Notes",
                "ui_ivstruct":      "Structure d'intervalles",
                "ui_triads_title":  "Accords de la gamme (triades)",
                "ui_degree":        "Degré",
                "ui_chord":         f"Accord (en {root['fr']})",
                "ui_quality":       "Qualité",
                "ui_about":         "À propos de cette gamme",
                "ui_cta_text":      f"Voir les positions sur le manche de guitare pour <strong>{root['fr']} {scale['label']}</strong> dans l'appli interactive.",
                "ui_cta_btn":       "Explorer dans ScalaBass →",
                "ui_other_keys":    "Même gamme dans d'autres toniques",
                "ui_all_scales":    "Toutes les gammes guitare",
                "ui_og_title":      f"Gamme {root['fr']} {scale['label']} — Guitare",
                "ui_og_desc":       f"{root['fr']} {scale['label']} guitare : {notes_str}",
                "ui_schema_head":   f"Gamme de {root['fr']} {scale['label']} pour guitare",
                "ui_schema_desc":   f"{root['fr']} {scale['label']} pour guitare 6 cordes : {notes_str}. Intervalles : {ivstr}.",
            }
            out_dir = OUT_ROOT_FR / root["slug"] / slug_s
            out_dir.mkdir(parents=True, exist_ok=True)
            (out_dir / "index.html").write_text(scale_tpl.render(**ctx_fr), encoding="utf-8")
            pages_fr.append(page_url_fr)

            # ---- Page EN ----
            triads_en = build_triads(root["name"], scale["ls"], scale["iv"], lang='en')
            desc_en   = SCALE_DESCS_GUITAR_EN.get(scale["id"]) or GROUP_DESCS_GUITAR_EN.get(scale["group"], "")
            notes_str_en = " – ".join(notes_en)
            ctx_en = {
                "lang":        "en",
                "root":        root,
                "scale":       scale,
                "scale_slug":  slug_s,
                "label":       scale.get("label_en", scale["label"]),
                "sub":         scale.get("sub_en", scale.get("sub", "")),
                "notes_primary":         notes_en,
                "notes_secondary":       notes_fr,
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
                "nav_base":    f"{BASE_URL}/en/scales-guitar",
                "ui_title":        f"{root['name']} {scale.get('label_en', scale['label'])} Guitar Scale — {notes_str_en}",
                "ui_meta_desc":    f"{root['name']} {scale.get('label_en', scale['label'])} scale for 6-string guitar: {notes_str_en}. {n_notes} note{'s' if n_notes>1 else ''}. Intervals: {ivstr}. Fretboard positions, interactive tab.",
                "ui_h1":           f"{root['name']} {scale.get('label_en', scale['label'])} Guitar Scale",
                "ui_instrument":   "6-string guitar",
                "ui_family":       f"{'major' if scale['fam']=='maj' else 'minor'} family",
                "ui_notes":        "Notes",
                "ui_ivstruct":     "Interval Structure",
                "ui_triads_title": "Scale Chords (triads)",
                "ui_degree":       "Degree",
                "ui_chord":        f"Chord (in {root['name']})",
                "ui_quality":      "Quality",
                "ui_about":        "About this scale",
                "ui_cta_text":     f"See fretboard positions for <strong>{root['name']} {scale.get('label_en', scale['label'])}</strong> on guitar in the interactive app.",
                "ui_cta_btn":      "Explore in ScalaBass →",
                "ui_other_keys":   "Same scale in other keys",
                "ui_all_scales":   "All guitar scales",
                "ui_og_title":     f"{root['name']} {scale.get('label_en', scale['label'])} Guitar Scale",
                "ui_og_desc":      f"{root['name']} {scale.get('label_en', scale['label'])} guitar: {notes_str_en}",
                "ui_schema_head":  f"{root['name']} {scale.get('label_en', scale['label'])} guitar scale",
                "ui_schema_desc":  f"{root['name']} {scale.get('label_en', scale['label'])} for 6-string guitar: {notes_str_en}. Intervals: {ivstr}.",
            }
            out_dir = OUT_ROOT_EN / root["slug_en"] / slug_s
            out_dir.mkdir(parents=True, exist_ok=True)
            (out_dir / "index.html").write_text(scale_tpl.render(**ctx_en), encoding="utf-8")
            pages_en.append(page_url_en)

    # ---- Pages enharmoniques ----
    print("Génération des pages enharmoniques guitare …")
    for scale in SCALE_DEFS:
        slug_s = scale_slug(scale["id"])
        for eroot in ENHARMONIC_ROOTS:
            notes_raw = build_scale(eroot["name"], scale["ls"], scale["iv"])
            notes_fr  = [fr_note(n) for n in notes_raw]
            notes_en  = [pretty(n)  for n in notes_raw]
            ivstr     = interval_str(scale["iv"])
            n_notes   = len(scale["iv"])
            app_link  = f"{APP_URL}?root={eroot['name']}&scale={scale['id']}"

            page_url_fr      = f"{BASE_URL}/fr/gammes-guitare/{eroot['slug']}/{slug_s}/"
            canonical_url_fr = f"{BASE_URL}/fr/gammes-guitare/{eroot['canonical_slug']}/{slug_s}/"
            page_url_en      = f"{BASE_URL}/en/scales-guitar/{eroot['slug_en']}/{slug_s}/"
            canonical_url_en = f"{BASE_URL}/en/scales-guitar/{eroot['canonical_slug_en']}/{slug_s}/"

            # FR
            triads_fr = build_triads(eroot["name"], scale["ls"], scale["iv"], lang='fr')
            desc_fr   = SCALE_DESCS_GUITAR_FR.get(scale["id"]) or GROUP_DESCS_GUITAR_FR.get(scale["group"], "")
            notes_str = " – ".join(notes_fr)
            ctx_fr = {
                "lang":        "fr",
                "root":        eroot,
                "scale":       scale,
                "scale_slug":  slug_s,
                "label":       scale["label"],
                "sub":         scale.get("sub", ""),
                "notes_primary":         notes_fr,
                "notes_secondary":       notes_en,
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
                "nav_base":    f"{BASE_URL}/fr/gammes-guitare",
                "ui_title":         f"Gamme de {eroot['fr']} {scale['label']} guitare — {notes_str}",
                "ui_meta_desc":     f"Gamme de {eroot['fr']} {scale['label']} pour guitare : {notes_str}. {n_notes} note{'s' if n_notes>1 else ''}. Intervalles : {ivstr}.",
                "ui_h1":            f"Gamme de {eroot['fr']} {scale['label']} à la guitare",
                "ui_instrument":    "Guitare 6 cordes",
                "ui_family":        f"famille {'majeure' if scale['fam']=='maj' else 'mineure'}",
                "ui_notes":         "Notes",
                "ui_ivstruct":      "Structure d'intervalles",
                "ui_triads_title":  "Accords de la gamme (triades)",
                "ui_degree":        "Degré",
                "ui_chord":         f"Accord (en {eroot['fr']})",
                "ui_quality":       "Qualité",
                "ui_about":         "À propos de cette gamme",
                "ui_cta_text":      f"Voir les positions sur le manche pour <strong>{eroot['fr']} {scale['label']}</strong> guitare dans l'appli.",
                "ui_cta_btn":       "Explorer dans ScalaBass →",
                "ui_other_keys":    "Même gamme dans d'autres toniques",
                "ui_all_scales":    "Toutes les gammes guitare",
                "ui_og_title":      f"Gamme {eroot['fr']} {scale['label']} — Guitare",
                "ui_og_desc":       f"{eroot['fr']} {scale['label']} guitare : {notes_str}",
                "ui_schema_head":   f"Gamme de {eroot['fr']} {scale['label']} pour guitare",
                "ui_schema_desc":   f"{eroot['fr']} {scale['label']} pour guitare : {notes_str}. Intervalles : {ivstr}.",
            }
            out_dir = OUT_ROOT_FR / eroot["slug"] / slug_s
            out_dir.mkdir(parents=True, exist_ok=True)
            (out_dir / "index.html").write_text(scale_tpl.render(**ctx_fr), encoding="utf-8")
            pages_fr.append(page_url_fr)

            # EN
            triads_en = build_triads(eroot["name"], scale["ls"], scale["iv"], lang='en')
            desc_en   = SCALE_DESCS_GUITAR_EN.get(scale["id"]) or GROUP_DESCS_GUITAR_EN.get(scale["group"], "")
            notes_str_en = " – ".join(notes_en)
            ctx_en = {
                "lang":        "en",
                "root":        eroot,
                "scale":       scale,
                "scale_slug":  slug_s,
                "label":       scale.get("label_en", scale["label"]),
                "sub":         scale.get("sub_en", scale.get("sub", "")),
                "notes_primary":         notes_en,
                "notes_secondary":       notes_fr,
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
                "nav_base":    f"{BASE_URL}/en/scales-guitar",
                "ui_title":        f"{eroot['name']} {scale.get('label_en', scale['label'])} Guitar Scale — {notes_str_en}",
                "ui_meta_desc":    f"{eroot['name']} {scale.get('label_en', scale['label'])} guitar scale: {notes_str_en}. {n_notes} note{'s' if n_notes>1 else ''}. Intervals: {ivstr}.",
                "ui_h1":           f"{eroot['name']} {scale.get('label_en', scale['label'])} Guitar Scale",
                "ui_instrument":   "6-string guitar",
                "ui_family":       f"{'major' if scale['fam']=='maj' else 'minor'} family",
                "ui_notes":        "Notes",
                "ui_ivstruct":     "Interval Structure",
                "ui_triads_title": "Scale Chords (triads)",
                "ui_degree":       "Degree",
                "ui_chord":        f"Chord (in {eroot['name']})",
                "ui_quality":      "Quality",
                "ui_about":        "About this scale",
                "ui_cta_text":     f"See fretboard positions for <strong>{eroot['name']} {scale.get('label_en', scale['label'])}</strong> on guitar in the interactive app.",
                "ui_cta_btn":      "Explore in ScalaBass →",
                "ui_other_keys":   "Same scale in other keys",
                "ui_all_scales":   "All guitar scales",
                "ui_og_title":     f"{eroot['name']} {scale.get('label_en', scale['label'])} Guitar Scale",
                "ui_og_desc":      f"{eroot['name']} {scale.get('label_en', scale['label'])} guitar: {notes_str_en}",
                "ui_schema_head":  f"{eroot['name']} {scale.get('label_en', scale['label'])} guitar scale",
                "ui_schema_desc":  f"{eroot['name']} {scale.get('label_en', scale['label'])} for guitar: {notes_str_en}. Intervals: {ivstr}.",
            }
            out_dir = OUT_ROOT_EN / eroot["slug_en"] / slug_s
            out_dir.mkdir(parents=True, exist_ok=True)
            (out_dir / "index.html").write_text(scale_tpl.render(**ctx_en), encoding="utf-8")
            pages_en.append(page_url_en)

    # ---- Hub FR ----
    OUT_ROOT_FR.mkdir(parents=True, exist_ok=True)
    hub_ctx_fr = {
        "scales":     SCALE_DEFS,
        "roots":      ROOTS,
        "BASE_URL":   BASE_URL,
        "scale_slug": scale_slug,
        "lang":       "fr",
        "hub_base":   f"{BASE_URL}/fr/gammes-guitare",
    }
    (OUT_ROOT_FR / "index.html").write_text(hub_tpl.render(**hub_ctx_fr), encoding="utf-8")
    pages_fr.append(f"{BASE_URL}/fr/gammes-guitare/")

    # ---- Hub EN ----
    OUT_ROOT_EN.mkdir(parents=True, exist_ok=True)
    hub_ctx_en = {
        "scales":     SCALE_DEFS,
        "roots":      ROOTS,
        "BASE_URL":   BASE_URL,
        "scale_slug": scale_slug,
        "lang":       "en",
        "hub_base":   f"{BASE_URL}/en/scales-guitar",
    }
    (OUT_ROOT_EN / "index.html").write_text(hub_tpl.render(**hub_ctx_en), encoding="utf-8")
    pages_en.append(f"{BASE_URL}/en/scales-guitar/")

    # ---- Sitemap (ajoute les pages guitare sans effacer les pages basse) ----
    update_sitemap(pages_fr, pages_en)

    total_fr = len(pages_fr) - 1
    total_en = len(pages_en) - 1
    print(f"  FR : {total_fr} pages + 1 hub = {len(pages_fr)} pages")
    print(f"  EN : {total_en} pages + 1 hub = {len(pages_en)} pages")
    print(f"  Total : {len(pages_fr) + len(pages_en)} nouvelles pages guitare")
    print("  sitemap.xml mis à jour")
    print("Done.")


def update_sitemap(pages_fr, pages_en):
    """Ajoute les pages guitare au sitemap sans toucher aux pages basse."""
    sitemap_path = Path(__file__).parent.parent / "sitemap.xml"
    existing = []
    if sitemap_path.exists():
        content = sitemap_path.read_text(encoding="utf-8")
        existing = re.findall(r'<loc>(.*?)</loc>', content)
    # Garde tout sauf les pages guitare (pour éviter les doublons à chaque run)
    kept = [u for u in existing
            if "/fr/gammes-guitare/" not in u and "/en/scales-guitar/" not in u]
    all_urls = kept + pages_fr + pages_en
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for url in all_urls:
        lines.append(f'  <url><loc>{url}</loc></url>')
    lines.append('</urlset>')
    sitemap_path.write_text('\n'.join(lines) + '\n', encoding="utf-8")


if __name__ == "__main__":
    main()
