"""Acceso al piloto y limitación de intentos en la PostgreSQL compartida."""
from alembic import op

revision = "0002_sessions"
down_revision = "0001_schema"


def upgrade():
    op.execute("""
        CREATE TABLE api_sessions (
            token_digest text PRIMARY KEY, user_id uuid NOT NULL REFERENCES users(id),
            expires_at timestamptz NOT NULL, revoked boolean NOT NULL DEFAULT false
        )
    """)
    op.execute("CREATE INDEX ix_api_sessions_expiry ON api_sessions(expires_at)")
    op.execute("""
        CREATE TABLE login_windows (
            source_digest text PRIMARY KEY, started_at timestamptz NOT NULL,
            attempts integer NOT NULL
        )
    """)
    op.execute("""
        DO $$ BEGIN
          IF EXISTS (SELECT FROM pg_roles WHERE rolname='ecoconecta_app') THEN
            GRANT SELECT, INSERT, UPDATE ON api_sessions, login_windows TO ecoconecta_app;
          END IF;
        END $$
    """)


def downgrade():
    op.drop_table("login_windows")
    op.drop_table("api_sessions")
