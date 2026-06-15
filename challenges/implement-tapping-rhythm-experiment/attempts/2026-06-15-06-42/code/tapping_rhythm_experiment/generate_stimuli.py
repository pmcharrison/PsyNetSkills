"""Regenerate public-safe metronome WAV files and manifest."""

from experiment import MANIFEST_PATH, write_manifest

if __name__ == "__main__":
    write_manifest(MANIFEST_PATH)
    print(f"Wrote generated stimuli to {MANIFEST_PATH.parent}")
