import json
import shutil
import subprocess
import textwrap
from pathlib import Path


def run_workflow_status_case(config: dict, responses: list[dict]) -> dict:
    node = shutil.which("node")
    if node is None:
        raise AssertionError("node is required to test workflow-status.js")

    script_path = Path("dashboard/static/js/workflow-status.js")
    script = textwrap.dedent(
        f"""
        const fs = require("fs");
        const vm = require("vm");
        const source = fs.readFileSync({json.dumps(str(script_path))}, "utf8");
        const config = {json.dumps(config)};
        const responses = {json.dumps(responses)};

        class ClassList {{
          constructor(classes) {{
            this.classes = new Set(classes.split(/\\s+/).filter(Boolean));
          }}
          add(...classes) {{
            classes.forEach((item) => this.classes.add(item));
          }}
          remove(...classes) {{
            classes.forEach((item) => this.classes.delete(item));
          }}
          contains(item) {{
            return this.classes.has(item);
          }}
        }}

        class Element {{
          constructor(classes = "") {{
            this.classList = new ClassList(classes);
            this.dataset = {{}};
            this.attributes = {{}};
            this.children = [];
            this.hidden = false;
            this.style = {{}};
            this.textContent = "";
            this.href = "";
          }}
          addEventListener() {{}}
          appendChild(child) {{
            this.children.push(child);
          }}
          getBoundingClientRect() {{
            return {{ left: 0, right: 100 }};
          }}
          querySelector(selector) {{
            return this[selector];
          }}
          replaceChildren(...children) {{
            this.children = children;
          }}
          setAttribute(name, value) {{
            this.attributes[name] = value;
          }}
        }}

        const statusLink = new Element("workflow-status-link workflow-status-unknown workflow-freshness-current");
        const icon = new Element("workflow-status-icon");
        const popover = new Element("workflow-status-popover");
        statusLink[".workflow-status-icon"] = icon;
        statusLink[".workflow-status-popover"] = popover;
        statusLink.dataset = config;

        const context = {{
          console,
          document: {{
            visibilityState: "visible",
            activeElement: null,
            addEventListener() {{}},
            createElement() {{ return new Element(); }},
            querySelector(selector) {{
              return selector === "[data-workflow-status]" ? statusLink : null;
            }},
          }},
          fetch: async () => {{
            const data = responses.shift();
            return {{
              ok: true,
              headers: {{ get: () => null }},
              json: async () => data,
            }};
          }},
          window: {{
            clearTimeout() {{}},
            innerWidth: 1024,
            matchMedia: () => {{ return {{ matches: false }}; }},
            requestAnimationFrame: (callback) => callback(),
            setTimeout() {{ return 0; }},
          }},
        }};

        vm.createContext(context);
        vm.runInContext(source, context);

        setImmediate(() => setImmediate(() => {{
          console.log(JSON.stringify({{
            icon: icon.textContent,
            isStale: statusLink.classList.contains("workflow-freshness-stale"),
            label: statusLink.attributes["aria-label"],
            lines: popover.children.map((child) => child.textContent),
          }}));
        }}));
        """
    )

    result = subprocess.run(
        [node, "-e", script],
        cwd=Path(__file__).resolve().parents[1],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def test_workflow_status_hides_warning_for_running_newer_build() -> None:
    result = run_workflow_status_case(
        {
            "enabled": "true",
            "owner": "pmcharrison",
            "repo": "PsyNetSkills",
            "workflow": "dashboard-preview.yml",
            "branch": "cursor/example",
            "renderedSha": "oldsha",
            "mode": "local",
        },
        [
            {
                "workflow_runs": [
                    {
                        "status": "in_progress",
                        "head_sha": "newsha",
                        "html_url": "https://example.test/run",
                    },
                ],
            },
        ],
    )

    assert result["icon"] == "●"
    assert result["isStale"] is False
    assert "A newer branch run is in progress." in result["label"]


def test_workflow_status_shows_warning_for_completed_newer_build() -> None:
    result = run_workflow_status_case(
        {
            "enabled": "true",
            "owner": "pmcharrison",
            "repo": "PsyNetSkills",
            "workflow": "dashboard-preview.yml",
            "branch": "cursor/example",
            "renderedSha": "oldsha",
            "mode": "local",
        },
        [
            {
                "workflow_runs": [
                    {
                        "status": "completed",
                        "conclusion": "success",
                        "head_sha": "newsha",
                        "html_url": "https://example.test/run",
                    },
                ],
            },
        ],
    )

    assert result["icon"] == "✓"
    assert result["isStale"] is True
    assert result["lines"][1].startswith("Refresh page to see new content:")
