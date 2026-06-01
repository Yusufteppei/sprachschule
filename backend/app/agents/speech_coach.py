from typing import Any, Dict, List
from app.agents.base import Agent
from app.services.audio import AudioService
import difflib
import re


class SpeechCoachAgent(Agent):
    """Speech coach that uses fuzzy matching between reference words and
    transcribed hypothesis words to detect likely mispronunciations.

    Heuristic rules:
    - Tokenize words using a simple word-regex
    - Ignore very short words (<=2 chars)
    - For each reference word, search a small window in the hypothesis
      (±2 positions) to find the best fuzzy match (SequenceMatcher)
    - Mark a word as an issue when best ratio < threshold (default 0.75)
    """

    def __init__(self, model: str = "gpt-4o-mini", threshold: float = 0.75, window: int = 2):
        super().__init__(model=model)
        self.audio_service = AudioService()
        self.threshold = threshold
        self.window = window

    def _tokenize(self, text: str) -> List[str]:
        # Keep only word-like tokens (letters, numbers). Lowercase for comparison.
        return re.findall(r"\b[\wäöüÄÖÜß]+\b", (text or "").lower())

    async def run(self, audio_bytes: bytes, reference_text: str, language: str = "German") -> Dict[str, Any]:
        try:
            if not audio_bytes or not reference_text:
                return self._format_response(False, error="Missing audio or reference text")

            transcription = self.audio_service.transcribe(audio_bytes)
            transcript_text = (transcription.get("text") or "").strip()

            ref_words = self._tokenize(reference_text)
            hyp_words = self._tokenize(transcript_text)

            issues = []

            for i, ref in enumerate(ref_words):
                if len(ref) <= 2:
                    continue

                best_ratio = 0.0
                best_match = None
                start = max(0, i - self.window)
                end = min(len(hyp_words), i + self.window + 1)
                for j in range(start, end):
                    hyp = hyp_words[j]
                    ratio = difflib.SequenceMatcher(None, ref, hyp).ratio()
                    if ratio > best_ratio:
                        best_ratio = ratio
                        best_match = hyp

                # If we couldn't find any hypothesis token, it's suspicious
                if best_match is None or best_ratio < self.threshold:
                    issues.append({"word": ref, "position": i, "best_match": best_match, "score": round(best_ratio, 2)})

            # Aggregate by word and include sample score/count
            agg: Dict[str, Dict[str, Any]] = {}
            for it in issues:
                w = it["word"]
                if w not in agg:
                    agg[w] = {"count": 0, "last_score": it.get("score", 0.0)}
                agg[w]["count"] += 1
                agg[w]["last_score"] = it.get("score", agg[w]["last_score"]) or agg[w]["last_score"]

            issue_list = [{"word": w, "count": v["count"], "language": language, "last_score": v["last_score"]} for w, v in agg.items()]

            return self._format_response(True, data={"transcript": transcript_text, "issues": issue_list})

        except Exception as e:
            return self._format_response(False, error=str(e))
