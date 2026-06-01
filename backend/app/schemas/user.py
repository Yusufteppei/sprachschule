from typing import Optional
from pydantic import BaseModel, EmailStr
from app.core.enums import TargetLanguage, ProficiencyLevel


class UserProfile(BaseModel):
    id: int
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    level: Optional[ProficiencyLevel] = None
    target_language: Optional[TargetLanguage] = None
    theme: Optional[str] = None

    model_config = {
        "from_attributes": True
    }


class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    level: Optional[ProficiencyLevel] = None
    target_language: Optional[TargetLanguage] = None
    theme: Optional[str] = None
