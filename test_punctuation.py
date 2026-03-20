import json
from pathlib import Path

from transcribe_enhance.application.punctuation_merge import merge_punctuation
from transcribe_enhance.domain.models import Segment, Word
from transcribe_enhance.infrastructure.ai_openai import (
    _coerce_transcription_segments,
    _coerce_transcription_words,
)


INPUT_LOG = Path("src/transcribe_enhance/infrastructure/transcription_segments.log")
OUTPUT_LOG = Path("src/transcribe_enhance/infrastructure/transcription_punctuation.log")


def _select_words_for_segments(segments: list[Segment], words: list[Word]) -> list[Word]:
    selected: list[Word] = []
    word_idx = 0

    for seg_idx, segment in enumerate(segments):
        next_start_ms = (
            segments[seg_idx + 1].start_ms if seg_idx + 1 < len(segments) else None
        )
        while word_idx < len(words):
            word = words[word_idx]
            if word.start_ms > segment.end_ms:
                break
            if (
                word.start_ms == segment.end_ms
                and next_start_ms is not None
                and word.start_ms >= next_start_ms
            ):
                break
            if word.start_ms >= segment.start_ms:
                selected.append(word)
            word_idx += 1

    return selected


def _debug_segment_word_alignment(
    segments: list[Segment], words: list[Word]
) -> tuple[int, Segment, list[Word]]:
    word_idx = 0

    for seg_idx, segment in enumerate(segments):
        next_start_ms = (
            segments[seg_idx + 1].start_ms if seg_idx + 1 < len(segments) else None
        )
        seg_words: list[Word] = []
        while word_idx < len(words):
            word = words[word_idx]
            if word.start_ms > segment.end_ms:
                break
            if (
                word.start_ms == segment.end_ms
                and next_start_ms is not None
                and word.start_ms >= next_start_ms
            ):
                break
            if word.start_ms >= segment.start_ms:
                seg_words.append(word)
            word_idx += 1

        try:
            merge_punctuation([segment], seg_words)
        except ValueError:
            return seg_idx, segment, seg_words

    raise AssertionError("No failing segment found")


def main() -> None:
    if not INPUT_LOG.exists():
        raise FileNotFoundError(f"Missing {INPUT_LOG}")

    data = json.loads(INPUT_LOG.read_text(encoding="utf-8"))
    segments = _coerce_transcription_segments(data["segments"])
    words = _coerce_transcription_words(data["words"])
    try:
        punctuated_words = merge_punctuation(segments, words)
    except ValueError as exc:
        seg_idx, segment, seg_words = _debug_segment_word_alignment(segments, words)
        print(f"Merge failed: {exc}")
        print(f"Failing segment index: {seg_idx}")
        print(f"Segment text: {segment.text}")
        print("Segment words:", [word.text for word in seg_words])
        raise

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

    first_segment_words = _select_words_for_segments(segments[:1], punctuated_words)
    print(f"Wrote {OUTPUT_LOG}")
    print("First segment words:", [word.text for word in first_segment_words])


if __name__ == "__main__":
    main()
