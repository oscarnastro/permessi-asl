#!/usr/bin/env bash
# ============================================================
# setup.sh – Primo avvio di Permessi ASL su NAS (senza Docker)
# Eseguire UNA SOLA VOLTA dopo il primo git clone.
# ============================================================
set -euo pipefail

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$APP_DIR/venv"
SERVICE_NAME="permessi-asl"
SERVICE_SRC="$APP_DIR/permessi-asl.service"

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

# 7. Genera template Word
echo "==> Genero il template Word..."
"$VENV_DIR/bin/python" "$APP_DIR/template/create_template.py"

# 8. Installa e abilita il servizio systemd (richiede sudo/root)
if command -v systemctl &>/dev/null; then
  # Usa Python per sostituire i percorsi in modo sicuro (evita injection via sed)
  python3 - "$APP_DIR" "$(id -un)" "$SERVICE_SRC" <<'PYEOF'
import sys
app_dir, user, src = sys.argv[1], sys.argv[2], sys.argv[3]
with open(src, 'r') as f:
    content = f.read()
content = content.replace('/volume1/homes/admin/permessi-asl', app_dir)
content = content.replace('User=admin', f'User={user}')
with open('/tmp/permessi-asl.service', 'w') as f:
    f.write(content)
PYEOF

  if [ "$(id -u)" -eq 0 ]; then
    cp /tmp/permessi-asl.service /etc/systemd/system/"$SERVICE_NAME".service
    systemctl daemon-reload
    systemctl enable "$SERVICE_NAME"
    systemctl restart "$SERVICE_NAME"
    echo "==> Servizio systemd '$SERVICE_NAME' avviato e abilitato all'avvio."
  else
    echo ""
    echo "Per installare il servizio systemd, esegui questi comandi come root:"
    echo "  sudo cp /tmp/permessi-asl.service /etc/systemd/system/$SERVICE_NAME.service"
    echo "  sudo systemctl daemon-reload"
    echo "  sudo systemctl enable $SERVICE_NAME"
    echo "  sudo systemctl restart $SERVICE_NAME"
    echo ""
    echo "Oppure avvia manualmente (senza systemd):"
    echo "  $VENV_DIR/bin/gunicorn --bind 0.0.0.0:5000 --workers 2 run:app &"
  fi
else
  echo ""
  echo "systemctl non disponibile. Avvio manuale:"
  echo "  cd $APP_DIR"
  echo "  $VENV_DIR/bin/gunicorn --bind 0.0.0.0:5000 --workers 2 run:app &"
fi

echo ""
echo "✅ Setup completato. L'app sarà raggiungibile su http://<IP-NAS>:5000"
