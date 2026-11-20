"""Persiste la pregunta activa y el contexto de la tarea."""

from alembic import op

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "ALTER TABLE conversations ADD COLUMN context jsonb NOT NULL DEFAULT '{}'"
    )


def downgrade():
    op.execute("ALTER TABLE conversations DROP COLUMN context")
