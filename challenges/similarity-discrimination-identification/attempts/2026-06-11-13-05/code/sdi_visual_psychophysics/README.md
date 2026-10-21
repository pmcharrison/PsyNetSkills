# Similarity, discrimination, and identification

This PsyNet experiment studies relationships between color similarity ratings,
same-different discrimination, and multi-item identification confusions.

## Design

- Six filled circles vary primarily in color. Each stimulus also stores `size_px`
  so the manifest can be extended to size or other dimensions.
- Each task trial starts with a 500 ms fixation frame. The initial fixation is
  removed before stimulus presentation.
- Stimulus presentation lasts 750 ms. Memory delays last 500 ms.
- The same-different and similarity blocks present all unordered pairs including
  identical pairs.
- The identification block crosses set sizes 3, 4, and 5 with probe-present and
  probe-absent lure trials over rotated displays.
- The Ishihara color-vision task is administered as a non-excluding end measure,
  followed by PsyNet's `BasicDemography` module.

## Review profile

The default `canonical` profile runs the full design. Set
`PSYNET_PROFILE=minimal` for visual evidence: it keeps three representative
trials per main block, includes set sizes 3, 4, and 5, and shortens the Ishihara
image timeout while leaving the canonical experiment unchanged.

## Commands

- `python experiment.py` prints node counts and timing constants.
- `psynet test local` runs PsyNet's local bot test.
- `python analysis.py --output ../../evidence/analysis_simulated` writes
  documented simulated analysis outputs.
