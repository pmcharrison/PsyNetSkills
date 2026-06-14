# Cross-cultural decision-making study

This PsyNet experiment asks participants to choose between two side-by-side
options on each trial. Each option contains a variable number of features, with
values from 0 to 100 and validities from 0 to 1.

The source locale is English. The experiment is prepared for English, Hindi, and
French participant flows with `supported_locales = ["en", "hi", "fr"]` in
`config.txt`.

Useful commands from this directory:

- `python experiment.py`
- `psynet translate hi fr`
- `psynet test local`
- `psynet simulate --n-bots 12`
