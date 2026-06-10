import math
import wave
from pathlib import Path

SAMPLE_RATE = 22050
DURATION_SECONDS = 3.0
AMPLITUDE = 0.32

STIMULI = {
    "andean_pulse.wav": [(392.0, 0.7), (587.3, 0.3)],
    "andean_lull.wav": [(329.6, 0.6), (493.9, 0.4)],
    "west_african_bright.wav": [(440.0, 0.5), (660.0, 0.5)],
    "west_african_low.wav": [(220.0, 0.7), (330.0, 0.3)],
    "east_asian_clear.wav": [(523.3, 0.6), (784.0, 0.4)],
    "east_asian_dark.wav": [(261.6, 0.5), (392.0, 0.5)],
}


def envelope(sample_index):
    seconds = sample_index / SAMPLE_RATE
    attack = min(seconds / 0.12, 1.0)
    release = min((DURATION_SECONDS - seconds) / 0.25, 1.0)
    pulse = 0.72 + 0.28 * math.sin(2 * math.pi * 2.2 * seconds)
    return max(0.0, min(attack, release)) * pulse


def sample_value(sample_index, partials):
    seconds = sample_index / SAMPLE_RATE
    value = sum(
        weight * math.sin(2 * math.pi * frequency * seconds)
        for frequency, weight in partials
    )
    return int(32767 * AMPLITUDE * envelope(sample_index) * value)


def write_wav(path, partials):
    total_samples = int(SAMPLE_RATE * DURATION_SECONDS)
    with wave.open(str(path), "w") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(SAMPLE_RATE)
        for index in range(total_samples):
            output.writeframesraw(sample_value(index, partials).to_bytes(2, "little", signed=True))


def main():
    audio_dir = Path(__file__).resolve().parents[1] / "data" / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    for filename, partials in STIMULI.items():
        write_wav(audio_dir / filename, partials)


if __name__ == "__main__":
    main()
