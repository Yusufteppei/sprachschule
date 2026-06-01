from faster_whisper import WhisperModel
import soundfile as sf
import io
import numpy as np
import time
import wave
from pathlib import Path
from kokoro import KPipeline
from piper import PiperVoice, SynthesisConfig


BACKEND_DIR = Path(__file__).resolve().parents[2]
GERMAN_PIPER_MODEL = BACKEND_DIR / "de_DE-thorsten-low.onnx"
GERMAN_PIPER_CONFIG = BACKEND_DIR / "de_DE-thorsten-low.onnx.json"
KOKORO_LANGUAGE_CONFIG = {
    "french": {"lang_code": "f", "voice": "ff_siwis"},
    "spanish": {"lang_code": "e", "voice": "ef_dora"},
    "italian": {"lang_code": "i", "voice": "if_sara"},
}
SUPPORTED_STORY_AUDIO_LANGUAGES = set(KOKORO_LANGUAGE_CONFIG) | {"german"}


class AudioService:
    def __init__(self, model_size="base"):
        # "base" is the best balance of speed vs accuracy for a local tutor.
        # "tiny" is faster but might miss subtle pronunciation errors.
        self.model = WhisperModel(model_size, device="cpu", compute_type="int8")
        self._piper_voices = {}

    def transcribe(self, audio_file: bytes) -> dict:
        # Convert bytes to a file-like object
        audio_fp = io.BytesIO(audio_file)
        
        segments, info = self.model.transcribe(audio_fp, beam_size=5)
        
        full_text = ""
        for segment in segments:
            full_text += segment.text
        
        return {
            "text": full_text.strip(),
            "language": info.language,
            "language_probability": info.language_probability
        }

    def generate_story_audio(
        self,
        text: str,
        output_path: Path,
        language: str = "German",
        lang_code: str = "f",
        voice: str = "ff_siwis",
        speed: float = 1.0
    ) -> Path:
        """Generate a story audio WAV file from the provided text."""
        normalized_language = self._normalize_language(language)

        if normalized_language == "german":
            return self._generate_german_story_audio(text, output_path, speed=speed)

        kokoro_config = KOKORO_LANGUAGE_CONFIG.get(normalized_language)
        if kokoro_config:
            lang_code = kokoro_config["lang_code"]
            voice = kokoro_config["voice"]
        elif normalized_language not in ("", "french"):
            raise ValueError(f"Story audio is not supported for {language}.")

        pipeline = KPipeline(lang_code=lang_code)
        generator = pipeline(text, voice=voice, speed=speed)

        output_path.parent.mkdir(parents=True, exist_ok=True)

        chunks = [audio for _, _, audio in generator]
        if not chunks:
            sf.write(output_path, np.array([], dtype=np.float32), 24000, format="WAV")
            return output_path

        full_audio = np.concatenate(chunks)
        sf.write(output_path, full_audio, 24000, format="WAV")

        return output_path

    def supports_story_audio(self, language: str) -> bool:
        return self._normalize_language(language) in SUPPORTED_STORY_AUDIO_LANGUAGES

    def _generate_german_story_audio(
        self,
        text: str,
        output_path: Path,
        speed: float = 1.0
    ) -> Path:
        """Generate German story audio with the local Piper German voice."""
        if not GERMAN_PIPER_MODEL.exists() or not GERMAN_PIPER_CONFIG.exists():
            raise FileNotFoundError(
                "German Piper voice files are missing: "
                f"{GERMAN_PIPER_MODEL} and {GERMAN_PIPER_CONFIG}"
            )

        output_path.parent.mkdir(parents=True, exist_ok=True)
        voice = self._get_piper_voice("German", GERMAN_PIPER_MODEL, GERMAN_PIPER_CONFIG)
        syn_config = SynthesisConfig(
            length_scale=1 / speed if speed > 0 else 1.0,
            normalize_audio=True,
        )

        with wave.open(str(output_path), "wb") as wav_file:
            voice.synthesize_wav(text, wav_file, syn_config=syn_config)

        return output_path

    def _get_piper_voice(
        self,
        language: str,
        model_path: Path,
        config_path: Path
    ) -> PiperVoice:
        voice = self._piper_voices.get(language)
        if voice is None:
            voice = PiperVoice.load(model_path, config_path=config_path)
            self._piper_voices[language] = voice

        return voice

    def _normalize_language(self, language: str) -> str:
        return (language or "").strip().lower()
    
    def save_error_segment(full_buffer, start_sec, end_sec, word):
        # Calculate bytes (SampleRate * BytesPerSample * Seconds)
        start_byte = int(start_sec * 16000 * 2)
        end_byte = int(end_sec * 16000 * 2)
        
        error_slice = full_buffer[start_byte:end_byte]
        
        with open(f"revisions/{word}_{int(time.time())}.wav", "wb") as f:
            # Wrap with a proper WAV header using soundfile
            sf.write(f, error_slice, 16000)
    
model = AudioService()
