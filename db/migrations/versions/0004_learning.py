"""Finalizaciones de módulos educativos por perfil."""
from alembic import op

revision = "0004_learning"
down_revision = "0003_coord_zones"


def upgrade():
    op.execute("""
        CREATE TABLE learning_completions (
            user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            module_id uuid NOT NULL REFERENCES educational_content(id) ON DELETE CASCADE,
            completed_at timestamptz NOT NULL DEFAULT now(),
            PRIMARY KEY (user_id, module_id)
        )
    """)
    op.execute("""
        DO $$ BEGIN
            IF EXISTS (SELECT FROM pg_roles WHERE rolname='ecoconecta_app') THEN
                GRANT SELECT, INSERT ON learning_completions TO ecoconecta_app;
            END IF;
        END $$
    """)


def downgrade():
    op.drop_table("learning_completions")
