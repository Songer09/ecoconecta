CREATE TABLE users (
 id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 handle text NOT NULL UNIQUE, role text NOT NULL CHECK(role IN ('resident','coordinator','collector','admin')),
 flow text CHECK(flow IN ('organic','recyclable')), phone text UNIQUE, token_hash text UNIQUE,
 active boolean NOT NULL DEFAULT true, notify_opt_in boolean NOT NULL DEFAULT false,
 last_inbound timestamptz, CHECK(role NOT IN ('coordinator','collector') OR flow IS NOT NULL)
);
CREATE TABLE consents (user_id int PRIMARY KEY REFERENCES users, audio boolean NOT NULL, changed_at timestamptz NOT NULL DEFAULT now());
CREATE TABLE conversations (user_id int PRIMARY KEY REFERENCES users, draft jsonb NOT NULL DEFAULT '{}');
CREATE TABLE materials (name text PRIMARY KEY, flow text NOT NULL CHECK(flow IN ('organic','recyclable')), accepted boolean NOT NULL DEFAULT false);
CREATE TABLE collection_requests (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(), owner_id int NOT NULL REFERENCES users,
 material text NOT NULL REFERENCES materials, flow text NOT NULL CHECK(flow IN ('organic','recyclable')),
 quantity numeric NOT NULL CHECK(quantity>0), unit text NOT NULL, address text NOT NULL,
 generator text NOT NULL, preference text NOT NULL,
 status text NOT NULL DEFAULT 'recibida' CHECK(status IN ('recibida','asignada','programada','recolectada','cancelada')), created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE assignments(request_id uuid PRIMARY KEY REFERENCES collection_requests, coordinator_id int NOT NULL REFERENCES users, collector_id int NOT NULL REFERENCES users);
CREATE TABLE schedules(request_id uuid PRIMARY KEY REFERENCES assignments, scheduled_at timestamptz NOT NULL, confirmed_by int NOT NULL REFERENCES users);
CREATE TABLE collection_events(request_id uuid PRIMARY KEY REFERENCES schedules, actor int NOT NULL REFERENCES users, quantity numeric NOT NULL CHECK(quantity>0), unit text NOT NULL, occurred_at timestamptz NOT NULL DEFAULT now());
CREATE TABLE points_rules(id int GENERATED ALWAYS AS IDENTITY PRIMARY KEY, material text NOT NULL REFERENCES materials, unit text NOT NULL, rate numeric NOT NULL CHECK(rate>0), starts_at timestamptz NOT NULL, ends_at timestamptz CHECK(ends_at>starts_at), approved_by int NOT NULL REFERENCES users);
CREATE TABLE points_ledger(request_id uuid PRIMARY KEY REFERENCES collection_events, rule_id int NOT NULL REFERENCES points_rules, points numeric NOT NULL CHECK(points>0));
CREATE TABLE request_status_history(id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY, request_id uuid NOT NULL REFERENCES collection_requests, status text NOT NULL, actor int NOT NULL REFERENCES users, at timestamptz NOT NULL DEFAULT now());
CREATE TABLE alerts(id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY, request_id uuid REFERENCES collection_requests, flow text, kind text NOT NULL, user_id int NOT NULL REFERENCES users, at timestamptz NOT NULL DEFAULT now());
CREATE TABLE events(id int GENERATED ALWAYS AS IDENTITY PRIMARY KEY, kind text NOT NULL CHECK(kind IN ('event','training')), title text NOT NULL, description text NOT NULL, starts_at timestamptz NOT NULL, place text NOT NULL, organizer text NOT NULL, category text NOT NULL, published boolean NOT NULL DEFAULT false);
CREATE TABLE articles(id int GENERATED ALWAYS AS IDENTITY PRIMARY KEY, title text NOT NULL UNIQUE, keywords text NOT NULL, answer text NOT NULL, source text NOT NULL, reviewer text NOT NULL, published boolean NOT NULL DEFAULT false, version int NOT NULL DEFAULT 1, reviewed_at timestamptz NOT NULL DEFAULT now());
CREATE INDEX articles_search ON articles USING gin(to_tsvector('spanish',keywords));
CREATE TABLE messages(id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY, external_id text UNIQUE NOT NULL, user_id int NOT NULL REFERENCES users, kind text NOT NULL, payload text, received_at timestamptz NOT NULL DEFAULT now(), processed boolean NOT NULL DEFAULT false);
CREATE INDEX messages_pending ON messages(id) WHERE NOT processed;
CREATE TABLE notifications(id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY, user_id int NOT NULL REFERENCES users, kind text NOT NULL, body text NOT NULL, state text NOT NULL DEFAULT 'pending', tries int NOT NULL DEFAULT 0, next_try timestamptz NOT NULL DEFAULT now(), external_id text UNIQUE);
CREATE TABLE audit_events(id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY, actor int NOT NULL REFERENCES users, action text NOT NULL, resource text, at timestamptz NOT NULL DEFAULT now());
