"""Generate the stimulus manifest (``stimuli.json``) for the visual similarity experiment.

The stimulus set is a collection of colored circles of fixed size. Colors are
defined by hues evenly spaced around the HSL color wheel at full saturation and
50% lightness. The manifest deliberately stores a ``size`` (radius) field for
every stimulus so that a *size* dimension can be added later simply by emitting
extra rows here, without touching ``experiment.py``.

Run ``python make_stimuli.py`` to regenerate ``stimuli.json``.
"""

import colorsys
import json
import os

# Number of evenly spaced hues around the color wheel.
N_HUES = 6

# Human-readable labels for the six hues at 0, 60, 120, 180, 240, 300 degrees.
HUE_LABELS = ["red", "yellow", "green", "cyan", "blue", "magenta"]

# Fixed circle radius, expressed in the GraphicPrompt's abstract coordinate units.
# Stored per stimulus so that size can become a varying dimension later.
FIXED_RADIUS = 26


def hsl_to_hex(hue_deg: float, saturation: float = 1.0, lightness: float = 0.5) -> str:
    # colorsys uses HLS ordering with all arguments in [0, 1].
    r, g, b = colorsys.hls_to_rgb(hue_deg / 360.0, lightness, saturation)
    return "#{:02x}{:02x}{:02x}".format(round(r * 255), round(g * 255), round(b * 255))


def build_stimuli():
    stimuli = []
    for i in range(N_HUES):
        hue = round(i * 360 / N_HUES, 2)
        stimuli.append(
            {
                "id": f"circle_{i}",
                "label": HUE_LABELS[i],
                "hue": hue,
                "hex": hsl_to_hex(hue),
                "size": FIXED_RADIUS,
            }
        )
    return stimuli


def main():
    stimuli = build_stimuli()
    out_path = os.path.join(os.path.dirname(__file__), "stimuli.json")
    with open(out_path, "w") as f:
        json.dump(stimuli, f, indent=2)
        f.write("\n")
    print(f"Wrote {len(stimuli)} stimuli to {out_path}")


if __name__ == "__main__":
    main()
