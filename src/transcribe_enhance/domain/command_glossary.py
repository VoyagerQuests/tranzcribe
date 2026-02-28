"""Command glossary and enforcement rules."""

import re
from dataclasses import dataclass

from transcribe_enhance.domain.models import Segment


@dataclass(frozen=True)
class CommandRule:
    phrase: str
    tokens: tuple[str, ...]


DEFAULT_RULES: list[CommandRule] = [
    CommandRule("uv sync", ("uv", "sync")),
    CommandRule("uv run", ("uv", "run")),
    CommandRule("uv add", ("uv", "add")),
    CommandRule("uv pip install -e .", ("uv", "pip", "install", "-e", ".")),
    CommandRule("git clone", ("git", "clone")),
]


def enforce_command_glossary(segments: list[Segment]) -> list[Segment]:
    """Enforce glossary on adjacent segments while keeping timings unchanged."""
    updated = list(segments)

    for i in range(len(updated) - 1):
        left = updated[i]
        right = updated[i + 1]

        for rule in DEFAULT_RULES:
            left_tokens = _tail_tokens(left.text, len(rule.tokens) - 1)
            right_tokens = _head_tokens(right.text, len(rule.tokens) - 1)

            if not left_tokens or not right_tokens:
                continue

            combined = left_tokens + right_tokens
            if _tokens_match(combined, rule.tokens):
                left_text = _replace_tail(left.text, len(left_tokens), " ".join(rule.tokens[:-1]))
                right_text = _replace_head(right.text, len(right_tokens), rule.tokens[-1])
                updated[i] = Segment(left.start_ms, left.end_ms, left_text)
                updated[i + 1] = Segment(right.start_ms, right.end_ms, right_text)

        # Specific fix: if model expanded "uv" into "Uvicorn" when followed by sync/run/add
        updated[i], updated[i + 1] = _fix_uvicn_misexpand(updated[i], updated[i + 1])

    return updated


def _normalize(text: str) -> list[str]:
    return [t.lower() for t in re.findall(r"[\w\.-]+", text)]


def _tail_tokens(text: str, count: int) -> list[str]:
    tokens = _normalize(text)
    if len(tokens) < count:
        return []
    return tokens[-count:]


def _head_tokens(text: str, count: int) -> list[str]:
    tokens = _normalize(text)
    if len(tokens) < count:
        return []
    return tokens[:count]


def _tokens_match(window: list[str], target: tuple[str, ...]) -> bool:
    if len(window) != len(target):
        return False
    return [t.lower() for t in window] == [t.lower() for t in target]


def _replace_tail(text: str, token_count: int, replacement: str) -> str:
    parts = re.split(r"(\s+)", text)
    tokens = [p for p in parts if p.strip()]
    if len(tokens) < token_count:
        return text
    # Replace last token_count tokens
    replaced_tokens = tokens[:-token_count] + [replacement]
    return " ".join(replaced_tokens)


def _replace_head(text: str, token_count: int, replacement: str) -> str:
    parts = re.split(r"(\s+)", text)
    tokens = [p for p in parts if p.strip()]
    if len(tokens) < token_count:
        return text
    replaced_tokens = [replacement] + tokens[token_count:]
    return " ".join(replaced_tokens)


def _fix_uvicn_misexpand(left: Segment, right: Segment) -> tuple[Segment, Segment]:
    # If left ends with "uvicorn" or "uvicorn," and right begins with sync/run/add,
    # replace uvicorn with uv.
    right_head = _head_tokens(right.text, 1)
    if not right_head:
        return left, right
    if right_head[0] not in {"sync", "run", "add"}:
        return left, right

    if re.search(r"\buvicorn\b", left.text, flags=re.IGNORECASE):
        fixed_left = re.sub(r"\buvicorn\b", "uv", left.text, flags=re.IGNORECASE)
        return Segment(left.start_ms, left.end_ms, fixed_left), right

    return left, right
