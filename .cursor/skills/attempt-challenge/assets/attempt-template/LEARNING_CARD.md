# Learning card template

```markdown
## Short descriptive title

What happened during implementation or testing.

*Actions:*

- **PsyNetSkills:** A repo, skill, docs, validation, dashboard, or evidence workflow change. Confidence: high. Impact: medium. Status: considering.
- **PsyNet:** A PsyNet framework, documentation, or command-line change. Confidence: medium. Impact: low. Status: considering.
```

Generate action bullets with:

```bash
uv run psynetsk-learning-action \
  --repository PsyNetSkills \
  --proposal "A standalone action another agent can execute" \
  --confidence high \
  --impact medium
```
