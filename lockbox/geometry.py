"""Virtual parcel-presence sensor based on overlap with the box interior."""


def parcel_present(center, size):
    """True when over half of the parcel's volume lies inside the usable cavity."""
    bounds = ((-0.29, 0.29), (-0.27, 0.27), (0.22, 0.70))
    overlap = 1.0
    volume = 1.0
    for axis in range(3):
        low = center[axis] - size[axis] / 2
        high = center[axis] + size[axis] / 2
        overlap *= max(0.0, min(high, bounds[axis][1]) - max(low, bounds[axis][0]))
        volume *= size[axis]
    return volume > 0 and overlap / volume > 0.5
