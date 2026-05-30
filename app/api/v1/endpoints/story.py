from fastapi import APIRouter, Depends
from app.api.dependencies import get_story_agent

router = APIRouter()

@router.get("/generate")
async def generate_story(
    level: str, 
    theme: str = "Software Development",
    agent = Depends(get_story_agent)
):
    return await agent.run(level=level)