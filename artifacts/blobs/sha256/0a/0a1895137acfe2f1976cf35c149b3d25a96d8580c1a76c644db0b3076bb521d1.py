import math
import os
import random
from copy import deepcopy

import psynet.experiment
from markupsafe import Markup
from psynet.bot import Bot
from psynet.page import InfoPage
from psynet.timeline import Page, PageMaker, Timeline, join
from psynet.trial.chain import ChainNode, ChainTrial, ChainTrialMaker


CANVAS_SIZE = 520
SHAPE_SIZE = 400
DOT_RADIUS = 5
ACCURACY_TOLERANCE = 0.08 * SHAPE_SIZE
SHAPES = [
    "circle",
    "triangle",
    "square",
    "vertical_oval",
    "horizontal_oval",
    "pentagon",
]

FULL_STUDY = os.environ.get("VISUAL_PRIORS_FULL_STUDY", "0") == "1"
SEEDS_PER_SHAPE = {
    "circle": 400 if FULL_STUDY else 2,
    "triangle": 500 if FULL_STUDY else 2,
    "square": 500 if FULL_STUDY else 2,
    "vertical_oval": 500 if FULL_STUDY else 2,
    "horizontal_oval": 500 if FULL_STUDY else 2,
    "pentagon": 500 if FULL_STUDY else 2,
}


def random_offset():
    margin = CANVAS_SIZE - SHAPE_SIZE
    return {
        "x": random.randint(20, margin - 20),
        "y": random.randint(20, margin - 20),
    }


def polygon_vertices(n, radius=185, center=(SHAPE_SIZE / 2, SHAPE_SIZE / 2)):
    cx, cy = center
    return [
        (
            cx + radius * math.cos(-math.pi / 2 + 2 * math.pi * i / n),
            cy + radius * math.sin(-math.pi / 2 + 2 * math.pi * i / n),
        )
        for i in range(n)
    ]


def point_in_polygon(x, y, vertices):
    inside = False
    j = len(vertices) - 1
    for i, (xi, yi) in enumerate(vertices):
        xj, yj = vertices[j]
        if ((yi > y) != (yj > y)) and (
            x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi
        ):
            inside = not inside
        j = i
    return inside


def point_in_shape(shape, x, y):
    cx = cy = SHAPE_SIZE / 2
    if shape == "circle":
        return (x - cx) ** 2 + (y - cy) ** 2 <= 190**2
    if shape == "vertical_oval":
        return ((x - cx) / 135) ** 2 + ((y - cy) / 190) ** 2 <= 1
    if shape == "horizontal_oval":
        return ((x - cx) / 190) ** 2 + ((y - cy) / 135) ** 2 <= 1
    if shape == "square":
        return 20 <= x <= 380 and 20 <= y <= 380
    if shape == "triangle":
        return point_in_polygon(x, y, [(200, 20), (20, 380), (380, 380)])
    if shape == "pentagon":
        return point_in_polygon(x, y, polygon_vertices(5))
    raise ValueError(f"Unknown shape: {shape}")


def sample_point(shape):
    for _ in range(10000):
        x = random.uniform(20, SHAPE_SIZE - 20)
        y = random.uniform(20, SHAPE_SIZE - 20)
        if point_in_shape(shape, x, y):
            return {"x": round(x, 2), "y": round(y, 2)}
    raise RuntimeError(f"Could not sample a point inside {shape}")


def make_seed_definition(shape, seed_index):
    point = sample_point(shape)
    return {
        "shape": shape,
        "seed_id": f"{shape}_{seed_index:03d}",
        "generation": 0,
        "x": point["x"],
        "y": point["y"],
        "display_offset": random_offset(),
        "previous_response_accurate": None,
    }


def make_start_nodes():
    nodes = []
    for shape in SHAPES:
        for seed_index in range(SEEDS_PER_SHAPE[shape]):
            nodes.append(SpatialChainNode(definition=make_seed_definition(shape, seed_index)))
    return nodes


STIMULUS_TEMPLATE = """
{% extends "timeline-page.html" %}
{% block stylesheets %}
{{ super() }}
<style>
  .spatial-wrapper { text-align: center; }
  .spatial-canvas { background: white; border: 1px solid #eeeeee; max-width: 92vw; }
  .spatial-instruction { font-size: 1.2rem; margin-bottom: 1rem; }
</style>
{% endblock %}
{% block main_body %}
<div class="spatial-wrapper">
  <p class="spatial-instruction">{{ instruction }}</p>
  <canvas id="spatial-canvas" class="spatial-canvas" width="{{ canvas_size }}" height="{{ canvas_size }}"></canvas>
</div>
{% endblock %}
{% block scripts %}
{{ super() }}
<script>
const shape = {{ shape | tojson }};
const offset = {{ offset | tojson }};
const point = {{ point | tojson }};
const showDot = {{ show_dot | tojson }};
const responseMode = {{ response_mode | tojson }};
const autoAdvanceMs = {{ auto_advance_ms | tojson }};
const canvas = document.getElementById("spatial-canvas");
const ctx = canvas.getContext("2d");
let responsePoint = null;
let pageStartedAt = performance.now();

function shapePoint(x, y) {
  return [offset.x + x, offset.y + y];
}

function regularPolygon(n) {
  const points = [];
  const cx = offset.x + 200;
  const cy = offset.y + 200;
  const radius = 185;
  for (let i = 0; i < n; i++) {
    const angle = -Math.PI / 2 + 2 * Math.PI * i / n;
    points.push([cx + radius * Math.cos(angle), cy + radius * Math.sin(angle)]);
  }
  return points;
}

function drawShape() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.lineWidth = 6;
  ctx.strokeStyle = "black";
  ctx.fillStyle = "white";
  ctx.beginPath();
  if (shape === "circle") {
    ctx.arc(offset.x + 200, offset.y + 200, 190, 0, 2 * Math.PI);
  } else if (shape === "vertical_oval") {
    ctx.ellipse(offset.x + 200, offset.y + 200, 135, 190, 0, 0, 2 * Math.PI);
  } else if (shape === "horizontal_oval") {
    ctx.ellipse(offset.x + 200, offset.y + 200, 190, 135, 0, 0, 2 * Math.PI);
  } else if (shape === "square") {
    ctx.rect(offset.x + 20, offset.y + 20, 360, 360);
  } else {
    const points = shape === "triangle"
      ? [[offset.x + 200, offset.y + 20], [offset.x + 20, offset.y + 380], [offset.x + 380, offset.y + 380]]
      : regularPolygon(5);
    ctx.moveTo(points[0][0], points[0][1]);
    for (const p of points.slice(1)) ctx.lineTo(p[0], p[1]);
    ctx.closePath();
  }
  ctx.fill();
  ctx.stroke();
}

function drawDot(x, y, color = "black") {
  const p = shapePoint(x, y);
  ctx.beginPath();
  ctx.fillStyle = color;
  ctx.arc(p[0], p[1], {{ dot_radius }}, 0, 2 * Math.PI);
  ctx.fill();
}

function drawAll() {
  drawShape();
  if (showDot) drawDot(point.x, point.y, "black");
  if (responsePoint !== null) drawDot(responsePoint.x, responsePoint.y, "#d62728");
}

function pointInShape(x, y) {
  const cx = 200, cy = 200;
  if (shape === "circle") return (x - cx) ** 2 + (y - cy) ** 2 <= 190 ** 2;
  if (shape === "vertical_oval") return ((x - cx) / 135) ** 2 + ((y - cy) / 190) ** 2 <= 1;
  if (shape === "horizontal_oval") return ((x - cx) / 190) ** 2 + ((y - cy) / 135) ** 2 <= 1;
  if (shape === "square") return x >= 20 && x <= 380 && y >= 20 && y <= 380;
  function inPoly(poly) {
    let inside = false;
    let j = poly.length - 1;
    for (let i = 0; i < poly.length; i++) {
      const xi = poly[i][0], yi = poly[i][1];
      const xj = poly[j][0], yj = poly[j][1];
      const intersect = ((yi > y) !== (yj > y)) && (x < (xj - xi) * (y - yi) / ((yj - yi) || 1e-12) + xi);
      if (intersect) inside = !inside;
      j = i;
    }
    return inside;
  }
  if (shape === "triangle") return inPoly([[200, 20], [20, 380], [380, 380]]);
  return inPoly([[200, 15], [376, 143], [309, 350], [91, 350], [24, 143]]);
}

drawAll();

if (responseMode) {
  const confirmButton = document.getElementById("confirm-response");
  const message = document.getElementById("response-message");
  canvas.addEventListener("click", function(event) {
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    const canvasX = (event.clientX - rect.left) * scaleX;
    const canvasY = (event.clientY - rect.top) * scaleY;
    const x = canvasX - offset.x;
    const y = canvasY - offset.y;
    if (!pointInShape(x, y)) {
      message.textContent = "Please click inside the shape.";
      return;
    }
    responsePoint = {x: x, y: y, canvas_x: canvasX, canvas_y: canvasY};
    confirmButton.disabled = false;
    message.textContent = "You can click again to reposition the dot, or confirm your answer.";
    drawAll();
  });
  confirmButton.addEventListener("click", function() {
    if (responsePoint === null) return;
    psynet.nextPage({
      response_x: responsePoint.x,
      response_y: responsePoint.y,
      canvas_x: responsePoint.canvas_x,
      canvas_y: responsePoint.canvas_y,
      rt_ms: Math.round(performance.now() - pageStartedAt)
    });
  });
} else if (autoAdvanceMs !== null) {
  setTimeout(function() { psynet.nextPage(); }, autoAdvanceMs);
}
</script>
{% endblock %}
"""

RESPONSE_BODY = """
{% block main_body %}
<div class="spatial-wrapper">
  <p class="spatial-instruction">{{ instruction }}</p>
  <canvas id="spatial-canvas" class="spatial-canvas" width="{{ canvas_size }}" height="{{ canvas_size }}"></canvas>
  <p id="response-message">Click inside the shape to place the remembered dot.</p>
  <button id="confirm-response" class="btn btn-primary" disabled>Confirm response</button>
</div>
{% endblock %}
"""


class SpatialDisplayPage(Page):
    def __init__(self, label, definition, duration_ms, show_dot, instruction):
        super().__init__(
            label=label,
            template_str=STIMULUS_TEMPLATE,
            template_arg={
                "instruction": instruction,
                "canvas_size": CANVAS_SIZE,
                "dot_radius": DOT_RADIUS,
                "shape": definition["shape"],
                "offset": definition["display_offset"],
                "point": {"x": definition["x"], "y": definition["y"]},
                "show_dot": show_dot,
                "response_mode": False,
                "auto_advance_ms": duration_ms,
            },
            time_estimate=duration_ms / 1000,
            save_answer=False,
        )

    def get_bot_response(self, experiment, bot):
        return None


class SpatialResponsePage(Page):
    def __init__(self, label, definition):
        template = STIMULUS_TEMPLATE.replace(
            "{% block main_body %}\n<div class=\"spatial-wrapper\">"
            "\n  <p class=\"spatial-instruction\">{{ instruction }}</p>"
            "\n  <canvas id=\"spatial-canvas\" class=\"spatial-canvas\" width=\"{{ canvas_size }}\" height=\"{{ canvas_size }}\"></canvas>"
            "\n</div>\n{% endblock %}",
            RESPONSE_BODY,
        )
        self.definition = deepcopy(definition)
        super().__init__(
            label=label,
            template_str=template,
            template_arg={
                "instruction": "Place the dot where you remember seeing it.",
                "canvas_size": CANVAS_SIZE,
                "dot_radius": DOT_RADIUS,
                "shape": definition["shape"],
                "offset": definition["display_offset"],
                "point": {"x": definition["x"], "y": definition["y"]},
                "show_dot": False,
                "response_mode": True,
                "auto_advance_ms": None,
            },
            time_estimate=8,
        )

    def format_answer(self, raw_answer, **kwargs):
        dx = raw_answer["response_x"] - self.definition["x"]
        dy = raw_answer["response_y"] - self.definition["y"]
        accurate = abs(dx) <= ACCURACY_TOLERANCE and abs(dy) <= ACCURACY_TOLERANCE
        return {
            "shape": self.definition["shape"],
            "seed_id": self.definition.get("seed_id"),
            "generation": self.definition.get("generation", 0),
            "stimulus_x": self.definition["x"],
            "stimulus_y": self.definition["y"],
            "response_x": round(raw_answer["response_x"], 2),
            "response_y": round(raw_answer["response_y"], 2),
            "canvas_x": round(raw_answer["canvas_x"], 2),
            "canvas_y": round(raw_answer["canvas_y"], 2),
            "display_offset": self.definition["display_offset"],
            "rt_ms": raw_answer.get("rt_ms"),
            "error_x": round(dx, 2),
            "error_y": round(dy, 2),
            "accurate": accurate,
            "propagated": accurate,
        }

    def get_bot_response(self, experiment, bot):
        noise = random.gauss(0, 12)
        if random.random() < 0.15:
            noise += random.choice([-80, 80])
        x = min(max(self.definition["x"] + noise, 25), SHAPE_SIZE - 25)
        y = min(max(self.definition["y"] + random.gauss(0, 12), 25), SHAPE_SIZE - 25)
        if not point_in_shape(self.definition["shape"], x, y):
            x, y = self.definition["x"], self.definition["y"]
        offset = self.definition["display_offset"]
        raw_answer = {
            "response_x": x,
            "response_y": y,
            "canvas_x": offset["x"] + x,
            "canvas_y": offset["y"] + y,
            "rt_ms": random.randint(700, 3000),
        }
        return self.format_answer(raw_answer)


def feedback_page(participant):
    answer = participant.answer
    if answer["accurate"]:
        return InfoPage(
            Markup("<p style='color: green; font-size: 2rem;'>This was accurate.</p>"),
            time_estimate=1,
        )
    return InfoPage(
        Markup("<p style='color: red; font-size: 2rem;'>This was not accurate.</p>"),
        time_estimate=1,
    )


def make_practice_definition():
    point = sample_point("circle")
    return {
        "shape": "circle",
        "seed_id": "practice",
        "generation": "practice",
        "x": point["x"],
        "y": point["y"],
        "display_offset": random_offset(),
    }


def make_practice_trial():
    definition = make_practice_definition()
    return join(
        SpatialDisplayPage(
            "practice_stimulus",
            definition,
            duration_ms=4000,
            show_dot=True,
            instruction="Practice: remember the dot location.",
        ),
        SpatialDisplayPage(
            "practice_delay",
            {**definition, "display_offset": random_offset()},
            duration_ms=1000,
            show_dot=False,
            instruction="Keep the dot location in memory.",
        ),
        SpatialResponsePage("practice_response", definition),
        PageMaker(feedback_page, time_estimate=1),
    )


class SpatialChainNode(ChainNode):
    def make_next_definition(self, experiment, participant):
        answer = self.completed_and_processed_trials[0].answer
        definition = deepcopy(self.definition)
        definition["generation"] = self.degree + 1
        definition["display_offset"] = random_offset()
        definition["previous_response_accurate"] = answer["accurate"]
        if answer["accurate"]:
            definition["x"] = answer["response_x"]
            definition["y"] = answer["response_y"]
        return definition


class SpatialChainTrial(ChainTrial):
    time_estimate = 11

    def show_trial(self, experiment, participant):
        return join(
            SpatialDisplayPage(
                "experimental_stimulus",
                self.definition,
                duration_ms=1000,
                show_dot=True,
                instruction="Remember the dot location.",
            ),
            SpatialDisplayPage(
                "experimental_delay",
                {**self.definition, "display_offset": random_offset()},
                duration_ms=1000,
                show_dot=False,
                instruction="Keep the dot location in memory.",
            ),
            SpatialResponsePage("experimental_response", self.definition),
            PageMaker(feedback_page, time_estimate=1),
        )


def get_timeline():
    return Timeline(
        InfoPage(
            Markup(
                """
                <h3>Spatial memory task</h3>
                <p>You will briefly see a dot inside a geometric outline. Try to
                remember the dot's position, then place it where you remember it.</p>
                <p>First you will complete a practice trial, then one serial
                reproduction trial. In the real study, the response from one
                participant becomes the stimulus for the next participant.</p>
                """
            ),
            time_estimate=5,
        ),
        make_practice_trial(),
        InfoPage("The main trial starts now.", time_estimate=2),
        ChainTrialMaker(
            id_="visual_priors_serial_reproduction",
            trial_class=SpatialChainTrial,
            node_class=SpatialChainNode,
            chain_type="across",
            start_nodes=make_start_nodes,
            expected_trials_per_participant=1,
            max_trials_per_participant=1,
            max_nodes_per_chain=10,
            trials_per_node=1,
            balance_across_chains=True,
            recruit_mode="n_trials",
            propagate_failure=False,
        ),
        InfoPage("You finished the experiment. Thank you!", time_estimate=1),
    )


class Exp(psynet.experiment.Experiment):
    label = "Visual priors serial reproduction"
    timeline = get_timeline()
    test_n_bots = 8

    def test_check_bot(self, bot: Bot, **kwargs):
        assert len(bot.alive_trials) == 1
        for trial in bot.alive_trials:
            answer = trial.answer
            assert answer["shape"] in SHAPES
            assert 0 <= answer["response_x"] <= SHAPE_SIZE
            assert 0 <= answer["response_y"] <= SHAPE_SIZE
            assert "propagated" in answer
