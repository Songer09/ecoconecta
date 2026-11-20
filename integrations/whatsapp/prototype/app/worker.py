import time
import logging
import httpx
from app.db import engine, one, query
from app.channel import reply, send
from app.operations import notify
from app.analytics import record


def process(db, msg):
    actor = one(
        db, "SELECT active,role FROM users WHERE id=:u FOR UPDATE", u=msg["user_id"]
    )
    answer = None
    if actor["active"] and actor["role"] == "resident":
        if not one(
            db,
            "SELECT id FROM messages WHERE user_id=:u AND processed LIMIT 1",
            u=msg["user_id"],
        ):
            record(db, "conversation_started")
        answer = reply(db, msg["user_id"], msg["kind"], msg["payload"])
        notify(db, msg["user_id"], "reply", answer)
        record(db, "reply_queued")
    query(
        db, "UPDATE messages SET processed=true,payload=NULL WHERE id=:id", id=msg["id"]
    )
    return answer


def incoming():
    with engine.begin() as db:
        msg = one(
            db,
            """SELECT m.* FROM messages m WHERE NOT processed AND NOT EXISTS
          (SELECT 1 FROM messages p WHERE p.user_id=m.user_id AND p.id<m.id AND NOT p.processed)
          ORDER BY id LIMIT 1 FOR UPDATE SKIP LOCKED""",
        )
        if msg:
            process(db, msg)
        return bool(msg)


def outgoing():
    with engine.begin() as db:
        item = one(
            db,
            """SELECT n.*,u.phone,u.last_inbound,u.notify_opt_in,u.active FROM notifications n
          JOIN users u ON u.id=n.user_id WHERE state='pending' AND next_try<=now()
          ORDER BY n.id LIMIT 1 FOR UPDATE OF n SKIP LOCKED""",
        )
        if not item:
            return False
        query(
            db,
            "UPDATE notifications SET state='sending',tries=tries+1 WHERE id=:id",
            id=item["id"],
        )
    external = None
    try:
        state, external = send(item) if item["active"] else ("panel_only", None)
    except (httpx.ConnectError, httpx.ConnectTimeout):
        state = "pending" if item["tries"] < 3 else "failed"
    except httpx.HTTPStatusError as err:
        state = (
            "pending"
            if err.response.status_code == 429 and item["tries"] < 3
            else "failed"
        )
    except (httpx.HTTPError, ValueError, KeyError, TypeError, IndexError):
        state = "unknown"
    with engine.begin() as db:
        query(
            db,
            "UPDATE notifications SET state=:s,external_id=:ext,next_try=now()+interval '30 seconds' WHERE id=:id",
            s=state,
            ext=external,
            id=item["id"],
        )
        if state in ("failed", "unknown"):
            record(
                db,
                "whatsapp_delivery_failure",
                channel="meta",
                state=state,
                kind=item["kind"],
            )
        elif state in ("sent", "simulated"):
            record(
                db,
                "response_sent",
                channel="meta" if state == "sent" else "mock",
                state=state,
                kind=item["kind"],
            )
    return True


if __name__ == "__main__":
    logging.getLogger("httpx").setLevel(logging.WARNING)
    while True:
        try:
            worked = incoming()
            if not outgoing() and not worked:
                time.sleep(0.5)
        except Exception:
            logging.error("Worker: fallo de procesamiento, revise la cola")
            time.sleep(2)
