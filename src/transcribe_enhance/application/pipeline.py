"""Application pipeline orchestration."""


from pathlib import Path

from transcribe_enhance.domain.models import Instructions
from transcribe_enhance.infrastructure.ai_openai import enhance_segments_openai
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
    enable_ai: bool,
) -> None:
    # TODO: validate inputs, run rules, call AI providers
    _ = audio_path
    _ = allow_timing_adjust

    parsed = parse_itt(itt_path)
    original_text = itt_path.read_text(encoding="utf-8")

    segments = parsed.segments
    if enable_ai:
        if instructions.ai.provider == "openai":
            segments = enhance_segments_openai(segments, instructions)
        else:
            raise ValueError(f"Unsupported AI provider: {instructions.ai.provider}")

    if _segments_unchanged(parsed, segments):
        output_path.write_text(original_text, encoding="utf-8")
        return

    write_itt(output_path, original_text, parsed, segments)
