# Analisi delle Forme Normali

Il database Raylix applica le regole di normalizzazione per garantire consistenza dei dati e ridurre la ridondanza. Questo documento analizza come il database rispetta le prime tre forme normali e spiega dove ho scelto di denormalizzare per migliorare le performance.

## Prima Forma Normale (1NF)

Il database rispetta completamente la 1NF. Tutti i campi contengono valori atomici e non ci sono gruppi ripetuti.

### Come ho gestito le relazioni complesse

Invece di creare campi multipli, ho usato tabelle di collegamento:

- **`train_wagons`**: Collega treni e vagoni con la posizione
- **`route_stations`**: Gestisce la sequenza delle fermate nelle rotte
- **`booking_segments`**: Spezza i viaggi complessi in parti semplici

### Il campo JSON in `train_services`

Il campo `operates_days` usa JSONB per i giorni di servizio:

```json
"operates_days": {
  "monday": true,
  "tuesday": true,
  "wednesday": true,
  "thursday": true,
  "friday": true,
  "saturday": false,
  "sunday": false
}
```

Anche se contiene struttura interna, PostgreSQL lo tratta come valore atomico, quindi rispetta la 1NF.

## Seconda Forma Normale (2NF)

Ho eliminato tutte le dipendenze parziali separando le informazioni che dipendevano solo da parte della chiave primaria.

### Esempi principali

**Tabella `wagon_seats`** con chiave `(wagon_id, seat_number)`:
- `seat_type` → dipende dal posto specifico nel vagone
- `row_number` → dipende dalla posizione fisica del posto  
- `is_accessible` → caratteristica del singolo posto

**Tabella `route_stations`** con chiave `(route_id, sequence)`:
- `arrival_offset_min` → dipende dalla fermata specifica nella rotta
- `platform` → binario per quella fermata in quella rotta

### Separazioni importanti

Ho separato entità che potevano sembrare unite:
- **Users vs Passengers**: Un utente può prenotare per altri
- **Services vs Trips**: I servizi sono template, i viaggi sono istanze con date
- **Stations vs Cities**: Le stazioni hanno coordinate precise diverse dalle città

## Terza Forma Normale (3NF)

Ho eliminato le dipendenze transitive dove un campo dipendeva da un altro campo non-chiave.

### Struttura geografica corretta

```sql
stations.city_id → cities.country_id → countries.name
```

Ho evitato di mettere `country_name` direttamente in `stations` perché sarebbe stata una dipendenza transitiva attraverso `city_id`.

### Gestione operatori e tariffe

```sql
train_services.operator_id → railway_operators.country_id
fares.operator_id → railway_operators.country_id
```

Le informazioni sull'operatore sono centralizzate nella tabella `railway_operators` invece di essere duplicate.

## Denormalizzazioni per Performance

In alcuni casi ho violato la 3NF per motivi di performance. Ecco dove e perché.

### Prezzo del segmento (`segment_amount`)

**Problema**: Calcolare il prezzo ogni volta richiederebbe questa query complessa:

```sql
SELECT bs.id,
       (f.base_fare + f.fare_per_km * bs.distance_km + 
        CASE WHEN f.is_cross_border THEN f.international_supplement ELSE 0 END)
FROM booking_segments bs
JOIN trips t ON bs.trip_id = t.id
JOIN train_services ts ON t.train_service_id = ts.id
JOIN fares f ON ts.operator_id = f.operator_id 
-- ... altri join per categoria vagone, tipo servizio
```

**Soluzione**: Ho salvato `segment_amount` direttamente nella prenotazione.

**Vantaggi**:
- I report finanziari sono immediati
- Il prezzo pagato resta fisso anche se le tariffe cambiano
- Niente calcoli complessi per ogni fattura

### Orari in `booking_segments`

**Problema**: Per mostrare gli orari di partenza e arrivo servivano 4 join ogni volta:

```sql
-- Query semplice con denormalizzazione:
SELECT planned_departure_time, planned_arrival_time 
FROM booking_segments 
WHERE booking_id = $1;

-- Query complessa senza denormalizzazione:
SELECT t.planned_departure_time + rs_origin.departure_offset_min * interval '1 minute',
       t.planned_departure_time + rs_dest.arrival_offset_min * interval '1 minute'  
FROM booking_segments bs
JOIN trips t ON bs.trip_id = t.id
JOIN route_stations rs_origin ON bs.origin_route_station_id = rs_origin.id
JOIN route_stations rs_dest ON bs.destination_route_station_id = rs_dest.id;
```

**Vantaggi**:
- Meno carico sul database per query frequenti
- Notifiche in tempo reale senza rallentamenti
