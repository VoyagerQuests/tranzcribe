"""Merge segment punctuation into word-level timings."""

import re

from transcribe_enhance.domain.models import Segment, Word


_WORD_RE = re.compile(r"[A-Za-z0-9]+(?:['’][A-Za-z0-9]+)*")
_TOKEN_RE = re.compile(r"[A-Za-z0-9]+(?:['’][A-Za-z0-9]+)*|\s+|[^A-Za-z0-9\s]")


def _tokenize(text: str) -> list[str]:
    """Split text into word, whitespace, and punctuation tokens."""
    return _TOKEN_RE.findall(text)


def _normalize_word(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9']", "", text).lower()


def _match_segment_words(
    segment: Segment,
    words: list[Word],
    word_idx: int,
) -> tuple[list[Word], int]:
    token_words = [
        token for token in _tokenize(segment.text) if _WORD_RE.fullmatch(token)
    ]
    if not token_words:
        return [], word_idx

    expected = [_normalize_word(token) for token in token_words]
    expected_count = len(expected)
    search_start = max(0, word_idx - 2)
    search_end = min(len(words), word_idx + expected_count + 6)

    for start in range(search_start, search_end):
        end = start + expected_count
        if end > len(words):
            break
        candidate = words[start:end]
        normalized = [_normalize_word(word.text) for word in candidate]
        if normalized == expected:
            return candidate, end

    seg_words: list[Word] = []
    current_idx = word_idx
    while current_idx < len(words):
        word = words[current_idx]
        if word.start_ms > segment.end_ms:
            break
        if word.end_ms > segment.start_ms:
            seg_words.append(word)
        current_idx += 1
    return seg_words, current_idx


def merge_punctuation(segments: list[Segment], words: list[Word]) -> list[Word]:
    """Attach punctuation from segment text to word-level tokens.

    The returned words preserve original timings but include punctuation from
    segment text, attached to the nearest word without splitting words.
    """
    if not words:
        return []

    punctuated: list[Word] = []
    word_idx = 0

    for seg_idx, segment in enumerate(segments):
        seg_words, word_idx = _match_segment_words(segment, words, word_idx)

        if not seg_words:
            continue

        tokens = _tokenize(segment.text)
        outputs: list[str] = []
        leading = ""
        seg_word_idx = 0

        def take_word(token: str) -> None:
            nonlocal leading, seg_word_idx
            if seg_word_idx >= len(seg_words):
                return
            current = token
            if leading:
                current = leading + current
                leading = ""
            outputs.append(current)
            seg_word_idx += 1

        for token in tokens:
            if _WORD_RE.fullmatch(token):
                take_word(token)
            elif token.isspace():
                if outputs:
                    outputs[-1] += token
                else:
                    leading += token
            else:
                if outputs:
                    outputs[-1] += token
                else:
                    leading += token

        if len(outputs) != len(seg_words):
            raise ValueError(
                "Token/word count mismatch for segment "
                f"{seg_idx}: tokens={len(outputs)} words={len(seg_words)}"
            )

        for word, punct in zip(seg_words, outputs, strict=True):
            punctuated.append(
                Word(
                    start_ms=word.start_ms,
                    end_ms=word.end_ms,
                    text=punct.strip(),
                )
            )

    return punctuated
