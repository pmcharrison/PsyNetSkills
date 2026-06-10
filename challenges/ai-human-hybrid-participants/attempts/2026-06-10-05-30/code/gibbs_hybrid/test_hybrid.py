import pytest

from experiment import (
    COLORS,
    HybridParticipantScheduler,
    _validate_nonnegative_int,
    _validate_percentage,
    build_ai_prompt,
    deterministic_slider_answer,
    make_color_slider_stimulus,
    parse_ai_slider_answer,
)


def test_pure_human_assignment_has_no_ai_slots():
    assignments = HybridParticipantScheduler.planned_assignments(
        total_participants=8, proportion=0
    )

    assert assignments == ["human"] * 8
    assert HybridParticipantScheduler.ai_bots_to_launch(0, 8, 0) == 0


def test_nonzero_ai_proportion_balances_assignments():
    assignments = HybridParticipantScheduler.planned_assignments(
        total_participants=6, proportion=50
    )

    assert assignments.count("ai") == 3
    assert assignments.count("human") == 3
    assert HybridParticipantScheduler.ai_bots_to_launch(1, 6, 50) == 2


def test_all_ai_assignment_uses_only_ai_slots():
    assignments = HybridParticipantScheduler.planned_assignments(
        total_participants=5, proportion=100
    )

    assert assignments == ["ai"] * 5
    assert HybridParticipantScheduler.ai_bots_to_launch(0, 5, 100) == 5


@pytest.mark.parametrize("value", [-1, 101])
def test_percentage_validation_rejects_out_of_range_values(value):
    with pytest.raises((AssertionError, ValueError)):
        _validate_percentage(value)
    with pytest.raises(ValueError):
        HybridParticipantScheduler.validate_proportion(value)


def test_target_total_validation_rejects_negative_values():
    with pytest.raises(AssertionError):
        _validate_nonnegative_int(-1)
    with pytest.raises(ValueError):
        HybridParticipantScheduler.target_ai_count(-1, 50)


def test_prompt_uses_same_stimulus_values_as_human_display():
    stimulus = make_color_slider_stimulus(
        target="banana",
        selected_idx=COLORS.index("green"),
        starting_values=[240, 100, 45],
        participant_group="A",
    )
    messages = build_ai_prompt(stimulus)
    prompt_text = "\n".join(message["content"] for message in messages)

    assert '"target_word": "banana"' in prompt_text
    assert '"active_color": "green"' in prompt_text
    assert '"green": 100' in prompt_text
    assert '"participant_group": "A"' in prompt_text


def test_ai_answer_parsing_accepts_json_and_rejects_bad_values():
    assert parse_ai_slider_answer('{"answer": 123}') == 123
    assert parse_ai_slider_answer("I would set it to 77.") == 77

    with pytest.raises(ValueError):
        parse_ai_slider_answer('{"answer": 300}')
    with pytest.raises(ValueError):
        parse_ai_slider_answer("no numeric answer")


def test_deterministic_fallback_returns_active_color_channel():
    stimulus = make_color_slider_stimulus(
        target="carrot",
        selected_idx=COLORS.index("red"),
        starting_values=[0, 0, 0],
        participant_group="B",
    )

    assert deterministic_slider_answer(stimulus) == 235
