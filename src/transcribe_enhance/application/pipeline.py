"""Application pipeline orchestration."""

from pathlib import Path

from transcribe_enhance.infrastructure.ai_openai import transcribe_audio_openai
from transcribe_enhance.infrastructure.itt_writer import write_itt_from_segments


def run_pipeline(audio_path: Path, output_path: Path) -> None:
    segments = transcribe_audio_openai(audio_path)
    write_itt_from_segments(output_path, segments)
