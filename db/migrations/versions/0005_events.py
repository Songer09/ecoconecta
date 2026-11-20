"""Agenda pública de eventos comunitarios."""
from alembic import op

revision = "0005_events"
down_revision = "0004_learning"


def upgrade():
    op.execute("""
        CREATE TABLE community_events (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            title text NOT NULL,
            description text NOT NULL,
            organizer text NOT NULL,
            location text NOT NULL,
            starts_at timestamptz NOT NULL,
            ends_at timestamptz NOT NULL CHECK (ends_at > starts_at),
            is_published boolean NOT NULL DEFAULT false,
            updated_at timestamptz NOT NULL DEFAULT now(),
            created_by uuid NOT NULL REFERENCES users(id)
        )
    """)
    op.execute("CREATE INDEX idx_events_agenda ON community_events(starts_at, id) WHERE is_published")
    op.execute("""
        DO $$ BEGIN
            IF EXISTS (SELECT FROM pg_roles WHERE rolname='ecoconecta_app') THEN
                GRANT SELECT, INSERT, UPDATE ON community_events TO ecoconecta_app;
            END IF;
        END $$
    """)


def downgrade():
    op.drop_table("community_events")
