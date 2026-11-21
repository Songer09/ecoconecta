import os
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

url = make_url(os.environ["DATABASE_URL"])
if url.get_backend_name() != "postgresql":
    raise ValueError("EcoConecta requiere PostgreSQL")
engine = create_engine(
    url.set(drivername="postgresql+psycopg"), pool_pre_ping=True, hide_parameters=True
)


def query(db, sql, **params):
    return db.execute(text(sql), params)


def rows(db, sql, **params):
    return query(db, sql, **params).mappings().all()


def one(db, sql, **params):
    return query(db, sql, **params).mappings().first()


def audit(db, actor, action, resource=None):
    query(
        db,
        "INSERT INTO audit_events(actor,action,resource) VALUES(:actor,:action,:resource)",
        actor=actor,
        action=action,
        resource=str(resource) if resource is not None else None,
    )
