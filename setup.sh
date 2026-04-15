#!/usr/bin/env bash
# ============================================================
# setup.sh – Primo avvio di Permessi ASL su NAS (senza Docker)
# Eseguire UNA SOLA VOLTA dopo il primo git clone.
# ============================================================
set -euo pipefail

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$APP_DIR/venv"
SERVICE_NAME="permessi-asl"

echo "==> Directory applicazione: $APP_DIR"

# 1. Verifica Python 3
if ! command -v python3 &>/dev/null; then
  echo "ERRORE: python3 non trovato. Installa Python 3.9+ sul NAS."
  exit 1
fi
echo "==> Python: $(python3 --version)"

# 2. Verifica LibreOffice (necessario per la conversione PDF)
if ! command -v soffice &>/dev/null; then
  echo "ATTENZIONE: LibreOffice (soffice) non trovato."
  echo "  La conversione PDF non funzionerà finché non viene installato."
  echo "  Su Synology: installa il pacchetto 'LibreOffice' dal Package Center."
else
  echo "==> LibreOffice: $(soffice --version 2>/dev/null | head -1)"
fi

# 3. Crea virtualenv
if [ ! -d "$VENV_DIR" ]; then
  echo "==> Creo virtualenv..."
  python3 -m venv "$VENV_DIR"
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
else
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
