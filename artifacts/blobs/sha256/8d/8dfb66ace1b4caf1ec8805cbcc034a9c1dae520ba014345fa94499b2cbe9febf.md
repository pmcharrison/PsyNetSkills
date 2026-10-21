# Open-ended STEP tagging experiment

This PsyNet experiment implements an open-ended STEP tagging task for
cross-cultural music-emotion research. Participants listen to 15-second clips,
add native-language single-word emotion tags, rate tags from previous
participants, and flag invalid tags.

## Local setup

From this directory:

1. Generate the synthetic demo stimuli:
   `python scripts/generate_demo_stimuli.py`
2. Install dependencies in the PsyNet environment:
   `uv pip install -r requirements.txt`
3. Generate constraints if needed:
   `dallinger constraints generate`
4. Run functional validation:
   `psynet test local`
5. Run a local debug server:
   `psynet debug local`

## Stimulus replacement

The demo uses `data/stimuli.csv`, which has `clip_id`, `culture`, `audio_path`,
and `description` columns. Replace this CSV and the files under `data/audio/`
with real 15-second excerpts for a full study. Set `TARGET_CULTURE` to choose
the target country for deterministic culture-balanced sampling. When the
manifest has more than 15 clips, the experiment selects approximately half of
the participant workload from the target culture and balances the rest across
the other cultures.

## STEP data

The STEP package persists a candidate list per stimulus. Each candidate stores:

- tag text;
- previous ratings, where `0` records a participant flag;
- whether the tag is currently flagged;
- whether the tag is frozen/completed;
- whether the tag was newly submitted on a trial.

Rejected new tags are also stored in each trial's `rejected_new_tags` variable.
After exporting PsyNet data, run
`python scripts/summarize_step_export.py ../../evidence/data.zip ../../evidence/analyses/step_summary.json`
to summarize candidate ratings and flags for review.

This attempt implements the STEP elicitation phase only. Tag cleaning,
emotionality validation, and dense emotion ratings are downstream stages.
