---
title: Gibbs bot profile simulation
type: experiment implementation
difficulty: 6
authors: [zeroada]
---

Adapt PsyNet's Gibbs sampling demo so that local simulated participants can be
assigned to distinct response profiles and the resulting behavior can be tested
and reported.

Start from the original PsyNet Gibbs demo at
`~/PsyNet/demos/experiments/gibbs`. The implemented experiment should preserve
the scientific task: participants are shown a target word, see an RGB color
state, and adjust the active color channel while the other RGB channels remain
fixed for that Gibbs trial. Human-facing instructions, trial structure, Gibbs
networks, nodes, and participant groups should remain recognizable unless a
change is needed to support simulation, profile assignment, or validation.

## Simulated participant profiles

Implement two bot response profiles for the color-response trials:

- `random`: an inattentive or task-agnostic profile that returns uniformly
  random valid RGB-channel values. Its responses should cover the allowed range
  from `0` to `255` without depending on the presented target word or current
  RGB state.
- `normal_rgb`: a locally stochastic profile that samples responses from a
  normal distribution over the RGB space presented on the current trial. For a
  Gibbs trial where only one channel is active, the bot may sample a full RGB
  vector around the displayed starting vector and return the active channel, or
  equivalently sample the active channel from a normal distribution centered on
  the presented active-channel value. Responses must be rounded or converted to
  the format expected by the trial and clipped to the valid range `0` to `255`.

The bot response logic should be connected through PsyNet's `bot_response`
mechanism for the relevant control or page, so simulated participants submit
answers in the same format as ordinary participants. Avoid bypassing trial
validation or writing answers directly to exported data.

Record the assigned profile in export-visible metadata, such as
`participant.var.bot_profile` and trial-level metadata or answer data. The
export should make it possible to connect every simulated color response to the
profile that produced it, the participant id, the target word, the active color
channel, the starting RGB vector, and the submitted RGB-channel response.

## Profile assignment and scheduling

Implement a scheduling or assignment algorithm for a test run with exactly
`10` simulated participants. The run should contain:

- `5` participants assigned to the `random` profile;
- `5` participants assigned to the `normal_rgb` profile.

The assignment order should be randomized for each run or for each configured
random seed, rather than assigning the first five participants to one profile
and the last five to the other. Once a participant receives a profile, that
profile should remain stable for all of the participant's trials and repeated
trials. The profile assignment should not be inferred from the participant's
numeric id alone unless the id is first mapped through a shuffled balanced
profile roster.

Keep the existing Gibbs participant-group behavior separate from the simulated
response profile. A participant's Gibbs group, network selection, and target
word scheduling should continue to follow the original demo's intent unless the
attempt explicitly documents a justified change.

## Testing and analysis

Configure the local test phase to run exactly `10` bots. Add automated checks
that verify:

- all `10` bots complete the expected Gibbs trial flow;
- exactly `5` completed participants have profile `random`;
- exactly `5` completed participants have profile `normal_rgb`;
- each participant keeps the same profile across all color trials;
- all submitted color-channel responses are valid integers in the inclusive
  range `0` to `255`;
- profile metadata is present in the exported or export-ready data.

The testing phase should report the actual participant behavior profile
distribution observed in the run. The report may be printed by the automated
test, written to an evidence file, or summarized in a short analysis script, but
it must include the observed count for each profile and enough context for a
reviewer to see that the counts came from the completed simulated participants.

Include a lightweight behavioral comparison between the profiles. For example,
summarize the response range or variance for the `random` profile and compare
it with the distance of `normal_rgb` responses from the presented RGB state. The
analysis is a simulation sanity check, not evidence about real human behavior.

## Deliverables

Include the following materials in the attempt:

- adapted runnable PsyNet experiment code based on the Gibbs demo;
- bot response functions for the `random` and `normal_rgb` profiles;
- the balanced randomized profile-assignment algorithm;
- tests or simulation checks for the exact `5`/`5` participant distribution;
- a reported actual profile distribution from a local `10`-bot run;
- exported or export-ready evidence containing participant profile metadata and
  color responses;
- a concise explanation of how the implementation preserves the original Gibbs
  sampling task while adding simulated participant behavior;
- implementation provenance in `agent.json`, a concise event timeline in
  `TIMELINE.md`, and reusable lessons in `LEARNINGS.md`.
