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
def get_splits(token, activity_id):
    # detalle de una carrera: me quedo con los splits de cada km
    url = f"https://www.strava.com/api/v3/activities/{activity_id}"
    headers = {"Authorization": f"Bearer {token}"}
    while True:
        r = requests.get(url, headers=headers)
        if r.status_code == 429:
            # limite de 200 cada 15 min, espero y repito
            print("limite de strava, espero 15 min...")
            time.sleep(15 * 60)
            continue
        r.raise_for_status()
        break
    splits = r.json().get("splits_metric", [])
    for s in splits:
        s["activity_id"] = activity_id  # para saber de que carrera es cada km
    return splits
def get_gear(token, gear_id):
    # marca y modelo de unas zapatillas a partir de su id
    url = f"https://www.strava.com/api/v3/gear/{gear_id}"
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    g = r.json()
    return {"gear_id": gear_id, "marca": g.get("brand_name"), "modelo": g.get("model_name"),
            "km_totales": round(g.get("distance", 0) / 1000)}