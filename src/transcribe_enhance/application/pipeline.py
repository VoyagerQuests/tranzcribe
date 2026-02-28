"""Application pipeline orchestration."""


from pathlib import Path

from transcribe_enhance.domain.models import Instructions
from transcribe_enhance.domain.command_glossary import enforce_command_glossary
from transcribe_enhance.infrastructure.ai_openai import enhance_segments_openai
from transcribe_enhance.infrastructure.itt_parser import parse_itt
from transcribe_enhance.infrastructure.itt_writer import write_itt


def _format_timecode_ms(ms: int) -> str:
    total_seconds, millis = divmod(ms, 1000)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{millis:03d}"


def _write_changes(
    output_path: Path,
    parsed,
    segments,
) -> None:
    changes: list[dict[str, str]] = []
    for idx, segment in enumerate(segments):
        original_text = parsed.original_texts[idx]
        original_begin, original_end = parsed.original_timecodes[idx]
        original_segment = parsed.segments[idx]

        text_changed = segment.text != original_text
        time_changed = (
            segment.start_ms != original_segment.start_ms
            or segment.end_ms != original_segment.end_ms
        )

        if not text_changed and not time_changed:
            continue

        change: dict[str, str] = {
            "index": str(idx),
            "original_time": f"{original_begin} --> {original_end}",
            "new_time": (
                f"{_format_timecode_ms(segment.start_ms)} --> "
                f"{_format_timecode_ms(segment.end_ms)}"
            ),
            "before": original_text,
            "after": segment.text,
        }
        changes.append(change)

    changes_path = output_path.with_suffix(".changes.txt")
    if not changes:
        changes_path.write_text("", encoding="utf-8")
        return

    lines: list[str] = []
    for idx, change in enumerate(changes, start=1):
        lines.append(f"Change {idx}")
        lines.append(f"Index: {change['index']}")
        lines.append(f"Original Time: {change['original_time']}")
        lines.append(f"New Time: {change['new_time']}")
        lines.append(f"Before: {change['before']}")
        lines.append(f"After: {change['after']}")
        lines.append("")

    changes_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


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

    segments = enforce_command_glossary(segments)

    if _segments_unchanged(parsed, segments):
        output_path.write_text(original_text, encoding="utf-8")
        _write_changes(output_path, parsed, segments)
        return

    write_itt(output_path, original_text, parsed, segments)
    _write_changes(output_path, parsed, segments)
