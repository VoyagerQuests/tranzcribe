"""Domain models."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Segment:
    start_ms: int
    end_ms: int
    text: str


@dataclass(frozen=True)
class Word:
    start_ms: int
    end_ms: int
    text: str
