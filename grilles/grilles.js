/* ScalaBass — Grilles d'accords — interface (dérivé de GrilleMaker) */
(function (G) {
  "use strict";
  const M = G.Model;
  const $ = s => document.querySelector(s);
  const $$ = s => Array.from(document.querySelectorAll(s));
  const OLD_STORE = "sbgrilles:song";
  const LIB = "sbgrilles:library";
  const PREFS = "sbgrilles:prefs";

  const state = { song: null, id: null, sec: 0, sel: [0, 0], item: -1, orient: "landscape", tab: "grids" };
  let lib = { current: null, songs: {} };   // songs[id] = { song, updated }

  const uid = () => Date.now().toString(36) + Math.random().toString(36).slice(2, 7);
  const clone = o => JSON.parse(JSON.stringify(o));

  /* ====================================================== TRADUCTION FR/EN */
  // Dictionnaire de l'interface, fusionné dans M.EN pour que model.js et pdf.js le voient aussi.
  Object.assign(M.EN, {
    "Basse": "Bass", "Guitare": "Guitar",
    "Titre du morceau": "Song title", "Titre": "Title", "Artiste": "Artist", "Tonalité": "Key", "Tempo": "Tempo",
    "Note de fin": "End note", "ex. Fin sur Dm": "e.g. End on Dm",
    "Orientation du PDF": "PDF orientation", "Portrait": "Portrait", "Paysage": "Landscape",
    "Copier le lien": "Copy link", "Aperçu": "Preview", "Télécharger le PDF": "Download PDF",
    "Grilles": "Charts", "Structure": "Structure", "Morceaux": "Songs",
    "Nouveau morceau": "New song", "Ouvrir un .grille": "Open a .grille file", "Enregistrer en .grille": "Save as .grille",
    "Type de section": "Section type", "Ajouter": "Add", "Dupliquer": "Duplicate", "Supprimer": "Delete",
    "Monter": "Move up", "Descendre": "Move down",
    "Section": "Section", "N°": "No.", "Nom perso": "Custom name", "ex. Refrain de fin": "e.g. Final chorus",
    "Cellules / ligne": "Bars per row", "Lignes": "Rows",
    "Actions sur la case sélectionnée": "Actions on the selected bar",
    "Début de reprise": "Start of repeat", "Début reprise": "Repeat start",
    "Fin de reprise": "End of repeat", "Fin reprise": "Repeat end", "Répéter ×": "Repeat ×",
    "Case 1.": "1st ending", "Case 2.": "2nd ending",
    "Même mesure que la précédente": "Same bar as the previous one", "Même mesure": "Same bar", "Vider la case": "Clear bar",
    "mesures": "bars", "Calcul auto": "Auto count", "Mesures (manuel)": "Bars (manual)",
    "Commentaire": "Comment", "imprimé sous la grille": "printed under the chart",
    "Type de partie": "Part type", "Ajouter une partie": "Add a part", "Renuméroter": "Renumber",
    "Partie sélectionnée": "Selected part", "Grille jouée": "Chart played", "Mesures de la grille": "Chart's bar count",
    "Mesures": "Bars", "Note": "Note", "ex. fin sur Dm": "e.g. end on Dm",
    "Avancer": "Move earlier", "Reculer": "Move later", "Retirer": "Remove",
    "Générer la structure": "Generate the structure", "Générer": "Generate",
    "Chercher un titre ou un artiste": "Search by title or artist", "Chercher un morceau": "Search for a song",
    "Sur cet appareil": "On this device", "Exemples": "Examples",
    // dynamique
    "Ligne {0}, mesure {1}": "Row {0}, bar {1}", "indication": "cue", "Indication ligne {0}, mesure {1}": "Cue, row {0}, bar {1}",
    "Stockage du navigateur plein : enregistre tes morceaux en .grille.": "Browser storage is full: save your songs as .grille files.",
    "Des cases remplies vont être supprimées. Continuer ?": "Some filled bars will be deleted. Continue?",
    "{0} créé à partir de {1}": "{0} created from {1}",
    "Supprimer la grille « {0} » ?": "Delete the chart “{0}”?",
    "sans grille": "no chart", "(aucune)": "(none)",
    "Remplacer la structure actuelle ?": "Replace the current structure?",
    "{0} parties générées": "{0} parts generated",
    "Ajoute au moins une grille avant d'exporter.": "Add at least one chart before exporting.",
    "Impossible de charger le module PDF.": "Unable to load the PDF module.",
    "PDF téléchargé : {0}": "PDF downloaded: {0}",
    "Autorise les fenêtres pop-up pour voir l'aperçu.": "Allow pop-up windows to see the preview.",
    "Fichier .grille enregistré": ".grille file saved",
    "« {0} » ouvert": "“{0}” opened",
    "Ce fichier n'est pas un .grille valide.": "This file is not a valid .grille file.",
    "{0} parties": "{0} parts", "modifié le {0}": "edited {0}", "{0}  (en cours)": "{0}  (current)",
    "Ouvrir": "Open", "{0} (copie)": "{0} (copy)",
    "Aucun morceau ne correspond à la recherche.": "No song matches your search.",
    "Aucun morceau pour l'instant.": "No songs yet.",
    "Supprimer « {0} » de cet appareil ? Cette action est définitive.": "Delete “{0}” from this device? This cannot be undone.",
    "« {0} » supprimé": "“{0}” deleted",
    "Aucun exemple ne correspond à la recherche.": "No example matches your search.",
    "en {0}": "in {0}", "Ouvrir une copie": "Open a copy",
    "« {0} » était déjà dans tes morceaux": "“{0}” was already in your songs",
    "« {0} » ajouté à tes morceaux": "“{0}” added to your songs",
    "Lien copié : la personne qui l'ouvre récupère ce morceau.": "Link copied: whoever opens it gets this song.",
    "Copie ce lien :": "Copy this link:", "Morceau": "Song", "Morceau partagé": "Shared song",
    "Ce lien de partage est incomplet ou abîmé.": "This share link is incomplete or damaged.",
    "Nouveau morceau. Le précédent reste dans l'onglet Morceaux.": "New song. The previous one stays in the Songs tab.",
    // textes de l'exemple intégré (appliqués seulement à la copie créée en anglais)
    "Refrain de fin": "Final chorus", "Solo guitare": "Guitar solo", "syncopé": "syncopated", "Fin sur Dm": "End on Dm"
  });
  const T = M.T, F = M.F, isEn = () => M.lang() === "en";
  const TITLE_EN = "Free chord chart maker (PDF export) | ScalaBass";
  // conteneurs reconstruits par le code (exclus du parcours, retraduits via T() dans applyLang)
  const DYN = "#section-list,#grid,#flow,#i-grid,#new-type,#s-type,#item-type,#gen,#lib-local,#lib-online,#ie-title,#t-total,#m-value";
  const ATTRS = [["aria-label", "frAria"], ["placeholder", "frPh"], ["title", "frTitle"]];
  function translateDom() {
    const en = isEn(), EN = M.EN, root = document.querySelector(".wrap");
    const w = document.createTreeWalker(root, NodeFilter.SHOW_TEXT); let n; const nodes = [];
    while ((n = w.nextNode())) nodes.push(n);
    nodes.forEach(n => {
      const el = n.parentElement;
      if (!el || el.closest(DYN) || el.closest("[data-en]") || el.closest("#notation-seg,#lang-seg,#site-nav")) return;
      const raw = n.nodeValue, t = raw.trim().replace(/\s+/g, " ");
      if (n.__fr === undefined) { if (!t || !EN[t]) return; n.__fr = raw; }
      const fr = n.__fr.trim();
      n.nodeValue = en ? n.__fr.replace(fr, EN[fr.replace(/\s+/g, " ")] || fr) : n.__fr;
    });
    root.querySelectorAll("[aria-label],[placeholder],[title]").forEach(el => {
      if (el.closest("#grid,#notation-seg,#lang-seg,#site-nav")) return;   // cases de la grille : voir applyLang
      ATTRS.forEach(([a, k]) => {
        if (!el.hasAttribute(a)) return;
        if (el.dataset[k] === undefined) { const v = el.getAttribute(a); if (!EN[v]) return; el.dataset[k] = v; }
        el.setAttribute(a, en ? (EN[el.dataset[k]] || el.dataset[k]) : el.dataset[k]);
      });
    });
    root.querySelectorAll("[data-en]").forEach(el => {
      if (el.dataset.fr === undefined) el.dataset.fr = el.innerHTML;
      el.innerHTML = en ? el.dataset.en : el.dataset.fr;
    });
    const tt = document.querySelector("title");
    if (tt) { if (tt.dataset.fr === undefined) tt.dataset.fr = tt.textContent; tt.textContent = en ? TITLE_EN : tt.dataset.fr; }
    document.documentElement.lang = en ? "en" : "fr";
  }
  /** Copie de l'exemple intégré dans la langue active (n'affecte jamais un morceau déjà enregistré). */
  function localExample() {
    const ex = clone(G.EXAMPLE);
    if (!isEn()) return ex;
    ["notes"].forEach(k => { ex[k] = T(ex[k] || ""); });
    ex.sections.forEach(s => {
      s.label = T(s.label || ""); s.comment = T(s.comment || "");
      s.rows.forEach(r => r.forEach(c => { c.note = T(c.note || ""); }));
    });
    ex.structure.forEach(it => { it.label = T(it.label || ""); it.note = T(it.note || ""); });
    return ex;
  }

  // --------------------------------------------------------------- persistance
  function writeLib() {
    try { localStorage.setItem(LIB, JSON.stringify(lib)); }
    catch (e) { toast(T("Stockage du navigateur plein : enregistre tes morceaux en .grille.")); }
  }
  let saveTimer = null;
  function persist() {
    clearTimeout(saveTimer);
    saveTimer = setTimeout(() => {
      if (!state.id) return;
      lib.songs[state.id] = { song: state.song, updated: Date.now() };
      lib.current = state.id;
      writeLib();
      if (state.tab === "library") renderLocal();
    }, 300);
  }
  function savePrefs() {
    try { localStorage.setItem(PREFS, JSON.stringify({ orient: state.orient, tab: state.tab })); } catch (e) { }
  }
  function readStorage() {
    try {
      const p = JSON.parse(localStorage.getItem(PREFS) || "{}");
      if (p.orient) state.orient = p.orient;
      if (p.tab) state.tab = p.tab;
      const raw = localStorage.getItem(LIB);
      if (raw) lib = Object.assign({ current: null, songs: {} }, JSON.parse(raw));
      const old = localStorage.getItem(OLD_STORE);         // migration de la 1re version
      if (old && !Object.keys(lib.songs).length) {
        const id = uid();
        lib.songs[id] = { song: JSON.parse(old), updated: Date.now() };
        lib.current = id;
        writeLib();
        localStorage.removeItem(OLD_STORE);
      }
    } catch (e) { }
  }
  /** Ajoute un morceau à "Sur cet appareil" (ou réutilise un doublon exact) et l'ouvre. */
  function addAndOpen(song) {
    const json = JSON.stringify(song);
    const dup = Object.keys(lib.songs).find(k => JSON.stringify(M.normalize(lib.songs[k].song)) === json);
    const id = dup || uid();
    if (!dup) { lib.songs[id] = { song, updated: Date.now() }; }
    loadSong(M.normalize(clone(lib.songs[id].song)), id);
    return !!dup;
  }

  function toast(msg) {
    const t = $("#toast");
    t.textContent = msg;
    t.classList.add("show");
    clearTimeout(toast._t);
    toast._t = setTimeout(() => t.classList.remove("show"), 2600);
  }

  const fileBase = () => (state.song.title.trim() || T("grille")).replace(/[\\/:*?"<>|]+/g, "-");
  const cur = () => state.song.sections[state.sec] || null;
  const changed = () => { persist(); refreshCounts(); };

  function download(blob, name) {
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = name;
    document.body.appendChild(a);
    a.click();
    setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 1000);
  }

  // --------------------------------------------------------------- chargement
  function loadSong(song, id) {
    state.song = song;
    state.id = id || uid();
    state.sec = song.sections.length ? 0 : -1;
    state.sel = [0, 0];
    state.item = song.structure.length ? 0 : -1;
    $("#f-title").value = song.title;
    $("#f-artist").value = song.artist;
    $("#f-key").value = song.key || "";
    $("#f-tempo").value = song.tempo || "";
    $("#f-notes").value = song.notes || "";
    renderAll();
    persist();
  }

  function renderAll() {
    renderSectionList();
    renderEditor();
    renderStructure();
    refreshCounts();
  }

  // --------------------------------------------------------------- onglets
  function setTab(tab) {
    state.tab = tab;
    $$(".tab").forEach(b => b.setAttribute("aria-selected", String(b.dataset.tab === tab)));
    $("#tab-grids").hidden = tab !== "grids";
    $("#tab-structure").hidden = tab !== "structure";
    $("#tab-library").hidden = tab !== "library";
    if (tab === "structure") renderStructure();
    if (tab === "library") { renderLocal(); renderExamples(); }
    savePrefs();
  }

  function setOrient(o) {
    state.orient = o;
    $$("#orient button").forEach(b => b.setAttribute("aria-checked", String(b.dataset.orient === o)));
    savePrefs();
  }

  // --------------------------------------------------------------- liste des sections
  function renderSectionList() {
    const ol = $("#section-list");
    ol.innerHTML = "";
    state.song.sections.forEach((s, i) => {
      const li = document.createElement("li");
      const b = document.createElement("button");
      b.type = "button";
      b.setAttribute("aria-current", String(i === state.sec));
      b.innerHTML = `<span></span><small></small>`;
      b.firstChild.textContent = M.sectionName(s);
      b.lastChild.textContent = M.meas(M.sectionMeasures(s));
      b.addEventListener("click", () => { state.sec = i; state.sel = [0, 0]; renderSectionList(); renderEditor(); });
      li.appendChild(b);
      ol.appendChild(li);
    });
  }

  function refreshCounts() {
    const items = $$("#section-list li button");
    state.song.sections.forEach((s, i) => {
      if (!items[i]) return;
      items[i].firstChild.textContent = M.sectionName(s);
      items[i].lastChild.textContent = M.meas(M.sectionMeasures(s));
    });
    const s = cur();
    if (s) {
      $("#m-value").textContent = M.sectionMeasures(s);
      $("#m-manual").disabled = s.measures_auto !== false;
      if (s.measures_auto !== false) $("#m-manual").value = M.computeMeasures(s);
    }
    const total = state.song.structure.reduce((a, it) => a + M.itemMeasures(state.song, it), 0);
    $("#t-total").textContent = state.song.structure.length ? M.meas(total) : "";
  }

  // --------------------------------------------------------------- éditeur de grille
  function chordClass(input) {
    const n = M.splitChords(input.value).length;
    input.classList.toggle("small", n === 2 || input.value.length > 5);
    input.classList.toggle("tiny", n >= 3 || input.value.length > 9);
  }

  function decorate(el, c) {
    el.classList.toggle("rep-start", c.start);
    el.classList.toggle("rep-end", c.end);
    el.querySelectorAll(".badge").forEach(b => b.remove());
    if (c.volta) {
      const v = document.createElement("span");
      v.className = `badge volta v${c.volta}`;
      v.textContent = `${c.volta}.`;
      el.appendChild(v);
    }
    if (c.end && parseInt(c.times) > 2) {
      const t = document.createElement("span");
      t.className = "badge times-badge";
      t.textContent = `x${parseInt(c.times)}`;
      el.appendChild(t);
    }
  }

  function renderEditor() {
    const s = cur();
    const ed = $("#editor");
    const grid = $("#grid");
    grid.innerHTML = "";
    ed.style.opacity = s ? "" : ".4";
    ed.style.pointerEvents = s ? "" : "none";
    if (!s) { $("#m-value").textContent = "–"; return; }

    $("#s-type").value = s.type;
    $("#s-num").value = s.num;
    $("#s-label").value = s.label || "";
    $("#s-cols").value = s.cols;
    $("#s-rows").value = s.rows.length;
    $("#s-comment").value = s.comment || "";
    $("#m-auto").checked = s.measures_auto !== false;
    $("#m-manual").value = s.measures_auto !== false ? M.computeMeasures(s) : s.measures;

    grid.style.gridTemplateColumns = `auto repeat(${s.cols}, max-content)`;
    grid.style.rowGap = "24px";
    s.rows.forEach((row, r) => {
      const num = document.createElement("span");
      num.className = "rownum";
      num.textContent = r + 1;
      grid.appendChild(num);
      row.forEach((c, k) => {
        const el = document.createElement("div");
        el.className = "cell";
        el.dataset.r = r; el.dataset.c = k;
        const chord = document.createElement("input");
        chord.className = "chord";
        chord.value = c.chord;
        chord.setAttribute("aria-label", F("Ligne {0}, mesure {1}", r + 1, k + 1));
        chord.autocomplete = "off"; chord.spellcheck = false;
        chord.setAttribute("autocapitalize", "characters");
        const note = document.createElement("input");
        note.className = "note";
        note.value = c.note;
        note.placeholder = T("indication");
        note.setAttribute("aria-label", F("Indication ligne {0}, mesure {1}", r + 1, k + 1));
        el.append(chord, note);
        decorate(el, c);
        chordClass(chord);

        chord.addEventListener("input", () => { cell(r, k).chord = chord.value; chordClass(chord); changed(); });
        note.addEventListener("input", () => { cell(r, k).note = note.value; changed(); });
        [chord, note].forEach(inp => inp.addEventListener("focus", () => select(r, k)));
        el.addEventListener("mousedown", e => { if (e.target === el) { select(r, k, true); e.preventDefault(); } });
        chord.addEventListener("keydown", e => {
          if (e.key === "Enter" || (e.key === "Tab" && !e.shiftKey)) { e.preventDefault(); move(1); }
          else if (e.key === "Tab" && e.shiftKey) { e.preventDefault(); move(-1); }
        });
        grid.appendChild(el);
      });
    });
    if (!s.rows[state.sel[0]] || state.sel[1] >= s.cols) state.sel = [0, 0];
    select(state.sel[0], state.sel[1]);
    refreshCounts();
  }

  const cell = (r, k) => cur().rows[r][k];
  const cellEl = (r, k) => document.querySelector(`.cell[data-r="${r}"][data-c="${k}"]`);

  function select(r, k, focus) {
    $$(".cell.selected").forEach(e => e.classList.remove("selected"));
    state.sel = [r, k];
    const el = cellEl(r, k);
    if (!el) return;
    el.classList.add("selected");
    const c = cell(r, k);
    $("#t-times").value = parseInt(c.times) || 2;
    $$(".tool[data-act]").forEach(b => {
      const a = b.dataset.act;
      const on = (a === "start" && c.start) || (a === "end" && c.end) || (a === "v1" && c.volta === "1") || (a === "v2" && c.volta === "2");
      if (["start", "end", "v1", "v2"].includes(a)) b.setAttribute("aria-pressed", String(on));
    });
    if (focus) { const i = el.querySelector(".chord"); i.focus(); i.select(); }
  }

  function move(d) {
    const s = cur();
    let idx = state.sel[0] * s.cols + state.sel[1] + d;
    if (idx >= s.rows.length * s.cols) {
      s.rows.push(Array.from({ length: s.cols }, () => M.newCell()));
      renderEditor();
    }
    idx = Math.max(0, Math.min(idx, s.rows.length * s.cols - 1));
    select(Math.floor(idx / s.cols), idx % s.cols, true);
  }

  function act(a) {
    const s = cur();
    if (!s) return;
    const [r, k] = state.sel;
    const c = cell(r, k);
    if (a === "start") c.start = !c.start;
    if (a === "end") { c.end = !c.end; if (c.end) c.times = parseInt($("#t-times").value) || 2; }
    if (a === "v1") c.volta = c.volta === "1" ? "" : "1";
    if (a === "v2") c.volta = c.volta === "2" ? "" : "2";
    if (a === "clear") Object.assign(c, M.newCell());
    if (a === "sim") {
      c.chord = "%";
      cellEl(r, k).querySelector(".chord").value = "%";
      changed(); move(1); return;
    }
    const el = cellEl(r, k);
    if (a === "clear") { el.querySelector(".chord").value = ""; el.querySelector(".note").value = ""; }
    decorate(el, c);
    select(r, k);
    changed();
  }

  function resize() {
    const s = cur();
    const cols = Math.max(1, Math.min(8, parseInt($("#s-cols").value) || s.cols));
    const rows = Math.max(1, Math.min(24, parseInt($("#s-rows").value) || s.rows.length));
    const lost = s.rows.slice(rows).some(r => r.some(c => !M.cellIsEmpty(c))) ||
      s.rows.some(r => r.slice(cols).some(c => !M.cellIsEmpty(c)));
    if (lost && !confirm(T("Des cases remplies vont être supprimées. Continuer ?"))) {
      $("#s-cols").value = s.cols; $("#s-rows").value = s.rows.length; return;
    }
    M.resizeSection(s, cols, rows);
    renderEditor(); changed();
  }

  // --------------------------------------------------------------- actions sections
  function addSection() {
    const t = $("#new-type").value;
    const nums = state.song.sections.filter(s => s.type === t).map(s => s.num);
    let num = nums.length ? Math.max(...nums) + 1 : (M.UNNUMBERED.includes(t) ? 0 : 1);
    if (num === 1 && nums.length === 1 && nums[0] === 0) num = 2;
    state.song.sections.push(M.newSection(t, num, 4, ["Couplet", "Solo"].includes(t) ? 4 : 2));
    state.sec = state.song.sections.length - 1;
    state.sel = [0, 0];
    renderSectionList(); renderEditor(); changed();
    select(0, 0, true);
  }

  function dupSection() {
    const s = cur(); if (!s) return;
    const d = M.duplicateSection(s);
    d.num = Math.max(0, ...state.song.sections.filter(x => x.type === s.type).map(x => x.num)) + 1;
    d.label = "";
    state.song.sections.splice(state.sec + 1, 0, d);
    state.sec++;
    renderSectionList(); renderEditor(); changed();
    toast(F("{0} créé à partir de {1}", M.sectionName(d), M.sectionName(s)));
  }

  function delSection() {
    const s = cur(); if (!s) return;
    if (!confirm(F("Supprimer la grille « {0} » ?", M.sectionName(s)))) return;
    state.song.structure.forEach(it => { if (it.grid === s.id) it.grid = ""; });
    state.song.sections.splice(state.sec, 1);
    state.sec = Math.min(state.sec, state.song.sections.length - 1);
    renderSectionList(); renderEditor(); changed();
  }

  function moveSection(d) {
    const L = state.song.sections, i = state.sec;
    if (i < 0 || i + d < 0 || i + d >= L.length) return;
    [L[i], L[i + d]] = [L[i + d], L[i]];
    state.sec += d;
    renderSectionList(); changed();
  }

  function metaChanged() {
    const s = cur(); if (!s) return;
    s.type = $("#s-type").value;
    s.num = parseInt($("#s-num").value) || 0;
    s.label = $("#s-label").value;
    s.comment = $("#s-comment").value;
    changed();
  }

  // --------------------------------------------------------------- structure
  function renderStructure() {
    const S = state.song;
    const ol = $("#flow");
    ol.innerHTML = "";
    $("#flow-empty").hidden = S.structure.length > 0;
    if (state.item >= S.structure.length) state.item = S.structure.length - 1;
    S.structure.forEach((it, i) => {
      const li = document.createElement("li");
      const b = document.createElement("button");
      b.type = "button";
      b.className = "chip";
      b.setAttribute("aria-current", String(i === state.item));
      const name = M.itemName(it);
      const sec = M.findSection(S, it.grid);
      const ref = sec ? M.sectionName(sec) : "";
      const extra = [ref && ref !== name ? `= ${ref}` : (sec ? "" : T("sans grille")), (it.note || "").trim()].filter(Boolean).join(" · ");
      b.innerHTML = `<span class="name"></span><span class="m"></span><span class="ref"></span>`;
      b.children[0].textContent = name;
      b.children[1].textContent = M.meas(M.itemMeasures(S, it));
      b.children[2].textContent = extra;
      b.addEventListener("click", () => { state.item = i; renderStructure(); });
      li.appendChild(b);
      ol.appendChild(li);
    });

    const sel = $("#i-grid");
    sel.innerHTML = `<option value="">${T("(aucune)")}</option>` +
      S.sections.map(s => `<option value="${s.id}"></option>`).join("");
    S.sections.forEach((s, i) => { sel.options[i + 1].textContent = M.sectionName(s); });

    const it = S.structure[state.item];
    $("#item-editor").classList.toggle("disabled", !it);
    if (it) {
      $("#ie-title").textContent = M.itemName(it);
      $("#i-label").value = it.label || "";
      $("#i-grid").value = it.grid || "";
      $("#i-auto").checked = it.measures_auto !== false;
      $("#i-meas").value = M.itemMeasures(S, it);
      $("#i-meas").disabled = it.measures_auto !== false && !!it.grid;
      $("#i-note").value = it.note || "";
    } else {
      $("#ie-title").textContent = T("Partie sélectionnée");
    }
    refreshCounts();
  }

  function itemChanged() {
    const it = state.song.structure[state.item];
    if (!it) return;
    it.label = $("#i-label").value;
    it.grid = $("#i-grid").value;
    it.note = $("#i-note").value;
    it.measures_auto = $("#i-auto").checked;
    if (!it.measures_auto || !it.grid) it.measures = parseInt($("#i-meas").value) || 0;
    const active = document.activeElement && document.activeElement.id;
    renderStructure();
    if (active) { const el = document.getElementById(active); if (el) { el.focus(); if (el.setSelectionRange && el.type !== "number") el.setSelectionRange(el.value.length, el.value.length); } }
    changed();
  }

  function addItem() {
    const t = $("#item-type").value;
    const L = state.song.structure;
    let n = M.nextNum(L, t);
    const it = M.newItem(t, n, M.bestGridFor(state.song, t, n));
    const pos = state.item >= 0 ? state.item + 1 : L.length;
    L.splice(pos, 0, it);
    state.item = pos;
    renderStructure(); changed();
  }

  function moveItem(d) {
    const L = state.song.structure, i = state.item;
    if (i < 0 || i + d < 0 || i + d >= L.length) return;
    [L[i], L[i + d]] = [L[i + d], L[i]];
    state.item += d;
    renderStructure(); changed();
  }

  function delItem() {
    if (state.item < 0) return;
    state.song.structure.splice(state.item, 1);
    state.item = Math.min(state.item, state.song.structure.length - 1);
    renderStructure(); changed();
  }

  function generate() {
    const counts = {};
    $$("#gen input").forEach(i => counts[i.dataset.type] = parseInt(i.value) || 0);
    if (state.song.structure.length && !confirm(T("Remplacer la structure actuelle ?"))) return;
    state.song.structure = M.generateStructure(state.song, counts);
    state.item = state.song.structure.length ? 0 : -1;
    renderStructure(); changed();
    toast(F("{0} parties générées", state.song.structure.length));
  }

  // --------------------------------------------------------------- PDF & fichiers
  let pdfLoading = null;
  function ensurePdf() {
    if (window.jspdf) return Promise.resolve();
    if (!pdfLoading) pdfLoading = new Promise((res, rej) => {
      const s = document.createElement("script");
      s.src = "grilles/jspdf.umd.min.js";
      s.onload = res; s.onerror = () => { pdfLoading = null; rej(new Error("jspdf")); };
      document.head.appendChild(s);
    });
    return pdfLoading;
  }
  async function makePdf(song) {
    song = song || state.song;
    if (!song.sections.length) { toast(T("Ajoute au moins une grille avant d'exporter.")); return null; }
    try { await ensurePdf(); } catch (e) { toast(T("Impossible de charger le module PDF.")); return null; }
    return G.PDF.render(song, state.orient);
  }

  async function exportPdf() {
    const doc = await makePdf(); if (!doc) return;
    const name = `${fileBase()} - ${T(state.orient === "landscape" ? "paysage" : "portrait")}.pdf`;
    doc.save(name);
    toast(F("PDF téléchargé : {0}", name));
  }

  async function previewPdf() {
    const w = window.open("", "_blank");            // ouvert tout de suite (anti pop-up), rempli ensuite
    const doc = await makePdf();
    if (!doc) { if (w) w.close(); return; }
    const url = doc.output("bloburl");
    if (w) w.location.href = url; else toast(T("Autorise les fenêtres pop-up pour voir l'aperçu."));
  }

  function saveFile() {
    const blob = new Blob([JSON.stringify(state.song, null, 1)], { type: "application/json" });
    download(blob, `${fileBase()}.grille`);
    toast(T("Fichier .grille enregistré"));
  }

  function openFile(file) {
    const rd = new FileReader();
    rd.onload = () => {
      try {
        addAndOpen(M.normalize(JSON.parse(rd.result)));
        setTab("grids");
        toast(F("« {0} » ouvert", state.song.title || file.name));
      } catch (e) {
        toast(T("Ce fichier n'est pas un .grille valide."));
      }
    };
    rd.readAsText(file);
  }


  // --------------------------------------------------------------- morceaux : sur cet appareil
  const fmtDate = t => new Date(t).toLocaleDateString(isEn() ? "en-GB" : "fr-FR", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });
  const filterText = () => $("#lib-filter").value.trim().toLowerCase();
  const matches = (title, artist) => { const f = filterText(); return !f || `${title} ${artist}`.toLowerCase().includes(f); };

  function libRow(title, meta, actions, current) {
    const li = document.createElement("li");
    if (current) li.className = "current";
    const info = document.createElement("div");
    info.className = "info";
    const t = document.createElement("strong"); t.textContent = title;
    const m = document.createElement("span"); m.textContent = meta;
    info.append(t, m);
    const acts = document.createElement("div");
    acts.className = "acts";
    actions.forEach(([label, fn, cls]) => {
      const b = document.createElement("button");
      b.type = "button"; b.className = cls || "link"; b.textContent = label;
      b.addEventListener("click", fn);
      acts.appendChild(b);
    });
    li.append(info, acts);
    return li;
  }

  function renderLocal() {
    const ul = $("#lib-local");
    ul.innerHTML = "";
    const ids = Object.keys(lib.songs).sort((a, b) => lib.songs[b].updated - lib.songs[a].updated);
    let shown = 0;
    ids.forEach(id => {
      const { song, updated } = lib.songs[id];
      const title = (song.title || "").trim() || T("Sans titre");
      if (!matches(title, song.artist || "")) return;
      shown++;
      const meta = [song.artist, F("{0} parties", (song.structure || []).length), F("modifié le {0}", fmtDate(updated))].filter(Boolean).join("  ·  ");
      const cur = id === state.id;
      ul.appendChild(libRow(cur ? F("{0}  (en cours)", title) : title, meta, [
        [T("Ouvrir"), () => { loadSong(M.normalize(clone(lib.songs[id].song)), id); setTab("grids"); }, "btn small"],
        [T("Dupliquer"), () => {
          const c = clone(lib.songs[id].song); c.title = F("{0} (copie)", c.title || T("Sans titre"));
          const nid = uid(); lib.songs[nid] = { song: c, updated: Date.now() }; writeLib(); renderLocal();
        }],
        [T("Supprimer"), () => deleteLocal(id), "link danger"],
      ], cur));
    });
    if (!shown) {
      const li = document.createElement("li"); li.className = "none";
      li.textContent = T(ids.length ? "Aucun morceau ne correspond à la recherche." : "Aucun morceau pour l'instant.");
      ul.appendChild(li);
    }
  }

  function deleteLocal(id) {
    const title = lib.songs[id].song.title || T("Sans titre");
    if (!confirm(F("Supprimer « {0} » de cet appareil ? Cette action est définitive.", title))) return;
    delete lib.songs[id];
    if (id === state.id) {
      const next = Object.keys(lib.songs).sort((a, b) => lib.songs[b].updated - lib.songs[a].updated)[0];
      if (next) loadSong(M.normalize(clone(lib.songs[next].song)), next);
      else loadSong(M.defaultSong());
    }
    writeLib();
    renderLocal();
    toast(F("« {0} » supprimé", title));
  }

  // --------------------------------------------------------------- morceaux : exemples intégrés
  function renderExamples() {
    const ul = $("#lib-online");
    ul.innerHTML = "";
    const ex = G.EXAMPLE;
    if (!matches(ex.title, ex.artist)) {
      const li = document.createElement("li"); li.className = "none";
      li.textContent = T("Aucun exemple ne correspond à la recherche.");
      ul.appendChild(li); return;
    }
    const meta = [ex.artist, ex.key && F("en {0}", ex.key), F("{0} parties", ex.structure.length)].filter(Boolean).join("  ·  ");
    ul.appendChild(libRow(ex.title, meta, [
      [T("Ouvrir une copie"), () => {
        const dup = addAndOpen(M.normalize(localExample()));
        setTab("grids");
        toast(F(dup ? "« {0} » était déjà dans tes morceaux" : "« {0} » ajouté à tes morceaux", ex.title));
      }, "btn small"],
      ["PDF", async () => {
        const doc = await makePdf(M.normalize(localExample()));
        if (doc) doc.save(`${ex.title} - ${T(state.orient === "landscape" ? "paysage" : "portrait")}.pdf`);
      }],
    ]));
  }

  // --------------------------------------------------------------- lien de partage
  const b64u = bytes => { let s = ""; bytes.forEach(b => s += String.fromCharCode(b)); return btoa(s).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, ""); };
  const unb64u = str => { str = str.replace(/-/g, "+").replace(/_/g, "/"); while (str.length % 4) str += "="; return Uint8Array.from(atob(str), c => c.charCodeAt(0)); };
  async function pipe(bytes, Stream) {
    return new Uint8Array(await new Response(new Blob([bytes]).stream().pipeThrough(new Stream("deflate-raw"))).arrayBuffer());
  }
  function compact(song) {
    const c = clone(song), d = M.newCell();
    c.sections.forEach(s => s.rows.forEach(r => r.forEach(cell => {
      Object.keys(d).forEach(k => { if (cell[k] === d[k]) delete cell[k]; });
    })));
    return c;
  }
  async function shareLink() {
    const bytes = new TextEncoder().encode(JSON.stringify(compact(state.song)));
    let hash;
    if (window.CompressionStream) hash = "g=" + b64u(await pipe(bytes, CompressionStream));
    else hash = "j=" + b64u(bytes);
    return `${location.origin}${location.pathname}#${hash}`;
  }
  async function copyShare() {
    const url = await shareLink();
    try {
      await navigator.clipboard.writeText(url);
      toast(T("Lien copié : la personne qui l'ouvre récupère ce morceau."));
    } catch (e) {
      prompt(T("Copie ce lien :"), url);
    }
  }
  async function readShareHash() {
    const h = location.hash.slice(1);
    if (!/^[gj]=/.test(h)) return false;
    try {
      let bytes = unb64u(h.slice(2));
      if (h[0] === "g") bytes = await pipe(bytes, DecompressionStream);
      const song = M.normalize(JSON.parse(new TextDecoder().decode(bytes)));
      const dup = addAndOpen(song);
      toast(dup ? F("« {0} » était déjà dans tes morceaux", song.title || T("Morceau")) : F("« {0} » ajouté à tes morceaux", song.title || T("Morceau partagé")));
    } catch (e) {
      toast(T("Ce lien de partage est incomplet ou abîmé."));
    }
    history.replaceState(null, "", location.pathname + location.search);
    return true;
  }

  // --------------------------------------------------------------- init
  function init() {
    fillTypes();
    $("#new-type").value = "Couplet"; $("#item-type").value = "Couplet";

    const gen = $("#gen");
    const def = { Intro: 1, Couplet: 2, Refrain: 2, Outro: 1 };
    M.SECTION_TYPES.forEach(t => {
      const id = "g-" + t.replace(/\W/g, "");
      const lab = document.createElement("label");
      lab.htmlFor = id; lab.textContent = T(t);
      const inp = document.createElement("input");
      inp.type = "number"; inp.min = 0; inp.max = 12; inp.value = def[t] || 0;
      inp.id = id; inp.dataset.type = t;
      gen.append(lab, inp);
    });

    ["title", "artist", "key", "tempo", "notes"].forEach(k => {
      $("#f-" + k).addEventListener("input", e => { state.song[k] = e.target.value; persist(); });
    });

    $$(".tab").forEach(b => b.addEventListener("click", () => setTab(b.dataset.tab)));
    $$("#orient button").forEach(b => b.addEventListener("click", () => setOrient(b.dataset.orient)));
    $("#b-pdf").addEventListener("click", exportPdf);
    $("#b-preview").addEventListener("click", previewPdf);
    $("#b-save").addEventListener("click", saveFile);
    $("#b-open").addEventListener("click", () => $("#file-input").click());
    $("#file-input").addEventListener("change", e => { if (e.target.files[0]) openFile(e.target.files[0]); e.target.value = ""; });
    $("#b-new").addEventListener("click", () => {
      clearTimeout(saveTimer);
      if (state.id) { lib.songs[state.id] = { song: state.song, updated: Date.now() }; }
      loadSong(M.defaultSong());
      setTab("grids");
      $("#f-title").focus();
      toast(T("Nouveau morceau. Le précédent reste dans l'onglet Morceaux."));
    });
    $("#b-share").addEventListener("click", copyShare);
    $("#lib-filter").addEventListener("input", () => { renderLocal(); renderExamples(); });
    window.addEventListener("hashchange", () => { readShareHash().then(ok => ok && setTab("grids")); });

    $("#b-add-section").addEventListener("click", addSection);
    $("#b-dup").addEventListener("click", dupSection);
    $("#b-del").addEventListener("click", delSection);
    $("#b-up").addEventListener("click", () => moveSection(-1));
    $("#b-down").addEventListener("click", () => moveSection(1));
    ["#s-type", "#s-num", "#s-label", "#s-comment"].forEach(s => $(s).addEventListener("input", metaChanged));
    ["#s-cols", "#s-rows"].forEach(s => $(s).addEventListener("change", resize));
    $$(".tool[data-act]").forEach(b => {
      b.addEventListener("mousedown", e => e.preventDefault());
      b.addEventListener("click", () => act(b.dataset.act));
    });
    $("#t-times").addEventListener("input", () => {
      const s = cur(); if (!s) return;
      const c = cell(...state.sel);
      c.times = Math.max(1, parseInt($("#t-times").value) || 2);
      c.end = true;
      decorate(cellEl(...state.sel), c); select(...state.sel); changed();
    });
    $("#m-auto").addEventListener("change", () => {
      const s = cur(); s.measures_auto = $("#m-auto").checked;
      if (!s.measures_auto) s.measures = parseInt($("#m-manual").value) || M.computeMeasures(s);
      changed();
    });
    $("#m-manual").addEventListener("input", () => { const s = cur(); s.measures = parseInt($("#m-manual").value) || 0; changed(); });

    ["#i-label", "#i-note", "#i-meas"].forEach(s => $(s).addEventListener("input", itemChanged));
    ["#i-grid", "#i-auto"].forEach(s => $(s).addEventListener("change", itemChanged));
    $("#b-add-item").addEventListener("click", addItem);
    $("#b-i-up").addEventListener("click", () => moveItem(-1));
    $("#b-i-down").addEventListener("click", () => moveItem(1));
    $("#b-i-del").addEventListener("click", delItem);
    $("#b-renum").addEventListener("click", () => { M.renumber(state.song.structure); renderStructure(); changed(); });
    $("#b-generate").addEventListener("click", generate);

    // glisser-déposer un .grille n'importe où
    document.addEventListener("dragover", e => e.preventDefault());
    document.addEventListener("drop", e => {
      e.preventDefault();
      const f = e.dataTransfer.files && e.dataTransfer.files[0];
      if (f) openFile(f);
    });

    readStorage();
    setOrient(state.orient);
    const cur = lib.current && lib.songs[lib.current];
    if (cur) loadSong(M.normalize(clone(cur.song)), lib.current);
    else loadSong(M.normalize(localExample()));
    setTab(state.tab);
    applyLang();
    window.onNotation = applyLang;
    readShareHash().then(ok => ok && setTab("grids"));
  }

  /* listes de types : la valeur reste le nom français (format .grille), seul le libellé est traduit */
  function fillTypes() {
    ["#new-type", "#s-type", "#item-type"].forEach(sel => {
      const el = $(sel), v = el.value;
      el.innerHTML = M.SECTION_TYPES.map(t => `<option value="${t}">${T(t)}</option>`).join("");
      if (v) el.value = v;
    });
  }

  /* bascule FR/EN : retraduit le statique et reconstruit le dynamique depuis l'état (rien n'est perdu) */
  function applyLang() {
    translateDom();
    fillTypes();
    const s = cur(); if (s) $("#s-type").value = s.type;
    $$("#gen label").forEach(l => { const i = document.getElementById(l.htmlFor); if (i) l.textContent = T(i.dataset.type); });
    $$("#grid .cell").forEach(el => {
      const r = +el.dataset.r + 1, k = +el.dataset.c + 1, note = el.querySelector(".note");
      el.querySelector(".chord").setAttribute("aria-label", F("Ligne {0}, mesure {1}", r, k));
      note.placeholder = T("indication");
      note.setAttribute("aria-label", F("Indication ligne {0}, mesure {1}", r, k));
    });
    renderSectionList();
    renderStructure();
    renderLocal(); renderExamples();
  }

  document.addEventListener("DOMContentLoaded", init);
})(window.GM = window.GM || {});
