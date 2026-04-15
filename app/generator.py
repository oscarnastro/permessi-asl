import os
import subprocess
from datetime import date, datetime
from docxtpl import DocxTemplate

TEMPLATE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "template", "permesso_template.docx"
)

CHECKED = "☒"
UNCHECKED = "○"


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
            if t == "104":
                context["giorni_104"] = str(_calc_days(data_dal, data_al))
                context["data_104"] = _fmt_date(data_dal)
                context["data_dal_104"] = _fmt_date(data_dal)
                context["data_al_104"] = _fmt_date(data_al)
            elif t == "altro":
                context["giorni_altro"] = "___"
                context["data_dal_altro"] = "___"
                context["data_al_altro"] = "___"
            else:
                context[f"giorni_{key}"] = str(_calc_days(data_dal, data_al))
                context[f"data_dal_{key}"] = _fmt_date(data_dal)
                context[f"data_al_{key}"] = _fmt_date(data_al)
        else:
            context[f"sel_{key}"] = UNCHECKED
            if t == "104":
                context["giorni_104"] = "___"
                context["data_104"] = "___"
                context["data_dal_104"] = "___"
                context["data_al_104"] = "___"
            else:
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

    result = subprocess.run(
        [
            "soffice",
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
    if result.returncode != 0:
        raise RuntimeError(f"LibreOffice conversion failed: {result.stderr}")

    pdf_path = os.path.join(output_dir, filename_base + ".pdf")
    if not os.path.exists(pdf_path):
        raise RuntimeError(f"PDF not found after conversion: {pdf_path}")

    return docx_path, pdf_path
