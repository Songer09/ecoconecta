"""Esquema de operaciones comunitarias."""

from pathlib import Path
from alembic import op

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    for statement in Path(__file__).with_suffix(".sql").read_text().split(";"):
        if statement.strip():
            op.execute(statement)


def downgrade():
    raise RuntimeError("La reversión eliminaría registros. Restaure una copia aislada.")
