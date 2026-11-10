/* ScalaBass — lien « fiche complète » des applis vers la page dédiée
   (/fr/gammes/re/dorian/, /en/chords-guitar/c/maj7/ …) de la gamme, de
   l'arpège ou de l'accord affiché. Relie les fiches au reste du site.
   Usage : <script src="fiche-link.js" data-kind="scale-bass" defer></script>
   data-kind : scale-bass | scale-guitar | arp-bass | arp-guitar | chord-guitar */
(function () {
  'use strict';
  var tag = document.currentScript, kind = tag && tag.getAttribute('data-kind');
  var K = {
    'scale-bass':   { fr: 'fr/gammes',          en: 'en/scales',           id: function () { return state.scaleId; }, after: '#scale-text',  t: ['Fiche complète de cette gamme : tablature, accords, conseils de travail', 'Full sheet for this scale: tab, chords, practice tips'] },
    'scale-guitar': { fr: 'fr/gammes-guitare',  en: 'en/scales-guitar',    id: function () { return state.scaleId; }, after: '#scale-text',  t: ['Fiche complète de cette gamme : tablature, accords, conseils de travail', 'Full sheet for this scale: tab, chords, practice tips'] },
    'arp-bass':     { fr: 'fr/arpeges-basse',   en: 'en/arpeggios-bass',   id: function () { return state.arpId; },   after: 'header .lede', t: ['Fiche complète de cet arpège : manche, tablature, conseils de travail', 'Full sheet for this arpeggio: fretboard, tab, practice tips'] },
    'arp-guitar':   { fr: 'fr/arpeges-guitare', en: 'en/arpeggios-guitar', id: function () { return state.arpId; },   after: 'header .lede', t: ['Fiche complète de cet arpège : manche, tablature, conseils de travail', 'Full sheet for this arpeggio: fretboard, tab, practice tips'] },
    'chord-guitar': { fr: 'fr/accords-guitare', en: 'en/chords-guitar',    id: function () { return state.chordId; }, after: 'header .lede', t: ['Fiche complète de cet accord : notes, positions, conseils de travail', 'Full sheet for this chord: notes, positions, practice tips'] }
  }[kind];
  if (!K) return;
  var FR = ['do', 're-bemol', 're', 'mi-bemol', 'mi', 'fa', 'fa-diese', 'sol', 'la-bemol', 'la', 'si-bemol', 'si'];
  var EN = ['c', 'db', 'd', 'eb', 'e', 'f', 'f-sharp', 'g', 'ab', 'a', 'bb', 'b'];
  // identifiants d'arpèges de l'appli → ceux des fiches
  var ARP = { '9': 'dom9', '11': 'dom11', '13': 'dom13', 'm9': 'min9', 'm11': 'min11', 'm13': 'min13', 'maj7#11': 'maj7sharp11' };
  var ARP_OK = 'aug aug7 dim dim7 dom11 dom13 dom7 dom7b5 dom7sus4 dom9 halfdim maj maj13 maj6 maj7 maj7sharp11 maj9 min min11 min13 min6 min7 min9 minmaj7 p5 sus2 sus4'.split(' ');
  var box = null, link = null;
  function mount() {
    var ref = document.querySelector(K.after); if (!ref) return false;
    box = document.createElement('p');
    box.className = 'fiche-link';
    box.style.cssText = 'margin:14px 0 6px;font-size:14px';
    link = document.createElement('a');
    link.style.cssText = 'color:var(--brass);text-decoration:none;border-bottom:1px solid currentColor;padding-bottom:1px';
    box.appendChild(link);
    ref.parentNode.insertBefore(box, ref.nextSibling);
    return true;
  }
  function update() {
    try {
      if (!box && !mount()) return;
      var id = K.id(), pc = state.rootPc;
      if (kind.indexOf('arp') === 0) { id = ARP[id] || id; if (ARP_OK.indexOf(id) < 0) id = null; }
      if (!id || pc == null) { box.style.display = 'none'; return; }
      var en = false; try { en = localStorage.getItem('sblang') === 'en'; } catch (e) { }
      link.href = '/' + (en ? K.en : K.fr) + '/' + (en ? EN : FR)[((pc % 12) + 12) % 12] + '/' + String(id).replace(/_/g, '-') + '/';
      link.textContent = K.t[en ? 1 : 0] + ' →';
      box.style.display = '';
    } catch (e) { if (box) box.style.display = 'none'; }
  }
  // l'appli redessine tout par render() : on s'y accroche
  var orig = window.render;
  if (typeof orig === 'function') {
    window.render = function () { var r = orig.apply(this, arguments); update(); return r; };
  }
  update();
})();
