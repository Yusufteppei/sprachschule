from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from app.api.dependencies import get_moderator_agent, get_db, get_current_active_user
from app.schemas.interaction import InteractionResponse
from app.database import models
from app.services.audio import AudioService

router = APIRouter()

audio_service = AudioService()
STORY_AUDIO_DIR = Path(__file__).resolve().parents[4] / "static" / "story_audio"
STORY_AUDIO_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/", response_model=InteractionResponse)
async def interact(
    input_text: Optional[str] = Form(None),
    audio_file: Optional[UploadFile] = File(None),
    level: Optional[str] = Form(None),
    theme: Optional[str] = Form(None),
    moderator = Depends(get_moderator_agent),
    db = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    if not input_text and not audio_file:
        raise HTTPException(status_code=400, detail="Provide either input_text or audio_file.")

    transcript = None
    if audio_file is not None:
        audio_bytes = await audio_file.read()
        transcription = audio_service.transcribe(audio_bytes)
        transcript = transcription["text"]
        if not input_text:
            input_text = transcript

    input_text = input_text.strip() if input_text else ""

    # Get user defaults but don't append to input
    default_level = level or current_user.level
    default_theme = theme or current_user.theme
    default_language = current_user.target_language

    if not input_text:
        raise HTTPException(status_code=400, detail="Could not determine text input from request.")

    # Pass user context to moderator but let it extract from natural language
    result = await moderator.run(
        input_text,
        user_level=default_level,
        user_theme=default_theme,
        user_language=default_language,
    )

    # Defensive: ensure moderator returned a dict
    if result is None or not isinstance(result, dict):
        result = {
            "success": False,
            "agent": "ModeratorAgent",
            "data": {},
            "error": "Moderator returned invalid response"
        }
    if not result.get("success", False):
        return result

    try:
        response_data = result.copy() if isinstance(result, dict) else {"success": False, "agent": "ModeratorAgent", "data": {}}
    except Exception:
        response_data = {"success": False, "agent": "ModeratorAgent", "data": {}}
    story_info = response_data.get("data", {}).get("story")

    if story_info and response_data.get("data", {}).get("type") == "story":
        db_story = models.Story(
            title=story_info.get("title"),
            content=story_info.get("content"),
            level=story_info.get("level", "A1"),
            theme=story_info.get("theme", "General"),
            language=response_data.get("data", {}).get("language") or default_language
        )
        db.add(db_story)
        db.commit()
        db.refresh(db_story)

        if hasattr(current_user, 'mark_story_as_read'):
            current_user.mark_story_as_read(db, db_story.id)

        story_language = response_data.get("data", {}).get("language") or default_language
        if audio_service.supports_story_audio(story_language):
            audio_path = STORY_AUDIO_DIR / f"story_{db_story.id}.wav"
            audio_service.generate_story_audio(
                story_info.get("content", ""),
                audio_path,
                language=story_language
            )

            db_story.audio_file_path = str(audio_path)
            db_story.audio_file_url = f"/story/audio/{db_story.id}"
            db_story.audio_generated = True
            db.commit()
            db.refresh(db_story)

            story_info["audio_file_url"] = db_story.audio_file_url
            response_data["data"]["audio_url"] = db_story.audio_file_url

            story_info["id"] = db_story.id
            response_data["data"]["story"] = story_info

    # Attach transcript if we produced one while accepting audio
    if transcript:
        response_data["data"]["transcript"] = transcript

    return response_data
