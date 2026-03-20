<!-- markdownlint-disable MD012 MD025 -->
# Tranzcribe

Tranzcribe is a Python CLI tool that transcribes audio into iTT (TTML) captions using OpenAI Whisper.

## Requirements
- Python 3.14
- `uv`
- `OPENAI_API_KEY` in your environment

## Run From Project Root

```bash
uv run tranzcribe \
  --audioin "demo_files/Q1E3a.m4a" \
  --ittout "demo_files/output.itt"
```

## Defaults

If `--audioin` is omitted, Tranzcribe searches for `audioin.*` in the current directory in this order:
`.wav`, `.mp3`, `.m4a`, `.mp4`, `.mpeg`, `.mpga`, `.webm`.
If `--ittout` is omitted, the default is `ittout.itt` in the current directory.
If `settings.toml` is omitted, defaults are `characters_per_segment=20` and `compression_format="m4a"`.

## Settings

Create a `settings.toml` file to control segmentation and compression:

```toml
characters_per_segment = 20
compression_format = "m4a"
```

## Compression

If your audio file is larger than 25 MB, use `--compress` to create a smaller file:

```bash
uv run tranzcribe --audioin "/path/to/audio.wav" --compress
```

This writes a new file named `<original>_compressed.m4a` and uses it for transcription.

## Notes
- `--audioin` supports `.mp3`, `.mp4`, `.mpeg`, `.mpga`, `.m4a`, `.wav`, and `.webm`.
- `--ittout` must end with `.itt`.
- Segments are split to a default maximum of 20 characters using word-level timings with punctuation merged from segment text.
