# funciones para sacar mis datos de strava
import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()


def get_access_token():
    # con el refresh token pido uno nuevo (el de acceso caduca a las 6h)
    r = requests.post("https://www.strava.com/oauth/token", data={
        "client_id": os.getenv("STRAVA_CLIENT_ID"),
        "client_secret": os.getenv("STRAVA_CLIENT_SECRET"),
        "refresh_token": os.getenv("STRAVA_REFRESH_TOKEN"),
        "grant_type": "refresh_token",
    })
    r.raise_for_status()
    return r.json()["access_token"]


def get_activities(token):
    # strava da las actividades por paginas, pido hasta que venga una vacia
    url = "https://www.strava.com/api/v3/athlete/activities"
    headers = {"Authorization": f"Bearer {token}"}
    actividades = []
    page = 1
    while True:
        r = requests.get(url, headers=headers, params={"per_page": 200, "page": page})
        if r.status_code == 429:
            # me he pasado del limite, espero 15 min y repito
            print("limite de strava, espero 15 min...")
            time.sleep(15 * 60)
            continue
        r.raise_for_status()
        datos = r.json()
        if not datos:
            break
        actividades.extend(datos)
        print(f"pagina {page}: {len(datos)} actividades")
        page += 1
    return actividades