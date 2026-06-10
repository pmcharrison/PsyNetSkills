import pytest

from experiment import (
    HybridSettings,
    build_ai_prompt,
    build_bot_response,
    build_color_stimulus,
    build_human_prompt,
    parse_ai_slider_answer,
    plan_ai_launches,
)


def test_pure_human_setting_launches_no_ai():
    settings = HybridSettings(ai_proportion=0, target_n_participants=6)

    assert plan_ai_launches(3, 0, settings, remaining_trial_capacity=3) == 0


def test_mixed_setting_launches_only_needed_ai_bots():
    settings = HybridSettings(ai_proportion=50, target_n_participants=6)

    assert plan_ai_launches(1, 0, settings, remaining_trial_capacity=5) == 1
    assert plan_ai_launches(2, 1, settings, remaining_trial_capacity=3) == 1
    assert plan_ai_launches(1, 1, settings, remaining_trial_capacity=4) == 0


def test_all_ai_setting_starts_gradually_and_respects_capacity():
    settings = HybridSettings(ai_proportion=100, target_n_participants=4)

    assert plan_ai_launches(0, 0, settings, remaining_trial_capacity=4) == 1
    assert plan_ai_launches(0, 3, settings, remaining_trial_capacity=1) == 1
    assert plan_ai_launches(0, 4, settings, remaining_trial_capacity=0) == 0


@pytest.mark.parametrize("ai_proportion", [-1, 101])
def test_ai_proportion_validation(ai_proportion):
    with pytest.raises(ValueError, match="hybrid_ai_proportion"):
        HybridSettings(ai_proportion=ai_proportion).validate()


def test_scheduler_respects_target_and_trial_capacity():
    settings = HybridSettings(ai_proportion=80, target_n_participants=5)

    assert plan_ai_launches(4, 0, settings, remaining_trial_capacity=1) == 1
    assert plan_ai_launches(4, 0, settings, remaining_trial_capacity=0) == 0
    assert plan_ai_launches(1, 4, settings, remaining_trial_capacity=5) == 0


def test_human_and_ai_prompts_share_the_same_stimulus():
    stimulus = build_color_stimulus("banana", selected_idx=1, starting_values=[10, 20, 30])

    human_prompt = str(build_human_prompt(stimulus, participant_group="A"))
    ai_prompt = build_ai_prompt(stimulus, participant_group="A")

    assert "banana" in human_prompt
    assert "banana" in ai_prompt
    assert "Participant group = A" in human_prompt
    assert "Participant group: A" in ai_prompt
    assert '"green": 20' in ai_prompt
    assert "Only the green channel" in ai_prompt


def test_ai_answer_parser_is_conservative():
    assert parse_ai_slider_answer('{"answer": 128}') == 128
    assert parse_ai_slider_answer("42") == 42

    with pytest.raises(ValueError):
        parse_ai_slider_answer('{"answer": 256}')
    with pytest.raises(ValueError):
        parse_ai_slider_answer('{"answer": 10, "extra": true}')
    with pytest.raises(ValueError):
        parse_ai_slider_answer("move the slider to 42")


def test_mock_ai_response_matches_slider_answer_format():
    settings = HybridSettings(ai_proportion=100, openrouter_mock=True)
    stimulus = build_color_stimulus("tree", selected_idx=2, starting_values=[10, 20, 30])

    response = build_bot_response(
        stimulus=stimulus,
        participant_group="B",
        is_ai_participant=True,
        settings=settings,
    )

    assert 0 <= response.answer <= 255
    assert response.metadata["participant_type"] == "ai"
    assert response.metadata["openrouter_mock"] is True
    assert response.metadata["stimulus"] == stimulus
