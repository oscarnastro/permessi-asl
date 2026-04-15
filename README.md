# Permessi ASL

Applicativo web per generare richieste di congedo/permesso in formato **Word** e **PDF**, con invio automatico via email.

---

## Requisiti sul NAS

| Requisito | Note |
|-----------|------|
| **Python 3.9+** | Su Synology: installa da *Package Center → Python 3* |
| **LibreOffice** | Per la conversione in PDF. Su Synology: *Package Center → LibreOffice* |
| **Git** | Su Synology: *Package Center → Git Server* oppure tramite `opkg` |
| **SSH abilitato** | Per il deploy automatico via GitHub Actions |

---

## Primo avvio (installazione)

```bash
# 1. Clona il repository sul NAS
git clone https://github.com/oscarnastro/permessi-asl.git
cd permessi-asl

# 2. Esegui lo script di setup (crea virtualenv, installa dipendenze, genera template)
bash setup.sh

# 3. Modifica il file .env con i tuoi dati
nano .env
```

### Configurazione `.env`

```env
# Dati dipendente (precompilano il documento)
NOME_COGNOME=ALFANO GIUSEPPINA
MATRICOLA=891620
SERVIZIO=UOC Controllo di Gestione

# SMTP per invio email
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USE_TLS=true
SMTP_USER=user@example.com
SMTP_PASSWORD=secret
EMAIL_FROM=user@example.com
EMAIL_TO=responsabile@example.com
EMAIL_SUBJECT=Richiesta di Congedo/Permesso - {NOME_COGNOME}
EMAIL_BODY=In allegato la richiesta di congedo/permesso di {NOME_COGNOME}.

# Cartella di output (dove salvare DOCX e PDF)
# Su Synology usa es. /volume1/permessi
OUTPUT_DIR=./output
```

---

## Avvio manuale

```bash
cd permessi-asl
venv/bin/gunicorn --bind 0.0.0.0:5000 --workers 2 run:app
```

L'app sarà raggiungibile su `http://<IP-NAS>:5000`.

---

## Servizio systemd (avvio automatico)

Lo script `setup.sh` genera e installa automaticamente il file di servizio.  
Se preferisci installarlo manualmente:

```bash
# Modifica il file service con i tuoi percorsi
nano permessi-asl.service

# Installa (richiede root / sudo)
sudo cp permessi-asl.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable permessi-asl
sudo systemctl start permessi-asl

# Verifica stato
sudo systemctl status permessi-asl
```

---

## Continuous Integration / Deploy automatico

Ad ogni push sul branch `main`, GitHub Actions esegue via SSH:
1. `git pull origin main`
2. `pip install -r requirements.txt`
3. Rigenerazione del template Word
4. `systemctl restart permessi-asl`

### Segreti da configurare in GitHub
*Settings → Secrets → Actions:*

| Segreto | Esempio |
|---------|---------|
| `NAS_HOST` | `192.168.1.100` |
| `NAS_USER` | `admin` |
| `NAS_SSH_KEY` | chiave privata SSH (es. contenuto di `~/.ssh/id_ed25519`) |
| `NAS_APP_PATH` | `/volume1/homes/admin/permessi-asl` |

#### Generare la coppia di chiavi SSH (se non ce l'hai già)
```bash
ssh-keygen -t ed25519 -C "github-deploy" -f ~/.ssh/nas_deploy
# Copia la chiave pubblica sul NAS
ssh-copy-id -i ~/.ssh/nas_deploy.pub admin@<IP-NAS>
# Il contenuto di ~/.ssh/nas_deploy va nel segreto NAS_SSH_KEY
```

---

## Template Word

Il file `template/permesso_template.docx` viene generato automaticamente da `setup.sh`.  
Per usare il **tuo template ufficiale** (con logo, intestazione, firma):

1. Sostituisci `template/permesso_template.docx` con il tuo file
2. Assicurati che contenga i segnaposto Jinja2:
   `{{ NOME_COGNOME }}`, `{{ MATRICOLA }}`, `{{ SERVIZIO }}`, `{{ DATA_CREAZIONE }}`,  
   `{{ sel_congedo }}`, `{{ giorni_congedo }}`, `{{ data_dal_congedo }}`, `{{ data_al_congedo }}`,  
   `{{ sel_festivita }}`, `{{ giorni_festivita }}`, `{{ data_dal_festivita }}`, `{{ data_al_festivita }}`,  
   `{{ sel_104 }}`, `{{ giorni_104 }}`, `{{ data_104 }}`,  
   `{{ sel_legge }}`, `{{ giorni_legge }}`, `{{ data_dal_legge }}`, `{{ data_al_legge }}`,  
   `{{ sel_altro }}`

