import os
from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url


def database_url():
    url = make_url(os.environ["DATABASE_URL"])
    if url.get_backend_name() != "postgresql":
        raise ValueError("Se requiere PostgreSQL")
    return url.set(drivername="postgresql+psycopg")


@lru_cache
def engine():
    return create_engine(database_url(), pool_pre_ping=True, hide_parameters=True)
