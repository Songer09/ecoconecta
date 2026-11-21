import json
import re
from uuid import uuid4
from app.db import query, one
from app.language import (
    norm,
    materials,
    SPECIAL,
    UNSAFE,
    OTHER,
    EDUCATION,
    INFORMATION,
    Interpretation,
)
from app.entities import amount, correction, mentions
from app.analytics import record
from app.providers import understand
from app.operations import create, history, declared_items, store_item
from app.knowledge import agenda, education, BOGOTA
from app.dialogue import (
    Dialogue,
    approval,
    navigation,
    save_context,
    simple_response,
    snapshot,
)

LIMIT = "Soy el asistente ambiental de EcoConecta. Puedo ayudarte con residuos, recolecciones y actividades de Villas de San Pablo."
CLARIFY = "Cuéntame un poco más para poder ayudarte. Si hablas de un residuo, dime cuál tienes en mente."
INTRO = (
    "Hola, soy EcoConecta, tu asistente ambiental de Villas de San Pablo.\n\n"
    "Puedo ayudarte a solicitar recolecciones de residuos, aprender sobre reciclaje y compostaje, "
    "o consultar actividades y capacitaciones de la comunidad.\n\n"
    "Cuéntame qué necesitas. También puedes enviarme una nota de voz."
)
ID = re.compile(r"\b(?:eco-)?([0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12})\b", re.I)
ADDRESS = re.compile(
    r"\b(?:manzana|mz|calle|carrera|cra|diagonal|transversal|avenida|conjunto|bloque|lote|barrio|casa|local)"
    r"\s+(?:\d[\w# -]{0,45}|[a-z][\w -]{0,45})"
    r"(?:,\s*(?:casa|local|lote|apto|apartamento)\s+[\w# -]{1,30})?"
)
PREF = re.compile(
    r"\b(?:pasado manana|manana|lunes|martes|miercoles|jueves|viernes|sabado|domingo|"
    r"(?:por|en) la (?:tarde|noche|manana)|sin preferencia|cualquier horario|"
    r"\d{1,2}/\d{1,2}(?:/\d{2,4})?|[01]?\d:[0-5]\d|2[0-3]:[0-5]\d)\b"
    r"(?:\s+(?:(?:por|en|de) la (?:manana|tarde|noche)|a las \d{1,2}(?::\d{2})?))?"
)
CLARIFICATIONS = {
    "plástico": {"botellas PET", "botellas de plástico"},
    "residuos de cocina": {"cáscaras", "restos vegetales", "café", "hojas"},
}
AMBIGUOUS = set(CLARIFICATIONS)


def save(db, uid, draft):
    query(
        db,
        """INSERT INTO conversations(user_id,draft) VALUES(:u,CAST(:d AS jsonb))
      ON CONFLICT(user_id) DO UPDATE SET draft=EXCLUDED.draft""",
        u=uid,
        d=json.dumps(draft, ensure_ascii=False),
    )


def catalog(db, mat):
    return one(db, "SELECT flow FROM materials WHERE name=:m AND accepted", m=mat)


def review(db, uid, attempt=None):
    record(db, "escalated", attempt, reason="human_review")
    query(db, "INSERT INTO alerts(kind,user_id) VALUES('revisión humana',:u)", u=uid)
    return "Dejé un aviso para revisión humana. Coordinación debe verificar el material antes de solicitar una recolección."


def summary(item):
    name = item.get("label") or item["material"]
    if item.get("quantity") is not None:
        desc = item.get("description")
        size = re.search(r"\b(grandes?|pequenas?|llenas?|median[ao]s?)$", desc or "")
        quantity = f"{item['quantity']:g} {item['unit']}"
        if (
            item["unit"]
            in {
                "bolsas",
                "cajas",
                "botellas",
                "baldes",
                "canecas",
                "costales",
                "unidades",
            }
            and item["quantity"] == 1
        ):
            quantity = (
                quantity.rstrip("s")
                if item["unit"] not in {"costales", "unidades"}
                else "1 " + {"costales": "costal", "unidades": "unidad"}[item["unit"]]
            )
        if size:
            quantity += " " + size[0]
        return f"{'aprox. ' if item.get('approximate') else ''}{quantity} de {name}"
    return f"{name} ({item.get('description') or 'cantidad sin indicar'})"


def missing(db, uid, draft, fields, text, state):
    draft["waiting"] = "details"
    draft["last_asked"] = fields
    state.ask("review" if fields == ["eligibility"] else "details")
    record(db, "missing_asked", draft.get("attempt"), fields=fields)
    save(db, uid, draft)
    return text


def progress(db, uid, d, state):
    state.primary = "collection"
    state.current = "collection"
    if special := d.get("unresolved", {}).get("special"):
        extra = (
            " Puedes decir «solo los demás» para continuar con el material reconocido."
            if d.get("items")
            else ""
        )
        return missing(
            db,
            uid,
            d,
            ["eligibility"],
            f"{special.capitalize()} requiere revisión. ¿Quieres pedir revisión humana?{extra}",
            state,
        )
    if d.get("unresolved"):
        labels = ", ".join(d["unresolved"].values())
        suffix = (
            " Puedes decir «solo los demás» para continuar con los materiales reconocidos."
            if d.get("items")
            else ""
        )
        return missing(
            db,
            uid,
            d,
            ["material"],
            f"Me falta confirmar qué material es o si la ruta recibe: {labels}. ¿Me lo aclaras?{suffix}",
            state,
        )
    if not d.get("items"):
        return missing(
            db,
            uid,
            d,
            ["material"],
            "¿Qué material tienes listo? Puedes decir, por ejemplo, cartón o cáscaras.",
            state,
        )
    if not d.get("address"):
        material = d["items"][0]["material"] if len(d["items"]) == 1 else None
        flow = catalog(db, material) if material else None
        team = {"organic": "huerteros", "recyclable": "recicladores"}
        lead = (
            f"Puedo avisar al equipo de {team[flow['flow']]} por tu {material}. "
            if flow
            else ""
        )
        return missing(
            db,
            uid,
            d,
            ["address"],
            lead + "¿En qué dirección o referencia lo tienes?",
            state,
        )
    if item := next((i for i in d["items"] if i.get("location_pending")), None):
        kind = (
            "item_address"
            if item["location_pending"] == "different"
            else "same_address"
        )
        state.ask(kind, material=item["material"])
        save(db, uid, d)
        if kind == "item_address":
            return "¿En qué dirección están los residuos que acabas de agregar?"
        return f"¿Los residuos que agregaste también están en {d['address']}?"
    state.suspended = None
    groups = {}
    for item in d["items"]:
        mat = catalog(db, item["material"])
        flow = mat["flow"] if mat else "pending"
        groups.setdefault((flow, item.get("address", d["address"])), []).append(
            summary(item)
        )
    labels = {"organic": "Huerta", "recyclable": "Reciclaje", "pending": "Por revisar"}
    parts = [
        f"{labels[flow]} · {', '.join(items)}"
        + (f" en {address}" if address != d["address"] else "")
        for (flow, address), items in groups.items()
    ]
    where = f"Lugar: {d['address']}."
    when = f" Preferencia: {d['preference']}." if d.get("preference") else ""
    split = " Se enviará un aviso por colectivo." if len(groups) > 1 else ""
    d["waiting"] = "confirm"
    d.pop("last_asked", None)
    operation = "update" if d.get("edit") else "register"
    state.ask(operation, fingerprint=approval(operation, d))
    save(db, uid, d)
    return f"{' / '.join(parts)}. {where}{when}{split} ¿Confirmas el aviso? Coordinación te confirmará la visita."


def address_and_preference(d, text, s, result):
    pref = PREF.search(s)
    if pref:
        d["preference"] = text[pref.start() : pref.end()].strip(" ,.")
    elif result:
        verified = [
            value for value in (result.date, result.time) if value and norm(value) in s
        ]
        if verified:
            d["preference"] = " ".join(verified)
    address_start = ADDRESS.search(s)
    if address_start:
        start = address_start.start()
        end = address_start.end()
        if pref and start < pref.start():
            end = min(end, pref.start())
        candidate = text[start:end]
        candidate = re.split(
            r"\s+(?:y\s+)?(?:pueden|puedes|podrian|pasen|hay|tengo|tenemos|queda(?:ria)? bien|para recoger)\b",
            candidate,
            maxsplit=1,
            flags=re.IGNORECASE,
        )[0]
        if re.search(
            r"\d|^(?:calle|barrio|conjunto|carrera|avenida|diagonal|transversal)\b",
            norm(candidate),
        ):
            d["address"] = candidate.strip(" ,.")
    elif "address" in d.get("last_asked", []) or d.get("waiting") == "address":
        candidate = text[: pref.start()] if pref else text
        candidate = re.sub(r"(?:[, ]+|[.])(?:y|para)?\s*$", "", candidate).strip()
        # Plain references are accepted in the answer to a location question.
        if 3 <= len(candidate) <= 160 and re.search(
            r"\b(?:frente|junto|esquina|al lado|detras|porter[ií]a|entrada|parque|iglesia|tienda)\b|\d",
            candidate,
            re.I,
        ):
            if not materials(norm(candidate)) and not amount(norm(candidate)):
                d["address"] = candidate


def original_excerpt(text, normalized, excerpt):
    start = normalized.find(excerpt) if excerpt else -1
    return text[start : start + len(excerpt)] if start >= 0 else excerpt


def slots(db, uid, d, text, result, state):
    text = text.strip()
    s = norm(text)
    if not d.get("attempt") and not d.get("edit"):
        d["attempt"] = str(uuid4())
        record(db, "request_started", d["attempt"])
    local = {hit.name: hit for hit in mentions(s)}
    for hit in result.materials:
        evidence = norm(hit.evidence)
        if (
            hit.name not in local
            and hit.name not in AMBIGUOUS
            and re.search(r"\b" + re.escape(evidence) + r"\b", s)
        ):
            if not mentions(evidence) and catalog(db, hit.name):
                local[hit.name] = hit.model_copy(
                    update={
                        "quantity": None,
                        "unit": None,
                        "description": None,
                        "approximate": False,
                    }
                )
    old = {i["material"]: i for i in d.get("items", [])}
    unresolved = d.setdefault("unresolved", {})
    if (
        unresolved
        and s in {"solo los demas", "continua con los demas", "solo los reconocidos"}
        and old
    ):
        unresolved.clear()
        return progress(db, uid, d, state)
    peers = re.split(r"\s+(?:y|e|junto con)\s+", s)
    if local and len(peers) > 1:
        for peer in peers[1:]:
            if (
                mentions(peer)
                or re.search(SPECIAL, peer)
                or PREF.search(peer)
                or ADDRESS.search(peer)
                or amount(peer)
            ):
                continue
            candidate = re.split(r"\s+(?:en|para|desde)\s+", peer, maxsplit=1)[0].strip(
                " ,.!?"
            )
            if re.fullmatch(
                r"(?:tambien )?(?:(?:un|una|unos|unas|varios|varias) )?[a-z][a-z ]{2,38}",
                candidate,
            ):
                if not re.search(
                    r"\b(?:pued\w*|necesit\w*|quier\w*|solicit\w*|"
                    r"recoj\w*|recolect\w*|retir\w*|pas\w*|avis\w*|"
                    r"entreg\w*|vengan|dispongo|tengo|de cada|recoger|gracias)\b",
                    candidate,
                ):
                    unresolved.setdefault("uncatalogued", candidate)
    special = re.search(SPECIAL, s)
    if special:
        chunks = re.split(r"\s+(?:y|e|junto con)\s+|[,;](?!\d)", s)
        flagged = {
            hit.name
            for chunk in chunks
            if re.search(SPECIAL, chunk)
            for hit in mentions(chunk)
        }
        unresolved["special"] = special[0]
        for name in flagged:
            local.pop(name, None)
            old.pop(name, None)
        if not old and not local:
            save(db, uid, {})
            state.finish("cancelled")
            return review(db, uid, d.get("attempt"))
    was_asking_material = "material" in d.get("last_asked", [])
    added = 0
    for name, hit in local.items():
        mat = catalog(db, name)
        if not mat or name in AMBIGUOUS:
            unresolved[name] = original_excerpt(text, s, hit.evidence)
            continue
        added += name not in old
        unresolved.pop(name, None)
        item = old.setdefault(name, {"material": name})
        if hit.evidence != norm(name):
            start = s.find(hit.evidence)
            item["label"] = (
                text[start : start + len(hit.evidence)] if start >= 0 else hit.evidence
            )
        if hit.quantity is not None or hit.description:
            item.update(
                quantity=hit.quantity,
                unit=hit.unit,
                approximate=hit.approximate,
                description=original_excerpt(text, s, hit.description),
            )
    if (
        added
        and was_asking_material
        and not special
        and not any(name in AMBIGUOUS or not catalog(db, name) for name in local)
    ):
        # A reply to the material clarification can supersede the unresolved label.
        # If several labels were pending, require an explicit acknowledgement first.
        if len(unresolved) <= 1 and "special" not in unresolved:
            unresolved.clear()
    for pending, alternatives in CLARIFICATIONS.items():
        if (
            was_asking_material
            and pending in unresolved
            and alternatives.intersection(local)
            and pending not in local
        ):
            if any(catalog(db, name) for name in alternatives.intersection(local)):
                unresolved.pop(pending, None)
    if local:
        record(db, "materials_identified", d.get("attempt"), count=len(local))
    if old and (not local or result.intent == "modify") and not special:
        target = next(iter(old.values())) if len(old) == 1 else None
        if result.intent == "modify" or (
            state.question and state.question.kind == "quantity"
        ):
            focus = (
                state.question.material
                if state.question and state.question.kind == "quantity"
                else (result.context_reference or state.focus)
            )
            target = old.get(focus, target)
        if len(local) == 1:
            target = old.get(next(iter(local)))
        candidate = (
            text
            if not local
            else re.sub(
                r"\b(?:"
                + "|".join(re.escape(hit.evidence) for hit in local.values())
                + r")\b",
                "",
                s,
            )
            .strip(" ,")
            .removeprefix("de ")
            .removesuffix(" de")
            .strip()
        )
        corrected = correction(norm(candidate), target or {})
        if corrected and not target:
            answer = missing(
                db,
                uid,
                d,
                ["quantity_target"],
                "¿De cuál material quieres indicar esa cantidad?",
                state,
            )
            state.ask("quantity", value=candidate.strip()[:120])
            return answer
        if (
            corrected
            and target
            and not any(hit.quantity is not None for hit in local.values())
        ):
            corrected["description"] = original_excerpt(
                text, s, corrected.get("description")
            )
            target.update(corrected)
    d["items"] = list(old.values())
    if re.search(r"\b(negocio|tienda|unidad productiva|restaurante|empresa)\b", s):
        d["generator"] = "unidad productiva"
    elif re.search(r"\b(hogar|mi casa)\b", s):
        d["generator"] = "hogar"
    address_and_preference(d, text, s, result)
    return progress(db, uid, d, state)


def education_reply(db, text, result):
    named = materials(norm(text))
    if len(named) > 1:
        return "\n".join(
            f"{name.capitalize()}: {education(db, name)}" for name in named
        )
    return education(db, text, result.topic)


def owned(db, uid, text):
    match = ID.search(text)
    return (
        one(
            db,
            """SELECT r.*,s.scheduled_at,u.handle AS collector FROM collection_requests r
       LEFT JOIN schedules s ON s.request_id=r.id LEFT JOIN assignments a ON a.request_id=r.id
       LEFT JOIN users u ON u.id=a.collector_id WHERE owner_id=:u
       AND (CAST(:id AS uuid) IS NULL OR r.id=CAST(:id AS uuid)) ORDER BY created_at DESC,r.id LIMIT 1 FOR UPDATE OF r""",
            u=uid,
            id=match.group(1) if match else None,
        )
        if match or "eco-" not in norm(text)
        else None
    )


def save_confirmed_request(db, uid, draft, state):
    if any(not catalog(db, item["material"]) for item in draft["items"]):
        state.interrupt(True)
        return review(db, uid, draft.get("attempt"))
    if draft.get("edit"):
        rid = draft["edit"]
        request = owned(db, uid, rid)
        if not request or request["status"] != "recibida":
            state.finish("cancelled")
            save(db, uid, {})
            return (
                "El aviso ya está en gestión. Coordinación puede ayudarte a corregirlo."
            )
        item = next(i for i in draft["items"] if i["material"] == request["material"])
        query(
            db,
            "UPDATE collection_requests SET quantity=:q,unit=:unit,preference=:p,address=:a WHERE id=:r",
            r=rid,
            q=item.get("quantity"),
            unit=item.get("unit"),
            p=draft["preference"],
            a=draft["address"],
        )
        for item in draft["items"]:
            store_item(db, rid, item)
        history(db, rid, "corregida", uid)
        response = f"Aviso ECO-{rid} actualizado."
    else:
        record(db, "request_confirmed", draft.get("attempt"))
        ids = create(db, uid, draft)
        count = len(ids.split(", "))
        record(db, "request_registered", draft.get("attempt"), count=count)
        record(db, "routed_to_coordinator", draft.get("attempt"), count=count)
        response = f"Aviso recibido: {ids}. Coordinación revisará la solicitud. Aún no hay visita programada."
        if count > 1:
            response = f"Listo, registré los avisos: {ids}. Cada equipo revisará su disponibilidad y te confirmará la visita."
    save(db, uid, {})
    state.finish("completed")
    return response


def cancel_confirmed(db, uid, rid):
    request = owned(db, uid, rid)
    if not request or request["status"] not in ("recibida", "asignada"):
        return "El estado ya cambió. Solicita contacto con coordinación."
    query(
        db,
        "UPDATE collection_requests SET status='cancelada' WHERE id=:r",
        r=request["id"],
    )
    history(db, request["id"], "cancelada", uid)
    return "Solicitud cancelada."


def information(db, uid, draft, intent, text, result):
    if intent in ("training", "event"):
        return agenda(db, intent, text)
    if intent == "points":
        val = one(
            db,
            """SELECT coalesce(sum(points),0) AS n FROM points_ledger
            JOIN collection_requests r ON r.id=request_id WHERE r.owner_id=:u""",
            u=uid,
        )
        return f"Tienes {val['n']:g} puntos acreditados."
    if intent == "track":
        request = owned(db, uid, text)
        if not request:
            return "No encuentro esa solicitud entre las tuyas."
        reply = f"ECO-{request['id']}: {request['status']}."
        if request["scheduled_at"]:
            reply += f" Programación: {request['scheduled_at'].astimezone(BOGOTA):%d/%m/%Y %H:%M}, {request['collector']}."
        return reply
    if intent == "human":
        return review(db, uid, draft.get("attempt"))
    return education_reply(db, text, result)


def resume(db, uid, draft, state):
    if not draft:
        state.interrupt(False)
        return "No tienes un aviso pendiente. Cuéntame qué residuos tienes si quieres avisar a coordinación."
    prefix = "Retomemos tu aviso. "
    if state.suspended and state.suspended.kind in (
        "quantity",
        "address",
        "preference",
        "correction_field",
    ):
        state.question = state.suspended
        state.suspended = None
        state.phase = "collecting"
        question = state.question
        return (
            prefix
            + {
                "quantity": "¿Qué cantidad quieres corregir?"
                if question.material
                else "¿De cuál material quieres indicar la cantidad?",
                "address": "¿Cuál es la dirección correcta?",
                "preference": "¿Qué día u horario te queda bien? Puedes decir «sin preferencia».",
                "correction_field": "¿Qué dato quieres corregir?",
            }[question.kind]
        )
    return prefix + progress(db, uid, draft, state)


def optional_preference(db, uid, draft, state):
    if draft.get("preference") or not draft.get("address"):
        return progress(db, uid, draft, state)
    state.ask("preference")
    return "¿Qué día y horario te quedan bien? Si te da igual, puedes decir «sin preferencia»."


def accepted_offer(db, uid, draft, state, text, result):
    offer = state.question
    s = norm(text)
    if not catalog(db, offer.material):
        state.interrupt(bool(draft))
        return (
            "Ese material requiere revisión antes de que pueda incluirlo en tu aviso."
        )
    description = amount(s)
    if description:
        description["description"] = original_excerpt(
            text, s, description["description"]
        )
    tentative = {}
    address_and_preference(tentative, text, s, result)
    item = {"material": offer.material, "label": offer.label, **description}
    if (
        tentative.get("address")
        and draft.get("address")
        and tentative["address"] != draft["address"]
    ):
        item["address"] = tentative["address"]
    elif tentative.get("address"):
        draft["address"] = tentative["address"]
    if tentative.get("preference"):
        draft["preference"] = tentative["preference"]
    if not any(i["material"] == item["material"] for i in draft["items"]):
        draft["items"].append(item)
        record(db, "materials_identified", draft.get("attempt"), count=1)
    state.focus = offer.material
    save(db, uid, draft)
    if (
        draft.get("address")
        and not tentative.get("address")
        and not re.search(r"\bmisma direccion\b", s)
    ):
        item["location_pending"] = "shared"
        save(db, uid, draft)
        state.ask("same_address", material=offer.material)
        labels = " y ".join(summary(i) for i in draft["items"])
        return f"Anoté {labels}. ¿Los residuos que acabas de agregar también están en {draft['address']}?"
    return optional_preference(db, uid, draft, state)


def follow_up(db, uid, draft, state, text, response, allow_confirmation):
    """Resolve only the active question. Unrelated input reaches interpretation."""
    question = state.question
    if not question:
        return None
    kind = question.kind
    s = norm(text).strip(" ¡!.")
    if kind in ("register", "update", "cancel") and response:
        if not allow_confirmation:
            return "Por favor confirma esa decisión por escrito."
        if kind == "cancel":
            if question.fingerprint != approval("cancel", {"id": question.request_id}):
                state.interrupt(bool(draft))
                return "Indícame de nuevo cuál aviso quieres cancelar."
            state.interrupt(bool(draft))
            return (
                cancel_confirmed(db, uid, question.request_id)
                if response == "yes"
                else "Dejé el aviso registrado como estaba."
            )
        if response == "no":
            if draft.get("attempt"):
                record(db, "request_abandoned", draft["attempt"], reason="declined")
            state.finish("cancelled")
            save(db, uid, {})
            return "Descarté el cambio pendiente."
        if (
            not draft.get("address")
            or not draft.get("items")
            or draft.get("unresolved")
        ):
            return resume(db, uid, draft, state)
        if question.fingerprint != approval(kind, draft):
            return progress(db, uid, draft, state)
        return save_confirmed_request(db, uid, draft, state)
    if kind == "offer_material":
        if response == "no":
            return "Entendido, era solo una consulta. " + resume(db, uid, draft, state)
        if response == "yes" or (
            amount(s)
            and re.match(r"^(?:si\b|como\b|aproximadamente\b|un[ao]?\b|[\d])", s)
        ):
            return accepted_offer(db, uid, draft, state, text, None)
    if kind in ("same_address", "item_address"):
        new_item = next(
            (i for i in draft.get("items", []) if i["material"] == question.material),
            None,
        )
        if new_item is None:
            state.interrupt(bool(draft))
            return None
        if kind == "same_address" and response == "yes":
            new_item.pop("location_pending", None)
            save(db, uid, draft)
            return optional_preference(db, uid, draft, state)
        if kind == "same_address" and response == "no":
            new_item["location_pending"] = "different"
            save(db, uid, draft)
            state.ask("item_address", material=question.material)
            return "¿En qué dirección están los residuos que acabas de agregar?"
        if "?" not in text:
            tentative = {"last_asked": ["address"]} if kind == "item_address" else {}
            address_and_preference(tentative, text, s, None)
            if tentative.get("address"):
                new_item["address"] = tentative["address"]
                new_item.pop("location_pending", None)
                if tentative.get("preference"):
                    draft["preference"] = tentative["preference"]
                save(db, uid, draft)
                return optional_preference(db, uid, draft, state)
    if kind == "reference":
        explicit = materials(s)
        if len(explicit) == 1:
            state.interrupt(bool(draft))
            state.topics = explicit
            return education(db, explicit[0]) + (
                " Tu borrador sigue pendiente." if draft else ""
            )
    if kind == "quantity" and not question.material and question.value:
        selected = [i for i in draft.get("items", []) if i["material"] in materials(s)]
        if len(selected) == 1:
            selected[0].update(correction(question.value, selected[0]))
            state.focus = selected[0]["material"]
            return progress(db, uid, draft, state)
    if kind == "preference" and (
        response == "no" or s in {"sin preferencia", "me da igual"}
    ):
        draft.pop("preference", None)
        return progress(db, uid, draft, state)
    if kind == "review" and response == "yes":
        if not allow_confirmation:
            return "Por favor confirma esa decisión por escrito."
        if draft.get("review_requested"):
            return "La revisión ya está solicitada. Puedes decir «solo los demás» para avanzar con lo demás."
        draft["review_requested"] = True
        save(db, uid, draft)
        return (
            review(db, uid, draft.get("attempt"))
            + " Puedes decir «solo los demás» para continuar."
        )
    return None


def correction_target(db, uid, draft, state, text, result):
    s = norm(text)
    field = (
        "address"
        if re.search(r"\b(?:direccion|ubicacion|referencia)\b", s)
        else "preference"
        if re.search(r"\b(?:hora|horario|preferencia|dia)\b", s)
        else "quantity"
        if re.search(r"\b(?:cantidad|kilos?|bolsas?|baldes?|cajas?|son|eran)\b", s)
        else result.correction_field
    )
    if not field:
        state.ask("correction_field")
        return "¿Qué dato quieres corregir?"
    if field == "address":
        # When the resident contrasts an old and new address, parse only the replacement.
        replacement = re.split(
            r"[,;.]?\s+(?:sino(?: que)?|la correcta es|es en|es)\s+",
            text,
            maxsplit=1,
            flags=re.I,
        )[-1]
        probe = (
            {"last_asked": ["address"]}
            if state.question and state.question.kind == "address"
            else {}
        )
        address_and_preference(probe, replacement, norm(replacement), result)
        negated = re.search(r"\b(?:no era|no es|incorrecta|esta mal)\b", s)
        if probe.get("address") and (not negated or replacement != text):
            draft["address"] = probe["address"]
            return progress(db, uid, draft, state)
        state.ask("address")
        return "¿Cuál es la dirección correcta?"
    if field == "preference":
        if PREF.search(s):
            return slots(db, uid, draft, text, result, state)
        state.ask("preference")
        return "¿Qué nuevo día u horario te queda bien?"
    named = [
        name
        for name in materials(s)
        if any(i["material"] == name for i in draft["items"])
    ]
    target = (
        named[0]
        if len(named) == 1
        else draft["items"][0]["material"]
        if len(draft["items"]) == 1
        else None
    )
    if amount(s) or correction(s, {"unit": "unidades"}):
        return slots(db, uid, draft, text, result, state)
    state.ask("quantity", material=target)
    return (
        "¿Qué cantidad quieres corregir?"
        if target
        else "¿De cuál material quieres corregir la cantidad?"
    )


def _turn(db, uid, draft, state, text, allow_confirmation):
    s = norm(text).strip(" ¡!.")
    if s in ("acepto audio", "revoco audio"):
        query(
            db,
            """INSERT INTO consents VALUES(:u,:v,now())
            ON CONFLICT(user_id) DO UPDATE SET audio=:v,changed_at=now()""",
            u=uid,
            v=s == "acepto audio",
        )
        return "Permiso de voz actualizado. Puedes revocarlo con REVOCO AUDIO."
    if re.search(UNSAFE + "|" + OTHER, s):
        state.interrupt(bool(draft))
        record(
            db,
            "intent_identified",
            draft.get("attempt"),
            intent="offtopic",
            scope="OUT_OF_SCOPE",
        )
        return LIMIT
    movement = navigation(text)
    # A pause or undo revokes any active confirmation without erasing the draft.
    if movement == "pause":
        state.interrupt(bool(draft), paused=True)
        return (
            "Claro, cuéntame tu otra pregunta. Guardé tu aviso para retomarlo después."
            if draft
            else "Claro, cuéntame tu pregunta."
        )
    if movement == "resume":
        return resume(db, uid, draft, state)
    if movement == "undo":
        if not draft or state.undo is None:
            return "No hay un cambio reciente que pueda deshacer."
        draft.clear()
        draft.update(state.undo)
        state.undo = None
        save(db, uid, draft)
        return "Deshice el último cambio. " + resume(db, uid, draft, state)
    response = simple_response(text)
    if contextual := follow_up(
        db, uid, draft, state, text, response, allow_confirmation
    ):
        return contextual
    if response:
        if draft:
            return resume(db, uid, draft, state)
        return "Cuéntame qué necesitas y seguimos desde ahí."
    bare_question = "?" in text or bool(
        re.match(r"\b(?:como|que|cual|cuando|donde|puedo)\b", s)
    )
    question = state.question
    # Plain responses to a pickup or correction address are interpreted locally.
    private_turn = not bare_question and (
        (question and question.kind in ("address", "item_address"))
        or ("address" in draft.get("last_asked", []) and not draft.get("address"))
    )
    result = understand(
        text,
        context=state.for_provider(draft),
        local_only=bool(private_turn or ID.search(text)),
        observe=lambda event, **attrs: record(db, event, draft.get("attempt"), **attrs),
    )
    intent = result.intent
    state.current = intent
    state.secondary = [item.intent for item in result.secondary_intents]
    record(
        db, "intent_identified", draft.get("attempt"), intent=intent, scope=result.scope
    )
    if intent == "hello":
        if (
            draft
            and state.question
            and state.question.kind in ("register", "update", "cancel")
        ):
            state.interrupt(True)
        if not state.introduced and not draft and state.phase == "idle":
            state.introduced = True
            return INTRO
        if draft:
            return "Hola, tu aviso sigue pendiente. Dime si quieres retomarlo."
        state.introduced = True
        return "Hola, qué gusto saludarte. Cuéntame en qué te ayudo."
    if intent == "bye":
        state.interrupt(bool(draft), paused=True)
        return (
            "Gracias. Guardé tu aviso para cuando quieras retomarlo."
            if draft
            else "Gracias por participar en EcoConecta."
        )
    if (
        result.requested_navigation in ("resume", "pause")
        and result.scope == "IN_SCOPE"
        and intent == "ambiguous"
    ):
        if result.requested_navigation == "resume":
            return resume(db, uid, draft, state)
        state.interrupt(bool(draft), paused=True)
        return "Te escucho. Podemos retomar el aviso después."
    if re.search(
        r"^(?:y )?(?:el otro|la otra|ese|esa|el de antes|la de antes)(?:[ ?.!]|$)",
        s.strip("¿"),
    ):
        options = list(
            dict.fromkeys(
                [
                    *state.topics,
                    *[i.get("label") or i["material"] for i in draft.get("items", [])],
                ]
            )
        )
        state.interrupt(bool(draft))
        if options:
            state.ask("reference")
            return f"¿Te refieres a {' o a '.join(options[-3:])}?"
    if intent == "cancel":
        if draft and not ID.search(text):
            if not re.search(r"\b(?:cancel\w*|anul\w*|desistir|descarta\w*)\b", s):
                state.interrupt(True, paused=True)
                return "Dejé el borrador guardado. Si quieres eliminarlo, dime «cancela mi solicitud»."
            if not allow_confirmation:
                return "Confirma por escrito si quieres descartar el borrador."
            if draft.get("attempt"):
                record(
                    db, "request_abandoned", draft["attempt"], reason="cancelled_draft"
                )
            save(db, uid, {})
            state.finish("cancelled")
            return "Descarté el borrador."
        request = owned(db, uid, text)
        if request and request["status"] in ("recibida", "asignada"):
            rid = str(request["id"])
            state.ask(
                "cancel", request_id=rid, fingerprint=approval("cancel", {"id": rid})
            )
            return f"¿Confirmas cancelar ECO-{rid}?"
        state.interrupt(bool(draft))
        return "No encuentro una solicitud propia disponible para cancelar."
    if intent == "modify" and not draft:
        request = owned(db, uid, text)
        if not request or request["status"] != "recibida":
            return (
                "Solo puedes corregir un aviso propio que siga pendiente de revisión."
            )
        draft.update(
            {k: request[k] for k in ("preference", "address", "generator")},
            edit=str(request["id"]),
            items=[
                {
                    "material": i["material"],
                    "quantity": float(i["quantity"])
                    if i["quantity"] is not None
                    else None,
                    "unit": i["unit"],
                    "approximate": i["approximate"],
                    "description": i["description"],
                }
                for i in declared_items(db, request["id"])
            ],
        )
        state.primary = "collection"
        save(db, uid, draft)
        if not (
            amount(s)
            or result.correction_field
            or re.search(r"\b(?:cantidad|direccion|horario|preferencia)\b", s)
        ):
            state.ask(
                "quantity",
                material=draft["items"][0]["material"]
                if len(draft["items"]) == 1
                else None,
            )
            return "¿Qué cantidad quieres corregir? Puedes decirme bolsas, cajas o la medida que tengas."
    if draft and (
        intent == "modify" or (question and question.kind == "correction_field")
    ):
        if (
            draft.get("edit")
            and materials(s)
            and not set(materials(s)).issubset({i["material"] for i in draft["items"]})
        ):
            return "Para cambiar de material, cancela el aviso y crea otro."
        if amount(s) or correction(s, {"unit": "unidades"}):
            return slots(db, uid, draft, text, result, state)
        return correction_target(db, uid, draft, state, text, result)
    if draft and question and question.kind == "address" and not bare_question:
        return correction_target(db, uid, draft, state, "dirección " + text, result)
    primary_text = result.primary_text or text
    clauses = [
        (intent, primary_text, result),
        *[
            (
                extra.intent,
                extra.text,
                Interpretation(
                    scope="IN_SCOPE", intent=extra.intent, topic=extra.topic
                ),
            )
            for extra in result.secondary_intents
        ],
    ]
    collection = [phrase for label, phrase, _ in clauses if label == "collection"]
    information_clauses = [
        (label, phrase, part)
        for label, phrase, part in clauses
        if label in INFORMATION | {"human"}
    ]
    if result.scope == "OUT_OF_SCOPE" and not (
        draft
        and question
        and question.kind in ("quantity", "preference")
        and not bare_question
    ):
        state.interrupt(bool(draft))
        return LIMIT
    if collection and result.scope == "IN_SCOPE":
        answers = [
            information(db, uid, draft, label, phrase, part)
            for label, phrase, part in information_clauses
        ]
        if draft.get("edit") and any(
            name not in {i["material"] for i in draft["items"]}
            for name in materials(norm(" y ".join(collection)))
        ):
            return "Para agregar material, primero termina la corrección de tu aviso."
        main = slots(db, uid, draft, " y ".join(collection), result, state)
        return "\n\n".join([*answers, main])
    if information_clauses:
        # A bare material during a draft can answer a clarification. Questions stay read-only.
        bare_material = (
            draft
            and len(information_clauses) == 1
            and intent in EDUCATION
            and not bare_question
            and not result.primary_text
        )
        if bare_material and state.phase == "collecting":
            return slots(db, uid, draft, text, result, state)
        replies = [
            information(db, uid, draft, label, phrase, part)
            for label, phrase, part in information_clauses
        ]
        state.interrupt(bool(draft))
        topics = list(
            dict.fromkeys(
                m
                for label, phrase, _ in information_clauses
                if label in EDUCATION
                for m in materials(norm(phrase))
            )
        )
        if topics:
            state.topics = topics
        if (
            draft
            and len(information_clauses) == 1
            and intent in EDUCATION
            and not draft.get("edit")
            and len(topics) == 1
        ):
            named = topics[0]
            if (
                catalog(db, named)
                and named not in {i["material"] for i in draft.get("items", [])}
                and not re.search(SPECIAL, s)
            ):
                hit = next((m for m in mentions(s) if m.name == named), None)
                label = (
                    original_excerpt(text.strip(), s, hit.evidence) if hit else named
                )
                state.ask("offer_material", material=named, label=label)
                state.phase = "interrupted"
                return "\n\n".join(
                    [*replies, f"¿También tienes {label} para entregar?"]
                )
        return "\n\n".join(replies) + (" Tu borrador sigue pendiente." if draft else "")
    if (
        re.search(r"\bcajas?\b", s)
        and re.search(r"\b(?:que hago|que hacer|no se|llena de)\b", s)
        and not materials(s)
    ):
        state.interrupt(bool(draft))
        return "Si son cajas de cartón, sepáralas limpias y secas. ¿Son de cartón y quieres que avise a recicladores?"
    if draft:
        if state.phase == "paused" and not any(
            (PREF.search(s), ADDRESS.search(s), amount(s))
        ):
            return "Tu aviso sigue guardado. Dime qué necesitas o cuándo quieres retomarlo."
        if question and question.kind == "cancel":
            state.interrupt(bool(draft))
            return resume(db, uid, draft, state)
        return slots(db, uid, draft, text, result, state)
    return CLARIFY


def handle(db, uid, text, *, allow_confirmation=True):
    one(db, "SELECT id FROM users WHERE id=:u AND active FOR UPDATE", u=uid)
    before = one(db, "SELECT draft,context FROM conversations WHERE user_id=:u", u=uid)
    draft = before["draft"] if before else {}
    state = Dialogue.model_validate(before["context"] if before else {})
    previous = snapshot(draft)
    reply = _turn(db, uid, draft, state, text, allow_confirmation)
    after = one(db, "SELECT draft FROM conversations WHERE user_id=:u", u=uid)
    current = after["draft"] if after else {}
    if (
        current
        and previous
        and snapshot(current) != previous
        and navigation(text) != "undo"
    ):
        state.undo = previous
    save_context(db, uid, state)
    record(db, "bot_reply", current.get("attempt") or previous.get("attempt"))
    return reply
