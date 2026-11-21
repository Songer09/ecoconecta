from dataclasses import replace
import json

import httpx


def say(ctx, text, **kwargs):
    return ctx.say(text, **kwargs)["reply"]


def records(ctx):
    return ctx.call("GET", "requests", "admin-demo").json()


def detail(ctx, rid):
    return ctx.call("GET", f"requests/{rid}").json()


def established(ctx, text="Hola, tengo dos bolsas de cartón"):
    assert "dirección" in say(ctx, text)
    assert "Confirmas" in say(ctx, "Manzana 12, casa 8")


def test_first_greeting_is_explanatory_and_not_repeated(ctx):
    introduction = say(ctx, "Hola")
    assert "Villas de San Pablo" in introduction and "nota de voz" in introduction
    assert "nota de voz" not in say(ctx, "Buenas tardes")
    assert "dirección" in say(ctx, "Tengo cartón")
    assert "nota de voz" not in say(ctx, "Hola de nuevo")


def test_resident_example_only_the_last_yes_registers(ctx):
    established(ctx)
    reply = say(ctx, "¿Y las cáscaras de banano se pueden reciclar?")
    assert all(word in reply for word in ("orgánicos", "compost", "También tienes"))
    assert records(ctx) == []
    reply = say(ctx, "Sí, como un balde")
    assert all(word in reply for word in ("balde", "cartón", "Manzana 12, casa 8"))
    assert records(ctx) == []
    assert "horario" in say(ctx, "Sí")
    assert records(ctx) == []
    assert "Confirmas" in say(ctx, "Mañana por la mañana")
    assert records(ctx) == []
    assert "registré los avisos" in say(ctx, "Sí")
    rows = records(ctx)
    assert len(rows) == 2
    byflow = {r["flow"]: detail(ctx, r["id"]) for r in rows}
    for request in byflow.values():
        assert request["address"] == "Manzana 12, casa 8"
        assert request["preference"] == "Mañana por la mañana"
        assert request["scheduled_at"] is None
    assert byflow["recyclable"]["items"][0]["quantity"] == 2
    organic = byflow["organic"]["items"][0]
    assert (
        organic["quantity"] == 1
        and organic["unit"] == "baldes"
        and organic["approximate"]
    )
    say(ctx, "Sí")
    assert len(records(ctx)) == 2


def test_two_interruptions_and_correction_after_resume(ctx):
    established(ctx)
    assert "Taller demo" in say(ctx, "¿Cuándo es el taller de compostaje?")
    assert "Café" in say(ctx, "¿Puedo compostar la borra de café?")
    assert "Confirmas" in say(ctx, "¿En qué íbamos?")
    assert "4 bolsas" in say(ctx, "Perdón, son cuatro")
    assert records(ctx) == []
    say(ctx, "Sí")
    (r,) = records(ctx)
    assert detail(ctx, r["id"])["address"] == "Manzana 12, casa 8"
    assert detail(ctx, r["id"])["items"][0]["quantity"] == 4


def test_side_question_decline_does_not_drop_or_add(ctx):
    say(ctx, "Tengo cartón para recoger")
    assert "También tienes" in say(ctx, "¿El papel periódico también sirve?")
    reply = say(ctx, "No, solo quería saber")
    assert "Retomemos" in reply and "dirección" in reply
    assert "Confirmas" in say(ctx, "Manzana 9 casa 2")
    say(ctx, "Sí")
    assert records(ctx)[0]["materials"] == ["cartón"]


def test_an_interruption_invalidates_previous_confirmation(ctx):
    established(ctx)
    assert "Todavía no hay" in say(ctx, "¿Qué eventos hay esta semana?")
    assert "Confirmas" in say(ctx, "Sí")
    assert records(ctx) == []
    say(ctx, "Sí")
    assert len(records(ctx)) == 1


def test_three_materials_add_correction_and_undo(ctx):
    say(ctx, "Tengo dos bolsas de cartón y un balde de cáscaras")
    say(ctx, "También tengo cinco botellas")
    say(ctx, "Manzana 7 casa 4")
    assert "4 bolsas" in say(ctx, "Perdón, son cuatro bolsas de cartón")
    assert "2 bolsas" in say(ctx, "Olvida lo último")
    assert "3 bolsas" in say(ctx, "Ahora son tres bolsas de cartón")
    say(ctx, "Sí")
    rows = records(ctx)
    assert len(rows) == 2
    items = {i["material"]: i for r in rows for i in detail(ctx, r["id"])["items"]}
    assert set(items) == {"cartón", "botellas", "cáscaras"}
    assert items["cartón"]["quantity"] == 3


def test_address_correction_and_pause_are_distinct(ctx):
    established(ctx)
    assert "guard" in say(ctx, "Después seguimos con eso").lower()
    assert "No" not in say(ctx, "Volvamos a lo anterior.")
    assert "dirección correcta" in say(ctx, "No, esa no era la dirección")
    assert "Papel" in say(ctx, "¿Sirve el papel para reciclar?")
    assert "dirección correcta" in say(ctx, "Regresa")
    new = say(ctx, "Manzana 10, casa 6")
    assert "Manzana 10, casa 6" in new and "Manzana 12" not in new
    say(ctx, "Sí")
    assert detail(ctx, records(ctx)[0]["id"])["address"] == "Manzana 10, casa 6"


def test_new_material_at_other_address_survives_interruption(ctx):
    established(ctx)
    say(ctx, "¿Y las cáscaras de banano se pueden compostar?")
    say(ctx, "Sí, como un balde")
    assert "dirección" in say(ctx, "No")
    say(ctx, "¿Cuándo es el taller de compostaje?")
    assert "dirección" in say(ctx, "Volvamos a lo anterior")
    say(ctx, "Manzana 2 casa 9")
    say(ctx, "Sin preferencia")
    say(ctx, "Sí")
    rows = {r["flow"]: detail(ctx, r["id"]) for r in records(ctx)}
    assert rows["recyclable"]["address"] == "Manzana 12, casa 8"
    assert rows["organic"]["address"] == "Manzana 2 casa 9"


def test_cancel_draft_and_registered_request_have_separate_actions(ctx):
    established(ctx)
    assert "Descarté el borrador" in say(ctx, "Cancela la solicitud")
    assert records(ctx) == []
    established(ctx)
    say(ctx, "Sí")
    rid = records(ctx)[0]["id"]
    assert "Confirmas cancelar" in say(ctx, "Cancela ECO-" + rid)
    say(ctx, "¿Qué eventos hay?")
    say(ctx, "Sí")
    assert detail(ctx, rid)["status"] == "recibida"
    say(ctx, "Cancela ECO-" + rid)
    assert "cancelada" in say(ctx, "Sí")
    assert detail(ctx, rid)["status"] == "cancelada"


def test_combined_collection_and_training(ctx):
    reply = say(
        ctx,
        "Tengo dos bolsas de plástico, quiero que las recojan y también saber cuándo es la próxima capacitación de compostaje",
    )
    assert all(word in reply for word in ("Taller demo", "plástico", "aclaras"))
    assert reply.index("Taller demo") < reply.index("Me falta")
    assert records(ctx) == []


def test_two_information_needs_and_indirect_or_negative_request(ctx):
    reply = say(ctx, "¿Hay eventos comunitarios? ¿Cómo separo el papel?")
    assert "Todavía no hay" in reply and "papel limpio y seco" in reply
    assert "cartón" in say(
        ctx, "Tengo la casa llena de cajas y ya no sé qué hacer con ellas"
    )
    reply = say(
        ctx, "No quiero recoger nada, solo necesito saber cómo separar el plástico"
    )
    assert "Vacía" in reply or "plástico" in reply or "residuos" in reply
    assert "Confirmas" not in reply and records(ctx) == []


def test_audio_carries_question_and_material_details(ctx):
    say(ctx, "ACEPTO AUDIO")
    reply = say(
        ctx,
        "Tengo dos bolsas de cartón en manzana 8 casa 1. ¿Cuándo es el taller de compostaje?",
        kind="demo_audio",
    )
    assert all(word in reply for word in ("Taller demo", "2 bolsas", "Confirmas"))
    assert "por escrito" in say(ctx, "Sí, envía los avisos", kind="demo_audio")
    assert records(ctx) == []
    say(ctx, "Sí")
    assert records(ctx)[0]["quantity"] == 2


def test_provider_receives_only_context_and_cannot_confirm(ctx, testdb, monkeypatch):
    from app import providers

    established(ctx)
    cfg = replace(testdb[-1], model="gemini-3.6-flash", key="synthetic")
    monkeypatch.setattr(providers, "settings", lambda: cfg)
    sent = []

    def gemini(url, **kwargs):
        payload = json.loads(kwargs["json"]["contents"][0]["parts"][0]["text"])
        sent.append(payload)
        model_data = {"scope": "IN_SCOPE", "intent": "material", "topic": "cafe borra"}
        return httpx.Response(
            200,
            request=httpx.Request("POST", url),
            json={
                "candidates": [
                    {"content": {"parts": [{"text": json.dumps(model_data)}]}}
                ]
            },
        )

    monkeypatch.setattr(providers.httpx, "post", gemini)
    assert "Café" in say(ctx, "¿Qué hago con lo que queda después de colar el tinto?")
    assert sent[0]["conversation_context"]["task"] == "collection"
    assert sent[0]["conversation_context"]["materials"] == ["cartón"]
    assert sent[0]["conversation_context"]["known_fields"] == ["address"]
    assert "Manzana" not in json.dumps(sent[0])
    assert "Confirmas" in say(ctx, "Sí")
    assert records(ctx) == []
    assert len(sent) == 1
