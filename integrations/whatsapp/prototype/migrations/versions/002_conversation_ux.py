"""Declaraciones opcionales, detalle por material y telemetría sin identidad."""

from pathlib import Path
from alembic import op

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade():
    for statement in Path(__file__).with_suffix(".sql").read_text().split(";"):
        if statement.strip():
            op.execute(statement)


def downgrade():
    raise RuntimeError(
        "La reversión perdería declaraciones sin peso y avisos con varios materiales."
    )
