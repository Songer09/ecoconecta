import re
from datetime import datetime, timedelta, timezone
import pytest


def confirm(ctx, user="hogar-demo"):
    return re.findall(r"ECO-([a-f0-9-]{36})", ctx.say("Sí", user)["reply"])


def detail(ctx, rid, user="hogar-demo"):
    return ctx.call("GET", "requests/" + rid, user).json()


def test_one_turn_complete_keeps_location_time_and_approximation(ctx):
    r = ctx.say(
        "Buenas tardes, tengo unas tres bolsas de cartón en la manzana 12 casa 8 y pueden pasar mañana en la tarde"
    )["reply"]
    assert "¿Confirmas" in r and "aprox. 3 bolsas de cartón" in r
    assert "Manzana 12 casa 8".lower() in r and "mañana en la tarde" in r
    assert ctx.call("GET", "requests", "admin-demo").json() == []
    (rid,) = confirm(ctx)
    d = detail(ctx, rid)
    assert d["address"] == "manzana 12 casa 8"
    assert d["preference"] == "mañana en la tarde"
    assert d["generator"] == "sin indicar"
    (item,) = d["items"]
    assert item["quantity"] == 3 and item["unit"] == "bolsas" and item["approximate"]
    assert item["verified_weight_kg"] is None
    assert confirm(ctx) == []


def test_resident_provides_only_location(ctx):
    r = ctx.say("Tengo cartón")["reply"]
    assert "dirección" in r and "cantidad" not in r
    assert "¿Confirmas" in ctx.say("Manzana 9 casa 2")["reply"]
    (rid,) = confirm(ctx)
    assert detail(ctx, rid)["items"][0]["quantity"] is None
    assert detail(ctx, rid)["items"][0]["unit"] is None


def test_accumulated_cardboard_can_be_reported_without_quantity(ctx):
    reply = ctx.say("Tengo cartón acumulado y necesito que lo recojan")["reply"]
    assert "dirección" in reply and "cantidad" not in reply and "kg" not in reply
    assert ctx.call("GET", "requests", "admin-demo").json() == []

    reply = ctx.say("Manzana 9 casa 2")["reply"]
    assert "cartón (cantidad sin indicar)" in reply
    assert "¿Confirmas" in reply
    assert ctx.call("GET", "requests", "admin-demo").json() == []

    (rid,) = confirm(ctx)
    request = detail(ctx, rid)
    (item,) = request["items"]
    assert request["flow"] == "recyclable"
    assert item["material"] == "cartón"
    assert item["quantity"] is None and item["unit"] is None
    alerts = ctx.call("GET", "alerts", "coord-reciclaje").json()
    assert any(alert["request_id"] == rid for alert in alerts)


@pytest.mark.parametrize(
    ("phrase", "material", "value", "unit", "description"),
    [
        ("tengo una caja llena de botellas", "botellas", 1, "cajas", "una caja llena"),
        ("tengo un balde de cáscaras", "cáscaras", 1, "baldes", "un balde"),
        ("veinte botellas", "botellas", 20, "botellas", "veinte botellas"),
        (
            "tengo unas cinco bolsas grandes de papel",
            "papel",
            5,
            "bolsas",
            "unas cinco bolsas grandes",
        ),
        ("tengo bastante cartón", "cartón", None, None, "bastante"),
        (
            "tengo una cantidad pequeña de residuos orgánicos",
            "restos vegetales",
            None,
            None,
            "una cantidad pequeña",
        ),
        ("tengo cartón y no sé cuánto pesa", "cartón", None, None, "no sé cuánto pesa"),
    ],
)
def test_declaration_without_scale(ctx, phrase, material, value, unit, description):
    reply = ctx.say(phrase)["reply"]
    assert "dirección" in reply
    reply = ctx.say("Manzana 9 casa 2")["reply"]
    assert "¿Confirmas" in reply
    (rid,) = confirm(ctx)
    (item,) = detail(ctx, rid)["items"]
    assert (item["material"], item["quantity"], item["unit"], item["description"]) == (
        material,
        value,
        unit,
        description,
    )
    assert item["verified_weight_kg"] is None


def test_three_materials_two_alerts_and_multi_item_close(ctx):
    r = ctx.say(
        "Tengo dos bolsas de papel, tres costales de cartón y un balde de cáscaras, manzana 4 casa 3"
    )["reply"]
    assert "¿Confirmas" in r and all(m in r for m in ("papel", "cartón", "cáscaras"))
    ids = confirm(ctx)
    assert len(ids) == 2
    two = {d["flow"]: d for d in (detail(ctx, i) for i in ids)}
    assert [item["material"] for item in two["recyclable"]["items"]] == [
        "cartón",
        "papel",
    ]
    assert [item["material"] for item in two["organic"]["items"]] == ["cáscaras"]
    rid = two["recyclable"]["id"]
    assert ctx.call("GET", "alerts", "coord-reciclaje").json()[0]["request_id"] == rid
    assert (
        ctx.call("GET", "alerts", "coord-huerta").json()[0]["request_id"]
        == two["organic"]["id"]
    )
    path = "requests/" + rid
    staff = ctx.call("GET", "collectors", "coord-reciclaje").json()[0]
    assert (
        ctx.call(
            "POST",
            path + "/assign",
            "coord-reciclaje",
            json={"collector_id": staff["id"]},
        ).status_code
        == 200
    )
    date = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    assert (
        ctx.call(
            "POST", path + "/schedule", "coord-reciclaje", json={"scheduled_at": date}
        ).status_code
        == 200
    )
    assert (
        ctx.call(
            "POST",
            path + "/collect",
            "reciclador-demo",
            json={"quantity": 3, "unit": "kg"},
        ).status_code
        == 409
    )
    body = {
        "items": [
            {"material": "cartón", "quantity": 2, "unit": "costales"},
            {"material": "papel", "quantity": 3, "unit": "kg"},
        ]
    }
    for _ in range(2):
        assert (
            ctx.call(
                "POST", path + "/collect", "reciclador-demo", json=body
            ).status_code
            == 200
        )
    closed = detail(ctx, rid)
    assert closed["status"] == "recolectada"
    assert [item["verified_weight_kg"] for item in closed["items"]] == [None, 3]


def test_correction_addition_and_education_preserve_draft(ctx):
    ctx.say("Tengo tres bolsas de papel")
    r = ctx.say("También tengo cáscaras de banano")["reply"]
    assert "dirección" in r
    r = ctx.say("¿Cómo separo cáscaras de banano y papel?")["reply"]
    assert all(n in r.lower() for n in ("cáscaras", "papel", "borrador"))
    assert not confirm(ctx)
    ctx.say("Perdón, son cuatro bolsas de papel")
    r = ctx.say("Manzana 2 casa 3")["reply"]
    assert "4 bolsas de papel" in r and "cáscara" in r
    assert len(confirm(ctx)) == 2


def test_correction_inherits_unit(ctx):
    ctx.say("Tengo tres bolsas de papel")
    ctx.say("Perdón, son cuatro")
    r = ctx.say("Manzana 2 casa 3")["reply"]
    assert "4 bolsas de papel" in r
    (rid,) = confirm(ctx)
    assert detail(ctx, rid)["items"][0]["quantity"] == 4


def test_ambiguous_material_requires_resolution(ctx):
    r = ctx.say("Tengo plástico y cosas de la cocina, manzana 2 casa 4")["reply"]
    assert "plástico" in r and "cosas de la cocina" in r and "¿Confirmas" not in r
    assert not confirm(ctx)
    r = ctx.say("Tengo botellas de plástico y cáscaras")["reply"]
    assert "¿Confirmas" in r and "botellas de plástico" in r and "cáscaras" in r


def test_special_does_not_erase_accepted_material(ctx):
    r = ctx.say("Tengo cartón y pilas en manzana 4 casa 3")["reply"]
    assert "pilas" in r.lower() and "¿Confirmas" not in r
    assert "cartón" in ctx.say("solo los demás")["reply"]
    (rid,) = confirm(ctx)
    assert detail(ctx, rid)["items"][0]["material"] == "cartón"


def test_unpublished_event_and_anonymous_analytics(ctx):
    with ctx.engine.begin() as db:
        db.exec_driver_sql(
            "INSERT INTO events(kind,title,description,starts_at,place,organizer,category) VALUES "
            "('event','Jornada sin publicar','borrador',now()+interval '1 day','Demo','Demo','Reciclaje')"
        )
    assert (
        "Todavía no hay"
        in ctx.say("¿Cuándo es la próxima jornada comunitaria?")["reply"]
    )
    ctx.say("Tengo cartón")
    ctx.say("Manzana 2 casa 3")
    confirm(ctx)
    assert ctx.call("GET", "admin/metrics").status_code == 403
    report = ctx.call("GET", "admin/metrics", "admin-demo").json()
    assert report["journeys"][0]["completed"] == 1
    assert report["journeys"][0]["mean_replies"] == 3
    assert "Manzana" not in str(report)
    assert report["providers"] == []
