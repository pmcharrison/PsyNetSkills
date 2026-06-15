# Learnings

## Gibbs demo capacity for larger bot runs

The original Gibbs demo settings did not provide enough available color trials for 10 bots to each complete four normal Gibbs trials plus three repeat trials. Increasing `trials_per_node` preserved the task structure while giving the required 10-bot simulation enough network capacity.

*Actions:*

- **PsyNetSkills:** Challenge guidance for adapting capacity-limited demos should tell agents to check whether original trial-maker settings support the requested simulated participant count before interpreting shortened bot flows as profile failures. Confidence: high. Impact: medium. Status: considering.

## Notebook tooling is separate from the PsyNet editable install

The PsyNet virtual environment did not include `nbformat` before analysis generation. Installing the documented notebook packages allowed the canonical notebook to be created and executed.

*Actions:*

- **PsyNetSkills:** Keep the experiment evidence checklist's explicit `uv pip install matplotlib jupyter nbconvert nbformat ipykernel` step; it prevented a stuck analysis workflow after the missing `nbformat` error. Confidence: high. Impact: low. Status: completed.
