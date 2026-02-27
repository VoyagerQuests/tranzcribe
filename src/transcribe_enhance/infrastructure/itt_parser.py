"""Parse iTT (TTML) into domain segments while preserving metadata."""


from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree as ET

from transcribe_enhance.domain.models import Segment


@dataclass(frozen=True)
class ParsedItt:
    tree: ET.ElementTree
    root: ET.Element
    segments: list[Segment]
    p_elements: list[ET.Element]
    namespaces: dict[str, str]


def _parse_timecode(timecode: str) -> int:
    # Expected format: HH:MM:SS.mmm (milliseconds optional)
    if timecode.endswith("s"):
        timecode = timecode[:-1]
    parts = timecode.split(":")
    if len(parts) != 3:
        raise ValueError(f"Unsupported timecode format: {timecode}")
    hours, minutes, seconds = parts
    if "." in seconds:
        secs, millis = seconds.split(".")
        millis = millis.ljust(3, "0")[:3]
    else:
        secs, millis = seconds, "000"
    total_ms = (
        int(hours) * 3600 * 1000
        + int(minutes) * 60 * 1000
        + int(secs) * 1000
        + int(millis)
    )
    return total_ms


def parse_itt(path: Path) -> ParsedItt:
    namespaces: dict[str, str] = {}
    for event, data in ET.iterparse(path, events=("start-ns",)):
        prefix, uri = data
        if prefix in namespaces:
            continue
        namespaces[prefix] = uri

    tree = ET.parse(path)
    root = tree.getroot()

    segments: list[Segment] = []
    p_elements: list[ET.Element] = []
    for elem in root.iter():
        if elem.tag.endswith("p"):
            begin = elem.attrib.get("begin")
            end = elem.attrib.get("end")
            if not begin or not end:
                continue
            text = "".join(elem.itertext()).strip()
            segments.append(
                Segment(
                    start_ms=_parse_timecode(begin),
                    end_ms=_parse_timecode(end),
                    text=text,
                )
            )
            p_elements.append(elem)

    return ParsedItt(
        tree=tree,
        root=root,
        segments=segments,
        p_elements=p_elements,
        namespaces=namespaces,
    )
