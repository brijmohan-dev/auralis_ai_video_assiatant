from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Any

import streamlit as st
from dotenv import load_dotenv

from ai_video_assistant import run_pipeline

load_dotenv()
st.set_page_config(page_title="Auralis | Meeting Intelligence", page_icon="✦", layout="wide")


CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
:root { --bg:#08070c; --panel:#14111d; --line:rgba(255,255,255,.11); --muted:#aaa4b9; --violet:#a15cff; --pink:#d94fc9; }
.stApp { color:#f8f5ff; background:radial-gradient(circle at 90% 0%,rgba(125,46,221,.3),transparent 30rem),linear-gradient(135deg,#08070c,#10091a 58%,#1b0b25); font-family:'DM Sans',sans-serif; }
.block-container { max-width:1400px; padding:2.6rem 4rem 4rem; }
[data-testid="stSidebar"] { background:linear-gradient(180deg,#0e0b14,#13091c); border-right:1px solid var(--line); }
.brand { display:flex;align-items:center;gap:.7rem;margin-bottom:2.8rem; }.mark { display:grid;place-items:center;width:2.2rem;height:2.2rem;border-radius:10px;background:linear-gradient(135deg,#c17aff,#6425b5);font-size:1.2rem;box-shadow:0 8px 25px #8b42df55; }.brand-name {font:700 1.2rem 'Space Grotesk';}.subtle {color:var(--muted);font-size:.76rem;}.eyebrow {color:#c18aff;font-size:.72rem;font-weight:700;letter-spacing:.16em;text-transform:uppercase;margin-bottom:.7rem;} h1,h2,h3 {font-family:'Space Grotesk' !important;letter-spacing:-.04em !important;} h1 {font-size:clamp(2.5rem,5vw,5rem) !important;line-height:1 !important;margin:0 !important;}.hero {color:var(--muted);font-size:1.05rem;line-height:1.65;max-width:700px;margin:1rem 0 2rem;}.rule {height:1px;background:linear-gradient(90deg,#a15cff,transparent);margin:1.8rem 0;}.label {color:var(--muted);font-size:.72rem;font-weight:700;letter-spacing:.13em;text-transform:uppercase;margin:1rem 0 .6rem;}
.card,.metric {background:linear-gradient(145deg,rgba(31,24,45,.93),rgba(13,11,19,.93));border:1px solid var(--line);border-radius:14px;box-shadow:0 18px 45px #0003;padding:1.35rem;}.metric {padding:1rem 1.1rem;}.metric strong {font:700 1.45rem 'Space Grotesk';display:block;}.metric span {color:var(--muted);font-size:.76rem;}
.stTextInput input,.stTextArea textarea {background:#08070ccc !important;color:#fff !important;border:1px solid #a15cff44 !important;border-radius:9px !important;}.stButton>button,.stDownloadButton>button {color:white !important;border:0 !important;border-radius:9px !important;background:linear-gradient(100deg,#6824b9,#9c4df1 55%,#d052c8) !important;font-weight:700 !important;min-height:2.7rem;box-shadow:0 8px 22px #913bd544 !important;}.stButton>button:hover,.stDownloadButton>button:hover {filter:brightness(1.1);transform:translateY(-1px);}.stTabs [data-baseweb="tab-list"] {gap:1rem;border-bottom:1px solid var(--line);}.stTabs [aria-selected="true"] {color:#c18aff !important;}.stChatMessage {border:1px solid var(--line);background:#ffffff08;border-radius:12px;}
@media(max-width:800px){.block-container{padding:2rem 1rem 3rem;}h1{font-size:2.8rem !important;}.hero{font-size:.95rem;}}
</style>
"""


def init_state() -> None:
    st.session_state.setdefault("result", None)
    st.session_state.setdefault("messages", [])


def save_upload(uploaded_file: Any) -> Path:
    directory = Path(os.getenv("AI_VIDEO_ASSISTANT_UPLOAD_DIR", "uploads"))
    directory.mkdir(parents=True, exist_ok=True)
    suffix = Path(uploaded_file.name).suffix or ".media"
    path = directory / f"{uuid.uuid4().hex}{suffix}"
    path.write_bytes(uploaded_file.getbuffer())
    return path


def sidebar_source() -> tuple[str, str, str | None, bool]:
    with st.sidebar:
        st.markdown('<div class="brand"><div class="mark">✦</div><div><div class="brand-name">Auralis</div><div class="subtle">AI meeting intelligence</div></div></div>', unsafe_allow_html=True)
        st.markdown('<div class="label">Source</div>', unsafe_allow_html=True)
        mode = st.radio("Input", ["YouTube URL", "Upload media"], label_visibility="collapsed")
        url = st.text_input("YouTube URL", placeholder="https://youtube.com/watch?v=...", label_visibility="collapsed") if mode == "YouTube URL" else ""
        uploaded = st.file_uploader("Audio or video", type=["mp3", "wav", "m4a", "mp4", "mov", "webm"], label_visibility="collapsed") if mode == "Upload media" else None
        language = st.selectbox("Language", ["english", "hinglish"], format_func=lambda x: "English transcription" if x == "english" else "Hinglish → English")
        st.markdown('<div class="label">Run</div>', unsafe_allow_html=True)
        clicked = st.button("✦  Analyze meeting", use_container_width=True)
        if clicked:
            if mode == "YouTube URL":
                return url.strip(), language, url.strip(), True
            if uploaded is not None:
                path = save_upload(uploaded)
                return str(path), language, uploaded.name, True
            st.error("Choose a media file first.")
    return "", "english", None, False


def run_with_live_progress(source: str, language: str, source_name: str | None) -> None:
    events: list[str] = []
    current = st.empty()
    progress = st.progress(0, text="Starting meeting analysis")
    status = st.status("Working on your meeting", expanded=True)
    steps = ["Starting meeting analysis", "Downloading audio from YouTube", "Converting media to 16 kHz WAV", "Splitting audio into transcription chunks", "Transcribing", "Transcription complete", "Generating meeting title", "Writing executive summary", "Extracting action items", "Extracting key decisions", "Finding open questions", "Indexing transcript for meeting chat", "Analysis complete"]

    def on_progress(message: str) -> None:
        events.append(message)
        index = next((i for i, step in enumerate(steps) if step in message), min(len(steps) - 1, len(events)))
        percent = min(99, max(2, int((index + 1) / len(steps) * 100)))
        progress.progress(percent, text=message)
        current.markdown(f'<div class="card"><div class="label">Live activity</div><h3 style="margin:.2rem 0">{message}</h3><div class="subtle">Step {index + 1} of {len(steps)} · {len(events)} event(s) received</div></div>', unsafe_allow_html=True)
        with status:
            st.write(f"✓ {message}")

    try:
        result = run_pipeline(source, language, on_progress=on_progress)
        st.session_state.result = result
        st.session_state.messages = []
        progress.progress(100, text="Analysis complete")
        status.update(label=f"Ready · {source_name or 'meeting'}", state="complete", expanded=False)
    except Exception as error:
        status.update(label="Analysis failed", state="error", expanded=True)
        st.exception(error)


def render_results(result: dict[str, Any]) -> None:
    transcript = result.get("transcript", "")
    st.markdown('<div class="eyebrow">Analysis complete</div>', unsafe_allow_html=True)
    st.title(result.get("title", "Untitled meeting"))
    st.markdown('<p class="hero">A structured brief generated from your conversation, with every insight grounded in the transcript.</p>', unsafe_allow_html=True)
    columns = st.columns(3)
    for column, value, label in zip(columns, [f"{len(transcript.split()):,}", "4", "Indexed"], ["transcript words", "insight views", "meeting status"]):
        with column:
            st.markdown(f'<div class="metric"><strong>{value}</strong><span>{label}</span></div>', unsafe_allow_html=True)
    tabs = st.tabs(["Overview", "Action items", "Decisions", "Questions", "Transcript"])
    content = [result.get("summary", "No summary available."), result.get("action_items", "No action items found."), result.get("key_decisions", "No key decisions found."), result.get("open_questions", "No open questions found.")]
    for tab, text in zip(tabs[:4], content):
        with tab:
            st.markdown(f'<div class="card">{text}</div>', unsafe_allow_html=True)
    with tabs[4]:
        st.download_button("Download transcript", transcript, "meeting-transcript.txt", "text/plain")
        st.text_area("Transcript", transcript, height=420, label_visibility="collapsed")


def render_chat(result: dict[str, Any]) -> None:
    st.markdown('<div class="rule"></div><div class="eyebrow">Ask the meeting</div>', unsafe_allow_html=True)
    st.subheader("A focused conversation with your transcript")
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    question = st.chat_input("Ask about a decision, owner, deadline, or question")
    if question:
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)
        with st.chat_message("assistant"):
            with st.spinner("Searching the meeting..."):
                answer = result["rag_chain"].invoke(question)
            st.markdown(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})


def main() -> None:
    init_state()
    st.markdown(CSS, unsafe_allow_html=True)
    source, language, source_name, clicked = sidebar_source()
    st.markdown('<div class="eyebrow">Meeting intelligence, without the busywork</div>', unsafe_allow_html=True)
    st.title("Turn long-form video into clear next steps.")
    st.markdown('<p class="hero">Bring in a conversation. Watch it move through transcription, synthesis, extraction, and indexing in real time.</p>', unsafe_allow_html=True)
    st.markdown('<div class="rule"></div>', unsafe_allow_html=True)
    if clicked and source:
        run_with_live_progress(source, language, source_name)
    if st.session_state.result:
        render_results(st.session_state.result)
        render_chat(st.session_state.result)
    else:
        st.markdown('<div class="card"><div class="label">Start with a source</div><p class="subtle">Choose a YouTube URL or upload a meeting recording from the sidebar. The live activity panel will show each real pipeline step as it executes.</p></div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
