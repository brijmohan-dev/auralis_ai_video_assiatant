import os
import shutil
from pathlib import Path
from collections.abc import Callable
from typing import Union

import yt_dlp
from pydub import AudioSegment

PathLike = Union[str, os.PathLike[str]]
ProgressCallback = Callable[[str], None]
DOWNLOAD_DIR = Path(os.getenv("AI_VIDEO_ASSISTANT_DOWNLOAD_DIR", "downloads"))


def _find_ffmpeg_location() -> str:
    """Return a directory containing both ffmpeg and ffprobe."""
    configured_location = os.getenv("FFMPEG_LOCATION")
    candidates = [configured_location] if configured_location else []
    candidates.extend([
        shutil.which("ffmpeg"),
        "/opt/homebrew/bin/ffmpeg",
        "/usr/local/bin/ffmpeg",
    ])

    for candidate in candidates:
        if not candidate:
            continue
        directory = Path(candidate) if os.path.isdir(candidate) else Path(candidate).parent
        ffmpeg = directory / "ffmpeg"
        ffprobe = directory / "ffprobe"
        if all(path.is_file() and os.access(path, os.X_OK) for path in (ffmpeg, ffprobe)):
            return str(directory)

    raise RuntimeError(
        "ffmpeg and ffprobe are required for YouTube downloads. "
        "Install them with `brew install ffmpeg`, or set FFMPEG_LOCATION "
        "to the directory containing both executables."
    )

def _configure_ffmpeg() -> str:
    """Configure pydub and return the directory containing FFmpeg."""
    location = _find_ffmpeg_location()
    AudioSegment.converter = str(Path(location) / "ffmpeg")
    AudioSegment.ffprobe = str(Path(location) / "ffprobe")
    return location


def download_youtube_audio(url: str) -> str:
    """Download a YouTube audio stream and convert it to WAV."""
    if not url.startswith(("http://", "https://")):
        raise ValueError("YouTube source must be an http:// or https:// URL")

    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    output_path = str(DOWNLOAD_DIR / "%(title)s.%(ext)s")
    ffmpeg_location = _find_ffmpeg_location()
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": output_path,
        "ffmpeg_location": ffmpeg_location,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
                "preferredquality": "192"
            }
        ],
        "quiet": True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = Path(ydl.prepare_filename(info)).with_suffix(".wav")
    return str(filename)

def convert_to_wav(input_path: PathLike) -> str:
    """Convert an audio/video file to mono, 16 kHz WAV."""
    source = Path(input_path)
    if not source.is_file():
        raise FileNotFoundError(f"Input media file does not exist: {source}")

    _configure_ffmpeg()
    output_path = source.with_name(f"{source.stem}_converted.wav")
    audio = AudioSegment.from_file(input_path)
    audio = audio.set_channels(1).set_frame_rate(16000)
    audio.export(output_path, format="wav")
    return str(output_path)

def chunk_audio(wav_path: PathLike, chunk_minutes: int = 10) -> list[str]:
    """Split a WAV file into fixed-duration WAV chunks."""
    source = Path(wav_path)
    if not source.is_file():
        raise FileNotFoundError(f"WAV file does not exist: {source}")
    if chunk_minutes <= 0:
        raise ValueError("chunk_minutes must be greater than zero")

    _configure_ffmpeg()
    audio = AudioSegment.from_wav(source)
    chunk_ms = chunk_minutes * 60 * 1000

    chunks: list[str] = []
    for i, start in enumerate(range(0, len(audio), chunk_ms)):
        chunk = audio[start: start + chunk_ms]
        chunk_path = source.with_name(f"{source.stem}_chunk_{i}.wav")
        chunk.export(chunk_path, format="wav")

        chunks.append(str(chunk_path))

    return chunks

def process_input(source: PathLike, on_progress: ProgressCallback | None = None) -> list[str]:
    """Prepare a local media file or YouTube URL for transcription."""
    source_value = os.fspath(source)
    if source_value.startswith(("http://", "https://")):
        print("Detected YouTube URL. Downloading audio...")
        if on_progress:
            on_progress("Downloading audio from YouTube")
        wav_path = download_youtube_audio(source_value)
    else:
        print("Detected local file. Converting to WAV...")
        if on_progress:
            on_progress("Converting media to 16 kHz WAV")
        wav_path = convert_to_wav(source_value)

    print("Chunking audio...")
    if on_progress:
        on_progress("Splitting audio into transcription chunks")
    chunks = chunk_audio(wav_path)
    print(f"Audio ready - {len(chunks)} chunk(s) created.")
    if on_progress:
        on_progress(f"Prepared {len(chunks)} audio chunk(s)")
    return chunks 