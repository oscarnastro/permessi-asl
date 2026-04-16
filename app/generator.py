import os
from datetime import date, datetime

import cloudmersive_convert_api_client
from cloudmersive_convert_api_client.rest import ApiException
from docxtpl import DocxTemplate

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
            context[f"sel_{t}"] = _DOCX_CHECKED
            context[f"giorni_{t}"] = str(_calc_days(data_dal, data_al))
            context[f"data_dal_{t}"] = _fmt_date(data_dal)
            context[f"data_al_{t}"] = _fmt_date(data_al)
        else:
            context[f"sel_{t}"] = _DOCX_UNCHECKED
            context[f"giorni_{t}"] = "___"
            context[f"data_dal_{t}"] = "___"
            context[f"data_al_{t}"] = "___"

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
    """Convert a DOCX file to PDF using the Cloudmersive Convert API SDK."""
    api_key = os.environ.get("CLOUDMERSIVE_API_KEY", "")
    if not api_key:
        raise ValueError("CLOUDMERSIVE_API_KEY environment variable non configurata")

    configuration = cloudmersive_convert_api_client.Configuration()
    configuration.api_key["Apikey"] = api_key
    api_instance = cloudmersive_convert_api_client.ConvertDocumentApi(
        cloudmersive_convert_api_client.ApiClient(configuration)
    )

    try:
        pdf_data = api_instance.convert_document_docx_to_pdf(docx_path)
    except ApiException as e:
        raise RuntimeError(f"Errore nella conversione DOCX -> PDF: {e}") from e

    with open(pdf_path, "wb") as f:
        f.write(pdf_data)
