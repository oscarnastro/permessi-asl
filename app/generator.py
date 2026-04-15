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

    soffice = _find_soffice()
    if soffice is None:
        raise RuntimeError(
            "LibreOffice non trovato. Installa LibreOffice e, se necessario, "
            "configura la variabile SOFFICE_PATH nel file .env con il percorso "
            "completo dell'eseguibile (es. /var/packages/LibreOffice/target/usr/bin/soffice)."
        )

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
    if result.returncode != 0:
        raise RuntimeError(f"LibreOffice: conversione PDF fallita: {result.stderr}")

    pdf_path = os.path.join(output_dir, filename_base + ".pdf")
    if not os.path.exists(pdf_path):
        raise RuntimeError(f"PDF non trovato dopo la conversione: {pdf_path}")

    return docx_path, pdf_path


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
