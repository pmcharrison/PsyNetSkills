# Report

## Summary

This attempt implements a simple PsyNet experiment in which participants rate the pleasantness of the primary colors red, green, and blue on a 1 to 7 scale. The experiment uses a static trial maker with explicit block ordering so every participant sees red first, green second, and blue third.

## Implementation

The runnable experiment lives in `code/primary_color_rating/`. It defines three static nodes, one for each color, and a `ColorRatingTrial` that renders a large color swatch with a `RatingControl(values=7)`. A custom `ColorRatingTrialMaker` overrides block ordering to preserve the requested red, green, blue sequence. The bot check verifies that each bot completes exactly one trial for each color, in the correct order, and that all ratings are integers between 1 and 7.

## Simulation

I ran `psynet simulate` after setting `Exp.test_n_bots = 24`, producing a simulated export in `evidence/simulated_data.zip`. This simulation completed 24 participants, each with three completed color-rating trials. The simulation uses deterministic bot responses, so it is best understood as a pipeline and data-integrity check rather than a model of human color preference.

## Analysis

The canonical dashboard-rendered analysis notebook is `evidence/analyses/analysis.ipynb`, with the runnable script in `evidence/analyses/summarize_ratings.py`. The analysis reads the simulated trial export, verifies that each simulated participant has exactly one rating for red, green, and blue, and writes:

- `rating_summary.csv`
- `rating_summary.json`
- `rating_means.svg`

The simulated ratings match the configured bot responses:

| Color | N | Mean | Median | Min | Max |
| --- | ---: | ---: | ---: | ---: | ---: |
| Red | 24 | 5.0 | 5.0 | 5 | 5 |
| Green | 24 | 6.0 | 6.0 | 6 | 6 |
| Blue | 24 | 4.0 | 4.0 | 4 | 4 |

The Friedman test over the deterministic within-participant ratings returned chi-square = 48.0 with df = 2. Because the bot responses are deterministic, this inferential statistic only confirms that the analysis pipeline detects the known ordering of the simulated ratings.

## Validation and evidence

Functional validation used `python experiment.py`, `psynet test local`, and a Playwright participant-flow test. The Playwright evidence captures the ad/start page, welcome page, red/green/blue trials, and thank-you page. A video review confirmed that the final participant recording shows the correct trial order, visible 1-7 rating controls, and a Next button that clears the reward footer.

Additional evidence includes:

- `evidence/participant.mp4`
- `evidence/screenshots/`
- `evidence/performance.json`
- `evidence/data.zip`
- `evidence/simulated_data.zip`
- `evidence/monitor.html`

The 40-bot performance test completed successfully with zero request or bot errors during the run.
