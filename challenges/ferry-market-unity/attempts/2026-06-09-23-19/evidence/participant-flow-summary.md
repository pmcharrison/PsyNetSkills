# Participant flow test summary

The PsyNet participant flow launches and the Unity WebGL build loads successfully.
The browser automation advanced through consent and instructions, focused the
Unity canvas, and sent movement/click input to the WebGL app.

## Successful checks

- Unity assets were served by the local PsyNet server after `static/scripts/` was
  allowed into PsyNet's source package.
- Unity initialized in Chrome and logged `Init` / `GetPage` messages.
- The participant runner focused `#unity-canvas`.
- The runner sent `ArrowUp`, `ArrowLeft`, and `ArrowRight` events.
- A revised runner held `ArrowUp` continuously and tapped side keys about 10% of
  the time, following Ofer's movement guidance.

## Blocking result

The WebGL app did not call back to PsyNet completion during the tested sequences.
The most relevant logs are:

- `participant-actions.json`: initial canvas-click and arrow-key run; timed out.
- `participant-actions-mostly-up.json`: 600-step mostly-up run; timed out.
- `participant-actions-held-up.json`: held-ArrowUp run with 10% side taps; timed out.

Manual GUI inspection confirmed that the game loads and coins can be collected,
but the ferry/rating/completion UI did not appear during the test window.
