"""Hysteresis and temporal filtering shared by runtime and failure tests."""
import math
from .core import Sensors

from .config import CONFIG


class SensorFilter:
    def __init__(self):
        self.present = False
        self.candidate = False
        self.samples = 0
        self.good_samples = 0

    def read(self, door, bolt, distances, acceleration):
        valid = (len(distances) == CONFIG["sensor_grid"] ** 2 and len(acceleration) == 3
                 and all(math.isfinite(x) for x in [door, bolt, *distances, *acceleration]))
        if not valid:
            self.samples = self.good_samples = 0
            return Sensors(parcel_present=self.present, latch_locked=False, latch_unlocked=False,
                           door_closed=False, valid=False)
        self.good_samples += 1
        threshold = CONFIG["parcel_exit_distance_m"] if self.present else CONFIG["parcel_enter_distance_m"]
        candidate = min(distances) < threshold
        self.samples = self.samples + 1 if candidate == self.candidate else 1
        self.candidate = candidate
        if self.samples >= CONFIG["parcel_debounce_samples"]:
            self.present = candidate
        if self.good_samples < CONFIG["parcel_debounce_samples"]:
            return Sensors(parcel_present=self.present, latch_locked=False, latch_unlocked=False,
                           door_closed=False, valid=False)
        return Sensors(door_open=door > CONFIG["door_open_rad"], door_closed=door < CONFIG["door_closed_rad"],
                       parcel_present=self.present, latch_locked=bolt >= CONFIG["bolt_locked_m"],
                       latch_unlocked=bolt <= CONFIG["bolt_unlocked_m"],
                       impact=max(abs(x) for x in acceleration) > CONFIG["impact_threshold_m_s2"])
