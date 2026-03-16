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

## Notes
- `--audioin` supports `.mp3`, `.mp4`, `.mpeg`, `.mpga`, `.m4a`, `.wav`, and `.webm`.
- `--ittout` must end with `.itt`.
