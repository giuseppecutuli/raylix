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

class DatabaseManager:
    """Gestione connessione e operazioni database"""
    
    def __init__(self, db_config):
        self.db_config = db_config
        self.conn = None
        
    def connect(self):
        """Connessione al database"""
        try:
            self.conn = psycopg2.connect(**self.db_config)
            self.conn.autocommit = True
            print("✅ Connesso al database PostgreSQL")
        except Exception as e:
            print(f"❌ Errore connessione database: {e}")
            raise
            
    def get_cursor(self):
        """Restituisce cursor per query"""
        return self.conn.cursor()
        
    def close(self):
        """Chiude connessione"""
        if self.conn:
            self.conn.close()

class StaticDataLoader:
    """Caricamento dati statici da file JSON"""
    
    @staticmethod
    def load_all():
        """Carica tutti i dati statici"""
        entities = [
            'countries', 'cities', 'stations', 'operators', 
            'service_types', 'wagon_categories', 'train_configs', 
            'routes', 'fares'
        ]
        
        data = {}
        for entity in entities:
            file_path = f'static_data/{entity}.json'
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data[entity] = json.load(f)
                print(f"✅ Caricato {entity}.json")
            except FileNotFoundError:
                print(f"⚠️ File {file_path} non trovato")
                data[entity] = []
                
        return data

class UniqueValueGenerator:
    """Generatore di valori unici per il database"""
    
    @staticmethod
    def uuid():
        return str(uuid.uuid4())
    
    @staticmethod
    def booking_reference(cursor):
        """Genera booking reference unico"""
        for _ in range(10):
            timestamp = int(datetime.now().timestamp() * 1000) % 1000000
            random_part = random.randint(100, 999)
            ref = f"BK{timestamp}{random_part}"
            
            cursor.execute("SELECT COUNT(*) FROM bookings WHERE booking_reference = %s", (ref,))
            if cursor.fetchone()[0] == 0:
                return ref
                
        return f"BK{random.randint(10000000, 99999999)}"
    
    @staticmethod
    def ticket_number(cursor):
        """Genera ticket number unico"""
        for _ in range(10):
            timestamp = int(datetime.now().timestamp() * 1000) % 1000000
            random_part = random.randint(100, 999)
            ticket = f"TK{timestamp}{random_part}"
            
            cursor.execute("SELECT COUNT(*) FROM tickets WHERE ticket_number = %s", (ticket,))
            if cursor.fetchone()[0] == 0:
                return ticket
                
        return f"TK{random.randint(10000000, 99999999)}"

class FareCalculator:
    """Calcolo tariffe intelligente"""
    
    def __init__(self, cursor):
        self.cursor = cursor
    
    def calculate(self, origin_country, dest_country, distance_km, service_type_id, wagon_category_id):
        """Calcola tariffa con sistema di priorità"""
        
        query = """
            SELECT f.base_fare, f.fare_per_km, f.international_supplement,
                   (CASE 
                       WHEN f.origin_country_id = %s AND f.destination_country_id = %s 
                            AND f.service_type_id = %s AND f.wagon_category_id = %s THEN 100
                       WHEN f.origin_country_id = %s AND f.destination_country_id = %s 
                            AND f.service_type_id = %s THEN 80
                       WHEN f.origin_country_id = %s AND f.destination_country_id = %s 
                            AND f.wagon_category_id = %s THEN 75
                       WHEN f.origin_country_id = %s AND f.destination_country_id = %s THEN 60
                       WHEN f.service_type_id = %s AND f.origin_country_id IS NULL THEN 40
                       WHEN f.wagon_category_id = %s AND f.origin_country_id IS NULL THEN 35
                       WHEN f.origin_country_id IS NULL AND f.destination_country_id IS NULL 
                            AND f.service_type_id IS NULL AND f.wagon_category_id IS NULL THEN 10
                       ELSE 0
                   END) as priority_score
            FROM fares f
            WHERE %s BETWEEN f.distance_min_km AND f.distance_max_km
            AND (
                (f.origin_country_id = %s AND f.destination_country_id = %s) OR
                (f.service_type_id = %s AND f.origin_country_id IS NULL) OR
                (f.wagon_category_id = %s AND f.origin_country_id IS NULL) OR
                (f.origin_country_id IS NULL AND f.destination_country_id IS NULL 
                 AND f.service_type_id IS NULL AND f.wagon_category_id IS NULL)
            )
            ORDER BY priority_score DESC, f.base_fare ASC
            LIMIT 1
        """
        
        params = [
            origin_country, dest_country, service_type_id, wagon_category_id,
            origin_country, dest_country, service_type_id,
            origin_country, dest_country, wagon_category_id,
            origin_country, dest_country,
            service_type_id, wagon_category_id,
            distance_km,
            origin_country, dest_country,
            service_type_id, wagon_category_id
        ]
        
        self.cursor.execute(query, params)
        result = self.cursor.fetchone()
        
        if result:
            base_fare, fare_per_km, supplement = result[:3]
            supplement = supplement or 0
            total = float(base_fare) + (float(fare_per_km) * distance_km) + float(supplement)
            return Decimal(str(round(total, 2)))
        else:
            # Fallback
            return Decimal(str(round(15.00 + (0.15 * distance_km), 2)))

class StaticDataInserter:
    """Inserimento dati statici nel database"""
    
    def __init__(self, cursor, static_data):
        self.cursor = cursor
        self.data = static_data
    
    def insert_all(self):
        """Inserisce tutti i dati statici"""
        self._insert_countries()
        self._insert_cities()
        self._insert_stations()
        self._insert_operators()
        self._insert_service_types()
        self._insert_wagon_categories()
    
    def _insert_countries(self):
        print("📍 Inserimento countries...")
        query = """
            INSERT INTO countries (id, name, iso_code, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s) ON CONFLICT (id) DO NOTHING
        """
        for country in self.data['countries']:
            self.cursor.execute(query, (
                country['id'], country['name'], country['iso_code'],
                datetime.now(), datetime.now()
            ))
    
    def _insert_cities(self):
        print("🏙️ Inserimento cities...")
        query = """
            INSERT INTO cities (id, name, country_id, latitude, longitude, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s) ON CONFLICT (id) DO NOTHING
        """
        for city in self.data['cities']:
            self.cursor.execute(query, (
                city['id'], city['name'], city['country_id'],
                city['latitude'], city['longitude'], datetime.now(), datetime.now()
            ))
    
    def _insert_stations(self):
        print("🚉 Inserimento stations...")
        query = """
            INSERT INTO stations (id, name, city_id, latitude, longitude, platforms, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (id) DO NOTHING
        """
        for station in self.data['stations']:
            platforms = json.dumps(station['platforms']) if 'platforms' in station else None
            self.cursor.execute(query, (
                station['id'], station['name'], station['city_id'],
                station['latitude'], station['longitude'], platforms,
                datetime.now(), datetime.now()
            ))
    
    def _insert_operators(self):
        print("🚂 Inserimento operators...")
        query = """
            INSERT INTO railway_operators (id, name, country_id, code, website, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s) ON CONFLICT (code) DO NOTHING
        """
        for op in self.data['operators']:
            self.cursor.execute(query, (
                op['id'], op['name'], op['country_id'], 
                op['code'], op.get('website'), datetime.now(), datetime.now()
            ))
    
    def _insert_service_types(self):
        print("🎫 Inserimento service types...")
        query = """
            INSERT INTO service_types (id, name, code, requires_seat_assignment, allows_standing, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s) ON CONFLICT (code) DO NOTHING
        """
        for service in self.data['service_types']:
            self.cursor.execute(query, (
                service['id'], service['name'], service['code'],
                service['requires_seat_assignment'], service['allows_standing'],
                datetime.now(), datetime.now()
            ))
    
    def _insert_wagon_categories(self):
        print("🚃 Inserimento wagon categories...")
        query = """
            INSERT INTO wagon_categories (id, name, created_at, updated_at)
            VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING
        """
        for cat in self.data['wagon_categories']:
            self.cursor.execute(query, (cat['id'], cat['name'], datetime.now(), datetime.now()))

class TrainGenerator:
    """Generazione treni, vagoni e posti"""
    
    def __init__(self, cursor, static_data):
        self.cursor = cursor
        self.data = static_data
    
    def generate_all(self):
        """Genera treni completi con vagoni e posti"""
        print("🚄 Generazione treni, vagoni e posti...")
        
        for train_config in self.data['train_configs']:
            self._create_train(train_config)
            self._create_wagons_for_train(train_config)
    
    def _create_train(self, config):
        """Crea un singolo treno"""
        query = """
            INSERT INTO trains (id, code, model, is_ship, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT (code) DO NOTHING
        """
        self.cursor.execute(query, (
            config['id'], config['code'], config['model'], 
            config['is_ship'], datetime.now(), datetime.now()
        ))
    
    def _create_wagons_for_train(self, train_config):
        """Crea vagoni per un treno"""
        for position, wagon_config in enumerate(train_config['wagon_configs'], 1):
            wagon_id = UniqueValueGenerator.uuid()
            wagon_code = f"{train_config['id'][:8]}_W{position:02d}"
            
            # Crea vagone
            self.cursor.execute("""
                INSERT INTO wagons (id, code, category_id, total_seats, total_rows, 
                                  seats_per_row, layout_pattern, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                wagon_id, wagon_code, wagon_config['category_id'], wagon_config['seats'], 
                wagon_config['rows'], wagon_config['seats_per_row'], 
                wagon_config.get('layout_pattern', '2+2'), datetime.now(), datetime.now()
            ))
            
            # Collega al treno
            self.cursor.execute("""
                INSERT INTO train_wagons (train_id, wagon_id, position, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s)
            """, (train_config['id'], wagon_id, position, datetime.now(), datetime.now()))
            
            # Genera posti
            if wagon_config['seats'] > 0:
                self._create_seats_for_wagon(wagon_id, wagon_config, train_config['is_ship'])
    
    def _create_seats_for_wagon(self, wagon_id, config, is_ship):
        """Crea posti per un vagone"""
        seat_types = ['WINDOW', 'AISLE'] if not is_ship else ['WINDOW', 'AISLE', 'COUCHETTE_LOWER', 'COUCHETTE_UPPER']
        orientations = ['FORWARD', 'BACKWARD']
        
        seat_number = 1
        for row in range(1, config['rows'] + 1):
            for col_idx in range(config['seats_per_row']):
                col_letter = chr(65 + col_idx)
                
                self.cursor.execute("""
                    INSERT INTO wagon_seats (id, wagon_id, seat_number, seat_type, 
                                           seat_orientation, row_number, column_letter, 
                                           is_accessible, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    UniqueValueGenerator.uuid(), wagon_id, str(seat_number), 
                    random.choice(seat_types), random.choice(orientations), 
                    row, col_letter, seat_number % 20 == 0,
                    datetime.now(), datetime.now()
                ))
                seat_number += 1

class RouteGenerator:
    """Generazione rotte e servizi"""
    
    def __init__(self, cursor, static_data):
        self.cursor = cursor
        self.data = static_data
    
    def generate_all(self):
        """Genera rotte complete con servizi"""
        print("🛤️ Generazione rotte e servizi...")
        
        for route_data in self.data['routes']:
            self._create_route(route_data)
            self._create_route_stations(route_data)
            self._create_services_for_route(route_data)
    
    def _create_route(self, route_data):
        """Crea una singola rotta"""
        self.cursor.execute("""
            INSERT INTO routes (id, name, description, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s) ON CONFLICT (id) DO NOTHING
        """, (
            route_data['id'], route_data['name'], 
            route_data.get('description', f"Rotta {route_data['name']}"), 
            datetime.now(), datetime.now()
        ))
    
    def _create_route_stations(self, route_data):
        """Crea stazioni della rotta con orari realistici"""
        base_time = route_data.get('base_time_minutes', 90)
        is_international = route_data.get('is_international', False)
        
        # Calcolo tempo per tratta basato su tipo rotta
        if is_international:
            stop_time = 15  # Più tempo per controlli internazionali
            travel_factor = 1.5  # Viaggi internazionali più lenti
        else:
            stop_time = 5   # Sosta breve per treni nazionali
            travel_factor = 1.0
        
        cumulative_time = 0
        
        for seq, station_id in enumerate(route_data['stations']):
            if seq == 0:
                # Prima stazione: solo partenza
                arrival_offset = None
                departure_offset = 0
            elif seq == len(route_data['stations']) - 1:
                # Ultima stazione: solo arrivo
                cumulative_time += int(base_time * travel_factor)
                arrival_offset = cumulative_time
                departure_offset = None
            else:
                # Stazioni intermedie: arrivo + sosta + partenza
                cumulative_time += int(base_time * travel_factor)
                arrival_offset = cumulative_time
                departure_offset = cumulative_time + stop_time
            
            platform = self._assign_platform(station_id, route_data)
            
            self.cursor.execute("""
                INSERT INTO route_stations (id, route_id, station_id, sequence, 
                                          arrival_offset_min, departure_offset_min, 
                                          platform, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                UniqueValueGenerator.uuid(), route_data['id'], station_id, seq + 1,
                arrival_offset, departure_offset, platform,
                datetime.now(), datetime.now()
            ))
    
    def _assign_platform(self, station_id, route_data):
        """Assegna binario casuale"""
        # Ottieni binari disponibili dal database
        self.cursor.execute("SELECT platforms FROM stations WHERE id = %s", (station_id,))
        result = self.cursor.fetchone()
        
        if result and result[0]:
            # Il campo platforms è già deserializzato come lista Python
            available = result[0] if isinstance(result[0], list) else ["1", "2", "3", "4"]
        else:
            # Fallback per stazioni senza binari definiti
            available = ["1", "2", "3", "4"]
        
        # Strategia binari semplificata
        is_international = route_data.get('is_international', False)
        is_high_speed = any(st in route_data.get('services', []) for st in ['st_frecciarossa', 'st_italo', 'st_tgv'])
        
        if is_international and len(available) > 15:
            preferred = available[-10:]
        elif is_high_speed and len(available) > 8:
            preferred = available[8:18] if len(available) > 18 else available[4:]
        else:
            preferred = available[:8] if len(available) > 8 else available[:4]
        
        return random.choice(preferred if preferred else available)
    
    def _create_services_for_route(self, route_data):
        """Crea servizi per una rotta"""
        departure_times = [time(6, 30), time(8, 15), time(10, 45), time(14, 20), time(17, 30), time(20, 10)]
        
        for service_type_id in route_data['services']:
            # Ottieni IDs necessari
            operator_id = self._get_random_operator()
            train_id = self._get_random_train()
            
            if not operator_id or not train_id:
                continue
            
            for dep_time in departure_times:
                service_id = self._create_train_service(
                    route_data['id'], service_type_id, operator_id, train_id, dep_time
                )
                self._create_trips_for_service(service_id, dep_time)
    
    def _get_random_operator(self):
        """Ottieni operatore casuale"""
        self.cursor.execute("SELECT id FROM railway_operators ORDER BY RANDOM() LIMIT 1")
        result = self.cursor.fetchone()
        return result[0] if result else None
    
    def _get_random_train(self):
        """Ottieni treno casuale"""
        self.cursor.execute("SELECT id FROM trains ORDER BY RANDOM() LIMIT 1")
        result = self.cursor.fetchone()
        return result[0] if result else None
    
    def _create_train_service(self, route_id, service_type_id, operator_id, train_id, dep_time):
        """Crea servizio treno"""
        service_id = UniqueValueGenerator.uuid()
        
        self.cursor.execute("SELECT code FROM service_types WHERE id = %s", (service_type_id,))
        service_code = self.cursor.fetchone()[0]
        
        operates_days = {
            "monday": True, "tuesday": True, "wednesday": True,
            "thursday": True, "friday": True, "saturday": True, "sunday": True
        }
        
        self.cursor.execute("""
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
        
        return service_id
    
    def _create_trips_for_service(self, service_id, departure_time):
        """Crea viaggi per un servizio"""
        start_date = date.today()
        for i in range(30):
            service_date = start_date + timedelta(days=i)
            
            planned_departure = datetime.combine(service_date, departure_time)
            planned_arrival = planned_departure + timedelta(hours=random.randint(2, 8))
            
            delay = random.choices([0, 5, 10, 15, 30, 60], weights=[70, 15, 8, 4, 2, 1])[0]
            status = 'SCHEDULED' if service_date > date.today() else random.choice(['COMPLETED', 'RUNNING'])
            
            self.cursor.execute("""
                INSERT INTO trips (id, train_service_id, service_date, 
                                 planned_departure_time, planned_arrival_time,
                                 status, delay_minutes, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                UniqueValueGenerator.uuid(), service_id, service_date,
                planned_departure, planned_arrival, status, delay,
                datetime.now(), datetime.now()
            ))

class BookingGenerator:
    """Generazione prenotazioni complete"""
    
    def __init__(self, cursor):
        self.cursor = cursor
        self.fare_calculator = FareCalculator(cursor)
    
    def generate_users_and_bookings(self, num_users=500, num_bookings=1500):
        """Genera utenti, prenotazioni, ticket e pagamenti"""
        print(f"👥 Generazione {num_users} utenti e {num_bookings} prenotazioni...")
        
        user_ids = self._create_users(num_users)
        booking_ids = self._create_bookings(user_ids, num_bookings)
        
        print("🎫 Generazione ticket...")
        self._create_tickets(booking_ids)
        
        print("💳 Generazione pagamenti...")
        self._create_payments(booking_ids)
        
        print("🪑 Generazione prenotazioni posti...")
        self._create_seat_reservations(booking_ids)
    
    def _create_users(self, num_users):
        """Crea utenti"""
        user_ids = []
        used_emails = set()
        
        for i in range(num_users):
            user_id = UniqueValueGenerator.uuid()
            
            # Email unica
            for _ in range(10):
                email = fake.email()
                if email not in used_emails:
                    used_emails.add(email)
                    break
            else:
                email = f"user{i}_{int(datetime.now().timestamp())}@example.com"
            
            self.cursor.execute("""
                INSERT INTO users (id, first_name, last_name, email, password, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                user_id, fake.first_name(), fake.last_name(), 
                email, fake.password(), datetime.now(), datetime.now()
            ))
            user_ids.append(user_id)
        
        return user_ids
    
    def _create_bookings(self, user_ids, num_bookings):
        """Crea prenotazioni"""
        booking_ids = []
        
        for i in range(num_bookings):
            user_id = random.choice(user_ids)
            
            # Crea passeggero
            passenger_id = UniqueValueGenerator.uuid()
            self.cursor.execute("""
                INSERT INTO passengers (id, user_id, first_name, last_name, email, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                passenger_id, user_id, fake.first_name(), fake.last_name(),
                fake.email(), datetime.now(), datetime.now()
            ))
            
            # Crea prenotazione
            booking_id = self._create_single_booking(passenger_id, user_id)
            if booking_id:
                booking_ids.append(booking_id)
            
            if (i + 1) % 100 == 0:
                print(f"   📋 {i + 1}/{num_bookings} prenotazioni...")
        
        return booking_ids
    
    def _create_single_booking(self, passenger_id, user_id):
        """Crea singola prenotazione con calcolo tariffa"""
        # Seleziona trip casuale
        self.cursor.execute("""
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
        
        trip_data = self.cursor.fetchone()
        if not trip_data:
            return None
        
        (trip_id, origin_station, dest_station, dep_time, arr_time, 
         service_type_id, train_id, origin_country, dest_country) = trip_data
        
        # Ottieni categoria vagone
        self.cursor.execute("""
            SELECT w.category_id FROM wagons w
            JOIN train_wagons tw ON w.id = tw.wagon_id
            WHERE tw.train_id = %s ORDER BY RANDOM() LIMIT 1
        """, (train_id,))
        
        result = self.cursor.fetchone()
        if not result:
            return None
        
        wagon_category_id = result[0]
        distance = random.randint(50, 800)
        
        # Calcola tariffa
        fare = self.fare_calculator.calculate(
            origin_country, dest_country, distance, service_type_id, wagon_category_id
        )
        
        # Crea prenotazione
        booking_id = UniqueValueGenerator.uuid()
        booking_ref = UniqueValueGenerator.booking_reference(self.cursor)
        
        self.cursor.execute("""
            INSERT INTO bookings (id, booking_reference, user_id, passenger_id,
                                origin_station_id, destination_station_id, departure_date,
                                total_amount, currency, status, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            booking_id, booking_ref, user_id, passenger_id,
            origin_station, dest_station, dep_time.date(),
            fare, 'EUR', 'CONFIRMED', datetime.now(), datetime.now()
        ))
        
        # Crea segmento
        self._create_booking_segment(booking_id, trip_data, distance, fare)
        
        return booking_id
    
    def _create_booking_segment(self, booking_id, trip_data, distance, fare):
        """Crea segmento prenotazione"""
        trip_id, origin_station, dest_station = trip_data[0], trip_data[1], trip_data[2]
        dep_time, arr_time = trip_data[3], trip_data[4]
        
        # Ottieni route stations
        self.cursor.execute("""
            SELECT rs.id FROM route_stations rs
            JOIN train_services ts ON rs.route_id = ts.route_id
            JOIN trips t ON ts.id = t.train_service_id
            WHERE t.id = %s AND rs.station_id = %s
        """, (trip_id, origin_station))
        origin_rs = self.cursor.fetchone()
        
        self.cursor.execute("""
            SELECT rs.id FROM route_stations rs
            JOIN train_services ts ON rs.route_id = ts.route_id
            JOIN trips t ON ts.id = t.train_service_id
            WHERE t.id = %s AND rs.station_id = %s
        """, (trip_id, dest_station))
        dest_rs = self.cursor.fetchone()
        
        if not origin_rs or not dest_rs:
            return
        
        self.cursor.execute("""
            INSERT INTO booking_segments (id, booking_id, trip_id, sequence,
                                        origin_station_id, destination_station_id,
                                        origin_route_station_id, destination_route_station_id,
                                        planned_departure_time, planned_arrival_time,
                                        distance_km, segment_amount, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            UniqueValueGenerator.uuid(), booking_id, trip_id, 1,
            origin_station, dest_station, origin_rs[0], dest_rs[0],
            dep_time, arr_time, distance, fare, datetime.now(), datetime.now()
        ))
    
    def _create_tickets(self, booking_ids):
        """Crea ticket per prenotazioni"""
        for booking_id in booking_ids:
            self.cursor.execute("""
                SELECT b.id, b.passenger_id, bs.id as segment_id, bs.trip_id,
                       bs.origin_station_id, bs.destination_station_id,
                       bs.segment_amount, b.departure_date
                FROM bookings b
                JOIN booking_segments bs ON b.id = bs.booking_id
                WHERE b.id = %s LIMIT 1
            """, (booking_id,))
            
            data = self.cursor.fetchone()
            if not data or len(data) < 8:
                continue
            
            # Ottieni categoria vagone separatamente
            self.cursor.execute("""
                SELECT w.category_id FROM wagons w
                JOIN train_wagons tw ON w.id = tw.wagon_id
                JOIN train_services ts ON tw.train_id = ts.train_id
                JOIN trips t ON ts.id = t.train_service_id
                WHERE t.id = %s LIMIT 1
            """, (data[3],))  # data[3] = trip_id
            
            wagon_result = self.cursor.fetchone()
            if not wagon_result:
                continue
                
            wagon_category_id = wagon_result[0]
            ticket_number = UniqueValueGenerator.ticket_number(self.cursor)
            
            # Estrai i valori dalla tupla esplicitamente
            (booking_id_result, passenger_id, segment_id, trip_id,
             origin_station_id, destination_station_id, fare_amount, 
             service_date) = data
            
            self.cursor.execute("""
                INSERT INTO tickets (id, ticket_number, booking_id, booking_segment_id,
                                   passenger_id, trip_id, origin_station_id, destination_station_id,
                                   wagon_category_id, fare_amount, currency, status,
                                   issued_at, service_date, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                UniqueValueGenerator.uuid(), ticket_number, booking_id_result, segment_id,
                passenger_id, trip_id, origin_station_id, destination_station_id,
                wagon_category_id, fare_amount, 'EUR', 'VALID',
                datetime.now(), service_date, datetime.now(), datetime.now()
            ))
    
    def _create_payments(self, booking_ids):
        """Crea pagamenti"""
        methods = ['CREDIT_CARD', 'DEBIT_CARD', 'PAYPAL', 'SEPA_DIRECT_DEBIT']
        
        for booking_id in booking_ids:
            self.cursor.execute("SELECT total_amount FROM bookings WHERE id = %s", (booking_id,))
            result = self.cursor.fetchone()
            if not result:
                continue
            
            amount = result[0]
            status = random.choices(['COMPLETED', 'PENDING', 'FAILED'], weights=[95, 3, 2])[0]
            paid_at = datetime.now() if status == 'COMPLETED' else None
            transaction_ref = f"TXN{random.randint(100000000, 999999999)}" if status == 'COMPLETED' else None
            
            self.cursor.execute("""
                INSERT INTO payments (id, booking_id, amount, currency, payment_method,
                                    status, transaction_ref, paid_at, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                UniqueValueGenerator.uuid(), booking_id, amount, 'EUR', 
                random.choice(methods), status, transaction_ref, paid_at,
                datetime.now(), datetime.now()
            ))
    
    def _create_seat_reservations(self, booking_ids):
        """Crea prenotazioni posti (60% delle prenotazioni)"""
        selected_bookings = random.sample(booking_ids, min(len(booking_ids), int(len(booking_ids) * 0.6)))
        
        for booking_id in selected_bookings:
            self.cursor.execute("""
                SELECT bs.id, bs.trip_id, bs.origin_route_station_id, bs.destination_route_station_id,
                       b.passenger_id, ts.train_id
                FROM booking_segments bs
                JOIN bookings b ON bs.booking_id = b.id
                JOIN trips t ON bs.trip_id = t.id
                JOIN train_services ts ON t.train_service_id = ts.id
                WHERE bs.booking_id = %s
            """, (booking_id,))
            
            data = self.cursor.fetchone()
            if not data:
                continue
            
            segment_id, trip_id, origin_rs, dest_rs, passenger_id, train_id = data
            
            # Trova posto disponibile
            self.cursor.execute("""
                SELECT ws.id FROM wagon_seats ws
                JOIN train_wagons tw ON ws.wagon_id = tw.wagon_id
                WHERE tw.train_id = %s
                AND ws.id NOT IN (
                    SELECT wagon_seat_id FROM seat_reservations 
                    WHERE trip_id = %s AND wagon_seat_id IS NOT NULL
                )
                ORDER BY RANDOM() LIMIT 1
            """, (train_id, trip_id))
            
            seat_result = self.cursor.fetchone()
            if not seat_result:
                continue
            
            self.cursor.execute("SELECT planned_departure_time FROM trips WHERE id = %s", (trip_id,))
            dep_result = self.cursor.fetchone()
            expires_at = dep_result[0] + timedelta(hours=2) if dep_result else datetime.now() + timedelta(hours=2)
            
            self.cursor.execute("""
                INSERT INTO seat_reservations (id, booking_segment_id, trip_id, wagon_seat_id,
                                             passenger_id, origin_route_station_id, destination_route_station_id,
                                             expires_at, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                UniqueValueGenerator.uuid(), segment_id, trip_id, seat_result[0], 
                passenger_id, origin_rs, dest_rs, expires_at,
                datetime.now(), datetime.now()
            ))

class DatabaseCleaner:
    """Pulizia database"""
    
    def __init__(self, cursor):
        self.cursor = cursor
    
    def clear_all_data(self):
        """Cancella tutti i dati"""
        print("🗑️ Cancellazione dati esistenti...")
        
        tables = [
            'payments', 'tickets', 'seat_reservations', 'fares', 
            'booking_segments', 'bookings', 'passengers', 'users', 
            'trip_station_updates', 'trips', 'service_exceptions',
            'train_services', 'route_stations', 'routes', 'wagon_seats',
            'cabins', 'train_wagons', 'wagons', 'wagon_categories', 
            'trains', 'service_types', 'railway_operators',
            'stations', 'cities', 'countries'
        ]
        
        for table in tables:
            try:
                self.cursor.execute(f"TRUNCATE TABLE {table} CASCADE")
                print(f"   🗑️ {table}")
            except Exception as e:
                print(f"   ⚠️ Errore {table}: {e}")

class RaylixDataGenerator:
    """Generatore principale per il database Raylix"""
    
    def __init__(self, db_config):
        self.db_manager = DatabaseManager(db_config)
        self.static_data = StaticDataLoader.load_all()
    
    def run_full_generation(self, clear_data=True):
        """Esegue la generazione completa"""
        print("🚄 Avvio generazione dati Raylix...")
        
        try:
            self.db_manager.connect()
            cursor = self.db_manager.get_cursor()
            
            if clear_data:
                DatabaseCleaner(cursor).clear_all_data()
            
            # Inserimento dati statici
            StaticDataInserter(cursor, self.static_data).insert_all()
            
            # Generazione strutture dinamiche
            TrainGenerator(cursor, self.static_data).generate_all()
            RouteGenerator(cursor, self.static_data).generate_all()
            
            # Inserimento tariffe
            self._insert_fares(cursor)
            
            # Generazione trip updates
            self._generate_trip_updates(cursor)
            
            # Generazione prenotazioni
            BookingGenerator(cursor).generate_users_and_bookings()
            
            # Eccezioni servizio
            self._generate_service_exceptions(cursor)
            
            print("✅ Generazione completata!")
            
        except Exception as e:
            print(f"❌ Errore durante la generazione: {e}")
            raise
        finally:
            self.db_manager.close()
    
    def _insert_fares(self, cursor):
        """Inserisce tariffe dai dati JSON"""
        print("💰 Inserimento fares...")
        
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
                fare_data['id'], fare_data['origin_country_id'], fare_data['destination_country_id'],
                fare_data['wagon_category_id'], fare_data['service_type_id'], 
                fare_data['distance_min_km'], fare_data['distance_max_km'],
                Decimal(str(fare_data['base_fare'])), Decimal(str(fare_data['fare_per_km'])),
                fare_data['is_cross_border'], Decimal(str(fare_data.get('international_supplement', 0.00))), 
                'EUR', datetime.now(), datetime.now() + timedelta(days=365),
                datetime.now(), datetime.now()
            ))
    
    def _generate_trip_updates(self, cursor):
        """Genera aggiornamenti stazioni viaggi"""
        print("📊 Generazione trip station updates...")
        
        cursor.execute("""
            SELECT t.id, t.service_date, t.planned_departure_time, 
                   t.delay_minutes, t.status, ts.route_id
            FROM trips t
            JOIN train_services ts ON t.train_service_id = ts.id
            ORDER BY t.service_date, t.planned_departure_time
        """)
        
        for trip_id, service_date, planned_dep, delay_minutes, status, route_id in cursor.fetchall():
            cursor.execute("""
                SELECT rs.id, rs.station_id, rs.sequence, rs.arrival_offset_min, rs.departure_offset_min
                FROM route_stations rs WHERE rs.route_id = %s ORDER BY rs.sequence
            """, (route_id,))
            
            for route_station_id, station_id, sequence, arrival_offset, departure_offset in cursor.fetchall():
                # Calcola orari pianificati: NULL solo se offset è effettivamente NULL
                planned_arrival = planned_dep + timedelta(minutes=arrival_offset) if arrival_offset is not None else None
                planned_departure = planned_dep + timedelta(minutes=departure_offset) if departure_offset is not None else None
                
                actual_arrival = actual_departure = station_delay = None
                
                if status in ['COMPLETED', 'RUNNING'] and service_date <= date.today():
                    base_delay = delay_minutes or 0
                    station_delay = max(0, base_delay + (sequence - 1) * 2 + random.choice([0, 2, 5]))
                    
                    # Calcola orari effettivi solo dove ci sono orari pianificati
                    if planned_arrival is not None:
                        actual_arrival = planned_arrival + timedelta(minutes=station_delay)
                    if planned_departure is not None:
                        actual_departure = planned_departure + timedelta(minutes=station_delay)
                
                cursor.execute("""
                    INSERT INTO trip_station_updates (
                        id, trip_id, route_station_id, planned_arrival, planned_departure,
                        actual_arrival, actual_departure, delay_minutes, updated_at, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (trip_id, route_station_id) DO UPDATE SET
                        actual_arrival = EXCLUDED.actual_arrival,
                        actual_departure = EXCLUDED.actual_departure,
                        delay_minutes = EXCLUDED.delay_minutes,
                        updated_at = EXCLUDED.updated_at
                """, (
                    UniqueValueGenerator.uuid(), trip_id, route_station_id, 
                    planned_arrival, planned_departure, actual_arrival, actual_departure, 
                    station_delay, datetime.now(), datetime.now()
                ))
    
    def _generate_service_exceptions(self, cursor):
        """Genera eccezioni del servizio"""
        print("⚠️ Inserimento service exceptions...")
        
        cursor.execute("SELECT id FROM train_services ORDER BY RANDOM() LIMIT 10")
        service_ids = [row[0] for row in cursor.fetchall()]
        
        exceptions = [
            ('2025-12-25', 'Giorno di Natale', False),
            ('2025-01-01', 'Capodanno', False),
            ('2025-05-01', 'Festa del Lavoro', False),
            ('2025-03-15', 'Sciopero trasporti', False),
            ('2025-12-24', 'Vigilia di Natale - Servizio ridotto', True)
        ]
        
        for i, (exc_date, reason, is_running) in enumerate(exceptions):
            if i < len(service_ids):
                cursor.execute("""
                    INSERT INTO service_exceptions (id, train_service_id, exception_date, 
                                                  is_running, reason, created_at, updated_at)
                    VALUES (%s, %s, %s::date, %s, %s, %s, %s)
                    ON CONFLICT (train_service_id, exception_date) DO NOTHING
                """, (
                    UniqueValueGenerator.uuid(), service_ids[i], exc_date,
                    is_running, reason, datetime.now(), datetime.now()
                ))

def main():
    """Entry point"""
    DB_CONFIG = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'database': os.getenv('DB_NAME', 'raylix'),
        'user': os.getenv('DB_USER', 'postgres'), 
        'password': os.getenv('DB_PASSWORD', 'postgres'),
        'port': os.getenv('DB_PORT', '5432')
    }
    
    print("🚄 Raylix Data Generator")
    print("=" * 40)
    
    clear_data = '--no-clear' not in sys.argv
    
    generator = RaylixDataGenerator(DB_CONFIG)
    generator.run_full_generation(clear_data=clear_data)

if __name__ == "__main__":
    main()
