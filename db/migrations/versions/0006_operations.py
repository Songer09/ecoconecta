"""Canjes, faltantes de huerta y orden de paradas."""
from alembic import op

revision = "0006_operations"
down_revision = "0005_events"


def upgrade():
    op.execute("""CREATE TABLE rewards (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(), name text NOT NULL UNIQUE,
        price integer NOT NULL CHECK(price>0), stock integer NOT NULL CHECK(stock>=0))""")
    op.execute("""CREATE TABLE redemptions (
        id uuid PRIMARY KEY REFERENCES points_ledger(id), user_id uuid NOT NULL REFERENCES users(id),
        reward_id uuid NOT NULL REFERENCES rewards(id), quantity integer NOT NULL CHECK(quantity>0),
        cost numeric NOT NULL CHECK(cost>0), created_at timestamptz NOT NULL DEFAULT now())""")
    op.execute("""CREATE TABLE garden_needs (
        id uuid PRIMARY KEY DEFAULT gen_random_uuid(),zone_id uuid NOT NULL REFERENCES zones(id),
        name text NOT NULL, unit text NOT NULL, quantity numeric(14,4) NOT NULL CHECK(quantity>=0),
        updated_at timestamptz NOT NULL DEFAULT now(), UNIQUE(zone_id,name,unit))""")
    op.execute("ALTER TABLE request_schedules ADD COLUMN stop_order integer CHECK(stop_order>0)")
    op.execute("""DO $$ BEGIN IF EXISTS(SELECT FROM pg_roles WHERE rolname='ecoconecta_app') THEN
        GRANT SELECT,INSERT,UPDATE ON rewards,garden_needs TO ecoconecta_app;
        GRANT SELECT,INSERT ON redemptions TO ecoconecta_app;
        GRANT SELECT,INSERT,DELETE ON coordinator_zones TO ecoconecta_app;
        END IF; END $$""")


def downgrade():
    op.drop_column("request_schedules","stop_order")
    op.drop_table("garden_needs")
    op.drop_table("redemptions")
    op.drop_table("rewards")
