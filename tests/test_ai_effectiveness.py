from dataclasses import dataclass

import pytest


@dataclass(frozen=True)
class SampleCase:
    input_text: str
    expected_text: str


SAMPLE_CASES = [
    SampleCase(
        input_text="Gandalf the Wite was creatd.",
        expected_text="Gandalf the White was created.",
    ),
    SampleCase(
        input_text="The api return it back to use.",
        expected_text="The API returns it back to us.",
    ),
]


def _dummy_ai_correct(text: str) -> str:
    # Placeholder for an AI provider. This will be replaced with real calls later.
    return text


@pytest.mark.xfail(reason="AI provider not integrated yet")
def test_ai_correction_improves_transcript() -> None:
    improvements = 0
    for case in SAMPLE_CASES:
        corrected = _dummy_ai_correct(case.input_text)
        if corrected == case.expected_text:
            improvements += 1

    assert improvements == len(SAMPLE_CASES)
