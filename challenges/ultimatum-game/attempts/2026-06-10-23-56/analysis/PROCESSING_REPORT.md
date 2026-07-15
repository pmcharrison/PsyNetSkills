# Ultimatum export processing report

## Source

- Export archive: `/workspace/challenges/ultimatum-game/attempts/2026-06-10-23-56/evidence/data.zip`
- Export scope: `regular`
- Authoritative round ledger: `regular/data/UltimatumSession.csv` field `state_json.history`.
- Trial audit pointers: `regular/data/GameTrial.csv` fields `id`, `response_id`, and `answer`.
- Participant audit pointers: `regular/data/Participant.csv` fields `failed`, `status`, and `performance_reward`.

## Source table counts

- `ExperimentConfig`: 1
- `GameTrial`: 2
- `Participant`: 4
- `ParticipantLinkSyncGroup`: 2
- `SimpleSyncGroup`: 1
- `UltimatumSession`: 1

## Missingness and exclusions

- Completed participants represented in dyadic rows: 2.
- Failed pre-pairing participants excluded from dyadic rows: 2.
- Skipped timeout rounds are retained with `round_skipped=true`, `decision=timeout`, zero round scores, and blank `counted_round_index`.
- There were no accepted server actions for timed-out rounds in the session event log; the timeout role is represented as `player_action_type=timeout` for the timed-out role and `partner_timeout` for the other player.

## Player-round preview

| dyad_id | round_index | participant_id | role | partner_participant_id | player_action_type | player_action_value | player_round_score | player_cumulative_score | round_skipped |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 1 | 3 | responder | 4 | partner_timeout | partner_timeout | 0 | 0 | true |
| 1 | 1 | 4 | proposer | 3 | timeout | timeout | 0 | 0 | true |
| 1 | 2 | 3 | responder | 4 | decision | accept | 4 | 4 | false |
| 1 | 2 | 4 | proposer | 3 | offer | 4 | 6 | 6 | false |

## Round-level preview

| dyad_id | round_index | proposer_id | responder_id | offer | decision | round_skipped | dyad_round_score |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 1 | 4 | 3 |  | timeout | true | 0 |
| 1 | 2 | 4 | 3 | 4 | accept | false | 10 |

## Validation

- PASS: 2 dyad-round(s) each have exactly two player rows.
- PASS: no duplicate participant rows within dyad-rounds.
- PASS: partner fields are symmetric.
- PASS: player and partner round scores sum to dyad round scores.
- PASS: final GameTrial answer scores match session totals.
- PASS: round_level.csv has one row for each of 2 dyad-round(s).

## Outputs

- `clean_round_player.csv`: one row per dyad, round, and player.
- `round_level.csv`: one row per dyad and round.
- `DATA_DICTIONARY.md`: column definitions for both processed tables.
