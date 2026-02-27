"""Serialize domain segments into iTT (TTML)."""


from pathlib import Path
from xml.etree import ElementTree as ET

from transcribe_enhance.domain.models import Segment
from transcribe_enhance.infrastructure.itt_parser import ParsedItt


def _format_timecode(ms: int) -> str:
    total_seconds, millis = divmod(ms, 1000)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{millis:03d}"

def _format_timecode_like(original: str, ms: int, frame_rate: float | None) -> str:
    if original.endswith("s"):
        original = original[:-1]
    parts = original.split(":")
    if len(parts) == 4:
        if frame_rate is None or frame_rate <= 0:
            return _format_timecode(ms)
        total_seconds, millis = divmod(ms, 1000)
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        frames = int(round((millis / 1000) * frame_rate))
        frames = max(0, min(frames, int(frame_rate) - 1))
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}:{frames:02d}"
    return _format_timecode(ms)


def _register_namespaces(namespaces: dict[str, str]) -> None:
    for prefix, uri in namespaces.items():
        ET.register_namespace(prefix, uri)


def write_itt(path: Path, parsed: ParsedItt, segments: list[Segment]) -> None:
    if len(parsed.p_elements) != len(segments):
        raise ValueError(
            "Segment count does not match original iTT structure. "
            "Refusing to write to avoid corrupting the document."
        )

    _register_namespaces(parsed.namespaces)

    for idx, (elem, segment) in enumerate(zip(parsed.p_elements, segments, strict=True)):
        original_begin, original_end = parsed.original_timecodes[idx]
        original_text = parsed.original_texts[idx]

        begin = _format_timecode_like(original_begin, segment.start_ms, parsed.frame_rate)
        end = _format_timecode_like(original_end, segment.end_ms, parsed.frame_rate)

        # If nothing changed, preserve original element exactly.
        if segment.text == original_text and begin == original_begin and end == original_end:
            continue

        existing_attrib = dict(elem.attrib)
        existing_children = list(elem)

        # Replace text content while preserving element attributes.
        elem.clear()
        elem.attrib.update(existing_attrib)
        elem.attrib["begin"] = begin
        elem.attrib["end"] = end
        elem.text = segment.text

        # Preserve child elements only if they were originally present and text unchanged.
        # If text changed, we drop children to avoid mismatched spans.
        if segment.text == original_text and existing_children:
            elem[:] = existing_children

    parsed.tree.write(path, encoding="utf-8", xml_declaration=True)
