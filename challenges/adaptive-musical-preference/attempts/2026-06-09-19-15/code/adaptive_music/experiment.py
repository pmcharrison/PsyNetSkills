import math
import random
import wave
from statistics import mean

import numpy as np
import psynet.experiment
from dominate import tags
from markupsafe import Markup
from psynet.asset import OnDemandAsset
from psynet.bot import Bot
from psynet.consent import MainConsent
from psynet.modular_page import AudioPrompt, PushButtonControl
from psynet.page import InfoPage, ModularPage
from psynet.timeline import PageMaker, Timeline
from psynet.trial.mcmcp import MCMCPNode, MCMCPTrial, MCMCPTrialMaker

TEMPOS = [84, 96, 108, 120, 132, 144]
BRIGHTNESSES = [1, 2, 3, 4, 5]
N_CHAINS = 2
CHAIN_LENGTH = 6
TRIALS_PER_PARTICIPANT = N_CHAINS * CHAIN_LENGTH


def clamp(value, values):
    return min(max(value, min(values)), max(values))


def stimulus_label(stimulus):
    return f"{stimulus['tempo']} BPM, brightness {stimulus['brightness']}/5"


def utility(stimulus):
    """Bot preference model used only for automated validation."""
    tempo_penalty = abs(stimulus["tempo"] - 120) / 12
    brightness_penalty = abs(stimulus["brightness"] - 4)
    return -(tempo_penalty + 0.8 * brightness_penalty)


def synth_clip(stimulus, sample_rate=44100):
    tempo = stimulus["tempo"]
    brightness = stimulus["brightness"]
    iois = 60.0 / tempo
    melody = [60, 64, 67, 72, 67, 64]
    clip = []

    for pitch in melody:
        duration = iois * 0.82
        silence = iois * 0.18
        t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
        frequency = 440 * 2 ** ((pitch - 69) / 12)
        tone = np.zeros_like(t)
        for harmonic in range(1, 6):
            weight = (brightness / 5) ** (harmonic - 1) / harmonic
            tone += weight * np.sin(2 * np.pi * frequency * harmonic * t)
        tone = tone / max(np.max(np.abs(tone)), 1e-9)
        attack = min(int(0.02 * sample_rate), len(tone) // 2)
        release = attack
        envelope = np.ones_like(tone)
        if attack:
            envelope[:attack] = np.linspace(0, 1, attack)
            envelope[-release:] = np.linspace(1, 0, release)
        clip.append(0.28 * tone * envelope)
        clip.append(np.zeros(int(sample_rate * silence)))

    return np.concatenate(clip)


def synth_pair(path, ordered):
    sample_rate = 44100
    first = synth_clip(ordered[0]["value"], sample_rate)
    second = synth_clip(ordered[1]["value"], sample_rate)
    gap = np.zeros(int(sample_rate * 0.8))
    waveform = np.concatenate([first, gap, second])
    waveform = np.int16(np.clip(waveform, -1, 1) * 32767)
    with wave.open(str(path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(sample_rate)
        output.writeframes(waveform.tobytes())


class PreferenceTrial(MCMCPTrial):
    time_estimate = 12

    def finalize_definition(self, definition, experiment, participant):
        pair_audio = OnDemandAsset(
            function=synth_pair,
            extension=".wav",
        )
        self.add_assets(
            {
                "pair_audio": pair_audio,
            }
        )
        # PsyNet 12.2 computes on-demand URLs before insert; recompute after add.
        pair_audio.url = pair_audio.get_url()
        return definition

    def show_trial(self, experiment, participant):
        labels = [
            f"First clip ({stimulus_label(self.first_stimulus)})",
            f"Second clip ({stimulus_label(self.second_stimulus)})",
        ]
        prompt = AudioPrompt(
            self.assets["pair_audio"],
            Markup(
                """
                <p>Listen to the two short musical clips. They differ in tempo
                and brightness. Which clip would you rather hear again?</p>
                <p>The clips play as: first clip, a short pause, then second clip.</p>
                """
            ),
            controls={"Play from start": "Replay pair"},
        )
        return ModularPage(
            "adaptive_music_choice",
            prompt,
            PushButtonControl(
                ["0", "1"],
                labels=labels,
                arrange_vertically=True,
                bot_response=self.get_bot_response,
            ),
            time_estimate=self.time_estimate,
        )

    def get_bot_response(self, bot: Bot):
        first_score = utility(self.first_stimulus)
        second_score = utility(self.second_stimulus)
        if math.isclose(first_score, second_score):
            return random.choice(["0", "1"])
        return "0" if first_score > second_score else "1"


class PreferenceNode(MCMCPNode):
    def create_initial_seed(self, experiment, participant):
        return {
            "tempo": random.choice(TEMPOS),
            "brightness": random.choice(BRIGHTNESSES),
        }

    def get_proposal(self, state, experiment, participant):
        tempo_step = random.choice([-24, -12, 12, 24])
        brightness_step = random.choice([-1, 1])
        return {
            "tempo": clamp(state["tempo"] + tempo_step, TEMPOS),
            "brightness": clamp(state["brightness"] + brightness_step, BRIGHTNESSES),
        }


def start_nodes(participant):
    seeds = [
        {"tempo": TEMPOS[0], "brightness": BRIGHTNESSES[0]},
        {"tempo": TEMPOS[-1], "brightness": BRIGHTNESSES[-1]},
    ]
    return [
        PreferenceNode(seed=seeds[chain_index], context={"chain_index": chain_index})
        for chain_index in range(N_CHAINS)
    ]


def participant_summary(participant):
    trials = (
        PreferenceTrial.query.filter_by(participant_id=participant.id, complete=True)
        .order_by(PreferenceTrial.id)
        .all()
    )
    choices = [trial.answer["value"] for trial in trials if trial.answer]
    if choices:
        avg_tempo = round(mean(choice["tempo"] for choice in choices), 1)
        avg_brightness = round(mean(choice["brightness"] for choice in choices), 1)
        final_choice = stimulus_label(choices[-1])
    else:
        avg_tempo = "not available"
        avg_brightness = "not available"
        final_choice = "not available"

    rows = [
        tags.li(f"Choices recorded: {len(choices)}"),
        tags.li(f"Average chosen tempo: {avg_tempo} BPM"),
        tags.li(f"Average chosen brightness: {avg_brightness}/5"),
        tags.li(f"Final selected region: {final_choice}"),
    ]
    return InfoPage(
        tags.div(
            tags.h3("Your preference summary"),
            tags.p(
                "The adaptive sampler moved toward the musical region you chose "
                "more often during the pairwise task."
            ),
            tags.ul(*rows),
        ),
        time_estimate=8,
    )


class Exp(psynet.experiment.Experiment):
    label = "Adaptive musical preference"
    test_n_bots = 3

    timeline = Timeline(
        MainConsent(),
        InfoPage(
            Markup(
                """
                <p>You will hear pairs of short synthesized musical clips.</p>
                <p>Each clip varies along two dimensions: tempo and brightness.
                After each pair, choose the clip you prefer. Later pairs adapt
                toward the regions you have selected.</p>
                """
            ),
            time_estimate=8,
        ),
        MCMCPTrialMaker(
            id_="adaptive_music",
            start_nodes=start_nodes,
            trial_class=PreferenceTrial,
            node_class=PreferenceNode,
            chain_type="within",
            expected_trials_per_participant=TRIALS_PER_PARTICIPANT,
            max_trials_per_participant=TRIALS_PER_PARTICIPANT,
            chains_per_participant=N_CHAINS,
            chains_per_experiment=None,
            max_nodes_per_chain=CHAIN_LENGTH,
            trials_per_node=1,
            balance_across_chains=True,
            check_performance_at_end=False,
            check_performance_every_trial=False,
            recruit_mode="n_participants",
            target_n_participants=3,
        ),
        PageMaker(participant_summary, time_estimate=8),
        InfoPage("Thank you for taking part!", time_estimate=3),
    )

    def test_check_bot(self, bot: Bot, **kwargs):
        trials = (
            PreferenceTrial.query.filter_by(participant_id=bot.id, complete=True)
            .order_by(PreferenceTrial.id)
            .all()
        )
        assert len(trials) == TRIALS_PER_PARTICIPANT
        for trial in trials:
            assert "current_state" in trial.definition
            assert "proposal" in trial.definition
            assert trial.assets["pair_audio"].id is not None
            assert "id=None" not in trial.assets["pair_audio"].url
            assert trial.answer["value"] in [
                trial.definition["current_state"],
                trial.definition["proposal"],
            ]


if __name__ == "__main__":
    print("Stimulus space")
    for tempo in TEMPOS:
        for brightness in BRIGHTNESSES:
            print(f"- {tempo} BPM, brightness {brightness}/5")
