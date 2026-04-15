#!/usr/bin/env python3
"""
Creates template/permesso_template.docx
Run from any directory: python template/create_template.py
"""
import os
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_PATH = os.path.join(SCRIPT_DIR, "permesso_template.docx")


def add_run(para, text, bold=False, underline=False, size=None):
    run = para.add_run(text)
    run.bold = bold
    run.underline = underline
    if size:
        run.font.size = Pt(size)
    return run


def set_spacing(para, before=0, after=0, line=None):
    pf = para.paragraph_format
    pf.space_before = Pt(before)
    pf.space_after = Pt(after)
    if line:
        pf.line_spacing = Pt(line)


def main():
    doc = Document()

    # Page margins
    for section in doc.sections:
        section.top_margin = Cm(2)
        section.bottom_margin = Cm(2)
        section.left_margin = Cm(2.5)
        section.right_margin = Cm(2.5)

    # ── Title ──────────────────────────────────────────────────────────────
    title_para = doc.add_paragraph()
    title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_spacing(title_para, before=0, after=6)
    add_run(title_para, "RICHIESTA DI CONGEDO E/O PERMESSO", bold=True, underline=True, size=14)

    # ── Intro ──────────────────────────────────────────────────────────────
    intro = doc.add_paragraph()
    set_spacing(intro, before=6, after=6)
    add_run(intro, "La sottoscritta ")
    add_run(intro, "{{ NOME_COGNOME }}", bold=True)
    add_run(intro, " matricola n° ")
    add_run(intro, "{{ MATRICOLA }}", bold=True)
    add_run(intro, " in servizio presso la ")
    add_run(intro, "{{ SERVIZIO }}", bold=True)
    add_run(intro, " chiede di fruire di:")

    # ── Permission rows ────────────────────────────────────────────────────
    rows = [
        (
            "{{ sel_congedo }}",
            "  Congedo ordinario n° ",
            "{{ giorni_congedo }}",
            " giorni per i giorni dal ",
            "{{ data_dal_congedo }}",
            " al ",
            "{{ data_al_congedo }}",
        ),
        (
            "{{ sel_festivita }}",
            "  Festività soppresse n° ",
            "{{ giorni_festivita }}",
            " giorni a decorrere dal ",
            "{{ data_dal_festivita }}",
            " fino a tutto il ",
            "{{ data_al_festivita }}",
        ),
        (
            "{{ sel_104 }}",
            "  104/95 art. 3 n° ",
            "{{ giorni_104 }}",
            " giorni per il giorno ",
            "{{ data_104 }}",
            "",
            "",
        ),
        (
            "{{ sel_legge }}",
            "  Legge Permesso art. 54 (ex 40 – prestazioni specialistiche / esami diagnostici) n° ",
            "{{ giorni_legge }}",
            " giorni a decorrere dal ",
            "{{ data_dal_legge }}",
            " fino a tutto il ",
            "{{ data_al_legge }}",
        ),
        (
            "{{ sel_altro }}",
            "  Altro",
            "",
            "",
            "",
            "",
            "",
        ),
    ]

    for row in rows:
        sel, label, giorni_var, mid, dal_var, sep, al_var = row
        para = doc.add_paragraph()
        para.paragraph_format.left_indent = Cm(1)
        set_spacing(para, before=3, after=3)
        add_run(para, sel, bold=True)
        add_run(para, label)
        if giorni_var:
            add_run(para, giorni_var, bold=True)
        if mid:
            add_run(para, mid)
        if dal_var:
            add_run(para, dal_var, bold=True)
        if sep:
            add_run(para, sep)
        if al_var:
            add_run(para, al_var, bold=True)

    # ── Date and signature ──────────────────────────────────────────────────
    doc.add_paragraph()
    date_para = doc.add_paragraph()
    set_spacing(date_para, before=12, after=0)
    add_run(date_para, "Data")

    date_val = doc.add_paragraph()
    set_spacing(date_val, before=2, after=12)
    add_run(date_val, "{{ DATA_CREAZIONE }}", bold=True)
    add_run(date_val, "                                    Firma del richiedente")

    sig_para = doc.add_paragraph()
    set_spacing(sig_para, before=0, after=12)
    add_run(sig_para, "                                                   ________________________")

    # ── Approval section ────────────────────────────────────────────────────
    sep_para = doc.add_paragraph()
    set_spacing(sep_para, before=6, after=6)
    add_run(sep_para, "Viste le esigenze di servizio si esprime parere")

    fav1 = doc.add_paragraph()
    fav1.paragraph_format.left_indent = Cm(1)
    set_spacing(fav1, before=2, after=2)
    add_run(fav1, "○  Favorevole")

    fav2 = doc.add_paragraph()
    fav2.paragraph_format.left_indent = Cm(1)
    set_spacing(fav2, before=2, after=2)
    add_run(fav2, "○  Non favorevole per il seguente motivo")

    # ── Footer ──────────────────────────────────────────────────────────────
    for line in [
        "U.O.C. Controllo di Gestione",
        "Il Direttore f.f.",
        "Dott.ssa A. De Stefano",
    ]:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        set_spacing(p, before=2, after=2)
        add_run(p, line)

    doc.save(OUTPUT_PATH)
    print(f"Template saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
