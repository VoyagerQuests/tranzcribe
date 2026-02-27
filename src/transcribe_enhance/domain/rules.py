"""Rules and utilities to enforce subtitle constraints."""


from transcribe_enhance.domain.models import OutputRules, Segment


def apply_output_rules(segments: list[Segment], rules: OutputRules) -> list[Segment]:
    # TODO: implement line breaking, duration constraints, and reading speed checks.
    _ = rules
    return segments
