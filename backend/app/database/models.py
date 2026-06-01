from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session
from app.core.enums import TargetLanguage, ProficiencyLevel
import time

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    full_name = Column(String, default="")

    level = Column(String, default=ProficiencyLevel.B2)  # Language proficiency level
    target_language = Column(String, default=TargetLanguage.GERMAN)  # User's target learning language
    theme = Column(String, default="Technology")  # Preferred story theme
    read_story_ids = Column(String, default="")  # Comma-separated list of story ids read by the user

    def read_story_ids_list(self) -> list[int]:
        if not self.read_story_ids:
            return []
        return [int(item.strip()) for item in self.read_story_ids.split(",") if item.strip().isdigit()]

    def mark_story_as_read(self, db: Session, story_id: int) -> None:
        ids = self.read_story_ids_list()
        if story_id in ids:
            return
        ids.append(story_id)
        ids = sorted(set(ids))
        self.read_story_ids = ",".join(str(i) for i in ids)
        db.add(self)
        db.commit()
        db.refresh(self)


class Story(Base):
    __tablename__ = "stories"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    content = Column(String)
    level = Column(String, default="A1")
    theme = Column(String, default="Technology")
    language = Column(String, default="German")

    created_at = Column(String, default=time.strftime("%Y-%m-%d %H:%M:%S"))

    audio_file_path = Column(String, nullable=True)  # Path to the generated audio file (optional)
    audio_file_url = Column(String, nullable=True)   # URL to access the audio file (optional)
    audio_generated = Column(Boolean, default=False)  # Flag to indicate if audio has been generated


class SpeechIssue(Base):
    __tablename__ = "speech_issues"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    word = Column(String, index=True)
    word_language = Column(String, default="German")
    mispronunciation_count = Column(Integer, default=0)
    last_mispronounced_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def bump(self, db: Session):
        self.mispronunciation_count = (self.mispronunciation_count or 0) + 1
        db.add(self)
        db.commit()
        db.refresh(self)