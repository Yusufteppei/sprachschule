from typing import Optional
from pydantic import BaseModel


class Story(BaseModel):
    id: int
    title: str
    content: str
    level: str
    theme: str
    language: Optional[str] = None
    created_at: Optional[str] = None
    audio_file_path: Optional[str] = None
    audio_file_url: Optional[str] = None
    audio_generated: Optional[bool] = False
    word_audio_urls: Optional[dict[str, str]] = None

    model_config = {
        "from_attributes": True
    }

