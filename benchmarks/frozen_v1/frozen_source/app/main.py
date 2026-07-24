from __future__ import annotations

import logging
import re
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api.routes import router
from app.core.config import APP_NAME, APP_VERSION, SETTINGS, STATIC_DIR

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("marketforge")
_REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]{1,64}$")

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="Local-first financial forecasting, data validation and evidence-aware walk-forward research.",
    docs_url="/docs" if SETTINGS.docs_enabled else None,
    redoc_url="/redoc" if SETTINGS.docs_enabled else None,
)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=list(SETTINGS.allowed_hosts))
app.include_router(router)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def _request_id(request: Request) -> str:
    supplied = request.headers.get("x-request-id", "")
    if _REQUEST_ID_PATTERN.fullmatch(supplied):
        return supplied
    return uuid.uuid4().hex[:16]


def _content_security_policy(path: str) -> str:
    if path in {"/docs", "/redoc"} or path.startswith("/docs/") or path.startswith("/redoc/"):
        return (
            "default-src 'self'; "
            "script-src 'self' https://cdn.jsdelivr.net; "
            "style-src 'self' https://cdn.jsdelivr.net; "
            "img-src 'self' data: https://fastapi.tiangolo.com; "
            "connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
        )
    return (
        "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
        "connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
    )


@app.middleware("http")
async def request_guardrails(request: Request, call_next):
    request_id = _request_id(request)
    started = time.perf_counter()
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            if int(content_length) > SETTINGS.max_request_bytes:
                return JSONResponse(
                    status_code=413,
                    content={"detail": "The request is too large.", "request_id": request_id},
                    headers={"X-Request-ID": request_id},
                )
        except ValueError:
            return JSONResponse(
                status_code=400,
                content={"detail": "The Content-Length header is invalid.", "request_id": request_id},
                headers={"X-Request-ID": request_id},
            )

    try:
        response = await call_next(request)
    except Exception:
        logger.exception("Unhandled request error request_id=%s path=%s", request_id, request.url.path)
        return JSONResponse(
            status_code=500,
            content={
                "detail": "An unexpected error occurred. Check the server log with this request ID.",
                "request_id": request_id,
            },
            headers={"X-Request-ID": request_id},
        )

    elapsed_ms = (time.perf_counter() - started) * 1000
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time-Ms"] = f"{elapsed_ms:.1f}"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(), payment=()"
    response.headers["Content-Security-Policy"] = _content_security_policy(request.url.path)
    response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
    response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")
