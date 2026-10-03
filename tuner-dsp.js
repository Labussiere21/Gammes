/* ================================================================
 * tuner-dsp.js — détection de hauteur (algorithme YIN) pour l'accordeur
 * Réf. : de Cheveigné & Kawahara, « YIN, a fundamental frequency
 * estimator for speech and music », JASA 2002.
 *
 * TunerDSP.yin(samples, sampleRate, minHz, maxHz)
 *   → { freq, prob } ou null si aucune hauteur fiable
 *
 * Le signal est sous-échantillonné (÷2 ou ÷4) pour garder un coût de calcul
 * faible même sur les basses (Si grave d'une basse 5 cordes ≈ 30,9 Hz), puis
 * la période est affinée par interpolation parabolique.
 * ================================================================ */
(function (g) {
  'use strict';
  function yin(x, sr, minF, maxF) {
    const D = sr >= 88000 ? 4 : sr >= 32000 ? 2 : 1;
    const n = Math.floor(x.length / D);
    const y = new Float32Array(n);
    for (let i = 0; i < n; i++) { let s = 0; for (let k = 0; k < D; k++) s += x[i * D + k]; y[i] = s / D; }
    const fs = sr / D;
    const tauMin = Math.max(2, Math.floor(fs / maxF));
    const tauMax = Math.min(Math.floor(fs / minF), Math.floor(n * 0.6));
    const W = n - tauMax;
    if (W < tauMax || tauMax <= tauMin + 2) return null;

    const d = new Float32Array(tauMax + 1);
    for (let tau = 1; tau <= tauMax; tau++) {
      let s = 0;
      for (let j = 0; j < W; j++) { const e = y[j] - y[j + tau]; s += e * e; }
      d[tau] = s;
    }
    // différence cumulée normalisée moyenne
    const c = new Float32Array(tauMax + 1);
    c[0] = 1; let run = 0;
    for (let tau = 1; tau <= tauMax; tau++) { run += d[tau]; c[tau] = run > 0 ? d[tau] * tau / run : 1; }

    const TH = 0.15;
    let tau = -1;
    for (let t = tauMin; t < tauMax; t++) {
      if (c[t] < TH) { while (t + 1 < tauMax && c[t + 1] < c[t]) t++; tau = t; break; }
    }
    if (tau < 0) {            // pas de creux net : on prend le minimum global s'il est acceptable
      let m = 1, mt = -1;
      for (let t = tauMin; t < tauMax; t++) if (c[t] < m) { m = c[t]; mt = t; }
      if (mt < 0 || m > 0.35) return null;
      tau = mt;
    }
    // interpolation parabolique
    let t2 = tau;
    if (tau > 1 && tau < tauMax) {
      const s0 = c[tau - 1], s1 = c[tau], s2 = c[tau + 1];
      const den = 2 * (s0 - 2 * s1 + s2);
      if (Math.abs(den) > 1e-12) t2 = tau + (s0 - s2) / den;
    }
    return { freq: fs / t2, prob: 1 - c[tau] };
  }
  /* Fondamentale faible (micro de PC/téléphone qui coupe les graves) : YIN peut
   * « s'accrocher » à un harmonique (ex. Mi grave 41,2 Hz → Si à 123,6 Hz = 3e harmonique).
   * On teste si f est en réalité le m-ième harmonique de f/m : l'énergie doit alors
   * exister aux fréquences f/m, 2f/m, … (série harmonique complète). */
  function mag(x, sr, f) {
    const n = x.length, w = 2 * Math.PI * f / sr, cw = 2 * Math.cos(w);
    let s1 = 0, s2 = 0;
    for (let i = 0; i < n; i++) {
      const h = 0.5 - 0.5 * Math.cos(2 * Math.PI * i / (n - 1));
      const s0 = x[i] * h + cw * s1 - s2; s2 = s1; s1 = s0;
    }
    return Math.sqrt(Math.max(0, s1 * s1 + s2 * s2 - cw * s1 * s2));
  }
  function fixSub(x, sr, f, minHz) {
    const m0 = mag(x, sr, f);
    if (m0 <= 0) return f;
    for (const m of [4, 3, 2]) {          // on essaie d'abord le plus grand diviseur
      const F = f / m;
      if (F < minHz) continue;
      let ok = true;
      const mF = mag(x, sr, F);
      if (mF < 0.05 * m0) ok = false;
      for (let k = 2; ok && k < m; k++) if (mag(x, sr, F * k) < 0.12 * m0) ok = false;
      if (ok) {
        // affinage : le pic réel est proche de F ; on prend le meilleur parmi ±1,5 %
        let bf = F, bm = mF;
        for (let d = -0.015; d <= 0.0151; d += 0.003) { const v = mag(x, sr, F * (1 + d)); if (v > bm) { bm = v; bf = F * (1 + d); } }
        return bf;
      }
    }
    return f;
  }
  g.TunerDSP = { yin, fixSub };
  if (typeof module !== 'undefined') module.exports = g.TunerDSP;
})(typeof window !== 'undefined' ? window : globalThis);
