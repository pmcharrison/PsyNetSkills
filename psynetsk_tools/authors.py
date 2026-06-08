"""Author registry helpers."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

AUTHORS_FILE = "authors.yaml"
GITHUB_ID_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,37}[a-z0-9])?$")


@dataclass(frozen=True)
class Author:
    """A public author record."""

    id: str
    name: str
    url: str
    email: str = ""
    affiliation: str = ""
    orcid: str = ""


def load_yaml_mapping(path: Path) -> tuple[dict[str, Any], list[str]]:
    """Load a YAML mapping from ``path``."""

    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        return {}, [f"{path}: invalid YAML: {exc}"]

    return validate_yaml_mapping(data, path)


def validate_yaml_mapping(data: Any, path: Path) -> tuple[dict[str, Any], list[str]]:
    """Validate that loaded YAML data is a mapping."""

    if data is None:
        return {}, []
    if not isinstance(data, dict):
        return {}, [f"{path}: YAML document must be a mapping"]

    mapping: dict[str, Any] = {}
    problems: list[str] = []
    for key, value in data.items():
        if not isinstance(key, str):
            problems.append(f"{path}: YAML keys must be strings")
            continue
        mapping[key] = value
    return mapping, problems


def read_author_registry(root: Path) -> tuple[dict[str, Author], list[str]]:
    """Read the central author registry."""

    authors_file = root / AUTHORS_FILE
    if not authors_file.exists():
        return {}, [f"{authors_file}: missing author registry"]

    data, problems = load_yaml_mapping(authors_file)
    authors: dict[str, Author] = {}
    for author_id, record in data.items():
        if not GITHUB_ID_RE.fullmatch(author_id):
            problems.append(
                f"{authors_file}: invalid GitHub author id {author_id!r}"
            )
            continue
        if not isinstance(record, dict):
            problems.append(f"{authors_file}: author {author_id!r} must be a mapping")
            continue

        name = record.get("name")
        if not isinstance(name, str) or not name.strip():
            problems.append(f"{authors_file}: author {author_id!r} missing name")
            continue

        url = normalize_optional_string(
            record.get("url"),
            authors_file,
            author_id,
            "url",
            problems,
        )
        affiliation = normalize_optional_string(
            record.get("affiliation", ""),
            authors_file,
            author_id,
            "affiliation",
            problems,
        )
        email = normalize_optional_string(
            record.get("email", ""),
            authors_file,
            author_id,
            "email",
            problems,
        )
        orcid = normalize_optional_string(
            record.get("orcid", ""),
            authors_file,
            author_id,
            "orcid",
            problems,
        )

        authors[author_id] = Author(
            id=author_id,
            name=name.strip(),
            url=(url or f"https://github.com/{author_id}").strip(),
            email=(email or "").strip(),
            affiliation=(affiliation or "").strip(),
            orcid=(orcid or "").strip(),
        )
    return authors, problems


def normalize_optional_string(
    value: Any,
    authors_file: Path,
    author_id: str,
    field_name: str,
    problems: list[str],
) -> str:
    """Return an optional author string field."""

    if value is None:
        return ""
    if isinstance(value, str):
        return value
    problems.append(
        f"{authors_file}: author {author_id!r} {field_name} must be a string"
    )
    return ""


def author_ids_from_value(value: Any) -> list[str]:
    """Return author ids from a structured metadata value."""

    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def resolve_authors(
    author_ids: list[str],
    registry: dict[str, Author],
) -> list[Author]:
    """Resolve author ids to public records."""

    return [registry[author_id] for author_id in author_ids if author_id in registry]
