"""CLI entrypoint for tranzcribe."""

import argparse
import logging
from pathlib import Path
import subprocess
import tomllib

from transcribe_enhance.application.pipeline import run_pipeline


DEFAULT_OUTPUT = Path("ittout.itt")
DEFAULT_SETTINGS = Path("settings.toml")
SUPPORTED_AUDIO_EXTS = (".wav", ".mp3", ".m4a", ".mp4", ".mpeg", ".mpga", ".webm")
MAX_UPLOAD_BYTES = 25 * 1024 * 1024
DEFAULT_MAX_CHARS_PER_SEGMENT = 20
DEFAULT_COMPRESS_FORMAT = "m4a"


def _resolve_default_audio() -> Path:
    for ext in SUPPORTED_AUDIO_EXTS:
        candidate = Path(f"audioin{ext}")
        if candidate.exists():
            return candidate
    raise FileNotFoundError(
        "No default audio file found. Expected audioin.* with one of: "
        + ", ".join(SUPPORTED_AUDIO_EXTS)
    )


def _load_settings(path: Path) -> tuple[int, str]:
    max_chars = DEFAULT_MAX_CHARS_PER_SEGMENT
    compress_format = DEFAULT_COMPRESS_FORMAT
    if not path.exists():
        return max_chars, compress_format
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    raw_max = data.get("characters_per_segment")
    if isinstance(raw_max, int) and raw_max > 0:
        max_chars = raw_max
    raw_format = data.get("compression_format")
    if isinstance(raw_format, str) and raw_format:
        compress_format = raw_format.lower()
    return max_chars, compress_format


def _compress_audio(audio_path: Path) -> Path:
    output_path = audio_path.with_name(f"{audio_path.stem}_compressed.m4a")
    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(audio_path),
        "-ac",
        "1",
        "-ar",
        "16000",
        "-c:a",
        "aac",
        "-b:a",
        "64k",
        str(output_path),
    ]
    try:
        subprocess.run(
            command,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError as exc:
        err = exc.stderr.decode("utf-8", errors="ignore")
        raise RuntimeError(f"ffmpeg failed to compress {audio_path}: {err}") from exc
    return output_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tranzcribe",
        description="Transcribe audio to iTT using OpenAI Whisper.",
    )
    parser.add_argument(
        "--audioin",
        type=Path,
        default=None,
        help=(
            "Path to input audio file. If omitted, will search for audioin.* in "
            "the current directory using this priority: "
            + ", ".join(SUPPORTED_AUDIO_EXTS)
            + "."
        ),
    )
    parser.add_argument(
        "--ittout",
        type=Path,
        default=DEFAULT_OUTPUT,
        help='Path to output .itt file. Defaults to "ittout.itt" in the current directory.',
    )
    parser.add_argument(
        "--compress",
        action="store_true",
        help="Compress input audio to <original>_compressed.m4a before transcription.",
    )
    parser.add_argument(
        "--settings",
        type=Path,
        default=DEFAULT_SETTINGS,
        help='Path to settings TOML file. Defaults to "settings.toml" in the current directory.',
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    audio_path = args.audioin or _resolve_default_audio()

    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file not found: {args.audioin}")

    audio_ext = audio_path.suffix.lower()
    if audio_ext not in SUPPORTED_AUDIO_EXTS:
        raise ValueError(
            "--audioin must be one of: " + ", ".join(SUPPORTED_AUDIO_EXTS)
        )
    max_chars, compress_format = _load_settings(args.settings)
    logging.getLogger("transcribe_enhance.cli").info(
        "Settings: characters_per_segment=%s compression_format=%s",
        max_chars,
        compress_format,
    )

    if args.compress:
        _logger = logging.getLogger("transcribe_enhance.cli")
        _logger.info("Compressing audio with ffmpeg: %s", audio_path)
        if compress_format != "m4a":
            raise ValueError(
                f"Unsupported compression_format: {compress_format} (only m4a is supported)"
            )
        audio_path = _compress_audio(audio_path)
        _logger.info("Compressed audio written to: %s", audio_path)

    audio_size = audio_path.stat().st_size
    logging.getLogger("transcribe_enhance.cli").info(
        "Audio size: %.1f MB", audio_size / (1024 * 1024)
    )
    if audio_size > MAX_UPLOAD_BYTES:
        size_mb = audio_size / (1024 * 1024)
        max_mb = MAX_UPLOAD_BYTES / (1024 * 1024)
        raise ValueError(
            f"Audio file is too large ({size_mb:.1f} MB). "
            f"OpenAI transcription uploads must be <= {max_mb:.0f} MB. "
            "Please compress or split the audio (try --compress)."
        )

    if args.ittout.suffix.lower() != ".itt":
        raise ValueError("--ittout must point to a .itt file")

    run_pipeline(
        audio_path=audio_path,
        output_path=args.ittout,
        max_chars_per_segment=max_chars,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
