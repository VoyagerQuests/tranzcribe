# Architecture Overview

## System Flow

```mermaid
flowchart LR
  A["CLI (delivery/cli.py)"] --> B["Pipeline (application/pipeline.py)"]
  B --> C["Parse iTT (infrastructure/itt_parser.py)"]
  B --> D["AI Enhance (infrastructure/ai_openai.py)"]
  B --> E["Write iTT (infrastructure/itt_writer.py)"]
  C --> B
  D --> B
  E --> F["Output .itt file"]
```

## Components

### Delivery Layer
- `delivery/cli.py`
  - Parses CLI args (`--audio`, `--itt`, `--instructions`, `--out`, `--enable-ai`).
  - Loads instructions TOML.
  - Boots the pipeline.
  - Sets logging configuration.

### Application Layer
- `application/pipeline.py`
  - Orchestrates the workflow.
  - Parses `.itt` into segments.
  - Optionally calls AI to enhance text.
  - Writes output with the patcher to preserve formatting.
  - Copies the original file if unchanged.

### Domain Layer
- `domain/models.py`
  - Core data structures: `Segment`, `Instructions`, `OutputRules`, `Context`, `AIConfig`.

- `domain/rules.py`
  - Placeholder for formatting rules (line breaks, durations, etc.).

### Infrastructure Layer
- `infrastructure/itt_parser.py`
  - Parses iTT/TTML XML.
  - Extracts segments and preserves metadata.

- `infrastructure/itt_writer.py`
  - Patches the original file text.
  - Preserves formatting exactly (only changes `<p>` text and `begin/end`).

- `infrastructure/toml_config.py`
  - Reads TOML instructions.
  - Loads optional `details.md`.

- `infrastructure/ai_openai.py`
  - Calls OpenAI for transcript improvements.
  - Structured output schema + logging.
  - Unescapes HTML entities.
