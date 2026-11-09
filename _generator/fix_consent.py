"""Consent Mode : mesure autorisee hors Europe, refusee en Europe sans accord.

Lancer depuis la racine du repo :  python _generator/fix_consent.py
Remplace la ligne gtag('consent','default',...) dans tous les .html et .jinja2.
Idempotent : relancer ne change rien.
"""
import os

OLD = ("gtag('consent','default',{'ad_storage':'denied','ad_user_data':'denied',"
       "'ad_personalization':'denied','analytics_storage':'denied','wait_for_update':500});")

EU = ['AT','BE','BG','HR','CY','CZ','DK','EE','FI','FR','DE','GR','HU','IE','IT',
      'LV','LT','LU','MT','NL','PL','PT','RO','SK','SI','ES','SE','IS','LI','NO',
      'GB','CH']
ADS = "'ad_storage':'denied','ad_user_data':'denied','ad_personalization':'denied'"
NEW = ("gtag('consent','default',{" + ADS + ",'analytics_storage':'granted'});"
       "gtag('consent','default',{" + ADS + ",'analytics_storage':'denied',"
       "'wait_for_update':500,'region':[" + ",".join("'%s'" % c for c in EU) + "]});")

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
changed = done = 0
missed = []
for dp, dn, fn in os.walk(root):
    dn[:] = [d for d in dn if d not in ('.git', '__pycache__', 'node_modules')]
    for f in fn:
        if not f.endswith(('.html', '.jinja2', '.py')):
            continue
        p = os.path.join(dp, f)
        if os.path.abspath(p) == os.path.abspath(__file__):
            continue
        with open(p, encoding='utf-8') as fh:
            s = fh.read()
        if NEW in s:
            done += 1
        elif OLD in s:
            with open(p, 'w', encoding='utf-8', newline='') as fh:
                fh.write(s.replace(OLD, NEW))
            changed += 1
        elif "'consent','default'" in s or 'googletagmanager' in s:
            missed.append(os.path.relpath(p, root))

print('Modifies :', changed, '| deja OK :', done)
if missed:
    print('A verifier a la main (GA present mais ligne differente) :')
    for m in missed:
        print('  ', m)
