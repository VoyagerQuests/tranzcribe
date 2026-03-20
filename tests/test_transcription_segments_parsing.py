import json
from pathlib import Path

import pytest

from transcribe_enhance.application.punctuation_merge import merge_punctuation
from transcribe_enhance.domain.models import Segment, Word
from transcribe_enhance.infrastructure.ai_openai import (
    _coerce_transcription_segments,
    _coerce_transcription_words,
)
from transcribe_enhance.application.pipeline import _split_words_into_segments


LOG_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "transcribe_enhance"
    / "infrastructure"
    / "transcription_segments.log"
)


@pytest.fixture(scope="module")
def whisper_log_payload() -> dict:
    return json.loads(LOG_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def parsed_transcription(whisper_log_payload: dict) -> tuple[list[Segment], list[Word]]:
    segments = _coerce_transcription_segments(whisper_log_payload["segments"])
    words = _coerce_transcription_words(whisper_log_payload["words"])
    return segments, words


def _segment_with_text(segments: list[Segment], text: str) -> Segment:
    for segment in segments:
        if segment.text == text:
            return segment
    raise AssertionError(f"Missing segment with text: {text}")


def _words_for_segments(segments: list[Segment], words: list[Word]) -> list[Word]:
    if not segments:
        return []

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


def test_coerce_transcription_segments_strips_text_and_converts_ms(
    whisper_log_payload: dict,
) -> None:
    segments = _coerce_transcription_segments(whisper_log_payload["segments"])

    assert segments[0] == Segment(
        start_ms=7220,
        end_ms=9600,
        text="When you start a new software project,",
    )
    assert segments[13] == Segment(
        start_ms=46760,
        end_ms=50700,
        text="I've been running software companies for the past 30 years.",
    )


def test_coerce_transcription_words_preserves_whisper_word_tokens(
    whisper_log_payload: dict,
) -> None:
    words = _coerce_transcription_words(whisper_log_payload["words"])

    assert words[0] == Word(start_ms=7220, end_ms=7820, text="When")
    assert [word.text for word in words[:8]] == [
        "When",
        "you",
        "start",
        "a",
        "new",
        "software",
        "project",
        "you're",
    ]
    assert any(word.text == "That's" for word in words)
    assert any(word.text == "I've" for word in words)


@pytest.mark.parametrize(
    ("segment_texts", "expected_words"),
    [
        (
            ["When you start a new software project,"],
            ["When", "you", "start", "a", "new", "software", "project,"],
        ),
        (
            ["How do you do this?"],
            ["How", "do", "you", "do", "this?"],
        ),
        (
            ["At some point, I was, what's the word,"],
            ["At", "some", "point,", "I", "was,", "what's", "the", "word,"],
        ),
        (
            ["read the blog there by Robert C. Martin."],
            ["read", "the", "blog", "there", "by", "Robert", "C.", "Martin."],
        ),
        (
            [
                "That's part of the...",
                "You, for example, have business logic in FastAPI.",
            ],
            [
                "That's",
                "part",
                "of",
                "the...",
                "You,",
                "for",
                "example,",
                "have",
                "business",
                "logic",
                "in",
                "FastAPI.",
            ],
        ),
    ],
)
def test_merge_punctuation_handles_real_whisper_punctuation_patterns(
    parsed_transcription: tuple[list[Segment], list[Word]],
    segment_texts: list[str],
    expected_words: list[str],
) -> None:
    segments, words = parsed_transcription
    selected_segments = [_segment_with_text(segments, text) for text in segment_texts]
    selected_words = _words_for_segments(selected_segments, words)

    punctuated_words = merge_punctuation(selected_segments, selected_words)

    assert [word.text for word in punctuated_words] == expected_words


def test_merge_punctuation_handles_adjacent_segments_with_mixed_punctuation(
    parsed_transcription: tuple[list[Segment], list[Word]],
) -> None:
    segments, words = parsed_transcription
    selected_segments = [
        _segment_with_text(segments, "read the blog there by Robert C. Martin."),
        _segment_with_text(segments, "The blog's a bit dated,"),
        _segment_with_text(segments, "some of the terminology is a bit old."),
    ]
    selected_words = _words_for_segments(selected_segments, words)

    punctuated_words = merge_punctuation(selected_segments, selected_words)

    assert [word.text for word in punctuated_words] == [
        "read",
        "the",
        "blog",
        "there",
        "by",
        "Robert",
        "C.",
        "Martin.",
        "The",
        "blog's",
        "a",
        "bit",
        "dated,",
        "some",
        "of",
        "the",
        "terminology",
        "is",
        "a",
        "bit",
        "old.",
    ]


def test_merge_punctuation_can_process_full_saved_whisper_log(
    parsed_transcription: tuple[list[Segment], list[Word]],
) -> None:
    segments, words = parsed_transcription

    punctuated_words = merge_punctuation(segments, words)

    assert punctuated_words
    assert punctuated_words[0].text == "When"
    assert any(word.text == "database," for word in punctuated_words)


def test_split_words_keeps_possible_in_following_caption(
    parsed_transcription: tuple[list[Segment], list[Word]],
) -> None:
    segments, words = parsed_transcription

    split_segments = _split_words_into_segments(merge_punctuation(segments, words), 20)

    texts = [segment.text for segment in split_segments]
    assert "moving as soon as" in texts
    assert "possible, which is" in texts
    assert "moving as soon as , which is" not in texts
