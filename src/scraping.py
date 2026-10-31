# funciones para sacar los ganadores de maratones de wikipedia
import time
import requests
import pandas as pd
from io import StringIO
from weather_api import get_weather

HEADERS = {"User-Agent": "data-wrangling-project (ironhack bootcamp)"}
CIUDADES = {"Berlin": (52.52, 13.40), "Londres": (51.50, -0.12)}

def leer_tablas(url, **kwargs):
    # descargo la pagina y saco sus tablas
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return pd.read_html(StringIO(r.text), **kwargs)

def limpiar_tiempos(df):
    # quito notas y WR, paso a segundos y a ritmo por km
    df["tiempo"] = df["tiempo"].astype(str).str.extract(r"(\d:\d{2}:\d{2})")[0]
    df = df.dropna(subset=["tiempo", "fecha"]).copy()
    df["segundos"] = pd.to_timedelta(df["tiempo"]).dt.total_seconds()
    df["ritmo_s_km"] = (df["segundos"] / 42.195).round(1)
    return df

def get_berlin():
    berlin = leer_tablas("https://en.wikipedia.org/wiki/List_of_winners_of_the_Berlin_Marathon",
                         match="Men's winner")[0]
    cols = berlin.columns
    h = berlin[[cols[1], cols[2], cols[3], cols[4]]].copy()
    m = berlin[[cols[1], cols[5], cols[6], cols[7]]].copy()
    h.columns = m.columns = ["fecha", "ganador", "pais", "tiempo"]
    h["sexo"], m["sexo"] = "M", "F"
    df = pd.concat([h, m], ignore_index=True)
    df["fecha"] = pd.to_datetime(df["fecha"].astype(str).str.replace(r"\[.*?\]", "", regex=True),
                                 format="mixed", errors="coerce")
    df = limpiar_tiempos(df)
    df["maraton"] = "Berlin"
    return df

def get_londres():
    tablas = leer_tablas("https://en.wikipedia.org/wiki/List_of_winners_of_the_London_Marathon")
    h = tablas[0].iloc[:, :4].copy()
    m = tablas[1].iloc[:, :4].copy()
    h.columns = m.columns = ["year", "ganador", "pais", "tiempo"]
    h["sexo"], m["sexo"] = "M", "F"
    df = pd.concat([h, m], ignore_index=True)
    # las fechas estan en la pagina principal
    fechas = leer_tablas("https://en.wikipedia.org/wiki/London_Marathon", match="Applicants")[0]
    fechas["fecha"] = pd.to_datetime(fechas["Date"].astype(str).str.replace(r"\[.*?\]", "", regex=True),
                                     format="mixed", errors="coerce")
    fechas["year"] = fechas["fecha"].dt.year
    df["year"] = pd.to_numeric(df["year"].astype(str).str[:4], errors="coerce")
    df["ganador"] = df["ganador"].astype(str).str.replace(r"\s*\(.*?\)", "", regex=True)
    df = df.merge(fechas[["year", "fecha"]], on="year", how="left").drop(columns="year")
    df = limpiar_tiempos(df)
    df["maraton"] = "Londres"
    return df

def get_clima_elite(elite):
    # clima medio de 9 a 11h el dia de cada carrera
    filas = []
    for _, c in elite[["maraton", "fecha"]].drop_duplicates().iterrows():
        lat, lon = CIUDADES[c["maraton"]]
        dia = c["fecha"].strftime("%Y-%m-%d")
        h = get_weather(lat, lon, dia, dia)
        h = h[h["time"].dt.hour.between(9, 11)]
        filas.append({"maraton": c["maraton"], "fecha": c["fecha"],
                      "temp": h["temperature_2m"].mean(), "humedad": h["relative_humidity_2m"].mean(),
                      "viento": h["wind_speed_10m"].mean(), "lluvia": h["precipitation"].sum()})
        time.sleep(0.2)
    return pd.DataFrame(filas)