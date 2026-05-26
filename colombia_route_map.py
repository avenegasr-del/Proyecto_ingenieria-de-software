"""Genera un mapa interactivo de Colombia con una ruta entre dos aeropuertos.

Este script crea un mapa centrado en Colombia usando folium,
agrega marcadores personalizados para el aeropuerto de origen y
el aeropuerto de destino, y dibuja una ruta geodésica entre ellos.
"""

import math
from pathlib import Path
import folium

OUTPUT_FILE = Path(__file__).with_name("colombia_route_map_satellite.html")

# Coordenadas de ejemplo para dos aeropuertos colombianos.
ORIGIN = {
    "code": "BOG",
    "name": "Aeropuerto El Dorado",
    "latitude": 4.7110,
    "longitude": -74.0721,
}
DESTINATION = {
    "code": "MDE",
    "name": "Aeropuerto José María Córdova",
    "latitude": 6.1647,
    "longitude": -75.4231,
}

# Límites estrictos de Colombia para enfocar únicamente en el territorio nacional.
COLOMBIA_BOUNDS = [[-4.5, -82.5], [13.8, -66.2]]
COLOMBIA_CENTER = [4.5, -74.0]


def great_circle_points(start, end, steps=128):
    """Calcula una serie de puntos en la ruta geodésica entre dos coordenadas."""
    lat1 = math.radians(start[0])
    lon1 = math.radians(start[1])
    lat2 = math.radians(end[0])
    lon2 = math.radians(end[1])

    delta = 2 * math.asin(
        math.sqrt(
            math.sin((lat2 - lat1) / 2) ** 2
            + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
        )
    )

    if delta == 0:
        return [start]

    points = []
    for step in range(steps + 1):
        fraction = step / steps
        a = math.sin((1 - fraction) * delta) / math.sin(delta)
        b = math.sin(fraction * delta) / math.sin(delta)
        x = a * math.cos(lat1) * math.cos(lon1) + b * math.cos(lat2) * math.cos(lon2)
        y = a * math.cos(lat1) * math.sin(lon1) + b * math.cos(lat2) * math.sin(lon2)
        z = a * math.sin(lat1) + b * math.sin(lat2)
        lat = math.degrees(math.atan2(z, math.sqrt(x ** 2 + y ** 2)))
        lon = math.degrees(math.atan2(y, x))
        points.append([lat, lon])
    return points


def create_colombia_route_map(output_path: Path):
    """Crea y guarda el mapa interactivo en formato HTML."""
    colombia_map = folium.Map(
        location=COLOMBIA_CENTER,
        zoom_start=6,
        min_zoom=6,
        max_zoom=10,
        max_bounds=True,
        tiles=None,
        control_scale=True,
        zoom_control=True,
        prefer_canvas=True,
    )

    folium.TileLayer(
        tiles="https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri World Imagery",
        name="Esri WorldImagery",
        overlay=False,
        control=False,
        max_zoom=18,
        min_zoom=1,
    ).add_to(colombia_map)

    colombia_map.fit_bounds(COLOMBIA_BOUNDS, padding=(20, 20))

    folium.Rectangle(
        bounds=COLOMBIA_BOUNDS,
        color="#ffdd57",
        weight=2,
        fill=False,
        opacity=0.7,
    ).add_to(colombia_map)

    origin_popup = f"<strong>{ORIGIN['name']}</strong><br>{ORIGIN['code']}"
    destination_popup = f"<strong>{DESTINATION['name']}</strong><br>{DESTINATION['code']}"

    folium.CircleMarker(
        location=[ORIGIN["latitude"], ORIGIN["longitude"]],
        radius=8,
        color="#00d084",
        fill=True,
        fill_color="#00d084",
        fill_opacity=0.9,
        popup=origin_popup,
        tooltip=ORIGIN["code"],
    ).add_to(colombia_map)

    folium.CircleMarker(
        location=[DESTINATION["latitude"], DESTINATION["longitude"]],
        radius=8,
        color="#ff3b30",
        fill=True,
        fill_color="#ff3b30",
        fill_opacity=0.9,
        popup=destination_popup,
        tooltip=DESTINATION["code"],
    ).add_to(colombia_map)

    route_points = great_circle_points(
        [ORIGIN["latitude"], ORIGIN["longitude"]],
        [DESTINATION["latitude"], DESTINATION["longitude"]],
        steps=128,
    )

    folium.PolyLine(
        locations=route_points,
        color="#ffcc00",
        weight=8,
        opacity=0.95,
        tooltip=f"Ruta {ORIGIN['code']} → {DESTINATION['code']}",
        popup=f"Ruta aérea: {ORIGIN['code']} → {DESTINATION['code']}",
    ).add_to(colombia_map)

    colombia_map.save(output_path)
    print(f"Mapa guardado en: {output_path}")


if __name__ == "__main__":
    create_colombia_route_map(OUTPUT_FILE)
