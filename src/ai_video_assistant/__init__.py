
from os import PathLike
from collections.abc import Callable
from typing import Any

from ai_video_assistant.utils.audio_processor import process_input
from ai_video_assistant.core.transcriber import transcribe_all
from ai_video_assistant.core.summarize import summarize, generate_title
from ai_video_assistant.core.extractor import extract_action_items, extract_key_decisions, extract_questions
from ai_video_assistant.core.rag_engine import build_rag_chain, ask_question


def run_pipeline(
    source: str | PathLike[str],
    language: str = "english",
    on_progress: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    """Run the complete media-to-meeting-insights workflow."""
    if not str(source).strip():
        raise ValueError("source must not be empty")

    if on_progress:
        on_progress("Starting meeting analysis")
    chunks = process_input(source, on_progress=on_progress)

    transcript = transcribe_all(chunks, language, on_progress=on_progress)
    print(f"Raw transcription (first 300 characters): {transcript[:300]}")

    if on_progress:
        on_progress("Generating meeting title")
    title = generate_title(transcript)

    if on_progress:
        on_progress("Writing executive summary")
    summary = summarize(transcript)

    if on_progress:
        on_progress("Extracting action items")
    action_items = extract_action_items(transcript)

    if on_progress:
        on_progress("Extracting key decisions")
    decisions = extract_key_decisions(transcript)

    if on_progress:
        on_progress("Finding open questions")
    questions = extract_questions(transcript)

    if on_progress:
        on_progress("Indexing transcript for meeting chat")
    rag_chain = build_rag_chain(transcript)

    if on_progress:
        on_progress("Analysis complete")

    return {
        "title": title,
        "transcript": transcript,
        "summary": summary,
        "action_items": action_items,
        "key_decisions": decisions,
        "open_questions": questions,
        "rag_chain": rag_chain,
    }

def main() -> None:
    """Run the interactive command-line application."""
    source = input("Enter YouTube URL or local file path: ").strip()
    language = input("Language (english/hinglish): ").strip() or "english"
    result = run_pipeline(source, language)

    print("\n" + "=" * 60)
    print(f"📌 Title: {result['title']}")
    print(f"\n📋 Summary:\n{result['summary']}")
    print(f"\n✅ Action Items:\n{result['action_items']}")
    print(f"\n🔑 Key Decisions:\n{result['key_decisions']}")
    print(f"\n❓ Open Questions:\n{result['open_questions']}")
    print("=" * 60)

    # Phase 2 — Chat with your meeting via RAG
    print("\n💬 Chat with your meeting (type 'exit' to quit)\n")
    rag_chain = result["rag_chain"]
    while True:
        question = input("You: ").strip()
        if question.lower() in ["exit", "quit", "q"]:
            print("👋 Goodbye!")
            break
        if not question:
            continue
        answer = ask_question(rag_chain, question)
        print(f"\n🤖 Assistant: {answer}\n")


if __name__ == "__main__":
    main()