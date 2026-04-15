# Permessi ASL

Applicativo web per generare richieste di congedo/permesso in formato **Word** e **PDF**, con invio automatico via email.

---

## Requisiti sul NAS

| Requisito | Note |
|-----------|------|
| **Python 3.9+** | Su Synology: installa da *Package Center → Python 3* |
| **LibreOffice** *(opzionale)* | Per la conversione in PDF. Su Synology: *Package Center → LibreOffice*. Se non disponibile, l'allegato email sarà in formato **DOCX**. |
| **Git** | Su Synology: *Package Center → Git Server* oppure tramite `opkg` |
| **Node.js + npm** | Per pm2. Su Synology: *Package Center → Node.js* |
| **pm2** | Process manager: `npm install -g pm2` |
---

## Primo avvio (installazione)

```bash
# 1. Clona il repository sul NAS
git clone https://github.com/oscarnastro/permessi-asl.git
cd permessi-asl

# 2. Esegui lo script di setup (crea virtualenv, installa dipendenze, genera template, avvia con pm2)
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

## Avvio con pm2

```bash
cd permessi-asl

# Avvia (o riavvia) tramite il file ecosystem
pm2 start ecosystem.config.js

# Salva la lista dei processi (sopravvive al reboot)
pm2 save

# Abilita pm2 all'avvio automatico del sistema (segui le istruzioni mostrate)
pm2 startup
```

L'app sarà raggiungibile su `http://<IP-NAS>:3002`.

### Comandi utili pm2

```bash
pm2 status                  # stato dei processi
pm2 logs permessi-asl       # log in tempo reale
pm2 restart permessi-asl    # riavvio
pm2 stop permessi-asl       # stop
pm2 delete permessi-asl     # rimozione dal registro pm2
```

---

## Avvio manuale (senza pm2)

```bash
cd permessi-asl
venv/bin/gunicorn --bind 0.0.0.0:3002 --workers 2 run:app
```

---

## Template Word

Il file `template/permesso_template.docx` è fornito direttamente dall'utente e rimane fisso nel repository.  
Assicurati che contenga i segnaposto Jinja2 elencati di seguito.

### Segnaposto del template

| Segnaposto | Descrizione |
|------------|-------------|
| `{{ NOME_COGNOME }}` | Nome e cognome del dipendente (da `.env`) |
| `{{ MATRICOLA }}` | Matricola (da `.env`) |
| `{{ SERVIZIO }}` | Unità organizzativa (da `.env`) |
| `{{ DATA_CREAZIONE }}` | Data di generazione del documento (gg/mm/aaaa) |
| `{{ sel_congedo }}` | Segno di spunta (☒ se selezionato, ○ altrimenti) |
| `{{ giorni_congedo }}` | Numero di giorni calcolato automaticamente |
| `{{ data_dal_congedo }}` | Data inizio (gg/mm/aaaa) |
| `{{ data_al_congedo }}` | Data fine (gg/mm/aaaa) |
| `{{ sel_festivita }}` | Segno di spunta |
| `{{ giorni_festivita }}` | Numero di giorni |
| `{{ data_dal_festivita }}` | Data inizio |
| `{{ data_al_festivita }}` | Data fine |
| `{{ sel_104 }}` | Segno di spunta |
| `{{ giorni_104 }}` | Numero di giorni |
| `{{ data_dal_104 }}` | Data inizio |
| `{{ data_al_104 }}` | Data fine |
| `{{ sel_legge }}` | Segno di spunta |
| `{{ giorni_legge }}` | Numero di giorni |
| `{{ data_dal_legge }}` | Data inizio |
| `{{ data_al_legge }}` | Data fine |
| `{{ sel_altro }}` | Segno di spunta |
| `{{ giorni_altro }}` | Numero di giorni |
| `{{ data_dal_altro }}` | Data inizio |
| `{{ data_al_altro }}` | Data fine |

> **Come funzionano i segnaposto `sel_`**  
> Quando l'utente seleziona un tipo di permesso (es. *Congedo ordinario*), il corrispondente `{{ sel_congedo }}` viene sostituito con il carattere **☒** (X nel quadrato).  
> Tutti gli altri `sel_` vengono sostituiti con **○** (casella vuota).  
> In questo modo il documento Word/PDF risultante mostra esattamente la casella barrata come nel modulo originale.

