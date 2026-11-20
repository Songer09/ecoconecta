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


def test_collection_recording(pilot):
    from concurrent.futures import ThreadPoolExecutor

    client, zone, password = pilot
    with engine().begin() as db:
        db.execute(text("DELETE FROM login_windows"))
        ids = {}
        for index in (7, 8):
            ids[index] = db.scalar(text("""
                INSERT INTO users(full_name,phone,role,password_hash,is_pilot)
                VALUES ('Prueba',:phone,'recolector',:hash,true) RETURNING id
            """), {"phone":f"+10000000{index}", "hash":hasher.hash(password)})
        group = db.scalar(text("SELECT id FROM collectives WHERE flow='organico'"))
        db.execute(text("INSERT INTO collective_members(collective_id,user_id,member_role) VALUES (:g,:uid,'recolector')"),
                   {"g":group, "uid":ids[7]})
        coord = db.scalar(text("SELECT id FROM users WHERE phone='+100000002'"))
        requester = db.scalar(text("SELECT id FROM users WHERE phone='+100000000'"))
        rid = db.scalar(text("""
            INSERT INTO pickup_requests(code,requester_id,collective_id,flow,zone_id,generator,contact_phone,address,source_channel,status)
            VALUES ('TEST-COLLECTION',:uid,:g,'organico',:zone,'hogar','test','test','web','asignada') RETURNING id
        """), {"uid":requester,"zone":zone,"g":group})
        assignment = db.scalar(text("""
            INSERT INTO request_assignments(request_id,coordinator_id,collector_id)
            VALUES (:r,:coord,:collector) RETURNING id
        """), {"r":rid,"coord":coord,"collector":ids[7]})
        materials = {}
        for label, flow, active in (("A","organico",True),("B","reciclable",True),("C","organico",False)):
            materials[label] = str(db.scalar(text("""
                INSERT INTO waste_types(name,flow,unit,is_active) VALUES (:label,:flow,'test-unit',:active) RETURNING id
            """), {"label":label,"flow":flow,"active":active}))
    owner, other, resident = [
        {"Authorization":"Bearer "+login(client,index,password).json()["access_token"]} for index in (7,8,0)
    ]
    catalog = client.get("/api/v1/public/materials",params={"flow":"organico"}).json()
    assert [m["id"] for m in catalog] == [materials["A"]]
    inbox = "/api/v1/collector/requests"
    assert str(rid) in {r["id"] for r in client.get(inbox,headers=owner).json()}
    assert client.get(inbox,headers=other).json() == []
    url = f"/api/v1/requests/{rid}/collection"
    assert client.post(url,headers=owner).status_code == 409
    with engine().begin() as db:
        db.execute(text("""
            INSERT INTO request_schedules(request_id,assignment_id,scheduled_start,created_by,confirmed_by)
            VALUES (:r,:a,now(),:coord,:coord)
        """), {"r":rid,"a":assignment,"coord":coord})
        db.execute(text("UPDATE pickup_requests SET status='programada' WHERE id=:id"), {"id":rid})
    assert client.get(url,headers=owner).status_code == 404
    assert client.post(url,headers=resident).status_code == 403
    assert client.post(url,headers=other).status_code == 404
    with ThreadPoolExecutor(max_workers=2) as pool:
        opens = list(pool.map(lambda _: client.post(url,headers=owner), range(2)))
    assert sorted(r.status_code for r in opens) == [200,201]
    assert opens[0].json()["id"] == opens[1].json()["id"]
    items = "/api/v1/collections/" + opens[0].json()["id"] + "/items"
    def record(label="A", quantity="1.25", headers=owner):
        return client.post(items,headers=headers,json={"waste_type_id":materials[label],"quantity":quantity})
    assert record(headers=other).status_code == 404
    assert record("B").status_code == 422
    assert record("C").status_code == 422
    assert record(quantity="0").status_code == 422
    assert record(quantity="0.00001").status_code == 422
    with ThreadPoolExecutor(max_workers=2) as pool:
        saves = list(pool.map(lambda _: record(), range(2)))
    assert sorted(r.status_code for r in saves) == [200,201]
    assert record(quantity="2.5").json()["code"] == "material_already_recorded"
    assert client.get(url,headers=other).status_code == 404
    saved = client.get(url,headers=owner).json()
    assert saved["confirmed_at"] is None
    assert saved["items"] == [saves[0].json()]
    assert saved["items"][0]["unit"] == "test-unit"

    with engine().begin() as db:
        db.execute(text("UPDATE waste_types SET unit='kg' WHERE id=:id"), {"id":materials["A"]})
        db.execute(text("UPDATE collection_items SET unit='kg' WHERE collection_id=:id"),
                   {"id":saved["id"]})
        db.execute(text("""
            INSERT INTO users(full_name, phone, role, password_hash, is_pilot)
            VALUES ('Test admin','+100000009','administrador',:hash,true)
        """), {"hash":hasher.hash(password)})
    admin, coordinator, outsider = [
        {"Authorization":"Bearer "+login(client,index,password).json()["access_token"]}
        for index in (9,2,3)
    ]
    review = f"/api/v1/coordinator/requests/{rid}/collection"
    assert client.get(review,headers=coordinator).json()["id"] == saved["id"]
    assert client.get(review,headers=outsider).status_code == 404
    confirm = f"/api/v1/collections/{saved['id']}/confirm"
    weights = {"items":[{"waste_type_id":materials["A"],"quantity":"2.5"}]}
    assert client.post(confirm,headers=owner,json=weights).status_code == 403
    assert client.post(confirm,headers=outsider,json=weights).status_code == 404
    assert client.post(confirm,headers=coordinator,json=weights).json()["code"] == "points_rule_missing"
    assert client.get(url,headers=owner).json()["items"][0]["quantity"] == saved["items"][0]["quantity"]
    rates = "/api/v1/admin/points/rules/organic"
    payload = {"valid_from":"2000-01-01T00:00:00Z"}
    assert client.post(rates,headers=coordinator,json=payload).status_code == 403
    published = client.post(rates,headers=admin,json=payload)
    assert published.status_code == 201, published.text
    with ThreadPoolExecutor(max_workers=2) as pool:
        closures = list(pool.map(lambda _: client.post(confirm,headers=coordinator,json=weights), range(2)))
    assert all(response.status_code == 200 for response in closures), [r.text for r in closures]
    assert closures[0].json() == closures[1].json()
    assert float(closures[0].json()["points_awarded"]) == 25
    assert client.get(f"/api/v1/requests/{rid}",headers=resident).json()["status"] == "recolectada"
    assert float(client.get("/api/v1/users/me/points",headers=resident).json()["balance"]) == 25
    assert record(quantity="3").status_code == 409
    weights["items"][0]["quantity"] = "3"
    assert client.post(confirm,headers=coordinator,json=weights).status_code == 409

    # Separate recycling pickup. The coordinator may enter weights even if the field draft is empty.
    with engine().begin() as db:
        db.execute(text("UPDATE waste_types SET unit='kg' WHERE id=:id"), {"id":materials["B"]})
        group = db.scalar(text("SELECT id FROM collectives WHERE flow='reciclable'"))
        coord = db.scalar(text("SELECT id FROM users WHERE phone='+100000003'"))
        db.execute(text("INSERT INTO collective_members(collective_id,user_id,member_role) VALUES (:g,:u,'recolector')"),
                   {"g":group,"u":ids[7]})
        rid = db.scalar(text("""
            INSERT INTO pickup_requests(code,requester_id,collective_id,flow,zone_id,generator,contact_phone,address,source_channel,status)
            VALUES ('TEST-RECYCLING',:u,:g,'reciclable',:z,'hogar','test','test','web','programada') RETURNING id
        """), {"u":requester,"g":group,"z":zone})
        assignment = db.scalar(text("""
            INSERT INTO request_assignments(request_id,coordinator_id,collector_id)
            VALUES (:r,:coord,:u) RETURNING id
        """), {"r":rid,"coord":coord,"u":ids[7]})
        db.execute(text("""
            INSERT INTO request_schedules(request_id,assignment_id,scheduled_start,created_by,confirmed_by)
            VALUES (:r,:a,now(),:coord,:coord)
        """), {"r":rid,"a":assignment,"coord":coord})
    draft = client.post(f"/api/v1/requests/{rid}/collection",headers=owner).json()
    assert draft["items"] == []
    recycling_rate = f"/api/v1/admin/points/rules/{materials['B']}"
    for value in ("2","3.5"):
        published = client.post(recycling_rate,headers=admin,json={**payload,"points_per_kg":value})
        assert published.status_code == 201, published.text
    verified = {"items":[{"waste_type_id":materials["B"],"quantity":"2.25"}]}
    closed = client.post(f"/api/v1/collections/{draft['id']}/confirm",headers=outsider,json=verified)
    assert closed.status_code == 200, closed.text
    assert float(closed.json()["points_awarded"]) == 7.875
    assert float(client.get("/api/v1/users/me/points",headers=resident).json()["balance"]) == 32.875


def test_learning_progress(pilot):
    from concurrent.futures import ThreadPoolExecutor

    client, _, password = pilot
    catalog = "/api/v1/public/education"
    profile = "/api/v1/users/me/learning-progress"
    # Separate client IP keeps this scenario independent of earlier login throttle tests.
    with TestClient(app, client=("education-test", 1234)) as session:
        owner, other = [
            {"Authorization": "Bearer " + login(session, i, password).json()["access_token"]}
            for i in (0, 1)
        ]
    empty = {"total": 0, "completed": 0, "percentage": 0, "completions": []}
    assert client.get(profile, headers=owner).json() == empty
    with engine().begin() as db:
        ids = [str(db.scalar(text("""
            INSERT INTO educational_content(title, body, category, created_by, is_published)
            SELECT :title, 'Contenido', 'huerta', id, :published FROM users
            WHERE phone='+100000000' RETURNING id
        """), {"title": str(i), "published": i < 2})) for i in range(3)]
    assert {m["id"] for m in client.get(catalog).json()} == set(ids[:2])
    assert client.get(f"{catalog}/{ids[0]}").json()["body"] == "Contenido"
    assert client.get(f"{catalog}/{ids[2]}").status_code == 404
    assert client.put(f"{profile}/{ids[2]}", headers=owner).status_code == 404
    assert client.get(profile).status_code == 401
    url = f"{profile}/{ids[0]}"
    assert client.put(url).status_code == 401
    with ThreadPoolExecutor(max_workers=2) as pool:
        replies = list(pool.map(lambda _: client.put(url, headers=owner), range(2)))
    assert all(r.status_code == 200 for r in replies)
    assert replies[0].json() == replies[1].json()
    assert client.get(profile, headers=owner).json() == {
        "completed": 1, "total": 2, "percentage": 50, "completions": [replies[0].json()]
    }
    assert client.get(profile, headers=other).json()["completed"] == 0
    with engine().begin() as db:
        db.execute(text("UPDATE educational_content SET is_published=false WHERE id=:id"), {"id": ids[0]})
    assert client.get(profile, headers=owner).json() == {**empty, "total": 1}


def test_education_editorial_lifecycle(pilot):
    from concurrent.futures import ThreadPoolExecutor

    _, _, password = pilot
    with engine().begin() as db:
        db.execute(text("""
            INSERT INTO users(full_name, phone, role, password_hash, is_pilot)
            VALUES ('Editor de prueba', '+1000000014', 'administrador', :hash, true)
        """), {"hash": hasher.hash(password)})
    with TestClient(app, client=("editorial-test", 1234)) as client:
        admin, reader = [
            {"Authorization": "Bearer " + login(client, i, password).json()["access_token"]}
            for i in (14, 1)
        ]
        catalog = "/api/v1/admin/education"
        draft = {"title": " Guía ", "category": "huerta", "body": "Texto sintético", "flow": "organico"}
        assert client.post(catalog, json=draft).status_code == 401
        assert client.post(catalog, json=draft, headers=reader).status_code == 403
        for invalid in ({"title": " "}, {"body": "a\x00b"}, {"flow": "otro"}, {"is_published": True}):
            assert client.post(catalog, json={**draft, **invalid}, headers=admin).status_code == 422
        result = client.post(catalog, json=draft, headers=admin)
        assert result.status_code == 201, result.text
        module = result.json()
        assert module["title"] == "Guía" and module["is_published"] is False
        mid = module["id"]
        edit = f"{catalog}/{mid}"
        public = f"/api/v1/public/education/{mid}"
        assert client.get(public).status_code == 404
        assert client.get(edit, headers=reader).status_code == 403
        assert client.get(catalog, headers=reader).status_code == 403
        assert mid in [m["id"] for m in client.get(catalog, headers=admin).json()]
        assert client.get(edit, headers=admin).json() == module
        change = {**draft, "is_published": True, "expected_updated_at": module["updated_at"]}
        assert client.put(edit, json=change, headers=reader).status_code == 403
        with ThreadPoolExecutor(max_workers=2) as pool:
            writes = list(pool.map(lambda _: client.put(edit, json=change, headers=admin), range(2)))
        assert sorted(r.status_code for r in writes) == [200, 409]
        assert client.get(public).json()["title"] == "Guía"
        version = next(r.json()["updated_at"] for r in writes if r.status_code == 200)
        progress = f"/api/v1/users/me/learning-progress/{mid}"
        completion = client.put(progress, headers=reader).json()
        assert completion["module_id"] == mid
        for publish in (False, True):
            change.update(is_published=publish, expected_updated_at=version, body="Contenido corregido")
            response = client.put(edit, json=change, headers=admin)
            assert response.status_code == 200, response.text
            version = response.json()["updated_at"]
            assert client.get(public).status_code == (200 if publish else 404)
        assert client.get(public).json()["body"] == "Contenido corregido"
        assert client.put(progress, headers=reader).json() == completion
        with engine().connect() as db:
            actions = db.scalars(text("""
                SELECT action FROM audit_log WHERE entity='educational_content' AND entity_id=:id
            """), {"id": mid}).all()
        assert sorted(actions) == sorted(["education.created", "education.published",
                                          "education.withdrawn", "education.published"])


def test_public_event_agenda(pilot):
    from concurrent.futures import ThreadPoolExecutor
    from datetime import datetime, timedelta, timezone

    _, _, password = pilot
    with engine().begin() as db:
        db.execute(text("""
            INSERT INTO users(full_name, phone, role, password_hash, is_pilot)
            VALUES ('Prueba de agenda', '+1000000015', 'administrador', :hash, true)
        """), {"hash": hasher.hash(password)})
    with TestClient(app, client=("agenda-test", 1234)) as client:
        admin, reader = [
            {"Authorization": "Bearer " + login(client, i, password).json()["access_token"]}
            for i in (15, 0)
        ]
        now = datetime.now(timezone(timedelta(hours=-5)))
        draft = {"title": "Jornada sintética", "organizer": "Organización de prueba",
                 "description": "Evento de prueba", "location": "Lugar de prueba",
                 "starts_at": (now - timedelta(hours=1)).isoformat(),
                 "ends_at": (now + timedelta(hours=1)).isoformat()}
        catalog = "/api/v1/admin/events"
        public = "/api/v1/public/events"
        assert client.post(catalog, json=draft).status_code == 401
        assert client.post(catalog, headers=reader, json=draft).status_code == 403
        assert client.get(catalog, headers=reader).status_code == 403
        for invalid in ({"ends_at": draft["starts_at"]}, {"title": " "}, {"is_published": True},
                        {"starts_at": "2030-01-01T09:00:00"}, {"location": "x\x00y"}):
            assert client.post(catalog, headers=admin, json={**draft, **invalid}).status_code == 422
        result = client.post(catalog, headers=admin, json=draft)
        assert result.status_code == 201, result.text
        event = result.json()
        assert event["is_published"] is False
        assert client.get(catalog, headers=admin).json() == [event]
        edit = f"{catalog}/{event['id']}"
        detail = f"{public}/{event['id']}"
        assert client.get(detail).status_code == 404
        assert client.get(public).json() == []
        assert client.get(edit, headers=reader).status_code == 403
        assert client.get(edit, headers=admin).json() == event
        payload = {**draft, "expected_updated_at": event["updated_at"], "is_published": True}
        assert client.put(edit, headers=reader, json=payload).status_code == 403
        with ThreadPoolExecutor(max_workers=2) as pool:
            responses = list(pool.map(lambda _: client.put(edit, headers=admin, json=payload), range(2)))
        assert sorted(r.status_code for r in responses) == [200, 409]
        published = client.get(detail).json()
        assert client.get(public).json() == [published]
        assert datetime.fromisoformat(published["starts_at"]) == datetime.fromisoformat(draft["starts_at"])
        assert "created_by" not in published and "is_published" not in published
        version = next(r.json()["updated_at"] for r in responses if r.status_code == 200)
        payload.update(expected_updated_at=version, starts_at=(now - timedelta(days=2)).isoformat(),
                       ends_at=(now - timedelta(days=1)).isoformat())
        changed = client.put(edit, headers=admin, json=payload)
        assert changed.status_code == 200
        assert client.get(public).json() == []
        assert client.get(public, params={"include_past": True}).json() == [client.get(detail).json()]
        payload.update(expected_updated_at=changed.json()["updated_at"], is_published=False)
        assert client.put(edit, headers=admin, json=payload).status_code == 200
        assert client.get(detail).status_code == 404
        assert client.get(public, params={"include_past": True}).json() == []
        with engine().connect() as db:
            actions = db.scalars(text("""
                SELECT action FROM audit_log WHERE entity='community_events' AND entity_id=:id
            """), {"id": event["id"]}).all()
        assert sorted(actions) == sorted(["event.created", "event.published", "event.edited", "event.withdrawn"])


def test_community_and_pilot_management(pilot):
    _, _, password = pilot
    with engine().begin() as db:
        db.execute(text("""
            INSERT INTO users(full_name, phone, role, password_hash, is_pilot)
            VALUES ('Piloto', '+1000000016', 'administrador', :hash, true)
        """), {"hash": hasher.hash(password)})
    with TestClient(app, client=("pilot-management-test", 1234)) as client:
        info = client.get("/api/v1/public/community")
        assert info.status_code == 200
        assert [item["name"] for item in info.json()] == ["Villas de San Pablo", "Fundación Santo Domingo"]
        admin = {"Authorization": "Bearer " + login(client, 16, password).json()["access_token"]}
        url = "/api/v1/admin/users"
        data = {"full_name": "Residente", "phone": "+1000000017", "password": password}
        assert client.get(url).status_code == 401
        assert client.post(url, headers=admin, json={**data, "role": "administrador"}).status_code == 422
        created = client.post(url, headers=admin, json=data)
        assert created.status_code == 201, created.text
        assert created.json() in client.get(url, headers=admin).json()
        assert client.post(url, headers=admin, json=data).status_code == 409
        reader = {"Authorization": "Bearer " + login(client, 17, password).json()["access_token"]}
        access = f"{url}/{created.json()['id']}/pilot-access"
        assert client.put(access, headers=reader, json={"is_pilot": False}).status_code == 403
        for enabled in (False, False, True):
            assert client.put(access, headers=admin, json={"is_pilot": enabled}).json()["is_pilot"] == enabled
            assert client.get("/api/v1/auth/me", headers=reader).status_code == 401
            assert login(client, 17, password).status_code == (200 if enabled else 401)
