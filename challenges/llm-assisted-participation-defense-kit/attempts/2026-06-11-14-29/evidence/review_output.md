# Participant manual-review output

This script flags participants for human inspection only. It does not reject participants and does not claim that telemetry proves AI use, automation, or platform fraud.

- `P001` (attentive_human_like): routine review. Signals: none.
- `P002` (inattentive): FLAG FOR REVIEW. Signals: failed checks: attention_color.
- `P003` (paste_heavy): FLAG FOR REVIEW. Signals: high paste count: 24.
- `P004` (fast_low_effort): FLAG FOR REVIEW. Signals: failed checks: attention_color, comprehension_source; very short response latencies on 8 pages.
- `P005` (mock_llm_assisted): FLAG FOR REVIEW. Signals: high paste count: 8; probe response needs inspection: probe_strategy, probe_assistance, probe_confidence.
- `P006` (browser_agent_like): FLAG FOR REVIEW. Signals: very short response latencies on 8 pages; sparse text-production telemetry: task_river_garden, task_library_hours, task_bike_racks, comprehension_source, probe_strategy, probe_assistance, probe_confidence.
