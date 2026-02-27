"""CLI entrypoint for transcribe-enhance."""


import argparse
import logging
from pathlib import Path

from transcribe_enhance.application.pipeline import run_pipeline
from transcribe_enhance.domain.models import Context, Instructions
from transcribe_enhance.infrastructure.toml_config import load_instructions


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="transcribe-enhance",
        description="Enhance an existing iTT transcript using AI and formatting rules.",
    )
    parser.add_argument("--audio", type=Path, required=True, help="Path to input audio file")
    parser.add_argument("--itt", type=Path, required=True, help="Path to input .itt file")
    parser.add_argument(
        "--instructions",
        type=Path,
        required=True,
        help="Path to instructions TOML file",
    )
    parser.add_argument("--out", type=Path, required=True, help="Path to output .itt file")
    parser.add_argument(
        "--details",
        type=Path,
        help="Optional path to extra context details (Markdown or text)",
    )
    parser.add_argument(
        "--no-timing-adjust",
        action="store_true",
        help="Disallow timing adjustments (use original timestamps)",
    )
    parser.add_argument(
        "--enable-ai",
        action="store_true",
        help="Enable AI enhancement (requires provider configuration and API key)",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    config = load_instructions(args.instructions)
    if args.details:
        details_text = args.details.read_text(encoding="utf-8").strip()
        config = Instructions(
            context=Context(
                purpose=config.context.purpose,
                audience=config.context.audience,
                tone=config.context.tone,
                details=details_text,
            ),
            output_rules=config.output_rules,
            ai=config.ai,
        )
    run_pipeline(
        audio_path=args.audio,
        itt_path=args.itt,
        instructions=config,
        output_path=args.out,
        allow_timing_adjust=not args.no_timing_adjust,
        enable_ai=args.enable_ai,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
