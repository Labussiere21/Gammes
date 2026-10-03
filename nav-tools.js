/* ================================================================
 * nav-tools.js — comportement du menu « Outils » (tactile, mobile) et
 * traduction FR/EN de ses libellés. Fonctionne par délégation d'événements,
 * donc aussi avec une navigation construite dynamiquement (sb-tools.js).
 * ================================================================ */
(function () {
  'use strict';
  var PAIRS = [['Outils', 'Tools'], ['Métronome', 'Metronome'], ['Accordeur', 'Tuner'], ['Grilles', 'Chord charts']];
  function lang() { try { return localStorage.getItem('sblang') || 'fr'; } catch (e) { return 'fr'; } }
  function translate() {
    var en = lang() === 'en';
    document.querySelectorAll('.nav-drop a').forEach(function (a) {
      PAIRS.forEach(function (p) { if (a.textContent === p[en ? 0 : 1]) a.textContent = p[en ? 1 : 0]; });
    });
  }
  function place(d) {
    var m = d.querySelector('.nav-menu'), t = d.querySelector('.nav-link');
    if (!m || !t) return;
    if (window.innerWidth > 760) { m.style.top = m.style.left = ''; return; }
    var r = t.getBoundingClientRect();
    m.style.top = (r.bottom + 6) + 'px';
    m.style.left = Math.max(8, Math.min(window.innerWidth - m.offsetWidth - 8, r.right - m.offsetWidth)) + 'px';
  }
  function closeAll(except) {
    document.querySelectorAll('.nav-drop.open').forEach(function (d) { if (d !== except) d.classList.remove('open'); });
  }
  document.addEventListener('click', function (e) {
    var top = e.target.closest ? e.target.closest('.nav-drop > .nav-link') : null;
    var drop = top ? top.parentNode : null;
    closeAll(drop);
    if (top) {
      var touch = window.matchMedia('(hover:none)').matches || window.innerWidth <= 760;
      if (touch && !drop.classList.contains('open')) {
        e.preventDefault(); drop.classList.add('open');
        requestAnimationFrame(function () { place(drop); });
      }
    }
    if (e.target.closest && e.target.closest('#lang-seg')) setTimeout(translate, 0);
  });
  window.addEventListener('resize', function () { document.querySelectorAll('.nav-drop.open').forEach(place); });
  window.addEventListener('scroll', function () { if (window.innerWidth <= 760) closeAll(); }, { passive: true });
  document.addEventListener('DOMContentLoaded', translate);
  window.SBNavTranslate = translate;
})();
