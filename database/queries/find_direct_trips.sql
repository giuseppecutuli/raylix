-- ========================================
-- Trova tutti i viaggi disponibili tra due stazioni (anche intermedie) in una data
-- Il join su route_stations permette di selezionare sia viaggi completi che tratte intermedie:
-- ad esempio puoi cercare Milano→Napoli (viaggio lungo) oppure Firenze→Roma (tratta intermedia).
-- La condizione sulla sequenza garantisce che la direzione sia corretta (partenza prima di arrivo).
-- I parametri di input sono:
-- - origin_station_id: ID della stazione di partenza
-- - destination_station_id: ID della stazione di arrivo
-- - service_date: Data del viaggio
-- ========================================

SELECT
    t.id AS trip_id,
    tsu_from.planned_departure AS departure_time,
    tsu_to.planned_arrival AS arrival_time,
    st_from.name AS origin_station,
    st_to.name AS destination_station,
    ts.service_name,
    ro.name AS operator,
    stype.name AS service_type,
    t.status
FROM trips t
JOIN train_services ts ON t.train_service_id = ts.id
JOIN railway_operators ro ON ts.operator_id = ro.id
JOIN service_types stype ON ts.service_type_id = stype.id
-- Il doppio join su route_stations permette di trovare partenza e arrivo sulla stessa rotta.
JOIN route_stations rs_from ON ts.route_id = rs_from.route_id
JOIN route_stations rs_to ON ts.route_id = rs_to.route_id
-- La condizione sulla sequenza è critica: assicura che la stazione di partenza venga prima di quella di arrivo.
    AND rs_from.sequence < rs_to.sequence
JOIN stations st_from ON rs_from.station_id = st_from.id
JOIN stations st_to ON rs_to.station_id = st_to.id
JOIN trip_station_updates tsu_from ON tsu_from.trip_id = t.id AND tsu_from.route_station_id = rs_from.id
JOIN trip_station_updates tsu_to ON tsu_to.trip_id = t.id AND tsu_to.route_station_id = rs_to.id
WHERE
    rs_from.station_id = 'fcd785f6-0d6d-4978-9c3e-48871240ea80' -- Parametro: ID Stazione di Origine (es. Firenze)
    AND rs_to.station_id = '6797b5e8-71c6-4aa7-8fe4-20bf54cc91e8'   -- Parametro: ID Stazione di Destinazione (es. Roma)
    AND t.service_date = '2025-09-03'                             -- Parametro: Data del viaggio
    AND t.status IN ('SCHEDULED', 'RUNNING')
ORDER BY
 -- Ordina i risultati per orario di partenza
    departure_time ASC;
