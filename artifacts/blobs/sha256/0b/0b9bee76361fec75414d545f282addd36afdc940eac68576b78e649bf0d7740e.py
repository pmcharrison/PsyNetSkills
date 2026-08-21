"""Generate simple sine-tone sequence stimuli for the experiment."""

from __future__ import annotations

import json
import math
import struct
import wave
from pathlib import Path


ROOT = Path(__file__).parent
MANIFEST = ROOT / "data" / "sequences.json"
AUDIO_DIR = ROOT / "data" / "generated_tones"
SAMPLE_RATE = 44_100
TONE_SECONDS = 0.42
GAP_SECONDS = 0.16
AMPLITUDE = 0.35
FREQUENCIES = {
    "low": 261.63,
    "medium": 329.63,
    "high": 392.00,
}


def load_sequences():
    return json.loads(MANIFEST.read_text())


def _sine_frames(frequency, duration_seconds):
    frame_count = int(SAMPLE_RATE * duration_seconds)
    for index in range(frame_count):
        envelope = min(1.0, index / 800, (frame_count - index) / 800)
        value = AMPLITUDE * envelope * math.sin(2 * math.pi * frequency * index / SAMPLE_RATE)
        yield struct.pack("<h", int(value * 32767))


def _silence_frames(duration_seconds):
    for _ in range(int(SAMPLE_RATE * duration_seconds)):
        yield struct.pack("<h", 0)


def write_sequence(sequence, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(SAMPLE_RATE)
        for tone_index, tone in enumerate(sequence):
            if tone_index:
                wav.writeframes(b"".join(_silence_frames(GAP_SECONDS)))
            wav.writeframes(b"".join(_sine_frames(FREQUENCIES[tone], TONE_SECONDS)))


def ensure_stimuli():
    for stimulus in load_sequences():
        path = ROOT / stimulus["audio_path"]
        if not path.exists():
            write_sequence(stimulus["sequence"], path)


if __name__ == "__main__":
    ensure_stimuli()
    print(f"Generated {len(load_sequences())} tone sequences in {AUDIO_DIR}.")
