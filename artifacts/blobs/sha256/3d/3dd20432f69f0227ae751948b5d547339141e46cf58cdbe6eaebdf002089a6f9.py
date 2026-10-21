import pytest

from experiment import (
    HybridConfig,
    HybridSchedulerState,
    build_color_stimulus,
    call_openrouter_for_slider,
    choose_ai_launch_count,
    parse_ai_slider_response,
    render_ai_prompt,
    render_human_prompt,
    validate_hybrid_config,
)


class FakeModuleState:
    participant_group = "A"


class FakeParticipant:
    module_state = FakeModuleState()


class FakeTrial:
    context = {"target": "banana"}
    initial_vector = [10, 20, 30]
    active_index = 1


def mock_config(**overrides):
    defaults = dict(
        ai_participant_proportion=50,
        target_n_participants=10,
        ai_scheduler_enabled=True,
        ai_scheduler_max_running_bots=4,
        openrouter_api_key_env="OPENROUTER_API_KEY_FOR_TEST",
        openrouter_model="test/model",
        openrouter_base_url="https://openrouter.ai/api/v1",
        openrouter_timeout_seconds=5,
        openrouter_max_retries=1,
        openrouter_mock_mode=True,
    )
    defaults.update(overrides)
    return HybridConfig(**defaults)


def test_prompt_and_human_page_share_color_stimulus():
    stimulus = build_color_stimulus(FakeTrial(), FakeParticipant())

    human_prompt = str(render_human_prompt(stimulus))
    ai_prompt = render_ai_prompt(stimulus)

    assert "banana" in human_prompt
    assert "banana" in ai_prompt
    assert "Participant group = A" in human_prompt
    assert "Participant group: A" in ai_prompt
    assert '"green": 20' in ai_prompt
    assert "Adjust only the green channel" in ai_prompt


def test_parse_ai_slider_response_accepts_only_strict_in_range_json():
    assert parse_ai_slider_response('{"value": 127}') == 127

    with pytest.raises(ValueError):
        parse_ai_slider_response("127")
    with pytest.raises(ValueError):
        parse_ai_slider_response('{"value": 256}')
    with pytest.raises(ValueError):
        parse_ai_slider_response('{"value": true}')
    with pytest.raises(ValueError):
        parse_ai_slider_response('{"value": 127, "reason": "extra"}')


def test_hybrid_config_validation_rejects_bad_values(monkeypatch):
    validate_hybrid_config(mock_config())

    with pytest.raises(ValueError):
        validate_hybrid_config(mock_config(ai_participant_proportion=-1))
    with pytest.raises(ValueError):
        validate_hybrid_config(mock_config(ai_participant_proportion=101))
    with pytest.raises(ValueError):
        validate_hybrid_config(mock_config(target_n_participants=None))
    with pytest.raises(ValueError):
        validate_hybrid_config(mock_config(ai_scheduler_max_running_bots=0))
    with pytest.raises(ValueError):
        validate_hybrid_config(mock_config(openrouter_timeout_seconds=0))
    with pytest.raises(ValueError):
        validate_hybrid_config(mock_config(openrouter_mock_mode=False))

    monkeypatch.setenv("OPENROUTER_API_KEY_FOR_TEST", "safe-test-token")
    validate_hybrid_config(mock_config(openrouter_mock_mode=False))


def test_mock_openrouter_path_returns_valid_slider_response():
    stimulus = build_color_stimulus(FakeTrial(), FakeParticipant())
    value, metadata = call_openrouter_for_slider(stimulus, mock_config())

    assert 0 <= value <= 255
    assert metadata["controller"] == "ai"
    assert metadata["mock_mode"] is True
    assert metadata["parser_status"] == "mock"


def test_incremental_scheduler_launch_count():
    assert (
        choose_ai_launch_count(
            HybridSchedulerState(
                human_count=0,
                ai_count=0,
                running_ai_count=0,
                participant_target=10,
            ),
            target_proportion=50,
        )
        == 0
    )
    assert (
        choose_ai_launch_count(
            HybridSchedulerState(
                human_count=1,
                ai_count=0,
                running_ai_count=0,
                participant_target=10,
            ),
            target_proportion=50,
        )
        == 1
    )
    assert (
        choose_ai_launch_count(
            HybridSchedulerState(
                human_count=3,
                ai_count=1,
                running_ai_count=0,
                participant_target=10,
            ),
            target_proportion=50,
        )
        == 2
    )
    assert (
        choose_ai_launch_count(
            HybridSchedulerState(
                human_count=0,
                ai_count=0,
                running_ai_count=0,
                participant_target=6,
            ),
            target_proportion=100,
        )
        == 6
    )
    assert (
        choose_ai_launch_count(
            HybridSchedulerState(
                human_count=4,
                ai_count=4,
                running_ai_count=1,
                participant_target=10,
            ),
            target_proportion=50,
        )
        == 0
    )
