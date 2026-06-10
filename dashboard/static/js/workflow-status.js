(function () {
  const statusLink = document.querySelector("[data-workflow-status]");

  if (!statusLink) {
    return;
  }

  const icon = statusLink.querySelector(".workflow-status-icon");
  const popover = statusLink.querySelector(".workflow-status-popover");
  const config = statusLink.dataset;
  const enabled = config.enabled === "true";
  const pollMs = Number(config.pollMs) || 90000;
  const hiddenPollMs = Number(config.hiddenPollMs) || 300000;
  const renderedSha = config.renderedSha || "";
  let timerId = null;
  let inFlight = false;
  let popoverOpen = false;

  function setPopoverLines(lines) {
    if (!popover) {
      return;
    }
    popover.replaceChildren(
      ...lines.map(function (line) {
        const row = document.createElement("span");
        row.textContent = line;
        return row;
      }),
    );
  }

  function showPopover() {
    if (!popover) {
      return;
    }
    popover.hidden = false;
    popover.style.transform = "";
    statusLink.classList.add("workflow-tooltip-open");
    popoverOpen = true;
    window.requestAnimationFrame(function () {
      const rect = popover.getBoundingClientRect();
      const viewportPadding = 12;
      let offset = 0;
      if (rect.right > window.innerWidth - viewportPadding) {
        offset -= rect.right - (window.innerWidth - viewportPadding);
      }
      if (rect.left + offset < viewportPadding) {
        offset += viewportPadding - (rect.left + offset);
      }
      if (offset !== 0) {
        popover.style.transform = `translateX(${offset}px)`;
      }
    });
  }

  function hidePopover() {
    if (!popover) {
      return;
    }
    popover.hidden = true;
    popover.style.transform = "";
    statusLink.classList.remove("workflow-tooltip-open");
    popoverOpen = false;
  }

  function usesTapTooltip() {
    return window.matchMedia(
      "(hover: none), (pointer: coarse), (max-width: 720px)",
    ).matches;
  }

  function setState(kind, symbol, labelLines, isStale) {
    const label = labelLines.join(" ");
    statusLink.classList.remove(
      "workflow-status-success",
      "workflow-status-running",
      "workflow-status-failure",
      "workflow-status-unknown",
      "workflow-freshness-current",
      "workflow-freshness-stale",
    );
    statusLink.classList.add(`workflow-status-${kind}`);
    statusLink.classList.add(
      isStale ? "workflow-freshness-stale" : "workflow-freshness-current",
    );
    if (icon) {
      icon.textContent = symbol;
    }
    statusLink.setAttribute("aria-label", label);
    setPopoverLines(labelLines);
  }

  function checkedAt(date) {
    return `Last checked ${date.toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    })}`;
  }

  function shortSha(sha) {
    return sha ? sha.slice(0, 7) : "unknown commit";
  }

  function statusForRun(run) {
    if (run.status !== "completed") {
      return {
        kind: "running",
        symbol: "●",
        text: `Build ${run.status.replace(/_/g, " ")}`,
      };
    }
    if (run.conclusion === "success") {
      return { kind: "success", symbol: "✓", text: "Build passing" };
    }
    return {
      kind: "failure",
      symbol: "×",
      text: `Build ${run.conclusion || "failed"}`,
    };
  }

  function freshnessText(run, isStale) {
    if (!renderedSha || !run.head_sha) {
      return "Page freshness unknown.";
    }
    if (!isStale) {
      return `Page is current at ${shortSha(renderedSha)}.`;
    }
    return `Page is stale: viewing ${shortSha(
      renderedSha,
    )}, latest branch run is ${shortSha(run.head_sha)}.`;
  }

  function branchRunsUrl() {
    const workflowPath = config.workflow
      ? `/actions/workflows/${encodeURIComponent(config.workflow)}`
      : "/actions";
    const query = config.branch
      ? `?query=branch%3A${encodeURIComponent(config.branch)}`
      : "";
    return `https://github.com/${config.owner}/${config.repo}${workflowPath}${query}`;
  }

  function apiUrl() {
    const workflow = encodeURIComponent(config.workflow);
    const branch = encodeURIComponent(config.branch);
    return `https://api.github.com/repos/${config.owner}/${config.repo}/actions/workflows/${workflow}/runs?branch=${branch}&per_page=1`;
  }

  function scheduleNext(delayMs) {
    window.clearTimeout(timerId);
    const baseDelay =
      delayMs ||
      (document.visibilityState === "hidden" ? hiddenPollMs : pollMs);
    const jitter = Math.floor(Math.random() * Math.min(baseDelay * 0.1, 10000));
    timerId = window.setTimeout(checkStatus, baseDelay + jitter);
  }

  async function checkStatus() {
    if (inFlight) {
      scheduleNext();
      return;
    }

    inFlight = true;
    const now = new Date();

    try {
      const response = await fetch(apiUrl(), {
        headers: { Accept: "application/vnd.github+json" },
      });

      if (!response.ok) {
        const resetSeconds = Number(response.headers.get("x-ratelimit-reset"));
        const resetDelay =
          response.status === 403 && resetSeconds
            ? Math.max(resetSeconds * 1000 - Date.now(), hiddenPollMs)
            : undefined;
        setState("unknown", "?", [
          "Could not load workflow status.",
          checkedAt(now),
        ], false);
        scheduleNext(resetDelay);
        return;
      }

      const data = await response.json();
      const run = data.workflow_runs && data.workflow_runs[0];

      if (!run) {
        setState("unknown", "?", [
          `No workflow run found for ${config.branch}.`,
          checkedAt(now),
        ], false);
        statusLink.href = branchRunsUrl();
        scheduleNext();
        return;
      }

      const state = statusForRun(run);
      const isStale = Boolean(
        renderedSha && run.head_sha && renderedSha !== run.head_sha,
      );
      const branch = config.branch ? ` on ${config.branch}` : "";
      const label = [
        `${state.text}${branch}.`,
        freshnessText(run, isStale),
        checkedAt(now),
      ];
      setState(state.kind, state.symbol, label, isStale);
      statusLink.href = run.html_url || branchRunsUrl();
      scheduleNext();
    } catch (error) {
      setState("unknown", "?", [
        "Could not load workflow status.",
        checkedAt(now),
      ], false);
      scheduleNext();
    } finally {
      inFlight = false;
    }
  }

  statusLink.addEventListener("mouseenter", function () {
    if (!usesTapTooltip()) {
      showPopover();
    }
  });

  statusLink.addEventListener("mouseleave", function () {
    if (!usesTapTooltip()) {
      hidePopover();
    }
  });

  statusLink.addEventListener("focus", showPopover);

  statusLink.addEventListener("blur", function () {
    window.setTimeout(function () {
      if (document.activeElement !== statusLink) {
        hidePopover();
      }
    }, 0);
  });

  statusLink.addEventListener("click", function (event) {
    if (!usesTapTooltip() || popoverOpen) {
      return;
    }
    event.preventDefault();
    showPopover();
  });

  document.addEventListener("click", function (event) {
    if (!usesTapTooltip() || statusLink.contains(event.target)) {
      return;
    }
    hidePopover();
  });

  if (
    !enabled ||
    !config.owner ||
    !config.repo ||
    !config.workflow ||
    !config.branch
  ) {
    setState("unknown", "?", [
      "Workflow status unavailable for this dashboard.",
      checkedAt(new Date()),
    ], false);
    return;
  }

  statusLink.href = branchRunsUrl();
  checkStatus();

  document.addEventListener("visibilitychange", function () {
    window.clearTimeout(timerId);
    if (document.visibilityState === "visible") {
      checkStatus();
    } else {
      scheduleNext(hiddenPollMs);
    }
  });
})();
