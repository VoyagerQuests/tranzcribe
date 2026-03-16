"""OpenAI Whisper transcription adapter."""

import html
import json
import logging
import os
from pathlib import Path
from typing import Any

from openai import OpenAI

from transcribe_enhance.domain.models import Segment


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


def transcribe_audio_openai(audio_path: Path) -> list[Segment]:
    if not os.getenv("OPENAI_API_KEY"):
        raise EnvironmentError("OPENAI_API_KEY is required to use OpenAI integration")

    client = OpenAI()
    request = {
        "model": "whisper-1",
        "response_format": "verbose_json",
        "timestamp_granularities": ["segment"],
    }
    with audio_path.open("rb") as audio_file:
        response = client.audio.transcriptions.create(file=audio_file, **request)

    raw_segments = getattr(response, "segments", None)
    if raw_segments is None and isinstance(response, dict):
        raw_segments = response.get("segments")

    log_path = Path(__file__).with_name("transcription_segments.log")
    log_payload = {
        "audio_file": str(audio_path),
        "segments": _serialize_transcription_segments(raw_segments),
    }
    log_path.write_text(json.dumps(log_payload, ensure_ascii=False, indent=2) + "\n")

    return _coerce_transcription_segments(raw_segments)
