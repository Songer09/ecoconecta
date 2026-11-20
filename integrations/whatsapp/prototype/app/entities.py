"""Extrae lo que dijo el vecino sin inferir equivalencias ni aceptación local."""

import re
from pydantic import BaseModel, ConfigDict, Field


class Mention(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=80)
    evidence: str = Field(min_length=1, max_length=120)
    quantity: float | None = Field(default=None, gt=0, le=100000)
    unit: str | None = Field(default=None, max_length=20)
    approximate: bool = False
    description: str | None = Field(default=None, max_length=120)


ALIASES = {
    "cartón": r"carton(?:es)?",
    "papel": r"papel(?:es)?(?: periodicos?)?|periodicos?",
    "botellas PET": r"botellas?\s+pet|pet",
    "botellas de plástico": r"botellas?\s+(?:plasticas?|de plastico)",
    "vidrio": r"botellas? de vidrio|vidrios?",
    "botellas": r"botellas?",
    "latas": r"latas?|aluminio",
    "cáscaras": r"cascaras?(?: de (?:banano|platano|frutas?))?|conchas de fruta",
    "restos vegetales": r"restos (?:vegetales|de (?:frutas?|verduras?))|residuos organicos|organicos",
    "hojas": r"hojas?|poda",
    "café": r"borra|posos de cafe|cafe molido",
    "plástico": r"plasticos?",
    "tetrapak": r"tetra\s?pa[ck]k?",
    "residuos de cocina": r"(?:cosas|sobras|restos|residuos) de (?:la )?cocina",
}
# Match longer phrases before standalone words. Consuming a match avoids
# counting "botellas de plástico" as three separate materials.
MATERIAL = re.compile(
    r"\b(?:"
    + "|".join(f"(?P<m{i}>{pattern})" for i, pattern in enumerate(ALIASES.values()))
    + r")\b"
)

NUM = dict(
    zip(
        "un una uno dos tres cuatro cinco seis siete ocho nueve diez once doce trece catorce quince dieciseis diecisiete dieciocho diecinueve veinte".split(),
        (1, 1, *range(1, 21)),
    )
)
NUM |= {
    "veinti" + w: v
    for w, v in zip(
        "uno dos tres cuatro cinco seis siete ocho nueve".split(), range(21, 30)
    )
}
NUM["treinta"] = 30
NUM["media"] = 0.5
NUM["medio"] = 0.5
NUMBER = r"(?<![-\d.,])\b(\d{1,6}(?:[.,]\d{1,3})?|" + "|".join(NUM) + r")\b"
UNITS = {
    "kg": r"kg|kilos?|kilogramos?",
    "bultos": r"bultos?",
    "bolsas": r"bolsas?",
    "costales": r"costal(?:es)?",
    "canecas": r"canecas?",
    "baldes": r"baldes?",
    "unidades": r"unidad(?:es)?|latas?",
    "botellas": r"botellas?",
    "l": r"litros?",
    "cajas": r"cajas?",
}
WORD_UNIT = "|".join(f"(?P<u{i}>{pattern})" for i, pattern in enumerate(UNITS.values()))
AMOUNT = re.compile(NUMBER + r"\s+(?:" + WORD_UNIT + r")\b")
APPROX = r"\b(?:unas?|unos?|como|aproximadamente|mas o menos|cerca de|alrededor de)\s*$"
QUALITATIVE = re.compile(
    r"\b(?:no (?:se|sabria) (?:cuanto(?: pesa| hay| tengo)?|el peso)|"
    r"(?:una )?cantidad (?:pequena|grande|regular)|un poco|un poquito|"
    r"bastante(?:s)?|much[oa]s?|poc[oa]s?|un monton|"
    r"(?:ya )?se me llenaron las bolsas|bolsas? llenas?)\b"
)


def numeric(token):
    return NUM[token] if token in NUM else float(token.replace(",", "."))


def amount(s):
    match = AMOUNT.search(s)
    if match and 0 < (value := numeric(match[1])) <= 100000:
        unit = list(UNITS)[int(match.lastgroup[1:])]
        tail = re.match(
            r"(?:\s+(?:grandes?|pequenas?|llenas?|median[ao]s?))?"
            r"(?P<half>\s+y\s+medi[oa])?"
            r"(?P<approx>\s*,?\s*(?:mas o menos|aproximadamente))?\b",
            s[match.end() :],
        )
        qualifier = re.search(APPROX, s[: match.start()])
        # A trailing "y medio" adds half of the declared unit. No conversion is involved.
        if tail and tail["half"]:
            value += 0.5
        return {
            "quantity": value,
            "unit": unit,
            "approximate": bool(qualifier or (tail and tail["approx"])),
            "description": s[
                qualifier.start() if qualifier else match.start() : match.end()
                + (tail.end() if tail else 0)
            ],
        }
    qualitative = QUALITATIVE.search(s)
    if qualitative:
        return {
            "quantity": None,
            "unit": None,
            "approximate": True,
            "description": qualitative[0],
        }
    return {}


def correction(s, previous):
    value = amount(s)
    if value:
        return value
    match = re.fullmatch(
        r"(?:perdon[, ]*|corrijo[, ]*|en realidad )?(?:son |eran |es |quedaron )?"
        + NUMBER
        + r"[ .!]*",
        s,
    )
    if not match or not 0 < (n := numeric(match[1])) <= 100000:
        return {}
    if previous.get("unit"):
        return {
            "quantity": n,
            "unit": previous["unit"],
            "approximate": False,
            "description": None,
        }
    return {
        "quantity": None,
        "unit": None,
        "approximate": True,
        "description": match[1],
    }


def mentions(s):
    names = list(ALIASES)
    # Split list members without splitting decimals or phrases like "caja de cartón".
    chunks = re.split(
        r"\s+(?:y(?!\s+medi[oa]\b)|e|ademas de|junto con|tambien tengo|tambien hay)\s+|[,;](?!\d)",
        s,
    )
    result = {}
    for index, chunk in enumerate(chunks):
        hits = list(MATERIAL.finditer(chunk))
        value = amount(chunk) if len(hits) == 1 else {}
        if len(hits) == 1 and not value and index + 1 < len(chunks):
            next_chunk = chunks[index + 1]
            if not MATERIAL.search(next_chunk) and re.match(
                r"^\s*" + NUMBER, next_chunk
            ):
                # A measure immediately following a comma can qualify the preceding item.
                separator = s.find(chunk) + len(chunk)
                if s[separator : separator + 1] == ",":
                    value = amount(next_chunk)
        for match in hits:
            name = names[int(match.lastgroup[1:])]
            count_unit = {
                "botellas": "botellas",
                "botellas PET": "botellas",
                "botellas de plástico": "botellas",
                "latas": "unidades",
            }.get(name)
            if len(hits) == 1 and not value and count_unit:
                count = re.search(
                    r"\b(?:cuento|hay|son|tengo)\s+(?:(unas?|unos?)\s+)?"
                    + NUMBER
                    + r"\s*$",
                    chunk,
                )
                if count and 0 < (n := numeric(count[2])) <= 100000:
                    value = {
                        "quantity": n,
                        "unit": count_unit,
                        "approximate": bool(count[1]),
                        "description": count[1] + " " + count[2]
                        if count[1]
                        else count[2],
                    }
            hit = Mention(name=name, evidence=match[0], **value)
            if name not in result or value:
                result[name] = hit
    if len(result) == 1:
        only = next(iter(result.values()))
        if only.quantity is None and not only.description:
            for k, v in amount(s).items():
                setattr(only, k, v)
    if len(result) > 1 and re.search(r"\bde cada (?:uno|una|material)\b", s):
        for hit in result.values():
            for k, v in amount(s).items():
                setattr(hit, k, v)
    return list(result.values())
