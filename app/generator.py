import os
from datetime import date, datetime

_PDF_CHECKED = "[X]"
_PDF_UNCHECKED = "[ ]"


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
        if t == tipo_permesso:
            context[f"sel_{t}"] = _PDF_CHECKED
            context[f"giorni_{t}"] = str(_calc_days(data_dal, data_al))
            context[f"data_dal_{t}"] = _fmt_date(data_dal)
            context[f"data_al_{t}"] = _fmt_date(data_al)
        else:
            context[f"sel_{t}"] = _PDF_UNCHECKED
            context[f"giorni_{t}"] = "___"
            context[f"data_dal_{t}"] = "___"
            context[f"data_al_{t}"] = "___"

    cognome = os.environ.get("NOME_COGNOME", "DIPENDENTE").replace(" ", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pdf_path = os.path.join(output_dir, f"permesso_{cognome}_{timestamp}.pdf")

    _generate_pdf_from_html(context, pdf_path)
    return pdf_path


def _generate_pdf_from_html(context: dict, pdf_path: str) -> None:
    """Generate a PDF by rendering the Jinja2 HTML template and converting with WeasyPrint."""
    import jinja2
    import weasyprint

    templates_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(os.path.abspath(templates_dir)),
        autoescape=jinja2.select_autoescape(["html"]),
    )
    template = env.get_template("permesso_pdf.html")
    html_content = template.render(**context)

    weasyprint.HTML(string=html_content).write_pdf(pdf_path)
