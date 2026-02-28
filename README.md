<!-- markdownlint-disable MD012 MD025 -->
# Tranzcribe

Transcribe-enhance is a Python CLI tool that improves existing iTT (TTML) subtitle files using AI.
It preserves the original iTT formatting and metadata while updating only the caption text and (optionally) timing.

## What It Does
- Reads an existing `.itt` file with timings.
- Uses AI to improve transcript accuracy, grammar, and clarity.
- Writes a new `.itt` file **without reformatting** the original XML.
- Produces a `*.changes.txt` file showing only the changes.

## Requirements
- Python 3.14
- `uv`
- `OPENAI_API_KEY` in your environment (only when `--enable-ai` is used)

## Run From Project Root

From the project root, run:

```bash
uv run transcribe-enhance \
  --audio demo_files/VoiceToPremier.m4a \
  --itt "demo_files/Captions Almost Done_iTT_English.itt" \
  --instructions demo_files/instructions.toml \
  --out demo_files/output.itt \
  --enable-ai
```

This will also write:
```
demo_files/output.changes.txt
```

## Instructions File (TOML)

Example:

```toml
[context]
purpose = "Walkthrough of Quest1 Episode 2 implementation"
audience = "Developers"
tone = "clear, instructional"
details_path = "details.md"

[output_rules]
max_chars_per_line = 42
max_lines_per_caption = 2
max_reading_speed_cps = 17
min_duration_ms = 700
max_duration_ms = 6000
line_break_style = "punctuation"
casing = "sentence"
punctuation = "standard"
profanity_policy = "mask"

[ai]
provider = "openai"
model = "gpt-4.1"
temperature = 0.2
```

## Notes
- The audio file path is accepted but not yet used in processing.
- If AI is disabled (omit `--enable-ai`), the output `.itt` will match the input exactly.
