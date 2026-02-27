from pathlib import Path

from transcribe_enhance.application.pipeline import run_pipeline
from transcribe_enhance.domain.models import AIConfig, Context, Instructions, OutputRules
from transcribe_enhance.infrastructure.itt_parser import parse_itt
from transcribe_enhance.infrastructure.itt_writer import write_itt


def _instructions() -> Instructions:
    return Instructions(
        context=Context(
            purpose="Test",
            audience="Test",
            tone="Neutral",
            details="",
        ),
        output_rules=OutputRules(
            max_chars_per_line=42,
            max_lines_per_caption=2,
            max_reading_speed_cps=17,
            min_duration_ms=700,
            max_duration_ms=6000,
            line_break_style="punctuation",
            casing="sentence",
            punctuation="standard",
            profanity_policy="mask",
        ),
        ai=AIConfig(provider="openai", model="gpt-4.1", temperature=0.2),
    )


def test_roundtrip_preserves_exact_bytes(tmp_path: Path) -> None:
    source = Path(__file__).parent / "fixtures" / "sample.itt"
    output = tmp_path / "output.itt"

    run_pipeline(
        audio_path=tmp_path / "audio.m4a",
        itt_path=source,
        instructions=_instructions(),
        output_path=output,
        allow_timing_adjust=True,
    )

    assert output.read_bytes() == source.read_bytes()


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
