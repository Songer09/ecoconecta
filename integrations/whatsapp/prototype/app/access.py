"""Provisiona las claves del panel desde secretos del servidor, sin mostrarlas."""

import argparse
import hashlib
import hmac
import os
import re


def provision(db, handle, role, flow, token, replace_token=False):
    from app.db import audit, one, query

    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]{2,63}", handle):
        raise ValueError("El identificador debe tener entre 3 y 64 caracteres simples")
    if role not in {"resident", "admin", "coordinator", "collector"}:
        raise ValueError("Rol inválido")
    if (
        role in {"coordinator", "collector"} and flow not in {"organic", "recyclable"}
    ) or (role in {"resident", "admin"} and flow is not None):
        raise ValueError("El flujo no corresponde al rol")
    if not re.fullmatch(r"[A-Za-z0-9_-]{32,256}", token):
        raise ValueError(
            "La clave debe ser un token aleatorio de 32 a 256 caracteres URL-safe"
        )
    digest = hashlib.sha256(token.encode()).hexdigest()
    created = one(
        db,
        """INSERT INTO users(handle,role,flow,token_hash)
        VALUES(:h,:r,:f,:t) ON CONFLICT(handle) DO NOTHING RETURNING id""",
        h=handle,
        r=role,
        f=flow,
        t=digest,
    )
    if created:
        audit(db, created["id"], "access_provisioned_locally", str(created["id"]))
        return "creado"
    current = one(db, "SELECT * FROM users WHERE handle=:h FOR UPDATE", h=handle)
    if not current["active"] or current["role"] != role or current["flow"] != flow:
        raise ValueError("La cuenta existente tiene otro rol, flujo o está desactivada")
    if hmac.compare_digest(current["token_hash"] or "", digest):
        return "sin cambios"
    if not replace_token:
        raise ValueError("La cuenta tiene otra clave; usa --replace-token para rotarla")
    query(db, "UPDATE users SET token_hash=:t WHERE id=:id", t=digest, id=current["id"])
    audit(db, current["id"], "access_rotated_locally", str(current["id"]))
    return "clave actualizada"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--handle", required=True)
    parser.add_argument(
        "--role",
        required=True,
        choices=["resident", "admin", "coordinator", "collector"],
    )
    parser.add_argument("--flow", choices=["organic", "recyclable"])
    parser.add_argument(
        "--token-env",
        required=True,
        help="Nombre de la variable secreta; nunca el valor",
    )
    parser.add_argument(
        "--replace-token",
        action="store_true",
        help="Revoca explícitamente la clave anterior",
    )
    args = parser.parse_args()
    token = os.environ.get(args.token_env, "")
    if not token:
        parser.exit(
            1, "Falta la variable secreta indicada; no se modificó el acceso.\n"
        )
    from sqlalchemy.exc import SQLAlchemyError
    from app.db import engine

    try:
        with engine.begin() as db:
            result = provision(
                db, args.handle, args.role, args.flow, token, args.replace_token
            )
    except ValueError as exc:
        parser.exit(1, f"{exc}\n")
    except SQLAlchemyError:
        parser.exit(
            1,
            "No se pudo configurar el acceso; verifica PostgreSQL y las migraciones.\n",
        )
    print(f"Acceso {result}. No se muestran claves.")


if __name__ == "__main__":
    main()
