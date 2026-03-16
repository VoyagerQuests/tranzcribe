"""Patch iTT (TTML) while preserving original formatting."""


from pathlib import Path
import re
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape

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


def _replace_attr(tag: str, name: str, value: str) -> str:
    pattern_double = rf'(\b{name}=")([^"]*)(")'
    pattern_single = rf"(\b{name}=')([^']*)(')"
    if re.search(pattern_double, tag):
        return re.sub(pattern_double, rf'\g<1>{value}\g<3>', tag, count=1)
    if re.search(pattern_single, tag):
        return re.sub(pattern_single, rf'\g<1>{value}\g<3>', tag, count=1)
    return tag


def _patch_itt_text(original_text: str, parsed: ParsedItt, segments: list[Segment]) -> str:
    pattern = re.compile(
        r'(?P<open><(?P<prefix>\w+:)?p\b[^>]*>)'
        r'(?P<inner>.*?)'
        r'(?P<close></(?(prefix)(?P=prefix))p>)',
        re.DOTALL,
    )

    matches = list(pattern.finditer(original_text))
    if len(matches) != len(segments):
        raise ValueError(
            "Segment count does not match original iTT structure. "
            "Refusing to patch to avoid corrupting the document."
        )

    parts: list[str] = []
    last_end = 0
    for idx, match in enumerate(matches):
        segment = segments[idx]
        original_begin, original_end = parsed.original_timecodes[idx]
        original_text_value = parsed.original_texts[idx]

        begin = _format_timecode_like(original_begin, segment.start_ms, parsed.frame_rate)
        end = _format_timecode_like(original_end, segment.end_ms, parsed.frame_rate)

        open_tag = match.group("open")
        inner = match.group("inner")
        close_tag = match.group("close")

        text_changed = segment.text != original_text_value
        time_changed = begin != original_begin or end != original_end

        if not text_changed and not time_changed:
            parts.append(original_text[last_end : match.end()])
            last_end = match.end()
            continue

        new_open = _replace_attr(open_tag, "begin", begin)
        new_open = _replace_attr(new_open, "end", end)

        if text_changed:
            new_inner = escape(segment.text)
        else:
            new_inner = inner

        parts.append(original_text[last_end : match.start()])
        parts.append(new_open)
        parts.append(new_inner)
        parts.append(close_tag)
        last_end = match.end()

    parts.append(original_text[last_end:])
    return "".join(parts)


def write_itt(
    path: Path,
    original_text: str,
    parsed: ParsedItt,
    segments: list[Segment],
) -> None:
    patched = _patch_itt_text(original_text, parsed, segments)
    path.write_text(patched, encoding="utf-8")


def write_itt_from_segments(
    path: Path,
    segments: list[Segment],
    language: str = "en",
) -> None:
    ttml_ns = "http://www.w3.org/ns/ttml"
    ttp_ns = "http://www.w3.org/ns/ttml#parameter"
    tts_ns = "http://www.w3.org/ns/ttml#styling"
    xml_ns = "http://www.w3.org/XML/1998/namespace"

    ET.register_namespace("", ttml_ns)
    ET.register_namespace("ttp", ttp_ns)
    ET.register_namespace("tts", tts_ns)

    root = ET.Element(
        f"{{{ttml_ns}}}tt",
        {
            f"{{{ttp_ns}}}timeBase": "media",
            f"{{{xml_ns}}}lang": language,
        },
    )
    head = ET.SubElement(root, f"{{{ttml_ns}}}head")
    styling = ET.SubElement(head, f"{{{ttml_ns}}}styling")
    ET.SubElement(
        styling,
        f"{{{ttml_ns}}}style",
        {
            f"{{{xml_ns}}}id": "normal",
            f"{{{tts_ns}}}color": "white",
            f"{{{tts_ns}}}fontFamily": "sansSerif",
            f"{{{tts_ns}}}fontSize": "100%",
        },
    )
    layout = ET.SubElement(head, f"{{{ttml_ns}}}layout")
    ET.SubElement(
        layout,
        f"{{{ttml_ns}}}region",
        {
            f"{{{xml_ns}}}id": "bottom",
            f"{{{tts_ns}}}displayAlign": "after",
            f"{{{tts_ns}}}extent": "100% 15%",
            f"{{{tts_ns}}}origin": "0% 85%",
            f"{{{tts_ns}}}writingMode": "lrtb",
        },
    )
    body = ET.SubElement(
        root,
        f"{{{ttml_ns}}}body",
        {
            f"{{{tts_ns}}}color": "white",
            "region": "bottom",
            "style": "normal",
        },
    )
    div = ET.SubElement(body, f"{{{ttml_ns}}}div")

    for segment in segments:
        p = ET.SubElement(
            div,
            f"{{{ttml_ns}}}p",
            {
                "begin": _format_timecode(segment.start_ms),
                "end": _format_timecode(segment.end_ms),
                "region": "bottom",
            },
        )
        p.text = segment.text

    tree = ET.ElementTree(root)
    try:
        ET.indent(tree, space="  ", level=0)
    except AttributeError:
        pass
    tree.write(path, encoding="utf-8", xml_declaration=True)
