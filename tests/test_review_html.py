import json

from psynetsk_tools.review_html import render_evidence_section, render_markdown_document
from psynetsk_tools.review_model import CompletenessItem, ReviewFile, classify_review_evidence


def file(path: str, content: str | None = "") -> ReviewFile:
    return ReviewFile(
        path=path,
        url=f"artifacts/{path}",
        content=content,
        size_bytes=len(content or ""),
        kind=path.rsplit(".", 1)[-1] if "." in path else "file",
    )


def unpublished_file(path: str) -> ReviewFile:
    return ReviewFile(
        path=path,
        url="",
        content=None,
        size_bytes=10,
        kind=path.rsplit(".", 1)[-1] if "." in path else "file",
        published=False,
        publication_note="Excluded from publication.",
    )


def test_render_evidence_section_uses_shared_dashboard_markup() -> None:
    view = classify_review_evidence(
        [
            file("participant.mp4", None),
            file("screenshots/01-intro.png", None),
            file(
                "screenshots/manifest.json",
                json.dumps({"captions": {"screenshots/01-intro.png": "Intro <screen>"}}),
            ),
            file(
                "performance.json",
                json.dumps(
                    {
                        "options": {
                            "n_bots_sweep": [2, 4],
                            "duration_minutes": 1.5,
                            "stagger_interval_s": 0.2,
                            "time_factor": 2,
                        },
                        "results": [
                            {
                                "n_bots": 4,
                                "total_bots_started": 5,
                                "bots_succeeded": 4,
                                "total_requests": 12,
                                "median_response_time": 0.1234,
                                "request_errors": 1,
                                "bot_errors": 2,
                            },
                        ],
                    }
                ),
            ),
            file("monitor.html", "<html></html>"),
            file("data.zip", None),
            file("simulated_data.zip", None),
            file(
                "analyses/analysis.ipynb",
                json.dumps(
                    {
                        "cells": [
                            {"cell_type": "markdown", "source": ["# Analysis\n\nReady."]},
                            {
                                "cell_type": "code",
                                "source": ["print('ok')"],
                                "outputs": [{"text": ["ok\n"]}],
                            },
                        ],
                    }
                ),
            ),
        ]
    )

    html = render_evidence_section(
        view,
        extra_completeness=[CompletenessItem("plan", "PLAN.md", True, "present")],
        include_heading=False,
        section_id=None,
        url_transform=lambda url: f"/{url}",
    )

    assert '<section>' in html
    assert 'src="/artifacts/participant.mp4"' in html
    assert "data-screenshot-gallery" in html
    assert "Intro &lt;screen&gt;" in html
    assert "Download simulated data" in html
    assert 'id="analysis-notebook"' in html
    assert "<h1>Analysis</h1>" in html
    assert "<td>0.123</td>" in html
    assert "<td>3</td>" in html
    assert "PLAN.md <span>present</span>" in html


def test_render_evidence_section_marks_unpublished_actions_without_empty_links() -> None:
    view = classify_review_evidence(
        [
            unpublished_file("simulated_data.zip"),
            unpublished_file("analyses/summary.html"),
        ]
    )

    html = render_evidence_section(view, include_heading=False, section_id=None)

    assert "Simulated data export not published" in html
    assert "Analysis summary not published" in html
    assert 'href=""' not in html


def test_render_markdown_document_renders_safe_report_markup() -> None:
    html = render_markdown_document(
        "# Report\n\n"
        "Experiment **works** with `psynet test local`.\n\n"
        "- Evidence captured\n"
        "- [Preview](https://example.test/review)\n\n"
        "```bash\npsynet-review-bundle validate\n```\n\n"
        "<script>alert('x')</script>\n"
    )

    assert "<h1>Report</h1>" in html
    assert "<strong>works</strong>" in html
    assert "<code>psynet test local</code>" in html
    assert "<ul><li>Evidence captured</li>" in html
    assert '<a href="https://example.test/review">Preview</a>' in html
    assert "psynet-review-bundle validate" in html
    assert "<script>" not in html
    assert "&lt;script&gt;alert(&#x27;x&#x27;)&lt;/script&gt;" in html


def test_render_evidence_section_renders_safe_notebook_rich_outputs() -> None:
    view = classify_review_evidence(
        [
            file(
                "analyses/analysis.ipynb",
                json.dumps(
                    {
                        "cells": [
                            {
                                "cell_type": "markdown",
                                "source": ["## Results\n\n- passed"],
                            },
                            {
                                "cell_type": "code",
                                "source": ["display_table()"],
                                "outputs": [
                                    {
                                        "output_type": "execute_result",
                                        "data": {
                                            "text/html": (
                                                "<table><tr><th>n</th></tr>"
                                                "<tr><td onclick=\"bad()\">4</td></tr></table>"
                                                "<script>bad()</script>"
                                            ),
                                        },
                                    },
                                    {
                                        "output_type": "display_data",
                                        "data": {
                                            "image/svg+xml": (
                                                '<svg viewBox="0 0 10 10" onload="bad()">'
                                                '<circle cx="5" cy="5" r="4" />'
                                                "<script>bad()</script></svg>"
                                            ),
                                        },
                                    },
                                    {
                                        "output_type": "execute_result",
                                        "data": {"text/plain": "plain result"},
                                    },
                                ],
                            },
                        ],
                    }
                ),
            ),
        ]
    )

    html = render_evidence_section(view, include_heading=False, section_id=None)

    assert "<h2>Results</h2>" in html
    assert "<ul><li>passed</li></ul>" in html
    assert '<div class="notebook-html">' in html
    assert "<table><tr><th>n</th></tr><tr><td>4</td></tr></table>" in html
    assert 'onclick="bad()"' not in html
    assert '<div class="notebook-svg">' in html
    assert '<svg viewBox="0 0 10 10"><circle cx="5" cy="5" r="4"></circle></svg>' in html
    assert 'onload="bad()"' not in html
    assert "<script>" not in html
    assert "plain result" in html
