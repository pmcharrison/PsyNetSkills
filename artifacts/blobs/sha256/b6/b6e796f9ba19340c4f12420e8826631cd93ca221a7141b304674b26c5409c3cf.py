# pylint: disable=unused-argument,abstract-method

import json
import math
import random
from statistics import mean

import psynet.experiment
from psynet.bot import Bot, BotResponse
from psynet.page import InfoPage
from psynet.timeline import FailedValidation, Page, Timeline
from psynet.trial.chain import ChainNetwork, ChainNode, ChainTrial, ChainTrialMaker


CANVAS_SIZE = 520
SHAPE_SIZE = 400
DOT_RADIUS = 6
PRACTICE_TRIALS = 10
CHAINS_PER_SHAPE = 2
MAX_CHAIN_GENERATIONS = 10
PRESENTATION_MS = 1000
PRACTICE_PRESENTATION_MS = 4000
RETENTION_MS = 1000
ACCURACY_TOLERANCE = 0.08

SHAPES = [
    "circle",
    "triangle",
    "square",
    "vertical_oval",
    "horizontal_oval",
    "pentagon",
]

SHAPE_LABELS = {
    "circle": "circle",
    "triangle": "equilateral triangle",
    "square": "square",
    "vertical_oval": "vertical oval",
    "horizontal_oval": "horizontal oval",
    "pentagon": "regular pentagon",
}


def polygon_vertices(n, radius=0.43, start_angle=-math.pi / 2):
    return [
        (
            0.5 + radius * math.cos(start_angle + 2 * math.pi * i / n),
            0.5 + radius * math.sin(start_angle + 2 * math.pi * i / n),
        )
        for i in range(n)
    ]


TRIANGLE_VERTICES = [(0.5, 0.1), (0.1, 0.86), (0.9, 0.86)]
PENTAGON_VERTICES = polygon_vertices(5)


def point_in_polygon(x, y, vertices):
    inside = False
    j = len(vertices) - 1
    for i, vertex in enumerate(vertices):
        xi, yi = vertex
        xj, yj = vertices[j]
        intersects = (yi > y) != (yj > y) and x < (
            (xj - xi) * (y - yi) / (yj - yi) + xi
        )
        if intersects:
            inside = not inside
        j = i
    return inside


def point_inside_shape(shape, x, y):
    if shape == "circle":
        return (x - 0.5) ** 2 + (y - 0.5) ** 2 <= 0.43**2
    if shape == "vertical_oval":
        return ((x - 0.5) / 0.30) ** 2 + ((y - 0.5) / 0.43) ** 2 <= 1
    if shape == "horizontal_oval":
        return ((x - 0.5) / 0.43) ** 2 + ((y - 0.5) / 0.30) ** 2 <= 1
    if shape == "square":
        return 0.14 <= x <= 0.86 and 0.14 <= y <= 0.86
    if shape == "triangle":
        return point_in_polygon(x, y, TRIANGLE_VERTICES)
    if shape == "pentagon":
        return point_in_polygon(x, y, PENTAGON_VERTICES)
    raise ValueError(f"Unknown shape: {shape}")


def sample_point(shape, rng):
    while True:
        x = rng.uniform(0.1, 0.9)
        y = rng.uniform(0.1, 0.9)
        if point_inside_shape(shape, x, y):
            return {"x": round(x, 4), "y": round(y, 4)}


def display_offset(rng):
    return {
        "offset_x": rng.randint(42, 78),
        "offset_y": rng.randint(42, 78),
    }


def svg_outline(shape):
    if shape == "circle":
        return '<circle class="shape-outline" cx="200" cy="200" r="172" />'
    if shape == "vertical_oval":
        return '<ellipse class="shape-outline" cx="200" cy="200" rx="120" ry="172" />'
    if shape == "horizontal_oval":
        return '<ellipse class="shape-outline" cx="200" cy="200" rx="172" ry="120" />'
    if shape == "square":
        return '<rect class="shape-outline" x="56" y="56" width="288" height="288" />'
    if shape == "triangle":
        return '<polygon class="shape-outline" points="200,40 40,344 360,344" />'
    if shape == "pentagon":
        points = " ".join(
            f"{round(x * SHAPE_SIZE, 1)},{round(y * SHAPE_SIZE, 1)}"
            for x, y in PENTAGON_VERTICES
        )
        return f'<polygon class="shape-outline" points="{points}" />'
    raise ValueError(f"Unknown shape: {shape}")


def make_definition(shape, chain_id, generation, target_x, target_y, rng):
    return {
        "shape": shape,
        "shape_label": SHAPE_LABELS[shape],
        "chain_id": chain_id,
        "generation": generation,
        "target_x": round(target_x, 4),
        "target_y": round(target_y, 4),
        "canvas_size": CANVAS_SIZE,
        "shape_size": SHAPE_SIZE,
        "dot_radius": DOT_RADIUS,
        "presentation_ms": PRESENTATION_MS,
        "retention_ms": RETENTION_MS,
        "accuracy_tolerance": ACCURACY_TOLERANCE,
        "svg_outline": svg_outline(shape),
        **display_offset(rng),
    }


def practice_definition(index):
    rng = random.Random(7000 + index)
    point = sample_point("circle", rng)
    definition = make_definition(
        shape="circle",
        chain_id=f"practice-{index + 1}",
        generation=0,
        target_x=point["x"],
        target_y=point["y"],
        rng=rng,
    )
    definition["presentation_ms"] = PRACTICE_PRESENTATION_MS
    definition["practice"] = True
    return definition


def get_start_nodes():
    rng = random.Random(20260613)
    nodes = []
    for shape in SHAPES:
        for chain_index in range(CHAINS_PER_SHAPE):
            point = sample_point(shape, rng)
            chain_id = f"{shape}-{chain_index + 1}"
            nodes.append(
                SpatialMemoryNode(
                    definition=make_definition(
                        shape=shape,
                        chain_id=chain_id,
                        generation=0,
                        target_x=point["x"],
                        target_y=point["y"],
                        rng=rng,
                    )
                )
            )
    return nodes


class SpatialMemoryPage(Page):
    def __init__(self, definition, label="spatial_memory", save_answer=True):
        self.definition = definition
        session_id = (
            f"memory-{label}-{definition['chain_id']}-{definition['generation']}"
        )
        super().__init__(
            label=label,
            time_estimate=(definition["presentation_ms"] + RETENTION_MS) / 1000 + 4,
            template_str=self.template(),
            js_vars={"memoryTrial": definition},
            scripts=[self.script()],
            css=[self.css()],
            session_id=session_id,
            save_answer=save_answer,
        )

    @staticmethod
    def template():
        return """
        {% extends "timeline-page.html" %}
        {% block main_body %}
        <div id="memory-task" class="memory-task">
          <h3 id="phase-title">Remember the dot location</h3>
          <p id="phase-instructions">
            Watch the dot carefully. It will disappear before you respond.
          </p>
          <svg id="memory-canvas" viewBox="0 0 520 520" width="430" height="430" style="visibility: hidden;"
               role="img" aria-label="Spatial memory shape">
            <g id="shape-layer"></g>
            <circle id="target-dot" r="6"></circle>
            <circle id="response-dot" r="6"></circle>
          </svg>
          <div id="feedback" aria-live="polite"></div>
          <button id="submit-response" class="btn btn-primary submit" disabled style="display: none;">
            Submit response
          </button>
        </div>
        <span id="psynet-event-listener"></span>
        {% endblock %}
        """

    @staticmethod
    def css():
        return """
        .memory-task {
          max-width: 660px;
          margin: 0 auto;
          text-align: center;
        }
        #memory-canvas {
          border: 1px solid #ddd;
          background: white;
          max-width: 100%;
          height: auto;
          cursor: default;
        }
        .shape-outline {
          fill: none;
          stroke: #111;
          stroke-width: 6;
        }
        #target-dot, #response-dot {
          fill: #111;
        }
        #response-dot {
          display: none;
          fill: #1f77b4;
        }
        #feedback {
          min-height: 2rem;
          margin: 0.35rem 0;
          font-weight: 700;
        }
        .feedback-good {
          color: #188038;
        }
        .feedback-bad {
          color: #b00020;
        }
        """

    @staticmethod
    def script():
        return """
        (function () {
          const trial = psynet.var.memoryTrial;
          const ns = "http://www.w3.org/2000/svg";
          const svg = document.getElementById("memory-canvas");
          const shapeLayer = document.getElementById("shape-layer");
          const targetDot = document.getElementById("target-dot");
          const responseDot = document.getElementById("response-dot");
          const feedback = document.getElementById("feedback");
          const submit = document.getElementById("submit-response");
          const title = document.getElementById("phase-title");
          const instructions = document.getElementById("phase-instructions");
          let response = null;
          let clickCount = 0;
          let acceptingResponses = false;

          shapeLayer.innerHTML = trial.svg_outline;
          shapeLayer.setAttribute("transform", `translate(${trial.offset_x}, ${trial.offset_y})`);
          targetDot.setAttribute("cx", trial.offset_x + trial.target_x * trial.shape_size);
          targetDot.setAttribute("cy", trial.offset_y + trial.target_y * trial.shape_size);
          targetDot.setAttribute("r", trial.dot_radius);
          responseDot.setAttribute("r", trial.dot_radius);
          svg.style.visibility = "visible";
          psynet.submit.disable();

          function localPoint(event) {
            const rect = svg.getBoundingClientRect();
            const transformed = {
              x: ((event.clientX - rect.left) / rect.width) * trial.canvas_size,
              y: ((event.clientY - rect.top) / rect.height) * trial.canvas_size,
            };
            return {
              x: (transformed.x - trial.offset_x) / trial.shape_size,
              y: (transformed.y - trial.offset_y) / trial.shape_size
            };
          }

          function insideShape(shape, x, y) {
            if (shape === "circle") {
              return Math.pow(x - 0.5, 2) + Math.pow(y - 0.5, 2) <= Math.pow(0.43, 2);
            }
            if (shape === "vertical_oval") {
              return Math.pow((x - 0.5) / 0.30, 2) + Math.pow((y - 0.5) / 0.43, 2) <= 1;
            }
            if (shape === "horizontal_oval") {
              return Math.pow((x - 0.5) / 0.43, 2) + Math.pow((y - 0.5) / 0.30, 2) <= 1;
            }
            if (shape === "square") {
              return x >= 0.14 && x <= 0.86 && y >= 0.14 && y <= 0.86;
            }
            return x >= 0 && x <= 1 && y >= 0 && y <= 1;
          }

          function setResponse(point) {
            clickCount += 1;
            response = {
              response_x: Number(point.x.toFixed(4)),
              response_y: Number(point.y.toFixed(4)),
              click_count: clickCount,
              shape: trial.shape,
              chain_id: trial.chain_id,
              generation: trial.generation
            };
            const errorX = Math.abs(response.response_x - trial.target_x);
            const errorY = Math.abs(response.response_y - trial.target_y);
            const accurate = errorX <= trial.accuracy_tolerance && errorY <= trial.accuracy_tolerance;
            response.error_x = Number(errorX.toFixed(4));
            response.error_y = Number(errorY.toFixed(4));
            response.accurate = accurate;
            responseDot.setAttribute("cx", trial.offset_x + response.response_x * trial.shape_size);
            responseDot.setAttribute("cy", trial.offset_y + response.response_y * trial.shape_size);
            responseDot.style.display = "block";
            feedback.textContent = accurate ? "This was accurate" : "This was not accurate";
            feedback.className = accurate ? "feedback-good" : "feedback-bad";
            submit.disabled = false;
          }

          function startResponsePhase() {
            targetDot.style.display = "none";
            title.textContent = "Reproduce the dot location";
            instructions.textContent = "Click inside the same shape where you remember the dot. You may click again before submitting.";
            svg.style.cursor = "crosshair";
            acceptingResponses = true;
            submit.style.display = "inline-block";
          }

          svg.addEventListener("click", (event) => {
            if (!acceptingResponses) {
              return;
            }
            const point = localPoint(event);
            if (!insideShape(trial.shape, point.x, point.y)) {
              feedback.textContent = "Please click inside the shape.";
              feedback.className = "feedback-bad";
              return;
            }
            setResponse(point);
          });

          submit.addEventListener("click", () => {
            if (response !== null) {
              psynet.nextPage(response, {
                target_x: trial.target_x,
                target_y: trial.target_y,
                presentation_ms: trial.presentation_ms,
                retention_ms: trial.retention_ms
              });
            }
          });

          setTimeout(() => {
            targetDot.style.display = "none";
            shapeLayer.style.display = "none";
            title.textContent = "Keep the dot in memory";
            instructions.textContent = "The screen is blank for a short delay.";
            setTimeout(() => {
              shapeLayer.style.display = "block";
              startResponsePhase();
            }, trial.retention_ms);
          }, trial.presentation_ms);
        })();
        """

    def format_answer(self, raw_answer, **kwargs):
        if not isinstance(raw_answer, dict):
            return {"invalid": True}
        x = float(raw_answer["response_x"])
        y = float(raw_answer["response_y"])
        error_x = abs(x - self.definition["target_x"])
        error_y = abs(y - self.definition["target_y"])
        accurate = (
            error_x <= self.definition["accuracy_tolerance"]
            and error_y <= self.definition["accuracy_tolerance"]
        )
        return {
            "shape": self.definition["shape"],
            "shape_label": self.definition["shape_label"],
            "chain_id": self.definition["chain_id"],
            "generation": self.definition["generation"],
            "target_x": self.definition["target_x"],
            "target_y": self.definition["target_y"],
            "response_x": round(x, 4),
            "response_y": round(y, 4),
            "error_x": round(error_x, 4),
            "error_y": round(error_y, 4),
            "euclidean_error": round(math.hypot(error_x, error_y), 4),
            "accurate": accurate,
            "click_count": int(raw_answer.get("click_count", 1)),
        }

    def validate(self, response, **kwargs):
        answer = response.answer
        if not isinstance(answer, dict) or answer.get("invalid"):
            return FailedValidation("Please click inside the shape before continuing.")
        if not point_inside_shape(
            answer["shape"], answer["response_x"], answer["response_y"]
        ):
            return FailedValidation("Please click inside the shape.")
        return None

    def get_bot_response(self, experiment, bot):
        rng = random.Random(bot.id * 1000 + self.definition["generation"])
        noisy_x = self.definition["target_x"] + rng.gauss(0, 0.035)
        noisy_y = self.definition["target_y"] + rng.gauss(0, 0.035)
        for scale in [1.0, 0.75, 0.5, 0.25, 0.0]:
            x = 0.5 + (noisy_x - 0.5) * scale
            y = 0.5 + (noisy_y - 0.5) * scale
            if point_inside_shape(self.definition["shape"], x, y):
                return BotResponse(
                    raw_answer={
                        "response_x": round(x, 4),
                        "response_y": round(y, 4),
                        "click_count": 1,
                    }
                )
        return BotResponse(
            raw_answer={
                "response_x": self.definition["target_x"],
                "response_y": self.definition["target_y"],
                "click_count": 1,
            }
        )


class SpatialMemoryNode(ChainNode):
    def make_next_definition(self, experiment, participant):
        answer = self.completed_and_processed_trials[0].answer
        rng = random.Random(f"{answer['chain_id']}-{answer['generation'] + 1}")
        return make_definition(
            shape=answer["shape"],
            chain_id=answer["chain_id"],
            generation=answer["generation"] + 1,
            target_x=answer["response_x"],
            target_y=answer["response_y"],
            rng=rng,
        )


class SpatialMemoryNetwork(ChainNetwork):
    pass


class SpatialMemoryTrial(ChainTrial):
    time_estimate = 6

    def show_trial(self, experiment, participant):
        return SpatialMemoryPage(self.definition)


class SpatialMemoryTrialMaker(ChainTrialMaker):
    response_timeout_sec = 90
    check_timeout_interval_sec = 30


def practice_pages():
    return [
        SpatialMemoryPage(
            practice_definition(i),
            label=f"practice_{i + 1}",
            save_answer=False,
        )
        for i in range(PRACTICE_TRIALS)
    ]


def make_timeline():
    return Timeline(
        InfoPage(
            """
            In this experiment you will briefly see a small black dot inside a geometric shape.
            Remember the dot's location, wait through a short blank delay, then click inside the
            same shape where you think the dot was. You can adjust your click before submitting.
            """,
            time_estimate=8,
        ),
        *practice_pages(),
        InfoPage(
            """
            Practice is complete. The next trials are the serial reproduction task:
            each remembered location can become the next location shown in the chain.
            """,
            time_estimate=4,
        ),
        SpatialMemoryTrialMaker(
            id_="spatial_memory_chains",
            trial_class=SpatialMemoryTrial,
            node_class=SpatialMemoryNode,
            network_class=SpatialMemoryNetwork,
            chain_type="across",
            start_nodes=get_start_nodes,
            expected_trials_per_participant="n_start_nodes",
            max_trials_per_participant="n_start_nodes",
            max_nodes_per_chain=MAX_CHAIN_GENERATIONS,
            trials_per_node=1,
            balance_across_chains=True,
            check_performance_at_end=False,
            check_performance_every_trial=False,
            recruit_mode="n_participants",
            target_n_participants=MAX_CHAIN_GENERATIONS,
        ),
        InfoPage("You finished the experiment. Thank you!", time_estimate=0),
    )


class Exp(psynet.experiment.Experiment):
    label = "Visual priors serial reproduction"
    timeline = make_timeline()
    test_n_bots = MAX_CHAIN_GENERATIONS
    test_time_factor = 0.0

    def test_check_bot(self, bot: Bot, **kwargs):
        assert not bot.failed
        chain_trials = [
            trial
            for trial in bot.alive_trials
            if isinstance(trial, SpatialMemoryTrial)
        ]
        assert len(chain_trials) == len(SHAPES) * CHAINS_PER_SHAPE
        for trial in chain_trials:
            assert trial.answer["shape"] in SHAPES
            assert point_inside_shape(
                trial.answer["shape"],
                trial.answer["response_x"],
                trial.answer["response_y"],
            )

    def test_check_bots(self, bots, **kwargs):
        super().test_check_bots(bots, **kwargs)
        trials = SpatialMemoryTrial.query.all()
        expected_trials = len(SHAPES) * CHAINS_PER_SHAPE * MAX_CHAIN_GENERATIONS
        assert len(trials) == expected_trials
        assert all(trial.answer is not None for trial in trials)
        final_generation_trials = [
            trial
            for trial in trials
            if trial.answer["generation"] == MAX_CHAIN_GENERATIONS - 1
        ]
        assert len(final_generation_trials) == len(SHAPES) * CHAINS_PER_SHAPE
        errors_by_shape = {}
        for trial in trials:
            errors_by_shape.setdefault(trial.answer["shape"], []).append(
                trial.answer["euclidean_error"]
            )
        assert set(errors_by_shape) == set(SHAPES)
        assert all(mean(errors) >= 0 for errors in errors_by_shape.values())


if __name__ == "__main__":
    exp = Exp()
    print(f"{exp.label}: {len(SHAPES) * CHAINS_PER_SHAPE} chains configured")
