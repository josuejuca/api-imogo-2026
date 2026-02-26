from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.db.init_db import init_db
from src.routes.auth import router as auth_router

app = FastAPI(title="imoGo API", version="2.0.0", description="imoGo App", swagger_ui_parameters={"syntaxHighlight": {"theme": "obsidian"}}, redoc_url=None, docs_url="/api/docs", openapi_url="/api/openapi.json")

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://([a-z0-9-]+\.)*(imogo\.com\.br|josuejuca\.com|juk\.re)$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


app.include_router(auth_router, prefix="/api/v2/auth", tags=["auth"])


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}

@app.get("/")
def home() -> dict[str, str]:
    return {"message":"Hello Clancy"}