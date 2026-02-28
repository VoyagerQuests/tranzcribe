from transcribe_enhance.domain.command_glossary import enforce_command_glossary
from transcribe_enhance.domain.models import Segment


def test_uv_sync_split_across_segments_is_fixed() -> None:
    segments = [
        Segment(0, 1000, "Use uv"),
        Segment(1000, 2000, "sync to install dependencies."),
    ]

    updated = enforce_command_glossary(segments)

    assert updated[0].text == "Use uv"
    assert updated[1].text == "sync to install dependencies."


def test_uvicn_misexpand_is_fixed() -> None:
    segments = [
        Segment(0, 1000, "Use Uvicorn"),
        Segment(1000, 2000, "sync to install dependencies."),
    ]

    updated = enforce_command_glossary(segments)

    assert updated[0].text == "Use uv"
    assert updated[1].text == "sync to install dependencies."
