"""Última posición operativa, sin historial."""
from alembic import op

revision = "0007_positions"
down_revision = "0006_operations"


def upgrade():
    op.execute("""CREATE TABLE live_positions (
        collector_id uuid PRIMARY KEY REFERENCES users(id), assignment_id uuid NOT NULL REFERENCES request_assignments(id),
        latitude double precision NOT NULL CHECK(latitude BETWEEN -90 AND 90),
        longitude double precision NOT NULL CHECK(longitude BETWEEN -180 AND 180),
        accuracy_m double precision NOT NULL CHECK(accuracy_m>0), updated_at timestamptz NOT NULL DEFAULT now())""")
    op.execute("""DO $$ BEGIN IF EXISTS(SELECT FROM pg_roles WHERE rolname='ecoconecta_app') THEN
        GRANT SELECT,INSERT,UPDATE,DELETE ON live_positions TO ecoconecta_app;
        END IF; END $$""")


def downgrade():
    op.drop_table("live_positions")
