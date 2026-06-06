---
name: record-participant-video
description: Record a PsyNet participant flow to evidence/participant.mp4 with screen and experiment audio using ffmpeg. Use when collecting challenge evidence, creating participant.mp4, or documenting participant-facing behavior.
---

# Record participant video

Use this skill when a challenge attempt needs `evidence/participant.mp4`.

## Goal

Create an MP4 recording of the participant-facing PsyNet flow that includes:

- The browser viewport seen by the participant.
- Experiment audio when the experiment produces audio.
- Enough of the flow for evaluators to judge instructions, trials, responses,
  feedback, and completion behavior.

Use `ffmpeg` for recording. Do not use browser-only video capture as the default
because it can miss system audio.

## Workflow

1. Start the PsyNet experiment and open the generated ad page in a browser.
2. Confirm the browser viewport is sized reasonably, usually 1280x720 or larger.
3. Start `ffmpeg` screen and audio capture before interacting with the page.
4. Progress through the participant flow as a real participant would.
5. Stop recording after the completion page or after the relevant behavior has
   been demonstrated.
6. Save the final file as `evidence/participant.mp4`.
7. Play the MP4 back, or otherwise inspect it, before treating it as valid
   evidence.

If recording fails or audio is missing, do not imply the participant video is
complete. Record the failure and the missing evidence in `EVALUATION.md`.

## Linux

Use X11/Xvfb screen capture plus PulseAudio/PipeWire monitor audio. Prefer a
dedicated display or window size so the recording contains only the experiment.

```bash
ffmpeg -y \
  -video_size 1280x720 -framerate 30 -f x11grab -i "$DISPLAY" \
  -f pulse -i "$(pactl get-default-sink).monitor" \
  -c:v libx264 -pix_fmt yuv420p -c:a aac -shortest \
  evidence/participant.mp4
```

If PulseAudio is unavailable, inspect the available audio inputs and choose the
browser/system monitor source:

```bash
pactl list short sources
```

## macOS

Use `ffmpeg` with `avfoundation`. macOS usually needs a virtual audio device
such as BlackHole 2ch to capture browser/system audio.

1. Route browser or system output to BlackHole, or another configured virtual
   audio device.
2. List available capture devices:

```bash
ffmpeg -f avfoundation -list_devices true -i ""
```

1. Record using the selected screen and audio device:

```bash
ffmpeg -y \
  -f avfoundation -framerate 30 -i "1:BlackHole 2ch" \
  -c:v libx264 -pix_fmt yuv420p -c:a aac \
  evidence/participant.mp4
```

The screen device index may differ between machines. Use the device list rather
than assuming `1` is correct.

## Evidence notes

- Prefer a short successful recording over a long unfocused one.
- If system audio capture cannot be configured, include the visual recording if
  possible and explicitly document the missing audio in `EVALUATION.md`.
- For audio-focused experiments, add supporting evidence such as generated
  stimulus files, event logs, exported data, or command logs.
