from dotenv import load_dotenv


def main() -> None:
	load_dotenv()

	from ai_video_assistant.utils.audio_processor import process_input
	from ai_video_assistant.core.transcriber import transcribe_all
	from ai_video_assistant.core.summarize import summarize, generate_title
	from ai_video_assistant.core.extractor import (
		extract_action_items,
		extract_key_decisions,
		extract_questions,
	)

	source = "https://www.youtube.com/watch?v=_Q-e_nczWqM&t=223s"
	language = "english"



	chunks = process_input(source)


	transcript = transcribe_all(chunks, language=language)
	print("\n" + "=" * 60)
	print("TRANSCRIPT")
	print("=" * 60)
	print(transcript[:500] + "..." if len(transcript) > 500 else transcript)


	title = generate_title(transcript)
	summary = summarize(transcript)

	print("\n" + "=" * 60)
	print(f"TITLE: {title}")
	print("=" * 60)
	print("\nSUMMARY")
	print("-" * 60)
	print(summary)



	action_items = extract_action_items(transcript)
	decisions = extract_key_decisions(transcript)
	questions = extract_questions(transcript)

	print("\n" + "=" * 60)
	print("ACTION ITEMS")
	print("=" * 60)
	print(action_items)

	print("\n" + "=" * 60)
	print("KEY DECISIONS")
	print("=" * 60)
	print(decisions)

	print("\n" + "=" * 60)
	print("OPEN QUESTIONS")
	print("=" * 60)
	print(questions)


if __name__ == "__main__":
	main()