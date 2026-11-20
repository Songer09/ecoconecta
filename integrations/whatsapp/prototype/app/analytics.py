"""Eventos de producto sin teléfono, dirección, audio ni cuerpos de mensajes."""

import json
from app.config import settings
from app.db import query, rows

ALLOWED = {
    "intent",
    "scope",
    "count",
    "organic",
    "recyclable",
    "fields",
    "reason",
    "provider",
    "latency_ms",
    "channel",
    "state",
    "kind",
}


def record(db, event, attempt=None, **attributes):
    payload = {key: value for key, value in attributes.items() if key in ALLOWED}
    source = "synthetic" if settings().env in ("demo", "test") else "pilot"
    query(
        db,
        """INSERT INTO chat_analytics(attempt,event,source,attributes)
        VALUES(CAST(:a AS uuid),:e,:s,CAST(:p AS jsonb))""",
        a=attempt,
        e=event,
        s=source,
        p=json.dumps(payload),
    )


def report(db):
    counts = rows(
        db,
        """SELECT source,event,count(*) AS count FROM chat_analytics
      GROUP BY source,event ORDER BY source,event""",
    )
    journey = rows(
        db,
        """WITH journeys AS (
      SELECT source,attempt,min(occurred_at) FILTER (WHERE event='request_started') AS started,
        max(occurred_at) FILTER (WHERE event='request_registered') AS registered,
        bool_or(event='request_abandoned') AS abandoned,
        count(*) FILTER (WHERE event='missing_asked') AS clarifications,
        count(*) FILTER (WHERE event='bot_reply') AS replies,
        bool_or(event='escalated') AS escalated
      FROM chat_analytics WHERE attempt IS NOT NULL GROUP BY source,attempt
    ) SELECT source,count(*) AS started,count(registered) AS completed,
      count(*) FILTER (WHERE abandoned AND registered IS NULL) AS explicitly_abandoned,
      count(*) FILTER (WHERE escalated) AS escalated,
      avg(clarifications) AS avg_clarifications,
      avg(replies) FILTER (WHERE registered IS NOT NULL) AS mean_replies,
      percentile_cont(.5) WITHIN GROUP(ORDER BY replies) FILTER (WHERE registered IS NOT NULL) AS median_replies,
      avg(extract(epoch FROM registered-started)) AS mean_registration_seconds,
      percentile_cont(.5) WITHIN GROUP(ORDER BY extract(epoch FROM registered-started)) AS median_registration_seconds
      FROM journeys WHERE started IS NOT NULL GROUP BY source""",
    )
    providers = rows(
        db,
        """SELECT source,attributes->>'provider' AS provider,
        count(*) FILTER (WHERE event='ai_error') AS errors,
        count(*) FILTER (WHERE event='ai_success') AS successes,
        percentile_cont(.5) WITHIN GROUP(ORDER BY (attributes->>'latency_ms')::float) AS p50_ms,
        percentile_cont(.95) WITHIN GROUP(ORDER BY (attributes->>'latency_ms')::float) AS p95_ms
      FROM chat_analytics WHERE event IN ('ai_error','ai_success')
      GROUP BY source,attributes->>'provider'""",
    )
    return {"events": counts, "journeys": journey, "providers": providers}
