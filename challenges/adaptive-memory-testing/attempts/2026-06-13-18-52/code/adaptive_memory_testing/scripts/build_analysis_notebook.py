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
        nbf.v4.new_code_cell("""from ast import literal_eval\nfrom pathlib import Path\nfrom zipfile import ZipFile\nimport pandas as pd\nimport matplotlib.pyplot as plt\n\nplt.rcParams['figure.dpi'] = 70\nevidence_dir = Path('..').resolve()\nstandalone_csv = evidence_dir / 'standalone_simulation' / 'adaptive_policy_simulation.csv'\nstandalone = pd.read_csv(standalone_csv)\nhmc = pd.read_csv(evidence_dir / 'standalone_simulation' / 'hmc_accuracy_comparison.csv')\nwith ZipFile(evidence_dir / 'simulated_data.zip') as zf:\n    with zf.open('regular/data/MemoryRecallTrial.csv') as f:\n        exported_trials = pd.read_csv(f)\nstandalone.head()"""),
        nbf.v4.new_code_cell("""exported_trials[['participant_id', 'trial_index', 'selected_length', 'target_string', 'raw_response', 'y', 'posterior_snapshot_id', 'acquisition_value']].head()"""),
        nbf.v4.new_code_cell("""def fit_ms(cell):\n    if isinstance(cell, str):\n        return literal_eval(cell).get('fit_posterior', 0)\n    return 0\n\nexport_summary = (exported_trials\n    .groupby('participant_id')\n    .agg(\n        n_trials=('id', 'count'),\n        mean_length=('selected_length', 'mean'),\n        accuracy=('y', 'mean'),\n        final_posterior_r=('posterior_r_mean', 'last'),\n        max_fit_ms=('timing_ms', lambda s: max(fit_ms(x) for x in s)),\n    )\n    .reset_index())\nexport_summary.head(12)"""),
        nbf.v4.new_code_cell("""summary = (\n    standalone.groupby(['adaptive', 'true_r'])\n    .agg(\n        mean_length=('selected_length', 'mean'),\n        final_posterior_r=('posterior_r_mean', 'last'),\n        mean_correct=('y', 'mean'),\n        mean_fit_ms=('fit_ms', 'mean'),\n        max_fit_ms=('fit_ms', 'max'),\n    )\n    .reset_index()\n)\nsummary"""),
        nbf.v4.new_code_cell("""hmc_summary = (hmc\n    .groupby('adaptive')\n    .agg(\n        n_participants=('participant_key', 'count'),\n        mean_absolute_error=('absolute_error', 'mean'),\n        rmse=('squared_error', lambda x: (x.mean()) ** 0.5),\n    )\n    .reset_index())\nhmc_summary"""),
        nbf.v4.new_code_cell("""plot_df = standalone.copy()\nplot_df['ability_bin'] = pd.cut(plot_df['true_r'], bins=[0, 0.75, 1.5, 2.25, 4.0], labels=['low', 'mid-low', 'mid-high', 'high'])\ntraj = plot_df.groupby(['adaptive', 'ability_bin', 'trial_index'], observed=True)['selected_length'].mean().reset_index()\nfig, ax = plt.subplots(figsize=(5, 3))\nfor (adaptive, ability_bin), group in traj.groupby(['adaptive', 'ability_bin'], observed=True):\n    if adaptive:\n        ax.plot(group['trial_index'], group['selected_length'], marker='o', label=str(ability_bin))\nax.set_xlabel('Trial')\nax.set_ylabel('Mean selected length')\nax.set_title('Adaptive length by ability bin')\nax.legend(fontsize=7)\nplt.show()"""),
        nbf.v4.new_code_cell("""fig, ax = plt.subplots(figsize=(4.5, 3.5))\nfor adaptive, group in hmc.groupby('adaptive'):\n    label = 'adaptive' if adaptive else 'random'\n    ax.scatter(group['true_r'], group['hmc_r_mean'], label=label, alpha=0.8, s=18)\nax.plot([0, 4], [0, 4], linestyle='--', color='black', linewidth=1)\nax.set_xlabel('True r')\nax.set_ylabel('HMC mean r')\nax.set_title('HMC recovery')\nax.legend(fontsize=7)\nplt.show()"""),
        nbf.v4.new_markdown_cell("""## Interpretation\n\nThe PsyNet export should contain 10 finalized trials per participant with target strings, raw responses, exact-match `y`, posterior snapshot IDs, acquisition values, and timing metadata. The standalone simulation contains 30 adaptive and 30 non-adaptive participants, and the HMC table compares participant ability-estimate accuracy between the two conditions. Timing summaries check whether VI fitting and candidate scoring remain within the participant-response budget for this challenge implementation."""),
    ]
    nbf.write(nb, notebook_path)
    if execute:
        client = NotebookClient(nb, timeout=240, kernel_name="python3")
        client.execute(cwd=str(analyses))
        for cell in nb.cells:
            for output in cell.get("outputs", []):
                data = output.get("data")
                if isinstance(data, dict) and len(data) > 1:
                    data.pop("text/plain", None)
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
