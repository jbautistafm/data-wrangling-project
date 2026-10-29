# funciones para pedir el clima a open-meteo (gratis, sin key)
import requests
import pandas as pd


def get_weather(lat, lon, inicio, fin):
    # pido el tiempo hora a hora entre dos fechas para una zona
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": inicio,  # formato "2020-05-01"
        "end_date": fin,
        "hourly": "temperature_2m,relative_humidity_2m,wind_speed_10m,precipitation",
        "timezone": "auto",  # horas en hora local, como strava
    }
    r = requests.get(url, params=params, timeout=60)
    r.raise_for_status()
    clima = pd.DataFrame(r.json()["hourly"])
    clima["time"] = pd.to_datetime(clima["time"])
    clima["lat"] = lat
    clima["lon"] = lon
    return clima