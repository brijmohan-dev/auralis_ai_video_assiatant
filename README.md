# Auralis: AI Video Assistant

Auralis turns a meeting recording or YouTube video into an English transcript, a concise meeting brief, action items, decisions, open questions, and a chat interface grounded in the transcript.

The Streamlit UI reports the pipeline's current stage as it runs, including individual transcription chunks.

## Features

- Process a YouTube URL or upload an audio/video file.
- Convert media to mono 16 kHz WAV and split it into chunks.
- Transcribe English locally with OpenAI Whisper.
- Translate Hindi/Hinglish speech into English with Whisper's local translation task.
- Generate a title and summary, and extract action items, decisions, and open questions with a local Ollama model.
- Ask follow-up questions using transcript retrieval and a local Chroma vector store.
- View live pipeline activity and download the transcript from the Streamlit UI.

## Requirements

- Python 3.11 or newer
- [uv](https://docs.astral.sh/uv/)
- FFmpeg and ffprobe
- [Ollama](https://ollama.com/) with the `llama3.2` model

The first run may download the Whisper model and the Hugging Face embedding model. Allow disk space and network access for those downloads.

### Install system tools

On macOS with Homebrew:

```bash
brew install ffmpeg
```

Install and start Ollama, then download the model used for summaries, extraction, and meeting chat:

```bash
ollama pull llama3.2
ollama serve
```

Keep Ollama running while using the application. If Ollama is already running as a background service, `ollama serve` may report that its port is occupied; in that case, just run the model pull command.

## Installation

From the repository root:

```bash
uv sync
```

To check that FFmpeg is available:

```bash
ffmpeg -version
ffprobe -version
```

If the executables are not on `PATH`, set `FFMPEG_LOCATION` to their directory (or to either executable):

```bash
export FFMPEG_LOCATION="/opt/homebrew/bin"
```

## Run the application

Start the Streamlit interface:

```bash
uv run streamlit run src/ai_video_assistant/app.py
```

Open the local URL printed by Streamlit, usually `http://localhost:8501`. Choose a YouTube URL or upload a supported media file, select a transcription mode, and choose **Analyze meeting**. The interface displays actual progress events as the pipeline executes.

Supported upload extensions are MP3, WAV, M4A, MP4, MOV, and WEBM. YouTube URLs must be accessible to yt-dlp.

The interactive command-line entry point is also available:

```bash
uv run ai-video-assistant
```

## Language modes

- **English transcription**: transcribes speech into its spoken language. It is intended for English audio.
- **Hinglish to English**: uses Whisper's `translate` task to translate non-English speech into English. This runs locally and does not require a Sarvam API key.

## Configuration

Configuration can be provided in a `.env` file at the repository root or as environment variables:

| Variable | Default | Purpose |
| --- | --- | --- |
| `WHISPER_MODEL` | `small` | Whisper model name, for example `base`, `small`, or `medium`. Larger models generally need more memory and compute. |
| `FFMPEG_LOCATION` | Auto-detected | Directory containing `ffmpeg` and `ffprobe`, or a path to either executable. |
| `AI_VIDEO_ASSISTANT_DOWNLOAD_DIR` | `downloads` | Directory used for downloaded YouTube audio. |
| `AI_VIDEO_ASSISTANT_UPLOAD_DIR` | `uploads` | Directory used for files uploaded through the UI. |

Example `.env`:

```dotenv
WHISPER_MODEL=small
FFMPEG_LOCATION=/opt/homebrew/bin
AI_VIDEO_ASSISTANT_DOWNLOAD_DIR=downloads
AI_VIDEO_ASSISTANT_UPLOAD_DIR=uploads
```

Ollama currently uses `llama3.2`; the embedding model is `all-MiniLM-L6-v2`. These model names are configured in the source code.

## Project layout

```text
src/ai_video_assistant/
├── app.py                 # Streamlit UI
├── __init__.py            # Pipeline and CLI entry point
├── core/
│   ├── transcriber.py     # Local Whisper transcription and translation
│   ├── summarize.py       # Title and summary generation
│   ├── extractor.py       # Action items, decisions, and questions
│   ├── rag_engine.py      # Transcript question answering
│   └── vector_store.py    # Chroma and embeddings
└── utils/
    └── audio_processor.py # Downloading, conversion, and chunking
```

## Troubleshooting

### `ffmpeg and ffprobe are required`

Install FFmpeg (`brew install ffmpeg` on macOS), confirm both commands work, and set `FFMPEG_LOCATION` if their directory is not discoverable by the application.

### Ollama connection or model errors

Make sure Ollama is running and the model is present:

```bash
ollama pull llama3.2
ollama list
```

### Transcription is slow

Whisper runs locally. Consider setting `WHISPER_MODEL=base` for lower resource use, or choose a larger model when transcription accuracy is more important and the machine has sufficient resources.

### YouTube download errors

Check that the URL is publicly accessible and that yt-dlp is current. Some videos may be unavailable due to age, region, authentication, or uploader restrictions.

## Notes on data and runtime

Audio transcription and Ollama inference run locally. YouTube media is fetched by yt-dlp, and first-time model downloads require network access. Uploaded files, downloaded audio, converted WAV files, chunks, and the Chroma database are stored locally; remove the relevant `uploads/`, `downloads/`, and `vector_db/` data when you no longer need it.
