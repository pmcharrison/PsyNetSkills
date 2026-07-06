"""Shared HTML rendering for review evidence."""

from __future__ import annotations

import html
import re
from collections.abc import Callable, Iterable
from html.parser import HTMLParser
from urllib.parse import urlparse

from psynetsk_tools.review_model import (
    CompletenessItem,
    ReviewEvidenceView,
    ReviewFile,
    screenshot_caption,
)

UrlTransform = Callable[[str], str]
SAFE_HTML_TAGS = {
    "a",
    "b",
    "blockquote",
    "br",
    "code",
    "dd",
    "div",
    "dl",
    "dt",
    "em",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "hr",
    "i",
    "li",
    "ol",
    "p",
    "pre",
    "span",
    "strong",
    "table",
    "tbody",
    "td",
    "th",
    "thead",
    "tr",
    "ul",
}
SAFE_SVG_TAGS = {
    "circle",
    "ellipse",
    "g",
    "line",
    "path",
    "polygon",
    "polyline",
    "rect",
    "svg",
    "text",
    "title",
}
SAFE_ATTRS = {
    "align",
    "aria-label",
    "class",
    "colspan",
    "height",
    "id",
    "role",
    "rowspan",
    "scope",
    "title",
    "width",
}
SAFE_SVG_ATTRS = {
    "cx",
    "cy",
    "d",
    "fill",
    "height",
    "points",
    "r",
    "rx",
    "ry",
    "stroke",
    "stroke-width",
    "viewbox",
    "width",
    "x",
    "x1",
    "x2",
    "xmlns",
    "y",
    "y1",
    "y2",
}


def identity_url(url: str) -> str:
    """Return a URL unchanged."""

    return url


def escape_url(url: str, url_transform: UrlTransform = identity_url) -> str:
    """Escape a transformed URL for use in an HTML attribute."""

    return html.escape(url_transform(url), quote=True)


def is_safe_url(url: str) -> bool:
    """Return whether a URL is safe to emit in rendered review HTML."""

    if not url:
        return False
    parsed = urlparse(url)
    return parsed.scheme in {"", "http", "https", "mailto"} and not url.lstrip().lower().startswith(
        "javascript:",
    )


class SafeHTMLRenderer(HTMLParser):
    """Render a small safe subset of HTML or SVG."""

    def __init__(self, allowed_tags: set[str], allowed_attrs: set[str]):
        super().__init__(convert_charrefs=True)
        self.allowed_tags = allowed_tags
        self.allowed_attrs = allowed_attrs
        self.skip_content_depth = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Emit a safe start tag when the tag is allowed."""

        tag = tag.lower()
        if tag in {"script", "style"}:
            self.skip_content_depth += 1
            return
        if tag not in self.allowed_tags:
            return
        attr_text = "".join(self.safe_attr(tag, name, value) for name, value in attrs)
        self.parts.append(f"<{tag}{attr_text}>")

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Emit a safe self-closing tag when the tag is allowed."""

        tag = tag.lower()
        if tag in {"script", "style"}:
            return
        if tag not in self.allowed_tags:
            return
        attr_text = "".join(self.safe_attr(tag, name, value) for name, value in attrs)
        if tag in {"br", "hr"}:
            self.parts.append(f"<{tag}{attr_text}>")
        else:
            self.parts.append(f"<{tag}{attr_text}></{tag}>")

    def handle_endtag(self, tag: str) -> None:
        """Emit a safe end tag when the tag is allowed."""

        tag = tag.lower()
        if self.skip_content_depth and tag in {"script", "style"}:
            self.skip_content_depth -= 1
            return
        if tag in self.allowed_tags:
            self.parts.append(f"</{tag}>")

    def handle_data(self, data: str) -> None:
        """Escape text data."""

        if not self.skip_content_depth:
            self.parts.append(html.escape(data))

    def safe_attr(self, tag: str, name: str, value: str | None) -> str:
        """Return a sanitized attribute or an empty string."""

        if value is None:
            return ""
        name = name.lower()
        if name.startswith("on") or name == "style":
            return ""
        if tag == "a" and name == "href":
            return f' href="{html.escape(value, quote=True)}"' if is_safe_url(value) else ""
        if name not in self.allowed_attrs:
            return ""
        output_name = "viewBox" if name == "viewbox" else name
        return f' {output_name}="{html.escape(value, quote=True)}"'

    def render(self) -> str:
        """Return the sanitized HTML string."""

        return "".join(self.parts)


def sanitize_html_fragment(source: str) -> str:
    """Render a safe subset of an HTML fragment."""

    renderer = SafeHTMLRenderer(SAFE_HTML_TAGS, SAFE_ATTRS)
    renderer.feed(source)
    renderer.close()
    return renderer.render()


def sanitize_svg_fragment(source: str) -> str:
    """Render a safe subset of an SVG fragment."""

    renderer = SafeHTMLRenderer(SAFE_SVG_TAGS, SAFE_ATTRS | SAFE_SVG_ATTRS)
    renderer.feed(source)
    renderer.close()
    return renderer.render()


def render_markdown_inline(source: str) -> str:
    """Render a small safe inline Markdown subset."""

    placeholders: list[str] = []

    def stash(value: str) -> str:
        placeholders.append(value)
        return f"\x00{len(placeholders) - 1}\x00"

    text = html.escape(source)
    text = re.sub(
        r"`([^`]+)`",
        lambda match: stash(f"<code>{match.group(1)}</code>"),
        text,
    )
    text = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        lambda match: stash(
            f'<a href="{html.escape(match.group(2), quote=True)}">{match.group(1)}</a>',
        )
        if is_safe_url(html.unescape(match.group(2)))
        else match.group(1),
        text,
    )
    text = re.sub(r"\*\*([^*]+)\*\*", lambda match: stash(f"<strong>{match.group(1)}</strong>"), text)
    text = re.sub(r"\*([^*]+)\*", lambda match: stash(f"<em>{match.group(1)}</em>"), text)
    for index, value in enumerate(placeholders):
        text = text.replace(f"\x00{index}\x00", value)
    return text


def render_markdown_document(source: str) -> str:
    """Render a small safe Markdown subset for reports and notebook cells."""

    blocks: list[str] = []
    paragraph: list[str] = []
    list_items: list[str] = []
    ordered_list = False
    code_lines: list[str] | None = None

    def flush_paragraph() -> None:
        if paragraph:
            blocks.append(f"<p>{render_markdown_inline(' '.join(paragraph))}</p>")
            paragraph.clear()

    def flush_list() -> None:
        nonlocal ordered_list
        if list_items:
            tag = "ol" if ordered_list else "ul"
            blocks.append(f"<{tag}>" + "".join(list_items) + f"</{tag}>")
            list_items.clear()
            ordered_list = False

    for line in source.splitlines():
        stripped = line.strip()
        if code_lines is not None:
            if stripped.startswith("```"):
                blocks.append(f"<pre><code>{html.escape(chr(10).join(code_lines))}</code></pre>")
                code_lines = None
            else:
                code_lines.append(line)
            continue
        if stripped.startswith("```"):
            flush_paragraph()
            flush_list()
            code_lines = []
            continue
        if not stripped:
            flush_paragraph()
            flush_list()
            continue
        if stripped.startswith("#"):
            marks, _, title = stripped.partition(" ")
            if title and set(marks) == {"#"}:
                flush_paragraph()
                flush_list()
                level = min(len(marks), 6)
                blocks.append(f"<h{level}>{render_markdown_inline(title)}</h{level}>")
                continue
        bullet_match = re.match(r"^[-*]\s+(.+)$", stripped)
        ordered_match = re.match(r"^\d+[.)]\s+(.+)$", stripped)
        if bullet_match or ordered_match:
            flush_paragraph()
            item = bullet_match.group(1) if bullet_match else ordered_match.group(1)
            item_ordered = ordered_match is not None
            if list_items and item_ordered != ordered_list:
                flush_list()
            ordered_list = item_ordered
            list_items.append(f"<li>{render_markdown_inline(item)}</li>")
            continue
        flush_list()
        paragraph.append(stripped)

    if code_lines is not None:
        blocks.append(f"<pre><code>{html.escape(chr(10).join(code_lines))}</code></pre>")
    flush_paragraph()
    flush_list()
    return "\n".join(blocks) if blocks else ""


def render_artifact_card(
    artifact: ReviewFile,
    *,
    url_transform: UrlTransform = identity_url,
) -> str:
    """Render one artifact card."""

    path = html.escape(artifact.path)
    kind = html.escape(artifact.kind)

    if artifact.url:
        action = f'<a href="{escape_url(artifact.url, url_transform)}">Open artifact</a>'
    else:
        action = "<span>No artifact file published.</span>"

    return (
        '<article class="artifact-card">'
        f"<h3><code>{path}</code></h3>"
        "<dl>"
        f"<dt>Kind</dt><dd>{kind}</dd>"
        f"<dt>Size</dt><dd>{artifact.size_bytes} bytes</dd>"
        "</dl>"
        f"<p>{action}</p>"
        "</article>"
    )


def render_participant_video(
    evidence: ReviewEvidenceView,
    *,
    url_transform: UrlTransform = identity_url,
) -> str:
    """Render participant video evidence."""

    video = evidence.participant_video
    if video is None:
        return "<p>No participant recording was found.</p>"
    return (
        '<video class="attempt-video" controls preload="metadata">'
        f'<source src="{escape_url(video.url, url_transform)}" type="video/mp4">'
        "Your browser does not support embedded video."
        "</video>"
        f'<p class="artifact-note"><code>{html.escape(video.path)}</code> '
        f"&middot; {video.size_bytes} bytes</p>"
    )


def render_screenshot_gallery(
    evidence: ReviewEvidenceView,
    *,
    url_transform: UrlTransform = identity_url,
) -> str:
    """Render screenshot evidence."""

    if not evidence.screenshots:
        return ""
    figures: list[str] = []
    for index, screenshot in enumerate(evidence.screenshots):
        caption = screenshot_caption(screenshot, evidence.screenshot_captions)
        hidden = " hidden" if index != 0 else ""
        figures.append(
            '<figure class="screenshot-card" data-screenshot-card '
            f'data-screenshot-caption-text="{html.escape(caption, quote=True)}"{hidden}>'
            f'<a href="{escape_url(screenshot.url, url_transform)}" '
            'aria-label="Open full-size screenshot">'
            f'<img src="{escape_url(screenshot.url, url_transform)}" '
            f'alt="{html.escape(caption, quote=True)}">'
            "</a>"
            "</figure>"
        )
    return (
        '<section class="screenshot-gallery" aria-labelledby="screenshot-gallery-heading">'
        '<div class="screenshot-gallery-header">'
        '<h3 id="screenshot-gallery-heading">Screenshot walkthrough</h3>'
        '<p class="artifact-note">Targeted participant-facing states captured with Playwright.</p>'
        "</div>"
        '<div class="screenshot-frame">'
        '<div class="screenshot-carousel" data-screenshot-gallery tabindex="0">'
        + "\n".join(figures)
        + "</div>"
        '<div class="screenshot-caption-panel">'
        '<div class="screenshot-controls" aria-label="Screenshot navigation">'
        '<button class="screenshot-nav" type="button" data-screenshot-prev '
        'aria-label="Previous screenshot">&lsaquo;</button>'
        f'<span class="screenshot-counter" data-screenshot-counter>1 / {len(evidence.screenshots)}</span>'
        '<button class="screenshot-nav" type="button" data-screenshot-next '
        'aria-label="Next screenshot">&rsaquo;</button>'
        "</div>"
        '<p class="screenshot-caption" data-screenshot-caption></p>'
        "</div></div></section>"
    )


def first_analysis_file(evidence: ReviewEvidenceView) -> ReviewFile | None:
    """Return the first available analysis artifact."""

    return evidence.analysis_files[0] if evidence.analysis_files else None


def render_evidence_actions(
    evidence: ReviewEvidenceView,
    *,
    url_transform: UrlTransform = identity_url,
) -> str:
    """Render direct evidence artifact links."""

    analysis_file = first_analysis_file(evidence)
    items = [
        evidence_action_item("Monitor snapshot", evidence.monitor_file, "Open monitor snapshot", url_transform),
        evidence_action_item(
            "Performance result",
            evidence.performance_file,
            "View performance test result",
            url_transform,
        ),
        evidence_action_item("Data export", evidence.data_file, "Download data export", url_transform),
        evidence_action_item(
            "Simulated data export",
            evidence.simulated_data_file,
            "Download simulated data",
            url_transform,
        ),
        analysis_action_item(evidence, analysis_file, url_transform),
    ]
    return '<ul class="evidence-actions">' + "\n".join(items) + "</ul>"


def evidence_action_item(
    missing_label: str,
    file: ReviewFile | None,
    action: str,
    url_transform: UrlTransform,
) -> str:
    """Render one evidence action item."""

    if file is None:
        return f'<li><span class="missing-artifact">{html.escape(missing_label)} missing</span></li>'
    if not file.url:
        detail = file.publication_note or "artifact file is not published"
        return (
            f'<li><span class="missing-artifact" title="{html.escape(detail, quote=True)}">'
            f"{html.escape(missing_label)} not published</span></li>"
        )
    return f'<li><a href="{escape_url(file.url, url_transform)}">{html.escape(action)}</a></li>'


def analysis_action_item(
    evidence: ReviewEvidenceView,
    analysis_file: ReviewFile | None,
    url_transform: UrlTransform,
) -> str:
    """Render the analysis evidence action item."""

    if evidence.has_analysis_notebook:
        return '<li><a href="#analysis-notebook">View analysis notebook</a></li>'
    if analysis_file is not None:
        if not analysis_file.url:
            detail = analysis_file.publication_note or "artifact file is not published"
            return (
                '<li><span class="missing-artifact" '
                f'title="{html.escape(detail, quote=True)}">Analysis summary not published</span></li>'
            )
        return (
            f'<li><a href="{escape_url(analysis_file.url, url_transform)}">'
            "View analysis artifact</a></li>"
        )
    return '<li><span class="missing-artifact">Analysis summary missing</span></li>'


def render_analysis_notebook(
    evidence: ReviewEvidenceView,
    *,
    url_transform: UrlTransform = identity_url,
) -> str:
    """Render a small safe preview of an analysis notebook."""

    notebook_file = evidence.analysis_notebook_file
    notebook = evidence.analysis_notebook
    if notebook_file is None or not notebook:
        return ""

    cells = notebook.get("cells")
    if not isinstance(cells, list):
        cells = []
    rendered_cells = [
        render_notebook_cell(cell)
        for cell in cells
        if isinstance(cell, dict)
    ]
    return (
        '<section id="analysis-notebook" class="analysis-notebook-panel evidence-subsection">'
        '<div class="section-heading">'
        "<h3>Analysis notebook</h3>"
        f'<a href="{escape_url(notebook_file.url, url_transform)}">Open raw notebook</a>'
        "</div>"
        f'<p class="artifact-note">Rendered from <code>{html.escape(notebook_file.path)}</code>.</p>'
        '<div class="notebook-preview">'
        + "\n".join(rendered_cells)
        + "</div></section>"
    )


def render_notebook_cell(cell: dict[str, object]) -> str:
    """Render one notebook cell with safe source and outputs."""

    cell_type = str(cell.get("cell_type") or "raw")
    source = notebook_text(cell.get("source"))
    safe_type = html.escape(cell_type)
    if cell_type == "markdown":
        body = f'<div class="attempt-markdown">{render_markdown_document(source)}</div>'
    elif cell_type == "code":
        body = (
            '<div class="notebook-code">'
            f"<pre><code>{html.escape(source)}</code></pre>"
            "</div>"
            f"{render_notebook_outputs(cell.get('outputs'))}"
        )
    else:
        body = f"<pre><code>{html.escape(source)}</code></pre>"
    return f'<section class="notebook-cell notebook-cell-{safe_type}">{body}</section>'


def notebook_text(value: object) -> str:
    """Return notebook source or output text as a string."""

    if isinstance(value, list):
        return "".join(str(part) for part in value)
    if isinstance(value, str):
        return value
    return ""


def render_notebook_outputs(outputs: object) -> str:
    """Render safe text, HTML, or SVG outputs from a notebook code cell."""

    if not isinstance(outputs, list) or not outputs:
        return ""
    rendered_outputs: list[str] = []
    for output in outputs:
        if not isinstance(output, dict):
            continue
        rendered = render_notebook_output(output)
        if rendered:
            rendered_outputs.append(rendered)
    if not rendered_outputs:
        return ""
    return '<div class="notebook-outputs">' + "\n".join(rendered_outputs) + "</div>"


def render_notebook_output(output: dict[str, object]) -> str:
    """Render one notebook output."""

    output_type = output.get("output_type")
    if output_type == "error":
        traceback = notebook_text(output.get("traceback"))
        return f'<pre class="notebook-error"><code>{html.escape(traceback)}</code></pre>' if traceback else ""

    text = notebook_text(output.get("text"))
    if text:
        return f"<pre><code>{html.escape(text)}</code></pre>"

    data = output.get("data")
    if not isinstance(data, dict):
        return ""
    svg = notebook_text(data.get("image/svg+xml"))
    if svg:
        return f'<div class="notebook-svg">{sanitize_svg_fragment(svg)}</div>'
    html_output = notebook_text(data.get("text/html"))
    if html_output:
        return f'<div class="notebook-html">{sanitize_html_fragment(html_output)}</div>'
    plain = notebook_text(data.get("text/plain"))
    if plain:
        return f"<pre><code>{html.escape(plain)}</code></pre>"
    return ""


def render_performance_result(
    evidence: ReviewEvidenceView,
    *,
    url_transform: UrlTransform = identity_url,
) -> str:
    """Render performance results when available."""

    if evidence.performance_file is None:
        return ""

    options = render_performance_options(evidence.performance_data.get("options"))
    if not evidence.performance_results:
        return (
            '<section class="performance-result">'
            f"{render_performance_header(evidence.performance_file, url_transform)}"
            f"{options}"
            '<p class="artifact-note">This performance artifact does not contain '
            "tabular result rows.</p></section>"
        )

    body: list[str] = []
    for row in evidence.performance_results:
        errors = int(row.get("request_errors") or 0) + int(row.get("bot_errors") or 0)
        body.append(
            "<tr>"
            f"<td>{html.escape(str(row.get('n_bots', '')))}</td>"
            f"<td>{html.escape(str(row.get('total_bots_started', '')))}</td>"
            f"<td>{html.escape(str(row.get('bots_succeeded', '')))}</td>"
            f"<td>{html.escape(str(row.get('total_requests', '')))}</td>"
            f"<td>{format_metric(row.get('median_response_time'))}</td>"
            f"<td>{format_metric(row.get('p95_response_time'))}</td>"
            f"<td>{format_metric(row.get('q_delay_p95'))}</td>"
            f"<td>{errors}</td>"
            "</tr>"
        )
    return (
        '<section class="performance-result">'
        f"{render_performance_header(evidence.performance_file, url_transform)}"
        f"{options}"
        '<div class="performance-table-wrap">'
        '<table class="performance-table"><thead><tr>'
        f"{performance_heading('Concurrent target', 'The target number of bot participants kept active during this load-test run.')}"
        f"{performance_heading('Bots started', 'Total bot participants launched during the run, including replacements started as earlier bots finish.')}"
        f"{performance_heading('Succeeded', 'Bots that completed the experiment successfully during the test window.')}"
        f"{performance_heading('Requests', 'HTTP requests observed for key participant endpoints such as timeline and response routes.')}"
        f"{performance_heading('Resp Med (s)', 'Median HTTP response time, in seconds, for key participant endpoints.')}"
        f"{performance_heading('Resp P95 (s)', '95th percentile HTTP response time, in seconds, for key participant endpoints; higher values show slower tail latency.')}"
        f"{performance_heading('Q P95 all (s)', '95th percentile async-process queue delay across trial makers, when queue metrics are available.')}"
        f"{performance_heading('Errors', 'Request errors plus bot errors recorded during the run.')}"
        "</tr></thead><tbody>"
        + "\n".join(body)
        + "</tbody></table></div></section>"
    )


def render_performance_header(
    performance_file: ReviewFile,
    url_transform: UrlTransform,
) -> str:
    """Render the performance section header."""

    return (
        '<header class="performance-result-header"><div><h3>'
        '<span class="header-popover" tabindex="0">Performance test result'
        '<span class="info-popover-content" role="tooltip">'
        "A performance test starts a local PsyNet server, repeatedly launches automated bot participants, "
        "and records how many complete the experiment, how many requests they make, and how quickly key "
        "pages respond under load."
        "</span></span></h3></div>"
        f'<a href="{escape_url(performance_file.url, url_transform)}">Raw JSON</a></header>'
    )


def render_performance_options(options: object) -> str:
    """Render performance-test options when available."""

    if not isinstance(options, dict):
        return ""
    n_bots = options.get("n_bots_sweep")
    n_bots_text = ", ".join(str(value) for value in n_bots) if isinstance(n_bots, list) else ""
    rows = [
        ("Target concurrent bots", n_bots_text),
        ("Duration", format_minutes(options.get("duration_minutes"))),
        ("Start stagger", format_seconds(options.get("stagger_interval_s"))),
        ("Time factor", str(options.get("time_factor") or "")),
    ]
    return (
        '<dl class="performance-options">'
        + "".join(
            f"<div><dt>{html.escape(label)}</dt><dd>{html.escape(value)}</dd></div>"
            for label, value in rows
            if value
        )
        + "</dl>"
    )


def performance_heading(label: str, tooltip: str) -> str:
    """Render a performance table heading with a tooltip."""

    return (
        "<th><span class=\"header-popover\" tabindex=\"0\">"
        f"{html.escape(label)}"
        f'<span class="info-popover-content" role="tooltip">{html.escape(tooltip)}</span>'
        "</span></th>"
    )


def format_metric(value: object) -> str:
    """Format a numeric performance metric."""

    if isinstance(value, int | float) and not isinstance(value, bool):
        return f"{value:.3f}"
    return "N/A"


def format_minutes(value: object) -> str:
    """Format a minute value."""

    if isinstance(value, int | float) and not isinstance(value, bool):
        return f"{value:.2f} min"
    return ""


def format_seconds(value: object) -> str:
    """Format a second value."""

    if isinstance(value, int | float) and not isinstance(value, bool):
        return f"{value:.1f}s"
    return ""


def render_completeness(
    evidence: ReviewEvidenceView,
    *,
    extra_items: Iterable[CompletenessItem] = (),
) -> str:
    """Render artifact completeness rows."""

    items = [
        f'<li class="{"present" if item.present else "missing"}">'
        f"{html.escape(item.label)} <span>{html.escape(item.detail)}</span></li>"
        for item in [*extra_items, *evidence.completeness]
    ]
    return (
        '<section class="evidence-subsection">'
        "<h3>Artifact completeness</h3>"
        '<ul class="artifact-checklist">'
        + "\n".join(items)
        + "</ul></section>"
    )


def render_visible_artifacts(
    evidence: ReviewEvidenceView,
    *,
    url_transform: UrlTransform = identity_url,
) -> str:
    """Render remaining evidence files."""

    if not evidence.visible_files:
        return "<p>No additional evidence files were found.</p>"
    cards = "\n".join(
        render_artifact_card(file, url_transform=url_transform)
        for file in evidence.visible_files
    )
    return f'<div class="artifact-grid">{cards}</div>'


def render_evidence_section(
    evidence: ReviewEvidenceView,
    *,
    extra_completeness: Iterable[CompletenessItem] = (),
    include_heading: bool = True,
    section_id: str | None = "evidence",
    url_transform: UrlTransform = identity_url,
) -> str:
    """Render the main evidence section."""

    heading = "<h2>Evidence</h2>" if include_heading else ""
    section_attributes = f' id="{html.escape(section_id, quote=True)}"' if section_id else ""
    return (
        f"<section{section_attributes}>"
        f"{heading}"
        f"{render_participant_video(evidence, url_transform=url_transform)}"
        f"{render_screenshot_gallery(evidence, url_transform=url_transform)}"
        f"{render_evidence_actions(evidence, url_transform=url_transform)}"
        f"{render_analysis_notebook(evidence, url_transform=url_transform)}"
        f"{render_performance_result(evidence, url_transform=url_transform)}"
        f"{render_completeness(evidence, extra_items=extra_completeness)}"
        "</section>"
    )
