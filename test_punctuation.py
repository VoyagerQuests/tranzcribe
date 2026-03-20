import json
from pathlib import Path

from transcribe_enhance.application.punctuation_merge import merge_punctuation
from transcribe_enhance.infrastructure.ai_openai import (
    _coerce_transcription_segments,
    _coerce_transcription_words,
)


INPUT_LOG = Path("src/transcribe_enhance/infrastructure/transcription_segments.log")
OUTPUT_LOG = Path("src/transcribe_enhance/infrastructure/transcription_punctuation.log")


def main() -> None:
    if not INPUT_LOG.exists():
        raise FileNotFoundError(f"Missing {INPUT_LOG}")

    data = json.loads(INPUT_LOG.read_text(encoding="utf-8"))
    segments = _coerce_transcription_segments(data["segments"])
    words = _coerce_transcription_words(data["words"])
    punctuated_words = merge_punctuation(segments, words)

    output = {
        "audio_file": data.get("audio_file"),
        "audio_size_bytes": data.get("audio_size_bytes"),
        "elapsed_ms": data.get("elapsed_ms"),
        "segments": [
            {
                "start": segment.start_ms / 1000,
                "end": segment.end_ms / 1000,
                "text": segment.text,
            }
            for segment in segments
        ],
        "words": [
            {
                "start": word.start_ms / 1000,
                "end": word.end_ms / 1000,
                "word": word.text,
            }
            for word in punctuated_words
        ],
    }
    OUTPUT_LOG.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n")
    print(f"Wrote {OUTPUT_LOG}")


if __name__ == "__main__":
    main()
