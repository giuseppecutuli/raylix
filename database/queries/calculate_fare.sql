-- ========================================
-- Calcolo Tariffe Dinamico per Tratte Specifiche
-- Trova la tariffa migliore per una tratta specifica di un viaggio usando un sistema di priorità.
-- Include la gestione dei supplementi per viaggi internazionali.
-- La query può calcolare tariffe sia per viaggi completi che per tratte intermedie
-- (es. Firenze-Napoli in un viaggio Roma-Messina).
-- I parametri di input sono:
-- - trip_id: ID del viaggio
-- - origin_station_id: ID stazione di partenza della tratta desiderata
-- - destination_station_id: ID stazione di arrivo della tratta desiderata
-- ========================================

WITH segment_details AS (
    -- ===================================================================
    -- Calcola i dettagli della tratta specifica richiesta
    -- Verifica che le stazioni siano sulla rotta e calcola la distanza
    -- Include controllo se è un viaggio internazionale
    -- ===================================================================
    SELECT 
        t.id AS trip_id,
        t.service_date,
        t.train_service_id,
        ts.route_id,
        ts.operator_id,
        ts.service_type_id,
        rs_from.station_id AS origin_station_id,
        rs_to.station_id AS destination_station_id,
        
        -- Calcola distanza approssimativa basata sulla differenza di sequenza
        -- Supponiamo 25 km per ogni step di sequenza, solo a scopo di esempio, dovrà essere sostituito con dati reali
        -- utilizzando dati geografici reali per calcolare la distanza effettiva
        (rs_to.sequence - rs_from.sequence) * 25 AS estimated_distance_km,
        
        -- Controllo se è viaggio internazionale
        CASE 
            WHEN origin_city.country_id != dest_city.country_id THEN true 
            ELSE false 
        END AS is_international,
        
        origin_city.country_id AS origin_country_id,
        dest_city.country_id AS destination_country_id,
        
        rs_from.sequence AS origin_sequence,
        rs_to.sequence AS destination_sequence
        
    FROM trips t
    JOIN train_services ts ON t.train_service_id = ts.id
    JOIN route_stations rs_from ON rs_from.route_id = ts.route_id
    JOIN route_stations rs_to ON rs_to.route_id = ts.route_id
    JOIN stations origin_station ON rs_from.station_id = origin_station.id
    JOIN stations dest_station ON rs_to.station_id = dest_station.id
    JOIN cities origin_city ON origin_station.city_id = origin_city.id
    JOIN cities dest_city ON dest_station.city_id = dest_city.id
    
    WHERE 
        t.id = '60f9ce37-8084-454a-9045-661f43f21bdb' -- Parametro: ID del viaggio
        AND rs_from.station_id = 'fcd785f6-0d6d-4978-9c3e-48871240ea80' -- Parametro: ID stazione di partenza (Firenze)
        AND rs_to.station_id = '6797b5e8-71c6-4aa7-8fe4-20bf54cc91e8'    -- Parametro: ID stazione di arrivo (Roma)
        AND rs_from.sequence < rs_to.sequence       -- Assicura direzione corretta
),

available_fares AS (
    -- ===================================================================
    -- Trova tutte le tariffe applicabili alla tratta richiesta
    -- Filtra per validità temporale, range di distanza e compatibilità internazionale
    -- ===================================================================
    SELECT 
        f.*,
        sd.estimated_distance_km,
        sd.is_international,
        -- Sistema a punti: regole più specifiche = punteggio più alto
        (CASE WHEN f.route_id IS NOT NULL THEN 40 ELSE 0 END) +
        (CASE WHEN f.operator_id IS NOT NULL THEN 30 ELSE 0 END) +
        (CASE WHEN f.service_type_id IS NOT NULL THEN 20 ELSE 0 END) +
        (CASE WHEN f.wagon_category_id IS NOT NULL THEN 10 ELSE 0 END) +
        (CASE WHEN f.origin_country_id IS NOT NULL AND f.destination_country_id IS NOT NULL THEN 15 ELSE 0 END)
        AS priority_score
        
    FROM fares f
    CROSS JOIN segment_details sd
    
    WHERE 
        -- La tariffa deve essere valida per la data del viaggio
        f.valid_from <= sd.service_date AND f.valid_to >= sd.service_date
        -- Compatibilità con operatore (se specificato nella tariffa)
        AND (f.operator_id IS NULL OR f.operator_id = sd.operator_id)
        -- Compatibilità con rotta (se specificata nella tariffa)  
        AND (f.route_id IS NULL OR f.route_id = sd.route_id)
        -- Compatibilità con tipo servizio (se specificato nella tariffa)
        AND (f.service_type_id IS NULL OR f.service_type_id = sd.service_type_id)
        -- Compatibilità paesi (se specificati nella tariffa)
        AND (f.origin_country_id IS NULL OR f.origin_country_id = sd.origin_country_id)
        AND (f.destination_country_id IS NULL OR f.destination_country_id = sd.destination_country_id)
        -- La distanza della tratta deve rientrare nel range della tariffa
        AND sd.estimated_distance_km BETWEEN f.distance_min_km AND f.distance_max_km
        -- Esclude tariffe cross-border se il viaggio non è internazionale
        AND (NOT f.is_cross_border OR sd.is_international)
),

best_fare AS (
    -- ===================================================================
    -- Seleziona la tariffa con il punteggio più alto
    -- In caso di parità, preferisce la tariffa con prezzo base più basso
    -- ===================================================================
    SELECT *
    FROM available_fares
    ORDER BY 
        priority_score DESC,
        base_fare ASC
    LIMIT 1
)

SELECT 
    -- Dettagli del viaggio
    t.id AS trip_id,
    t.service_date,
    ts.service_name,
    ro.name AS operator,
    st.name AS service_type,
    
    -- Stazioni della tratta specifica richiesta
    origin.name AS origin_station,
    destination.name AS destination_station,
    origin_country.name AS origin_country,
    dest_country.name AS destination_country,
    
    -- Controllo internazionale
    sd.is_international,
    
    -- Dettagli orari della tratta
    tsu_from.planned_departure AS departure_time,
    tsu_to.planned_arrival AS arrival_time,
    
    -- Calcolo del prezzo per la tratta specifica
    bf.base_fare,
    bf.fare_per_km,
    sd.estimated_distance_km AS segment_distance_km,
    
    -- Componenti del prezzo
    bf.base_fare AS base_component,
    (bf.fare_per_km * sd.estimated_distance_km) AS distance_component,
    CASE 
        WHEN sd.is_international AND bf.is_cross_border 
        THEN COALESCE(bf.international_supplement, 0)
        ELSE 0 
    END AS international_component,
    
    -- Prezzo totale = tariffa base + (tariffa per km * distanza) + supplemento internazionale
    bf.base_fare + 
    (bf.fare_per_km * sd.estimated_distance_km) +
    CASE 
        WHEN sd.is_international AND bf.is_cross_border 
        THEN COALESCE(bf.international_supplement, 0)
        ELSE 0 
    END AS total_price,
    
    bf.currency,
    
    -- Tipo di tariffa applicata (per trasparenza)
    CASE 
        WHEN bf.route_id IS NOT NULL THEN 'Tariffa specifica rotta'
        WHEN bf.operator_id IS NOT NULL THEN 'Tariffa operatore'
        WHEN bf.origin_country_id IS NOT NULL THEN 'Tariffa paesi specifici'
        WHEN bf.service_type_id IS NOT NULL THEN 'Tariffa tipo servizio'
        ELSE 'Tariffa generale'
    END AS fare_type,
    
    bf.priority_score,
    bf.is_cross_border

FROM segment_details sd
JOIN trips t ON t.id = sd.trip_id
JOIN train_services ts ON t.train_service_id = ts.id
JOIN railway_operators ro ON ts.operator_id = ro.id  
JOIN service_types st ON ts.service_type_id = st.id

-- Join per ottenere le stazioni specifiche della tratta
JOIN stations origin ON sd.origin_station_id = origin.id
JOIN stations destination ON sd.destination_station_id = destination.id
JOIN cities origin_city ON origin.city_id = origin_city.id
JOIN cities dest_city ON destination.city_id = dest_city.id
JOIN countries origin_country ON origin_city.country_id = origin_country.id
JOIN countries dest_country ON dest_city.country_id = dest_country.id

-- Join per ottenere gli orari specifici della tratta
JOIN route_stations rs_from ON rs_from.route_id = ts.route_id 
    AND rs_from.station_id = sd.origin_station_id
JOIN route_stations rs_to ON rs_to.route_id = ts.route_id 
    AND rs_to.station_id = sd.destination_station_id
JOIN trip_station_updates tsu_from ON tsu_from.trip_id = t.id 
    AND tsu_from.route_station_id = rs_from.id
JOIN trip_station_updates tsu_to ON tsu_to.trip_id = t.id 
    AND tsu_to.route_station_id = rs_to.id

-- Join con la tariffa migliore
CROSS JOIN best_fare bf;
