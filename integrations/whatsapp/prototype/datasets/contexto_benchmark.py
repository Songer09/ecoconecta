"""Pruebas comparables de intención y diálogo contra FastAPI y PostgreSQL."""

import argparse
from collections import defaultdict
import json
import os
from pathlib import Path
from statistics import mean, median
import sys
from uuid import uuid4

from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from datasets.ux_benchmark import DATA, asked, call, load


def contains(reply, tokens):
    return all(token.casefold() in reply.casefold() for token in tokens)


def measure_case(api, tokens, case):
    turns = []
    previous_count = 0
    known = set()
    for spec in case["turns"]:
        known.difference_update(spec.get("reset", []))
        known.update(spec.get("give", []))
        reply = call(
            api,
            tokens,
            "hogar-demo",
            "POST",
            "demo/messages",
            json={"text": spec["say"], "kind": spec.get("kind", "text")},
        )["reply"]
        requests = call(api, tokens, "admin-demo", "GET", "requests")
        delta = len(requests) - previous_count
        previous_count = len(requests)
        expected = spec.get("allow", 0)
        terms_ok = contains(reply, spec.get("match", []))
        exclusions_ok = not any(
            x.casefold() in reply.casefold() for x in spec.get("exclude", [])
        )
        turns.append(
            {
                "say": spec["say"],
                "reply": reply,
                "tags": spec.get("tag", []),
                "ok": terms_ok and exclusions_ok and delta == expected,
                "created": delta,
                "allowed": expected,
                "premature": max(0, delta - expected),
                "unnecessary": sorted(asked(reply) & known),
                "answers": [
                    contains(reply, terms) for terms in spec.get("answers", [])
                ],
            }
        )
    actual = {}
    states_ok = True
    for request in requests:
        detail = call(api, tokens, "hogar-demo", "GET", "requests/" + request["id"])
        states_ok &= request["status"] == "recibida" and detail["scheduled_at"] is None
        for item in detail["items"]:
            actual[item["material"]] = [
                item["quantity"],
                item["unit"],
                detail["address"],
                detail["preference"],
            ]
    expected_finish = case.get("finish")
    data_ok = actual == expected_finish if expected_finish else not actual
    return {
        "id": case["id"],
        "label": case["label"],
        "expected": expected_finish,
        "actual": actual,
        "completed": data_ok and states_ok and not any(t["premature"] for t in turns),
        "states_ok": states_ok,
        "turns": turns,
    }


def evaluate(cases):
    scores = defaultdict(list)
    turns = [turn for case in cases for turn in case["turns"]]
    for turn in turns:
        for tag in turn["tags"]:
            scores[tag].append(turn["ok"])
        if turn["answers"]:
            scores["primary_answer"].append(turn["answers"][0])
        if "multi" in turn["tags"]:
            scores["multi_recall"].extend(turn["answers"])
            scores["ignored_part"].append(not all(turn["answers"]))
    registered = [case for case in cases if case["expected"] and case["completed"]]
    counts = [len(case["turns"]) for case in registered]
    return {
        "scenarios": len(cases),
        "turns": len(turns),
        "checks": {key: [sum(vals), len(vals)] for key, vals in sorted(scores.items())},
        "completed_registrations": [
            len(registered),
            sum(bool(c["expected"]) for c in cases),
        ],
        "unnecessary_questions": sum(bool(t["unnecessary"]) for t in turns),
        "premature_creations": sum(t["premature"] for t in turns),
        "unexpected_community_facts": sum(not c["states_ok"] for c in cases)
        + sum(not t["ok"] for t in turns if "community_fact" in t["tags"]),
        "turns_to_complete": {"mean": mean(counts), "median": median(counts)}
        if counts
        else None,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--app-dir", type=Path, default=DATA.parent)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.app_dir.resolve()
    output = args.output.resolve()
    sys.path.insert(0, str(root))
    os.chdir(root)
    base = create_engine(
        make_url(os.environ["TEST_DATABASE_URL"]).set(drivername="postgresql+psycopg")
    )
    schema = "eco_context_" + uuid4().hex
    with base.begin() as db:
        db.exec_driver_sql(f"CREATE SCHEMA {schema}")
    os.environ.update(
        DATABASE_URL=base.url.update_query_dict(
            {"options": "-csearch_path=" + schema}
        ).render_as_string(hide_password=False),
        APP_ENV="test",
        AI_PROVIDER="mock",
        WHATSAPP_PROVIDER="mock",
    )
    try:
        command.upgrade(Config(str(root / "alembic.ini")), "head")
        from app.main import app, buckets
        from app.db import engine
        from app.seed import demo

        cases = []
        with TestClient(app) as api:
            for case in load("contexto_dialogos.jsonl"):
                buckets.clear()
                with engine.begin() as db:
                    db.exec_driver_sql(
                        "TRUNCATE materials,users,articles,events RESTART IDENTITY CASCADE"
                    )
                    tokens = demo(db)
                cases.append(measure_case(api, tokens, case))
        summary = evaluate(cases)
        print(json.dumps(summary, ensure_ascii=False))
        output.write_text(
            json.dumps(
                {"provider": "mock", "summary": summary, "cases": cases},
                indent=2,
                ensure_ascii=False,
            )
            + "\n"
        )
        engine.dispose()
    finally:
        with base.begin() as db:
            db.exec_driver_sql(f"DROP SCHEMA {schema} CASCADE")
        base.dispose()


if __name__ == "__main__":
    main()
