"""Estado de la conversación. Las preguntas activas no son permisos del modelo."""

from copy import deepcopy
from hashlib import sha256
import json
import re
from typing import Literal

from pydantic import BaseModel, Field

from app.db import query
from app.entities import ALIASES
from app.language import Intent, norm

YES = re.compile(
    r"(?:si(?:[ ,]+(?:confirmo|envia los avisos|envia el aviso|por favor))?|confirmo|confirmar|de acuerdo)"
)
NO = re.compile(
    r"no(?:[ ,]+(?:gracias|solo queria saber(?:lo)?|era (?:solo )?una pregunta))?"
)
QuestionKind = Literal[
    "register",
    "update",
    "cancel",
    "details",
    "review",
    "offer_material",
    "same_address",
    "item_address",
    "preference",
    "correction_field",
    "quantity",
    "address",
    "reference",
]


class Question(BaseModel):
    kind: QuestionKind
    material: str | None = None
    label: str | None = None
    fingerprint: str | None = None
    request_id: str | None = None
    value: str | None = None


class Dialogue(BaseModel):
    introduced: bool = False
    phase: Literal[
        "idle", "collecting", "interrupted", "paused", "completed", "cancelled"
    ] = "idle"
    primary: Intent | None = None
    current: Intent | None = None
    secondary: list[Intent] = Field(default_factory=list)
    focus: str | None = None
    topics: list[str] = Field(default_factory=list)
    question: Question | None = None
    suspended: Question | None = None
    undo: dict | None = None

    def ask(self, kind: QuestionKind, **kwargs):
        self.question = Question(kind=kind, **kwargs)
        self.phase = "collecting"

    def interrupt(self, has_task, *, paused=False):
        if (
            has_task
            and self.question
            and self.question.kind
            in (
                "same_address",
                "item_address",
                "preference",
                "quantity",
                "address",
                "correction_field",
            )
        ):
            self.suspended = self.question
        self.question = None
        self.phase = ("paused" if paused else "interrupted") if has_task else "idle"

    def finish(self, phase):
        self.phase = phase
        self.primary = None
        self.question = None
        self.focus = None
        self.suspended = None
        self.undo = None

    def for_provider(self, draft):
        """Only project vocabulary and slots already filled. No addresses or utterances."""
        if not draft and not self.question and not self.topics:
            return None
        return {
            "task": self.primary,
            "phase": self.phase,
            "question": self.question.kind if self.question else None,
            "materials": [
                item["material"]
                for item in draft.get("items", [])
                if item["material"] in ALIASES
            ],
            "focus": self.focus if self.focus in ALIASES else None,
            "topics": [name for name in self.topics if name in ALIASES],
            "known_fields": [
                key for key in ("address", "preference", "generator") if draft.get(key)
            ],
            "required_fields_missing": [
                field
                for field, present in (
                    ("material", draft.get("items")),
                    ("address", draft.get("address")),
                )
                if draft and not present
            ],
        }


def snapshot(draft):
    return {
        key: deepcopy(draft[key])
        for key in (
            "items",
            "address",
            "preference",
            "generator",
            "unresolved",
            "edit",
            "attempt",
        )
        if key in draft
    }


def approval(kind, draft):
    fields = {"id": draft.get("id")} if kind == "cancel" else snapshot(draft)
    return sha256(
        json.dumps(fields, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()


def save_context(db, uid, dialogue):
    query(
        db,
        """INSERT INTO conversations(user_id,context) VALUES(:u,CAST(:c AS jsonb))
       ON CONFLICT(user_id) DO UPDATE SET context=EXCLUDED.context""",
        u=uid,
        c=dialogue.model_dump_json(),
    )


def simple_response(text):
    s = norm(text).strip(" ¡!.,")
    if YES.fullmatch(s):
        return "yes"
    if NO.fullmatch(s):
        return "no"
    return None


def navigation(text):
    s = norm(text).strip(" ¡!.,¿?")
    if re.fullmatch(r"(?:olvida|deshaz|borra) (?:lo ultimo|el ultimo cambio)", s):
        return "undo"
    if re.match(
        r"^(?:volvamos|volver|regresa|regresemos|retomemos|retoma|sigamos|continuemos|quiero (?:volver|retomar|seguir|continuar)|en que ibamos|en que quedamos)\b",
        s,
    ):
        return "resume"
    if re.fullmatch(
        r"(?:espera|despues seguimos(?: con eso)?|despues retomamos|dejemoslo para despues|mejor quiero preguntar otra cosa|espera[, ]+tengo otra pregunta|tengo otra pregunta)",
        s,
    ):
        return "pause"
    return None
