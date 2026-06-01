from typing import Any, Dict, Optional
from pydantic import BaseModel
from app.schemas.story import Story


class InteractionResponse(BaseModel):
    success: bool
    agent: str
    type: Optional[str] = None
    message: Optional[str] = None
    story: Optional[Story] = None
    audio_url: Optional[str] = None
    transcript: Optional[str] = None
    quiz: Optional[Dict[str, Any]] = None
    analysis: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    model_config = {
        "extra": "allow"
    }
