/* PsyNet adapter for upstream js/config.js.
 * This file keeps the upstream global variable contract but sources condition,
 * item layout, and action budget from the PsyNet ChainTrial definition.
 */
const discoveryDefinition = window.discoveryTrialDefinition;
const discoveryGameConfig = discoveryDefinition.game_config;

const MAX_ACTIONS = discoveryGameConfig.action_budget;
const gridSize = discoveryGameConfig.grid_size;
const conditions = discoveryDefinition.run_parameters.conditions;
const COND = discoveryDefinition.condition === "hard" ? "hard-1" : discoveryDefinition.condition;

let items = discoveryGameConfig.items.map(item => ({
  item_name: item.item_name,
  x: item.x,
  y: item.y,
  item_level: item.item_level,
  item_icon: `/static/discovery-chains/img/${item.item_name}.svg`
}));
let transitions = [];
let ACTIONS = MAX_ACTIONS;
let POINTS = 0;
const MAXLEVEL = discoveryGameConfig.max_level;

let token = `psynet-${discoveryDefinition.participant_id || 'participant'}`;
let playerPosition = { ...discoveryGameConfig.player_start };
getEl('task-info-actions').innerHTML = ACTIONS;
getEl('task-info-points').innerHTML = POINTS;

let baseItems = discoveryGameConfig.items.filter(item => item.item_level === 0).map(item => item.item_name);
let shapes = discoveryGameConfig.shapes;
let textures = discoveryGameConfig.textures;

window.discoveryMessagesByCondition = {
  [COND]: discoveryDefinition.incoming_message_set.messages || []
};
