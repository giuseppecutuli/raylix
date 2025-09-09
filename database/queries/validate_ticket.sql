-- ========================================
-- Verifica Validità Biglietto
-- Controlla se un ticket è valido per una specifica data/tratta.
-- Include controlli su: stato biglietto, date viaggio, tratte coperte,
-- stato prenotazione e scadenza posto.
-- Usato per validazione QR code e controlli a bordo.
-- I parametri di input sono:
-- - ticket_number: Numero biglietto da validare
-- - current_station_id: Stazione dove avviene il controllo
-- ========================================

SELECT 
    -- Informazioni biglietto e prenotazione
    t.id AS ticket_id,
    t.ticket_number,
    t.status AS ticket_status,
    t.service_date,
    b.status AS booking_status,
    b.booking_reference,

    -- Dettagli passeggero
    p.first_name,
    p.last_name,
    p.document_number,

    -- Tratta del biglietto
    st_origin.name AS origin_station,
    st_dest.name AS destination_station,

    -- ===================================================================
    -- VALIDAZIONE: Determina se il biglietto è valido
    -- ===================================================================
    CASE 
        WHEN t.status NOT IN ('VALID', 'USED') THEN 'INVALID_STATUS'
        WHEN b.status != 'CONFIRMED' THEN 'BOOKING_NOT_CONFIRMED'
        WHEN tr.status = 'CANCELED' THEN 'TRIP_CANCELED'
        WHEN t.service_date != CURRENT_DATE THEN 'WRONG_DATE'
        WHEN sr.expires_at IS NOT NULL AND sr.expires_at < NOW() THEN 'SEAT_EXPIRED'
        WHEN NOT EXISTS (
            SELECT 1 
            FROM route_stations rs_check
            WHERE rs_check.station_id = '86eebb20-e1a1-4169-8415-2b8a70638b14' -- Parametro: station_id (la stazione dove avviene il controllo)
                AND rs_check.route_id = rs_origin.route_id
                AND rs_check.sequence BETWEEN rs_origin.sequence AND rs_dest.sequence
        ) THEN 'STATION_NOT_COVERED'
        ELSE 'VALID'
    END AS validation_result,
    
    -- Posto assegnato (se presente)
    ws.seat_number,
    ws.seat_type,
    wc.name AS wagon_category,
    sr.expires_at AS seat_expires_at

FROM tickets t
JOIN bookings b ON t.booking_id = b.id
JOIN passengers p ON t.passenger_id = p.id
JOIN booking_segments bs ON t.booking_segment_id = bs.id
JOIN trips tr ON t.trip_id = tr.id
JOIN train_services ts ON tr.train_service_id = ts.id
JOIN railway_operators ro ON ts.operator_id = ro.id

JOIN stations st_origin ON t.origin_station_id = st_origin.id
JOIN stations st_dest ON t.destination_station_id = st_dest.id

-- Route stations per controllo tratta
JOIN route_stations rs_origin ON bs.origin_route_station_id = rs_origin.id
JOIN route_stations rs_dest ON bs.destination_route_station_id = rs_dest.id

-- Join per posto e categoria
LEFT JOIN seat_reservations sr ON t.seat_reservation_id = sr.id
LEFT JOIN wagon_seats ws ON sr.wagon_seat_id = ws.id
LEFT JOIN wagons w ON ws.wagon_id = w.id
LEFT JOIN wagon_categories wc ON w.category_id = wc.id

-- Parametro: ticket_number (il numero del biglietto da validare)
WHERE t.ticket_number = 'TK698342301'; 
