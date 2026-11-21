"""Administración local por un operador con acceso a la BD."""

import argparse
import hashlib
import secrets
from app.db import engine, one, query
from app.knowledge import ARTICLES
from app.config import settings


def articles(db):
    for title, keywords, answer, source in ARTICLES:
        query(
            db,
            """INSERT INTO articles(title,keywords,answer,source,reviewer,published)
            VALUES(:t,:k,:a,:s,'Revisión documental del prototipo',true) ON CONFLICT(title) DO NOTHING""",
            t=title,
            k=keywords,
            a=answer,
            s=source,
        )


def user(db, handle, role, flow=None, phone=None, opt_in=False):
    token = secrets.token_urlsafe(32)
    row = one(
        db,
        """INSERT INTO users(handle,role,flow,phone,notify_opt_in,token_hash)
      VALUES(:h,:r,:f,:p,:n,:t) ON CONFLICT(handle) DO NOTHING RETURNING id""",
        h=handle,
        r=role,
        f=flow,
        p=phone,
        n=opt_in,
        t=hashlib.sha256(token.encode()).hexdigest(),
    )
    return token if row else None


def demo(db):
    if settings().env not in {"demo", "test"} or settings().channel != "mock":
        raise ValueError("Las fixtures requieren entorno demo y canal mock")
    articles(db)
    for name, flow in [
        ("cartón", "recyclable"),
        ("botellas PET", "recyclable"),
        ("botellas de plástico", "recyclable"),
        ("botellas", "recyclable"),
        ("papel", "recyclable"),
        ("latas", "recyclable"),
        ("cáscaras", "organic"),
        ("restos vegetales", "organic"),
        ("hojas", "organic"),
        ("café", "organic"),
    ]:
        query(
            db,
            "INSERT INTO materials VALUES(:n,:f,true) ON CONFLICT DO NOTHING",
            n=name,
            f=flow,
        )
    tokens = {}
    for handle, role, flow in [
        ("hogar-demo", "resident", None),
        ("tienda-demo", "resident", None),
        ("admin-demo", "admin", None),
        ("coord-huerta", "coordinator", "organic"),
        ("coord-reciclaje", "coordinator", "recyclable"),
        ("huertero-demo", "collector", "organic"),
        ("reciclador-demo", "collector", "recyclable"),
    ]:
        token = user(db, handle, role, flow)
        if token:
            tokens[handle] = token
    query(
        db,
        """INSERT INTO events(kind,title,description,starts_at,place,organizer,category,published)
      SELECT 'training','Taller demo de compostaje','Ejemplo sintético',now()+interval '2 days','Lugar simulado','Equipo demo','compostaje',true
      WHERE NOT EXISTS(SELECT 1 FROM events WHERE title='Taller demo de compostaje')""",
    )
    return tokens


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["demo", "articles", "user"])
    parser.add_argument("--handle")
    parser.add_argument(
        "--role", choices=["resident", "admin", "collector", "coordinator"]
    )
    parser.add_argument("--flow", choices=["organic", "recyclable"])
    parser.add_argument("--phone")
    parser.add_argument("--notification-opt-in", action="store_true")
    args = parser.parse_args()
    with engine.begin() as db:
        if args.action == "demo":
            for handle, token in demo(db).items():
                print(handle, token)
        elif args.action == "articles":
            articles(db)
        else:
            print(
                user(
                    db,
                    args.handle,
                    args.role,
                    args.flow,
                    args.phone,
                    args.notification_opt_in,
                )
                or "Ya existe"
            )
