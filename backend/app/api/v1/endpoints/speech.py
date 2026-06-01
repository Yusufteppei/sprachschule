from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Form
from typing import Optional
from app.api.dependencies import get_speech_coach_agent, get_db, get_current_active_user, get_moderator_agent
from app.services.audio import AudioService
from app.database import models
from app.database.session import get_db as db_session
from datetime import datetime

router = APIRouter()
audio_service = AudioService()


@router.post("/analyze")
async def analyze_speech(
    story_id: int = Form(...),
    audio_file: UploadFile = File(...),
    coach = Depends(get_speech_coach_agent),
    moderator = Depends(get_moderator_agent),
    db = Depends(get_db),
    current_user = Depends(get_current_active_user),
):
    if audio_file is None:
        raise HTTPException(status_code=400, detail="Missing audio file")

    audio_bytes = await audio_file.read()

    # Find story
    story = db.query(models.Story).filter(models.Story.id == story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    # Run speech coach
    result = await coach.run(audio_bytes, story.content, language=story.language)
    if not result.get("success", False):
        return result

    data = result.get("data", {})
    issues = data.get("issues", [])

    # Persist issues to DB per-word
    for it in issues:
        word = it.get("word")
        count = it.get("count", 1)
        word_lang = it.get("language") or story.language

        existing = db.query(models.SpeechIssue).filter(models.SpeechIssue.user_id == current_user.id, models.SpeechIssue.word == word, models.SpeechIssue.word_language == word_lang).first()
        if existing:
            existing.mispronunciation_count = (existing.mispronunciation_count or 0) + count
            existing.last_mispronounced_at = datetime.utcnow()
            db.add(existing)
            db.commit()
            db.refresh(existing)
        else:
            si = models.SpeechIssue(
                user_id=current_user.id,
                word=word,
                word_language=word_lang,
                mispronunciation_count=count,
                last_mispronounced_at=datetime.utcnow()
            )
            db.add(si)
            db.commit()
            db.refresh(si)

    # Let moderator format a response to the user about pronunciation
    # Reuse moderator formatting by creating a simple feedback message
    feedback_text = f"We detected {len(issues)} challenging words. Would you like focused practice?"
    formatted = moderator._format_response(True, data={"type": "speech_feedback", "feedback": feedback_text, "issues": issues})

    return formatted
