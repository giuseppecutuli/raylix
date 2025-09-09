-- ========================================
-- Storico Prenotazioni Cliente (Vista Lista)
-- Query ottimizzata per visualizzazione in lista dello storico.
-- Mostra solo le informazioni essenziali per l'overview.
-- I parametri di input sono:
-- - user_id: ID dell'utente di cui recuperare lo storico
-- ========================================

SELECT 
    -- Informazioni prenotazione
    b.id AS booking_id,
    b.booking_reference,
    b.status AS booking_status,
    b.departure_date,
    b.total_amount,
    b.currency,
    b.created_at AS booking_date,
    
    -- Tratta completa
    st_origin.name AS origin_station,
    st_dest.name AS destination_station,
    
    -- Date reali del viaggio completo
    bs_first.planned_departure_time AS journey_departure,
    bs_last.planned_arrival_time AS journey_arrival,
    
    -- Stato del viaggio aggregato dai trip
    CASE 
        WHEN trip_stats.canceled_count > 0 THEN 'CANCELED'
        WHEN trip_stats.completed_count = trip_stats.total_count THEN 'COMPLETED'
        WHEN trip_stats.running_count > 0 THEN 'RUNNING'
        WHEN trip_stats.delayed_count > 0 THEN 'DELAYED'
        ELSE 'SCHEDULED'
    END AS trip_status

FROM bookings b
JOIN stations st_origin ON b.origin_station_id = st_origin.id
JOIN stations st_dest ON b.destination_station_id = st_dest.id

-- Primo segmento per partenza
JOIN booking_segments bs_first ON b.id = bs_first.booking_id AND bs_first.sequence = 1
-- Ultimo segmento per arrivo
JOIN booking_segments bs_last ON b.id = bs_last.booking_id 
    AND bs_last.sequence = (
        SELECT MAX(sequence) 
        FROM booking_segments 
        WHERE booking_id = b.id
    )
JOIN trips tr_first ON bs_first.trip_id = tr_first.id
JOIN train_services ts_first ON tr_first.train_service_id = ts_first.id

-- Aggregazione stati dei trip
JOIN (
    SELECT 
        bs.booking_id,
        COUNT(*) as total_count,
        COUNT(CASE WHEN tr.status = 'CANCELED' THEN 1 END) as canceled_count,
        COUNT(CASE WHEN tr.status = 'COMPLETED' THEN 1 END) as completed_count,
        COUNT(CASE WHEN tr.status = 'RUNNING' THEN 1 END) as running_count,
        COUNT(CASE WHEN tr.status = 'DELAYED' THEN 1 END) as delayed_count
    FROM booking_segments bs
    JOIN trips tr ON bs.trip_id = tr.id
    GROUP BY bs.booking_id
) trip_stats ON b.id = trip_stats.booking_id

WHERE b.user_id = '5aebba09-33bb-4e3b-9aae-1329bff84349' -- Parametro: user_id

ORDER BY b.created_at DESC;