# Visual priors serial reproduction

This PsyNet experiment recreates the participant-facing core of Langlois,
Jacoby, Suchow, and Griffiths (2017), "Uncovering visual priors in spatial
memory using serial reproduction."

## Participant flow

1. Participants read brief instructions.
2. A practice trial shows a dot inside a circle for 4000 ms, waits 1000 ms, then
   asks the participant to reproduce the dot location.
3. The main task uses PsyNet across-participant chains. Each trial shows a dot
   inside one geometric outline for 1000 ms, waits 1000 ms, then asks the
   participant to place the dot from memory.
4. Participants can click repeatedly to reposition the response dot and then
   confirm.
5. Trial feedback is green "This was accurate." or red "This was not accurate."
   using the paper's 8% width/height tolerance rule.
6. Accurate responses become the next generation's stimulus in the chain.
   Inaccurate responses are retained in the data but the previous stimulus is
   carried forward instead of propagating the inaccurate response.

## Stimuli

The implemented Experiment 1 shapes are circle, equilateral triangle, square,
vertical oval, horizontal oval, and regular pentagon. Shapes are drawn on a
520 x 520 px canvas with a 400 x 400 px shape coordinate system, 6 px black
outline, white fill, and randomized display offset.

By default the experiment uses two seeds per shape so local tests run quickly.
Set `VISUAL_PRIORS_FULL_STUDY=1` to generate the paper-scale seed set: 400
circle seeds and 500 seeds for each other Experiment 1 shape. The chain length
is 10 generations in both modes.

## Data fields

Each chain trial answer records shape, seed id, generation, stimulus
coordinates, response coordinates, canvas coordinates, display offset, response
time, x/y errors, accuracy, and whether the response propagated.

## Running

```bash
cd challenges/visual-priors-serial-reproduction/attempts/2026-06-10-12-35/code/visual_priors_serial_reproduction
source ~/PsyNet/.venv/bin/activate
uv pip install -r constraints.txt
psynet test local
```

For a browser run:

```bash
psynet debug local
```

For the full seed scale:

```bash
VISUAL_PRIORS_FULL_STUDY=1 psynet test local
```

## Analysis

The `scripts/simulate_and_analyze.py` script generates simulated chain data,
plots final-generation response clouds, computes a Gaussian-kernel density on a
grid, and reports Jensen-Shannon divergence between successive generations. It
does not require live participant data.
