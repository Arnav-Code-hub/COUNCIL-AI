import logging
import secrets
import threading
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import UUID

from fastapi import BackgroundTasks, Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware

from council.config import Settings
from council.engine import SimulatedReviewer, assess
from council.pdf import make_pdf
from council.schemas import Project
from council.store import Store

logger = logging.getLogger(__name__)


def create_app(settings=None, provider=None):
    settings = settings or Settings()
    store = Store(settings.data_dir)
    lock = threading.Lock()
    if provider is None:
        provider = SimulatedReviewer()
        if settings.mode == "gemini":
            from council.gemini import GeminiReviewer

            provider = GeminiReviewer(settings)

    @asynccontextmanager
    async def lifespan(app):
        store.recover()
        yield

    app = FastAPI(title="Independent AI Council", version="1.0", lifespan=lifespan)
    app.state.store = store
    app.state.settings = settings

    if not settings.service_key.get_secret_value():
        app.add_middleware(
            TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost", "testserver", "test"]
        )

    @app.middleware("http")
    async def boundary(request: Request, call_next):
        origin = request.headers.get("origin")
        allowed = {settings.cors_origin, "http://127.0.0.1:8090", "http://localhost:8090"}
        if origin and origin not in allowed:
            return JSONResponse({"detail": "Origin is not allowed."}, status_code=403)
        if request.method in {"POST", "PUT", "PATCH"}:
            data = bytearray()
            async for chunk in request.stream():
                data.extend(chunk)
                if len(data) > 1000000:
                    return JSONResponse({"detail": "Request exceeds 1 MB."}, status_code=413)
            request._body = bytes(data)
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    def authorize(request: Request):
        supplied = request.headers.get("X-Council-Key", "")
        expected = settings.service_key.get_secret_value()
        if expected:
            if not secrets.compare_digest(supplied, expected):
                raise HTTPException(401, "Service authentication required.")
        elif (
            not settings.trust_loopback_proxy
            and request.client
            and request.client.host
            not in {
                "127.0.0.1",
                "::1",
                "localhost",
                "testclient",
                "test",
            }
        ):
            raise HTTPException(
                403, "Local workspace only. Configure service authentication for integration."
            )

    def run(identity):
        with lock:
            row = store.get(identity)
            store.update(identity, "running")
            try:
                report = assess(
                    Project.model_validate(row["project"]),
                    provider,
                    progress=lambda count: store.update(identity, "running", count),
                )
                content = make_pdf(
                    identity, row["created_at"], Project.model_validate(row["project"]), report
                )
                folder = settings.data_dir / "reports"
                folder.mkdir(exist_ok=True)
                temporary = folder / f"{identity}.tmp"
                temporary.write_bytes(content)
                temporary.replace(folder / f"{identity}.pdf")
                store.update(identity, "completed", 5, report)
            except Exception as exc:
                logger.error("Assessment %s failed (%s)", identity, type(exc).__name__)
                current = store.get(identity)
                store.update(
                    identity,
                    "incomplete",
                    current["completed_reviewers"],
                    error="Review or PDF generation failed. No completed report was published; retry explicitly.",
                )

    @app.get("/health")
    def health():
        return {"status": "ok", "mode": settings.mode, "contract_version": "1.0"}

    @app.get("/v1/assessments", dependencies=[Depends(authorize)])
    def history():
        return store.list()

    @app.post("/v1/assessments", status_code=202, dependencies=[Depends(authorize)])
    def create(
        body: Project,
        tasks: BackgroundTasks,
        key: str = Header(alias="Idempotency-Key", min_length=1, max_length=200, pattern=r"\S"),
    ):
        try:
            row, created = store.create(key, body)
        except ValueError as exc:
            raise HTTPException(409, str(exc)) from exc
        except OverflowError as exc:
            raise HTTPException(429, str(exc)) from exc
        if created:
            tasks.add_task(run, row["id"])
        return {"id": row["id"], "status": row["status"]}

    def find(identity):
        row = store.get(identity)
        if row is None:
            raise HTTPException(404, "Assessment not found.")
        return row

    @app.get("/v1/assessments/{identity}", dependencies=[Depends(authorize)])
    def read(identity: UUID):
        return find(str(identity))

    @app.post(
        "/v1/assessments/{identity}/retry", status_code=202, dependencies=[Depends(authorize)]
    )
    def retry(
        identity: UUID,
        tasks: BackgroundTasks,
        key: str = Header(alias="Idempotency-Key", min_length=1, max_length=200, pattern=r"\S"),
    ):
        find(str(identity))
        try:
            retried = store.retry(str(identity), key)
        except OverflowError as exc:
            raise HTTPException(429, str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(409, str(exc)) from exc
        if retried:
            tasks.add_task(run, str(identity))
        return {"id": str(identity), "status": find(str(identity))["status"]}

    @app.get("/v1/assessments/{identity}/pdf", dependencies=[Depends(authorize)])
    def pdf(identity: UUID):
        row = find(str(identity))
        if row["status"] != "completed":
            raise HTTPException(409, "A complete report is not available.")
        path = settings.data_dir / "reports" / f"{identity}.pdf"
        if not path.is_file():
            raise HTTPException(503, "Report artifact unavailable; restore from backup.")
        return FileResponse(path, media_type="application/pdf", filename=f"council-{identity}.pdf")

    web = Path(__file__).resolve().parents[1] / "web" / "dist"
    if web.is_dir():
        app.mount("/", StaticFiles(directory=web, html=True), name="web")
    return app
