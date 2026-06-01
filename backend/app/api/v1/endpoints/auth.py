import logging
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token, verify_password, get_password_hash
from app.core.enums import TargetLanguage, ProficiencyLevel
from app.api.dependencies import get_current_active_user
from app.database import models
from app.database.session import get_db
from app.schemas.user import UserProfile, UserProfileUpdate

logger = logging.getLogger("app.auth")
logger.setLevel(logging.DEBUG)

router = APIRouter()


class SignupRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: str | None = None
    level: ProficiencyLevel = ProficiencyLevel.B2
    target_language: TargetLanguage = TargetLanguage.GERMAN
    theme: str = "Technology"


@router.post("/signup")
async def signup(data: SignupRequest, db: Session = Depends(get_db)):
    logger.debug("Signup request: username=%s email=%s password_length=%s full_name=%s level=%s target_language=%s theme=%s", data.username, data.email, len(data.password), data.full_name, data.level, data.target_language, data.theme)
    existing_user = db.query(models.User).filter(
        (models.User.username == data.username) | (models.User.email == data.email)
    ).first()
    if existing_user:
        logger.warning("Signup failed: username or email already registered: %s / %s", data.username, data.email)
        raise HTTPException(status_code=400, detail="Username or email already registered")

    user = models.User(
        username=data.username,
        email=data.email,
        hashed_password=get_password_hash(data.password),
        full_name=data.full_name or "",
        level=data.level.value,
        target_language=data.target_language.value,
        theme=data.theme,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "level": user.level,
            "target_language": user.target_language,
            "theme": user.theme,
        },
    }


@router.post("/token")
async def token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    logger.debug("Login request: username=%s password_length=%s", form_data.username, len(form_data.password))
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user:
        logger.warning("Login failed: user not found %s", form_data.username)
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    logger.debug(
        "Stored hash metadata: type=%s length=%s prefix=%s",
        type(user.hashed_password).__name__,
        len(user.hashed_password or ""),
        repr((user.hashed_password or "")[:60]),
    )

    try:
        verified = verify_password(form_data.password, user.hashed_password)
    except Exception:
        logger.exception("Verification exception for user %s", form_data.username)
        raise HTTPException(status_code=500, detail="Internal auth error")

    if not verified:
        logger.warning("Login failed: password verification failed for %s", form_data.username)
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "level": user.level,
            "target_language": user.target_language,
            "theme": user.theme,
        },
    }


@router.get("/profile", response_model=UserProfile)
async def get_profile(current_user = Depends(get_current_active_user)):
    return current_user


@router.put("/profile", response_model=UserProfile)
async def update_profile(
    data: UserProfileUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    if data.full_name is not None:
        current_user.full_name = data.full_name
    if data.level is not None:
        current_user.level = data.level.value
    if data.target_language is not None:
        current_user.target_language = data.target_language.value
    if data.theme is not None:
        current_user.theme = data.theme

    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user
