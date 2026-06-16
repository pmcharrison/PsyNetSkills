/* Thin PsyNet bridge for the upstream discovery-chains task.
 * The upstream files own display, keyboard handling, fusions, message browsing,
 * notebook behavior, and composer validation. This adapter only starts the right
 * section for PsyNet and submits the upstream state through psynet.nextPage().
 */
(function () {
  const definition = window.discoveryTrialDefinition;
  const originalHideAndShowNext = window.hideAndShowNext;

  function sanitizeForPsyNet(text) {
    return String(text || '').replace(/["'`\\@#$%^*]/g, '').replace(/\s+/g, ' ').trim();
  }

  function valuesWithIds(obj) {
    return Object.entries(obj || {}).map(([id, value]) => ({ id, ...value }));
  }

  function currentActionData() {
    return typeof actionData === 'undefined' ? {} : actionData;
  }

  function currentEventData() {
    return typeof eventData === 'undefined' ? {} : eventData;
  }

  function currentNotesData() {
    return typeof notesData === 'undefined' ? {} : notesData;
  }

  function currentSubjectData() {
    return typeof subjectData === 'undefined' ? {} : subjectData;
  }

  function harvestedRewards() {
    return valuesWithIds(currentActionData())
      .filter(action => ['consume', 'harvest'].includes(action.action) && Number(action.points || 0) > 0)
      .map(action => ({ item: action.held, points: action.points, action_id: action.id }));
  }

  function timingData() {
    const subject = currentSubjectData();
    return {
      instruction_ms: subject.instruction_duration || 0,
      messages_browse_ms: subject.messages_browse_duration || 0,
      messages_reflect_ms: subject.messages_reflect_duration || 0,
      game_ms: subject.task_duration || 0,
      composition_ms: subject.composition_duration || 0,
    };
  }

  function buildAnswer() {
    const notes = currentNotesData();
    const outgoing = {
      messageHow: sanitizeForPsyNet(document.getElementById('composer-text-how').value),
      messageRules: sanitizeForPsyNet(document.getElementById('composer-text-rules').value),
    };
    return {
      chain_id: definition.chain_id,
      condition: definition.condition,
      generation_index: definition.generation_index,
      trial_index_within_generation: definition.trial_index_within_generation,
      participant_id_hint: definition.participant_id,
      game_config: definition.game_config,
      incoming_message_set: definition.incoming_message_set,
      game: {
        total_points: typeof POINTS === 'undefined' ? 0 : POINTS,
        actions_remaining: typeof ACTIONS === 'undefined' ? 0 : ACTIONS,
        actions: valuesWithIds(currentActionData()),
        events: valuesWithIds(currentEventData()),
        transitions: typeof transitions === 'undefined' ? [] : transitions,
        harvested_rewards: harvestedRewards(),
        final_position: typeof playerPosition === 'undefined' ? null : playerPosition,
        final_carrying: typeof currentlyCarrying === 'undefined' ? null : currentlyCarrying,
      },
      messages: {
        incoming: definition.incoming_message_set,
        notebook: notes.notebook || [],
        notebook_deleted: notes.notebookDeleted || [],
        read_events: notes.msgsRead || [],
        strategy_summary: sanitizeForPsyNet(notes.summary || currentSubjectData().summary || ''),
        outgoing,
      },
      timing: timingData(),
      source: 'upstream_discovery_chains_with_psynet_adapter',
    };
  }

  window.hideAndShowNext = function (hid, sid, display, center = true) {
    if (sid === 'messages' && typeof messages_browse_start_time !== 'undefined') {
      messages_browse_start_time = new Date();
      if (typeof subjectData !== 'undefined' && typeof instruction_start_time !== 'undefined' && instruction_start_time) {
        subjectData.instruction_duration = messages_browse_start_time - instruction_start_time;
      }
    }
    return originalHideAndShowNext(hid, sid, display, center);
  };

  window.handle_submit = function () {
    const composerTextHow = document.getElementById('composer-text-how').value;
    const composerTextRules = document.getElementById('composer-text-rules').value;
    if (composerTextHow === '' || composerTextRules === '') {
      alert('Please type your message in both text areas. You will be bonused for the quality of your message.');
      return;
    }
    if (typeof task_end_time !== 'undefined' && task_end_time && typeof subjectData !== 'undefined') {
      const messageDoneTime = new Date();
      subjectData.composition_duration = messageDoneTime - task_end_time;
    }
    psynet.nextPage(buildAnswer());
  };

  window.discoveryPsyNetAdapter = {
    buildAnswer,
    finishGameForReview: function () {
      if (typeof grid_done === 'function') grid_done();
    },
  };

  function resolveDiscoveryIcon(src) {
    return String(src || '').replace(/^\.\.\/img\//, '/static/discovery-chains/img/');
  }

  if (typeof drawItem === 'function') {
    const upstreamDrawItem = drawItem;
    drawItem = function (itemId, itemIcon, type = 'grid') {
      return upstreamDrawItem(itemId, resolveDiscoveryIcon(itemIcon), type);
    };
  }

  if (typeof nameToIcon === 'function') {
    nameToIcon = function (itemName, size = '24px') {
      let item = items.find((item) => item.item_name === itemName);
      if (item) {
        return `<img src="${resolveDiscoveryIcon(item.item_icon)}" style="width:${size}; height:${size};">`;
      } else {
        return itemName;
      }
    };
  }

  function startAtPsyNetEntryPoint() {
    const welcome = document.getElementById('welcome');
    const prolific = document.getElementById('prolific_id');
    const instruction = document.getElementById('instruction');
    if (welcome) welcome.style.display = 'none';
    if (prolific) prolific.style.display = 'none';
    if (instruction) instruction.style.display = 'block';
    if (typeof subjectData !== 'undefined') {
      subjectData.prolific_id = `psynet-${definition.participant_id || 'participant'}`;
    }
    if (typeof instruction_start_time !== 'undefined') {
      instruction_start_time = new Date();
    }
    if (typeof allowRegeneration !== 'undefined') {
      allowRegeneration = Boolean(discoveryGameConfig.allow_regeneration);
    }
  }

  startAtPsyNetEntryPoint();
})();
