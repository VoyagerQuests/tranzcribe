"""OpenAI provider adapter."""

import html
import json
import logging
import os
from typing import Any

from openai import OpenAI

from transcribe_enhance.domain.models import Instructions, Segment


_SYSTEM_PROMPT = (
    "You are a transcript editor. Improve the transcript text for accuracy, "
    "grammar, and clarity. Do not change timing or reorder segments."
)

_logger = logging.getLogger("transcribe_enhance.ai_openai")


def _build_user_payload(segments: list[Segment], instructions: Instructions) -> dict[str, Any]:
    return {
        "context": {
            "purpose": instructions.context.purpose,
            "audience": instructions.context.audience,
            "tone": instructions.context.tone,
            "details": instructions.context.details,
        },
        "output_rules": {
            "max_chars_per_line": instructions.output_rules.max_chars_per_line,
            "max_lines_per_caption": instructions.output_rules.max_lines_per_caption,
            "max_reading_speed_cps": instructions.output_rules.max_reading_speed_cps,
            "min_duration_ms": instructions.output_rules.min_duration_ms,
            "max_duration_ms": instructions.output_rules.max_duration_ms,
            "line_break_style": instructions.output_rules.line_break_style,
            "casing": instructions.output_rules.casing,
            "punctuation": instructions.output_rules.punctuation,
            "profanity_policy": instructions.output_rules.profanity_policy,
        },
        "segment_count": len(segments),
        "segments": [
            {
                "id": idx,
                "start_ms": segment.start_ms,
                "end_ms": segment.end_ms,
                "text": segment.text,
            }
            for idx, segment in enumerate(segments)
        ],
    }


def _extract_output_text(response: Any) -> str:
    output_text = getattr(response, "output_text", None)
    if output_text:
        return output_text
    output = getattr(response, "output", None)
    if output:
        for item in output:
            for content in getattr(item, "content", []):
                text = getattr(content, "text", None)
                if text:
                    return text
    raise ValueError("Unable to extract text from OpenAI response")


def enhance_segments_openai(
    segments: list[Segment],
    instructions: Instructions,
) -> list[Segment]:
    if not os.getenv("OPENAI_API_KEY"):
        raise EnvironmentError("OPENAI_API_KEY is required to use OpenAI integration")

    client = OpenAI()
    payload = _build_user_payload(segments, instructions)
    _logger.info(
        "OpenAI request: model=%s segments=%s temperature=%s",
        instructions.ai.model,
        len(segments),
        instructions.ai.temperature,
    )
    _logger.debug("OpenAI payload: %s", json.dumps(payload, ensure_ascii=False))

    response = client.responses.create(
        model=instructions.ai.model,
        input=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    "Return JSON only. The response MUST include the same number of "
                    "segments as provided, and each segment must include the same id. "
                    f"segment_count MUST be {len(segments)}.\\n\\n"
                    + json.dumps(payload, ensure_ascii=False)
                ),
            },
        ],
        temperature=instructions.ai.temperature,
        text={
            "format": {
                "type": "json_schema",
                "name": "subtitle_segments",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "segment_count": {"type": "integer"},
                        "segments": {
                            "type": "array",
                            "minItems": len(segments),
                            "maxItems": len(segments),
                            "items": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "integer"},
                                    "text": {"type": "string"},
                                },
                                "required": ["id", "text"],
                                "additionalProperties": False,
                            },
                        },
                    },
                    "required": ["segment_count", "segments"],
                    "additionalProperties": False,
                },
            }
        },
    )

    output_text = _extract_output_text(response)
    _logger.info("OpenAI response length: %s", len(output_text))
    if os.getenv("OPENAI_LOG_FULL") == "1":
        _logger.debug("OpenAI response: %s", output_text)
    else:
        _logger.debug("OpenAI response preview: %s", output_text[:2000])
    data = json.loads(output_text)
    if data.get("segment_count") != len(segments):
        _logger.error(
            "OpenAI segment_count mismatch: expected=%s got=%s",
            len(segments),
            data.get("segment_count"),
        )
    items = data.get("segments")
    if not isinstance(items, list):
        _logger.error("OpenAI response JSON: %s", output_text)
        raise ValueError("AI response missing 'segments' list")

    expected = len(segments)
    if len(items) != expected:
        _logger.error(
            "OpenAI segment count mismatch: expected=%s got=%s", expected, len(items)
        )
        _logger.error("OpenAI response JSON: %s", output_text)
        raise ValueError("AI response did not return the expected number of segments")

    updated: list[Segment] = []
    for segment, item in zip(segments, items, strict=True):
        text = item.get("text")
        if not isinstance(text, str):
            raise ValueError("AI response item missing 'text'")
        cleaned = html.unescape(text).strip()
        updated.append(
            Segment(
                start_ms=segment.start_ms,
                end_ms=segment.end_ms,
                text=cleaned,
            )
        )

    return updated
