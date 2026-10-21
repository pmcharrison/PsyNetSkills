import random

from adaptive_policy import (
    MAX_SEQUENCE_LENGTH,
    MIN_SEQUENCE_LENGTH,
    MemoryObservation,
    choose_length,
    simulate_response,
    state_summary,
)


def run_synthetic_participant(ability, n_trials=10):
    rng = random.Random(int(ability * 1000))
    observations = []
    state = None
    rows = []
    for trial_index in range(n_trials):
        selection = choose_length(observations, state, adaptive=True, rng=rng)
        response = simulate_response(selection.target, ability, rng)
        correct = response == selection.target
        observations.append(MemoryObservation(selection.length, correct))
        state = selection.posterior_state
        rows.append(
            {
                "trial": trial_index + 1,
                "ability": ability,
                "length": selection.length,
                "correct": correct,
                "acquisition": round(selection.selected_acquisition_value, 5),
                **{
                    key: round(value, 4)
                    for key, value in state_summary(selection.posterior_state).items()
                },
            }
        )
    return rows


def main():
    for ability in [0.45, 1.0, 2.5]:
        rows = run_synthetic_participant(ability)
        assert len(rows) == 10
        assert all(MIN_SEQUENCE_LENGTH <= row["length"] <= MAX_SEQUENCE_LENGTH for row in rows)
        assert all("mu_mean" in row and "alpha_mean" in row and "r_mean" in row for row in rows)
        print(f"ability={ability}")
        for row in rows:
            print(row)


if __name__ == "__main__":
    main()
