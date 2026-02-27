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
    frame_rate: float | None
    original_timecodes: list[tuple[str, str]]
    original_texts: list[str]


def _parse_timecode(timecode: str, frame_rate: float | None) -> int:
    # Expected formats:
    # - HH:MM:SS.mmm (milliseconds optional)
    # - HH:MM:SS:FF (frames, requires frame_rate)
    if timecode.endswith("s"):
        timecode = timecode[:-1]
    parts = timecode.split(":")
    if len(parts) == 3:
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

    if len(parts) == 4:
        if frame_rate is None or frame_rate <= 0:
            raise ValueError(
                f"Frame-based timecode requires a valid frame_rate: {timecode}"
            )
        hours, minutes, seconds, frames = parts
        base_ms = (
            int(hours) * 3600 * 1000
            + int(minutes) * 60 * 1000
            + int(seconds) * 1000
        )
        frame_ms = int(round((int(frames) / frame_rate) * 1000))
        return base_ms + frame_ms

    raise ValueError(f"Unsupported timecode format: {timecode}")


def _parse_frame_rate(root: ET.Element) -> float | None:
    # TTML/iTT may store frame rate with namespace prefixes.
    def _get_attr(name: str) -> str | None:
        if name in root.attrib:
            return root.attrib[name]
        for attr_name, value in root.attrib.items():
            if attr_name.endswith(name):
                return value
        return None

    frame_rate_raw = _get_attr("frameRate")
    if not frame_rate_raw:
        return None

    try:
        frame_rate = float(frame_rate_raw)
    except ValueError:
        return None

    multiplier_raw = _get_attr("frameRateMultiplier")
    if multiplier_raw:
        parts = multiplier_raw.split()
        if len(parts) == 2:
            try:
                num = float(parts[0])
                den = float(parts[1])
                if den != 0:
                    frame_rate *= num / den
            except ValueError:
                pass

    return frame_rate


def parse_itt(path: Path) -> ParsedItt:
    namespaces: dict[str, str] = {}
    for event, data in ET.iterparse(path, events=("start-ns",)):
        prefix, uri = data
        if prefix in namespaces:
            continue
        namespaces[prefix] = uri

    tree = ET.parse(path)
    root = tree.getroot()

    frame_rate = _parse_frame_rate(root)
    segments: list[Segment] = []
    p_elements: list[ET.Element] = []
    original_timecodes: list[tuple[str, str]] = []
    original_texts: list[str] = []
    for elem in root.iter():
        if elem.tag.endswith("p"):
            begin = elem.attrib.get("begin")
            end = elem.attrib.get("end")
            if not begin or not end:
                continue
            text = "".join(elem.itertext()).strip()
            segments.append(
                Segment(
                    start_ms=_parse_timecode(begin, frame_rate),
                    end_ms=_parse_timecode(end, frame_rate),
                    text=text,
                )
            )
            p_elements.append(elem)
            original_timecodes.append((begin, end))
            original_texts.append(text)

    return ParsedItt(
        tree=tree,
        root=root,
        segments=segments,
        p_elements=p_elements,
        namespaces=namespaces,
        frame_rate=frame_rate,
        original_timecodes=original_timecodes,
        original_texts=original_texts,
    )
