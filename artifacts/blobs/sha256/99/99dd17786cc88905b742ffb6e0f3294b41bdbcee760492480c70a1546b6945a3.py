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

COLORS = ["red", "green", "blue"]
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
        "behavior": "Contains finalized trials from both simulated response profiles.",
    },
    "none": {
        "label": "no trials",
        "class": "profile-none",
        "color": "#9ca3af",
        "behavior": "No finalized profile-labeled trials are attached.",
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


def pill(profile: str) -> str:
    style = PROFILE_STYLES.get(profile, PROFILE_STYLES["none"])
    return f"<span class='profile-pill {style['class']}'>{esc(style['label'])}</span>"


def starting_active_channel(row: pd.Series):
    vector = parse_jsonish(row["initial_vector"], [])
    active_index = int(row["active_index"])
    return vector[active_index] if vector else ""


def trial_detail_html(row: pd.Series) -> str:
    profile = row["bot_profile"]
    style = PROFILE_STYLES.get(profile, PROFILE_STYLES["none"])
    starting = parse_jsonish(row["initial_vector"], [])
    updated = parse_jsonish(row["updated_vector"], [])
    answer = int(row["answer"])
    start_value = starting_active_channel(row)
    distance = abs(answer - start_value) if start_value != "" else ""
    repeat = "repeat" if bool(row["is_repeat_trial"]) else "main"
    return f"""
      <div class="curated-card">
        <h5>Trial {int(row['id'])}: participant {int(row['participant_id'])}</h5>
        <table class="table table-sm curated-table">
          <tr><th>Profile</th><td>{pill(profile)} {esc(style['behavior'])}</td></tr>
          <tr><th>Target</th><td>{esc(row['target'])}</td></tr>
          <tr><th>Active channel</th><td>{esc(row['active_color'])} (index {int(row['active_index'])})</td></tr>
          <tr><th>Starting RGB</th><td><code>{esc(starting)}</code></td></tr>
          <tr><th>Submitted response</th><td><strong>{answer}</strong></td></tr>
          <tr><th>Updated RGB</th><td><code>{esc(updated)}</code></td></tr>
          <tr><th>|response - start|</th><td>{esc(distance)}</td></tr>
          <tr><th>Trial type</th><td>{repeat}</td></tr>
        </table>
      </div>
    """


def node_detail_html(node: pd.Series, node_trials: pd.DataFrame) -> str:
    context = parse_jsonish(node["context"], {})
    definition = parse_jsonish(node["definition"], {})
    counts = Counter(node_trials["bot_profile"].dropna())
    key = profile_key(counts)
    active_index = definition.get("active_index", "")
    active_color = COLORS[active_index] if active_index in [0, 1, 2] else ""
    count_label = ", ".join(f"{profile}: {count}" for profile, count in sorted(counts.items())) or "no profile trials"
    trial_rows = "".join(trial_detail_html(row) for _, row in node_trials.sort_values("id").iterrows())
    if not trial_rows:
        trial_rows = "<p><em>No finalized trials are attached to this node.</em></p>"
    return f"""
      <h4>Node {int(node['id'])}</h4>
      <table class="table table-sm curated-table">
        <tr><th>Profile summary</th><td>{pill(key)} {esc(count_label)}</td></tr>
        <tr><th>Behavior summary</th><td>{esc(PROFILE_STYLES[key]['behavior'])}</td></tr>
        <tr><th>Target</th><td>{esc(context.get('target', ''))}</td></tr>
        <tr><th>Participant group</th><td>{esc(node['participant_group'])}</td></tr>
        <tr><th>Degree</th><td>{int(node['degree'])}</td></tr>
        <tr><th>Active channel</th><td>{esc(active_color)}</td></tr>
        <tr><th>Summarized trial IDs</th><td>{esc(parse_jsonish(node.get('summarize_trials_used'), []))}</td></tr>
        <tr><th>Summarized output</th><td>{esc(node.get('summarize_trials_output', ''))}</td></tr>
      </table>
      <details open>
        <summary>Trials: participant ID, response, profile behavior</summary>
        {trial_rows}
      </details>
    """


def network_detail_html(network: pd.Series, network_trials: pd.DataFrame) -> str:
    context = parse_jsonish(network["context"], {})
    counts = Counter(network_trials["bot_profile"].dropna())
    key = profile_key(counts)
    count_label = ", ".join(f"{profile}: {count}" for profile, count in sorted(counts.items())) or "no profile trials"
    return f"""
      <h4>Network {int(network['id'])}</h4>
      <table class="table table-sm curated-table">
        <tr><th>Profile summary</th><td>{pill(key)} {esc(count_label)}</td></tr>
        <tr><th>Behavior summary</th><td>{esc(PROFILE_STYLES[key]['behavior'])}</td></tr>
        <tr><th>Target</th><td>{esc(context.get('target', ''))}</td></tr>
        <tr><th>Participant group</th><td>{esc(network['participant_group'])}</td></tr>
        <tr><th>Completed trials</th><td>{int(len(network_trials))}</td></tr>
        <tr><th>Trials per node</th><td>{int(network['trials_per_node'])}</td></tr>
      </table>
    """


def details_accordion(networks: pd.DataFrame, nodes: pd.DataFrame, trials: pd.DataFrame) -> str:
    sections = []
    for _, network in networks.sort_values("id").iterrows():
        network_trials = trials[trials["network_id"] == network["id"]]
        node_sections = []
        network_nodes = nodes[nodes["network_id"] == network["id"]].sort_values(["degree", "id"])
        for _, node in network_nodes.iterrows():
            node_trials = trials[trials["node_id"] == node["id"]]
            node_sections.append(
                f"""
                <details>
                  <summary>Node {int(node['id'])}: node/trial summary</summary>
                  {node_detail_html(node, node_trials)}
                </details>
                """
            )
        sections.append(
            f"""
            <details class="network-expander">
              <summary>Network {int(network['id'])}: node tree and trials</summary>
              {network_detail_html(network, network_trials)}
              {''.join(node_sections)}
            </details>
            """
        )
    return "".join(sections)


def make_graph_data(networks: pd.DataFrame, nodes: pd.DataFrame, trials: pd.DataFrame):
    graph_nodes = [
        {
            "id": "experiment",
            "label": "Experiment",
            "shape": "box",
            "level": 0,
            "color": {"background": "#198754", "border": "#0f5132"},
            "font": {"color": "white"},
            "detailId": "experiment",
        },
        {
            "id": "role-default",
            "label": "default networks",
            "shape": "box",
            "level": 1,
            "color": {"background": "#0d6efd", "border": "#084298"},
            "font": {"color": "white"},
            "detailId": "role-default",
        },
    ]
    graph_edges = [{"from": "experiment", "to": "role-default", "color": "#111827"}]
    details = {
        "experiment": "<h4>Experiment</h4><p>Gibbs demo simulation export with curated profile-aware monitor data.</p>",
        "role-default": "<h4>default networks</h4><p>All Gibbs networks in this attempt use the original default role.</p>",
    }

    for _, network in networks.sort_values("id").iterrows():
        network_id = f"network-{int(network['id'])}"
        network_trials = trials[trials["network_id"] == network["id"]]
        key = profile_key(Counter(network_trials["bot_profile"].dropna()))
        context = parse_jsonish(network["context"], {})
        graph_nodes.append(
            {
                "id": network_id,
                "label": f"network:{int(network['id'])}\\n{context.get('target', '')}/{network['participant_group']}",
                "shape": "box",
                "level": 2,
                "color": {"background": PROFILE_STYLES[key]["color"], "border": "#111827"},
                "font": {"color": "white"},
                "detailId": network_id,
            }
        )
        graph_edges.append({"from": "role-default", "to": network_id, "color": "#111827"})
        details[network_id] = network_detail_html(network, network_trials)

    for _, node in nodes.sort_values(["network_id", "degree", "id"]).iterrows():
        node_id = f"node-{int(node['id'])}"
        node_trials = trials[trials["node_id"] == node["id"]]
        key = profile_key(Counter(node_trials["bot_profile"].dropna()))
        context = parse_jsonish(node["context"], {})
        label_prefix = "source" if "source" in str(node["type"]).lower() else "node"
        graph_nodes.append(
            {
                "id": node_id,
                "label": f"{label_prefix}:{int(node['id'])}\\n{context.get('target', '')}",
                "shape": "dot" if label_prefix == "node" else "diamond",
                "level": 3 + int(node["degree"]),
                "color": {"background": PROFILE_STYLES[key]["color"], "border": "#111827"},
                "font": {"color": "#111827"},
                "detailId": node_id,
            }
        )
        parent_id = node.get("parent_id")
        graph_edges.append(
            {
                "from": f"node-{int(parent_id)}" if pd.notna(parent_id) else f"network-{int(node['network_id'])}",
                "to": node_id,
                "arrows": "to",
                "color": "#374151",
            }
        )
        details[node_id] = node_detail_html(node, node_trials)

    for _, trial in trials.sort_values(["node_id", "id"]).iterrows():
        profile = trial["bot_profile"]
        trial_id = f"trial-{int(trial['id'])}"
        graph_nodes.append(
            {
                "id": trial_id,
                "label": f"trial:{int(trial['id'])}\\nP{int(trial['participant_id'])}: {int(trial['answer'])}",
                "shape": "ellipse",
                "level": 5 + int(trial.get("repeat_trial_index", 0) if pd.notna(trial.get("repeat_trial_index", 0)) else 0),
                "color": {"background": PROFILE_STYLES[profile]["color"], "border": "#111827"},
                "font": {"color": "white"},
                "detailId": trial_id,
            }
        )
        graph_edges.append(
            {
                "from": f"node-{int(trial['node_id'])}",
                "to": trial_id,
                "dashes": bool(trial["is_repeat_trial"]),
                "arrows": "to",
                "color": PROFILE_STYLES[profile]["color"],
            }
        )
        details[trial_id] = trial_detail_html(trial)

    return graph_nodes, graph_edges, details


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
        f"<tr><td>{pill(profile)}</td><td>{int(count)}</td></tr>"
        for profile, count in distribution.items()
    )
    graph_nodes, graph_edges, details = make_graph_data(networks, nodes, trials)
    accordion = details_accordion(networks, nodes, trials)

    network_checkboxes = "".join(
        f"""
        <div class="field p-1">
          <input class="network-input" id="val-{int(row['id'])}" type="checkbox" value="{int(row['id'])}" checked />
          <label for="val-{int(row['id'])}">{int(row['id'])}</label>
        </div>
        """
        for _, row in networks.sort_values("id").iterrows()
    )

    css = """
    body { background: #fff; }
    #monitor-wrapper { gap: 1rem; }
    #mynetwork { height: 720px; border: 1px solid #dee2e6; border-radius: .25rem; background: #f8f9fa; margin-bottom: 1rem; }
    #details-pane { border: 1px solid #dee2e6; border-radius: .25rem; padding: 1rem; margin-bottom: 1rem; background: #fff; }
    #element-details { display: block; }
    .profile-pill { border-radius: 999px; color: white; display: inline-block; font-size: .78rem; font-weight: 700; padding: .12rem .5rem; }
    .profile-random { background: #f58518; }
    .profile-normal { background: #4c78a8; }
    .profile-mixed { background: #7b61ff; }
    .profile-none { background: #9ca3af; }
    .curated-table th { width: 12rem; color: #495057; }
    .curated-card { border-left: 5px solid #dee2e6; padding: .75rem 1rem; margin: .75rem 0; background: #f8f9fa; }
    .network-expander { border: 1px solid #dee2e6; border-radius: .25rem; margin: .5rem 0; padding: .5rem .75rem; background: #fff; }
    details summary { cursor: pointer; font-weight: 600; }
    aside#sidebar { width: 320px; min-width: 280px; }
    .sidebar-pane { border: 1px solid #dee2e6; border-radius: .25rem; margin-bottom: 1rem; padding: .75rem; background: #f8f9fa; }
    .legend-row { display: flex; align-items: center; gap: .5rem; margin: .35rem 0; }
    code { background: #e9ecef; border-radius: .2rem; padding: .1rem .25rem; }
    """
    js = f"""
    const graphNodes = {json.dumps(graph_nodes)};
    const graphEdges = {json.dumps(graph_edges)};
    const curatedDetails = {json.dumps(details)};
    let network = null;

    function selectedNetworkIds() {{
      return Array.from(document.querySelectorAll('.network-input:checked')).map(el => el.value);
    }}

    function showDetail(nodeId, data) {{
      const node = data.nodes.get(nodeId);
      if (!node) return;
      document.getElementById('element-details').innerHTML = curatedDetails[node.detailId] || '<p>No curated detail available.</p>';
    }}

    function drawNetwork() {{
      const selected = selectedNetworkIds();
      const search = document.getElementById('search').value.toLowerCase();
      const visibleNodes = graphNodes.filter(node => {{
        const text = JSON.stringify(node).toLowerCase();
        if (node.id.startsWith('network-')) return selected.includes(node.id.replace('network-', '')) && text.includes(search);
        if (node.id.startsWith('node-') || node.id.startsWith('trial-')) {{
          const linkedEdges = graphEdges.filter(edge => edge.to === node.id || edge.from === node.id);
          const linkedNetwork = linkedEdges.some(edge => selected.some(id => JSON.stringify(edge).includes('network-' + id)));
          return search === '' || text.includes(search) || linkedNetwork;
        }}
        return true;
      }});
      const visibleIds = new Set(visibleNodes.map(node => node.id));
      const visibleEdges = graphEdges.filter(edge => visibleIds.has(edge.from) && visibleIds.has(edge.to));
      const data = {{nodes: new vis.DataSet(visibleNodes), edges: new vis.DataSet(visibleEdges)}};
      const options = {{
        layout: {{hierarchical: {{direction: 'UD', sortMethod: 'directed', nodeSpacing: 180, treeSpacing: 220}}}},
        interaction: {{dragNodes: false, hover: true}},
        physics: {{enabled: false}},
        edges: {{width: 2, smooth: {{type: 'cubicBezier', forceDirection: 'vertical', roundness: 0.35}}}},
      }};
      if (network) network.destroy();
      network = new vis.Network(document.getElementById('mynetwork'), data, options);
      network.on('select', params => {{
        if (params.nodes.length > 0) showDetail(params.nodes[0], data);
      }});
      network.on('click', params => {{
        if (params.nodes.length > 0) showDetail(params.nodes[0], data);
      }});
      if (visibleNodes.length > 2) showDetail(visibleNodes[2].id, data);
    }}

    window.addEventListener('load', drawNetwork);
    """

    html_doc = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
  <title>Experiment Monitoring - Curated Profile Dashboard</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@4.6.2/dist/css/bootstrap.min.css">
  <link href="https://unpkg.com/vis-network@9.1.9/styles/vis-network.min.css" rel="stylesheet">
  <style>{css}</style>
</head>
<body>
  <div class="container">
    <nav id="dashboard-navigation">
      <ul class="nav nav-tabs">
        <li class="nav-item"><a class="nav-link" href="#">Config</a></li>
        <li class="nav-item"><a class="nav-link" href="#">Deployments</a></li>
        <li class="nav-item dropdown">
          <a class="nav-link dropdown-toggle active" data-toggle="dropdown" href="#">Monitor</a>
          <div class="dropdown-menu show position-static d-inline-block">
            <a class="dropdown-item active" href="#">Monitoring</a>
            <a class="dropdown-item" href="#">Timeline</a>
            <a class="dropdown-item" href="#">Resources</a>
            <a class="dropdown-item" href="#">Participants</a>
          </div>
        </li>
        <li class="nav-item"><a class="nav-link" href="#">Basic data</a></li>
        <li class="nav-item"><a class="nav-link" href="#">Export</a></li>
      </ul>
    </nav>
    <h1>Experiment Monitoring</h1>
    <p>This static monitor was generated from <code>evidence/simulated_data.zip</code>. It keeps the PsyNet monitor structure but colors nodes/trials by simulated participant profile and replaces raw JSON details with curated summaries.</p>
    <div id="monitor-wrapper" class="d-flex justify-content-between align-items-stretch">
      <main class="flex-fill">
        <div class="d-flex flex-wrap">
          <div class="form-group mr-3">
            <label for="sortBy">Sort networks by</label>
            <select class="form-control" id="sortBy" onchange="drawNetwork()">
              <option value="network_id">Network ID</option>
              <option value="n_completed_infos">Number of completed infos</option>
              <option value="n_alive_nodes">Number of completed nodes</option>
            </select>
          </div>
          <div class="form-group mr-3">
            <label for="max-networks">Number of networks</label>
            <input type="number" min="1" class="form-control" id="max-networks" placeholder="Networks to print">
          </div>
          <div class="form-group">
            <label for="search">Freetext search</label>
            <input type="text" class="form-control" id="search" placeholder="Search networks" oninput="drawNetwork()">
          </div>
        </div>
        <div class="collapse show p-3 bg-light" id="statistics">
          <h4>Statistics</h4>
          <div class="row">
            <div class="col"><div class="card"><div class="card-body"><h5 class="card-title">Participants</h5><p class="card-text">{len(completed)} completed</p></div></div></div>
            <div class="col"><div class="card"><div class="card-body"><h5 class="card-title">Networks</h5><p class="card-text">{len(networks)} total, 0 failed</p></div></div></div>
            <div class="col"><div class="card"><div class="card-body"><h5 class="card-title">Nodes</h5><p class="card-text">{len(nodes)} total, 0 failed</p></div></div></div>
            <div class="col"><div class="card"><div class="card-body"><h5 class="card-title">Trials</h5><p class="card-text">{len(trials)} finalized</p></div></div></div>
          </div>
        </div>
        <div class="collapse show p-3 bg-light" id="advanced-filter">
          <h4>Advanced Filter</h4>
          <fieldset id="network-ids"><h5>Network IDs</h5>{network_checkboxes}</fieldset>
          <button class="btn btn-primary btn-sm" onclick="drawNetwork()">Apply filters</button>
        </div>
        <section id="mynetwork"></section>
        <section id="details-pane">
          <h2>Details</h2>
          <div id="element-details"><p>Select a network, node, or trial in the graph to see curated information.</p></div>
        </section>
        <section id="curated-accordion">
          <h2>Expandable node and trial summaries</h2>
          {accordion}
        </section>
      </main>
      <aside id="sidebar">
        <div class="sidebar-pane">
          <h2>Profile distribution</h2>
          <table class="table table-sm"><thead><tr><th>Profile</th><th>Completed participants</th></tr></thead><tbody>{distribution_html}</tbody></table>
        </div>
        <div class="sidebar-pane">
          <h2>Legend</h2>
          <div class="legend-row">{pill('random')} <span>Uniform random RGB-channel responses.</span></div>
          <div class="legend-row">{pill('normal_rgb')} <span>Normal RGB responses centered on the active channel.</span></div>
          <div class="legend-row">{pill('mixed')} <span>Mixed profile evidence under this element.</span></div>
          <div class="legend-row">{pill('none')} <span>No finalized profile-labeled trials.</span></div>
        </div>
      </aside>
    </div>
  </div>
  <script src="https://unpkg.com/vis-network@9.1.9/standalone/umd/vis-network.min.js"></script>
  <script>{js}</script>
</body>
</html>
"""
    OUTPUT_HTML.write_text(html_doc)
    print(OUTPUT_HTML)


if __name__ == "__main__":
    main()
