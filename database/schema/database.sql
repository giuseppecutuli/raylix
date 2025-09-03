-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- =========================
-- ENUM TYPES
-- =========================
CREATE TYPE trip_status AS ENUM ('SCHEDULED','RUNNING','COMPLETED','CANCELED','DELAYED');
CREATE TYPE booking_status AS ENUM ('PENDING','CONFIRMED','CANCELED','REFUNDED');
CREATE TYPE ticket_status AS ENUM ('VALID','USED','CANCELED','REFUNDED');
CREATE TYPE payment_status AS ENUM ('PENDING','COMPLETED','FAILED','REFUNDED');
CREATE TYPE seat_type AS ENUM (
  'WINDOW','AISLE','MIDDLE','TABLE',
  'COUCHETTE_LOWER','COUCHETTE_MIDDLE','COUCHETTE_UPPER',
  'SLEEPER_SINGLE','SLEEPER_DOUBLE'
);
CREATE TYPE seat_orientation AS ENUM ('FORWARD','BACKWARD','FACING_TABLE');
CREATE TYPE cabin_type AS ENUM ('COUCHETTE_4','COUCHETTE_6','SLEEPER_SINGLE','SLEEPER_DOUBLE');
CREATE TYPE currency_code AS ENUM (
  'EUR','GBP','CHF','SEK','NOK','DKK','PLN','CZK','HUF','RON','BGN','HRK','USD'
);
CREATE TYPE payment_method AS ENUM (
  'CREDIT_CARD','DEBIT_CARD','PAYPAL','SEPA_DIRECT_DEBIT',
  'BANCONTACT','IDEAL','SOFORT','GIROPAY','APPLE_PAY','GOOGLE_PAY'
);

-- =========================
-- CORE TABLES
-- =========================

CREATE TABLE countries (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  iso_code VARCHAR(3) UNIQUE NOT NULL,
  created_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE railway_operators (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  country_id UUID REFERENCES countries(id),
  code VARCHAR(10) UNIQUE NOT NULL,
  website TEXT,
  created_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX idx_railway_operators_country_id ON railway_operators(country_id);

CREATE TABLE cities (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  country_id UUID REFERENCES countries(id),
  latitude DOUBLE PRECISION,
  longitude DOUBLE PRECISION,
  created_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX idx_cities_country_id ON cities(country_id);

CREATE TABLE stations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  city_id UUID REFERENCES cities(id),
  latitude DOUBLE PRECISION,
  longitude DOUBLE PRECISION,
  platforms JSONB,
  created_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX idx_stations_city_id ON stations(city_id);
CREATE INDEX idx_stations_latlong ON stations(latitude, longitude);
CREATE INDEX idx_stations_name ON stations(name);
CREATE INDEX idx_stations_platforms ON stations USING gin(platforms);

CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  first_name TEXT NOT NULL,
  last_name TEXT NOT NULL,
  email TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE passengers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  first_name TEXT NOT NULL,
  last_name TEXT NOT NULL,
  email TEXT,
  phone TEXT,
  document_number TEXT,
  created_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX idx_passengers_user_id ON passengers(user_id);
CREATE INDEX idx_passengers_email ON passengers(email);

CREATE TABLE service_types (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  code VARCHAR(20) UNIQUE NOT NULL,
  requires_seat_assignment BOOLEAN DEFAULT TRUE NOT NULL,
  allows_standing BOOLEAN DEFAULT FALSE NOT NULL,
  created_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE wagon_categories (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE wagons (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  code VARCHAR(20) UNIQUE NOT NULL,
  category_id UUID REFERENCES wagon_categories(id),
  total_seats INTEGER,
  total_rows INTEGER,
  seats_per_row INTEGER,
  layout_pattern TEXT,
  row_numbering_start INTEGER DEFAULT 1 NOT NULL,
  created_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE cabins (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  wagon_id UUID REFERENCES wagons(id),
  cabin_number TEXT NOT NULL,
  cabin_type cabin_type NOT NULL,
  total_beds INTEGER NOT NULL,
  has_private_bathroom BOOLEAN DEFAULT FALSE NOT NULL,
  created_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL,
  UNIQUE(wagon_id, cabin_number)
);

CREATE TABLE wagon_seats (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  wagon_id UUID REFERENCES wagons(id),
  cabin_id UUID REFERENCES cabins(id),
  seat_number TEXT NOT NULL,
  seat_type seat_type NOT NULL,
  seat_orientation seat_orientation DEFAULT 'FORWARD' NOT NULL,
  row_number INTEGER,
  column_letter TEXT,
  is_accessible BOOLEAN DEFAULT FALSE NOT NULL,
  created_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL,
  UNIQUE(wagon_id, seat_number)
);
CREATE INDEX idx_wagon_seats_wagon_seat_type ON wagon_seats(wagon_id, seat_type);
CREATE INDEX idx_wagon_seats_cabin_id ON wagon_seats(cabin_id);

-- =========================
-- TRAINS & ROUTES
-- =========================

CREATE TABLE trains (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  code VARCHAR(20) UNIQUE NOT NULL,
  model TEXT NOT NULL,
  is_ship BOOLEAN DEFAULT FALSE NOT NULL,
  created_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE train_wagons (
  train_id UUID REFERENCES trains(id),
  wagon_id UUID REFERENCES wagons(id),
  position INTEGER NOT NULL,
  created_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL,
  PRIMARY KEY(train_id, wagon_id),
  UNIQUE(train_id, position)
);

CREATE TABLE routes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  description TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE route_stations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  route_id UUID REFERENCES routes(id),
  station_id UUID REFERENCES stations(id),
  sequence INTEGER NOT NULL,
  arrival_offset_min INTEGER,
  departure_offset_min INTEGER,
  platform TEXT,
  created_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL,
  UNIQUE(route_id, sequence),
  UNIQUE(route_id, station_id)
);
CREATE INDEX idx_route_stations_station_platform ON route_stations(station_id, platform);

-- =========================
-- SERVICES & TRIPS
-- =========================

CREATE TABLE train_services (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  train_id UUID REFERENCES trains(id),
  route_id UUID REFERENCES routes(id),
  service_type_id UUID REFERENCES service_types(id),
  operator_id UUID REFERENCES railway_operators(id),
  departure_time TIME NOT NULL,
  service_name TEXT,
  operates_days JSONB NOT NULL,
  valid_from DATE NOT NULL,
  valid_to DATE NOT NULL,
  cabins_enabled BOOLEAN DEFAULT FALSE NOT NULL,
  created_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX idx_train_services_operator_id ON train_services(operator_id);
CREATE INDEX idx_train_services_service_type_id ON train_services(service_type_id);
CREATE INDEX idx_train_services_route_departure ON train_services(route_id, departure_time);
CREATE INDEX idx_train_services_operator_service_type ON train_services(operator_id, service_type_id);
CREATE INDEX idx_train_services_valid ON train_services(valid_from, valid_to);

CREATE TABLE service_exceptions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  train_service_id UUID REFERENCES train_services(id),
  exception_date DATE NOT NULL,
  is_running BOOLEAN NOT NULL,
  reason TEXT,
  created_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL,
  UNIQUE(train_service_id, exception_date)
);
CREATE INDEX idx_service_exceptions_date ON service_exceptions(exception_date);

CREATE TABLE trips (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  train_service_id UUID REFERENCES train_services(id),
  service_date DATE NOT NULL,
  planned_departure_time TIMESTAMPTZ NOT NULL,
  planned_arrival_time TIMESTAMPTZ NOT NULL,
  status trip_status DEFAULT 'SCHEDULED' NOT NULL,
  delay_minutes INTEGER DEFAULT 0 NOT NULL,
  created_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL,
  UNIQUE(train_service_id, service_date)
);
CREATE INDEX idx_trips_service_date_status ON trips(service_date, status);
CREATE INDEX idx_trips_service_date_delay ON trips(service_date, delay_minutes);
CREATE INDEX idx_trips_planned_departure_time ON trips(planned_departure_time);
CREATE INDEX idx_trips_status_departure_time ON trips(status, planned_departure_time);

CREATE TABLE trip_station_updates (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  trip_id UUID REFERENCES trips(id),
  route_station_id UUID REFERENCES route_stations(id),
  planned_arrival TIMESTAMPTZ,
  planned_departure TIMESTAMPTZ,
  actual_arrival TIMESTAMPTZ,
  actual_departure TIMESTAMPTZ,
  delay_minutes INTEGER,
  updated_at TIMESTAMPTZ NOT NULL,
  created_at TIMESTAMPTZ NOT NULL,
  UNIQUE(trip_id, route_station_id)
);
CREATE INDEX idx_trip_station_updates_trip ON trip_station_updates(trip_id);
CREATE INDEX idx_trip_station_updates_updated ON trip_station_updates(updated_at);
CREATE INDEX idx_trip_station_updates_trip_updated ON trip_station_updates(trip_id, updated_at);
CREATE INDEX idx_trip_station_updates_delay_updated ON trip_station_updates(delay_minutes, updated_at);

-- =========================
-- BOOKINGS, SEGMENTS & FARES
-- =========================

CREATE TABLE bookings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  booking_reference VARCHAR(20) UNIQUE NOT NULL,
  user_id UUID REFERENCES users(id),
  passenger_id UUID REFERENCES passengers(id),
  origin_station_id UUID REFERENCES stations(id),
  destination_station_id UUID REFERENCES stations(id),
  departure_date DATE NOT NULL,
  total_amount NUMERIC,
  currency currency_code DEFAULT 'EUR' NOT NULL,
  status booking_status DEFAULT 'PENDING' NOT NULL,
  created_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX idx_bookings_user_id ON bookings(user_id);
CREATE INDEX idx_bookings_passenger_id ON bookings(passenger_id);
CREATE INDEX idx_bookings_departure_date ON bookings(departure_date);
CREATE INDEX idx_bookings_origin_dest ON bookings(origin_station_id, destination_station_id);
CREATE INDEX idx_bookings_user_created ON bookings(user_id, created_at);
CREATE INDEX idx_bookings_status_created ON bookings(status, created_at);
CREATE INDEX idx_bookings_departure_status ON bookings(departure_date, status);

CREATE TABLE booking_segments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  booking_id UUID REFERENCES bookings(id),
  trip_id UUID REFERENCES trips(id),
  sequence INTEGER NOT NULL,
  origin_station_id UUID REFERENCES stations(id),
  destination_station_id UUID REFERENCES stations(id),
  origin_route_station_id UUID REFERENCES route_stations(id),
  destination_route_station_id UUID REFERENCES route_stations(id),
  planned_departure_time TIMESTAMPTZ NOT NULL,
  planned_arrival_time TIMESTAMPTZ NOT NULL,
  connection_time_minutes INTEGER,
  platform_departure TEXT,
  platform_arrival TEXT,
  distance_km NUMERIC NOT NULL,
  segment_amount NUMERIC NOT NULL,
  created_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL,
  UNIQUE(booking_id, sequence)
);
CREATE INDEX idx_booking_segments_trip_id ON booking_segments(trip_id);
CREATE INDEX idx_booking_segments_booking_id ON booking_segments(booking_id);
CREATE INDEX idx_booking_segments_departure_time ON booking_segments(planned_departure_time);

CREATE TABLE fares (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  route_id UUID REFERENCES routes(id),
  operator_id UUID REFERENCES railway_operators(id),
  origin_country_id UUID REFERENCES countries(id),
  destination_country_id UUID REFERENCES countries(id),
  wagon_category_id UUID REFERENCES wagon_categories(id),
  service_type_id UUID REFERENCES service_types(id),
  distance_min_km INTEGER NOT NULL,
  distance_max_km INTEGER NOT NULL,
  base_fare NUMERIC NOT NULL,
  fare_per_km NUMERIC NOT NULL,
  is_cross_border BOOLEAN DEFAULT FALSE NOT NULL,
  international_supplement NUMERIC,
  currency currency_code DEFAULT 'EUR' NOT NULL,
  valid_from TIMESTAMPTZ NOT NULL,
  valid_to TIMESTAMPTZ NOT NULL,
  created_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX idx_fares_route_operator_category_service ON fares(route_id, operator_id, wagon_category_id, service_type_id);
CREATE INDEX idx_fares_operator_origin_dest ON fares(operator_id, origin_country_id, destination_country_id);
CREATE INDEX idx_fares_valid ON fares(valid_from, valid_to);
CREATE INDEX idx_fares_service_type ON fares(service_type_id);

-- =========================
-- RESERVATIONS, TICKETS, PAYMENTS
-- =========================

CREATE TABLE seat_reservations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  booking_segment_id UUID REFERENCES booking_segments(id) UNIQUE,
  trip_id UUID REFERENCES trips(id),
  wagon_seat_id UUID REFERENCES wagon_seats(id),
  passenger_id UUID REFERENCES passengers(id),
  origin_route_station_id UUID REFERENCES route_stations(id),
  destination_route_station_id UUID REFERENCES route_stations(id),
  expires_at TIMESTAMPTZ NOT NULL,
  created_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX idx_seat_reservations_trip_wagon_seat ON seat_reservations(trip_id, wagon_seat_id);
CREATE INDEX idx_seat_reservations_passenger ON seat_reservations(passenger_id);
CREATE INDEX idx_seat_reservations_expires_at ON seat_reservations(expires_at);
CREATE INDEX idx_seat_reservations_trip_expires ON seat_reservations(trip_id, expires_at);

CREATE TABLE tickets (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  ticket_number VARCHAR(30) UNIQUE NOT NULL,
  booking_id UUID REFERENCES bookings(id),
  booking_segment_id UUID REFERENCES booking_segments(id) UNIQUE,
  passenger_id UUID REFERENCES passengers(id),
  trip_id UUID REFERENCES trips(id),
  origin_station_id UUID REFERENCES stations(id),
  destination_station_id UUID REFERENCES stations(id),
  wagon_category_id UUID REFERENCES wagon_categories(id),
  seat_reservation_id UUID REFERENCES seat_reservations(id),
  fare_amount NUMERIC NOT NULL,
  currency currency_code DEFAULT 'EUR' NOT NULL,
  status ticket_status DEFAULT 'VALID' NOT NULL,
  issued_at TIMESTAMPTZ NOT NULL,
  service_date DATE NOT NULL,
  created_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX idx_tickets_booking_id ON tickets(booking_id);
CREATE INDEX idx_tickets_trip_id ON tickets(trip_id);
CREATE INDEX idx_tickets_passenger_id ON tickets(passenger_id);
CREATE INDEX idx_tickets_service_date ON tickets(service_date);
CREATE INDEX idx_tickets_service_date_trip ON tickets(service_date, trip_id);
CREATE INDEX idx_tickets_passenger_date ON tickets(passenger_id, service_date);
CREATE INDEX idx_tickets_status_date ON tickets(status, service_date);

CREATE TABLE payments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  booking_id UUID REFERENCES bookings(id),
  amount NUMERIC NOT NULL,
  currency currency_code DEFAULT 'EUR' NOT NULL,
  payment_method payment_method NOT NULL,
  status payment_status DEFAULT 'PENDING' NOT NULL,
  transaction_ref TEXT,
  paid_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX idx_payments_booking_id ON payments(booking_id);
