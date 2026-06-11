# Open-ended STEP tagging demo

This PsyNet experiment collects open-ended emotion tags for short local audio clips.
It is prepared for `psynet translate`: participant-facing strings in
`experiment.py` use PsyNet's `get_translator()` helper, and `config.txt` sets
`locale = en` with `supported_locales = ["en"]`. Add target locales after
generating the corresponding `.po` files.

## Run locally

From this directory, with the PsyNet virtual environment active:

1. Regenerate demo audio if needed:
   `python scripts/generate_demo_stimuli.py`
2. Check that the manifest loads:
   `python experiment.py`
3. Extract or update a target translation:
   `psynet translate de`
4. Run the functional test:
   `psynet test local`

The committed demo audio is synthetic and 15 seconds long. Replace it with real
15-second study excerpts before running a real study.

## Cint/Lucid readiness

`experiment.py` includes Cint/Lucid recruiter settings and a class-level
`Exp.config` with `locale`, `wage_per_hour`, `publish_experiment`, and
`recruiter_settings`. Because real deployment targets have not been chosen yet,
the current Lucid config path points to
`qualifications/lucid/mock-lucid-ENG-US.json`, which is only for local import and
test checks. To run local tests without Lucid credentials, set
`PSYNET_CINT_LOCAL_MOCK=1`; real Cint deployments should leave that variable
unset and provide real Lucid credentials through the deployment environment.

To prepare real Cint qualifications:

1. Choose deployment language-country pairs.
2. Verify each Lucid tag pair with `psynet lucid locale`.
3. Verify `locales/<locale>/LC_MESSAGES/experiment.po` exists for each target.
4. Update `create_qualifications.py` by uncommenting only requested
   `country_language_tags` and qualification filters.
5. Run `python create_qualifications.py`.
6. Update `LANGUAGE`, `COUNTRY`, `LUCID_CONFIG_PATH`, `locale`, and
   `wage_per_hour` in `experiment.py` for the active deployment target.

The mock Lucid file is not deployable.

## Replacing stimuli

Edit `data/stimuli.csv` and put the corresponding `.wav` files under
`data/audio/`. Each row needs:

- `stimulus_id`: stable clip identifier;
- `culture`: culture or country label used as the PsyNet block;
- `description`: analyst-facing description;
- `audio_path`: path relative to this experiment directory.

The demo has six clips, so each participant sees all six. For a larger study
manifest, set `expected_trials_per_participant` and `max_trials_per_participant`
to `15` in `experiment.py` to use the requested default subset size.

## Saved data

Each completed trial stores a structured answer with:

- `stimulus_id` and `culture`;
- `iteration`, computed from prior completed trials for the stimulus;
- `new_tags`, normalized participant-submitted tags;
- `ratings`, mapping existing tags to 1-5 applicability ratings;
- `flags`, listing existing tags marked for review;
- `existing_tags_seen`, the tag pool shown on that trial.

These answers are enough to reconstruct a weighted bag of words per clip. A
later cleaning stage can average ratings by tag, down-weight or exclude flagged
tags, and keep native-language tags for language-specific review.
