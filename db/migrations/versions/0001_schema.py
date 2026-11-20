"""Baseline publicado en 34ad455. Conservar db/schema.sql como snapshot inicial."""
from pathlib import Path
from alembic import op

revision = "0001_schema"
down_revision = None


def upgrade():
    schema = Path(__file__).resolve().parents[2] / "schema.sql"
    op.get_bind().exec_driver_sql(schema.read_text(encoding="utf-8"), execution_options={"no_parameters": True})


def downgrade():
    raise RuntimeError("El baseline contiene datos operativos. Restaurar desde backup.")
