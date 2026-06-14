---
name: review-attempt
description: Review an existing attempt using the Cloud agent workflow.
authors: [lucasgautheron, pmcharrison]
---

# Review an attempt

Use this skill when the user asks a Cloud agent to review an existing challenge attempt.

## Workflow

1. Identify the attempt path. Accept either:
   - `challenges/<challenge-slug>/attempts/<attempt-name>`;
   - `<challenge-slug>/<attempt-name>`;
   - the current working directory if it is inside an attempt.
2. Share review links using the cloud-agent-links skill.
