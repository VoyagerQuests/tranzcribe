"""Serialize domain segments into iTT (TTML)."""

from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree as ET

from transcribe_enhance.domain.models import Segment


def _format_timecode(ms: int) -> str:
    total_seconds, millis = divmod(ms, 1000)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{millis:03d}"


def write_itt(path: Path, segments: list[Segment]) -> None:
    tt = ET.Element("tt", {"xmlns": "http://www.w3.org/ns/ttml"})
    body = ET.SubElement(tt, "body")
    div = ET.SubElement(body, "div")

    for segment in segments:
        attrs = {
            "begin": _format_timecode(segment.start_ms),
            "end": _format_timecode(segment.end_ms),
        }
        p = ET.SubElement(div, "p", attrs)
        p.text = segment.text

    tree = ET.ElementTree(tt)
    tree.write(path, encoding="utf-8", xml_declaration=True)
