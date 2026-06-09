from flask import Blueprint, render_template, request, jsonify, current_app, send_from_directory
from datetime import datetime
from .generator import generate_documents
from .mailer import send_mail

bp = Blueprint("main", __name__)

@bp.route("/")
def index():
    return render_template("index.html")

@bp.route("/sw.js")
def service_worker():
    static_dir = current_app.static_folder
    response = send_from_directory(static_dir, "sw.js")
    response.headers["Service-Worker-Allowed"] = "/"
    response.headers["Cache-Control"] = "no-cache"
    return response

@bp.route("/genera", methods=["POST"])
def genera():
    data = request.get_json()
    if data is None:
        return jsonify({"ok": False, "errors": {"general": "Richiesta non valida (Content-Type deve essere application/json)."}}), 400
    tipo = data.get("tipo_permesso", "").strip()

    errors = {}
    if not tipo:
        errors["tipo_permesso"] = "Seleziona il tipo di permesso."
    
    VALID_TYPES = {"congedo", "festivita", "104", "legge", "altro"}
    if tipo and tipo not in VALID_TYPES:
        errors["tipo_permesso"] = "Tipo di permesso non valido."

    raw_intervalli = data.get("intervalli")
    if raw_intervalli is None:
        raw_intervalli = [{
            "data_dal": data.get("data_dal", "").strip(),
            "data_al": data.get("data_al", "").strip(),
        }]

    if not isinstance(raw_intervalli, list):
        errors["intervalli"] = "Gli intervalli devono essere una lista."
        raw_intervalli = []

    if len(raw_intervalli) == 0:
        errors["intervalli"] = "Inserisci almeno un intervallo."
    elif len(raw_intervalli) > 3:
        errors["intervalli"] = "Puoi inserire al massimo 3 intervalli."

    intervalli = []
    for idx, raw_intervallo in enumerate(raw_intervalli[:3], start=1):
        if not isinstance(raw_intervallo, dict):
            errors[f"intervallo_{idx}"] = "Intervallo non valido."
            continue

        data_dal_str = str(raw_intervallo.get("data_dal", "")).strip()
        data_al_str = str(raw_intervallo.get("data_al", "")).strip()
        data_dal = None
        data_al = None

        if not data_dal_str:
            errors[f"intervallo_{idx}_data_dal"] = "La data di inizio è obbligatoria."
        else:
            try:
                data_dal = datetime.strptime(data_dal_str, "%Y-%m-%d").date()
            except ValueError:
                errors[f"intervallo_{idx}_data_dal"] = "Formato data non valido."

        if not data_al_str:
            errors[f"intervallo_{idx}_data_al"] = "La data di fine è obbligatoria."
        else:
            try:
                data_al = datetime.strptime(data_al_str, "%Y-%m-%d").date()
            except ValueError:
                errors[f"intervallo_{idx}_data_al"] = "Formato data non valido."

        if data_dal and data_al and data_al < data_dal:
            errors[f"intervallo_{idx}_data_al"] = "La data di fine deve essere uguale o successiva alla data di inizio."

        if data_dal and data_al:
            intervalli.append({"data_dal": data_dal, "data_al": data_al})

    if errors:
        return jsonify({"ok": False, "errors": errors}), 400

    try:
        pdf_path = generate_documents(
            tipo_permesso=tipo,
            intervalli=intervalli,
            output_dir=current_app.config["OUTPUT_DIR"],
        )
        send_mail(pdf_path)
        return jsonify({"ok": True, "message": "Permesso generato e inviato con successo."})
    except Exception as exc:
        current_app.logger.exception("Errore nella generazione o invio del permesso")
        return jsonify({"ok": False, "errors": {"general": "Errore interno del server. Contatta l'amministratore."}}), 500
