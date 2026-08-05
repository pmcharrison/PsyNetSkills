# Cross-cultural decision-making study

This PsyNet experiment asks participants to choose between two side-by-side
options on each trial. Every option contains the same five-feature set
(quality, cost saving, community benefit, time saving, and safety), with values
from 0 to 100 and validities from 0 to 1.

The source locale is English. The experiment is prepared for English, Hindi, and
French participant flows with `supported_locales = ["en", "hi", "fr"]` in
`config.txt`.

Useful commands from this directory:

- `python experiment.py`
- `psynet translate hi fr`
- `psynet test local`
- `psynet simulate --n-bots 12`
