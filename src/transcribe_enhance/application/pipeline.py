"""Application pipeline orchestration."""

from pathlib import Path

from transcribe_enhance.domain.models import Segment, Word
from transcribe_enhance.infrastructure.ai_openai import transcribe_audio_openai
from transcribe_enhance.infrastructure.itt_writer import write_itt_from_segments
from transcribe_enhance.application.punctuation_merge import merge_punctuation


def _append_word(current_text: str, word: str) -> str:
    if not current_text:
        return word.lstrip()
    if word.startswith((" ", "\t")):
        return current_text + word
    return current_text + " " + word


def _split_words_into_segments(
    words: list[Word],
    max_chars: int,
) -> list[Segment]:
    segments: list[Segment] = []
    current_words: list[Word] = []
    current_text = ""

    def flush_segment() -> None:
        if not current_words:
            return
        segments.append(
            Segment(
                start_ms=current_words[0].start_ms,
                end_ms=current_words[-1].end_ms,
                text=current_text.strip(),
            )
        )

    for word in words:
        proposed = _append_word(current_text, word.text)
        if current_words and len(proposed) > max_chars:
            flush_segment()
            current_words = []
            current_text = ""
            proposed = _append_word(current_text, word.text)

        current_words.append(word)
        current_text = proposed

        if len(current_text) >= max_chars:
            flush_segment()
            current_words = []
            current_text = ""

    flush_segment()
    return segments


def run_pipeline(audio_path: Path, output_path: Path, max_chars_per_segment: int) -> None:
    segments, words = transcribe_audio_openai(audio_path)
    if not words:
        raise ValueError("No word timings returned from Whisper")
    punctuated_words = merge_punctuation(segments, words)
    if not punctuated_words:
        raise ValueError("No punctuated words produced from Whisper response")
    segments = _split_words_into_segments(punctuated_words, max_chars_per_segment)
    write_itt_from_segments(output_path, segments)
