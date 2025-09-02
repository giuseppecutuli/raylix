CREATE TYPE "trip_status" AS ENUM (
  'SCHEDULED',
  'RUNNING',
  'COMPLETED',
  'CANCELED',
  'DELAYED'
);

CREATE TYPE "booking_status" AS ENUM (
  'PENDING',
  'CONFIRMED',
  'CANCELED',
  'REFUNDED'
);

CREATE TYPE "ticket_status" AS ENUM (
  'VALID',
  'USED',
  'CANCELED',
  'REFUNDED'
);

CREATE TYPE "payment_status" AS ENUM (
  'PENDING',
  'COMPLETED',
  'FAILED',
  'REFUNDED'
);

CREATE TYPE "seat_type" AS ENUM (
  'WINDOW',
  'AISLE',
  'MIDDLE',
  'TABLE',
  'COUCHETTE_LOWER',
  'COUCHETTE_MIDDLE',
  'COUCHETTE_UPPER',
  'SLEEPER_SINGLE',
  'SLEEPER_DOUBLE'
);

CREATE TYPE "seat_orientation" AS ENUM (
  'FORWARD',
  'BACKWARD',
  'FACING_TABLE'
);

CREATE TYPE "cabin_type" AS ENUM (
  'COUCHETTE_4',
  'COUCHETTE_6',
  'SLEEPER_SINGLE',
  'SLEEPER_DOUBLE'
);

CREATE TYPE "currency_code" AS ENUM (
  'EUR',
  'GBP',
  'CHF',
  'SEK',
  'NOK',
  'DKK',
  'PLN',
  'CZK',
  'HUF',
  'RON',
  'BGN',
  'HRK',
  'USD'
);

CREATE TYPE "payment_method" AS ENUM (
  'CREDIT_CARD',
  'DEBIT_CARD',
  'PAYPAL',
  'SEPA_DIRECT_DEBIT',
  'BANCONTACT',
  'IDEAL',
  'SOFORT',
  'GIROPAY',
  'APPLE_PAY',
  'GOOGLE_PAY'
);

CREATE TABLE "countries" (
  "id" string PRIMARY KEY,
  "name" string,
  "iso_code" string UNIQUE,
  "created_at" datetime,
  "updated_at" datetime
);

CREATE TABLE "railway_operators" (
  "id" string PRIMARY KEY,
  "name" string,
  "country_id" string,
  "code" string UNIQUE,
  "website" string,
  "created_at" datetime,
  "updated_at" datetime
);

CREATE TABLE "cities" (
  "id" string PRIMARY KEY,
  "name" string,
  "country_id" string,
  "latitude" double,
  "longitude" double,
  "created_at" datetime,
  "updated_at" datetime
);

CREATE TABLE "stations" (
  "id" string PRIMARY KEY,
  "name" string,
  "city_id" string,
  "latitude" double,
  "longitude" double,
  "created_at" datetime,
  "updated_at" datetime
);

CREATE TABLE "users" (
  "id" string PRIMARY KEY,
  "first_name" string,
  "last_name" string,
  "email" string UNIQUE,
  "password" string,
  "created_at" datetime,
  "updated_at" datetime
);

CREATE TABLE "passengers" (
  "id" string PRIMARY KEY,
  "user_id" string,
  "first_name" string,
  "last_name" string,
  "email" string,
  "phone" string,
  "document_number" string,
  "created_at" datetime,
  "updated_at" datetime
);

CREATE TABLE "service_types" (
  "id" string PRIMARY KEY,
  "name" string,
  "code" string UNIQUE,
  "requires_seat_assignment" bool DEFAULT true,
  "allows_standing" bool DEFAULT false,
  "created_at" datetime,
  "updated_at" datetime
);

CREATE TABLE "wagon_categories" (
  "id" string PRIMARY KEY,
  "name" string,
  "created_at" datetime,
  "updated_at" datetime
);

CREATE TABLE "wagons" (
  "id" string PRIMARY KEY,
  "code" string UNIQUE,
  "category_id" string,
  "total_seats" integer,
  "total_rows" integer,
  "seats_per_row" integer,
  "layout_pattern" string,
  "row_numbering_start" integer DEFAULT 1,
  "created_at" datetime,
  "updated_at" datetime
);

CREATE TABLE "cabins" (
  "id" string PRIMARY KEY,
  "wagon_id" string,
  "cabin_number" string,
  "cabin_type" cabin_type,
  "total_beds" integer,
  "has_private_bathroom" bool DEFAULT false,
  "created_at" datetime,
  "updated_at" datetime
);

CREATE TABLE "wagon_seats" (
  "id" string PRIMARY KEY,
  "wagon_id" string,
  "cabin_id" string,
  "seat_number" string,
  "seat_type" seat_type,
  "seat_orientation" seat_orientation DEFAULT 'FORWARD',
  "row_number" integer,
  "column_letter" string,
  "is_accessible" bool DEFAULT false,
  "created_at" datetime,
  "updated_at" datetime
);

CREATE TABLE "trains" (
  "id" string PRIMARY KEY,
  "code" string UNIQUE,
  "model" string,
  "is_ship" bool DEFAULT false,
  "created_at" datetime,
  "updated_at" datetime
);

CREATE TABLE "train_wagons" (
  "train_id" string,
  "wagon_id" string,
  "position" integer,
  "created_at" datetime,
  "updated_at" datetime,
  PRIMARY KEY ("train_id", "wagon_id")
);

CREATE TABLE "routes" (
  "id" string PRIMARY KEY,
  "name" string,
  "description" string,
  "created_at" datetime,
  "updated_at" datetime
);

CREATE TABLE "route_stations" (
  "id" string PRIMARY KEY,
  "route_id" string,
  "station_id" string,
  "sequence" integer,
  "arrival_offset_min" integer,
  "departure_offset_min" integer,
  "created_at" datetime,
  "updated_at" datetime
);

CREATE TABLE "train_services" (
  "id" string PRIMARY KEY,
  "train_id" string,
  "route_id" string,
  "service_type_id" string,
  "operator_id" string,
  "departure_time" time,
  "service_name" string,
  "operates_days" jsonb,
  "valid_from" date,
  "valid_to" date,
  "cabins_enabled" bool DEFAULT false,
  "created_at" datetime,
  "updated_at" datetime
);

CREATE TABLE "service_exceptions" (
  "id" string PRIMARY KEY,
  "train_service_id" string,
  "exception_date" date,
  "is_running" bool,
  "reason" string,
  "created_at" datetime,
  "updated_at" datetime
);

CREATE TABLE "trips" (
  "id" string PRIMARY KEY,
  "train_service_id" string,
  "service_date" date,
  "planned_departure_time" datetime,
  "planned_arrival_time" datetime,
  "status" trip_status DEFAULT 'SCHEDULED',
  "delay_minutes" integer DEFAULT 0,
  "created_at" datetime,
  "updated_at" datetime
);

CREATE TABLE "trip_station_updates" (
  "id" string PRIMARY KEY,
  "trip_id" string,
  "route_station_id" string,
  "planned_arrival" datetime,
  "planned_departure" datetime,
  "actual_arrival" datetime,
  "actual_departure" datetime,
  "delay_minutes" integer,
  "platform_change" string,
  "updated_at" datetime,
  "created_at" datetime
);

CREATE TABLE "bookings" (
  "id" string PRIMARY KEY,
  "booking_reference" string UNIQUE,
  "user_id" string,
  "passenger_id" string,
  "origin_station_id" string,
  "destination_station_id" string,
  "departure_date" date,
  "total_amount" decimal,
  "currency" currency_code DEFAULT 'EUR',
  "status" booking_status DEFAULT 'PENDING',
  "created_at" datetime,
  "updated_at" datetime
);

CREATE TABLE "booking_segments" (
  "id" string PRIMARY KEY,
  "booking_id" string,
  "trip_id" string,
  "sequence" integer,
  "origin_station_id" string,
  "destination_station_id" string,
  "origin_route_station_id" string,
  "destination_route_station_id" string,
  "planned_departure_time" datetime,
  "planned_arrival_time" datetime,
  "connection_time_minutes" integer,
  "platform_departure" string,
  "platform_arrival" string,
  "distance_km" decimal,
  "segment_amount" decimal,
  "created_at" datetime,
  "updated_at" datetime
);

CREATE TABLE "fares" (
  "id" string PRIMARY KEY,
  "route_id" string,
  "operator_id" string,
  "origin_country_id" string,
  "destination_country_id" string,
  "wagon_category_id" string,
  "service_type_id" string,
  "distance_min_km" integer,
  "distance_max_km" integer,
  "base_fare" decimal,
  "fare_per_km" decimal,
  "is_cross_border" bool DEFAULT false,
  "international_supplement" decimal,
  "currency" currency_code DEFAULT 'EUR',
  "valid_from" datetime,
  "valid_to" datetime,
  "created_at" datetime,
  "updated_at" datetime
);

CREATE TABLE "seat_reservations" (
  "id" string PRIMARY KEY,
  "booking_segment_id" string,
  "trip_id" string,
  "wagon_seat_id" string,
  "passenger_id" string,
  "origin_route_station_id" string,
  "destination_route_station_id" string,
  "expires_at" datetime,
  "created_at" datetime,
  "updated_at" datetime
);

CREATE TABLE "tickets" (
  "id" string PRIMARY KEY,
  "ticket_number" string UNIQUE,
  "booking_id" string,
  "booking_segment_id" string,
  "passenger_id" string,
  "trip_id" string,
  "origin_station_id" string,
  "destination_station_id" string,
  "wagon_category_id" string,
  "seat_reservation_id" string,
  "fare_amount" decimal,
  "currency" currency_code DEFAULT 'EUR',
  "status" ticket_status DEFAULT 'VALID',
  "issued_at" datetime,
  "service_date" date,
  "created_at" datetime,
  "updated_at" datetime
);

CREATE TABLE "payments" (
  "id" string PRIMARY KEY,
  "booking_id" string,
  "amount" decimal,
  "currency" currency_code DEFAULT 'EUR',
  "payment_method" payment_method,
  "status" payment_status DEFAULT 'PENDING',
  "transaction_ref" string,
  "paid_at" datetime,
  "created_at" datetime,
  "updated_at" datetime
);

CREATE INDEX ON "railway_operators" ("country_id");

CREATE INDEX ON "cities" ("country_id");

CREATE INDEX ON "stations" ("city_id");

CREATE INDEX ON "stations" ("latitude", "longitude");

CREATE INDEX ON "stations" ("name");

CREATE INDEX ON "passengers" ("user_id");

CREATE INDEX ON "passengers" ("email");

CREATE UNIQUE INDEX ON "cabins" ("wagon_id", "cabin_number");

CREATE UNIQUE INDEX ON "wagon_seats" ("wagon_id", "seat_number");

CREATE INDEX ON "wagon_seats" ("wagon_id", "seat_type");

CREATE INDEX ON "wagon_seats" ("cabin_id");

CREATE UNIQUE INDEX ON "train_wagons" ("train_id", "position");

CREATE UNIQUE INDEX ON "route_stations" ("route_id", "sequence");

CREATE UNIQUE INDEX ON "route_stations" ("route_id", "station_id");

CREATE INDEX ON "train_services" ("operator_id");

CREATE INDEX ON "train_services" ("service_type_id");

CREATE INDEX ON "train_services" ("route_id", "departure_time");

CREATE INDEX ON "train_services" ("operator_id", "service_type_id");

CREATE INDEX ON "train_services" ("valid_from", "valid_to");

CREATE UNIQUE INDEX ON "service_exceptions" ("train_service_id", "exception_date");

CREATE INDEX ON "service_exceptions" ("exception_date");

CREATE UNIQUE INDEX ON "trips" ("train_service_id", "service_date");

CREATE INDEX ON "trips" ("service_date", "status");

CREATE INDEX ON "trips" ("service_date", "delay_minutes");

CREATE INDEX ON "trips" ("planned_departure_time");

CREATE INDEX ON "trips" ("status", "planned_departure_time");

CREATE UNIQUE INDEX ON "trip_station_updates" ("trip_id", "route_station_id");

CREATE INDEX ON "trip_station_updates" ("trip_id");

CREATE INDEX ON "trip_station_updates" ("updated_at");

CREATE INDEX ON "trip_station_updates" ("trip_id", "updated_at");

CREATE INDEX ON "trip_station_updates" ("delay_minutes", "updated_at");

CREATE INDEX ON "bookings" ("user_id");

CREATE INDEX ON "bookings" ("passenger_id");

CREATE INDEX ON "bookings" ("booking_reference");

CREATE INDEX ON "bookings" ("departure_date");

CREATE INDEX ON "bookings" ("origin_station_id", "destination_station_id");

CREATE INDEX ON "bookings" ("user_id", "created_at");

CREATE INDEX ON "bookings" ("status", "created_at");

CREATE INDEX ON "bookings" ("departure_date", "status");

CREATE UNIQUE INDEX ON "booking_segments" ("booking_id", "sequence");

CREATE INDEX ON "booking_segments" ("trip_id");

CREATE INDEX ON "booking_segments" ("booking_id");

CREATE INDEX ON "booking_segments" ("planned_departure_time");

CREATE INDEX ON "fares" ("route_id", "operator_id", "wagon_category_id", "service_type_id");

CREATE INDEX ON "fares" ("operator_id", "origin_country_id", "destination_country_id");

CREATE INDEX ON "fares" ("valid_from", "valid_to");

CREATE INDEX ON "fares" ("service_type_id");

CREATE UNIQUE INDEX ON "seat_reservations" ("booking_segment_id");

CREATE INDEX ON "seat_reservations" ("trip_id", "wagon_seat_id");

CREATE INDEX ON "seat_reservations" ("passenger_id");

CREATE INDEX ON "seat_reservations" ("expires_at");

CREATE INDEX ON "seat_reservations" ("trip_id", "expires_at");

CREATE INDEX ON "tickets" ("booking_id");

CREATE UNIQUE INDEX ON "tickets" ("booking_segment_id");

CREATE INDEX ON "tickets" ("trip_id");

CREATE INDEX ON "tickets" ("passenger_id");

CREATE INDEX ON "tickets" ("service_date");

CREATE INDEX ON "tickets" ("ticket_number");

CREATE INDEX ON "tickets" ("service_date", "trip_id");

CREATE INDEX ON "tickets" ("passenger_id", "service_date");

CREATE INDEX ON "tickets" ("status", "service_date");

CREATE INDEX ON "payments" ("booking_id");

ALTER TABLE "railway_operators" ADD FOREIGN KEY ("country_id") REFERENCES "countries" ("id");

ALTER TABLE "cities" ADD FOREIGN KEY ("country_id") REFERENCES "countries" ("id");

ALTER TABLE "stations" ADD FOREIGN KEY ("city_id") REFERENCES "cities" ("id");

ALTER TABLE "passengers" ADD FOREIGN KEY ("user_id") REFERENCES "users" ("id");

ALTER TABLE "wagons" ADD FOREIGN KEY ("category_id") REFERENCES "wagon_categories" ("id");

ALTER TABLE "cabins" ADD FOREIGN KEY ("wagon_id") REFERENCES "wagons" ("id");

ALTER TABLE "wagon_seats" ADD FOREIGN KEY ("wagon_id") REFERENCES "wagons" ("id");

ALTER TABLE "wagon_seats" ADD FOREIGN KEY ("cabin_id") REFERENCES "cabins" ("id");

ALTER TABLE "train_wagons" ADD FOREIGN KEY ("train_id") REFERENCES "trains" ("id");

ALTER TABLE "train_wagons" ADD FOREIGN KEY ("wagon_id") REFERENCES "wagons" ("id");

ALTER TABLE "route_stations" ADD FOREIGN KEY ("route_id") REFERENCES "routes" ("id");

ALTER TABLE "route_stations" ADD FOREIGN KEY ("station_id") REFERENCES "stations" ("id");

ALTER TABLE "train_services" ADD FOREIGN KEY ("train_id") REFERENCES "trains" ("id");

ALTER TABLE "train_services" ADD FOREIGN KEY ("route_id") REFERENCES "routes" ("id");

ALTER TABLE "train_services" ADD FOREIGN KEY ("service_type_id") REFERENCES "service_types" ("id");

ALTER TABLE "train_services" ADD FOREIGN KEY ("operator_id") REFERENCES "railway_operators" ("id");

ALTER TABLE "service_exceptions" ADD FOREIGN KEY ("train_service_id") REFERENCES "train_services" ("id");

ALTER TABLE "trips" ADD FOREIGN KEY ("train_service_id") REFERENCES "train_services" ("id");

ALTER TABLE "trip_station_updates" ADD FOREIGN KEY ("trip_id") REFERENCES "trips" ("id");

ALTER TABLE "trip_station_updates" ADD FOREIGN KEY ("route_station_id") REFERENCES "route_stations" ("id");

ALTER TABLE "bookings" ADD FOREIGN KEY ("user_id") REFERENCES "users" ("id");

ALTER TABLE "bookings" ADD FOREIGN KEY ("passenger_id") REFERENCES "passengers" ("id");

ALTER TABLE "bookings" ADD FOREIGN KEY ("origin_station_id") REFERENCES "stations" ("id");

ALTER TABLE "bookings" ADD FOREIGN KEY ("destination_station_id") REFERENCES "stations" ("id");

ALTER TABLE "booking_segments" ADD FOREIGN KEY ("booking_id") REFERENCES "bookings" ("id");

ALTER TABLE "booking_segments" ADD FOREIGN KEY ("trip_id") REFERENCES "trips" ("id");

ALTER TABLE "booking_segments" ADD FOREIGN KEY ("origin_station_id") REFERENCES "stations" ("id");

ALTER TABLE "booking_segments" ADD FOREIGN KEY ("destination_station_id") REFERENCES "stations" ("id");

ALTER TABLE "booking_segments" ADD FOREIGN KEY ("origin_route_station_id") REFERENCES "route_stations" ("id");

ALTER TABLE "booking_segments" ADD FOREIGN KEY ("destination_route_station_id") REFERENCES "route_stations" ("id");

ALTER TABLE "fares" ADD FOREIGN KEY ("route_id") REFERENCES "routes" ("id");

ALTER TABLE "fares" ADD FOREIGN KEY ("operator_id") REFERENCES "railway_operators" ("id");

ALTER TABLE "fares" ADD FOREIGN KEY ("origin_country_id") REFERENCES "countries" ("id");

ALTER TABLE "fares" ADD FOREIGN KEY ("destination_country_id") REFERENCES "countries" ("id");

ALTER TABLE "fares" ADD FOREIGN KEY ("wagon_category_id") REFERENCES "wagon_categories" ("id");

ALTER TABLE "fares" ADD FOREIGN KEY ("service_type_id") REFERENCES "service_types" ("id");

ALTER TABLE "seat_reservations" ADD FOREIGN KEY ("booking_segment_id") REFERENCES "booking_segments" ("id");

ALTER TABLE "seat_reservations" ADD FOREIGN KEY ("trip_id") REFERENCES "trips" ("id");

ALTER TABLE "seat_reservations" ADD FOREIGN KEY ("wagon_seat_id") REFERENCES "wagon_seats" ("id");

ALTER TABLE "seat_reservations" ADD FOREIGN KEY ("passenger_id") REFERENCES "passengers" ("id");

ALTER TABLE "seat_reservations" ADD FOREIGN KEY ("origin_route_station_id") REFERENCES "route_stations" ("id");

ALTER TABLE "seat_reservations" ADD FOREIGN KEY ("destination_route_station_id") REFERENCES "route_stations" ("id");

ALTER TABLE "tickets" ADD FOREIGN KEY ("booking_id") REFERENCES "bookings" ("id");

ALTER TABLE "tickets" ADD FOREIGN KEY ("booking_segment_id") REFERENCES "booking_segments" ("id");

ALTER TABLE "tickets" ADD FOREIGN KEY ("passenger_id") REFERENCES "passengers" ("id");

ALTER TABLE "tickets" ADD FOREIGN KEY ("trip_id") REFERENCES "trips" ("id");

ALTER TABLE "tickets" ADD FOREIGN KEY ("origin_station_id") REFERENCES "stations" ("id");

ALTER TABLE "tickets" ADD FOREIGN KEY ("destination_station_id") REFERENCES "stations" ("id");

ALTER TABLE "tickets" ADD FOREIGN KEY ("wagon_category_id") REFERENCES "wagon_categories" ("id");

ALTER TABLE "tickets" ADD FOREIGN KEY ("seat_reservation_id") REFERENCES "seat_reservations" ("id");

ALTER TABLE "payments" ADD FOREIGN KEY ("booking_id") REFERENCES "bookings" ("id");
