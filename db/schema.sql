-- =====================================================================
-- EcoConecta Villas de San Pablo - Esquema PostgreSQL (MVP)
-- Crear previamente una base vacía y ejecutar este archivo dentro de ella.
-- Base: Reto Oficial Hackathon (RN-01..RN-08, secciones 5, 6, 7 y 9)
-- Importar en drawDB: File > Import from source > PostgreSQL
-- Convenciones: ids UUID, fechas timestamptz (UTC), NOT NULL por defecto.
-- Revisado: definición inicial, NO migración para una BD con datos.
-- Aplicar cambios reales mediante Alembic tras inspeccionar la BD existente.
-- SQL PostgreSQL: vistas, índices y triggers pueden no representarse en drawDB.
-- =====================================================================

-- ---------- Tipos enumerados ----------
CREATE TYPE user_role AS ENUM (
  'solicitante', 'coordinador_huerteros', 'coordinador_recicladores',
  'recolector', 'administrador'
);

CREATE TYPE waste_flow AS ENUM ('organico', 'reciclable');          -- RN-01

CREATE TYPE generator_type AS ENUM ('hogar', 'unidad_productiva');

CREATE TYPE request_status AS ENUM (
  'recibida', 'en_revision', 'programada', 'asignada', 'recolectada', 'cancelada'
);                                                                   -- RN-04

CREATE TYPE member_role AS ENUM ('coordinador', 'recolector');

CREATE TYPE channel_type AS ENUM ('whatsapp', 'web');

CREATE TYPE message_direction AS ENUM ('entrante', 'saliente');

CREATE TYPE chat_role AS ENUM ('user', 'assistant', 'system', 'tool');

CREATE TYPE chat_status AS ENUM ('activa', 'cerrada', 'escalada_a_humano');

CREATE TYPE points_reason AS ENUM ('recoleccion', 'canje', 'ajuste');

-- ---------- Identidad y acceso ----------
CREATE TABLE users (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  full_name      TEXT NOT NULL,
  phone          TEXT NOT NULL UNIQUE,            -- E.164, identidad en WhatsApp
  email          TEXT UNIQUE,
  password_hash  TEXT,                            -- Argon2id; NULL si solo usa WhatsApp
  role           user_role NOT NULL,
  is_active      BOOLEAN NOT NULL DEFAULT TRUE,
  is_pilot       BOOLEAN NOT NULL DEFAULT FALSE,  -- RN-08: usuarios piloto
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE consents (                           -- Ley 1581: autorizacion registrada
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id        UUID NOT NULL,
  policy_version TEXT NOT NULL,
  channel        channel_type NOT NULL,
  accepted_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  revoked_at     TIMESTAMPTZ,
  CHECK (revoked_at IS NULL OR revoked_at >= accepted_at)
);

CREATE TABLE requester_profiles (                 -- solicitante: hogar o unidad productiva
  user_id          UUID PRIMARY KEY,
  generator_type   generator_type NOT NULL,
  business_name    TEXT,                          -- solo unidades productivas
  address          TEXT NOT NULL,
  neighborhood     TEXT,
  latitude         NUMERIC(9,6),
  longitude        NUMERIC(9,6),
  CHECK (latitude BETWEEN -90 AND 90),
  CHECK (longitude BETWEEN -180 AND 180),
  CHECK ((latitude IS NULL) = (longitude IS NULL))
);

-- ---------- Colectivos (huerteros / recicladores) ----------
CREATE TABLE collectives (
  id    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name  TEXT NOT NULL UNIQUE,
  flow  waste_flow NOT NULL UNIQUE,               -- un colectivo por flujo
  UNIQUE (id, flow)
);

CREATE TABLE collective_members (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  collective_id  UUID NOT NULL,
  user_id        UUID NOT NULL,
  member_role    member_role NOT NULL,
  is_available   BOOLEAN NOT NULL DEFAULT TRUE,   -- boton de disponibilidad
  joined_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (collective_id, user_id),
  UNIQUE (id, user_id)
);

-- Cobertura real pendiente: no precargar zonas, personas ni horarios inventados.
CREATE TABLE zones (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  code TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  is_active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE collector_zone_coverage (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  member_id UUID NOT NULL REFERENCES collective_members(id) ON DELETE RESTRICT,
  zone_id UUID NOT NULL REFERENCES zones(id) ON DELETE RESTRICT,
  valid_from DATE NOT NULL,
  valid_until DATE,
  CHECK (valid_until IS NULL OR valid_until >= valid_from),
  UNIQUE (member_id, zone_id, valid_from)
);

CREATE TABLE availability_slots (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  coverage_id UUID NOT NULL REFERENCES collector_zone_coverage(id) ON DELETE RESTRICT,
  weekday SMALLINT NOT NULL CHECK (weekday BETWEEN 1 AND 7),
  starts_at TIME NOT NULL,
  ends_at TIME NOT NULL,
  timezone TEXT NOT NULL DEFAULT 'America/Bogota',
  valid_from DATE NOT NULL,
  valid_until DATE,
  CHECK (ends_at > starts_at),
  CHECK (valid_until IS NULL OR valid_until >= valid_from)
);

CREATE TABLE collection_schedules (               -- horarios y rutas publicados (5.2)
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  collective_id  UUID NOT NULL,
  generator      generator_type NOT NULL,
  weekday        SMALLINT NOT NULL CHECK (weekday BETWEEN 1 AND 7),
  starts_at      TIME NOT NULL,
  ends_at        TIME NOT NULL,
  timezone       TEXT NOT NULL DEFAULT 'America/Bogota',
  zone_id        UUID NOT NULL REFERENCES zones(id) ON DELETE RESTRICT,
  valid_from     DATE NOT NULL,
  valid_until    DATE,
  CHECK (ends_at > starts_at),
  CHECK (valid_until IS NULL OR valid_until >= valid_from),
  notes          TEXT
);

-- ---------- Catalogo y puntos ----------
CREATE TABLE waste_types (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name         TEXT NOT NULL UNIQUE,              -- ej. carton, PET, restos de cocina
  flow         waste_flow NOT NULL,
  description  TEXT,
  unit         TEXT NOT NULL CHECK (length(trim(unit)) > 0), -- unidad oficial por confirmar
  is_active    BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE points_rules (                       -- RN-06: parametrizable y explicable
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  waste_type_id  UUID NOT NULL,
  points_per_unit NUMERIC(18,6) NOT NULL CHECK (points_per_unit >= 0),
  version        INTEGER NOT NULL CHECK (version > 0),
  base_unit      TEXT NOT NULL CHECK (length(trim(base_unit)) > 0),
  description    TEXT NOT NULL,                   -- explicacion de la regla
  valid_from     TIMESTAMPTZ NOT NULL,
  valid_to       TIMESTAMPTZ,
  validated_by_fsd BOOLEAN NOT NULL DEFAULT FALSE,
  created_by     UUID NOT NULL,
  approved_by    UUID REFERENCES users(id) ON DELETE RESTRICT,
  CHECK (valid_to IS NULL OR valid_to > valid_from),
  CHECK (NOT validated_by_fsd OR approved_by IS NOT NULL),
  UNIQUE (waste_type_id, version)
);

-- ---------- Solicitudes ----------
CREATE TABLE pickup_requests (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  code             TEXT NOT NULL UNIQUE,          -- identificador legible, ej. SR-000123
  requester_id     UUID NOT NULL,
  collective_id    UUID NOT NULL,                 -- RN-01: colectivo destino
  flow             waste_flow NOT NULL,
  zone_id          UUID NOT NULL REFERENCES zones(id) ON DELETE RESTRICT,
  generator        generator_type NOT NULL,
  contact_phone    TEXT NOT NULL,
  address          TEXT NOT NULL,
  latitude         NUMERIC(9,6),
  longitude        NUMERIC(9,6),
  observations     TEXT,
  preferred_time   TEXT,                          -- disponibilidad / preferencia horaria
  status           request_status NOT NULL DEFAULT 'recibida',
  source_channel   channel_type NOT NULL,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK (latitude BETWEEN -90 AND 90),
  CHECK (longitude BETWEEN -180 AND 180),
  CHECK ((latitude IS NULL) = (longitude IS NULL)),
  FOREIGN KEY (collective_id, flow) REFERENCES collectives(id, flow) ON DELETE RESTRICT
);

CREATE TABLE request_items (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  request_id     UUID NOT NULL,
  waste_type_id  UUID NOT NULL,
  estimated_qty  NUMERIC(14,4) CHECK (estimated_qty > 0),
  UNIQUE (request_id, waste_type_id)
);

CREATE TABLE request_assignments (                -- RN-03: coordinador + recolector
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  request_id      UUID NOT NULL,
  coordinator_id  UUID NOT NULL,
  collector_id    UUID NOT NULL,
  is_current      BOOLEAN NOT NULL DEFAULT TRUE,  -- permite reasignar sin perder historial
  assigned_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (id, request_id),
  UNIQUE (id, request_id, collector_id)
);

CREATE TABLE request_schedules (                  -- RN-02: dia + hora + persona
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  request_id      UUID NOT NULL,
  assignment_id   UUID NOT NULL,
  is_current      BOOLEAN NOT NULL DEFAULT TRUE,
  scheduled_start TIMESTAMPTZ NOT NULL,
  scheduled_end   TIMESTAMPTZ,
  notes           TEXT,
  confirmed_with_user_at TIMESTAMPTZ,             -- confirmacion al usuario
  created_by      UUID NOT NULL,
  confirmed_by    UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  timezone        TEXT NOT NULL DEFAULT 'America/Bogota',
  CHECK (scheduled_end IS NULL OR scheduled_end > scheduled_start),
  FOREIGN KEY (assignment_id, request_id) REFERENCES request_assignments(id, request_id)
);

CREATE TABLE request_status_history (             -- RN-04: trazabilidad
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  request_id    UUID NOT NULL,
  from_status   request_status,
  to_status     request_status NOT NULL,
  changed_by    UUID,                             -- NULL si lo hizo el sistema
  reason        TEXT,
  changed_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------- Recoleccion y puntos ----------
CREATE TABLE collections (                        -- RN-05: cierre
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  request_id    UUID NOT NULL UNIQUE,             -- una recoleccion por solicitud
  collector_id  UUID NOT NULL,
  collected_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  result_notes  TEXT,
  assignment_id UUID NOT NULL,
  confirmed_by  UUID REFERENCES users(id) ON DELETE RESTRICT,
  confirmed_at  TIMESTAMPTZ,
  confirmation_key UUID UNIQUE,
  CHECK ((confirmed_at IS NULL AND confirmed_by IS NULL AND confirmation_key IS NULL)
      OR (confirmed_at IS NOT NULL AND confirmed_by IS NOT NULL AND confirmation_key IS NOT NULL)),
  FOREIGN KEY (assignment_id, request_id, collector_id)
    REFERENCES request_assignments(id, request_id, collector_id)
);

CREATE TABLE collection_items (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  collection_id  UUID NOT NULL,
  waste_type_id  UUID NOT NULL,
  quantity       NUMERIC(14,4) NOT NULL CHECK (quantity > 0),
  unit           TEXT NOT NULL CHECK (length(trim(unit)) > 0),
  UNIQUE (collection_id, waste_type_id),
  UNIQUE (id, collection_id)
);

CREATE TABLE points_ledger (                      -- libro mayor: solo inserciones
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id        UUID NOT NULL,
  collection_id  UUID,                            -- NULL en canjes y ajustes
  rule_id        UUID,
  collection_item_id UUID,
  base_quantity  NUMERIC(14,4),
  base_unit      TEXT,
  reason         points_reason NOT NULL,
  points         NUMERIC(24,6) NOT NULL CHECK (points <> 0),
  idempotency_key UUID NOT NULL UNIQUE,
  note           TEXT,
  created_by     UUID NOT NULL,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  CHECK (reason <> 'recoleccion' OR (
    collection_id IS NOT NULL AND collection_item_id IS NOT NULL AND rule_id IS NOT NULL
    AND base_quantity IS NOT NULL AND base_quantity > 0 AND base_unit IS NOT NULL AND points > 0
  )),
  CHECK (reason <> 'canje' OR points < 0),
  FOREIGN KEY (collection_item_id, collection_id) REFERENCES collection_items(id, collection_id)
);

-- Una sola acreditación por material recolectado, no una sola por recolección.
CREATE UNIQUE INDEX uq_points_collection_item ON points_ledger(collection_item_id)
  WHERE reason = 'recoleccion';

CREATE VIEW requester_points_balances AS
SELECT u.id AS user_id, COALESCE(SUM(p.points), 0) AS points_balance
FROM users u LEFT JOIN points_ledger p ON p.user_id = u.id GROUP BY u.id;

-- ---------- Contenido educativo ----------
CREATE TABLE educational_content (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title         TEXT NOT NULL,
  body          TEXT NOT NULL,
  category      TEXT NOT NULL,                    -- separacion, huerta, horarios, rutas...
  flow          waste_flow,                       -- NULL = general
  is_published  BOOLEAN NOT NULL DEFAULT FALSE,
  created_by    UUID NOT NULL,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------- WhatsApp: Twilio prototipo / Cloud API definitivo ----------
CREATE TABLE whatsapp_messages (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  provider        TEXT NOT NULL CHECK (provider IN ('twilio', 'whatsapp_cloud')),
  provider_message_id TEXT,
  user_id         UUID,
  request_id      UUID,
  direction       message_direction NOT NULL,
  template_name   TEXT,                           -- plantilla si va fuera de ventana 24h
  body            TEXT,                           -- opcional; retención/PII por acordar
  delivery_status TEXT NOT NULL DEFAULT 'pendiente',
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (provider, provider_message_id)
);

-- Eventos separados del mensaje: un mensaje puede tener varios callbacks de estado.
CREATE TABLE webhook_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  provider TEXT NOT NULL CHECK (provider IN ('twilio', 'whatsapp_cloud')),
  event_key TEXT NOT NULL,
  event_kind TEXT NOT NULL,
  provider_message_id TEXT,
  processing_status TEXT NOT NULL DEFAULT 'received'
    CHECK (processing_status IN ('received', 'processing', 'processed', 'failed')),
  attempts INTEGER NOT NULL DEFAULT 0 CHECK (attempts >= 0),
  received_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  processed_at TIMESTAMPTZ,
  safe_error_code TEXT,
  UNIQUE (provider, event_key)
);

-- ---------- Chatbot opcional: fuera del núcleo MVP hasta acordar alcance ----------
-- El bot solo invoca casos de uso autorizados del backend, nunca SQL libre.
CREATE TABLE chat_conversations (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id       UUID,                             -- NULL si aun no esta identificado
  channel       channel_type NOT NULL,
  status        chat_status NOT NULL DEFAULT 'activa',
  request_id    UUID,                             -- solicitud en contexto (opcional)
  started_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  closed_at     TIMESTAMPTZ
);

CREATE TABLE chat_messages (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  conversation_id  UUID NOT NULL,
  role             chat_role NOT NULL,
  content          TEXT NOT NULL,
  model            TEXT,                          -- modelo usado (Claude/OpenAI)
  input_tokens     INTEGER CHECK (input_tokens >= 0),
  output_tokens    INTEGER CHECK (output_tokens >= 0),
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE chat_tool_calls (                    -- consultas que el bot hace a la BD
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  message_id      UUID NOT NULL,
  tool_name       TEXT NOT NULL,                  -- ej. consultar_estado_solicitud
  arguments       JSONB NOT NULL,
  result_summary  TEXT,
  succeeded       BOOLEAN NOT NULL DEFAULT TRUE,
  executed_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE chat_faq (                           -- respuestas curadas para el bot
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  question      TEXT NOT NULL,
  answer        TEXT NOT NULL,
  flow          waste_flow,
  content_id    UUID,                             -- ficha educativa de respaldo
  is_active     BOOLEAN NOT NULL DEFAULT TRUE
);

-- ---------- Auditoria ----------
CREATE TABLE audit_log (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  actor_id     UUID,
  action       TEXT NOT NULL,
  entity       TEXT NOT NULL,
  entity_id    UUID,
  detail       JSONB,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- =====================================================================
-- Llaves foraneas
-- =====================================================================
ALTER TABLE consents ADD FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE requester_profiles ADD FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE collective_members ADD FOREIGN KEY (collective_id) REFERENCES collectives(id) ON DELETE RESTRICT;
ALTER TABLE collective_members ADD FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE RESTRICT;
ALTER TABLE collection_schedules ADD FOREIGN KEY (collective_id) REFERENCES collectives(id) ON DELETE CASCADE;
ALTER TABLE points_rules ADD FOREIGN KEY (waste_type_id) REFERENCES waste_types(id) ON DELETE RESTRICT;
ALTER TABLE points_rules ADD FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE RESTRICT;
ALTER TABLE pickup_requests ADD FOREIGN KEY (requester_id) REFERENCES users(id) ON DELETE RESTRICT;
ALTER TABLE pickup_requests ADD FOREIGN KEY (collective_id) REFERENCES collectives(id) ON DELETE RESTRICT;
ALTER TABLE request_items ADD FOREIGN KEY (request_id) REFERENCES pickup_requests(id) ON DELETE CASCADE;
ALTER TABLE request_items ADD FOREIGN KEY (waste_type_id) REFERENCES waste_types(id) ON DELETE RESTRICT;
ALTER TABLE request_assignments ADD FOREIGN KEY (request_id) REFERENCES pickup_requests(id) ON DELETE CASCADE;
ALTER TABLE request_assignments ADD FOREIGN KEY (coordinator_id) REFERENCES users(id) ON DELETE RESTRICT;
ALTER TABLE request_assignments ADD FOREIGN KEY (collector_id) REFERENCES users(id) ON DELETE RESTRICT;
ALTER TABLE request_schedules ADD FOREIGN KEY (request_id) REFERENCES pickup_requests(id) ON DELETE CASCADE;
ALTER TABLE request_schedules ADD FOREIGN KEY (assignment_id) REFERENCES request_assignments(id) ON DELETE RESTRICT;
ALTER TABLE request_schedules ADD FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE RESTRICT;
ALTER TABLE request_status_history ADD FOREIGN KEY (request_id) REFERENCES pickup_requests(id) ON DELETE CASCADE;
ALTER TABLE request_status_history ADD FOREIGN KEY (changed_by) REFERENCES users(id) ON DELETE SET NULL;
ALTER TABLE collections ADD FOREIGN KEY (request_id) REFERENCES pickup_requests(id) ON DELETE RESTRICT;
ALTER TABLE collections ADD FOREIGN KEY (collector_id) REFERENCES users(id) ON DELETE RESTRICT;
ALTER TABLE collection_items ADD FOREIGN KEY (collection_id) REFERENCES collections(id) ON DELETE CASCADE;
ALTER TABLE collection_items ADD FOREIGN KEY (waste_type_id) REFERENCES waste_types(id) ON DELETE RESTRICT;
ALTER TABLE points_ledger ADD FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE RESTRICT;
ALTER TABLE points_ledger ADD FOREIGN KEY (collection_id) REFERENCES collections(id) ON DELETE RESTRICT;
ALTER TABLE points_ledger ADD FOREIGN KEY (rule_id) REFERENCES points_rules(id) ON DELETE RESTRICT;
ALTER TABLE points_ledger ADD FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE RESTRICT;
ALTER TABLE educational_content ADD FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE RESTRICT;
ALTER TABLE whatsapp_messages ADD FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL;
ALTER TABLE whatsapp_messages ADD FOREIGN KEY (request_id) REFERENCES pickup_requests(id) ON DELETE SET NULL;
ALTER TABLE chat_conversations ADD FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL;
ALTER TABLE chat_conversations ADD FOREIGN KEY (request_id) REFERENCES pickup_requests(id) ON DELETE SET NULL;
ALTER TABLE chat_messages ADD FOREIGN KEY (conversation_id) REFERENCES chat_conversations(id) ON DELETE CASCADE;
ALTER TABLE chat_tool_calls ADD FOREIGN KEY (message_id) REFERENCES chat_messages(id) ON DELETE CASCADE;
ALTER TABLE chat_faq ADD FOREIGN KEY (content_id) REFERENCES educational_content(id) ON DELETE SET NULL;
ALTER TABLE audit_log ADD FOREIGN KEY (actor_id) REFERENCES users(id) ON DELETE SET NULL;

-- =====================================================================
-- Indices (campos filtrados y llaves foraneas de uso frecuente)
-- =====================================================================
CREATE INDEX idx_requests_collective_status ON pickup_requests (collective_id, status);
CREATE INDEX idx_requests_requester ON pickup_requests (requester_id, created_at);
CREATE INDEX idx_assignments_collector ON request_assignments (collector_id, is_current);
CREATE INDEX idx_schedules_start ON request_schedules (scheduled_start);
CREATE INDEX idx_status_history_request ON request_status_history (request_id, changed_at);
CREATE INDEX idx_ledger_user ON points_ledger (user_id, created_at);
CREATE INDEX idx_members_user ON collective_members (user_id);
CREATE INDEX idx_wa_messages_user ON whatsapp_messages (user_id, created_at);
CREATE INDEX idx_chat_messages_conv ON chat_messages (conversation_id, created_at);
CREATE INDEX idx_chat_conv_user ON chat_conversations (user_id);
CREATE INDEX idx_audit_entity ON audit_log (entity, entity_id);
CREATE UNIQUE INDEX uq_current_assignment ON request_assignments(request_id) WHERE is_current;
CREATE UNIQUE INDEX uq_current_schedule ON request_schedules(request_id) WHERE is_current;
CREATE INDEX idx_requests_zone_status ON pickup_requests(zone_id, status, created_at);
CREATE INDEX idx_coverage_zone ON collector_zone_coverage(zone_id, valid_from, valid_until);
CREATE INDEX idx_availability_coverage ON availability_slots(coverage_id, weekday);
CREATE INDEX idx_webhook_processing ON webhook_events(processing_status, received_at);

-- El libro es append-only también frente a UPDATE/DELETE/TRUNCATE directos.
-- El usuario runtime no debe ser propietario ni superusuario (podría desactivar triggers).
CREATE FUNCTION reject_ledger_mutation() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION 'points_ledger es inmutable; registrar un movimiento compensatorio'
    USING ERRCODE = '23514';
END;
$$;
CREATE TRIGGER points_ledger_immutable
  BEFORE UPDATE OR DELETE OR TRUNCATE ON points_ledger
  FOR EACH STATEMENT EXECUTE FUNCTION reject_ledger_mutation();

CREATE FUNCTION protect_used_points_rule() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF EXISTS (SELECT 1 FROM points_ledger WHERE rule_id = OLD.id) THEN
    RAISE EXCEPTION 'Regla ya utilizada: crear otra version, no cambiar el historial'
      USING ERRCODE = '23514';
  END IF;
  IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
  RETURN NEW;
END;
$$;
CREATE TRIGGER used_points_rule_immutable
  BEFORE UPDATE OR DELETE ON points_rules
  FOR EACH ROW EXECUTE FUNCTION protect_used_points_rule();

-- Validación financiera mínima; el cálculo/redondeo y selección de regla son del backend.
CREATE FUNCTION validate_points_credit() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
  event_row collections%ROWTYPE;
  item_row collection_items%ROWTYPE;
  rule_row points_rules%ROWTYPE;
  owner_id UUID;
BEGIN
  IF NEW.reason <> 'recoleccion' THEN RETURN NEW; END IF;
  SELECT * INTO event_row FROM collections WHERE id = NEW.collection_id FOR UPDATE;
  SELECT * INTO item_row FROM collection_items WHERE id = NEW.collection_item_id;
  SELECT * INTO rule_row FROM points_rules WHERE id = NEW.rule_id FOR SHARE;
  SELECT requester_id INTO owner_id FROM pickup_requests WHERE id = event_row.request_id;
  IF event_row.id IS NULL OR event_row.confirmed_at IS NULL
     OR item_row.id IS NULL OR rule_row.id IS NULL
     OR NEW.user_id IS DISTINCT FROM owner_id
     OR item_row.collection_id IS DISTINCT FROM event_row.id
     OR item_row.waste_type_id IS DISTINCT FROM rule_row.waste_type_id
     OR NOT rule_row.validated_by_fsd OR rule_row.approved_by IS NULL
     OR event_row.collected_at < rule_row.valid_from
     OR (rule_row.valid_to IS NOT NULL AND event_row.collected_at >= rule_row.valid_to)
     OR NEW.base_unit IS DISTINCT FROM rule_row.base_unit THEN
    RAISE EXCEPTION 'Acreditacion sin recoleccion confirmada, propietario o regla compatible'
      USING ERRCODE = '23514';
  END IF;
  RETURN NEW;
END;
$$;
CREATE TRIGGER points_credit_valid
  BEFORE INSERT ON points_ledger FOR EACH ROW EXECUTE FUNCTION validate_points_credit();

CREATE FUNCTION protect_confirmed_collection() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
  target_id UUID;
  target_confirmed_at TIMESTAMPTZ;
BEGIN
  IF TG_TABLE_NAME = 'collections' THEN
    IF OLD.confirmed_at IS NOT NULL THEN
      RAISE EXCEPTION 'Cierre confirmado inmutable; coordinar correccion auditada' USING ERRCODE = '23514';
    END IF;
  ELSE
    IF TG_OP <> 'INSERT' THEN
      target_id := OLD.collection_id;
      SELECT confirmed_at INTO target_confirmed_at FROM collections WHERE id = target_id FOR UPDATE;
      IF target_confirmed_at IS NOT NULL THEN
        RAISE EXCEPTION 'Material de cierre confirmado inmutable' USING ERRCODE = '23514';
      END IF;
    END IF;
    IF TG_OP <> 'DELETE' THEN
      target_id := NEW.collection_id;
      SELECT confirmed_at INTO target_confirmed_at FROM collections WHERE id = target_id FOR UPDATE;
      IF target_confirmed_at IS NOT NULL THEN
        RAISE EXCEPTION 'No agregar materiales a un cierre confirmado' USING ERRCODE = '23514';
      END IF;
    END IF;
  END IF;
  IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
  RETURN NEW;
END;
$$;
CREATE TRIGGER confirmed_collection_immutable BEFORE UPDATE OR DELETE ON collections
  FOR EACH ROW EXECUTE FUNCTION protect_confirmed_collection();
CREATE TRIGGER confirmed_items_immutable BEFORE INSERT OR UPDATE OR DELETE ON collection_items
  FOR EACH ROW EXECUTE FUNCTION protect_confirmed_collection();

-- Integridad transaccional: evaluar al COMMIT permite actualizar estado, agenda y
-- confirmación en una misma transacción. No sustituye autorización server-side.
CREATE FUNCTION validate_request_integrity() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
  old_data JSONB;
  new_data JSONB;
  request_ids UUID[];
  target_id UUID;
  current_request pickup_requests%ROWTYPE;
BEGIN
  IF TG_OP <> 'INSERT' THEN old_data := to_jsonb(OLD); END IF;
  IF TG_OP <> 'DELETE' THEN new_data := to_jsonb(NEW); END IF;
  IF TG_TABLE_NAME = 'pickup_requests' THEN
    request_ids := ARRAY[(old_data->>'id')::UUID, (new_data->>'id')::UUID];
  ELSIF TG_TABLE_NAME = 'collection_items' THEN
    request_ids := ARRAY(
      SELECT DISTINCT request_id FROM collections
      WHERE id IN ((old_data->>'collection_id')::UUID, (new_data->>'collection_id')::UUID)
    );
  ELSE
    request_ids := ARRAY[(old_data->>'request_id')::UUID, (new_data->>'request_id')::UUID];
  END IF;
  FOR target_id IN SELECT DISTINCT x FROM unnest(request_ids) x WHERE x IS NOT NULL LOOP
    SELECT * INTO current_request FROM pickup_requests WHERE id = target_id FOR UPDATE;
    IF NOT FOUND THEN CONTINUE; END IF;
    IF current_request.status IN ('asignada', 'programada', 'recolectada') AND NOT EXISTS (
      SELECT 1 FROM request_assignments WHERE request_id = target_id AND is_current
    ) THEN
      RAISE EXCEPTION 'Solicitud % requiere asignacion vigente', target_id USING ERRCODE = '23514';
    END IF;
    IF current_request.status IN ('programada', 'recolectada') AND NOT EXISTS (
      SELECT 1 FROM request_schedules s JOIN request_assignments a ON a.id = s.assignment_id
      WHERE s.request_id = target_id AND s.is_current AND a.is_current
    ) THEN
      RAISE EXCEPTION 'Solicitud % requiere programacion y asignacion vigentes', target_id
        USING ERRCODE = '23514';
    END IF;
    IF EXISTS (
      SELECT 1 FROM request_assignments a
      WHERE a.request_id = target_id AND a.is_current AND (
        NOT EXISTS (SELECT 1 FROM collective_members m WHERE m.user_id = a.collector_id
          AND m.collective_id = current_request.collective_id AND m.member_role = 'recolector')
        OR NOT EXISTS (SELECT 1 FROM collective_members m WHERE m.user_id = a.coordinator_id
          AND m.collective_id = current_request.collective_id AND m.member_role = 'coordinador')
      )
    ) THEN
      RAISE EXCEPTION 'Asignacion fuera del colectivo o funcion correspondiente' USING ERRCODE = '23514';
    END IF;
    IF EXISTS (
      SELECT 1 FROM request_items i JOIN waste_types w ON w.id = i.waste_type_id
      WHERE i.request_id = target_id AND w.flow <> current_request.flow
    ) OR EXISTS (
      SELECT 1 FROM collections c JOIN collection_items i ON i.collection_id = c.id
      JOIN waste_types w ON w.id = i.waste_type_id WHERE c.request_id = target_id
      AND (w.flow <> current_request.flow OR i.unit <> w.unit)
    ) THEN
      RAISE EXCEPTION 'Material o unidad incompatible con el flujo de la solicitud' USING ERRCODE = '23514';
    END IF;
    IF current_request.status = 'recolectada' AND NOT EXISTS (
      SELECT 1 FROM collections c JOIN request_assignments a ON a.id = c.assignment_id
      WHERE c.request_id = target_id AND c.confirmed_at IS NOT NULL AND a.is_current
    ) THEN
      RAISE EXCEPTION 'Solicitud recolectada sin cierre confirmado' USING ERRCODE = '23514';
    END IF;
    IF EXISTS (
      SELECT 1 FROM collections c WHERE c.request_id = target_id AND c.confirmed_at IS NOT NULL
      AND (current_request.status <> 'recolectada' OR NOT EXISTS (
        SELECT 1 FROM collection_items i WHERE i.collection_id = c.id
      ))
    ) THEN
      RAISE EXCEPTION 'Cierre confirmado requiere estado recolectada y materiales' USING ERRCODE = '23514';
    END IF;
  END LOOP;
  RETURN NULL;
END;
$$;

CREATE CONSTRAINT TRIGGER request_integrity AFTER INSERT OR UPDATE OR DELETE ON pickup_requests
  DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION validate_request_integrity();
CREATE CONSTRAINT TRIGGER assignment_integrity AFTER INSERT OR UPDATE OR DELETE ON request_assignments
  DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION validate_request_integrity();
CREATE CONSTRAINT TRIGGER schedule_integrity AFTER INSERT OR UPDATE OR DELETE ON request_schedules
  DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION validate_request_integrity();
CREATE CONSTRAINT TRIGGER collection_integrity AFTER INSERT OR UPDATE OR DELETE ON collections
  DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION validate_request_integrity();
CREATE CONSTRAINT TRIGGER collection_item_integrity AFTER INSERT OR UPDATE OR DELETE ON collection_items
  DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION validate_request_integrity();
CREATE CONSTRAINT TRIGGER request_item_integrity AFTER INSERT OR UPDATE OR DELETE ON request_items
  DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION validate_request_integrity();

-- El backend debe bloquear pickup_requests FOR UPDATE antes de cada comando,
-- validar rol/objeto, cobertura y disponibilidad, transiciones e historial.
-- No se fijan tasas, redondeo, zonas ni horarios sin confirmación del equipo.
