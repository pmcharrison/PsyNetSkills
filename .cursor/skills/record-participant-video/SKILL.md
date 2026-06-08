---
name: record-participant-video
description: Record a PsyNet participant flow to evidence/participant.mp4 with screen and experiment audio using ffmpeg. Use when collecting challenge evidence, creating participant.mp4, or documenting participant-facing behavior.
authors: [pmcharrison]
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

For audio-sensitive evidence, do not rely on a shared desktop/audio session
without calibration. Use the calibrated Linux workflow below, or record and
document why calibration was not possible.

When sharing a recorded video inline in a Cursor final response, warn the user
if the evidence depends on audio: the Cursor agent video player may not play the
audio track. Tell them to download the MP4 directly or view it through the
dashboard/PR preview to hear the audio.

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

If no PulseAudio/PipeWire source is exposed in Cursor Cloud, create a PulseAudio
null sink and route the browser through it:

```bash
sudo apt-get update
sudo apt-get install -y pulseaudio pulseaudio-utils

export XDG_RUNTIME_DIR="/tmp/xdg-runtime-$UID"
mkdir -p "$XDG_RUNTIME_DIR"
chmod 700 "$XDG_RUNTIME_DIR"
pulseaudio --start --exit-idle-time=-1 --log-target=stderr || true
pactl load-module module-null-sink sink_name=psynet_rec \
  sink_properties=device.description=psynet_rec || true
pactl set-default-sink psynet_rec
pactl list short sources
```

Launch Chrome or the scripted browser with the same PulseAudio environment so
WebAudio output is routed into the sink:

```bash
export PULSE_SERVER="unix:$XDG_RUNTIME_DIR/pulse/native"
google-chrome --no-first-run --new-window --window-size=1280,720 "$PARTICIPANT_URL"
```

Record the screen and the null-sink monitor:

```bash
ffmpeg -y \
  -video_size 1280x720 -framerate 30 -f x11grab -i "$DISPLAY" \
  -f pulse -i psynet_rec.monitor \
  -c:v libx264 -pix_fmt yuv420p -c:a aac -shortest \
  evidence/participant.mp4
```

For audio-sensitive recordings in Cursor Cloud, prefer an isolated display and
dedicated sink, then calibrate the recording:

1. Start a fresh Xvfb display and PulseAudio null sink for the recording.
2. Launch only the participant browser on that display and route it to that sink.
3. Record with large input queues and a low-latency x264 preset:

```bash
ffmpeg -y \
  -thread_queue_size 4096 \
  -video_size 1280x720 -framerate 30 -f x11grab -i "$DISPLAY" \
  -thread_queue_size 4096 -isync 0 -f pulse -i psynet_rec.monitor \
  -fps_mode cfr \
  -c:v libx264 -preset ultrafast -tune zerolatency -pix_fmt yuv420p \
  -c:a aac -shortest \
  evidence/participant_raw.mp4
```

4. Before publishing the participant recording, run a short sync probe in the
   same browser/display/sink that flashes the screen and plays a beep from the
   same JavaScript callback.
5. Measure the flash/beep offset from the resulting MP4. If audio is early or
   late, post-process the participant recording using the measured offset, for
   example:

```bash
ffmpeg -y -i evidence/participant_raw.mp4 \
  -filter_complex "[0:a]adelay=<delay_ms>|<delay_ms>[a]" \
  -map 0:v:0 -map "[a]" -c:v copy -c:a aac \
  evidence/participant.mp4
```

6. Save the sync-probe analysis logs with the evidence. Do not hard-code a
   delay from a previous run; measure it for the current recording environment.

Verify that the MP4 really has a non-silent audio stream:

```bash
ffprobe -hide_banner -show_streams evidence/participant.mp4
ffmpeg -hide_banner -i evidence/participant.mp4 \
  -af volumedetect -vn -sn -dn -f null /tmp/volumedetect-null
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
