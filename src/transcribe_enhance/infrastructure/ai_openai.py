"""OpenAI Whisper transcription adapter."""

import html
import json
import logging
import os
from pathlib import Path
import time
from typing import Any

from openai import OpenAI
from openai import OpenAIError

from transcribe_enhance.domain.models import Segment, Word


_logger = logging.getLogger("transcribe_enhance.ai_openai")


def _coerce_transcription_segments(raw_segments: Any) -> list[Segment]:
    if raw_segments is None:
        raise ValueError("OpenAI transcription response missing segments")

    segments: list[Segment] = []
    for item in raw_segments:
        if isinstance(item, dict):
            start = item.get("start")
            end = item.get("end")
            text = item.get("text")
        else:
            start = getattr(item, "start", None)
            end = getattr(item, "end", None)
            text = getattr(item, "text", None)

        if start is None or end is None or text is None:
            raise ValueError("OpenAI transcription segment missing start/end/text")

        start_ms = int(round(float(start) * 1000))
        end_ms = int(round(float(end) * 1000))
        cleaned = html.unescape(str(text)).strip()
        segments.append(Segment(start_ms=start_ms, end_ms=end_ms, text=cleaned))

    return segments


def _serialize_transcription_segments(raw_segments: Any) -> list[dict[str, Any]]:
    serialized: list[dict[str, Any]] = []
    if raw_segments is None:
        return serialized
    for item in raw_segments:
        if isinstance(item, dict):
            start = item.get("start")
            end = item.get("end")
            text = item.get("text")
        else:
            start = getattr(item, "start", None)
            end = getattr(item, "end", None)
            text = getattr(item, "text", None)
        serialized.append({"start": start, "end": end, "text": text})
    return serialized


def _coerce_transcription_words(raw_words: Any) -> list[Word]:
    if raw_words is None:
        raise ValueError("OpenAI transcription response missing words")

    words: list[Word] = []
    for item in raw_words:
        if isinstance(item, dict):
            start = item.get("start")
            end = item.get("end")
            text = item.get("word")
        else:
            start = getattr(item, "start", None)
            end = getattr(item, "end", None)
            text = getattr(item, "word", None)

        if start is None or end is None or text is None:
            raise ValueError("OpenAI transcription word missing start/end/word")

        start_ms = int(round(float(start) * 1000))
        end_ms = int(round(float(end) * 1000))
        cleaned = html.unescape(str(text))
        words.append(Word(start_ms=start_ms, end_ms=end_ms, text=cleaned))

    return words


def _serialize_transcription_words(raw_words: Any) -> list[dict[str, Any]]:
    serialized: list[dict[str, Any]] = []
    if raw_words is None:
        return serialized
    for item in raw_words:
        if isinstance(item, dict):
            start = item.get("start")
            end = item.get("end")
            text = item.get("word")
        else:
            start = getattr(item, "start", None)
            end = getattr(item, "end", None)
            text = getattr(item, "word", None)
        serialized.append({"start": start, "end": end, "word": text})
    return serialized


def transcribe_audio_openai(audio_path: Path) -> tuple[list[Segment], list[Word]]:
    if not os.getenv("OPENAI_API_KEY"):
        raise EnvironmentError("OPENAI_API_KEY is required to use OpenAI integration")

    client = OpenAI()
    request = {
        "model": "whisper-1",
        "response_format": "verbose_json",
        "timestamp_granularities": ["segment", "word"],
    }
    audio_bytes = audio_path.read_bytes()
    audio_size = len(audio_bytes)
    _logger.info(
        "OpenAI transcription request: model=%s response_format=%s timestamp_granularities=%s audio_path=%s audio_size_bytes=%s",
        request["model"],
        request["response_format"],
        request["timestamp_granularities"],
        audio_path,
        audio_size,
    )
    start_time = time.perf_counter()
    with audio_path.open("rb") as audio_file:
        try:
            response = client.audio.transcriptions.create(file=audio_file, **request)
        except OpenAIError as exc:
            elapsed_ms = int((time.perf_counter() - start_time) * 1000)
            _logger.exception(
                "OpenAI transcription failed after %sms: %s", elapsed_ms, exc
            )
            raise

    elapsed_ms = int((time.perf_counter() - start_time) * 1000)
    _logger.info("OpenAI transcription completed in %sms", elapsed_ms)
    raw_segments = getattr(response, "segments", None)
    if raw_segments is None and isinstance(response, dict):
        raw_segments = response.get("segments")
    raw_words = getattr(response, "words", None)
    if raw_words is None and isinstance(response, dict):
        raw_words = response.get("words")

    log_payload = {
        "audio_file": str(audio_path),
        "audio_size_bytes": audio_size,
        "elapsed_ms": elapsed_ms,
        "segments": _serialize_transcription_segments(raw_segments),
        "words": _serialize_transcription_words(raw_words),
    }
    if os.getenv("OPENAI_LOG_SEGMENTS") != "0":
        log_path = Path(__file__).with_name("transcription_segments.log")
        log_path.write_text(json.dumps(log_payload, ensure_ascii=False, indent=2) + "\n")
    else:
        _logger.debug(
            "OpenAI transcription summary: segments=%s elapsed_ms=%s",
            len(log_payload["segments"]),
            elapsed_ms,
        )

    return (
        _coerce_transcription_segments(raw_segments),
        _coerce_transcription_words(raw_words),
    )
