"""BluePilot Ford lateral, the openpilot side (opendbc/bluepilot_lateral/HOSTS.md).

Upstream openpilot has no settings UI or CarControl extension for the library, so:
- settings come from bluepilot_settings.json at the repo root, read once at startup, except the steering
  mode, which is the FordSteeringMode param (driving settings on the device);
- the startup safety bits are ORed into the Ford safetyParam before CarParams is written for pandad;
- every frame, the model / vehicle-parameter inputs are copied into the Ford CarController's FrameInputs.
"""
import json
import os

from openpilot.common.basedir import BASEDIR
from openpilot.common.params import Params
from openpilot.common.swaglog import cloudlog

SETTINGS_FILE = os.path.join(BASEDIR, "bluepilot_settings.json")
SERVICES = ['modelV2', 'vehicleParameters', 'lateralDelay']

# FordSteeringMode param index -> (disable_BP_lat_UI, FordPrefLateralControl)
STEERING_MODES = {
  0: ("0", "1"),  # angle (BluePilot)
  1: ("0", "0"),  # curvature (BluePilot)
  2: ("1", "0"),  # curvature (comma stock): BluePilot lateral off, upstream Ford lateral and safety verbatim
}


def _text(v) -> str:
  # the library parses bools as "1"/"0" and numbers from text
  if isinstance(v, bool):
    return "1" if v else "0"
  return str(v)


def load_settings() -> dict[str, str]:
  try:
    with open(SETTINGS_FILE) as f:
      raw = json.load(f)
  except Exception:
    cloudlog.exception("bluepilot: settings file unreadable, using library defaults")
    raw = {}
  settings = {k: _text(v) for k, v in raw.items() if not k.startswith("_")}
  try:
    mode = int(Params().get("FordSteeringMode") or 0)
  except Exception:
    mode = 0
  settings["disable_BP_lat_UI"], settings["FordPrefLateralControl"] = STEERING_MODES.get(mode, STEERING_MODES[0])
  return settings


class BluePilotHost:
  def __init__(self, CI):
    from opendbc.bluepilot_lateral.params.manifest import PER_FRAME_KEYS
    from opendbc.bluepilot_lateral.hosts.starpilot.lateral import FrameInputs
    from opendbc.bluepilot_lateral.hosts.starpilot.safety_param import init_ford_safety_param_starpilot, lateral_inputs_required

    self.CI = CI
    self.settings = load_settings()
    self.active = CI.CP.brand == 'ford' and CI.CC is not None and lateral_inputs_required(CI.CP)
    if not self.active:
      return

    # startup bits -> Ford safetyParam bits 9-14 (read by ford_init on the panda), then rebuild the lateral from them
    init_ford_safety_param_starpilot(CI.CP, self.settings)
    CI.CC.bp_init()

    params = [FrameInputs.Param(key=k, value=self.settings[k].encode()) for k in PER_FRAME_KEYS if k in self.settings]
    self.frame_inputs = FrameInputs(params=params)
    CI.CC.bp_frame_inputs = self.frame_inputs
    cloudlog.warning(f"bluepilot: safetyParam {CI.CP.safetyConfigs[-1].safetyParam}, settings {self.settings}")

  def update(self, sm) -> None:
    """Copy this frame's model / vehicle-parameter inputs (HOSTS.md, 'Every frame: inputs')."""
    if not self.active:
      return
    li = self.frame_inputs.lateralInputs
    li.valid = False
    if not (sm.seen['modelV2'] and sm.seen['vehicleParameters']):
      return
    md, vp = sm['modelV2'], sm['vehicleParameters']
    if len(md.laneLines) < 3:
      return
    li.pathYawRate = list(md.orientationRate.z)
    li.pathX = list(md.position.x)
    li.pathY = list(md.position.y)
    li.laneLineLeftX = list(md.laneLines[1].x)
    li.laneLineLeftY = list(md.laneLines[1].y)
    li.laneLineRightX = list(md.laneLines[2].x)
    li.laneLineRightY = list(md.laneLines[2].y)
    li.laneLineProbs = list(md.laneLineProbs)
    li.laneLineStds = list(md.laneLineStds)
    li.laneChangeState = int(md.meta.laneChangeState.raw)
    li.laneChangeDirection = int(md.meta.laneChangeDirection.raw)
    li.steerRatio = float(vp.steerRatio)
    li.stiffnessFactor = float(vp.stiffnessFactor)
    li.roll = float(vp.roll)
    li.angleOffsetDeg = float(vp.angleOffsetDeg)
    li.lateralDelay = float(sm['lateralDelay'].lateralDelay)
    li.valid = True
