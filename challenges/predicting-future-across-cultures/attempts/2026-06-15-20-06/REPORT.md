# Report

## Implementation

The attempt implements a runnable PsyNet experiment in `code/predicting_future_across_cultures/`. The experiment uses a static trial maker with five category blocks, sampling one `t_past` value per category for each participant. The participant flow includes a concise translated instruction page, five numeric prediction trials, validation that rejects non-numeric or below-`t_past` predictions, and a debrief page.

The participant-facing text is marked for PsyNet internationalization and has complete Italian (`it`) and Hebrew (`he`) locale files. Hebrew pages set right-to-left direction for experiment-owned content. The active locale can be selected with `PSYNET_LOCALE=en`, `PSYNET_LOCALE=it`, or `PSYNET_LOCALE=he`.

## Simulation and analysis

Bots return finite predictions that are always at least `t_past`. Locale-specific bot profiles inject modest test differences by category: Italian bots predict slightly longer marriage and waiting durations, while Hebrew bots predict slightly longer life spans and movie run times and slightly shorter poem lengths.

Simulations were run separately for English, Italian, and Hebrew, then copied into `evidence/simulated_exports/` and zipped as `evidence/simulated_data.zip`. The executed notebook `evidence/analyses/analysis.ipynb` reads the exported `PredictionTrial.csv` files directly, validates the locale/category coverage, summarizes trial counts, and plots finite predicted `t_total` against `t_past` in a category-by-language grid.

The simulated patterns are workflow evidence only. They show that the experiment and analysis can represent condition-by-language variation; they do not estimate real cross-cultural differences.

## Validation

- `python experiment.py` passed.
- `psynet translate it he --translator null` passed and found no missing new text after manual `.po` completion.
- `PSYNET_LOCALE=en psynet test local` passed.
- `PSYNET_LOCALE=it psynet test local` passed.
- `PSYNET_LOCALE=he psynet test local` passed.
- `psynet performance-test local --n-bots 40 --duration-minutes 5 --time-factor 1.0` completed with 0 bot errors and wrote `evidence/performance.json`.
- `psynet simulate` completed for `en`, `it`, and `he`.
- Playwright participant-flow evidence passed for all three locales; Hebrew video evidence is saved as `evidence/participant.mp4`.

## Evidence

- `evidence/screenshots/` contains localized instruction, trial, validation, and debrief screenshots for English, Italian, and Hebrew.
- `evidence/participant.mp4` shows a short Hebrew participant walkthrough with RTL presentation and validation.
- `evidence/monitor.html` contains an authenticated local PsyNet dashboard snapshot.
- `evidence/performance.json` contains sustained load-test metrics.
- `evidence/simulated_data.zip` contains the combined simulated export.
- `evidence/analyses/analysis.ipynb` contains the executed analysis.

## Limitations

The Italian and Hebrew translations were written manually for challenge evidence and should receive native-speaker review before real deployment. Bot-generated differences are intentionally artificial and should not be interpreted as human cultural effects.
