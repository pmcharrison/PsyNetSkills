# LLM-assisted participation defense kit report

## Implemented PsyNet experiment

The experiment is a compact text-heavy PsyNet study. Participants first see a clear instruction page prohibiting AI assistance, browser agents, search engines, and external writing tools. They then acknowledge the instruction on a saved PsyNet page before completing three open-text passage tasks, one attention check, one comprehension check, and three open-text probe questions.

The task is only a local quality-review demonstration. It uses neutral passages about community planning, libraries, and campus bike racks. The final page reminds participants that the collected signals support manual review only.

## AI-use instruction and disclosure component

The participant-facing instruction states that answers should be written without AI assistance or external writing tools. The acknowledgement page saves the selected acknowledgement in the participant variable `ai_use_acknowledgement`. The final probe asks participants to disclose AI assistants, browser agents, search engines, or external writing aids.

## Telemetry fields

The `TelemetryTextControl` browser template records these fields directly in `metadata.telemetry` for each open-text page:

- `page_load_time`, `trial_start_time`, `submission_time`, and `response_latency_ms`;
- `focus_events` and `focus_event_count` from browser focus and blur listeners;
- `visibility_events` and `visibility_event_count` from `document.visibilitychange`;
- `paste_events` and `paste_count` from textarea paste events, including pasted text length but not pasted content;
- `keydown_count`, `edit_count`, and `text_growth` samples from textarea keydown/input events; and
- trial identifiers, trial type, and stimulus identifiers.

PsyNet bots cannot generate browser DOM events. Bot metadata and `simulate_export.py` therefore use explicitly labeled local fixtures with `source: synthetic_bot` or `source: local_simulation`. These fixtures are for testing review logic and do not replace browser-recorded telemetry.

## Simulated participant profiles

`simulate_export.py` creates six transparent local profiles:

- `attentive_human_like`: careful answers, checks passed, no paste or focus events;
- `inattentive`: focus/visibility changes and failed attention check;
- `paste_heavy`: repeated paste events with otherwise coherent responses;
- `fast_low_effort`: very short answers and very low response latencies;
- `mock_llm_assisted`: polished generic wording plus explicit AI-use disclosure;
- `browser_agent_like`: near-zero keydown telemetry and automation-like probe language.

The generated `participants.json` and `responses.jsonl` preserve participant IDs, profile labels, page/trial labels, stimulus metadata, answer objects, check outcomes, and telemetry metadata in a PsyNet-like export shape.

## Manual-review flagging rules

`review_participants.py` reads either an export directory or zipped export and produces JSON, CSV, and Markdown outputs. It flags participants for manual review when it sees one or more of these review-worthy signals:

- failed attention or comprehension checks;
- two or more very short response latencies below 3500 ms;
- total paste count of at least two;
- sparse text-production telemetry for nontrivial text;
- missing telemetry fields; or
- probe wording that merits inspection.

The script never rejects participants automatically and never labels someone as definitively using AI.

## Threat taxonomy

| Threat category | In-study PsyNet signals | What the kit can establish | What it cannot establish |
| --- | --- | --- | --- |
| Attentive human-like participation | Passed checks, plausible latency, ordinary typing, no unusual probes | No obvious local review signal in this fixture | It cannot prove the participant is honest or high quality |
| Inattentive or low-effort participation | Failed checks, short text, distractor focus events, very short latencies | A response set needs human inspection for quality | It cannot prove intent or platform fraud |
| AI-assisted participation by verified human | Disclosure probe, paste events, polished/generic responses, sparse typing | Possible AI-assistance concern worth review | It cannot prove LLM use without external evidence or disclosure |
| Browser automation or browser-agent participation | Very low latency, zero or sparse keydown counts, automation-like probe text | Browser behavior is unusual for a typing task | It cannot prove which tool or script was used |
| Platform or account fraud | Not directly observable in this PsyNet study | The kit can preserve in-study signals for later review | It cannot verify identity, payment, recruitment-account abuse, VPN/proxy behavior, or account sharing |

## PsyNet-native versus platform-level defenses

This kit operates inside the PsyNet study: participant instructions, page responses, trial metadata, telemetry metadata, check outcomes, and local review outputs. Platform-level defenses require recruitment or payment platform controls such as identity checks, account-history review, payment verification, device fingerprinting policies, and fraud-team investigations. The report and review output intentionally avoid claiming that client-side telemetry proves AI use, automation, or platform fraud.
