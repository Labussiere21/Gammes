/* ScalaBass — lecture audio des pages de gammes, d'arpèges et d'accords.
   Boutons [data-play="midi,midi,…"] : data-mode="chord" joue les notes ensemble
   (égrenées), sinon la suite monte puis redescend. Synthèse Web Audio, aucun fichier. */
(function () {
  var ctx = null, stopAt = 0, current = null;
  function freq(m) { return 440 * Math.pow(2, (m - 69) / 12); }
  function tone(m, t, dur, bass) {
    var o = ctx.createOscillator(), o2 = ctx.createOscillator(), g = ctx.createGain(), f = ctx.createBiquadFilter();
    o.type = 'triangle'; o2.type = 'sawtooth';
    o.frequency.value = freq(m); o2.frequency.value = freq(m);
    var mix = ctx.createGain(); mix.gain.value = bass ? 0.12 : 0.2;
    f.type = 'lowpass'; f.frequency.setValueAtTime(bass ? 900 : 2600, t);
    f.frequency.exponentialRampToValueAtTime(bass ? 300 : 700, t + dur);
    g.gain.setValueAtTime(0.0001, t);
    g.gain.exponentialRampToValueAtTime(0.32, t + 0.012);
    g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    o.connect(f); o2.connect(mix); mix.connect(f); f.connect(g); g.connect(ctx.destination);
    o.start(t); o2.start(t); o.stop(t + dur + 0.05); o2.stop(t + dur + 0.05);
  }
  function play(btn) {
    var AC = window.AudioContext || window.webkitAudioContext;
    if (!AC) return;
    if (!ctx) ctx = new AC();
    if (ctx.state === 'suspended') ctx.resume();
    if (current) current.classList.remove('on');
    var notes = (btn.getAttribute('data-play') || '').split(',').map(Number).filter(function (n) { return n > 0; });
    if (!notes.length) return;
    var bass = btn.getAttribute('data-inst') === 'bass';
    var t = ctx.currentTime + 0.06, total;
    if (btn.getAttribute('data-mode') === 'chord') {
      notes.forEach(function (m, i) { tone(m, t + i * 0.045, 2.2, false); });
      total = 2.4;
    } else {
      var seq = notes.concat(notes.slice(0, -1).reverse()), step = 0.34;
      seq.forEach(function (m, i) { tone(m, t + i * step, step * 1.6, bass); });
      total = seq.length * step + 0.4;
    }
    current = btn; btn.classList.add('on');
    var mine = ++stopAt;
    setTimeout(function () { if (mine === stopAt) btn.classList.remove('on'); }, total * 1000);
  }
  document.addEventListener('click', function (e) {
    var b = e.target.closest ? e.target.closest('[data-play]') : null;
    if (b) play(b);
  });
})();
