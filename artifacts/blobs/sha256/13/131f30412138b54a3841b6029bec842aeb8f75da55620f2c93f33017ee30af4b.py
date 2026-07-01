from __future__ import annotations

import html
import json
import zipfile
from collections import Counter
from pathlib import Path

import pandas as pd


ATTEMPT_DIR = Path(__file__).resolve().parents[2]
EVIDENCE_DIR = ATTEMPT_DIR / "evidence"
EXPORT_ZIP = EVIDENCE_DIR / "simulated_data.zip"
OUTPUT_HTML = EVIDENCE_DIR / "curated_profile_monitor.html"

PROFILE_STYLES = {
    "random": {
        "label": "random",
        "class": "profile-random",
        "color": "#f58518",
        "behavior": "Uniform random valid RGB-channel response.",
    },
    "normal_rgb": {
        "label": "normal_rgb",
        "class": "profile-normal",
        "color": "#4c78a8",
        "behavior": "Normal sample around the presented active-channel value (SD 20 RGB units), clipped to 0-255.",
    },
    "mixed": {
        "label": "mixed",
        "class": "profile-mixed",
        "color": "#7b61ff",
        "behavior": "Node contains trials from both simulated response profiles.",
    },
    "none": {
        "label": "no trials",
        "class": "profile-none",
        "color": "#9ca3af",
        "behavior": "No finalized profile-labeled trials are attached to this node.",
    },
}


def read_export_csv(name: str) -> pd.DataFrame:
    with zipfile.ZipFile(EXPORT_ZIP) as zf:
        with zf.open(f"simulated_data/regular/data/{name}") as f:
            return pd.read_csv(f)


def parse_jsonish(value, fallback=None):
    if pd.isna(value):
        return fallback
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return fallback
    return value


def profile_key(profile_counts: Counter) -> str:
    profiles = [profile for profile, count in profile_counts.items() if count > 0]
    if len(profiles) == 1:
        return profiles[0]
    if len(profiles) > 1:
        return "mixed"
    return "none"


def esc(value) -> str:
    if isinstance(value, (list, tuple, dict)):
        return html.escape(str(value))
    if pd.isna(value):
        return ""
    return html.escape(str(value))


def trial_summary(row: pd.Series) -> str:
    profile = row["bot_profile"]
    style = PROFILE_STYLES.get(profile, PROFILE_STYLES["none"])
    starting = parse_jsonish(row["initial_vector"], [])
    active_index = int(row["active_index"])
    start_value = starting[active_index] if starting else ""
    answer = int(row["answer"])
    distance = abs(answer - start_value) if start_value != "" else ""
    repeat = "repeat" if bool(row["is_repeat_trial"]) else "main"
    response = (
        f"<strong>P{int(row['participant_id'])}</strong> "
        f"<span class='pill {style['class']}'>{esc(profile)}</span> "
        f"<span>{esc(repeat)} trial</span> "
        f"<span>target <strong>{esc(row['target'])}</strong></span> "
        f"<span>active <strong>{esc(row['active_color'])}</strong></span> "
        f"<span>start RGB <code>{esc(starting)}</code></span> "
        f"<span>response <strong>{answer}</strong></span> "
        f"<span>|distance from start| <strong>{distance}</strong></span>"
    )
    return f"<li>{response}<br><small>{esc(style['behavior'])}</small></li>"


def render_node(node: pd.Series, trials: pd.DataFrame, children_by_parent: dict[int, list[pd.Series]]) -> str:
    node_trials = trials[trials["node_id"] == node["id"]].sort_values("id")
    counts = Counter(node_trials["bot_profile"].dropna())
    key = profile_key(counts)
    style = PROFILE_STYLES[key]
    context = parse_jsonish(node["context"], {})
    definition = parse_jsonish(node["definition"], {})
    target = context.get("target", "")
    active_index = definition.get("active_index", "")
    active_color = ["red", "green", "blue"][active_index] if active_index in [0, 1, 2] else ""
    count_label = ", ".join(f"{profile}: {count}" for profile, count in sorted(counts.items())) or "no profile trials"
    child_nodes = children_by_parent.get(int(node["id"]), [])

    children_html = "".join(render_node(child, trials, children_by_parent) for child in child_nodes)
    trial_html = "\n".join(trial_summary(row) for _, row in node_trials.iterrows())
    if not trial_html:
        trial_html = "<li><em>No finalized trials attached to this node.</em></li>"

    return f"""
    <li class="tree-item {style['class']}">
      <details open>
        <summary>
          <span class="node-dot"></span>
          <strong>Node {int(node['id'])}</strong>
          <span>degree {int(node['degree'])}</span>
          <span>group {esc(node['participant_group'])}</span>
          <span>target {esc(target)}</span>
          <span>active {esc(active_color)}</span>
          <span class="pill {style['class']}">{esc(style['label'])}</span>
          <span class="counts">{esc(count_label)}</span>
        </summary>
        <div class="node-body">
          <p class="curated">Curated summary: {esc(style['behavior'])}</p>
          <details>
            <summary>Trials: participant ID, response, profile behavior</summary>
            <ul class="trial-list">{trial_html}</ul>
          </details>
          {f'<ul class="tree">{children_html}</ul>' if children_html else ''}
        </div>
      </details>
    </li>
    """


def main() -> None:
    networks = read_export_csv("CustomNetwork.csv")
    nodes = read_export_csv("CustomNode.csv")
    trials = read_export_csv("CustomTrial.csv")
    bots = read_export_csv("Bot.csv")

    trials = trials[trials["finalized"] == True].copy()
    trials["answer"] = trials["answer"].astype(int)

    completed = bots[(bots["complete"] == True) & (bots["aborted"] == False)]
    distribution = completed["bot_profile"].value_counts().sort_index()
    distribution_html = "".join(
        f"<tr><td><span class='pill {PROFILE_STYLES[profile]['class']}'>{esc(profile)}</span></td><td>{int(count)}</td></tr>"
        for profile, count in distribution.items()
    )

    children_by_parent: dict[int, list[pd.Series]] = {}
    for _, node in nodes[nodes["parent_id"].notna()].sort_values(["parent_id", "id"]).iterrows():
        children_by_parent.setdefault(int(node["parent_id"]), []).append(node)

    network_sections = []
    for _, network in networks.sort_values("id").iterrows():
        network_nodes = nodes[nodes["network_id"] == network["id"]]
        root_nodes = network_nodes[network_nodes["parent_id"].isna()].sort_values("id")
        network_trials = trials[trials["network_id"] == network["id"]]
        network_counts = Counter(network_trials["bot_profile"].dropna())
        key = profile_key(network_counts)
        context = parse_jsonish(network["context"], {})
        tree_html = "".join(render_node(node, trials, children_by_parent) for _, node in root_nodes.iterrows())
        network_sections.append(
            f"""
            <section class="network-card {PROFILE_STYLES[key]['class']}">
              <h2>Network {int(network['id'])}: target {esc(context.get('target', ''))}, group {esc(network['participant_group'])}</h2>
              <p>
                <span class="pill {PROFILE_STYLES[key]['class']}">{esc(PROFILE_STYLES[key]['label'])}</span>
                {esc(', '.join(f'{profile}: {count}' for profile, count in sorted(network_counts.items())) or 'no profile trials')}
              </p>
              <ul class="tree">{tree_html}</ul>
            </section>
            """
        )

    css = """
    body { font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 2rem; color: #111827; background: #f8fafc; }
    h1 { margin-bottom: 0.25rem; }
    .subtitle { color: #4b5563; margin-top: 0; }
    .summary-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1rem; margin: 1.5rem 0; }
    .summary-card, .network-card { background: white; border: 1px solid #e5e7eb; border-radius: 14px; padding: 1rem; box-shadow: 0 1px 3px rgba(15, 23, 42, 0.08); }
    table { border-collapse: collapse; width: 100%; }
    td, th { border-bottom: 1px solid #e5e7eb; padding: 0.45rem; text-align: left; }
    .pill { border-radius: 999px; color: white; display: inline-block; font-size: 0.8rem; font-weight: 700; padding: 0.18rem 0.55rem; }
    .profile-random > details > summary, .pill.profile-random { background: #f58518; }
    .profile-normal > details > summary, .pill.profile-normal { background: #4c78a8; }
    .profile-mixed > details > summary, .pill.profile-mixed { background: #7b61ff; }
    .profile-none > details > summary, .pill.profile-none { background: #9ca3af; }
    .network-card.profile-random { border-top: 6px solid #f58518; }
    .network-card.profile-normal { border-top: 6px solid #4c78a8; }
    .network-card.profile-mixed { border-top: 6px solid #7b61ff; }
    .network-card.profile-none { border-top: 6px solid #9ca3af; }
    .tree { list-style: none; margin: 0.75rem 0 0 0; padding-left: 1rem; border-left: 2px solid #d1d5db; }
    .tree-item { margin: 0.45rem 0; }
    .tree-item summary { color: white; border-radius: 10px; cursor: pointer; display: flex; flex-wrap: wrap; gap: 0.55rem; align-items: center; padding: 0.55rem 0.75rem; }
    .node-body { background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 0 0 10px 10px; padding: 0.75rem; }
    .trial-list { margin: 0.5rem 0 0 0; padding-left: 1.25rem; }
    .trial-list li { margin: 0.55rem 0; }
    .trial-list span { margin-right: 0.45rem; }
    .curated, small, .counts { color: #4b5563; }
    code { background: #e5e7eb; border-radius: 5px; padding: 0.1rem 0.25rem; }
    """

    html_doc = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Curated profile monitor - Gibbs bot profile simulation</title>
  <style>{css}</style>
</head>
<body>
  <h1>Curated profile monitor</h1>
  <p class="subtitle">Generated from <code>evidence/simulated_data.zip</code>. Node colors summarize participant profiles observed in finalized trials.</p>
  <div class="summary-grid">
    <div class="summary-card">
      <h2>Completed participant profile distribution</h2>
      <table><thead><tr><th>Profile</th><th>Completed participants</th></tr></thead><tbody>{distribution_html}</tbody></table>
    </div>
    <div class="summary-card">
      <h2>Legend</h2>
      <p><span class="pill profile-random">random</span> Uniform random valid RGB-channel responses.</p>
      <p><span class="pill profile-normal">normal_rgb</span> Normal RGB responses centered on the active channel, SD 20.</p>
      <p><span class="pill profile-mixed">mixed</span> Trials from both profiles appear under this node/network.</p>
      <p><span class="pill profile-none">no trials</span> No finalized profile-labeled trials.</p>
    </div>
  </div>
  {''.join(network_sections)}
</body>
</html>
"""
    OUTPUT_HTML.write_text(html_doc)
    print(OUTPUT_HTML)


if __name__ == "__main__":
    main()
