#!/usr/bin/env bash
# ============================================================
# setup.sh – Primo avvio di Permessi ASL su NAS (senza Docker)
# Eseguire UNA SOLA VOLTA dopo il primo git clone.
# ============================================================
set -euo pipefail

APP_DIR="$(cd "").
VENV_DIR="$APP_DIR/venv"
SERVICE_NAME="permessi-asl"

echo "==> Directory applicazione: $APP_DIR"

# 1. Verifica Python 3 – preferisce python3.14 se disponibile
if command -v python3.14 &>/dev/null; then
  PYTHON_BIN="python3.14"
elif command -v python3 &>/dev/null; then
  PYTHON_BIN="python3"
else
  echo "ERRORE: python3 non trovato. Installa Python 3.9+ sul NAS."
  exit 1
fi
echo "==> Python: $($PYTHON_BIN --version)"

# 2. Verifica LibreOffice (necessario per la conversione PDF)
_SOFFICE_PATH="${SOFFICE_PATH:-}"
_SOFFICE_CANDIDATES=(
  "$_SOFFICE_PATH"
  "$(command -v soffice 2>/dev/null || true)"
  "$(command -v libreoffice 2>/dev/null || true)"
  "/var/packages/LibreOffice/target/usr/bin/soffice"
  "/var/packages/LibreOffice/target/usr/bin/libreoffice"
  "/opt/bin/soffice"
  "/opt/bin/libreoffice"
  "/opt/lib/libreoffice/program/soffice"
  "/usr/lib/libreoffice/program/soffice"
  "/usr/local/lib/libreoffice/program/soffice"
)
_SOFFICE_FOUND=""
for _candidate in "${_SOFFICE_CANDIDATES[@]}"; do
  if [ -n "$_candidate" ] && [ -x "$_candidate" ]; then
    _SOFFICE_FOUND="$_candidate"
    break
  fi
done

if [ -z "$_SOFFICE_FOUND" ]; then
  echo "INFO: LibreOffice non trovato – il PDF sarà generato in Python (fpdf2)."
  echo "  Per massima fedeltà al template Word installa LibreOffice (opzionale)."
  echo "  Se è installato in un percorso non standard, aggiungi nel .env:"
  echo "    SOFFICE_PATH=/percorso/completo/soffice"
else
  echo "==> LibreOffice: $("$_SOFFICE_FOUND" --version 2>/dev/null | head -1) [$_SOFFICE_FOUND]"
fi

# 3. Crea virtualenv
if [ ! -d "$VENV_DIR" ]; then
  echo "==> Creo virtualenv..."
  $PYTHON_BIN -m venv "$VENV_DIR"
fi

# 4. Installa dipendenze
echo "==> Installo dipendenze Python..."
"$VENV_DIR/bin/pip" install --quiet --upgrade pip
"$VENV_DIR/bin/pip" install --quiet -r "$APP_DIR/requirements.txt"

# 5. Crea .env se non esiste
if [ ! -f "$APP_DIR/.env" ]; then
  cp "$APP_DIR/.env.example" "$APP_DIR/.env"
  echo "==> Creato .env da .env.example – MODIFICA i valori prima di avviare!"
else
  echo "==> .env già esistente, mantenuto."
fi

# 6. Cartella output
mkdir -p "$APP_DIR/output"
echo "==> Cartella output: $APP_DIR/output"

# 7. Verifica che il template Word sia presente
if [ ! -f "$APP_DIR/template/permesso_template.docx" ]; then
  echo "ATTENZIONE: template/permesso_template.docx non trovato."
  echo "  Copia il tuo template nella cartella 'template/' prima di avviare l'app."
  exit 1
fi
echo "==> Template Word trovato."

# 8. Avvia il servizio con pm2
if ! command -v pm2 &>/dev/null; then
  echo "ATTENZIONE: pm2 non trovato."
  echo "  Installalo con: npm install -g pm2"
  echo "  Poi avvia manualmente con: pm2 start ecosystem.config.js"
els
  echo "==> pm2: $(pm2 --version)"
  # Ferma l'eventuale istanza precedente (ignora errore se non esiste)
pm2 delete "$SERVICE_NAME" 2>/dev/null || true
  pm2 start "$APP_DIR/ecosystem.config.js"
pm2 save
  echo "==> Servizio '$SERVICE_NAME' avviato con pm2."
  echo "    Per avviarlo automaticamente al boot esegui:"
  echo "      pm2 startup"
  echo "    e segui le istruzioni mostrate."
fi
echo ""
echo "✅ Setup completato. L'app sarà raggiungibile su http://<IP-NAS>:3002"