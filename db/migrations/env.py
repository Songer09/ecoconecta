from alembic import context
from sqlalchemy import create_engine
from ecoconecta.db import database_url

with create_engine(database_url(), hide_parameters=True).connect() as connection:
    context.configure(connection=connection)
    with context.begin_transaction():
        context.run_migrations()
