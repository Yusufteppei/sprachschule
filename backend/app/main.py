import logging
from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.api.v1.endpoints import story, urls, auth
from app.database import models, session
from app.core.config import settings

from app.api.v1.endpoints import speech as speech_endpoint

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(name)s %(message)s')
router = APIRouter()

router.include_router(story.router, prefix="/story", tags=["story"])
router.include_router(urls.router, prefix="/interaction", tags=["interaction"])

router.include_router(speech_endpoint.router, prefix="/speech", tags=["speech"])
models.Base.metadata.create_all(bind=session.engine)


def _ensure_sqlite_schema(engine):
    if "sqlite" not in str(engine.url):
        return

    with engine.begin() as conn:
        for table, column, ddl in [
            ("users", "read_story_ids", "ALTER TABLE users ADD COLUMN read_story_ids VARCHAR DEFAULT ''"),
            ("stories", "language", "ALTER TABLE stories ADD COLUMN language VARCHAR DEFAULT 'German'"),
        ]:
            existing = [row[1] for row in conn.execute(text(f"PRAGMA table_info({table})")).all()]
            if column not in existing:
                conn.execute(text(ddl))


_ensure_sqlite_schema(session.engine)

app = FastAPI()

# CORS
app.add_middleware(
	CORSMiddleware,
	allow_origins=settings.CORS_ALLOWED_ORIGINS,
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

app.include_router(router)

# Auth router
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])