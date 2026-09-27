import os
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

import whisper


WHISPER_MODEL = os.getenv("WHISPER_MODEL", "small")

_model: Any | None = None


def load_model() -> Any:

    global _model  

    if _model is None:
        print(f"Loading Whisper model: {WHISPER_MODEL} ...")
        _model = whisper.load_model(WHISPER_MODEL)
        print("Whisper model loaded.")
    return _model


def _transcribe(chunk_path: str | os.PathLike[str], task: str) -> str:
    path = Path(chunk_path)
    if not path.is_file():
        raise FileNotFoundError(f"Audio chunk does not exist: {path}")

    result = load_model().transcribe(str(path), task=task)
    return str(result["text"]).strip()


def transcribe_chunk_whisper(chunk_path: str | os.PathLike[str]) -> str:
    return _transcribe(chunk_path, task="transcribe")


def transcribe_chunk_whisper_translation(chunk_path: str | os.PathLike[str]) -> str:
    """Transcribe Hindi/Hinglish locally and translate it to English."""
    return _transcribe(chunk_path, task="translate")



def transcribe_chunk(
    chunk_path: str | os.PathLike[str], language: str = "english"
) -> str:
    """
    Route one chunk to local Whisper transcription or translation.
    - english  → Whisper (local model)
    - hinglish → Whisper (local model, translated to English)
    """
    normalized_language = language.strip().lower()
    if normalized_language not in {"english", "hinglish"}:
        raise ValueError("language must be either 'english' or 'hinglish'")
    if normalized_language == "hinglish":
        return transcribe_chunk_whisper_translation(chunk_path)
    return transcribe_chunk_whisper(chunk_path)


def transcribe_all(
    chunks: Sequence[str | os.PathLike[str]],
    language: str = "english",
    on_progress: Callable[[str], None] | None = None,
) -> str:
    if not chunks:
        raise ValueError("At least one audio chunk is required")

    normalized_language = language.strip().lower()
    if normalized_language not in {"english", "hinglish"}:
        raise ValueError("language must be either 'english' or 'hinglish'")

    engine = "Whisper translation" if normalized_language == "hinglish" else "Whisper"
    print(f"Using {engine} for transcription.")

    transcripts: list[str] = []
    for i, chunk in enumerate(chunks):  

        print(f"Transcribing chunk {i + 1}/{len(chunks)}...")
        if on_progress:
            on_progress(f"Transcribing chunk {i + 1} of {len(chunks)} with {engine}")

        text = transcribe_chunk(chunk, language=normalized_language)
        if text:
            transcripts.append(text)

    print("Transcription complete.")
    if on_progress:
        on_progress("Transcription complete")

    return " ".join(transcripts)