from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from ecoconecta.auth import hasher
from ecoconecta.db import engine
from ecoconecta.main import app


@pytest.fixture
def route_case(pilot, monkeypatch):
    _, zone, password = pilot
    phones = {index: f"+199{uuid4().int % 10**12:012d}" for index in (22, 23, 24)}
    monkeypatch.setenv("LIVE_TRACKING_ENABLED", "1")
    with engine().begin() as db:
        group = db.scalar(text("SELECT id FROM collectives WHERE flow='organico'"))
        owner = db.scalar(text("SELECT id FROM users WHERE phone='+100000000'"))
        isolated = db.scalar(
            text("INSERT INTO zones(code,name) VALUES (:code,'Zona QA') RETURNING id"),
            {"code": uuid4().hex},
        )
        for index, role in (
            (22, "recolector"),
            (23, "recolector"),
            (24, "coordinador_huerteros"),
        ):
            uid = db.scalar(
                text("""INSERT INTO users(full_name,phone,password_hash,role,is_pilot)
                VALUES ('QA',:phone,:hash,:role,true) RETURNING id"""),
                {"phone": phones[index], "hash": hasher.hash(password), "role": role},
            )
            if index == 22:
                collector = uid
                membership = db.scalar(
                    text("""INSERT INTO collective_members(user_id,collective_id,member_role)
                    VALUES (:uid,:group,'recolector') RETURNING id"""),
                    {"uid": uid, "group": group},
                )
                coverage = db.scalar(
                    text("""INSERT INTO collector_zone_coverage(member_id,zone_id,valid_from)
                    VALUES (:member,:zone,current_date-1) RETURNING id"""),
                    {"member": membership, "zone": zone},
                )
                db.execute(
                    text("""INSERT INTO availability_slots(coverage_id,weekday,starts_at,ends_at,valid_from)
                    SELECT :coverage,day,'08:00','18:00',current_date-1 FROM generate_series(1,7) day"""),
                    {"coverage": coverage},
                )
            if index == 24:
                member = db.scalar(
                    text("""INSERT INTO collective_members(user_id,collective_id,member_role)
                    VALUES (:uid,:group,'coordinador') RETURNING id"""),
                    {"uid": uid, "group": group},
                )
                db.execute(
                    text("INSERT INTO coordinator_zones VALUES (:member,:zone)"),
                    {"member": member, "zone": isolated},
                )
        coordinator = db.scalar(text("SELECT id FROM users WHERE phone='+100000002'"))
        request_id = db.scalar(
            text("""INSERT INTO pickup_requests(code,requester_id,collective_id,flow,
            zone_id,generator,contact_phone,address,status,source_channel)
            VALUES (:code,:owner,:group,'organico',:zone,'hogar','+100000000','Sintética','programada','web')
            RETURNING id"""),
            {"code": uuid4().hex, "owner": owner, "group": group, "zone": zone},
        )
        assignment = db.scalar(
            text("""INSERT INTO request_assignments(request_id,collector_id,coordinator_id)
            VALUES (:request,:collector,:coordinator) RETURNING id"""),
            {"request": request_id, "collector": collector, "coordinator": coordinator},
        )
        db.execute(
            text("""INSERT INTO request_schedules(request_id,assignment_id,scheduled_start,
                          scheduled_end,created_by,confirmed_by)
            VALUES (:request,:assignment,now(),now()+interval '1 hour',:coordinator,:coordinator)"""),
            {
                "request": request_id,
                "assignment": assignment,
                "coordinator": coordinator,
            },
        )
    with TestClient(app, client=(f"qa-{uuid4().hex}", 1234)) as client:
        sessions = {}
        for name, index in (
            ("owner", 0),
            ("coord", 2),
            ("other_flow", 3),
            ("collector", 22),
            ("other_collector", 23),
            ("other_zone", 24),
        ):
            result = client.post(
                "/api/v1/auth/login",
                json={
                    "phone": phones.get(index, f"+10000000{index}"),
                    "password": password,
                },
            )
            assert result.status_code == 200
            sessions[name] = {
                "Authorization": "Bearer " + result.json()["access_token"]
            }
        yield client, sessions, request_id, collector
    with engine().begin() as db:
        db.execute(
            text("DELETE FROM live_positions WHERE collector_id=:id"), {"id": collector}
        )


POSITION = "/api/v1/collector/location"
MAP = "/api/v1/coordinator/locations"


def test_latest_position_and_stop_are_private(route_case):
    client, auth, rid, collector = route_case
    payload = {
        "request_id": str(rid),
        "latitude": 10.9,
        "longitude": -74.8,
        "accuracy_m": 10,
    }
    assert (
        client.put(POSITION, headers=auth["other_collector"], json=payload).status_code
        == 404
    )
    assert client.get(MAP, headers=auth["owner"]).status_code == 403
    assert client.get(MAP, headers=auth["collector"]).status_code == 403
    for latitude in (10.9, 11.0):
        assert (
            client.put(
                POSITION,
                headers=auth["collector"],
                json={**payload, "latitude": latitude},
            ).status_code
            == 204
        )
    positions = client.get(MAP, headers=auth["coord"]).json()
    assert len(positions) == 1
    assert positions[0]["latitude"] == 11.0
    for role in ("other_flow", "other_zone"):
        assert client.get(MAP, headers=auth[role]).json() == []
    assert client.delete(POSITION, headers=auth["other_collector"]).status_code == 204
    assert len(client.get(MAP, headers=auth["coord"]).json()) == 1
    for _ in range(2):
        assert client.delete(POSITION, headers=auth["collector"]).status_code == 204
    assert client.get(MAP, headers=auth["coord"]).json() == []
    with engine().connect() as db:
        assert not db.scalar(
            text("SELECT 1 FROM live_positions WHERE collector_id=:id"),
            {"id": collector},
        )


def test_expired_position_cannot_be_viewed_or_verified(route_case):
    from ecoconecta.tracking import purge_expired

    client, auth, rid, collector = route_case
    payload = {
        "request_id": str(rid),
        "latitude": 10.9,
        "longitude": -74.8,
        "accuracy_m": 10,
    }
    assert (
        client.put(POSITION, headers=auth["collector"], json=payload).status_code == 204
    )
    with engine().begin() as db:
        db.execute(
            text(
                "UPDATE live_positions SET updated_at=now()-interval '5 minutes' WHERE collector_id=:id"
            ),
            {"id": collector},
        )
    assert client.get(MAP, headers=auth["coord"]).json() == []
    assert (
        client.post(
            f"/api/v1/coordinator/requests/{rid}/verify-location", headers=auth["coord"]
        ).status_code
        == 404
    )
    purge_expired()
    with engine().connect() as db:
        assert not db.scalar(
            text("SELECT 1 FROM live_positions WHERE collector_id=:id"),
            {"id": collector},
        )


def test_missed_stop_has_single_transition_and_no_credit(route_case):
    client, auth, rid, _ = route_case
    path = f"/api/v1/requests/{rid}/missed"
    reason = {"reason": "Incidencia sintética"}
    assert client.post(path, json=reason, headers=auth["collector"]).status_code == 403
    assert client.post(path, json=reason, headers=auth["other_zone"]).status_code == 404
    assert (
        client.post(path, json={"reason": " "}, headers=auth["coord"]).status_code
        == 422
    )
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(
            pool.map(
                lambda _: client.post(path, json=reason, headers=auth["coord"]),
                range(2),
            )
        )
    assert sorted(response.status_code for response in responses) == [200, 409]
    with engine().connect() as db:
        params = {"id": rid}
        assert (
            db.scalar(text("SELECT status FROM pickup_requests WHERE id=:id"), params)
            == "asignada"
        )
        assert db.scalars(
            text("SELECT reason FROM request_status_history WHERE request_id=:id"),
            params,
        ).all() == [reason["reason"]]
        assert db.scalars(
            text("SELECT is_current FROM request_schedules WHERE request_id=:id"),
            params,
        ).all() == [False]
        assert (
            db.scalar(
                text("SELECT is_current FROM request_assignments WHERE request_id=:id"),
                params,
            )
            is True
        )
        assert not db.scalar(
            text("SELECT 1 FROM collections WHERE request_id=:id"), params
        )


def test_position_not_reused_after_rescheduling(route_case):
    client, auth, rid, _ = route_case
    payload = {
        "request_id": str(rid),
        "latitude": 10.9,
        "longitude": -74.8,
        "accuracy_m": 10,
    }
    assert (
        client.put(POSITION, headers=auth["collector"], json=payload).status_code == 204
    )
    result = client.post(
        f"/api/v1/requests/{rid}/missed",
        headers=auth["coord"],
        json={"reason": "Parada fallida"},
    )
    assert result.status_code == 200
    assert client.get(MAP, headers=auth["coord"]).json() == []

    start = (datetime.now(timezone(timedelta(hours=-5))) + timedelta(days=2)).replace(
        hour=10, minute=0, second=0, microsecond=0
    )
    scheduled = client.post(
        f"/api/v1/requests/{rid}/schedule",
        headers=auth["coord"],
        json={
            "scheduled_start": start.isoformat(),
            "scheduled_end": (start + timedelta(hours=1)).isoformat(),
        },
    )
    assert scheduled.status_code == 201, scheduled.text
    assert client.get(MAP, headers=auth["coord"]).json() == []
