"""Ámbito de acceso territorial para coordinadores del piloto."""
from alembic import op

revision = "0003_coord_zones"
down_revision = "0002_sessions"


def upgrade():
    op.execute("""
        CREATE TABLE coordinator_zones (
            member_id uuid NOT NULL REFERENCES collective_members(id),
            zone_id uuid NOT NULL REFERENCES zones(id),
            PRIMARY KEY (member_id, zone_id)
        )
    """)
    op.execute("""
        DO $$ BEGIN
          IF EXISTS (SELECT FROM pg_roles WHERE rolname='ecoconecta_app') THEN
            GRANT SELECT ON coordinator_zones TO ecoconecta_app;
          END IF;
        END $$
    """)


def downgrade():
    op.drop_table("coordinator_zones")
