"""CLI entrypoint for tranzcribe."""

import argparse
import logging
from pathlib import Path

from transcribe_enhance.application.pipeline import run_pipeline


DEFAULT_OUTPUT = Path("ittout.itt")
SUPPORTED_AUDIO_EXTS = (".wav", ".mp3", ".m4a", ".mp4", ".mpeg", ".mpga", ".webm")


def _resolve_default_audio() -> Path:
    for ext in SUPPORTED_AUDIO_EXTS:
        candidate = Path(f"audioin{ext}")
        if candidate.exists():
            return candidate
    raise FileNotFoundError(
        "No default audio file found. Expected audioin.* with one of: "
        + ", ".join(SUPPORTED_AUDIO_EXTS)
    )


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

    if args.ittout.suffix.lower() != ".itt":
        raise ValueError("--ittout must point to a .itt file")

    run_pipeline(
        audio_path=audio_path,
        output_path=args.ittout,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
