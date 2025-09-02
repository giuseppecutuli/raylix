import json
import uuid
import random
import os
import sys
from datetime import datetime, date, time, timedelta
from decimal import Decimal
import psycopg2
from faker import Faker

fake = Faker('it_IT')

class RaylixDataGenerator:
    def __init__(self, db_config):
        self.db_config = db_config
        self.conn = None
        self.static_data = self.load_static_data()
        
    def load_static_data(self):
        """Carica i dati statici dai file JSON"""
        data = {}
        static_files = [
            'countries', 'cities', 'stations', 'operators', 
            'service_types', 'wagon_categories', 'train_configs', 
            'routes', 'fares'
        ]
        
        for entity in static_files:
            file_path = f'static_data/{entity}.json'
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data[entity] = json.load(f)
            else:
                print(f"⚠️ Warning: File {file_path} non trovato")
                data[entity] = []
        
        return data
    
    def connect_db(self):
        """Connessione al database"""
        try:
            self.conn = psycopg2.connect(**self.db_config)
            self.conn.autocommit = True
            print("✅ Connesso al database PostgreSQL")
        except Exception as e:
            print(f"❌ Errore connessione database: {e}")
            raise
        
    def generate_uuid(self):
        return str(uuid.uuid4())
    
    def generate_unique_booking_reference(self, cursor):
        """Genera un booking reference unico verificando il database"""
        for attempt in range(10):  # Massimo 10 tentativi
            # Usa timestamp + random per massimizzare unicità
            timestamp = int(datetime.now().timestamp() * 1000) % 1000000  # Ultime 6 cifre del timestamp
            random_part = random.randint(100, 999)
            booking_reference = f"BK{timestamp}{random_part}"
            
            # Verifica se esiste già
            cursor.execute("SELECT COUNT(*) FROM bookings WHERE booking_reference = %s", (booking_reference,))
            if cursor.fetchone()[0] == 0:
                return booking_reference
        
        # Fallback se tutti i tentativi falliscono
        return f"BK{random.randint(10000000, 99999999)}"
        
    def generate_unique_ticket_number(self, cursor):
        """Genera un ticket number unico verificando il database"""
        for attempt in range(10):  # Massimo 10 tentativi
            # Usa timestamp + random per massimizzare unicità
            timestamp = int(datetime.now().timestamp() * 1000) % 1000000  # Ultime 6 cifre del timestamp
            random_part = random.randint(100, 999)
            ticket_number = f"TK{timestamp}{random_part}"
            
            # Verifica se esiste già
            cursor.execute("SELECT COUNT(*) FROM tickets WHERE ticket_number = %s", (ticket_number,))
            if cursor.fetchone()[0] == 0:
                return ticket_number
        
        # Fallback se tutti i tentativi falliscono
        return f"TK{random.randint(10000000, 99999999)}"
    
    def clear_all_data(self):
        """Cancella tutti i dati per rifare il seed"""
        print("🗑️ Cancellazione dati esistenti...")
        cursor = self.conn.cursor()
        
        # Lista tabelle in ordine di dipendenza (dal basso verso l'alto)
        tables_to_clear = [
            'payments', 'tickets', 'seat_reservations', 'fares', 
            'booking_segments', 'bookings', 'passengers', 'users', 
            'trip_station_updates', 'trips', 'service_exceptions',
            'train_services', 'route_stations', 'routes', 'wagon_seats',
            'cabins', 'train_wagons', 'wagons', 'wagon_categories', 
            'trains', 'service_types', 'railway_operators',
            'stations', 'cities', 'countries'
        ]
        
        for table in tables_to_clear:
            try:
                cursor.execute(f"TRUNCATE TABLE {table} CASCADE")
                print(f"   🗑️ {table}")
            except Exception as e:
                print(f"   ⚠️ Errore {table}: {e}")
    
    def insert_static_data(self):
        """Inserisce i dati statici nel database"""
        cursor = self.conn.cursor()
        
        # Countries
        print("📍 Inserimento countries...")
        for country in self.static_data['countries']:
            cursor.execute("""
                INSERT INTO countries (id, name, iso_code, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, (
                country['id'], country['name'], country['iso_code'],
                datetime.now(), datetime.now()
            ))
        
        # Cities
        print("🏙️ Inserimento cities...")
        for city in self.static_data['cities']:
            cursor.execute("""
                INSERT INTO cities (id, name, country_id, latitude, longitude, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, (
                city['id'], city['name'], city['country_id'],
                city['latitude'], city['longitude'],
                datetime.now(), datetime.now()
            ))
        
        # Stations
        print("🚉 Inserimento stations...")
        for station in self.static_data['stations']:
            cursor.execute("""
                INSERT INTO stations (id, name, city_id, latitude, longitude, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, (
                station['id'], station['name'], station['city_id'],
                station['latitude'], station['longitude'],
                datetime.now(), datetime.now()
            ))
    
    def generate_operators(self):
        """Genera operatori dai dati JSON"""
        print("🚂 Inserimento operatori...")
        cursor = self.conn.cursor()
        
        for op in self.static_data['operators']:
            cursor.execute("""
                INSERT INTO railway_operators (id, name, country_id, code, website, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (code) DO NOTHING
            """, (
                op['id'], op['name'], op['country_id'], 
                op['code'], op.get('website'), datetime.now(), datetime.now()
            ))
    
    def generate_service_types(self):
        """Genera tipi di servizio dai dati JSON"""
        print("🎫 Inserimento service types...")
        cursor = self.conn.cursor()
        
        for service in self.static_data['service_types']:
            cursor.execute("""
                INSERT INTO service_types (id, name, code, requires_seat_assignment, allows_standing, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (code) DO NOTHING
            """, (
                service['id'], service['name'], service['code'],
                service['requires_seat_assignment'], service['allows_standing'],
                datetime.now(), datetime.now()
            ))
    
    def generate_wagon_categories(self):
        """Genera categorie vagoni dai dati JSON"""
        print("🚃 Inserimento wagon categories...")
        cursor = self.conn.cursor()
        
        for cat in self.static_data['wagon_categories']:
            cursor.execute("""
                INSERT INTO wagon_categories (id, name, created_at, updated_at)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            """, (cat['id'], cat['name'], datetime.now(), datetime.now()))
    
    def generate_trains_and_wagons(self):
        """Genera treni e vagoni dai dati JSON"""
        print("🚄 Inserimento trains e wagons...")
        cursor = self.conn.cursor()
        
        for train_config in self.static_data['train_configs']:
            cursor.execute("""
                INSERT INTO trains (id, code, model, is_ship, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (code) DO NOTHING
            """, (
                train_config['id'], train_config['code'], train_config['model'], 
                train_config['is_ship'], datetime.now(), datetime.now()
            ))
            
            # Genera vagoni per questo treno
            self.generate_wagons_for_train(train_config['id'], train_config)
    
    def generate_wagons_for_train(self, train_id, train_config):
        """Genera vagoni specifici per configurazione treno"""
        cursor = self.conn.cursor()
        position = 1
        
        for wagon_config in train_config['wagon_configs']:
            # Usa direttamente category_id dalla configurazione
            category_id = wagon_config['category_id']
            
            wagon_id = self.generate_uuid()
            wagon_code = f"{train_id[:8]}_W{position:02d}"
            
            cursor.execute("""
                INSERT INTO wagons (id, code, category_id, total_seats, total_rows, 
                                  seats_per_row, layout_pattern, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                wagon_id, wagon_code, category_id, wagon_config['seats'], 
                wagon_config['rows'], wagon_config['seats_per_row'], 
                wagon_config.get('layout_pattern', '2+2'),
                datetime.now(), datetime.now()
            ))
            
            # Collega vagone al treno
            cursor.execute("""
                INSERT INTO train_wagons (train_id, wagon_id, position, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            """, (train_id, wagon_id, position, datetime.now(), datetime.now()))
            
            # Genera posti per questo vagone
            if wagon_config['seats'] > 0:
                self.generate_seats_for_wagon(wagon_id, wagon_config, train_config['is_ship'])
            
            position += 1
    
    def generate_seats_for_wagon(self, wagon_id, config, is_ship):
        """Genera posti per un vagone"""
        cursor = self.conn.cursor()
        
        seat_types = ['WINDOW', 'AISLE'] if not is_ship else ['WINDOW', 'AISLE', 'COUCHETTE_LOWER', 'COUCHETTE_UPPER']
        orientations = ['FORWARD', 'BACKWARD']
        
        seat_number = 1
        for row in range(1, config['rows'] + 1):
            for col_idx in range(config['seats_per_row']):
                col_letter = chr(65 + col_idx)  # A, B, C, D...
                
                seat_type = random.choice(seat_types)
                orientation = random.choice(orientations)
                
                cursor.execute("""
                    INSERT INTO wagon_seats (id, wagon_id, seat_number, seat_type, 
                                           seat_orientation, row_number, column_letter, 
                                           is_accessible, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    self.generate_uuid(), wagon_id, str(seat_number), seat_type,
                    orientation, row, col_letter, random.choice([True, False]) and seat_number % 20 == 0,
                    datetime.now(), datetime.now()
                ))
                seat_number += 1
    
    def generate_routes_and_services(self):
        """Genera rotte e servizi dai dati JSON"""
        print("🛤️ Inserimento routes e services...")
        cursor = self.conn.cursor()
        
        for route_data in self.static_data['routes']:
            cursor.execute("""
                INSERT INTO routes (id, name, description, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, (
                route_data['id'], route_data['name'], 
                route_data.get('description', f"Rotta {route_data['name']}"), 
                datetime.now(), datetime.now()
            ))
            
            # Aggiungi stazioni alla rotta
            base_time = 120 if route_data.get('is_international', False) else 90
            for seq, station_id in enumerate(route_data['stations']):
                arrival_offset = seq * base_time if seq > 0 else None
                departure_offset = arrival_offset + (10 if route_data.get('is_international', False) else 5) if arrival_offset else 0
                
                cursor.execute("""
                    INSERT INTO route_stations (id, route_id, station_id, sequence, 
                                              arrival_offset_min, departure_offset_min, 
                                              created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                """, (
                    self.generate_uuid(), route_data['id'], station_id, seq + 1,
                    arrival_offset, departure_offset,
                    datetime.now(), datetime.now()
                ))
            
            # Genera servizi per questa rotta usando gli UUID dei service types
            self.generate_services_for_route(route_data['id'], route_data['services'], route_data.get('is_international', False))
    
    def generate_services_for_route(self, route_id, service_type_ids, is_international):
        """Genera servizi per una rotta usando gli UUID dei service types"""
        cursor = self.conn.cursor()
        
        for service_type_id in service_type_ids:
            # Ottieni IDs necessari
            cursor.execute("SELECT id, code FROM service_types WHERE id = %s", (service_type_id,))
            service_type_result = cursor.fetchone()
            if not service_type_result:
                continue
            service_type_id, service_code = service_type_result
            
            cursor.execute("SELECT id FROM railway_operators ORDER BY RANDOM() LIMIT 1")
            operator_result = cursor.fetchone()
            if not operator_result:
                continue
            operator_id = operator_result[0]
            
            cursor.execute("SELECT id FROM trains ORDER BY RANDOM() LIMIT 1")
            train_result = cursor.fetchone()
            if not train_result:
                continue
            train_id = train_result[0]
            
            # Orari realistici
            departure_times = [
                time(6, 30), time(8, 15), time(10, 45), 
                time(14, 20), time(17, 30), time(20, 10)
            ]
            
            for dep_time in departure_times:
                service_id = self.generate_uuid()
                
                operates_days = {
                    "monday": True, "tuesday": True, "wednesday": True,
                    "thursday": True, "friday": True, "saturday": True, "sunday": True
                }
                
                cursor.execute("""
                    INSERT INTO train_services (id, train_id, route_id, service_type_id, 
                                               operator_id, departure_time, service_name,
                                               operates_days, valid_from, valid_to,
                                               cabins_enabled, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    service_id, train_id, route_id, service_type_id, operator_id,
                    dep_time, f"{service_code} {dep_time.strftime('%H:%M')}",
                    json.dumps(operates_days), date.today(), 
                    date.today() + timedelta(days=365),
                    service_code in ['FER_N'], datetime.now(), datetime.now()
                ))
                
                # Genera alcuni viaggi per questo servizio
                self.generate_trips_for_service(service_id, dep_time)
    
    def generate_trips_for_service(self, service_id, departure_time):
        """Genera viaggi per un servizio nei prossimi 30 giorni"""
        cursor = self.conn.cursor()
        
        start_date = date.today()
        for i in range(30):
            service_date = start_date + timedelta(days=i)
            
            # Calcola orari pianificati
            planned_departure = datetime.combine(service_date, departure_time)
            planned_arrival = planned_departure + timedelta(hours=random.randint(2, 8))
            
            # Possibili ritardi
            delay = random.choices([0, 5, 10, 15, 30, 60], weights=[70, 15, 8, 4, 2, 1])[0]
            status = 'SCHEDULED' if service_date > date.today() else random.choice(['COMPLETED', 'RUNNING'])
            
            cursor.execute("""
                INSERT INTO trips (id, train_service_id, service_date, 
                                 planned_departure_time, planned_arrival_time,
                                 status, delay_minutes, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            """, (
                self.generate_uuid(), service_id, service_date,
                planned_departure, planned_arrival, status, delay,
                datetime.now(), datetime.now()
            ))
    
    def generate_trip_station_updates(self):
        """Genera aggiornamenti realistici per le stazioni dei viaggi"""
        cursor = self.conn.cursor()
        
        # Ottieni tutti i viaggi e le loro stazioni
        cursor.execute("""
            SELECT t.id as trip_id, t.service_date, t.planned_departure_time, 
                   t.planned_arrival_time, t.delay_minutes, t.status,
                   ts.route_id
            FROM trips t
            JOIN train_services ts ON t.train_service_id = ts.id
            ORDER BY t.service_date, t.planned_departure_time
        """)
        
        trips = cursor.fetchall()
        
        for trip in trips:
            trip_id, service_date, planned_dep, planned_arr, delay_minutes, status, route_id = trip
            
            # Ottieni le stazioni della rotta
            cursor.execute("""
                SELECT rs.id, rs.station_id, rs.sequence, rs.arrival_offset_min, rs.departure_offset_min
                FROM route_stations rs
                WHERE rs.route_id = %s
                ORDER BY rs.sequence
            """, (route_id,))
            
            route_stations = cursor.fetchall()
            
            if not route_stations:
                continue
                
            # Genera aggiornamenti per ogni stazione della rotta
            for station in route_stations:
                route_station_id, station_id, sequence, arrival_offset, departure_offset = station
                
                # Calcola orari pianificati basati su service_date e offset
                planned_arrival = None
                planned_departure = None
                
                if arrival_offset is not None:
                    planned_arrival = planned_dep + timedelta(minutes=arrival_offset)
                    
                if departure_offset is not None:
                    planned_departure = planned_dep + timedelta(minutes=departure_offset)
                
                # Genera aggiornamenti realistici
                actual_arrival = None
                actual_departure = None
                station_delay = 0
                platform_change = None
                
                # Solo per viaggi passati o in corso
                if status in ['COMPLETED', 'RUNNING'] and service_date <= date.today():
                    # Simula ritardi cumulativi (aumentano lungo la rotta)
                    base_delay = delay_minutes or 0
                    additional_delay = random.choices([0, 2, 5, 10], weights=[60, 25, 10, 5])[0]
                    station_delay = max(0, base_delay + (sequence - 1) * 2 + additional_delay)
                    
                    # Calcola orari effettivi
                    if planned_arrival:
                        actual_arrival = planned_arrival + timedelta(minutes=station_delay)
                    if planned_departure:
                        actual_departure = planned_departure + timedelta(minutes=station_delay)
                    
                    # Occasionali cambi binario (5% probabilità)
                    if random.random() < 0.05:
                        platform_change = f"Binario {random.randint(1, 12)}"
                
                # Inserisci aggiornamento stazione
                update_id = self.generate_uuid()
                cursor.execute("""
                    INSERT INTO trip_station_updates (
                        id, trip_id, route_station_id, planned_arrival, planned_departure,
                        actual_arrival, actual_departure, delay_minutes, platform_change,
                        updated_at, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (trip_id, route_station_id) DO UPDATE SET
                        actual_arrival = EXCLUDED.actual_arrival,
                        actual_departure = EXCLUDED.actual_departure,
                        delay_minutes = EXCLUDED.delay_minutes,
                        platform_change = EXCLUDED.platform_change,
                        updated_at = EXCLUDED.updated_at
                """, (
                    update_id, trip_id, route_station_id, planned_arrival, planned_departure,
                    actual_arrival, actual_departure, station_delay, platform_change,
                    datetime.now(), datetime.now()
                ))
    
    def generate_fares(self):
        """Genera tariffe dai dati JSON"""
        print("💰 Inserimento fares...")
        cursor = self.conn.cursor()
        
        for fare_data in self.static_data['fares']:
            cursor.execute("""
                INSERT INTO fares (id, origin_country_id, destination_country_id,
                                 wagon_category_id, service_type_id,
                                 distance_min_km, distance_max_km, base_fare,
                                 fare_per_km, is_cross_border, international_supplement,
                                 currency, valid_from, valid_to, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, (
                fare_data['id'], 
                fare_data['origin_country_id'], fare_data['destination_country_id'],
                fare_data['wagon_category_id'], fare_data['service_type_id'], 
                fare_data['distance_min_km'], fare_data['distance_max_km'],
                Decimal(str(fare_data['base_fare'])), Decimal(str(fare_data['fare_per_km'])),
                fare_data['is_cross_border'], Decimal(str(fare_data.get('international_supplement', 0.00))), 
                'EUR', datetime.now(), datetime.now() + timedelta(days=365),
                datetime.now(), datetime.now()
            ))
    
    def calculate_fare_for_booking(self, origin_country, dest_country, distance_km, service_type_id, wagon_category_id):
        """Calcola la tariffa per una prenotazione con sistema di priorità intelligente"""
        cursor = self.conn.cursor()
        
        # Query per ottenere tutte le tariffe potenzialmente applicabili con scoring
        cursor.execute("""
            SELECT f.base_fare, f.fare_per_km, f.international_supplement,
                   f.origin_country_id, f.destination_country_id, 
                   f.service_type_id, f.wagon_category_id,
                   f.route_id, f.operator_id,
                   -- Calcolo score di priorità (più alto = più specifico)
                   (CASE 
                       -- Match perfetto: tutti i campi specifici
                       WHEN f.origin_country_id = %s AND f.destination_country_id = %s 
                            AND f.service_type_id = %s AND f.wagon_category_id = %s THEN 100
                       -- Match paesi + servizio
                       WHEN f.origin_country_id = %s AND f.destination_country_id = %s 
                            AND f.service_type_id = %s THEN 80
                       -- Match paesi + categoria vagone
                       WHEN f.origin_country_id = %s AND f.destination_country_id = %s 
                            AND f.wagon_category_id = %s THEN 75
                       -- Match solo paesi
                       WHEN f.origin_country_id = %s AND f.destination_country_id = %s THEN 60
                       -- Match solo servizio (tariffa generica per tipo servizio)
                       WHEN f.service_type_id = %s AND f.origin_country_id IS NULL THEN 40
                       -- Match solo categoria vagone (tariffa generica per categoria)
                       WHEN f.wagon_category_id = %s AND f.origin_country_id IS NULL THEN 35
                       -- Tariffa generica (tutti NULL tranne distanza)
                       WHEN f.origin_country_id IS NULL AND f.destination_country_id IS NULL 
                            AND f.service_type_id IS NULL AND f.wagon_category_id IS NULL THEN 10
                       ELSE 0
                   END) as priority_score
            FROM fares f
            WHERE %s BETWEEN f.distance_min_km AND f.distance_max_km
            AND (
                -- Match specifici
                (f.origin_country_id = %s AND f.destination_country_id = %s) OR
                -- Match parziali
                (f.service_type_id = %s AND f.origin_country_id IS NULL) OR
                (f.wagon_category_id = %s AND f.origin_country_id IS NULL) OR
                -- Tariffa generica
                (f.origin_country_id IS NULL AND f.destination_country_id IS NULL 
                 AND f.service_type_id IS NULL AND f.wagon_category_id IS NULL)
            )
            ORDER BY priority_score DESC, f.base_fare ASC
            LIMIT 5
        """, (
            # Parametri per scoring
            origin_country, dest_country, service_type_id, wagon_category_id,  # Match perfetto
            origin_country, dest_country, service_type_id,                    # Match paesi + servizio
            origin_country, dest_country, wagon_category_id,                  # Match paesi + categoria
            origin_country, dest_country,                                     # Match solo paesi
            service_type_id,                                                  # Match solo servizio
            wagon_category_id,                                                # Match solo categoria
            # Parametri per WHERE
            distance_km,                                                      # Distanza
            origin_country, dest_country,                                     # Match paesi
            service_type_id,                                                  # Match servizio
            wagon_category_id                                                 # Match categoria
        ))
        
        fare_results = cursor.fetchall()
        
        if fare_results:
            # Prende la tariffa con score più alto (prima nella lista ordinata)
            best_fare = fare_results[0]
            base_fare, fare_per_km, supplement, *_, priority_score = best_fare
            
            # Log della tariffa scelta per debug
            print(f"   💰 Tariffa scelta: score={priority_score}, base={base_fare}€, per_km={fare_per_km}€")
            
            # Calcola tariffa finale
            supplement = supplement or 0  # NULL -> 0
            total_fare = float(base_fare) + (float(fare_per_km) * distance_km) + float(supplement)
            return Decimal(str(round(total_fare, 2)))
        else:
            # Fallback: calcolo base se non trova alcuna tariffa
            print(f"   ⚠️  Nessuna tariffa trovata, usando calcolo base")
            return Decimal(str(round(15.00 + (0.15 * distance_km), 2)))
    
    def generate_users_and_bookings(self, num_users=500, num_bookings=1500):
        """Genera utenti e prenotazioni con dati più realistici"""
        print(f"👥 Generazione di {num_users} utenti e {num_bookings} prenotazioni...")
        cursor = self.conn.cursor()
        
        # Genera utenti
        user_ids = []
        used_emails = set()  # Per evitare email duplicate
        
        for i in range(num_users):
            user_id = self.generate_uuid()
            
            # Genera email unica
            attempts = 0
            while attempts < 10:  # Max 10 tentativi
                email = fake.email()
                if email not in used_emails:
                    used_emails.add(email)
                    break
                attempts += 1
            else:
                # Se non riesce a generare email unica, usa un timestamp
                email = f"user{i}_{int(datetime.now().timestamp())}@example.com"
            
            cursor.execute("""
                INSERT INTO users (id, first_name, last_name, email, password, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                user_id, fake.first_name(), fake.last_name(), 
                email, fake.password(), datetime.now(), datetime.now()
            ))
            user_ids.append(user_id)
        
        # Genera passeggeri e prenotazioni con distribuzione realistica
        booking_ids = []
        for i in range(num_bookings):
            user_id = random.choice(user_ids)
            
            # Passeggero
            passenger_id = self.generate_uuid()
            cursor.execute("""
                INSERT INTO passengers (id, user_id, first_name, last_name, email, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                passenger_id, user_id, fake.first_name(), fake.last_name(),
                fake.email(), datetime.now(), datetime.now()
            ))
            
            # Prenotazione
            booking_id = self.generate_booking_for_passenger(passenger_id, user_id)
            if booking_id:
                booking_ids.append(booking_id)
                
            # Mostra progresso ogni 100 prenotazioni
            if (i + 1) % 100 == 0:
                print(f"   📋 Generate {i + 1}/{num_bookings} prenotazioni...")
        
        print(f"🎫 Generazione di {len(booking_ids)} ticket...")
        # Genera ticket per tutte le prenotazioni
        self.generate_tickets_for_bookings(booking_ids)
        
        print(f"💳 Generazione pagamenti...")
        # Genera pagamenti per le prenotazioni
        self.generate_payments_for_bookings(booking_ids)
        
        print(f"🪑 Generazione prenotazioni posti...")
        # Genera alcune prenotazioni di posti
        self.generate_seat_reservations(booking_ids)
    
    def generate_booking_for_passenger(self, passenger_id, user_id):
        """Genera una prenotazione realistica con calcolo tariffe"""
        cursor = self.conn.cursor()
        
        # Seleziona trip casuale con più dettagli
        cursor.execute("""
            SELECT t.id, rs_orig.station_id as origin, rs_dest.station_id as dest,
                   t.planned_departure_time, t.planned_arrival_time,
                   ts.service_type_id, ts.train_id,
                   c_orig.country_id as origin_country, c_dest.country_id as dest_country
            FROM trips t
            JOIN train_services ts ON t.train_service_id = ts.id
            JOIN route_stations rs_orig ON ts.route_id = rs_orig.route_id AND rs_orig.sequence = 1
            JOIN route_stations rs_dest ON ts.route_id = rs_dest.route_id AND rs_dest.sequence = (
                SELECT MAX(sequence) FROM route_stations WHERE route_id = ts.route_id
            )
            JOIN stations s_orig ON rs_orig.station_id = s_orig.id
            JOIN stations s_dest ON rs_dest.station_id = s_dest.id
            JOIN cities c_orig ON s_orig.city_id = c_orig.id
            JOIN cities c_dest ON s_dest.city_id = c_dest.id
            ORDER BY RANDOM() LIMIT 1
        """)
        
        trip_data = cursor.fetchone()
        if not trip_data:
            return None
            
        (trip_id, origin_station, dest_station, dep_time, arr_time, 
         service_type_id, train_id, origin_country, dest_country) = trip_data
        
        # Seleziona vagone casuale del treno
        cursor.execute("""
            SELECT w.category_id FROM wagons w
            JOIN train_wagons tw ON w.id = tw.wagon_id
            WHERE tw.train_id = %s
            ORDER BY RANDOM() LIMIT 1
        """, (train_id,))
        
        wagon_cat_result = cursor.fetchone()
        wagon_category_id = wagon_cat_result[0] if wagon_cat_result else None
        
        if not wagon_category_id:
            return None
        
        # Calcola distanza realistica
        distance = random.randint(50, 800)
        
        # Calcola tariffa basata sui dati reali usando UUID
        calculated_fare = self.calculate_fare_for_booking(
            origin_country, dest_country, distance, service_type_id, wagon_category_id
        )
        
        booking_id = self.generate_uuid()
        # Genera un booking reference unico usando timestamp + random
        booking_ref = self.generate_unique_booking_reference(cursor)
        
        cursor.execute("""
            INSERT INTO bookings (id, booking_reference, user_id, passenger_id,
                                origin_station_id, destination_station_id, departure_date,
                                total_amount, currency, status, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            booking_id, booking_ref, user_id, passenger_id,
            origin_station, dest_station, dep_time.date(),
            calculated_fare, 'EUR', 'CONFIRMED',
            datetime.now(), datetime.now()
        ))
        
        # Genera segmento di prenotazione
        self.generate_booking_segment(booking_id, trip_id, origin_station, dest_station, 
                                    dep_time, arr_time, distance, calculated_fare)
        
        return booking_id  # Restituisci l'ID per generare ticket e pagamenti
    
    def generate_booking_segment(self, booking_id, trip_id, origin_station, dest_station, 
                               dep_time, arr_time, distance, total_amount):
        """Genera segmento di prenotazione con calcolo tariffe corretto"""
        cursor = self.conn.cursor()
        
        try:
            # Ottieni route stations
            cursor.execute("""
                SELECT rs.id FROM route_stations rs
                JOIN train_services ts ON rs.route_id = ts.route_id
                JOIN trips t ON ts.id = t.train_service_id
                WHERE t.id = %s AND rs.station_id = %s
            """, (trip_id, origin_station))
            origin_route_station_result = cursor.fetchone()
            
            cursor.execute("""
                SELECT rs.id FROM route_stations rs
                JOIN train_services ts ON rs.route_id = ts.route_id
                JOIN trips t ON ts.id = t.train_service_id
                WHERE t.id = %s AND rs.station_id = %s
            """, (trip_id, dest_station))
            dest_route_station_result = cursor.fetchone()
            
            if not origin_route_station_result or not dest_route_station_result:
                return
                
            origin_route_station = origin_route_station_result[0]
            dest_route_station = dest_route_station_result[0]
            
            segment_id = self.generate_uuid()
            
            cursor.execute("""
                INSERT INTO booking_segments (id, booking_id, trip_id, sequence,
                                            origin_station_id, destination_station_id,
                                            origin_route_station_id, destination_route_station_id,
                                            planned_departure_time, planned_arrival_time,
                                            distance_km, segment_amount, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                segment_id, booking_id, trip_id, 1,
                origin_station, dest_station, origin_route_station, dest_route_station,
                dep_time, arr_time, distance, total_amount, datetime.now(), datetime.now()
            ))
        except Exception as e:
            print(f"⚠️ Errore generazione booking segment: {e}")
    
    def generate_tickets_for_bookings(self, booking_ids):
        """Genera ticket per tutte le prenotazioni"""
        cursor = self.conn.cursor()
        
        for booking_id in booking_ids:
            # Ottieni dettagli prenotazione per generare ticket
            cursor.execute("""
                SELECT b.id, b.passenger_id, bs.id as segment_id, bs.trip_id,
                       bs.origin_station_id, bs.destination_station_id,
                       bs.segment_amount, b.departure_date, w.category_id
                FROM bookings b
                JOIN booking_segments bs ON b.id = bs.booking_id
                JOIN trips t ON bs.trip_id = t.id
                JOIN train_services ts ON t.train_service_id = ts.id
                JOIN train_wagons tw ON ts.train_id = tw.train_id
                JOIN wagons w ON tw.wagon_id = w.id
                WHERE b.id = %s
                LIMIT 1
            """, (booking_id,))
            
            booking_data = cursor.fetchone()
            if not booking_data:
                continue
                
            (booking_id, passenger_id, segment_id, trip_id, origin_station, 
             dest_station, amount, service_date, wagon_category_id) = booking_data
            
            ticket_id = self.generate_uuid()
            ticket_number = self.generate_unique_ticket_number(cursor)
            
            cursor.execute("""
                INSERT INTO tickets (id, ticket_number, booking_id, booking_segment_id,
                                   passenger_id, trip_id, origin_station_id, destination_station_id,
                                   wagon_category_id, fare_amount, currency, status,
                                   issued_at, service_date, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                ticket_id, ticket_number, booking_id, segment_id, passenger_id, trip_id,
                origin_station, dest_station, wagon_category_id, amount, 'EUR', 'VALID',
                datetime.now(), service_date, datetime.now(), datetime.now()
            ))
    
    def generate_payments_for_bookings(self, booking_ids):
        """Genera pagamenti per le prenotazioni"""
        cursor = self.conn.cursor()
        payment_methods = ['CREDIT_CARD', 'DEBIT_CARD', 'PAYPAL', 'SEPA_DIRECT_DEBIT']
        
        for booking_id in booking_ids:
            cursor.execute("""
                SELECT total_amount FROM bookings WHERE id = %s
            """, (booking_id,))
            
            amount_result = cursor.fetchone()
            if not amount_result:
                continue
                
            amount = amount_result[0]
            payment_id = self.generate_uuid()
            
            # 95% pagamenti completati, 5% pending/failed
            status = random.choices(['COMPLETED', 'PENDING', 'FAILED'], weights=[95, 3, 2])[0]
            paid_at = datetime.now() if status == 'COMPLETED' else None
            transaction_ref = f"TXN{random.randint(100000000, 999999999)}" if status == 'COMPLETED' else None
            
            cursor.execute("""
                INSERT INTO payments (id, booking_id, amount, currency, payment_method,
                                    status, transaction_ref, paid_at, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                payment_id, booking_id, amount, 'EUR', random.choice(payment_methods),
                status, transaction_ref, paid_at, datetime.now(), datetime.now()
            ))
    
    def generate_seat_reservations(self, booking_ids):
        """Genera prenotazioni di posti per alcuni biglietti"""
        cursor = self.conn.cursor()
        
        # Prenota posti solo per il 60% delle prenotazioni (simulazione realistica)
        bookings_with_seats = random.sample(booking_ids, min(len(booking_ids), int(len(booking_ids) * 0.6)))
        
        for booking_id in bookings_with_seats:
            # Ottieni dettagli per la prenotazione del posto
            cursor.execute("""
                SELECT bs.id, bs.trip_id, bs.origin_route_station_id, bs.destination_route_station_id,
                       b.passenger_id, ts.train_id
                FROM booking_segments bs
                JOIN bookings b ON bs.booking_id = b.id
                JOIN trips t ON bs.trip_id = t.id
                JOIN train_services ts ON t.train_service_id = ts.id
                WHERE bs.booking_id = %s
            """, (booking_id,))
            
            segment_data = cursor.fetchone()
            if not segment_data:
                continue
                
            (segment_id, trip_id, origin_route_station, dest_route_station, 
             passenger_id, train_id) = segment_data
            
            # Trova un posto disponibile
            cursor.execute("""
                SELECT ws.id FROM wagon_seats ws
                JOIN train_wagons tw ON ws.wagon_id = tw.wagon_id
                WHERE tw.train_id = %s
                AND ws.id NOT IN (
                    SELECT wagon_seat_id FROM seat_reservations 
                    WHERE trip_id = %s AND wagon_seat_id IS NOT NULL
                )
                ORDER BY RANDOM() LIMIT 1
            """, (train_id, trip_id))
            
            seat_result = cursor.fetchone()
            if not seat_result:
                continue  # Nessun posto disponibile
                
            seat_id = seat_result[0]
            reservation_id = self.generate_uuid()
            
            # Prenotazione valida per 2 ore dopo l'orario di partenza
            cursor.execute("""
                SELECT planned_departure_time FROM trips WHERE id = %s
            """, (trip_id,))
            departure_result = cursor.fetchone()
            expires_at = departure_result[0] + timedelta(hours=2) if departure_result else datetime.now() + timedelta(hours=2)
            
            cursor.execute("""
                INSERT INTO seat_reservations (id, booking_segment_id, trip_id, wagon_seat_id,
                                             passenger_id, origin_route_station_id, destination_route_station_id,
                                             expires_at, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                reservation_id, segment_id, trip_id, seat_id, passenger_id,
                origin_route_station, dest_route_station, expires_at,
                datetime.now(), datetime.now()
            ))
    
    def generate_service_exceptions(self):
        """Genera eccezioni del servizio (cancellazioni, scioperi, etc)"""
        print("⚠️ Inserimento service exceptions...")
        
        cursor = self.conn.cursor()
        
        # Ottieni i train_service_id esistenti
        cursor.execute("SELECT id FROM train_services ORDER BY RANDOM() LIMIT 10")
        train_service_ids = [row[0] for row in cursor.fetchall()]
        
        if not train_service_ids:
            print("❌ Nessun train_service trovato")
            return
        
        # Date specifiche per le eccezioni
        exception_dates_and_reasons = [
            ('2025-12-25', 'Giorno di Natale', False),
            ('2025-01-01', 'Capodanno', False),
            ('2025-05-01', 'Festa del Lavoro', False),
            ('2025-08-15', 'Ferragosto', False),
            ('2025-04-25', 'Festa della Liberazione', False),
            ('2025-06-02', 'Festa della Repubblica', False),
            ('2025-03-15', 'Sciopero trasporti', False),
            ('2025-07-20', 'Sciopero generale', False),
            ('2025-12-24', 'Vigilia di Natale - Servizio ridotto', True),
            ('2025-12-31', 'San Silvestro - Servizio extra', True)
        ]
        
        for i, (date, reason, is_running) in enumerate(exception_dates_and_reasons):
            # Usa un train_service diverso per ogni eccezione
            train_service_id = train_service_ids[i % len(train_service_ids)]
            
            cursor.execute("""
                INSERT INTO service_exceptions (id, train_service_id, exception_date, 
                                              is_running, reason, created_at, updated_at)
                VALUES (%s, %s, %s::date, %s, %s, %s::timestamp, %s::timestamp)
                ON CONFLICT (train_service_id, exception_date) DO NOTHING
            """, (
                str(uuid.uuid4()),
                train_service_id,
                date,
                is_running,
                reason,
                datetime.now(),
                datetime.now()
            ))
        
        self.conn.commit()
        print(f"✅ Service exceptions inserite")
    
    def run_full_generation(self, clear_data=True):
        """Esegue la generazione completa dei dati"""
        print("🚄 Avvio generazione dati Raylix...")
        
        self.connect_db()
        
        try:
            if clear_data:
                self.clear_all_data()
            
            print("📍 Inserimento dati statici...")
            self.insert_static_data()
            
            print("🚂 Generazione operatori...")
            self.generate_operators()
            
            print("🎫 Generazione tipi di servizio...")
            self.generate_service_types()
            
            print("🚃 Generazione categorie vagoni...")
            self.generate_wagon_categories()
            
            print("🚄 Generazione treni e vagoni...")
            self.generate_trains_and_wagons()
            
            print("🛤️ Generazione rotte e servizi...")
            self.generate_routes_and_services()
            
            self.generate_service_exceptions()
            
            print("� Generazione aggiornamenti viaggi...")
            self.generate_trip_station_updates()
            
            print("�💰 Generazione tariffe...")
            self.generate_fares()
            
            print("👥 Generazione utenti e prenotazioni...")
            self.generate_users_and_bookings(num_users=500, num_bookings=1500)
            
            print("✅ Generazione completata!")
            
        except Exception as e:
            print(f"❌ Errore durante la generazione: {e}")
            raise
        finally:
            if self.conn:
                self.conn.close()

def main():
    # Configurazione database
    DB_CONFIG = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'database': os.getenv('DB_NAME', 'raylix'),
        'user': os.getenv('DB_USER', 'postgres'), 
        'password': os.getenv('DB_PASSWORD', 'postgres'),
        'port': os.getenv('DB_PORT', '5432')
    }
    
    print("🚄 Raylix Data Generator")
    print("=" * 40)
    
    # Opzioni da CLI
    clear_data = '--no-clear' not in sys.argv
    
    generator = RaylixDataGenerator(DB_CONFIG)
    generator.run_full_generation(clear_data=clear_data)

if __name__ == "__main__":
    main()