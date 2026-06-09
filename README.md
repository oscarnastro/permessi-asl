# Permessi ASL

A web application to generate leave/permission requests in **Word** and **PDF** format, with automatic email delivery.

---

## NAS Requirements

| Requirement | Notes |
|-------------|-------|
| **Python 3.9+** | On Synology: install from *Package Center → Python 3* |
| **Git** | On Synology: *Package Center → Git Server* or via `opkg` |
| **Node.js + npm** | Required for pm2. On Synology: *Package Center → Node.js* |
| **pm2** | Process manager: `npm install -g pm2` |
| **Cloudmersive API Key** | Sign up at [cloudmersive.com](https://cloudmersive.com/) to get a free key (750 conversions/month included) |
---

## First Start (Installation)

```bash
# 1. Clone the repository on the NAS
git clone https://github.com/oscarnastro/permessi-asl.git
cd permessi-asl

# 2. Run the setup script (creates virtualenv, installs dependencies, generates template, starts with pm2)
bash setup.sh

# 3. Edit the .env file with your details
nano .env
```

### `.env` Configuration

```env
# Employee data (pre-fills the document)
NOME_COGNOME=ALFANO GIUSEPPINA
MATRICOLA=891620
SERVIZIO=UOC Controllo di Gestione

# SMTP for email sending
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USE_TLS=true
SMTP_USER=user@example.com
SMTP_PASSWORD=secret
EMAIL_FROM=user@example.com
EMAIL_TO=responsabile@example.com
EMAIL_SUBJECT=Richiesta di Congedo/Permesso - {NOME_COGNOME}
EMAIL_BODY=In allegato la richiesta di congedo/permesso di {NOME_COGNOME}.

# Output folder (where to save DOCX and PDF files)
# On Synology use e.g. /volume1/permessi
OUTPUT_DIR=./output

# Cloudmersive API key for DOCX → PDF conversion
# Get your free key at https://cloudmersive.com/
CLOUDMERSIVE_API_KEY=your_api_key_here
```

---

## Starting with pm2

```bash
cd permessi-asl

# Start (or restart) using the ecosystem file
pm2 start ecosystem.config.js

# Save the process list (survives reboots)
pm2 save

# Enable pm2 to start automatically at system boot (follow the displayed instructions)
pm2 startup
```

The app will be accessible at `http://<NAS-IP>:3002`.

### Useful pm2 Commands

```bash
pm2 status                  # process status
pm2 logs permessi-asl       # real-time logs
pm2 restart permessi-asl    # restart
pm2 stop permessi-asl       # stop
pm2 delete permessi-asl     # remove from pm2 registry
```

---

## Manual Start (without pm2)

```bash
cd permessi-asl
venv/bin/gunicorn --bind 0.0.0.0:3002 --workers 2 run:app
```

---

## PDF Generation

The generation flow is:

1. The Word template (`permesso_template.docx`) is filled with employee data via `docxtpl`.
2. The compiled DOCX file is sent to the [Cloudmersive Convert](https://cloudmersive.com/convert-api) API for PDF conversion.
3. Both files (DOCX and PDF) are saved in the `OUTPUT_DIR` folder.
4. The PDF is attached and sent via email.

> Conversion via Cloudmersive ensures maximum fidelity to the original Word template, with no need to install LibreOffice on the NAS.

---

## Word Template

The `permesso_template.docx` file is provided directly by the user and remains fixed in the repository.  
Make sure it contains the Jinja2 placeholders listed below.

### Template Placeholders

| Placeholder | Description |
|-------------|-------------|
| `{{ NOME_COGNOME }}` | Employee full name (from `.env`) |
| `{{ MATRICOLA }}` | Employee ID number (from `.env`) |
| `{{ SERVIZIO }}` | Organisational unit (from `.env`) |
| `{{ DATA_CREAZIONE }}` | Document generation date (dd/mm/yyyy) |
| `{{ sel_congedo }}` | Checkbox (☒ if selected, ○ otherwise) |
| `{{ giorni_congedo }}` | Number of days calculated automatically |
| `{{ data_dal_congedo }}` | Start date (dd/mm/yyyy) |
| `{{ data_al_congedo }}` | End date (dd/mm/yyyy) |
| `{{ sel_festivita }}` | Checkbox |
| `{{ giorni_festivita }}` | Number of days |
| `{{ data_dal_festivita }}` | Start date |
| `{{ data_al_festivita }}` | End date |
| `{{ sel_104 }}` | Checkbox |
| `{{ giorni_104 }}` | Number of days |
| `{{ data_dal_104 }}` | Start date |
| `{{ data_al_104 }}` | End date |
| `{{ sel_legge }}` | Checkbox |
| `{{ giorni_legge }}` | Number of days |
| `{{ data_dal_legge }}` | Start date |
| `{{ data_al_legge }}` | End date |
| `{{ sel_altro }}` | Checkbox |
| `{{ giorni_altro }}` | Number of days |
| `{{ data_dal_altro }}` | Start date |
| `{{ data_al_altro }}` | End date |

> **Intervalli multipli (max 3)**  
> L'app consente di inserire fino a 3 intervalli di date per una singola richiesta.  
> Nel documento, i campi `data_dal_*` e `data_al_*` vengono valorizzati con le date dei vari intervalli separate da ` / `, mentre `giorni_*` riporta la somma totale dei giorni richiesti.

> **How `sel_` placeholders work**  
> When the user selects a leave type (e.g. *Ordinary leave*), the corresponding `{{ sel_congedo }}` is replaced with the **☒** character (X in a box).  
> All other `sel_` placeholders are replaced with **○** (empty box).  
> This way the resulting Word/PDF document shows exactly the ticked box as in the original form.
