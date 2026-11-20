"""NLU local y contrato de interpretación. Los resultados nunca son comandos."""

import re
import unicodedata
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field
from app.entities import Mention, amount, mentions

Intent = Literal[
    "collection",
    "track",
    "event",
    "training",
    "recycling",
    "compost",
    "material",
    "points",
    "modify",
    "cancel",
    "human",
    "hello",
    "bye",
    "ambiguous",
    "offtopic",
]
Scope = Literal["IN_SCOPE", "OUT_OF_SCOPE", "UNCERTAIN"]


class SecondaryIntent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    intent: Intent
    text: str = Field(min_length=1, max_length=1200)
    topic: str = Field(default="", max_length=100)


class Interpretation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    scope: Scope
    intent: Intent
    materials: list[Mention] = Field(default_factory=list, max_length=20)
    date: str | None = Field(default=None, max_length=80)
    time: str | None = Field(default=None, max_length=80)
    generator: Literal["hogar", "unidad productiva"] | None = None
    topic: str = Field(default="", max_length=100)
    secondary_intents: list[SecondaryIntent] = Field(default_factory=list, max_length=5)
    primary_text: str | None = Field(default=None, max_length=2000)
    dialogue_act: Literal[
        "request", "question", "answer", "correction", "navigation", "ambiguous"
    ] = "ambiguous"
    requested_navigation: Literal["resume", "pause", "undo"] | None = None
    correction_field: Literal["quantity", "address", "preference"] | None = None
    context_reference: str | None = Field(default=None, max_length=80)
    confidence: float | None = Field(default=None, ge=0, le=1)
    needs_clarification: bool = False


def norm(s):
    return "".join(
        c
        for c in unicodedata.normalize("NFD", s.lower())
        if not unicodedata.combining(c)
    ).strip()


SPECIAL = r"\b(pilas?|baterias?|medicamentos?|aceites?|panales?|sanitari[oa]s?|electronicos?|jeringas?|vidrio roto|icopor|contaminad[oa]s?|suci[oa]s?|mojad[oa]s?|humed[oa]s?|servilletas?|carne|huesos?|lacteos?|quimicos?|pintura|grasient[oa]s?|grasos?[oa]?|grasa|pizza)\b"
UNSAFE = r"(ignora|olvida|omite|desobedece).{0,35}(instrucciones|reglas|prompt)|actua como|revela.{0,20}(clave|prompt|token)|system prompt"
OTHER = r"\b(mundial|futbol|partido de futbol|bitcoin|criptomoneda|python|javascript|pelicula|presidente|celular|horoscopo|programacion de software|receta de cocina)\b"


def materials(s):
    return [hit.name for hit in mentions(s)]


def classify(text):
    s = norm(text)
    mats = mentions(s)

    def result(intent, scope="IN_SCOPE"):
        return Interpretation(intent=intent, scope=scope, materials=mats[:20])

    if re.search(UNSAFE + "|" + OTHER, s):
        return result("offtopic", "OUT_OF_SCOPE")
    rules = [
        ("cancel", r"\b(cancelar?|anula\w*|desistir)\b"),
        (
            "modify",
            r"\b(corregir|modific\w*|cambiar|corrijo|perdon|en realidad|no son|me equivoque|no era la direccion|direccion (?:esta mal|incorrecta))\b",
        ),
        ("points", r"\bpuntos\b"),
        (
            "track",
            r"\b(estado|seguimiento|como va|por donde va|en que quedo|que paso con (?:mi|el) (?:aviso|pedido)|ya pasaron|mis solicitudes|codigo eco)\b|eco-[0-9a-f]",
        ),
        (
            "training",
            r"\b(taller\w*|curso\w*|capacit\w*|formacion(?:es)?|ensen\w*|charla\w*|encuentro en el que expliquen)\b",
        ),
        ("event", r"\b(evento\w*|actividad\w*|jornada\w*|agenda)\b"),
        ("human", r"\b(humano|asesor|persona real|hablar con coordinacion)\b"),
        (
            "collection",
            r"\b(tengo|tenemos|me quedaron|quedaron|reuni(?:mos)?|junt[eo](?:mos)?|acumul[eo]|guarde|list[oa]s? para (?:entregar|recoger)|necesito que|vengan|pueden (?:venir|recoger|pasar|retirar|llevar)|(?:quiero|queremos) (?:entregar|avisar|solicitar)\w*|pasen por)\b",
        ),
        (
            "recycling",
            r"\bcomo (?:prepar[oa]r?|separ[oa]r?|dispongo)\b(?=.{0,75}\b(?:papel|carton|latas|vidrio|reciclab))",
        ),
        ("compost", r"\b(compost\w*|huerta|abono|biodegradable)\b"),
        ("recycling", r"\b(recicl\w*|separ\w*|aprovech\w*)\b"),
    ]
    for intent, pattern in rules:
        if re.search(pattern, s):
            if intent == "collection" and (
                re.search(
                    r"\b(si tengo|hipoteticamente|que hago|como (separo|separar|reciclo|reciclar|dispongo|preparo|preparar)|puedo (?:reciclar|compostar)|(?:sirve|sirven) para)\b",
                    s,
                )
                or not (
                    mats
                    or re.search(
                        SPECIAL
                        + r"|residu|basura|recoge|recolec|recicla|huerta|pasen|botellas?|recoger|entregar",
                        s,
                    )
                )
            ):
                continue
            return result(intent)
    if mats or re.search(
        SPECIAL + r"|\b(?:fundas?|empaques?|envases?|envolturas?|bolsas? negras)\b", s
    ):
        return result("collection" if amount(s) and "?" not in s else "material")
    if re.fullmatch(
        r"(hola(?: de nuevo)?|buenas|buenos dias|buenas tardes|buenas noches)[!. ]*",
        s.lstrip("¡ "),
    ):
        return result("hello")
    if re.fullmatch(r"(adios|hasta luego|chao|gracias)[!. ]*", s):
        return result("bye")
    if "?" in s or s.startswith(("quien ", "cuanto cuesta", "escribe ")):
        return result("offtopic", "OUT_OF_SCOPE")
    return result("ambiguous", "UNCERTAIN")


INFORMATION = {
    "event",
    "training",
    "points",
    "track",
    "recycling",
    "compost",
    "material",
}
EDUCATION = {"recycling", "compost", "material"}
SPLIT = re.compile(
    r"(?<=\?)\s+(?=[^\s])|(?<!^)(?=¿)|"
    r"\s+(?:y|pero)\s+(?:tambi[eé]n\s+)?(?=(?:(?:quiero|quisiera|necesito)\s+)?(?:saber|consultar|preguntar)\b|"
    r"(?:cu[aá]ndo|d[oó]nde|c[oó]mo|qu[eé])\b|(?:tengo|tenemos|quiero que recojan)\b)",
    re.I,
)


def classify_turn(text):
    s = norm(text)
    # An explicit "solo quiero saber" narrows the turn to information, not a collection action.
    if re.search(r"\bno (?:quiero|necesito|voy a) (?:recog|entreg|solicit|envi)\w*", s):
        match = re.search(r"\bsolo (?:quiero|necesito|queria) (?:saber|preguntar)\b", s)
        if match:
            fragment = text.strip()[match.end() :].lstrip()
            classified = classify(fragment)
            if classified.intent in EDUCATION:
                return classified.model_copy(
                    update={"primary_text": fragment, "dialogue_act": "question"}
                )
    parsed = []
    for fragment in SPLIT.split(text.strip()):
        fragment = fragment.strip()
        if fragment:
            result = classify(fragment)
            if result.scope == "IN_SCOPE" and result.intent in INFORMATION | {
                "collection"
            }:
                parsed.append((fragment, result))
    if len(parsed) > 1:
        primary_index = next(
            (n for n, (_, item) in enumerate(parsed) if item.intent == "collection"), 0
        )
        fragment, primary = parsed[primary_index]
        secondary = [
            SecondaryIntent(intent=item.intent, text=part, topic=item.topic)
            for n, (part, item) in enumerate(parsed)
            if n != primary_index
        ][:5]
        return primary.model_copy(
            update={
                "primary_text": fragment,
                "secondary_intents": secondary,
                "dialogue_act": "request"
                if primary.intent == "collection"
                else "question",
            }
        )
    result = classify(text)
    act = {"collection": "request", "modify": "correction"}.get(
        result.intent, "question" if result.intent in INFORMATION else "ambiguous"
    )
    return result.model_copy(
        update={"dialogue_act": act, "needs_clarification": result.scope == "UNCERTAIN"}
    )


def private_text(s):
    return bool(
        re.search(
            r"@|\d{6,}|\b(calle|carrera|cra|manzana|direccion|me llamo|mi nombre|telefono|diagonal|transversal|avenida|barrio|mz|bloque|lote|conjunto|apartamento|apto|porteria|vivo en|cedula|casa \d)\b",
            norm(s),
        )
    )
