import os
from datetime import date, datetime

from docxtpl import DocxTemplate
import requests

_DOCX_CHECKED = "☒"
_DOCX_UNCHECKED = "○"

_TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "..", "permesso_template.docx")


def _fmt_date(d):
    if d is None:
        return "___"
    return d.strftime("%d/%m/%Y")


def _calc_days(data_dal, data_al):
    if data_dal is None or data_al is None:
        return "___"
    return (data_al - data_dal).days + 1


def _calc_total_days(intervalli):
    if not intervalli:
        return "___"
    return sum(_calc_days(item["data_dal"], item["data_al"]) for item in intervalli)


def _format_intervalli_per_document(intervalli):
    if not intervalli:
        return "___", "___"
    data_dal_values = ", ".join(_fmt_date(item["data_dal"]) for item in intervalli)
    data_al_values = ", ".join(_fmt_date(item["data_al"]) for item in intervalli)
    return data_dal_values, data_al_values


def _format_single_interval(item):
    if item["data_dal"] == item["data_al"]:
        return _fmt_date(item["data_dal"])
    return f"{_fmt_date(item['data_dal'])} - {_fmt_date(item['data_al'])}"


def _format_intervalli_single_field(intervalli):
    if not intervalli:
        return "___"
    return " / ".join(
        f"dal {_fmt_date(item['data_dal'])} al {_fmt_date(item['data_al'])}"
        for item in intervalli
    )


def generate_documents(tipo_permesso: str, intervalli, output_dir: str):
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
            data_dal_value, data_al_value = _format_intervalli_per_document(intervalli)
            context[f"sel_{t}"] = _DOCX_CHECKED
            context[f"giorni_{t}"] = str(_calc_total_days(intervalli))
            context[f"data_dal_{t}"] = data_dal_value
            context[f"data_al_{t}"] = data_al_value
            context[f"intervalli_{t}"] = _format_intervalli_single_field(intervalli)
        else:
            context[f"sel_{t}"] = _DOCX_UNCHECKED
            context[f"giorni_{t}"] = "___"
            context[f"data_dal_{t}"] = "___"
            context[f"data_al_{t}"] = "___"
            context[f"intervalli_{t}"] = "___"

    cognome = os.environ.get("NOME_COGNOME", "DIPENDENTE").replace(" ", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    docx_path = os.path.join(output_dir, f"permesso_{cognome}_{timestamp}.docx")
    pdf_path = os.path.join(output_dir, f"permesso_{cognome}_{timestamp}.pdf")

    _fill_docx_template(context, docx_path)
    _convert_docx_to_pdf_cloudmersive(docx_path, pdf_path)
    return pdf_path


def _fill_docx_template(context: dict, docx_path: str) -> None:
    """Fill the DOCX template with the given context and save to docx_path."""
    tpl = DocxTemplate(os.path.realpath(_TEMPLATE_PATH))
    tpl.render(context)
    tpl.save(docx_path)


def _convert_docx_to_pdf_cloudmersive(docx_path: str, pdf_path: str) -> None:
    """Convert a DOCX file to PDF using the Cloudmersive Convert API."""
    api_key = os.environ.get("CLOUDMERSIVE_API_KEY", "")
    if not api_key:
        raise ValueError("CLOUDMERSIVE_API_KEY environment variable non configurata")

    try:
        with open(docx_path, "rb") as source_file:
            response = requests.post(
                "https://api.cloudmersive.com/convert/docx/to/pdf",
                headers={"Apikey": api_key},
                files={
                    "inputFile": (
                        os.path.basename(docx_path),
                        source_file,
                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    )
                },
                timeout=60,
            )
    except requests.RequestException as exc:
        raise RuntimeError(f"Errore di rete nella conversione DOCX -> PDF: {exc}") from exc

    if not response.ok:
        raise RuntimeError(
            "Errore nella conversione DOCX -> PDF: "
            f"status={response.status_code}, body={response.text[:500]}"
        )

    with open(pdf_path, "wb") as f:
        f.write(response.content)
