---
name: prepare-experiment-tunnel
description: Start a live PsyNet experiment preview and expose it through a temporary public tunnel for user review.
authors: [pmcharrison]
---

# Prepare experiment tunnel

Use this skill to obtain temporary public participant and dashboard links for a
running local PsyNet experiment.

## Workflow

1. Start the experiment with the relevant caller skill, usually `run-attempt`.
2. Follow the `public-tunnel` skill for port `5000`.
3. Derive the public participant and dashboard/develop links:
   - the public participant link is the public tunnel origin with `/ad?generate_tokens=true&recruiter=hotair` appended
   - the public dashboard link is the public tunnel origin with `/dashboard/develop` appended and local debug credentials embedded, for example `https://<username>:<password>@<host>/dashboard/develop`
