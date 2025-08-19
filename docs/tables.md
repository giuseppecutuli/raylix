## Tabelle

### `cities`
**Scopo**: Rappresenta le città servite dalla rete ferroviaria. Ogni città può contenere una o più stazioni ferroviarie.

| Campo | Tipo | Descrizione | Indice |
|-------|------|-------------|-------|
| `id` | string | Identificativo univoco della città | PK |
| `name` | string | Nome della città (es. "Roma", "Milano") | - |
| `country` | string | Paese di appartenenza (es. "Italia", "Francia") | - |
| `latitude` | double | Coordinata geografica per geolocalizzazione | - |
| `longitude` | double | Coordinata geografica per geolocalizzazione | - |
| `created_at` | datetime | Timestamp di creazione record | - |
| `updated_at` | datetime | Timestamp ultimo aggiornamento | - |

### `stations`
**Scopo**: Rappresenta le singole stazioni ferroviarie. Una città metropolitana come Roma può avere multiple stazioni (Termini, Tiburtina, Ostiense).

| Campo | Tipo | Descrizione | Indice |
|-------|------|-------------|-------|
| `id` | string | Identificativo univoco della stazione | PK |
| `name` | string | Nome completo della stazione (es. "Roma Termini") | - |
| `city_id` | string | Riferimento alla città di appartenenza | INDEX |
| `latitude` | double | Posizione GPS specifica della stazione | - |
| `longitude` | double | Posizione GPS specifica della stazione | - |
| `created_at` | datetime | Timestamp di creazione record | - |
| `updated_at` | datetime | Timestamp ultimo aggiornamento | - |

**Indici**:
- `city_id`: Query frequenti come "mostra tutte le stazioni di Roma" richiedono accesso rapido per città. Questo indice è critico per le performance del sistema di ricerca.

### `users`
**Scopo**: Account registrati degli utenti del sistema di prenotazione online.

| Campo | Tipo | Descrizione | Indice |
|-------|------|-------------|-------|
| `id` | string | Identificativo univoco dell'utente | PK |
| `first_name` | string | Nome dell'utente | - |
| `last_name` | string | Cognome dell'utente | - |
| `email` | string | Email per autenticazione (unica nel sistema) | UNIQUE |
| `password_hash` | string | Password criptata (sicurezza: mai in chiaro) | - |
| `created_at` | datetime | Data registrazione account | - |
| `updated_at` | datetime | Ultimo aggiornamento profilo | - |

**Vincolo UNIQUE su email**: Garantisce che ogni account abbia un identificativo univoco per l'autenticazione e previene duplicazioni.

### `passengers`
**Scopo**: Rappresenta le persone che effettivamente viaggiano. La separazione da `users` permette a un utente di prenotare per familiari o colleghi.

| Campo | Tipo | Descrizione | Indice |
|-------|------|-------------|-------|
| `id` | string | Identificativo univoco del passeggero | PK |
| `user_id` | string | Riferimento all'utente (NULL per vendite in biglietteria) | INDEX |
| `first_name` | string | Nome del passeggero (come su documento) | - |
| `last_name` | string | Cognome del passeggero (come su documento) | - |
| `email` | string | Email del passeggero per comunicazioni | INDEX |
| `phone` | string | Numero di telefono per emergenze | - |
| `document_number` | string | Documento di identità per controlli a bordo | - |
| `created_at` | datetime | Timestamp di creazione | - |
| `updated_at` | datetime | Timestamp ultimo aggiornamento | - |

**Indici**:
- `user_id`: Query frequenti "tutti i passeggeri dell'utente X"
- `email`: Ricerca diretta passeggeri per comunicazioni automatiche

---

### `wagon_categories`
**Scopo**: Definisce le tipologie di vagoni (Prima Classe, Seconda Classe, Vagone Ristorante) per differenziazione servizi e tariffe.

| Campo | Tipo | Descrizione | Indice |
|-------|------|-------------|-------|
| `id` | string | Identificativo univoco della categoria | PK |
| `name` | string | Nome categoria (es. "Prima Classe", "Business") | - |
| `created_at` | datetime | Timestamp di creazione | - |
| `updated_at` | datetime | Timestamp ultimo aggiornamento | - |

### `wagons`
**Scopo**: Configurazione fisica dei singoli vagoni con sistema di generazione automatica del layout posti.

| Campo | Tipo | Descrizione | Indice |
|-------|------|-------------|-------|
| `id` | string | Identificativo univoco del vagone | PK |
| `code` | string | Codice identificativo vagone (es. "ETR500-01") | UNIQUE |
| `category_id` | string | Riferimento alla categoria di servizio | FK |
| `total_seats` | integer | Numero totale posti disponibili | - |
| `total_rows` | integer | Numero di file di sedili | - |
| `seats_per_row` | integer | Posti per fila | - |
| `layout_pattern` | string | Schema disposizione (es. "AB\|CD" dove \| = corridoio) | - |
| `row_numbering_start` | integer | Numero iniziale numerazione file (default: 1) | - |
| `created_at` | datetime | Timestamp di creazione | - |
| `updated_at` | datetime | Timestamp ultimo aggiornamento | - |

**Innovazione nel layout pattern**: Il campo `layout_pattern` "AB|CD" permette la generazione automatica di tutti i posti senza inserimento manuale. Significa: posto A, posto B, corridoio, posto C, posto D. Scalabile per qualsiasi configurazione (2+1, 2+2, 1+2, etc.).

### `wagon_seats`
**Scopo**: Rappresentazione di ogni singolo posto con posizione esatta nel layout del vagone.

| Campo | Tipo | Descrizione | Indice |
|-------|------|-------------|-------|
| `id` | string | Identificativo univoco del posto | PK |
| `wagon_id` | string | Riferimento al vagone di appartenenza | INDEX |
| `seat_number` | string | Numero posto user-friendly (es. "1A", "2B") | UNIQUE (con wagon_id) |
| `seat_type` | enum | Tipologia: WINDOW/AISLE/MIDDLE/TABLE | - |
| `seat_orientation` | enum | Orientamento: FORWARD/BACKWARD/FACING_TABLE | - |
| `row_number` | integer | Numero fila nella griglia | UNIQUE (con wagon_id, column_letter) |
| `column_letter` | string | Lettera colonna (A, B, C, D, etc.) | UNIQUE (con wagon_id, row_number) |
| `is_accessible` | bool | Posto accessibile per disabili | - |
| `created_at` | datetime | Timestamp di creazione | - |
| `updated_at` | datetime | Timestamp ultimo aggiornamento | - |

**Indici**:
- `(wagon_id, seat_number)` UNIQUE: Previene duplicazione numeri posto
- `(wagon_id, row_number, column_letter)` UNIQUE: Evita sovrapposizioni nella griglia
- `wagon_id`: Accelera ricerche posti liberi per vagone

### `trains`
**Scopo**: Rappresenta le composizioni ferroviarie complete (convoglio di locomotive e vagoni).

| Campo | Tipo | Descrizione | Indice |
|-------|------|-------------|-------|
| `id` | string | Identificativo univoco del treno | PK |
| `code` | string | Codice identificativo (es. "ETR500-001") | UNIQUE |
| `model` | string | Modello treno (es. "Frecciarossa 1000") | - |
| `created_at` | datetime | Timestamp di creazione | - |
| `updated_at` | datetime | Timestamp ultimo aggiornamento | - |

### `train_wagons`
**Scopo**: Definisce la composizione specifica di ogni treno (quali vagoni in che ordine).

| Campo | Tipo | Descrizione | Indice |
|-------|------|-------------|-------|
| `train_id` | string | Riferimento al treno | PK (con wagon_id) |
| `wagon_id` | string | Riferimento al vagone | PK (con train_id) |
| `position` | integer | Posizione nella composizione (1=testa) | UNIQUE (con train_id) |
| `created_at` | datetime | Timestamp di creazione | - |
| `updated_at` | datetime | Timestamp ultimo aggiornamento | - |

**Vincoli di integrità**:
- PRIMARY KEY composta: Un vagone può appartenere a un treno una sola volta
- UNIQUE su position: Una posizione può ospitare un solo vagone

---

### `routes`
**Scopo**: Definisce i percorsi fisici che collegano sequenze di stazioni (es. "Linea Alta Velocità Roma-Milano").

| Campo | Tipo | Descrizione | Indice |
|-------|------|-------------|-------|
| `id` | string | Identificativo univoco della route | PK |
| `name` | string | Nome commerciale del percorso | - |
| `description` | string | Descrizione dettagliata del servizio | - |
| `created_at` | datetime | Timestamp di creazione | - |
| `updated_at` | datetime | Timestamp ultimo aggiornamento | - |

### `route_stations`
**Scopo**: Definisce le stazioni che compongono ogni route con timing precisi e distanze cumulative.

| Campo | Tipo | Descrizione | Indice |
|-------|------|-------------|-------|
| `id` | string | Identificativo univoco del record | PK |
| `route_id` | string | Riferimento alla route | UNIQUE (con sequence) |
| `station_id` | string | Riferimento alla stazione | UNIQUE (con route_id) |
| `sequence` | integer | Ordine progressivo fermata (1, 2, 3...) | UNIQUE (con route_id) |
| `arrival_offset_min` | integer | Minuti dall'origine per arrivo | - |
| `departure_offset_min` | integer | Minuti dall'origine per partenza | - |
| `distance_from_start_km` | decimal | Distanza cumulativa dall'origine | - |
| `created_at` | datetime | Timestamp di creazione | - |
| `updated_at` | datetime | Timestamp ultimo aggiornamento | - |

**Logica degli offset temporali**: Se un servizio parte alle 08:00 da Roma e Milano ha `departure_offset_min=180`, la partenza da Milano sarà alle 11:00. Questo permette calcolo dinamico degli orari per qualsiasi servizio sulla stessa route.

**Ridondanza**: `distance_from_start_km` potrebbe essere calcolata dinamicamente, ma averla precompilata accelera significativamente il calcolo delle tariffe chilometriche.

### `service_calendars`
**Scopo**: Definisce i pattern di operatività temporale dei servizi (es. "Lunedì-Venerdì", "Solo weekend").

| Campo | Tipo | Descrizione | Indice |
|-------|------|-------------|-------|
| `id` | string | Identificativo univoco del calendario | PK |
| `name` | string | Nome descrittivo (es. "Feriale", "Festivo") | - |
| `start_date` | date | Data inizio validità | - |
| `end_date` | date | Data fine validità | - |
| `monday` | bool | Operativo il lunedì | - |
| `tuesday` | bool | Operativo il martedì | - |
| `wednesday` | bool | Operativo il mercoledì | - |
| `thursday` | bool | Operativo il giovedì | - |
| `friday` | bool | Operativo il venerdì | - |
| `saturday` | bool | Operativo il sabato | - |
| `sunday` | bool | Operativo la domenica | - |
| `created_at` | datetime | Timestamp di creazione | - |
| `updated_at` | datetime | Timestamp ultimo aggiornamento | - |

### `train_services`
**Scopo**: Template dei servizi ricorrenti. Collega treno, route e calendario per definire un servizio operativo.

| Campo | Tipo | Descrizione | Indice |
|-------|------|-------------|-------|
| `id` | string | Identificativo univoco del servizio | PK |
| `train_id` | string | Riferimento alla composizione treno | FK |
| `route_id` | string | Riferimento al percorso | FK |
| `calendar_id` | string | Riferimento al calendario operativo | FK |
| `departure_time` | time | Orario partenza dalla stazione origine | - |
| `service_name` | string | Nome commerciale (es. "FR 9615") | - |
| `created_at` | datetime | Timestamp di creazione | - |
| `updated_at` | datetime | Timestamp ultimo aggiornamento | - |

**Esempio pratico**: "Frecciarossa 9615 Roma-Milano, composizione ETR500-001, route AV-Roma-Milano, parte alle 08:15, operativo lunedì-sabato".

---

### `trips`
**Scopo**: Istanza specifica di un servizio in una data particolare. Ogni `train_service` genera un `trip` per ogni giorno operativo.

| Campo | Tipo | Descrizione | Indice |
|-------|------|-------------|-------|
| `id` | string | Identificativo univoco del trip | PK |
| `train_service_id` | string | Riferimento al servizio template | UNIQUE (con service_date) |
| `service_date` | date | Data specifica del viaggio | INDEX (con route_id) |
| `planned_departure_time` | datetime | Orario previsto partenza origine | - |
| `actual_departure_time` | datetime | Orario effettivo (gestione ritardi) | - |
| `estimated_arrival_time` | datetime | Stima arrivo destinazione finale | - |
| `status` | enum | SCHEDULED/RUNNING/COMPLETED/CANCELED/DELAYED | INDEX (con service_date) |
| `delay_minutes` | integer | Ritardo accumulato in minuti | INDEX (con service_date) |
| `train_id` | string | Riferimento al treno fisico | FK |
| `route_id` | string | Riferimento alla route | INDEX (con service_date) |
| `created_at` | datetime | Timestamp di creazione | - |
| `updated_at` | datetime | Timestamp ultimo aggiornamento | - |

**Indici**:
- `(service_date, route_id)`: "Tutti i treni Roma-Milano di domani"
- `(service_date, status)`: "Treni cancellati oggi"
- `(service_date, delay_minutes)`: Dashboard ritardi operativa

### `trip_station_updates`
**Scopo**: Tracking real-time dello stato del treno in ogni stazione per informazioni passeggeri.

| Campo | Tipo | Descrizione | Indice |
|-------|------|-------------|-------|
| `id` | string | Identificativo univoco aggiornamento | PK |
| `trip_id` | string | Riferimento al trip | UNIQUE (con route_station_id) |
| `route_station_id` | string | Riferimento alla fermata specifica | UNIQUE (con trip_id) |
| `planned_arrival` | datetime | Arrivo pianificato | - |
| `planned_departure` | datetime | Partenza pianificata | - |
| `actual_arrival` | datetime | Arrivo effettivo | - |
| `actual_departure` | datetime | Partenza effettiva | - |
| `delay_minutes` | integer | Ritardo in questa stazione specifica | - |
| `platform_change` | string | Eventuale cambio binario | - |
| `updated_at` | datetime | Timestamp aggiornamento real-time | INDEX |
| `created_at` | datetime | Timestamp di creazione | - |

**Indici**
- `updated_at`: Ordinamento per aggiornamenti in tempo reale.

---

### `bookings`
**Scopo**: Container principale per ogni prenotazione. Design unificato che gestisce sia viaggi diretti che journey multi-tratta.

| Campo | Tipo | Descrizione | Indice |
|-------|------|-------------|-------|
| `id` | string | Identificativo univoco prenotazione | PK |
| `booking_reference` | string | Codice alfanumerico per il cliente | UNIQUE |
| `user_id` | string | Riferimento utente (NULL per vendite anonime) | INDEX |
| `passenger_id` | string | Riferimento passeggero principale | INDEX |
| `origin_station_id` | string | Stazione partenza complessiva | INDEX (con destination_station_id) |
| `destination_station_id` | string | Stazione arrivo finale | INDEX (con origin_station_id) |
| `departure_date` | date | Data partenza | INDEX |
| `total_amount` | decimal | Importo totale prenotazione | - |
| `currency` | enum | Valuta (EUR, USD, CHF, etc.) | INDEX |
| `status` | enum | PENDING/CONFIRMED/CANCELED/REFUNDED | - |
| `created_at` | datetime | Timestamp creazione | INDEX |
| `updated_at` | datetime | Timestamp ultimo aggiornamento | - |

**Design pattern semplificato**: Ogni prenotazione, sia viaggio diretto che journey, usa sempre la stessa struttura. La complessità è gestita dai segments collegati.

### `booking_segments`
**Scopo**: Cuore del sistema. Ogni segment rappresenta una tratta su un singolo treno. Approccio unificato per tutto.

| Campo | Tipo | Descrizione | Indice |
|-------|------|-------------|-------|
| `id` | string | Identificativo univoco segment | PK |
| `booking_id` | string | Riferimento alla prenotazione | UNIQUE (con sequence) |
| `trip_id` | string | Riferimento al trip specifico | INDEX |
| `sequence` | integer | Ordine progressivo (1 per diretti, 1,2,3... per journey) | UNIQUE (con booking_id) |
| `origin_station_id` | string | Stazione partenza segment | FK |
| `destination_station_id` | string | Stazione arrivo segment | FK |
| `origin_route_station_id` | string | Punto partenza nella route | FK |
| `destination_route_station_id` | string | Punto arrivo nella route | FK |
| `planned_departure_time` | datetime | Orario partenza pianificato | - |
| `planned_arrival_time` | datetime | Orario arrivo pianificato | - |
| `actual_departure_time` | datetime | Orario partenza effettivo | - |
| `actual_arrival_time` | datetime | Orario arrivo effettivo | - |
| `connection_time_minutes` | integer | Tempo cambio treno (NULL per ultimo segment) | - |
| `platform_departure` | string | Binario partenza | - |
| `platform_arrival` | string | Binario arrivo | - |
| `distance_km` | decimal | Distanza specifica segment | - |
| `segment_amount` | decimal | Costo segment (somma = total_amount) | - |
| `created_at` | datetime | Timestamp creazione | - |
| `updated_at` | datetime | Timestamp ultimo aggiornamento | - |

**Approccio**:
- Viaggio diretto Roma-Milano: 1 segment (sequence=1)
- Multi tratta Roma-Zurich via Milano: 2 segments (sequence=1,2)

### `seat_reservations`
**Scopo**: Gestione prenotazioni posti specifici. Sempre collegata a un segment per coerenza.

| Campo | Tipo | Descrizione | Indice |
|-------|------|-------------|-------|
| `id` | string | Identificativo univoco prenotazione posto | PK |
| `booking_segment_id` | string | Riferimento al segment | UNIQUE |
| `trip_id` | string | Riferimento al trip | INDEX (con wagon_seat_id) |
| `wagon_seat_id` | string | Riferimento posto fisico | INDEX (con trip_id) |
| `passenger_id` | string | Riferimento passeggero | INDEX |
| `origin_route_station_id` | string | Inizio occupazione posto | FK |
| `destination_route_station_id` | string | Fine occupazione posto | FK |
| `expires_at` | datetime | Scadenza prenotazione temporanea | INDEX |
| `created_at` | datetime | Timestamp creazione | - |
| `updated_at` | datetime | Timestamp ultimo aggiornamento | - |

**Gestione overbooking**: `expires_at` permette prenotazioni temporanee che scadono se non confermate entro X minuti.

### `tickets`
**Scopo**: Biglietto finale emesso per ogni segment. Un journey multi-tratta genera multiple tickets.

| Campo | Tipo | Descrizione | Indice |
|-------|------|-------------|-------|
| `id` | string | Identificativo univoco biglietto | PK |
| `ticket_number` | string | Numero biglietto univoco | UNIQUE |
| `booking_id` | string | Riferimento prenotazione | INDEX |
| `booking_segment_id` | string | Riferimento segment specifico | UNIQUE |
| `passenger_id` | string | Riferimento passeggero | INDEX |
| `trip_id` | string | Riferimento trip | INDEX |
| `origin_station_id` | string | Stazione partenza | - |
| `destination_station_id` | string | Stazione arrivo | - |
| `wagon_category_id` | string | Categoria vagone | FK |
| `seat_reservation_id` | string | Riferimento posto (se prenotato) | FK |
| `fare_amount` | decimal | Tariffa biglietto | - |
| `currency` | enum | Valuta biglietto | INDEX |
| `status` | enum | VALID/USED/CANCELED/REFUNDED | - |
| `issued_at` | datetime | Data emissione | - |
| `service_date` | date | Data viaggio | INDEX |
| `created_at` | datetime | Timestamp creazione | - |
| `updated_at` | datetime | Timestamp ultimo aggiornamento | - |

**Ridondanza**: `origin_station_id` duplicato da segment accelera query tipo "biglietti da Roma" evitando join complessi su tabelle grandi.

---

### `fares`
**Scopo**: Struttura tariffaria flessibile basata su scaglioni chilometrici e categorie servizio.

| Campo | Tipo | Descrizione | Indice |
|-------|------|-------------|-------|
| `id` | string | Identificativo univoco tariffa | PK |
| `route_id` | string | Route specifica (NULL per tariffe generiche) | INDEX (con wagon_category_id) |
| `wagon_category_id` | string | Categoria servizio | INDEX (con route_id) |
| `distance_min_km` | integer | Scaglione chilometrico minimo | - |
| `distance_max_km` | integer | Scaglione chilometrico massimo | - |
| `base_fare` | decimal | Tariffa base fissa | - |
| `fare_per_km` | decimal | Tariffa variabile per chilometro | - |
| `currency` | enum | Valuta tariffa | INDEX |
| `valid_from` | datetime | Inizio validità | INDEX (con valid_to) |
| `valid_to` | datetime | Fine validità | INDEX (con valid_from) |
| `created_at` | datetime | Timestamp creazione | - |
| `updated_at` | datetime | Timestamp ultimo aggiornamento | - |

**Formula calcolo**: `tariffa_finale = base_fare + (distanza_km × fare_per_km)`

**Indici**:
- `(route_id, wagon_category_id)`: Lookup veloce tariffa specifica
- `(valid_from, valid_to)`: Filtro validità temporale
- `currency`: Raggruppamento per valuta

### `payments`
**Scopo**: Gestione completa dei pagamenti per tutte le tipologie di prenotazione.

| Campo | Tipo | Descrizione | Indice |
|-------|------|-------------|-------|
| `id` | string | Identificativo univoco pagamento | PK |
| `booking_id` | string | Riferimento prenotazione | INDEX |
| `amount` | decimal | Importo pagamento | - |
| `currency` | enum | Valuta transazione | INDEX |
| `method` | string | Metodo (carta, PayPal, contanti, etc.) | - |
| `status` | enum | PENDING/COMPLETED/FAILED/REFUNDED | INDEX |
| `transaction_ref` | string | Riferimento sistema pagamenti esterno | - |
| `paid_at` | datetime | Timestamp completamento pagamento | - |
| `created_at` | datetime | Timestamp creazione | - |
| `updated_at` | datetime | Timestamp ultimo aggiornamento | - |

---
