/* ================================================================
 * sb-audio.js — ScalaBass / ScalaGuitare — moteur audio des outils
 * (métronome, groove, accordeur)
 *
 * Expose window.SBA :
 *   ctx(), resume(), setVol(bus,v)            contexte + volumes (click/drums/bass/guitar/tone)
 *   click(t,level,kind,soft)                   sons de métronome (synthétisés)
 *   drum(name,t,vel) / DRUM_STYLES             batterie synthétisée (kick/snare/hat/ohat/rim)
 *   loadInstrument('bass'|'guitar')            vrais samples via soundfont-player (CDN gleitz)
 *   note(kind,midi,t,dur,vel)                  basse/guitare : sample si chargé, sinon synthé
 *   strum(kind,midis,t,opts)                   accord gratté
 *   tone(freq,t,dur)                           note de référence (accordeur)
 *   Clock(cb)                                  séquenceur à anticipation (« two clocks »)
 *   draw(t,fn)                                 callback visuel synchronisé sur l'horloge audio
 *
 * Dépendance optionnelle : soundfont-player (CDN) pour les samples réels.
 * Sans réseau, tout fonctionne avec le repli synthétisé.
 * ================================================================ */
(function (g) {
  'use strict';
  const SBA = {};
  let ctx = null, master = null, noiseBuf = null;
  const buses = {};

  SBA.ctx = function () {
    if (!ctx) {
      const AC = g.AudioContext || g.webkitAudioContext;
      ctx = new AC({ latencyHint: 'interactive' });
      master = ctx.createGain(); master.gain.value = 0.9;
      const comp = ctx.createDynamicsCompressor();
      comp.threshold.value = -10; comp.knee.value = 12; comp.ratio.value = 6;
      comp.attack.value = 0.003; comp.release.value = 0.15;
      master.connect(comp); comp.connect(ctx.destination);
      ['click', 'drums', 'bass', 'guitar', 'tone'].forEach(n => {
        const b = ctx.createGain(); b.gain.value = 0.6; b.connect(master); buses[n] = b;
      });
      noiseBuf = ctx.createBuffer(1, ctx.sampleRate, ctx.sampleRate);
      const d = noiseBuf.getChannelData(0);
      for (let i = 0; i < d.length; i++) d[i] = Math.random() * 2 - 1;
    }
    return ctx;
  };
  SBA.resume = async function () {
    const c = SBA.ctx();
    if (c.state !== 'running') { try { await c.resume(); } catch (e) { } }
    return c;
  };
  SBA.setVol = function (bus, v) {
    SBA.ctx();
    buses[bus].gain.setTargetAtTime(Math.max(0, v), ctx.currentTime, 0.02);
  };
  SBA.midiToFreq = m => 440 * Math.pow(2, (m - 69) / 12);

  /* ---------- enveloppes & blocs ---------- */
  function amp(t, peak, decay, attack) {
    const gn = ctx.createGain();
    attack = attack || 0.001;
    gn.gain.setValueAtTime(0.0001, t);
    gn.gain.exponentialRampToValueAtTime(Math.max(peak, 0.0002), t + attack);
    gn.gain.exponentialRampToValueAtTime(0.0001, t + attack + decay);
    return gn;
  }
  function osc(type, f0, t, dur, f1) {
    const o = ctx.createOscillator(); o.type = type;
    o.frequency.setValueAtTime(f0, t);
    if (f1) o.frequency.exponentialRampToValueAtTime(f1, t + dur * 0.5);
    o.start(t); o.stop(t + dur + 0.05);
    return o;
  }
  function noise(t, dur, type, freq, q) {
    const s = ctx.createBufferSource(); s.buffer = noiseBuf;
    s.loop = true;
    const f = ctx.createBiquadFilter(); f.type = type; f.frequency.value = freq; f.Q.value = q || 0.7;
    s.connect(f);
    s.start(t, Math.random() * 0.5); s.stop(t + dur + 0.05);
    return f;
  }

  /* ---------- clics de métronome ---------- */
  const CLICKS = {
    bois:    { f: [900, 1250, 1700], d: 0.05, type: 'sine' },
    bip:     { f: [880, 1320, 1760], d: 0.07, type: 'sine' },
    clave:   { f: [1800, 2300, 2900], d: 0.035, type: 'triangle' },
    cloche:  { f: [660, 990, 1320], d: 0.4, type: 'sine', partial: 2.76 },
    charley: { noise: true, d: 0.05 },
  };
  SBA.CLICK_KINDS = { bois: 'Bois', bip: 'Bip', clave: 'Clave', cloche: 'Cloche', charley: 'Charley' };

  /* level 1 = faible, 2 = moyen, 3 = fort ; soft = subdivision (plus discret) */
  SBA.click = function (t, level, kind, soft) {
    if (!level) return;
    SBA.ctx();
    const cfg = CLICKS[kind] || CLICKS.bois;
    const vel = [0, 0.4, 0.7, 1][level] * (soft ? 0.5 : 1);
    if (cfg.noise) {
      const f = noise(t, cfg.d * 2, 'highpass', soft ? 6000 : 7500 + level * 600, 0.8);
      const a = amp(t, vel * 0.9, cfg.d * (level === 3 ? 1.6 : 1));
      f.connect(a); a.connect(buses.click);
      return;
    }
    const f0 = cfg.f[level - 1] * (soft ? 0.82 : 1);
    const a = amp(t, vel, cfg.d);
    const o = osc(cfg.type, f0, t, cfg.d + 0.02);
    o.connect(a);
    if (cfg.partial) { const o2 = osc('sine', f0 * cfg.partial, t, cfg.d); const g2 = ctx.createGain(); g2.gain.value = 0.4; o2.connect(g2); g2.connect(a); }
    a.connect(buses.click);
  };

  /* ---------- batterie synthétisée ---------- */
  SBA.drum = function (name, t, vel) {
    SBA.ctx();
    vel = vel == null ? 1 : vel;
    const out = buses.drums;
    if (name === 'kick') {
      const a = amp(t, 1.0 * vel, 0.32);
      const o = osc('sine', 165, t, 0.3, 46); o.connect(a); a.connect(out);
      const f = noise(t, 0.02, 'lowpass', 900); const a2 = amp(t, 0.35 * vel, 0.018); f.connect(a2); a2.connect(out);
    } else if (name === 'snare') {
      const f = noise(t, 0.2, 'bandpass', 2300, 0.7); const a = amp(t, 0.7 * vel, 0.17); f.connect(a); a.connect(out);
      const o = osc('triangle', 190, t, 0.12, 140); const a2 = amp(t, 0.5 * vel, 0.1); o.connect(a2); a2.connect(out);
    } else if (name === 'hat' || name === 'ohat') {
      const open = name === 'ohat';
      const f = noise(t, open ? 0.3 : 0.07, 'highpass', 7200, 0.6);
      const a = amp(t, (open ? 0.32 : 0.28) * vel, open ? 0.24 : 0.045); f.connect(a); a.connect(out);
    } else if (name === 'rim') {
      const o = osc('triangle', 1750, t, 0.05); const a = amp(t, 0.45 * vel, 0.04); o.connect(a); a.connect(out);
      const f = noise(t, 0.03, 'bandpass', 3000, 1); const a2 = amp(t, 0.25 * vel, 0.03); f.connect(a2); a2.connect(out);
    }
  };

  /* grille 16 doubles-croches : x = fort, o = moyen, g = fantôme, . = vide */
  const R = s => s.split('').map(c => c === 'x' ? 1 : c === 'o' ? 0.55 : c === 'g' ? 0.28 : 0);
  SBA.DRUM_STYLES = {
    rock:   { label: 'Rock',          k: R('x.......x.o.....'), s: R('....x.......x...'), h: R('xoxoxoxoxoxoxoxo') },
    pop:    { label: 'Pop',           k: R('x.....o.x.....o.'), s: R('....x.......x...'), h: R('xoxoxoxoxoxoxoxo') },
    funk:   { label: 'Funk',          k: R('x.....x.x.x...o.'), s: R('....x..g.g..x...'), h: R('xoxoxoxoxoxoxoxo') },
    disco:  { label: 'Disco',         k: R('x...x...x...x...'), s: R('....x.......x...'), h: R('o...o...o...o...'), oh: R('..x...x...x...x.') },
    reggae: { label: 'Reggae',        k: R('........x.......'), r: R('........x.......'), h: R('x.o.x.o.x.o.x.o.') },
    blues:  { label: 'Blues shuffle', k: R('x.......x.o.....'), s: R('....x.......x...'), h: R('x.o.x.o.x.o.x.o.'), swing: 100 },
  };
  SBA.drumStep = function (styleId, step, t, vol) {
    const st = SBA.DRUM_STYLES[styleId]; if (!st) return;
    const v = vol == null ? 1 : vol;
    if (st.k && st.k[step]) SBA.drum('kick', t, st.k[step] * v);
    if (st.s && st.s[step]) SBA.drum('snare', t, st.s[step] * v);
    if (st.r && st.r[step]) SBA.drum('rim', t, st.r[step] * v);
    if (st.h && st.h[step]) SBA.drum('hat', t, st.h[step] * v);
    if (st.oh && st.oh[step]) SBA.drum('ohat', t, st.oh[step] * v);
  };

  /* ---------- basse / guitare : samples (soundfont) + repli synthétisé ---------- */
  const FONTS = { bass: 'electric_bass_finger', guitar: 'acoustic_guitar_steel' };
  SBA.FONTS = FONTS;
  const loaded = {}, loading = {};
  SBA.status = {};          // 'loading' | 'ready' | 'synth'
  SBA.onStatus = null;
  function setStatus(kind, s) { SBA.status[kind] = s; if (SBA.onStatus) SBA.onStatus(kind, s); }

  SBA.setFont = function (kind, name) { FONTS[kind] = name; delete loaded[kind]; delete loading[kind]; };

  SBA.loadInstrument = function (kind) {
    if (loaded[kind]) return Promise.resolve(loaded[kind]);
    if (loading[kind]) return loading[kind];
    SBA.ctx();
    if (!g.Soundfont) { setStatus(kind, 'synth'); return Promise.resolve(null); }
    setStatus(kind, 'loading');
    const name = FONTS[kind];
    const load = g.Soundfont.instrument(ctx, name, {
      soundfont: 'MusyngKite', format: 'mp3', destination: buses[kind], gain: kind === 'bass' ? 3.2 : 2.4,
      nameToUrl: (n, sf, fmt) => `https://gleitz.github.io/midi-js-soundfonts/${sf}/${n}-${fmt}.js`,
    });
    const timeout = new Promise((_, rej) => setTimeout(() => rej(new Error('timeout')), 12000));
    loading[kind] = Promise.race([load, timeout]).then(inst => {
      loaded[kind] = inst; setStatus(kind, 'ready'); return inst;
    }).catch(() => { delete loading[kind]; setStatus(kind, 'synth'); return null; });
    return loading[kind];
  };

  function synthNote(kind, midi, t, dur, vel) {
    const f = SBA.midiToFreq(midi);
    const out = buses[kind];
    const lp = ctx.createBiquadFilter(); lp.type = 'lowpass'; lp.Q.value = 1.2;
    const a = ctx.createGain();
    a.gain.setValueAtTime(0.0001, t);
    a.gain.exponentialRampToValueAtTime(Math.max(0.0002, vel * (kind === 'bass' ? 0.9 : 0.5)), t + 0.006);
    a.gain.exponentialRampToValueAtTime(0.0001, t + Math.max(dur, 0.12) + (kind === 'bass' ? 0.12 : 0.5));
    if (kind === 'bass') {
      lp.frequency.setValueAtTime(1100, t); lp.frequency.exponentialRampToValueAtTime(260, t + 0.25);
      const o1 = osc('triangle', f, t, dur + 0.3), o2 = osc('sine', f / 2, t, dur + 0.3);
      const g2 = ctx.createGain(); g2.gain.value = 0.5;
      o1.connect(lp); o2.connect(g2); g2.connect(lp);
    } else {
      lp.frequency.setValueAtTime(4200, t); lp.frequency.exponentialRampToValueAtTime(900, t + 0.5);
      const o1 = osc('sawtooth', f, t, dur + 0.6), o2 = osc('sawtooth', f * 1.004, t, dur + 0.6);
      o1.connect(lp); o2.connect(lp);
    }
    lp.connect(a); a.connect(out);
  }

  SBA.note = function (kind, midi, t, dur, vel) {
    SBA.ctx();
    vel = vel == null ? 0.9 : vel;
    const inst = loaded[kind];
    if (inst) inst.play(midi, t, { duration: dur, gain: vel });
    else synthNote(kind, midi, t, dur, vel);
  };

  SBA.strum = function (kind, midis, t, o) {
    o = o || {};
    const gap = o.gap == null ? 0.012 : o.gap;
    const list = o.down === false ? midis.slice().reverse() : midis;
    list.forEach((m, i) => SBA.note(kind, m, t + i * gap, o.dur || 0.5, (o.vel == null ? 0.8 : o.vel) * (1 - i * 0.03)));
  };

  /* ---------- note de référence (accordeur) ---------- */
  let toneNodes = null;
  SBA.tone = function (freq, dur) {
    SBA.ctx(); SBA.stopTone();
    const t = ctx.currentTime;
    const a = ctx.createGain();
    a.gain.setValueAtTime(0.0001, t);
    a.gain.exponentialRampToValueAtTime(0.7, t + 0.03);
    a.gain.setValueAtTime(0.7, t + dur - 0.2);
    a.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    const o1 = osc('sine', freq, t, dur), o2 = osc('triangle', freq, t, dur);
    const g2 = ctx.createGain(); g2.gain.value = 0.25;
    o1.connect(a); o2.connect(g2); g2.connect(a); a.connect(buses.tone);
    toneNodes = [o1, o2, a];
  };
  SBA.stopTone = function () {
    if (!toneNodes) return;
    try {
      const [o1, o2, a] = toneNodes; const t = ctx.currentTime;
      a.gain.cancelScheduledValues(t); a.gain.setValueAtTime(Math.max(a.gain.value, 0.0002), t);
      a.gain.exponentialRampToValueAtTime(0.0001, t + 0.05);
      o1.stop(t + 0.08); o2.stop(t + 0.08);
    } catch (e) { }
    toneNodes = null;
  };

  /* ---------- horloge de séquencement (anticipation) ---------- */
  /* cb(index, time) planifie le pas puis renvoie sa durée en secondes. */
  SBA.Clock = function (cb) {
    let timer = null, next = 0, i = 0;
    this.running = false;
    this.start = function (delay) {
      SBA.ctx(); this.stop();
      next = ctx.currentTime + (delay == null ? 0.08 : delay); i = 0; this.running = true;
      const tick = () => {
        while (next < ctx.currentTime + 0.14) { const d = cb(i, next); next += d; i++; }
      };
      tick(); timer = setInterval(tick, 25);
    };
    this.stop = function () { clearInterval(timer); timer = null; this.running = false; };
  };

  /* ---------- file de callbacks visuels ---------- */
  const q = []; let raf = 0;
  function loop() {
    const lat = ctx ? (ctx.outputLatency || ctx.baseLatency || 0) : 0;
    const now = ctx ? ctx.currentTime - lat : 0;
    for (let k = 0; k < q.length;) { if (q[k].t <= now) q.splice(k, 1)[0].fn(); else k++; }
    raf = q.length ? requestAnimationFrame(loop) : 0;
  }
  SBA.draw = function (t, fn) { q.push({ t, fn }); if (!raf) raf = requestAnimationFrame(loop); };
  SBA.clearDraw = function () { q.length = 0; };

  g.SBA = SBA;
})(window);
