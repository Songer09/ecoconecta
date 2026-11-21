from fastapi import HTTPException
from datetime import datetime, timezone
from app.db import one, query, rows, audit
from app.knowledge import BOGOTA


def history(db, rid, status, actor):
    query(
        db,
        "INSERT INTO request_status_history(request_id,status,actor) VALUES(:r,:s,:a)",
        r=rid,
        s=status,
        a=actor,
    )
    audit(db, actor, status, rid)


def notify(db, user, kind, body):
    query(
        db,
        "INSERT INTO notifications(user_id,kind,body) VALUES(:u,:k,:b)",
        u=user,
        k=kind,
        b=body,
    )


def store_item(db, rid, item):
    query(
        db,
        """INSERT INTO collection_request_items(request_id,material,quantity,unit,approximate,description)
           VALUES(:r,:m,:q,:u,:approx,:description)
           ON CONFLICT(request_id,material) DO UPDATE SET quantity=:q,unit=:u,
              approximate=:approx,description=:description""",
        r=rid,
        m=item["material"],
        q=item.get("quantity"),
        u=item.get("unit"),
        approx=item.get("approximate", False),
        description=item.get("description"),
    )


def create(db, user, draft):
    groups = {}
    for item in sorted(draft["items"], key=lambda item: item["material"]):
        mat = one(
            db,
            "SELECT flow FROM materials WHERE name=:name AND accepted FOR SHARE",
            name=item["material"],
        )
        if not mat:
            raise HTTPException(
                409, "La aceptación del material cambió. Consulta coordinación."
            )
        groups.setdefault(
            (mat["flow"], item.get("address") or draft["address"]), []
        ).append(item)
    ids = []
    for (flow, address), items in groups.items():
        primary = items[0]
        rid = one(
            db,
            """INSERT INTO collection_requests(owner_id,material,flow,quantity,unit,address,generator,preference)
               VALUES(:owner,:material,:flow,:quantity,:unit,:address,:generator,:preference) RETURNING id""",
            owner=user,
            flow=flow,
            material=primary["material"],
            quantity=primary.get("quantity"),
            unit=primary.get("unit"),
            address=address,
            generator=draft.get("generator", "sin indicar"),
            preference=draft.get("preference", "sin preferencia"),
        )["id"]
        for item in items:
            store_item(db, rid, item)
        history(db, rid, "recibida", user)
        query(
            db,
            "INSERT INTO alerts(request_id,flow,kind,user_id) VALUES(:r,:f,'nuevo aviso',:u)",
            r=rid,
            f=flow,
            u=user,
        )
        for coord in rows(
            db,
            "SELECT id FROM users WHERE active AND role='coordinator' AND flow=:f",
            f=flow,
        ):
            notify(
                db,
                coord["id"],
                "alert",
                f"Nuevo aviso ECO-{rid}. Consulta la bandeja de tu colectivo.",
            )
        ids.append("ECO-" + str(rid))
    return ", ".join(ids)


def declared_items(db, rid):
    return rows(
        db,
        """SELECT i.material,i.quantity,i.unit,i.approximate,i.description,
        c.quantity AS verified_quantity,c.unit AS verified_unit,
        CASE WHEN c.unit='kg' THEN c.quantity END AS verified_weight_kg
        FROM collection_request_items i LEFT JOIN collected_items c USING(request_id,material)
        WHERE i.request_id=:r ORDER BY i.material""",
        r=rid,
    )


def visible(db, rid, actor, lock=False):
    sql = """SELECT r.*,a.collector_id,a.coordinator_id,s.scheduled_at FROM collection_requests r
        LEFT JOIN assignments a ON r.id=a.request_id LEFT JOIN schedules s ON r.id=s.request_id
        WHERE r.id=:rid AND (:role='admin' OR (r.owner_id=:uid AND :role='resident')
        OR (r.flow=:flow AND :role='coordinator') OR (a.collector_id=:uid AND :role='collector'))"""
    row = one(
        db,
        sql + (" FOR UPDATE OF r" if lock else ""),
        rid=rid,
        role=actor["role"],
        uid=actor["id"],
        flow=actor["flow"],
    )
    if not row:
        raise HTTPException(404, "Solicitud no disponible")
    return row


def transition(db, rid, actor, action, data):
    row = visible(db, rid, actor, True)
    uid = actor["id"]
    if action in ("assign", "schedule") and actor["role"] != "coordinator":
        raise HTTPException(403, "Se requiere coordinación del colectivo")
    if action == "assign":
        collector = one(
            db,
            "SELECT id FROM users WHERE id=:id AND active AND role='collector' AND flow=:f FOR SHARE",
            id=data.collector_id,
            f=row["flow"],
        )
        if row["status"] != "recibida" or not collector:
            raise HTTPException(409, "Verifica el estado y el recolector del colectivo")
        query(
            db,
            "INSERT INTO assignments VALUES(:r,:u,:c)",
            r=rid,
            u=uid,
            c=data.collector_id,
        )
        status = "asignada"
    elif action == "schedule":
        if row["status"] != "asignada" or data.scheduled_at <= datetime.now(
            timezone.utc
        ):
            raise HTTPException(409, "Se requiere asignación y una fecha futura")
        query(
            db,
            "INSERT INTO schedules VALUES(:r,:t,:u)",
            r=rid,
            t=data.scheduled_at,
            u=uid,
        )
        handle = one(
            db, "SELECT handle FROM users WHERE id=:id", id=row["collector_id"]
        )["handle"]
        notify(
            db,
            row["owner_id"],
            "schedule",
            f"ECO-{rid} programada para {data.scheduled_at.astimezone(BOGOTA):%d/%m/%Y %H:%M}. Responsable: {handle}.",
        )
        status = "programada"
    elif action == "collect":
        if actor["role"] != "collector" or row["collector_id"] != uid:
            raise HTTPException(403, "Se requiere el recolector asignado")
        expected = {item["material"] for item in declared_items(db, rid)}
        if data.items is not None:
            actual = {item.material: (item.quantity, item.unit) for item in data.items}
        else:
            actual = {row["material"]: (data.quantity, data.unit)}
        if set(actual) != expected:
            raise HTTPException(
                409, "Verifica la cantidad y unidad de todos los materiales del aviso."
            )
        if row["status"] == "recolectada":
            events = rows(
                db,
                "SELECT material,quantity,unit FROM collected_items WHERE request_id=:r",
                r=rid,
            )
            if actual != {e["material"]: (e["quantity"], e["unit"]) for e in events}:
                raise HTTPException(
                    409, "El cierre existente tiene otras cantidades o unidades."
                )
            return {"status": "recolectada"}
        if row["status"] != "programada":
            raise HTTPException(409, "Falta la programación")
        primary_amount, primary_unit = actual[row["material"]]
        query(
            db,
            "INSERT INTO collection_events(request_id,actor,quantity,unit) VALUES(:r,:u,:q,:unit)",
            r=rid,
            u=uid,
            q=primary_amount,
            unit=primary_unit,
        )
        for material, (quantity, unit) in actual.items():
            query(
                db,
                "INSERT INTO collected_items(request_id,material,quantity,unit) VALUES(:r,:m,:q,:unit)",
                r=rid,
                m=material,
                q=quantity,
                unit=unit,
            )
            query(
                db,
                """INSERT INTO points_ledger(request_id,material,rule_id,points)
                   SELECT :r,:m,id,rate*:q FROM points_rules WHERE material=:m AND unit=:unit
                    AND starts_at<=now() AND (ends_at IS NULL OR ends_at>now())
                   ORDER BY starts_at DESC,id DESC LIMIT 1""",
                r=rid,
                m=material,
                q=quantity,
                unit=unit,
            )
        status = "recolectada"
    else:
        raise ValueError("Acción desconocida")
    query(db, "UPDATE collection_requests SET status=:s WHERE id=:r", s=status, r=rid)
    history(db, rid, status, uid)
    return {"status": status}
