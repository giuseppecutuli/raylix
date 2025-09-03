# Documentazione Tabelle

## Note di Progettazione

Durante lo sviluppo dello schema, alcune decisioni si sono rivelate più complesse del previsto. Questo documento raccoglie la logica dietro la struttura delle tabelle e le considerazioni che mi hanno portato alle scelte finali.

### Separazione `users` vs `passengers`
Inizialmente avevo pensato a una struttura più semplice con una sola tabella utenti. Tuttavia, analizzando i casi d'uso reali (prenotazioni aziendali, genitori che prenotano per figli, acquisti per terzi), ho capito che era necessario separare chi paga da chi viaggia.

### Gestione Multi-Segmento
La parte più complessa è stata progettare `booking_segments`. L'alternativa era avere una tabella `connections` separata, ma avrebbe reso le query molto più complesse. La soluzione attuale permette di gestire sia viaggi diretti che con cambi usando la stessa logica.

### Indicizzazione Strategica
Gli indici sono stati pensati per le query più comuni:
- Ricerca viaggi disponibili: `trips(service_date, status)`
- Timeline prenotazioni utente: `bookings(user_id, created_at)`
- Controllo biglietti: `tickets(ticket_number, service_date)`

## Problemi Risolti Durante lo Sviluppo

### Concorrenza sui Posti
**Problema**: Due utenti che tentano di prenotare lo stesso posto simultaneamente.
**Soluzione**: Campo `expires_at` in `seat_reservations` che crea una "prenotazione temporanea" durante il processo di checkout. Se il pagamento non viene completato entro il tempo limite, il posto si libera automaticamente.

### Gestione Orari Complessi
**Problema**: Come gestire orari che cambiano stagionalmente, giorni festivi, scioperi.
**Soluzione**: Combinazione di `operates_days` (JSONB) per il calendario base e `service_exceptions` per le eccezioni. Più flessibile di una tabella calendar rigida.

### Performance Ricerche
**Problema**: Le query per cercare viaggi disponibili erano lentissime su dataset grandi.
**Soluzione**: Indici composti strategici, in particolare `trips(service_date, status, planned_departure_time)` che copre il 90% delle ricerche comuni.

### Tariffe Multi-Paese
**Problema**: Operatori diversi con regole tariffarie completamente diverse.
**Soluzione**: Sistema di priorità in `fares` che parte dalle regole più specifiche (route + operatore + categoria) fino alle più generiche (solo distanza).

## Alternative Considerate

### Gestione Posti
**Alternativa scartata**: Tabella separata `seat_availability` con uno snapshot per ogni combinazione trip/posto.
**Perché scartata**: Troppo pesante in termini di storage. Con 1000 posti per treno e 100 viaggi al giorno = 100k record solo per un giorno.

### Struttura Prenotazioni
**Alternativa scartata**: Tabella unica `bookings` con campo JSON per i segmenti.
**Perché scartata**: Le query per cercare prenotazioni per trip specifici diventavano complesse e lente.

### Gestione Prezzi
**Alternativa scartata**: Prezzi fissi per ogni combinazione origine-destinazione.
**Perché scartata**: Non scalabile per un sistema internazionale con centinaia di operatori e migliaia di rotte.

## Tabelle

### `countries`
**Scopo**: Definisce le nazioni in cui opera il servizio. Fondamentale per un sistema multi-country.

| Campo | Tipo | Descrizione | Indice |
|-------|------|-------------|-------|
| `id` | string | Identificativo univoco del paese | PK |
| `name` | string | Nome del paese (es. "Italia", "Svizzera") | - |
| `iso_code` | string | Codice ISO 3166-1 alpha-2 (es. "IT", "CH") | UNIQUE |
| `created_at` | datetime | Timestamp di creazione record | - |
| `updated_at` | datetime | Timestamp ultimo aggiornamento | - |

### `railway_operators`
**Scopo**: Rappresenta le diverse compagnie ferroviarie che operano i servizi, ciascuna legata a un paese.

| Campo | Tipo | Descrizione | Indice |
|-------|------|-------------|-------|
| `id` | string | Identificativo univoco dell'operatore | PK |
| `name` | string | Nome dell'operatore (es. "Trenitalia", "SBB CFF FFS") | - |
| `country_id` | string | Riferimento al paese di origine dell'operatore | INDEX |
| `code` | string | Codice univoco (es. "TI", "SBB") | UNIQUE |
| `website` | string | Sito web ufficiale | - |
| `created_at` | datetime | Timestamp di creazione record | - |
| `updated_at` | datetime | Timestamp ultimo aggiornamento | - |

### `cities`
**Scopo**: Rappresenta le città servite. Ogni città può contenere una o più stazioni.

| Campo | Tipo | Descrizione | Indice |
|-------|------|-------------|-------|
| `id` | string | Identificativo univoco della città | PK |
| `name` | string | Nome della città (es. "Roma", "Milano") | - |
| `country_id` | string | Riferimento al paese di appartenenza | INDEX |
| `latitude` | double | Coordinata geografica per geolocalizzazione | - |
| `longitude` | double | Coordinata geografica per geolocalizzazione | - |
| `created_at` | datetime | Timestamp di creazione record | - |
| `updated_at` | datetime | Timestamp ultimo aggiornamento | - |

### `stations`
**Scopo**: Rappresenta le singole stazioni. Una città può avere multiple stazioni (es. Roma Termini, Roma Tiburtina).

| Campo | Tipo | Descrizione | Indice |
|-------|------|-------------|-------|
| `id` | string | Identificativo univoco della stazione | PK |
| `name` | string | Nome completo della stazione (es. "Roma Termini") | INDEX |
| `city_id` | string | Riferimento alla città di appartenenza | INDEX |
| `latitude` | double | Posizione GPS specifica della stazione | INDEX (con longitude) |
| `longitude` | double | Posizione GPS specifica della stazione | INDEX (con latitude) |
| `created_at` | datetime | Timestamp di creazione record | - |
| `updated_at` | datetime | Timestamp ultimo aggiornamento | - |

### `users`
**Scopo**: Account registrati degli utenti del sistema di prenotazione.

| Campo | Tipo | Descrizione | Indice |
|-------|------|-------------|-------|
| `id` | string | Identificativo univoco dell'utente | PK |
| `first_name` | string | Nome dell'utente | - |
| `last_name` | string | Cognome dell'utente | - |
| `email` | string | Email per autenticazione (unica nel sistema) | UNIQUE |
| `password` | string | Password criptata (mai in chiaro) | - |
| `created_at` | datetime | Data registrazione account | - |
| `updated_at` | datetime | Ultimo aggiornamento profilo | - |

### `passengers`
**Scopo**: Rappresenta le persone che viaggiano. Separata da `users` per permettere a un utente di prenotare per altri (familiari, colleghi).

| Campo | Tipo | Descrizione | Indice |
|-------|------|-------------|-------|
| `id` | string | Identificativo univoco del passeggero | PK |
| `user_id` | string | Riferimento all'utente (NULL per acquisti anonimi) | INDEX |
| `first_name` | string | Nome del passeggero (come su documento) | - |
| `last_name` | string | Cognome del passeggero (come su documento) | - |
| `email` | string | Email del passeggero per comunicazioni | INDEX |
| `phone` | string | Numero di telefono per emergenze | - |
| `document_number` | string | Documento di identità per controlli | - |
| `created_at` | datetime | Timestamp di creazione | - |
| `updated_at` | datetime | Timestamp ultimo aggiornamento | - |

### `service_types`
**Scopo**: Classifica i tipi di servizio (es. Alta Velocità, Regionale, Intercity) che influenzano regole come la prenotazione del posto obbligatoria.

| Campo | Tipo | Descrizione | Indice |
|-------|------|-------------|-------|
| `id` | string | Identificativo univoco del tipo servizio | PK |
| `name` | string | Nome del servizio (es. "Alta Velocità") | - |
| `code` | string | Codice univoco (es. "AV", "REG") | UNIQUE |
| `requires_seat_assignment` | bool | `true` se la prenotazione del posto è obbligatoria | - |
| `allows_standing` | bool | `true` se sono ammessi passeggeri in piedi | - |
| `created_at` | datetime | Timestamp di creazione | - |
| `updated_at` | datetime | Timestamp ultimo aggiornamento | - |

### `wagon_categories`
**Scopo**: Definisce le classi di servizio (Prima, Seconda, Business) per differenziare servizi e tariffe.

| Campo | Tipo | Descrizione | Indice |
|-------|------|-------------|-------|
| `id` | string | Identificativo univoco della categoria | PK |
| `name` | string | Nome categoria (es. "Prima Classe", "Business") | - |
| `created_at` | datetime | Timestamp di creazione | - |
| `updated_at` | datetime | Timestamp ultimo aggiornamento | - |

### `wagons`
**Scopo**: Configurazione fisica dei singoli vagoni.

| Campo | Tipo | Descrizione | Indice |
|-------|------|-------------|-------|
| `id` | string | Identificativo univoco del vagone | PK |
| `code` | string | Codice identificativo vagone (es. "W-ETR500-1CL-01") | UNIQUE |
| `category_id` | string | Riferimento alla categoria di servizio | FK |
| `total_seats` | integer | Numero totale posti disponibili | - |
| `total_rows` | integer | Numero di file di sedili | - |
| `seats_per_row` | integer | Posti per fila | - |
| `layout_pattern` | string | Schema disposizione (es. "AB|CD" dove | = corridoio) | - |
| `row_numbering_start` | integer | Numero iniziale numerazione file (default: 1) | - |
| `created_at` | datetime | Timestamp di creazione | - |
| `updated_at` | datetime | Timestamp ultimo aggiornamento | - |

### `cabins`
**Scopo**: Gestisce le cabine per i viaggi notturni (cuccette, vagoni letto).

| Campo | Tipo | Descrizione | Indice |
|-------|------|-------------|-------|
| `id` | string | Identificativo univoco della cabina | PK |
| `wagon_id` | string | Riferimento al vagone di appartenenza | FK |
| `cabin_number` | string | Numero della cabina (es. "C4-101") | UNIQUE (con wagon_id) |
| `cabin_type` | cabin_type | Tipologia (es. `COUCHETTE_4`, `SLEEPER_SINGLE`) | - |
| `total_beds` | integer | Numero di letti nella cabina | - |
| `has_private_bathroom` | bool | `true` se la cabina ha un bagno privato | - |
| `created_at` | datetime | Timestamp di creazione | - |
| `updated_at` | datetime | Timestamp ultimo aggiornamento | - |

### `wagon_seats`
**Scopo**: Rappresenta ogni singolo posto o letto, con posizione esatta e associazione a una cabina (se applicabile).

| Campo | Tipo | Descrizione | Indice |
|-------|------|-------------|-------|
| `id` | string | Identificativo univoco del posto/letto | PK |
| `wagon_id` | string | Riferimento al vagone di appartenenza | INDEX (con seat_number, seat_type) |
| `cabin_id` | string | Riferimento alla cabina (NULL se non è in una cabina) | INDEX |
| `seat_number` | string | Numero posto user-friendly (es. "1A", "Letto 102") | UNIQUE (con wagon_id) |
| `seat_type` | seat_type | Tipologia: `WINDOW`, `AISLE`, `COUCHETTE_LOWER` | - |
| `seat_orientation` | seat_orientation | Orientamento: `FORWARD`, `BACKWARD` | - |
| `row_number` | integer | Numero fila nella griglia | - |
| `column_letter` | string | Lettera colonna (A, B, C, D, etc.) | - |
| `is_accessible` | bool | Posto accessibile per disabili | - |
| `created_at` | datetime | Timestamp di creazione | - |
| `updated_at` | datetime | Timestamp ultimo aggiornamento | - |

**Logica Posto/Cabina**: Se `cabin_id` è valorizzato, il posto è in realtà un letto all'interno di una cabina. Questo permette di gestire sia posti a sedere tradizionali che cuccette/vagoni letto con un'unica tabella.

### `trains`
**Scopo**: Rappresenta i convogli. Include un flag per gestire mezzi navali (traghetti) per tratte marittime.

| Campo | Tipo | Descrizione | Indice |
|-------|------|-------------|-------|
| `id` | string | Identificativo univoco del treno/nave | PK |
| `code` | string | Codice identificativo (es. "ETR1000-01", "SHIP-PAL-NAP") | UNIQUE |
| `model` | string | Modello (es. "Frecciarossa 1000", "Traghetto veloce") | - |
| `is_ship` | bool | `true` se il mezzo è una nave/traghetto | - |
| `created_at` | datetime | Timestamp di creazione | - |
| `updated_at` | datetime | Timestamp ultimo aggiornamento | - |

**Gestione Intermodale**: Il flag `is_ship` permette di usare la stessa logica di prenotazione per tratte che includono una traversata marittima, soddisfacendo un requisito chiave del progetto.

### `train_wagons`
**Scopo**: Definisce la composizione specifica di ogni treno (quali vagoni in che ordine).

| Campo | Tipo | Descrizione | Indice |
|-------|------|-------------|-------|
| `train_id` | string | Riferimento al treno | PK (con wagon_id) |
| `wagon_id` | string | Riferimento al vagone | PK (con train_id) |
| `position` | integer | Posizione nella composizione (1=testa) | UNIQUE (con train_id) |
| `created_at` | datetime | Timestamp di creazione | - |
| `updated_at` | datetime | Timestamp ultimo aggiornamento | - |

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
**Scopo**: Definisce le fermate che compongono ogni route con i relativi tempi di percorrenza.

| Campo | Tipo | Descrizione | Indice |
|-------|------|-------------|-------|
| `id` | string | Identificativo univoco del record | PK |
| `route_id` | string | Riferimento alla route | UNIQUE (con sequence, station_id) |
| `station_id` | string | Riferimento alla stazione | UNIQUE (con route_id) |
| `sequence` | integer | Ordine progressivo fermata (1, 2, 3...) | UNIQUE (con route_id) |
| `arrival_offset_min` | integer | Minuti dall'origine per l'arrivo (NULL per la partenza) | - |
| `departure_offset_min` | integer | Minuti dall'origine per la partenza (NULL per destinazione) | - |
| `created_at` | datetime | Timestamp di creazione | - |
| `updated_at` | datetime | Timestamp ultimo aggiornamento | - |

### `train_services`
**Scopo**: Template dei servizi ricorrenti. Collega treno, route e calendario per definire un servizio operativo.

**Nota**: Inizialmente avevo chiamato questa tabella `schedules`, ma poi ho capito che era più appropriato `train_services` perché rappresenta effettivamente un servizio commerciale con nome, orari e validità.

| Campo | Tipo | Descrizione | Indice |
|-------|------|-------------|-------|
| `id` | string | Identificativo univoco del servizio | PK |
| `train_id` | string | Riferimento alla composizione treno/nave | FK |
| `route_id` | string | Riferimento al percorso | INDEX (con departure_time) |
| `service_type_id` | string | Riferimento al tipo di servizio (AV, REG) | INDEX (con operator_id) |
| `operator_id` | string | Riferimento all'operatore ferroviario | INDEX (con service_type_id) |
| `departure_time` | time | Orario partenza dalla stazione origine | - |
| `service_name` | string | Nome commerciale (es. "FR 9615") | - |
| `operates_days` | jsonb | Giorni operativi (es. `{"mon": true, "tue": true...}`) | - |
| `valid_from` | date | Data inizio validità orario | INDEX (con valid_to) |

**Nota su operates_days**: Ho scelto JSONB invece di una tabella separata per i giorni operativi perché la maggior parte dei servizi ha pattern semplici (es. "dal lunedì al venerdì"). Per casi complessi si può sempre usare `service_exceptions`.
| `valid_to` | date | Data fine validità orario | INDEX (con valid_from) |
| `cabins_enabled` | bool | `true` se il servizio offre cabine/cuccette | - |
| `created_at` | datetime | Timestamp di creazione | - |
| `updated_at` | datetime | Timestamp ultimo aggiornamento | - |

**Logica Orari**: Invece di una tabella `calendars`, si usa un approccio più flessibile. `operates_days` (JSONB) definisce i giorni della settimana, mentre `valid_from` e `valid_to` definiscono il periodo di validità dell'orario (es. orario estivo/invernale).

### `service_exceptions`
**Scopo**: Gestisce le eccezioni al calendario regolare, come cancellazioni per sciopero o servizi straordinari.

| Campo | Tipo | Descrizione | Indice |
|-------|------|-------------|-------|
| `id` | string | Identificativo univoco dell'eccezione | PK |
| `train_service_id` | string | Riferimento al servizio | UNIQUE (con exception_date) |
| `exception_date` | date | Data specifica dell'eccezione | INDEX |
| `is_running` | bool | `true` se il servizio è attivo (corsa extra), `false` se cancellato | - |
| `reason` | string | Motivo dell'eccezione (es. "Sciopero", "Manutenzione") | - |
| `created_at` | datetime | Timestamp di creazione | - |
| `updated_at` | datetime | Timestamp ultimo aggiornamento | - |

### `trips`
**Scopo**: Istanza specifica di un `train_service` in una data particolare. È il viaggio concreto che i passeggeri possono prenotare.

| Campo | Tipo | Descrizione | Indice |
|-------|------|-------------|-------|
| `id` | string | Identificativo univoco del viaggio | PK |
| `train_service_id` | string | Riferimento al servizio template | UNIQUE (con service_date) |
| `service_date` | date | Data specifica del viaggio | INDEX (con status, delay_minutes) |
| `planned_departure_time` | datetime | Orario previsto partenza origine | INDEX (con status) |
| `planned_arrival_time` | datetime | Orario previsto arrivo destinazione | - |
| `status` | trip_status | `SCHEDULED`, `RUNNING`, `COMPLETED`, `CANCELED` | INDEX (con service_date, planned_departure_time) |
| `delay_minutes` | integer | Ritardo accumulato in minuti | - |
| `created_at` | datetime | Timestamp di creazione | - |
| `updated_at` | datetime | Timestamp ultimo aggiornamento | - |

### `trip_station_updates`
**Scopo**: Tracking real-time dello stato del treno in ogni stazione per tabelloni e app.

| Campo | Tipo | Descrizione | Indice |
|-------|------|-------------|-------|
| `id` | string | Identificativo univoco aggiornamento | PK |
| `trip_id` | string | Riferimento al trip | UNIQUE (con route_station_id), INDEX (con updated_at) |
| `route_station_id` | string | Riferimento alla fermata specifica | UNIQUE (con trip_id) |
| `planned_arrival` | datetime | Arrivo pianificato | - |
| `planned_departure` | datetime | Partenza pianificata | - |
| `actual_arrival` | datetime | Arrivo effettivo | - |
| `actual_departure` | datetime | Partenza effettiva | - |
| `delay_minutes` | integer | Ritardo in questa stazione specifica | INDEX (con updated_at) |
| `platform_change` | string | Eventuale cambio binario | - |
| `updated_at` | datetime | Timestamp aggiornamento real-time | INDEX |
| `created_at` | datetime | Timestamp di creazione | - |

### `bookings`
**Scopo**: Container principale per ogni prenotazione, che sia un viaggio diretto o con cambi.

| Campo | Tipo | Descrizione | Indice |
|-------|------|-------------|-------|
| `id` | string | Identificativo univoco prenotazione | PK |
| `booking_reference` | string | Codice alfanumerico per il cliente (PNR) | UNIQUE |
| `user_id` | string | Riferimento utente (NULL per vendite anonime) | INDEX (con created_at) |
| `passenger_id` | string | Riferimento passeggero principale | INDEX |
| `origin_station_id` | string | Stazione partenza complessiva | INDEX (con destination_station_id) |
| `destination_station_id` | string | Stazione arrivo finale | INDEX (con origin_station_id) |
| `departure_date` | date | Data partenza | INDEX (con status) |
| `total_amount` | decimal | Importo totale prenotazione | - |
| `currency` | currency_code | Valuta (EUR, CHF, etc.) | - |
| `status` | booking_status | `PENDING`, `CONFIRMED`, `CANCELED` | INDEX (con created_at) |
| `created_at` | datetime | Timestamp creazione | - |
| `updated_at` | datetime | Timestamp ultimo aggiornamento | - |

### `booking_segments`
**Scopo**: Cuore del sistema. Ogni `segment` rappresenta una tratta su un singolo treno. Un viaggio con cambi avrà più segmenti.

**Nota di implementazione**: Questa è stata la tabella più difficile da progettare. Ho dovuto bilanciare flessibilità e performance, gestendo sia viaggi semplici che complessi con la stessa struttura. L'uso di `sequence` permette di ricostruire l'ordine dei segmenti, mentre i riferimenti alle `route_stations` permettono di calcolare con precisione gli orari.

| Campo | Tipo | Descrizione | Indice |
|-------|------|-------------|-------|
| `id` | string | Identificativo univoco segment | PK |
| `booking_id` | string | Riferimento alla prenotazione | UNIQUE (con sequence), INDEX |
| `trip_id` | string | Riferimento al viaggio specifico | INDEX |
| `sequence` | integer | Ordine progressivo (1 per diretti, 1,2... per cambi) | UNIQUE (con booking_id) |
| `origin_station_id` | string | Stazione partenza segment | FK |
| `destination_station_id` | string | Stazione arrivo segment | FK |
| `origin_route_station_id` | string | Punto partenza nella route | FK |
| `destination_route_station_id` | string | Punto arrivo nella route | FK |
| `planned_departure_time` | datetime | Orario partenza pianificato | INDEX |
| `planned_arrival_time` | datetime | Orario arrivo pianificato | - |
| `connection_time_minutes` | integer | Tempo cambio treno (NULL per ultimo segment) | - |
| `platform_departure` | string | Binario partenza | - |
| `platform_arrival` | string | Binario arrivo | - |
| `distance_km` | decimal | Distanza specifica segment | - |
| `segment_amount` | decimal | Costo segment (somma = total_amount) | - |
| `created_at` | datetime | Timestamp creazione | - |
| `updated_at` | datetime | Timestamp ultimo aggiornamento | - |

### `fares`
**Scopo**: Struttura tariffaria flessibile basata su regole (distanza, rotta, operatore, etc.).

| Campo | Tipo | Descrizione | Indice |
|-------|------|-------------|-------|
| `id` | string | Identificativo univoco tariffa | PK |
| `route_id` | string | Route specifica (NULL per tariffe generiche) | INDEX (con operator_id, wagon_category_id, service_type_id) |
| `operator_id` | string | Operatore specifico (NULL per tariffe generiche) | INDEX (con origin_country_id, destination_country_id) |
| `origin_country_id` | string | Paese di origine | FK |
| `destination_country_id` | string | Paese di destinazione | FK |
| `wagon_category_id` | string | Categoria servizio | FK |
| `service_type_id` | string | Tipo di servizio (AV, REG) | INDEX |
| `distance_min_km` | integer | Scaglione chilometrico minimo | - |
| `distance_max_km` | integer | Scaglione chilometrico massimo | - |
| `base_fare` | decimal | Tariffa base fissa | - |
| `fare_per_km` | decimal | Tariffa variabile per chilometro | - |
| `is_cross_border` | bool | `true` se la tariffa è per viaggi internazionali | - |
| `international_supplement` | decimal | Supplemento per viaggi internazionali | - |
| `currency` | currency_code | Valuta tariffa | - |
| `valid_from` | datetime | Inizio validità | INDEX (con valid_to) |
| `valid_to` | datetime | Fine validità | INDEX (con valid_from) |
| `created_at` | datetime | Timestamp creazione | - |
| `updated_at` | datetime | Timestamp ultimo aggiornamento | - |

### `seat_reservations`
**Scopo**: Gestisce la prenotazione di un posto/letto specifico per un segmento di viaggio.

| Campo | Tipo | Descrizione | Indice |
|-------|------|-------------|-------|
| `id` | string | Identificativo univoco prenotazione posto | PK |
| `booking_segment_id` | string | Riferimento al segment | UNIQUE |
| `trip_id` | string | Riferimento al trip | INDEX (con wagon_seat_id, expires_at) |
| `wagon_seat_id` | string | Riferimento posto fisico (NULL se non c'è posto assegnato) | INDEX (con trip_id) |
| `passenger_id` | string | Riferimento passeggero | INDEX |
| `origin_route_station_id` | string | Inizio occupazione posto | FK |
| `destination_route_station_id` | string | Fine occupazione posto | FK |
| `expires_at` | datetime | Scadenza prenotazione temporanea (carrello) | INDEX |
| `created_at` | datetime | Timestamp creazione | - |
| `updated_at` | datetime | Timestamp ultimo aggiornamento | - |

### `tickets`
**Scopo**: Biglietto finale emesso per ogni passeggero per ogni segmento di viaggio.

| Campo | Tipo | Descrizione | Indice |
|-------|------|-------------|-------|
| `id` | string | Identificativo univoco biglietto | PK |
| `ticket_number` | string | Numero biglietto univoco per il controllo | UNIQUE |
| `booking_id` | string | Riferimento prenotazione | INDEX |
| `booking_segment_id` | string | Riferimento segment specifico | UNIQUE |
| `passenger_id` | string | Riferimento passeggero | INDEX (con service_date) |
| `trip_id` | string | Riferimento trip | INDEX (con service_date) |
| `origin_station_id` | string | Stazione partenza | - |
| `destination_station_id` | string | Stazione arrivo | - |
| `wagon_category_id` | string | Categoria vagone | FK |
| `seat_reservation_id` | string | Riferimento posto (se prenotato) | FK |
| `fare_amount` | decimal | Tariffa biglietto | - |
| `currency` | currency_code | Valuta biglietto | - |
| `status` | ticket_status | `VALID`, `USED`, `CANCELED` | INDEX (con service_date) |
| `issued_at` | datetime | Data emissione | - |
| `service_date` | date | Data viaggio | INDEX |
| `created_at` | datetime | Timestamp creazione | - |
| `updated_at` | datetime | Timestamp ultimo aggiornamento | - |

### `payments`
**Scopo**: Gestione delle transazioni finanziarie per le prenotazioni.

| Campo | Tipo | Descrizione | Indice |
|-------|------|-------------|-------|
| `id` | string | Identificativo univoco pagamento | PK |
| `booking_id` | string | Riferimento prenotazione | INDEX |
| `amount` | decimal | Importo pagamento | - |
| `currency` | currency_code | Valuta transazione | - |
| `payment_method` | payment_method | Metodo (carta, PayPal, etc.) | - |
| `status` | payment_status | `PENDING`, `COMPLETED`, `FAILED` | INDEX |
| `transaction_ref` | string | Riferimento gateway di pagamento esterno | - |
| `paid_at` | datetime | Timestamp completamento pagamento | - |
| `created_at` | datetime | Timestamp creazione | - |
| `updated_at` | datetime | Timestamp ultimo aggiornamento | - |
