"""Tarifas oficiales de compra separadas de los puntos."""
from alembic import op

revision = "0008_purchase_rates"
down_revision = "0007_positions"


def upgrade():
    op.execute("""CREATE TABLE purchase_rates(id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
        material_id uuid NOT NULL REFERENCES waste_types(id),valid_from timestamptz NOT NULL,
        cop_per_kg numeric(14,2) NOT NULL CHECK(cop_per_kg>=0),source text NOT NULL,
        created_by uuid NOT NULL REFERENCES users(id),UNIQUE(material_id,valid_from))""")
    op.execute("""DO $$ BEGIN IF EXISTS(SELECT FROM pg_roles WHERE rolname='ecoconecta_app') THEN
        GRANT SELECT,INSERT ON purchase_rates TO ecoconecta_app; END IF; END $$""")


def downgrade():
    op.drop_table("purchase_rates")
