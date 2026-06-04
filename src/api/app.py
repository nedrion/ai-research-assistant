from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.routes import documents, query, status


@asynccontextmanager
async def lifespan(app: FastAPI):
    from src.api.dependencies import get_pipeline
    _ = get_pipeline()
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


app.include_router(documents.router)
app.include_router(query.router)
app.include_router(status.router)
