ALTER TABLE collection_requests ALTER COLUMN quantity DROP NOT NULL, ALTER COLUMN unit DROP NOT NULL;
ALTER TABLE collection_requests ADD CHECK ((quantity IS NULL) = (unit IS NULL));
CREATE TABLE collection_request_items (
  request_id uuid NOT NULL REFERENCES collection_requests,
  material text NOT NULL REFERENCES materials,
  quantity numeric CHECK(quantity > 0),
  unit text,
  approximate boolean NOT NULL DEFAULT false,
  description varchar(120),
  PRIMARY KEY (request_id, material),
  CHECK ((quantity IS NULL) = (unit IS NULL))
);
INSERT INTO collection_request_items(request_id,material,quantity,unit)
SELECT id,material,quantity,unit FROM collection_requests;
CREATE TABLE collected_items (
  request_id uuid NOT NULL REFERENCES collection_events,
  material text NOT NULL,
  quantity numeric NOT NULL CHECK(quantity > 0),
  unit text NOT NULL,
  PRIMARY KEY (request_id, material),
  FOREIGN KEY (request_id, material) REFERENCES collection_request_items
);
INSERT INTO collected_items(request_id,material,quantity,unit)
SELECT e.request_id,r.material,e.quantity,e.unit FROM collection_events e
JOIN collection_requests r ON r.id=e.request_id;
ALTER TABLE points_ledger ADD COLUMN material text;
UPDATE points_ledger p SET material=r.material FROM collection_requests r WHERE r.id=p.request_id;
ALTER TABLE points_ledger ALTER COLUMN material SET NOT NULL, DROP CONSTRAINT points_ledger_pkey;
ALTER TABLE points_ledger ADD PRIMARY KEY (request_id,material);
ALTER TABLE points_ledger ADD FOREIGN KEY (request_id,material) REFERENCES collected_items;
CREATE TABLE chat_analytics (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  attempt uuid,
  event text NOT NULL,
  source text NOT NULL,
  attributes jsonb NOT NULL DEFAULT '{}',
  occurred_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX chat_analytics_attempt ON chat_analytics(attempt,occurred_at) WHERE attempt IS NOT NULL;
