# Authors

PsyNetSkills uses a central author registry for public attribution. Author keys
are canonical GitHub usernames without `@`.

## Registry

Author records live in `authors.yaml`:

```yaml
pmcharrison: Peter Harrison
```

Each key is a GitHub username without `@`. Each value is the author's full
display name. Profile links are derived from the GitHub key.

## References

Challenges and attempts reference author keys:

```yaml
# challenges/<slug>/INSTRUCTIONS.md frontmatter
authors: [pmcharrison]
```

```json
// attempts/<timestamp>/agent.json
{
  "authors": ["pmcharrison"]
}
```

Agent Skills in `.cursor/skills/` do **not** carry `authors` metadata. Skill
history is tracked in git.

Cursor, model, client, and runtime metadata are provenance, not authorship, and
should stay in their existing metadata fields.

## Agent workflow

When creating a challenge or attempt, use the `identify-author` skill to
identify the human author before writing metadata:

1. Read `authors.yaml`.
2. Ask which GitHub username should be credited as author.
3. If the username exists, reference that key.
4. If the username is missing, ask whether to register a new author.
5. For a new author, ask for their full display name, then add the record to
   `authors.yaml`.

Suggested prompt:

> Who should be credited as author? Please provide a GitHub username. Existing
> authors include `pmcharrison`. If this is a new author, please also provide a
> full display name.
