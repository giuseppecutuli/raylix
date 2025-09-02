# Raylix 🚄

Raylix è il progetto che ho sviluppato per la mia tesi di laurea in **Informatica per le Aziende Digitali (L-31)**. Si tratta di un modello di database pensato per gestire tutto quello che c'è dietro un sistema di prenotazione di biglietti nel settore dei trasporti ferroviari.

## Il Problema

Chiunque abbia mai provato a prenotare un treno sa quanto possano essere complessi questi sistemi. Dietro le quinte ci sono orari che cambiano, prezzi diversi, treni con configurazioni varie, viaggi che attraversano più paesi, e un molte altre cose da tenere sotto controllo.

Ho voluto creare uno schema di database che riesca a gestire tutta questa complessità senza diventare un disastro ingestibile.

## La Mia Soluzione: Raylix

Invece di buttarmi a creare un'app completa, mi sono concentrato sulla parte più importante: le fondamenta. Raylix è uno schema di database PostgreSQL che può gestire tutti i processi di vendita dei biglietti.

Ho progettato il sistema per gestire situazioni reali e complesse:

*   **Viaggi Misti**: Non solo treni - il sistema può gestire anche traghetti per le tratte via mare. Utile per viaggi verso le isole o per attraversare bracci di mare.
*   **Viaggi con Cambi**: Supporta sia viaggi diretti che quelli con uno o più cambi. Ogni tratta è gestita separatamente (nelle `booking_segments`) ma tutto resta collegato.
*   **Posti e Cabine**: Va oltre il semplice posto numerato. Gestisce tutto, dai posti finestrino/corridoio fino alle cabine per i viaggi notturni con le cuccette.
*   **Multi-paese**: Pensato per operatori che lavorano in più nazioni, con valute diverse e operatori ferroviari diversi.
*   **Orari Complessi**: Gestisce orari che cambiano stagionalmente, giorni della settimana diversi, e anche le eccezioni tipo scioperi o corse straordinarie.

## Perché PostgreSQL

Per il database ho scelto **PostgreSQL** per alcuni motivi pratici:

*   **Affidabilità**: In un sistema di prenotazioni non puoi permetterti che due persone prenotino lo stesso posto. PostgreSQL garantisce che le transazioni siano atomiche e sicure.
*   **Flessibilità**: Supporta tipi di dati avanzati come JSONB, che ho usato per gestire i giorni operativi dei servizi in modo flessibile.
*   **Performance**: Ha strumenti di indicizzazione potenti, fondamentali per le ricerche di viaggi disponibili.
*   **Open Source**: È gratis e ha una community enorme, quindi è una scelta sicura anche per progetti reali.

## Cosa Contiene il Progetto

**Importante**: Raylix non è un'app pronta all'uso. È la struttura dati su cui costruire un'applicazione.

Nel repository trovi:
*   Lo **schema DBML** completo con tutte le tabelle e relazioni
*   Il **dump SQL** per creare il database su PostgreSQL
*   La **documentazione** dettagliata di tutte le tabelle
*   **Query di esempio** per le operazioni più comuni (ricerca viaggi, storico prenotazioni, verifica biglietti)

Manca tutto il resto (API, interfaccia utente, ecc.) perché l'obiettivo era concentrarsi solo sulla progettazione dei dati.

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

## Struttura del Repository

```
raylix/
├── database/
│   ├── schema/
│   │   └── schema.dbml          # Schema completo del database
│   ├── seeds/                   # Dati di esempio
│   └── queries/                 # Query SQL di esempio
├── docs/
│   ├── tables.md               # Documentazione delle tabelle
│   └── er-diagram.png          # Diagramma entità-relazione
└── README.md                   # Questo file
```
