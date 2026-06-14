"""Shared review evidence classification helpers."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Protocol


class ReviewFileLike(Protocol):
    """A file-like object used by review renderers."""

    path: str
    url: str
    content: str | None
    size_bytes: int
    kind: str
    truncated: bool
    published: bool
    publication_note: str


@dataclass(frozen=True)
class ReviewFile:
    """A file available to a review renderer."""

    path: str
    url: str
    content: str | None
    size_bytes: int
    kind: str
    truncated: bool = False
    published: bool = True
    publication_note: str = ""


@dataclass(frozen=True)
class CompletenessItem:
    """A review completeness row."""

    key: str
    label: str
    present: bool
    detail: str


@dataclass(frozen=True)
class ReviewEvidenceView:
    """Classified review evidence artifacts."""

    participant_video: ReviewFile | None
    screenshots: list[ReviewFile]
    screenshot_captions: dict[str, str]
    performance_file: ReviewFile | None
    performance_data: dict[str, object]
    performance_results: list[dict[str, object]]
    monitor_file: ReviewFile | None
    data_file: ReviewFile | None
    simulated_data_file: ReviewFile | None
    analysis_files: list[ReviewFile]
    analysis_notebook_file: ReviewFile | None
    analysis_notebook: dict[str, object]
    visible_files: list[ReviewFile]
    completeness: list[CompletenessItem]

    @property
    def has_participant_video(self) -> bool:
        """Return whether participant video evidence is present."""

        return self.participant_video is not None

    @property
    def has_screenshots(self) -> bool:
        """Return whether screenshot evidence is present."""

        return bool(self.screenshots)

    @property
    def has_performance(self) -> bool:
        """Return whether performance evidence is present."""

        return self.performance_file is not None

    @property
    def has_monitor(self) -> bool:
        """Return whether monitor evidence is present."""

        return self.monitor_file is not None

    @property
    def has_data(self) -> bool:
        """Return whether data export evidence is present."""

        return self.data_file is not None

    @property
    def has_simulated_data(self) -> bool:
        """Return whether simulated data export evidence is present."""

        return self.simulated_data_file is not None

    @property
    def has_analyses(self) -> bool:
        """Return whether analysis evidence is present."""

        return bool(self.analysis_files)

    @property
    def has_analysis_notebook(self) -> bool:
        """Return whether a renderable analysis notebook is present."""

        return self.analysis_notebook_file is not None and bool(self.analysis_notebook)


SCREENSHOT_EXTENSIONS = {"gif", "jpeg", "jpg", "png", "webp"}
TEXT_REVIEW_EXTENSIONS = {
    ".csv",
    ".html",
    ".ipynb",
    ".json",
    ".log",
    ".md",
    ".txt",
    ".yaml",
    ".yml",
}


def file_kind(path: str) -> str:
    """Return a display-oriented file type."""

    suffix = path.rsplit(".", 1)[-1].lower() if "." in path else ""
    return suffix or "file"


def review_file_from_file(file: ReviewFileLike) -> ReviewFile:
    """Convert a compatible file object into a shared review file."""

    return ReviewFile(
        path=file.path,
        url=file.url,
        content=file.content,
        size_bytes=file.size_bytes,
        kind=file.kind,
        truncated=file.truncated,
        published=file.published,
        publication_note=file.publication_note,
    )


def evidence_path(path: str) -> str:
    """Return a dashboard-compatible evidence path."""

    if path.startswith("artifacts/"):
        return path.removeprefix("artifacts/")
    return path


def default_caption(path: str) -> str:
    """Derive a readable caption from a screenshot path."""

    name = re.sub(r"\.[^.]+$", "", evidence_path(path).rsplit("/", 1)[-1])
    return name.replace("-", " ").replace("_", " ")


def first_file_by_evidence_path(
    files: list[ReviewFile],
    expected_path: str,
) -> ReviewFile | None:
    """Find the first file with a matching evidence path."""

    for file in files:
        if evidence_path(file.path) == expected_path:
            return file
    return None


def parse_json_content(file: ReviewFile | None) -> dict[str, object]:
    """Parse a JSON object from a review file's text content."""

    if file is None or not file.content:
        return {}
    try:
        data = json.loads(file.content)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def parse_screenshot_captions(manifest_file: ReviewFile | None) -> dict[str, str]:
    """Parse screenshot captions from a screenshot manifest."""

    manifest = parse_json_content(manifest_file)
    captions = manifest.get("captions")
    if not isinstance(captions, dict):
        return {}
    return {
        str(path): str(caption)
        for path, caption in captions.items()
        if isinstance(path, str) and isinstance(caption, str)
    }


def screenshot_caption(
    screenshot: ReviewFile,
    captions: dict[str, str],
) -> str:
    """Return the best caption for a screenshot."""

    path = screenshot.path
    normalized_path = evidence_path(path)
    return captions.get(path) or captions.get(normalized_path) or default_caption(path)


def performance_results(performance_data: dict[str, object]) -> list[dict[str, object]]:
    """Extract tabular performance result rows."""

    results = performance_data.get("results")
    if not isinstance(results, list):
        return []
    return [row for row in results if isinstance(row, dict)]


def analysis_files(files: list[ReviewFile]) -> list[ReviewFile]:
    """Return analysis files under the canonical analyses directory."""

    return [
        file
        for file in files
        if evidence_path(file.path).startswith("analyses/")
        or file.path.startswith("analyses/")
    ]


def classify_review_evidence(files: list[ReviewFileLike]) -> ReviewEvidenceView:
    """Classify review evidence files using shared path conventions."""

    review_files = [review_file_from_file(file) for file in files]
    participant_video = first_file_by_evidence_path(review_files, "participant.mp4")
    screenshot_files = [
        file
        for file in review_files
        if evidence_path(file.path).startswith("screenshots/")
        and file.kind in SCREENSHOT_EXTENSIONS
    ]
    screenshot_manifest = first_file_by_evidence_path(
        review_files,
        "screenshots/manifest.json",
    )
    screenshot_captions = parse_screenshot_captions(screenshot_manifest)
    performance_file = first_file_by_evidence_path(review_files, "performance.json")
    performance_data = parse_json_content(performance_file)
    monitor_file = first_file_by_evidence_path(review_files, "monitor.html")
    data_file = first_file_by_evidence_path(review_files, "data.zip")
    simulated_data_file = first_file_by_evidence_path(
        review_files,
        "simulated_data.zip",
    )
    analyses = analysis_files(review_files)
    notebook_files = [file for file in analyses if file.kind == "ipynb"]
    analysis_notebook_file = (
        first_file_by_evidence_path(review_files, "analyses/analysis.ipynb")
        or (notebook_files[0] if notebook_files else None)
    )
    analysis_notebook = parse_json_content(analysis_notebook_file)

    visible_files = [
        file
        for file in review_files
        if not is_special_rendered_file(
            file,
            screenshot_files,
            screenshot_manifest,
            analysis_notebook_file,
        )
    ]
    completeness = completeness_items(
        participant_video=participant_video,
        screenshots=screenshot_files,
        performance_file=performance_file,
        monitor_file=monitor_file,
        data_file=data_file,
        simulated_data_file=simulated_data_file,
        analyses=analyses,
    )
    return ReviewEvidenceView(
        participant_video=participant_video,
        screenshots=screenshot_files,
        screenshot_captions=screenshot_captions,
        performance_file=performance_file,
        performance_data=performance_data,
        performance_results=performance_results(performance_data),
        monitor_file=monitor_file,
        data_file=data_file,
        simulated_data_file=simulated_data_file,
        analysis_files=analyses,
        analysis_notebook_file=analysis_notebook_file,
        analysis_notebook=analysis_notebook,
        visible_files=visible_files,
        completeness=completeness,
    )


def is_special_rendered_file(
    file: ReviewFile,
    screenshots: list[ReviewFile],
    screenshot_manifest: ReviewFile | None,
    analysis_notebook_file: ReviewFile | None,
) -> bool:
    """Return whether a file is rendered elsewhere in the evidence view."""

    if evidence_path(file.path) == "participant.mp4":
        return True
    if file in screenshots:
        return True
    if screenshot_manifest is not None and file.path == screenshot_manifest.path:
        return True
    if evidence_path(file.path) == "screenshots/README.md":
        return True
    if analysis_notebook_file is not None and file.path == analysis_notebook_file.path:
        return True
    return False


def completeness_items(
    *,
    participant_video: ReviewFile | None,
    screenshots: list[ReviewFile],
    performance_file: ReviewFile | None,
    monitor_file: ReviewFile | None,
    data_file: ReviewFile | None,
    simulated_data_file: ReviewFile | None,
    analyses: list[ReviewFile],
) -> list[CompletenessItem]:
    """Build review artifact completeness rows."""

    return [
        CompletenessItem(
            "participant_video",
            "participant.mp4",
            participant_video is not None,
            "present" if participant_video is not None else "missing",
        ),
        CompletenessItem(
            "screenshots",
            "screenshots/",
            bool(screenshots),
            f"{len(screenshots)} image{'s' if len(screenshots) != 1 else ''}"
            if screenshots
            else "missing",
        ),
        CompletenessItem(
            "performance",
            "performance.json",
            performance_file is not None,
            "present" if performance_file is not None else "missing",
        ),
        CompletenessItem(
            "monitor",
            "monitor.html",
            monitor_file is not None,
            "present" if monitor_file is not None else "missing",
        ),
        CompletenessItem(
            "data",
            "data.zip",
            data_file is not None,
            "present" if data_file is not None else "missing",
        ),
        CompletenessItem(
            "simulated_data",
            "simulated_data.zip",
            simulated_data_file is not None,
            "present" if simulated_data_file is not None else "missing",
        ),
        CompletenessItem(
            "analyses",
            "analyses/",
            bool(analyses),
            f"{len(analyses)} file{'s' if len(analyses) != 1 else ''}"
            if analyses
            else "missing",
        ),
    ]
