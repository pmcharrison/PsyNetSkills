import tomllib
from pathlib import Path


def test_giscus_uses_strict_pathname_matching() -> None:
    config = tomllib.loads(
        Path("dashboard/hugo.toml").read_text(encoding="utf-8"),
    )

    giscus = config["params"]["giscus"]

    assert giscus["mapping"] == "pathname"
    assert giscus["strict"] == "1"
