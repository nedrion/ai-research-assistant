import asyncio
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from src.api.routes import documents, query, sessions, status
from src.core.logging import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    from src.api.deps import get_embedder, get_llm_client
    embedder = get_embedder()
    await embedder.async_load()
    llm = get_llm_client()
    asyncio.create_task(llm.ensure_model_async())
    yield


app = FastAPI(
    title="AI Research Assistant",
    description="RAG-powered API for querying PDF documents",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    logger.info("%s %s -> %s (%.2fs)", request.method, request.url.path, response.status_code, duration)
    return response


@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    errors = []
    for err in exc.errors():
        location = " -> ".join(str(loc) for loc in err.get("loc", []))
        errors.append(f"{location}: {err['msg']}")
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Request validation failed",
            "errors": errors,
            "hint": "Send JSON with Content-Type: application/json. "
                    "Example: {\"question\": \"your question\"}",
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


app.include_router(documents.router, prefix="/api")
app.include_router(query.router, prefix="/api")
app.include_router(sessions.router, prefix="/api")
app.include_router(status.router, prefix="/api")

ui_dist = Path(__file__).resolve().parent.parent / "ui" / "dist"
spa_index = ui_dist / "index.html"

if ui_dist.is_dir():
    app.mount("/assets", StaticFiles(directory=str(ui_dist / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        if full_path.startswith("api/") or full_path.startswith("assets/"):
            raise HTTPException(status_code=404)
        return FileResponse(str(spa_index))
