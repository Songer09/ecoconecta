import os
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from ecoconecta.auth import hasher
from ecoconecta.db import engine
from ecoconecta.main import app


@pytest.fixture(scope="module")
def pilot():
    url = make_url(os.environ["TEST_DATABASE_URL"]).set(drivername="postgresql+psycopg")
    assert url.database.endswith("_test"), "Usar una base de pruebas"
    schema = "api_test_" + uuid4().hex
    bootstrap = create_engine(url)
    with bootstrap.begin() as db:
        db.execute(text(f"CREATE SCHEMA {schema}"))
    scoped = url.update_query_dict({"options": f"-csearch_path={schema}"})
    with pytest.MonkeyPatch.context() as patch:
        patch.setenv("DATABASE_URL", scoped.render_as_string(hide_password=False))
        engine.cache_clear()
        try:
            command.upgrade(Config("alembic.ini"), "head")
            password = uuid4().hex
            hashed = hasher.hash(password)
            with engine().begin() as db:
                zone = db.scalar(
                    text(
                        "INSERT INTO zones(code,name) VALUES ('TEST','Zona sintética') RETURNING id"
                    )
                )
                for flow in ("organico", "reciclable"):
                    db.execute(
                        text("INSERT INTO collectives(flow,name) VALUES (:f,:name)"),
                        {"f": flow, "name": flow},
                    )
                for index, role in enumerate(
                    (
                        "solicitante",
                        "solicitante",
                        "coordinador_huerteros",
                        "coordinador_recicladores",
                        "solicitante",
                    )
                ):
                    user = db.scalar(
                        text("""
                        INSERT INTO users(full_name,phone,password_hash,role,is_pilot)
                        VALUES ('Prueba',:phone,:password,:role,:pilot) RETURNING id
                    """),
                        {
                            "phone": f"+10000000{index}",
                            "role": role,
                            "password": hashed,
                            "pilot": index != 4,
                        },
                    )
                    if index in (2, 3):
                        member = db.scalar(
                            text("""
                            INSERT INTO collective_members(user_id,member_role,collective_id)
                            SELECT :u,'coordinador',id FROM collectives WHERE flow=:f RETURNING id
                        """),
                            {
                                "u": user,
                                "f": "organico" if index == 2 else "reciclable",
                            },
                        )
                        db.execute(
                            text(
                                "INSERT INTO coordinator_zones VALUES (:member,:zone)"
                            ),
                            {"member": member, "zone": zone},
                        )
            with TestClient(app) as client:
                yield client, str(zone), password
        finally:
            engine().dispose()
            engine.cache_clear()
            with bootstrap.begin() as db:
                db.execute(text(f"DROP SCHEMA {schema} CASCADE"))
            bootstrap.dispose()
