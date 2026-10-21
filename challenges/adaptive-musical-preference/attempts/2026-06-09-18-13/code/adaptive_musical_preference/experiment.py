import math
from statistics import mean

import numpy as np
import psynet.experiment
import soundfile as sf
from dallinger import db
from markupsafe import Markup
from sqlalchemy.orm import object_session

from psynet.asset import OnDemandAsset
from psynet.bot import Bot
from psynet.modular_page import AudioPrompt, ModularPage, PushButtonControl
from psynet.page import InfoPage
from psynet.timeline import Event, PageMaker, Timeline
from psynet.trial.mcmcp import MCMCPNode, MCMCPTrial, MCMCPTrialMaker


N_TRIALS = 8
TARGET_TEMPO = 132
TARGET_BRIGHTNESS = 0.72


class SessionBoundOnDemandAsset(OnDemandAsset):
    def get_url(self):
        if object_session(self) is None:
            db.session.add(self)
        db.session.flush()
        if self.id is None:
            raise RuntimeError("On-demand asset was not assigned an id before URL generation.")
        return f"/on-demand-asset?id={self.id}&secret={self.secret}"


def clamp(value, lower, upper):
    return max(lower, min(upper, value))


def stimulus_id(stimulus):
    return f"tempo-{stimulus['tempo']}_brightness-{stimulus['brightness']:.2f}"


def preference_distance(stimulus):
    tempo_term = abs(stimulus["tempo"] - TARGET_TEMPO) / 60
    brightness_term = abs(stimulus["brightness"] - TARGET_BRIGHTNESS)
    return tempo_term + brightness_term


class PreferenceNode(MCMCPNode):
    def create_initial_seed(self, experiment, participant):
        return {
            "stimulus_id": stimulus_id({"tempo": 108, "brightness": 0.35}),
            "tempo": 108,
            "brightness": 0.35,
        }

    def get_proposal(self, state, experiment, participant):
        tempo_step = 12 if state["tempo"] < TARGET_TEMPO else -6
        brightness_step = 0.12 if state["brightness"] < TARGET_BRIGHTNESS else -0.08
        proposal = {
            "tempo": int(clamp(state["tempo"] + tempo_step, 84, 156)),
            "brightness": round(clamp(state["brightness"] + brightness_step, 0.2, 0.9), 2),
        }
        proposal["stimulus_id"] = stimulus_id(proposal)
        return proposal


def start_nodes(participant):
    return [PreferenceNode(context={"dimensions": ["tempo", "brightness"]})]


class PreferenceTrial(MCMCPTrial):
    time_estimate = 7
    sample_rate = 44100

    def finalize_definition(self, definition, experiment, participant):
        definition = super().finalize_definition(definition, experiment, participant)
        pair_asset = SessionBoundOnDemandAsset(
            function=self.synth_pair,
            extension=".wav",
        )
        self.add_assets({"pair": pair_asset})
        return definition

    def synth_pair(self, path):
        ordered = self.definition["ordered"]
        option_a = self.synth_stimulus(ordered[0]["value"])
        option_b = self.synth_stimulus(ordered[1]["value"])
        silence = np.zeros(int(0.7 * self.sample_rate))
        waveform = np.concatenate([option_a, silence, option_b])
        sf.write(path, waveform, self.sample_rate)

    def synth_stimulus(self, stimulus):
        beat = 60 / stimulus["tempo"]
        note_duration = beat * 0.75
        rest_duration = beat * 0.12
        brightness = stimulus["brightness"]
        frequencies = [261.63, 329.63, 392.00, 523.25, 392.00, 329.63]
        notes = []
        for frequency in frequencies:
            notes.append(self.make_note(frequency, note_duration, brightness))
            notes.append(np.zeros(int(rest_duration * self.sample_rate)))
        return np.concatenate(notes) * 0.55

    def make_note(self, frequency, duration, brightness):
        n_samples = int(duration * self.sample_rate)
        t = np.arange(n_samples) / self.sample_rate
        waveform = np.sin(2 * math.pi * frequency * t)
        waveform += brightness * 0.55 * np.sin(2 * math.pi * frequency * 2 * t)
        waveform += brightness * 0.25 * np.sin(2 * math.pi * frequency * 3 * t)
        envelope = np.ones(n_samples)
        ramp = max(1, int(0.025 * self.sample_rate))
        envelope[:ramp] = np.linspace(0, 1, ramp)
        envelope[-ramp:] = np.linspace(1, 0, ramp)
        return waveform * envelope / (1 + brightness * 0.8)

    def show_trial(self, experiment, participant):
        pair_asset = self.assets["pair"]
        return ModularPage(
            "adaptive_preference_trial",
            AudioPrompt(
                pair_asset,
                Markup(
                    """
                    <p>You will hear <strong>Option A</strong>, a short pause, then
                    <strong>Option B</strong>. Which musical pattern do you prefer?</p>
                    <p>The task adapts by comparing your current preferred region with
                    a nearby tempo/brightness proposal.</p>
                    """
                ),
            ),
            PushButtonControl(
                ["0", "1"],
                labels=["Option A", "Option B"],
                arrange_vertically=False,
                bot_response=self.get_bot_response,
            ),
            events={
                "responseEnable": Event(is_triggered_by="promptEnd"),
                "submitEnable": Event(is_triggered_by="promptEnd"),
            },
            time_estimate=self.time_estimate,
        )

    def get_bot_response(self, bot: Bot):
        distances = [
            preference_distance(item["value"]) for item in self.definition["ordered"]
        ]
        return str(int(distances[1] < distances[0]))


def make_summary_page(participant):
    trials = PreferenceTrial.query.filter_by(participant_id=participant.id).all()
    trials = sorted(trials, key=lambda trial: trial.id)
    completed_trials = [trial for trial in trials if trial.answer]
    if not completed_trials:
        return InfoPage("No completed choices were found.", time_estimate=3)

    chosen = [trial.answer["value"] for trial in completed_trials]
    final_choice = chosen[-1]
    rows = "".join(
        "<tr>"
        f"<td>{i + 1}</td>"
        f"<td>{trial.definition['ordered'][0]['value']['tempo']} BPM / "
        f"{trial.definition['ordered'][0]['value']['brightness']:.2f}</td>"
        f"<td>{trial.definition['ordered'][1]['value']['tempo']} BPM / "
        f"{trial.definition['ordered'][1]['value']['brightness']:.2f}</td>"
        f"<td>Option {'A' if trial.answer['position'] == 0 else 'B'}</td>"
        "</tr>"
        for i, trial in enumerate(completed_trials)
    )
    return InfoPage(
        Markup(
            f"""
            <h3>Your adaptive music summary</h3>
            <p>You made {len(completed_trials)} pairwise choices. Your final preferred
            region was <strong>{final_choice['tempo']} BPM</strong> with brightness
            <strong>{final_choice['brightness']:.2f}</strong>.</p>
            <p>Across your chosen options, the average tempo was
            <strong>{mean(item['tempo'] for item in chosen):.1f} BPM</strong> and the
            average brightness was <strong>{mean(item['brightness'] for item in chosen):.2f}</strong>.</p>
            <table class="table table-sm">
                <thead>
                    <tr><th>Trial</th><th>Option A</th><th>Option B</th><th>Choice</th></tr>
                </thead>
                <tbody>{rows}</tbody>
            </table>
            """
        ),
        time_estimate=10,
    )


class Exp(psynet.experiment.Experiment):
    label = "Adaptive musical preference"
    test_n_bots = 3

    timeline = Timeline(
        InfoPage(
            Markup(
                """
                <h3>Adaptive musical preference task</h3>
                <p>In each trial, listen to two synthesized musical patterns and choose
                the one you prefer. The patterns vary in tempo and brightness, and later
                pairings are chosen near the region you have preferred so far.</p>
                """
            ),
            time_estimate=5,
        ),
        MCMCPTrialMaker(
            id_="adaptive_musical_preference",
            start_nodes=start_nodes,
            trial_class=PreferenceTrial,
            node_class=PreferenceNode,
            chain_type="within",
            expected_trials_per_participant=N_TRIALS,
            max_trials_per_participant=N_TRIALS,
            chains_per_participant=1,
            chains_per_experiment=None,
            max_nodes_per_chain=N_TRIALS,
            trials_per_node=1,
            balance_across_chains=True,
            check_performance_at_end=False,
            check_performance_every_trial=False,
            recruit_mode="n_participants",
            target_n_participants=1,
        ),
        PageMaker(make_summary_page, time_estimate=10),
    )

    def test_check_bot(self, bot: Bot, **kwargs):
        assert not bot.failed
        trials = sorted(bot.all_trials, key=lambda trial: trial.id)
        assert len(trials) == N_TRIALS

        previous_choice = None
        accepted_proposals = 0
        for trial in trials:
            definition = trial.definition
            pair_asset = trial.assets["pair"]
            assert pair_asset.id is not None
            assert "id=None" not in pair_asset.url
            assert f"id={pair_asset.id}" in pair_asset.url
            assert set(definition) >= {"current_state", "proposal", "ordered"}
            assert {item["role"] for item in definition["ordered"]} == {
                "current_state",
                "proposal",
            }
            assert trial.answer["value"] == definition["ordered"][
                trial.answer["position"]
            ]["value"]
            if previous_choice is not None:
                assert definition["current_state"] == previous_choice
            if trial.answer["role"] == "proposal":
                accepted_proposals += 1
            previous_choice = trial.answer["value"]

        assert accepted_proposals >= 2
        final_distance = preference_distance(trials[-1].answer["value"])
        initial_distance = preference_distance(trials[0].definition["current_state"])
        assert final_distance < initial_distance
