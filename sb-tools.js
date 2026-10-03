/* ================================================================
 * sb-tools.js — ScalaBass / ScalaSix — coque commune des pages outils
 * (métronome, accordeur, grilles) : bascule Basse/Guitare, navigation,
 * logo, menu « Outils », traductions de la navigation.
 *
 * Pages outils = pages partagées (comme cadences.html). L'instrument est
 * mémorisé dans sessionStorage/localStorage 'sbinst' ('bass' | 'guitar'),
 * ou forcé par ?inst=guitar.
 * ================================================================ */
(function (g) {
  'use strict';

  const NAV = {
    bass: [
      ['index.html', 'Manche'], ['gammes.html', 'Gammes'], ['arpeges-basse.html', 'Arpèges'],
      ['accords-basse.html', 'Accords'], ['intervalles.html', 'Intervalles'], ['cadences.html', 'Cadences'],
      ['analyse.html', 'Analyse'], ['quintes.html', 'Tonalités'],
    ],
    guitar: [
      ['manche-guitare.html', 'Manche'], ['gammes-guitare.html', 'Gammes'], ['arpeges-guitare.html', 'Arpèges'],
      ['accords-guitare.html', 'Accords'], ['intervalles-guitare.html', 'Intervalles'], ['cadences-guitare.html', 'Cadences'],
      ['analyse-guitare.html', 'Analyse'], ['tonalites-guitare.html', 'Tonalités'],
    ],
  };
  const EN = {
    'Manche': 'Fretboard', 'Gammes': 'Scales', 'Arpèges': 'Arpeggios', 'Accords': 'Chords', 'Intervalles': 'Intervals',
    'Cadences': 'Cadences', 'Analyse': 'Analyse', 'Tonalités': 'Key Index',
    'Outils': 'Tools', 'Métronome': 'Metronome', 'Accordeur': 'Tuner', 'Grilles': 'Chord charts',
  };
  const TOOLS = [['metronome.html', 'Métronome', '/en/metronome/', 'metronome'], ['accordeur.html', 'Accordeur', '/en/tuner/', 'accordeur'], ['grilles.html', 'Grilles', '/en/chord-charts/', 'grilles']];
  const thref = t => lang() === 'en' ? t[2] : t[0];
  const BRAND = { bass: 'ScalaBass', guitar: 'ScalaSix' };
  const LOGO = { bass: 'img/logobasse.png', guitar: 'img/logoguitare.png' };

  const lang = () => { try { return localStorage.getItem('sblang') || 'fr'; } catch (e) { return 'fr'; } };
  const tr = s => (lang() === 'en' && EN[s]) || s;

  function readInst() {
    try {
      const q = new URLSearchParams(location.search).get('inst');
      if (q === 'guitar' || q === 'bass') return q;
      return sessionStorage.getItem('sbinst') || localStorage.getItem('sbinst') || 'bass';
    } catch (e) { return 'bass'; }
  }

  let inst = 'bass';
  const page = () => document.body.dataset.tool || '';

  function buildNav() {
    const nav = document.getElementById('site-nav'); if (!nav) return;
    nav.innerHTML = '';
    NAV[inst].forEach(([href, label]) => {
      const a = document.createElement('a'); a.href = href; a.className = 'nav-link'; a.textContent = tr(label);
      nav.appendChild(a);
    });
    const drop = document.createElement('div'); drop.className = 'nav-drop';
    const top = document.createElement('a'); top.href = thref(TOOLS[0]); top.className = 'nav-link active'; top.textContent = tr('Outils');
    top.setAttribute('aria-haspopup', 'true');
    drop.appendChild(top);
    const menu = document.createElement('div'); menu.className = 'nav-menu';
    TOOLS.forEach(t => {
      const label = t[1];
      const a = document.createElement('a'); a.href = thref(t); a.className = 'nav-link' + (t[3] === page() ? ' active' : '');
      a.textContent = tr(label); menu.appendChild(a);
    });
    drop.appendChild(menu); nav.appendChild(drop);
  }

  function apply(i, persist) {
    inst = i;
    document.documentElement.dataset.inst = i;
    document.querySelectorAll('.inst-btn').forEach(b => b.classList.toggle('active', b.dataset.inst === i));
    const logo = document.getElementById('site-logo');
    if (logo) { logo.src = LOGO[i]; logo.alt = BRAND[i]; }
    const nm = document.getElementById('site-name'); if (nm) nm.textContent = BRAND[i];
    const fl = document.getElementById('footer-brand'); if (fl) fl.textContent = '© 2026 ' + BRAND[i];
    const meta = document.querySelector('meta[name="theme-color"]'); if (meta) meta.content = i === 'guitar' ? '#0e0608' : '#15100c';
    buildNav();
    if (persist) { try { sessionStorage.setItem('sbinst', i); localStorage.setItem('sbinst', i); } catch (e) { } }
    if (typeof g.onInstChange === 'function') g.onInstChange(i);
  }

  const SBT = {
    inst: () => inst,
    refreshNav: buildNav,
    init() {
      document.querySelectorAll('.inst-btn').forEach(b => b.addEventListener('click', () => apply(b.dataset.inst, true)));
      apply(readInst(), false);
      if (g.SB && SB.initNotationLang) SB.initNotationLang();
    },
  };
  /* appelé par music-core (initNotationLang) quand la notation/la langue change */
  g.render = function () {
    buildNav();
    if (typeof g.onNotation === 'function') g.onNotation();
  };
  /* l'URL fixe la langue (métronome.html ↔ /en/metronome/…) : changer de langue = changer de page */
  document.addEventListener('click', e => {
    const b = e.target.closest && e.target.closest('#lang-seg [data-lang]'); if (!b) return;
    const alt = document.querySelector('link[rel="alternate"][hreflang="' + b.dataset.lang + '"]'); if (!alt) return;
    const u = new URL(alt.getAttribute('href'), location.href);
    if (u.pathname !== location.pathname) setTimeout(() => { location.href = u.pathname + location.search + location.hash; }, 0);
  });
  g.SBT = SBT;
})(window);
