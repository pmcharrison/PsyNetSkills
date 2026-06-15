# Live scheduler distribution report

## Configuration

- Target AI proportion: 50%
- Target participants: 2
- AI scheduler enabled: true
- Maximum running AI bots: 1
- OpenRouter mode: deterministic mock (`openrouter_mock_mode = true`)

## Procedure

A Playwright browser participant entered through the normal `/ad` recruitment route, selected group `A`, completed the Gibbs color-slider trials, and reached recruiter completion. The scheduler was enabled during the run and launched an AI bot through PsyNet's bot flow.

## Actual distribution

| Controller | Count |
|---|---:|
| Human | 1 |
| AI | 1 |
| Total | 2 |

Actual AI proportion: 50%.

## Participant rows

| Participant id | Type | Controller | AI profile | Group | Status | Failed | Finalized trials |
|---:|---|---|---|---|---|---|---:|
| 1 | Participant | human | none | A | approved | False | 7/7 |
| 2 | Bot | ai | mock_openrouter | A | approved | False | 7/7 |

## Notes

The AI participant is a mock-OpenRouter bot. This run validates live scheduling and data-path behavior without using real API credentials.
