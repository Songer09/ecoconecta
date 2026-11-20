"""Banco inicial contrastado con las fuentes indicadas. La aceptación local se configura aparte."""

import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from app.db import one, rows
from app.language import UNSAFE, norm

BOGOTA = ZoneInfo("America/Bogota")
COMPOST = "https://www.epa.gov/recycle/composting-home"
RECYCLE = "https://www.epa.gov/recycle/frequent-questions-recycling"
CONTEXT = "Contexto integral EcoConecta, secciones 3 y 8, 2026-11-20"
ARTICLES = [
    (
        "Cáscaras de banano",
        "cascara cascaras banano platano fruta",
        "Las cáscaras de banano son residuos orgánicos. Se pueden aprovechar para hacer compost. Consulta con la huerta las condiciones de entrega.",
        COMPOST,
    ),
    (
        "Papel para reciclaje",
        "papel papeles periodico hojas impresas",
        "Separa el papel limpio y seco. Mantén aparte el papel con grasa, humedad o restos de comida y confirma la aceptación con la ruta local.",
        RECYCLE,
    ),
    (
        "Restos vegetales",
        "frutas verduras cascaras peladuras conchas restos vegetales compostar abono compost compostaje",
        "Mezcla las cáscaras de frutas y verduras con hojas secas. Mantén la mezcla húmeda y aireada. Consulta con la huerta antes de llevar material.",
        COMPOST,
    ),
    (
        "Cáscara de huevo",
        "huevo huevos cascara huevo",
        "Las cáscaras de huevo trituradas se pueden incorporar al compost doméstico. Confirma con la huerta cómo las recibe.",
        COMPOST,
    ),
    (
        "Café",
        "cafe posos borra tinto",
        "Los posos de café pueden entrar al compost con material seco. Retira cápsulas y empaques.",
        COMPOST,
    ),
    (
        "Hojas",
        "hojas secas poda jardin",
        "Las hojas secas aportan material marrón al compost. Alterna con restos vegetales húmedos.",
        COMPOST,
    ),
    (
        "Pañales",
        "panal panales sanitario sanitarios",
        "Separa los pañales usados de los aprovechables. No los mezcles con los residuos para la huerta.",
        CONTEXT,
    ),
    (
        "Pilas",
        "pila pilas baterias bateria electronicos",
        "Las pilas, baterías y aparatos electrónicos requieren manejo diferenciado. Consulta un punto de recepción autorizado para el artículo.",
        RECYCLE,
    ),
    (
        "Pizza y cartón",
        "pizza carton grasa caja humedo grasiento",
        "Vacía la caja y separa el cartón limpio y seco de las partes con restos de comida. Consulta cuáles acepta la ruta local.",
        RECYCLE,
    ),
    (
        "Botellas y envases",
        "botellas envases pet plastico lata aluminio vidrio",
        "Vacía el envase y retira los restos. El material y las condiciones de la ruta determinan si puedes entregarlo.",
        RECYCLE,
    ),
    (
        "Separación en origen",
        "separar separacion negocio residuos reciclables reciclaje",
        "Separa restos vegetales, materiales aprovechables limpios y residuos especiales desde donde se generan. Consulta el catálogo de la ruta antes de entregarlos.",
        CONTEXT,
    ),
    (
        "Empaques compostables",
        "biodegradable compostable empaque industrial",
        "Un empaque biodegradable puede requerir condiciones específicas para descomponerse. Revisa si la etiqueta indica compostaje industrial y consulta el protocolo de la huerta.",
        RECYCLE,
    ),
    (
        "Servilletas usadas",
        "servilleta servilletas usadas",
        "Mantén las servilletas usadas fuera del papel limpio para reciclaje. La aceptación en compost depende de su composición y de lo que absorbieron.",
        CONTEXT,
    ),
    (
        "Aceite",
        "aceite cocina usado",
        "Separa el aceite usado en un recipiente cerrado y consulta una ruta autorizada. Si el envase conserva aceite, evita mezclarlo con envases limpios.",
        CONTEXT,
    ),
    (
        "Manejo diferenciado",
        "medicamentos cortopunzantes jeringa vidrio roto",
        "Separa estos materiales del reciclaje ordinario y de los residuos de la huerta. Pide orientación para su manejo específico.",
        CONTEXT,
    ),
    (
        "Huerta comunitaria",
        "huerta materiales aceptacion local",
        "La coordinación de huerteros confirma qué materiales recibe la huerta. Indica el material que quieres entregar para revisar el catálogo.",
        CONTEXT,
    ),
]


def education(db, text, topic=""):
    # Query expansion from NLU is used only if direct retrieval misses.
    for phrase in (text, topic):
        tokens = set(re.findall(r"[a-z]{3,}", norm(phrase))) - set(
            "que para como una unos las los del con son puedo sirve donde cual por tengo hacer".split()
        )
        if not tokens:
            continue
        # Search specific terms first so a generic match for compost cannot
        # take precedence over the material explicitly named by the user.
        specific = tokens - {
            "compost",
            "compostaje",
            "reciclaje",
            "reciclar",
            "reciclable",
            "reciclables",
            "residuo",
            "residuos",
            "abono",
        }
        for terms in (specific, tokens):
            if not terms:
                continue
            row = one(
                db,
                """WITH search AS (SELECT to_tsquery('spanish',:terms) AS q)
                SELECT title,answer,source FROM articles,search WHERE published
                AND length(trim(reviewer))>0 AND length(trim(source))>0
                AND to_tsvector('spanish',keywords) @@ q
                ORDER BY ts_rank(to_tsvector('spanish',keywords),q) DESC,id LIMIT 1""",
                terms=" | ".join(sorted(terms)[:40]),
            )
            if row and not re.search(UNSAFE, norm(row["title"] + " " + row["answer"])):
                return f"{row['answer']}\nFuente: {row['title']} · {row['source']}"
    return "Todavía no tengo una respuesta revisada para ese material. Puedes pedir hablar con coordinación."


def agenda(db, kind, text):
    now = datetime.now(BOGOTA)
    end = None
    s = norm(text)
    if "semana" in s:
        end = (now + timedelta(days=7 - now.weekday())).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
    elif "mes" in s:
        end = (now.replace(day=28) + timedelta(days=4)).replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
    category = next((x for x in ("compost", "recicl", "nino") if x in s), "")
    category = {"nino": "niñ"}.get(category, category)
    records = rows(
        db,
        """SELECT * FROM events WHERE published AND kind=:kind AND starts_at>=:now
       AND (CAST(:end AS timestamptz) IS NULL OR starts_at<:end)
       AND concat_ws(' ',category,title,description) ILIKE :category ORDER BY starts_at LIMIT 3""",
        kind=kind,
        now=now,
        end=end,
        category="%" + category + "%",
    )
    if not records:
        return (
            "Todavía no hay capacitaciones confirmadas para esa consulta. Puedo orientarte sobre compostaje o reciclaje."
            if kind == "training"
            else "Todavía no hay actividades confirmadas publicadas para esa consulta."
        )
    lines = [
        f"{r['title']} · {r['starts_at'].astimezone(BOGOTA):%d/%m/%Y %H:%M} (Barranquilla) · {r['place']}. Organiza {r['organizer']}."
        for r in records
    ]
    if "cupo" in s:
        lines.append("No tengo información confirmada sobre cupos.")
    return "\n".join(lines)
