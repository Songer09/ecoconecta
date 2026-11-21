import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class Settings:
    env: str
    ai: str
    channel: str
    model: str
    key: str
    phone_id: str
    account: str
    secret: str
    verify: str
    token: str
    graph: str


@lru_cache
def settings():
    env = os.getenv("APP_ENV", "demo")
    ai = os.getenv("AI_PROVIDER", "mock")
    channel = os.getenv("WHATSAPP_PROVIDER", "mock")
    if (
        env not in {"demo", "pilot", "official", "test"}
        or ai not in {"mock", "gemini", "openai"}
        or channel not in {"mock", "meta"}
    ):
        raise ValueError("Configuración de proveedores inválida")
    if (
        ai == "gemini"
        and env == "official"
        and os.getenv("GEMINI_WRITTEN_AUTHORIZATION") != "confirmed"
    ):
        raise ValueError("Gemini requiere autorización escrita en evaluación oficial")
    if channel == "meta" and env in {"demo", "test"}:
        raise ValueError("Separe los datos de simulación del canal real")
    s = Settings(
        env,
        ai,
        channel,
        os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        if ai == "openai"
        else os.getenv("GEMINI_MODEL", "gemini-3.6-flash"),
        os.getenv("OPENAI_API_KEY" if ai == "openai" else "GEMINI_API_KEY", ""),
        os.getenv("META_PHONE_NUMBER_ID", ""),
        os.getenv("META_WABA_ID", ""),
        os.getenv("META_APP_SECRET", ""),
        os.getenv("META_VERIFY_TOKEN", ""),
        os.getenv("META_ACCESS_TOKEN", ""),
        os.getenv("META_GRAPH_VERSION", ""),
    )
    if (
        ai != "mock"
        and not s.key
        or channel == "meta"
        and not all((s.phone_id, s.account, s.secret, s.verify, s.token, s.graph))
    ):
        raise ValueError("Falta configuración para el proveedor seleccionado")
    return s
