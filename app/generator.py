import os
import subprocess
from datetime import date, datetime
from docxtpl import DocxTemplate

TEMPLATE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "template", "permesso_template.docx"
)

CHECKED = "☒"
UNCHECKED = "○"

# Symbols used in the native PDF (built-in fonts only support Latin-1)
_PDF_CHECKED = "[X]"
_PDF_UNCHECKED = "[ ]"

_TYPE_LABELS = {
    "congedo": "Congedo ordinario",
    "festivita": "Festivita' soppresse",
    "104": "Permessi L. 104/92",
    "legge": "Altre leggi/CCNL",
    "altro": "Altro",
}


def _fmt_date(d):
    if d is None:
        return "___"
    return d.strftime("%d/%m/%Y")


def _calc_days(data_dal, data_al):
    if data_dal is None or data_al is None:
        return "___"
    return (data_al - data_dal).days + 1


def generate_documents(tipo_permesso: str, data_dal, data_al, output_dir: str):
    # Resolve and validate output_dir to prevent path traversal
    output_dir = os.path.realpath(output_dir)
    os.makedirs(output_dir, exist_ok=True)

    types = ["congedo", "festivita", "104", "legge", "altro"]
    
    context = {
        "NOME_COGNOME": os.environ.get("NOME_COGNOME", "___"),
        "MATRICOLA": os.environ.get("MATRICOLA", "___"),
        "SERVIZIO": os.environ.get("SERVIZIO", "___"),
        "DATA_CREAZIONE": date.today().strftime("%d/%m/%Y"),
    }

    for t in types:
        key = t
        if t == tipo_permesso:
            context[f"sel_{key}"] = CHECKED
            context[f"giorni_{key}"] = str(_calc_days(data_dal, data_al))
            context[f"data_dal_{key}"] = _fmt_date(data_dal)
            context[f"data_al_{key}"] = _fmt_date(data_al)
        else:
            context[f"sel_{key}"] = UNCHECKED
            context[f"giorni_{key}"] = "___"
            context[f"data_dal_{key}"] = "___"
            context[f"data_al_{key}"] = "___"

    tpl = DocxTemplate(TEMPLATE_PATH)
    tpl.render(context)

    cognome = os.environ.get("NOME_COGNOME", "DIPENDENTE").replace(" ", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename_base = f"permesso_{cognome}_{timestamp}"

    docx_path = os.path.join(output_dir, filename_base + ".docx")
    tpl.save(docx_path)

    pdf_path = os.path.join(output_dir, filename_base + ".pdf")

    soffice = _find_soffice()
    if soffice is not None:
        result = subprocess.run(
            [
                soffice,
                "--headless",
                "--convert-to",
                "pdf",
                "--outdir",
                output_dir,
                docx_path,
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode == 0 and os.path.exists(pdf_path):
            return docx_path, pdf_path

    # LibreOffice not available or conversion failed – generate PDF natively
    _generate_pdf_native(context, types, tipo_permesso, pdf_path)
    return docx_path, pdf_path


def _generate_pdf_native(context: dict, types: list, tipo_permesso: str, pdf_path: str) -> None:
    """Generate a PDF using fpdf2 (pure Python, no external dependencies)."""
    from fpdf import FPDF

    pdf = FPDF()
    pdf.set_margins(20, 20, 20)
    pdf.add_page()

    # ── Title ──────────────────────────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "RICHIESTA DI CONGEDO / PERMESSO", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    # ── Header fields ──────────────────────────────────────────────────────
    pdf.set_font("Helvetica", "", 10)
    usable_w = pdf.w - pdf.l_margin - pdf.r_margin  # ~170 mm

    label_w = 30
    value_w = usable_w / 2 - label_w - 4

    def header_row(label1, val1, label2, val2):
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(label_w, 7, label1 + ":", border=0)
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(value_w, 7, val1, border="B")
        pdf.cell(4, 7, "", border=0)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(label_w, 7, label2 + ":", border=0)
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 7, val2, border="B", new_x="LMARGIN", new_y="NEXT")

    header_row("Dipendente", context["NOME_COGNOME"], "Matricola", context["MATRICOLA"])
    header_row("Servizio/UO", context["SERVIZIO"], "Data", context["DATA_CREAZIONE"])
    pdf.ln(6)

    # ── Table header ───────────────────────────────────────────────────────
    col_tipo = 65
    col_sel = 18
    col_giorni = 20
    col_dal = 35
    col_al = 35

    pdf.set_fill_color(220, 220, 220)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(col_tipo, 7, "Tipo di permesso/congedo", border=1, align="C", fill=True)
    pdf.cell(col_sel, 7, "Richiesto", border=1, align="C", fill=True)
    pdf.cell(col_giorni, 7, "Giorni", border=1, align="C", fill=True)
    pdf.cell(col_dal, 7, "Dal", border=1, align="C", fill=True)
    pdf.cell(col_al, 7, "Al", border=1, align="C", fill=True, new_x="LMARGIN", new_y="NEXT")

    # ── Table rows ─────────────────────────────────────────────────────────
    pdf.set_font("Helvetica", "", 9)
    for t in types:
        is_sel = t == tipo_permesso
        sel_symbol = _PDF_CHECKED if is_sel else _PDF_UNCHECKED
        fill = is_sel
        pdf.set_fill_color(235, 245, 255)

        pdf.set_font("Helvetica", "B" if is_sel else "", 9)
        pdf.cell(col_tipo, 7, _TYPE_LABELS.get(t, t), border=1, fill=fill)
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(col_sel, 7, sel_symbol, border=1, align="C", fill=fill)
        pdf.cell(col_giorni, 7, context.get(f"giorni_{t}", "___"), border=1, align="C", fill=fill)
        pdf.cell(col_dal, 7, context.get(f"data_dal_{t}", "___"), border=1, align="C", fill=fill)
        pdf.cell(col_al, 7, context.get(f"data_al_{t}", "___"), border=1, align="C", fill=fill,
                 new_x="LMARGIN", new_y="NEXT")

    pdf.ln(12)

    # ── Signature area ─────────────────────────────────────────────────────
    sig_w = 70
    pdf.set_font("Helvetica", "", 9)
    pdf.set_x(pdf.w - pdf.r_margin - sig_w)
    pdf.cell(sig_w, 5, "Firma del dipendente", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(pdf.w - pdf.r_margin - sig_w)
    pdf.cell(sig_w, 10, "", border="B", new_x="LMARGIN", new_y="NEXT")

    pdf.output(pdf_path)


def _find_soffice():
    """Return the path to soffice/libreoffice, or None if not available.

    Search order:
    1. SOFFICE_PATH environment variable (user override)
    2. PATH (shutil.which)
    3. Common Synology NAS installation paths
    """
    import shutil

    # 1. User-configured explicit path
    env_path = os.environ.get("SOFFICE_PATH", "").strip()
    if env_path and os.path.isfile(env_path) and os.access(env_path, os.X_OK):
        return env_path

    # 2. Standard PATH lookup
    for cmd in ("soffice", "libreoffice"):
        path = shutil.which(cmd)
        if path:
            return path

    # 3. Common Synology / NAS installation paths
    synology_candidates = [
        # Package Center (DSM 6/7)
        "/var/packages/LibreOffice/target/usr/bin/soffice",
        "/var/packages/LibreOffice/target/usr/bin/libreoffice",
        # Entware / opkg
        "/opt/bin/soffice",
        "/opt/bin/libreoffice",
        "/opt/lib/libreoffice/program/soffice",
        # Generic Linux fallbacks
        "/usr/lib/libreoffice/program/soffice",
        "/usr/local/lib/libreoffice/program/soffice",
    ]
    for candidate in synology_candidates:
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate

    return None



def _find_soffice():
    """Return the path to soffice/libreoffice, or None if not available.

    Search order:
    1. SOFFICE_PATH environment variable (user override)
    2. PATH (shutil.which)
    3. Common Synology NAS installation paths
    """
    import shutil

    # 1. User-configured explicit path
    env_path = os.environ.get("SOFFICE_PATH", "").strip()
    if env_path and os.path.isfile(env_path) and os.access(env_path, os.X_OK):
        return env_path

    # 2. Standard PATH lookup
    for cmd in ("soffice", "libreoffice"):
        path = shutil.which(cmd)
        if path:
            return path

    # 3. Common Synology / NAS installation paths
    synology_candidates = [
        # Package Center (DSM 6/7)
        "/var/packages/LibreOffice/target/usr/bin/soffice",
        "/var/packages/LibreOffice/target/usr/bin/libreoffice",
        # Entware / opkg
        "/opt/bin/soffice",
        "/opt/bin/libreoffice",
        "/opt/lib/libreoffice/program/soffice",
        # Generic Linux fallbacks
        "/usr/lib/libreoffice/program/soffice",
        "/usr/local/lib/libreoffice/program/soffice",
    ]
    for candidate in synology_candidates:
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate

    return None
