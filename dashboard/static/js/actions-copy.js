(function () {
  const dataElement = document.getElementById("action-copy-data");
  if (!dataElement) {
    return;
  }

  let actions = [];
  try {
    actions = JSON.parse(dataElement.textContent || "[]");
  } catch (_error) {
    actions = [];
  }

  const actionsById = new Map(actions.map((action) => [action.id, action]));
  const checkboxes = Array.from(
    document.querySelectorAll("[data-action-copy-checkbox]"),
  );
  const toolbar = document.querySelector("[data-action-copy-toolbar]");
  const countElement = document.querySelector("[data-action-copy-count]");
  const button = document.querySelector("[data-action-copy-button]");
  const previewButton = document.querySelector("[data-action-preview-button]");
  const previewPopover = document.querySelector("[data-action-preview-popover]");
  const previewText = document.querySelector("[data-action-preview-text]");
  const previewClose = document.querySelector("[data-action-preview-close]");
  const deselectButton = document.querySelector("[data-action-deselect-button]");
  const statusElement = document.querySelector("[data-action-copy-status]");

  if (!toolbar || !countElement || !button || checkboxes.length === 0) {
    return;
  }

  function selectedActions() {
    return checkboxes
      .filter((checkbox) => checkbox.checked)
      .map((checkbox) => actionsById.get(checkbox.value))
      .filter(Boolean);
  }

  function absoluteDashboardUrl(path) {
    return new URL(path, window.location.origin).toString();
  }

  function formatAction(action) {
    const context = action.copy_context || {};
    const actionPoint = context.action || action.proposal;
    const lines = [
      `## ${actionPoint}`,
      "",
      `Action ID: ${context.id || action.id}`,
      `Challenge: ${context.challenge || action.challenge_title}`,
      `Attempt: ${context.attempt || action.attempt_name}`,
      `Source: ${context.source_path || action.source_path}`,
      `Dashboard link: ${absoluteDashboardUrl(context.dashboard_path || action.source_url)}`,
      `Repository target: ${context.repository || action.repository}`,
      `Confidence: ${context.confidence || action.confidence}`,
      `Impact: ${context.impact || action.impact}`,
      `Status: ${context.status || action.status}`,
      "",
      "Learning context:",
      context.learning_context || action.learning_context || "(No learning context recorded.)",
    ];

    const notes = context.notes || action.notes;
    if (notes) {
      lines.push("", "Notes:", notes);
    }

    return lines.join("\n");
  }

  function formatBrief(selected) {
    return [
      "# PsyNetSkills action points",
      "",
      "Please address the following outstanding action points from historic challenge attempts. If they fall into clearly separate pieces of work, address those pieces one at a time, discussing strategy with the user and getting confirmation before continuing.",
      "",
      selected.map((action) => formatAction(action)).join("\n\n"),
    ].join("\n").trim() + "\n";
  }

  function updateState() {
    const count = selectedActions().length;
    toolbar.hidden = count === 0;
    countElement.textContent = `${count} selected`;
    button.disabled = count === 0;
    if (previewButton) {
      previewButton.disabled = count === 0;
    }
    if (deselectButton) {
      deselectButton.disabled = count === 0;
    }
    if (count === 0 && statusElement) {
      statusElement.textContent = "";
    }
    updatePreview();
  }

  function clearSelections() {
    checkboxes.forEach((checkbox) => {
      checkbox.checked = false;
    });
    updateState();
  }

  function closePreview() {
    if (previewPopover) {
      previewPopover.hidden = true;
    }
  }

  function updatePreview() {
    if (!previewPopover || !previewText) {
      return;
    }

    const selected = selectedActions();
    if (selected.length === 0) {
      previewText.textContent = "";
      closePreview();
      return;
    }
    previewText.textContent = formatBrief(selected);
  }

  async function copyText(text) {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text);
      return;
    }

    const textarea = document.createElement("textarea");
    textarea.value = text;
    textarea.setAttribute("readonly", "");
    textarea.style.position = "fixed";
    textarea.style.left = "-9999px";
    document.body.appendChild(textarea);
    textarea.select();
    const copied = document.execCommand("copy");
    document.body.removeChild(textarea);
    if (!copied) {
      throw new Error("Copy command failed");
    }
  }

  async function copySelectedActions() {
    const selected = selectedActions();
    if (selected.length === 0) {
      return false;
    }

    try {
      await copyText(formatBrief(selected));
      if (statusElement) {
        statusElement.textContent = `Copied ${selected.length} action${selected.length === 1 ? "" : "s"}.`;
      }
      return true;
    } catch (_error) {
      if (statusElement) {
        statusElement.textContent = "Copy failed. Please try again.";
      }
      return false;
    }
  }

  function isTextEditableTarget(target) {
    if (!(target instanceof Element)) {
      return false;
    }
    if (
      target.closest(
        "textarea, select, [contenteditable=''], [contenteditable='true']",
      )
    ) {
      return true;
    }

    const input = target.closest("input");
    if (!input) {
      return false;
    }

    const nonTextTypes = new Set([
      "button",
      "checkbox",
      "color",
      "file",
      "hidden",
      "image",
      "radio",
      "range",
      "reset",
      "submit",
    ]);
    return !nonTextTypes.has((input.getAttribute("type") || "text").toLowerCase());
  }

  function hasTextSelection() {
    const selection = window.getSelection && window.getSelection();
    return Boolean(selection && !selection.isCollapsed && selection.toString());
  }

  checkboxes.forEach((checkbox) => {
    checkbox.addEventListener("change", updateState);
  });

  document.querySelectorAll("[data-action-card-row]").forEach((row) => {
    row.addEventListener("click", (event) => {
      if (event.target.closest("a, button, input, label")) {
        return;
      }

      const checkbox = row.querySelector("[data-action-copy-checkbox]");
      if (!checkbox) {
        return;
      }
      checkbox.checked = !checkbox.checked;
      checkbox.dispatchEvent(new Event("change", { bubbles: true }));
    });
  });

  document.querySelectorAll(".learning-action").forEach((action) => {
    action.addEventListener("click", (event) => {
      if (event.target.closest("a, button, input, label")) {
        return;
      }

      const checkbox = action.querySelector("[data-action-copy-checkbox]");
      if (!checkbox) {
        return;
      }
      checkbox.checked = !checkbox.checked;
      checkbox.dispatchEvent(new Event("change", { bubbles: true }));
    });
  });

  button.addEventListener("click", async () => {
    await copySelectedActions();
  });

  if (previewButton && previewPopover && previewText) {
    previewButton.addEventListener("click", () => {
      updatePreview();
      previewPopover.hidden = false;
    });
  }

  if (previewClose) {
    previewClose.addEventListener("click", closePreview);
  }

  if (deselectButton) {
    deselectButton.addEventListener("click", () => {
      clearSelections();
    });
  }

  document.addEventListener("click", (event) => {
    if (selectedActions().length === 0) {
      return;
    }
    if (
      event.target.closest(
        "[data-action-card-row], [data-action-copy-toolbar], .learning-action",
      )
    ) {
      return;
    }
    clearSelections();
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      closePreview();
      return;
    }

    if (
      event.key.toLowerCase() === "c" &&
      (event.metaKey || event.ctrlKey) &&
      !event.altKey &&
      !isTextEditableTarget(event.target) &&
      !hasTextSelection()
    ) {
      if (selectedActions().length === 0) {
        return;
      }
      event.preventDefault();
      copySelectedActions();
    }
  });

  updateState();
})();
