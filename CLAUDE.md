# CLAUDE.md — eliant-code/openpilot (EliPilot)

EliPilot is Elias's personal openpilot fork: latest openpilot plus BluePilot's
Ford steering, with a toggle to use Ford's own cruise. Elias does not read or
write code: Claude does the coding. Explain every change in plain language —
what it does in the car, not how the code works.

## Git rules (always)
- Only push to remotes owned by `eliant-code`. Never push to, open pull
  requests against, or file issues on commaai, BluePilot or any repository
  not owned by eliant-code.
- Work branch is `elipilot`. `master` tracks upstream commaai/openpilot;
  don't commit EliPilot changes there.
- Never force-push or delete a branch without asking Elias first.
- The `opendbc_repo` submodule points at eliant-code/opendbc (branch
  `elipilot`). Push the opendbc commit first, wait for its GitHub checks to
  pass, then set the pointer to that exact commit. A wrong hash makes the
  device's update fail.

## Pushing to `elipilot` ships to the car
- Elias's comma four runs this branch and updates from it. Every push to
  `elipilot` is downloaded by the device and installed on its next restart.
- Push only when Elias asks. Before pushing, say in one or two plain sentences
  what will change in the car, and get Elias's OK.
- Run whatever tests can run first. This fork has no GitHub checks of its own;
  opendbc's checks cover the safety code.

## The car and device
- Ford Focus Mk4 Titanium, MY2019 (built 2018), CAN (not CAN FD).
- comma four, no eGPU. SSH into it only when the car is parked and the device
  is offroad.

## Safety
- This code controls steering and speed on a real car. Never loosen safety
  limits (panda safety, torque or angle limits, allowed TX messages) without
  explaining the change and getting Elias's explicit approval.

## Logs
- Drive logs go in eliant-code/elipilot-logs, which must stay private (GPS).
