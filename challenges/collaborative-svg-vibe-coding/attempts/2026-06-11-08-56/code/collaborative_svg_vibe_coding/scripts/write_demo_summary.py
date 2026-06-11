import json
import sys
from pathlib import Path

from experiment import ROLE_CONDITIONS, simulate_condition_summaries


def main() -> None:
    output = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("demo_summary.json")
    payload = {
        "role_conditions": ROLE_CONDITIONS,
        "condition_summaries": simulate_condition_summaries(),
        "mock_ai_mode": True,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"wrote {output}")


if __name__ == "__main__":
    main()
