import os
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException
from sqlalchemy.exc import OperationalError
from pydantic import BaseModel

from . import whatsapp_intake, catalog_admin, reports, tracking, photos, garden, operations, rewards, routes, auth, collections, community, education, events, pilot_users, points, requests, scheduling

class ApiError(BaseModel):
    code: str
    message: str
    correlation_id: str


app = FastAPI(lifespan=tracking.lifespan, title="EcoConecta", version="0.1.0",
              responses={s: {"model": ApiError} for s in (401, 403, 404, 409, 422, 429, 503)})


origins = [origin.strip() for origin in os.getenv("FRONTEND_ORIGINS", "").split(",") if origin.strip()]
if origins:
    app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["GET", "PUT", "POST", "DELETE"],
                       allow_headers=["Authorization", "Content-Type"], expose_headers=["X-Correlation-ID"])


@app.middleware("http")
async def request_context(request: Request, call_next):
    request.state.correlation_id = str(uuid4())
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = request.state.correlation_id
    response.headers["Cache-Control"] = "no-store"
    return response


def error(request, status, code, message, headers=None):
    return JSONResponse({"code": code, "message": message, "correlation_id": request.state.correlation_id},
                        status_code=status, headers=headers)


@app.exception_handler(HTTPException)
async def http_error(request, exc):
    messages = {401: "Se requiere autenticación válida.", 403: "Acceso denegado.",
                404: "Recurso no encontrado.", 409: "La operación entra en conflicto con el estado o la disponibilidad actual.",
                422: "Verifica los datos de la solicitud.", 429: "Intenta de nuevo más tarde."}
    return error(request, exc.status_code, exc.detail, messages.get(exc.status_code, "Solicitud inválida."), exc.headers)


@app.exception_handler(RequestValidationError)
async def invalid_input(request, exc):
    return error(request, 422, "invalid_input", "Verifica los campos enviados.")


@app.exception_handler(OperationalError)
async def unavailable(request, exc):
    return error(request, 503, "database_unavailable", "Servicio temporalmente no disponible.")


app.include_router(whatsapp_intake.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(requests.router, prefix="/api/v1")
app.include_router(scheduling.router, prefix="/api/v1")
app.include_router(collections.router, prefix="/api/v1")
app.include_router(points.router, prefix="/api/v1")
app.include_router(education.router, prefix="/api/v1")
app.include_router(events.router, prefix="/api/v1")
app.include_router(community.router, prefix="/api/v1")
app.include_router(pilot_users.router, prefix="/api/v1")
for router in (catalog_admin.router, reports.router, tracking.router, photos.router, operations.router, rewards.router, garden.router, routes.router):
    app.include_router(router, prefix='/api/v1')
