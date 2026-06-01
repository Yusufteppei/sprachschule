from app.agents.storyteller import StorytellerAgent
from app.agents.moderator import ModeratorAgent
from app.core.config import Settings, settings
from app.database.session import get_db
from typing import Optional
from app.core.security import get_current_user, get_current_user_optional
from fastapi import Depends


def get_story_agent() -> StorytellerAgent:
    return StorytellerAgent()


def get_moderator_agent() -> ModeratorAgent:
    return ModeratorAgent()


def get_speech_coach_agent():
    from app.agents.speech_coach import SpeechCoachAgent
    return SpeechCoachAgent()


def get_app_settings() -> Settings:
    return settings


def get_current_active_user(user = Depends(get_current_user)):
    return user