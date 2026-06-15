# Plan

## Science

This attempt will preserve PsyNet's Gibbs sampling demo as the scientific and
behavioral baseline. The original task asks participants to adjust one RGB
slider so that the resulting color matches a target word, while Gibbs sampling
uses the submitted values to grow chains across participant groups. The hybrid
extension will only vary who controls a participant session: a human, an AI bot,
or a mixture of both. It will not change the target words, RGB response format,
chain structure, performance check, or human-facing response interface except
where metadata is needed to record whether a participant was human-controlled or
AI-controlled.

The key methodological risk is that AI participants can move much faster than
humans and consume the finite Gibbs trial capacity. The design therefore treats
AI participation as an actively scheduled recruitment supplement, not as a
one-time bulk launch.

## Methods

The experiment will use the existing Gibbs demo from
`~/PsyNet/demos/experiments/gibbs` as its starting point. Human participants
will enter through the normal recruiter flow, choose participant group `A` or
`B`, read the same color-matching prompt, adjust the same slider, complete the
same repeat trials, receive the same consistency feedback, collect the same
export-test coin table entry, and provide the same end feedback.

The configured AI proportion will range from `0` to `100` percent. At `0`, no AI
sessions will be launched and the experiment should behave like the original
pure-human demo. At `100`, the scheduler will fill the participant target with
AI-controlled sessions. At intermediate values, human arrivals and AI bot
launches will be balanced incrementally so the realized participant mix
approximates the target without starving human participants of trials.

AI participants will receive task instructions that mirror the human prompt:
they will be told the target word, the current RGB vector, the active color
channel, the allowed integer range `0..255`, and the required answer format.
The prompt will not reveal network state, other participants' answers, future
targets, or implementation details that a human would not see. The same
structured stimulus object will feed both the `ColorSliderPage` display and the
AI prompt, so prompt/stimulus consistency can be tested directly.

## Implementation

The runnable attempt code will live in `code/gibbs_hybrid/` to avoid importing
from a package named `code`. I will copy the full Gibbs demo support files,
including `.gitignore`, `config.txt`, templates, and PsyNet launch files, then
pin PsyNet in `requirements.txt` to the refreshed local checkout commit and
regenerate `constraints.txt`.

Configuration will be documented in `config.txt` and read through the experiment
configuration. Planned keys are:

- `ai_participant_proportion`: integer or float percentage from `0` to `100`.
- `target_n_participants`: total desired participant sessions across humans and
  AI.
- `ai_scheduler_enabled`: opt-in scheduler switch for deployments and tests.
- `ai_scheduler_max_running_bots`: upper bound for concurrently active AI bots.
- `openrouter_api_key_env`: environment variable name containing the API key.
- `openrouter_model`: model identifier.
- `openrouter_base_url`: default `https://openrouter.ai/api/v1`.
- `openrouter_timeout_seconds`: per-request timeout.
- `openrouter_max_retries`: retry count for transient failures.
- `openrouter_mock_mode`: local deterministic mock mode for tests without real
  credentials.

Configuration validation will reject invalid proportions, missing participant
targets when the scheduler is enabled, negative concurrency limits, unsafe
timeout/retry values, and missing OpenRouter credentials when mock mode is off.
No real keys will be committed; only the environment variable name will be
stored in configuration.

The Gibbs trial implementation will be refactored around a shared stimulus
builder, for example `build_color_stimulus(trial, participant)`, returning the
target, starting RGB vector, active channel, slider bounds, and participant
group. `CustomTrial.show_trial` will use this object to render the existing
`ColorSliderPage`. The AI response path will use the same object to build an
OpenRouter request and parse the answer.

The AI response function will:

1. Render prompt messages from the shared stimulus and human-equivalent
   instructions.
2. Call OpenRouter with the configured model, base URL, timeout, and retry
   policy, unless local mock mode is enabled.
3. Parse a strict JSON response such as `{"value": 127}`.
4. Validate that the value is an integer in `0..255`.
5. Return the same scalar response format expected by `SliderControl`.
6. Store export-visible metadata for AI/mock status, model, parser result,
   latency, retry count, and prompt template version without storing secrets.

The scheduler will be an active, idempotent backend routine under `Exp`. On each
check it will count human-controlled participants, AI-controlled participants,
working AI bots, succeeded/failed totals, and remaining participant capacity.
It will launch only the number of bots needed to move the current realized
ratio toward the target, capped by remaining capacity and
`ai_scheduler_max_running_bots`. It will stop once the configured participant
target is reached or trial capacity is exhausted. Bot participants will be
marked with participant vars such as `controller = "ai"` and
`ai_profile = "openrouter"` or `"mock_openrouter"`; human participants will be
marked `controller = "human"`.

For local tests, `initialize_bot` will assign deterministic mock profiles and
participant groups when needed, while `run_bot` will preserve `bot=None`
support and delegate to `super().run_bot(...)` for framework-created bots. Any
custom scheduling tests will exercise the normal participant/bot flow rather
than mutating final trial data directly.

## Validation and evidence

Automated tests will cover:

- Pure-human setting (`ai_participant_proportion = 0`) retains the original
  Gibbs bot test expectations.
- Mixed setting launches AI bots incrementally and keeps realized proportions
  close to the target across human arrivals and bot completions.
- All-AI setting reaches the configured participant target with AI-controlled
  sessions.
- Configuration validation rejects invalid proportions, missing targets, unsafe
  API settings, and missing credentials outside mock mode.
- Human display and AI prompt are built from the same stimulus object.
- Malformed OpenRouter outputs are rejected conservatively and do not submit
  out-of-range slider values.
- Scheduler stop conditions cover exhausted trial capacity, reached participant
  target, failed bots, and existing running AI bots.

Functional validation after implementation will run `python experiment.py`,
`psynet test local`, `psynet simulate`, the executed canonical analysis notebook,
and the required performance test from the experiment directory. Evidence will
include `evidence/simulated_data.zip`, `evidence/analyses/analysis.ipynb`,
`evidence/performance.json` or a documented blocker, participant-flow
screenshots/video, a monitor snapshot, and `REPORT.md`.

No live OpenRouter calls are required for the default evidence path. If a real
key is intentionally supplied later, the evidence will label those checks
separately and will not store key material or provider logs containing secrets.

## Human review

Please review this plan before implementation. In particular, confirm whether
the configuration names and scheduler target should be participant-level, as
planned here, or whether the challenge should target an AI-human proportion over
Gibbs trials or chains instead.
