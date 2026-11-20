import os
from dataclasses import replace
from uuid import uuid4
from pathlib import Path
import sys
import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


@pytest.fixture(scope="session")
def testdb():
    dsn = os.getenv("TEST_DATABASE_URL")
    if not dsn:
        pytest.fail("Define TEST_DATABASE_URL con una conexión PostgreSQL de pruebas")
    from app.config import settings
    from unittest.mock import patch

    schema = "eco_test_" + uuid4().hex
    url = make_url(dsn).set(drivername="postgresql+psycopg")
    base = create_engine(url)
    isolated = url.update_query_dict({"options": "-csearch_path=" + schema})
    with base.begin() as db:
        db.exec_driver_sql(f"CREATE SCHEMA {schema}")
    try:
        with patch.dict(
            os.environ,
            {
                "DATABASE_URL": isolated.render_as_string(hide_password=False),
                "APP_ENV": "test",
                "AI_PROVIDER": "mock",
                "WHATSAPP_PROVIDER": "mock",
                "META_APP_SECRET": "synthetic-webhook-secret",
                "META_PHONE_NUMBER_ID": "123",
                "META_VERIFY_TOKEN": "verify-demo",
                "META_WABA_ID": "456",
            },
        ):
            settings.cache_clear()
            command.upgrade(Config(str(ROOT / "alembic.ini")), "head")
            from app.db import engine
            from app.main import app, buckets
            from app.seed import demo

            yield engine, app, demo, buckets, replace(settings(), ai="gemini")
            engine.dispose()
    finally:
        settings.cache_clear()
        with base.begin() as db:
            db.exec_driver_sql(f"DROP SCHEMA {schema} CASCADE")
        base.dispose()


@pytest.fixture
def ctx(testdb):
    from fastapi.testclient import TestClient

    engine, app, demo, buckets, _ = testdb
    buckets.clear()
    with engine.begin() as db:
        db.exec_driver_sql(
            "TRUNCATE materials, users, articles, events, chat_analytics RESTART IDENTITY CASCADE"
        )
        tokens = demo(db)
    with TestClient(app) as api:

        class Context:
            def call(self, method, path, user="hogar-demo", **kw):
                return api.request(
                    method,
                    "/api/v1/" + path,
                    headers={"Authorization": "Bearer " + tokens[user]},
                    **kw,
                )

            def say(self, text, user="hogar-demo", **kw):
                result = self.call(
                    "POST", "demo/messages", user, json={"text": text, **kw}
                )
                assert result.status_code == 200, result.text
                return result.json()

        c = Context()
        c.api = api
        c.engine = engine
        yield c
