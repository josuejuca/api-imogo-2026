from fastapi import FastAPI

from src.db.init_db import init_db
from src.routes.auth import router as auth_router

app = FastAPI(title="Auth API", version="2.0.0")


@app.on_event("startup")
def on_startup() -> None:
    init_db()


app.include_router(auth_router, prefix="/api/v2/auth", tags=["auth"])


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}