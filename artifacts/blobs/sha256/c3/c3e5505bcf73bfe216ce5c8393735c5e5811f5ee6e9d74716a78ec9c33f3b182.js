(function () {
  "use strict";

  const definition = window.discoveryTrialDefinition;
  const config = definition.game_config;
  const app = document.getElementById("discovery-app");
  const state = {
    startedAt: Date.now(),
    instructionStart: Date.now(),
    messageBrowseStart: null,
    messageReflectStart: null,
    gameStart: null,
    gameEnd: null,
    compositionStart: null,
    position: {...config.player_start},
    actionsLeft: config.action_budget,
    points: 0,
    carrying: null,
    transitions: [],
    harvested: [],
    actions: [],
    events: [],
    eventCounter: 0,
    actionCounter: 0,
    items: config.items.map((item) => ({...item, on_grid: true})),
    regenerated: new Set(),
    readIds: new Set(),
    notebook: [],
    notebookDeleted: [],
    readEvents: [],
    currentMessage: null,
    messageOpenTime: null,
    strategySummary: "",
    timings: {
      instruction_ms: 0,
      messages_browse_ms: 0,
      messages_reflect_ms: 0,
      game_ms: 0,
      composition_ms: 0,
    },
  };

  function sanitizeText(text) {
    return String(text || "").replace(/["'`\\@#$%^*]/g, "").replace(/\s+/g, " ").trim();
  }

  function itemParts(name) {
    const [shape, texture, level] = name.split("_");
    return {shape, texture, level: Number(level)};
  }

  function itemPoints(name) {
    return Math.pow(10, itemParts(name).level);
  }

  function newObject(held, target) {
    const heldParts = itemParts(held);
    const targetParts = itemParts(target);
    const newLevel = Math.max(heldParts.level, targetParts.level) + 1;
    if (newLevel >= config.max_level) return "";
    return `${heldParts.shape}_${targetParts.texture}_${newLevel}`;
  }

  function transitionSucceeds(condition, held, target) {
    const heldParts = itemParts(held);
    const targetParts = itemParts(target);
    const shapeSum = config.shapes.indexOf(heldParts.shape) + config.shapes.indexOf(targetParts.shape);
    const textureSum = config.textures.indexOf(heldParts.texture) + config.textures.indexOf(targetParts.texture);
    if (condition === "easy") return heldParts.shape === targetParts.shape;
    if (condition === "medium") return shapeSum === 3 && heldParts.texture !== targetParts.texture;
    if (condition === "hard") return shapeSum === 3 && (config.textures.indexOf(heldParts.texture) % 2 === 0 || config.textures.indexOf(targetParts.texture) % 2 === 0);
    return false;
  }

  function itemSymbol(name) {
    const parts = itemParts(name);
    return {triangle: "T", circle: "C", square: "S", diamond: "D"}[parts.shape] || "?";
  }

  function itemHtml(name) {
    if (!name) return "";
    const parts = itemParts(name);
    return `<span class="discovery-item ${parts.shape} level-${parts.level} discovery-texture-${parts.texture}" title="${name}"><span>${itemSymbol(name)}</span></span>`;
  }

  function itemAt(x, y) {
    return state.items.find((item) => item.on_grid && item.x === x && item.y === y);
  }

  function logEvent(action) {
    state.eventCounter += 1;
    state.events.push({
      event_id: `event-${state.eventCounter}`,
      timestamp: new Date().toISOString(),
      action,
      x: state.position.x,
      y: state.position.y,
      actions_left: state.actionsLeft,
      current_points: state.points,
      currently_carrying: state.carrying || "",
    });
  }

  function logScoredAction(record) {
    state.actionCounter += 1;
    state.actionsLeft -= 1;
    state.actions.push({
      action_id: `act-${state.actionCounter}`,
      actions_left_after: state.actionsLeft,
      ...record,
    });
  }

  function renderInstruction() {
    app.innerHTML = `
      <section class="discovery-panel">
        <h2>Crystal discovery game</h2>
        <p>You are exploring a planet covered with crystals. Move the rover with the arrow keys. Press Space to pick up a crystal, fuse a carried crystal with one on the current tile, or harvest a carried crystal on an empty tile. Press D to drop your carried crystal.</p>
        <p>Successful fusions make higher-level crystals worth ten times more points. This run uses the <strong>${definition.condition}</strong> rule family, ${config.action_budget} scored fusion/harvest actions, chain ${definition.chain_id}, generation ${definition.generation_index}.</p>
        <p class="discovery-muted">This PsyNet version saves through the trial answer instead of the reference repository's PHP endpoint.</p>
        <button id="instruction-next" class="discovery-button">${definition.generation_index > 0 ? "Read previous messages" : "Start game"}</button>
      </section>`;
    document.getElementById("instruction-next").addEventListener("click", () => {
      state.timings.instruction_ms = Date.now() - state.instructionStart;
      if (definition.generation_index > 0) renderMessages(); else renderGame();
    });
  }

  function renderMessages() {
    state.messageBrowseStart = Date.now();
    const messages = definition.incoming_message_set.messages || [];
    app.innerHTML = `
      <section class="discovery-panel">
        <h2>Before you start: messages from previous players</h2>
        <p>Open a message, highlight useful text, and save it into your notebook.</p>
        <div class="discovery-row">
          <div class="discovery-main"><div id="message-list" class="message-list"></div></div>
          <aside class="discovery-sidebar discovery-panel">
            <h3>Your notebook</h3>
            <ul id="notebook-list" class="notebook-list"><li class="discovery-muted">Nothing saved yet.</li></ul>
            <button id="messages-next" class="discovery-button" disabled>Continue</button>
          </aside>
        </div>
      </section>`;
    const list = document.getElementById("message-list");
    messages.forEach((msg, index) => {
      const card = document.createElement("article");
      card.className = "message-card";
      card.id = `message-card-${msg.sample_id}`;
      card.innerHTML = `
        <h3>Player #${index + 1}: ${Number(msg.total_points || 0).toLocaleString()} points</h3>
        <p><strong>Strategy:</strong> <span class="message-text">${msg.messageHow}</span></p>
        <p><strong>Rules:</strong> <span class="message-text">${msg.messageRules}</span></p>
        <button class="discovery-button open-message" data-sample-id="${msg.sample_id}">Mark read</button>
        <button class="discovery-button save-note" data-sample-id="${msg.sample_id}">Save highlighted text</button>`;
      list.appendChild(card);
    });
    list.querySelectorAll(".open-message").forEach((btn) => btn.addEventListener("click", markRead));
    list.querySelectorAll(".save-note").forEach((btn) => btn.addEventListener("click", saveNote));
    document.getElementById("messages-next").addEventListener("click", renderReflection);
  }

  function markRead(event) {
    const sampleId = Number(event.target.dataset.sampleId);
    const messages = definition.incoming_message_set.messages || [];
    const msg = messages.find((candidate) => Number(candidate.sample_id) === sampleId);
    if (!msg) return;
    state.readIds.add(sampleId);
    document.getElementById(`message-card-${sampleId}`).classList.add("visited");
    state.readEvents.push({
      msgEventId: `msg-${sampleId}-${state.readEvents.length + 1}`,
      sampleId,
      rank: msg.rank,
      dwellMs: 1000,
      openedAt: new Date().toISOString(),
      closedAt: new Date().toISOString(),
    });
    unlockMessages();
  }

  function saveNote(event) {
    const sampleId = Number(event.target.dataset.sampleId);
    const selection = sanitizeText(window.getSelection().toString());
    const messages = definition.incoming_message_set.messages || [];
    const msg = messages.find((candidate) => Number(candidate.sample_id) === sampleId);
    const fallback = msg ? sanitizeText(msg.messageRules || msg.messageHow).slice(0, 160) : "";
    const text = selection || fallback;
    if (!text) return;
    state.notebook.push({
      from: `Player #${messages.indexOf(msg) + 1}`,
      text,
      sampleId,
      savedAt: new Date().toISOString(),
    });
    renderNotebook();
    window.getSelection().removeAllRanges();
    unlockMessages();
  }

  function renderNotebook() {
    const list = document.getElementById("notebook-list");
    if (!list) return;
    list.innerHTML = "";
    state.notebook.forEach((entry, index) => {
      const li = document.createElement("li");
      li.innerHTML = `<em>${entry.from}:</em> ${entry.text} <button class="delete-note" data-index="${index}" aria-label="Delete note">x</button>`;
      list.appendChild(li);
    });
    list.querySelectorAll(".delete-note").forEach((btn) => btn.addEventListener("click", (event) => {
      const index = Number(event.target.dataset.index);
      const entry = {...state.notebook[index], deletedAt: new Date().toISOString()};
      state.notebookDeleted.push(entry);
      state.notebook.splice(index, 1);
      renderNotebook();
      unlockMessages();
    }));
  }

  function unlockMessages() {
    const btn = document.getElementById("messages-next");
    if (btn) btn.disabled = !(state.readIds.size >= 1 && state.notebook.length >= 1);
  }

  function renderReflection() {
    state.timings.messages_browse_ms = Date.now() - state.messageBrowseStart;
    state.messageReflectStart = Date.now();
    app.innerHTML = `
      <section class="discovery-panel">
        <h2>Write a short strategy summary</h2>
        <p>This summary will be visible while you play.</p>
        <ul>${state.notebook.map((entry) => `<li><em>${entry.from}:</em> ${entry.text}</li>`).join("")}</ul>
        <textarea id="strategy-summary" class="discovery-textarea" placeholder="What do you want to remember?"></textarea>
        <button id="start-game" class="discovery-button" disabled>Start the game</button>
      </section>`;
    const textarea = document.getElementById("strategy-summary");
    const btn = document.getElementById("start-game");
    textarea.addEventListener("input", () => { btn.disabled = sanitizeText(textarea.value).length === 0; });
    btn.addEventListener("click", () => {
      state.strategySummary = sanitizeText(textarea.value);
      state.timings.messages_reflect_ms = Date.now() - state.messageReflectStart;
      renderGame();
    });
  }

  function renderGame() {
    state.gameStart = Date.now();
    app.innerHTML = `
      <section class="discovery-panel">
        <div class="discovery-stats">
          <div class="discovery-stat"><strong>Points:</strong> <span id="points">0</span></div>
          <div class="discovery-stat"><strong>Actions:</strong> <span id="actions-left">${state.actionsLeft}</span></div>
          <div class="discovery-stat"><strong>Carrying:</strong> <span id="carrying"></span></div>
          <div class="discovery-stat"><strong>Here:</strong> <span id="current-tile"></span></div>
        </div>
        ${state.strategySummary ? `<div class="discovery-summary"><strong>Your summary:</strong> ${state.strategySummary}</div>` : ""}
        <p class="discovery-muted">Keyboard: arrow keys move; Space picks up, fuses, or harvests; D drops. The review helper can end the game after the interaction is demonstrated.</p>
        <div class="discovery-row">
          <div class="discovery-main"><div id="game-grid" class="discovery-grid" tabindex="0"></div></div>
          <aside class="discovery-sidebar discovery-panel">
            <h3>Hint</h3><div id="fusion-hint"></div>
            <h3>Found recipes</h3><table class="discovery-log"><tbody id="recipe-log"></tbody></table>
            <h3>Harvested rewards</h3><table class="discovery-log"><tbody id="reward-log"></tbody></table>
            <button id="finish-review" class="discovery-button">Finish game and write messages</button>
          </aside>
        </div>
      </section>`;
    document.addEventListener("keydown", handleKeyPress);
    document.getElementById("finish-review").addEventListener("click", finishGame);
    renderGrid();
    updateStatus();
    setTimeout(() => document.getElementById("game-grid").focus(), 50);
  }

  function renderGrid() {
    const grid = document.getElementById("game-grid");
    if (!grid) return;
    grid.innerHTML = "";
    grid.style.gridTemplateColumns = `repeat(${config.grid_size}, 28px)`;
    grid.style.gridTemplateRows = `repeat(${config.grid_size}, 28px)`;
    for (let y = 0; y < config.grid_size; y += 1) {
      for (let x = 0; x < config.grid_size; x += 1) {
        const cell = document.createElement("div");
        cell.className = "discovery-cell";
        cell.dataset.x = String(x);
        cell.dataset.y = String(y);
        const item = itemAt(x, y);
        if (item) cell.innerHTML = itemHtml(item.item_name);
        if (state.position.x === x && state.position.y === y) {
          const player = document.createElement("div");
          player.className = "discovery-player";
          cell.appendChild(player);
        }
        grid.appendChild(cell);
      }
    }
  }

  function updateStatus() {
    const item = itemAt(state.position.x, state.position.y);
    document.getElementById("points").textContent = String(state.points);
    document.getElementById("actions-left").textContent = String(state.actionsLeft);
    document.getElementById("carrying").innerHTML = state.carrying ? itemHtml(state.carrying) : "";
    document.getElementById("current-tile").innerHTML = item ? itemHtml(item.item_name) : "";
    const hint = document.getElementById("fusion-hint");
    if (hint && state.carrying && item) {
      const record = state.transitions.find((transition) => transition.held === state.carrying && transition.target === item.item_name);
      hint.innerHTML = `${itemHtml(state.carrying)} + ${itemHtml(item.item_name)} = ${record ? (record.yield ? itemHtml(record.yield) : "No fusion") : "?"}`;
    } else if (hint) {
      hint.innerHTML = "";
    }
  }

  function handleKeyPress(event) {
    if (!document.getElementById("game-grid")) return;
    if (["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight", " ", "d", "D"].includes(event.key)) event.preventDefault();
    const {x, y} = state.position;
    if (event.key === "ArrowUp" && y > 0) { state.position.y -= 1; logEvent("moveUp"); }
    else if (event.key === "ArrowDown" && y < config.grid_size - 1) { state.position.y += 1; logEvent("moveDown"); }
    else if (event.key === "ArrowLeft" && x > 0) { state.position.x -= 1; logEvent("moveLeft"); }
    else if (event.key === "ArrowRight" && x < config.grid_size - 1) { state.position.x += 1; logEvent("moveRight"); }
    else if (event.key === " ") handleSpace();
    else if (event.key === "d" || event.key === "D") handleDrop();
    renderGrid();
    updateStatus();
    if (state.actionsLeft <= 0) finishGame();
  }

  function handleSpace() {
    const target = itemAt(state.position.x, state.position.y);
    if (target && state.carrying) combineItem(target);
    else if (target && !state.carrying) {
      state.carrying = target.item_name;
      target.on_grid = false;
      logEvent("pickUp");
    } else if (!target && state.carrying) harvestCarried();
  }

  function combineItem(target) {
    const held = state.carrying;
    let record = state.transitions.find((candidate) => candidate.held === held && candidate.target === target.item_name);
    if (!record) {
      const yieldItem = transitionSucceeds(definition.condition, held, target.item_name) ? newObject(held, target.item_name) : "";
      record = {held, target: target.item_name, yield: yieldItem};
      state.transitions.push(record);
      const row = document.createElement("tr");
      row.innerHTML = `<td>${itemHtml(held)} + ${itemHtml(target.item_name)} = ${yieldItem ? itemHtml(yieldItem) : "No fusion"}</td>`;
      document.getElementById("recipe-log").appendChild(row);
    }
    if (record.yield) {
      target.on_grid = false;
      const parts = itemParts(record.yield);
      if (!state.items.find((item) => item.item_name === record.yield)) {
        state.items.push({item_name: record.yield, x: state.position.x, y: state.position.y, item_level: parts.level, shape: parts.shape, texture: parts.texture, on_grid: false});
      }
      state.carrying = record.yield;
      maybeRegenerate([held, target.item_name]);
    }
    logScoredAction({action: "combine", held, target: target.item_name, yield: record.yield, points: 0});
    logEvent("combine");
  }

  function harvestCarried() {
    const gained = itemPoints(state.carrying);
    state.points += gained;
    const reward = {item: state.carrying, points: gained, x: state.position.x, y: state.position.y, timestamp: new Date().toISOString()};
    state.harvested.push(reward);
    const row = document.createElement("tr");
    row.innerHTML = `<td>${itemHtml(state.carrying)}</td><td>${gained.toLocaleString()} pts</td>`;
    document.getElementById("reward-log").appendChild(row);
    logScoredAction({action: "harvest", held: state.carrying, target: "", yield: "", points: gained});
    maybeRegenerate([state.carrying]);
    state.carrying = null;
    logEvent("consume");
  }

  function handleDrop() {
    if (!state.carrying || itemAt(state.position.x, state.position.y)) return;
    const existing = state.items.find((item) => item.item_name === state.carrying);
    if (existing) {
      existing.x = state.position.x;
      existing.y = state.position.y;
      existing.on_grid = true;
    }
    state.carrying = null;
    logEvent("drop");
  }

  function maybeRegenerate(itemNames) {
    if (!config.allow_regeneration) return;
    itemNames.filter((name) => name.endsWith("_0") && !state.regenerated.has(name)).forEach((name) => {
      state.regenerated.add(name);
      setTimeout(() => {
        const existing = state.items.find((item) => item.item_name === name);
        if (!existing || existing.on_grid) return;
        for (let y = 0; y < config.grid_size; y += 1) {
          for (let x = 0; x < config.grid_size; x += 1) {
            if (!itemAt(x, y) && !(state.position.x === x && state.position.y === y)) {
              existing.x = x;
              existing.y = y;
              existing.on_grid = true;
              renderGrid();
              return;
            }
          }
        }
      }, config.regeneration_delay_ms || 400);
    });
  }

  function finishGame() {
    document.removeEventListener("keydown", handleKeyPress);
    state.gameEnd = Date.now();
    state.timings.game_ms = state.gameEnd - state.gameStart;
    state.compositionStart = Date.now();
    renderComposer();
  }

  function renderComposer() {
    app.innerHTML = `
      <section class="discovery-panel">
        <h2>Leave messages for future players</h2>
        <p>You scored <strong>${state.points.toLocaleString()}</strong> points. Share what helped and what rules you noticed.</p>
        <label><strong>Tips or strategies</strong><textarea id="message-how" class="discovery-textarea"></textarea></label>
        <label><strong>Rules or patterns</strong><textarea id="message-rules" class="discovery-textarea"></textarea></label>
        <button id="submit-answer" class="discovery-button">Submit</button>
      </section>`;
    document.getElementById("message-how").value = `I scored ${state.points} points by trying fusions and harvesting upgraded crystals.`;
    document.getElementById("message-rules").value = definition.condition === "easy" ? "Crystals with the same shape seemed to fuse." : "Look for shape and texture patterns before spending actions.";
    document.getElementById("submit-answer").addEventListener("click", submitAnswer);
  }

  function compileAnswer() {
    state.timings.composition_ms = Date.now() - state.compositionStart;
    return {
      chain_id: definition.chain_id,
      condition: definition.condition,
      generation_index: definition.generation_index,
      trial_index_within_generation: definition.trial_index_within_generation,
      participant_id_hint: definition.participant_id,
      game_config: definition.game_config,
      incoming_message_set: definition.incoming_message_set,
      game: {
        total_points: state.points,
        actions_remaining: state.actionsLeft,
        actions: state.actions,
        events: state.events,
        transitions: state.transitions,
        harvested_rewards: state.harvested,
        final_position: state.position,
        final_carrying: state.carrying,
      },
      messages: {
        incoming: definition.incoming_message_set,
        notebook: state.notebook,
        notebook_deleted: state.notebookDeleted,
        read_events: state.readEvents,
        strategy_summary: sanitizeText(state.strategySummary),
        outgoing: {
          messageHow: sanitizeText(document.getElementById("message-how").value),
          messageRules: sanitizeText(document.getElementById("message-rules").value),
        },
      },
      timing: state.timings,
      source: "browser_js",
    };
  }

  function submitAnswer() {
    const answer = compileAnswer();
    if (!answer.messages.outgoing.messageHow || !answer.messages.outgoing.messageRules) {
      psynet.alert("Please complete both message boxes.");
      return;
    }
    psynet.nextPage(answer);
  }

  window.discoveryGame = {
    state,
    forceFinish: finishGame,
    compileAnswer,
  };

  renderInstruction();
})();
