"""Example-only PsyNet experiment entry point.

A real attempt would replace this placeholder with a runnable PsyNet
experiment implementation. This file is present so the example artifact
matches the documented experiment-attempt schema.
"""

STIMULUS_SPACE = [
    {"tempo": "slow", "brightness": "dark"},
    {"tempo": "fast", "brightness": "bright"},
]


def describe_example() -> str:
    """Return a short description of the illustrative experiment."""
    return "Adaptive musical preference experiment placeholder"
