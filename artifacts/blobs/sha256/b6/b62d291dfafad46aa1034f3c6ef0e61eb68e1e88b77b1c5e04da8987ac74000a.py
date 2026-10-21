"""Generate short deterministic WAV stimuli for local STEP tagging tests."""

from __future__ import annotations

import csv
import math
import wave
from pathlib import Path

SAMPLE_RATE = 8000
DURATION_SECONDS = 15
AMPLITUDE = 0.25
ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "stimuli.csv"
PATTERNS = {
    "us_bright": [392, 494, 587, 784],
    "us_melancholy": [440, 392, 349, 330],
    "brazil_warm": [330, 392, 494, 392, 523],
    "brazil_calm": [262, 330, 392, 330],
    "korea_clear": [294, 330, 392, 440, 523],
    "korea_tense": [349, 370, 349, 370, 415],
}


def envelope(position: float) -> float:
    attack = min(1.0, position / 0.05)
    release = min(1.0, (1.0 - position) / 0.08)
    return max(0.0, min(attack, release, 1.0))


def sample_value(frequency: float, time: float, local_position: float) -> int:
    fundamental = math.sin(2 * math.pi * frequency * time)
    overtone = 0.35 * math.sin(2 * math.pi * frequency * 2 * time)
    value = AMPLITUDE * envelope(local_position) * (fundamental + overtone)
    return int(max(-1.0, min(1.0, value)) * 32767)


def synthesize(path: Path, frequencies: list[int]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    total_frames = SAMPLE_RATE * DURATION_SECONDS
    note_frames = max(1, total_frames // len(frequencies))

    with wave.open(str(path), "w") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(SAMPLE_RATE)
        for frame in range(total_frames):
            note_index = min(len(frequencies) - 1, frame // note_frames)
            local_frame = frame - note_index * note_frames
            local_position = local_frame / note_frames
            time = frame / SAMPLE_RATE
            value = sample_value(frequencies[note_index], time, local_position)
            handle.writeframesraw(value.to_bytes(2, byteorder="little", signed=True))


def main() -> None:
    with MANIFEST.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    for row in rows:
        synthesize(ROOT / row["audio_path"], PATTERNS[row["clip_id"]])


if __name__ == "__main__":
    main()
