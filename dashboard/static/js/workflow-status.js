(function () {
  const branchContextLabel = document.querySelector("[data-branch-context-label]");

  if (branchContextLabel) {
    const branchPopover = branchContextLabel.querySelector(".branch-context-popover");

    if (branchPopover) {
      const showBranchPopover = function () {
        branchPopover.hidden = false;
      };
      const hideBranchPopover = function () {
        branchPopover.hidden = true;
      };

      branchContextLabel.addEventListener("mouseenter", showBranchPopover);
      branchContextLabel.addEventListener("mouseleave", hideBranchPopover);
      branchContextLabel.addEventListener("focus", showBranchPopover);
      branchContextLabel.addEventListener("blur", hideBranchPopover);
      branchContextLabel.addEventListener("click", function (event) {
        event.preventDefault();
        branchPopover.hidden = !branchPopover.hidden;
      });
    }
  }

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
  let tapArmed = false;

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
    tapArmed = false;
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

  function relativeTime(date, now) {
    const elapsedSeconds = Math.max(
      0,
      Math.round((now.getTime() - date.getTime()) / 1000),
    );
    const units = [
      ["year", 31536000],
      ["month", 2592000],
      ["week", 604800],
      ["day", 86400],
      ["hour", 3600],
      ["minute", 60],
    ];

    for (const [unit, seconds] of units) {
      const value = Math.floor(elapsedSeconds / seconds);
      if (value >= 1) {
        return `${value} ${unit}${value === 1 ? "" : "s"} ago`;
      }
    }

    return "just now";
  }

  function runDate(run) {
    const timestamp =
      run.status === "completed"
        ? run.updated_at || run.created_at
        : run.run_started_at || run.created_at || run.updated_at;

    if (!timestamp) {
      return null;
    }

    const date = new Date(timestamp);
    return Number.isNaN(date.getTime()) ? null : date;
  }

  function pagesTimeText(run, now) {
    const date = runDate(run);
    if (!date) {
      return `Last checked ${relativeTime(now, now)}`;
    }
    if (run.status !== "completed") {
      return `Publishing started ${relativeTime(date, now)}`;
    }
    if (run.conclusion === "success") {
      return `Last published ${relativeTime(date, now)}`;
    }
    return `Publish ended ${relativeTime(date, now)}`;
  }

  function shortSha(sha) {
    return sha ? sha.slice(0, 7) : "unknown commit";
  }

  function isPagesMode() {
    return config.mode === "production" || config.mode === "pr-preview";
  }

  function statusForRun(run) {
    if (isPagesMode()) {
      if (run.status !== "completed") {
        return {
          kind: "running",
          symbol: "●",
          text: `Pages publication ${run.status.replace(/_/g, " ")}`,
        };
      }
      if (run.conclusion === "success") {
        return { kind: "success", symbol: "✓", text: "Pages published" };
      }
      return {
        kind: "failure",
        symbol: "×",
        text: `Pages publish ${run.conclusion || "failed"}`,
      };
    }

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
    if (!renderedSha) {
      return "Page freshness unknown.";
    }
    if (isPagesMode()) {
      if (run.status !== "completed") {
        return `Viewing ${shortSha(renderedSha)} while GitHub Pages finishes publishing.`;
      }
      if (run.conclusion !== "success") {
        return `Viewing ${shortSha(renderedSha)} because the latest GitHub Pages publication did not complete.`;
      }
      return `Published page includes ${shortSha(renderedSha)}.`;
    }
    if (!run.head_sha) {
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
    if (isPagesMode()) {
      return `https://github.com/${config.owner}/${config.repo}/actions?query=workflow%3Apages-build-deployment`;
    }

    const workflowPath = config.workflow
      ? `/actions/workflows/${encodeURIComponent(config.workflow)}`
      : "/actions";
    const query = config.branch
      ? `?query=branch%3A${encodeURIComponent(config.branch)}`
      : "";
    return `https://github.com/${config.owner}/${config.repo}${workflowPath}${query}`;
  }

  function apiUrl() {
    if (isPagesMode()) {
      return `https://api.github.com/repos/${config.owner}/${config.repo}/actions/runs?event=dynamic&per_page=1`;
    }

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
        const missingRun = isPagesMode()
          ? "No GitHub Pages deployment run found."
          : `No workflow run found for ${config.branch}.`;
        setState("unknown", "?", [
          missingRun,
          checkedAt(now),
        ], false);
        statusLink.href = branchRunsUrl();
        scheduleNext();
        return;
      }

      const state = statusForRun(run);
      const isStale = isPagesMode()
        ? run.status !== "completed" || run.conclusion !== "success"
        : Boolean(renderedSha && run.head_sha && renderedSha !== run.head_sha);
      const branch =
        !isPagesMode() && config.branch ? ` on ${config.branch}` : "";
      const label = [
        `${state.text}${branch}.`,
        freshnessText(run, isStale),
        isPagesMode() ? pagesTimeText(run, now) : checkedAt(now),
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
    if (!usesTapTooltip()) {
      return;
    }
    if (!tapArmed) {
      event.preventDefault();
      showPopover();
      tapArmed = true;
    }
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
