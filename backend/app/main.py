from fastapi import FastAPI

from backend.app.api.routes import router
from backend.app.core.config import settings
from backend.app.db.base import Base
from backend.app.db.session import engine
from backend.app.models import Recipe


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    description="Protótipo inicial do backend do NutriFlow AI",
)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)


app.include_router(router)