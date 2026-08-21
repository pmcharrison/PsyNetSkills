# discovery-chains reference

Public source repository: <https://github.com/zhaobn/discovery-chains>

Commit inspected while creating this challenge:
`b89fcf85a475a8757f4d0bac6238edbb2ba43ca3`

Files inspected:

- `desc.md`
- `task-base.html`
- `task-after.html`
- `js/config.js`
- `js/grid.js`
- `js/task-base.js`
- `js/task-after.js`
- `js/selection.js`
- `js/messages.js`
- `js/utilities.js`
- `prepare_messages.py`

The repository defines a browser-based crystal-discovery game and a transmission
logic sketch. The full specification in `desc.md` asks for configurable chains,
conditions, generations, and participants per generation. The first generation
uses the base game flow; later generations receive aggregated messages prepared
from the previous generation's outputs.

The upstream repository does not include a top-level license file. Challenge
attempts should preserve attribution to the source repository and should copy or
adapt only the files needed for a local PsyNet implementation.
