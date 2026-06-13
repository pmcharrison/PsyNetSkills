from __future__ import annotations

import argparse
from pathlib import Path

import nbformat as nbf
from nbclient import NotebookClient


def build_notebook(evidence_dir: Path, execute: bool = True) -> Path:
    analyses = evidence_dir / "analyses"
    analyses.mkdir(parents=True, exist_ok=True)
    notebook_path = analyses / "analysis.ipynb"
    nb = nbf.v4.new_notebook()
    nb.cells = [
        nbf.v4.new_markdown_cell("""# Adaptive memory testing analysis\n\nThis notebook reads the PsyNet simulated export and standalone adaptive-policy CSV evidence directly. It summarizes exported trial metadata and checks whether the adaptive policy learns sensible digit-string lengths for synthetic participants."""),
        nbf.v4.new_code_cell("""from ast import literal_eval\nfrom pathlib import Path\nfrom zipfile import ZipFile\nimport pandas as pd\nimport matplotlib.pyplot as plt\n\nevidence_dir = Path('..').resolve()\nstandalone_csv = evidence_dir / 'standalone_simulation' / 'adaptive_policy_simulation.csv'\nstandalone = pd.read_csv(standalone_csv)\nwith ZipFile(evidence_dir / 'simulated_data.zip') as zf:\n    with zf.open('regular/data/MemoryRecallTrial.csv') as f:\n        exported_trials = pd.read_csv(f)\nstandalone.head()"""),
        nbf.v4.new_code_cell("""exported_trials[['participant_id', 'trial_index', 'selected_length', 'target_string', 'raw_response', 'y', 'posterior_snapshot_id', 'acquisition_value']].head()"""),
        nbf.v4.new_code_cell("""def fit_ms(cell):\n    if isinstance(cell, str):\n        return literal_eval(cell).get('fit_posterior', 0)\n    return 0\n\nexport_summary = (exported_trials\n    .groupby('participant_id')\n    .agg(\n        n_trials=('id', 'count'),\n        mean_length=('selected_length', 'mean'),\n        accuracy=('y', 'mean'),\n        final_posterior_r=('posterior_r_mean', 'last'),\n        max_fit_ms=('timing_ms', lambda s: max(fit_ms(x) for x in s)),\n    )\n    .reset_index())\nexport_summary.head(12)"""),
        nbf.v4.new_code_cell("""summary = (\n    standalone.groupby(['adaptive', 'true_r'])\n    .agg(\n        mean_length=('selected_length', 'mean'),\n        final_posterior_r=('posterior_r_mean', 'last'),\n        mean_correct=('y', 'mean'),\n        mean_fit_ms=('fit_ms', 'mean'),\n        max_fit_ms=('fit_ms', 'max'),\n    )\n    .reset_index()\n)\nsummary"""),
        nbf.v4.new_code_cell("""fig, ax = plt.subplots(figsize=(8, 5))\nfor (true_r, adaptive), group in standalone.groupby(['true_r', 'adaptive']):\n    label = f\"r={true_r}, {'adaptive' if adaptive else 'random'}\"\n    ax.plot(group['trial_index'], group['selected_length'], marker='o', label=label)\nax.set_xlabel('Trial')\nax.set_ylabel('Selected digit-string length')\nax.set_title('Adaptive policy changes length over trials')\nax.legend(fontsize=7, ncol=2)\nfig"""),
        nbf.v4.new_code_cell("""adaptive = standalone[standalone['adaptive']]\nfig, ax = plt.subplots(figsize=(6, 5))\nscatter = ax.scatter(adaptive['true_r'], adaptive['posterior_r_mean'], c=adaptive['trial_index'], cmap='viridis')\nax.plot([0, 4], [0, 4], linestyle='--', color='black', linewidth=1)\nax.set_xlabel('True synthetic ability r')\nax.set_ylabel('Posterior mean ability r')\nax.set_title('Posterior recovery diagnostic')\nfig.colorbar(scatter, ax=ax, label='Trial index')\nfig"""),
        nbf.v4.new_markdown_cell("""## Interpretation\n\nThe PsyNet export should contain 10 finalized trials per participant with target strings, raw responses, exact-match `y`, posterior snapshot IDs, acquisition values, and timing metadata. The standalone simulation should show that selected lengths and posterior means vary with synthetic ability. Timing summaries check whether VI fitting and candidate scoring remain within the participant-response budget for this small challenge implementation."""),
    ]
    nbf.write(nb, notebook_path)
    if execute:
        client = NotebookClient(nb, timeout=240, kernel_name="python3")
        client.execute(cwd=str(analyses))
        nbf.write(nb, notebook_path)
    return notebook_path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-dir", default="../../../evidence")
    parser.add_argument("--no-execute", action="store_true")
    args = parser.parse_args()
    print(build_notebook(Path(args.evidence_dir).resolve(), execute=not args.no_execute))


if __name__ == "__main__":
    main()
