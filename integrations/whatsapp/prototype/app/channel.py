"""WhatsApp Cloud API. El simulador nunca contacta a Meta."""

import hashlib
import hmac
import os
import re
from urllib.parse import urlsplit
from datetime import datetime, timedelta, timezone
import httpx
from app.config import settings
from time import perf_counter
from app.analytics import record
from app.providers import provider
from app.db import one, query
from app.conversation import handle

CAP = 4 * 1024 * 1024


def signed(raw, signature):
    secret = settings().secret
    return bool(
        secret
        and hmac.compare_digest(
            "sha256=" + hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest(),
            signature or "",
        )
    )


def audio(media_id, observe=None):
    cfg = settings()
    if not re.fullmatch(r"[0-9]{1,32}", media_id):
        raise ValueError("Identificador de audio inválido")
    headers = {"Authorization": "Bearer " + cfg.token}
    with httpx.Client(timeout=10, follow_redirects=False, headers=headers) as client:
        meta = client.get(
            f"https://graph.facebook.com/{cfg.graph}/{media_id}",
            params={"phone_number_id": cfg.phone_id},
        )
        meta.raise_for_status()
        info = meta.json()
        url = urlsplit(info["url"])
        if (
            url.scheme != "https"
            or url.hostname != "lookaside.fbsbx.com"
            or url.port not in (None, 443)
            or url.username
            or url.password
        ):
            raise ValueError("Host de medios inválido")
        mime = info["mime_type"].split(";")[0]
        if mime != "audio/ogg" or not 0 < int(info["file_size"]) <= CAP:
            raise ValueError("Formato o tamaño no admitido")
        with client.stream("GET", url.geturl()) as res:
            res.raise_for_status()
            if res.headers.get("content-type", "").split(";")[0] not in (
                mime,
                "application/octet-stream",
            ):
                raise ValueError("Tipo de descarga inválido")
            data = bytearray()
            for chunk in res.iter_bytes(65536):
                if len(data) + len(chunk) > CAP:
                    raise ValueError("Audio demasiado grande")
                data.extend(chunk)
    if (
        not data.startswith(b"OggS")
        or b"OpusHead" not in data[:256]
        or len(data) != int(info["file_size"])
    ):
        raise ValueError("Audio Ogg/Opus inválido")
    start = perf_counter()
    try:
        transcript = provider().transcribe(bytes(data), mime)
    except (ValueError, TypeError, KeyError, IndexError, httpx.HTTPError):
        if observe:
            observe(
                "ai_error",
                provider=cfg.ai,
                latency_ms=(perf_counter() - start) * 1000,
                kind="audio",
            )
        raise
    if observe:
        observe(
            "ai_success",
            provider=cfg.ai,
            latency_ms=(perf_counter() - start) * 1000,
            kind="audio",
        )
    return transcript


def receive(db, user, mid, kind, payload, stamp):
    row = one(
        db,
        """INSERT INTO messages(external_id,user_id,kind,payload,received_at)
      VALUES(:mid,:u,:k,:p,:stamp) ON CONFLICT(external_id) DO NOTHING RETURNING id""",
        mid=mid,
        u=user,
        k=kind,
        p=payload,
        stamp=stamp,
    )
    if row:
        query(
            db,
            "UPDATE users SET last_inbound=greatest(last_inbound,:s) WHERE id=:u",
            s=stamp,
            u=user,
        )
    return row


def reply(db, user, kind, payload):
    if kind in ("audio", "demo_audio"):
        consent = one(db, "SELECT audio FROM consents WHERE user_id=:u", u=user)
        if not consent or not consent["audio"]:
            return "Para enviar tu nota a la IA y transcribirla, escribe ACEPTO AUDIO y reenvíala. Puedes escribir en su lugar o usar REVOCO AUDIO."
        if kind == "audio":
            try:
                transcript = audio(
                    payload, observe=lambda event, **attrs: record(db, event, **attrs)
                )
                if not transcript.clear or not transcript.text.strip():
                    raise ValueError("Audio incierto")
                payload = transcript.text
            except (ValueError, TypeError, KeyError, IndexError, httpx.HTTPError):
                return "No pude distinguir la nota con seguridad. ¿Puedes escribir el material y la cantidad?"
        # Confirmations, consent and destructive actions require a written turn.
        from app.language import norm

        if norm(payload).strip(" .!") in (
            "si",
            "confirmo",
            "si confirmo",
            "confirmar",
            "de acuerdo",
            "acepto audio",
            "revoco audio",
            "no",
        ):
            return "Por favor confirma esa decisión por escrito."
    if kind not in ("audio", "demo_audio", "text"):
        return "Por ahora puedo leer texto y notas de voz Ogg/Opus."
    return handle(db, user, payload, allow_confirmation=kind == "text")


def send(item):
    cfg = settings()
    if cfg.channel == "mock":
        return "simulated", None
    within = item["last_inbound"] and item["last_inbound"] > datetime.now(
        timezone.utc
    ) - timedelta(hours=24)
    if not item["phone"] or (item["kind"] != "reply" and not item["notify_opt_in"]):
        return "panel_only", None
    body = {"messaging_product": "whatsapp", "to": item["phone"]}
    if within:
        body.update(type="text", text={"body": item["body"][:4096]})
    else:
        template = (
            os.getenv("META_TEMPLATE_" + item["kind"].upper(), "")
            if item["kind"] in ("alert", "schedule")
            else ""
        )
        if not template:
            return "panel_only", None
        body.update(
            type="template",
            template={
                "name": template,
                "language": {"code": os.getenv("META_TEMPLATE_LANGUAGE", "es_CO")},
                "components": [
                    {
                        "type": "body",
                        "parameters": [{"type": "text", "text": item["body"]}],
                    }
                ],
            },
        )
    result = httpx.post(
        f"https://graph.facebook.com/{cfg.graph}/{cfg.phone_id}/messages",
        timeout=10,
        headers={"Authorization": "Bearer " + cfg.token},
        json=body,
    )
    result.raise_for_status()
    return "sent", result.json()["messages"][0]["id"]
