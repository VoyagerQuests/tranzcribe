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

    for elem, segment in zip(parsed.p_elements, segments, strict=True):
        existing_attrib = dict(elem.attrib)

        # Replace text content while preserving element attributes.
        # Existing child elements (e.g., <span>) are removed for now.
        elem.clear()
        elem.attrib.update(existing_attrib)
        elem.attrib["begin"] = _format_timecode(segment.start_ms)
        elem.attrib["end"] = _format_timecode(segment.end_ms)
        elem.text = segment.text

    parsed.tree.write(path, encoding="utf-8", xml_declaration=True)
