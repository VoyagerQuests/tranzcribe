from pathlib import Path

from transcribe_enhance.infrastructure.itt_parser import parse_itt
from transcribe_enhance.infrastructure.itt_writer import write_itt

def test_patch_only_updates_target_segment(tmp_path: Path) -> None:
    source = Path(__file__).parent / "fixtures" / "sample.itt"
    original_text = source.read_text(encoding="utf-8")
    parsed = parse_itt(source)

    updated_segments = list(parsed.segments)
    updated_segments[0] = type(parsed.segments[0])(
        start_ms=parsed.segments[0].start_ms,
        end_ms=parsed.segments[0].end_ms + 500,
        text="Alpha UPDATED_TEXT_ONE",
    )

    output = tmp_path / "patched.itt"
    write_itt(output, original_text, parsed, updated_segments)

    patched_text = output.read_text(encoding="utf-8")

    assert "Alpha UNIQUE_TEXT_ONE" not in patched_text
    assert "Alpha UPDATED_TEXT_ONE" in patched_text
    assert "end=\"00:00:02:15\"" not in patched_text
    assert "end=\"00:00:03:00\"" in patched_text

    # Revert the changes and compare to ensure only the intended edits happened.
    reverted = patched_text.replace(
        "Alpha UPDATED_TEXT_ONE", "Alpha UNIQUE_TEXT_ONE"
    ).replace("end=\"00:00:03:00\"", "end=\"00:00:02:15\"")
    assert reverted == original_text
