from pathlib import Path

from psynetsk_tools.pr_preview_redirect import (
    redirect_destination,
    write_redirect_preview,
)


def write(path: Path, text: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_redirect_destination_preserves_dashboard_paths() -> None:
    base_url = "https://example.github.io/PsyNetSkills/"

    assert redirect_destination(base_url, Path("index.html")) == base_url
    assert (
        redirect_destination(base_url, Path("challenges/example/index.html"))
        == "https://example.github.io/PsyNetSkills/challenges/example/"
    )
    assert (
        redirect_destination(base_url, Path("workflow/index.html"))
        == "https://example.github.io/PsyNetSkills/workflow/"
    )


def test_write_redirect_preview_replaces_html_pages_and_removes_assets(
    tmp_path: Path,
) -> None:
    target = tmp_path / "pr-preview/pr-12"
    write(target / "index.html", "<h1>Preview</h1>")
    write(target / "challenges/example/index.html", "<h1>Challenge</h1>")
    write(target / "workflow/index.html", "<h1>Workflow</h1>")
    write(target / "css/site.css", "body {}")

    write_redirect_preview(target, "https://example.github.io/PsyNetSkills")

    assert not (target / "css/site.css").exists()
    assert (
        'url=https://example.github.io/PsyNetSkills/"'
        in (target / "index.html").read_text(encoding="utf-8")
    )
    assert (
        'url=https://example.github.io/PsyNetSkills/challenges/example/"'
        in (target / "challenges/example/index.html").read_text(encoding="utf-8")
    )
    assert (
        'url=https://example.github.io/PsyNetSkills/workflow/"'
        in (target / "workflow/index.html").read_text(encoding="utf-8")
    )


def test_write_redirect_preview_creates_root_redirect_without_existing_preview(
    tmp_path: Path,
) -> None:
    target = tmp_path / "pr-preview/pr-12"

    write_redirect_preview(target, "https://example.github.io/PsyNetSkills/")

    assert (
        'url=https://example.github.io/PsyNetSkills/"'
        in (target / "index.html").read_text(encoding="utf-8")
    )
