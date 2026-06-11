"""Regenerate the local demonstration WAV stimuli used by this attempt."""

# The committed WAV files were produced with the same deterministic synthesis
# routine used during attempt setup. Researchers can replace stimulus_metadata.csv
# with real rows pointing to study-owned clips while preserving the columns.

from pathlib import Path
import math
import wave

STIMULI = {
    "warm_major": ("static/stimuli/warm_major.wav", [261.63, 329.63, 392.00]),
    "dark_minor": ("static/stimuli/dark_minor.wav", [220.00, 261.63, 329.63]),
    "bright_rise": ("static/stimuli/bright_rise.wav", [293.66, 369.99, 440.00]),
}
SAMPLE_RATE = 16000
DURATION = 3.0


def synthesize(stimulus_id: str, rel_path: str, freqs: list[float]) -> None:
    path = Path(rel_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "w") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(SAMPLE_RATE)
        frames = bytearray()
        for i in range(int(SAMPLE_RATE * DURATION)):
            t = i / SAMPLE_RATE
            envelope = min(1.0, t / 0.08, (DURATION - t) / 0.12)
            pulse = 0.65 + 0.35 * math.sin(2 * math.pi * 2.0 * t)
            sweep = 1.0 + 0.35 * (t / DURATION) if stimulus_id == "bright_rise" else 1.0
            value = sum(math.sin(2 * math.pi * f * sweep * t) for f in freqs) / len(freqs)
            sample = int(max(-1.0, min(1.0, value * envelope * pulse * 0.35)) * 32767)
            frames.extend(sample.to_bytes(2, byteorder="little", signed=True))
        wav.writeframes(frames)


if __name__ == "__main__":
    for stimulus_id, (rel_path, freqs) in STIMULI.items():
        synthesize(stimulus_id, rel_path, freqs)
