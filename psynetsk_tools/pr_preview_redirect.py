"""Helpers for replacing merged pull request previews with redirects."""

from __future__ import annotations

import argparse
import html
import shutil
from pathlib import Path, PurePosixPath


def ensure_trailing_slash(url: str) -> str:
    """Return ``url`` with a trailing slash."""

    return url if url.endswith("/") else f"{url}/"


def redirect_destination(base_url: str, relative_html_path: Path) -> str:
    """Map a preview HTML path to the matching production dashboard URL.

    Parameters
    ----------
    base_url
        Production dashboard base URL.
    relative_html_path
        Path to the HTML file relative to the preview root.

    Returns
    -------
    str
        URL where the redirect page should send visitors.
    """

    path = PurePosixPath(relative_html_path.as_posix()).as_posix()
    if path == "index.html":
        suffix = ""
    elif path.endswith("/index.html"):
        suffix = path[: -len("index.html")]
    else:
        suffix = path

    return ensure_trailing_slash(base_url) + suffix


def redirect_html(destination_url: str) -> str:
    """Build a minimal static HTML redirect page."""

    escaped_url = html.escape(destination_url, quote=True)
    return (
        "<!doctype html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '  <meta charset="utf-8">\n'
        '  <meta name="robots" content="noindex">\n'
        f'  <link rel="canonical" href="{escaped_url}">\n'
        f'  <meta http-equiv="refresh" content="0; url={escaped_url}">\n'
        "  <title>Redirecting...</title>\n"
        "</head>\n"
        "<body>\n"
        f'  <p>Redirecting to <a href="{escaped_url}">{escaped_url}</a>.</p>\n'
        "</body>\n"
        "</html>\n"
    )


def write_redirect_preview(target: Path, base_url: str) -> None:
    """Replace a preview directory with redirect pages.

    Existing HTML paths are preserved so old deep links redirect to their
    matching production dashboard pages after a pull request is merged. If the
    preview directory is missing or contains no HTML, only the preview root gets
    a redirect.
    """

    html_paths = []
    if target.exists():
        html_paths = [
            path.relative_to(target)
            for path in sorted(target.rglob("*.html"))
            if path.is_file()
        ]
        shutil.rmtree(target)

    if not html_paths:
        html_paths = [Path("index.html")]

    for relative_html_path in html_paths:
        redirect_file = target / relative_html_path
        redirect_file.parent.mkdir(parents=True, exist_ok=True)
        destination_url = redirect_destination(base_url, relative_html_path)
        redirect_file.write_text(redirect_html(destination_url), encoding="utf-8")


def main() -> None:
    """Run the redirect writer from the command line."""

    parser = argparse.ArgumentParser(
        description="Replace a merged PR dashboard preview with redirect pages.",
    )
    parser.add_argument("target", type=Path)
    parser.add_argument("base_url")
    args = parser.parse_args()

    write_redirect_preview(args.target, args.base_url)


if __name__ == "__main__":
    main()
