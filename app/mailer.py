import os
import smtplib
from email.message import EmailMessage
from email.utils import formataddr


def send_mail(pdf_path: str):
    smtp_host = os.environ.get("SMTP_HOST", "")
    if not smtp_host:
        raise ValueError("SMTP_HOST non configurato nel file .env")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_use_tls = os.environ.get("SMTP_USE_TLS", "true").lower() == "true"
    smtp_user = os.environ.get("SMTP_USER", "")
    smtp_password = os.environ.get("SMTP_PASSWORD", "")

    nome_cognome = os.environ.get("NOME_COGNOME", "Dipendente")
    email_from = os.environ.get("EMAIL_FROM", smtp_user)
    email_to_raw = os.environ.get("EMAIL_TO", "")
    email_to = [addr.strip() for addr in email_to_raw.split(",") if addr.strip()]

    if not email_to:
        raise ValueError("EMAIL_TO non configurato.")

    subject_tpl = os.environ.get(
        "EMAIL_SUBJECT", "Richiesta di Congedo/Permesso - {NOME_COGNOME}"
    )
    body_tpl = os.environ.get(
        "EMAIL_BODY",
        "In allegato la richiesta di congedo/permesso di {NOME_COGNOME}.\n\nDistinti saluti.",
    )

    subject = subject_tpl.format(NOME_COGNOME=nome_cognome)
    body = body_tpl.format(NOME_COGNOME=nome_cognome)

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = formataddr((nome_cognome, email_from))
    msg["To"] = ", ".join(email_to)
    msg.set_content(body)

    with open(pdf_path, "rb") as f:
        pdf_data = f.read()

    pdf_filename = os.path.basename(pdf_path)
    msg.add_attachment(pdf_data, maintype="application", subtype="pdf", filename=pdf_filename)

    if smtp_use_tls:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            if smtp_user and smtp_password:
                server.login(smtp_user, smtp_password)
            server.send_message(msg)
    else:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            if smtp_user and smtp_password:
                server.login(smtp_user, smtp_password)
            server.send_message(msg)
