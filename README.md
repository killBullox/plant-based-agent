# Plant Based Agent

Sistema multi-agente AI per la gestione automatizzata di un'attività di nutrizione plant-based.
Costruito con Python e Claude (Anthropic).

## Moduli

| Modulo | Descrizione |
|---|---|
| `social_agent` | Genera e pubblica contenuti su Instagram e Facebook (ricette, tips, promozioni) |
| `calendar_agent` | Gestisce il calendario editoriale e gli appuntamenti su Google Calendar |
| `booking_agent` | Gestisce le prenotazioni per consulenze nutrizionali tramite Calendly |
| `email_agent` | Invia newsletter, conferme di prenotazione e follow-up via SendGrid |

## Requisiti

- Python 3.11+
- Chiavi API: Anthropic, Meta Graph API, Google Calendar, Calendly, SendGrid

## Setup

```bash
# 1. Clona il repository
git clone <repo-url>
cd plant-based-agent

# 2. Crea e attiva il virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 3. Installa le dipendenze
pip install -r requirements.txt

# 4. Configura le variabili d'ambiente
cp .env.example .env
# Modifica .env con le tue chiavi API

# 5. Avvia l'agente
python main.py
```

## Struttura del progetto

```
plant-based-agent/
├── social_agent/       # Pubblicazione contenuti sui social
├── calendar_agent/     # Gestione calendario e appuntamenti
├── booking_agent/      # Sistema di prenotazione consulenze
├── email_agent/        # Newsletter e comunicazioni email
├── main.py             # Entry point
├── requirements.txt    # Dipendenze Python
├── .env                # Variabili d'ambiente (NON committare)
└── .env.example        # Template variabili d'ambiente
```

## Sicurezza

Il file `.env` è escluso dal version control tramite `.gitignore`.
Non committare mai chiavi API o credenziali nel repository.
