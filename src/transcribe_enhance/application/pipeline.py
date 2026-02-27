"""Application pipeline orchestration."""


from pathlib import Path

from transcribe_enhance.domain.models import Instructions
from transcribe_enhance.infrastructure.itt_parser import parse_itt
from transcribe_enhance.infrastructure.itt_writer import write_itt


def _segments_unchanged(parsed, segments) -> bool:
    if len(parsed.segments) != len(segments):
        return False
    for idx, segment in enumerate(segments):
        original = parsed.segments[idx]
        original_text = parsed.original_texts[idx]
        if (
            segment.start_ms != original.start_ms
            or segment.end_ms != original.end_ms
            or segment.text != original_text
        ):
            return False
    return True


def run_pipeline(
    audio_path: Path,
    itt_path: Path,
    instructions: Instructions,
    output_path: Path,
    allow_timing_adjust: bool,
) -> None:
    # TODO: validate inputs, run rules, call AI providers
    _ = audio_path
    _ = allow_timing_adjust

    parsed = parse_itt(itt_path)

    if _segments_unchanged(parsed, parsed.segments):
        output_path.write_bytes(itt_path.read_bytes())
        return

    write_itt(output_path, parsed, parsed.segments)
