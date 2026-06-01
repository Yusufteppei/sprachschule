from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, WebSocket, WebSocketDisconnect, status
from fastapi.responses import FileResponse, StreamingResponse
from app.api.dependencies import get_story_agent, get_db, get_current_user_optional
from app.schemas.story import Story
from app.database import models
from app.services.audio import AudioService
from faster_whisper import WhisperModel
from kokoro import KPipeline
import soundfile as sf
import io
import time

router = APIRouter()

audio_service = AudioService()
STORY_AUDIO_DIR = Path(__file__).resolve().parents[4] / "static" / "story_audio"
STORY_AUDIO_DIR.mkdir(parents=True, exist_ok=True)


def _parse_read_story_ids(value: Optional[str]) -> set[int]:
    if not value:
        return set()
    return {int(item) for item in value.split(",") if item.strip().isdigit()}


def _get_unread_story(db, user, generic: bool = False, level: Optional[str] = None, theme: Optional[str] = None, language: Optional[str] = None):
    query = db.query(models.Story)
    if user is not None:
        read_ids = _parse_read_story_ids(user.read_story_ids)
        if read_ids:
            query = query.filter(~models.Story.id.in_(read_ids))

    if language:
        query = query.filter(models.Story.language == language)

    if not generic:
        if level:
            query = query.filter(models.Story.level == level)
        if theme:
            query = query.filter(models.Story.theme == theme)

    story = query.order_by(models.Story.id.asc()).first()
    if story is None and generic and user is not None:
        query = db.query(models.Story)
        if read_ids:
            query = query.filter(~models.Story.id.in_(read_ids))
        if language:
            query = query.filter(models.Story.language == language)
        story = query.order_by(models.Story.id.asc()).first()

    return story

@router.get("/generate", response_model=Story)
async def generate_story(
    level: Optional[str] = None,
    theme: Optional[str] = None,
    language: Optional[str] = None,
    agent = Depends(get_story_agent),
    db = Depends(get_db),
    current_user = Depends(get_current_user_optional)
):
    default_language = language or (current_user.target_language if current_user else "German")
    default_level = level or (current_user.level if current_user else "A1")
    default_theme = theme or (current_user.theme if current_user else "Software Development")

    result = await agent.run(level=default_level, theme=default_theme, language=default_language)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Story generation failed."))

    story = result["data"]["story"]
    db_story = models.Story(
        title=story["title"],
        content=story["content"],
        level=default_level,
        theme=default_theme,
        language=default_language
    )
    db.add(db_story)
    db.commit()
    db.refresh(db_story)

    if current_user is not None:
        current_user.mark_story_as_read(db, db_story.id)

    if audio_service.supports_story_audio(language):
        audio_path = STORY_AUDIO_DIR / f"story_{db_story.id}.wav"
        audio_service.generate_story_audio(story["content"], audio_path, language=language)

        db_story.audio_file_path = str(audio_path)
        db_story.audio_file_url = f"/story/audio/{db_story.id}"
        db_story.audio_generated = True
        db.commit()
        db.refresh(db_story)

    return db_story


@router.get("/", response_model=list[Story])
async def list_stories(db = Depends(get_db)):
    return db.query(models.Story).order_by(models.Story.id.desc()).all()


@router.get("/{story_id}", response_model=Story)
async def get_story(story_id: int, db = Depends(get_db), current_user = Depends(get_current_user_optional)):
    story = db.query(models.Story).filter(models.Story.id == story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found.")

    if current_user is not None:
        current_user.mark_story_as_read(db, story_id)

    return story


@router.get("/audio/{story_id}")
async def get_story_audio(story_id: int, db = Depends(get_db)):
    story = db.query(models.Story).filter(models.Story.id == story_id).first()
    if not story or not story.audio_file_path:
        raise HTTPException(status_code=404, detail="Story audio not found.")

    return FileResponse(story.audio_file_path, media_type="audio/wav", filename=Path(story.audio_file_path).name)


@router.get("/speak")
async def speak(text: str, title: str = "story"+str(int(time.time()))):
    
    print("Loading Kokoro...")
    # 'g' stands for German context, 'a' for American English
    pipeline = KPipeline(lang_code='f')
    
    print("✅ Kokoro Ready")
    generator = pipeline(text, voice='ff_siwis', speed=1) # af_sarah
    
    async def audio_stream():
        audio_file = open(f"{title}.wav", "wb")
        for _, _, audio in generator:
            # Convert NumPy chunk to WAV bytes in memory
            buffer = io.BytesIO()
            sf.write(buffer, audio, 24000, format='WAV')
            yield buffer.getvalue()
            audio_file.write(buffer.getvalue())
        audio_file.close()


    return StreamingResponse(audio_stream(), media_type="audio/wav")

@router.websocket("/ws/listen")
async def listen(websocket: WebSocket, token: str | None = None):
    # Simple token-in-query authentication for WebSocket
    from app.core.security import decode_access_token

    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    try:
        decode_access_token(token)
    except HTTPException:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    print("Loading Whisper...")
    whisper_model = WhisperModel("tiny", device="cpu")
    print("✅ Whisper Ready")
    await websocket.accept()
    # In-memory byte array for the current session
    audio_buffer = bytearray()

    try:
        while True:
            # 1. Receive raw binary chunk from browser
            chunk = await websocket.receive_bytes()
            audio_buffer.extend(chunk)

            # 2. Heuristic: Every 3 seconds of audio, run a "peek" transcription
            # (Assuming 16kHz mono 16-bit audio = 32000 bytes per second)
            if len(audio_buffer) > 96000:
                transcript = whisper_model.transcribe(io.BytesIO(audio_buffer))
                # Send partial feedback back to the student
                await websocket.send_json({"partial": transcript})

    except WebSocketDisconnect:
        # 3. Final processing on disconnect
        final_transcript = whisper_model.transcribe(io.BytesIO(audio_buffer))

        # 4. CRITICAL: Trigger the "Error Filter"
        # If the Critic Agent finds errors, we save ONLY those bytes.
        await process_and_save_errors(audio_buffer, final_transcript)
