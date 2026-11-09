"""Rendu PDF des grilles d'accords (reportlab)."""
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape, portrait
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas

import model

INK = colors.HexColor("#1c1c1c")
GREY = colors.HexColor("#6b6b6b")
ACCENT = colors.HexColor("#5b3a8c")
LIGHT = colors.HexColor("#f1ecf7")

MARGIN = 1.2 * cm
LABEL_W = 3.3 * cm
REP_PAD = 0.45 * cm      # place pour ||: et :|| hors des cases
HEAD = 0.42 * cm         # place au-dessus d'une ligne (cases 1./2., xN)
BLOCK_GAP = 0.6 * cm


# ------------------------------------------------------------------ outils texte
def fit_font(c, text, font, size, max_w):
    while size > 5 and c.stringWidth(text, font, size) > max_w:
        size -= 0.5
    return size


def draw_simile(c, cx, cy, h):
    s = h * 0.22
    c.saveState()
    c.setLineWidth(max(1.6, h * 0.07))
    c.line(cx - s, cy - s, cx + s, cy + s)
    r = h * 0.055
    c.circle(cx - s * 0.95, cy + s * 0.55, r, stroke=0, fill=1)
    c.circle(cx + s * 0.95, cy - s * 0.55, r, stroke=0, fill=1)
    c.restoreState()


# ------------------------------------------------------------------ cellule
def draw_cell(c, x, y, w, h, cell):
    """(x, y) = coin bas-gauche."""
    c.setStrokeColor(INK)
    c.setFillColor(INK)
    c.setLineWidth(0.9)
    c.rect(x, y, w, h, stroke=1, fill=0)
    chord = cell["chord"].strip()
    font = "Helvetica-Bold"
    if chord in ("%", "/.", "./."):
        draw_simile(c, x + w / 2, y + h / 2, h)
    else:
        parts = model.split_chords(chord)
        if len(parts) == 1:
            fs = fit_font(c, parts[0], font, h * 0.46, w * 0.72)
            c.setFont(font, fs)
            c.drawCentredString(x + w / 2, y + h / 2 - fs * 0.35, parts[0])
        elif len(parts) == 2:
            c.setLineWidth(0.6)
            c.line(x, y, x + w, y + h)
            fs = min(fit_font(c, parts[0], font, h * 0.36, w * 0.46),
                     fit_font(c, parts[1], font, h * 0.36, w * 0.46))
            c.setFont(font, fs)
            c.drawCentredString(x + w * 0.27, y + h * 0.60, parts[0])
            c.drawCentredString(x + w * 0.73, y + h * 0.13, parts[1])
        elif parts:
            n = len(parts)
            slot = (w * 0.86) / n
            fs = min(fit_font(c, p, font, h * 0.34, slot * 0.92) for p in parts)
            c.setFont(font, fs)
            for i, p in enumerate(parts):
                c.drawCentredString(x + w * 0.07 + slot * (i + 0.5), y + h / 2 - fs * 0.35, p)
    if cell["note"].strip():
        c.setFont("Helvetica-Oblique", 7)
        c.setFillColor(GREY)
        c.drawCentredString(x + w / 2, y - 8, cell["note"].strip())
        c.setFillColor(INK)


def draw_repeat_start(c, x, y, h):
    c.saveState()
    c.setLineWidth(2.6); c.line(x - 6.5, y, x - 6.5, y + h)
    c.setLineWidth(0.9); c.line(x - 3, y, x - 3, y + h)
    r = max(1.3, h * 0.045)
    c.circle(x + 3, y + h * 0.36, r, stroke=0, fill=1)
    c.circle(x + 3, y + h * 0.64, r, stroke=0, fill=1)
    c.restoreState()


def draw_repeat_end(c, x, y, h, times):
    c.saveState()
    c.setLineWidth(0.9); c.line(x + 3, y, x + 3, y + h)
    c.setLineWidth(2.6); c.line(x + 6.5, y, x + 6.5, y + h)
    r = max(1.3, h * 0.045)
    c.circle(x - 3, y + h * 0.36, r, stroke=0, fill=1)
    c.circle(x - 3, y + h * 0.64, r, stroke=0, fill=1)
    if times and int(times) > 2:
        c.setFont("Helvetica-Bold", 10)
        c.drawRightString(x + 8, y + h + 3, f"x{int(times)}")
    c.restoreState()


def draw_row(c, x0, y, cw, ch, cells):
    for i, cell in enumerate(cells):
        draw_cell(c, x0 + i * cw, y, cw, ch, cell)
    # cases 1. / 2. (regroupées si consécutives)
    i = 0
    while i < len(cells):
        v = cells[i]["volta"]
        if not v:
            i += 1; continue
        j = i
        while j + 1 < len(cells) and cells[j + 1]["volta"] == v:
            j += 1
        xa, xb = x0 + i * cw + 2, x0 + (j + 1) * cw - 2
        top = y + ch + HEAD * 0.85
        c.setLineWidth(0.8)
        c.line(xa, y + ch + 2, xa, top)
        c.line(xa, top, xb, top)
        if v == "1":
            c.line(xb, top, xb, y + ch + 2)
        c.setFont("Helvetica-Bold", 8)
        c.drawString(xa + 3, top - 8, f"{v}.")
        i = j + 1
    for i, cell in enumerate(cells):
        if cell["start"]:
            draw_repeat_start(c, x0 + i * cw, y, ch)
        if cell["end"]:
            draw_repeat_end(c, x0 + (i + 1) * cw, y, ch, cell.get("times"))


# ------------------------------------------------------------------ blocs section
def row_head(cells):
    if any(c["volta"] or (c["end"] and int(c.get("times") or 2) > 2) for c in cells):
        return HEAD
    return 0.1 * cm


def section_geometry(sec, col_w, ch):
    rows = model.used_rows(sec)
    ncols = max([len(r) for r in rows] + [sec["cols"], 1])
    avail = col_w - LABEL_W - 2 * REP_PAD
    cw = min(ch * 2.3, avail / ncols)
    heads = [row_head(r) for r in rows]
    notes = [0.3 * cm if any(c["note"].strip() for c in r) else 0 for r in rows]
    height = sum(heads) + len(rows) * ch + sum(notes)
    if sec.get("comment", "").strip():
        height += 0.4 * cm
    return rows, cw, (heads, notes), max(height, 1.6 * cm)


def draw_label_box(c, x, y_top, w, name, sub, note=None):
    h = 0.75 * cm
    c.setFillColor(LIGHT); c.setStrokeColor(ACCENT); c.setLineWidth(1.1)
    c.roundRect(x, y_top - h, w, h, 6, stroke=1, fill=1)
    c.setFillColor(INK)
    fs = fit_font(c, name, "Helvetica-Bold", 11, w - 8)
    c.setFont("Helvetica-Bold", fs)
    c.drawCentredString(x + w / 2, y_top - h / 2 - fs * 0.35, name)
    c.setFont("Helvetica-Bold", 10); c.setFillColor(ACCENT)
    c.drawCentredString(x + w / 2, y_top - h - 12, sub)
    if note:
        c.setFont("Helvetica-Oblique", 7.5); c.setFillColor(GREY)
        c.drawCentredString(x + w / 2, y_top - h - 22, note)
    c.setFillColor(INK)


def draw_section(c, sec, x, y_top, col_w, ch):
    rows, cw, (heads, notes), _ = section_geometry(sec, col_w, ch)
    first = heads[0] if heads else 0
    draw_label_box(c, x, y_top - first, LABEL_W - 0.45 * cm, model.section_name(sec),
                   f"{model.section_measures(sec)} M")
    gx = x + LABEL_W + REP_PAD
    y = y_top
    for cells, hd, nt in zip(rows, heads, notes):
        y -= hd + ch
        draw_row(c, gx, y, cw, ch, cells)
        y -= nt
    if sec.get("comment", "").strip():
        c.setFont("Helvetica-Oblique", 8.5); c.setFillColor(GREY)
        c.drawString(gx, y - 0.32 * cm, sec["comment"].strip())
        c.setFillColor(INK)


# ------------------------------------------------------------------ structure
def structure_boxes(c, song):
    out = []
    for it in song["structure"]:
        name = model.item_name(it)
        sec = model.find_section(song, it.get("grid", ""))
        ref = model.section_name(sec) if sec else ""
        sub = f"{model.item_measures(song, it)} M"
        extra = f"= {ref}" if ref and ref != name else ""
        if it.get("note", "").strip():
            extra = (extra + "  " if extra else "") + it["note"].strip()
        w = max(c.stringWidth(name, "Helvetica-Bold", 9.5),
                c.stringWidth(extra, "Helvetica-Oblique", 7), 1.4 * cm) + 12
        out.append((name, sub, extra, w))
    return out


def structure_height(c, song, width):
    if not song["structure"]:
        return 0
    boxes = structure_boxes(c, song)
    lines, x = 1, 0
    for b in boxes:
        if x and x + b[3] > width:
            lines += 1; x = 0
        x += b[3] + 0.5 * cm
    return 0.55 * cm + lines * 1.35 * cm + 0.2 * cm


def draw_structure(c, song, x0, y_top, width):
    if not song["structure"]:
        return
    c.setFont("Helvetica-Bold", 10); c.setFillColor(ACCENT)
    total = sum(model.item_measures(song, it) for it in song["structure"])
    c.drawString(x0, y_top - 10, f"STRUCTURE  ·  {total} mesures")
    c.setFillColor(INK)
    y = y_top - 0.55 * cm
    x = x0
    boxes = structure_boxes(c, song)
    for i, (name, sub, extra, w) in enumerate(boxes):
        if x > x0 and x + w > x0 + width:
            x = x0; y -= 1.35 * cm
        h = 0.62 * cm
        c.setFillColor(LIGHT); c.setStrokeColor(ACCENT); c.setLineWidth(0.9)
        c.roundRect(x, y - h, w, h, 5, stroke=1, fill=1)
        c.setFillColor(INK); c.setFont("Helvetica-Bold", 9.5)
        c.drawCentredString(x + w / 2, y - h / 2 - 3.3, name)
        c.setFont("Helvetica-Bold", 8.5); c.setFillColor(ACCENT)
        c.drawCentredString(x + w / 2, y - h - 10, sub)
        if extra:
            c.setFont("Helvetica-Oblique", 7); c.setFillColor(GREY)
            c.drawCentredString(x + w / 2, y - h - 19, extra)
        c.setFillColor(INK)
        if i < len(boxes) - 1:
            nxt_w = boxes[i + 1][3]
            if not (x + w + 0.5 * cm + nxt_w > x0 + width):
                c.setFont("Helvetica", 10); c.setFillColor(GREY)
                c.drawCentredString(x + w + 0.25 * cm, y - h / 2 - 3.5, "›")
                c.setFillColor(INK)
        x += w + 0.5 * cm


# ------------------------------------------------------------------ page
def draw_header(c, song, pw, ph):
    y = ph - MARGIN
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 20)
    title = song["title"].strip() or "Sans titre"
    c.drawString(MARGIN, y - 18, title)
    info = [song["artist"].strip()]
    if song.get("key", "").strip():
        info.append(f"Tonalité : {song['key'].strip()}")
    if song.get("tempo", "").strip():
        info.append(f"Tempo : {song['tempo'].strip()}")
    info = "  ·  ".join(i for i in info if i)
    c.setFont("Helvetica", 10); c.setFillColor(GREY)
    c.drawRightString(pw - MARGIN, y - 16, info)
    c.setStrokeColor(ACCENT); c.setLineWidth(1.5)
    c.line(MARGIN, y - 26, pw - MARGIN, y - 26)
    c.setFillColor(INK)
    return y - 26 - 0.35 * cm


def plan(song, pw, ph, c):
    """Cherche la mise en page qui tient sur une page ; sinon multi-pages."""
    width = pw - 2 * MARGIN
    top = ph - MARGIN - 26 - 0.35 * cm
    st_h = structure_height(c, song, width)
    notes_h = 0.8 * cm if song.get("notes", "").strip() else 0
    avail = top - st_h - MARGIN - notes_h
    secs = [s for s in song["sections"]]
    col_options = [2, 1] if pw > ph else [1, 2]
    for ch in [x * cm for x in (1.5, 1.4, 1.3, 1.2, 1.1, 1.0, 0.92, 0.85, 0.78, 0.7, 0.62)]:
        for ncol in col_options:
            col_w = (width - (ncol - 1) * 0.8 * cm) / ncol
            if col_w < LABEL_W + 2 * REP_PAD + 4 * ch * 1.3:
                continue
            cols, cur, used = [[]], 0, 0
            ok = True
            for s in secs:
                h = section_geometry(s, col_w, ch)[3]
                if used + h > avail:
                    if len(cols) == ncol:
                        ok = False; break
                    cols.append([]); used = 0
                cols[-1].append(s); used += h + BLOCK_GAP
            if ok:
                return {"single": True, "ch": ch, "ncol": ncol, "col_w": col_w, "cols": cols,
                        "st_h": st_h}
    ncol = col_options[0]
    col_w = (width - (ncol - 1) * 0.8 * cm) / ncol
    return {"single": False, "ch": 0.9 * cm, "ncol": ncol, "col_w": col_w, "st_h": st_h}


def render(song, path, orientation="paysage"):
    size = landscape(A4) if orientation.lower().startswith("pay") else portrait(A4)
    pw, ph = size
    c = canvas.Canvas(path, pagesize=size)
    c.setTitle(song["title"] or "Grille")
    c.setAuthor(song.get("artist", ""))
    p = plan(song, pw, ph, c)
    width = pw - 2 * MARGIN

    y = draw_header(c, song, pw, ph)
    draw_structure(c, song, MARGIN, y, width)
    y -= p["st_h"]
    ch, col_w, ncol = p["ch"], p["col_w"], p["ncol"]

    def notes_footer():
        if song.get("notes", "").strip():
            c.setFont("Helvetica-Oblique", 9.5); c.setFillColor(INK)
            c.drawString(MARGIN, MARGIN + 0.1 * cm, "→ " + song["notes"].strip())

    if p["single"]:
        for ci, col in enumerate(p["cols"]):
            x = MARGIN + ci * (col_w + 0.8 * cm)
            yy = y
            for s in col:
                draw_section(c, s, x, yy, col_w, ch)
                yy -= section_geometry(s, col_w, ch)[3] + BLOCK_GAP
        notes_footer()
    else:
        bottom = MARGIN + (0.8 * cm if song.get("notes", "").strip() else 0)
        ci, yy = 0, y
        top_page = y
        for s in song["sections"]:
            h = section_geometry(s, col_w, ch)[3]
            if yy - h < bottom:
                ci += 1; yy = top_page
                if ci >= ncol:
                    notes_footer()
                    c.showPage()
                    top_page = draw_header(c, song, pw, ph)
                    yy, ci = top_page, 0
            x = MARGIN + ci * (col_w + 0.8 * cm)
            draw_section(c, s, x, yy, col_w, ch)
            yy -= h + BLOCK_GAP
        notes_footer()
    c.showPage()
    c.save()
    return path
