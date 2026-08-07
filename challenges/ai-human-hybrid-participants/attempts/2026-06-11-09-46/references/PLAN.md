# Experiment plan: AI and hybrid human-AI Gibbs participants

## Science

- Required: canonical reference (citation + URL or `references/` path): No published canonical reference beyond the public challenge and PsyNet Gibbs demo. Implementation baseline is `~/PsyNet/demos/experiments/gibbs` at PsyNet commit `d84382b300c4d4cc8a0b0648428152e0740ab7d2`; copied challenge notes live in `challenge/references/implementation-notes.md`.
- Required: research question: Can the original Gibbs color-slider task run with pure human, pure AI, and mixed human-AI participants without changing the human task?
- Required: construct: Iterated Gibbs sampling over color associations for target words, with AI participation treated as an implementation condition rather than a new psychological construct.
- Required: hypotheses or expected patterns: Technical demonstration; pure-human configuration should match the original demo, while mixed and all-AI configurations should complete the same trials and save responses in the same format.
- Required: conditions / independent variables: Internal AI proportion from 0 to 100 percent; participant-facing condition labels remain unchanged except for existing participant group A/B display.
- Required: dependent variables: Slider responses for red/green/blue Gibbs dimensions, response metadata, participant group, trial/node/network state, AI prompt metadata, and scheduler launch decisions.
- Required: stimulus domain and source: Original Gibbs demo targets (`tree`, `rock`, `carrot`, `banana`) and RGB slider values; no new stimuli.
- Required: participant population: Local human/debug participants and local bot/AI participants; bots are validation tools unless a real OpenRouter key is intentionally supplied at runtime.
- Required: interpretation boundary: Local mocked AI runs validate implementation behavior only; they do not support claims about real model behavior or human-AI scientific differences.
- Required: minimal analysis: Verify participant counts by AI/human role, config validation, prompt-stimulus parity, completed trial counts, exported data presence, and performance-test health.
- Required: purpose (demo / pilot / formal experiment): Proof-of-concept implementation challenge.
- Optional: sample-size rationale: Use small local tests and the original demo bot count for functional checks; performance evidence uses the repository standard load-test command where feasible.
- Optional: adaptive / group / AI logic: Active scheduler compares completed/launched AI count and human count against the target proportion, launching only enough AI bots to restore the configured mixture.
- Optional: ethical or domain constraints: No real credentials are committed; OpenRouter key is read only from the configured environment variable.
- Negotiation points: A production study would need human approval of the exact AI model, temperature, retry policy, and whether AI data is pooled or analyzed separately.
- Out of scope: Scientific comparison of humans and AI, production recruitment, real credential verification, and changing the Gibbs sampling paradigm.

## Design

- Required: participant journey (consent -> questionnaire -> prescreens -> instructions -> comprehension check -> practice -> main trials -> debrief -> reward summary -> completion; mark omitted stages as out of scope): Preserve the original Gibbs journey: ad/consent handled by PsyNet, choose participant group, complete Gibbs color-slider trials, collect demo coin/export row, complete experiment feedback, and exit. Questionnaires, prescreens, comprehension checks, and practice are out of scope because the baseline demo omits them.
- Required: trial experience: Humans see the original target-word prompt, participant group heading, color square, and one active RGB slider per Gibbs step.
- Required: response modality: Human response is the original slider control; AI response is a validated integer 0-255 submitted through the same bot page path.
- Required: timing, progress bar, and replay rules: Preserve original time estimates and progress behavior; no replay or custom timing is added.
- Required: assignment and counterbalancing: Preserve original group A/B button choice and Gibbs trial maker balancing; AI role assignment is internal metadata and does not alter target/group selection.
- Required: quality controls: Config validation for proportion and API settings; prompt/response validation for model output; local mocked API path for tests.
- Required: participant-visible feedback, scoring, and reward display: Preserve original consistency score feedback and PsyNet reward footer behavior.
- Required: completion states: Preserve original success/failure behavior; malformed AI output fails conservatively into local mock fallback or raises a validation error in tests.
- Optional: visual direction: No visual changes beyond preserving the copied color-slider template.
- Optional: audio/media direction: Not applicable.
- Optional: practice/training: Out of scope.
- Optional: participant evidence profile: Record a concise local participant flow showing group selection, representative color-slider trials, and completion.
- Optional: accessibility needs: Preserve baseline browser accessibility; no extra translation or keyboard work.
- Negotiation points: Production deployments should decide whether participants are told about AI participants; the challenge requires internal hybrid support, not disclosure UI.
- Out of scope: New frontend design, additional surveys, and participant-facing AI disclosure copy.

## Implementation oversight

- Required: PsyNet version and base demo: PsyNet `13.3.0a0`, source commit `d84382b300c4d4cc8a0b0648428152e0740ab7d2`, base demo `~/PsyNet/demos/experiments/gibbs`.
- Required: experiment architecture: Gibbs trial maker plus AI/hybrid scheduling and bot-response extension.
- Required: core PsyNet mapping: Keep `CustomNode`, `CustomTrial`, `CustomTrialMaker`, `ColorSliderPage`, and `Timeline`; add config registration, shared stimulus helpers, OpenRouter client wrapper, AI bot response, and scheduler helpers.
- Required: configuration strategy: Document and register `ai_participant_proportion`, `ai_total_participant_target`, `openrouter_api_key_env_var`, `openrouter_model`, `openrouter_base_url`, `openrouter_timeout_seconds`, `openrouter_max_retries`, and `openrouter_mock_mode`.
- Required: stimulus and asset pipeline: Use the original target/context and current RGB vector; no external assets.
- Required: data schema: Save role metadata on participants, AI prompt/model metadata in bot responses, scheduler counts in experiment vars, and original response/trial data unchanged.
- Required: bot and simulation path: Pure-human tests use original random slider bots; AI tests use mocked OpenRouter output and active launch decisions; `run_bot(bot=None, ...)` remains supported for performance tests.
- Required: testing plan: Run helper unit tests for config/scheduling/prompt parsing, then `python experiment.py`, `psynet test local`, performance test JSON/log, export, and participant recording when local services allow.
- Required: deployment plan: Local-only challenge attempt; no live deployment or real credentials.
- Required: evidence and review artifacts: `participant.mp4`, performance JSON/log, monitor snapshot, data export, and command logs or blockers in `evidence/`.
- Optional: custom frontend justification: None; baseline PsyNet template is reused.
- Optional: external API integration: OpenRouter wrapper supports live calls only when a key is supplied through the configured environment variable; tests use mocks.
- Optional: performance envelope: Target standard challenge load test; scheduler should avoid bulk-launching all AI participants at once.
- Optional: export customization: Preserve default export plus metadata fields; add a small analysis summary if useful.
- Optional: translation/localization plan: Out of scope.
- Optional: operations constraints: Do not store API keys; do not claim real OpenRouter verification unless run with safe credentials.
- Negotiation points: Production AI model choice and disclosure policy need human review.
- Out of scope: Real OpenRouter credential setup, production deployment, and changes to PsyNet core.
