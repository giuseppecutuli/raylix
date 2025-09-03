# Raylix 🚄

Sistema di gestione dati per prenotazioni ferroviarie sviluppato come progetto di tesi per la laurea in **Informatica per le Aziende Digitali (L-31)**.

## Obiettivo

Il progetto nasce dall'esigenza di progettare un modello di persistenza dati robusto per il settore dei trasporti ferroviari. L'obiettivo è gestire la complessità dei sistemi di prenotazione reali: viaggi con cambi, orari variabili, operatori internazionali e tipologie di posto diverse.

Durante l'analisi del dominio, è emersa la necessità di supportare scenari complessi come viaggi intermodali (treno + traghetto), gestione di cabine per viaggi notturni, e coordinamento tra operatori di paesi diversi.

## Scelte Progettuali

### PostgreSQL come DBMS
La scelta di PostgreSQL è motivata da:
- **Integrità transazionale**: Essenziale per evitare sovraprenotazioni
- **Supporto JSONB**: Utilizzato per la gestione flessibile degli orari operativi
- **Indicizzazione avanzata**: Necessaria per query complesse di ricerca viaggi
- **Affidabilità**: Standard consolidato per applicazioni critiche

### Architettura Multi-Segmento
Il sistema gestisce viaggi complessi attraverso la tabella `booking_segments`, permettendo:
- Viaggi diretti e con cambi
- Tratte gestite da operatori diversi
- Calcolo preciso dei tempi di coincidenza
- Supporto per mezzi misti (treno + traghetto)

### Gestione Posti e Cabine
Implementata una struttura flessibile che supporta:
- Posti standard con preferenze (finestrino/corridoio)
- Cabine per viaggi notturni (cuccette, vagoni letto)
- Prenotazioni temporanee con scadenza automatica
- Gestione accessibilità

## Limitazioni del Progetto

Questo progetto si concentra esclusivamente sulla progettazione del modello dati. Non include:
- Interfaccia utente
- API di servizio
- Logica applicativa
- Sistema di pagamenti reale

## Possibili Sviluppi

Se dovessi continuare il progetto, le prossime cose da aggiungere sarebbero:

*   **API REST o GraphQL**: Per far comunicare app e siti web con il database
*   **Sistema di Prezzi Dinamici**: Estendere le tariffe per farle cambiare in base alla domanda o al tempo rimasto prima della partenza
*   **Cache per la Disponibilità**: Un sistema per calcolare velocemente quanti posti sono liberi senza dover interrogare tutto il database ogni volta
*   **Integrazioni Esterne**: Collegamento con sistemi di pagamento reali e magari con altri operatori per offrire più opzioni di viaggio
*   **Intelligenza Artificiale**: Usare tutti i dati raccolti per:
    *   Prevedere quanta gente vorrà viaggiare su certe tratte
    *   Suggerire viaggi personalizzati in base alle preferenze degli utenti
    *   Creare un chatbot intelligente per l'assistenza clienti

## Struttura Repository

```
raylix/
├── database/
│   ├── schema/
│   │   ├── schema.dbml          # Modello dati principale
│   │   └── database.sql         # Script DDL PostgreSQL
│   ├── seeds/                   # Generazione dati di test
│   └── queries/                 # Query di esempio per casi d'uso comuni
├── docs/
│   ├── tables.md               # Documentazione dettagliata tabelle
│   └── er-diagram.png          # Diagramma entità-relazione
└── README.md
```

## Generazione Dati di Test

Il progetto include un sistema completo per generare dati realistici che permette di testare lo schema con scenari d'uso reali.

### Requisiti
- **Docker & Docker Compose** (approccio consigliato)
- **Oppure**: PostgreSQL locale + Python 3.11+

### Setup con Docker (Consigliato)

```bash
# Naviga nella cartella seeds
cd database/seeds

# Avvia l'ambiente completo
./run.sh
```

Questo comando:
- Crea un database PostgreSQL 17 sulla porta 5432
- Applica automaticamente lo schema del database
- Genera dati di test realistici (operatori, stazioni, treni, prenotazioni)
- Avvia Adminer su http://localhost:8080 per esplorare i dati

### Setup Manuale

```bash
# 1. Crea il database
createdb raylix

# 2. Applica lo schema
psql -d raylix -f database/schema/database.sql

# 3. Installa dipendenze Python
cd database/seeds
pip install -r requirements.txt

# 4. Crea il file .env con le variabili d'ambiente
echo "DB_NAME=raylix
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432" > .env

# 4. Genera i dati di test
python generate_seed_data.py
```

### Esplorazione Dati

Una volta completato il setup, puoi:
- **Accedere ad Adminer**: http://localhost:8080 (user: postgres, password: postgres)
- **Connetterti via psql**: `psql -h localhost -d raylix -U postgres`
- **Eseguire le query di esempio** dalla cartella `database/queries/`

---

# Raylix 🚄 (English Version)

Railway booking data management system developed as a thesis project for the **Digital Business Informatics (L-31)** degree.

## Objective

The project stems from the need to design a robust data persistence model for the railway transport sector. The goal is to manage the complexity of real booking systems: journeys with transfers, variable schedules, international operators, and different seat types.

During domain analysis, the need emerged to support complex scenarios such as intermodal journeys (train + ferry), overnight cabin management, and coordination between operators from different countries.

## Design Choices

### PostgreSQL as DBMS
The choice of PostgreSQL is motivated by:
- **Transactional integrity**: Essential to avoid overbooking
- **JSONB support**: Used for flexible management of operating schedules
- **Advanced indexing**: Necessary for complex journey search queries
- **Reliability**: Established standard for critical applications

### Multi-Segment Architecture
The system manages complex journeys through the `booking_segments` table, enabling:
- Direct journeys and journeys with transfers
- Routes managed by different operators
- Precise calculation of connection times
- Support for mixed transport modes (train + ferry)

### Seat and Cabin Management
Implemented a flexible structure that supports:
- Standard seats with preferences (window/aisle)
- Cabins for overnight journeys (couchettes, sleeper cars)
- Temporary reservations with automatic expiration
- Accessibility management

## Project Limitations

This project focuses exclusively on data model design. It does not include:
- User interface
- Service APIs
- Application logic
- Real payment system

## Possible Future Developments

If I were to continue the project, the next things to add would be:

* **REST or GraphQL APIs**: To enable apps and websites to communicate with the database
* **Dynamic Pricing System**: Extend fares to change based on demand or time remaining before departure
* **Availability Cache**: A system to quickly calculate how many seats are available without querying the entire database every time
* **External Integrations**: Connection with real payment systems and possibly other operators to offer more travel options
* **Artificial Intelligence**: Use all collected data to:
  * Predict how many people will want to travel on certain routes
  * Suggest personalized journeys based on user preferences
  * Create an intelligent chatbot for customer assistance

## Repository Structure

```
raylix/
├── database/
│   ├── schema/
│   │   ├── schema.dbml          # Main data model
│   │   └── database.sql         # PostgreSQL DDL script
│   ├── seeds/                   # Test data generation
│   └── queries/                 # Example queries for common use cases
├── docs/
│   ├── tables.md               # Detailed table documentation
│   └── er-diagram.png          # Entity-relationship diagram
└── README.md
```

## Test Data Generation

The project includes a complete system for generating realistic data that allows testing the schema with real-world use scenarios.

### Requirements
- **Docker & Docker Compose** (recommended approach)
- **Or**: Local PostgreSQL + Python 3.11+

### Docker Setup (Recommended)

```bash
# Navigate to seeds folder
cd database/seeds

# Start the complete environment
./run.sh
```

This command:
- Creates a PostgreSQL 17 database on port 5432
- Automatically applies the database schema
- Generates realistic test data (operators, stations, trains, bookings)
- Starts Adminer on http://localhost:8080 to explore the data

### Manual Setup

```bash
# 1. Create database
createdb raylix

# 2. Apply schema
psql -d raylix -f database/schema/database.sql

# 3. Install Python dependencies
cd database/seeds
pip install -r requirements.txt

# 4. Create .env file with environment variables
echo "DB_NAME=raylix
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432" > .env

# 5. Generate test data
python generate_seed_data.py
```

### Data Exploration

Once setup is complete, you can:
- **Access Adminer**: http://localhost:8080 (user: postgres, password: postgres)
- **Connect via psql**: `psql -h localhost -d raylix -U postgres`
- **Execute example queries** from the `database/queries/` folder
