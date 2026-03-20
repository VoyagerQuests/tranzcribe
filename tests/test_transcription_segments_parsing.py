import json
from pathlib import Path

import pytest

from transcribe_enhance.application.pipeline import _split_words_into_segments
from transcribe_enhance.application.punctuation_merge import merge_punctuation
from transcribe_enhance.domain.models import Segment, Word
from transcribe_enhance.infrastructure.ai_openai import (
    _coerce_transcription_segments,
    _coerce_transcription_words,
)


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


def test_coerce_transcription_segments_strips_text_and_converts_ms(
    whisper_log_payload: dict,
) -> None:
    segments = _coerce_transcription_segments(whisper_log_payload["segments"])

    assert len(segments) == 9
    assert segments[0] == Segment(
        start_ms=7220,
        end_ms=9600,
        text="When you start a new software project,",
    )
    assert segments[-1] == Segment(
        start_ms=33420,
        end_ms=34740,
        text="Database systems might change.",
    )


def test_coerce_transcription_words_preserves_whisper_word_tokens(
    whisper_log_payload: dict,
) -> None:
    words = _coerce_transcription_words(whisper_log_payload["words"])

    assert len(words) == 71
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
    assert any(word.text == "possible" for word in words)
    assert any(word.text == "That's" for word in words)


@pytest.mark.parametrize(
    ("segment_text", "expected_words"),
    [
        (
            "When you start a new software project,",
            ["When", "you", "start", "a", "new", "software", "project,"],
        ),
        (
            "the project and you want to get moving as soon as possible,",
            [
                "the",
                "project",
                "and",
                "you",
                "want",
                "to",
                "get",
                "moving",
                "as",
                "soon",
                "as",
                "possible,",
            ],
        ),
        (
            "getting feedback from your customers. That's one thing.",
            [
                "getting",
                "feedback",
                "from",
                "your",
                "customers.",
                "That's",
                "one",
                "thing.",
            ],
        ),
        (
            "Database systems might change.",
            ["Database", "systems", "might", "change."],
        ),
    ],
)
def test_merge_punctuation_matches_current_saved_whisper_segments(
    parsed_transcription: tuple[list[Segment], list[Word]],
    segment_text: str,
    expected_words: list[str],
) -> None:
    segments, words = parsed_transcription
    selected_segment = _segment_with_text(segments, segment_text)

    punctuated_words = merge_punctuation([selected_segment], words)

    assert [word.text for word in punctuated_words] == expected_words


def test_merge_punctuation_can_process_full_saved_whisper_log(
    parsed_transcription: tuple[list[Segment], list[Word]],
) -> None:
    segments, words = parsed_transcription

    punctuated_words = merge_punctuation(segments, words)

    assert len(punctuated_words) == len(words)
    assert punctuated_words[0].text == "When"
    assert any(word.text == "possible," for word in punctuated_words)
    assert any(word.text == "customers." for word in punctuated_words)
    assert any(word.text == "thing." for word in punctuated_words)


def test_split_words_keeps_possible_in_following_caption(
    parsed_transcription: tuple[list[Segment], list[Word]],
) -> None:
    segments, words = parsed_transcription

    split_segments = _split_words_into_segments(merge_punctuation(segments, words), 20)

    texts = [segment.text for segment in split_segments]
    assert "moving as soon as" in texts
    assert "possible, which is" in texts
    assert "moving as soon as , which is" not in texts
