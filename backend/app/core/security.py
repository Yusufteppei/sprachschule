import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
import bcrypt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database import models
from app.database.session import get_db

logger = logging.getLogger("app.security")
logger.setLevel(logging.DEBUG)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token", auto_error=False)


def normalize_password(password: str) -> str:
    original_type = type(password).__name__
    if isinstance(password, bytes):
        password = password.decode("utf-8", errors="ignore")

    encoded = password.encode("utf-8", errors="ignore")
    if len(encoded) > 72:
        truncated = encoded[:72]
        normalized = truncated.decode("utf-8", errors="ignore")
        logger.debug(
            "Password truncated by bytes: original_chars=%s original_bytes=%s normalized_chars=%s normalized_bytes=%s type=%s",
            len(password),
            len(encoded),
            len(normalized),
            len(truncated),
            original_type,
        )
    else:
        normalized = password
        logger.debug(
            "Password normalized: chars=%s bytes=%s type=%s",
            len(normalized),
            len(encoded),
            original_type,
        )
    return normalized


def verify_password(plain_password: str, hashed_password: str) -> bool:
    normalized_password = normalize_password(plain_password)
    logger.debug(
        "Verifying password: normalized_chars=%s normalized_bytes=%s hashed_password_type=%s hashed_password_prefix=%s",
        len(normalized_password),
        len(normalized_password.encode("utf-8")),
        type(hashed_password).__name__,
        repr((hashed_password or "")[:60]),
    )
    try:
        result = bcrypt.checkpw(normalized_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        logger.exception("Password verify exception")
        raise
    logger.debug("Password verify result=%s", result)
    return result


def get_password_hash(password: str) -> str:
    normalized_password = normalize_password(password)
    logger.debug("Hashing password: normalized_chars=%s normalized_bytes=%s", len(normalized_password), len(normalized_password.encode("utf-8")))
    try:
        hashed = bcrypt.hashpw(normalized_password.encode("utf-8"), bcrypt.gensalt())
        hashed_str = hashed.decode("utf-8")
    except Exception:
        logger.exception("Password hash exception")
        raise
    logger.debug("Generated password hash length=%s prefix=%s", len(hashed_str), repr(hashed_str[:60]))
    return hashed_str


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_user(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = decode_access_token(token)
    username = payload.get("sub")
    if username is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")

    user = get_user(db, username)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def get_current_user_optional(token: str | None = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    if token is None:
        return None
    return get_current_user(token, db)
