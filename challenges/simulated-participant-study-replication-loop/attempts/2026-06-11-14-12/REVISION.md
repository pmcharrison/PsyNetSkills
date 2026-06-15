# Documented revision

## Observed initial failure mode

The initial simulated run reproduced the preregistered interference problem. The
`mock_llm_memory_limited` profile selected recent-target lures on 10 of 12
interference trials and reached only 0.167 interference accuracy. The
`semantic_bias` profile also made semantic-lure errors on 10 of 12 interference
trials.

## Revision

The revised simulation strategy added an explicit warning to the prompt-style
task representation: "Remember: recent words from other pairs can be traps." The
study structure, stimulus manifest, response options, and PsyNet experiment code
were otherwise kept stable so the rerun tests the effect of clearer memory
instructions rather than a changed scientific task.

## Rerun outcome

After the revision, the `mock_llm_memory_limited` profile selected recent-target
lures on 3 of 12 interference trials and reached 0.750 interference accuracy.
This addressed the concrete failure mode while preserving distinct profile
behavior: the semantic-bias profile still produced semantic-lure errors, and the
PsyNet bot rule profile remained at ceiling.
