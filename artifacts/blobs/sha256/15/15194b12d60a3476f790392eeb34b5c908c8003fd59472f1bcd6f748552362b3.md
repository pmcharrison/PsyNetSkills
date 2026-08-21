# Collaborative SVG vibe coding attempt

This PsyNet experiment implements a compact local demonstration of the collaborative SVG vibe-coding paradigm from Hu et al. (2026).

## What the demo covers

- Three instructor iterations for one human-led cat chain.
- The first iteration starts with no SVG; the second shows the first SVG as the current best; the third adds a selector comparison between previous and newly generated SVGs.
- Deterministic mock SVG generation behind a `SVGGeneratorClient` interface.
- Saved role-configuration summaries for human-led, AI-led, and hybrid chains.
- A separate similarity-rating page that hides condition labels and prompt/model metadata from the evaluator.

## Running locally

```bash
python experiment.py
psynet test local
psynet debug local
```

`SVG_GENERATOR_PROVIDER=mock` is the default and needs no credentials. Real provider mode is intentionally a placeholder; add a private client outside this repository and provide credentials only through the environment if a future study deliberately enables it.
