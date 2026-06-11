(function () {
  const form = document.getElementById("challenge-builder-form");
  const status = document.getElementById("builder-status");
  const titleInput = document.getElementById("challenge-title");
  const slugInput = document.getElementById("challenge-slug");
  const typeInput = document.getElementById("challenge-type");
  const difficultyInput = document.getElementById("challenge-difficulty");
  const authorsInput = document.getElementById("challenge-authors");
  const instructionsInput = document.getElementById("challenge-instructions");
  const criteriaInput = document.getElementById("challenge-criteria");
  const criteriaOutput = document.getElementById("criteria-output");

  const previews = {
    instructions: document.getElementById("instructions-preview"),
    criteria: document.getElementById("criteria-preview"),
    gitkeep: document.getElementById("gitkeep-preview"),
  };

  const paths = {
    instructions: document.getElementById("instructions-path"),
    criteria: document.getElementById("criteria-path"),
    gitkeep: document.getElementById("gitkeep-path"),
  };

  let slugWasEdited = false;

  function slugify(value) {
    return value
      .toLowerCase()
      .trim()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "")
      .replace(/-{2,}/g, "-");
  }

  function yamlString(value) {
    return JSON.stringify(value.trim());
  }

  function authorList(value) {
    return value
      .split(/[,\s]+/)
      .map((author) => author.trim().replace(/^@/, ""))
      .filter(Boolean);
  }

  function normalizeBody(value) {
    const trimmed = value.trim();
    return trimmed ? `${trimmed}\n` : "";
  }

  function criteriaMarkdown(value) {
    const body = normalizeBody(value);
    if (!body) {
      return "";
    }
    return /^#\s/m.test(body) ? body : `# Criteria\n\n${body}`;
  }

  function challengeFiles() {
    const slug = slugify(slugInput.value) || "example";
    const authors = authorList(authorsInput.value);
    const authorYaml = authors.length ? authors.join(", ") : "github-username";
    const difficulty = difficultyInput.value || "3";
    const instructions = normalizeBody(instructionsInput.value);
    const criteria = criteriaMarkdown(criteriaInput.value);

    return {
      slug,
      instructions:
        "---\n" +
        `title: ${yamlString(titleInput.value || "Untitled challenge")}\n` +
        `type: ${yamlString(typeInput.value || "experiment implementation")}\n` +
        `difficulty: ${difficulty}\n` +
        `authors: [${authorYaml}]\n` +
        "---\n\n" +
        instructions,
      criteria,
      gitkeep: "",
    };
  }

  function setPreview(element, value, placeholder) {
    element.textContent = value || placeholder;
    element.dataset.fileContent = value;
  }

  function updatePreview() {
    const files = challengeFiles();
    const root = `challenges/${files.slug}`;

    paths.instructions.textContent = `${root}/INSTRUCTIONS.md`;
    paths.criteria.textContent = `${root}/CRITERIA.md`;
    paths.gitkeep.textContent = `${root}/attempts/.gitkeep`;

    setPreview(previews.instructions, files.instructions, "");
    setPreview(previews.criteria, files.criteria, "");
    setPreview(previews.gitkeep, files.gitkeep, "(empty file)");

    criteriaOutput.hidden = !files.criteria;
  }

  function cursorPrompt() {
    const files = challengeFiles();
    const root = `challenges/${files.slug}`;
    const sections = [
      `Create a new PsyNetSkills challenge at \`${root}\` using the create-challenge workflow.`,
      `Write \`${root}/INSTRUCTIONS.md\` with:\n\n\`\`\`markdown\n${files.instructions}\`\`\``,
    ];

    if (files.criteria) {
      sections.push(
        `Write \`${root}/CRITERIA.md\` with:\n\n\`\`\`markdown\n${files.criteria}\`\`\``,
      );
    }

    sections.push(
      `Create \`${root}/attempts/.gitkeep\` as an empty file.`,
      "Run `uv run psynetsk-validate` and the narrowest useful additional checks.",
    );

    return sections.join("\n\n");
  }

  function fallbackCopyText(text) {
    const textarea = document.createElement("textarea");
    textarea.value = text;
    textarea.setAttribute("readonly", "");
    textarea.style.position = "absolute";
    textarea.style.left = "-9999px";
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand("copy");
    textarea.remove();
  }

  async function copyText(text, label) {
    try {
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(text);
      } else {
        fallbackCopyText(text);
      }
    } catch (error) {
      fallbackCopyText(text);
    }
    status.textContent = `Copied ${label}.`;
  }

  form.addEventListener("input", (event) => {
    if (event.target === slugInput) {
      slugWasEdited = true;
      slugInput.value = slugify(slugInput.value);
    }
    if (event.target === titleInput && !slugWasEdited) {
      slugInput.value = slugify(titleInput.value);
    }
    updatePreview();
  });

  document.addEventListener("click", (event) => {
    const button = event.target.closest("[data-copy-target]");
    if (!button) {
      return;
    }
    const target = document.getElementById(button.dataset.copyTarget);
    copyText(target.dataset.fileContent || "", target.closest("section").querySelector("h3").textContent);
  });

  document.getElementById("copy-cursor-prompt").addEventListener("click", () => {
    copyText(cursorPrompt(), "Cursor prompt");
  });

  updatePreview();
})();
