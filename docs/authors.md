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

Skills and challenges reference author keys in YAML frontmatter:

```yaml
authors: [pmcharrison]
```

Attempts reference the same keys in `agent.json`:

```json
{
  "authors": ["pmcharrison"]
}
```

Cursor, model, client, and runtime metadata are provenance, not authorship, and
should stay in their existing metadata fields.

## Agent workflow

When creating a skill, challenge, or attempt, use the `identify-author` skill to
identify the human author before writing the metadata:

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
