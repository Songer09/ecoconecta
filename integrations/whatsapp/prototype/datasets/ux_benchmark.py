"""Compara la API FastAPI de dos versiones contra las mismas frases y diálogos."""

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
from statistics import mean, median
import sys
from time import perf_counter
from uuid import uuid4

from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url


DATA = Path(__file__).resolve().parent


def load(name):
    return [json.loads(x) for x in (DATA / name).read_text().splitlines() if x]


def comprehension(classify, data, flows):
    from datasets.evaluation import evaluate

    summary = evaluate(classify, data)
    tp = expected = predicted = all_matches = flow_correct = flow_total = (
        quantity_ok
    ) = quantity_total = unit_ok = unit_total = 0
    multi = multi_ok = 0
    failures = []
    for case in data:
        result = classify(case["text"])
        got = (
            {x.name: (x.quantity, x.unit) for x in result.materials}
            if hasattr(result, "materials")
            else (
                {result.material: (result.quantity, result.unit)}
                if result.material
                else {}
            )
        )
        want = {x["name"]: (x["quantity"], x["unit"]) for x in case["materials"]}
        tp += len(got.keys() & want.keys())
        expected += len(want)
        predicted += len(got)
        all_matches += got.keys() == want.keys()
        if len(want) > 1:
            multi += 1
            multi_ok += got.keys() == want.keys()
        for item in case["materials"]:
            name = item["name"]
            if item["flow"]:
                flow_total += 1
                flow_correct += name in got and flows.get(name) == item["flow"]
            if item["quantity"] is not None:
                quantity_total += 1
                quantity_ok += name in got and got[name][0] == item["quantity"]
            if item["unit"] is not None:
                unit_total += 1
                unit_ok += name in got and got[name][1] == item["unit"]
        bad_quantities = {
            k: {"expected": v, "actual": got.get(k)}
            for k, v in want.items()
            if v[0] is not None and v != got.get(k)
        }
        if (
            result.intent != case["intent"]
            or result.scope != case["scope"]
            or got.keys() != want.keys()
            or bad_quantities
        ):
            failures.append(
                {
                    "id": case["id"],
                    "expected_intent": case["intent"],
                    "actual_intent": result.intent,
                    "expected_scope": case["scope"],
                    "actual_scope": result.scope,
                    "missing_materials": sorted(want.keys() - got.keys()),
                    "extra_materials": sorted(got.keys() - want.keys()),
                    "incorrect_quantities": bad_quantities,
                }
            )
    return {
        **summary,
        "material_recall": [tp, expected],
        "material_precision": [tp, predicted],
        "all_materials": [all_matches, len(data)],
        "all_materials_in_multi": [multi_ok, multi],
        "flow_accuracy": [flow_correct, flow_total],
        "quantities": [quantity_ok, quantity_total],
        "units": [unit_ok, unit_total],
        "failures": failures,
    }


def asked(reply):
    tests = {
        "material": r"¿qué material|¿me lo aclaras",
        "eligibility": r"¿quieres pedir revisión humana",
        "address": r"¿(?:en qué|cuál es la) dirección",
        "quantity": r"¿qué cantidad|¿cuál es la cantidad",
        "generator": r"¿la entrega es de",
        "preference": r"¿qué día|si tienes una preferencia",
    }
    return {k for k, pat in tests.items() if re.search(pat, reply.lower())}


def call(api, tokens, user, method, path, **args):
    r = api.request(
        method,
        "/api/v1/" + path,
        headers={"Authorization": "Bearer " + tokens[user]},
        **args,
    )
    r.raise_for_status()
    return r.json()


def report_dialogue(api, tokens, case):
    admin = "admin-demo"
    start = perf_counter()
    events = []
    seen = set()
    early = 0
    for turn in case["turns"] + [["Sí", []]]:
        phrase, fields = turn[:2]
        seen.update(fields)
        reply = call(
            api,
            tokens,
            "hogar-demo",
            "POST",
            "demo/messages",
            json={"text": phrase, "kind": turn[2] if len(turn) > 2 else "text"},
        )["reply"]
        prompts = asked(reply)
        events.append(
            {
                "asked": sorted(prompts),
                "redundant": sorted(prompts & seen),
                "reply": reply,
            }
        )
        if phrase != "Sí":
            early += bool(call(api, tokens, admin, "GET", "requests"))
    elapsed = perf_counter() - start
    records = call(api, tokens, admin, "GET", "requests")
    points = call(
        api,
        tokens,
        "hogar-demo",
        "POST",
        "demo/messages",
        json={"text": "¿Cuántos puntos tengo?"},
    )["reply"]
    routed = Counter()
    actual = {}
    for row in records:
        details = call(api, tokens, admin, "GET", "requests/" + row["id"])
        actual.setdefault(row["flow"], []).extend(
            i["material"] for i in details.get("items", [row])
        )
        target = "coord-huerta" if row["flow"] == "organic" else "coord-reciclaje"
        routed[row["id"]] = sum(
            a["request_id"] == row["id"]
            for a in call(api, tokens, target, "GET", "alerts")
        )
    actual = {flow: sorted(items) for flow, items in actual.items()}
    expected = {flow: sorted(items) for flow, items in case["materials"].items()}
    return {
        "id": case["id"],
        "complete": actual == expected and len(records) == len(expected),
        "expected": expected,
        "actual": actual,
        "replies": len(events),
        "responses_until_registration": len(events) if records else None,
        "clarifications": sum(bool(e["asked"]) for e in events),
        "redundant_questions": sum(bool(e["redundant"]) for e in events),
        "required_kg": sum(
            bool(re.search(r"¿[^?]*(?:en kg|en kilos|en kilogramos)", e["reply"], re.I))
            for e in events
        ),
        "human_review": any("aviso para revisión humana" in e["reply"] for e in events),
        "routing_errors": sum(value != 1 for value in routed.values())
        + sum(
            items.count(material)
            for flow, items in actual.items()
            for material in set(items) - set(expected.get(flow, []))
        ),
        "without_confirmation": early,
        "automatic_schedule": sum(row["status"] != "recibida" for row in records),
        "early_points": not points.startswith("Tienes 0 puntos"),
        "registration_seconds": round(elapsed, 5) if records else None,
        "turns": events,
    }


def safety(api, tokens, db):
    # Explicitly synthetic account, signature and event. Never sends a network request to Meta.
    db.exec_driver_sql(
        "UPDATE users SET phone='570000000001' WHERE handle='hogar-demo'"
    )
    # This commit makes the synthetic sender available to the in-process API transaction.
    db.commit()
    raw = json.dumps(
        {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "id": "ux-account",
                    "changes": [
                        {
                            "field": "messages",
                            "value": {
                                "metadata": {"phone_number_id": "123"},
                                "messages": [
                                    {
                                        "id": "wamid.ux-repeat",
                                        "from": "570000000001",
                                        "timestamp": str(
                                            int(datetime.now(timezone.utc).timestamp())
                                        ),
                                        "type": "text",
                                        "text": {"body": "Hola"},
                                    }
                                ],
                            },
                        }
                    ],
                }
            ],
        }
    ).encode()
    valid = (
        "sha256=" + hmac.new(b"synthetic-ux-secret", raw, hashlib.sha256).hexdigest()
    )
    path = "/api/v1/integrations/whatsapp/webhook"
    codes = [
        api.post(path, content=raw, headers={"x-hub-signature-256": valid}).status_code
        for _ in range(2)
    ]
    from app.worker import incoming

    incoming()
    count = db.exec_driver_sql(
        "SELECT count(*) FROM messages WHERE external_id='wamid.ux-repeat'"
    ).scalar()
    event = call(
        api,
        tokens,
        "hogar-demo",
        "POST",
        "demo/messages",
        json={"text": "¿Cuál es la siguiente jornada?"},
    )["reply"]
    return {
        "duplicate_rows": max(0, count - 1),
        "valid_webhook_errors": sum(c != 200 for c in codes),
        "invalid_signature_rejected": api.post(path, content=raw).status_code == 403,
        "invented_event": not event.startswith("Todavía no hay"),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--app-dir", type=Path, default=DATA.parent)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    directory = args.app_dir.resolve()
    os.chdir(directory)
    sys.path.insert(0, str(directory))
    base = create_engine(
        make_url(os.environ["TEST_DATABASE_URL"]).set(drivername="postgresql+psycopg")
    )
    schema = "ecoux_" + uuid4().hex
    with base.begin() as db:
        db.exec_driver_sql(f"CREATE SCHEMA {schema}")
    os.environ.update(
        DATABASE_URL=base.url.update_query_dict(
            {"options": "-csearch_path=" + schema}
        ).render_as_string(hide_password=False),
        APP_ENV="test",
        AI_PROVIDER="mock",
        WHATSAPP_PROVIDER="mock",
        META_APP_SECRET="synthetic-ux-secret",
        META_PHONE_NUMBER_ID="123",
        META_WABA_ID="ux-account",
    )
    try:
        command.upgrade(Config(str(directory / "alembic.ini")), "head")
        from app.language import classify
        from app.db import engine
        from app.main import app, buckets
        from app.seed import demo

        with engine.begin() as db:
            tokens = demo(db)
            flows = dict(
                db.exec_driver_sql(
                    "SELECT name,flow FROM materials WHERE accepted"
                ).all()
            )
        journeys = []
        with TestClient(app) as api:
            for case in load("ux_dialogos.jsonl"):
                buckets.clear()
                with engine.begin() as db:
                    db.exec_driver_sql(
                        "TRUNCATE materials,users,articles,events RESTART IDENTITY CASCADE"
                    )
                    tokens = demo(db)
                journeys.append(report_dialogue(api, tokens, case))
            with engine.connect() as db:
                checks = safety(api, tokens, db)
        successes = [x for x in journeys if x["complete"]]
        prompts = sum(j["clarifications"] for j in journeys)
        safety_keys = (
            "without_confirmation",
            "automatic_schedule",
            "early_points",
            "required_kg",
        )
        outcome = {
            "n": len(journeys),
            "completed": len(successes),
            "clarifications": prompts,
            "redundant_questions": sum(x["redundant_questions"] for x in journeys),
            "cases_with_repetition_needed": sum(
                x["redundant_questions"] > 0 for x in journeys
            ),
            "mean_replies_all": mean(x["replies"] for x in journeys),
            "early_confirmation": sum(x["without_confirmation"] for x in journeys),
            "mean_replies_completed": mean(x["replies"] for x in successes)
            if successes
            else None,
            "median_replies_completed": median(x["replies"] for x in successes)
            if successes
            else None,
            "mean_registration_seconds_completed": mean(
                x["registration_seconds"] for x in successes
            )
            if successes
            else None,
            "median_registration_seconds_completed": median(
                x["registration_seconds"] for x in successes
            )
            if successes
            else None,
            "mean_clarifications": mean(x["clarifications"] for x in journeys),
            "human_review_cases": sum(x["human_review"] for x in journeys),
            "routing_errors": sum(x["routing_errors"] for x in journeys),
            **{key: sum(x[key] for x in journeys) for key in safety_keys},
            **checks,
        }
        result = {
            "provider": "mock",
            "additional_challenge": comprehension(
                classify, load("ux_reto_adicional.jsonl"), flows
            ),
            "comprehension": comprehension(
                classify, load("ux_intenciones.jsonl"), flows
            ),
            "dialogue": outcome,
            "cases": journeys,
        }
        output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
        print(json.dumps(outcome, ensure_ascii=False))
        engine.dispose()
    finally:
        with base.begin() as db:
            db.exec_driver_sql(f"DROP SCHEMA {schema} CASCADE")
        base.dispose()


if __name__ == "__main__":
    main()
