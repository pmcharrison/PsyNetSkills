---
name: cloud-agent-links
description: Share links to help the user review generated content.
authors: [pmcharrison]
---

# Cloud agent links

Use this skill to share links to help the user review generated content.

## Link format

Write generated URLs as ordinary Markdown text so they are clickable; do not put
them in fenced code blocks or inline code.

## Approach

We take two complementary approaches to sharing content with the user:

1. Tunnels from a local development server
2. Uploads to GitHub Pages

The tunnel approach is best for immediate interaction, but it may expire when the agent goes to sleep.
The GitHub Pages approach is persistent, but takes a few minutes to build.

## Content

It's standard to share the following:

1. The current build of the repo's dashboard
2. (If relevant) The current build of the current experiment.

When we share an experiment build, we typically share both
a participant link (which allows the user to take the experiment) and a dashboard link (which allows the user to view the experiment's progress).

The tunnel approach supports both 1 and 2, but the GitHub Pages approach only supports 1.

## Deriving links

To obtain tunnel links, use the `prepare-dashboard-tunnel` and `prepare-experiment-tunnel` skills.

To obtain GitHub Pages links, use the `dashboard-preview-links` skill.

## Sharing links

Links should be shared in the concise format described below.
Use Markdown links, omit unavailable links, and choose concise labels that match
the target page. The first dashboard link can point to any relevant dashboard
page or section, not just an attempt plan.

### Exact format to use

**Links**

- [Dashboard]({dashboard-tunnel-url})
- [Experiment participant link]({experiment-tunnel-participant-url})
- [Experiment dashboard]({experiment-tunnel-dashboard-url-with-credentials})

*These temporary links will fail once the agent goes to sleep. In that case, you
can ask for new links, or use the [backup dashboard preview (will take a few
minutes to build)]({pr-preview-url}).*
