from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from single_chord_emotion_replication.analysis import main as run_analysis
from single_chord_emotion_replication.questionnaires import score_omsi
from single_chord_emotion_replication.simulate_data import main as simulate_data
from single_chord_emotion_replication.synthesize_stimuli import CHORD_SPECS, TIMBRE_SPECS, main as synthesize_stimuli


def test_stimulus_manifest_contains_all_reconstructed_stimuli(tmp_path: Path):
    synthesize_stimuli(tmp_path)
    manifest = json.loads((tmp_path / 'generated_stimuli' / 'stimulus_manifest.json').read_text(encoding='ascii'))
    assert len(manifest) == len(CHORD_SPECS) * len(TIMBRE_SPECS)
    assert {item['timbre'] for item in manifest} == {'piano', 'strings'}
    assert all((tmp_path / item['audio_path']).exists() for item in manifest)


def test_omsi_scoring_respects_musician_thresholds():
    novice = score_omsi(
        {
            'omsi_age': 30,
            'omsi_age_started': 0,
            'omsi_private_lessons_years': 0,
            'omsi_regular_practice_years': 0,
            'omsi_current_practice_amount': 'rarely_or_never',
            'omsi_college_coursework': 'none',
            'omsi_composition_experience': 'never',
            'omsi_concert_attendance': 'none',
            'omsi_self_title': 'nonmusician',
        }
    )
    musician = score_omsi(
        {
            'omsi_age': 32,
            'omsi_age_started': 6,
            'omsi_private_lessons_years': 14,
            'omsi_regular_practice_years': 16,
            'omsi_current_practice_amount': 'more_than_two_hours_per_day',
            'omsi_college_coursework': 'graduate_level',
            'omsi_composition_experience': 'performed_for_regional_or_national_audience',
            'omsi_concert_attendance': 'thirteen_or_more',
            'omsi_self_title': 'professional_musician',
        }
    )
    assert novice['score'] < 250
    assert musician['score'] >= 750


def test_simulation_and_analysis_pipeline(tmp_path: Path):
    simulated_dir = simulate_data(tmp_path / 'simulated', n_participants=24, seed=5)
    output_dir = run_analysis(simulated_dir, tmp_path / 'analysis')
    report = json.loads((output_dir / 'analysis_summary.json').read_text(encoding='ascii'))
    assert report['n_participants'] == 24
    family_rows = pd.DataFrame(report['summary_by_family'])
    assert family_rows.shape[0] == 7
    major_valence = float(family_rows.loc[family_rows['family'] == 'major_triad', 'valence'].iloc[0])
    diminished_valence = float(family_rows.loc[family_rows['family'] == 'diminished_triad', 'valence'].iloc[0])
    strings_nostalgia = next(row['nostalgia_longing'] for row in report['summary_by_timbre'] if row['timbre'] == 'strings')
    piano_nostalgia = next(row['nostalgia_longing'] for row in report['summary_by_timbre'] if row['timbre'] == 'piano')
    assert major_valence > diminished_valence
    assert strings_nostalgia > piano_nostalgia
