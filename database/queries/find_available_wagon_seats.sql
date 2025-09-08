-- ========================================
-- Trova tutti i posti disponibili di un vagone per una tratta specifica
-- Controlla sovrapposizioni con altre prenotazioni (viaggi misti)
-- Un posto è occupato se esiste una prenotazione che si sovrappone alla tratta richiesta
-- I parametri di input sono:
-- - trip_id: ID del viaggio
-- - origin_route_station_id: ID della route_station di partenza
-- - destination_route_station_id: ID della route_station di arrivo  
-- - wagon_id: ID del vagone specifico
-- ========================================


WITH seat_occupancy AS (
    -- ===================================================================
    -- Identifica tutti i posti occupati per la tratta richiesta
    -- Controlla sovrapposizioni di sequenza tra prenotazioni esistenti
    -- e la tratta che si vuole prenotare
    -- ===================================================================
    SELECT DISTINCT
        sr.wagon_seat_id
    FROM seat_reservations sr
    JOIN wagon_seats ws ON sr.wagon_seat_id = ws.id
    JOIN route_stations rs_existing_origin ON sr.origin_route_station_id = rs_existing_origin.id
    JOIN route_stations rs_existing_dest ON sr.destination_route_station_id = rs_existing_dest.id
    JOIN route_stations rs_requested_origin ON rs_requested_origin.id = 'fcd785f6-0d6d-4978-9c3e-48871240ea80' -- Parametro: origin_route_station_id (Firenze)
    JOIN route_stations rs_requested_dest ON rs_requested_dest.id = '6797b5e8-71c6-4aa7-8fe4-20bf54cc91e8'     -- Parametro: destination_route_station_id (Roma)
    WHERE 
        sr.trip_id = '60f9ce37-8084-454a-9045-661f43f21bdb' -- Parametro: trip_id
        AND ws.wagon_id = '37d43818-76e2-4842-8c0c-46ba989d7981' -- Parametro: wagon_id
        AND sr.expires_at > NOW()    -- Prenotazione ancora valida
        -- Verifica sovrapposizione delle sequenze
        AND (
            -- Caso 1: La prenotazione esistente inizia prima/durante la nostra richiesta 
            -- e finisce dopo l'inizio della nostra richiesta
            (rs_existing_origin.sequence <= rs_requested_origin.sequence 
             AND rs_existing_dest.sequence > rs_requested_origin.sequence)
            OR
            -- Caso 2: La prenotazione esistente inizia prima della fine della nostra richiesta 
            -- e finisce durante/dopo la nostra richiesta
            (rs_existing_origin.sequence < rs_requested_dest.sequence 
             AND rs_existing_dest.sequence >= rs_requested_dest.sequence)
            OR
            -- Caso 3: La prenotazione esistente è completamente contenuta nella nostra richiesta
            (rs_existing_origin.sequence >= rs_requested_origin.sequence 
             AND rs_existing_dest.sequence <= rs_requested_dest.sequence)
        )
)

SELECT 
    -- Dettagli del posto
    ws.id AS seat_id,
    ws.seat_number,
    ws.seat_type,
    ws.seat_orientation,
    ws.row_number,
    ws.column_letter,
    ws.is_accessible,
    
    -- Dettagli cabina
    c.cabin_number,
    c.cabin_type,
    
    -- Stato di disponibilità
    CASE 
        WHEN so.wagon_seat_id IS NOT NULL THEN 'OCCUPIED'
        ELSE 'AVAILABLE'
    END AS seat_status

FROM wagon_seats ws
LEFT JOIN cabins c ON ws.cabin_id = c.id
LEFT JOIN seat_occupancy so ON ws.id = so.wagon_seat_id
WHERE 
    ws.wagon_id = '8281148b-681a-47c5-b994-958edff4cb6a' -- Parametro: wagon_id
ORDER BY 
    ws.row_number ASC, 
    ws.column_letter ASC,
    ws.seat_number ASC;