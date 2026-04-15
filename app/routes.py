from flask import Blueprint, render_template, request, jsonify, current_app
from datetime import datetime
from .generator import generate_documents
from .mailer import send_mail

bp = Blueprint("main", __name__)

@bp.route("/")
def index():
    return render_template("index.html")

@bp.route("/genera", methods=["POST"])
def genera():
    data = request.get_json(force=True)
    tipo = data.get("tipo_permesso", "").strip()
    data_dal_str = data.get("data_dal", "").strip()
    data_al_str = data.get("data_al", "").strip()

    errors = {}
    if not tipo:
        errors["tipo_permesso"] = "Seleziona il tipo di permesso."
    
    VALID_TYPES = {"congedo", "festivita", "104", "legge", "altro"}
    if tipo and tipo not in VALID_TYPES:
        errors["tipo_permesso"] = "Tipo di permesso non valido."

    data_dal = None
    data_al = None

    if tipo != "altro":
        if not data_dal_str:
            errors["data_dal"] = "La data di inizio è obbligatoria."
        else:
            try:
                data_dal = datetime.strptime(data_dal_str, "%Y-%m-%d").date()
            except ValueError:
                errors["data_dal"] = "Formato data non valido."

        if not data_al_str:
            errors["data_al"] = "La data di fine è obbligatoria."
        else:
            try:
                data_al = datetime.strptime(data_al_str, "%Y-%m-%d").date()
            except ValueError:
                errors["data_al"] = "Formato data non valido."

        if data_dal and data_al and data_al < data_dal:
            errors["data_al"] = "La data di fine deve essere uguale o successiva alla data di inizio."

    if errors:
        return jsonify({"ok": False, "errors": errors}), 400

    try:
        docx_path, pdf_path = generate_documents(
            tipo_permesso=tipo,
            data_dal=data_dal,
            data_al=data_al,
            output_dir=current_app.config["OUTPUT_DIR"],
        )
        send_mail(pdf_path)
        return jsonify({"ok": True, "message": "Permesso generato e inviato con successo."})
    except Exception as exc:
        current_app.logger.exception("Errore nella generazione o invio del permesso")
        return jsonify({"ok": False, "errors": {"general": "Errore interno del server. Contatta l'amministratore."}}), 500
