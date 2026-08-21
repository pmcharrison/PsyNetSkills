"""Generate deterministic speech-to-song audio stimuli."""

from __future__ import annotations

import json
import shutil
import subprocess
import wave
from pathlib import Path

SENTENCES = [
    {"sentence_id": "s01", "text": "I love you"},
    {"sentence_id": "s09", "text": "how fast does a Zamboni go?"},
    {"sentence_id": "s18", "text": "I will head to the department store tomorrow"},
]

REPETITION_LEVELS = range(5)
SILENCE_MS = 350
VOICE = "en-us"
RATE = "155"
PITCH = "50"

ROOT = Path(__file__).parent
DATA_DIR = ROOT / "data"
AUDIO_DIR = DATA_DIR / "audio"
BASE_DIR = AUDIO_DIR / "base"
MANIFEST_PATH = DATA_DIR / "stimulus_manifest.json"


def _tts_command() -> str | None:
    return shutil.which("espeak-ng") or shutil.which("espeak")


def _write_silence(handle: wave.Wave_write, n_frames: int) -> None:
    sample_width = handle.getsampwidth()
    n_channels = handle.getnchannels()
    handle.writeframes(b"\x00" * n_frames * sample_width * n_channels)


def _read_wave(path: Path) -> tuple[wave._wave_params, bytes]:
    with wave.open(str(path), "rb") as source:
        return source.getparams(), source.readframes(source.getnframes())


def _compose_repetitions(base_path: Path, output_path: Path, n_presentations: int) -> float:
    params, frames = _read_wave(base_path)
    silence_frames = int(params.framerate * SILENCE_MS / 1000)
    with wave.open(str(output_path), "wb") as target:
        target.setparams(params)
        for index in range(n_presentations):
            if index > 0:
                _write_silence(target, silence_frames)
            target.writeframes(frames)
    with wave.open(str(output_path), "rb") as target:
        return target.getnframes() / target.getframerate()


def ensure_audio_assets(require_tts: bool = False) -> list[dict]:
    """Create or validate the local deterministic speech stimuli."""
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    BASE_DIR.mkdir(parents=True, exist_ok=True)

    tts = _tts_command()
    if tts is None and require_tts:
        raise RuntimeError("Audio generation requires espeak-ng or espeak.")

    manifest = []
    for sentence in SENTENCES:
        sentence_id = sentence["sentence_id"]
        base_path = BASE_DIR / f"{sentence_id}.wav"

        if not base_path.exists():
            if tts is None:
                raise RuntimeError(
                    f"Missing {base_path}; install espeak-ng or commit generated assets."
                )
            subprocess.run(
                [
                    tts,
                    "-v",
                    VOICE,
                    "-s",
                    RATE,
                    "-p",
                    PITCH,
                    "-w",
                    str(base_path),
                    sentence["text"],
                ],
                check=True,
            )

        for repetition_level in REPETITION_LEVELS:
            n_presentations = repetition_level + 1
            output_path = AUDIO_DIR / f"{sentence_id}_rep{repetition_level}.wav"
            if not output_path.exists():
                duration_sec = _compose_repetitions(
                    base_path, output_path, n_presentations
                )
            else:
                with wave.open(str(output_path), "rb") as existing:
                    duration_sec = existing.getnframes() / existing.getframerate()

            manifest.append(
                {
                    "sentence_id": sentence_id,
                    "sentence_text": sentence["text"],
                    "repetition_level": repetition_level,
                    "n_presentations": n_presentations,
                    "audio_path": str(output_path.relative_to(ROOT)),
                    "duration_sec": round(duration_sec, 3),
                    "pause_ms": SILENCE_MS,
                    "tts": {
                        "engine": Path(tts).name if tts else "pre-generated",
                        "voice": VOICE,
                        "rate": RATE,
                        "pitch": PITCH,
                    },
                }
            )

    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


if __name__ == "__main__":
    generated = ensure_audio_assets(require_tts=True)
    print(f"Wrote {len(generated)} audio stimulus entries to {MANIFEST_PATH}.")
