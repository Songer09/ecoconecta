from alembic import context
from app.db import engine

with engine.begin() as connection:
    context.configure(connection=connection)
    with context.begin_transaction():
        context.run_migrations()
