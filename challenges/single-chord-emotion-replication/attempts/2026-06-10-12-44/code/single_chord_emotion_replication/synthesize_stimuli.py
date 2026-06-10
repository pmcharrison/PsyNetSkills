from __future__ import annotations

    import json
    import math
    import wave
    from pathlib import Path

    import numpy as np

    SAMPLE_RATE = 22050
    DURATION_SECONDS = 4.0
    ROOT_MIDI = 60

    TIMBRE_SPECS = {
        "piano": {
            "harmonics": [1.0, 0.56, 0.31, 0.18, 0.10, 0.05],
            "attack": 0.015,
            "decay": 0.70,
            "sustain": 0.34,
            "release": 1.10,
            "vibrato_hz": 0.0,
            "vibrato_depth": 0.0,
            "reverb": 0.09,
        },
        "strings": {
            "harmonics": [1.0, 0.82, 0.61, 0.43, 0.25, 0.16],
            "attack": 0.18,
            "decay": 0.45,
            "sustain": 0.72,
            "release": 0.85,
            "vibrato_hz": 5.3,
            "vibrato_depth": 0.0025,
            "reverb": 0.16,
        },
    }

    CHORD_SPECS = [
        {"family": "major_triad", "label": "C major root", "symbol": "C", "inversion": "root", "notes": [60, 64, 67]},
        {"family": "major_triad", "label": "C major 1st inversion", "symbol": "C/E", "inversion": "first", "notes": [64, 67, 72]},
        {"family": "major_triad", "label": "C major 2nd inversion", "symbol": "C/G", "inversion": "second", "notes": [67, 72, 76]},
        {"family": "minor_triad", "label": "C minor root", "symbol": "Cm", "inversion": "root", "notes": [60, 63, 67]},
        {"family": "minor_triad", "label": "C minor 1st inversion", "symbol": "Cm/Eb", "inversion": "first", "notes": [63, 67, 72]},
        {"family": "minor_triad", "label": "C minor 2nd inversion", "symbol": "Cm/G", "inversion": "second", "notes": [67, 72, 75]},
        {"family": "diminished_triad", "label": "C diminished root", "symbol": "Co", "inversion": "root", "notes": [60, 63, 66]},
        {"family": "augmented_triad", "label": "C augmented root", "symbol": "C+", "inversion": "root", "notes": [60, 64, 68]},
        {"family": "dominant_seventh", "label": "C dominant seventh root", "symbol": "C7", "inversion": "root", "notes": [60, 64, 67, 70]},
        {"family": "dominant_seventh", "label": "C dominant seventh 3rd inversion", "symbol": "C7/Bb", "inversion": "third", "notes": [58, 60, 64, 67]},
        {"family": "minor_seventh", "label": "C minor seventh root", "symbol": "Cm7", "inversion": "root", "notes": [60, 63, 67, 70]},
        {"family": "minor_seventh", "label": "C minor seventh 3rd inversion", "symbol": "Cm7/Bb", "inversion": "third", "notes": [58, 60, 63, 67]},
        {"family": "major_seventh", "label": "C major seventh root", "symbol": "Cmaj7", "inversion": "root", "notes": [60, 64, 67, 71]},
        {"family": "major_seventh", "label": "C major seventh 3rd inversion", "symbol": "Cmaj7/B", "inversion": "third", "notes": [59, 60, 64, 67]},
    ]


    def midi_to_hz(midi_note: int) -> float:
        return 440.0 * (2.0 ** ((midi_note - 69) / 12.0))


    def adsr_envelope(sample_count: int, timbre: str) -> np.ndarray:
        spec = TIMBRE_SPECS[timbre]
        attack = int(spec["attack"] * SAMPLE_RATE)
        decay = int(spec["decay"] * SAMPLE_RATE)
        release = int(spec["release"] * SAMPLE_RATE)
        sustain = max(sample_count - attack - decay - release, 1)

        env = np.concatenate(
            [
                np.linspace(0.0, 1.0, max(attack, 1), endpoint=False),
                np.linspace(1.0, spec["sustain"], max(decay, 1), endpoint=False),
                np.full(sustain, spec["sustain"]),
                np.linspace(spec["sustain"], 0.0, max(release, 1), endpoint=True),
            ]
        )
        if env.size < sample_count:
            env = np.pad(env, (0, sample_count - env.size), mode="edge")
        return env[:sample_count]


    def add_simple_reverb(signal: np.ndarray, amount: float) -> np.ndarray:
        if amount <= 0:
            return signal
        impulse = np.zeros(int(0.22 * SAMPLE_RATE))
        tap_positions = [0, int(0.031 * SAMPLE_RATE), int(0.071 * SAMPLE_RATE), int(0.121 * SAMPLE_RATE)]
        tap_gains = [1.0, amount * 0.55, amount * 0.32, amount * 0.18]
        for position, gain in zip(tap_positions, tap_gains):
            if position < impulse.size:
                impulse[position] = gain
        wet = np.convolve(signal, impulse, mode="full")[: signal.size]
        return wet


    def render_note(midi_note: int, timbre: str, duration_seconds: float) -> np.ndarray:
        sample_count = int(SAMPLE_RATE * duration_seconds)
        times = np.linspace(0.0, duration_seconds, sample_count, endpoint=False)
        spec = TIMBRE_SPECS[timbre]
        fundamental = midi_to_hz(midi_note)
        vibrato = 1.0 + spec["vibrato_depth"] * np.sin(2.0 * math.pi * spec["vibrato_hz"] * times)
        waveform = np.zeros_like(times)
        for harmonic_number, amplitude in enumerate(spec["harmonics"], start=1):
            frequency = fundamental * harmonic_number
            phase = 2.0 * math.pi * frequency * times * vibrato
            waveform += amplitude * np.sin(phase)
        waveform *= adsr_envelope(sample_count, timbre)
        return waveform


    def roughness_from_partials(frequencies: list[float], amplitudes: list[float]) -> float:
        roughness = 0.0
        for i, freq_a in enumerate(frequencies):
            for j, freq_b in enumerate(frequencies):
                if j <= i:
                    continue
                min_freq = min(freq_a, freq_b)
                s = 0.24 / (0.021 * min_freq + 19.0)
                x = abs(freq_b - freq_a)
                dissonance = math.exp(-3.5 * s * x) - math.exp(-5.75 * s * x)
                roughness += amplitudes[i] * amplitudes[j] * max(dissonance, 0.0)
        return roughness


    def spectral_irregularity(amplitudes: list[float]) -> float:
        if len(amplitudes) < 2:
            return 0.0
        return float(sum(abs(b - a) for a, b in zip(amplitudes, amplitudes[1:])) / (len(amplitudes) - 1))


    def extract_features(signal: np.ndarray, midi_notes: list[int], timbre: str) -> dict[str, float]:
        fft = np.fft.rfft(signal)
        magnitudes = np.abs(fft)
        freqs = np.fft.rfftfreq(signal.size, d=1.0 / SAMPLE_RATE)
        spectral_sum = float(magnitudes.sum()) or 1.0
        centroid = float(np.sum(freqs * magnitudes) / spectral_sum)
        high_energy_ratio = float(magnitudes[freqs >= 1000.0].sum() / spectral_sum)

        frame_size = 1024
        hop = 512
        flux_terms = []
        for start in range(0, signal.size - frame_size, hop):
            frame_a = np.abs(np.fft.rfft(signal[start : start + frame_size]))
            frame_b = np.abs(np.fft.rfft(signal[start + hop : start + hop + frame_size]))
            flux_terms.append(np.linalg.norm(frame_b - frame_a))
        spectral_flux = float(np.mean(flux_terms)) if flux_terms else 0.0

        energy = np.abs(signal)
        threshold = 0.9 * float(energy.max())
        onset_index = int(np.argmax(energy >= threshold))
        attack_time = max(onset_index / SAMPLE_RATE, 1e-6)

        base_amplitudes = []
        base_frequencies = []
        harmonic_profile = TIMBRE_SPECS[timbre]["harmonics"]
        for midi_note in midi_notes:
            base_frequency = midi_to_hz(midi_note)
            for harmonic_number, amplitude in enumerate(harmonic_profile[:4], start=1):
                base_frequencies.append(base_frequency * harmonic_number)
                base_amplitudes.append(amplitude)

        return {
            "brightness": round(centroid, 6),
            "high_energy_ratio": round(high_energy_ratio, 6),
            "spectral_flux": round(spectral_flux, 6),
            "log_attack_time": round(math.log10(attack_time), 6),
            "roughness": round(roughness_from_partials(base_frequencies, base_amplitudes), 6),
            "irregularity": round(spectral_irregularity(base_amplitudes), 6),
            "mean_midi_note": round(float(np.mean(midi_notes)), 6),
            "n_notes": len(midi_notes),
        }


    def render_chord(midi_notes: list[int], timbre: str) -> np.ndarray:
        layers = [render_note(midi_note, timbre, DURATION_SECONDS) for midi_note in midi_notes]
        signal = np.sum(layers, axis=0)
        signal /= max(np.max(np.abs(signal)), 1e-6)
        signal = add_simple_reverb(signal, TIMBRE_SPECS[timbre]["reverb"])
        signal /= max(np.max(np.abs(signal)), 1e-6)
        return signal.astype(np.float32)


    def write_wav(path: Path, signal: np.ndarray) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        clipped = np.clip(signal, -1.0, 1.0)
        pcm = (clipped * 32767.0).astype(np.int16)
        with wave.open(str(path), "wb") as handle:
            handle.setnchannels(1)
            handle.setsampwidth(2)
            handle.setframerate(SAMPLE_RATE)
            handle.writeframes(pcm.tobytes())


    def build_manifest(output_dir: Path) -> list[dict[str, object]]:
        stimuli = []
        for chord_index, chord in enumerate(CHORD_SPECS, start=1):
            for timbre in ["piano", "strings"]:
                stimulus_id = f"{chord['family']}__{chord['inversion']}__{timbre}"
                signal = render_chord(chord["notes"], timbre)
                relative_audio_path = Path("generated_stimuli") / f"{stimulus_id}.wav"
                audio_path = output_dir / relative_audio_path
                write_wav(audio_path, signal)
                features = extract_features(signal, chord["notes"], timbre)
                stimuli.append(
                    {
                        "stimulus_id": stimulus_id,
                        "family": chord["family"],
                        "symbol": chord["symbol"],
                        "label": chord["label"],
                        "inversion": chord["inversion"],
                        "timbre": timbre,
                        "duration_seconds": DURATION_SECONDS,
                        "sample_rate": SAMPLE_RATE,
                        "midi_notes": chord["notes"],
                        "audio_path": relative_audio_path.as_posix(),
                        "reconstruction": {
                            "root_reference": "C4",
                            "temperament": "12-TET",
                            "synthesis": "deterministic additive synthesis with timbre-specific harmonic envelopes",
                        },
                        "features": features,
                    }
                )
        return stimuli


    def main(output_dir: str | Path | None = None) -> Path:
        base_dir = Path(output_dir) if output_dir else Path(__file__).resolve().parent
        stimuli = build_manifest(base_dir)
        manifest_path = base_dir / "generated_stimuli" / "stimulus_manifest.json"
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(stimuli, indent=2) + "
", encoding="ascii")
        return manifest_path


    if __name__ == "__main__":
        path = main()
        print(f"Wrote {path}")
