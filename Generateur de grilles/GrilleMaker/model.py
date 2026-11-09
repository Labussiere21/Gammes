"""Modèle de données de GrilleMaker (grilles d'accords + structure)."""
import copy
import json
import re
import uuid

SECTION_TYPES = ["Intro", "Couplet", "Pré-refrain", "Refrain", "Pont", "Solo",
                 "Interlude", "Break", "Outro", "Coda"]

# ---------------------------------------------------------------- cellules
def new_cell(chord=""):
    return {"chord": chord, "start": False, "end": False, "times": 2,
            "volta": "", "note": ""}


def cell_is_empty(cell):
    return not (cell["chord"].strip() or cell["start"] or cell["end"]
                or cell["volta"] or cell["note"].strip())


def split_chords(text):
    """'C, Bb' ou 'Dm Bb Bb' -> liste d'accords (le / reste dans l'accord : C/E)."""
    return [p for p in re.split(r"[,\s]+", text.strip()) if p]


# ---------------------------------------------------------------- sections
def new_section(stype="Couplet", num=1, cols=4, rows=4):
    return {"id": uuid.uuid4().hex[:8], "type": stype, "num": num, "label": "",
            "cols": cols, "rows": [[new_cell() for _ in range(cols)] for _ in range(rows)],
            "measures_auto": True, "measures": 0, "comment": ""}


def section_name(sec):
    if sec.get("label", "").strip():
        return sec["label"].strip()
    return f"{sec['type']} {sec['num']}" if sec.get("num") else sec["type"]


def resize_section(sec, cols=None, rows=None):
    if cols is not None:
        sec["cols"] = cols
        for row in sec["rows"]:
            while len(row) < cols:
                row.append(new_cell())
            del row[cols:]
    if rows is not None:
        while len(sec["rows"]) < rows:
            sec["rows"].append([new_cell() for _ in range(sec["cols"])])
        del sec["rows"][rows:]


def used_rows(sec):
    """Lignes à afficher : lignes non vides, cellules vides de fin retirées."""
    out = []
    for row in sec["rows"]:
        cells = list(row)
        while cells and cell_is_empty(cells[-1]):
            cells.pop()
        if cells:
            out.append(cells)
    return out


def compute_measures(sec):
    """Compte les mesures jouées en tenant compte des reprises et des cases 1./2."""
    total = 0
    in_block, block, v1 = False, 0, 0
    for row in used_rows(sec):
        for cell in row:
            if cell["start"]:
                in_block, block, v1 = True, 0, 0
            if in_block:
                if cell["volta"] == "1":
                    v1 += 1
                else:
                    block += 1
                if cell["end"]:
                    t = max(1, int(cell.get("times") or 2))
                    total += block * t + v1 * (t - 1)
                    in_block = False
            else:
                if cell["end"]:  # fin de reprise sans début : reprise depuis le début
                    t = max(1, int(cell.get("times") or 2))
                    total = (total + 1) * t
                else:
                    total += 1
    if in_block:
        total += block + v1
    return total


def section_measures(sec):
    return compute_measures(sec) if sec.get("measures_auto", True) else int(sec.get("measures") or 0)


# ---------------------------------------------------------------- structure
def new_item(stype, num, grid_id=""):
    return {"type": stype, "num": num, "label": "", "grid": grid_id,
            "measures_auto": True, "measures": 0, "note": ""}


def item_name(item):
    if item.get("label", "").strip():
        return item["label"].strip()
    return f"{item['type']} {item['num']}" if item.get("num") else item["type"]


def find_section(song, sid):
    for s in song["sections"]:
        if s["id"] == sid:
            return s
    return None


def item_measures(song, item):
    sec = find_section(song, item.get("grid", ""))
    if item.get("measures_auto", True) and sec:
        return section_measures(sec)
    return int(item.get("measures") or 0)


def next_num(items, stype):
    nums = [i["num"] for i in items if i["type"] == stype]
    return (max(nums) + 1) if nums else 1


def best_grid_for(song, stype, num):
    same = [s for s in song["sections"] if s["type"] == stype]
    if not same:
        return ""
    for s in same:
        if s["num"] == num:
            return s["id"]
    same.sort(key=lambda s: s["num"])
    return same[(num - 1) % len(same)]["id"]


def generate_structure(song, counts):
    """counts = {'Intro':1, 'Couplet':4, 'Refrain':3, 'Solo':1, ...}"""
    items = []

    def add(stype):
        n = next_num(items, stype)
        items.append(new_item(stype, n, best_grid_for(song, stype, n)))

    for _ in range(counts.get("Intro", 0)):
        add("Intro")
    nc, nr, npre = counts.get("Couplet", 0), counts.get("Refrain", 0), counts.get("Pré-refrain", 0)
    middles = [t for t in ("Pont", "Solo", "Interlude", "Break") if counts.get(t, 0)]
    # avec pont/solo : le dernier refrain arrive après eux, sans couplet devant
    groups_n = nr - 1 if (middles and nr >= 2) else nr
    dist = []
    if groups_n > 0:
        base, extra = divmod(nc, groups_n)
        dist = [base + (1 if i < extra else 0) for i in range(groups_n)]
    for i in range(nr):
        if i < groups_n:
            for _ in range(dist[i]):
                add("Couplet")
        if middles and nr >= 2 and i == nr - 1:
            for t in middles:
                for _ in range(counts[t]):
                    add(t)
        if npre > 0:
            add("Pré-refrain"); npre -= 1
        add("Refrain")
    for _ in range(nc - sum(dist)):
        add("Couplet")
    if middles and nr < 2:
        for t in middles:
            for _ in range(counts[t]):
                add(t)
    for t in ("Coda", "Outro"):
        for _ in range(counts.get(t, 0)):
            add(t)
    for it in items:  # un seul élément d'un type -> pas de numéro
        if sum(1 for j in items if j["type"] == it["type"]) == 1 and it["type"] not in ("Couplet", "Refrain"):
            it["num"] = 0
            if not it["grid"]:
                it["grid"] = best_grid_for(song, it["type"], 1)
    return items


# ---------------------------------------------------------------- morceau
def new_song():
    return {"version": 1, "title": "", "artist": "", "key": "", "tempo": "",
            "notes": "", "sections": [], "structure": []}


def normalize(song):
    base = new_song()
    base.update(song)
    for s in base["sections"]:
        d = new_section(s.get("type", "Couplet"), s.get("num", 1), s.get("cols", 4), 0)
        d.update(s)
        s.clear(); s.update(d)
        for row in s["rows"]:
            for i, c in enumerate(row):
                nc = new_cell(); nc.update(c); row[i] = nc
        resize_section(s, cols=s["cols"])
    for i, it in enumerate(base["structure"]):
        d = new_item(it.get("type", "Couplet"), it.get("num", 1)); d.update(it)
        base["structure"][i] = d
    return base


def save_song(song, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(song, f, ensure_ascii=False, indent=1)


def load_song(path):
    with open(path, encoding="utf-8") as f:
        return normalize(json.load(f))


def duplicate_section(sec):
    d = copy.deepcopy(sec)
    d["id"] = uuid.uuid4().hex[:8]
    return d
