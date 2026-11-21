import hashlib
import secrets
import sys

import pytest


def configure(ctx, token, **overrides):
    from app.access import provision

    args = dict(handle="portable-resident", role="resident", flow=None, token=token)
    args.update(overrides)
    with ctx.engine.begin() as db:
        return provision(db, **args)


def identity(ctx, token):
    return ctx.api.get("/api/v1/me", headers={"Authorization": "Bearer " + token})


def test_imported_token_authenticates_and_only_hash_is_stored(ctx):
    token = secrets.token_urlsafe(32)
    assert configure(ctx, token) == "creado"
    assert identity(ctx, token).json()["handle"] == "portable-resident"
    assert identity(ctx, token + "x").status_code == 401
    assert (
        ctx.api.get(
            "/api/v1/admin/metrics", headers={"Authorization": "Bearer " + token}
        ).status_code
        == 403
    )
    with ctx.engine.begin() as db:
        row = db.exec_driver_sql(
            "SELECT token_hash FROM users WHERE handle='portable-resident'"
        ).scalar_one()
    assert row == hashlib.sha256(token.encode()).hexdigest()
    assert row != token


def test_repeated_provision_keeps_identity_and_requires_explicit_rotation(ctx):
    first, second = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
    configure(ctx, first)
    original_id = identity(ctx, first).json()["id"]
    assert configure(ctx, first) == "sin cambios"
    with pytest.raises(ValueError, match="--replace-token"):
        configure(ctx, second)
    assert identity(ctx, first).status_code == 200
    assert configure(ctx, second, replace_token=True) == "clave actualizada"
    assert identity(ctx, first).status_code == 401
    assert identity(ctx, second).json()["id"] == original_id


def test_import_cannot_escalate_or_reactivate_accounts(ctx):
    token = secrets.token_urlsafe(32)
    configure(ctx, token)
    with pytest.raises(ValueError, match="otro rol"):
        configure(ctx, token, role="admin", replace_token=True)
    assert identity(ctx, token).json()["role"] == "resident"
    with ctx.engine.begin() as db:
        db.exec_driver_sql(
            "UPDATE users SET active=false WHERE handle='portable-resident'"
        )
    with pytest.raises(ValueError, match="desactivada"):
        configure(ctx, token, replace_token=True)
    assert identity(ctx, token).status_code == 401


@pytest.mark.parametrize("bad", ["short", " " * 43, "a" * 31, "a" * 257])
def test_import_rejects_weak_or_malformed_tokens(ctx, bad):
    with pytest.raises(ValueError, match="token aleatorio"):
        configure(ctx, bad)


def test_cli_does_not_print_tokens_and_missing_secret_fails(ctx, monkeypatch, capsys):
    from app.access import main

    token = secrets.token_urlsafe(32)
    monkeypatch.setenv("PANEL_TEST_ACCESS", token)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "app.access",
            "--handle",
            "portable-admin",
            "--role",
            "admin",
            "--token-env",
            "PANEL_TEST_ACCESS",
        ],
    )
    main()
    captured = capsys.readouterr()
    assert "Acceso creado" in captured.out
    assert token not in captured.out + captured.err
    assert identity(ctx, token).json()["role"] == "admin"
    monkeypatch.delenv("PANEL_TEST_ACCESS")
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 1
    assert "Falta la variable" in capsys.readouterr().err
