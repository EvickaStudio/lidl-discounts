from math import atan2, cos, radians, sin, sqrt


def distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    earth_radius_km = 6371.0
    dlat: float = radians(lat2 - lat1)
    dlon: float = radians(lon2 - lon1)

    a: float = (
        sin(dlat / 2) ** 2
        + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    )

    return earth_radius_km * 2 * atan2(sqrt(a), sqrt(1 - a))
