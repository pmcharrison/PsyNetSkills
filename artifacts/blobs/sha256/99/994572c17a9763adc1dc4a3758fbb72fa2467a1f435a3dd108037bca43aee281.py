"""Validate simulated PsyNet export data for the tapping challenge."""

from __future__ import annotations

import ast
import csv
import json
import tempfile
import zipfile
from pathlib import Path

ATTEMPT_DIR = Path(__file__).resolve().parent.parent
EXPORT_ZIP = ATTEMPT_DIR / 'evidence' / 'simulated_data.zip'
MANIFEST = ATTEMPT_DIR / 'code' / 'tapping_rhythm_experiment' / 'stimuli' / 'manifest.json'
REQUIRED_PROFILES = {'good', 'too-few-taps', 'off-tempo', 'noisy', 'dropout'}


def rows_by_file(export_zip: Path):
    with tempfile.TemporaryDirectory() as tmp:
        with zipfile.ZipFile(export_zip) as zf:
            zf.extractall(tmp)
        root = Path(tmp)
        csvs = {str(p.relative_to(root)): p for p in root.rglob('*.csv')}
        return {name: list(csv.DictReader(path.open(newline='', encoding='utf-8'))) for name, path in csvs.items()}


def parse_answer(value):
    if value in (None, ''):
        return None
    for parser in (json.loads, ast.literal_eval):
        try:
            return parser(value)
        except Exception:
            pass
    raise AssertionError(f'Could not parse trial answer: {value[:80]!r}')


def main() -> int:
    assert EXPORT_ZIP.exists(), f'Missing export zip: {EXPORT_ZIP}'
    manifest_ids = {row['stimulus_id'] for row in json.loads(MANIFEST.read_text(encoding='utf-8'))['stimuli']}
    tables = rows_by_file(EXPORT_ZIP)
    participant_rows = tables.get('regular/data/Bot.csv') or tables.get('anonymous/data/Bot.csv')
    trial_rows = tables.get('regular/data/TappingTrial.csv') or tables.get('anonymous/data/TappingTrial.csv')
    assert participant_rows, 'participant rows exist'
    assert trial_rows, 'trial rows exist'
    participant_profiles = {row.get('simulated_profile_id') for row in participant_rows}
    missing_participant_profiles = REQUIRED_PROFILES - participant_profiles
    assert not missing_participant_profiles, (
        f'missing simulated profiles in participant metadata: {sorted(missing_participant_profiles)}'
    )

    answers = [parse_answer(row.get('answer')) for row in trial_rows if row.get('answer')]
    tapping_answers = [answer for answer in answers if isinstance(answer, dict) and answer.get('trial_kind') in {'calibration', 'main'}]
    assert tapping_answers, 'tapping trial answers exist'

    profiles = {answer.get('simulated_profile_id') for answer in tapping_answers}
    missing_profiles = REQUIRED_PROFILES - profiles
    assert not missing_profiles, f'missing simulated profiles in trial metadata: {sorted(missing_profiles)}'

    calibration = [answer for answer in tapping_answers if answer['trial_kind'] == 'calibration']
    main_trials = [answer for answer in tapping_answers if answer['trial_kind'] == 'main']
    assert calibration, 'calibration trial rows exist'
    assert main_trials, 'main tapping trial rows exist'
    assert all(answer['stimulus_id'] in manifest_ids for answer in tapping_answers), 'stimulus ids match manifest'
    assert all(isinstance(answer['tap_onsets'], list) for answer in tapping_answers), 'tap onset fields are parseable lists'
    assert all('calibration_status' in answer for answer in tapping_answers), 'calibration status field is present'
    assert any(answer['calibration_status'] == 'passed' for answer in calibration), 'at least one profile passes calibration'
    failed = [answer for answer in calibration if answer['failed']]
    assert failed, 'failed calibration profiles are present'
    assert all(answer['failure_reason'] for answer in failed), 'failed profiles have failure reasons'
    dropout = [answer for answer in calibration if answer['simulated_profile_id'] == 'dropout']
    assert dropout and dropout[0]['dropout'] and dropout[0]['failure_reason'] == 'dropout_no_taps', 'dropout is distinguishable'

    print(json.dumps({
        'participant_rows': len(participant_rows),
        'trial_rows': len(trial_rows),
        'tapping_trial_answers': len(tapping_answers),
        'profiles': sorted(profiles),
        'manifest_ids': sorted(manifest_ids),
        'failed_calibration_reasons': sorted({answer['failure_reason'] for answer in failed}),
    }, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
