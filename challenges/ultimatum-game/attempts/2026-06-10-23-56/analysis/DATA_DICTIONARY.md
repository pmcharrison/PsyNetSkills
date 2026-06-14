# Data dictionary

These columns describe the processed repeated Ultimatum game export.

| Column | Description |
| --- | --- |
| `deployment_id` | Exported PsyNet deployment identifier; used as the experimental batch ID. |
| `export_scope` | Archive namespace used as input, normally regular. |
| `session_id` | UltimatumSession row ID in the export. |
| `dyad_id` | Stable dyad identifier, equal to the PsyNet sync group/session group_id. |
| `sync_group_id` | SimpleSyncGroup row ID joined from dyad_id. |
| `round_index` | Round number from the session history, including skipped timeout rounds. |
| `history_index` | Zero-based position of the round in UltimatumSession.state_json.history. |
| `counted_round_index` | One-based index among non-skipped scored rounds; blank for skipped rounds. |
| `round_counted` | True when the round produced a scored decision and counted toward completion. |
| `round_skipped` | True when the round was skipped, currently because of a timeout. |
| `timeout_role` | Role that timed out for skipped rounds; blank otherwise. |
| `decision` | Round decision: accept, reject, or timeout. |
| `offer` | Coin offer made by the proposer; blank if no offer was accepted by the server. |
| `offer_fraction` | Offer divided by the 10-coin endowment when offer is present. |
| `accepted` | True for accepted offers, False for rejected offers, blank for skipped rounds. |
| `participant_id` | PsyNet participant ID for this player row. |
| `player_order` | Stable zero-based order from the session participant list sorted by participant ID. |
| `role` | Participant role in this round: proposer or responder. |
| `partner_participant_id` | The other participant in the dyad. |
| `partner_role` | Partner role in this round. |
| `player_action_type` | Player-level action represented by the row: offer, decision, timeout, or partner_timeout. |
| `player_action_value` | Offer amount, decision value, or timeout marker matching player_action_type. |
| `player_timed_out` | True when this participant held the role that timed out. |
| `partner_timed_out` | True when the partner held the role that timed out. |
| `player_round_score` | Coins earned by the participant in this round. |
| `partner_round_score` | Coins earned by the partner in this round. |
| `dyad_round_score` | Sum of both players' round scores. |
| `player_cumulative_score` | Participant cumulative score after this round. |
| `partner_cumulative_score` | Partner cumulative score after this round. |
| `player_final_score` | Participant final score from the completed session state. |
| `partner_final_score` | Partner final score from the completed session state. |
| `session_counted_rounds` | Final counted-round total recorded in the session state. |
| `session_timeout_count` | Final timeout count recorded in the session state. |
| `session_status` | Final session status, such as complete or failed. |
| `completion_reason` | Final completion reason recorded in the session state. |
| `trial_id` | GameTrial row ID for this participant's live game trial. |
| `response_id` | Response row ID associated with the participant's GameTrial answer. |
| `trial_failed` | Failure flag on the participant's GameTrial row. |
| `participant_failed` | Failure flag on the Participant row. |
| `participant_status` | Participant status from the export. |
| `performance_reward` | Participant performance reward recorded by PsyNet. |
| `round_events_json` | JSON list of session events with this round_index. |
| `round_state_json` | Original JSON object for this history round. |
| `proposer_id` | Participant assigned as proposer in the round. |
| `responder_id` | Participant assigned as responder in the round. |
| `proposer_payoff` | Coins earned by the proposer in the round. |
| `responder_payoff` | Coins earned by the responder in the round. |
| `proposer_cumulative_score` | Proposer cumulative score after this round. |
| `responder_cumulative_score` | Responder cumulative score after this round. |
