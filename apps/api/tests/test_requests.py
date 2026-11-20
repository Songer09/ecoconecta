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
                zone = db.scalar(text("INSERT INTO zones(code,name) VALUES ('TEST','Zona sintética') RETURNING id"))
                for flow in ("organico", "reciclable"):
                    db.execute(text("INSERT INTO collectives(flow,name) VALUES (:f,:name)"), {"f": flow, "name": flow})
                for index, role in enumerate(("solicitante","solicitante","coordinador_huerteros","coordinador_recicladores","solicitante")):
                    user = db.scalar(text("""
                        INSERT INTO users(full_name,phone,password_hash,role,is_pilot)
                        VALUES ('Prueba',:phone,:password,:role,:pilot) RETURNING id
                    """), {"phone": f"+10000000{index}", "role": role, "password": hashed, "pilot": index != 4})
                    if index in (2,3):
                        member = db.scalar(text("""
                            INSERT INTO collective_members(user_id,member_role,collective_id)
                            SELECT :u,'coordinador',id FROM collectives WHERE flow=:f RETURNING id
                        """), {"u": user, "f": "organico" if index == 2 else "reciclable"})
                        db.execute(text("INSERT INTO coordinator_zones VALUES (:member,:zone)"), {"member":member,"zone":zone})
            with TestClient(app) as client:
                yield client, str(zone), password
        finally:
            engine().dispose()
            engine.cache_clear()
            with bootstrap.begin() as db:
                db.execute(text(f"DROP SCHEMA {schema} CASCADE"))
            bootstrap.dispose()


def login(client, index, password):
    return client.post("/api/v1/auth/login", json={"phone": f"+10000000{index}", "password": password})


def test_auth(pilot):
    client, _, password = pilot
    assert login(client, 0, "invalid").status_code == 401
    assert login(client, 4, password).status_code == 401
    assert client.get("/api/v1/auth/me").status_code == 401
    token = login(client, 0, password).json()["access_token"]
    headers = {"Authorization": "Bearer " + token}
    assert client.get("/api/v1/auth/me", headers=headers).json()["role"] == "solicitante"
    assert client.post("/api/v1/auth/logout", headers=headers).status_code == 204
    assert client.get("/api/v1/auth/me", headers=headers).status_code == 401


@pytest.mark.parametrize("flow,index", [("organico",2), ("reciclable",3)])
def test_request_lifecycle(pilot, flow, index):
    client, zone, password = pilot
    headers = [{"Authorization": "Bearer " + login(client,i,password).json()["access_token"]} for i in range(4)]
    assert zone in {z["id"] for z in client.get("/api/v1/zones", headers=headers[0]).json()}
    payload = {"generator": "hogar", "flow": flow, "zone_id": zone, "address": "Referencia sintética",
               "contact_phone": "+100000000", "preferred_time": "mañana"}
    url = "/api/v1/requests"
    assert client.post(url, headers=headers[0], json={**payload, "requester_id": zone}).status_code == 422
    assert client.post(url, headers=headers[0], json={**payload, "zone_id": str(uuid4())}).status_code == 422
    assert client.post(url, headers=headers[index], json=payload).status_code == 403
    result = client.post(url, headers=headers[0], json=payload)
    assert result.status_code == 201, result.text
    detail = url + "/" + result.json()["id"]
    assert client.get(detail, headers=headers[0]).json()["history"][0]["to_status"] == "recibida"
    assert client.get(detail, headers=headers[1]).status_code == 404
    assert client.get(detail, headers=headers[index]).status_code == 200
    assert client.get(detail, headers=headers[5-index]).status_code == 404
    inbox = client.get("/api/v1/coordinator/requests", headers=headers[index], params={"flow":flow}).json()
    assert any(x["id"] == result.json()["id"] for x in inbox)
    assert all("address" not in row and "contact_phone" not in row for row in inbox)
    assert client.get("/api/v1/coordinator/requests", headers=headers[5-index], params={"flow":flow}).json() == []
    with engine().begin() as db:
        other_zone = db.scalar(text("INSERT INTO zones(code,name) VALUES (:code,'Otra zona') RETURNING id"), {"code":uuid4().hex})
    other = client.post(url, headers=headers[0], json={**payload, "zone_id": str(other_zone)}).json()
    assert client.get(url + "/" + other["id"], headers=headers[index]).status_code == 404
    assert client.get("/api/v1/coordinator/requests", headers=headers[index], params={"zone_id":str(other_zone)}).json() == []


def test_login_throttle(pilot):
    client, _, _ = pilot
    from ecoconecta.auth import digest
    with engine().begin() as db:
        db.execute(text("""
            INSERT INTO login_windows VALUES (:ip, now(), 20)
            ON CONFLICT (source_digest) DO UPDATE SET attempts=20,started_at=now()
        """), {"ip":digest("testclient")})
    response = login(client, 0, "invalid")
    assert response.status_code == 429
    assert response.json()["correlation_id"] == response.headers["X-Correlation-ID"]


def test_scheduling(pilot):
    from concurrent.futures import ThreadPoolExecutor
    from datetime import UTC, datetime, timedelta

    client, zone, password = pilot
    # This module shares the pilot fixture. Reset the synthetic peer after the throttle test.
    with engine().begin() as db:
        db.execute(text("DELETE FROM login_windows"))
    requester, coordinator, outsider = [
        {"Authorization": "Bearer " + login(client, index, password).json()["access_token"]}
        for index in (0, 2, 3)
    ]
    start = (datetime.now(UTC) + timedelta(days=8)).replace(hour=15, minute=0, second=0, microsecond=0)
    with engine().begin() as db:
        collector = str(db.scalar(text("""
            INSERT INTO users(full_name,phone,role,is_pilot)
            VALUES ('Recolector de prueba','+100000006','recolector',true) RETURNING id
        """)))
        member = db.scalar(text("""
            INSERT INTO collective_members(user_id,collective_id,member_role)
            SELECT :user,id,'recolector' FROM collectives WHERE flow='organico' RETURNING id
        """), {"user": collector})
        coverage = db.scalar(text("""
            INSERT INTO collector_zone_coverage(member_id,zone_id,valid_from)
            VALUES (:member,:zone,current_date) RETURNING id
        """), {"member": member, "zone": zone})
        db.execute(text("""
            INSERT INTO availability_slots(coverage_id,weekday,starts_at,ends_at,valid_from)
            VALUES (:coverage,:day,'09:00','12:00',current_date)
        """), {"coverage": coverage, "day": start.isoweekday()})

    urls = []
    for _ in range(2):
        new = client.post("/api/v1/requests", headers=requester, json={
            "generator":"hogar", "flow":"organico", "zone_id":zone, "address":"Prueba",
            "contact_phone":"+100000000", "preferred_time":"mañana",
        })
        rid = new.json()["id"]
        url = "/api/v1/requests/" + rid
        urls.append(url)
        candidates = "/api/v1/collectors/availability"
        assert client.get(candidates, params={"request_id":rid}, headers=outsider).status_code == 404
        assert client.get(candidates, params={"request_id":rid}, headers=coordinator).json()[0]["collector_id"] == collector
        assert client.post(url+"/review", headers=requester).status_code == 403
        assert client.post(url+"/review", headers=outsider).status_code == 404
        assign = url + "/assignments"
        assert client.post(assign, headers=coordinator, json={"collector_id":collector}).status_code == 409
        assert client.post(url+"/review", headers=coordinator).json()["status"] == "en_revision"
        assert client.post(assign, headers=coordinator, json={"collector_id":str(uuid4())}).status_code == 409
        assert client.post(assign, headers=coordinator, json={"collector_id":collector}).json()["status"] == "asignada"

    def window(begin, end):
        return {"scheduled_start":begin.isoformat(), "scheduled_end":end.isoformat()}

    end = start + timedelta(hours=1)
    def book(url, payload):
        return client.post(url+"/schedule", headers=coordinator, json=payload)

    assert book(urls[0], window(end,start)).status_code == 422
    assert book(urls[0], window(start.replace(tzinfo=None),end)).status_code == 422
    assert book(urls[0], window(start, end+timedelta(hours=3))).json()["code"] == "outside_availability"
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(lambda url: book(url, window(start,end)), urls))
    assert sorted(resp.status_code for resp in responses) == [201,409], [r.text for r in responses]
    loser = next(i for i,r in enumerate(responses) if r.status_code == 409)
    assert responses[loser].json()["code"] == "schedule_overlap"
    assert book(urls[loser], window(end,end+timedelta(hours=1))).status_code == 201
    for url in urls:
        detail = client.get(url, headers=requester).json()
        assert detail["collector_id"] == collector and detail["scheduled_start"] and detail["scheduled_end"]
        assert [h["to_status"] for h in detail["history"]] == ["recibida","en_revision","asignada","programada"]
        with engine().connect() as db:
            assert db.scalar(text("SELECT count(*) FROM audit_log WHERE entity_id=:id"),
                             {"id":detail["id"]}) == 3
