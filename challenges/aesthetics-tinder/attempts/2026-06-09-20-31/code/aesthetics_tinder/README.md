# Aesthetics Tinder

This PsyNet demo asks participants to rate 15 real-world images with the keyboard:
left arrow for `Dislike`, right arrow for `Like`.

Stimuli are stored in `static/stimuli/` as committed 500 x 500 px JPEG files.
`stimuli/manifest.json` documents the Wikimedia Commons source page, original
image URL, license, artist, and credit metadata for each image.

To regenerate the demo image set:

```bash
~/PsyNet/.venv/bin/python scripts/prepare_stimuli.py
```
