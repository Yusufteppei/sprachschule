from fastapi import FastAPI, APIRouter
from app.api.v1.endpoints import story
router = APIRouter()

router.include_router(story.router, prefix="/story", tags=["story"])

app = FastAPI()
app.include_router(router)