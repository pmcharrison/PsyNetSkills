import json

from psynetsk_tools.review_html import render_evidence_section
from psynetsk_tools.review_model import CompletenessItem, ReviewFile, classify_review_evidence


def file(path: str, content: str | None = "") -> ReviewFile:
    return ReviewFile(
        path=path,
        url=f"artifacts/{path}",
        content=content,
        size_bytes=len(content or ""),
        kind=path.rsplit(".", 1)[-1] if "." in path else "file",
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
