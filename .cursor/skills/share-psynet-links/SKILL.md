---
name: share-psynet-links
description: Format and share PsyNetSkills dashboard, PsyNet experiment, and backup preview links for user review.
authors: [pmcharrison]
---

# Share PsyNet links

Use this skill when handing the user live or backup review links for
PsyNetSkills dashboard pages, challenge attempt pages, or PsyNet experiment
participant/dashboard pages.

This skill owns link presentation only. Caller skills still own starting local
servers, creating tunnels, deriving experiment URLs, and checking that links
work.

## Related skills

- Use `public-tunnel` to expose an already-running local dashboard or experiment
  server through a temporary public URL.
- Use `dashboard-preview-links` only when a caller needs to derive or verify the
  publication status of durable GitHub Pages previews for pull requests.
- Use caller skills such as `preview-dashboard-live`, `run-attempt`, or
  `psynet-experiment-implementation` to decide which links exist for the current
  workflow.

## Format

Use Markdown links, omit unavailable links, and choose concise labels that match
the target page. The first dashboard link can point to any relevant dashboard
page or section, not just an attempt plan.

**Links**

- [Dashboard]({live-dashboard-url})
- [Experiment participant link]({participant-url})
- [Experiment dashboard]({dashboard-url-with-credentials})

*These temporary links will fail once the agent goes to sleep. In that case, you
can ask for new links, or use the [backup dashboard preview (will take a few
minutes to build)]({pr-preview-url}).*

If no durable backup preview exists, end the italic sentence after "ask for new
links." If the main dashboard target is more specific, replace `Dashboard` with
the most useful label, such as `Attempt`, `Plan`, `Evidence`, `Report`, or
`Dashboard home`.

## Rules

- Do not show local `127.0.0.1` links to users unless the caller skill explicitly
  says they are useful in the current environment.
- Do not wait for dashboard preview builds just to format links. If a
  deterministic backup preview URL is already known, include it immediately.
- Do not invent links. Only share links created or derived by the caller skill.
- Include experiment dashboard credentials only when they are local, ephemeral
  PsyNet/Dallinger debug credentials.
- Do not include real service credentials or production deployment links.
