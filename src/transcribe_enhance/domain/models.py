"""Domain models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class OutputRules:
    max_chars_per_line: int
    max_lines_per_caption: int
    max_reading_speed_cps: int
    min_duration_ms: int
    max_duration_ms: int
    line_break_style: Literal["punctuation", "phrase"]
    casing: Literal["sentence", "upper", "lower"]
    punctuation: Literal["standard", "minimal", "strict"]
    profanity_policy: Literal["mask", "keep", "remove"]


@dataclass(frozen=True)
class Context:
    purpose: str
    audience: str
    tone: str


@dataclass(frozen=True)
class AIConfig:
    provider: Literal["openai", "gemini"]
    model: str
    temperature: float


@dataclass(frozen=True)
class Instructions:
    context: Context
    output_rules: OutputRules
    ai: AIConfig


@dataclass(frozen=True)
class Segment:
    start_ms: int
    end_ms: int
    text: str
