"""Registro público de vecinos con perfil de vivienda y consentimiento."""
from alembic import op

revision = "0009_public_resident_registration"
down_revision = "0008_purchase_rates"


def upgrade():
    op.execute("""
        ALTER TABLE requester_profiles
            ADD COLUMN stage text,
            ADD COLUMN tower text,
            ADD COLUMN apartment text,
            ADD CONSTRAINT requester_profiles_stage_length
                CHECK (stage IS NULL OR length(trim(stage)) BETWEEN 1 AND 80),
            ADD CONSTRAINT requester_profiles_tower_length
                CHECK (tower IS NULL OR length(trim(tower)) BETWEEN 1 AND 30),
            ADD CONSTRAINT requester_profiles_apartment_length
                CHECK (apartment IS NULL OR length(trim(apartment)) BETWEEN 1 AND 30)
    """)
    op.execute("""
        CREATE TABLE registration_windows (
            source_digest text PRIMARY KEY,
            started_at timestamptz NOT NULL,
            attempts integer NOT NULL CHECK (attempts > 0)
        )
    """)
    op.execute("CREATE INDEX ix_registration_windows_started_at ON registration_windows(started_at)")
    op.execute("""
        DO $$ BEGIN
          IF EXISTS (SELECT FROM pg_roles WHERE rolname='ecoconecta_app') THEN
            GRANT SELECT, INSERT, UPDATE, DELETE ON registration_windows TO ecoconecta_app;
          END IF;
        END $$
    """)


def downgrade():
    raise RuntimeError("La migración contiene datos estructurados de domicilios; respaldar y planear su conservación antes de revertirla.")
