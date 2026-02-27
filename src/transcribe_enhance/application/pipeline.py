"""Application pipeline orchestration."""

from __future__ import annotations

from pathlib import Path

from transcribe_enhance.domain.models import Instructions
from transcribe_enhance.infrastructure.itt_parser import parse_itt
from transcribe_enhance.infrastructure.itt_writer import write_itt


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

    segments = parse_itt(itt_path)
    write_itt(output_path, segments)
