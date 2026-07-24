"""
Référentiel géographique volontairement approximatif de Mbolo.

Nous utilisons le centre général des principales villes gabonaises pour
calculer une proximité utile sans enregistrer la position GPS exacte,
l'adresse ou les habitudes de déplacement d'un membre.
"""

from math import asin, cos, radians, sin, sqrt


# Coordonnées publiques et approximatives des centres urbains.
# La valeur technique "other" reste volontairement absente : une ville non
# précisée ne doit jamais recevoir une distance inventée.
GABON_CITY_CENTROIDS: dict[str, tuple[float, float]] = {
    "libreville": (0.4162, 9.4673),
    "port_gentil": (-0.7193, 8.7815),
    "franceville": (-1.6333, 13.5833),
    "oyem": (1.5995, 11.5793),
    "moanda": (-1.5655, 13.1987),
    "lambarene": (-0.7001, 10.2406),
    "mouila": (-1.8685, 11.0559),
    "tchibanga": (-2.8561, 11.0270),
    "koulamoutou": (-1.1367, 12.4630),
    "makokou": (0.5738, 12.8642),
    "bitam": (2.0759, 11.5007),
}


def approximate_city_distance_km(
    first_city: str,
    second_city: str,
) -> int | None:
    """
    Calcule la distance à vol d'oiseau entre deux centres urbains.

    None signifie que l'une des villes ne possède pas de position fiable.
    La valeur est arrondie au kilomètre et ne représente ni un itinéraire
    routier ni la position réelle d'un utilisateur.
    """

    first = GABON_CITY_CENTROIDS.get(first_city)
    second = GABON_CITY_CENTROIDS.get(second_city)

    if first is None or second is None:
        return None

    first_latitude, first_longitude = map(radians, first)
    second_latitude, second_longitude = map(radians, second)

    latitude_delta = second_latitude - first_latitude
    longitude_delta = second_longitude - first_longitude

    haversine = (
        sin(latitude_delta / 2) ** 2
        + cos(first_latitude)
        * cos(second_latitude)
        * sin(longitude_delta / 2) ** 2
    )

    earth_radius_km = 6371.0088
    return round(
        2 * earth_radius_km * asin(sqrt(haversine))
    )


def public_distance_label(distance_km: int | None) -> str | None:
    """
    Transforme une distance interne en libellé public suffisamment imprécis.

    L'arrondi par tranche empêche de présenter la donnée comme une localisation
    GPS exacte et rend l'information plus honnête pour l'utilisateur.
    """

    if distance_km is None:
        return None

    if distance_km < 10:
        return "Moins de 10 km"

    rounded_distance = max(
        10,
        round(distance_km / 10) * 10,
    )
    return f"Environ {rounded_distance} km"
