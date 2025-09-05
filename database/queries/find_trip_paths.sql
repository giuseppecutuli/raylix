--- ========================================
 -- Query per la ricerca di itinerari di viaggio con cambi.
 -- Utilizza una CTE ricorsiva per costruire percorsi passo dopo passo,
 -- partendo da una stazione di origine e cercando connessioni successive
 -- fino a raggiungere la destinazione finale.
 -- La query in teoria permette un numero illimitato di cambi, ma per motivi
 -- di performance e praticità, si limita a un massimo di 3 segmenti (2 cambio). 
-- ========================================

WITH RECURSIVE trip_paths AS (
    -- ===================================================================
    -- ANCHOR MEMBER: Trova tutti i segmenti di viaggio iniziali (diretti)
    -- che partono dalla stazione di origine. Questi sono i punti di
    -- partenza per la costruzione ricorsiva degli itinerari.
    -- ===================================================================
    SELECT
        -- Dati per il tracciamento del percorso
        ARRAY[t.id] AS trip_ids,
        ARRAY[rs_to.station_id] AS visited_station_ids, -- Array di ID stazioni per evitare cicli
        rs_to.station_id AS last_station_id,            -- Ultima stazione raggiunta nel percorso
        tsu_to.planned_arrival AS last_arrival_time,    -- Orario di arrivo all'ultima stazione
        0 AS changes,                                   -- Contatore dei cambi, 0 per i diretti

        -- Dettagli dei segmenti che compongono l'itinerario
        ARRAY[st_from.name] AS segment_origins,
        ARRAY[st_to.name] AS segment_destinations,
        ARRAY[tsu_from.planned_departure] AS segment_departures,
        ARRAY[tsu_to.planned_arrival] AS segment_arrivals,
        ARRAY[ro.name] AS segment_operators,
        ARRAY[stype.name] AS segment_service_types

    FROM trips t
    JOIN train_services ts ON t.train_service_id = ts.id
    JOIN railway_operators ro ON ts.operator_id = ro.id
    JOIN service_types stype ON ts.service_type_id = stype.id
    JOIN route_stations rs_from ON ts.route_id = rs_from.route_id
    JOIN route_stations rs_to ON ts.route_id = rs_to.route_id AND rs_from.sequence < rs_to.sequence
    JOIN stations st_from ON rs_from.station_id = st_from.id
    JOIN stations st_to ON rs_to.station_id = st_to.id
    JOIN trip_station_updates tsu_from ON tsu_from.trip_id = t.id AND tsu_from.route_station_id = rs_from.id
    JOIN trip_station_updates tsu_to ON tsu_to.trip_id = t.id AND tsu_to.route_station_id = rs_to.id
    WHERE
        rs_from.station_id = 'e4cb671d-12ce-47c7-be03-8f94cb2ffb6c' -- Parametro: ID Stazione di Origine (Milano)
        AND t.service_date = '2025-09-03' -- Parametro: Data del viaggio
        AND t.status IN ('SCHEDULED', 'RUNNING')

    UNION ALL

    -- ===================================================================
    -- RECURSIVE MEMBER: Estende i percorsi trovati fino ad ora.
    -- Per ogni percorso esistente (tp), cerca un nuovo viaggio (next_trip)
    -- che parte dall'ultima stazione raggiunta.
    -- ===================================================================
    SELECT
        -- Estensione dei dati di tracciamento con il nuovo segmento
        tp.trip_ids || next_trip.id,
        tp.visited_station_ids || next_rs_to.station_id,
        next_rs_to.station_id,
        next_tsu_to.planned_arrival,
        tp.changes + 1,

        -- Estensione dei dettagli dei segmenti con il nuovo viaggio
        tp.segment_origins || next_st_from.name,
        tp.segment_destinations || next_st_to.name,
        tp.segment_departures || next_tsu_from.planned_departure,
        tp.segment_arrivals || next_tsu_to.planned_arrival,
        tp.segment_operators || next_ro.name,
        tp.segment_service_types || next_stype.name

    FROM trip_paths tp
    -- Join per trovare il segmento di viaggio successivo
    JOIN trips next_trip ON next_trip.service_date = '2025-09-03' AND next_trip.status IN ('SCHEDULED', 'RUNNING')
    JOIN train_services next_ts ON next_trip.train_service_id = next_ts.id
    JOIN railway_operators next_ro ON next_ts.operator_id = next_ro.id
    JOIN service_types next_stype ON next_ts.service_type_id = next_stype.id
    JOIN route_stations next_rs_from ON next_ts.route_id = next_rs_from.route_id
    JOIN route_stations next_rs_to ON next_ts.route_id = next_rs_to.route_id AND next_rs_from.sequence < next_rs_to.sequence
    JOIN stations next_st_from ON next_rs_from.station_id = next_st_from.id
    JOIN stations next_st_to ON next_rs_to.station_id = next_st_to.id
    JOIN trip_station_updates next_tsu_from ON next_tsu_from.trip_id = next_trip.id AND next_tsu_from.route_station_id = next_rs_from.id
    JOIN trip_station_updates next_tsu_to ON next_tsu_to.trip_id = next_trip.id AND next_tsu_to.route_station_id = next_rs_to.id
    WHERE
        -- Vincolo di connessione: la nuova partenza deve avvenire dalla stazione di arrivo precedente.
        next_rs_from.station_id = tp.last_station_id
        -- Vincolo temporale: garantisce un tempo minimo per il cambio (es. 20 minuti).
        AND next_tsu_from.planned_departure > tp.last_arrival_time + INTERVAL '20 minutes'

        -- Vincoli di terminazione e ottimizzazione della ricerca
        -- Limita il numero massimo di cambi (in questo caso, max 2 cambio, quindi 3 segmenti).
        AND tp.changes <= 2 
        -- Evita i cicli: non visitare una stazione in cui si è già passati.
        AND NOT (next_rs_to.station_id = ANY(tp.visited_station_ids))
        -- Limita la finestra di ricerca per le partenze (es. entro 6 ore dalla partenza originale).
        AND next_tsu_from.planned_departure < tp.segment_departures[1] + INTERVAL '6 hours'
)
-- ===================================================================
-- SELEZIONE FINALE: Filtra e ordina i risultati
-- Dalla lista completa di tutti i percorsi generati, seleziona solo
-- quelli che terminano alla destinazione finale desiderata.
-- ===================================================================
SELECT
    trip_ids,
    segment_origins,
    segment_destinations,
    segment_departures,
    segment_arrivals,
    segment_operators,
    segment_service_types,
    changes,
    ARRAY_LENGTH(trip_ids, 1) AS segments
FROM trip_paths
WHERE
    last_station_id = '86eebb20-e1a1-4169-8415-2b8a70638b14' -- Parametro: ID Stazione di Destinazione (Messina)
ORDER BY
    segment_departures[1] ASC, -- Ordina per orario di partenza del primo treno
    changes ASC,               -- A parità di partenza, preferisce meno cambi
    segment_arrivals[array_length(segment_arrivals, 1)] ASC -- A parità, preferisce chi arriva prima
-- Limita il numero di risultati restituiti
LIMIT 50;
