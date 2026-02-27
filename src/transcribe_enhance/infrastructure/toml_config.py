"""Load instructions from a TOML file."""


from pathlib import Path
import tomllib

from transcribe_enhance.domain.models import AIConfig, Context, Instructions, OutputRules


DEFAULT_OUTPUT_RULES = OutputRules(
    max_chars_per_line=42,
    max_lines_per_caption=2,
    max_reading_speed_cps=17,
    min_duration_ms=700,
    max_duration_ms=6000,
    line_break_style="punctuation",
    casing="sentence",
    punctuation="standard",
    profanity_policy="mask",
)


DEFAULT_AI = AIConfig(provider="openai", model="gpt-4.1", temperature=0.2)


def _load_details(details_path: Path) -> str:
    if not details_path.exists():
        raise FileNotFoundError(f"Details file not found: {details_path}")
    return details_path.read_text(encoding="utf-8").strip()


def load_instructions(path: Path) -> Instructions:
    data = tomllib.loads(path.read_text(encoding="utf-8"))

    context_raw = data.get("context", {})
    output_raw = data.get("output_rules", {})
    ai_raw = data.get("ai", {})

    details = ""
    details_path_raw = context_raw.get("details_path")
    if details_path_raw:
        details_path = (path.parent / details_path_raw).resolve()
        details = _load_details(details_path)

    context = Context(
        purpose=context_raw.get("purpose", ""),
        audience=context_raw.get("audience", ""),
        tone=context_raw.get("tone", ""),
        details=details,
    )

    output_rules = OutputRules(
        max_chars_per_line=output_raw.get(
            "max_chars_per_line", DEFAULT_OUTPUT_RULES.max_chars_per_line
        ),
        max_lines_per_caption=output_raw.get(
            "max_lines_per_caption", DEFAULT_OUTPUT_RULES.max_lines_per_caption
        ),
        max_reading_speed_cps=output_raw.get(
            "max_reading_speed_cps", DEFAULT_OUTPUT_RULES.max_reading_speed_cps
        ),
        min_duration_ms=output_raw.get(
            "min_duration_ms", DEFAULT_OUTPUT_RULES.min_duration_ms
        ),
        max_duration_ms=output_raw.get(
            "max_duration_ms", DEFAULT_OUTPUT_RULES.max_duration_ms
        ),
        line_break_style=output_raw.get(
            "line_break_style", DEFAULT_OUTPUT_RULES.line_break_style
        ),
        casing=output_raw.get("casing", DEFAULT_OUTPUT_RULES.casing),
        punctuation=output_raw.get(
            "punctuation", DEFAULT_OUTPUT_RULES.punctuation
        ),
        profanity_policy=output_raw.get(
            "profanity_policy", DEFAULT_OUTPUT_RULES.profanity_policy
        ),
    )

    ai = AIConfig(
        provider=ai_raw.get("provider", DEFAULT_AI.provider),
        model=ai_raw.get("model", DEFAULT_AI.model),
        temperature=ai_raw.get("temperature", DEFAULT_AI.temperature),
    )

    return Instructions(context=context, output_rules=output_rules, ai=ai)
