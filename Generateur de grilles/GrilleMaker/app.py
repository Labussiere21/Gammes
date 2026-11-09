"""GrilleMaker — générateur de grilles d'accords (basse / guitare)."""
import os
import subprocess
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import model
import pdf_render

APP_NAME = "GrilleMaker"
PURPLE = "#5b3a8c"
LIGHT = "#f1ecf7"
SEL = "#ffcc4d"


def resource(*parts):
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, *parts)


def open_file(path):
    try:
        if sys.platform.startswith("win"):
            os.startfile(path)  # noqa
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
    except Exception:
        pass


# =====================================================================
class CellWidget(tk.Frame):
    def __init__(self, master, app, r, c):
        super().__init__(master, bd=0, highlightthickness=2, highlightbackground="#cfcfcf",
                         bg="white", padx=2, pady=1)
        self.app, self.r, self.c = app, r, c
        self.flags = tk.Label(self, text="", fg=PURPLE, bg="white", font=("Segoe UI", 8, "bold"),
                              anchor="w")
        self.flags.pack(fill="x")
        self.v_chord = tk.StringVar()
        self.v_note = tk.StringVar()
        self.e_chord = tk.Entry(self, textvariable=self.v_chord, width=9, justify="center",
                                font=("Segoe UI", 13, "bold"), relief="flat", bg="white")
        self.e_chord.pack(fill="x")
        self.e_note = tk.Entry(self, textvariable=self.v_note, width=9, justify="center",
                               font=("Segoe UI", 8, "italic"), relief="flat", fg="#777", bg="#fafafa")
        self.e_note.pack(fill="x")
        for w in (self, self.e_chord, self.e_note, self.flags):
            w.bind("<FocusIn>", lambda e: self.app.select_cell(self.r, self.c), add="+")
            w.bind("<Button-1>", lambda e: self.app.select_cell(self.r, self.c), add="+")
        self.e_chord.bind("<Return>", lambda e: self.app.move_cell(1))
        self.e_chord.bind("<Tab>", lambda e: (self.app.move_cell(1), "break")[1])
        self.e_chord.bind("<Shift-Tab>", lambda e: (self.app.move_cell(-1), "break")[1])
        self.e_chord.bind("<ISO_Left_Tab>", lambda e: (self.app.move_cell(-1), "break")[1])
        self.load()
        self.v_chord.trace_add("write", self._changed)
        self.v_note.trace_add("write", self._changed)

    @property
    def cell(self):
        return self.app.cur_section()["rows"][self.r][self.c]

    def load(self):
        self.v_chord.set(self.cell["chord"])
        self.v_note.set(self.cell["note"])
        self.refresh_flags()

    def _changed(self, *_):
        self.cell["chord"] = self.v_chord.get()
        self.cell["note"] = self.v_note.get()
        self.app.section_changed()

    def refresh_flags(self):
        c = self.cell
        f = []
        if c["start"]:
            f.append("‖:")
        if c["volta"]:
            f.append(f"[{c['volta']}.")
        if c["end"]:
            f.append(":‖" + (f" x{c['times']}" if int(c["times"]) != 2 else ""))
        self.flags.config(text="  ".join(f) or " ")

    def set_selected(self, on):
        self.config(highlightbackground=SEL if on else "#cfcfcf",
                    highlightcolor=SEL if on else "#cfcfcf")


# =====================================================================
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.geometry("1180x760")
        self.minsize(980, 620)
        self.path = None
        self.song = model.new_song()
        self.sec_idx = -1
        self.sel = (0, 0)
        self.cells = {}
        self._loading = False
        self._style()
        try:
            self._icon = tk.PhotoImage(file=resource("icon.png"))
            self.iconphoto(True, self._icon)
        except Exception:
            pass
        self._build()
        self.new_song(ask=False)
        self.protocol("WM_DELETE_WINDOW", self.quit_app)

    # ---------------------------------------------------------------- UI
    def _style(self):
        st = ttk.Style(self)
        try:
            st.theme_use("clam")
        except tk.TclError:
            pass
        st.configure("Accent.TButton", foreground="white", background=PURPLE)
        st.map("Accent.TButton", background=[("active", "#734ea8")])
        st.configure("H.TLabel", font=("Segoe UI", 11, "bold"), foreground=PURPLE)
        st.configure("Treeview", rowheight=24)

    def _build(self):
        # ---- barre du haut
        top = ttk.Frame(self, padding=(10, 8))
        top.pack(fill="x")
        for txt, cmd in (("Nouveau", self.new_song), ("Ouvrir…", self.open_song),
                         ("Enregistrer", self.save), ("Enregistrer sous…", self.save_as),
                         ("Exemple", self.load_example)):
            ttk.Button(top, text=txt, command=cmd).pack(side="left", padx=2)
        ttk.Button(top, text="Générer le PDF", style="Accent.TButton",
                   command=self.export_pdf).pack(side="right", padx=2)
        self.v_orient = tk.StringVar(value="paysage")
        ttk.Radiobutton(top, text="Paysage", value="paysage", variable=self.v_orient).pack(side="right")
        ttk.Radiobutton(top, text="Portrait", value="portrait", variable=self.v_orient).pack(side="right")

        info = ttk.Frame(self, padding=(10, 0, 10, 6))
        info.pack(fill="x")
        self.v_title, self.v_artist = tk.StringVar(), tk.StringVar()
        self.v_key, self.v_tempo, self.v_notes = tk.StringVar(), tk.StringVar(), tk.StringVar()
        for lbl, var, w in (("Titre", self.v_title, 28), ("Artiste", self.v_artist, 20),
                            ("Tonalité", self.v_key, 6), ("Tempo", self.v_tempo, 7),
                            ("Note de fin", self.v_notes, 22)):
            ttk.Label(info, text=lbl).pack(side="left", padx=(8, 3))
            ttk.Entry(info, textvariable=var, width=w).pack(side="left")
            var.trace_add("write", self._song_info_changed)

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.tab_grids = ttk.Frame(nb, padding=8)
        self.tab_struct = ttk.Frame(nb, padding=8)
        nb.add(self.tab_grids, text="  Grilles  ")
        nb.add(self.tab_struct, text="  Structure  ")
        nb.bind("<<NotebookTabChanged>>", lambda e: self.refresh_structure())
        self._build_grids_tab()
        self._build_struct_tab()

        self.status = ttk.Label(self, text="", anchor="w", padding=(10, 2))
        self.status.pack(fill="x", side="bottom")

    # ---------------------------------------------------------------- onglet grilles
    def _build_grids_tab(self):
        left = ttk.Frame(self.tab_grids)
        left.pack(side="left", fill="y")
        ttk.Label(left, text="Grilles", style="H.TLabel").pack(anchor="w")
        self.lb = tk.Listbox(left, width=24, height=18, exportselection=False,
                             font=("Segoe UI", 10), activestyle="none",
                             selectbackground=PURPLE)
        self.lb.pack(fill="y", expand=True, pady=4)
        self.lb.bind("<<ListboxSelect>>", self._on_lb)
        addf = ttk.Frame(left)
        addf.pack(fill="x")
        self.v_newtype = tk.StringVar(value="Couplet")
        ttk.Combobox(addf, textvariable=self.v_newtype, values=model.SECTION_TYPES,
                     width=11, state="readonly").pack(side="left")
        ttk.Button(addf, text="+ Ajouter", command=self.add_section).pack(side="left", padx=3)
        bf = ttk.Frame(left)
        bf.pack(fill="x", pady=3)
        for txt, cmd in (("Dupliquer", self.dup_section), ("Supprimer", self.del_section),
                         ("↑", lambda: self.move_section(-1)), ("↓", lambda: self.move_section(1))):
            ttk.Button(bf, text=txt, command=cmd, width=9 if len(txt) > 1 else 3).pack(side="left", padx=1)

        right = ttk.Frame(self.tab_grids, padding=(14, 0, 0, 0))
        right.pack(side="left", fill="both", expand=True)
        self.editor = right

        hdr = ttk.Frame(right)
        hdr.pack(fill="x")
        self.v_stype, self.v_snum, self.v_slabel = tk.StringVar(), tk.IntVar(), tk.StringVar()
        self.v_cols, self.v_rows = tk.IntVar(value=4), tk.IntVar(value=4)
        ttk.Label(hdr, text="Section").pack(side="left")
        ttk.Combobox(hdr, textvariable=self.v_stype, values=model.SECTION_TYPES, width=11,
                     state="readonly").pack(side="left", padx=3)
        ttk.Label(hdr, text="N°").pack(side="left", padx=(6, 2))
        ttk.Spinbox(hdr, from_=0, to=20, textvariable=self.v_snum, width=4).pack(side="left")
        ttk.Label(hdr, text="Nom perso").pack(side="left", padx=(8, 2))
        ttk.Entry(hdr, textvariable=self.v_slabel, width=16).pack(side="left")
        ttk.Label(hdr, text="Cellules / ligne").pack(side="left", padx=(12, 2))
        ttk.Spinbox(hdr, from_=1, to=8, textvariable=self.v_cols, width=4,
                    command=self._resize).pack(side="left")
        ttk.Label(hdr, text="Lignes").pack(side="left", padx=(8, 2))
        ttk.Spinbox(hdr, from_=1, to=16, textvariable=self.v_rows, width=4,
                    command=self._resize).pack(side="left")
        for v in (self.v_stype, self.v_snum, self.v_slabel):
            v.trace_add("write", self._section_meta_changed)

        tools = ttk.Frame(right, padding=(0, 8, 0, 2))
        tools.pack(fill="x")
        ttk.Label(tools, text="Case sélectionnée :", width=18).pack(side="left")
        for txt, cmd in (("‖:  Début reprise", lambda: self.toggle("start")),
                         (":‖  Fin reprise", lambda: self.toggle("end"))):
            ttk.Button(tools, text=txt, command=cmd).pack(side="left", padx=2)
        ttk.Label(tools, text="Répéter x").pack(side="left", padx=(10, 2))
        self.v_times = tk.IntVar(value=2)
        sp = ttk.Spinbox(tools, from_=2, to=32, textvariable=self.v_times, width=4,
                         command=self._times_changed)
        sp.pack(side="left")
        sp.bind("<KeyRelease>", lambda e: self._times_changed())
        tools2 = ttk.Frame(right, padding=(0, 0, 0, 8))
        tools2.pack(fill="x")
        ttk.Label(tools2, text="", width=18).pack(side="left")
        for txt, cmd in (("Case 1.", lambda: self.set_volta("1")),
                         ("Case 2.", lambda: self.set_volta("2")),
                         ("%  Même mesure", self.set_simile),
                         ("Effacer la case", self.clear_cell)):
            ttk.Button(tools2, text=txt, command=cmd).pack(side="left", padx=2)

        gridbox = tk.Frame(right, bg=LIGHT, padx=12, pady=12)
        gridbox.pack(fill="both", expand=True)
        self.grid_frame = tk.Frame(gridbox, bg=LIGHT)
        self.grid_frame.pack(side="left", anchor="n")
        side = tk.Frame(gridbox, bg=LIGHT, padx=18)
        side.pack(side="left", anchor="n")
        tk.Label(side, text="Mesures", bg=LIGHT, fg=PURPLE, font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.lbl_meas = tk.Label(side, text="0 M", bg=LIGHT, fg="#222", font=("Segoe UI", 26, "bold"))
        self.lbl_meas.pack(anchor="w")
        self.v_mauto = tk.BooleanVar(value=True)
        self.v_mman = tk.IntVar(value=0)
        ttk.Checkbutton(side, text="Calcul auto", variable=self.v_mauto,
                        command=self._meas_mode).pack(anchor="w", pady=(6, 2))
        self.sp_mman = ttk.Spinbox(side, from_=0, to=999, textvariable=self.v_mman, width=6,
                                   command=self._meas_mode)
        self.sp_mman.pack(anchor="w")
        self.sp_mman.bind("<KeyRelease>", lambda e: self._meas_mode())
        tk.Label(side, text="Commentaire", bg=LIGHT, fg=PURPLE,
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(18, 0))
        self.v_comment = tk.StringVar()
        ttk.Entry(side, textvariable=self.v_comment, width=24).pack(anchor="w")
        self.v_comment.trace_add("write", self._section_meta_changed)
        tk.Label(side, justify="left", bg=LIGHT, fg="#666", font=("Segoe UI", 8), text=(
            "\nAstuces\n"
            "• 2 accords dans une mesure : « C Bb »\n"
            "   ou « C, Bb » (diagonale dans le PDF)\n"
            "• « C/E » reste un accord renversé\n"
            "• % = même mesure que la précédente\n"
            "• Petite ligne sous l'accord : rythme,\n"
            "   indication (ex. « syncopé »)\n"
            "• Entrée / Tab : case suivante\n"
            "• Les cases vides en fin de ligne\n"
            "   ne sont pas imprimées")).pack(anchor="w")

    # ---------------------------------------------------------------- onglet structure
    def _build_struct_tab(self):
        left = ttk.Frame(self.tab_struct)
        left.pack(side="left", fill="both", expand=True)
        ttk.Label(left, text="Déroulé du morceau", style="H.TLabel").pack(anchor="w")
        cols = ("n", "section", "grille", "mesures", "note")
        self.tree = ttk.Treeview(left, columns=cols, show="headings", selectmode="browse", height=18)
        for cid, txt, w in (("n", "#", 40), ("section", "Section", 170), ("grille", "Grille jouée", 170),
                            ("mesures", "Mesures", 80), ("note", "Note", 200)):
            self.tree.heading(cid, text=txt)
            self.tree.column(cid, width=w, anchor="center" if cid in ("n", "mesures") else "w")
        self.tree.pack(fill="both", expand=True, pady=4)
        self.tree.bind("<<TreeviewSelect>>", self._on_tree)
        self.lbl_total = ttk.Label(left, text="", style="H.TLabel")
        self.lbl_total.pack(anchor="w")

        bar = ttk.Frame(left)
        bar.pack(fill="x", pady=4)
        self.v_itype = tk.StringVar(value="Couplet")
        ttk.Combobox(bar, textvariable=self.v_itype, values=model.SECTION_TYPES, width=11,
                     state="readonly").pack(side="left")
        ttk.Button(bar, text="+ Ajouter", command=self.add_item).pack(side="left", padx=3)
        for txt, cmd in (("Supprimer", self.del_item), ("↑", lambda: self.move_item(-1)),
                         ("↓", lambda: self.move_item(1)), ("Renuméroter", self.renumber)):
            ttk.Button(bar, text=txt, command=cmd).pack(side="left", padx=2)

        right = ttk.Frame(self.tab_struct, padding=(16, 0, 0, 0))
        right.pack(side="left", fill="y")
        ed = ttk.LabelFrame(right, text=" Élément sélectionné ", padding=10)
        ed.pack(fill="x")
        self.v_ilabel, self.v_igrid, self.v_inote = tk.StringVar(), tk.StringVar(), tk.StringVar()
        self.v_imauto, self.v_imeas = tk.BooleanVar(value=True), tk.IntVar()
        ttk.Label(ed, text="Nom perso (ex. Refrain de fin)").grid(row=0, column=0, sticky="w")
        ttk.Entry(ed, textvariable=self.v_ilabel, width=26).grid(row=1, column=0, sticky="w", pady=(0, 6))
        ttk.Label(ed, text="Grille jouée").grid(row=2, column=0, sticky="w")
        self.cb_grid = ttk.Combobox(ed, textvariable=self.v_igrid, width=24, state="readonly")
        self.cb_grid.grid(row=3, column=0, sticky="w", pady=(0, 6))
        self.cb_grid.bind("<<ComboboxSelected>>", self._item_changed)
        mf = ttk.Frame(ed)
        mf.grid(row=4, column=0, sticky="w", pady=(0, 6))
        ttk.Checkbutton(mf, text="Mesures de la grille", variable=self.v_imauto,
                        command=self._item_changed).pack(side="left")
        sp = ttk.Spinbox(mf, from_=0, to=999, textvariable=self.v_imeas, width=5,
                         command=self._item_changed)
        sp.pack(side="left", padx=6)
        sp.bind("<KeyRelease>", self._item_changed)
        ttk.Label(ed, text="Note (ex. « fin sur Dm »)").grid(row=5, column=0, sticky="w")
        ttk.Entry(ed, textvariable=self.v_inote, width=26).grid(row=6, column=0, sticky="w")
        for v in (self.v_ilabel, self.v_inote):
            v.trace_add("write", self._item_changed)

        gen = ttk.LabelFrame(right, text=" Générateur de structure ", padding=10)
        gen.pack(fill="x", pady=12)
        self.gen_vars = {}
        defaults = {"Intro": 1, "Couplet": 2, "Refrain": 2, "Outro": 1}
        for i, t in enumerate(model.SECTION_TYPES):
            v = tk.IntVar(value=defaults.get(t, 0))
            self.gen_vars[t] = v
            ttk.Label(gen, text=t).grid(row=i // 2, column=(i % 2) * 2, sticky="w", padx=(0, 4), pady=2)
            ttk.Spinbox(gen, from_=0, to=12, textvariable=v, width=4).grid(
                row=i // 2, column=(i % 2) * 2 + 1, sticky="w", padx=(0, 14))
        ttk.Button(gen, text="Générer la structure", style="Accent.TButton",
                   command=self.generate).grid(row=6, column=0, columnspan=4, pady=(10, 0), sticky="ew")
        ttk.Label(gen, foreground="#666", font=("Segoe UI", 8), justify="left", text=(
            "Numérote automatiquement (Couplet 1, 2, 3…) et relie chaque\n"
            "élément à sa grille (Couplet 3 → grille Couplet 1 s'il n'y\n"
            "a que 2 grilles). Tu peux ensuite réordonner.")).grid(
            row=7, column=0, columnspan=4, sticky="w", pady=(6, 0))

    # ================================================================ morceau
    def load_song_obj(self, song, path=None):
        self._loading = True
        self.song = song
        self.path = path
        self.v_title.set(song["title"]); self.v_artist.set(song["artist"])
        self.v_key.set(song.get("key", "")); self.v_tempo.set(song.get("tempo", ""))
        self.v_notes.set(song.get("notes", ""))
        self._loading = False
        self.sec_idx = 0 if song["sections"] else -1
        self.refresh_list()
        self.show_section()
        self.refresh_structure()
        self.dirty = False
        self._title()

    def _title(self):
        name = os.path.basename(self.path) if self.path else "Nouveau morceau"
        self.title(f"{APP_NAME} — {name}{' •' if getattr(self, 'dirty', False) else ''}")

    def mark(self):
        if not self._loading:
            self.dirty = True
            self._title()

    def _song_info_changed(self, *_):
        if self._loading:
            return
        self.song["title"] = self.v_title.get(); self.song["artist"] = self.v_artist.get()
        self.song["key"] = self.v_key.get(); self.song["tempo"] = self.v_tempo.get()
        self.song["notes"] = self.v_notes.get()
        self.mark()

    def confirm_discard(self):
        if getattr(self, "dirty", False):
            r = messagebox.askyesnocancel(APP_NAME, "Enregistrer les modifications ?")
            if r is None:
                return False
            if r:
                return self.save()
        return True

    def new_song(self, ask=True):
        if ask and not self.confirm_discard():
            return
        s = model.new_song()
        s["sections"] = [model.new_section("Intro", 0, 4, 1), model.new_section("Couplet", 1),
                         model.new_section("Refrain", 1, 4, 2)]
        self.load_song_obj(s)

    def open_song(self):
        if not self.confirm_discard():
            return
        p = filedialog.askopenfilename(filetypes=[("Grille", "*.grille"), ("JSON", "*.json"), ("Tous", "*.*")])
        if p:
            self.open_path(p)

    def open_path(self, p):
        try:
            self.load_song_obj(model.load_song(p), p)
        except Exception as e:
            messagebox.showerror(APP_NAME, f"Impossible d'ouvrir le fichier :\n{e}")

    def load_example(self):
        if not self.confirm_discard():
            return
        p = resource("exemples", "Sultans_of_Swing.grille")
        try:
            self.load_song_obj(model.load_song(p), None)
            self.dirty = True; self._title()
        except Exception as e:
            messagebox.showerror(APP_NAME, str(e))

    def save(self):
        if not self.path:
            return self.save_as()
        model.save_song(self.song, self.path)
        self.dirty = False; self._title()
        self.flash(f"Enregistré : {self.path}")
        return True

    def save_as(self):
        p = filedialog.asksaveasfilename(defaultextension=".grille", filetypes=[("Grille", "*.grille")],
                                         initialfile=(self.song["title"] or "morceau") + ".grille")
        if not p:
            return False
        self.path = p
        return self.save()

    def export_pdf(self):
        if not self.song["sections"]:
            messagebox.showinfo(APP_NAME, "Ajoute au moins une grille.")
            return
        base = (self.song["title"] or "grille").replace("/", "-")
        p = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF", "*.pdf")],
                                         initialfile=f"{base} - {self.v_orient.get()}.pdf")
        if not p:
            return
        try:
            pdf_render.render(self.song, p, self.v_orient.get())
        except PermissionError:
            messagebox.showerror(APP_NAME, "Le PDF est peut-être ouvert ailleurs. Ferme-le et réessaie.")
            return
        except Exception as e:
            messagebox.showerror(APP_NAME, f"Erreur PDF :\n{e}")
            return
        self.flash(f"PDF généré : {p}")
        open_file(p)

    def quit_app(self):
        if self.confirm_discard():
            self.destroy()

    def flash(self, msg):
        self.status.config(text=msg)
        self.after(6000, lambda: self.status.config(text=""))

    # ================================================================ sections
    def cur_section(self):
        if 0 <= self.sec_idx < len(self.song["sections"]):
            return self.song["sections"][self.sec_idx]
        return None

    def refresh_list(self):
        self.lb.delete(0, "end")
        for s in self.song["sections"]:
            self.lb.insert("end", f"  {model.section_name(s)}   ({model.section_measures(s)} M)")
        if self.sec_idx >= 0:
            self.lb.selection_clear(0, "end")
            self.lb.selection_set(self.sec_idx)
            self.lb.see(self.sec_idx)

    def _on_lb(self, _):
        sel = self.lb.curselection()
        if sel and sel[0] != self.sec_idx:
            self.sec_idx = sel[0]
            self.sel = (0, 0)
            self.show_section()

    def add_section(self):
        t = self.v_newtype.get()
        nums = [s["num"] for s in self.song["sections"] if s["type"] == t]
        num = (max(nums) + 1) if nums else (0 if t in ("Intro", "Outro", "Solo", "Pont", "Coda") else 1)
        if num == 1 and nums == [0]:
            num = 2
        self.song["sections"].append(model.new_section(t, num, 4, 4 if t in ("Couplet", "Solo") else 2))
        self.sec_idx = len(self.song["sections"]) - 1
        self.refresh_list(); self.show_section(); self.mark()

    def dup_section(self):
        s = self.cur_section()
        if not s:
            return
        d = model.duplicate_section(s)
        d["num"] = max([x["num"] for x in self.song["sections"] if x["type"] == s["type"]] + [0]) + 1
        d["label"] = ""
        self.song["sections"].insert(self.sec_idx + 1, d)
        self.sec_idx += 1
        self.refresh_list(); self.show_section(); self.mark()

    def del_section(self):
        s = self.cur_section()
        if not s or not messagebox.askyesno(APP_NAME, f"Supprimer la grille « {model.section_name(s)} » ?"):
            return
        for it in self.song["structure"]:
            if it["grid"] == s["id"]:
                it["grid"] = ""
        del self.song["sections"][self.sec_idx]
        self.sec_idx = min(self.sec_idx, len(self.song["sections"]) - 1)
        self.refresh_list(); self.show_section(); self.mark()

    def move_section(self, d):
        i, L = self.sec_idx, self.song["sections"]
        if 0 <= i + d < len(L) and i >= 0:
            L[i], L[i + d] = L[i + d], L[i]
            self.sec_idx += d
            self.refresh_list(); self.mark()

    def show_section(self):
        for w in self.grid_frame.winfo_children():
            w.destroy()
        self.cells = {}
        s = self.cur_section()
        state = "normal" if s else "disabled"
        if not s:
            tk.Label(self.grid_frame, text="Aucune grille — ajoute une section à gauche.",
                     bg=LIGHT, fg="#666").grid()
            self.lbl_meas.config(text="–")
            return
        self._loading = True
        self.v_stype.set(s["type"]); self.v_snum.set(s["num"]); self.v_slabel.set(s.get("label", ""))
        self.v_cols.set(s["cols"]); self.v_rows.set(len(s["rows"]))
        self.v_mauto.set(s.get("measures_auto", True)); self.v_mman.set(s.get("measures", 0))
        self.v_comment.set(s.get("comment", ""))
        self._loading = False
        for r, row in enumerate(s["rows"]):
            tk.Label(self.grid_frame, text=str(r + 1), bg=LIGHT, fg="#999",
                     font=("Segoe UI", 8)).grid(row=r, column=0, padx=(0, 4))
            for c in range(len(row)):
                w = CellWidget(self.grid_frame, self, r, c)
                w.grid(row=r, column=c + 1, padx=1, pady=1, sticky="nsew")
                self.cells[(r, c)] = w
        r, c = self.sel
        if (r, c) not in self.cells:
            self.sel = (0, 0)
        self.select_cell(*self.sel, focus=False)
        self.update_measures()
        _ = state

    def _section_meta_changed(self, *_):
        s = self.cur_section()
        if self._loading or not s:
            return
        s["type"] = self.v_stype.get()
        try:
            s["num"] = int(self.v_snum.get())
        except (tk.TclError, ValueError):
            pass
        s["label"] = self.v_slabel.get()
        s["comment"] = self.v_comment.get()
        self.lb.delete(self.sec_idx)
        self.lb.insert(self.sec_idx, f"  {model.section_name(s)}   ({model.section_measures(s)} M)")
        self.lb.selection_set(self.sec_idx)
        self.mark()

    def _resize(self):
        s = self.cur_section()
        if not s:
            return
        try:
            cols, rows = int(self.v_cols.get()), int(self.v_rows.get())
        except (tk.TclError, ValueError):
            return
        lost = any(not model.cell_is_empty(c) for row in s["rows"][rows:] for c in row) or \
            any(not model.cell_is_empty(c) for row in s["rows"] for c in row[cols:])
        if lost and not messagebox.askyesno(APP_NAME, "Des cases remplies vont être supprimées. Continuer ?"):
            self.v_cols.set(s["cols"]); self.v_rows.set(len(s["rows"]))
            return
        model.resize_section(s, cols=cols, rows=rows)
        self.show_section(); self.section_changed()

    def section_changed(self):
        self.update_measures()
        s = self.cur_section()
        if s:
            self.lb.delete(self.sec_idx)
            self.lb.insert(self.sec_idx, f"  {model.section_name(s)}   ({model.section_measures(s)} M)")
            self.lb.selection_set(self.sec_idx)
        self.mark()

    def update_measures(self):
        s = self.cur_section()
        if not s:
            return
        self.lbl_meas.config(text=f"{model.section_measures(s)} M")
        self.sp_mman.config(state="disabled" if s.get("measures_auto", True) else "normal")

    def _meas_mode(self):
        s = self.cur_section()
        if not s or self._loading:
            return
        s["measures_auto"] = self.v_mauto.get()
        if not s["measures_auto"]:
            try:
                s["measures"] = int(self.v_mman.get())
            except (tk.TclError, ValueError):
                pass
        else:
            self.v_mman.set(model.compute_measures(s))
        self.section_changed()

    # ---------------------------------------------------------------- cellules
    def select_cell(self, r, c, focus=False):
        old = self.cells.get(self.sel)
        if old:
            old.set_selected(False)
        self.sel = (r, c)
        w = self.cells.get((r, c))
        if w:
            w.set_selected(True)
            self._loading = True
            self.v_times.set(int(w.cell.get("times") or 2))
            self._loading = False
            if focus:
                w.e_chord.focus_set()
                w.e_chord.icursor("end")

    def move_cell(self, d):
        s = self.cur_section()
        if not s:
            return
        cols = s["cols"]
        idx = self.sel[0] * cols + self.sel[1] + d
        total = len(s["rows"]) * cols
        if idx >= total:
            s["rows"].append([model.new_cell() for _ in range(cols)])
            self.show_section()
        idx = max(0, min(idx, len(s["rows"]) * cols - 1))
        self.select_cell(idx // cols, idx % cols, focus=True)
        return "break"

    def cur_cell_widget(self):
        return self.cells.get(self.sel)

    def toggle(self, flag):
        w = self.cur_cell_widget()
        if not w:
            return
        w.cell[flag] = not w.cell[flag]
        if flag == "end" and w.cell["end"]:
            w.cell["times"] = int(self.v_times.get() or 2)
        w.refresh_flags(); self.section_changed()

    def set_volta(self, v):
        w = self.cur_cell_widget()
        if not w:
            return
        w.cell["volta"] = "" if w.cell["volta"] == v else v
        w.refresh_flags(); self.section_changed()

    def set_simile(self):
        w = self.cur_cell_widget()
        if w:
            w.v_chord.set("%")
            self.move_cell(1)

    def clear_cell(self):
        w = self.cur_cell_widget()
        if not w:
            return
        w.cell.update(model.new_cell())
        w.load(); self.section_changed()

    def _times_changed(self):
        if self._loading:
            return
        w = self.cur_cell_widget()
        if not w:
            return
        try:
            t = int(self.v_times.get())
        except (tk.TclError, ValueError):
            return
        w.cell["times"] = max(1, t)
        if not w.cell["end"]:
            w.cell["end"] = True
        w.refresh_flags(); self.section_changed()

    # ================================================================ structure
    def grid_choices(self):
        return ["(aucune)"] + [model.section_name(s) for s in self.song["sections"]]

    def refresh_structure(self, keep=None):
        if keep is None:
            sel = self.tree.selection()
            keep = int(sel[0]) if sel else None
        self.tree.delete(*self.tree.get_children())
        for i, it in enumerate(self.song["structure"]):
            sec = model.find_section(self.song, it["grid"])
            self.tree.insert("", "end", iid=str(i), values=(
                i + 1, model.item_name(it), model.section_name(sec) if sec else "—",
                model.item_measures(self.song, it), it.get("note", "")))
        total = sum(model.item_measures(self.song, it) for it in self.song["structure"])
        self.lbl_total.config(text=f"Total : {total} mesures · {len(self.song['structure'])} parties")
        self.cb_grid.config(values=self.grid_choices())
        if keep is not None and 0 <= keep < len(self.song["structure"]):
            self.tree.selection_set(str(keep)); self.tree.see(str(keep))

    def cur_item(self):
        sel = self.tree.selection()
        if sel:
            return int(sel[0]), self.song["structure"][int(sel[0])]
        return None, None

    def _on_tree(self, _):
        i, it = self.cur_item()
        if it is None:
            return
        self._loading = True
        self.v_ilabel.set(it.get("label", "")); self.v_inote.set(it.get("note", ""))
        sec = model.find_section(self.song, it["grid"])
        self.v_igrid.set(model.section_name(sec) if sec else "(aucune)")
        self.v_imauto.set(it.get("measures_auto", True))
        self.v_imeas.set(model.item_measures(self.song, it))
        self._loading = False

    def _item_changed(self, *_):
        if self._loading:
            return
        i, it = self.cur_item()
        if it is None:
            return
        it["label"] = self.v_ilabel.get(); it["note"] = self.v_inote.get()
        g = self.v_igrid.get()
        idx = self.grid_choices().index(g) - 1 if g in self.grid_choices() else -1
        it["grid"] = self.song["sections"][idx]["id"] if idx >= 0 else ""
        it["measures_auto"] = self.v_imauto.get()
        if not it["measures_auto"]:
            try:
                it["measures"] = int(self.v_imeas.get())
            except (tk.TclError, ValueError):
                pass
        else:
            self._loading = True
            self.v_imeas.set(model.item_measures(self.song, it))
            self._loading = False
        self.refresh_structure(keep=i); self.mark()

    def add_item(self):
        t = self.v_itype.get()
        L = self.song["structure"]
        n = model.next_num(L, t)
        if n == 1 and any(x["type"] == t for x in L):
            n = 2
        it = model.new_item(t, n, model.best_grid_for(self.song, t, n))
        i, _ = self.cur_item()
        pos = (i + 1) if i is not None else len(L)
        L.insert(pos, it)
        self.refresh_structure(keep=pos); self._on_tree(None); self.mark()

    def del_item(self):
        i, it = self.cur_item()
        if it is None:
            return
        del self.song["structure"][i]
        self.refresh_structure(keep=min(i, len(self.song["structure"]) - 1)); self.mark()

    def move_item(self, d):
        i, it = self.cur_item()
        L = self.song["structure"]
        if it is None or not (0 <= i + d < len(L)):
            return
        L[i], L[i + d] = L[i + d], L[i]
        self.refresh_structure(keep=i + d); self.mark()

    def renumber(self):
        counts = {}
        for it in self.song["structure"]:
            counts[it["type"]] = counts.get(it["type"], 0) + 1
        seen = {}
        for it in self.song["structure"]:
            if counts[it["type"]] == 1 and it["type"] not in ("Couplet", "Refrain"):
                it["num"] = 0
            else:
                seen[it["type"]] = seen.get(it["type"], 0) + 1
                it["num"] = seen[it["type"]]
        self.refresh_structure(); self.mark()

    def generate(self):
        counts = {}
        for t, v in self.gen_vars.items():
            try:
                counts[t] = int(v.get())
            except (tk.TclError, ValueError):
                counts[t] = 0
        if self.song["structure"] and not messagebox.askyesno(
                APP_NAME, "Remplacer la structure actuelle ?"):
            return
        self.song["structure"] = model.generate_structure(self.song, counts)
        self.refresh_structure(keep=0); self._on_tree(None); self.mark()


def main():
    app = App()
    if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]):
        app.open_path(sys.argv[1])
    app.mainloop()


if __name__ == "__main__":
    main()
