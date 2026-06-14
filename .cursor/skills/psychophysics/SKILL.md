---
name: psychophysics
description: Implement psychophysics experiments with PsyNet, focusing on precise visual displays, timing, response collection, and conservative interpretation of reference figures.
authors: [raja-marjieh, jacobyn]
---

# Implement PsyNet psychophysics experiment

## General guidelines

Follow the general workflow in `psynet-experiment-implementation/SKILL.md`.

- Prioritize correct display of all visual elements, correct timing, and no
  additional lingering display items such as fixation crosses or unrelated
  graphical elements that are not specified.

- Do not display any additional elements that are not mentioned in the task
  description.

- Make sure that PsyNet node and trial constructs are used correctly.

- Measure reaction time with JavaScript only when needed, and keep it minimal.
  Reaction time should be strongly tied to native events in PsyNet's event
  management system, and reaction-time JavaScript should be isolated. Responses
  should be recorded in the answer of each trial. Prefer existing PsyNet Control
  mechanisms where possible, for example `GraphicPrompt` frame sequencing with
  `prevent_control_response`/`activate_control_response`,
  `KeyboardPushButtonControl`, and event-log reaction-time extraction before
  adding custom JavaScript.

- Implement keyboard-button responses with `KeyboardPushButtonControl` rather
  than dedicated JavaScript.

- Center response buttons and questions around the stimuli.

- Do not show technical details that are not participant-facing, such as labeling
  display items "stimuli".

- When implementing an experiment based on a PDF paper, keep in mind that display
  items such as dots and stimuli may be exaggerated in size in schematic figures.
  If the paper provides explicit size specifications for the elements, use those
  values. If not, be cautious when estimating sizes from schematic figures,
  especially when the figure contains multiple components and the actual display
  is only one part of the image. However, if a screenshot or a clear
  single-display schematic is provided, the relative sizes are likely to be more
  indicative of the intended appearance.

## Reaction time from the native event log

Reaction time can usually be recorded without any bespoke timing JavaScript. Drive
the stimulus with a `GraphicPrompt` whose response is locked until the stimulus
frame, and read the timing back from the page's event log in `format_answer`.

The key wiring:

- Set `prevent_control_response=True` (and usually `prevent_control_submit=True`)
  on the `GraphicPrompt`, so the response interface is locked during the fixation
  frame.
- Mark the stimulus frame with `activate_control_response=True` (and
  `activate_control_submit=True`). PsyNet then fires the standard `responseEnable`
  event exactly at stimulus onset, which is logged in the event log.
- Use `KeyboardPushButtonControl`; each press logs a `pushButtonClicked` event.
- Reaction time is `localTime(pushButtonClicked) − localTime(responseEnable)`,
  i.e. stimulus-onset-to-response.

```python
from datetime import datetime
from psynet.graphics import Circle, Frame, GraphicPrompt, Path
from psynet.modular_page import KeyboardPushButtonControl, ModularPage


def _parse(t):
    # Front-end localTime values are ISO 8601 strings ending in "Z".
    return datetime.fromisoformat(t.replace("Z", "+00:00"))


def reaction_time_msec(event_log):
    onset = next((e["localTime"] for e in event_log if e["eventType"] == "responseEnable"), None)
    click = next((e["localTime"] for e in reversed(event_log) if e["eventType"] == "pushButtonClicked"), None)
    if onset is None or click is None:
        return None
    return (_parse(click) - _parse(onset)).total_seconds() * 1000.0


class RatingControl(KeyboardPushButtonControl):
    def format_answer(self, raw_answer, **kwargs):
        event_log = kwargs["metadata"].get("event_log", [])
        return {"rating": int(raw_answer), "rt_msec": reaction_time_msec(event_log)}


page = ModularPage(
    "trial",
    prompt=GraphicPrompt(
        text="How similar are these two shapes?",
        dimensions=[200, 100],
        frames=[
            Frame([Path("fixation", "M93,50 L107,50 M100,43 L100,57",
                        attributes={"stroke": "#000", "stroke-width": 3, "fill": "none"})],
                  duration=0.8),
            Frame([Circle("left", 60, 50, radius=26, attributes={"fill": "#ff0000"}),
                   Circle("right", 140, 50, radius=26, attributes={"fill": "#0000ff"})],
                  duration=None, activate_control_response=True, activate_control_submit=True),
        ],
        prevent_control_response=True,
        prevent_control_submit=True,
    ),
    control=RatingControl(choices=["1", "2", "3", "4", "5"],
                          keys=["Digit1", "Digit2", "Digit3", "Digit4", "Digit5"]),
    time_estimate=5,
)
```

For simulation, leave `bot_response` unset and implement `get_bot_response` to
return `BotResponse(raw_answer=..., metadata={"event_log": [...]})` with a
synthetic `responseEnable`/`pushButtonClicked` pair, so simulated bots flow through
the same `format_answer` and produce real `rt_msec` values. (Passing
`bot_response=None` instead would bypass `get_bot_response` and `format_answer`.)
