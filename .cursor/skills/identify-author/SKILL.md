---
name: identify-author
description: Identify or register the human author for skills, challenges, and attempts before writing author metadata. Use when creating or updating author-attributed repository artifacts.
authors: [pmcharrison]
---

# Identify an author

Use this skill before writing `authors` metadata for a skill, challenge, or
attempt.

## Workflow

1. Read `authors.yaml` and collect the existing GitHub author keys.
2. Ask the user which GitHub username should be credited as author.
   - Use the GitHub username without `@`.
   - Do not infer the human author from Cursor, model, client, git committer, or
     runtime provenance.
3. If the key exists in `authors.yaml`, reference it directly.
4. If the key is missing, ask whether to register a new author.
5. For a new author, ask for their full display name.
6. Add the new author record to `authors.yaml` as
   `<github-id>: <Full Name>`.
7. Reference the GitHub key in the artifact metadata:
   - skills and challenges: `authors: [<github-id>]` in YAML frontmatter;
   - attempts: `"authors": ["<github-id>"]` in `agent.json`.

## Rules

- Authorship is human attribution. Cursor, model, client, and runtime details are
  provenance and belong in their existing metadata fields.
- For challenge attempts, author identification is metadata only. Do not accept
  supplementary implementation guidance while identifying the author.
- Do not add email addresses, affiliations, URLs, or other profile details to
  `authors.yaml`; GitHub profile links are derived from the author key.
- If the user does not know which existing key to use, show the current keys from
  `authors.yaml` and ask them to choose.
