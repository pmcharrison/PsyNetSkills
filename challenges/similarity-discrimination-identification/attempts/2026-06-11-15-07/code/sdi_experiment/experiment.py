# pylint: disable=abstract-method,unused-argument

import math
import os
import random
from datetime import datetime
from itertools import combinations_with_replacement

import psynet.experiment
from markupsafe import Markup
from psynet.bot import Bot
from psynet.demography.general import BasicDemography
from psynet.graphics import Circle, Frame, GraphicPrompt, Text
from psynet.modular_page import ModularPage, PushButtonControl
from psynet.page import InfoPage
from psynet.prescreen import ColorBlindnessTest
from psynet.timeline import Timeline
from psynet.trial.static import StaticNode, StaticTrial, StaticTrialMaker

FIXATION_SECONDS = 0.6
STIMULUS_SECONDS = 1.0
DELAY_SECONDS = 0.7
PROFILE = os.environ.get("PSYNET_PROFILE", "full")
STIMULI = [{'stimulus_id': 'red', 'label': 'Red', 'dimensions': {'color': {'hex': '#d73027', 'hue_degrees': 5, 'lightness': 48}, 'size': {'radius_px': 24}, 'shape': 'filled_circle'}},
    {'stimulus_id': 'orange', 'label': 'Orange', 'dimensions': {'color': {'hex': '#fc8d59', 'hue_degrees': 24, 'lightness': 67}, 'size': {'radius_px': 24}, 'shape': 'filled_circle'}},
    {'stimulus_id': 'yellow', 'label': 'Yellow', 'dimensions': {'color': {'hex': '#fee08b', 'hue_degrees': 50, 'lightness': 77}, 'size': {'radius_px': 24}, 'shape': 'filled_circle'}},
    {'stimulus_id': 'green', 'label': 'Green', 'dimensions': {'color': {'hex': '#91cf60', 'hue_degrees': 104, 'lightness': 59}, 'size': {'radius_px': 24}, 'shape': 'filled_circle'}},
    {'stimulus_id': 'blue', 'label': 'Blue', 'dimensions': {'color': {'hex': '#4575b4', 'hue_degrees': 212, 'lightness': 49}, 'size': {'radius_px': 24}, 'shape': 'filled_circle'}},
    {'stimulus_id': 'purple', 'label': 'Purple', 'dimensions': {'color': {'hex': '#7b3294', 'hue_degrees': 286, 'lightness': 39}, 'size': {'radius_px': 24}, 'shape': 'filled_circle'}}]


def load_stimuli():
    return STIMULI


def stimulus_by_id():
    return {stimulus["stimulus_id"]: stimulus for stimulus in load_stimuli()}


def minimal(nodes, n):
    return nodes[:n] if PROFILE == "minimal" else nodes


def hue_distance(stimulus_a, stimulus_b):
    hue_a = stimulus_a["dimensions"]["color"]["hue_degrees"]
    hue_b = stimulus_b["dimensions"]["color"]["hue_degrees"]
    delta = abs(hue_a - hue_b) % 360
    return min(delta, 360 - delta)


def circle(stimulus, x, y, id_suffix):
    return Circle(
        f"circle_{id_suffix}",
        x,
        y,
        radius=stimulus["dimensions"]["size"]["radius_px"],
        attributes={
            "fill": stimulus["dimensions"]["color"]["hex"],
            "stroke": "#333333",
            "stroke-width": 1.5,
        },
    )


def circle_html(stimulus, label=None):
    size = stimulus["dimensions"]["size"]["radius_px"] * 2
    color = stimulus["dimensions"]["color"]["hex"]
    label_html = f"<span class='sdi-circle-label'>{label}</span>" if label else ""
    return (
        "<span class='sdi-circle' "
        f"style='width:{size}px;height:{size}px;background:{color};'>"
        f"{label_html}</span>"
    )


def timed_prompt_html(trial_id, instructions, stimulus_html, response_html):
    root_id = "sdi_" + "".join(ch if ch.isalnum() else "_" for ch in trial_id)
    delay_ms = int((FIXATION_SECONDS + STIMULUS_SECONDS + DELAY_SECONDS) * 1000)
    stimulus_ms = int(FIXATION_SECONDS * 1000)
    blank_ms = int((FIXATION_SECONDS + STIMULUS_SECONDS) * 1000)
    return f"""
<div id="{root_id}" class="sdi-task">
  <p>{instructions}</p>
  <div class="sdi-stage">
    <div class="sdi-phase sdi-fixation">+</div>
    <div class="sdi-phase sdi-stimulus">{stimulus_html}</div>
    <div class="sdi-phase sdi-blank"></div>
    <div class="sdi-phase sdi-response">{response_html}</div>
  </div>
</div>
<style>
  .sdi-stage {{ min-height: 260px; display: flex; align-items: center; justify-content: center; }}
  .sdi-phase {{ display: none; text-align: center; width: 100%; }}
  .sdi-fixation {{ font-size: 56px; font-weight: bold; line-height: 260px; }}
  .sdi-circle {{ border-radius: 50%; border: 2px solid #333; display: inline-flex; align-items: center; justify-content: center; margin: 16px 32px; vertical-align: middle; }}
  .sdi-circle-label {{ font-weight: bold; color: #111; font-size: 18px; }}
  .sdi-response-note {{ font-size: 18px; margin-top: 20px; }}
  .push-button.response {{ visibility: hidden; }}
</style>
<script>
(function() {{
  function setResponsesVisible(show) {{
    document.querySelectorAll(".push-button.response, button.response").forEach(function(button) {{
      button.disabled = !show;
      button.style.visibility = show ? "visible" : "hidden";
    }});
  }}
  function showPhase(root, name) {{
    root.querySelectorAll(".sdi-phase").forEach(function(phase) {{ phase.style.display = "none"; }});
    root.querySelector("." + name).style.display = "block";
  }}
  function startSdiTrial() {{
    var root = document.getElementById("{root_id}");
    if (!root) return;
    setResponsesVisible(false);
    showPhase(root, "sdi-fixation");
    window.setTimeout(function() {{ showPhase(root, "sdi-stimulus"); }}, {stimulus_ms});
    window.setTimeout(function() {{ showPhase(root, "sdi-blank"); }}, {blank_ms});
    window.setTimeout(function() {{
      showPhase(root, "sdi-response");
      setResponsesVisible(true);
      if (window.psynet && psynet.trial && psynet.trial.registerEvent) {{
        psynet.trial.registerEvent("sdiResponseEnable");
      }}
    }}, {delay_ms});
  }}
  if (document.readyState === "loading") {{
    document.addEventListener("DOMContentLoaded", startSdiTrial);
  }} else {{
    window.setTimeout(startSdiTrial, 0);
  }}
}})();
</script>
"""


def pair_prompt_html(definition, instructions):
    stimulus_html = (
        circle_html(definition["stimulus_a"])
        + circle_html(definition["stimulus_b"])
    )
    return timed_prompt_html(
        definition["trial_id"],
        instructions,
        stimulus_html,
        "<div class='sdi-response-note'>The circles have disappeared. Answer using the buttons below.</div>",
    )


def identification_prompt_html(definition, instructions):
    display_html = "".join(
        circle_html(item["stimulus"], label=item["number"])
        for item in definition["display_items"]
    )
    response_html = (
        circle_html(definition["probe_stimulus"])
        + "<div class='sdi-response-note'>Probe: choose the display number that best matches.</div>"
    )
    return timed_prompt_html(definition["trial_id"], instructions, display_html, response_html)


def numbered_circle(item):
    stimulus = item["stimulus"]
    x = item["position"]["x"]
    y = item["position"]["y"]
    number = str(item["number"])
    return [
        circle(stimulus, x, y, f"display_{number}"),
        Text(
            f"label_{number}",
            number,
            x,
            y,
            attributes={"font-size": 18, "font-weight": "bold", "fill": "#111111"},
        ),
    ]


def fixation_objects(include_display_fixation=False):
    objects = [
        Text(
            "fixation",
            "+",
            50,
            50,
            attributes={"font-size": 36, "font-weight": "bold", "fill": "#111111"},
        )
    ]
    if include_display_fixation:
        objects.append(
            Text(
                "display_hint",
                "Keep your eyes on the center.",
                50,
                82,
                attributes={"font-size": 8, "fill": "#555555"},
            )
        )
    return objects


def pair_frames(stimulus_a, stimulus_b):
    return [
        Frame(fixation_objects(), duration=FIXATION_SECONDS),
        Frame(
            [circle(stimulus_a, 32, 50, "left"), circle(stimulus_b, 68, 50, "right")],
            duration=STIMULUS_SECONDS,
        ),
        Frame([], duration=DELAY_SECONDS),
        Frame([], activate_control_response=True, activate_control_submit=True),
    ]


def display_positions(set_size):
    center_x, center_y, radius = 50, 50, 34
    return [
        {
            "x": round(center_x + radius * math.cos(2 * math.pi * i / set_size - math.pi / 2), 2),
            "y": round(center_y + radius * math.sin(2 * math.pi * i / set_size - math.pi / 2), 2),
            "angle_degrees": round((360 * i / set_size) - 90, 2),
        }
        for i in range(set_size)
    ]


def identification_frames(definition):
    display_objects = fixation_objects(include_display_fixation=False)
    for item in definition["display_items"]:
        display_objects.extend(numbered_circle(item))
    probe = definition["probe_stimulus"]
    return [
        Frame(fixation_objects(include_display_fixation=True), duration=FIXATION_SECONDS),
        Frame(display_objects, duration=STIMULUS_SECONDS),
        Frame([], duration=DELAY_SECONDS),
        Frame(
            [
                circle(probe, 50, 44, "probe"),
                Text(
                    "probe_label",
                    "Probe: choose the display number that best matches",
                    50,
                    75,
                    attributes={"font-size": 8, "fill": "#333333"},
                ),
            ],
            activate_control_response=True,
            activate_control_submit=True,
        ),
    ]


def parse_time(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ")
    except ValueError:
        return None


def event_time(event_log, event_names):
    for event in event_log or []:
        if event.get("eventType") in event_names:
            parsed = parse_time(event.get("localTime"))
            if parsed is not None:
                return parsed
    return None


class ReactionTimePushButtonControl(PushButtonControl):
    def format_answer(self, raw_answer, **kwargs):
        event_log = kwargs.get("metadata", {}).get("event_log", [])
        click_time = event_time(event_log, {"pushButtonClicked"})
        enable_time = event_time(
            event_log,
            {"sdiResponseEnable", "graphicPromptEnableResponse", "responseEnable", "promptEnd", "trialStart"},
        )
        reaction_time_sec = None
        if click_time is not None and enable_time is not None:
            reaction_time_sec = max(0.0, round((click_time - enable_time).total_seconds(), 4))
        return {"response": raw_answer, "reaction_time_sec": reaction_time_sec}


def choice_response(answer):
    return answer.get("response") if isinstance(answer, dict) else answer


def rt_response(answer):
    return answer.get("reaction_time_sec") if isinstance(answer, dict) else None


class MetadataTrial(StaticTrial):
    def format_answer(self, raw_answer, **kwargs):
        response = choice_response(raw_answer)
        return {
            "block": self.definition["block"],
            "trial_id": self.definition["trial_id"],
            "response": response,
            "reaction_time_sec": rt_response(raw_answer),
            "definition": self.definition,
        }


class SameDifferentTrial(MetadataTrial):
    time_estimate = FIXATION_SECONDS + STIMULUS_SECONDS + DELAY_SECONDS + 2.0

    def show_trial(self, experiment, participant):
        return ModularVisualChoicePage(
            label="same_different_trial",
            prompt_html=pair_prompt_html(
                self.definition,
                "Decide whether the two circles were identical or different. The circles disappear before you can answer.",
            ),
            choices=["same", "different"],
            labels=["Same", "Different"],
            bot_response=self.definition["correct_answer"],
            time_estimate=self.time_estimate,
        )

    def score_answer(self, answer, definition):
        return int(answer["response"] == definition["correct_answer"])


class SimilarityTrial(MetadataTrial):
    time_estimate = FIXATION_SECONDS + STIMULUS_SECONDS + DELAY_SECONDS + 3.0

    def show_trial(self, experiment, participant):
        return ModularVisualChoicePage(
            label="similarity_trial",
            prompt_html=pair_prompt_html(
                self.definition,
                "Rate how similar the two circles were. The circles disappear before the scale appears. Use 0 for completely dissimilar and 6 for completely similar.",
            ),
            choices=[str(i) for i in range(7)],
            labels=[
                "0 Dissimilar",
                "1",
                "2",
                "3",
                "4",
                "5",
                "6 Similar",
            ],
            arrange_vertically=False,
            bot_response=str(self.definition["simulated_rating"]),
            time_estimate=self.time_estimate,
        )

    def score_answer(self, answer, definition):
        return None


class IdentificationTrial(MetadataTrial):
    time_estimate = FIXATION_SECONDS + STIMULUS_SECONDS + DELAY_SECONDS + 3.0

    def show_trial(self, experiment, participant):
        return ModularVisualChoicePage(
            label="identification_trial",
            prompt_html=identification_prompt_html(
                self.definition,
                "Remember the numbered display. After it disappears, choose the display number most similar to the probe.",
            ),
            choices=[str(item["number"]) for item in self.definition["display_items"]],
            labels=[f"Item {item['number']}" for item in self.definition["display_items"]],
            arrange_vertically=False,
            bot_response=str(self.definition["nearest_item_number"]),
            time_estimate=self.time_estimate,
        )

    def format_answer(self, raw_answer, **kwargs):
        answer = super().format_answer(raw_answer, **kwargs)
        response = answer["response"]
        nearest = str(self.definition["nearest_item_number"])
        correct = str(self.definition["correct_item_number"])
        answer["nearest_neighbor_correct"] = response == nearest
        answer["accuracy"] = response == correct if self.definition["probe_present"] else response == nearest
        return answer

    def score_answer(self, answer, definition):
        return int(answer["accuracy"])


class ModularVisualChoicePage(ModularPage):
    def __init__(
        self,
        label,
        prompt_html,
        choices,
        labels,
        bot_response,
        time_estimate,
        arrange_vertically=True,
    ):
        super().__init__(
            label,
            prompt=Markup(prompt_html),
            control=ReactionTimePushButtonControl(
                choices=choices,
                labels=labels,
                arrange_vertically=arrange_vertically,
                bot_response=bot_response,
            ),
            time_estimate=time_estimate,
        )


def same_different_nodes():
    stimuli = load_stimuli()
    nodes = []
    for index, stimulus in enumerate(stimuli):
        nodes.append(
            StaticNode(
                definition={
                    "block": "same_different",
                    "trial_id": f"sd_same_{stimulus['stimulus_id']}",
                    "stimulus_a": stimulus,
                    "stimulus_b": stimulus,
                    "is_identical": True,
                    "correct_answer": "same",
                    "order_policy": "StaticTrialMaker randomizes node order for each participant.",
                    "pair_index": index,
                }
            )
        )
    for index, (stimulus_a, stimulus_b) in enumerate(combinations_with_replacement(stimuli, 2)):
        if stimulus_a["stimulus_id"] == stimulus_b["stimulus_id"]:
            continue
        nodes.append(
            StaticNode(
                definition={
                    "block": "same_different",
                    "trial_id": f"sd_diff_{stimulus_a['stimulus_id']}_{stimulus_b['stimulus_id']}",
                    "stimulus_a": stimulus_a,
                    "stimulus_b": stimulus_b,
                    "is_identical": False,
                    "correct_answer": "different",
                    "order_policy": "StaticTrialMaker randomizes node order for each participant.",
                    "pair_index": index,
                }
            )
        )
    if PROFILE == "minimal":
        return [nodes[0], nodes[-1]]
    return nodes


def similarity_nodes():
    stimuli = load_stimuli()
    nodes = []
    for index, (stimulus_a, stimulus_b) in enumerate(combinations_with_replacement(stimuli, 2)):
        distance = hue_distance(stimulus_a, stimulus_b)
        simulated_rating = int(round(6 * (1 - distance / 180)))
        nodes.append(
            StaticNode(
                definition={
                    "block": "similarity",
                    "trial_id": f"sim_{stimulus_a['stimulus_id']}_{stimulus_b['stimulus_id']}",
                    "stimulus_a": stimulus_a,
                    "stimulus_b": stimulus_b,
                    "pair_identity": [stimulus_a["stimulus_id"], stimulus_b["stimulus_id"]],
                    "hue_distance_degrees": distance,
                    "simulated_rating": max(0, min(6, simulated_rating)),
                    "order_policy": "All unordered pairs including identical anchors; StaticTrialMaker randomizes node order.",
                    "pair_index": index,
                }
            )
        )
    if PROFILE == "minimal":
        return [nodes[0], nodes[-1]]
    return nodes


def identification_nodes():
    stimuli = load_stimuli()
    nodes = []
    for set_size in [3, 4, 5]:
        for repeat in range(2):
            for probe_present in [True, False]:
                start = (set_size + repeat * 2 + int(probe_present)) % len(stimuli)
                display = [stimuli[(start + offset) % len(stimuli)] for offset in range(set_size)]
                positions = display_positions(set_size)
                display_items = [
                    {"number": i + 1, "stimulus": stimulus, "position": positions[i]}
                    for i, stimulus in enumerate(display)
                ]
                if probe_present:
                    target_index = (repeat + set_size) % set_size
                    probe = display[target_index]
                    nearest_item_number = target_index + 1
                    correct_item_number = nearest_item_number
                else:
                    lure_candidates = [stimulus for stimulus in stimuli if stimulus not in display]
                    probe = lure_candidates[repeat % len(lure_candidates)]
                    nearest_item = min(
                        display_items,
                        key=lambda item: hue_distance(probe, item["stimulus"]),
                    )
                    nearest_item_number = nearest_item["number"]
                    correct_item_number = nearest_item_number
                trial_id = f"id_n{set_size}_{'present' if probe_present else 'absent'}_{repeat + 1}"
                nodes.append(
                    StaticNode(
                        definition={
                            "block": "identification",
                            "trial_id": trial_id,
                            "set_size": set_size,
                            "display_items": display_items,
                            "probe_stimulus": probe,
                            "probe_present": probe_present,
                            "nearest_item_number": nearest_item_number,
                            "correct_item_number": correct_item_number,
                            "sampling_policy": "For each set size, two probe-present and two probe-absent trials are generated deterministically from the stimulus ring.",
                            "display_duration_sec": STIMULUS_SECONDS,
                            "delay_duration_sec": DELAY_SECONDS,
                            "fixation_duration_sec": FIXATION_SECONDS,
                        }
                    )
                )
    return minimal(nodes, 2)


class Exp(psynet.experiment.Experiment):
    label = "Similarity discrimination identification"
    test_n_bots = 1

    timeline = Timeline(
        InfoPage(
            "Welcome. You will complete three short visual tasks with colored circles: same-different discrimination, similarity ratings, and multi-item identification.",
            time_estimate=5,
        ),
        InfoPage(
            "Each trial starts with a fixation cross. The main display appears briefly, disappears, and only then can you answer.",
            time_estimate=5,
        ),
        InfoPage("Block 1: decide whether two circles were the same or different.", time_estimate=4),
        StaticTrialMaker(
            id_="same_different",
            trial_class=SameDifferentTrial,
            nodes=same_different_nodes,
            expected_trials_per_participant="n_nodes",
            max_trials_per_participant="n_nodes",
            allow_repeated_nodes=False,
        ),
        InfoPage("Block 2: rate how similar two circles were on a 0 to 6 scale.", time_estimate=4),
        StaticTrialMaker(
            id_="similarity",
            trial_class=SimilarityTrial,
            nodes=similarity_nodes,
            expected_trials_per_participant="n_nodes",
            max_trials_per_participant="n_nodes",
            allow_repeated_nodes=False,
        ),
        InfoPage("Block 3: remember the numbered circle display, then match the probe to the closest item number.", time_estimate=5),
        StaticTrialMaker(
            id_="identification",
            trial_class=IdentificationTrial,
            nodes=identification_nodes,
            expected_trials_per_participant="n_nodes",
            max_trials_per_participant="n_nodes",
            allow_repeated_nodes=False,
        ),
        InfoPage("Next you will complete a brief Ishihara-style color-vision check.", time_estimate=4),
        ColorBlindnessTest(
            hide_after=2.0 if PROFILE == "minimal" else 3.0,
            performance_threshold=0 if PROFILE == "minimal" else 4,
        ),
        InfoPage("Finally, please answer a short demographics questionnaire.", time_estimate=4),
        BasicDemography(),
        InfoPage("Thank you for participating.", time_estimate=3),
    )

    def test_experiment(self):
        super().test_experiment()
        assert SameDifferentTrial.query.count() == len(same_different_nodes())
        assert SimilarityTrial.query.count() == len(similarity_nodes())
        assert IdentificationTrial.query.count() == len(identification_nodes())
        for trial in SameDifferentTrial.query.all():
            assert trial.answer["definition"]["stimulus_a"]["dimensions"]["color"]["hex"]
            assert trial.answer["response"] in ["same", "different"]
            assert trial.score in [0, 1]
        for trial in SimilarityTrial.query.all():
            assert trial.answer["response"] in [str(i) for i in range(7)]
            assert "reaction_time_sec" in trial.answer
        for trial in IdentificationTrial.query.all():
            assert trial.answer["definition"]["set_size"] in [3, 4, 5]
            assert len(trial.answer["definition"]["display_items"]) == trial.answer["definition"]["set_size"]
            assert "nearest_neighbor_correct" in trial.answer

    @classmethod
    def run_bot(cls, bot: Bot, **kwargs):
        super().run_bot(bot, **kwargs)


if __name__ == "__main__":
    print("Stimuli:")
    for stimulus in load_stimuli():
        color = stimulus["dimensions"]["color"]
        print(f"- {stimulus['stimulus_id']}: {color['hex']} hue={color['hue_degrees']}")
